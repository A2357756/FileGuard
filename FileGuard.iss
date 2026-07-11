[Setup]
AppName=FileGuard
AppVersion=1.0
AppPublisher=Ling
DefaultDirName={autopf}\FileGuard
DefaultGroupName=FileGuard
OutputDir=installer_output
OutputBaseFilename=FileGuard_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
SetupIconFile=fileguard_icon.ico

[Files]
Source: "dist\FileGuard.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "fileguard_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\FileGuard"; Filename: "{app}\FileGuard.exe"; IconFilename: "{app}\fileguard_icon.ico"
Name: "{group}\解除安裝 FileGuard"; Filename: "{uninstallexe}"
Name: "{autodesktop}\FileGuard"; Filename: "{app}\FileGuard.exe"; IconFilename: "{app}\fileguard_icon.ico"

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\FileGuard"