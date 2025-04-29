@echo off
REM Initialize conda for environment switching in Cursor terminal

REM Add conda to PATH
SET "PATH=%USERPROFILE%\anaconda3\Scripts;%USERPROFILE%\anaconda3;%PATH%"

REM Initialize conda for command line usage
call %USERPROFILE%\anaconda3\Scripts\activate.bat

echo.
echo Conda is now initialized. You can use the following commands:
echo - conda activate [environment_name]  : to switch environment
echo - conda env list                     : to list available environments
echo - conda info                         : to show current environment
echo. 