#!/usr/bin/env python3
"""
tts-studio/build.py
Empaqueta TTS Studio como ejecutable standalone con PyInstaller.

Uso:
  pip install pyinstaller
  python build.py

Genera:
  dist/TTS-Studio/          ← carpeta portable (Windows)
  dist/TTS-Studio.app/      ← app bundle (macOS)

La carpeta dist/TTS-Studio/ se puede comprimir y distribuir.
El usuario final no necesita Python instalado.
"""

import subprocess
import sys
import shutil
from pathlib import Path

RAIZ = Path(__file__).parent

def check_pyinstaller():
    try:
        import PyInstaller
    except ImportError:
        print("❌  PyInstaller no está instalado.")
        print("   pip install pyinstaller")
        sys.exit(1)

def limpiar():
    for d in ["build", "dist", "__pycache__"]:
        ruta = RAIZ / d
        if ruta.exists():
            shutil.rmtree(ruta)
            print(f"   🗑  {d}/ eliminado")
    spec = RAIZ / "tts-studio.spec"
    if spec.exists():
        spec.unlink()

def build():
    check_pyinstaller()
    limpiar()

    print("\n🔨  Empaquetando TTS Studio…\n")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name", "TTS-Studio",

        # Un solo directorio portable (no un .exe único — más rápido de arrancar)
        "--onedir",

        # Sin ventana de consola en Windows (la app abre el navegador)
        "--noconsole",

        # Incluir index.html junto al ejecutable
        "--add-data", f"index.html{':' if sys.platform != 'win32' else ';'}.",

        # Incluir carpeta output/ vacía
        "--add-data", f"output{':' if sys.platform != 'win32' else ';'}output",

        # Icono (opcional — si existe)
        *(["--icon", str(RAIZ / "icon.ico")] if (RAIZ / "icon.ico").exists() else []),
        *(["--icon", str(RAIZ / "icon.icns")] if (RAIZ / "icon.icns").exists() and sys.platform == "darwin" else []),

        # Ocultar imports que PyInstaller no detecta automáticamente
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
        "--hidden-import", "edge_tts",
        "--hidden-import", "edge_tts.communicate",
        "--hidden-import", "websockets",

        str(RAIZ / "launcher.py"),
    ]

    result = subprocess.run(cmd, cwd=str(RAIZ))

    if result.returncode != 0:
        print("\n❌  Error al empaquetar.")
        sys.exit(1)

    # Crear carpeta output/ vacía en dist si no existe
    output_dist = RAIZ / "dist" / "TTS-Studio" / "output"
    output_dist.mkdir(exist_ok=True)
    (output_dist / ".gitkeep").touch()

    print("\n✅  Listo.")
    print(f"   Distribuible: dist/TTS-Studio/")
    print(f"   Comprime esa carpeta y compártela — no requiere Python.")
    if sys.platform == "win32":
        print(f"   Ejecutable: dist/TTS-Studio/TTS-Studio.exe")
    elif sys.platform == "darwin":
        print(f"   Ejecutable: dist/TTS-Studio/TTS-Studio")
        print(f"   (o dist/TTS-Studio.app si usas --windowed en macOS)")
    else:
        print(f"   Ejecutable: dist/TTS-Studio/TTS-Studio")

if __name__ == "__main__":
    build()