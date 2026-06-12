from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from fastapi.responses import FileResponse, HTMLResponse

from database import engine
from models import Base
from routers import auth, chat, websocket

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="E2EE Messenger API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Plug in the sub-departments!
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(websocket.router)

# Route to serve the frontend homepage
@app.get("/")
async def read_index():
    # Attempt to locate index.html relative to main.py
    # Adjust "index.html" or "../frontend/index.html" depending on your repository folder structure
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
        
    # Check parent directory or alternative frontend path
    parent_html_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    if os.path.exists(parent_html_path):
        return FileResponse(parent_html_path)
        
    # If the file is placed inside a "frontend" folder:
    frontend_html_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(frontend_html_path):
        return FileResponse(frontend_html_path)

    # Friendly error fallback if paths are misaligned
    return HTMLResponse(
        content="<h2>index.html was not found in the container paths. Please check your folder layout!</h2>", 
        status_code=404
    )

# Execution entrypoint (Always keep at the absolute bottom!)
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
