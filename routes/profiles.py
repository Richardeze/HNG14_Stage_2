from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import ProfileCreate, ProfileResponse, ProfileListResponse
from services.external_apis import fetch_external_data
from uuid6 import uuid7

router = APIRouter(
    prefix="/api/profiles",
    tags=["Profiles"]
)

@router.get("", response_model=ProfileListResponse)
@router.get("", response_model=ProfileListResponse)
def get_profiles(
    gender: str = None,
    country_id: str = None,
    age_group: str = None,
    min_age: int = None,
    max_age: int = None,
    min_gender_probability: float = None,
    min_country_probability: float = None,
    sort_by: str = None,
    order: str = "asc",
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):


    if limit > 50:
        limit = 50

    query = db.query(models.Profile)


    if gender:
        query = query.filter(models.Profile.gender == gender)

    if country_id:
        query = query.filter(models.Profile.country_id == country_id)

    if age_group:
        query = query.filter(models.Profile.age_group == age_group)

    if min_age:
        query = query.filter(models.Profile.age >= min_age)

    if max_age:
        query = query.filter(models.Profile.age <= max_age)

    if min_gender_probability:
        query = query.filter(models.Profile.gender_probability >= min_gender_probability)

    if min_country_probability:
        query = query.filter(models.Profile.country_probability >= min_country_probability)


    if not sort_by:
        query = query.order_by(models.Profile.created_at.desc())


    valid_sort = ["age", "created_at", "gender_probability"]

    if sort_by:
        if sort_by not in valid_sort:
            return {
                "status": "error",
                "message": "Invalid query parameters"
            }

        column = getattr(models.Profile, sort_by)

        if order == "desc":
            column = column.desc()
        else:
            column = column.asc()

        query = query.order_by(column)


    total = query.count()
    offset = (page - 1) * limit
    profiles = query.offset(offset).limit(limit).all()

    return {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "data": profiles
    }


@router.get("/search", response_model=ProfileListResponse)
def search_profiles(
    q: str,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):

    if limit > 50:
        limit = 50

    q_lower = q.lower()

    gender = None
    min_age = None
    max_age = None
    country_id = None
    age_group = None


    if "male" in q_lower and "female" not in q_lower:
        gender = "male"
    elif "female" in q_lower and "male" not in q_lower:
        gender = "female"


    if "young" in q_lower:
        min_age, max_age = 16, 24

    if "teen" in q_lower:
        age_group = "teenager"

    if "adult" in q_lower:
        age_group = "adult"


    words = q_lower.split()
    for i, word in enumerate(words):
        if word.isdigit():
            val = int(word)

            if "above" in q_lower or "over" in q_lower:
                min_age = val
            elif "below" in q_lower or "under" in q_lower:
                max_age = val


    if "nigeria" in q_lower:
        country_id = "NG"
    elif "kenya" in q_lower:
        country_id = "KE"
    elif "ghana" in q_lower:
        country_id = "GH"
    elif "angola" in q_lower:
        country_id = "AO"


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

    if min_age:
        query = query.filter(models.Profile.age >= min_age)

    if max_age:
        query = query.filter(models.Profile.age <= max_age)

    total = query.count()
    offset = (page - 1) * limit
    profiles = query.offset(offset).limit(limit).all()

    return {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "data": profiles
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


@router.post("", status_code=201)
async def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)):

    name = payload.name.lower().strip()

    if not name:
        raise HTTPException(status_code=400, detail="Missing or empty name")

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


@router.delete("/{id}", status_code=204)
def delete_profile(id: str, db: Session = Depends(get_db)):

    profile = db.query(models.Profile).filter(models.Profile.id == id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    db.delete(profile)
    db.commit()

    return
