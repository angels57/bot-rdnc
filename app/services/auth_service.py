"""Servicio de autenticación contra la tabla usuarios con bcrypt."""

import bcrypt
from app.core import get_app_logger
from app.db.session import get_session_factory
from app.models.usuario import Usuario

logger = get_app_logger("auth_service")

ROLES_PERMITIDOS = {"ADMIN"}


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
        usuario = session.query(Usuario).filter(
            Usuario.usr_nick == nick.strip()
        ).first()

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
        return {
            "nick": usuario.usr_nick,
            "nombres": usuario.usr_nombres,
            "apellidos": usuario.usr_apellidos,
            "role": usuario.usr_role,
        }
    except Exception as e:
        logger.error(f"Error en autenticacion: {e}")
        return None
    finally:
        session.close()
