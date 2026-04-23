import httpx
from fastapi import HTTPException
from utils.classification import get_age_group


GENDERIZE_URL = "https://api.genderize.io"
AGIFY_URL = "https://api.agify.io"
NATIONALIZE_URL = "https://api.nationalize.io"


async def fetch_external_data(name: str):
    async with httpx.AsyncClient() as client:
        try:
            gender_res = await client.get(GENDERIZE_URL, params={"name": name})
            age_res = await client.get(AGIFY_URL, params={"name": name})
            nation_res = await client.get(NATIONALIZE_URL, params={"name": name})
        except Exception:
            raise HTTPException(status_code=502, detail="External API request failed")


        gender_data = gender_res.json()
        age_data = age_res.json()
        nation_data = nation_res.json()

        if gender_data.get("gender") is None or gender_data.get("count") == 0:
            raise HTTPException(
                status_code=502,
                detail="Genderize returned an invalid response"
            )

        # Agify
        if age_data.get("age") is None:
            raise HTTPException(
                status_code=502,
                detail="Agify returned an invalid response"
            )

        # Nationalize
        countries = nation_data.get("country")
        if not countries:
            raise HTTPException(
                status_code=502,
                detail="Nationalize returned an invalid response"
            )

        top_country = max(countries, key=lambda x: x["probability"])

        return {
            "gender": gender_data["gender"],
            "gender_probability": gender_data["probability"],
            "sample_size": gender_data["count"],
            "age": age_data["age"],
            "age_group": get_age_group(age_data["age"]),
            "country_id": top_country["country_id"],
            "country_name": top_country["country_id"],
            "country_probability": top_country["probability"]
        }
