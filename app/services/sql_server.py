from __future__ import annotations

import os
import unicodedata

from typing import Any
from urllib.parse import parse_qs, unquote_plus, urlparse

import polars as pl

from app.config.settings import settings
from app.core import get_app_logger

logger = get_app_logger("sql_server")


def normalizar_texto(valor: str | None) -> str:
    if not valor:
        return ""

    valor = valor.strip().upper()
    valor = valor.replace("\r", "").replace("\n", "")

    valor = "".join(
        c
        for c in unicodedata.normalize("NFD", valor)
        if unicodedata.category(c) != "Mn"
    )

    if "-" in valor:
        valor = valor.split("-", 1)[0].strip()

    return valor


def _mask_connection_string(conn_string: str) -> str:
    masked_parts = []
    for part in conn_string.split(";"):
        if part.upper().startswith("PWD="):
            masked_parts.append("PWD=***")
        elif part.upper().startswith("UID="):
            masked_parts.append("UID=***")
        else:
            masked_parts.append(part)
    return ";".join(masked_parts)


def _build_connection_string() -> str | None:
    conn_string = os.getenv("SQLSERVER_CONN")
    if conn_string:
        logger.info("Conexión SQL Server configurada usando SQLSERVER_CONN.")
        logger.debug(
            "Cadena de conexión SQLSERVER_CONN: %s",
            _mask_connection_string(conn_string),
        )
        return conn_string

    db_url = settings.DATABASE_URL or os.getenv("DATABASE_URL", "")
    if db_url:
        logger.info("Conexión SQL Server configurada usando DATABASE_URL.")
        logger.debug("DATABASE_URL: %s", db_url)
        return _build_connection_string_from_url(db_url)

    server = os.getenv("SQLSERVER_SERVER")
    database = os.getenv("SQLSERVER_DATABASE")
    if not server or not database:
        logger.warning(
            "No está configurada la conexión a SQL Server. "
            "Usa SQLSERVER_CONN, DATABASE_URL o SQLSERVER_SERVER/SQLSERVER_DATABASE."
        )
        return None

    driver = os.getenv("SQLSERVER_DRIVER", "{ODBC Driver 17 for SQL Server}")
    user = os.getenv("SQLSERVER_USER")
    password = os.getenv("SQLSERVER_PASSWORD")

    if user and password:
        connection_string = (
            f"DRIVER={driver};SERVER={server};DATABASE={database};"
            f"UID={user};PWD={password};"
        )
        logger.info(
            "Conexión SQL Server configurada desde variables de entorno con usuario/contraseña."
        )
        logger.debug(
            "Cadena de conexión construida: %s",
            _mask_connection_string(connection_string),
        )
        return connection_string

    connection_string = (
        f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
    )
    logger.info(
        "Conexión SQL Server configurada desde variables de entorno usando Trusted Connection."
    )
    logger.debug(
        "Cadena de conexión construida: %s", _mask_connection_string(connection_string)
    )
    return connection_string


def _build_connection_string_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in ("mssql", "mssql+pyodbc", "sqlserver", "sqlserver+pyodbc"):
        logger.warning(
            "DATABASE_URL tiene un esquema no soportado para SQL Server: %s",
            parsed.scheme,
        )
        return None

    database = parsed.path.lstrip("/")
    host = parsed.hostname
    if not host or not database:
        logger.warning("DATABASE_URL no contiene host o base de datos válidos.")
        return None

    server = host
    if parsed.port:
        server = f"{host},{parsed.port}"

    query_params = parse_qs(parsed.query)
    driver = query_params.get(
        "driver", [os.getenv("SQLSERVER_DRIVER", "{ODBC Driver 17 for SQL Server}")]
    )[0]
    driver = unquote_plus(driver)

    connection_fields = {
        "DRIVER": driver,
        "SERVER": server,
        "DATABASE": database,
    }

    if parsed.username and parsed.password:
        connection_fields["UID"] = unquote_plus(parsed.username)
        connection_fields["PWD"] = unquote_plus(parsed.password)
        auth_type = "user/password"
    else:
        connection_fields["Trusted_Connection"] = "yes"
        auth_type = "trusted_connection"

    logger.debug(
        "DATABASE_URL parseado: server=%s, database=%s, driver=%s, auth=%s, extra_params=%s",
        server,
        database,
        driver,
        auth_type,
        {k: v for k, v in query_params.items() if k.lower() != "driver"},
    )

    for key, values in query_params.items():
        if not values:
            continue
        if key.lower() == "driver":
            continue
        value = unquote_plus(values[0])
        connection_fields[key.upper()] = value

    return ";".join(f"{k}={v}" for k, v in connection_fields.items()) + ";"


def _get_pyodbc_connection() -> Any | None:
    try:
        import pyodbc
    except ImportError:
        logger.warning(
            "pyodbc no está instalado. La consulta SQL Server no estará disponible."
        )
        return None

    conn_string = _build_connection_string()
    if not conn_string:
        return None

    try:
        logger.info("Intentando conectar a SQL Server.")
        logger.debug(
            "Cadena de conexión final (oculta): %s",
            _mask_connection_string(conn_string),
        )
        connection = pyodbc.connect(conn_string, autocommit=True)
        logger.info("Conexión a SQL Server establecida correctamente.")
        return connection
    except Exception as exc:
        logger.error(f"Error al conectar con SQL Server: {exc!s}")
        return None


def consultar_ruta_sql_server(
    configuracion: str | None,
    destino: str | None,
    origen: str | None,
) -> pl.DataFrame:

    origen = normalizar_texto(origen)
    destino = normalizar_texto(destino)

    if not origen or not destino or not configuracion:
        logger.warning(
            "Faltan parámetros para consultar SQL Server: origen, destino o configuracion."
        )
        return pl.DataFrame()

    connection = _get_pyodbc_connection()
    if connection is None:
        return pl.DataFrame()

    query = """
        SELECT TOP(1)
            ENPD.Fecha_Crea AS FECHA,
            ORIG.Nombre AS ORIGEN,
            DEST.Nombre AS DESTINO,
            ENPD.Valor_Flete_Transportador,
            ENPD.Valor_Flete_Cliente,
            CONCAT(COVE.Campo5, CORE.Campo2) AS CONFIGURACION
        FROM Detalle_Despacho_Orden_Servicios ENPD
        INNER JOIN Rutas RUTA ON ENPD.RUTA_Codigo = RUTA.Codigo
        INNER JOIN Ciudades ORIG ON RUTA.CIUD_Codigo_Origen = ORIG.Codigo
        INNER JOIN Ciudades DEST ON RUTA.CIUD_Codigo_Destino = DEST.Codigo
        INNER JOIN Vehiculos VEHI ON ENPD.VEHI_Codigo = VEHI.Codigo
        INNER JOIN Valor_Catalogos COVE ON VEHI.CATA_TIVE_Codigo = COVE.Codigo
        LEFT JOIN Semirremolques REMO ON VEHI.SEMI_Codigo = REMO.Codigo
        LEFT JOIN Valor_Catalogos CORE ON REMO.CATA_TISE_Codigo = CORE.Codigo
        WHERE ORIG.Nombre LIKE UPPER(?)
          AND DEST.Nombre LIKE UPPER(?)
          AND CONCAT(COVE.Campo5, CORE.Campo2) = ?
        ORDER BY ENPD.Fecha_Crea DESC;
    """

    try:
        cursor = connection.cursor()
        cursor.execute(query, f"%{origen}%", f"%{destino}%", configuracion)
        rows = cursor.fetchall()

        if not rows:
            return pl.DataFrame()

        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        return pl.DataFrame(data)

    except Exception as exc:
        logger.error(
            "Error ejecutando la consulta SQL Server: %s | Params: %s",
            exc,
            (origen, destino, configuracion),
        )
        return pl.DataFrame()
    finally:
        try:
            connection.close()
        except Exception:
            pass
