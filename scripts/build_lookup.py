import json
from pathlib import Path

import polars as pl
from rapidfuzz import fuzz

from app.nlp.normalizer import clean_text
from app.nlp.parser import parse_rndc, parse_sicetac


def main():
    print("🚀 Iniciando la generación del lookup table SICETAC -> RNDC...")

    # 1. Cargar las opciones de SICETAC
    sicetac_path = Path("data/sicetac_options.json")
    if not sicetac_path.exists():
        print(
            f"❌ Error: No se encontró el archivo de opciones de SICETAC en {sicetac_path}"
        )
        return

    with open(sicetac_path, encoding="utf-8") as f:
        sicetac_data = json.load(f)

    # Unificar origen y destino para tener la lista completa y única
    sicetac_entries = sorted(
        set(sicetac_data.get("origen", []) + sicetac_data.get("destino", []))
    )
    print(f"📦 Cargadas {len(sicetac_entries)} entradas únicas de SICETAC.")

    # 2. Cargar RNDC.xlsx y extraer pares únicos de Municipio + Departamento
    rndc_path = Path("data/RNDC.xlsx")
    if not rndc_path.exists():
        print(f"❌ Error: No se encontró el archivo RNDC en {rndc_path}")
        return

    print("📖 Leyendo data/RNDC.xlsx con Polars (esto puede tomar unos segundos)...")
    df = pl.read_excel(rndc_path)

    print("🧹 Extrayendo combinaciones únicas de origen y destino en RNDC...")
    origenes = (
        df.select(
            [
                pl.col("MUNICIPIOORIGEN").alias("rndc_full"),
                pl.col("DEPARTAMENTOORIGEN").alias("dpto"),
            ]
        )
        .drop_nulls()
        .unique()
    )

    destinos = (
        df.select(
            [
                pl.col("MUNICIPIODESTINO").alias("rndc_full"),
                pl.col("DEPARTAMENTODESTINO").alias("dpto"),
            ]
        )
        .drop_nulls()
        .unique()
    )

    rndc_pairs = pl.concat([origenes, destinos]).unique().to_dicts()
    print(
        f"📦 Encontrados {len(rndc_pairs)} pares únicos de Municipio-Departamento en RNDC."
    )

    # 3. Pre-parsear todos los candidatos RNDC
    parsed_rndc_list = []
    for item in rndc_pairs:
        rndc_full = item["rndc_full"].strip()
        dpto = item["dpto"].strip()

        parsed = parse_rndc(rndc_full)
        parsed_rndc_list.append(
            {
                "rndc_full": rndc_full,
                "municipio_clean": clean_text(parsed["municipio"]),
                "dpto_clean": clean_text(dpto),
            }
        )

    # 4. Resolver cada entrada SICETAC
    lookup = {}
    unmatched = []

    print("🔍 Realizando el cruce y mapeo estructurado...")

    for entry in sicetac_entries:
        parsed_sic = parse_sicetac(entry)
        muni_clean = clean_text(parsed_sic["municipio"])
        dpto_clean = clean_text(parsed_sic["departamento"])
        lugar_clean = clean_text(parsed_sic["lugar"])

        # Filtrar candidatos RNDC por departamento si se tiene
        if dpto_clean:
            # Intentar match por departamento
            candidates = [c for c in parsed_rndc_list if c["dpto_clean"] == dpto_clean]

            # Fallback especial para departamentos que pueden tener nombres ligeramente alternativos
            # e.g., NARIÑO vs NARINO, BOGOTA D. C. vs BOGOTA DISTRITO CAPITAL
            if not candidates:
                # Buscar con fuzzy en el nombre del departamento
                best_dpto_match = None
                best_dpto_score = 0
                for c in parsed_rndc_list:
                    score = fuzz.ratio(dpto_clean, c["dpto_clean"])
                    if score > best_dpto_score:
                        best_dpto_score = score
                        best_dpto_match = c["dpto_clean"]

                if best_dpto_score >= 80 and best_dpto_match:
                    candidates = [
                        c
                        for c in parsed_rndc_list
                        if c["dpto_clean"] == best_dpto_match
                    ]
                else:
                    candidates = parsed_rndc_list
        else:
            candidates = parsed_rndc_list

        # Realizar fuzzy matching dentro de los candidatos filtrados
        best_match = None
        best_score = -1.0

        for c in candidates:
            # 1. Comparar solo municipio
            score_muni = fuzz.ratio(muni_clean, c["municipio_clean"])

            # 2. Comparar Lugar + Municipio (si existe un lugar distinto)
            if lugar_clean and lugar_clean != muni_clean:
                full_sic_clean = clean_text(
                    parsed_sic["lugar"] + " " + parsed_sic["municipio"]
                )
                score_full = fuzz.ratio(full_sic_clean, c["municipio_clean"])
            else:
                score_full = score_muni

            # Combinación de scores
            score = max(score_muni, score_full)

            # Desempate preferente para coincidencia exacta
            if score > best_score:
                best_score = score
                best_match = c
            elif score == best_score and best_match is not None:
                # Preferir el que tenga una longitud más cercana al municipio buscado
                len_diff_current = abs(len(muni_clean) - len(c["municipio_clean"]))
                len_diff_best = abs(
                    len(muni_clean) - len(best_match["municipio_clean"])
                )
                if len_diff_current < len_diff_best:
                    best_match = c

        # Verificar si cumple con el umbral (score >= 80)
        if best_match and best_score >= 80:
            lookup[entry] = best_match["rndc_full"]
        else:
            # Si falló, intentar fuzzy con token_set_ratio a nivel global como último recurso
            global_best_match = None
            global_best_score = -1.0

            for c in parsed_rndc_list:
                score = fuzz.token_set_ratio(muni_clean, c["municipio_clean"])
                if score > global_best_score:
                    global_best_score = score
                    global_best_match = c

            if global_best_match and global_best_score >= 85:
                lookup[entry] = global_best_match["rndc_full"]
            else:
                unmatched.append(entry)

    # Agregar las no emparejadas al lookup bajo la clave "_unmatched"
    lookup["_unmatched"] = sorted(unmatched)

    # 5. Guardar el archivo JSON resultante
    output_path = Path("data/sicetac_to_rndc.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(lookup, f, indent=2, ensure_ascii=False)

    # Mostrar reporte
    total = len(sicetac_entries)
    matched = total - len(unmatched)
    pct = (matched / total) * 100 if total > 0 else 0

    print("\n📊 --- REPORTE DE RESOLUCIÓN ---")
    print(f"✅ Total emparejados exitosamente: {matched} / {total} ({pct:.2f}%)")
    print(f"❌ Sin coincidencia (agregados a '_unmatched'): {len(unmatched)}")
    print(f"💾 Lookup table guardado en: {output_path}")

    if unmatched:
        print("\n⚠️ Primeros 10 casos sin match para inspección:")
        for u in unmatched[:10]:
            print(f"  - {u}")


if __name__ == "__main__":
    main()
