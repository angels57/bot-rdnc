import streamlit as st


def init_state():
    """Inicializa todos los estados necesarios en la sesión de Streamlit."""
    if "message" not in st.session_state:
        st.session_state.message = []
    if "loading" not in st.session_state:
        st.session_state.loading = False
    if "resultado" not in st.session_state:
        st.session_state.resultado = None


def set_loading(loading: bool):
    """Establece el estado de carga de la aplicación."""
    st.session_state.loading = loading


def is_loading() -> bool:
    """Verifica si la aplicación está en estado de carga."""
    return st.session_state.get("loading", False)


def set_resultado(resultado: dict | None):
    """Guarda el resultado de la cotización en el estado."""
    st.session_state.resultado = resultado


def get_resultado() -> dict | None:
    """Obtiene el resultado actual de la cotización."""
    return st.session_state.get("resultado", None)


def add_message(role: str, content: str, dataframe=None):
    """Agrega un mensaje al historial (si se usa en chat)."""
    msg = {"role": role, "content": content}
    if dataframe is not None:
        msg["dataframe"] = dataframe
    st.session_state.message.append(msg)
