; ============================================================
; CheckNumber v9.2 - NSIS Installer Script
; ============================================================

Unicode true

!include "MUI2.nsh"
!include "FileFunc.nsh"

; -------------------- App Info --------------------
Name "CheckNumber"
OutFile "CheckNumber-Setup.exe"
InstallDir "$PROGRAMFILES\CheckNumber"
RequestExecutionLevel admin

VIProductVersion "9.3.0.0"
VIAddVersionKey "ProductName" "CheckNumber"
VIAddVersionKey "CompanyName" "Soup_007"
VIAddVersionKey "FileDescription" "Random Name Picker Setup"
VIAddVersionKey "LegalCopyright" "(c) 2023-2026 Soup_007"

; -------------------- Modern UI --------------------
!define MUI_ABORTWARNING
!define MUI_ICON "app.ico"
!define MUI_UNICON "app.ico"

Var StartMenuFolder
!define MUI_STARTMENUPAGE_DEFAULTFOLDER "CheckNumber"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\CheckNumber.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch CheckNumber"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "SimpChinese"

; -------------------- Install --------------------
Section "Install"
    SetOutPath "$INSTDIR"
    File /r "build\v9.2.dist\*"
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CheckNumber" "DisplayName" "CheckNumber v9.3"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CheckNumber" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CheckNumber" "DisplayIcon" '"$INSTDIR\CheckNumber.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CheckNumber" "Publisher" "Soup_007"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CheckNumber" "DisplayVersion" "9.3"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CheckNumber" "EstimatedSize" "$0"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CheckNumber" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CheckNumber" "NoRepair" 1

    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
        CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
        CreateShortcut "$SMPROGRAMS\$StartMenuFolder\CheckNumber.lnk" "$INSTDIR\CheckNumber.exe"
        CreateShortcut "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    !insertmacro MUI_STARTMENU_WRITE_END

    CreateShortcut "$DESKTOP\CheckNumber.lnk" "$INSTDIR\CheckNumber.exe"
SectionEnd

; -------------------- Uninstall --------------------
Section "Uninstall"
    RMDir /r "$INSTDIR"
    !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
    Delete "$SMPROGRAMS\$StartMenuFolder\CheckNumber.lnk"
    Delete "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk"
    RMDir "$SMPROGRAMS\$StartMenuFolder"
    Delete "$DESKTOP\CheckNumber.lnk"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CheckNumber"
SectionEnd
