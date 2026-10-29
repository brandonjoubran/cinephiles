import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.users import router as users_router
from api.stats import router as stats_router
from api.movies import router as movies_router
from api.meetings import router as meetings_router
from api.cache import router as cache_router
from api.nominators import router as nominators_router
from api.pages import router as pages_router

app = FastAPI(title="OnlyCinephiles API")

_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:5174,http://127.0.0.1:5174",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(stats_router)
app.include_router(movies_router)
app.include_router(meetings_router)
app.include_router(nominators_router)
app.include_router(cache_router)
app.include_router(pages_router)


@app.get("/")
def root():
    return {"message": "OnlyCinephiles API", "docs": "/docs"}
