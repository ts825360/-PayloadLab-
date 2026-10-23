from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.labs import router as labs_router

app = FastAPI(title="PayloadLab API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(labs_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
