@echo off
echo ========================================
echo DESACTIVAR SUSPENSION DE WINDOWS
echo ========================================
echo.
echo Este script desactivará la suspensión de Windows mientras
echo el script de extracción se ejecuta.
echo.
echo IMPORTANTE: Ejecutar como ADMINISTRADOR
echo (Click derecho > Ejecutar como administrador)
echo.
pause

echo.
echo Desactivando suspensión de pantalla y PC...
powercfg -change -standby-timeout-ac 0
powercfg -change -standby-timeout-dc 0
powercfg -change -monitor-timeout-ac 0
powercfg -change -monitor-timeout-dc 0
powercfg -change -disk-timeout-ac 0
powercfg -change -disk-timeout-dc 0

echo.
echo ✓ Suspensión desactivada correctamente
echo.
echo Configuración actual:
powercfg /query SCHEME_CURRENT SUB_SLEEP
echo.
echo Para REACTIVAR la suspensión después, ejecuta:
echo REACTIVAR_SUSPENSION.bat
echo.
pause
