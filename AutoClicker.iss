#define AppName "PulseMacro Studio"
#define AppVersion "1.1.1"
#define AppPublisher "Aras"

[Setup]
AppId={{F4E14C25-ACD3-4D8B-9DB6-61BD4D6A4FC1}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\Makro
DefaultGroupName={#AppName}
UninstallDisplayIcon={app}\PulseMacro.exe
LicenseFile=LICENSE
OutputDir=release
OutputBaseFilename=PulseMacro-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
DisableProgramGroupPage=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "release\PulseMacro.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\PulseMacro.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\PulseMacro.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PulseMacro.exe"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
