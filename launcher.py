#!/usr/bin/env python3
"""
tts-studio/launcher.py
Punto de entrada para el ejecutable empaquetado.
Arranca el servidor FastAPI en un hilo y abre la app en una ventana
nativa con pywebview (sin Chrome, sin barra de URL).

Requisitos:
  pip install pywebview
"""

import sys
import threading
import time
import urllib.request
from pathlib import Path

# ─── Resolver rutas dentro del bundle ────────────────────────────────────────
if getattr(sys, "frozen", False):
    BASE_DIR   = Path(sys._MEIPASS)
    OUTPUT_DIR = Path(sys.executable).parent / "output"
else:
    BASE_DIR   = Path(__file__).parent
    OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)

import os
os.environ["TTS_STUDIO_BASE"]   = str(BASE_DIR)
os.environ["TTS_STUDIO_OUTPUT"] = str(OUTPUT_DIR)

# ─── Importar la app ──────────────────────────────────────────────────────────
sys.path.insert(0, str(BASE_DIR))

from server import app, OUTPUT_DIR as _  # noqa

import server as _srv
_srv.OUTPUT_DIR = OUTPUT_DIR
_srv.INDEX_HTML = BASE_DIR / "index.html"

# ─── Configuración ────────────────────────────────────────────────────────────
PORT   = 8765
URL    = f"http://127.0.0.1:{PORT}"
TITULO = "TTS Studio"
ANCHO  = 1200
ALTO   = 780

# ─── Servidor uvicorn en hilo daemon ─────────────────────────────────────────
def _run_server():
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=PORT,
        log_level="warning",
        access_log=False,
    )

def _esperar_servidor(timeout: float = 5.0) -> bool:
    """Espera hasta que el servidor responda. Devuelve True si arrancó."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{URL}/voces", timeout=0.3)
            return True
        except Exception:
            time.sleep(0.1)
    return False

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    # Verificar pywebview
    try:
        import webview
    except ImportError:
        print("\n[ERROR] pywebview no está instalado.")
        print("   pip install pywebview\n")
        # Fallback: abrir en navegador del sistema
        import webbrowser
        hilo_srv = threading.Thread(target=_run_server, daemon=True)
        hilo_srv.start()
        if _esperar_servidor():
            webbrowser.open(URL)
        hilo_srv.join()
        return

    print(f"\n  TTS Studio")
    print(f"  Servidor en {URL}")
    print(f"  Audios en:  {OUTPUT_DIR}\n")

    # Servidor en hilo daemon
    hilo_srv = threading.Thread(target=_run_server, daemon=True)
    hilo_srv.start()

    # Esperar a que el servidor esté listo antes de abrir la ventana
    if not _esperar_servidor():
        print("[WARN] El servidor tardó demasiado en arrancar.")

    # Crear ventana nativa
    # confirm_close=True muestra diálogo "¿Cerrar TTS Studio?" al salir
    ventana = webview.create_window(
        title           = TITULO,
        url             = URL,
        width           = ANCHO,
        height          = ALTO,
        resizable       = True,
        confirm_close   = False,
        text_select     = True,
        # min_size evita que la ventana quede inutilizable al redimensionar
        min_size        = (800, 560),
    )

    # Iniciar webview — bloquea hasta que el usuario cierra la ventana
    # gui=None → pywebview elige el mejor backend disponible:
    #   Windows → WebView2 (Edge Chromium, ya incluido en Win10/11)
    #   macOS   → WKWebView
    #   Linux   → gtk / qt
    webview.start(debug=False)

    # Cuando la ventana se cierra, el proceso termina
    print("\n  TTS Studio cerrado.")


if __name__ == "__main__":
    main()