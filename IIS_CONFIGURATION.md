# Configuración de IIS para /cotizacion

Este documento describe cómo configurar Microsoft Internet Information Server (IIS) para alojar la aplicación `bot-rdnc` en la ruta `/cotizacion`.

## Requisitos previos

- Windows Server con IIS 8.5+ instalado
- Application Request Routing (ARR) instalado en IIS
- URL Rewrite Module instalado en IIS
- Python 3.12+ instalado en el servidor
- WebSocket Protocol habilitado en IIS
- La aplicación Python ejecutándose en puerto local (ej: 8501)

## Instalación de módulos IIS requeridos

```powershell
# Descargar e instalar ARR (Application Request Routing)
# https://www.iis.net/downloads/microsoft/application-request-routing

# Descargar e instalar URL Rewrite Module
# https://www.iis.net/downloads/microsoft/url-rewrite

# Habilitar WebSocket Protocol
Enable-WindowsOptionalFeature -FeatureName IIS-WebSocket -Online
```

## Paso 1: Crear la aplicación en IIS

1. Abrir **IIS Manager** (`inetmgr`)
2. Expandir el nodo del servidor y localizar **Sitios**
3. Hacer clic derecho en **Sitios** → **Agregar sitio web**
4. Configurar:
   - **Nombre del sitio**: `cotizacion` (o el nombre que prefieras)
   - **Ruta de acceso física**: `C:\ruta\a\bot-rdnc` (ruta absoluta del proyecto)
   - **Vinculación - Protocolo**: `http`
   - **Vinculación - Dirección IP**: `Todas sin asignar` o la IP específica del servidor
   - **Vinculación - Puerto**: `80` (o el puerto que uses)
   - **Nombre de host**: Dejar en blanco o especificar `tu-servidor.com`
5. Hacer clic en **Aceptar**

## Paso 2: Crear una aplicación virtual

1. En IIS Manager, seleccionar el sitio creado
2. Hacer clic derecho → **Agregar aplicación**
3. Configurar:
   - **Alias**: `cotizacion` (esto crea la ruta `/cotizacion`)
   - **Ruta de acceso física**: `C:\ruta\a\bot-rdnc` (misma ruta del sitio)
   - **Grupo de aplicaciones**: Crear nuevo o seleccionar existente
4. Hacer clic en **Aceptar**

## Paso 3: Configurar el grupo de aplicaciones (App Pool)

1. En IIS Manager, expandir **Grupos de aplicaciones**
2. Localizar el grupo asignado (ej: `cotizacion` AppPool)
3. Hacer clic derecho → **Configuración avanzada**
4. Modificar:
   - **Identidad**: `ApplicationPoolIdentity` o cuenta de servicio específica
   - **Habilitar aplicaciones de 32 bits**: `False` (para Python 64-bit)
   - **Pipeline administrado**: `Integrado`
5. Hacer clic en **Aceptar**

## Paso 4: Permisos de carpeta

1. En el explorador de archivos, localizar `C:\ruta\a\bot-rdnc`
2. Hacer clic derecho → **Propiedades** → **Pestaña Seguridad**
3. Hacer clic en **Editar**
4. Seleccionar la identidad del App Pool (ej: `IIS APPPOOL\cotizacion`)
5. Conceder permisos:
   - **Leer y ejecutar**: ✓
   - **Mostrar contenido de carpeta**: ✓
   - **Leer**: ✓
   - **Escribir**: ✓ (solo si la aplicación genera logs o descarga archivos)
6. Hacer clic en **Aplicar** → **Aceptar**

## Paso 5: Configurar web.config

1. Copiar el archivo `web.config` a la raíz del proyecto (`C:\ruta\a\bot-rdnc\web.config`)
2. El archivo contiene:
   - Reglas de URL Rewrite para redirigir tráfico a la aplicación Python local
   - Configuración de proxy inverso
   - Headers de WebSocket

## Paso 6: Habilitar WebSocket en IIS

1. En IIS Manager, seleccionar el sitio `cotizacion`
2. En el panel central, buscar **Protocolo WebSocket**
3. Hacer clic en **Protocolo WebSocket**
4. En la columna derecha, hacer clic en **Habilitar** (si no está habilitado)

## Paso 7: Configurar ARR (Application Request Routing)

1. En IIS Manager, seleccionar el sitio `cotizacion`
2. En el panel central, hacer doble clic en **Enrutamiento de solicitudes de aplicación**
3. Si no está habilitado, hacer clic en **Habilitar** en la columna derecha
4. Hacer clic en **Editar configuración de proxy**:
   - **Tiempo de espera (segundos)**: `300`
   - **Modo de caché**: `Nunca caché`
   - **Habilitar proxy reverso**: ✓

## Paso 8: Iniciar la aplicación Python

En el servidor, abrir PowerShell como administrador:

```powershell
cd C:\ruta\a\bot-rdnc
# Activar el entorno virtual
.\.venv\Scripts\Activate.ps1

# Ejecutar la aplicación (en modo headless para servicio)
streamlit run main.py --server.port 8501 --server.headless true --server.baseUrlPath /cotizacion
```

O crear un servicio Windows que arranque automáticamente:

```powershell
# Crear tarea programada o servicio
# Ver instrucción de servicio Windows más abajo
```

## Paso 9: Crear un servicio Windows (Opcional pero recomendado)

Crear un script `C:\ruta\a\bot-rdnc\start-service.ps1`:

```powershell
$env:PYTHONUNBUFFERED=1
$env:STREAMLIT_SERVER_PORT=8501
$env:STREAMLIT_SERVER_HEADLESS=true
$env:STREAMLIT_SERVER_BASEURL=http://localhost/cotizacion
$env:STREAMLIT_SERVER_MAXUPLOADSIZE=500

cd "C:\ruta\a\bot-rdnc"
.\.venv\Scripts\Activate.ps1
python -m streamlit run main.py
```

Usar **NSSM** (Non-Sucking Service Manager) para crear el servicio:

```powershell
# Descargar NSSM desde https://nssm.cc/download
# Descomprimir en C:\nssm

C:\nssm\nssm.exe install CotizacionService `
  "powershell.exe" `
  "-File C:\ruta\a\bot-rdnc\start-service.ps1"

# Iniciar el servicio
Start-Service CotizacionService

# Verificar estado
Get-Service CotizacionService
```

## Paso 10: Validar la configuración

1. Abrir navegador y acceder a:
   ```
   http://localhost/cotizacion
   o
   http://tu-servidor.com/cotizacion
   ```

2. Si hay errores, revisar los logs:
   - IIS: `C:\inetpub\logs\LogFiles\`
   - Aplicación: `C:\ruta\a\bot-rdnc\logs\`

3. Verificar que el proxy inverso está funcionando:
   ```powershell
   # En el servidor, validar que la aplicación está escuchando
   netstat -ano | findstr "8501"
   ```

## Configuración de proxy corporativo (si aplica)

Si el servidor está detrás de un proxy corporativo:

1. Editar el archivo `config.toml` o crear variables de entorno:
   ```toml
   [proxy]
   http_proxy = "http://proxy.empresa.com:8080"
   https_proxy = "http://proxy.empresa.com:8080"
   no_proxy = "localhost,127.0.0.1,.empresa.local"
   ```

2. O establecer variables de entorno en el servicio Windows:
   ```powershell
   $env:HTTP_PROXY = "http://proxy.empresa.com:8080"
   $env:HTTPS_PROXY = "http://proxy.empresa.com:8080"
   ```

3. Configurar Playwright para usar el proxy:
   - Editar `app/scrapper/browser.py` para pasar proxy en el contexto

## Checklist de validación

- [ ] IIS instalado y ARR/URL Rewrite módulos instalados
- [ ] WebSocket Protocol habilitado
- [ ] Sitio/aplicación creado en `/cotizacion`
- [ ] Permisos de carpeta configurados correctamente
- [ ] `web.config` en la raíz del proyecto
- [ ] Aplicación Python ejecutándose en puerto 8501
- [ ] Servicio Windows creado (si es necesario)
- [ ] Acceso a `http://localhost/cotizacion` exitoso
- [ ] Logs sin errores de proxy o WebSocket
- [ ] Proxy corporativo configurado (si aplica)

## Notas finales

- La ruta `/cotizacion` es ahora la raíz de la aplicación en el navegador
- El proxy inverso en IIS redirige automáticamente a `http://localhost:8501`
- WebSocket está habilitado para Streamlit
- Los logs de IIS y la aplicación ayudan a diagnosticar problemas
