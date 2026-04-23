Stage 2 Backend Assessment – Intelligence Query Engine
Overview

This API provides advanced filtering, sorting, pagination, and natural language search over demographic profiles stored in a SQLite database.

Features
1. Filtering System

Supports:

gender
country_id
age_group
min_age / max_age
gender_probability
country_probability

All filters can be combined in a single request.

2. Sorting

Supported fields:

age
created_at
gender_probability

Order:

asc
desc
3. Pagination

Implemented using:

page (default: 1)
limit (default: 10)

Response includes:

total records
current page
limit 
4. Natural Language Search

Endpoint:

GET /api/profiles/search?q=

Approach

A rule-based parser converts natural language into structured filters.

Examples:
"young males" → gender=male, age 16–24
"females above 30" → gender=female, min_age=30
"people from nigeria" → country_id=NG
Limitations
No ML/AI model used
Only keyword-based parsing
Cannot interpret complex sentences
Limited country mapping
Does not support slang or misspellings
Deployment

Deployed using:
Base URL: 

Testing

All endpoints tested via:

Swagger UI

Tech Stack
FastAPI
SQLAlchemy
SQLite
Python 3.12