#define AppName "Makro"
#define AppVersion "1.0.2"
#define AppPublisher "Aras"

[Setup]
AppId={{F4E14C25-ACD3-4D8B-9DB6-61BD4D6A4FC1}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\Makro
DefaultGroupName={#AppName}
UninstallDisplayIcon={app}\AutoClicker.exe
LicenseFile=LICENSE
OutputDir=release
OutputBaseFilename=Makro-Setup-{#AppVersion}
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
Source: "release\AutoClicker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Makro"; Filename: "{app}\AutoClicker.exe"
Name: "{autodesktop}\Makro"; Filename: "{app}\AutoClicker.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AutoClicker.exe"; Description: "{cm:LaunchProgram,Makro}"; Flags: nowait postinstall skipifsilent
