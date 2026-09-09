# Laboratorio 04 — Docker

Repositorio con los dos casos prácticos de la semana 4. Cada aplicación está aislada en su propia carpeta, incluye tres variantes de `Dockerfile`, pruebas y documentación específica.

## Requisitos

- Docker Desktop instalado y en ejecución.
- Puertos `5050` y `5080` disponibles.
- Git, únicamente si se desea clonar el repositorio.

## Obtener el proyecto

```bash
git clone https://github.com/luisdionicio-lgtm/LAB04_DOCKER.git
cd LAB04_DOCKER
```

## Caso 1 — Droply

Aplicación web para procesar descargas de contenido multimedia público o autorizado. Ofrece selección de calidad, progreso de la descarga y eliminación automática de archivos temporales.

- [Código y documentación del Caso 1](caso1/)
- [README detallado del Caso 1](caso1/README.md)

### Instalación y ejecución

Ejecuta estos comandos desde la raíz del repositorio:

```bash
docker build -f caso1/Dockerfile.optimizado -t droply:caso1 caso1
docker run -d --name droply-caso1 -p 5050:5000 -v droply-downloads:/app/downloads droply:caso1
```

Abre [http://localhost:5050](http://localhost:5050).

Para detenerlo y volver a iniciarlo:

```bash
docker stop droply-caso1
docker start droply-caso1
```

Usa Droply únicamente con contenido propio, de dominio público o con autorización.

## Caso 2 — Mesa Clara

Aplicación local para importar DNIs desde Excel, organizar la verificación individual en ONPE, registrar la ubicación electoral y exportar el consolidado de miembros de mesa.

- [Código y documentación del Caso 2](caso2/)
- [README detallado del Caso 2](caso2/README.md)

### Instalación y ejecución

Ejecuta estos comandos desde la raíz del repositorio:

```bash
docker build -f caso2/Dockerfile.optimizado -t mesa-clara:caso2 caso2
docker run -d --name mesa-clara-caso2 -p 5080:5000 -v mesa-clara-data:/app/data mesa-clara:caso2
```

Abre [http://localhost:5080](http://localhost:5080).

Para detenerlo y volver a iniciarlo:

```bash
docker stop mesa-clara-caso2
docker start mesa-clara-caso2
```

Los DNIs permanecen en el volumen local `mesa-clara-data`. La consulta oficial se realiza de forma asistida y la aplicación no intenta evadir CAPTCHA ni controles del portal.

## Ejecutar ambos casos

Los puertos son diferentes, por lo que ambas aplicaciones pueden funcionar al mismo tiempo:

| Caso | Contenedor | Dirección local |
|---|---|---|
| Caso 1 — Droply | `droply-caso1` | <http://localhost:5050> |
| Caso 2 — Mesa Clara | `mesa-clara-caso2` | <http://localhost:5080> |

Comprueba el estado con:

```bash
docker ps --filter name=droply-caso1 --filter name=mesa-clara-caso2
```

En la columna `STATUS`, ambos contenedores deben aparecer como `healthy` después de unos segundos.

## Detener ambos casos

```bash
docker stop droply-caso1 mesa-clara-caso2
```

Repositorio: <https://github.com/luisdionicio-lgtm/LAB04_DOCKER>
