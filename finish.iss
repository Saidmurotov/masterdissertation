 Intelligent DAQ Environment Installer Script ---

[Setup]
AppName=Intelligent DAQ Environment
AppVersion=1.0
AppPublisher=Sulaymon Saidmurotov
DefaultDirName={autopf}\IntelligentDAQ
DefaultGroupName=Intelligent DAQ
OutputDir=C:\Users\sulay\Desktop\DAQ_Setup_Output
OutputBaseFilename=DAQ_System_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
; Flutter ilovasining barcha fayllari
Source: "C:\Users\sulay\PycharmProjects\DAQ_systems\flutter_ui\build\windows\x64\runner\Release\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Backend server fayli
Source: "C:\Users\sulay\PycharmProjects\DAQ_systems\backend_server.exe"; DestDir: "{app}"; Flags: ignoreversion
; Templates papkasi
Source: "C:\Users\sulay\PycharmProjects\DAQ_systems\templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Intelligent DAQ"; Filename: "{app}\daq_sensor_dashboard.exe"
Name: "{autodesktop}\Intelligent DAQ"; Filename: "{app}\daq_sensor_dashboard.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\daq_sensor_dashboard.exe"; Description: "{cm:LaunchProgram,Intelligent DAQ}"; Flags: nowait postinstall skipifsilent
```