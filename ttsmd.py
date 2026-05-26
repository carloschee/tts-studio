"""
ttsmd.py — Parser de TTS-Markdown a SSML
=========================================

Sintaxis soportada:
  **texto**        → énfasis mayor  (emphasis strong)
  ~~texto~~        → énfasis menor  (emphasis reduced)
  >>texto<<        → contour descendente (entonación que baja al final)
  <<texto>>        → contour ascendente  (entonación que sube al final)
  ---              → pausa corta (300ms)
  ///              → pausa larga (700ms)
  ((texto|ph))     → fonema IPA  ej. ((válido|ˈba.li.ðo))

Combinaciones válidas:
  <<**texto**>>    contour ascendente + énfasis mayor
  >>~~texto~~<<    contour descendente + énfasis menor
  **((x|ph))**     énfasis + fonema

Uso:
  from ttsmd import to_ssml
  ssml = to_ssml("La **fotosíntesis** es importante. ---")
"""

import re

# ── Valores fijos ─────────────────────────────────────────────────────────────
CONTOUR_DESC = '(0%,+0Hz)(60%,+2Hz)(100%,-5Hz)'
CONTOUR_ASC  = '(0%,+0Hz)(80%,+3Hz)(100%,+6Hz)'
BREAK_SHORT  = '300ms'
BREAK_LONG   = '700ms'


# ── Helpers internos ──────────────────────────────────────────────────────────

def _escape_inner(text: str) -> str:
    """
    Antes de aplicar contours, codifica el > de las etiquetas XML internas
    como \x00GT\x00 para que el regex de >> / << no lo confunda con
    el delimitador de cierre del contour.
    Después de aplicar contours, decodifica de vuelta.
    """
    return text.replace('>', '\x00GT\x00')

def _unescape_inner(text: str) -> str:
    return text.replace('\x00GT\x00', '>')


# ── parse ─────────────────────────────────────────────────────────────────────

def parse(text: str) -> str:
    """
    Convierte TTS-Markdown a fragmento SSML interior (sin wrapper <speak>/<voice>).
    """
    result = text

    # Paso 1 — Fonemas (sin otros marcadores dentro)
    result = re.sub(
        r'\(\((.+?)\|(.+?)\)\)',
        lambda m: f'<phoneme alphabet="ipa" ph="{m.group(2)}">{m.group(1)}</phoneme>',
        result,
    )

    # Paso 2 — Énfasis (puede haber fonemas dentro, ya convertidos a XML)
    result = re.sub(
        r'\*\*(.+?)\*\*',
        lambda m: f'<emphasis level="strong">{m.group(1)}</emphasis>',
        result, flags=re.DOTALL,
    )
    result = re.sub(
        r'~~(.+?)~~',
        lambda m: f'<emphasis level="reduced">{m.group(1)}</emphasis>',
        result, flags=re.DOTALL,
    )

    # Paso 3 — Contours
    # Los > de las etiquetas XML ya generadas se escapan temporalmente
    # para que >> y << solo hagan match con los delimitadores reales.
    def apply_contour(txt):
        # Escapar > dentro de etiquetas XML existentes
        # Solo escapamos el > que forma parte de una etiqueta (</xxx> o <xxx>)
        escaped = re.sub(r'(</?\w[^<]*?)/?>', lambda m: m.group(0)[:-1] + '\x00GT\x00', txt)

        # Descendente: >>...<<
        escaped = re.sub(
            r'>>(.+?)<<',
            lambda m: f'<prosody contour="{CONTOUR_DESC}">{m.group(1)}</prosody>',
            escaped, flags=re.DOTALL,
        )
        # Ascendente: <<...>>
        escaped = re.sub(
            r'<<(.+?)>>',
            lambda m: f'<prosody contour="{CONTOUR_ASC}">{m.group(1)}</prosody>',
            escaped, flags=re.DOTALL,
        )

        # Restaurar
        return escaped.replace('\x00GT\x00', '>')

    result = apply_contour(result)

    # Paso 4 — Breaks (al final, sin >> ni << sueltos)
    result = re.sub(r'\s*///\s*', f'<break time="{BREAK_LONG}"/>', result)
    result = re.sub(r'\s*---\s*', f'<break time="{BREAK_SHORT}"/>', result)

    return result


# ── to_ssml ───────────────────────────────────────────────────────────────────

def to_ssml(
    text: str,
    voice: str = "es-MX-DaliaNeural",
    style: str = "",
    style_degree: float = 1.0,
    lang: str = "es-MX",
) -> str:
    """
    Convierte TTS-Markdown a SSML completo listo para edge-tts o Azure.
    """
    inner = parse(text)

    if style:
        inner = (
            f'<mstts:express-as style="{style}" styledegree="{style_degree:.1f}">'
            f'{inner}'
            f'</mstts:express-as>'
        )

    return (
        f'<speak version="1.0" '
        f'xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xmlns:mstts="https://www.w3.org/2001/mstts" '
        f'xml:lang="{lang}">'
        f'<voice name="{voice}">'
        f'{inner}'
        f'</voice>'
        f'</speak>'
    )


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    DEMO = (
        "La **fotosíntesis** es el proceso por el cual\n"
        "las plantas convierten la luz solar en energía. ---\n"
        ">>Este proceso ocurre principalmente en las hojas de la planta.<< ///\n"
        "<<¿((entendiste|en.ten.ˈdis.te)) la explicación?>>\n"
        "~~Este dato es complementario~~ y puede omitirse en el examen."
    )
    source = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else DEMO
    voice  = sys.argv[2] if len(sys.argv) > 2 else "es-MX-DaliaNeural"
    print(to_ssml(source, voice=voice))