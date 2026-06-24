@echo off
REM Launcher for the sync.dat batch engine (Windows executes .bat, not .dat).
REM Double-click this, or:  sync.bat once | install | uninstall
copy /y "%~dp0sync.dat" "%TEMP%\plumas-sync.cmd" >nul
call "%TEMP%\plumas-sync.cmd" "%~dp0" %*
