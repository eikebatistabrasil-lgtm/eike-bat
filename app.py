import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()

# Lista de conexões WebSocket ativas
active_connections = []


@app.get("/")
async def root():
    return {"status": "✅ Backend Python ativo no Render"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        await websocket.send_text("🔗 Conectado ao backend Python (Render)")

        while True:
            data = await websocket.receive_text()
            msg = f"💬 {data}"
            # Envia para todos os clientes conectados (broadcast)
            for conn in active_connections:
                await conn.send_text(msg)

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("🔴 Cliente desconectado")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
