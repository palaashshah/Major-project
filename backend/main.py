from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

import models  # registers every table with Base
from database import Base, engine
from routers import investors
from routers import interactions
from routers import risk
from routers import optimize

# Create any tables that do not exist yet (existing tables are left alone).
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(investors.router)
app.include_router(interactions.router)
app.include_router(risk.router)
app.include_router(optimize.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "OpenGlass Portfolio API is running"}