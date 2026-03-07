from typing import Any
import logging
from fastapi import FastAPI, HTTPException
from .database import Database
from .migrations import migrate_database

app = FastAPI()

db = Database(get_db_url(), get_db_type())

@app.on_event("startup")
async def startup_event() -> None:
    if get_db_type() == "postgresql":
        migrate_database()

@app.get("/data")
async def get_data() -> dict[str, Any]:
    try:
        data = await db.fetch_one("SELECT * FROM data LIMIT 1")
        return {"data": data} if data else {"message": "No data found"}
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```