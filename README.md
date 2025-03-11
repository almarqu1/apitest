# API de Carga y Descarga de Archivos

Una API simple y eficiente para la carga, descarga y gestión de archivos, construida con Flask.

## Características

- Carga de archivos con verificación de tipos permitidos
- Descarga de archivos con nombres originales preservados
- Listado de todos los archivos almacenados
- Eliminación de archivos específicos
- Autenticación mediante clave API
- Registro de todas las operaciones
- Interfaz web simple para pruebas

## Requisitos

- Python 3.6 o superior
- Flask
- Werkzeug

## Instalación

1. Clona este repositorio:
   ```
   git clone https://github.com/usuario/api-archivos.git
   cd api-archivos
   ```

2. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

3. Configura las variables de entorno (opcional):
   ```
   export SECRET_KEY="tu-clave-secreta"
   export API_KEY="tu-clave-api"
   ```

## Ejecución

Para iniciar el servidor:

```
python app.py
```

Por defecto, el servidor se ejecutará en `http://127.0.0.1:5000`.

## Uso de la API

### Carga de archivo (POST /upload)

Requiere autenticación con encabezado `X-API-Key`.

**Python:**
```python
import requests

url = "http://127.0.0.1:5000/upload"
headers = {"X-API-Key": "tu-clave-api"}
files = {"file": ("nombre_archivo.pdf", open("ruta/a/archivo.pdf", "rb"))}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

### Descarga de archivo (GET /download/{filename})

No requiere autenticación.

**Python:**
```python
import requests

url = "http://127.0.0.1:5000/download/nombre_archivo"
response = requests.get(url, stream=True)

if response.status_code == 200:
    with open("archivo_descargado.pdf", "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            f.write(chunk)
```

### Listar archivos (GET /files)

Requiere autenticación con encabezado `X-API-Key`.

**Python:**
```python
import requests

url = "http://127.0.0.1:5000/files"
headers = {"X-API-Key": "tu-clave-api"}

response = requests.get(url, headers=headers)
print(response.json())
```

### Eliminar archivo (DELETE /files/{filename})

Requiere autenticación con encabezado `X-API-Key`.

**Python:**
```python
import requests

url = "http://127.0.0.1:5000/files/nombre_archivo"
headers = {"X-API-Key": "tu-clave-api"}

response = requests.delete(url, headers=headers)
print(response.json())
```

## Configuración

La aplicación permite configurar:

- `UPLOAD_FOLDER`: Carpeta donde se almacenan los archivos
- `MAX_CONTENT_LENGTH`: Tamaño máximo de archivo (16MB por defecto)
- `ALLOWED_EXTENSIONS`: Extensiones de archivo permitidas
- `SECRET_KEY`: Clave secreta para la aplicación
- `API_KEY`: Clave para autenticar solicitudes a la API

## Seguridad

- Las claves API deben mantenerse seguras
- Los nombres de archivo se sanitizan con `secure_filename`
- Se utiliza UUID para evitar conflictos de nombres
- Se verifica el tipo de archivo antes de la carga

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request para sugerencias y mejoras.

## Licencia

[MIT](LICENSE)
