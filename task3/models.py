from datetime import datetime

from pydantic import BaseModel, Field


class Submeters(BaseModel):
    """Energy (Wh) from the three submeters. Same names as the MongoDB documents."""

    sub_metering_1: float = Field(ge=0)  # kitchen
    sub_metering_2: float = Field(ge=0)  # laundry
    sub_metering_3: float = Field(ge=0)  # water heater and air conditioning


class ReadingCreate(BaseModel):
    """What the client sends for POST and PUT (a full reading, without an id)."""

    recorded_at: datetime
    global_active_power: float = Field(ge=0)
    global_reactive_power: float = Field(ge=0)
    voltage: float = Field(gt=0)
    global_intensity: float = Field(ge=0)
    submeters: Submeters


class Reading(ReadingCreate):
    """What the API returns: a reading plus its id.

    MySQL ids are integers (reading_id), MongoDB ids are strings (_id),
    so id accepts either.
    """

    id: int | str
    