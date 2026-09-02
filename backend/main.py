from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from routers import investors
from routers import interactions


app = FastAPI()

app.include_router(investors.router)
app.include_router(interactions.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "OpenGlass Portfolio API is running"}