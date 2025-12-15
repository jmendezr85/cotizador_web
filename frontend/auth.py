import streamlit as st
import time

# ==========================================
# 🔐 CONFIGURACIÓN DE USUARIOS
# ==========================================
USUARIOS = {
    "admin": "admin123",
    "ramon": "virtual2026",
    "ventas": "cotizar"
}

def verificar():
    """Valida usuario y contraseña y setea el estado persistente"""
    user = st.session_state.auth_user
    pwd = st.session_state.auth_pwd
    
    if user in USUARIOS and USUARIOS[user] == pwd:
        # 🔥 Esto asegura que el estado sea True
        st.session_state.esta_logueado = True 
        st.success("✅ Acceso concedido")
        # Forzamos un rerun rápido para salir del formulario de login
        time.sleep(0.1) 
        st.rerun() 
    else:
        st.error("❌ Usuario o contraseña incorrectos")

def mostrar_login():
    """Muestra la interfaz de Login y maneja el flujo de acceso"""
    
    # 1. Inicializar estado (Esto intenta mantener el estado tras el refresh)
    if 'esta_logueado' not in st.session_state:
        st.session_state.esta_logueado = False

    # 2. Control de flujo: Si está logueado, sale de la función y permite que la APP corra.
    if st.session_state.esta_logueado:
        return True 

    # 3. Mostrar Login si no está logueado
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("""
                <div style="text-align:center; margin-bottom:20px;">
                    <div style="font-size:3rem; margin-bottom:10px;">🔒</div>
                    <h2 style="margin:0; font-weight:700;">Acceso Restringido</h2>
                    <p style="font-size:0.9rem; opacity:0.7;">Sistema de Cotización Profesional</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.text_input("Usuario", key="auth_user")
            st.text_input("Contraseña", type="password", key="auth_pwd")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Iniciar Sesión", type="primary", use_container_width=True):
                verificar()

    # 🛑 ESTO DETIENE LA EJECUCIÓN SI NO HAY ACCESO
    st.stop() 
    
def sidebar_logout():
    """Muestra el botón de cerrar sesión en el sidebar"""
    if st.session_state.get('esta_logueado', False):
        if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
            st.session_state.esta_logueado = False
            st.rerun()