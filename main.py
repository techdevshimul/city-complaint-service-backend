from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from router.auth import router as auth_router
from router.complaints import router as complaints_router
from router.admin import router as admin_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title='CityCare Complaint API', version='1.0.0')

origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://city-complaint-service-frontend.netlify.app",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(complaints_router)
app.include_router(admin_router)


@app.get('/')
def health_check():
    return {'message': 'CityCare API is running'}
