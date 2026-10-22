from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.recovery import recover_interrupted_jobs
from app.routers import books, bookmarks, generation, voices

settings = get_settings()

Base.metadata.create_all(bind=engine)

# Un-stick voices and chapters that were mid-way through when the app last
# stopped. Must run before requests are served (nothing is in flight yet).
with SessionLocal() as _db:
    _recovered = recover_interrupted_jobs(_db)
if any(_recovered.values()):
    print(f"Recovered interrupted work from last run: {_recovered}", flush=True)

app = FastAPI(title="PersonalVoice Reader API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books.router, tags=["books"])
app.include_router(bookmarks.router, tags=["bookmarks"])
app.include_router(voices.router, tags=["voices"])
app.include_router(generation.router, tags=["generation"])


@app.get("/health")
def health():
    return {"status": "ok"}
