#!/usr/bin/env python3
"""
tts-studio/launcher.py
Punto de entrada para el ejecutable empaquetado.
Arranca el servidor FastAPI en un hilo y abre el navegador automáticamente.
PyInstaller usa este archivo como entry point (no server.py).
"""

import sys
import threading
import time
import webbrowser
from pathlib import Path

# ─── Resolver rutas dentro del bundle ────────────────────────────────────────
# PyInstaller extrae los archivos a sys._MEIPASS en modo --onedir
# En desarrollo normal, usa el directorio del script
if getattr(sys, "frozen", False):
    # Corriendo como ejecutable empaquetado
    BASE_DIR = Path(sys._MEIPASS)
    # Los archivos generados van junto al .exe, no dentro del bundle
    OUTPUT_DIR = Path(sys.executable).parent / "output"
else:
    # Corriendo en desarrollo
    BASE_DIR   = Path(__file__).parent
    OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)

# Parchear las rutas en server.py antes de importarlo
import os
os.environ["TTS_STUDIO_BASE"]   = str(BASE_DIR)
os.environ["TTS_STUDIO_OUTPUT"] = str(OUTPUT_DIR)

# ─── Importar la app ──────────────────────────────────────────────────────────
# Añadir BASE_DIR al path para que server.py se encuentre
sys.path.insert(0, str(BASE_DIR))

from server import app, OUTPUT_DIR as _  # noqa — solo para forzar el import

# Parchear OUTPUT_DIR en server con la ruta correcta
import server as _srv
_srv.OUTPUT_DIR   = OUTPUT_DIR
_srv.INDEX_HTML   = BASE_DIR / "index.html"

# ─── Arrancar servidor en hilo secundario ─────────────────────────────────────
PORT = 8765

def _run_server():
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=PORT,
        log_level="warning",
        access_log=False,
    )

def _esperar_y_abrir():
    """Espera a que el servidor arranque y luego abre el navegador."""
    import urllib.request
    for _ in range(30):  # hasta 3 segundos
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/voces", timeout=0.3)
            break
        except Exception:
            time.sleep(0.1)
    webbrowser.open(f"http://127.0.0.1:{PORT}")

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print(f"\n🎙️  TTS Studio")
    print(f"   Servidor en http://127.0.0.1:{PORT}")
    print(f"   Audios guardados en: {OUTPUT_DIR}")
    print(f"   Cierra esta ventana para detener.\n")

    # Servidor en hilo daemon — muere cuando cierra el proceso principal
    hilo = threading.Thread(target=_run_server, daemon=True)
    hilo.start()

    # Abrir navegador en hilo separado para no bloquear
    threading.Thread(target=_esperar_y_abrir, daemon=True).start()

    # Mantener el proceso vivo
    try:
        hilo.join()
    except KeyboardInterrupt:
        print("\n👋  TTS Studio detenido.")

if __name__ == "__main__":
    main()