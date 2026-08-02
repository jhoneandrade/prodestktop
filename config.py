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
        'loja': 'ProDesktop',
        'imagem_fundo': 'fundo_moderno.png',
        'caminho_pdv': r'C:\GansoPDV\PDV.exe',
        'ativar_repouso': '900',
        'caminho_banco': r'C:\GansoPDV\GansoPDV.IB',
        'codigo_filial': '1',
        'exibir_promocoes': 'S',
        'exibir_imagens_promocoes': 'S'
    }
    with open(caminho, 'w', encoding='utf-8') as f:
        config.write(f)

def carregar_config():
    if not os.path.exists(CAMINHO_INI):
        criar_ini_padrao(CAMINHO_INI)
        
    config = configparser.ConfigParser()
    config.read(CAMINHO_INI, encoding="utf-8")
    
    # Atualiza o arquivo existente com as novas chaves caso faltem
    salvar = False
    if not config.has_option("SISTEMA", "exibir_promocoes"):
        if not config.has_section("SISTEMA"):
            config.add_section("SISTEMA")
        config.set("SISTEMA", "exibir_promocoes", "S")
        salvar = True
    if not config.has_option("SISTEMA", "exibir_imagens_promocoes"):
        config.set("SISTEMA", "exibir_imagens_promocoes", "S")
        salvar = True
        
    if salvar:
        with open(CAMINHO_INI, 'w', encoding='utf-8') as f:
            config.write(f)
    
    # Retorna um dicionário com todas as configurações prontas
    return {
        "IP_SERVIDOR": config.get("REDE", "IP", fallback="127.0.0.1"),
        "PDV": config.get("SISTEMA", "PDV", fallback="1"),
        "NOME_LOJA": config.get("SISTEMA", "loja", fallback="ProDesktop"),
        "IMAGEM_FUNDO": config.get("SISTEMA", "IMAGEM_FUNDO", fallback=""),
        "CAMINHO_PDV": config.get("SISTEMA", "CAMINHO_PDV", fallback=""),
        "ATIVAR_REPOUSO": config.getint("SISTEMA", "ATIVAR_REPOUSO", fallback=0),
        "CAMINHO_BANCO": config.get("SISTEMA", "CAMINHO_BANCO", fallback=""),
        "CODIGO_FILIAL": config.get("SISTEMA", "CODIGO_FILIAL", fallback="1"),
        "EXIBIR_PROMOCOES": config.get("SISTEMA", "EXIBIR_PROMOCOES", fallback="S"),
        "EXIBIR_IMAGENS_PROMOCOES": config.get("SISTEMA", "EXIBIR_IMAGENS_PROMOCOES", fallback="S"),
        "CAMINHO_INI": CAMINHO_INI
    }