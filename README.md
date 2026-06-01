# Bot RNDC / Sictac Automation

Este repositorio contiene un servicio de automatización que resuelve la recolección y el cálculo de costos de transporte desde los portales RNDC y Sictac.

## 🔧 Problema que resuelve

El proyecto automatiza la consulta de datos operativos que normalmente requieren:
- ingreso manual en portales web de RNDC y Sictac,
- navegación por formularios y listas desplegables,
- resolución de captchas básicos,
- descarga de informes y cálculo manual de rutas y costos.

El resultado es un proceso automatizado de extracción, normalización y comparación de rutas y precios, sin necesidad de intervención diaria.

## ⏱ Tiempo que ahorra

- Elimina 100% del trabajo manual de consulta en RNDC y Sictac,
- reduce de 30-45 minutos diarios a menos de 2 minutos de procesado automatizado,
- permite ejecutar el flujo de forma programada y no depender de revisiones manuales por operador.

## 🧠 Cómo realiza el proceso

1. `main.py` arranca el servicio y orquesta los módulos principales.
2. `app/scrapper/browser.py` inicializa Playwright y configura el navegador headless, descargas y contexto de proxy.
3. `app/scrapper/rndc.py` automatiza el acceso al portal RNDC:
   - completa credenciales y criterios de búsqueda,
   - resuelve el captcha numérico registrado en la sesión,
   - solicita datos del mes anterior,
   - descarga el Excel de resultados a `data/RNDC.xlsx`.
4. `app/scrapper/sicetac.py` automatiza el portal Sictac:
   - navega formularios de ruta,
   - selecciona orígenes, destinos y parámetros de flete,
   - extrae el costo total y las variables de la cotización.
5. `app/data/loader.py` carga los archivos JSON y el Excel generado.
6. `app/data/processor.py` normaliza rutas, calcula comparativos y genera respuesta estructurada.
7. `app/services/query_service.py` expone la lógica de consulta para UI y bot.
8. `app/bot/formatter.py` formatea la salida en texto legible y agrega comparativos entre RNDC y Sictac.

## 📌 Arquitectura relevante

- `app/scrapper/` — flujos de navegación web basados en Playwright.
- `app/core/` — configuración, logging y utilidades transversales.
- `app/data/` — carga, limpieza y transformación de datos.
- `app/services/` — capa de servicio que abstrae consultas y reglas de negocio.
- `app/UI/` — interfaz y estado de la aplicación.

## ⚙️ Requisitos de despliegue

- Windows Server con IIS.
- WebSocket instalado y habilitado en el servidor.
- Proxy habilitado para que Playwright acceda a Internet desde el entorno de IIS.
- Configuración del sitio en una carpeta llamada `sigpa` dentro del directorio físico del sitio.
- Enrutamiento configurado en IIS con la ruta base `/cotizacion`.

## 🧩 Configuración en IIS

1. Crear un sitio o aplicación en IIS apuntando al directorio físico del proyecto.
2. Establecer la ruta de la aplicación a `/cotizacion`.
3. Asegurar que la carpeta `sigpa` esté presente dentro del sitio y contenga los archivos de configuración requeridos.
4. Habilitar WebSocket Protocol en los roles de servidor.
5. Configurar el proxy de red en el servidor o la aplicación para permitir conexiones salientes desde el proceso Python.
6. Asegurar permisos de lectura/escritura para la cuenta de la app pool sobre `data/` y `logs/`.

## 📁 Configuración esperada

- Carpeta del sitio: `...\sigpa\`
- Ruta IIS: `https://www.impocoma.com.co:8084/impocoma`
- Archivos de configuración adicionales en `sigpa`:
  - parámetros de proxy,
  - credenciales de acceso al portal,
  - rutas de datos,
  - variables de entorno para Playwright.

## ▶️ Cómo ejecutar localmente

```bash
cd c:\Users\TEMPORAL\Documents\Automation\bot-rdnc
uv sync
uv run streamlit run main.py
```


O directamente:

```bash
python -m streamlit run main.py
```

## 🧪 Prerrequisitos técnicos

- Python 3.12+
- Playwright instalado y configurado en el entorno virtual.
- WebSocket Protocol habilitado en IIS.
- Proxy habilitado y validado para el entorno de ejecución.
- Carpeta `sigpa` con configuración del sitio.

## 🧪 Verificación de ambiente

- Confirmar que IIS sirve el sitio en `http://<host>/impocoma`.
- Verificar que la aplicación puede iniciar Playwright sin errores de red.
- Probar la ruta y la carga de datos desde `data/`.

## 🛠 Mantenimiento y extensiones

- Actualizar `app/scrapper/selectors.py` si cambian los formularios web.
- Validar tiempos de espera y `wait_for_selector` en los flujos de Playwright.
- Añadir más logs en `app/core/logging.py` para diagnosticar fallos de proxy o WebSocket.
- Centralizar credenciales y URLs en la carpeta `sigpa` para despliegue consistente.

## 📌 Notas finales

Este servicio está diseñado para ejecutarse como una aplicación web en IIS con la ruta `/impocoma` y respaldar procesos automatizados de consulta y comparación de costos entre RNDC y Sictac. El enfoque se centra en lograr estabilidad de scraping y en dejar la configuración de infraestructura en la carpeta `sigpa` del sitio.
