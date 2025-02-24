import uvicorn
from fastapi import FastAPI
from app.config.database import init_db
from app.routes.user_routes import router as user_router

app = FastAPI(title="WAHIRE API", version="0.1")

@app.on_event("startup")
async def start_db():
    await init_db()

@app.get("/")
async def root():
    return {"message": "Welcome to the WAHIRE API"}

app.include_router(user_router, prefix="/users", tags=["Users"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
