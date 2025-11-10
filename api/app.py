from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, json, asyncio, time
from collections import deque
import uvicorn

# Cria o app FastAPI
app = FastAPI()

# Configura templates e arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Lista de conexões WebSocket e histórico
connections = set()
connections_lock = asyncio.Lock()
history = deque(maxlen=100)

# Rota principal
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Endpoint WebSocket
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    async with connections_lock:
        connections.add(websocket)

    # Envia histórico ao novo cliente
    await websocket.send_text(json.dumps({
        "type": "history",
        "messages": list(history)
    }))

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue

            if payload.get("type") == "message":
                msg = {
                    "type": "message",
                    "username": payload.get("username") or "Anônimo",
                    "message": payload.get("message"),
                    "timestamp": int(time.time())
                }
                history.append(msg)
                await broadcast(msg)

    except WebSocketDisconnect:
        async with connections_lock:
            connections.remove(websocket)


# Função de broadcast (envia pra todos)
async def broadcast(message: dict):
    text = json.dumps(message)
    async with connections_lock:
        to_remove = []
        for ws in list(connections):
            try:
                await ws.send_text(text)
            except:
                to_remove.append(ws)
        for ws in to_remove:
            connections.remove(ws)


# Inicialização (Render usa variável PORT)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
