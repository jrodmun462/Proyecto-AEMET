import oracledb
import sys
import os
from dotenv import load_dotenv
oracledb.init_oracle_client(lib_dir=r"C:\instantclient_ 23_26\instantclient_23_26")

load_dotenv()  
class OracleClient:
    def __init__(self):
        """Inicializa los parámetros de configuración de la base de datos."""
        self.user = os.getenv("ORACLE_USER")
        self.password = os.getenv("ORACLE_PASSWORD")
        self.dsn = os.getenv("ORACLE_DSN")
        self.conexion = None

    def connect(self):
        """Establece la conexión física con el servidor Oracle."""
        try:
            if not self.conexion:
                print("Intentando conectar a la base de datos Oracle...")
                self.conexion = oracledb.connect(
                    user=self.user,
                    password=self.password,
                    dsn=self.dsn
                )
                print(f"¡Conexión establecida con éxito! (Versión: {self.conexion.version})")
            return self.conexion
        except oracledb.Error as e:
            print(f"❌ Error al conectar a Oracle: {e}")
            sys.exit(1)

    def select(self, query, parametros=None):
        """Ejecuta una consulta de lectura (SELECT) y devuelve los resultados."""
        self.connect()
        try:
            with self.conexion.cursor() as cursor:
                if parametros:
                    cursor.execute(query, parametros)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
        except oracledb.Error as e:
            print(f"❌ Error al ejecutar consulta SQL: {e}")
            return None

    def execute(self, query, parametros=None):
        """Ejecuta una acción de escritura (INSERT, UPDATE, DELETE, CREATE)."""
        self.connect()
        try:
            with self.conexion.cursor() as cursor:
                if parametros:
                    cursor.execute(query, parametros)
                else:
                    cursor.execute(query)
                # Aplicamos commit para guardar los cambios de forma permanente
                self.conexion.commit()
                print("Operación completada y guardada (COMMIT) con éxito.")
                return True
        except oracledb.Error as e:
            print(f"❌ Error en la operación SQL: {e}")
            
            self.conexion.rollback()  # Deshace cambios si hubo un fallo
            return False
        
    def insertar_provincias_masivo(self, lista_provincias):
        """Carga masiva de provincias en la tabla PROVINCE."""
        query = """
            INSERT INTO PROVINCE (ID_PROV, ID_COMM, NAM_PROV, DATE_OPRTN_INSERT)
            VALUES (
                :id_ine_prov,
                (SELECT DISTINCT ID_COMM FROM AUT_COMM WHERE ID_AEMET_COMM = :id_comm_aemet),
                :nombre_provincia,
                SYSTIMESTAMP
            )
        """
        self.connect()
        try:
            with self.conexion.cursor() as cursor:
                cursor.executemany(query, lista_provincias)
                self.conexion.commit()
                print(f"✅ {len(lista_provincias)} registros insertados y confirmados (COMMIT).")
                return True
        except oracledb.Error as e:
            print(f"❌ Error en la inserción masiva: {e}")
            self.conexion.rollback()
            return False

    def insertar_comunidades_masivo(self, lista_comunidades):
        """Carga masiva de comunidades autónomas en la tabla AUT_COMM."""

        query = """
            INSERT INTO AUT_COMM (ID_AEMET_COMM, NAM_COMM,  DATE_OPRTN_INSERT)
            VALUES (
                :id_aemet_com,
                :nam_comm,
                SYSTIMESTAMP
            )
        """
        self.connect()
        try:
            with self.conexion.cursor() as cursor:
                cursor.executemany(query, lista_comunidades)
                self.conexion.commit()
                print(f"✅ {len(lista_comunidades)} registros insertados y confirmados (COMMIT).")
                return True
        except oracledb.Error as e:
            print(f"❌ Error en la inserción masiva: {e}")
            self.conexion.rollback()
            return False

    def comprobar_provincia_existente(self, idProv):
        """Comprueba si hay algun municipio que tenga una provincia que no tenga código."""
        query = "SELECT COUNT(*) FROM PROVINCE WHERE ID_PROV= :idProv"
        self.connect()
        try:
            with self.conexion.cursor() as cursor:
                cursor.execute(query, {"idProv": idProv})
                count = cursor.fetchone()[0]
                return count
        except oracledb.Error as e:
            print(f"❌ Error al comprobar provincia existente: {e}")
            return False

    def insertar_municipios_masivo(self, lista_municipios):
        """Carga masiva de municipios en la tabla MUNICIPALITIES."""
        query = """
            MERGE INTO MUNICIPALITIES M
                USING (SELECT :id_mun AS id_mun, :id_mun_aemet AS id_mun_aemet, :id_prov AS id_prov, :nam_mun AS nombre FROM DUAL) D
                ON (M.ID_MUN_AEMET = D.id_mun_aemet AND M.ID_PROV = D.id_prov)
            WHEN NOT MATCHED THEN
                INSERT (ID_MUN, ID_MUN_AEMET, ID_PROV, NAM_MUN) VALUES (D.id_mun, D.id_mun_aemet, D.id_prov, D.nombre)
        """
        query2= "SELECT COUNT(*) FROM MUNICIPALITIES"
        self.connect()
        try:
            vacio = True
            with self.conexion.cursor() as cursor:
                #Comprobamos si ya hay registros en la tabla MUNICIPALITIES
                cursor.execute(query2)
                total_registros = cursor.fetchone()[0]
                if total_registros > 0:
                    print(f"⚠️ Aviso: La tabla no esta vacia. Hay Registros que no han sido insertados para evitar duplicados.")
                    vacio = False

                cursor.executemany(query, lista_municipios)
                self.conexion.commit()
                if vacio == True:
                    print(f"✅ Registros insertados y confirmados (COMMIT).")
                return True
        except oracledb.Error as e:
            print(f"❌ Error en la inserción masiva: {e}")
            self.conexion.rollback()
            return False

    def close(self):
        """Cierra la conexión de forma segura si está abierta."""
        if self.conexion:
            self.conexion.close()
            self.conexion = None
            print("Conexión con Oracle cerrada correctamente.")
