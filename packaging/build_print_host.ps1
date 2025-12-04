Param(
    [string]$ProjectRoot = "c:\Users\pepe\Desktop\Mundowaffles_app"
)

Write-Host "== Mundo Waffles - Build Print Host ==" -ForegroundColor Cyan
Push-Location $ProjectRoot

# Activar entorno
.\env\Scripts\Activate.ps1

# Instalar dependencias necesarias para el host y empaquetado
pip install -r .\packaging\requirements_print_host.txt; pip install pyinstaller

# Limpiar
Remove-Item -Recurse -Force .\build  -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\dist   -ErrorAction SilentlyContinue

# Construir ejecutable
pyinstaller --onefile --noconsole --name "MundoWaffles_PrintHost" .\app\printer_host.py

if (Test-Path .\dist\MundoWaffles_PrintHost.exe) {
    Write-Host "Ejecutable creado: dist\MundoWaffles_PrintHost.exe" -ForegroundColor Green
} else {
    Write-Error "No se creó el ejecutable. Revisar errores de PyInstaller."
}

Pop-Location
