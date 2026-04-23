from sqlalchemy import Column, String, Integer, Float, DateTime
from database import Base
from datetime import datetime
from sqlalchemy.sql import func
import uuid6

def generate_uuid7():
    return str(uuid6.uuid7())

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, index=True, default=generate_uuid7)

    name = Column(String(2), unique=True, index=True, nullable=False)

    gender = Column(String, nullable=False)
    gender_probability = Column(Float, nullable=False)

    age = Column(Integer, nullable=False)
    age_group = Column(String, nullable=False)

    country_id = Column(String, nullable=False)
    country_name = Column(String, nullable=False)
    country_probability = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
