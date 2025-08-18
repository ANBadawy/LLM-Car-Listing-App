from __future__ import annotations
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, conint

class Tires(BaseModel):
    type: Optional[Literal["brand-new","used","winter","summer","all-season","other"]] = None
    manufactured_year: Optional[conint(ge=1990, le=2100)] = None

class Notice(BaseModel):
    # Keep type free-form to preserve phrases like "small accident"
    type: Optional[str] = None
    description: Optional[str] = None

class Price(BaseModel):
    # Keep amounts as INT to avoid 220000.0 diffs
    amount: Optional[conint(ge=0)] = None
    currency: Optional[str] = None  # free-form to allow "L.E"

class Car(BaseModel):
    # Filled later from IMAGE
    body_type: Optional[str] = None

    color: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    manufactured_year: Optional[conint(ge=1950, le=2100)] = None
    motor_size_cc: Optional[conint(ge=100, le=10000)] = None

    tires: Optional[Tires] = None

    # Normalize to a small enum to reduce drift
    windows: Optional[Literal["tinted","electrical","manual","none"]] = None

    notices: Optional[List[Notice]] = None

    # Support BOTH keys, but only one should be present after post-processing
    price: Optional[Price] = None
    estimated_price: Optional[Price] = None

class CarDoc(BaseModel):
    car: Car
