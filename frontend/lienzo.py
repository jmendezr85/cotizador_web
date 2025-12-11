import streamlit as st
from PIL import Image, ImageDraw
import fitz  # PyMuPDF
import numpy as np
import pandas as pd
import os

# ==========================================
# 🧠 FUNCIONES LÓGICAS (HELPERS)
# ==========================================
def reset_lienzo():
    st.session_state.uploaded_file = None
    st.session_state.preview_image_obj = None
    st.session_state.real_file_w = 0.0
    st.session_state.real_file_h = 0.0
    
    st.session_state.img_rotation = 0
    st.session_state.scale_mode = "Ajustar a Lienzo"
    st.session_state.custom_w = 0.0
    st.session_state.custom_h = 0.0
    
    st.session_state.pixel_analysis_done = False
    st.session_state.costo_final = 0.0
    st.session_state.cobertura_tinta = 0.0
    st.session_state.area_ocupada_real = 0.0
    st.session_state.tipo_pliego = "-"
    st.session_state.msg_error_precio = None
    st.session_state.origen_datos = ""
    
    st.session_state.lienzo_uploader_key += 1 

def asegurar_rgb(img_pil):
    if img_pil.mode != 'RGBA':
        return img_pil.convert('RGBA')
    return img_pil

def procesar_archivo(uploaded_file):
    if uploaded_file is None: return None, 0, 0
    try:
        if uploaded_file.type == "application/pdf":
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            page = doc.load_page(0)
            rect = page.rect
            w_cm = (rect.width / 72) * 2.54
            h_cm = (rect.height / 72) * 2.54
            
            pix = page.get_pixmap(dpi=150, alpha=False) 
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return img, w_cm, h_cm
        else:
            img = Image.open(uploaded_file)
            img = asegurar_rgb(img)
            
            dpi = img.info.get('dpi')
            if dpi:
                w_cm = (img.width / dpi[0]) * 2.54
                h_cm = (img.height / dpi[1]) * 2.54
            else:
                w_cm = (img.width / 72) * 2.54
                h_cm = (img.height / 72) * 2.54
            return img, w_cm, h_cm
    except Exception as e:
        st.error(f"Error: {e}")
        return None, 0, 0

def calcular_tinta_imagen(img_pil):
    if not img_pil: return 0.0
    img_rgb = img_pil.convert("RGB")
    img_small = img_rgb.resize((400, 400))
    arr = np.array(img_small)
    
    umbral = 240
    mask_blancos = (arr[:,:,0] > umbral) & (arr[:,:,1] > umbral) & (arr[:,:,2] > umbral)
    
    pixeles_totales = arr.shape[0] * arr.shape[1]
    pixeles_blancos = np.sum(mask_blancos)
    pixeles_tinta = pixeles_totales - pixeles_blancos
    
    return (pixeles_tinta / pixeles_totales)

# --- NUEVA LÓGICA DE TAMAÑOS ---
def determinar_pliego(w, h):
    """
    Clasificación exacta según tus reglas:
    - 1/4 Pliego: 50x35
    - 1/2 Pliego: 70x50
    - Pliego: 100x70
    - Extra 90: > Pliego con ancho <= 90
    - Extra 100: > Pliego con ancho > 90
    """
    # Ordenamos dimensiones para comparar siempre "lado corto" vs "lado largo"
    # Esto evita problemas si el usuario pone 35x50 en vez de 50x35
    lados = sorted([w, h]) 
    min_lado, max_lado = lados[0], lados[1]
    
    # 1. Cuarto Pliego (50x35) con pequeña tolerancia (1.0 cm)
    if min_lado <= 36 and max_lado <= 51:
        return "1/4 PLIEGO"
        
    # 2. Medio Pliego (70x50)
    elif min_lado <= 51 and max_lado <= 71:
        return "1/2 PLIEGO"
        
    # 3. Pliego Completo (100x70)
    elif min_lado <= 71 and max_lado <= 101:
        return "PLIEGO 100x70" # Nombre exacto del CSV
        
    # 4. Extras (Supera el tamaño Pliego)
    else:
        # Si el lado más corto cabe en el rollo de 90cm
        if min_lado <= 91:
            return "PLIEGO 100x90" # Mapea a tu CSV "PLIEGO 100x90" (Extra 90)
        else:
            return "EXTRAPLIEGO 100X100" # Mapea a tu CSV "EXTRAPLIEGO 100X100" (Extra 100)

# ==========================================
# 💰 LÓGICA DE PRECIOS (RANGOS EXACTOS)
# ==========================================
def cargar_precios_csv():
    rutas_posibles = [
        r"E:\2026\cotizador-app\backend\data\precios.csv",  # TU RUTA
        "backend/data/precios.csv",
        "../backend/data/precios.csv",
        "precios.csv"
    ]
    
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            try:
                # Detectar cabecera (fila con "PRECIOS DE PLOTEO")
                fila_header = 0
                with open(ruta, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines[:20]):
                        if "PRECIOS DE PLOTEO" in line.upper() and ";" in line:
                            fila_header = i
                            break
                
                # Leer con separador ';'
                df = pd.read_csv(ruta, header=fila_header, sep=';', encoding='latin-1')
                df = df.dropna(how='all') 
                
                # Definir Índice
                col_index = None
                for col in df.columns:
                    if "PRECIOS DE PLOTEO" in str(col).upper():
                        col_index = col
                        break
                if col_index:
                    df.set_index(col_index, inplace=True)
                else:
                    df.set_index(df.columns[0], inplace=True)
                
                # Eliminar duplicados quedándonos con el primero
                df = df[~df.index.duplicated(keep='first')]

                return df, ruta
            except Exception as e:
                print(f"Error {ruta}: {e}")
                continue
                
    return None, None

def obtener_nombre_columna_por_rango(porcentaje):
    """Mapea el % exacto al nombre de la columna en el CSV"""
    p = porcentaje # 0 a 100
    
    if p <= 5: return "LINEA COLOR"
    if p <= 14: return "10%"
    if p <= 24: return "20%"
    if p <= 34: return "30%"
    if p <= 44: return "40%"
    if p <= 54: return "50%"
    if p <= 64: return "60%"
    if p <= 74: return "70%"
    if p <= 84: return "80%"
    if p <= 94: return "90%"
    return "FULL COLOR" # 95% a 100%

def buscar_precio_en_csv(df, tipo_pliego, cobertura_decimal):
    try:
        if df is None or df.empty:
            return 0.0, "Error: Tabla vacía."

        # 1. ENCONTRAR FILA (FORMATO)
        row_match = None
        # Búsqueda flexible para que "1/4 PLIEGO" encuentre "1/4 PLIEGO 50x35"
        for idx in df.index:
            idx_clean = str(idx).upper().replace(' ', '').replace(u'\xa0', '')
            pliego_clean = tipo_pliego.upper().replace(' ', '')
            
            if pliego_clean in idx_clean or idx_clean in pliego_clean:
                row_match = idx
                break
        
        if not row_match:
            # Fallback especial para extras
            if "100X100" in tipo_pliego:
                 for idx in df.index:
                     if "100X100" in str(idx).upper(): 
                         row_match = idx; break
            elif "100x90" in tipo_pliego:
                 for idx in df.index:
                     if "100X90" in str(idx).upper(): 
                         row_match = idx; break

        if not row_match:
            row_match = df.index[0]
            msg = f"Formato '{tipo_pliego}' no hallado. Base: {row_match}"
        else:
            msg = f"Tarifa: {row_match}"

        # 2. ENCONTRAR COLUMNA (SEGÚN TUS RANGOS)
        pct_real = cobertura_decimal * 100
        col_name_target = obtener_nombre_columna_por_rango(pct_real)
        
        col_match = None
        # Buscamos la columna en el CSV que coincida con el nombre objetivo
        for c in df.columns:
            if "Unnamed" in str(c): continue
            c_clean = str(c).upper().strip()
            target_clean = col_name_target.upper().strip()
            
            if c_clean == target_clean:
                col_match = c
                break
            # Match parcial para "LINEA COLOR"
            if target_clean == "LINEA COLOR" and "COLOR" in c_clean and "LINEA" in c_clean:
                col_match = c
                break

        if not col_match:
            # Si no encuentra la columna exacta (ej: CSV dice "10 %" y buscamos "10%"), fallback
            col_match = df.columns[-1] # Full Color por seguridad
            msg += f" | Columna '{col_name_target}' no hallada, usando {col_match}"
        else:
            msg += f" | Tinta: {col_match} ({pct_real:.1f}%)"

        # 3. OBTENER PRECIO
        raw_val = df.loc[row_match, col_match]
        
        if isinstance(raw_val, pd.Series): raw_val = raw_val.iloc[0]
        
        if isinstance(raw_val, str):
            clean_val = raw_val.replace('.', '').replace(',', '.').strip()
            precio = float(clean_val)
        else:
            precio = float(raw_val)
            if precio < 100 and precio > 0: precio = precio * 1000 
        
        return precio, msg

    except Exception as e:
        return 0.0, f"Error cálculo: {str(e)}"

# ==========================================
# 🎨 VISOR GRÁFICO (SIN CAMBIOS)
# ==========================================
def crear_visor_lienzo(canvas_w, canvas_h, img_pil=None, rotation=0, scale_mode="Ajustar", custom_w=0, custom_h=0, real_w=0, real_h=0):
    MESA_W = 1000
    MESA_H = 700
    BG_COLOR_MESA = (248, 249, 250) 
    
    mesa = Image.new("RGB", (MESA_W, MESA_H), BG_COLOR_MESA)
    draw_mesa = ImageDraw.Draw(mesa)
    
    if canvas_w <= 0: canvas_w = 1
    if canvas_h <= 0: canvas_h = 1

    PADDING = 40 
    area_util_w = MESA_W - (PADDING * 2)
    area_util_h = MESA_H - (PADDING * 2)
    
    ratio_w = area_util_w / canvas_w
    ratio_h = area_util_h / canvas_h
    scale_factor = min(ratio_w, ratio_h)
    
    paper_w_px = int(canvas_w * scale_factor)
    paper_h_px = int(canvas_h * scale_factor)
    
    paper_x = (MESA_W - paper_w_px) // 2
    paper_y = (MESA_H - paper_h_px) // 2
    
    # Objeto Papel Blanco Puro
    papel = Image.new("RGB", (paper_w_px, paper_h_px), (255, 255, 255))
    
    if img_pil:
        img_temp = img_pil.copy().convert("RGBA")
        if rotation != 0: 
            img_temp = img_temp.rotate(-rotation, expand=True, fillcolor=(255,255,255,0))
        
        target_w, target_h = 0, 0
        
        if scale_mode == "Ajustar a Lienzo":
            r_img_w = paper_w_px / img_temp.width
            r_img_h = paper_h_px / img_temp.height
            factor_img = min(r_img_w, r_img_h)
            target_w = int(img_temp.width * factor_img)
            target_h = int(img_temp.height * factor_img)
            
        elif scale_mode == "Tamaño Real de la Imagen":
            if real_w > 0:
                target_w = int(real_w * scale_factor)
                if img_temp.width > 0:
                    target_h = int(target_w * (img_temp.height / img_temp.width))
            else:
                 target_w = int((img_temp.width/72*2.54) * scale_factor)
                 target_h = int((img_temp.height/72*2.54) * scale_factor)

        elif scale_mode == "Tamaño Personalizado (cm)":
            target_w = int(custom_w * scale_factor)
            target_h = int(custom_h * scale_factor)

        if target_w > 0 and target_h > 0:
            img_temp = img_temp.resize((target_w, target_h), Image.Resampling.LANCZOS)
            px = (paper_w_px - target_w) // 2
            py = (paper_h_px - target_h) // 2
            papel.paste(img_temp, (px, py), img_temp)

    draw_mesa.rectangle([(paper_x + 5, paper_y + 5), (paper_x + paper_w_px + 5, paper_y + paper_h_px + 5)], fill=(220, 220, 220))
    mesa.paste(papel, (paper_x, paper_y))
    draw_mesa.rectangle([(paper_x, paper_y), (paper_x + paper_w_px, paper_y + paper_h_px)], outline=(180, 180, 180), width=1)

    return mesa

# ==========================================
# 🚀 APP PRINCIPAL
# ==========================================
def app():
    if 'canvas_width' not in st.session_state: st.session_state.canvas_width = 100.0
    if 'canvas_height' not in st.session_state: st.session_state.canvas_height = 70.0
    if 'canvas_created' not in st.session_state: st.session_state.canvas_created = False
    if 'uploaded_file' not in st.session_state: st.session_state.uploaded_file = None
    if 'preview_image_obj' not in st.session_state: st.session_state.preview_image_obj = None
    if 'real_file_w' not in st.session_state: st.session_state.real_file_w = 0.0
    if 'real_file_h' not in st.session_state: st.session_state.real_file_h = 0.0
    if 'lienzo_uploader_key' not in st.session_state: st.session_state.lienzo_uploader_key = 0
    if 'img_rotation' not in st.session_state: st.session_state.img_rotation = 0
    if 'scale_mode' not in st.session_state: st.session_state.scale_mode = "Ajustar a Lienzo"
    if 'mantener_aspecto' not in st.session_state: st.session_state.mantener_aspecto = True
    if 'custom_w' not in st.session_state: st.session_state.custom_w = 0.0
    if 'custom_h' not in st.session_state: st.session_state.custom_h = 0.0
    
    if 'pixel_analysis_done' not in st.session_state: st.session_state.pixel_analysis_done = False
    if 'costo_final' not in st.session_state: st.session_state.costo_final = 0.0
    if 'cobertura_tinta' not in st.session_state: st.session_state.cobertura_tinta = 0.0
    if 'area_ocupada_real' not in st.session_state: st.session_state.area_ocupada_real = 0.0
    if 'tipo_pliego' not in st.session_state: st.session_state.tipo_pliego = "-"
    if 'msg_error_precio' not in st.session_state: st.session_state.msg_error_precio = None
    if 'origen_datos' not in st.session_state: st.session_state.origen_datos = ""

    st.markdown("""
        <style>
        .block-container { padding-top: 2rem !important; padding-bottom: 5rem !important; }
        [data-testid="column"]:last-child { position: sticky; top: 1rem; height: 95vh; overflow: hidden; display: block; }
        .visor-title { margin: 0 !important; padding: 0 !important; font-size: 1rem; color: #555; margin-bottom: 5px !important; font-weight: 600; }
        </style>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 2.5], gap="large")

    with col_left:
        with st.container(border=True):
            st.markdown("##### Crear Lienzo (cm)")
            c1, c2 = st.columns(2)
            with c1: w_in = st.number_input("Ancho", value=st.session_state.canvas_width)
            with c2: h_in = st.number_input("Alto", value=st.session_state.canvas_height)
            
            if st.button("Crear Lienzo", type="primary", use_container_width=True):
                st.session_state.canvas_width = w_in
                st.session_state.canvas_height = h_in
                st.session_state.canvas_created = True
                st.session_state.pixel_analysis_done = False 
                st.rerun()

        if st.session_state.canvas_created:
            st.write("")
            with st.container(border=True):
                st.markdown("##### Cargar Imagen / PDF")
                file = st.file_uploader("Archivo", type=["jpg","png","pdf"], key=f"up_{st.session_state.lienzo_uploader_key}", label_visibility="collapsed")
                
                if file and st.session_state.uploaded_file != file:
                    st.session_state.uploaded_file = file
                    img_obj, rw, rh = procesar_archivo(file)
                    st.session_state.preview_image_obj = img_obj
                    st.session_state.real_file_w = rw
                    st.session_state.real_file_h = rh
                    st.session_state.pixel_analysis_done = False 
                
                if st.session_state.preview_image_obj:
                    st.caption(f"📏 Detectado: {st.session_state.real_file_w:.2f} x {st.session_state.real_file_h:.2f} cm")

            if st.session_state.preview_image_obj:
                st.write("")
                with st.container(border=True):
                    st.markdown("##### Ajustar Imagen")
                    
                    mode = st.radio("Modo", ["Ajustar a Lienzo", "Tamaño Real de la Imagen", "Tamaño Personalizado (cm)"], label_visibility="collapsed")
                    st.session_state.scale_mode = mode
                    
                    if mode == "Tamaño Real de la Imagen":
                        c1, c2 = st.columns(2)
                        with c1: st.session_state.real_file_w = st.number_input("Ancho Real (cm)", value=st.session_state.real_file_w)
                        with c2:
                             asp = 1.0
                             if st.session_state.preview_image_obj.width > 0:
                                 asp = st.session_state.preview_image_obj.height / st.session_state.preview_image_obj.width
                             st.number_input("Alto Real (cm)", value=st.session_state.real_file_w * asp, disabled=True)

                    if mode == "Tamaño Personalizado (cm)":
                        chk = st.checkbox("Mantener Relación", value=st.session_state.mantener_aspecto)
                        st.session_state.mantener_aspecto = chk
                        cc1, cc2 = st.columns(2)
                        with cc1: cw = st.number_input("Ancho", value=st.session_state.custom_w if st.session_state.custom_w > 0 else 10.0)
                        with cc2:
                            if chk:
                                asp = 1.0
                                if st.session_state.preview_image_obj.width > 0: asp = st.session_state.preview_image_obj.height / st.session_state.preview_image_obj.width
                                if st.session_state.img_rotation % 180 != 0 and asp!=0: asp = 1/asp
                                ch_calc = cw * asp
                                st.number_input("Alto", value=ch_calc, disabled=True)
                                st.session_state.custom_h = ch_calc
                            else:
                                st.session_state.custom_h = st.number_input("Alto", value=st.session_state.custom_h)
                        st.session_state.custom_w = cw

                    c1, c2 = st.columns(2)
                    with c1: 
                        if st.button("↶ 90°", use_container_width=True): st.session_state.img_rotation -= 90
                    with c2:
                        if st.button("↷ 90°", use_container_width=True): st.session_state.img_rotation += 90

            st.write("")
            with st.container(border=True):
                st.markdown("##### Cotización (precios.csv)")
                if st.button("Calcular Costo Final", type="primary", use_container_width=True, disabled=not st.session_state.preview_image_obj):
                    st.session_state.pixel_analysis_done = True
                    st.session_state.msg_error_precio = None
                    
                    # 1. ÁREA
                    area_imagen_cm2 = 0
                    if st.session_state.scale_mode == "Ajustar a Lienzo":
                        cw = st.session_state.canvas_width
                        ch = st.session_state.canvas_height
                        imw = st.session_state.preview_image_obj.width
                        imh = st.session_state.preview_image_obj.height
                        if st.session_state.img_rotation % 180 != 0: imw, imh = imh, imw
                        ratio_w = cw / imw
                        ratio_h = ch / imh
                        scale = min(ratio_w, ratio_h)
                        area_imagen_cm2 = (imw * scale) * (imh * scale)
                    elif st.session_state.scale_mode == "Tamaño Personalizado (cm)":
                        area_imagen_cm2 = st.session_state.custom_w * st.session_state.custom_h
                    else:
                         area_imagen_cm2 = st.session_state.real_file_w * st.session_state.real_file_h
                    
                    st.session_state.area_ocupada_real = area_imagen_cm2
                    area_lienzo_total = st.session_state.canvas_width * st.session_state.canvas_height
                    
                    # 2. TINTA
                    factor_tinta_imagen = calcular_tinta_imagen(st.session_state.preview_image_obj)
                    cobertura_global = factor_tinta_imagen * (area_imagen_cm2 / area_lienzo_total)
                    st.session_state.cobertura_tinta = cobertura_global * 100 
                    
                    # 3. DETERMINAR PLIEGO (REGLAS NUEVAS)
                    st.session_state.tipo_pliego = determinar_pliego(st.session_state.canvas_width, st.session_state.canvas_height)

                    # 4. PRECIO
                    df_precios, origen = cargar_precios_csv()
                    st.session_state.origen_datos = origen
                    
                    if df_precios is not None:
                         precio_encontrado, msg = buscar_precio_en_csv(df_precios, st.session_state.tipo_pliego, cobertura_global)
                         st.session_state.costo_final = precio_encontrado
                         st.session_state.msg_error_precio = msg
                    else:
                         st.session_state.costo_final = 0
                         st.session_state.msg_error_precio = f"No se encontró precios.csv en E:/.../backend/data/"

                if st.session_state.pixel_analysis_done: 
                    st.success(f"Cobertura Detectada: {st.session_state.cobertura_tinta:.1f}%")
                    if st.session_state.origen_datos:
                        st.caption(f"📂 Origen: {st.session_state.origen_datos}")
                    
                    if st.session_state.costo_final == 0:
                        st.error(f"⚠️ {st.session_state.msg_error_precio}")
                    else:
                        st.caption(f"✅ {st.session_state.msg_error_precio}")

            st.write("")
            with st.container(border=True):
                st.markdown("##### Resultados")
                c1, c2 = st.columns(2)
                with c1: 
                    st.caption("Formato Detectado")
                    st.write(f"**{st.session_state.tipo_pliego}**")
                with c2:
                    st.caption("Costo Final")
                    st.markdown(f"<span style='color:green; font-weight:bold; font-size:1.6rem'>${st.session_state.costo_final:,.0f}</span>", unsafe_allow_html=True)

            st.write("")
            st.markdown("##### Controles")
            if st.button("Reiniciar Todo", type="secondary", use_container_width=True):
                reset_lienzo()
                st.rerun()

    with col_right:
        with st.container(border=True):
            st.markdown('<p class="visor-title">👁️ Vista Previa</p>', unsafe_allow_html=True)

            if not st.session_state.canvas_created:
                st.markdown("""
                <div style="height:400px; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#ccc; border: 2px dashed #ddd; border-radius:10px;">
                    <h3>Lienzo no inicializado</h3>
                    <p>Configura el tamaño en el panel izquierdo (a).</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown('<div style="background-color:#f8f9fa; padding:20px; border-radius:8px; display:flex; justify-content:center; align-items: flex-start; width: 100%;">', unsafe_allow_html=True)
                
                visor = crear_visor_lienzo(
                    st.session_state.canvas_width,
                    st.session_state.canvas_height,
                    st.session_state.preview_image_obj,
                    st.session_state.img_rotation,
                    st.session_state.scale_mode,
                    st.session_state.custom_w,
                    st.session_state.custom_h,
                    st.session_state.real_file_w,
                    st.session_state.real_file_h
                )
                
                st.image(visor, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.caption(f"Lienzo: {st.session_state.canvas_width} x {st.session_state.canvas_height} cm")