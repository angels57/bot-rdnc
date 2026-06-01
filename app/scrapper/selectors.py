"""Selectores y constantes para el scraper de RNDC."""

# URL principal del sitio de RNDC
URL = "https://rndc.mintransporte.gov.co/MenuPrincipal/tabid/204/language/es-MX/Default.aspx?returnurl=%2fProgramasRNDC%2fCrearDocumento%2ftabid%2f69%2fctl%2fMaestro%2fmid%2f396%2flanguage%2fes-MX%2fDefault.aspx"

# Selector para el span que contiene el captcha (números a sumar)
SELECTOR_CAPTCHA = "span#dnn_ctr678_VigiaPublico_Cat"

# Selector para el input donde se ingresa el resultado del captcha
SELECTOR_RESULTADO = "input[id='dnn_ctr678_VigiaPublico_Resultado']"

# Selector para el input donde se ingresa la fecha inicial (formato AAAAMM)
SELECTOR_FECHA_INICIAL = "input[id='dnn_ctr678_VigiaPublico_AnoMesInicial']"

# Selector para el botón de descargar estadísticas
SELECTOR_BT_ESTADISTICAS = "input[id='dnn_ctr678_VigiaPublico_btEstadisticas']"

# URL de la página de SICETAC
URL_SICETAC = "https://plc.mintransporte.gov.co/Runtime/empresa/ctl/SiceTAC/mid/417"

SELECTOR_CONFIG_VEHICULO = "select[id='dnn_ctr417_SiceTAC_CONFIGURACION']"

SELECTOR_CONDICION_CARGA = "select[id='dnn_ctr417_SiceTAC_CONDICIONCARGA']"
SELECTOR_CARROCERIA_VEHICULO = "select[id='dnn_ctr417_SiceTAC_UNIDADTRANSPORTE']"
SELECTOR_TIPO_CARGA = "select[id='dnn_ctr417_SiceTAC_TIPOCARGA']"
SELECTOR_ORIGEN_VIAJE = "select[id='dnn_ctr417_SiceTAC_ORIGEN']"
SELECTOR_DESTINO_VIAJE = "select[id='dnn_ctr417_SiceTAC_DESTINO']"
SELECTOR_HORAS_CARGUE = "input[id='dnn_ctr417_SiceTAC_HORASCARGUE']"
SELECTOR_HORAS_DESCARGUE = "input[id='dnn_ctr417_SiceTAC_HORASDESCARGUE']"

SELECTOR_CAPTCHA = "span[id='dnn_ctr678_VigiaPublico_Cat']"
SELECTOR_RESULTADO_CAPTCHA = "input[id='dnn_ctr417_SiceTAC_Resultado']"
SELECTOR_BT_CALCULAR = "a[id='dnn_ctr417_SiceTAC_btCalcular']"

SELECTOR_COSTO_TOTAL_VIAJE = "input[id='dnn_ctr417_SiceTAC_COSTOTOTALVIAJE']"
