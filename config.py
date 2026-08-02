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
    # Valores padrões nativos
    def_ip = '127.0.0.1'
    def_pdv = '1'
    def_banco = r'C:\GansoPDV\GansoPDV.IB'
    def_filial = '1'
    
    # Tenta ler o PDV.INI original para importar as configurações de forma invisível
    caminho_pdv_ini = r'C:\GansoPDV\PDV.INI'
    if os.path.exists(caminho_pdv_ini):
        try:
            # interpolation=None evita erros caso o INI do Delphi tenha "%"
            pdv_config = configparser.ConfigParser(interpolation=None)
            # Lê o INI com o encoding padrão do sistema (seguro para INIs gerados no Windows/Delphi)
            pdv_config.read(caminho_pdv_ini) 
            
            if pdv_config.has_option('REMOTO', 'IP'):
                def_ip = pdv_config.get('REMOTO', 'IP')
                
            if pdv_config.has_option('LOCAL', 'PDV'):
                def_pdv = pdv_config.get('LOCAL', 'PDV')
                
            if pdv_config.has_option('LOCAL', 'Path_Database'):
                def_banco = pdv_config.get('LOCAL', 'Path_Database')
                
            if pdv_config.has_option('LOCAL', 'FILIAL'):
                def_filial = pdv_config.get('LOCAL', 'FILIAL')
        except Exception:
            pass # Se o arquivo estiver corrompido ou inacessível, usa os padrões nativos
            
    config = configparser.ConfigParser()
    config['REDE'] = {'ip': def_ip}
    config['SISTEMA'] = {
        'pdv': def_pdv,
        'loja': 'ProDesktop',
        'imagem_fundo': 'fundo_moderno.png',
        'caminho_pdv': r'C:\GansoPDV\PDV.exe',
        'ativar_repouso': '900',
        'caminho_banco': def_banco,
        'codigo_filial': def_filial,
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