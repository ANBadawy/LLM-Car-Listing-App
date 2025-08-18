from __future__ import annotations
from typing import Optional, List, Literal
from pydantic import BaseModel, conint

# Type aliases
Windows = Literal["tinted", "electrical", "manual", "none"]
TireType = Literal["brand-new", "used", "winter", "summer", "all-season", "other"]

class Tires(BaseModel):
    type: Optional[TireType] = None
    manufactured_year: Optional[conint(ge=1990, le=2100)] = None

    model_config = {"extra": "forbid"}

class Notice(BaseModel):
    # Free-form to preserve phrases like "small accident"
    type: Optional[str] = None
    description: Optional[str] = None

    model_config = {"extra": "forbid"}

class Price(BaseModel):
    # Keep as int to avoid 220000.0 diffs
    amount: Optional[conint(ge=0)] = None
    currency: Optional[str] = None  # allows "L.E"

    model_config = {"extra": "forbid"}

class Car(BaseModel):
    body_type: Optional[str] = None  # filled later from IMAGE
    color: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    manufactured_year: Optional[conint(ge=1950, le=2100)] = None
    motor_size_cc: Optional[conint(ge=100, le=10000)] = None
    tires: Optional[Tires] = None
    windows: Optional[Windows] = None
    notices: Optional[List[Notice]] = None

    # Support either one (post-processing keeps only one)
    price: Optional[Price] = None
    estimated_price: Optional[Price] = None

    model_config = {"extra": "forbid"}

class CarDoc(BaseModel):
    car: Car

    model_config = {"extra": "forbid"}
