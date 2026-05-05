; instalador.iss — Script de Inno Setup para Sistema de Asistencias

#define AppName "Sistema de Asistencias"
#define AppVersion "1.3"
#define AppPublisher "HOPD"
#define AppExeName "SistemaAsistencias.exe"
#define AppIconName "Logo.ico"
#define SourceDir "dist\SistemaAsistencias"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=instalador_salida
OutputBaseFilename=Instalador_SistemaAsistencias_v{#AppVersion}
SetupIconFile=Logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

; ✅ AQUÍ personalizamos el mensaje nativo (solo aparece UNO)
[Messages]
ConfirmUninstall=¿Desea desinstalar {#AppName}?%n%n⚠ Los datos guardados en Documentos\Asistencias NO serán eliminados.

[Tasks]
Name: "desktopicon";   Description: "Crear icono en el Escritorio";          GroupDescription: "Accesos directos:"; Flags: checkedonce
Name: "startmenuicon"; Description: "Crear acceso directo en el Menú Inicio"; GroupDescription: "Accesos directos:"; Flags: checkedonce

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";             Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}";       Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Iniciar {#AppName} ahora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\Asistencias"