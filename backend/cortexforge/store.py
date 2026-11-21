import json
from datetime import UTC, datetime

from sqlalchemy import Column, Integer, MetaData, String, Table, Text, create_engine, select, update


def now():
    return datetime.now(UTC).isoformat()


class Store:
    """Durable run documents and append-only evidence, with optimistic concurrency."""

    def __init__(self, url):
        self.engine = create_engine(url)
        metadata = MetaData()
        self.runs = Table(
            "runs",
            metadata,
            Column("id", String, primary_key=True),
            Column("version", Integer, nullable=False),
            Column("document", Text, nullable=False),
        )
        self.events = Table(
            "events",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("run_id", String, index=True),
            Column("time", String),
            Column("kind", String),
            Column("payload", Text),
        )
        metadata.create_all(self.engine)

    def create(self, run):
        run["version"] = 0
        with self.engine.begin() as conn:
            conn.execute(self.runs.insert().values(id=run["id"], version=0, document=json.dumps(run)))

    def get(self, run_id):
        with self.engine.connect() as conn:
            value = conn.execute(
                select(self.runs.c.document).where(self.runs.c.id == run_id)
            ).scalar_one_or_none()
        if value is None:
            raise KeyError(run_id)
        return json.loads(value)

    def save(self, run):
        old = run["version"]
        run["version"] += 1
        run["updated"] = now()
        with self.engine.begin() as conn:
            result = conn.execute(
                update(self.runs)
                .where(self.runs.c.id == run["id"], self.runs.c.version == old)
                .values(version=run["version"], document=json.dumps(run))
            )
            if result.rowcount != 1:
                raise RuntimeError("Concurrent run update rejected")

    def event(self, run_id, kind, payload):
        with self.engine.begin() as conn:
            conn.execute(
                self.events.insert().values(run_id=run_id, time=now(), kind=kind, payload=json.dumps(payload))
            )

    def history(self, run_id):
        with self.engine.connect() as conn:
            rows = (
                conn.execute(
                    select(self.events).where(self.events.c.run_id == run_id).order_by(self.events.c.id)
                )
                .mappings()
                .all()
            )
        return [{**r, "payload": json.loads(r["payload"])} for r in rows]

    def cancellation_requested(self, run_id):
        with self.engine.connect() as conn:
            return (
                conn.execute(
                    select(self.events.c.id)
                    .where(self.events.c.run_id == run_id, self.events.c.kind == "cancellation_requested")
                    .limit(1)
                ).first()
                is not None
            )

    def list(self):
        with self.engine.connect() as conn:
            return [json.loads(x) for x in conn.execute(select(self.runs.c.document)).scalars()]
