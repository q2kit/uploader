from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import PlainTextResponse
from fastapi.templating import Jinja2Templates

from uuid import uuid4
import datetime
import threading
import os


class Cache:
    def __init__(self):
        self.cache = {}

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value, ex: int = None):
        self.cache[key] = value

        if ex:
            if not isinstance(ex, int):
                raise ValueError("ex must be int")
            threading.Timer(ex, self.delete, args=[key]).start()

    def delete(self, key):
        self.cache.pop(key)


app = FastAPI(docs_url=None, redoc_url=None)
cache = Cache()
templates = Jinja2Templates(directory="templates")
if not os.getenv("HOST"):
    SCHEMA = "http"
    os.environ["HOST"] = "localhost"
else:
    SCHEMA = "https"
SECRET_KEY = os.getenv("SECRET_KEY")
HOST = os.getenv("HOST")


def write_logs(request, file, file_name):
    now = datetime.datetime.now()
    LOG_DIR = "logs/"
    log_file = open(LOG_DIR + now.strftime("%Y-%m-%d") + ".txt", "a")
    log_dict = {
        "Time": now.strftime("%H:%M:%S"),
        "ip": request.client.host,
        "file_name": file.filename,
        "new_file_name": file_name
    }
    log_file.write(" - ".join([f"{key}: {val}" for key, val in log_dict.items()]) + "\n")  # noqa
    log_file.close()


@app.get("/")
async def root(request: Request, f: str = ""):
    file_path = f"files/{f}"
    context = {"request": request}
    if f and os.path.exists(file_path):
        context.update({
            "file_download_url": f"{SCHEMA}://{HOST}/f/{f}",
            "file_display_url": f"{SCHEMA}://{HOST}?f={f}"
        })
    try:
        return templates.TemplateResponse("index.html", context)
    except Exception as e:
        return PlainTextResponse(str(e))

@app.get("/health")
async def health():
    return PlainTextResponse("ok")


@app.get("/curl/{path:path}")
async def curl_command_str(path: str):
    return PlainTextResponse(
        f"""curl {SCHEMA}://{HOST} -X POST -F 'file=@"{path}"' """
    )


def checkKey(key):
    if SECRET_KEY and key == SECRET_KEY:
        return True
    return False


@app.post("/get_code/")
async def get_code(key: str = Form("")):
    if checkKey(key):
        code = str(uuid4())
        cache.set(code, "1", ex=60 * 60 * 2)  # 2 hours
        return PlainTextResponse(code)
    else:
        return PlainTextResponse("Invalid Key", status_code=403)


@app.post("/")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    force: bool = Form(False),
    code: str = Form("")
):
    DIR = 'files/'
    if force and cache.get(code):
        cache.delete(code)
        file_name = file.filename
    else:
        ext = file.filename.split(".")[-1] if "." in file.filename else ""
        file_name = str(uuid4())[-8:]
        if ext:
            file_name += f".{ext}"
    write_logs(request, file, file_name)
    with open(DIR + file_name, "wb") as f:
        f.write(file.file.read())
    return PlainTextResponse(f"{SCHEMA}://{HOST}?f={file_name}")


@app.get("/docs")
async def docs(request: Request):
    return templates.TemplateResponse(
        "docs.html",
        {"request": request, "HOST": os.getenv("HOST")}
    )


@app.get("/logs/{date}/{key}")
async def get_logs(date: str, key: str):
    try:
        if not checkKey(key):
            return PlainTextResponse("Server Error", status_code=500)
        LOG_DIR = "logs/"
        txt = open(LOG_DIR + date + ".txt", "r").read()
        return PlainTextResponse(txt)
    except Exception:
        return PlainTextResponse("Nothing")


@app.exception_handler(404)
async def not_found(request, exc):
    return PlainTextResponse("Not Found", status_code=404)
