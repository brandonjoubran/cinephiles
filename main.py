from fastapi import FastAPI
from api.users import router as users_router
from api.stats import router as stats_router

app = FastAPI()
app.include_router(users_router)
app.include_router(stats_router)

@app.get("/")
async def root():
    return {"message": "OnlyCinephiles API V2"}