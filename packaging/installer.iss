[Setup]
AppName=Mundo Waffles Print Host
AppVersion=1.0.0
DefaultDirName={pf}\MundoWaffles
DefaultGroupName=Mundo Waffles
OutputBaseFilename=MundoWaffles_PrintHost_Setup
Compression=lzma2
SolidCompression=yes

[Files]
Source: "..\dist\MundoWaffles_PrintHost.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Print Host"; Filename: "{app}\MundoWaffles_PrintHost.exe"
Name: "{commonstartup}\Mundo Waffles Print Host"; Filename: "{app}\MundoWaffles_PrintHost.exe"; WorkingDir: "{app}"

[Run]
Filename: "{app}\MundoWaffles_PrintHost.exe"; Description: "Iniciar Print Host"; Flags: nowait postinstall skipifsilent
