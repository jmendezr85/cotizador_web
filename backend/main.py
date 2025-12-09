from fastapi import FastAPI, UploadFile, File, Form
from typing import List
from backend.logic import CotizadorMotor
import os

app = FastAPI(title="Cotizador Plotter Multi-Modo")

base_dir = os.path.dirname(os.path.abspath(__file__))
ruta_csv = os.path.join(base_dir, "data", "precios.csv")
motor = CotizadorMotor(ruta_csv)

@app.post("/cotizar_lote/")
async def cotizar_lote(
    files: List[UploadFile] = File(...),
    modo: str = Form("AUTO") # Nuevo parámetro que recibe el modo (AUTO, PLIEGO, MEDIO, etc.)
):
    todos_los_resultados = []
    
    for file in files:
        if file.filename.endswith(".pdf"):
            try:
                contenido = await file.read()
                # Pasamos el "modo" al motor lógico
                resultados_pdf = motor.analizar_archivo(contenido, file.filename, modo)
                todos_los_resultados.extend(resultados_pdf)
            except Exception as e:
                print(f"Error procesando {file.filename}: {e}")
    
    gran_total = sum(item['precio'] for item in todos_los_resultados)
    
    return {
        "items": todos_los_resultados,
        "total_global": gran_total
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)