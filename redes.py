import time
import socket
import subprocess
import configparser
from config import carregar_config

# Variáveis globais de status
status_int = "Internet: Buscando..."
cor_int = "yellow"
status_srv = "Servidor: Buscando..."
cor_srv = "yellow"

def loop_verificacao_redes():
    """
    Roda em segundo plano testando a rede e atualiza as variáveis.
    """
    global status_int, cor_int, status_srv, cor_srv
    
    while True:
        cfg = carregar_config()
        ip_servidor = cfg["IP_SERVIDOR"]
        numero_pdv = cfg["PDV"]
        texto_caixa = f"PDV {numero_pdv.zfill(2)}"
        
        # 1. Testa a Internet
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            status_int = "Internet: Online "
            cor_int = "lightgreen"
        except OSError:
            status_int = "Internet: Offline "
            cor_int = "red"
            
        # 2. Testa o Servidor (Ping)
        comando = ["ping", "-n", "1", "-w", "1000", ip_servidor]
        resultado = subprocess.run(comando, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        if resultado.returncode == 0:
            status_srv = f"{texto_caixa} | Servidor {ip_servidor}: Conectado "
            cor_srv = "lightgreen"
        else:
            status_srv = f"{texto_caixa} | Servidor {ip_servidor}: Sem Comunicação "
            cor_srv = "red"
            
        time.sleep(5)