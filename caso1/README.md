# Caso práctico 1 — Droply

Aplicación web para descargar contenido multimedia público o autorizado desde YouTube, Instagram, TikTok, Facebook y LinkedIn. Incluye selección de calidad, extracción de audio MP3, progreso en tiempo real, eliminación automática de archivos y una interfaz adaptable a celulares.

> Utiliza la aplicación únicamente con contenido propio, de dominio público o para el que tengas autorización. La disponibilidad depende de cada plataforma; el contenido privado, protegido o con restricciones geográficas puede requerir autenticación o no estar disponible.

## Tecnologías

- Python 3.11 y Flask
- yt-dlp para extracción y descarga
- FFmpeg para combinar audio/video y generar MP3
- Node.js como motor JavaScript requerido por el soporte completo de YouTube
- Gunicorn como servidor WSGI
- Docker

## Ejecución con Docker

Desde la carpeta `caso1`:

```bash
docker build -t droply:1.0 .
docker run --rm -p 5000:5000 --name droply droply:1.0
```

Abre <http://localhost:5000>.

Los archivos generados se eliminan del contenedor después de una hora. Para conservar temporalmente el directorio entre reinicios puedes montar un volumen:

```bash
docker run --rm -p 5000:5000 -v droply_downloads:/app/downloads droply:1.0
```

## Variantes de imagen

### Dockerfile estándar

```bash
docker build -t droply:standard -f Dockerfile .
```

Incluye las dependencias en una imagen Debian Slim y ejecuta Gunicorn.

### Dockerfile optimizado

```bash
docker build -t droply:optimized -f Dockerfile.optimizado .
```

Reduce capas, copia únicamente los archivos necesarios, ejecuta con usuario no root e incorpora un `HEALTHCHECK`.

### Dockerfile multistage

```bash
docker build -t droply:multistage -f Dockerfile.multistage .
```

Instala los paquetes de Python en una etapa de construcción y copia el entorno virtual a la imagen final.

Para comparar tamaños:

```bash
docker images --filter reference="droply:*"
```

## Ejecución local

Requiere Python 3.11 o superior y FFmpeg disponible en el `PATH`.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Interfaz web |
| `GET` | `/health` | Estado del servicio |
| `POST` | `/api/downloads` | Inicia una descarga |
| `GET` | `/api/downloads/<id>` | Consulta el progreso |
| `GET` | `/api/downloads/<id>/file` | Entrega el archivo terminado |

Ejemplo de solicitud:

```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "quality": "720"
}
```

Calidades disponibles: `best`, `1080`, `720`, `480` y `audio`.

## Configuración

| Variable | Valor predeterminado | Uso |
|---|---:|---|
| `PORT` | `5000` | Puerto HTTP |
| `MAX_WORKERS` | `2` | Descargas simultáneas |
| `DOWNLOAD_TTL_SECONDS` | `3600` | Tiempo de conservación |
| `DOWNLOAD_DIR` | `/app/downloads` | Directorio temporal |

## Estructura

```text
caso1/
├── app.py
├── templates/index.html
├── static/styles.css
├── static/app.js
├── tests/test_app.py
├── Dockerfile
├── Dockerfile.optimizado
├── Dockerfile.multistage
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Consideraciones de compatibilidad

Las plataformas cambian con frecuencia. Mantén `yt-dlp` actualizado cuando un extractor deje de funcionar. Algunas publicaciones de Instagram, Facebook, TikTok o LinkedIn solo funcionan durante una sesión autenticada; esta entrega no almacena cookies ni credenciales y se limita a enlaces públicos.

## Repositorio

<https://github.com/luisdionicio-lgtm/LAB04_DOCKER>
