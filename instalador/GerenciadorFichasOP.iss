; Script do Inno Setup que gera o instalador do Gerenciador de Fichas OP.
; Não rode direto: use o build.ps1 na raiz do projeto, que gera o executável antes
; e passa a versão lida de app/__init__.py.

#ifndef AppVersion
  #error Rode pelo build.ps1 (ou passe /DAppVersion=x.y.z para o ISCC).
#endif

#define AppName "Gerenciador de Fichas OP"
#define AppExe "GerenciadorFichasOP.exe"

[Setup]
; Identifica o app para o Windows entre versões: nunca mude, senão as atualizações
; passam a ser instaladas como um programa diferente.
AppId={{F42A7CE5-7441-4CE5-A2F3-A91C6BD3AFA2}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Edric Leoni Savio
AppPublisherURL=https://github.com/edricls/gerenciador_fichas_op
AppSupportURL=https://github.com/edricls/gerenciador_fichas_op/issues
VersionInfoVersion={#AppVersion}
; Instala só para o usuário atual, sem pedir permissão de administrador
; (na pasta %LOCALAPPDATA%\Programs); quem quiser pode escolher instalar para todos.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\build\GerenciadorFichasOP\GerenciadorFichasOP.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
OutputDir=..\dist
OutputBaseFilename=GerenciadorFichasOP-{#AppVersion}-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\GerenciadorFichasOP\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

; Os personagens ficam em %APPDATA%\Gerenciador de Fichas OP e não são apagados na
; desinstalação, para que reinstalar ou atualizar o app não faça ninguém perder as fichas.
