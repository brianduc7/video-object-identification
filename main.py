from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routes import router
from db.database import init_db

app = FastAPI(title="Video Object Identification")

init_db()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)
