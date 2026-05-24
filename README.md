# TTS Studio 🎙️

Herramienta local para generar audios con voces neurales de Microsoft Edge.
Soporta estilos expresivos (cheerful, excited, whispering, sad…) y control
fino de velocidad, tono y volumen vía SSML.

## Instalación

```bash
pip install fastapi uvicorn edge-tts python-multipart
```

## Uso

```bash
python server.py
```

Abre **http://localhost:8765** en tu navegador.

Los audios generados se guardan en la carpeta `output/`.

## Voces disponibles

| Voz | Idioma | Estilos |
|-----|--------|---------|
| Dalia | es-MX | cheerful, excited, friendly, hopeful, sad, shouting, whispering… |
| Elvira | es-ES | cheerful, empathetic, friendly, sad |
| Aria | en-US | chat, cheerful, angry, hopeful, narration, newscast, whispering… |
| Jenny | en-US | assistant, chat, excited, friendly, hopeful, sad, whispering… |
| Guy | en-US | angry, cheerful, excited, newscast, sad, shouting, whispering… |

## Atajos de teclado

- **Cmd/Ctrl + Enter** — Generar audio

## Notas

- Los audios sin nombre se nombran automáticamente con timestamp + primeras palabras del texto.
- El audio recién generado se reproduce automáticamente.
- La carpeta `output/` se puede usar directamente como fuente para otros proyectos.