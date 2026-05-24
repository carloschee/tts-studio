#!/usr/bin/env python3
"""
TTS Studio — server.py v2
Cola de generación, lotes, preview temporal, renombrado de archivos.

Instalación:
  pip install fastapi uvicorn edge-tts python-multipart

Uso:
  python server.py  →  http://localhost:8765
"""

import asyncio
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

# ─── Dependencias ─────────────────────────────────────────────────────────────
def _check_deps():
    missing = []
    for pkg in ["fastapi", "uvicorn", "edge_tts"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg.replace("_", "-"))
    if missing:
        print(f"\n❌  Faltan: {', '.join(missing)}")
        print(f"   pip install {' '.join(missing)} python-multipart\n")
        sys.exit(1)

_check_deps()

import edge_tts
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

# ─── Setup ────────────────────────────────────────────────────────────────────
app = FastAPI(title="TTS Studio")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

OUTPUT_DIR  = Path(__file__).parent / "output"
PREVIEW_DIR = Path(__file__).parent / "preview"
INDEX_HTML  = Path(__file__).parent / "index.html"
OUTPUT_DIR.mkdir(exist_ok=True)
PREVIEW_DIR.mkdir(exist_ok=True)

# ─── Voces ────────────────────────────────────────────────────────────────────
VOCES = {
    "es-MX-DaliaNeural":  { "label": "Dalia — México (ES)",       "lang": "es-MX" },
    "es-MX-JorgeNeural":  { "label": "Jorge — México (ES, masc)", "lang": "es-MX" },
    "es-ES-ElviraNeural": { "label": "Elvira — España (ES)",      "lang": "es-ES" },
    "en-US-AriaNeural":   { "label": "Aria — USA (EN)",           "lang": "en-US" },
    "en-US-JennyNeural":  { "label": "Jenny — USA (EN)",          "lang": "en-US" },
    "en-US-GuyNeural":    { "label": "Guy — USA (EN, masc)",      "lang": "en-US" },
}

# ─── Cola de generación ───────────────────────────────────────────────────────
_cola: asyncio.Queue = None
_trabajos: dict      = {}   # job_id → estado

@app.on_event("startup")
async def _startup():
    global _cola
    _cola = asyncio.Queue()
    asyncio.create_task(_worker())

async def _worker():
    """Worker único que procesa la cola secuencialmente."""
    while True:
        job = await _cola.get()
        jid = job["id"]
        _trabajos[jid]["estado"] = "procesando"
        try:
            await _sintetizar(
                texto   = job["texto"],
                voz     = job["voz"],
                rate    = job["rate"],
                pitch   = job["pitch"],
                volume  = job["volume"],
                destino = job["destino"],
            )
            _trabajos[jid]["estado"]  = "listo"
            _trabajos[jid]["nombre"]  = job["destino"].name
            _trabajos[jid]["tamaño"]  = job["destino"].stat().st_size
        except Exception as e:
            _trabajos[jid]["estado"] = "error"
            _trabajos[jid]["error"]  = str(e)
            if job["destino"].exists():
                job["destino"].unlink()
        finally:
            _cola.task_done()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def _norm(val: str, suffix: str) -> str:
    val = str(val).strip().replace(" ", "")
    if not val.endswith(suffix):
        val += suffix
    if not val.startswith(("+", "-")):
        val = "+" + val
    return val

def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", texto[:30].lower().strip()).strip("-")

def _nombre_archivo(texto: str, nombre_custom: str) -> str:
    if nombre_custom.strip():
        nombre = re.sub(r"[^\w\-.]", "_", nombre_custom.strip())
    else:
        ts     = datetime.now().strftime("%Y%m%d-%H%M%S")
        nombre = f"{ts}-{_slug(texto)}"
    return nombre if nombre.endswith(".mp3") else nombre + ".mp3"

async def _sintetizar(texto: str, voz: str, rate: str, pitch: str, volume: str, destino: Path):
    communicate = edge_tts.Communicate(texto, voice=voz, rate=rate, pitch=pitch, volume=volume)
    await communicate.save(str(destino))

# ─── Modelos ──────────────────────────────────────────────────────────────────
class GenerarRequest(BaseModel):
    texto:  str
    voz:    str = "es-MX-DaliaNeural"
    rate:   str = "+0%"
    pitch:  str = "+0Hz"
    volume: str = "+0%"
    nombre: str = ""

class LoteItem(BaseModel):
    texto:  str
    nombre: str = ""

class LoteRequest(BaseModel):
    items:  List[LoteItem]
    voz:    str = "es-MX-DaliaNeural"
    rate:   str = "+0%"
    pitch:  str = "+0Hz"
    volume: str = "+0%"

class PreviewRequest(BaseModel):
    texto:  str
    voz:    str = "es-MX-DaliaNeural"
    rate:   str = "+0%"
    pitch:  str = "+0Hz"
    volume: str = "+0%"

class RenombrarRequest(BaseModel):
    nuevo: str

# ─── Rutas ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    if INDEX_HTML.exists():
        return HTMLResponse(INDEX_HTML.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>index.html no encontrado</h1>")

@app.get("/voces")
async def get_voces():
    return JSONResponse(VOCES)

# ── Biblioteca ────────────────────────────────────────────────────────────────

@app.get("/archivos")
async def listar_archivos():
    archivos = []
    for f in sorted(OUTPUT_DIR.glob("*.mp3"), key=lambda x: x.stat().st_mtime, reverse=True):
        archivos.append({
            "nombre": f.name,
            "tamaño": f.stat().st_size,
            "fecha":  datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            "ruta":   str(f.resolve()),
        })
    return JSONResponse(archivos)

@app.get("/audio/{nombre}")
async def servir_audio(nombre: str):
    ruta = OUTPUT_DIR / nombre
    if not ruta.exists():
        raise HTTPException(404, "No encontrado")
    return FileResponse(str(ruta), media_type="audio/mpeg")

@app.delete("/audio/{nombre}")
async def eliminar_audio(nombre: str):
    ruta = OUTPUT_DIR / nombre
    if ruta.exists():
        ruta.unlink()
    return {"ok": True}

@app.put("/audio/{nombre}/renombrar")
async def renombrar_audio(nombre: str, req: RenombrarRequest):
    origen  = OUTPUT_DIR / nombre
    if not origen.exists():
        raise HTTPException(404, "No encontrado")
    nuevo = req.nuevo.strip()
    if not nuevo:
        raise HTTPException(400, "Nombre vacío")
    nuevo = re.sub(r"[^\w\-.]", "_", nuevo)
    if not nuevo.endswith(".mp3"):
        nuevo += ".mp3"
    destino = OUTPUT_DIR / nuevo
    if destino.exists():
        raise HTTPException(409, f"Ya existe {nuevo}")
    origen.rename(destino)
    return {"ok": True, "nombre": nuevo}

# ── Generación individual (con cola) ──────────────────────────────────────────

@app.post("/generar")
async def generar(req: GenerarRequest):
    if not req.texto.strip():
        raise HTTPException(400, "Texto vacío")
    if req.voz not in VOCES:
        raise HTTPException(400, "Voz no disponible")

    jid     = str(uuid.uuid4())
    nombre  = _nombre_archivo(req.texto, req.nombre)
    destino = OUTPUT_DIR / nombre

    _trabajos[jid] = {"estado": "en_cola", "nombre": nombre}

    await _cola.put({
        "id":      jid,
        "texto":   req.texto.strip(),
        "voz":     req.voz,
        "rate":    _norm(req.rate,   "%"),
        "pitch":   _norm(req.pitch,  "Hz"),
        "volume":  _norm(req.volume, "%"),
        "destino": destino,
    })

    return JSONResponse({"ok": True, "job_id": jid, "nombre": nombre})

@app.get("/jobs/{jid}")
async def estado_job(jid: str):
    if jid not in _trabajos:
        raise HTTPException(404, "Job no encontrado")
    return JSONResponse(_trabajos[jid])

# ── Generación por lotes ──────────────────────────────────────────────────────

@app.post("/lote")
async def generar_lote(req: LoteRequest):
    if not req.items:
        raise HTTPException(400, "Lista vacía")
    if req.voz not in VOCES:
        raise HTTPException(400, "Voz no disponible")

    rate   = _norm(req.rate,   "%")
    pitch  = _norm(req.pitch,  "Hz")
    volume = _norm(req.volume, "%")

    jobs = []
    for item in req.items:
        if not item.texto.strip():
            continue
        jid     = str(uuid.uuid4())
        nombre  = _nombre_archivo(item.texto, item.nombre)
        destino = OUTPUT_DIR / nombre
        _trabajos[jid] = {"estado": "en_cola", "nombre": nombre, "texto": item.texto[:40]}
        await _cola.put({
            "id": jid, "texto": item.texto.strip(),
            "voz": req.voz, "rate": rate, "pitch": pitch, "volume": volume,
            "destino": destino,
        })
        jobs.append({"job_id": jid, "nombre": nombre, "texto": item.texto[:40]})

    return JSONResponse({"ok": True, "total": len(jobs), "jobs": jobs})

@app.get("/lote/estado")
async def estado_lote(ids: str):
    """ids = job_ids separados por coma"""
    result = {}
    for jid in ids.split(","):
        jid = jid.strip()
        result[jid] = _trabajos.get(jid, {"estado": "desconocido"})
    return JSONResponse(result)

# ── Preview (sin guardar en output/) ─────────────────────────────────────────

@app.post("/preview")
async def preview(req: PreviewRequest):
    if not req.texto.strip():
        raise HTTPException(400, "Texto vacío")
    if req.voz not in VOCES:
        raise HTTPException(400, "Voz no disponible")

    # Limpiar previews anteriores
    for f in PREVIEW_DIR.glob("*.mp3"):
        try: f.unlink()
        except: pass

    nombre  = f"preview-{uuid.uuid4().hex[:8]}.mp3"
    destino = PREVIEW_DIR / nombre

    try:
        await _sintetizar(
            texto   = req.texto.strip(),
            voz     = req.voz,
            rate    = _norm(req.rate,   "%"),
            pitch   = _norm(req.pitch,  "Hz"),
            volume  = _norm(req.volume, "%"),
            destino = destino,
        )
        return JSONResponse({"ok": True, "ruta": f"/preview/{nombre}"})
    except Exception as e:
        if destino.exists(): destino.unlink()
        raise HTTPException(500, str(e))

@app.get("/preview/{nombre}")
async def servir_preview(nombre: str):
    ruta = PREVIEW_DIR / nombre
    if not ruta.exists():
        raise HTTPException(404, "Preview no encontrado")
    return FileResponse(str(ruta), media_type="audio/mpeg")

# ── Ruta del archivo en disco (para copiar al portapapeles) ───────────────────

@app.get("/audio/{nombre}/ruta")
async def obtener_ruta(nombre: str):
    ruta = OUTPUT_DIR / nombre
    if not ruta.exists():
        raise HTTPException(404, "No encontrado")
    return JSONResponse({"ruta": str(ruta.resolve())})

# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🎙️  TTS Studio v2")
    print(f"   http://localhost:8765")
    print(f"   Audios en: {OUTPUT_DIR.resolve()}\n")
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")