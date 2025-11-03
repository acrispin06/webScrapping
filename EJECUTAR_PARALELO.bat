@echo off
chcp 65001 > nul
cls

echo ================================================================================
echo EJECUTOR PARALELO - EXTRACCIÓN COMPLETA DE CINEPLANET
echo ================================================================================
echo.
echo 📋 Scripts a ejecutar:
echo    1. inspector_asientos_totales_v2.py → Capacidades (CSV)
echo    2. main.py → Precios (CSV)
echo.
echo ⚙️  Configuración:
echo    • Modo: HEADLESS (sin ventana)
echo    • Cines: TODOS (~43)
echo    • Películas: TODAS
echo    • Funciones: TODAS
echo ================================================================================
echo.
pause
echo.

echo 🚀 Iniciando procesos en paralelo...
echo.

REM Ejecutar inspector_asientos_totales_v2.py en segundo plano
start "Capacidades" /MIN python inspector_asientos_totales_v2.py
echo ✅ Proceso 1: inspector_asientos_totales_v2.py iniciado

timeout /t 2 /nobreak > nul

REM Ejecutar main.py en segundo plano
start "Precios" /MIN python main.py
echo ✅ Proceso 2: main.py iniciado

echo.
echo ================================================================================
echo PROCESOS EN EJECUCIÓN
echo ================================================================================
echo.
echo 📊 Monitorea el progreso:
echo    • Capacidades: capacidades_cineplanet_EN_PROGRESO.csv
echo    • Precios: precios_cineplanet_EN_PROGRESO.csv
echo.
echo ⏱️  Tiempo estimado: 30-60 minutos (depende de la cantidad de datos)
echo.
echo 💡 Se han abierto 2 ventanas minimizadas (revisa la barra de tareas)
echo.
echo ⚠️  IMPORTANTE:
echo    - Los procesos corren en segundo plano
echo    - Puedes cerrar ESTA ventana sin afectar la extracción
echo    - Para detener: cierra las ventanas "Capacidades" y "Precios"
echo.
pause
