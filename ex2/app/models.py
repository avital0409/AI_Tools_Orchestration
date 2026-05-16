from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

Intent = Literal["getWeather", "calculateMath", "getExchangeRate", "generalChat"]

class RouterParameters(BaseModel):
    model_config = ConfigDict(extra="ignore")

    city: Optional[str] = None
    cities: Optional[list[str]] = None
    comparison: Optional[bool] = None
    expression: Optional[str] = None
    word_problem: Optional[bool] = None
    currencyCode: Optional[str] = None
    currencyCodes: Optional[list[str]] = None
    conversion: Optional[bool] = None

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
