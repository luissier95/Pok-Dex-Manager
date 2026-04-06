# DOCUMENTACION TECNICA ACTUALIZADA: POKEDEX ANALYTICS PRO
-------------------------------------------------------

## 1. DESCRIPCION DEL PROYECTO
#### Sistema de Business Intelligence para la gestión de activos Pokemon, con integración de Visión Artificial (Gemini 2.5 Flash) y persistencia en Google Sheets API.

## 2. ESPECIFICACIONES DEL ENTORNO (DEPENDENCIAS COMPLETAS)

#### Para garantizar el funcionamiento de los módulos de autenticación de Google y el procesamiento de imágenes, instale el siguiente conjunto de librerías:

## COMANDO DE INSTALACION:
#### pip install fastapi uvicorn requests google-genai pillow google-api-python-client google-auth-httplib2 google-auth-oauthlib passlib[pbkdf2] python-multipart

## DESGLOSE DE LIBRERIAS CRITICAS:
#### - fastapi: Framework core para la API.
#### - uvicorn: Servidor para ejecutar la aplicación.
#### - google-genai: SDK para la identificación por IA (Gemini).
#### - google-api-python-client: Cliente para manipular Google Sheets.
#### - google-auth-oauthlib: Manejo de flujo de credenciales JSON.
#### - google-auth-httplib2: Transporte para la autenticación de Google.
#### - python-multipart: Necesaria para recibir archivos (UploadFile) desde el frontend.
#### - passlib[pbkdf2]: Cifrado de contraseñas de usuarios.
#### - pillow: Procesamiento de archivos de imagen (PIL).
#### - requests: Consumo de la PokeAPI externa.

## 3. CONFIGURACION DE ARCHIVOS MAESTROS

## El proyecto requiere la presencia de los siguientes archivos en el directorio raíz:
#### 1. main.py (Código lógico del servidor)
#### 2. index.html (Interfaz de usuario)
#### 3. credentials.json (Llave de cuenta de servicio de Google Cloud)

## 4. ESTRUCTURA DE LA BASE DE DATOS (GOOGLE SHEETS)

## El sistema opera mediante un proceso ETL (Extract, Transform, Load) que organiza los datos de la siguiente manera:
#### - Hoja 'Users_DB': Almacena Username y Password (Hashed).
#### - Hoja 'Coleccion_{Usuario}': Dataset con 12 columnas técnicas (ID, Nombre, Tipo, Altura, Peso, HP, Atk, Def, Spd, Skills, Moves, User).

## 5. ENDPOINTS DE LA API

#### - POST /api/register: Genera usuario y base de datos personal en la nube.
#### - POST /api/login: Autenticación mediante comparación de hashes.
#### - POST /api/ai-identify: Identificación visual de Pokemon via Gemini.
#### - GET /api/pokemon/{name}: Extracción de metadatos desde PokeAPI.
#### - POST /api/favorites: Persistencia de datos transformados en el Spreadsheet.
#### - GET /api/collection: Extracción de registros para el Dashboard de BI.
-------------------------------------------------------
## Desarrollado por: Luis Angel Sierra Fragoso
