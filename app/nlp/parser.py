import re
import unicodedata


def clean_text(text: str) -> str:
    """Quita tildes, signos diacríticos y convierte a mayúsculas."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.lower().strip()


# Canónical list of Colombian departments
DPTOS_COLOMBIA = {
    "ANTIOQUIA",
    "CUNDINAMARCA",
    "ATLANTICO",
    "BOLIVAR",
    "BOYACA",
    "CALDAS",
    "CAQUETA",
    "CASANARE",
    "CAUCA",
    "CESAR",
    "CHOCO",
    "CORDOBA",
    "HUILA",
    "LA GUAJIRA",
    "MAGDALENA",
    "META",
    "NARINO",
    "NORTE DE SANTANDER",
    "PUTUMAYO",
    "QUINDIO",
    "RISARALDA",
    "SANTANDER",
    "SUCRE",
    "TOLIMA",
    "VALLE DEL CAUCA",
    "ARAUCA",
    "AMAZONAS",
    "GUAINIA",
    "GUAVIARE",
    "VAUPES",
    "VICHADA",
    "BOGOTA D. C.",
}

# Regex to match different types of dashes (normal, en-dash, em-dash) and surrounding whitespace
DASHES = re.compile(r"\s*[-–—]\s*")  # noqa: RUF001


def parse_sicetac(entry: str) -> dict[str, str]:
    """
    Parse a SICETAC entry into a dictionary of:
    - lugar: Specific place, station, airport, or neighborhood
    - municipio: Canonical municipality name
    - departamento: Department name

    Handles 3 main formats:
    - Tipo A (3+ parts): 'AEROPUERTO - RIONEGRO - ANTIOQUIA' -> RIONEGRO, ANTIOQUIA
    - Tipo B (2 parts): 'AGUACHICA-CESAR' -> AGUACHICA, CESAR
    - Tipo C (1 part): 'BOGOTÁ' -> BOGOTA, ''
    """
    entry = entry.strip()
    partes = [p.strip() for p in DASHES.split(entry) if p.strip()]

    if len(partes) >= 3:
        # e.g., 'BUENOS AIRES - LAS PAVAS - CANALETE - CORDOBA'
        # Last part is department, second to last is municipality, everything before is place
        departamento = partes[-1]
        municipio = partes[-2]
        lugar = " - ".join(partes[:-2])
        return {"lugar": lugar, "municipio": municipio, "departamento": departamento}
    elif len(partes) == 2:
        # e.g., 'AGUACHICA-CESAR' or 'ARBOLETES - ANTIOQUIA'
        municipio = partes[0]
        departamento = partes[1]
        return {
            "lugar": municipio,
            "municipio": municipio,
            "departamento": departamento,
        }
    elif len(partes) == 1:
        # e.g., 'BOGOTÁ'
        municipio = partes[0]
        return {"lugar": municipio, "municipio": municipio, "departamento": ""}
    else:
        return {"lugar": "", "municipio": "", "departamento": ""}


def parse_rndc(entry: str) -> dict[str, str]:
    """
    Parse an RNDC string from the end to isolate the department.

    Example:
    - 'ABEJORRAL ANTIOQUIA' -> municipio='ABEJORRAL', departamento='ANTIOQUIA'
    - 'AEROPUERTO RIONEGRO ANTIOQUIA' -> municipio='AEROPUERTO RIONEGRO', departamento='ANTIOQUIA'
    """
    entry = entry.strip()
    entry_up = clean_text(entry)

    # Sort departments by their cleaned length descending to avoid matching substrings first
    # e.g., VALLE DEL CAUCA before CAUCA
    sorted_dptos = sorted(
        DPTOS_COLOMBIA, key=lambda d: len(clean_text(d)), reverse=True
    )

    for dpto in sorted_dptos:
        dpto_clean = clean_text(dpto)
        if entry_up.endswith(dpto_clean):
            # Find the split index based on the cleaned version
            # We want to keep the original casing of the municipality
            # Calculate length of department in raw string by finding matching suffix
            # since there could be differences in spaces/accents, we search from the back.
            # Usually, they are roughly the same length. Let's just slice it.
            # To be safe, we can find where the department starts in the cleaned string.
            split_idx_clean = len(entry_up) - len(dpto_clean)

            # Reconstruct approximately based on words from original entry
            words = entry.split()
            # Try to match words from the end
            dpto_words_count = len(dpto.split())
            if len(words) > dpto_words_count:
                municipio = " ".join(words[:-dpto_words_count])
                departamento = " ".join(words[-dpto_words_count:])
                return {
                    "municipio": municipio.strip(),
                    "departamento": departamento.strip(),
                }
            else:
                # If there are not enough words, fallback to simple slice
                municipio = entry[:split_idx_clean].strip()
                departamento = entry[split_idx_clean:].strip()
                return {"municipio": municipio, "departamento": departamento}

    return {"municipio": entry, "departamento": ""}
