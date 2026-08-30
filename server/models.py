from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, Literal

EngineState = Literal["PENDING","RUNNING","PASS","CHECK","BLOCKED","FAILED","REJECTED","SKIPPED"]

class NewSessionRequest(BaseModel):
    salon_name: str = "ABC Salon"
    specialist_name: str = "متخصص ارشد"
    client_label: str = "مشتری"

class ContextUpdate(BaseModel):
    service: str = "hair_general"
    goal: str = ""
    occasion: str = "Everyday"
    style: str = "Refined"
    change_level: str = "Noticeable"
    maintenance: str = "Moderate"
    exclusions: list[str] = Field(default_factory=list)
    notes: str = ""

class MessageRequest(BaseModel):
    text: str

class SelectLookRequest(BaseModel):
    look_id: str

class PreviewRequest(BaseModel):
    look_id: str
    scope: str = "hair_beard"
    extra_instruction: str = ""

class ValidationRequest(BaseModel):
    decision: Literal["PROCEED","MODIFY","CHECK_FIRST","DEFER","STOP"]
    notes: str = ""

class EngineRecord(BaseModel):
    id: str
    label: str
    state: EngineState = "PENDING"
    started_at: float | None = None
    finished_at: float | None = None
    duration_ms: int | None = None
    summary: str = ""
    detail: dict[str, Any] = Field(default_factory=dict)
