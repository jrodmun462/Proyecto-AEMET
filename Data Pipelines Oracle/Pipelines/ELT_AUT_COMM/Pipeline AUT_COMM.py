from pathlib import Path
import sys
import os
import pandas as pd

# 1. Subimos dos niveles de forma limpia en el árbol de carpetas
ruta_script = os.path.dirname(__file__)                  # Pipeline PROVINCE
ruta_pipelines = os.path.dirname(ruta_script)            # Pipelines
ruta_raiz_oracle = os.path.dirname(ruta_pipelines)       # Data Pipelines Oracle

# 2. Construimos la ruta hacia los clientes de conexión
ruta_conexion = os.path.join(ruta_raiz_oracle, "ConexionClient")

# 3. Añadimos la ruta al path de Python si no está ya
if ruta_conexion not in sys.path:
    sys.path.append(ruta_conexion)

# 4. Importamos el cliente
from OracleClient import OracleClient

def localizarArchivoComunidadAutonoma():
    # Obtiene la carpeta exacta donde está este script actual
    script_dir = Path(__file__).resolve().parent
    
    # Sube 3 niveles hacia atrás para llegar a la raíz (PROYECTO-AEMET)
    # script_dir es 'ELT_PROVINCE' -> .parent es 'Pipelines' -> .parent.parent es 'Data Pipelines Oracle' -> .parent.parent.parent es la raíz
    raiz_proyecto = script_dir.parent.parent.parent
    
    # Construye la ruta apuntando a la nueva carpeta centralizada
    ruta_json = raiz_proyecto / "Archivos de Extracción" / "Comunidad autonoma.json"

    return ruta_json

def extraerComunidades():
    # Extraer dato
    dir = localizarArchivoComunidadAutonoma()
    df = pd.read_json(dir)
    return df

def confirmacion(listaParaInsertar):
    db = OracleClient()
    # --- Resumen, siempre se muestra, haya o no fallos ---
    print(f"\n{len(listaParaInsertar)} registros listos para insertar.")

    # --- Confirmación, siempre se pregunta ---
    respuesta = input("¿Quiere realizar commit? S/N: ").upper()

    while respuesta != "S" and respuesta != "N":
        print("Opción no válida. Por favor, introduzca S o N.")
        respuesta = input("¿Quiere realizar commit? S/N: ").upper()

    if respuesta == "S":
        db.insertar_comunidades_masivo(listaParaInsertar)
    else:
        print("Volcado cancelado por el usuario")

    db.close()

def pipeline():
    
    lista = extraerComunidades()
    listaParaInsertar = []  # <-- aquí guardamos los registros válidos

    for indice, fila in lista.iterrows():
        codigo = fila["id_aemet_comm"]
        nombre = fila["nam_comm"]

        # En vez de imprimir el string, guardamos los datos para el insert masivo
        listaParaInsertar.append({
            "id_aemet_com": codigo,
            "nam_comm": nombre,
        })
    confirmacion(listaParaInsertar)
pipeline()