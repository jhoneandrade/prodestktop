@echo off
echo ========================================================
echo COMPILANDO PRODESKTOP DESCANSO
echo ========================================================

echo Instalando PyInstaller e dependencias (caso nao tenha)...
pip install pyinstaller Pillow fdb

echo Compilando o executavel...
pyinstaller --noconfirm --onefile --windowed --icon "logo.ico" --name "ProDesktop_Descanso" --version-file "version_info.txt" --add-data "fbclient.dll;." --add-data "logo_prodesktop.png;." --add-data "logo.ico;." "main.py"

echo ========================================================
echo COMPILACAO CONCLUIDA!
echo O seu executavel esta dentro da pasta "dist\ProDesktop_Descanso"
echo ========================================================
pause
