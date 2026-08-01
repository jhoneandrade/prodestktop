import tkinter as tk
from PIL import Image, ImageTk
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

# Variáveis de controle de imagem
caminho_imagem_atual = None
imagem_fundo_salva = None  
id_imagem_canvas = None     

# Textos na tela
id_texto_loja = canvas.create_text(largura_tela / 2, altura_tela / 12,
                                   text=NOME_LOJA,
                                   font=("Helvetica", 60, "bold"),
                                   fill="orange")

texto_titulo_status = canvas.create_text(largura_tela / 2, altura_tela / 5 - 40,
                   text="CAIXA FECHADO",
                   font=("Helvetica", 45, "bold"),
                   fill="red",
                   justify="center")

texto_secundario_status = canvas.create_text(largura_tela / 2, altura_tela / 2 + 20,
                   text="Aperte F12 para acessar com seu usuário",
                   font=("Helvetica", 25),
                   fill="orange",
                   justify="center")

# Relógio e Data
texto_relogio = canvas.create_text(largura_tela - 150, 50,
                    text="00:00:00",
                    font=("Helvetica", 50, "bold"),
                    fill="orange")

texto_data = canvas.create_text(largura_tela - 150, 110,
                    text="00/00/0000",
                    font=("Helvetica", 18, "bold"),
                    fill="orange")

# IP Computador Rede
nome_computador = socket.gethostname()
ip_maquina = socket.gethostbyname(nome_computador)

canvas.create_text(30, altura_tela - 50,
                     text=f"Terminal: {nome_computador} | IP: {ip_maquina}",
                     font=("Helvetica", 10, "bold"),
                     fill="white",
                     anchor="sw")

texto_internet = canvas.create_text(350, altura_tela - 50, 
                    text=status_int, 
                    font=("Helvetica", 10, "bold"), 
                    fill=cor_int, 
                    anchor="sw")

texto_servidor = canvas.create_text(550, altura_tela - 50, 
                    text=status_srv, 
                    font=("Helvetica", 10, "bold"), 
                    fill=cor_srv,    
                    anchor="sw")

texto_usuario_caixa = canvas.create_text(880, altura_tela - 50, 
                    text="", 
                    font=("Helvetica", 10, "bold"), 
                    fill="white",    
                    anchor="sw")

# Campo de Busca Rápida de Produtos (Modo Repouso)
frame_busca = tk.Frame(janela, bg="black")
lbl_busca = tk.Label(frame_busca, text="Consulta Rápida", font=("Helvetica", 14), fg="orange", bg="black")
lbl_busca.pack(side="top", pady=(0, 10))

# Validação para aceitar apenas números
def somente_numeros(P):
    return P == "" or P.isdigit()
vcmd = (janela.register(somente_numeros), '%P')

entry_busca = tk.Entry(frame_busca, font=("Helvetica", 20), width=30, bg="#222", fg="white", insertbackground="white", relief="flat", highlightbackground="#555", highlightthickness=1, justify="center", validate="key", validatecommand=vcmd)
entry_busca.pack(side="top")

canvas.create_window(largura_tela / 2, altura_tela / 2 + 100, window=frame_busca)

texto_resultado_busca = canvas.create_text(largura_tela / 2, altura_tela / 2 + 180,
                                           text="",
                                           font=("Helvetica", 25, "bold"),
                                           fill="lime",
                                           justify="center")

id_timer_busca = None

def limpar_resultado_busca():
    canvas.itemconfig(texto_resultado_busca, text="")

def exibir_resultado(texto, cor):
    global id_timer_busca
    if id_timer_busca:
        janela.after_cancel(id_timer_busca)
    canvas.itemconfig(texto_resultado_busca, text=texto, fill=cor)
    id_timer_busca = janela.after(10000, limpar_resultado_busca)

def realizar_busca(event=None):
    codigo = entry_busca.get().strip()
    if codigo:
        entry_busca.delete(0, tk.END)
        canvas.itemconfig(texto_resultado_busca, text=f"Buscando {codigo}...", fill="yellow")
        
        def buscar_no_banco():
            resultado = consultar_produto(codigo)
            if resultado["encontrado"]:
                desc = resultado["descricao"]
                preco_v = resultado["preco_venda"]
                preco_p = resultado["preco_promocao"]
                
                texto_venda = f"R$ {preco_v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                if preco_p > 0:
                    texto_promo = f"R$ {preco_p:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    texto_exibicao = f"{desc}    |    Valor Normal: {texto_venda}    |    Promoção: {texto_promo}"
                else:
                    texto_exibicao = f"{desc}    |    Valor: {texto_venda}"
                
                cor = "lime"
            else:
                texto_exibicao = resultado.get("erro", "Produto não encontrado")
                cor = "red"
                
            janela.after(0, lambda: exibir_resultado(texto_exibicao, cor))
            
        threading.Thread(target=buscar_no_banco, daemon=True).start()

entry_busca.bind('<Return>', realizar_busca)

# Funções de atualização da interface
def atualizar_relogio():
    hora_atual = time.strftime('%H:%M:%S')
    data_atual = time.strftime('%d/%m/%Y')
    canvas.itemconfig(texto_relogio, text=hora_atual)
    canvas.itemconfig(texto_data, text=data_atual)
    janela.after(1000, atualizar_relogio)
    
atualizar_relogio()

def atualizar_tela_redes():
    # Puxa as variáveis atualizadas do arquivo redes.py
    import redes
    canvas.itemconfig(texto_internet, text=redes.status_int, fill=redes.cor_int)
    canvas.itemconfig(texto_servidor, text=redes.status_srv, fill=redes.cor_srv)
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
        texto_titulo = ""
        texto_secundario = "Aperte ESC, F12 ou ESPAÇO para retornar ao PDV"
        texto_rodape = f"Usuário Atual: {usuario}" if usuario else ""
    else:
        texto_titulo = "CAIXA FECHADO"
        texto_secundario = "Aperte F12 para acessar com seu usuário"
        texto_rodape = f"Último Usuário: {usuario}" if usuario else ""
        
    def aplicar():
        canvas.itemconfig(texto_titulo_status, text=texto_titulo)
        canvas.itemconfig(texto_secundario_status, text=texto_secundario)
        canvas.itemconfig(texto_usuario_caixa, text=texto_rodape)
        
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
    global caminho_imagem_atual, imagem_fundo_salva, id_imagem_canvas
    
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
                imagem_fundo_salva = ImageTk.PhotoImage(img_redim)
                
                if id_imagem_canvas is None:
                    id_imagem_canvas = canvas.create_image(0, 0, image=imagem_fundo_salva, anchor="nw")
                else:
                    canvas.itemconfig(id_imagem_canvas, image=imagem_fundo_salva)
                
                canvas.tag_lower(id_imagem_canvas)
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