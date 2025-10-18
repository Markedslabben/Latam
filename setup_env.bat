@echo off
REM This script opens two Anaconda Prompt windows

start "" "%windir%\\System32\\cmd.exe" /K "C:\\Users\\%USERNAME%\\anaconda3\\Scripts\\activate.bat"
start "" "%windir%\\System32\\cmd.exe" /K "C:\\Users\\%USERNAME%\\anaconda3\\Scripts\\activate.bat"