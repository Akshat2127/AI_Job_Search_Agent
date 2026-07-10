from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from backend.app.core.config import settings
from backend.app.db.session import Base, engine
from backend.app.models.job import Job  # noqa: F401
from backend.app.api.jobs import router as jobs_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.export import router as export_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")

@app.get("/", include_in_schema=False)
def dashboard_redirect():
    return RedirectResponse(url="/static/dashboard.html")

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "version": settings.app_version}

app.include_router(jobs_router)
app.include_router(analytics_router)
app.include_router(export_router)
