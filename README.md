# TTS Studio 🎙️

Herramienta local para generar audios con voces neurales de Microsoft Edge.
Controla velocidad, tono y volumen con presets de estilo predefinidos y personalizables.
Soporta generación individual, por lotes, preview sin guardar y comparación A/B.

---

## Instalación

```bash
pip install fastapi uvicorn edge-tts python-multipart
```

## Uso

```bash
python server.py
```

Abre **http://localhost:8765** en tu navegador. Los audios se guardan en `output/`.

**Atajo de teclado:** `Cmd+Enter` / `Ctrl+Enter` para generar sin soltar el teclado.

---

## Voces disponibles

| Voz | Idioma | Género |
|-----|--------|--------|
| Dalia | es-MX | Femenino |
| Jorge | es-MX | Masculino |
| Elvira | es-ES | Femenino |
| Aria | en-US | Femenino |
| Jenny | en-US | Femenino |
| Guy | en-US | Masculino |

---

## Estilos predefinidos

Los presets ajustan automáticamente velocidad, tono y volumen para simular diferentes registros expresivos:

| Preset | Velocidad | Tono | Volumen |
|--------|-----------|------|---------|
| ⚪ Neutro | 0% | 0 Hz | 0% |
| 🎉 Emocionado | +20% | +10 Hz | +10% |
| 😄 Alegre | +10% | +8 Hz | +5% |
| 🤝 Amigable | -10% | +5 Hz | 0% |
| 🌅 Esperanzador | -5% | +6 Hz | -5% |
| 😢 Triste | -25% | -8 Hz | -5% |
| 🤫 Susurro | -30% | -5 Hz | -20% |
| 📢 Gritando | +10% | +5 Hz | +20% |
| 😤 Hostil | +15% | -3 Hz | +10% |

Los sliders de ajuste fino permiten modificar cualquier parámetro individualmente después de elegir un preset. Si ajustas manualmente, el preset activo se desmarca.

---

## Funcionalidades

### Generación individual
Escribe el texto en el panel izquierdo, elige voz y estilo, y genera. Los trabajos se encolan y procesan uno a la vez — un badge en el topbar muestra cuántos están pendientes.

### Preview sin guardar
El botón **👁 Preview** sintetiza el audio y lo reproduce directamente sin guardarlo en `output/`. Útil para afinar parámetros antes de confirmar.

### Generación por lotes
La pestaña **Por lotes** acepta una frase por línea. Formato:

```
¡Muy bien!
¡Lo lograste!
¡Sigue intentando!
```

Formato con nombre de archivo personalizado (separado por `|`):

```
celebracion-1|¡Muy bien!
celebracion-2|¡Lo lograste!
error-suave|¡Sigue intentando!
```

Todos los ítems del lote usan la misma voz y parámetros del panel izquierdo. El progreso de cada ítem se muestra en tiempo real.

### Presets personalizados
El botón **+ Guardar configuración actual** guarda la voz y parámetros actuales con un nombre personalizado. Los presets se almacenan localmente en el navegador y persisten entre sesiones. Cada preset tiene un botón × para eliminarlo.

### Biblioteca
- **Doble clic** en el nombre de un archivo para renombrarlo in situ
- **Búsqueda** en tiempo real por nombre de archivo
- **⎘ Copiar ruta** — copia la ruta absoluta del archivo al portapapeles (útil para referenciar el archivo desde otro proyecto)
- **⬇ Descargar** — descarga el archivo directamente desde el navegador
- **✕ Eliminar** — elimina el archivo del disco

### Comparador A/B
El botón **A/B** en el header de la biblioteca activa el modo comparación. Selecciona dos archivos tocando en ellos — se marcan con un borde azul. Los botones A y B en el panel flotante reproducen cada uno para comparar.

---

## Cola de generación

El servidor procesa las solicitudes secuencialmente — nunca se solapan dos síntesis. El badge en el topbar muestra cuántos trabajos están pendientes. Los resultados aparecen en la biblioteca automáticamente al terminar cada trabajo.

---

## Estructura de carpetas

```
tts-studio/
├── server.py      ← servidor FastAPI con cola de generación
├── launcher.py    ← entry point para el ejecutable empaquetado
├── index.html     ← UI completa
├── build.py       ← empaquetado con PyInstaller
├── output/        ← audios generados (persistentes)
├── preview/       ← audios de preview (temporales, se limpian automáticamente)
└── README.md
```

---

## Empaquetar como ejecutable standalone

Genera un distributable que no requiere Python instalado:

```bash
pip install pyinstaller
python build.py
```

Produce `dist/TTS-Studio/` — comprime esa carpeta y compártela. El usuario hace doble clic en `TTS-Studio.exe` (Windows) o `TTS-Studio` (Mac/Linux) y el navegador se abre automáticamente.

**Nota:** requiere conexión a internet — los servidores de Microsoft Edge TTS no se pueden empaquetar localmente.

---

## Notas técnicas

- El SSML con estilos expresivos (`mstts:express-as`) no funciona vía la API WebSocket que usa edge-tts. Los estilos se simulan con combinaciones de `rate`, `pitch` y `volume`.
- Los archivos de preview se limpian automáticamente en cada nueva solicitud de preview.
- Los presets personalizados se guardan en `localStorage` del navegador — no se sincronizan entre navegadores ni máquinas.
- El servidor corre en `127.0.0.1:8765` — solo accesible desde la misma máquina.
