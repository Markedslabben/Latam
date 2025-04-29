@echo off
REM Switch conda environment
IF "%1"=="" (
    echo Usage: switch_env [environment_name]
    echo Available environments:
    conda env list
) ELSE (
    call %USERPROFILE%\anaconda3\Scripts\activate.bat %1
    echo Switched to environment: %1
) 