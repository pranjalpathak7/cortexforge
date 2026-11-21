import hmac
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from cortexforge.contracts import CreateRun, Resume, Review
from cortexforge.locking import run_lock
from cortexforge.repository import PolicyViolation
from cortexforge.workflow import AGENTS, Engine

load_dotenv()


def create_app(engine=None):
    @asynccontextmanager
    async def lifespan(app):
        if not hasattr(app.state, "engine"):
            app.state.engine = Engine()
        yield

    app = FastAPI(title="CortexForge", lifespan=lifespan)
    if engine:
        app.state.engine = engine
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Review-Token"],
    )

    def auth(x_review_token: str = Header(default="")):
        token = os.getenv("REVIEW_TOKEN", "")
        if not token or not hmac.compare_digest(token, x_review_token):
            raise HTTPException(401, "A configured human REVIEW_TOKEN is required")

    def current():
        return app.state.engine

    @app.exception_handler(PolicyViolation)
    async def policy_error(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=404, content={"detail": "Run not found"})

    @app.get("/api/health")
    def health(engine=Depends(current)):
        return {
            "status": "ok",
            "docker": engine.executor.available(),
            "live_configured": bool(os.getenv("GROQ_API_KEY") and os.getenv("LLM_MODEL")),
            "agents": AGENTS,
            "repair_limit": engine.limit,
            "model": os.getenv("LLM_MODEL", "not configured"),
        }

    @app.get("/api/runs", dependencies=[Depends(auth)])
    def runs(engine=Depends(current)):
        return engine.store.list()

    @app.post("/api/runs", dependencies=[Depends(auth)])
    def create(body: CreateRun, background: BackgroundTasks, engine=Depends(current)):
        run = engine.create(body)
        background.add_task(engine.run, run["id"])
        return run

    @app.get("/api/runs/{run_id}", dependencies=[Depends(auth)])
    def detail(run_id: str, engine=Depends(current)):
        return {**engine.store.get(run_id), "events": engine.store.history(run_id)}

    @app.post("/api/runs/{run_id}/cancel", dependencies=[Depends(auth)])
    def cancel(run_id: str, engine=Depends(current)):
        return engine.cancel(run_id)

    @app.post("/api/runs/{run_id}/resume", dependencies=[Depends(auth)])
    def resume(run_id: str, body: Resume, background: BackgroundTasks, engine=Depends(current)):
        engine.store.get(run_id)
        with run_lock(engine.data / f"{run_id}.lock"):
            result = engine.resume(run_id, clear_demo_fault=body.clear_demo_fault)
        background.add_task(engine.run, run_id)
        return result

    class Clarification(BaseModel):
        answer: str = Field(min_length=1, max_length=5000)

    @app.post("/api/runs/{run_id}/clarify", dependencies=[Depends(auth)])
    def clarify(run_id: str, body: Clarification, background: BackgroundTasks, engine=Depends(current)):
        engine.store.get(run_id)
        with run_lock(engine.data / f"{run_id}.lock"):
            result = engine.clarify(run_id, body.answer)
        background.add_task(engine.run, run_id)
        return result

    @app.post("/api/runs/{run_id}/review", dependencies=[Depends(auth)])
    def review(run_id: str, body: Review, engine=Depends(current)):
        engine.store.get(run_id)
        with run_lock(engine.data / f"{run_id}.lock"):
            return engine.review(run_id, body)

    @app.get("/api/runs/{run_id}/patch", response_class=PlainTextResponse, dependencies=[Depends(auth)])
    def patch(run_id: str, engine=Depends(current)):
        run = engine.store.get(run_id)
        if run["state"] != "APPROVED" or engine.repo.fingerprint(run["workspace"]) != run["tree_hash"]:
            raise PolicyViolation("Only unchanged, human-approved patches can be exported")
        return run["diff"]

    return app


app = create_app()
