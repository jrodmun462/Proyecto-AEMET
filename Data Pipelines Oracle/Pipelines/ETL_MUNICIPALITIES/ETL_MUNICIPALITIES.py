import sys
import os
import json
import pandas as pd

# 1. Subimos dos niveles de forma limpia en el árbol de carpetas
ruta_script = os.path.dirname(__file__)                  # Pipeline MUNICIPALITIES
ruta_pipelines = os.path.dirname(ruta_script)            # Pipelines
ruta_raiz_oracle = os.path.dirname(ruta_pipelines)       # Data Pipelines Oracle

# 2. Construimos la ruta hacia los clientes de conexión
ruta_conexionOracle = os.path.join(ruta_raiz_oracle, "ConexionClient")
ruta_conexionAemet = os.path.join(ruta_raiz_oracle, "AemetClient")
# 3. Añadimos la ruta al path de Python si no está ya
if ruta_conexionOracle not in sys.path:
    sys.path.append(ruta_conexionOracle)
    sys.path.append(ruta_conexionAemet)

# 4. Ahora sí, importamos el cliente sin errores
from OracleClient import OracleClient
from AemetClient import AemetClient


# Preparamos los datos
print("ELT para la inserción de datos en PROVINCE en Oracle")
BASE_URL = "https://opendata.aemet.es/opendata/api/maestro/municipios/"
BASE_URL2 = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"
def extraerMunicipiosAemet():
    ac = AemetClient()
    db = OracleClient()
    # Extraer dato
    info1=ac.getDataFrame(BASE_URL)
    info2=ac.getDataFrame(BASE_URL2)
    info3= ac._realizar_peticion(BASE_URL)

    print("DataFrame1:\n", info1.head(100),"\n")
    print("DataFrame2:\n", info2.head(100))

extraerMunicipiosAemet()