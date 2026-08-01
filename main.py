import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import time
import socket 
import threading
import subprocess
import os
import ctypes
# Importando dos nossos arquivos separados
from config import carregar_config
from redes import loop_verificacao_redes, status_int, cor_int, status_srv, cor_srv
from banco import consultar_produto, verificar_status_caixa

# Carrega as configurações iniciais
cfg = carregar_config()
IP_DO_SERVIDOR = cfg["IP_SERVIDOR"]
NUMERO_PDV = cfg["PDV"]
CAMINHO_IMAGEM = cfg["IMAGEM_FUNDO"]
NOME_LOJA = cfg["NOME_LOJA"]
CAMINHO_INI = cfg["CAMINHO_INI"]

# 1. Rotina de Auto-Instalação "Vírus do Bem"
def auto_instalar():
    import sys
    import shutil
    
    if not getattr(sys, 'frozen', False):
        return
        
    exe_atual = sys.executable
    pasta_oficial = r"C:\GansoPDV\DescansoTela"
    exe_oficial = os.path.join(pasta_oficial, "ProDesktop_Descanso.exe")
    
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    startup = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
    
    atalho_desktop = os.path.join(desktop, 'ProDesktop_Descanso.lnk')
    atalho_startup = os.path.join(startup, 'ProDesktop_Descanso.lnk')
    
    def criar_atalhos(alvo):
        vbs_path = os.path.join(os.environ['TEMP'], 'create_shortcut.vbs')
        vbs_content = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{atalho_desktop}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{alvo}"
oLink.WorkingDirectory = "{os.path.dirname(alvo)}"
oLink.Save

sLinkFile2 = "{atalho_startup}"
Set oLink2 = oWS.CreateShortcut(sLinkFile2)
oLink2.TargetPath = "{alvo}"
oLink2.WorkingDirectory = "{os.path.dirname(alvo)}"
oLink2.Save
"""
        if not os.path.exists(atalho_desktop) or not os.path.exists(atalho_startup):
            try:
                with open(vbs_path, "w", encoding="utf-8") as f:
                    f.write(vbs_content)
                subprocess.run(["cscript", "//nologo", vbs_path], creationflags=subprocess.CREATE_NO_WINDOW)
                os.remove(vbs_path)
            except Exception as e:
                print(f"Erro ao criar atalhos: {e}")

    # Verifica se já está rodando do local correto
    if exe_atual.lower() == exe_oficial.lower():
        criar_atalhos(exe_oficial)
        return
        
    # Se está rodando de outro lugar (ex: Downloads), instala e reinicia
    try:
        os.makedirs(pasta_oficial, exist_ok=True)
        shutil.copy2(exe_atual, exe_oficial)
        criar_atalhos(exe_oficial)
        
        # Inicia a cópia correta recém-criada
        os.startfile(exe_oficial)
        
        # Encerra este processo (o usuário não vai nem perceber a piscada)
        sys.exit()
    except Exception as e:
        print(f"Falha na auto-instalação para C:, rodando do local atual: {e}")
        criar_atalhos(exe_atual)

auto_instalar()

def resource_path(relative_path):
    import sys, os
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.dirname(sys.executable), relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

# 2. Cria a janela principal em tela cheia
janela = tk.Tk()
janela.attributes('-fullscreen', True)

# Remove a pena do Tkinter e coloca o ícone oficial na barra de tarefas
try:
    caminho_ico = resource_path('logo.ico')
    if os.path.exists(caminho_ico):
        janela.iconbitmap(caminho_ico)
except Exception:
    pass

largura_tela = janela.winfo_screenwidth()
altura_tela = janela.winfo_screenheight()

canvas = tk.Canvas(janela, width=largura_tela, height=altura_tela, highlightthickness=0, bg="black")
canvas.pack(fill="both", expand=True)

# Funções de escalonamento para 16:9
def f(tamanho):
    return int(tamanho * (largura_tela / 1920))

def px(valor):
    return valor * (largura_tela / 1920)

def py(valor):
    return valor * (altura_tela / 1080)

# Variáveis de controle de imagem
caminho_imagem_atual = None
imagem_fundo_salva = None  
id_imagem_canvas = None     

# ---------------- NOVO LAYOUT (DESIGN MOCKUP) ----------------
# Logo Topo Esquerdo
id_texto_loja = canvas.create_text(px(100), py(100),
                                   text=NOME_LOJA,
                                   font=("Helvetica", f(45), "bold"),
                                   fill="#FF6600", anchor="w")

# Relógio e Data (Canto Superior Direito)
# Deslocados para a esquerda (X=1700) para dar espaço ao relógio analógico
texto_relogio = canvas.create_text(px(1700), py(30),
                    text="00:00:00",
                    font=("Helvetica", f(60), "bold"),
                    fill="#FF6600", anchor="ne")

texto_data = canvas.create_text(px(1700), py(105),
                    text="00 de Janeiro de 0000",
                    font=("Helvetica", f(17)),
                    fill="#AAAAAA", anchor="ne")

texto_dia_semana = canvas.create_text(px(1700), py(130),
                    text="Sábado",
                    font=("Helvetica", f(17), "bold"),
                    fill="#FF6600", anchor="ne")

# --- RELÓGIO ANALÓGICO ---
import math
# Linha divisória
canvas.create_line(px(1730), py(40), px(1730), py(140), fill="#444444", width=2)

cx, cy = 1830, 90  # Centro do relógio analógico
raio_relogio = 55

# Marcadores (ticks)
for i in range(12):
    angulo = math.radians(i * 30 - 90)
    # Ticks maiores nos 3, 6, 9, 12
    if i % 3 == 0:
        tx1 = cx + (raio_relogio - 8) * math.cos(angulo)
        ty1 = cy + (raio_relogio - 8) * math.sin(angulo)
        tx2 = cx + raio_relogio * math.cos(angulo)
        ty2 = cy + raio_relogio * math.sin(angulo)
        canvas.create_line(px(tx1), py(ty1), px(tx2), py(ty2), fill="#FF6600", width=4, capstyle="round")
    else:
        tx = cx + raio_relogio * math.cos(angulo)
        ty = cy + raio_relogio * math.sin(angulo)
        canvas.create_oval(px(tx-2), py(ty-2), px(tx+2), py(ty+2), fill="#FF6600", outline="")

# Ponteiros (criados vazios, serão atualizados no loop)
ponteiro_h = canvas.create_line(px(cx), py(cy), px(cx), py(cy), fill="#FF6600", width=5, capstyle="round")
ponteiro_m = canvas.create_line(px(cx), py(cy), px(cx), py(cy), fill="#FF6600", width=3, capstyle="round")
ponteiro_s = canvas.create_line(px(cx), py(cy), px(cx), py(cy), fill="#FF6600", width=1.5, capstyle="round")

# --- FUNÇÕES AUXILIARES PARA FUNDOS NATIVOS COM GLOW ---
def aplicar_efeito_vidro(largura, altura, x, y):
    global fundo_pil_global
    if 'fundo_pil_global' not in globals() or fundo_pil_global is None:
        # Fallback
        return Image.new('RGBA', (int(largura), int(altura)), (255, 255, 255, 150))
    
    # 1. Crop do fundo (onde a caixa vai ficar)
    crop = fundo_pil_global.crop((int(x), int(y), int(x + largura), int(y + altura)))
    
    # 2. Desfoque intenso (Estilo iOS)
    blur = crop.filter(ImageFilter.GaussianBlur(35)).convert("RGBA")
    
    # Aumentar um pouco o brilho do fundo desfocado para dar aquele ar premium claro
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Brightness(blur)
    blur = enhancer.enhance(1.1)
    
    # 3. Tint esbranquiçado (Gelo) em vez de smoke escuro, para bater com a imagem de referência
    tint = Image.new('RGBA', blur.size, (255, 255, 255, 60))
    glass = Image.alpha_composite(blur, tint)
    return glass

def gerar_caixa_status(largura, altura, cor_glow, x=0, y=0):
    # Valores padrões para a primeira criação (antes das resoluções)
    if x == 0: x = px(1400)
    if y == 0: y = py(180)
    
    img = aplicar_efeito_vidro(largura, altura, x, y)
    
    mask = Image.new('L', img.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([(0, 0), (int(largura)-1, int(altura)-1)], radius=15, fill=255)
    img.putalpha(mask)
    
    border = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw_border = ImageDraw.Draw(border)
    draw_border.rounded_rectangle([(0, 0), (int(largura)-1, int(altura)-1)], radius=15, outline=(255, 255, 255, 130), width=2)
    img = Image.alpha_composite(img, border)
    
    draw = ImageDraw.Draw(img)
    
    glow_colors = {
        "red": (255, 0, 0, 255),
        "green": (0, 255, 0, 255),
        "lime": (50, 205, 50, 255),
        "yellow": (255, 255, 0, 255)
    }
    r, g, b, a = glow_colors.get(cor_glow, (100, 100, 100, 255))
    
    linha_y = int(altura) - 10
    margin = 50
    draw.line([(margin, linha_y), (int(largura)-margin, linha_y)], fill=(r, g, b, 255), width=3)
    
    cx = int(largura * (90/500))
    cy = int(altura * (110/200))
    
    raio_linha = int(altura * 0.35)
    draw.ellipse([(cx - raio_linha, cy - raio_linha), (cx + raio_linha, cy + raio_linha)], outline=(r, g, b, 150), width=2)
    
    return ImageTk.PhotoImage(img)

def gerar_caixa_consulta(largura, altura, raio=15, x=0, y=0):
    if x == 0: x = px(1400)
    if y == 0: y = py(570)
    
    img = aplicar_efeito_vidro(largura, altura, x, y)
    
    mask = Image.new('L', img.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([(0, 0), (int(largura)-1, int(altura)-1)], radius=int(raio), fill=255)
    img.putalpha(mask)
    
    border = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw_border = ImageDraw.Draw(border)
    draw_border.rounded_rectangle([(0, 0), (int(largura)-1, int(altura)-1)], radius=int(raio), outline=(255, 255, 255, 130), width=2)
    img = Image.alpha_composite(img, border)
    
    draw = ImageDraw.Draw(img)
    
    iy1 = int(altura * (135/240))
    iy2 = int(altura * (195/240))
    ix1 = int(largura * (20/500))
    ix2 = int(largura * (480/500))
    
    draw.rounded_rectangle([(ix1, iy1), (ix2, iy2)], radius=10, fill=(0, 0, 0, 60), outline=(255, 255, 255, 60), width=1)
    
    bx_start = int(largura * (40/500))
    by1 = int(altura * (145/240))
    by2 = int(altura * (185/240))
    espaco = int(largura * (4/500))
    
    for i in range(10):
        w = 1 if i % 2 == 0 else 2
        draw.line([(bx_start + i*espaco, by1), (bx_start + i*espaco, by2)], fill=(200, 200, 200, 255), width=w)
        
    return ImageTk.PhotoImage(img)

def gerar_caixa_atalhos(largura, altura, status, raio=15, x=0, y=0):
    if x == 0: x = px(1400)
    if y == 0: y = py(410)
    
    img = aplicar_efeito_vidro(largura, altura, x, y)
    
    mask = Image.new('L', img.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([(0, 0), (int(largura)-1, int(altura)-1)], radius=int(raio), fill=255)
    img.putalpha(mask)
    
    border = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw_border = ImageDraw.Draw(border)
    draw_border.rounded_rectangle([(0, 0), (int(largura)-1, int(altura)-1)], radius=int(raio), outline=(255, 255, 255, 130), width=2)
    img = Image.alpha_composite(img, border)
    
    draw = ImageDraw.Draw(img)
    
    def desenhar_tecla(x1, y1, x2, y2):
        draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=8, fill=(0, 0, 0, 40), outline=(255, 255, 255, 80), width=1)
        
    w = int(largura)
    h = int(altura)
    
    # Altura fixa para as teclas na parte inferior
    y_topo = int(h*(60/140)) if status != "aberto" else int(h*(60/240))
    y_base = int(h*(120/140)) if status != "aberto" else int(h*(120/240))
    
    if status == "aberto":
        # 3 Teclas. Largura total = 80 + 20 + 80 + 20 + 120 = 320. Margem = (500-320)/2 = 90
        # F12: 90 a 170
        desenhar_tecla(int(w*(90/500)), y_topo, int(w*(170/500)), y_base)
        # ESC: 190 a 270
        desenhar_tecla(int(w*(190/500)), y_topo, int(w*(270/500)), y_base)
        # ESPAÇO: 290 a 410
        desenhar_tecla(int(w*(290/500)), y_topo, int(w*(410/500)), y_base)
    else:
        # Apenas F12. Largura = 80. Margem = (500-80)/2 = 210
        desenhar_tecla(int(w*(210/500)), y_topo, int(w*(290/500)), y_base)
        
    return ImageTk.PhotoImage(img)

# --- BLOCO 1 DIREITA (STATUS CAIXA) ---
janela.img_box_status = gerar_caixa_status(px(500), py(200), "red")
id_fundo_status = canvas.create_image(px(1400), py(180), image=janela.img_box_status, anchor="nw")

icone_status = canvas.create_text(px(1490), py(280), text="🔒", font=("Segoe UI Emoji", f(50)), fill="red", anchor="center")
texto_titulo_status = canvas.create_text(px(1560), py(280),
                   text="CAIXA FECHADO",
                   font=("Helvetica", f(30), "bold"),
                   fill="red",
                   anchor="w")

texto_secundario_status = canvas.create_text(px(1560), py(305),
                   text="",
                   font=("Helvetica", f(20)),
                   fill="#AAAAAA",
                   anchor="w")

# --- BLOCO 2 DIREITA (ATALHOS - F12, ESC, ESPAÇO) ---
janela.img_box_atalhos = gerar_caixa_atalhos(px(500), py(140), "fechado")
id_fundo_atalhos = canvas.create_image(px(1400), py(410), image=janela.img_box_atalhos, anchor="nw")

# O texto descritivo fica centralizado na parte de cima da caixa (X absoluto = 1400 + 250 = 1650)
texto_desc_atalhos = canvas.create_text(px(1650), py(445), text="Pressione para abrir o caixa", font=("Helvetica", f(18), "bold"), fill="white", anchor="center")

# Criamos as teclas na parte de baixo da caixa. (Inicialmente fechado, então apenas o F12 fica centralizado em 1650)
texto_btn_f12 = canvas.create_text(px(1650), py(500), text="F12", font=("Helvetica", f(20), "bold"), fill="#FF6600", anchor="center")
texto_btn_esc = canvas.create_text(px(1630), py(500), text="", font=("Helvetica", f(20), "bold"), fill="#FF6600", anchor="center")
texto_btn_espaco = canvas.create_text(px(1750), py(500), text="", font=("Helvetica", f(16), "bold"), fill="#FF6600", anchor="center")

# --- BLOCO 3 DIREITA (CONSULTA RÁPIDA) ---
janela.img_box_consulta = gerar_caixa_consulta(px(500), py(240))
id_fundo_consulta = canvas.create_image(px(1400), py(580), image=janela.img_box_consulta, anchor="nw")

canvas.create_text(px(1460), py(645), text="🔍", font=("Segoe UI Emoji", f(40)), fill="#FF6600", anchor="center")
canvas.create_text(px(1510), py(625), text="CONSULTA RÁPIDA", font=("Helvetica", f(22), "bold"), fill="white", anchor="w")
canvas.create_text(px(1510), py(665), text="Passe o leitor ou digite o código do produto", font=("Helvetica", f(14)), fill="#AAAAAA", anchor="w")

frame_busca = tk.Frame(janela, bg="#111111")
def somente_numeros(P):
    return P == "" or P.isdigit()
vcmd = (janela.register(somente_numeros), '%P')
entry_busca = tk.Entry(frame_busca, font=("Helvetica", f(25)), bg="#111111", fg="white", insertbackground="white", relief="flat", highlightthickness=0, justify="center", validate="key", validatecommand=vcmd)
entry_busca.pack(fill="both", expand=True, padx=2, pady=2)
frame_busca.place(x=px(1490), y=py(720), width=px(385), height=py(50))

# --- FUNDO NATIVO DO RODAPÉ (GERADO VIA PIL) ---
def gerar_fundo_rodape(x=0, y=0):
    if x == 0: x = px(20)
    if y == 0: y = py(920)
    
    largura = int(px(1200))
    altura = int(py(110))
    raio = int(px(15))
    
    img = aplicar_efeito_vidro(largura, altura, x, y)
    
    mask = Image.new('L', img.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([(0, 0), (largura-1, altura-1)], radius=raio, fill=255)
    img.putalpha(mask)
    
    border = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw_border = ImageDraw.Draw(border)
    draw_border.rounded_rectangle([(0, 0), (largura-1, altura-1)], radius=raio, outline=(255, 255, 255, 130), width=2)
    img = Image.alpha_composite(img, border)
    
    draw = ImageDraw.Draw(img)
    
    # Divisórias
    divisores_x = [250, 480, 715, 950]
    for x_val in divisores_x:
        x_linha = int(px(x_val))
        draw.line([(x_linha, 15), (x_linha, altura - 15)], fill=(255, 255, 255, 40), width=1)
        
    return ImageTk.PhotoImage(img)

# Gerar e colocar na tela
img_fundo_rodape = gerar_fundo_rodape()
# Precisamos guardar a referência globalmente para não ser coletada pelo Garbage Collector
janela.img_fundo_rodape = img_fundo_rodape 
id_fundo_rodape = canvas.create_image(px(20), py(920), image=img_fundo_rodape, anchor="nw")

# --- BARRA DE STATUS INFERIOR (RODAPÉ) ---
# 1. Terminal
nome_computador = socket.gethostname()
canvas.create_text(px(80), py(970), text="💻", font=("Segoe UI Emoji", f(30)), fill="#FF6600", anchor="center")
canvas.create_text(px(110), py(950), text="TERMINAL", font=("Helvetica", f(12)), fill="#AAAAAA", anchor="w")
canvas.create_text(px(110), py(990), text=f"{nome_computador}", font=("Helvetica", f(13), "bold"), fill="#FF6600", anchor="w")

# 2. Servidor
icone_servidor = canvas.create_text(px(310), py(970), text="🖧", font=("Segoe UI Emoji", f(45)), fill="lime", anchor="center")
canvas.create_text(px(350), py(950), text="SERVIDOR", font=("Helvetica", f(12)), fill="#AAAAAA", anchor="w")
texto_servidor = canvas.create_text(px(340), py(990), text="Online", font=("Helvetica", f(16), "bold"), fill="lime", anchor="w")

# 3. Internet
icone_internet = canvas.create_text(px(540), py(970), text="🌐", font=("Segoe UI Emoji", f(30)), fill="lime", anchor="center")
canvas.create_text(px(570), py(950), text="INTERNET", font=("Helvetica", f(12)), fill="#AAAAAA", anchor="w")
texto_internet = canvas.create_text(px(570), py(990), text="Online", font=("Helvetica", f(16), "bold"), fill="lime", anchor="w")

# 4. Banco de Dados
icone_banco = canvas.create_text(px(760), py(970), text="🗄️", font=("Segoe UI Emoji", f(30)), fill="lime", anchor="center")
canvas.create_text(px(790), py(950), text="BANCO DE DADOS", font=("Helvetica", f(12)), fill="#AAAAAA", anchor="w")
texto_banco = canvas.create_text(px(790), py(990), text="Conectado", font=("Helvetica", f(16), "bold"), fill="lime", anchor="w")

# 5. Usuário
canvas.create_text(px(1000), py(970), text="👤", font=("Segoe UI Emoji", f(30)), fill="white", anchor="center")
texto_titulo_usuario = canvas.create_text(px(1030), py(950), text="ÚLTIMO USUÁRIO", font=("Helvetica", f(12)), fill="#AAAAAA", anchor="w")
texto_usuario_caixa = canvas.create_text(px(1030), py(990), text="", font=("Helvetica", f(16), "bold"), fill="white", anchor="w")

# --- TEXTOS EXTRAS NO RODAPÉ INFERIOR (Início, Meio e Fim na mesma linha Y=1050) ---
# INÍCIO (Esquerda)
canvas.create_text(px(20), py(1050), text="🛡️", font=("Segoe UI Emoji", f(14)), fill="#FF6600", anchor="w")
canvas.create_text(px(50), py(1050), text="SEGURANÇA", font=("Helvetica", f(14), "bold"), fill="#FF6600", anchor="w")
canvas.create_text(px(165), py(1050), text=" Este terminal é monitorado e protegido", font=("Helvetica", f(14), "bold"), fill="white", anchor="w")

# MEIO (Centro Visual Absoluto)
# Total de caracteres é ~33. O ponto de divisão ("ProDesktop " -> "Tecnologia...") fica levemente deslocado para a esquerda (X=910)
# para que o bloco inteiro fique centralizado em X=960.
canvas.create_text(px(910), py(1050), text="ProDesktop ", font=("Helvetica", f(14), "bold"), fill="#FF6600", anchor="e")
canvas.create_text(px(910), py(1050), text="Tecnologia que conecta", font=("Helvetica", f(14), "bold"), fill="white", anchor="w")

# FIM (Direita)
# Ancorados exatamente na margem direita (1900). 
# "Volte sempre!" ocupa ~120px, então "Obrigado..." termina em 1780.
canvas.create_text(px(1900), py(1050), text="Volte sempre!", font=("Helvetica", f(14), "bold"), fill="#FF6600", anchor="e")
canvas.create_text(px(1780), py(1050), text="Obrigado pela preferência! ", font=("Helvetica", f(14), "bold"), fill="white", anchor="e")

texto_nome_produto = canvas.create_text(px(630), py(400),
                                           text="",
                                           font=("Helvetica", f(35), "bold"),
                                           fill="white",
                                           justify="center",
                                           width=px(1000))  # Quebra de linha automática

texto_preco_produto = canvas.create_text(px(630), py(550),
                                           text="",
                                           font=("Helvetica", f(45), "bold"),
                                           fill="#2ECC71",  # Verde esmeralda moderno
                                           justify="center")

id_timer_busca = None

def limpar_resultado_busca():
    canvas.itemconfig(texto_nome_produto, text="")
    canvas.itemconfig(texto_preco_produto, text="")

def exibir_resultado(nome, valores, cor):
    global id_timer_busca
    if id_timer_busca:
        janela.after_cancel(id_timer_busca)
    canvas.itemconfig(texto_nome_produto, text=nome, fill="white" if cor != "red" else "red")
    canvas.itemconfig(texto_preco_produto, text=valores, fill=cor)
    id_timer_busca = janela.after(5000, limpar_resultado_busca)

def realizar_busca(event=None):
    codigo = entry_busca.get().strip()
    if codigo:
        entry_busca.delete(0, tk.END)
        #-canvas.itemconfig(texto_nome_produto, text=f"Buscando {codigo}...", fill="yellow")
        #-canvas.itemconfig(texto_preco_produto, text="")
        
        def buscar_no_banco():
            resultado = consultar_produto(codigo)
            if resultado["encontrado"]:
                desc = resultado["descricao"]
                preco_v = resultado["preco_venda"]
                preco_p = resultado["preco_promocao"]
                
                texto_venda = f"R$ {preco_v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                if preco_p > 0:
                    texto_promo = f"R$ {preco_p:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    texto_valores = f"Valor Normal: {texto_venda}\nPromoção: {texto_promo}"
                else:
                    texto_valores = f"Valor: {texto_venda}"
                
                cor = "#2ECC71"
            else:
                desc = "PRODUTO NÃO ENCONTRADO"
                texto_valores = ""
                cor = "red"
                
            janela.after(0, lambda: exibir_resultado(desc, texto_valores, cor))
            
        threading.Thread(target=buscar_no_banco, daemon=True).start()

entry_busca.bind('<Return>', realizar_busca)

# Funções de atualização da interface
def atualizar_relogio():
    dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    meses = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    
    agora = time.localtime()
    hora_atual = time.strftime('%H:%M:%S', agora)
    
    dia = agora.tm_mday
    mes = meses[agora.tm_mon]
    ano = agora.tm_year
    data_formatada = f"{dia:02d} de {mes} de {ano}"
    
    dia_semana_atual = dias_semana[agora.tm_wday]
    
    canvas.itemconfig(texto_relogio, text=hora_atual)
    canvas.itemconfig(texto_data, text=data_formatada)
    canvas.itemconfig(texto_dia_semana, text=dia_semana_atual)
    
    # Atualiza Relógio Analógico
    h = agora.tm_hour % 12
    m = agora.tm_min
    s = agora.tm_sec
    
    ang_s = math.radians(s * 6 - 90)
    ang_m = math.radians(m * 6 + s * 0.1 - 90)
    ang_h = math.radians(h * 30 + m * 0.5 - 90)
    
    # Centro e raios
    cx, cy = 1830, 90
    r_s = 45
    r_m = 40
    r_h = 25
    
    canvas.coords(ponteiro_s, px(cx), py(cy), px(cx + r_s * math.cos(ang_s)), py(cy + r_s * math.sin(ang_s)))
    canvas.coords(ponteiro_m, px(cx), py(cy), px(cx + r_m * math.cos(ang_m)), py(cy + r_m * math.sin(ang_m)))
    canvas.coords(ponteiro_h, px(cx), py(cy), px(cx + r_h * math.cos(ang_h)), py(cy + r_h * math.sin(ang_h)))
    
    janela.after(1000, atualizar_relogio)
    
atualizar_relogio()

def atualizar_tela_redes():
    # Puxa as variáveis atualizadas do arquivo redes.py
    import redes
    
    # --- Internet ---
    texto_int = redes.status_int.split(":")[1].strip()
    cor_int = redes.cor_int
    font_int = ("Helvetica", f(13), "bold") if "Offline" in texto_int else ("Helvetica", f(16), "bold")
    canvas.itemconfig(texto_internet, text=texto_int, fill=cor_int, font=font_int)
    canvas.itemconfig(icone_internet, fill=cor_int)
    
    # --- Servidor ---
    status_srv_limpo = "Conectado" if "Conectado" in redes.status_srv else "Sem Comunicação"
    cor_srv = redes.cor_srv
    font_srv = ("Helvetica", f(13), "bold") if status_srv_limpo == "Sem Comunicação" else ("Helvetica", f(16), "bold")
    canvas.itemconfig(texto_servidor, text=status_srv_limpo, fill=cor_srv, font=font_srv)
    canvas.itemconfig(icone_servidor, fill=cor_srv)
    
    janela.after(1000, atualizar_tela_redes)

atualizar_tela_redes()

def pdv_esta_rodando(caminho):
    try:
        nome_exe = os.path.basename(caminho)
        # Usa o filtro do tasklist para ser exato
        comando = ['tasklist', '/FI', f'IMAGENAME eq {nome_exe}', '/NH']
        saida = subprocess.check_output(comando, creationflags=subprocess.CREATE_NO_WINDOW).decode('utf-8', errors='ignore').strip()
        return nome_exe.lower() in saida.lower()
    except Exception:
        return False

def focar_janela_pdv(nome_exe):
    try:
        comando = ['tasklist', '/FI', f'IMAGENAME eq {nome_exe}', '/FO', 'CSV', '/NH']
        saida = subprocess.check_output(comando, creationflags=subprocess.CREATE_NO_WINDOW).decode('utf-8', errors='ignore').strip()
        
        if not saida or saida.startswith("INFO:"):
            return False
            
        pid = None
        for linha in saida.splitlines():
            partes = linha.split('","')
            if len(partes) > 1:
                pid_str = partes[1].replace('"', '')
                if pid_str.isdigit():
                    pid = int(pid_str)
                    break
                    
        if not pid:
            return False
            
        EnumWindows = ctypes.windll.user32.EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
        IsWindowVisible = ctypes.windll.user32.IsWindowVisible
        GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
        SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow
        ShowWindow = ctypes.windll.user32.ShowWindow
        
        hwnd_alvo = None
        
        def foreach_window(hwnd, lParam):
            nonlocal hwnd_alvo
            if IsWindowVisible(hwnd) and GetWindowTextLength(hwnd) > 0:
                pid_janela = ctypes.c_ulong()
                GetWindowThreadProcessId(hwnd, ctypes.byref(pid_janela))
                if pid_janela.value == pid:
                    hwnd_alvo = hwnd
                    return False
            return True
            
        EnumWindows(EnumWindowsProc(foreach_window), 0)
        
        if hwnd_alvo:
            ShowWindow(hwnd_alvo, 9) # SW_RESTORE
            SetForegroundWindow(hwnd_alvo)
            return True
    except Exception as e:
        print(f"Erro ao focar PDV: {e}")
    return False

def ocultar_painel_seguro():
    janela.attributes('-topmost', False)
    janela.lower()
    cfg_atual = carregar_config()
    caminho_executavel = cfg_atual["CAMINHO_PDV"]
    if caminho_executavel:
        focar_janela_pdv(os.path.basename(caminho_executavel))

def abrir_sistema_venda(event=None):
    global modo_descanso_ativo
    
    cfg_atual = carregar_config()
    caminho_executavel = cfg_atual["CAMINHO_PDV"]
    
    if caminho_executavel:
        # Verifica se o processo já está rodando no Windows
        if pdv_esta_rodando(caminho_executavel):
            print("PDV já está rodando. Ocultando painel auxiliar...")
            # Se a tela estiver ativa, usa a função de ocultar que desarma a flag
            if modo_descanso_ativo:
                return ocultar_painel(event)
            else:
                janela.after(150, ocultar_painel_seguro)
        else:
            print(f"PDV fechado! Abrindo o sistema: {caminho_executavel}")
            modo_descanso_ativo = False
            try:
                janela.attributes('-topmost', False)
                os.startfile(caminho_executavel)
                janela.lower()
            except Exception as e:
                print(f"Erro ao abrir: {e}")
    else:
        print("Aviso: CAMINHO_PDV não está configurado.")
    return 'break'

def ocultar_painel(event=None):
    global modo_descanso_ativo
    modo_descanso_ativo = False
    # Espera 150ms antes de jogar a tela para o fundo, para que a tecla física termine de subir
    janela.after(150, ocultar_painel_seguro)
    return 'break'

# Bloqueia o pressionamento (KeyDown) para não vazar a tecla para o PDV 
janela.bind('<F12>', lambda e: 'break')
janela.bind('<Escape>', lambda e: 'break')
janela.bind('<space>', lambda e: 'break')

# Executa as ações apenas quando a tecla for SOLTA (KeyRelease)
janela.bind('<KeyRelease-F12>', abrir_sistema_venda)
janela.bind('<KeyRelease-Escape>', ocultar_painel)
janela.bind('<KeyRelease-space>', ocultar_painel)

# --- LÓGICA DO MODO REPOUSO (Trazendo a nossa tela principal de volta) ---
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint),
                ("dwTime", ctypes.c_uint)]

def get_idle_duration():
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        ticks = ctypes.windll.kernel32.GetTickCount()
        millis = (ticks - lii.dwTime) & 0xFFFFFFFF
        return millis / 1000.0
    return 0.0

cfg_inicial = carregar_config()
tempo_limite_repouso = cfg_inicial["ATIVAR_REPOUSO"]
ativar_repouso = cfg_inicial["ATIVAR_REPOUSO"] > 0

modo_descanso_ativo = False

def forcar_foco_janela(janela_tk):
    try:
        user32 = ctypes.windll.user32
        hwnd = int(janela_tk.wm_frame(), 16)
        
        # Simula um leve toque no ALT. Isso engana a proteção do Windows e permite roubar o foco
        user32.keybd_event(0x12, 0, 0, 0)
        user32.keybd_event(0x12, 0, 2, 0)
        
        foreground_hwnd = user32.GetForegroundWindow()
        if foreground_hwnd == hwnd:
            return
            
        foreground_thread = user32.GetWindowThreadProcessId(foreground_hwnd, None)
        current_thread = ctypes.windll.kernel32.GetCurrentThreadId()
        
        # Anexa a thread atual à thread do PDV temporariamente para burlar o bloqueio
        if foreground_thread and foreground_thread != current_thread:
            user32.AttachThreadInput(current_thread, foreground_thread, True)
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)
            user32.AttachThreadInput(current_thread, foreground_thread, False)
        else:
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)
    except Exception as e:
        print(f"Erro ao forçar foco: {e}")

def atualizar_texto_status():
    dados_caixa = verificar_status_caixa()
    status = dados_caixa.get("status", "F")
    usuario = dados_caixa.get("usuario", "")
    
    if status == 'A':
        texto_titulo = "CAIXA LIVRE"
        texto_secundario = ""
        cor = "lime"
        icone = "🔓"
        cor_icone = "lime"
        texto_titulo_usr = "USUÁRIO ATUAL"
        texto_rodape = f"{usuario}" if usuario else "DESCONHECIDO"
        
        # Banco conectado
        txt_bd = "Conectado"
        cor_bd = "lime"
        font_bd = ("Helvetica", f(16), "bold")
    elif status == 'ERRO':
        texto_titulo = "CAIXA FECHADO"
        texto_secundario = ""
        cor = "red"
        icone = "🔒"
        cor_icone = "red"
        texto_titulo_usr = "ÚLTIMO USUÁRIO"
        texto_rodape = f"{usuario}" if usuario else "NENHUM"
        
        # Banco sem comunicação
        txt_bd = "Sem Comunicação"
        cor_bd = "red"
        font_bd = ("Helvetica", f(13), "bold")
    else:
        texto_titulo = "CAIXA FECHADO"
        texto_secundario = ""
        cor = "red"
        icone = "🔒"
        cor_icone = "red"
        texto_titulo_usr = "ÚLTIMO USUÁRIO"
        texto_rodape = f"{usuario}" if usuario else "NENHUM"
        
        # Banco conectado (Caixa fechado normalmente)
        txt_bd = "Conectado"
        cor_bd = "lime"
        font_bd = ("Helvetica", f(16), "bold")
        
    def aplicar():
        canvas.itemconfig(texto_titulo_status, text=texto_titulo, fill=cor)
        canvas.itemconfig(texto_secundario_status, text=texto_secundario)
        canvas.itemconfig(icone_status, text=icone, fill=cor_icone)
        canvas.itemconfig(texto_titulo_usuario, text=texto_titulo_usr)
        canvas.itemconfig(texto_usuario_caixa, text=texto_rodape)
        
        # Atualiza a cor, fonte e texto do Banco de Dados no rodapé
        canvas.itemconfig(texto_banco, text=txt_bd, fill=cor_bd, font=font_bd)
        canvas.itemconfig(icone_banco, fill=cor_bd)
        
        # Recria a textura da caixa de status
        nova_img_status = gerar_caixa_status(px(500), py(200), cor)
        janela.img_box_status = nova_img_status 
        canvas.itemconfig(id_fundo_status, image=nova_img_status)
        
        # Recria a textura da caixa de atalhos (teclas adicionais se Livre)
        status_atalhos = "aberto" if "LIVRE" in texto_titulo else "fechado"
        nova_img_atalhos = gerar_caixa_atalhos(px(500), py(140), status_atalhos)
        janela.img_box_atalhos = nova_img_atalhos
        canvas.itemconfig(id_fundo_atalhos, image=nova_img_atalhos)
        
        if status_atalhos == "aberto":
            canvas.itemconfig(texto_btn_f12, text="F12")
            canvas.coords(texto_btn_f12, px(1530), py(500))
            
            canvas.itemconfig(texto_btn_esc, text="ESC")
            canvas.coords(texto_btn_esc, px(1630), py(500))
            
            canvas.itemconfig(texto_btn_espaco, text="ESPAÇO")
            canvas.coords(texto_btn_espaco, px(1750), py(500))
            
            canvas.itemconfig(texto_desc_atalhos, text="Pressione para retornar ao caixa")
        else:
            canvas.itemconfig(texto_btn_f12, text="F12")
            canvas.coords(texto_btn_f12, px(1650), py(500))
            
            canvas.itemconfig(texto_btn_esc, text="")
            canvas.itemconfig(texto_btn_espaco, text="")
            canvas.itemconfig(texto_desc_atalhos, text="Pressione para abrir o caixa")
        
    janela.after(0, aplicar)

def ativar_modo_descanso():
    global modo_descanso_ativo
    if not modo_descanso_ativo and 'janela' in globals():
        modo_descanso_ativo = True
        
        # Dispara a verificação no banco em paralelo para não travar a subida da tela
        threading.Thread(target=atualizar_texto_status, daemon=True).start()
        
        janela.deiconify()
        janela.attributes('-fullscreen', True)
        janela.attributes('-topmost', True) 
        janela.lift()
        
        # Executa o roubo agressivo de foco do teclado
        forcar_foco_janela(janela)
        
        janela.focus_force()
        entry_busca.focus_force() 

def registrar_atividade(event=None):
    if event and hasattr(event, 'keysym'):
        if event.keysym.lower() not in ('f12', 'escape', 'space', 'return'):
            # Direciona o foco para o campo de busca se já não estiver
            if janela.focus_get() != entry_busca:
                entry_busca.focus_set()
                if event.char and event.char.isprintable():
                    if event.char.isdigit():
                        entry_busca.insert(tk.END, event.char)
    # A variável modo_descanso_ativo só é desligada pelos atalhos específicos (F12, Esc, Space)

def monitorar_inatividade():
    while True:
        try:
            time.sleep(1)
            if not modo_descanso_ativo:
                tempo_parado = get_idle_duration()
                print(f"[DEBUG] Tempo ocioso atual: {tempo_parado:.1f}s / {tempo_limite_repouso}s", flush=True)
                if tempo_parado >= tempo_limite_repouso:
                    if 'janela' in globals():
                        janela.after(0, ativar_modo_descanso)
        except Exception as e:
            print(f"Erro no monitor: {e}")

# Só ativa o monitoramento se ATIVAR_REPOUSO for maior que 0 no config.ini
if ativar_repouso:
    janela.bind('<Key>', registrar_atividade)
    threading.Thread(target=monitorar_inatividade, daemon=True).start()

def monitorar_fechamento_pdv():
    cfg_atual = carregar_config()
    caminho = cfg_atual.get("CAMINHO_PDV", "")
    if not caminho: return
    
    while True:
        try:
            time.sleep(2)
            # Se a tela está oculta, assumimos que o operador está no PDV
            if not modo_descanso_ativo:
                # Mas se o executável não estiver mais rodando, o PDV foi fechado!
                if not pdv_esta_rodando(caminho):
                    print("[MONITOR] O PDV foi fechado! Subindo a tela auxiliar...")
                    janela.after(0, ativar_modo_descanso)
        except:
            pass

threading.Thread(target=monitorar_fechamento_pdv, daemon=True).start()

# Força a checagem do status do caixa no momento exato em que o painel é aberto pela 1ª vez
threading.Thread(target=atualizar_texto_status, daemon=True).start()

# ------------------------------------------------------------------

def atualizar_fundo_dinamico():
    global caminho_imagem_atual, imagem_fundo_salva, id_imagem_canvas, fundo_pil_global
    global id_fundo_consulta, id_fundo_atalhos, id_fundo_status, id_fundo_rodape
    
    cfg_atual = carregar_config()
    novo_nome = cfg_atual["NOME_LOJA"].strip()
    if novo_nome == "":
        novo_nome = "Ganso Sistemas LTDA"
        
    canvas.itemconfig(id_texto_loja, text=novo_nome)
    
    novo_caminho = cfg_atual["IMAGEM_FUNDO"]
    
    if novo_caminho != caminho_imagem_atual:
        caminho_imagem_atual = novo_caminho 
        if novo_caminho: 
            try:
                img_orig = Image.open(novo_caminho)
                img_redim = img_orig.resize((largura_tela, altura_tela))
                fundo_pil_global = img_redim.copy()
                imagem_fundo_salva = ImageTk.PhotoImage(img_redim)
                
                if id_imagem_canvas is None:
                    id_imagem_canvas = canvas.create_image(0, 0, image=imagem_fundo_salva, anchor="nw")
                else:
                    canvas.itemconfig(id_imagem_canvas, image=imagem_fundo_salva)
                
                canvas.tag_lower(id_imagem_canvas)
                
                # Regerar blocos de vidro com o novo fundo
                nova_img_consulta = gerar_caixa_consulta(px(500), py(240), x=px(1400), y=py(570))
                janela.img_box_consulta = nova_img_consulta
                canvas.itemconfig(id_fundo_consulta, image=nova_img_consulta)
                
                # Para saber se a caixa de atalhos está aberta ou fechada, checamos o status real do texto
                texto_titulo = canvas.itemcget(texto_titulo_status, 'text')
                status_atalhos = "aberto" if "LIVRE" in texto_titulo else "fechado"
                
                nova_img_atalhos = gerar_caixa_atalhos(px(500), py(140) if status_atalhos == "fechado" else py(240), status_atalhos, x=px(1400), y=py(410))
                janela.img_box_atalhos = nova_img_atalhos
                canvas.itemconfig(id_fundo_atalhos, image=nova_img_atalhos)
                
                # Rodapé (agora com vidro)
                nova_img_rodape = gerar_fundo_rodape(x=px(20), y=py(920))
                janela.img_fundo_rodape = nova_img_rodape
                canvas.itemconfig(id_fundo_rodape, image=nova_img_rodape)
                
                # A caixa de status é atualizada sozinha a cada 1 segundo no loop, mas forçamos agora também
                dados_caixa = verificar_status_caixa()
                st = dados_caixa.get("status", "F")
                cor = "lime" if st == 'A' else "red"
                nova_img_status = gerar_caixa_status(px(500), py(200), cor, x=px(1400), y=py(180))
                janela.img_box_status = nova_img_status 
                canvas.itemconfig(id_fundo_status, image=nova_img_status)
                
            except FileNotFoundError:
                if id_imagem_canvas is not None:
                    canvas.delete(id_imagem_canvas)
                    id_imagem_canvas = None
        else:
            if id_imagem_canvas is not None:
                canvas.delete(id_imagem_canvas)
                id_imagem_canvas = None
                
    janela.after(3000, atualizar_fundo_dinamico)

atualizar_fundo_dinamico()

# Inicia a thread de rede em segundo plano
threading.Thread(target=loop_verificacao_redes, daemon=True).start()

janela.mainloop()