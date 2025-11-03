@echo off
REM ============================================================================
REM PROGRAMADOR DE TAREA - EXTRACCIÓN CAPACIDADES CINEPLANET
REM ============================================================================
REM Este script programa la extracción para las 3:00 AM todos los días
REM ============================================================================

echo.
echo ================================================================================
echo PROGRAMAR EXTRACCION DE CAPACIDADES - 3:00 AM
echo ================================================================================
echo.
echo Este script creara una tarea programada en Windows que ejecutara
echo la extraccion de capacidades a las 3:00 AM todos los dias.
echo.
echo IMPORTANTE:
echo - Debes ejecutar este script como ADMINISTRADOR
echo - El PC debe estar encendido a las 3:00 AM
echo - Se recomienda desactivar la suspension automatica
echo.
pause

REM Obtener la ruta actual del script
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%inspector_asientos_totales.py"
set "LOG_FILE=%SCRIPT_DIR%extraccion_capacidades_log.txt"

echo.
echo Creando tarea programada...
echo.

REM Eliminar tarea anterior si existe
schtasks /Delete /TN "Extraccion_Capacidades_Cineplanet" /F >nul 2>&1

REM Crear un script temporal para ejecutar
set "TEMP_SCRIPT=%SCRIPT_DIR%run_extraccion.bat"
echo @echo off > "%TEMP_SCRIPT%"
echo cd /d "%SCRIPT_DIR%" >> "%TEMP_SCRIPT%"
echo python "%PYTHON_SCRIPT%" ^>^> "%LOG_FILE%" 2^>^&1 >> "%TEMP_SCRIPT%"

REM Crear nueva tarea programada para las 3:00 AM
schtasks /Create /TN "Extraccion_Capacidades_Cineplanet" ^
    /TR "\"%TEMP_SCRIPT%\"" ^
    /SC DAILY ^
    /ST 03:00 ^
    /RL HIGHEST ^
    /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo TAREA PROGRAMADA CREADA EXITOSAMENTE
    echo ================================================================================
    echo.
    echo Nombre de la tarea: Extraccion_Capacidades_Cineplanet
    echo Horario: 3:00 AM (todos los dias^)
    echo Script: %PYTHON_SCRIPT%
    echo Log: %LOG_FILE%
    echo.
    echo La extraccion se ejecutara automaticamente a las 3:00 AM.
    echo Los resultados se guardaran en el mismo directorio.
    echo.
    echo RECOMENDACIONES:
    echo 1. Asegurate de que el PC este encendido a las 3:00 AM
    echo 2. Ejecuta DESACTIVAR_SUSPENSION.bat antes de dormir
    echo 3. Revisa el archivo de log para ver el progreso
    echo.
    echo Para ver todas las tareas programadas: schtasks /Query /TN "Extraccion_Capacidades_Cineplanet"
    echo Para eliminar la tarea: schtasks /Delete /TN "Extraccion_Capacidades_Cineplanet" /F
    echo.
) else (
    echo.
    echo ================================================================================
    echo ERROR AL CREAR LA TAREA
    echo ================================================================================
    echo.
    echo Asegurate de ejecutar este script como ADMINISTRADOR.
    echo Haz clic derecho en el archivo y selecciona "Ejecutar como administrador"
    echo.
)

echo ================================================================================
pause
