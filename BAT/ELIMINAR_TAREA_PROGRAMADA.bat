@echo off
REM ============================================================================
REM ELIMINAR TAREA PROGRAMADA
REM ============================================================================

echo.
echo ================================================================================
echo ELIMINAR TAREA PROGRAMADA - EXTRACCION CAPACIDADES
echo ================================================================================
echo.
echo Esta accion eliminara la tarea programada para las 3:00 AM.
echo.
pause

schtasks /Delete /TN "Extraccion_Capacidades_Cineplanet" /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo TAREA ELIMINADA EXITOSAMENTE
    echo ================================================================================
    echo.
    echo La extraccion ya no se ejecutara automaticamente a las 3:00 AM.
    echo.
) else (
    echo.
    echo ================================================================================
    echo ERROR O TAREA NO EXISTE
    echo ================================================================================
    echo.
    echo La tarea no pudo ser eliminada o no existe.
    echo.
)

echo ================================================================================
pause
