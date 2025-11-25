from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middlewares.auth_middleware import authentication
from app import models
from app.integrations.redis import init_redis
from app.integrations.alchemy import SessionLocal, engine
from app.routers import accounts, user, tts, subscription, storage
from app.config import APP_ENV

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Define allowed origins for production
origins = [
    "https://spellcast.nhexa.cl",
]

# Check if in development environment
if APP_ENV == "development":
    # Specific origin for development to allow credentials
    origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Origin", "X-Requested-With",
                    "Content-Type", "Accept", "Authorization"]
)

# Middleware
app.middleware("http")(authentication)

# Data base connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to SpellCast API"}

#Starting Redis Client
@app.on_event('startup')
async def startup_event():
    init_redis()

# Routers
app.include_router(tts.router)
app.include_router(user.router)
app.include_router(storage.router)
app.include_router(accounts.router)
app.include_router(subscription.router)