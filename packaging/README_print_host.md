# Mundo Waffles - Print Host

## Requisitos
- Windows 10/11
- Impresora térmica instalada (ej. EPSON TM-T88V)
- Permisos de administrador para imprimir (spooler)

## Construcción (desarrollador)

```powershell
Push-Location "c:\Users\pepe\Desktop\Mundowaffles_app"
./packaging/build_print_host.ps1
```

El ejecutable quedará en `dist/MundoWaffles_PrintHost.exe`.

## Instalador (opcional)
Usa Inno Setup para crear instalador:

```powershell
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\installer.iss
```
El instalador quedará como `packaging\Output\MundoWaffles_PrintHost_Setup.exe`.

## Ejecución (cliente)
- Ejecutar `MundoWaffles_PrintHost.exe`
- Verificar en navegador: `http://127.0.0.1:8765/health`

## Endpoint de impresión
`POST http://127.0.0.1:8765/print/raw`
```json
{
  "driver": "EPSON TM-T88V Receipt5",
  "content": "Texto a imprimir\n",
  "feed": 3,
  "cut": true
}
```

## Troubleshooting
- Si no imprime: ejecutar como Administrador.
- Verificar nombre exacto del driver en Windows.
- Comprobar que el servicio de Print Spooler esté activo.