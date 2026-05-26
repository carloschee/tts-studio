#!/usr/bin/env python3
"""
tts-studio/build.py
Empaqueta TTS Studio como ejecutable standalone con PyInstaller + pywebview.

Uso:
  pip install pyinstaller pywebview
  python build.py

Genera:
  dist/TTS-Studio/        ← carpeta portable (Windows / Linux)
  dist/TTS-Studio.app/    ← app bundle (macOS, con --windowed)

La carpeta dist/TTS-Studio/ se puede comprimir y distribuir.
El usuario final NO necesita Python, Chrome ni ningún navegador instalado.
En Windows 10/11 usa el WebView2 de Edge que ya viene en el sistema.
"""

import subprocess
import sys
import shutil
from pathlib import Path

RAIZ = Path(__file__).parent

SEP = ";" if sys.platform == "win32" else ":"   # separador add-data


def check_deps():
    faltantes = []
    for pkg in ["PyInstaller", "webview"]:
        try:
            __import__(pkg)
        except ImportError:
            faltantes.append(pkg)
    if faltantes:
        print(f"\n[ERROR] Faltan dependencias: {', '.join(faltantes)}")
        print(f"   pip install {' '.join(f.lower() for f in faltantes)}")
        sys.exit(1)


def limpiar():
    for d in ["build", "dist", "__pycache__"]:
        ruta = RAIZ / d
        if ruta.exists():
            shutil.rmtree(ruta)
            print(f"   eliminado: {d}/")
    for spec in RAIZ.glob("*.spec"):
        spec.unlink()
        print(f"   eliminado: {spec.name}")


def build():
    check_deps()
    limpiar()

    print("\n  Empaquetando TTS Studio...\n")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name", "TTS-Studio",
        "--onedir",
        "--noconsole",      # sin ventana de consola negra en Windows

        # Archivos de datos
        "--add-data", f"index.html{SEP}.",
        "--add-data", f"output{SEP}output",

        # Icono (opcional — coloca icon.ico en la raíz del proyecto)
        *(["--icon", str(RAIZ / "icon.ico")]
          if (RAIZ / "icon.ico").exists() else []),
        *(["--icon", str(RAIZ / "icon.icns")]
          if (RAIZ / "icon.icns").exists() and sys.platform == "darwin" else []),

        # ── Hidden imports: uvicorn ──
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "anyio",
        "--hidden-import", "anyio._backends._asyncio",

        # ── Hidden imports: edge-tts ──
        "--hidden-import", "edge_tts",
        "--hidden-import", "edge_tts.communicate",
        "--hidden-import", "websockets",

        # ── Hidden imports: pywebview ──
        "--hidden-import", "webview",
        "--hidden-import", "webview.platforms.winforms",  # Windows
        "--hidden-import", "webview.platforms.cocoa",     # macOS
        "--hidden-import", "webview.platforms.gtk",       # Linux GTK
        "--hidden-import", "webview.platforms.qt",        # Linux Qt
        "--hidden-import", "clr",                         # pythonnet (Windows)

        str(RAIZ / "launcher.py"),
    ]

    # En Windows, pywebview con WebView2 necesita el runtime de .NET
    # PyInstaller no lo copia solo — se distribuye junto al .exe
    if sys.platform == "win32":
        cmd += [
            "--hidden-import", "System",
            "--hidden-import", "System.Windows.Forms",
        ]

    result = subprocess.run(cmd, cwd=str(RAIZ))

    if result.returncode != 0:
        print("\n[ERROR] Falló el empaquetado.")
        sys.exit(1)

    # Crear carpeta output/ vacía en dist
    output_dist = RAIZ / "dist" / "TTS-Studio" / "output"
    output_dist.mkdir(exist_ok=True)
    (output_dist / ".gitkeep").touch()

    # Nota sobre WebView2 en Windows
    if sys.platform == "win32":
        _nota_webview2()

    print("\n[OK] Empaquetado completado.")
    print(f"   Distribuible : dist/TTS-Studio/")
    print(f"   Ejecutable   : dist/TTS-Studio/TTS-Studio.exe")
    print(f"   Comprime la carpeta dist/TTS-Studio/ para distribuir.")


def _nota_webview2():
    """Imprime nota sobre el runtime WebView2 en Windows."""
    print("""
  NOTA — Windows y WebView2:
  La ventana nativa usa el motor WebView2 de Microsoft Edge,
  que viene preinstalado en Windows 10 (actualización 1803+) y Windows 11.

  Si el usuario tiene un Windows muy desactualizado (raro), necesitará
  instalar el runtime manualmente desde:
  https://developer.microsoft.com/microsoft-edge/webview2/

  Para distribuir el runtime junto al instalador, puedes usar
  el "Evergreen Bootstrapper" de Microsoft (1.7 MB).
""")


if __name__ == "__main__":
    build()