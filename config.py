import os
import sys
import configparser

# Caminho inteligente: se for executável único, lê da pasta do .exe. Senão, da pasta do script.
if getattr(sys, 'frozen', False):
    DIRETORIO_ATUAL = os.path.dirname(sys.executable)
else:
    DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
    
CAMINHO_INI = os.path.join(DIRETORIO_ATUAL, 'config.ini')

def criar_ini_padrao(caminho):
    config = configparser.ConfigParser()
    config['REDE'] = {'ip': '127.0.0.1'}
    config['SISTEMA'] = {
        'pdv': '1',
        'nome_loja': 'GANSO SISTEMAS PDV',
        'imagem_fundo': 'fundo_moderno.png',
        'caminho_pdv': r'C:\GansoPDV\PDV.exe',
        'ativar_repouso': '900',
        'caminho_banco': r'C:\GansoPDV\GansoPDV.IB',
        'codigo_filial': '1'
    }
    with open(caminho, 'w', encoding='utf-8') as f:
        config.write(f)

def carregar_config():
    if not os.path.exists(CAMINHO_INI):
        criar_ini_padrao(CAMINHO_INI)
        
    config = configparser.ConfigParser()
    config.read(CAMINHO_INI, encoding="utf-8")
    
    # Retorna um dicionário com todas as configurações prontas
    return {
        "IP_SERVIDOR": config.get("REDE", "IP", fallback="127.0.0.1"),
        "PDV": config.get("SISTEMA", "PDV", fallback="1"),
        "NOME_LOJA": config.get("SISTEMA", "NOME_LOJA", fallback="GANSO SISTEMAS PDV"),
        "IMAGEM_FUNDO": config.get("SISTEMA", "IMAGEM_FUNDO", fallback=""),
        "CAMINHO_PDV": config.get("SISTEMA", "CAMINHO_PDV", fallback=""),
        "ATIVAR_REPOUSO": config.getint("SISTEMA", "ATIVAR_REPOUSO", fallback=0),
        "CAMINHO_BANCO": config.get("SISTEMA", "CAMINHO_BANCO", fallback=""),
        "CODIGO_FILIAL": config.get("SISTEMA", "CODIGO_FILIAL", fallback="1"),
        "CAMINHO_INI": CAMINHO_INI
        
    }