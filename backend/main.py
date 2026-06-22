from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from fastapi.responses import FileResponse, HTMLResponse

from database import engine
from models import Base
from routers import auth, chat, websocket


#mcp related imports:
from mcp.server.fastmcp import FastMCP                                                                                                                                                                                                                                                          
from mcp.server.sse import SseServerTransport                                                                                                                                                                                                                                                   
from routers.websocket import manager                                                                                                                                                                                                                                                           
from sqlalchemy import select                                                                                                                                                                                                                                                                   
from models import User, Message                                                                                                                                                                                                                                                                
from sqlalchemy.ext.asyncio import AsyncSession                                                                                                                                                                                                                                                 
from sqlalchemy.orm import sessionmaker                                                                                                                                                                                                                                                         
from fastapi import Request 


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="E2EE Messenger API", lifespan=lifespan)
mcp = FastMCP("Messenger Tools")                                                                                                                                                                                                                                                                
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)



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
    
    #mcp tools
@mcp.tool()                                                                                                                                                                                                                                                                                     
async def get_active_connections() -> str:                                                                                                                                                                                                                                                      
    """                                                                                                                                                                                                                                                                                         
    Returns a list of usernames currently connected to the real-time websocket server.                                                                                                                                                                                                          
    """                                                                                                                                                                                                                                                                                         
    users = list(manager.active_users.keys())                                                                                                                                                                                                                                                   
    if not users:                                                                                                                                                                                                                                                                               
        return "No users currently connected to the chat websocket."                                                                                                                                                                                                                            
    return f"Active chat connections ({len(users)}): {', '.join(users)}"                                                                                                                                                                                                                        
                                                                                                                                                                                                                                                                                                
@mcp.tool()                                                                                                                                                                                                                                                                                     
async def check_encryption_keys() -> str:                                                                                                                                                                                                                                                       
    """                                                                                                                                                                                                                                                                                         
    Verifies that all registered users have valid ECDH and ECDSA public keys set.                                                                                                                                                                                                               
    """                                                                                                                                                                                                                                                                                         
    try:                                                                                                                                                                                                                                                                                        
        async with AsyncSessionLocal() as session:                                                                                                                                                                                                                                              
            result = await session.execute(select(User))                                                                                                                                                                                                                                        
            users = result.scalars().all()                                                                                                                                                                                                                                                      
                                                                                                                                                                                                                                                                                                
        corrupted_users = []                                                                                                                                                                                                                                                                    
        for user in users:                                                                                                                                                                                                                                                                      
            if not user.ecdh_public_key or not user.ecdsa_public_key:                                                                                                                                                                                                                           
                corrupted_users.append(user.username)                                                                                                                                                                                                                                           
                                                                                                                                                                                                                                                                                                
        if corrupted_users:                                                                                                                                                                                                                                                                     
            return f"🚨 CRITICAL: Users missing encryption/signature keys: {', '.join(corrupted_users)}"                                                                                                                                                                                        
        return f"✅ SUCCESS: All {len(users)} registered users have valid public keys."                                                                                                                                                                                                         
    except Exception as e:                                                                                                                                                                                                                                                                      
        return f"Database Query Error: {str(e)}"                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                                
@mcp.tool()                                                                                                                                                                                                                                                                                     
async def get_message_stats() -> str:                                                                                                                                                                                                                                                           
    """                                                                                                                                                                                                                                                                                         
    Returns the total number of encrypted messages stored in the database.                                                                                                                                                                                                                      
    """                                                                                                                                                                                                                                                                                         
    try:                                                                                                                                                                                                                                                                                        
        async with AsyncSessionLocal() as session:                                                                                                                                                                                                                                              
            result = await session.execute(select(Message))                                                                                                                                                                                                                                     
            msgs = result.scalars().all()                                                                                                                                                                                                                                                       
        return f"Total routed encrypted messages: {len(msgs)}"                                                                                                                                                                                                                                  
    except Exception as e:                                                                                                                                                                                                                                                                      
        return f"Error: {str(e)}" 
    
    
    #mcp sse endpoint
mcp_transport = SseServerTransport("/mcp/messages/")

@app.get("/mcp/sse")
async def handle_mcp_sse(request: Request):
    async with mcp_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as (in_stream, out_stream):
        await mcp._mcp_server.run(
            in_stream,
            out_stream,
            mcp._mcp_server.create_initialization_options()
        )

@app.post("/mcp/messages/")
async def handle_mcp_messages(request: Request):
    return await mcp_transport.handle_post_message(request.scope, request.receive, request._send)
    
        
# Execution entrypoint (Always keep at the absolute bottom!)
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
