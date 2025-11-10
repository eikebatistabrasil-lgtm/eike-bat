from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json, os, asyncio

app = FastAPI()

# Libera acesso pro front (Tumblr, Blogger etc)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "db/data.json"
LOCK = asyncio.Lock()
connections = set()

def read_db():
    if not os.path.exists(DB_PATH):
        os.makedirs("db", exist_ok=True)
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump({"messages": []}, f)
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

async def write_db(data):
    async with LOCK:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

@app.get("/")
def home():
    return {"status": "✅ API FastAPI ativa no Vercel", "messages": len(read_db()["messages"])}

@app.get("/api/messages")
def get_messages():
    return JSONResponse(read_db())

@app.post("/api/send/{user}/{text}")
async def send_message(user: str, text: str):
    db = read_db()
    db["messages"].append({"user": user, "text": text})
    await write_db(db)
    return {"ok": True, "messages": db["messages"]}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.add(ws)
    await ws.send_json({"system": "🔗 Conectado com sucesso"})

    try:
        while True:
            msg = await ws.receive_json()
            db = read_db()
            db["messages"].append(msg)
            await write_db(db)

            for c in connections:
                await c.send_json(msg)
    except WebSocketDisconnect:
        connections.remove(ws)
