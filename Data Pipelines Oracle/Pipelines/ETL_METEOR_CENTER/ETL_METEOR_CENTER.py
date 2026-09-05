import sys
import os
import time
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
from detectarProvincia import analizarProvincia


# Preparamos los datos
BASE_URL = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"

def revisarListaDeFallos(listaFallos):
    if len(listaFallos) != 0:
        print(f"Se han detectado {len(listaFallos)} centros que no se insertarian en caso de commit:")
        respuesta = input("¿Quiere verlos? S/N: ").upper()

        while respuesta != "S" and respuesta != "N":
            print("Opción no válida. Por favor, introduzca S o N.")
            respuesta = input("¿Quiere realizar commit? S/N: ").upper()

        if respuesta == "S":
            print("\n".join(listaFallos))
            print()

def confirmacion(listaFallos,listaParaInsertar,cantidadRegistrosValidos,cantidadTotal):
    db = OracleClient()
    # --- Resumen, siempre se muestra, haya o no fallos ---
    print(f"\n{cantidadRegistrosValidos}/{cantidadTotal} registros listos para insertar.")

    revisarListaDeFallos(listaFallos)

    # --- Confirmación, siempre se pregunta ---
    respuesta = input("¿Quiere realizar commit? S/N: ").upper()

    while respuesta != "S" and respuesta != "N":
        print("Opción no válida. Por favor, introduzca S o N.")
        respuesta = input("¿Quiere realizar commit? S/N: ").upper()

    if respuesta == "S":
        db.insertar_centros_masivo(listaParaInsertar)
    else:
        print("Volcado cancelado por el usuario")

    db.close()

def listaMeteorCenter(listaParaInsertar,indicativo,idProv,nombre,latitud,hemisLat,longitud,hemisLongt,altitud):

    listaParaInsertar.append({
                "idCenter": indicativo,
                "idProv": int(idProv),
                "namCenter": nombre,
                "numLatitude": latitud,
                "hemisphereLat": hemisLat,
                "numLongitude": longitud,
                "hemisphereLongt": hemisLongt,
                "numElevation": altitud,
        })
    return listaParaInsertar

def errorDeDatos(listaFallos,nombre,indicativo,provincia,idProv):
    listaFallos.append(f"⚠️ El centro {nombre} con su identificador {indicativo} con provincia sin limpiar {provincia} en la provincia limpiada {idProv} no existe en base de datos.")

def extraerCentrosAemet():
    ac = AemetClient()
    db = OracleClient()
    dp = analizarProvincia()

    listaFallos = []
    listaParaInsertar = []  # <-- aquí guardamos los registros válidos

    cantidadValida = 0
    
    # Extraer dato
    lista=ac.getDataFrame(BASE_URL)
    cantidadTotal = len(lista)
    db.connect() 
    try:
        with db.conexion.cursor() as cursor:
            for fila in lista.itertuples():
                idProv = None  # Reiniciamos idProv para la siguiente iteración                    
                idProv = dp.buscarNombre(fila.provincia,cursor)                        
                if idProv is not None:
                    hemisLat = str(fila.latitud)[-1]  # Tomamos el último carácter de la latitud para determinar el hemisferio
                    hemisLongt = str(fila.longitud)[-1]  # Tomamos el último carácter de la longitud para determinar el hemisferio
                    latitud = int(fila.latitud[:-1])  # Tomamos todos los caracteres excepto el último para obtener la latitud numérica
                    longitud = int(fila.longitud[:-1])  # Tomamos todos los caracteres excepto el último para obtener la longitud numérica
                    listaParaInsertar = listaMeteorCenter(listaParaInsertar,fila.indicativo,idProv,fila.nombre,latitud,hemisLat,longitud,hemisLongt,fila.altitud)
                    cantidadValida += 1
                    
                else:
                    errorDeDatos(listaFallos, fila.nombre, fila.indicativo, fila.provincia, idProv)

            confirmacion(listaFallos,listaParaInsertar,cantidadValida,cantidadTotal)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    finally:
        db.close()
extraerCentrosAemet()