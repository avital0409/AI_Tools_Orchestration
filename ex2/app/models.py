from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

Intent = Literal["getWeather", "calculateMath", "getExchangeRate", "generalChat"]

class RouterParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city: Optional[str] = None
    expression: Optional[str] = None
    currencyCode: Optional[str] = None

class RouterDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Intent
    parameters: RouterParameters
    confidence: float = Field(ge=0, le=1)

class FinalAnswer(BaseModel):
    response: str

class GuardrailCheck(BaseModel):
    blocked: bool
    reason: str
