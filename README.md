# Proyecto AEMET

Proyecto de portfolio que simula una migración de una base de datos on-premise (Oracle) a Azure, utilizando **Azure Data Factory** para orquestar procesos de **ETL/ELT**. Como caso de uso real para poblar el modelo de datos, se integra la **API pública de AEMET OpenData** y el catálogo de códigos del **INE**.

## Objetivo del proyecto

Demostrar el ciclo de trabajo de un Data Engineer:
- Diseño de un modelo de datos relacional en Oracle.
- Ingesta de datos desde fuentes externas (API REST, ficheros oficiales).
- Procesos de extracción, transformación y carga con control de calidad de datos.
- Migración de un modelo relacional Oracle → Azure SQL Database orquestada con Azure Data Factory.

## Arquitectura de datos

### ETL en Python (Oracle)

Todos los pipelines de carga en Oracle siguen el mismo patrón, con las tres fases de un ETL real:

- **Extract:** lectura desde múltiples fuentes (ficheros oficiales del INE, API/JSON de AEMET).
- **Transform:** cruce de fuentes por campos comunes, normalización de nombres, resolución de discrepancias entre fuentes (mapeo manual para casos como Baleares/Canarias, donde AEMET modela por islas y el INE por provincia), validación y detección de registros sin coincidencia.
- **Load:** inserción masiva parametrizada (`executemany`) con bind variables (sin inyección SQL), confirmación interactiva del usuario antes de comprometer cambios (modo dry-run + resumen + S/N), y manejo de errores con rollback.

| Pipeline | Fuentes | Estado |
|---|---|---|
| `Pipelines/ETL_AUT_COMM` | JSON AEMET | ✅ Completado |
| `Pipelines/ETL_PROVINCE` | Excel INE + JSON AEMET | ✅ Completado |
| `Pipelines/ETL_MUNICIPALITIES` | API REST AEMET | ✅ Completado|
| `Pipelines/ETL_METEOR_CENTER` | API REST AEMET | 🚧 En progreso |
| `Pipelines/ETL_TIME_REPORT` | ¿? | ¿? |

### Migración a Azure (Azure Data Factory)

En paralelo al ETL en Oracle, se ha montado la infraestructura de migración a la nube:

- **Self-Hosted Integration Runtime** conectando el Oracle local con Azure Data Factory.
- **Linked Services** hacia Oracle (origen) y Azure SQL Database (destino).
- **Datasets** y **Pipeline** con actividades Copy Data para `AUT_COMM` y `PROVINCE`, encadenadas respetando la integridad referencial (FK).
- Esquema de tablas replicado en Azure SQL (T-SQL), incluyendo la traducción de tipos de datos entre motores (Oracle `TIMESTAMP` → SQL Server `DATETIME2`, secuencias → `IDENTITY`, etc.).
- **Control de versiones nativo de ADF** conectado a este mismo repositorio de GitHub (carpeta `/Azure Data Factory`), de modo que cada cambio en los pipelines, datasets y linked services queda versionado como código.

## Modelo de datos

Tablas principales en Oracle (`Model and Tables Oracle/Oracle Tables`), replicadas en Azure SQL (`Model and Tables Oracle/Azure SQL Tables`):

| Tabla | Descripción |
|---|---|
| `AUT_COMM` | Comunidades autónomas de España |
| `PROVINCE` | Provincias, relacionadas con su comunidad autónoma |
| `MUNICIPIO` | Municipios según catálogo de AEMET, relacionados con su provincia |
| `METEOR_CENTER` | Estaciones/centros meteorológicos |
| `TIME_REPORT` | Datos de predicción/observación obtenidos de la API |

*(Diagrama entidad-relación disponible en `Model and Tables Oracle/Data Model`)*

## Tecnologías utilizadas

- **Python** (`requests`, `pandas`, `oracledb`) — extracción, transformación y carga de datos
- **Oracle Database** — almacenamiento origen
- **Azure SQL Database** — almacenamiento destino
- **Azure Data Factory** — orquestación de la migración (Self-Hosted IR, Linked Services, Pipelines)
- **AEMET OpenData API** e **INE** — fuentes de datos externas
- **Git / GitHub** — control de versiones, incluyendo integración nativa con ADF

## Nota sobre el uso de IA
Este proyecto se ha desarrollado con el apoyo de Claude (Anthropic) como asistente
de programación y aprendizaje —para depurar errores, discutir decisiones de diseño
y acelerar la escritura de código—, bajo dirección y revisión propias en cada paso

## Estado del proyecto

- [x] Modelo de datos en Oracle y Azure SQL
- [x] ETL de comunidades autónomas y provincias (doble fuente, INE + AEMET)
- [x] Infraestructura de migración a Azure (Integration Runtime, Linked Services, Datasets)
- [x] Pipeline de ADF: Oracle → Azure SQL para `AUT_COMM` y `PROVINCE`
- [x] Control de versiones de ADF conectado a GitHub
- [x] ETL de municipios desde API de AEMET
- [ ] ETL de centros meteorológicos desde API de AEMET
- [ ] Ingesta de datos de predicción/observación meteorológica
- [ ] Extender el pipeline de ADF a las tablas restantes
- [ ] Automatizar despliegue de ADF con GitHub Actions (CI/CD)

## Próximos pasos

1. Completar el ETL de municipios contra la API en vivo de AEMET.
2. Completar el ETL de centros meteorológicos.
3. Diseñar el pipeline de ingesta de predicciones meteorológicas (datos que cambian frecuentemente → ETL incremental).
4. Extender el pipeline de Azure Data Factory al resto de tablas del modelo.
5. Automatizar el despliegue de ADF con GitHub Actions.