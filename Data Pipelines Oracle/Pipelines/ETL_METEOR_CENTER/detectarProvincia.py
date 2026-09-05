import sys
import os

ruta_script = os.path.dirname(__file__)                  # Pipeline MUNICIPALITIES
ruta_pipelines = os.path.dirname(ruta_script)            # Pipelines
ruta_raiz_oracle = os.path.dirname(ruta_pipelines)       # Data Pipelines Oracle

# Construimos la ruta hacia los clientes de conexión
ruta_conexionOracle = os.path.join(ruta_raiz_oracle, "ConexionClient")

# Añadimos las rutas al path de Python si no están añadidas ya
if ruta_conexionOracle not in sys.path:
    sys.path.append(ruta_conexionOracle)

# Importamos tus clientes personalizados de conexión
from OracleClient import OracleClient

class analizarProvincia:
    def buscarNombre(self,namProv,cursor):
        db = OracleClient()
        nombre_formateado = namProv.title()
                
        # Comprobación de coincidencia exacta en la base de datos
        id_prov = db.existeProvincia(nombre_formateado, cursor)
        if id_prov is not None:
            return id_prov
            
        # Búsqueda parcial usando el nombre completo
        id_prov_parcial = db.buscarProvinciaParcial(nombre_formateado, cursor)
        if id_prov_parcial is not None:
            return id_prov_parcial
            
        # Si tiene espacios, buscar usando la parte posterior al primer espacio (ej: "Las Palmas" -> "Palmas")
        if " " in namProv:
            partes = namProv.split(' ', 1)
            segunda_parte = partes[1].title()
            id_prov_parcial_2 = db.buscarProvinciaParcial(segunda_parte, cursor)
            if id_prov_parcial_2 is not None:
                return id_prov_parcial_2
        if namProv == "BALEARES":
            return 7
        return None