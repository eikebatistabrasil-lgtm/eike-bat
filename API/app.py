from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json, os, time

# Caminhos absolutos seguros pro Vercel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)  # sobe um nível

DB_PATH = os.path.join(ROOT_DIR, "db", "data.json")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
STATIC_DIR = os.path.join(ROOT_DIR, "static")

app = FastAPI()

# Monta arquivos estáticos e templates
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Garante que o DB existe
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
if not os.path.exists(DB_PATH):
    with open(DB_PATH, "w") as f:
        json.dump({"messages": []}, f)

def read_db():
    with open(DB_PATH, "r") as f:
        return json.load(f)

def write_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

# Página inicial
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    data = read_db()
    return templates.TemplateResponse("index.html", {"request": request, "messages": data["messages"]})

# Enviar nova mensagem
@app.post("/send")
async def send_message(username: str = Form(...), message: str = Form(...)):
    data = read_db()
    msg = {
        "username": username or "Anônimo",
        "message": message,
        "timestamp": int(time.time())
    }
    data["messages"].append(msg)
    write_db(data)
    return RedirectResponse("/", status_code=303)

# API JSON simples
@app.get("/api/messages")
async def get_messages():
    return JSONResponse(read_db())
