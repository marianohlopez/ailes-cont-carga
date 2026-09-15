# Carga automática de observaciones de facturas en Indyco

Automatización que sincroniza observaciones de facturas desde un reporte contable en Google Drive hacia la plataforma de gestión **Indyco**, evitando la carga manual y repetitiva por parte del equipo contable.

## ¿Qué hace?

1. **Extrae** las filas marcadas con `A indyco = sí` de las hojas `Alertas` y `Cobradas dentro de los 60 días` de un Excel (`reporte_contable.xlsx`) alojado en una unidad compartida de Google Drive.
2. **Inicia sesión** en Indyco vía Playwright y busca cada factura por su número de comprobante.
3. **Compara** los datos de la factura en Indyco (importe, fecha, período, titular) contra el Excel para confirmar que corresponde a la misma factura antes de tocarla.
4. Si la observación del Excel todavía no está cargada, **edita el campo de observaciones** de la factura en Indyco y guarda los cambios. Si ya estaba cargada, la salta.
5. **Registra el resultado** de la corrida (cantidad de observaciones a ingresar, ingresadas, ya existentes y tiempo total) en base de datos.

Se ejecuta de forma programada una vez por semana mediante **GitHub Actions**.

## Arquitectura

```
main.py       → orquesta el flujo completo
extract.py    → autentica con Google Drive API y extrae las filas del Excel
load.py       → automatiza el login y la carga en Indyco con Playwright
db.py         → registra el resultado de cada corrida
```

## Requisitos

- Python 3.10+
- [Playwright](https://playwright.dev/python/) con navegadores instalados (`playwright install chromium`)
- Credenciales de una **Service Account** de Google con acceso de lectura a la unidad compartida de Drive
- Variables de entorno (archivo `.env`):

| Variable | Descripción |
|---|---|
| `MAIL_USER` | Usuario/email para el login en Indyco |
| `PASSWORD` | Contraseña para el login en Indyco |

> Las credenciales de la Service Account de Google se resuelven automáticamente vía `google.auth.default()` (variable de entorno `GOOGLE_APPLICATION_CREDENTIALS` o configuración del entorno de ejecución, por ejemplo un secret de GitHub Actions).

## Instalación

```bash
pip install -r requirements.txt
playwright install chromium
```

## Uso

```bash
python main.py
```

El script:
- Busca el archivo `reporte_contable.xlsx` dentro de la carpeta configurada (`PARENT_FOLDER_ID`) en la unidad compartida (`SHARED_DRIVE_ID`).
- Filtra y carga las observaciones pendientes en Indyco.
- Loguea el resultado (facturas procesadas, observaciones ingresadas, observaciones que ya estaban cargadas y tiempo total de ejecución).

## Automatización

El proceso corre semanalmente vía un workflow de **GitHub Actions**, sin intervención manual, usando secrets del repositorio para las credenciales.

## Notas

- La comparación entre Excel e Indyco se hace por número de factura, importe, fecha, período y titular, para evitar cargar una observación en la factura equivocada.
- Los textos de observación se normalizan (minúsculas, sin saltos de línea, espacios colapsados) antes de compararlos, para no reingresar una observación que ya está cargada con un formato levemente distinto.
- Si una factura no se encuentra en la tabla de Indyco después de varios reintentos, el proceso se corta para evitar cargar datos sobre una búsqueda inconsistente.
