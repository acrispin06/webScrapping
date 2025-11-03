@echo off
REM ============================================================================
REM VERIFICAR ESTADO DE TAREA PROGRAMADA
REM ============================================================================

echo.
echo ================================================================================
echo ESTADO DE LA TAREA PROGRAMADA - EXTRACCION CAPACIDADES
echo ================================================================================
echo.

REM Verificar si la tarea existe
schtasks /Query /TN "Extraccion_Capacidades_Cineplanet" /FO LIST /V 2>nul

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo PROXIMA EJECUCION
    echo ================================================================================
    schtasks /Query /TN "Extraccion_Capacidades_Cineplanet" /FO LIST | findstr /C:"Próxima hora de ejecución" /C:"Next Run Time"
    echo.
    echo ================================================================================
    echo HISTORIAL DE EJECUCIONES
    echo ================================================================================
    echo.
    echo Ultimas 10 ejecuciones desde el log:
    echo.
    if exist "%~dp0extraccion_capacidades_log.txt" (
        powershell -Command "Get-Content '%~dp0extraccion_capacidades_log.txt' -Tail 50 | Select-String 'EXTRACTOR DE CAPACIDADES|FINALIZADO|Total registros'"
    ) else (
        echo No hay archivo de log todavia. La tarea no se ha ejecutado.
    )
    echo.
) else (
    echo ================================================================================
    echo NO HAY TAREA PROGRAMADA
    echo ================================================================================
    echo.
    echo La tarea "Extraccion_Capacidades_Cineplanet" no existe.
    echo Ejecuta PROGRAMAR_EXTRACCION_3AM.bat para crearla.
    echo.
)

echo ================================================================================
echo ARCHIVOS GENERADOS
echo ================================================================================
echo.
dir /B "%~dp0capacidades_cineplanet_*.csv" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo No hay archivos de capacidades todavia.
) else (
    echo.
    echo Para ver detalles de los archivos:
    dir "%~dp0capacidades_cineplanet_*.csv"
)
echo.
echo ================================================================================
pause
