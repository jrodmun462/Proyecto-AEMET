import sys
import os

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
BASE_URL = "https://opendata.aemet.es/opendata/api/maestro/municipios/"

def revisarListaDeFallos(listaFallos):
    if len(listaFallos) != 0:
        print(f"Se han detectado {len(listaFallos)} municipios que no se insertarian en caso de commit:")
        respuesta = input("¿Quiere verlos? S/N: ").upper()

        while respuesta != "S" and respuesta != "N":
            print("Opción no válida. Por favor, introduzca S o N.")
            respuesta = input("¿Quiere realizar commit? S/N: ").upper()

        if respuesta == "S":
            print("\n".join(listaFallos))
            print()

def confirmacion(listaFallos,listaParaInsertar,cantidadRegistrosValidos):
    db = OracleClient()
    # --- Resumen, siempre se muestra, haya o no fallos ---
    print(f"\n{cantidadRegistrosValidos} registros listos para insertar.")

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

def formatearNombreMunicipio(nombre):
    # Creamos una tabla de traducción mapeando cada tilde con su letra limpia
    tabla_tildes = str.maketrans({
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U"
    })
    
    # Aplicamos la traducción al texto recibido
    return nombre.translate(tabla_tildes)

def extraerMunicipiosAemet():
    ac = AemetClient()
    db = OracleClient()
    listaParaInsertar = []  # <-- aquí guardamos los registros válidos
    listaFallos = []
    x = 0
    # Extraer dato
    lista=ac.getDataFrame(BASE_URL)

    db.connect() 
    try:
        with db.conexion.cursor() as cursor:
            for fila in lista.itertuples():

                codMunicipioDF = str(fila.id)
                nombreMunicipio = formatearNombreMunicipio(str(fila.nombre))
        
                #Sacamos el código de la provincia a partir del código del municipio
                codProvincia = codMunicipioDF[2:4]
                codMunicipio = codMunicipioDF[4:7]
                comprobar = db.comprobar_provincia_existente(codProvincia,cursor)
                if comprobar == 0:
                    listaFallos.append(f"⚠️ El municipio {nombreMunicipio} con código {codMunicipioDF} no se ha insertado porque la provincia con código {codProvincia} no existe en la base de datos.")
                    
                else:
                    x += 1
                    listaParaInsertar.append({
                        "id_mun": None,  # Se deja como None para que el trigger genere el ID automáticamente
                        "id_mun_aemet": codMunicipio,
                        "id_prov": codProvincia,
                        "nam_mun": nombreMunicipio
                    })
        confirmacion(listaFallos,listaParaInsertar,x)

    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    finally:
        db.close()

extraerMunicipiosAemet()