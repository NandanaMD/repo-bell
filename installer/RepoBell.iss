[Setup]
AppId={{D2BD1A15-BC44-4BEF-ABDD-3258A894E9C0}
AppName=Repo Bell
AppVersion=1.0.0
AppPublisher=Repo Bell Contributors
AppPublisherURL=https://github.com/NandanaMD/repo-bell
AppSupportURL=https://github.com/NandanaMD/repo-bell/issues
DefaultDirName={autopf}\Repo Bell
DefaultGroupName=Repo Bell
DisableProgramGroupPage=yes
LicenseFile=installer\terms_and_conditions.txt
OutputDir=installer\output
OutputBaseFilename=RepoBellSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\RepoBell.exe
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startwithwindows"; Description: "Start Repo Bell with Windows"; GroupDescription: "Additional options:"; Flags: unchecked

[Files]
Source: "dist\RepoBell.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Repo Bell"; Filename: "{app}\RepoBell.exe"; IconFilename: "{app}\RepoBell.exe"
Name: "{autodesktop}\Repo Bell"; Filename: "{app}\RepoBell.exe"; Tasks: desktopicon; IconFilename: "{app}\RepoBell.exe"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "RepoBell"; ValueData: """{app}\RepoBell.exe"""; Tasks: startwithwindows; Flags: uninsdeletevalue

[Run]
Filename: "{app}\RepoBell.exe"; Description: "Launch Repo Bell"; Flags: nowait postinstall skipifsilent
