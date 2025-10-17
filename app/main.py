from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.database.db import init_db

app = FastAPI(
    title="AI Customer Support Bot API",
    description="Backend API for AI customer support including FAQ handling, session tracking, and escalation simulation",
    version="1.0.0"
)

# Allow CORS for frontend connection
origins = [
    "https://portfolio-backend-uroc.onrender.com",  
    "http://127.0.0.1:3000",
    "https://www.himanshuchitoria.me/"
    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    # Initialize database connection
    await init_db()

# Register API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Customer Support Bot API"}

