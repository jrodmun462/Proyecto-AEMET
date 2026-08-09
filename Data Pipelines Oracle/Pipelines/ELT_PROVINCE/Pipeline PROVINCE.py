from pathlib import Path
import sys
import os
import pandas as pd

# Subimos dos niveles de forma limpia en el árbol de carpetas
ruta_script = os.path.dirname(__file__)                  # Pipeline MUNICIPALITIES
ruta_pipelines = os.path.dirname(ruta_script)            # Pipelines
ruta_raiz_oracle = os.path.dirname(ruta_pipelines)       # Data Pipelines Oracle

# Construimos la ruta hacia los clientes de conexión
ruta_conexionOracle = os.path.join(ruta_raiz_oracle, "ConexionClient")
ruta_conexionAemet = os.path.join(ruta_raiz_oracle, "AemetClient")
# Añadimos la ruta al path de Python si no está ya
if ruta_conexionOracle not in sys.path:
    sys.path.append(ruta_conexionOracle)
    sys.path.append(ruta_conexionAemet)

# Ahora sí, importamos el cliente sin errores
from OracleClient import OracleClient
from AemetClient import AemetClient

def localizarArchivoCodIne():
    # Obtiene la carpeta exacta donde está este script actual
    script_dir = Path(__file__).resolve().parent
    
    # Sube 3 niveles hacia atrás para llegar a la raíz (PROYECTO-AEMET)
    # script_dir es 'ELT_PROVINCE' -> .parent es 'Pipelines' -> .parent.parent es 'Data Pipelines Oracle' -> .parent.parent.parent es la raíz
    raiz_proyecto = script_dir.parent.parent.parent
    
    # Construye la ruta apuntando a la nueva carpeta centralizada
    ruta_excel = raiz_proyecto / "Archivos de Extracción" / "Codigo de las provincias en la INE.xlsx"

    return ruta_excel

def localizarArchivoProvincias():
    # Obtiene la carpeta exacta donde está este script actual
    script_dir = Path(__file__).resolve().parent
    
    # Sube 3 niveles hacia atrás para llegar a la raíz (PROYECTO-AEMET)
    # script_dir es 'ELT_PROVINCE' -> .parent es 'Pipelines' -> .parent.parent es 'Data Pipelines Oracle' -> .parent.parent.parent es la raíz
    raiz_proyecto = script_dir.parent.parent.parent
    
    # Construye la ruta apuntando a la nueva carpeta centralizada
    ruta_json = raiz_proyecto / "Archivos de Extracción" / "Provincias.json"

    return ruta_json

def extraerCodIne():
    # Extraer dato
    dir = localizarArchivoCodIne()
    df = pd.read_excel(dir, engine='openpyxl')
    return df

def extraerProvincias():
    # Extraer dato
    dir = localizarArchivoProvincias()
    df = pd.read_json(dir)
    return df

def confirmacion(listaFallos,listaParaInsertar):
    db = OracleClient()
    # --- Resumen, siempre se muestra, haya o no fallos ---
    print(f"\n{len(listaParaInsertar)} registros listos para insertar.")

    if listaFallos:
        print("\n".join(listaFallos))
        print()

    # --- Confirmación, siempre se pregunta ---
    respuesta = input("¿Quiere realizar commit? S/N: ").upper()

    while respuesta != "S" and respuesta != "N":
        print("Opción no válida. Por favor, introduzca S o N.")
        respuesta = input("¿Quiere realizar commit? S/N: ").upper()

    if respuesta == "S":
        db.connect()
        db.insertar_provincias_masivo(listaParaInsertar)
        print("Commit realizado con éxito.")
    else:
        print("Volcado cancelado por el usuario")

    db.close()

def pipeline():
    
    lista = extraerCodIne()
    listaProvJSON = extraerProvincias()
    listaFallos = []
    listaParaInsertar = []  # <-- aquí guardamos los registros válidos
    x = 1

    for indice, fila in lista.iterrows():
        codigo = fila["COD_INS"]
        nombre = fila["TXT_NAM"]

        codProvinceJson = listaProvJSON.loc[listaProvJSON["provincia"] == nombre, "aemet__code"].values

        if len(codProvinceJson) == 0:
            if len(listaFallos) == 0:
                listaFallos.append("--------ADVERTENCIA--------")
                listaFallos.append("Se han encontrado registros sin coincidencias.")
            listaFallos.append(f" '{x}'⚠️  Sin coincidencia AEMET para: '{nombre}' (COD_INS={codigo})")
            x += 1
            continue

        codProvince = str(codProvinceJson[0]).strip()

        # En vez de imprimir el string, guardamos los datos para el insert masivo
        listaParaInsertar.append({
            "id_ine_prov": int(codigo),
            "id_comm_aemet": codProvince,
            "nombre_provincia": nombre
        })
    confirmacion(listaFallos,listaParaInsertar)
  
pipeline()
