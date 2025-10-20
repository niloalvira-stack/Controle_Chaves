@echo off
for /r %%f in (*_init_py) do (
    echo Renomeando %%f para __init__.py
    ren "%%f" __init__.py
)
echo Renomeação concluída.
pause