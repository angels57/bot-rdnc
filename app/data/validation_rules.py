"""Reglas de validación y datos válidos para Excel."""

# Configuraciones de vehículos válidas
CONFIGURACIONES_VALIDAS = {
    "3S3",
    "3S2",
    "2S2",
    "2S3",
    "3",
    "V2",
    "V3",
    "V4",
    "2",
    "2_7_8",
    "2_8_9",
    "2_9_105",
}

CONDICIONES_VALIDAS = {"CARGADO", "VACIO"}

CARROCERIAS_VALIDAS = {
    "ESTACAS",
    "ESTIBAS",
    "TANQUE",
    "FURGON",
    "PORTACONTENEDORES",
    "TRAYLER",
    "VOLCO",
    "PLATAFORMA",
    "FURGON REFRIGERADO",
}

TIPOS_CARGA_VALIDOS = {"General", "Granel Sólido"}

HORAS_VALIDAS = {"1", "2", "3", "4", "5", "6"}

# Esquema de validación por columna
COLUMN_VALIDATORS = {
    "configuracion": {
        "type": "enum",
        "valores": CONFIGURACIONES_VALIDAS,
        "mensaje": f"Debe ser uno de: {', '.join(sorted(CONFIGURACIONES_VALIDAS))}",
    },
    "condicion_carga": {
        "type": "enum",
        "valores": CONDICIONES_VALIDAS,
        "mensaje": f"Debe ser uno de: {', '.join(sorted(CONDICIONES_VALIDAS))}",
    },
    "carroceria": {
        "type": "enum",
        "valores": CARROCERIAS_VALIDAS,
        "mensaje": f"Debe ser uno de: {', '.join(sorted(CARROCERIAS_VALIDAS))}",
    },
    "tipo_carga": {
        "type": "enum",
        "valores": TIPOS_CARGA_VALIDOS,
        "mensaje": f"Debe ser uno de: {', '.join(sorted(TIPOS_CARGA_VALIDOS))}",
    },
    "horas_cargue_descargue": {
        "type": "enum",
        "valores": HORAS_VALIDAS,
        "mensaje": f"Debe ser uno de: {', '.join(sorted(HORAS_VALIDAS))}",
    },
    "origen": {"type": "string", "mensaje": "No puede estar vacío"},
    "destino": {"type": "string", "mensaje": "No puede estar vacío"},
}


def validar_fila(row: dict, columns_map: dict[str, str]) -> tuple[bool, list[str]]:
    """
    Valida una fila del Excel.

    Args:
        row: Diccionario con los datos de la fila
        columns_map: Mapeo de nombres canónicos a nombres reales de columnas

    Returns:
        Tupla (es_válida, lista_errores)
    """
    errores = []

    for canonical_name, validator in COLUMN_VALIDATORS.items():
        if canonical_name not in columns_map:
            continue

        original_col_name = columns_map[canonical_name]
        valor = str(row.get(original_col_name, "")).strip()

        # Validar que no esté vacío
        if not valor:
            errores.append(f"{canonical_name}: {validator['mensaje']}")
            continue

        # Validar tipo enum
        if validator["type"] == "enum" and valor not in validator["valores"]:
            errores.append(
                f"{canonical_name}: valor '{valor}' inválido. {validator['mensaje']}"
            )

    return len(errores) == 0, errores
