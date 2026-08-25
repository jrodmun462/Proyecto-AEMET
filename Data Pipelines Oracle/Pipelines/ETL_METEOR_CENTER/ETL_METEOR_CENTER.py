import sys
import os
from datetime import datetime

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
BASE_URL = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"
BASE_URL_2 = "https://opendata.aemet.es/opendata/api/valores/climatologicos/mensualesanuales/datos/anioini/{anioIniStr}/aniofin/{anioFinStr}/estacion/{idema}"

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
        db.insertar_municipios_masivo(listaParaInsertar)
    else:
        print("Volcado cancelado por el usuario")

    db.close()

def casosEspeciales(idProv):
    val_sinop = int(idProv)
    if 60001 <= val_sinop <= 60025:
        return 38  # S.C. Tenerife
    elif 60026 <= val_sinop <= 60099:
        return 35  # Las Palmas
    elif 60320 <= val_sinop <= 60329:
        return 51  # Ceuta
    elif 60330 <= val_sinop <= 60339:
        return 52  # Melilla

def listaMeteorCenter(listaParaInsertar,indicativo,idProv,nombre,latitud,hemisLat,longitud,hemisLongt,altitud):

    listaParaInsertar.append({
                "id_center": indicativo,
                "id_prov": idProv,
                "date_start": None,       # pendiente de definir convención (ver nota)
                "date_end": None,         # pendiente de definir convención (ver nota)
                "nam_center": nombre,
                "cod_center_stat": None,  # pendiente del CASE de comparación API vs Oracle
                "num_latitude": latitud,
                "hemisphere_lat": hemisLat,
                "num_longitude": longitud,
                "hemisphere_longt": hemisLongt,
                "num_elevation": altitud,
                "date_oprtn_insert": None  # se rellena en Oracle, por trigger o default SYSTIMESTAMP
        })
    return listaParaInsertar

def errorDeDatos(listaFallos,nombre,indicativo,indsinop,idProv):
    listaFallos.append(f"⚠️ El centro {nombre} con su identificador {indicativo} con provincia sin limpiar {indsinop} en la provincia limpiada {idProv} no existe en base de datos.")

def calcularFechas():
    pass
def calcularEstado():
    pass
def calcularHemisferio():
    pass

def extraerCentrosAemet():
    ac = AemetClient()
    db = OracleClient()
    listaFallos = []
    listaParaInsertar = []  # <-- aquí guardamos los registros válidos

    cantidadValida = 0
    cantidadTotal = 0
    # Extraer dato
    lista=ac.getDataFrame(BASE_URL)
    print(lista)

    for fila in lista.itertuples():
        cantidadTotal += 1
        idProv = 0
        hemisLat = str(fila.latitud)[-1]  # Tomamos el último carácter de la latitud para determinar el hemisferio
        hemisLongt = str(fila.longitud)[-1]  # Tomamos el último carácter de la longitud para determinar el hemisferio
        url = BASE_URL_2.format(anioIniStr="1900", anioFinStr=datetime.now().year, idema=fila.indicativo)
        lista2=ac.getDataFrame(url)
        print(lista2)


        # Si la provincia viene con valor, sacamos su ID_PROV
        if fila.indsinop is not None and fila.indsinop != "":
            idProv = str(fila.indsinop)[0:2]  # <-- Tomamos los dos primeros caracteres del código de provincia

        # Si la provincia viene vacia del dataset, significa que no es que no vaya a casar el codigo con la base de datos, sino que la estacion no opera a nivel nacional. 
        # En este caso, se le asigna el valor 99 (provincia desconocida) y se inserta igualmente.
        if fila.indsinop is None or fila.indsinop == "":
            idProv = 99
            listaMeteorCenter(listaParaInsertar, fila.indsinop, idProv, fila.nombre, fila.latitud, hemisLat, fila.longitud, hemisLongt, fila.altitud)

            cantidadValida += 1
        # Si la provincia viene con valor, se comprueba que exista en la base de datos. Si no existe, se añade a la lista de fallos y no se inserta.
        elif db.comprobar_provincia_centro(idProv)==0:
            if idProv == "60":  # Canarias/África, casos especiales
                # Se comprueba si el código sinop está dentro de los rangos especiales y se asigna la provincia correspondiente. Si no, se añade a la lista de fallos y no se inserta.
                try:
                    idProv = casosEspeciales(fila.indsinop)
                except ValueError:
                    errorDeDatos(listaFallos, fila.nombre, fila.indicativo, fila.indsinop, idProv)

                # Si idProv es None, significa que no se ha podido asignar una provincia válida, por lo que se añade a la lista de fallos y no se inserta. Si idProv tiene un valor válido, se añade a la lista de inserción.
                if idProv is not None:
                    listaMeteorCenter(listaParaInsertar, fila.indsinop, idProv, fila.nombre, fila.latitud, hemisLat, fila.longitud, hemisLongt, fila.altitud)

                    cantidadValida += 1
                else:
                    errorDeDatos(listaFallos, fila.nombre, fila.indicativo, fila.indsinop, idProv)
            else:
                errorDeDatos(listaFallos, fila.nombre, fila.indicativo, fila.indsinop, idProv)
        else:
            listaMeteorCenter(listaParaInsertar, fila.indsinop, idProv, fila.nombre, fila.latitud, hemisLat, fila.longitud, hemisLongt, fila.altitud)

            cantidadValida += 1
    confirmacion(listaFallos,listaParaInsertar,cantidadValida,cantidadTotal)


extraerCentrosAemet()