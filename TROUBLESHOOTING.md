<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <webSocket enabled="true" />
    <rewrite>
      <rules>
        <clear />

        <rule name="StreamlitStatic" stopProcessing="true">
          <match url="^static/(.*)$" />
          <action type="Rewrite" url="http://127.0.0.1:8501/cotizacion/static/{R:1}" />
        </rule>

        <rule name="StreamlitWebSocket" stopProcessing="true">
          <match url="^_stcore/stream/?$" />
          <conditions logicalGrouping="MatchAll" trackAllCaptures="false">
            <add input="{HTTP_UPGRADE}" pattern="websocket" ignoreCase="true" />
          </conditions>
          <action type="Rewrite" url="http://127.0.0.1:8501/cotizacion/_stcore/stream" />
        </rule>

        <rule name="StreamlitAll" stopProcessing="true">
          <match url="^(.*)$" />
          <action type="Rewrite" url="http://127.0.0.1:8501/cotizacion/{R:1}" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration># Diagnóstico del error 500 en /cotizacion

El error `500 Internal Server Error` en `https://impocoma.com.co:8084/cotizacion` puede ocurrir por varias razones. Sigue estos pasos:

## Paso 1: Verificar que Streamlit está ejecutándose

```powershell
# En el servidor, verificar si el puerto 8501 está escuchando
netstat -ano | findstr "8501"

# Debería mostrar algo como:
# TCP    127.0.0.1:8501         0.0.0.0:0              LISTENING    12345
```

Si no aparece nada:
1. Ejecuta: `C:\Users\TEMPORAL\Documents\Automation\bot-rdnc\start-streamlit.bat`
2. Espera a que veas "You can now view your Streamlit app in your browser."
3. Si falla, revisa el error en la consola

## Paso 2: Probar conexión local a Streamlit

```powershell
# Desde el servidor, probar si Streamlit responde localmente
curl http://localhost:8501

# O desde PowerShell:
(Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing).StatusCode

# Debería devolver 200 OK
```

Si devuelve error:
- Streamlit no está corriendo
- Puerto 8501 está siendo usado por otra aplicación
- Firewall está bloqueando la conexión local

## Paso 3: Verificar logs de IIS

```powershell
# Ver últimas líneas del log de IIS
Get-Content "C:\inetpub\logs\LogFiles\W3SVC1\u_ex*.log" -Tail 50 | Select-String "cotizacion"

# O buscar directamente la carpeta:
ls "C:\inetpub\logs\LogFiles\W3SVC1\" | sort LastWriteTime -Descending | select -First 1 | Get-Content -Tail 50
```

**Errores comunes:**
- `500.0` — Error interno IIS
- `502` — Bad Gateway (Streamlit no responde)
- `404` — Ruta no encontrada

## Paso 4: Verificar configuración de IIS

1. Abrir **IIS Manager** → seleccionar sitio
2. Buscar **URL Rewrite** → Verificar que el módulo está **habilitado**
3. Hacer clic en **Ver reglas implementadas** → verificar que aparecen las reglas de proxy

## Paso 5: Verificar web.config

```powershell
# Validar sintaxis XML del web.config
[xml]$config = Get-Content "C:\Users\TEMPORAL\Documents\Automation\bot-rdnc\web.config"
Write-Host "web.config válido"

# O validar desde IIS:
# - IIS Manager → Sitio → Configuration Editor
# - Seleccionar "system.webServer" → "rewrite"
# Debe mostrar las reglas sin errores
```

## Paso 6: Verificar permisos

```powershell
# La cuenta del App Pool debe tener permisos de lectura en la carpeta
$acl = Get-Acl "C:\Users\TEMPORAL\Documents\Automation\bot-rdnc"
$acl.Access | Where-Object {$_.IdentityReference -like "*IIS*"} | Select IdentityReference, FileSystemRights, AccessControlType
```

Si no hay entradas para IIS AppPool, añadir permisos:
```powershell
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "IIS APPPOOL\cotizacion",
    "ReadAndExecute",
    "ContainerInherit,ObjectInherit",
    "None",
    "Allow"
)
Get-Acl "C:\Users\TEMPORAL\Documents\Automation\bot-rdnc" | ForEach-Object {$_.AddAccessRule($rule); Set-Acl -Path "C:\Users\TEMPORAL\Documents\Automation\bot-rdnc" -AclObject $_}
```

## Paso 7: Habilitar debug en Streamlit

Editar `.streamlit/config.toml`:

```toml
[logger]
level = "debug"

[client]
showErrorDetails = true
```

Reiniciar Streamlit y revisar logs en la consola.

## Paso 8: Prueba desde cliente

Una vez que `http://localhost:8501` funciona:

```powershell
# Desde otra máquina, probar HTTPS a impocoma.com.co:8084
# Asegurarse de que:
# 1. El certificado SSL es válido
# 2. El puerto 8084 es accesible desde Internet
# 3. El firewall permite HTTPS en puerto 8084
```

## Paso 9: Forzar reinicio de IIS

Si todos los pasos anteriores parecen correctos pero aún hay 500:

```powershell
# Detener IIS
iisreset /stop

# Esperar 5 segundos
Start-Sleep 5

# Iniciar IIS
iisreset /start

# O reiniciar el Application Pool específico
$pool = Get-IISAppPool -Name "cotizacion"
Restart-WebAppPool -Name "cotizacion"
```

## Configuración final esperada

Después de todos los pasos, verifica:

✅ Streamlit escuchando en `http://localhost:8501`  
✅ Acceso local exitoso a `http://localhost:8501`  
✅ Sitio en IIS creado con ruta `/cotizacion`  
✅ `web.config` válido y con URL Rewrite habilitado  
✅ Permisos de lectura en la carpeta del proyecto  
✅ WebSocket Protocol habilitado en IIS  
✅ Acceso remoto exitoso a `https://impocoma.com.co:8084/cotizacion`  

## Logs a revisar

- **IIS**: `C:\inetpub\logs\LogFiles\W3SVC1\u_ex*.log`
- **Streamlit**: Consola del `start-streamlit.bat`
- **Aplicación**: `C:\Users\TEMPORAL\Documents\Automation\bot-rdnc\logs\app.json`
- **Sistema**: Event Viewer → Windows Logs → Application

## Si nada funciona

```powershell
# Verificar que el puerto 8501 está realmente escuchando
netstat -ano -p tcp | findstr "8501"

# Revisar si hay otro proceso usando el puerto
Get-Process | Where-Object {$_.Id -eq <PID>}

# Cambiar puerto en .streamlit/config.toml a otro (ej: 8502)
# Y actualizar web.config con nuevo puerto
```

---

**Próximos pasos después de resolver el 500:**
1. Probar flujo completo de scraping
2. Revisar logs de Playwright
3. Validar proxy corporativo si aplica
