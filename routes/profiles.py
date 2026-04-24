from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
import models
from schemas import ProfileCreate, ProfileResponse, ProfileListResponse
from services.external_apis import fetch_external_data
from uuid6 import uuid7

router = APIRouter(prefix="/api/profiles", tags=["Profiles"])


@router.get("", response_model=ProfileListResponse)
def get_profiles(
    gender: Optional[str] = None,
    country_id: Optional[str] = None,
    age_group: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_gender_probability: Optional[float] = None,
    min_country_probability: Optional[float] = None,
    sort_by: Optional[str] = None,
    order: str = "asc",
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):

    if limit > 50:
        limit = 50

    if page < 1:
        page = 1

    query = db.query(models.Profile)

    if gender:
        query = query.filter(models.Profile.gender == gender)

    if country_id:
        query = query.filter(models.Profile.country_id == country_id)

    if age_group:
        query = query.filter(models.Profile.age_group == age_group)

    if min_age is not None:
        query = query.filter(models.Profile.age >= min_age)

    if max_age is not None:
        query = query.filter(models.Profile.age <= max_age)

    if min_gender_probability is not None:
        query = query.filter(models.Profile.gender_probability >= min_gender_probability)

    if min_country_probability is not None:
        query = query.filter(models.Profile.country_probability >= min_country_probability)

    valid_sort = ["age", "created_at", "gender_probability"]

    if sort_by:
        if sort_by not in valid_sort:
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameters"
            )

        column = getattr(models.Profile, sort_by)

        if order == "desc":
            column = column.desc()
        else:
            column = column.asc()

        query = query.order_by(column)
    else:
        query = query.order_by(models.Profile.created_at.desc())

    total = query.count()
    offset = (page - 1) * limit

    data = query.offset(offset).limit(limit).all()

    return {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "data": data
    }



@router.post("", status_code=201)
async def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)):

    name = payload.name.lower().strip()

    existing = db.query(models.Profile).filter(models.Profile.name == name).first()

    if existing:
        return {
            "status": "success",
            "message": "Profile already exists",
            "data": ProfileResponse.model_validate(existing)
        }

    data = await fetch_external_data(name)

    new_profile = models.Profile(
        id=str(uuid7()),
        name=name,
        gender=data["gender"],
        gender_probability=data["gender_probability"],
        age=data["age"],
        age_group=data["age_group"],
        country_id=data["country_id"],
        country_name=data["country_name"],
        country_probability=data["country_probability"],
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return {
        "status": "success",
        "data": ProfileResponse.model_validate(new_profile)
    }


@router.get("/search", response_model=ProfileListResponse)
def search_profiles(
    q: str = Query(...),
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):

    if not q or q.strip() == "":
        raise HTTPException(status_code=400, detail="Invalid query parameters")

    ql = q.lower()

    gender = None
    min_age = None
    max_age = None
    country_id = None
    age_group = None


    if "male" in ql and "female" not in ql:
        gender = "male"
    elif "female" in ql and "male" not in ql:
        gender = "female"


    if "young" in ql:
        min_age, max_age = 16, 24

    if "teenager" in ql or "teen" in ql:
        age_group = "teenager"

    if "adult" in ql:
        age_group = "adult"

    if "senior" in ql:
        age_group = "senior"


    words = ql.split()
    for i, w in enumerate(words):
        if w.isdigit():
            val = int(w)

            if "above" in ql or "over" in ql:
                min_age = val
            elif "below" in ql or "under" in ql:
                max_age = val


    country_map = {
        "nigeria": "NG",
        "kenya": "KE",
        "ghana": "GH",
        "angola": "AO",
        "benin": "BJ"
    }

    for k, v in country_map.items():
        if k in ql:
            country_id = v
            break

    if not any([gender, min_age, max_age, country_id, age_group]):
        return {
            "status": "error",
            "message": "Unable to interpret query"
        }

    query = db.query(models.Profile)

    if gender:
        query = query.filter(models.Profile.gender == gender)

    if country_id:
        query = query.filter(models.Profile.country_id == country_id)

    if age_group:
        query = query.filter(models.Profile.age_group == age_group)

    if min_age is not None:
        query = query.filter(models.Profile.age >= min_age)

    if max_age is not None:
        query = query.filter(models.Profile.age <= max_age)

    total = query.count()
    offset = (page - 1) * limit

    data = query.offset(offset).limit(limit).all()

    return {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "data": data
    }


@router.get("/{id}")
def get_profile(id: str, db: Session = Depends(get_db)):

    profile = db.query(models.Profile).filter(models.Profile.id == id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "status": "success",
        "data": ProfileResponse.model_validate(profile)
    }


@router.delete("/{id}", status_code=204)
def delete_profile(id: str, db: Session = Depends(get_db)):

    profile = db.query(models.Profile).filter(models.Profile.id == id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    db.delete(profile)
    db.commit()
