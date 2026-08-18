import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../.."))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
ROUTERS_DIR = os.path.join(BASE_DIR, "routers")

for path in [PROJECT_ROOT, BACKEND_DIR, BASE_DIR, ROUTERS_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from fastapi import FastAPI  # type: ignore[import-not-found] # pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-not-found] # pyrefly: ignore [missing-import]


try:
    from backend.api.routers import cloud_visibility_router
except ImportError:
    try:
        from api.routers import cloud_visibility_router
    except ImportError:
        import cloud_visibility_router  # type: ignore[import-not-found]


app = FastAPI(
    title="Aviation Weather Forecast Verification API",
    description="Hyper-Local Aviation Weather Forecast & Verification API for Sri Lankan Monsoon Patterns",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cloud_visibility_router.router)

@app.get("/")
def root():
    return {"message": "Aviation Weather Forecast Verification System API is active."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="127.0.0.1", port=8000, reload=True)
