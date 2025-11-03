@echo off
echo ========================================
echo REACTIVAR SUSPENSION DE WINDOWS
echo ========================================
echo.
echo Este script restaurará la configuración normal de suspensión.
echo.
pause

echo.
echo Reactivando suspensión (30 minutos conectado, 15 minutos batería)...
powercfg -change -standby-timeout-ac 30
powercfg -change -standby-timeout-dc 15
powercfg -change -monitor-timeout-ac 10
powercfg -change -monitor-timeout-dc 5

echo.
echo ✓ Suspensión reactivada correctamente
echo.
echo Configuración actual:
powercfg /query SCHEME_CURRENT SUB_SLEEP
echo.
pause
