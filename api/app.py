from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json, os, time

# --- Caminhos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../db/data.json")
TEMPLATES_DIR = os.path.join(BASE_DIR, "../templates")

app = FastAPI()

# --- Configuração de templates e arquivos estáticos ---
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "../static")), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- Inicializa DB se não existir ---
if not os.path.exists(DB_PATH):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w") as f:
        json.dump({"messages": []}, f, indent=2)

def read_db():
    with open(DB_PATH, "r") as f:
        return json.load(f)

def write_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

# --- Rotas ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = read_db()
    return templates.TemplateResponse("index.html", {"request": request, "messages": data["messages"]})

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
    return RedirectResponse(url="/", status_code=303)

@app.get("/api/messages")
async def get_messages():
    data = read_db()
    return JSONResponse(data)
