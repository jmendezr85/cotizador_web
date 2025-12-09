import fitz  # PyMuPDF
import pandas as pd
import numpy as np
import io
import re

class CotizadorMotor:
    def __init__(self, ruta_csv):
        self.df = pd.DataFrame()
        try:
            self.df = pd.read_csv(ruta_csv, header=2, sep=';', encoding='latin-1', dtype=str)
            self.df.columns = self.df.columns.str.strip() 
            self.df = self.df.dropna(subset=['PRECIOS DE PLOTEO'])
            self.df['PRECIOS DE PLOTEO'] = self.df['PRECIOS DE PLOTEO'].apply(self.normalizar_texto)

            cols_precios = self.df.columns[1:] 
            for col in cols_precios:
                self.df[col] = self.df[col].str.replace('.', '', regex=False)
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
            print("✅ Motor actualizado con modos forzados.")
        except Exception as e:
            print(f"❌ Error cargando CSV: {e}")

    def normalizar_texto(self, texto):
        if pd.isna(texto): return ""
        texto = str(texto).upper()
        texto = re.sub(r'\s+', ' ', texto)
        return texto.strip()

    def obtener_columna_precio(self, porcentaje, es_color):
        if porcentaje <= 0.050: return "LINEA COLOR" if es_color else "LINEA NEGRA"
        elif porcentaje <= 0.15: return "10%"
        elif porcentaje <= 0.25: return "20%"
        elif porcentaje <= 0.35: return "30%"
        elif porcentaje <= 0.45: return "40%"
        elif porcentaje <= 0.55: return "50%"
        elif porcentaje <= 0.65: return "60%"
        elif porcentaje <= 0.75: return "70%"
        elif porcentaje <= 0.85: return "80%"
        elif porcentaje <= 0.95: return "90%"
        else: return "FULL COLOR"

    def analizar_archivo(self, archivo_bytes, nombre_archivo, modo="AUTO"):
        resultados_archivo = []
        doc = fitz.open(stream=archivo_bytes, filetype="pdf")
        
        # Mapeo de modos a nombres en el Excel
        mapa_forzado = {
            "PLIEGO": "PLIEGO 100X70",
            "MEDIO": "1/2 PLIEGO 70X50",
            "CUARTO": "1/4 PLIEGO 50X35"
        }

        for i, page in enumerate(doc):
            # Análisis Visual (Siempre es necesario para saber la tinta)
            pix = page.get_pixmap(dpi=72, alpha=False)
            img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
            mask_blanco = np.all(img_np > 240, axis=2)
            mask_tinta = ~mask_blanco
            porcentaje = np.sum(mask_tinta) / (img_np.size / 3)
            
            es_color = False
            if np.sum(mask_tinta) > 0:
                pixels_tinta = img_np[mask_tinta]
                if len(pixels_tinta) > 1000:
                    pixels_tinta = pixels_tinta[np.random.choice(len(pixels_tinta), 1000, replace=False)]
                es_color = np.mean(np.std(pixels_tinta, axis=1)) > 5

            columna = self.obtener_columna_precio(porcentaje, es_color)
            
            # --- LÓGICA DE PRECIO SEGÚN MODO ---
            precio_final = 0
            tipo_calculo = ""
            
            rect = page.rect
            ancho_cm = round(rect.width * 0.0352778, 2)
            alto_cm = round(rect.height * 0.0352778, 2)
            dims_txt = f"{ancho_cm}x{alto_cm}"

            # OPCIÓN 1: MODO FORZADO (Usuario eligió un tamaño fijo)
            if modo in mapa_forzado:
                nombre_fila_forzada = mapa_forzado[modo]
                try:
                    fila = self.df[self.df['PRECIOS DE PLOTEO'] == nombre_fila_forzada]
                    if not fila.empty:
                        precio_final = fila[columna].values[0]
                        tipo_calculo = f"Forzado a {modo}"
                except:
                    tipo_calculo = "Error buscando precio forzado"

            # OPCIÓN 2: MODO AUTOMÁTICO (Tu lógica original de tamaños)
            else:
                ancho_impresion = min(ancho_cm, alto_cm)
                largo_impresion = max(ancho_cm, alto_cm)
                encontrado = False
                
                # Reglas de Tamaño Automático
                if ancho_impresion <= 36 and largo_impresion <= 52:
                    target = "1/4 PLIEGO 50X35"
                elif ancho_impresion <= 52 and largo_impresion <= 72:
                    target = "1/2 PLIEGO 70X50"
                elif ancho_impresion <= 72 and largo_impresion <= 102:
                    target = "PLIEGO 100X70"
                elif ancho_impresion <= 91 and largo_impresion <= 102:
                    target = "PLIEGO 100X90"
                else:
                    target = "METRO LINEAL"

                # Buscar Precio Automático
                if target != "METRO LINEAL":
                    try:
                        fila = self.df[self.df['PRECIOS DE PLOTEO'] == target]
                        if not fila.empty:
                            precio_final = fila[columna].values[0]
                            tipo_calculo = f"Auto ({target})"
                            encontrado = True
                    except: pass
                
                # Metro Lineal
                if not encontrado:
                    metros = largo_impresion / 100
                    if ancho_impresion <= 72:
                        base = "PLIEGO 100X70"
                        nom = "Rollo 70cm"
                    elif ancho_impresion <= 91:
                        base = "PLIEGO 100X90"
                        nom = "Rollo 90cm"
                    else:
                        base = "EXTRAPLIEGO 100X100"
                        nom = "Rollo 100cm"
                    
                    try:
                        fila = self.df[self.df['PRECIOS DE PLOTEO'] == base]
                        precio_m = fila[columna].values[0]
                        precio_final = metros * precio_m
                        tipo_calculo = f"Auto ML ({nom})"
                    except: pass

            resultados_archivo.append({
                "archivo": nombre_archivo,
                "pagina": i + 1,
                "dimensiones": dims_txt,
                "cobertura": f"{porcentaje*100:.1f}%",
                "tipo": columna,
                "detalle": tipo_calculo,
                "precio": int(round(precio_final, -2))
            })
            
        return resultados_archivo