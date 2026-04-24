from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
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
    if limit < 1:
        limit = 1
    if page < 1:
        page = 1

    query = db.query(models.Profile)

    if gender:
        query = query.filter(models.Profile.gender == gender.lower())

    if country_id:
        query = query.filter(models.Profile.country_id == country_id.upper())

    if age_group:
        query = query.filter(models.Profile.age_group == age_group.lower())

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
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Invalid query parameters"}
            )

        column = getattr(models.Profile, sort_by)
        column = column.desc() if order == "desc" else column.asc()
        query = query.order_by(column)
    else:
        query = query.order_by(models.Profile.created_at.desc())

    total = query.count()
    total_pages = (total + limit - 1) // limit  # ceiling division
    offset = (page - 1) * limit
    data = query.offset(offset).limit(limit).all()

    return {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
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


@router.get("/search")
def search_profiles(
    q: str = Query(...),
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):

    if not q or not q.strip():
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid query parameters"}
        )

    if limit > 50:
        limit = 50
    if limit < 1:
        limit = 1
    if page < 1:
        page = 1

    ql = q.lower().strip()

    gender = None
    min_age = None
    max_age = None
    country_id = None
    age_group = None

    has_male = "male" in ql
    has_female = "female" in ql

    if has_male and not has_female:
        gender = "male"
    elif has_female and not has_male:
        gender = "female"
    elif has_female and has_male:
        gender = None

    if "teenager" in ql or "teen" in ql:
        age_group = "teenager"
    elif "child" in ql or "children" in ql:
        age_group = "child"
    elif "senior" in ql or "elderly" in ql or "old" in ql:
        age_group = "senior"
    elif "adult" in ql:
        age_group = "adult"

    if "young" in ql:
        min_age = 16
        max_age = 24

    words = ql.split()
    for i, w in enumerate(words):
        if w.isdigit():
            val = int(w)
            prev_word = words[i - 1] if i > 0 else ""
            if prev_word in ("above", "over", "older", "than"):
                min_age = val
            elif prev_word in ("below", "under", "younger"):
                max_age = val
            else:
                before = " ".join(words[:i])
                if any(kw in before for kw in ("above", "over")):
                    min_age = val
                elif any(kw in before for kw in ("below", "under")):
                    max_age = val


    country_map = {
        "nigeria": "NG",
        "kenya": "KE",
        "ghana": "GH",
        "angola": "AO",
        "benin": "BJ",
        "cameroon": "CM",
        "ethiopia": "ET",
        "south africa": "ZA",
        "tanzania": "TZ",
        "uganda": "UG",
        "senegal": "SN",
        "ivory coast": "CI",
        "côte d'ivoire": "CI",
        "rwanda": "RW",
        "mozambique": "MZ",
        "zambia": "ZM",
        "zimbabwe": "ZW",
        "mali": "ML",
        "niger": "NE",
        "burkina faso": "BF",
        "togo": "TG",
        "sierra leone": "SL",
        "liberia": "LR",
        "guinea": "GN",
    }

    for country_name, code in country_map.items():
        if country_name in ql:
            country_id = code
            break


    if not any([gender, min_age, max_age, country_id, age_group]):
        return JSONResponse(
            status_code=200,  # spec shows this as a 200 with error status
            content={"status": "error", "message": "Unable to interpret query"}
        )

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
    total_pages = (total + limit - 1) // limit
    offset = (page - 1) * limit
    data = query.offset(offset).limit(limit).all()

    return {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "data": [ProfileResponse.model_validate(p) for p in data]
    }


@router.get("/{id}")
def get_profile(id: str, db: Session = Depends(get_db)):
    profile = db.query(models.Profile).filter(models.Profile.id == id).first()

    if not profile:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "Profile not found"}
        )

    return {
        "status": "success",
        "data": ProfileResponse.model_validate(profile)
    }


@router.delete("/{id}", status_code=204)
def delete_profile(id: str, db: Session = Depends(get_db)):
    profile = db.query(models.Profile).filter(models.Profile.id == id).first()

    if not profile:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "Profile not found"}
        )

    db.delete(profile)
    db.commit()
