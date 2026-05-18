"""Shared schema primitives."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class AppBaseModel(BaseModel):
    """Base schema model for API contracts."""

    model_config = ConfigDict(extra="forbid")


Latitude = Annotated[float, Field(ge=-90, le=90)]
Longitude = Annotated[float, Field(ge=-180, le=180)]
ScoreValue = Annotated[int, Field(ge=0, le=100)]
ConfidenceRatio = Annotated[float, Field(ge=0, le=1)]
PositiveInt = Annotated[int, Field(ge=0)]
PositiveFloat = Annotated[float, Field(ge=0)]
CreatedAt = datetime
