from fastapi import FastAPI
from api.users import router as users_router
from api.stats import router as stats_router
from api.cache import router as cache_router

app = FastAPI()
app.include_router(users_router)
app.include_router(stats_router)
app.include_router(cache_router)

@app.get("/")
async def root():
    return {"message": "OnlyCinephiles API V2"}