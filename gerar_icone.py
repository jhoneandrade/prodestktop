import os
from PIL import Image

def converter_para_ico():
    diretorio = os.path.dirname(os.path.abspath(__file__))
    caminho_png = os.path.join(diretorio, "logo_prodesktop.png")
    caminho_ico = os.path.join(diretorio, "logo.ico")
    
    if not os.path.exists(caminho_png):
        print(f"Erro: {caminho_png} não encontrado.")
        return
        
    try:
        img = Image.open(caminho_png)
        img.save(caminho_ico, format='ICO', sizes=[(256, 256)])
        print(f"Ícone gerado com sucesso em: {caminho_ico}")
    except Exception as e:
        print(f"Erro ao gerar ícone: {e}")

if __name__ == "__main__":
    converter_para_ico()
