"""Servicio de autenticación contra la tabla usuarios con bcrypt."""

import base64
import hashlib
import hmac
import json
import time

import bcrypt

from app.config.settings import settings
from app.core import get_app_logger
from app.db.session import get_session_factory
from app.models.usuario import Usuario
from app.db.crud import actualizar_ultima_conexion

logger = get_app_logger("auth_service")

ROLES_PERMITIDOS = {"ADMIN", "FLETES", "COMERCIAL"}


def autenticar(nick: str, password: str) -> dict | None:
    """Autentica un usuario contra la DB con bcrypt.

    Args:
        nick: Nombre de usuario (usr_nick)
        password: Contraseña en texto plano

    Returns:
        dict con datos del usuario si auth OK y rol permitido,
        None en caso contrario.
    """
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        usuario = (
            session.query(Usuario).filter(Usuario.usr_nick == nick.strip()).first()
        )

        if not usuario:
            logger.warning(f"Usuario no encontrado: {nick}")
            return None

        if usuario.usr_role not in ROLES_PERMITIDOS:
            logger.warning(
                f"Usuario {nick} tiene rol '{usuario.usr_role}' no permitido"
            )
            return None

        if not bcrypt.checkpw(
            password.encode("utf-8"),
            usuario.usr_password.encode("utf-8"),
        ):
            logger.warning(f"Password incorrecto para usuario: {nick}")
            return None

        logger.info(f"Usuario autenticado: {nick} (rol: {usuario.usr_role})")
        actualizar_ultima_conexion(usuario.usr_nick)
        return {
            "nick": usuario.usr_nick,
            "nombres": usuario.usr_nombres,
            "apellidos": usuario.usr_apellidos,
            "role": usuario.usr_role,
            "agencia": usuario.usr_agencia,
        }
    except Exception as e:
        logger.error(f"Error en autenticacion: {e}")
        return None
    finally:
        session.close()


SECRET_KEY = settings.COOKIE_SECRET


def create_token(nick: str, role: str, expires_in: int = 3600) -> str:
    """Crea un token HMAC firmado para cookie de sesión."""
    payload = {
        "nick": nick,
        "role": role,
        "exp": int(time.time()) + expires_in,
    }
    payload_json = json.dumps(payload, separators=(",", ":"))
    sig = hmac.new(
        SECRET_KEY.encode(), payload_json.encode(), hashlib.sha256
    ).hexdigest()
    token_data = f"{payload_json}.{sig}"
    return base64.urlsafe_b64encode(token_data.encode()).decode()


def verify_token(token: str) -> dict | None:
    """Verifica un token HMAC. Retorna payload si válido, None si no."""
    try:
        token_data = base64.urlsafe_b64decode(token.encode()).decode()
        payload_json, sig = token_data.rsplit(".", 1)
        expected_sig = hmac.new(
            SECRET_KEY.encode(), payload_json.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload = json.loads(payload_json)
        if int(time.time()) > payload["exp"]:
            return None
        return payload
    except Exception:
        return None
