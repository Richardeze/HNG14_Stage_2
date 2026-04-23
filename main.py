from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
import os
from routes.profiles import router as profiles_router


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(profiles_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root
@app.get("/")
def root():
    return {
        "status": "success",
        "message": "HNG Stage 1 API is running"
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Invalid input"
        }
    )

port = int(os.environ.get("PORT", 7860))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port)
