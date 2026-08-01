@echo off
title Travar Papel de Parede Definitivo
echo Aplicando bloqueio total do papel de parede...

:: 1. Cria e define a diretiva de bloqueio no registro do usuario atual
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\ActiveDesktop" /v "NoChangingWallPaper" /t REG_DWORD /d 1 /f

:: 2. Cria e define tambem na chave geral do sistema (Machine)
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\ActiveDesktop" /v "NoChangingWallPaper" /t REG_DWORD /d 1 /f

:: 3. Força a atualização das políticas de grupo do Windows instantaneamente
gpupdate /force >nul

:: 4. Reinicia o Explorador de Arquivos para aplicar o bloqueio e fechar telas de config abertas
echo Reiniciando o explorador do Windows para aplicar o bloqueio...
taskkill /f /im explorer.exe >nul
start explorer.exe

echo.
echo [SUCESSO] Bloqueio aplicado! Tente abrir as configuracoes de tema novamente.
echo.
pause