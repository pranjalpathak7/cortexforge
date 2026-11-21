from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Specification(StrictModel):
    acceptance: list[str] = Field(min_length=1)
    tasks: list[str] = Field(min_length=1)
    questions: list[str] = []
    constraints: list[str] = []


class Design(StrictModel):
    files: list[str] = Field(min_length=1, max_length=12)
    rationale: str = Field(min_length=1)
    risks: list[str]
    validation: list[str] = Field(min_length=1)


class FileChange(StrictModel):
    path: str
    content: str = Field(max_length=100_000)


class Implementation(StrictModel):
    agrees_with_design: bool
    disagreement: str = ""
    changes: list[FileChange] = Field(max_length=12)
    summary: str


class Resolution(StrictModel):
    decision: Literal["retain", "revise", "escalate"]
    rationale: str
    design: Design


class CreateRun(StrictModel):
    requirement: str = Field(min_length=10, max_length=12_000)
    repository: str
    mode: Literal["live", "demo"] = "live"
    acceptance_profile: Literal["none", "payments_discount", "refunds"] = "none"
    fault: Literal["none", "test", "security", "malformed", "provider", "scope", "repeat", "disagree"] = (
        "none"
    )


class Review(StrictModel):
    decision: Literal["approve", "reject"]
    reviewer: str = Field(min_length=1, max_length=100)
    comment: str = Field(min_length=1, max_length=2000)
    evidence_hash: str


class Resume(StrictModel):
    clear_demo_fault: bool = False
