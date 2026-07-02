import secrets
import string
import unicodedata

import bcrypt

from app.core import get_app_logger
from app.db.session import get_engine, get_session_factory
from app.models.flete import Base, FleteRegistro
from app.models.usuario import Usuario

logger = get_app_logger("db_crud")


def _generar_nick(nombres: str, apellidos: str, session) -> str:
    """Genera un nick único: primera letra del nombre + apellido."""
    def limpiar(texto: str) -> str:
        texto = unicodedata.normalize("NFKD", texto.lower())
        texto = texto.encode("ascii", "ignore").decode("ascii")
        return texto.strip()
    
    base = limpiar(nombres)[0] + limpiar(apellidos).replace(" ", "")
    
    nick = base
    contador = 1
    while session.query(Usuario).filter(Usuario.usr_nick == nick).first():
        nick = f"{base}{contador}"
        contador += 1
    return nick


def init_db() -> bool:
    """Crea las tablas si no existen."""
    try:
        engine = get_engine()
        Base.metadata.create_all(engine)
        logger.info("Tablas de base de datos inicializadas")
        return True
    except Exception as e:
        logger.error(f"Error creando tablas: {e}")
        return False


def guardar_flete(
    cod_vehiculo: str,
    origen: str,
    destino: str,
    tarifa: int,
    tipo_flete: str,
    fuente: str,
    agencia: str,
) -> FleteRegistro | None:
    """Guarda un registro de flete en la base de datos."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        db_flete = FleteRegistro(
            cod_vehiculo=cod_vehiculo,
            origen=origen,
            destino=destino,
            tarifa=tarifa,
            tipo_flete=tipo_flete,
            fuente=fuente,
            agencia=agencia,
        )
        session.add(db_flete)
        session.commit()
        session.refresh(db_flete)
        logger.info(f"Flete registrado: {origen} → {destino} (${tarifa:,.0f})")
        return db_flete
    except Exception as e:
        session.rollback()
        logger.error(f"Error guardando flete: {e}")
        return None
    finally:
        session.close()


def obtener_ultimos_registros(limite: int = 10) -> list[FleteRegistro]:
    """Obtiene los últimos registros únicos por COD+origen+destino."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        registros = (
            session.query(FleteRegistro)
            .order_by(FleteRegistro.creado_en.desc())
            .limit(50)
            .all()
        )
        vistos = set()
        unicos = []
        for r in registros:
            key = (r.cod_vehiculo, r.origen, r.destino)
            if key not in vistos:
                vistos.add(key)
                unicos.append(r)
                if len(unicos) >= limite:
                    break
        return unicos
    except Exception as e:
        logger.error(f"Error obteniendo últimos registros: {e}")
        return []
    finally:
        session.close()


def crear_usuario(
    nombres: str,
    apellidos: str,
    role: str,
) -> dict | None:
    """Crea un usuario con nick y contraseña auto-generados.

    Returns:
        dict con nick y password si se creó OK,
        None si falló.
    """
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        nick = _generar_nick(nombres, apellidos, session)

        alfabeto = string.ascii_letters + string.digits
        password_plano = "".join(secrets.choice(alfabeto) for _ in range(10))

        hashed = bcrypt.hashpw(
            password_plano.encode("utf-8"),
            bcrypt.gensalt(rounds=10),
        ).decode("utf-8")

        nuevo = Usuario(
            usr_nick=nick,
            usr_nombres=nombres.strip(),
            usr_apellidos=apellidos.strip(),
            usr_password=hashed,
            usr_role=role,
        )
        session.add(nuevo)
        session.commit()
        logger.info(f"Usuario creado: {nick} (rol: {role})")
        return {"nick": nick, "password": password_plano}
    except Exception as e:
        session.rollback()
        logger.error(f"Error creando usuario: {e}")
        return None
    finally:
        session.close()
