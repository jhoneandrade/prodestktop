import os
import fdb
from config import carregar_config

# Força o Python (64-bits) a carregar o driver 64-bits do Firebird baixado na nossa pasta
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_dll = os.path.join(diretorio_atual, 'fbclient.dll')
if os.path.exists(caminho_dll):
    fdb.load_api(caminho_dll)


def consultar_produto(codigo_busca):
    cfg = carregar_config()
    caminho_banco = cfg.get("CAMINHO_BANCO", "")
    codigo_filial = cfg.get("CODIGO_FILIAL", "1")
    
    if not caminho_banco:
        return {"encontrado": False, "erro": "Caminho do banco não configurado no .ini"}
        
    try:
        # A conexão usa charset UTF8 ou WIN1252 dependendo do banco, fdb lida bem com default na maioria das vezes.
        # Caso retorne caracteres estranhos, podemos adicionar charset='WIN1252' na conexão.
        con = fdb.connect(
            dsn=caminho_banco,
            user="SYSDBA",
            password="1652498327",
            charset="WIN1252"
        )
        cur = con.cursor()
        
        sql = """
            SELECT FIRST 1
                pp.codigo_produto AS codigo_produto,
                p.descricao,
                pp.codigo_filial,
                pp.preco_venda, 
                ppm.valor AS preco_promocao,
                LIST(DISTINCT pcb.codigo_barra, ', ') AS codigos_barras
            FROM produto_parametros pp
            LEFT JOIN produto p ON p.codigo = pp.codigo_produto
            LEFT JOIN produto_promocao ppm ON ppm.codigo_produto = p.codigo 
            LEFT JOIN produto_codigosbarras pcb ON pcb.codigo_produto = p.codigo
            WHERE pp.codigo_filial = ? 
              AND (
                   pcb.codigo_barra = ? 
                   OR CAST(p.codigo AS VARCHAR(50)) = ? 
              )
            GROUP BY 
                pp.codigo_produto,
                p.descricao, 
                pp.codigo_filial,
                pp.preco_venda, 
                ppm.valor
        """
        
        cur.execute(sql, (codigo_filial, codigo_busca, codigo_busca))
        row = cur.fetchone()
        
        if row:
            # row[1] -> descricao
            # row[3] -> preco_venda
            # row[4] -> preco_promocao
            descricao = row[1]
            preco_venda = float(row[3]) if row[3] else 0.0
            preco_promocao = float(row[4]) if row[4] else 0.0
            
            return {
                "encontrado": True,
                "descricao": descricao.strip() if descricao else "Produto sem nome",
                "preco_venda": preco_venda,
                "preco_promocao": preco_promocao
            }
        else:
            return {"encontrado": False, "erro": "Produto não encontrado."}
            
    except Exception as e:
        return {"encontrado": False, "erro": f"Erro de comunicação com banco: {e}"}
    finally:
        if 'con' in locals():
            con.close()

def verificar_status_caixa():
    cfg = carregar_config()
    caminho_banco = cfg.get("CAMINHO_BANCO", "")
    
    if not caminho_banco:
        return {"status": "F", "usuario": ""} # Fallback
        
    try:
        con = fdb.connect(
            dsn=caminho_banco,
            user="SYSDBA",
            password="1652498327",
            charset="WIN1252"
        )
        cur = con.cursor()
        
        sql = "SELECT FIRST 1 status, usuario_abertura, usuario_reabertura FROM caixa"
        cur.execute(sql)
        row = cur.fetchone()
        
        if row:
            status_real = row[0].strip().upper() if row[0] else "F"
            us_abertura = row[1].strip() if row[1] else ""
            us_reabertura = row[2].strip() if row[2] else ""
            
            # A lógica perfeita: se reabertura estiver vazio, é o de abertura.
            # E como o PDV sobrescreve o reabertura, o último será sempre ele (se existir).
            usuario_ativo = us_reabertura if us_reabertura else us_abertura
            
            return {"status": status_real, "usuario": usuario_ativo}
        return {"status": "F", "usuario": ""}
            
    except Exception as e:
        print(f"[BANCO ERRO] Falha ao verificar status: {e}")
        return {"status": "ERRO", "usuario": ""}
    finally:
        if 'con' in locals():
            con.close()
