from fastapi import FastAPI
from routes.admin_routes import router as admin_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
from database import db

app.include_router(admin_router, prefix="/admin", tags=["Admin"])



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ANY frontend can connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/test-db")
async def test_db():
    try:
        collections = await db.list_collection_names()
        return {"status": "connected", "collections": collections}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

@app.get("/")
def root():
    return {"status": "Admin Backend Running"}
