import streamlit as st
import os
import base64
import auth
from PIL import Image
import requests
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
import io
import base64
import lienzo
import simulador
import numpy as np
from scipy.interpolate import make_interp_spline # Para suavizar la curva

# ==========================================
# 🎨 1. CONFIGURACIÓN VISUAL (UX/UI)
# ==========================================
# Gestión de Estado Inicial
if 'conf_dark_mode' not in st.session_state: st.session_state.conf_dark_mode = False
if 'historial' not in st.session_state: st.session_state.historial = []
if 'resultados' not in st.session_state: st.session_state.resultados = None
if 'conf_auto_calc' not in st.session_state: st.session_state.conf_auto_calc = False
if 'active_tab' not in st.session_state: st.session_state.active_tab = "Plotter Inkjet"
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0

# Colores Dinámicos
if st.session_state.conf_dark_mode:
    # --- MODO OSCURO (PREMIUM / ELEGANTE) ---
    C_BG = "#0D1117"        # Fondo: Azul grisáceo muy oscuro (Estilo GitHub Dark)
    C_CARD = "#161B22"      # Tarjetas: Un tono más claro que el fondo
    C_TEXT = "#F0F6FC"      # Texto: Blanco hueso (no quema la vista)
    C_SUBTEXT = "#D0D7DE"   # Subtexto: Gris acero
    C_BORDER = "#30363D"    # Bordes: Sutiles y elegantes
    C_UPLOAD = "#0D1117"    # Fondo del área de carga
    
    # Colores de Acento (Saturación balanceada)
    C_PRIMARY = "#F778BA"   # Rosa/Coral moderno (Destaca sin ser agresivo) 
    # O SI PREFIERES MANTENER EL NARANJA, USA ESTE: C_PRIMARY = "#FF8C42" 
    
    C_SUCCESS = "#238636"   # Verde Bosque (Profesional y serio)
    C_WARNING = "#D29922"   # Ocre/Ambar (Mejor que el amarillo limón)
    RED = "#DA3633"         # Rojo ladrillo
    
else:
    # --- MODO CLARO (LIMPIO / MINIMALISTA) ---
    C_BG = "#F3F4F6"        # Fondo: Gris muy suave (casi blanco)
    C_CARD = "#FFFFFF"      # Tarjetas: Blanco puro
    C_TEXT = "#1F2937"      # Texto: Gris muy oscuro (mejor que negro puro)
    C_SUBTEXT = "#6B7280"   # Subtexto: Gris medio
    C_BORDER = "#E5E7EB"    # Bordes: Muy suaves
    C_UPLOAD = "#F9FAFB"    # Fondo carga
    
    # Colores de Acento
    C_PRIMARY = "#EA580C"   # Naranja Quemado (Corporativo)
    C_SUCCESS = "#059669"   # Esmeralda
    C_WARNING = "#D97706"   # Ambar oscuro
    RED = "#DC2626"         # Rojo estándar
    
C_NEUTRAL = "#9CA3AF"

# ==========================================
# 🔒 0.5 SEGURIDAD (MÓDULO NUEVO)
# ==========================================

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ruta_logo = os.path.join(current_dir, "logo_virtual.png")
    favicon = Image.open(ruta_logo)
except:
    favicon = "🖨️ "

st.set_page_config(page_title="Centro de Cotización", layout="wide", page_icon=favicon)
auth.mostrar_login()

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Poppins', sans-serif;
        color: {C_TEXT};
        background-color: {C_BG};
    }}
    .block-container {{ padding-top: 1.5rem; padding-bottom: 5rem; }}
    header, footer, #MainMenu {{ visibility: hidden; }}
    .stApp {{ background-color: {C_BG}; margin-top: -50px; }}

    /* KPI CARDS (DISEÑO UNIFICADO) */
    .kpi-card {{
        background-color: {C_CARD};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        border-left: 5px solid {C_SUCCESS};
        height: 160px; /* Altura fija para alineación perfecta */
        display: flex;
        flex-direction: column;
        justify-content: center;
        position: relative;
        border: 1px solid {C_BORDER};
        transition: transform 0.2s;
    }}
    .kpi-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 15px rgba(0,0,0,0.05); }}
    
    .kpi-title {{ 
        font-size: 0.8rem; 
        color: {C_SUBTEXT}; 
        text-transform: uppercase; 
        letter-spacing: 1px; 
        font-weight: 600;
        margin-bottom: 5px;
    }}
    .kpi-value {{ 
        font-size: 2.2rem; 
        font-weight: 700; 
        color: {C_TEXT}; 
        line-height: 1.2;
    }}
    .kpi-note {{ font-size: 0.75rem; color: {C_SUBTEXT}; margin-top: 5px; }}

    /* CONTENEDOR DE GRÁFICA INTEGRADA */
    .graph-container {{
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
    }}
    .graph-img {{
        width: 100%;
        height: 80px;
        object-fit: cover;
        opacity: 0.9;
        margin-bottom: -10px; /* Ajuste fino */
        mask-image: linear-gradient(to bottom, black 80%, transparent 100%);
    }}

    /* TARJETAS DE CONTENIDO */
    .card-box {{
        background-color: {C_CARD};
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
        border: 1px solid {C_BORDER};
        height: 100%;
    }}

    /* BOTONES */
    button[kind="primary"] {{
        background: linear-gradient(135deg, {C_PRIMARY} 0%, #E63E15 100%);
        color: white !important;
        border: none;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(252, 74, 26, 0.3);
        transition: 0.3s;
    }}
    button[kind="primary"]:hover {{ transform: translateY(-2px); box-shadow: 0 6px 15px rgba(252, 74, 26, 0.5); }}

    /* BOTÓN SECUNDARIO (RESET) - AHORA AMARILLO/WARNING */
    button[kind="secondary"] {{
        background: transparent; 
        color: {C_WARNING}; /* COLOR AMARILLO/WARNING */
        border: 2px solid {C_WARNING}; /* BORDE AMARILLO/WARNING */
        border-radius: 10px; 
        font-weight: 500;
    }}
    button[kind="secondary"]:hover {{ 
        border-color: {C_WARNING}; 
        color: {RED}; 
        background: rgba(247, 183, 51, 0.1); /* Hover suave */
    }}

    /* UPLOAD */
    .upload-zone {{
        border: 2px dashed {C_BORDER}; background: {C_UPLOAD}; border-radius: 12px; padding: 2rem; text-align: center;
    }}
    .upload-zone:hover {{ border-color: {C_SUCCESS}; }}
    
    /* NAV BASE */
    div[data-testid="column"] button.nav-btn {{ background: transparent; border: none; color: {C_SUBTEXT}; font-weight: 600; }}
    div.row-widget.stButton > button {{ background: transparent; border: none; color: {C_SUBTEXT}; box-shadow: none; }}
    div.row-widget.stButton > button:hover {{ color: {C_PRIMARY}; background: rgba(252, 74, 26, 0.05); }}

    /* Ajuste para Popover */
    div[data-testid="stPopover"] button {{ border: 1px solid {C_BORDER}; color: {C_TEXT}; }}

    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. GENERADOR DE GRÁFICAS (MATPLOTLIB -> IMAGE)
# ==========================================
def generar_sparkline_img(datos):
    """Genera una imagen PNG transparente de la curva de tendencia"""
    if not datos: return ""
    
    # Datos
    y = np.array(datos)
    x = np.arange(len(y))
    
    # Suavizado (Spline)
    if len(y) > 2:
        x_new = np.linspace(x.min(), x.max(), 300)
        try:
            spl = make_interp_spline(x, y, k=3)
            y_new = spl(x_new)
            # Evitar valores negativos por la interpolación
            y_new[y_new < 0] = 0
        except:
            x_new, y_new = x, y
    else:
        x_new, y_new = x, y

    # Configuración de Matplotlib
    plt.style.use('dark_background' if st.session_state.conf_dark_mode else 'default')
    fig, ax = plt.subplots(figsize=(5, 2))
    
    # Color de la línea según tema
    line_color = C_WARNING 
    
    # Dibujar
    ax.plot(x_new, y_new, color=line_color, linewidth=2.5)
    ax.fill_between(x_new, y_new, color=line_color, alpha=0.2)
    
    # Limpiar ejes
    ax.axis('off')
    fig.patch.set_alpha(0.0) # Fondo transparente figura
    ax.patch.set_alpha(0.0)  # Fondo transparente ejes
    
    # Guardar a buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, transparent=True)
    plt.close(fig)
    
    # Convertir a Base64
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"data:image/png;base64,{data}"

# ==========================================
# 4. FUNCIONES LÓGICAS
# ==========================================
def switch_tab(name): st.session_state.active_tab = name
def reset_carga():
    st.session_state.uploader_key += 1
    st.session_state.resultados = None
def borrar_historial(): st.session_state.historial = []

def calcular_cotizacion(files, modo_etiqueta):
    if not files: return
    
    # 1. DEFINIR LA URL DE LA API (INTELIGENTE)
    # Intenta buscar una variable de entorno llamada 'BACKEND_URL'.
    # Si no la encuentra (ej. en tu PC local), usa 'http://127.0.0.1:8000' por defecto.
    # Cuando lo subas a Hugging Face, configurarás esa variable con la URL de Render.
    api_url = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
    
    # Aseguramos que la URL no termine en barra '/' para evitar errores al concatenar
    api_url = api_url.rstrip("/")

    with st.spinner("Analizando geometría..."):
        try:
            mapa = {"Automático (Real)":"AUTO", "Todo Pliego (100x70)":"PLIEGO", "Todo 1/2 Pliego":"MEDIO", "Todo 1/4 Pliego":"CUARTO"}
            payload = [("files", (f.name, f.getvalue(), "application/pdf")) for f in files]
            
            # 2. USAR LA VARIABLE api_url
            endpoint = f"{api_url}/cotizar_lote/"
            
            res = requests.post(endpoint, files=payload, data={"modo": mapa[modo_etiqueta]})
            
            if res.status_code == 200:
                st.session_state.resultados = res.json()
                st.session_state.historial.insert(0, {
                    "hora": datetime.now().strftime("%H:%M"),
                    "data": st.session_state.resultados,
                    "modo": modo_etiqueta
                })
            else: 
                st.error(f"Error Backend ({res.status_code}): {res.text}")
                
        except requests.exceptions.ConnectionError:
            st.error(f"❌ No se pudo conectar con el servidor Backend en: {api_url}")
            st.info("Si estás en local, verifica que el backend esté corriendo. Si estás en la nube, verifica la URL en los Secrets.")
        except Exception as e: 
            st.error(f"Error inesperado: {e}")

# Generador PDF
def generar_pdf(items, total_global):
    class PDF(FPDF):
        def header(self):
            self.set_fill_color(74, 189, 172)
            self.rect(0, 0, 210, 6, 'F')
            self.ln(12)
            self.set_font('Helvetica', 'B', 16)
            self.cell(0, 10, 'COTIZACION DE SERVICIO', 0, 1, 'C')
            self.ln(5)
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1)
    
    pdf.set_fill_color(247, 183, 51)
    pdf.set_font("Helvetica", 'B', 9)
    headers = ["Archivo", "Medidas", "Tinta", "Detalle", "Precio"]
    widths = [75, 25, 20, 45, 25]
    for i, h in enumerate(headers): pdf.cell(widths[i], 10, h, 1, 0, 'C', True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for item in items:
        nom = item['archivo'][:35].encode('latin-1','replace').decode('latin-1')
        det = item['detalle'][:25].encode('latin-1','replace').decode('latin-1')
        pdf.cell(widths[0], 10, nom, 1)
        pdf.cell(widths[1], 10, item['dimensiones'], 1, 0, 'C')
        pdf.cell(widths[2], 10, item['cobertura'], 1, 0, 'C')
        pdf.cell(widths[3], 10, det, 1, 0, 'C')
        pdf.cell(widths[4], 10, f"${item['precio']:,}", 1, 1, 'R')
        pdf.ln()
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"TOTAL: ${total_global:,.0f}", 0, 1, 'R')
    return pdf.output(dest='S').encode('latin-1')

# --- PREPARACIÓN DEL LOGO PARA HTML ---
def obtener_imagen_base64(ruta):
    with open(ruta, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

# Definimos la ruta y convertimos
ruta_img_header = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_virtual.png")
try:
    img_b64 = obtener_imagen_base64(ruta_img_header)
    # Creamos la etiqueta HTML de la imagen
    logo_html = f'<img src="data:image/png;base64,{img_b64}" style="width:50px; height:50px; object-fit:contain;">'
except:
    # Si falla, usamos el emoji de respaldo
    logo_html = '<div style="font-size:2rem;">🖨️</div>'
# --------------------------------------

# ==========================================
# 5. HEADER
# ==========================================
with st.container():
    st.write("") 
    c_logo, c_nav, c_conf = st.columns([2.5, 4, 1])
    
    with c_logo:
        # CORRECCIÓN: El HTML está pegado a la izquierda para evitar errores de indentación
        st.markdown(f"""
<div style="display:flex; align-items:center; gap:15px;">
    <div style="display:flex; align-items:center; justify-content:center;">
        {logo_html}
    </div>
    <div style="line-height: 1.2;">
        <h2 style="margin:0; font-size:1.4rem; color:{C_SUCCESS}; font-weight:700; letter-spacing:-0.5px;">Centro de Cotización</h2>
        <span style="font-size:0.75rem; color:{C_SUBTEXT}; letter-spacing:1px; text-transform:uppercase;">Panel Profesional</span>
    </div>
</div>
""", unsafe_allow_html=True)
        
    with c_nav:
        n1, n2, n3 = st.columns(3)
        
        # --- Plotter Inkjet (Color ACTIVO: PRIMARY/Naranja) ---
        with n1:
            if st.button("Plotter Inkjet"): switch_tab("Plotter Inkjet")
            if st.session_state.active_tab == "Plotter Inkjet": 
                # Borde inferior Naranja, Texto Naranja
                st.markdown(f'<style>div[data-testid="column"]:nth-of-type(2) button{{border-bottom: 3px solid {C_PRIMARY} !important; color: {C_PRIMARY} !important; font-weight: 700 !important;}}</style>', unsafe_allow_html=True)
            
        # --- Corte Láser (Color ACTIVO: SUCCESS/Turquesa) ---
        with n2:
            # 🚨 CAMBIO CLAVE AQUÍ:
            # Antes decía "Corte Láser", ahora debe decir "Lienzo Imagen" en ambos lugares
            if st.button("Lienzo Imagen"): switch_tab("Lienzo Imagen")
            
            if st.session_state.active_tab == "Lienzo Imagen": 
                 # Borde inferior Turquesa, Texto Turquesa
                 st.markdown(f'<style>div[data-testid="column"]:nth-of-type(3) button{{border-bottom: 3px solid {C_SUCCESS} !important; color: {C_SUCCESS} !important; font-weight: 700 !important;}}</style>', unsafe_allow_html=True)
        # --- Impresión Digital (Color ACTIVO: WARNING/Amarillo) ---
        with n3: # Asumiendo que n3 es la variable para la columna
            # Botón de la pestaña
            if st.button("Simulador de Impresión"): 
                switch_tab("Simulador de Impresión")
                
            # Aplicar el estilo de activo si esta es la pestaña seleccionada
            if st.session_state.active_tab == "Simulador de Impresión": 
                # CRÍTICO: El CSS aplica el estilo de borde al botón que está en la cuarta columna (nth-of-type(4))
                st.markdown(f'<style>div[data-testid="column"]:nth-of-type(4) button{{border-bottom: 3px solid {C_WARNING} !important; color: {C_WARNING} !important; font-weight: 700 !important;}}</style>', unsafe_allow_html=True)


    with c_conf:
        with st.popover("⚙️ Ajustes", use_container_width=True):
            st.caption("VISUAL")
            mode = st.toggle("Modo Oscuro", value=st.session_state.conf_dark_mode)
            if mode != st.session_state.conf_dark_mode:
                st.session_state.conf_dark_mode = mode
                st.rerun()
            st.caption("SISTEMA")
            auto = st.toggle("Cálculo Automático", value=st.session_state.conf_auto_calc)
            if auto != st.session_state.conf_auto_calc:
                st.session_state.conf_auto_calc = auto
                st.rerun()
            st.divider()
            if st.button("Cerrar Sesión", type="primary", use_container_width=True):
                st.session_state.esta_logueado = False
                st.rerun()

st.markdown(f'<div style="height:3px; background:linear-gradient(90deg, {C_SUCCESS} 0%, {C_WARNING} 50%, {C_PRIMARY} 100%); opacity:0.6; margin-bottom:1.5rem;"></div>', unsafe_allow_html=True)

# ==========================================
# 6. CONTENIDO PRINCIPAL
# ==========================================

# 🚨 ÚNICO BLOQUE DE CONTENIDO DEFINIDO: Plotter Inkjet 🚨
if st.session_state.active_tab == "Plotter Inkjet":
    
    # --- DASHBOARD DE KPI ---
    total_dinero = sum(item['data']['total_global'] for item in st.session_state.historial)
    total_planos = sum(len(item['data']['items']) for item in st.session_state.historial)
    
    # Preparamos datos para la gráfica (Invertimos para orden cronológico)
    hist_values = [h['data']['total_global'] for h in st.session_state.historial[:10][::-1]]
    if not hist_values: hist_values = [0, 0, 0] # Datos dummy para visual
    img_chart = generar_sparkline_img(hist_values)

    kp1, kp2, kp3 = st.columns([1, 1, 1.5])
    
    # 1. PLANOS HOY
    with kp1:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {C_PRIMARY};">
            <div>
                <div class="kpi-title">Planos Procesados</div>
                <div class="kpi-value">{total_planos}</div>
                <div class="kpi-note">Sesión actual</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    # 2. TOTAL COTIZADO
    with kp2:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {C_SUCCESS};">
            <div>
                <div class="kpi-title">Venta Potencial</div>
                <div class="kpi-value">${total_dinero:,.0f}</div>
                <div class="kpi-note">Acumulado hoy</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    # 3. GRÁFICA INCRUSTADA (SOLUCIÓN UX/UI DEFINITIVA)
    with kp3:
        # Aquí insertamos la imagen directamente en el HTML de la tarjeta
        # Esto garantiza que la gráfica quede DENTRO del cuadro
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {C_WARNING}; justify-content: space-between; overflow: hidden; padding-bottom: 0;">
            <div style="padding: 0 10px;">
                <div class="kpi-title" style="margin-top: 20px;">Tendencia de Ventas (Últimos 10)</div>
            </div>
            <div class="graph-container">
                <img src="{img_chart}" class="graph-img">
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ÁREA DE TRABAJO ---
    col_main_1, col_main_2 = st.columns([0.65, 0.35], gap="large")
    
    # IZQUIERDA
    with col_main_1:
        #st.markdown('<div class="card-box">', unsafe_allow_html=True)
        st.markdown(f"""
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:15px;">
                <span style="font-size:1.4rem; color:{C_WARNING};">📂</span>
                <h3 style="margin:0; font-size:1.2rem; color:{C_TEXT};">Carga de Planos</h3>
            </div>
        """, unsafe_allow_html=True)
        
        #st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:2.5rem; color:{C_BORDER}; margin-bottom:10px;'>☁️</div>", unsafe_allow_html=True)
        st.markdown(f"<strong style='color:{C_TEXT};'>Arrastra y suelta tus archivos aquí</strong>", unsafe_allow_html=True)
        
        files = st.file_uploader(" ", type="pdf", accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}", label_visibility="collapsed")
        st.markdown('</div></div>', unsafe_allow_html=True)

    # DERECHA
    with col_main_2:
        #st.markdown('<div class="card-box">', unsafe_allow_html=True)
        st.markdown(f"""
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:20px;">
                <span style="font-size:1.4rem; color:{C_SUCCESS};">⚙️</span>
                <h3 style="margin:0; font-size:1.2rem; color:{C_TEXT};">Ajustes</h3>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**Modo de Cobro**")
        modo = st.radio("Criterio:", ["Automático (Real)", "Todo Pliego (100x70)", "Todo 1/2 Pliego", "Todo 1/4 Pliego"], label_visibility="collapsed")
        
        st.divider()
        
        c1, c2 = st.columns([1, 1.5])
        with c1:
            if st.button("🔄 RESET", type="secondary", use_container_width=True):
                reset_carga()
                st.rerun()
        
        with c2:
            if files:
                # FIX: Solo calcula automáticamente si la opción está activa Y no hay resultados en pantalla
                if st.session_state.conf_auto_calc and st.session_state.resultados is None:
                    st.caption("⚡ Auto-calculando...")
                    calcular_cotizacion(files, modo)
                else:
                    if st.button("🚀 CALCULAR", type="primary", use_container_width=True):
                        calcular_cotizacion(files, modo)
            else:
                 st.button("🚀 CALCULAR", type="primary", disabled=True, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # --- RESULTADOS ---
    if st.session_state.resultados:
        res = st.session_state.resultados
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, {C_SUCCESS} 0%, #2A8C7A 100%); padding: 25px; border-radius: 12px; color: white; display:flex; justify-content:space-between; align-items:center; box-shadow:0 10px 20px rgba(0,0,0,0.1);">
            <div>
                <h2 style="color:white !important; margin:0;">Total Estimado</h2>
                <span style="opacity:0.9;">{len(res['items'])} planos procesados</span>
            </div>
            <div style="text-align:right;">
                <div style="font-size:3rem; font-weight:800;">${res['total_global']:,.0f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        c_p, c_t = st.columns([1, 4])
        with c_p:
            st.write("")
            st.write("")
            pdf_bytes = generar_pdf(res["items"], res["total_global"])
            st.download_button("📄 Descargar PDF", data=pdf_bytes, file_name="Cotizacion.pdf", mime="application/pdf", type="secondary", use_container_width=True)
        with c_t:
            st.write("")
            df = pd.DataFrame(res["items"])
            st.dataframe(df[["archivo", "dimensiones", "tipo", "detalle", "precio"]], use_container_width=True, hide_index=True)

    # ==========================================
    # 7. HISTORIAL (SOLO AQUÍ)
    # ==========================================
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='color:{C_TEXT}; border-bottom:1px solid {C_BORDER}; padding-bottom:10px;'>🕒 Historial de Sesión</h4>", unsafe_allow_html=True)

    if not st.session_state.historial:
        st.info("El historial está vacío.")
    else:
        if st.button("🗑️ Limpiar Historial", type="secondary"):
            borrar_historial()
            st.rerun()

        for i, item in enumerate(st.session_state.historial):
            label = f"{item['hora']} | Total: ${item['data']['total_global']:,.0f} | {item['modo']}"
            with st.expander(label):
                col_h1, col_h2 = st.columns([1, 5])
                with col_h1:
                    pdf_h = generar_pdf(item['data']['items'], item['data']['total_global'])
                    st.download_button(f"Bajar PDF", data=pdf_h, file_name=f"Hist_{item['hora']}.pdf", mime="application/pdf", key=f"btn_h_{i}", use_container_width=True)
                with col_h2:
                    df_h = pd.DataFrame(item['data']['items'])
                    st.dataframe(df_h[["archivo", "dimensiones", "precio"]], use_container_width=True, hide_index=True)



elif st.session_state.active_tab == "Lienzo Imagen":
    lienzo.app()      # Ejecutamos la función principal de ese archivo

# ------------------------------------------
# PESTAÑA 3: IMPRESIÓN DIGITAL (AÚN EN CONSTRUCCIÓN)
# ------------------------------------------
elif st.session_state.active_tab == "Simulador de Impresión": # Nota el nuevo nombre de la pestaña
    import simulador
    simulador.app()
