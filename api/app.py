# api/app.py
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, json, time, tempfile
from threading import Lock

# --- Paths seguros (arquivo está em /api/app.py) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # .../repo/api
ROOT_DIR = os.path.dirname(BASE_DIR)                    # .../repo
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
STATIC_DIR = os.path.join(ROOT_DIR, "static")
DB_DIR = os.path.join(ROOT_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "data.json")

# --- App ---
app = FastAPI(title="Eike Chat - API")

# monta estáticos se existir
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# cria DB se não existir
os.makedirs(DB_DIR, exist_ok=True)
if not os.path.exists(DB_PATH):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump({"messages": []}, f, ensure_ascii=False, indent=2)

# lock na escrita (thread safe dentro da mesma instância)
_WRITE_LOCK = Lock()

# util helpers
def _read_db():
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"messages": []}

def _atomic_write(data):
    # escreve em arquivo temporário e renomeia (mais seguro)
    with _WRITE_LOCK:
        dirn = os.path.dirname(DB_PATH)
        fd, tmp = tempfile.mkstemp(dir=dirn, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, DB_PATH)
        except Exception:
            try:
                os.remove(tmp)
            except Exception:
                pass
            raise

def _next_id(messages):
    mx = 0
    for m in messages:
        try:
            if int(m.get("id", 0)) > mx:
                mx = int(m.get("id", 0))
        except:
            pass
    return mx + 1

# --------------------
# ROTAS HTML / UI
# --------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Renderiza index.html — o frontend carrega mensagens por fetch('/api/messages')
    """
    # Se templates não existirem, retorna erro amigável
    if not os.path.isdir(TEMPLATES_DIR):
        return JSONResponse({
            "error": "templates_not_found",
            "expected": TEMPLATES_DIR
        }, status_code=500)
    return templates.TemplateResponse("index.html", {"request": request})

# --------------------
# API REST (JSON)
# --------------------
@app.get("/api/messages")
async def api_get_messages(limit: int = 100, since: int = 0):
    """
    Retorna mensagens. Query params:
      - limit: número máximo (default 100)
      - since: timestamp unix — retorna mensagens com timestamp > since
    """
    data = _read_db()
    msgs = data.get("messages", [])
    if since:
        msgs = [m for m in msgs if int(m.get("timestamp", 0)) > int(since)]
    # retorna as mais recentes primeiro
    msgs_sorted = sorted(msgs, key=lambda x: x.get("timestamp", 0))
    return JSONResponse({"messages": msgs_sorted[-limit:]})

@app.post("/api/send", status_code=201)
async def api_send_json(payload: dict):
    """
    Recebe JSON { "username": "...", "message": "..." }
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be JSON object")
    text = str(payload.get("message", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail="message is required")
    username = str(payload.get("username") or "Anônimo")
    data = _read_db()
    msgs = data.setdefault("messages", [])
    msg = {
        "id": _next_id(msgs),
        "username": username,
        "message": text,
        "timestamp": int(time.time())
    }
    msgs.append(msg)
    _atomic_write(data)
    return JSONResponse({"ok": True, "message": msg})

@app.post("/send")
async def api_send_form(username: str = Form(None), message: str = Form(...)):
    """
    Endpoint compatível com formulário HTML (utilizado pelo form padrão).
    Redireciona pra "/".
    """
    username = username or "Anônimo"
    text = (message or "").strip()
    if not text:
        return RedirectResponse("/", status_code=303)
    data = _read_db()
    msgs = data.setdefault("messages", [])
    msg = {
        "id": _next_id(msgs),
        "username": username,
        "message": text,
        "timestamp": int(time.time())
    }
    msgs.append(msg)
    _atomic_write(data)
    return RedirectResponse("/", status_code=303)

@app.get("/api/message/{msg_id}")
async def api_get_message(msg_id: int):
    data = _read_db()
    for m in data.get("messages", []):
        if int(m.get("id", 0)) == int(msg_id):
            return JSONResponse(m)
    raise HTTPException(status_code=404, detail="not found")

@app.put("/api/message/{msg_id}")
async def api_edit_message(msg_id: int, payload: dict):
    """
    Edita texto de uma mensagem (payload: { "message": "novo texto" })
    """
    new_text = (payload.get("message") or "").strip()
    if not new_text:
        raise HTTPException(status_code=400, detail="message required")
    data = _read_db()
    changed = False
    for m in data.get("messages", []):
        if int(m.get("id", 0)) == int(msg_id):
            m["message"] = new_text
            m["edited_at"] = int(time.time())
            changed = True
            break
    if not changed:
        raise HTTPException(status_code=404, detail="not found")
    _atomic_write(data)
    return JSONResponse({"ok": True})

@app.delete("/api/message/{msg_id}")
async def api_delete_message(msg_id: int):
    data = _read_db()
    msgs = data.get("messages", [])
    new_msgs = [m for m in msgs if int(m.get("id", 0)) != int(msg_id)]
    if len(new_msgs) == len(msgs):
        raise HTTPException(status_code=404, detail="not found")
    data["messages"] = new_msgs
    _atomic_write(data)
    return JSONResponse({"ok": True})

@app.get("/api/search")
async def api_search(q: str, limit: int = 50):
    """
    Busca por texto simples (case-insensitive) nas mensagens.
    """
    data = _read_db()
    ql = str(q).lower()
    found = [m for m in data.get("messages", []) if ql in (m.get("message","").lower() + m.get("username","").lower())]
    found_sorted = sorted(found, key=lambda x: x.get("timestamp", 0))
    return JSONResponse({"messages": found_sorted[-limit:]})
