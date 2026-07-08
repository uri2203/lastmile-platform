# ========================================
# SISTEMA INTEGRAL AS/400 - V7R1
# Script de Ejecución Windows
# ========================================

echo ========================================
echo   SISTEMA INTEGRAL AS/400 - V7R1
echo ========================================
echo.

set JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot"
set CP="C:\Users\Sistemas\as400\BOOT-INF\lib\jt400-21.0.6.jar;C:\Users\Sistemas\as400\lib-reports\*;."

echo [1/7] Compilando sistema...
%JAVA_HOME%\bin\javac.exe -cp %CP% src\*.java
if errorlevel 1 (
    echo Error en compilación
    pause
    exit /b 1
)

echo [2/7] Iniciando API REST (puerto 8080)...
start "API REST AS/400" %JAVA_HOME%\bin\java.exe -cp %CP% api.AS400API
timeout /t 3 /nobreak > nul

echo [3/7] Iniciando Dashboard Web...
start "" "http://localhost:8080/dashboard"
echo Dashboard abierto en navegador

echo [4/7] Iniciando Sistema de Alertas...
start "Alertas AS/400" %JAVA_HOME%\bin\java.exe -cp %CP% alertas.SistemaAlertas

echo [5/7] Generando Presentación Ejecutiva...
%JAVA_HOME%\bin\java.exe -cp %CP% presentaciones.GeneradorPresentaciones

echo [6/7] Ejecutando Duplicador Inteligente...
%JAVA_HOME%\bin\java.exe -cp %CP% duplicador.DuplicadorInteligente

echo.
echo ========================================
echo   TODOS LOS SISTEMAS INICIADOS
echo ========================================
echo.
echo APIs disponibles:
echo   http://localhost:8080/api/ventas?periodo=2026
echo   http://localhost:8080/api/inventario
echo   http://localhost:8080/api/clientes?top=10
echo   http://localhost:8080/api/kpis
echo   http://localhost:8080/api/alertas
echo   http://localhost:8080/api/predicciones?meses=3
echo   http://localhost:8080/api/dashboard
echo.
echo Dashboard: http://localhost:8080/dashboard
echo.
echo Presiona Ctrl+C en las ventanas de consola para detener
pause
