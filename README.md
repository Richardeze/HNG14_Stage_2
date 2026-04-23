# HNG Stage 2 Backend – Intelligence Query Engine

## Overview
This project is a demographic intelligence API that supports:
- Advanced filtering
- Sorting
- Pagination
- Natural language query parsing

## API Base URL
https://richardeze-hng-stage-2.hf.space/docs

---

## Endpoints

### 1. Get Profiles
GET /api/profiles

Supports:
- gender
- country_id
- age_group
- min_age
- max_age
- sorting (age, created_at, gender_probability)
- order (asc, desc)
- pagination (page, limit)

---

### 2. Search Profiles (Natural Language)
GET /api/profiles/search?q=

Examples:
- "young males from nigeria"
- "females above 30"
- "adult males from kenya"

### Parsing Rules:
- young → age 16–24
- male/female → gender filter
- country names → ISO codes (NG, KE, GH)
- adult/teenager → age_group filter

---

## Limitations
- Rule-based parsing only (no AI/NLP models)
- Limited country mapping
- Cannot handle complex sentences or slang
- Requires strict keyword matching

---

## Tech Stack
- FastAPI
- SQLAlchemy
- SQLite