# api/app.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json, os, time

# Caminhos: api/ -> sobe um nível para achar /templates e /db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))       # .../repo/api
ROOT_DIR = os.path.dirname(BASE_DIR)                        # .../repo

TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
DB_DIR = os.path.join(ROOT_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "data.json")
STATIC_DIR = os.path.join(ROOT_DIR, "static")

app = FastAPI()

# monta estáticos somente se existir a pasta
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# inicializa templates — se o diretório não existir, levantamos um erro claro
if not os.path.isdir(TEMPLATES_DIR):
    # expõe informação útil no root JSON para debug no Vercel (evita 500)
    @app.get("/", response_class=JSONResponse)
    async def missing_templates():
        return JSONResponse({
            "error": "templates_not_found",
            "expected_templates_dir": TEMPLATES_DIR,
            "hint": "Crie a pasta 'templates' na raiz do repositório e adicione index.html"
        }, status_code=500)
else:
    templates = Jinja2Templates(directory=TEMPLATES_DIR)

# garante DB
os.makedirs(DB_DIR, exist_ok=True)
if not os.path.exists(DB_PATH):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump({"messages": []}, f, indent=2, ensure_ascii=False)

def read_db():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def write_db(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Se templates existem, serve index; se não, a rota "/" já foi definida acima para debug
if os.path.isdir(TEMPLATES_DIR):
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        data = read_db()
        # passa mensagens para o template (padrão: index.html)
        return templates.TemplateResponse("index.html", {"request": request, "messages": data.get("messages", [])})

# rota para ver JSON das mensagens
@app.get("/api/messages")
async def get_messages():
    return JSONResponse(read_db())

# rota de envio via form (submissão simples)
@app.post("/send")
async def send_message(username: str = Form(None), message: str = Form(...)):
    data = read_db()
    msg = {
        "username": username or "Anônimo",
        "message": message,
        "timestamp": int(time.time())
    }
    data.setdefault("messages", []).append(msg)
    write_db(data)
    # redireciona para a raiz para exibir a lista atualizada
    return RedirectResponse("/", status_code=303)
