from pydantic import BaseModel
from datetime import datetime
from typing import List


class ProfileCreate(BaseModel):
    name: str


class ProfileResponse(BaseModel):
    id: str
    name: str
    gender: str
    gender_probability: float
    age: int
    age_group: str
    country_id: str
    country_name: str
    country_probability: float
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileListResponse(BaseModel):
    status: str
    page: int
    limit: int
    total: int
    data: List[ProfileResponse]

    class Config:
        from_attributes = True
