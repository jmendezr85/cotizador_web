import streamlit as st
import math
import pandas as pd
import plotly.graph_objects as go 

# ==========================================
# ⚙️ CONSTANTES EXACTAS (Lógica de Negocio)
# ==========================================

# 1. Precios Materiales
VALOR_ML_VINILO = 13600
VALOR_ML_LONA = 21700
VALOR_ML_FOTOGRAFICO = 13000
VALOR_ML_PROPALCOTE = 8000
VALOR_ML_PERGAMINO = 6000
VALOR_M2_LIENZO = 83000

# 2. Costos de Impresión
VALOR_M2_PLOTEO = 25000
VALOR_MIN_PLOTEO = 10000

# 3. Especiales Lienzo
VALOR_M2_PLOTEO_LIENZO = 50000
VALOR_MIN_PLOTEO_LIENZO = 12500
VALOR_MIN_MATERIAL_LIENZO = 12500

# 4. Extras
VALOR_ML_TUBO = 6200 
MEDIDA_MINIMA = 20 
COSTO_ML_CORTE = 7800 

# ==========================================
# 🧠 LÓGICA DE NEGOCIO
# ==========================================

def obtener_ancho_maximo(material, ancho, alto):
    if material == 'Vinilo': return 130
    if material == 'Lona': return 130
    if material == 'Propalcote': return 130
    if material == 'Pendón Vertical': return 130
    if material == 'Lienzo': return 125
    if material == 'Fotográfico': return 70
    if material == 'Pergamino': return 90
    
    if material == 'Pendón Horizontal':
        if ancho <= 130: return 130
        else: return 120 
    return 130 

def validar_medidas(ancho, alto, ancho_maximo):
    if ancho < MEDIDA_MINIMA or alto < MEDIDA_MINIMA:
        return False, f"Las medidas deben ser mínimo de {MEDIDA_MINIMA} cm."
    if ancho <= ancho_maximo or alto <= ancho_maximo:
        return True, "OK"
    else:
        return False, f"Alguna medida debe ser menor o igual a {ancho_maximo} cm."

def calcular_precio_general(ancho, alto, valor_ml_material, es_pendon=False):
    ancho_m = ancho / 100.0
    alto_m = alto / 100.0
    
    precio_ploteo = math.ceil((ancho_m * alto_m * VALOR_M2_PLOTEO) / 1000) * 1000
    if precio_ploteo < VALOR_MIN_PLOTEO:
        precio_ploteo = VALOR_MIN_PLOTEO
        
    ancho_max = 130 
    precio_material = 0
    
    if ancho > ancho_max:
        precio_material = ancho_m * valor_ml_material
    elif alto > ancho_max:
        precio_material = alto_m * valor_ml_material
    elif ancho < alto:
        precio_material = ancho_m * valor_ml_material
    else:
        precio_material = alto_m * valor_ml_material
        
    precio_material = math.ceil(precio_material / 1000) * 1000
    
    valor_tubos = 0
    if es_pendon:
        valor_tubos = math.ceil((ancho_m * VALOR_ML_TUBO * 2) / 1000) * 1000
        
    return precio_material + precio_ploteo + valor_tubos

def calcular_precio_lienzo(ancho, alto):
    ancho_m = ancho / 100.0
    alto_m = alto / 100.0
    
    precio_ploteo = round((ancho_m * alto_m * VALOR_M2_PLOTEO_LIENZO) / 1000) * 1000
    if precio_ploteo < VALOR_MIN_PLOTEO_LIENZO:
        precio_ploteo = VALOR_MIN_PLOTEO_LIENZO
        
    precio_material = ((ancho + 10) / 100) * ((alto + 10) / 100) * VALOR_M2_LIENZO
    precio_material = math.ceil(precio_material / 1000) * 1000
    
    if precio_material < VALOR_MIN_MATERIAL_LIENZO:
        precio_material = VALOR_MIN_MATERIAL_LIENZO
        
    return precio_material + precio_ploteo

def cotizar(material, ancho, alto):
    if material == 'Pendón Vertical' and ancho > alto:
        return 0, "Advertencia: En pendón vertical el ancho no debe ser mayor al alto."
    if material == 'Pendón Horizontal' and alto > ancho:
        return 0, "Advertencia: En pendón horizontal el alto no debe ser mayor al ancho."
        
    max_w = obtener_ancho_maximo(material, ancho, alto)
    es_valido, msg = validar_medidas(ancho, alto, max_w)
    if not es_valido:
        return 0, msg
        
    precio = 0
    if material == 'Lienzo':
        precio = calcular_precio_lienzo(ancho, alto)
    elif material == 'Vinilo':
        precio = calcular_precio_general(ancho, alto, VALOR_ML_VINILO)
    elif material == 'Lona':
        precio = calcular_precio_general(ancho, alto, VALOR_ML_LONA)
    elif material == 'Pendón Vertical' or material == 'Pendón Horizontal':
        precio = calcular_precio_general(ancho, alto, VALOR_ML_LONA, es_pendon=True)
    elif material == 'Propalcote':
        precio = calcular_precio_general(ancho, alto, VALOR_ML_PROPALCOTE)
    elif material == 'Fotográfico':
        precio = calcular_precio_general(ancho, alto, VALOR_ML_FOTOGRAFICO)
    elif material == 'Pergamino':
        precio = calcular_precio_general(ancho, alto, VALOR_ML_PERGAMINO)
        
    return precio, "OK"

# ==========================================
# 🧠 OPTIMIZACIÓN Y GRÁFICOS (Plotly)
# ==========================================
def optimizar_lienzo(lienzo_w, lienzo_h, pieza_w, pieza_h):
    lienzo_w = max(lienzo_w, 0.1)
    lienzo_h = max(lienzo_h, 0.1)
    pieza_w = max(pieza_w, 0.1)
    pieza_h = max(pieza_h, 0.1)

    # Opción A: Normal
    cols_a = int(lienzo_w // pieza_w)
    rows_a = int(lienzo_h // pieza_h)
    total_a = cols_a * rows_a
    
    # Opción B: Rotada
    cols_b = int(lienzo_w // pieza_h)
    rows_b = int(lienzo_h // pieza_w)
    total_b = cols_b * rows_b
    
    if total_a >= total_b:
        return total_a, (cols_a, rows_a), False 
    else:
        return total_b, (cols_b, rows_b), True 

def dibujar_distribucion_plotly(lienzo_w, lienzo_h, pieza_w, pieza_h, grid_config, rotado):
    cols, rows = grid_config
    fig = go.Figure()

    # Fondo del Lienzo
    fig.add_shape(type="rect",
        x0=0, y0=0, x1=lienzo_w, y1=lienzo_h,
        line=dict(color="#333333", width=2), fillcolor="white", layer="below"
    )

    if lienzo_w > 0 and lienzo_h > 0 and pieza_w > 0 and pieza_h > 0 and cols > 0 and rows > 0:
        w_p = pieza_h if rotado else pieza_w
        h_p = pieza_w if rotado else pieza_h
        
        total_used_w = cols * w_p
        total_used_h = rows * h_p
        
        # Área ocupada (azul)
        fig.add_shape(type="rect",
            x0=0, y0=0, x1=total_used_w, y1=total_used_h,
            line=dict(width=0), fillcolor="#3b82f6", opacity=0.9, layer="below"
        )
        
        # Rejilla (Líneas blancas)
        for i in range(1, cols + 1):
            fig.add_shape(type="line", x0=i*w_p, y0=0, x1=i*w_p, y1=total_used_h, line=dict(color="white", width=1))
        for j in range(1, rows + 1):
            fig.add_shape(type="line", x0=0, y0=j*h_p, x1=total_used_w, y1=j*h_p, line=dict(color="white", width=1))

        # Tooltips (puntos invisibles)
        if (cols * rows) < 1000:
            x_centers = []
            y_centers = []
            texts = []
            for r in range(rows):
                y_c = (r * h_p) + (h_p / 2)
                for c in range(cols):
                    x_c = (c * w_p) + (w_p / 2)
                    x_centers.append(x_c)
                    y_centers.append(y_c)
                    texts.append(f"Pieza {(r*cols)+c+1}")

            fig.add_trace(go.Scatter(
                x=x_centers, y=y_centers, mode='markers',
                marker=dict(size=5, color='white', opacity=0),
                text=texts, hoverinfo='text'
            ))

    fig.update_xaxes(range=[-lienzo_w*0.05, max(lienzo_w*1.05, 1)], showgrid=False, zeroline=False, visible=False, fixedrange=True)
    fig.update_yaxes(range=[-lienzo_h*0.05, max(lienzo_h*1.05, 1)], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1, fixedrange=True)
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
        title=dict(text=f"Distribución {cols}x{rows} ({cols*rows} piezas)", x=0.5, font=dict(size=14, color="#555")),
        showlegend=False
    )
    return fig

# ==========================================
# 🧠 CALLBACKS & STATE
# ==========================================
def reset_inputs_cot():
    st.session_state.calc_ancho = 0.0
    st.session_state.calc_alto = 0.0
    st.session_state.calc_precio = None
    st.session_state.calc_msg = ""

def reset_inputs_sim():
    st.session_state.sim_lw = 0.0
    st.session_state.sim_lh = 0.0
    st.session_state.sim_cw = 0.0
    st.session_state.sim_ch = 0.0

def agregar_cotizacion():
    precio = st.session_state.calc_precio
    if precio and precio > 0:
        item = {
            "Material": st.session_state.calc_material,
            "Dimensiones": f"{st.session_state.calc_ancho:.0f}x{st.session_state.calc_alto:.0f} cm",
            "Precio": precio
        }
        st.session_state.sim_cotizaciones.append(item)
        reset_inputs_cot()

# ==========================================
# 🚀 APP PRINCIPAL
# ==========================================
def app():
    # Inicializar estado
    if 'sim_cotizaciones' not in st.session_state: st.session_state.sim_cotizaciones = []
    if 'calc_ancho' not in st.session_state: st.session_state.calc_ancho = 0.0
    if 'calc_alto' not in st.session_state: st.session_state.calc_alto = 0.0
    if 'calc_precio' not in st.session_state: st.session_state.calc_precio = None
    if 'calc_msg' not in st.session_state: st.session_state.calc_msg = ""
    
    if 'sim_lw' not in st.session_state: st.session_state.sim_lw = 0.0
    if 'sim_lh' not in st.session_state: st.session_state.sim_lh = 0.0
    if 'sim_cw' not in st.session_state: st.session_state.sim_cw = 0.0
    if 'sim_ch' not in st.session_state: st.session_state.sim_ch = 0.0

    # ==========================================
    # 🟧 SIDEBAR: CÁLCULO Y GESTIÓN
    # ==========================================
    with st.sidebar:
        st.markdown("## 🟧 Cotizador App") 

        st.divider()
        st.markdown("### 1. Cálculo y Gestión")
        
        with st.container(border=True):
            st.caption("Nueva Cotización")
            opciones = ['Vinilo', 'Lona', 'Pendón Vertical', 'Pendón Horizontal', 'Lienzo', 'Propalcote', 'Fotográfico', 'Pergamino']
            material = st.selectbox("Material", opciones, key="calc_material", label_visibility="collapsed")
            
            c1, c2 = st.columns(2)
            with c1: st.number_input("Ancho (cm)", min_value=0.0, step=0.1, key="calc_ancho")
            with c2: st.number_input("Alto (cm)", min_value=0.0, step=0.1, key="calc_alto")
            
            st.write("")
            if st.button("Calcular Precio", use_container_width=True, type="primary"):
                precio, msg = cotizar(material, st.session_state.calc_ancho, st.session_state.calc_alto)
                if precio > 0:
                    st.session_state.calc_precio = precio
                    st.session_state.calc_msg = "OK"
                else:
                    st.session_state.calc_precio = 0
                    st.session_state.calc_msg = msg

            # Resultado Precio
            if st.session_state.calc_precio is not None and st.session_state.calc_precio > 0:
                st.markdown(f"""
                <div style="background-color:#e8fdf5; border-radius:8px; padding:10px; text-align:center; margin-top:10px; border: 1px solid #b7ebc5;">
                    <span style="font-size:1.5rem; font-weight:bold; color:#155724;">${st.session_state.calc_precio:,.0f}</span>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("➕ Añadir a Lista", use_container_width=True, on_click=agregar_cotizacion):
                    pass
            elif st.session_state.calc_msg and st.session_state.calc_msg != "OK":
                st.error(st.session_state.calc_msg)

            if st.button("Limpiar Campos", use_container_width=True, on_click=reset_inputs_cot):
                pass

        # Lista Resumen en Sidebar con IVA
        st.markdown("### 📋 Historial")
        if st.session_state.sim_cotizaciones:
            # Cálculos de Total e IVA
            total_neto = sum(x["Precio"] for x in st.session_state.sim_cotizaciones)
            total_iva = total_neto * 0.19
            gran_total = total_neto + total_iva

            st.markdown(f"""
            <div style="text-align:right; font-size:0.9rem; margin-bottom:10px; background-color:#f8f9fa; padding:10px; border-radius:5px;">
                Subtotal: <b>${total_neto:,.0f}</b><br>
                IVA (19%): <b>${total_iva:,.0f}</b><br>
                <hr style="margin:5px 0;">
                <span style="color:#0099cc; font-size:1.2rem; font-weight:bold;">Total: ${gran_total:,.0f}</span>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("Ver Detalles"):
                df = pd.DataFrame(st.session_state.sim_cotizaciones)
                # Formatear precio para mostrar
                df_show = df.copy()
                df_show["Precio"] = df_show["Precio"].apply(lambda x: f"${x:,.0f}")
                st.dataframe(df_show[["Material", "Precio"]], hide_index=True)
                
                if st.button("Borrar Historial"):
                    st.session_state.sim_cotizaciones = []
                    st.rerun()
        else:
            st.caption("No hay cotizaciones aún.")

    # ==========================================
    # 🟦 MAIN: SIMULADOR DE DISTRIBUCIÓN
    # ==========================================
    
    st.markdown("## Simulador de Distribución")
    
    # Inputs Horizontales Limpios
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.number_input("Ancho Lienzo", key="sim_lw", min_value=0.0, step=0.1)
        with c2: st.number_input("Alto Lienzo", key="sim_lh", min_value=0.0, step=0.1)
        with c3: st.number_input("Ancho Pieza", key="sim_cw", min_value=0.0, step=0.1)
        with c4: st.number_input("Alto Pieza", key="sim_ch", min_value=0.0, step=0.1)
        
        col_dummy, col_btn = st.columns([6, 1])
        with col_btn:
            if st.button("🗑️", help="Limpiar simulador", on_click=reset_inputs_sim): pass

    # Cálculos en tiempo real
    lw, lh, cw, ch = st.session_state.sim_lw, st.session_state.sim_lh, st.session_state.sim_cw, st.session_state.sim_ch
    total, grid, rotado = optimizar_lienzo(lw, lh, cw, ch)
    area_l = lw * lh
    area_u = total * (cw * ch)
    desp = 0.0
    if area_l > 0: desp = 100 * (1 - (area_u / area_l))

    # Gráfico Principal
    fig = dibujar_distribucion_plotly(lw, lh, cw, ch, grid, rotado)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # Tarjetas de Métricas
    col_metrics1, col_metrics2, col_metrics3 = st.columns(3)

    with col_metrics1:
        with st.container(border=True):
            st.metric(label="Piezas Totales", value=total)
            st.caption("Capacidad máxima")

    with col_metrics2:
        with st.container(border=True):
            st.metric(label="Desperdicio", value=f"{desp:.1f}%", delta=f"-{desp:.1f}%", delta_color="inverse")
            st.caption("Área no utilizada")

    with col_metrics3:
        with st.container(border=True):
            orientacion = "Rotada (Mejor)" if rotado else "Normal"
            st.metric(label="Orientación", value="🔄" if rotado else "⏹️", delta=orientacion, delta_color="off")
            st.caption("Estrategia óptima")