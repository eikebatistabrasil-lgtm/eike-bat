from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from supabase import create_client
import os, time

# -----------------------------------------------------
#  Configuração do Supabase
# -----------------------------------------------------
SUPABASE_URL = "https://bceykkqbdsdrclmeybxx.supabase.co"  # substitua aqui
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJjZXlra3FiZHNkcmNsbWV5Ynh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI3ODYxODEsImV4cCI6MjA3ODM2MjE4MX0.mZ5j9DRHANmX2w2avkMGydbj4a8GibSaozsegm24dR8"                # substitua aqui
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------------------------------
#  App FastAPI e diretórios
# -----------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
STATIC_DIR = os.path.join(ROOT_DIR, "static")

app = FastAPI(title="Eike Chat - Supabase Edition")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# -----------------------------------------------------
#  Rotas HTML
# -----------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# -----------------------------------------------------
#  Funções auxiliares
# -----------------------------------------------------
def get_messages(limit: int = 100):
    result = supabase.table("messages").select("*").order("created_at", desc=False).limit(limit).execute()
    return result.data or []

def insert_message(username: str, message: str):
    data = {
        "username": username,
        "message": message,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    supabase.table("messages").insert(data).execute()
    return data

# -----------------------------------------------------
#  Rotas da API
# -----------------------------------------------------
@app.get("/api/messages")
async def api_get_messages(limit: int = 100):
    msgs = get_messages(limit)
    return JSONResponse({"messages": msgs})

@app.post("/api/send", status_code=201)
async def api_send_json(payload: dict):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be JSON object")
    text = str(payload.get("message", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail="message is required")
    username = str(payload.get("username") or "Anônimo")
    msg = insert_message(username, text)
    return JSONResponse({"ok": True, "message": msg})

@app.post("/send")
async def api_send_form(username: str = Form(None), message: str = Form(...)):
    username = username or "Anônimo"
    text = (message or "").strip()
    if not text:
        return RedirectResponse("/", status_code=303)
    insert_message(username, text)
    return RedirectResponse("/", status_code=303)
