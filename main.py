import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from database import db, create_document, get_documents

app = FastAPI(title="Rugby Polos API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SubscribeRequest(BaseModel):
    email: EmailStr


@app.get("/")
def read_root():
    return {"message": "Rugby Polos Backend Running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


# -------- Products --------

def _default_products() -> List[dict]:
    return [
        {
            "title": "Heritage Hoops Polo",
            "description": "Thick navy/cream hoops with vintage collar and embroidered crest.",
            "price": 89.0,
            "category": "retro",
            "in_stock": True,
            "images": [
                "https://images.unsplash.com/photo-1520975916090-3105956dac38?q=80&w=1200&auto=format&fit=crop"
            ],
            "colors": ["Navy/Cream"],
            "sizes": ["S", "M", "L", "XL"]
        },
        {
            "title": "Classic Touchline Polo",
            "description": "Solid forest green with contrast white collar, heavyweight jersey.",
            "price": 79.0,
            "category": "vintage",
            "in_stock": True,
            "images": [
                "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?q=80&w=1200&auto=format&fit=crop"
            ],
            "colors": ["Forest/White"],
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"]
        },
        {
            "title": "Retro Club Stripe",
            "description": "Bold burgundy/gold bars inspired by 90s club kits.",
            "price": 85.0,
            "category": "retro",
            "in_stock": True,
            "images": [
                "https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?q=80&w=1200&auto=format&fit=crop"
            ],
            "colors": ["Burgundy/Gold"],
            "sizes": ["S", "M", "L", "XL"]
        },
        {
            "title": "Custom Matchday Polo",
            "description": "Your colors, your crest. Built to order with premium fabric.",
            "price": 99.0,
            "category": "custom",
            "in_stock": True,
            "images": [
                "https://images.unsplash.com/photo-1509631179647-0177331693ae?q=80&w=1200&auto=format&fit=crop"
            ],
            "colors": ["Custom"],
            "sizes": ["S", "M", "L", "XL", "XXL"]
        }
    ]


@app.get("/api/products")
async def list_products(limit: Optional[int] = None):
    try:
        products = get_documents("product", {}, limit)
        if products is None:
            products = []
        # Seed with defaults if collection is empty
        if len(products) == 0:
            for p in _default_products():
                try:
                    create_document("product", p)
                except Exception:
                    pass
            products = get_documents("product", {}, limit)
        # Convert ObjectId to str if present
        for p in products:
            if "_id" in p:
                p["id"] = str(p["_id"])  # expose as id
                del p["_id"]
        return {"items": products}
    except Exception as e:
        # If database not available, fall back to static defaults
        return {"items": _default_products()}


# -------- Newsletter --------

@app.post("/api/subscribe")
async def subscribe(body: SubscribeRequest):
    try:
        doc_id = create_document("subscriber", {"email": body.email})
        return {"status": "ok", "id": doc_id}
    except Exception as e:
        # even if DB down, respond gracefully
        raise HTTPException(status_code=400, detail=str(e)[:200])


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
