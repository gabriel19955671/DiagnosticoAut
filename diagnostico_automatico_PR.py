import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import time
from fpdf import FPDF 
import tempfile
import re
import json
import plotly.express as px
import plotly.graph_objects as go 
import uuid

st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", initial_sidebar_state="expanded")

# !!!!! PASSO DE DEPURAÇÃO IMPORTANTE !!!!!
# !!!!! PARA TESTAR, MANTENHA A LINHA ABAIXO COMENTADA INICIALMENTE !!!!!
# st.markdown("""
# <style>
# /* SEU CSS PERSONALIZADO AQUI */
# .login-container { max-width: 400px; margin: 60px auto 0 auto; padding: 40px; border-radius: 8px; background-color: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.15); font-family: 'Segoe UI', sans-serif; }
# .login-container h2 { text-align: center; margin-bottom: 30px; font-weight: 600; font-size: 26px; color: #2563eb; }
# /* ... (COLE SEU CSS COMPLETO AQUI SE DESCOMENTAR) ... */
# .kpi-card .value { font-size: 1.8em; font-weight: bold; color: #2563eb; }
# </style>
# """, unsafe_allow_html=True)
# !!!!! SE O CONTEÚDO APARECER APÓS COMENTAR, O PROBLEMA ESTÁ NO SEU CSS !!!!!

st.title("🔒 Portal de Diagnóstico")

admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv"
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv"
historico_csv = "historico_clientes.csv"
analises_perguntas_csv = "analises_perguntas.csv"
notificacoes_csv = "notificacoes.csv"
instrucoes_txt_file = "instrucoes_clientes.txt"
LOGOS_DIR = "client_logos"
ST_KEY_VERSION = "v25_restore" 

default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {},
    "confirmou_instrucoes_checkbox_cliente": False,
    "admin_user_login_identifier": None,
    "last_cnpj_input": "" 
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_'); s = re.sub(r'(?u)[^-\w.]', '', s); return s
def pdf_safe_text_output(text): 
    return str(text).encode('latin-1', 'replace').decode('latin-1')
def find_client_logo_path(cnpj_arg):
    if not cnpj_arg: return None
    base = str(cnpj_arg).replace('/', '').replace('.', '').replace('-', '')
    for ext in ["png", "jpg", "jpeg"]:
        path = os.path.join(LOGOS_DIR, f"{base}_logo.{ext}")
        if os.path.exists(path): return path
    return None

if not os.path.exists(LOGOS_DIR):
    try: os.makedirs(LOGOS_DIR)
    except OSError as e: st.error(f"Erro ao criar diretório de logos '{LOGOS_DIR}': {e}")

colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone",
                         "ConfirmouInstrucoesParaSlotAtual", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados", "LiberacoesExtrasConcedidas"]
colunas_base_perguntas = ["Pergunta", "Categoria"]
colunas_base_analises = ["ID_Analise", "TextoPerguntaOriginal", "TipoCondicao", "CondicaoValorMin", "CondicaoValorMax", "CondicaoValorExato", "TextoAnalise"]
colunas_base_notificacoes = ["ID_Notificacao", "CNPJ_Cliente", "Mensagem", "DataHora", "Lida"]

def inicializar_csv(filepath, columns, defaults=None):
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init = pd.DataFrame(columns=columns)
            if defaults:
                for col, default_val in defaults.items():
                    if col in columns: df_init[col] = default_val
            df_init.to_csv(filepath, index=False, encoding='utf-8')
        else:
            # Verificar se todas as colunas existem, adicionar se faltar
            try:
                df_check = pd.read_csv(filepath, encoding='utf-8', nrows=0) # Ler só cabeçalhos
                col_missing = False
                temp_df_to_save = pd.read_csv(filepath, encoding='utf-8') # Ler completo para adicionar colunas

                for col_idx, col_name in enumerate(columns):
                    if col_name not in df_check.columns:
                        default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                        temp_df_to_save.insert(loc=min(col_idx, len(temp_df_to_save.columns)), column=col_name, value=default_val)
                        col_missing = True
                if col_missing:
                    temp_df_to_save.to_csv(filepath, index=False, encoding='utf-8')
            except pd.errors.EmptyDataError: # Arquivo só com cabeçalho ou totalmente vazio
                df_init = pd.DataFrame(columns=columns)
                if defaults:
                    for col, default_val in defaults.items():
                        if col in columns: df_init[col] = default_val
                df_init.to_csv(filepath, index=False, encoding='utf-8')


    except Exception as e:
        st.error(f"Erro Crítico ao inicializar ou ler o arquivo {filepath}: {e}")

try:
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios, defaults={"ConfirmouInstrucoesParaSlotAtual": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0, "LiberacoesExtrasConcedidas": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"]) 
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos) 
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False}) 

    if not os.path.exists(instrucoes_txt_file):
        with open(instrucoes_txt_file, "w", encoding="utf-8") as f:
            f.write("""**Bem-vindo ao Portal de Diagnóstico Empresarial!** (Conteúdo padrão das instruções)""")
except Exception as e_init_global:
    st.error(f"⚠️ ERRO CRÍTICO NA INICIALIZAÇÃO GLOBAL DE ARQUIVOS: {e_init_global}")
    st.exception(e_init_global); st.stop() 

# --- Funções Utilitárias (Notificação, Ação, Usuário, Análise) ---
def criar_notificacao(cnpj_cliente, mensagem, data_diag_ref=None):
    try:
        df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df_notificacoes = pd.DataFrame(columns=colunas_base_notificacoes)
    msg_final = mensagem
    if data_diag_ref:
        msg_final = f"O consultor adicionou comentários ao seu diagnóstico de {data_diag_ref}."
    nova_notificacao = {"ID_Notificacao": str(uuid.uuid4()), "CNPJ_Cliente": str(cnpj_cliente), "Mensagem": msg_final, "DataHora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Lida": False}
    df_notificacoes = pd.concat([df_notificacoes, pd.DataFrame([nova_notificacao])], ignore_index=True)
    df_notificacoes.to_csv(notificacoes_csv, index=False, encoding='utf-8')

def get_unread_notifications_count(cnpj_cliente):
    try:
        df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
        unread_count = len(df_notificacoes[(df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente)) & (df_notificacoes['Lida'] == False)])
        return unread_count
    except: return 0

def marcar_notificacoes_como_lidas(cnpj_cliente, ids_notificacoes=None):
    try:
        df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
        if ids_notificacoes:
            df_notificacoes.loc[(df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente)) & (df_notificacoes['ID_Notificacao'].isin(ids_notificacoes)), 'Lida'] = True
        else:
            df_notificacoes.loc[df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente), 'Lida'] = True
        df_notificacoes.to_csv(notificacoes_csv, index=False, encoding='utf-8')
        return True
    except Exception as e: st.error(f"Erro ao marcar notificações como lidas: {e}"); return False

def registrar_acao(cnpj, acao, desc):
    try:
        if os.path.exists(historico_csv) and os.path.getsize(historico_csv) > 0:
            hist_df = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
        else:
            hist_df = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
        new_entry = {"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": desc}
        hist_df = pd.concat([hist_df, pd.DataFrame([new_entry])], ignore_index=True)
        hist_df.to_csv(historico_csv, index=False, encoding='utf-8')
    except Exception as e_hist: st.error(f"Erro ao registrar ação no histórico: {e_hist}")

def update_user_data(cnpj, field, value):
    try:
        users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
        idx = users_df[users_df['CNPJ'] == str(cnpj)].index
        if not idx.empty:
            users_df.loc[idx, field] = value
            users_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
            if 'user' in st.session_state and st.session_state.user and str(st.session_state.user.get('CNPJ')) == str(cnpj):
                if field in ["DiagnosticosDisponiveis", "TotalDiagnosticosRealizados", "LiberacoesExtrasConcedidas"]:
                    st.session_state.user[field] = int(value)
                elif field == "ConfirmouInstrucoesParaSlotAtual":
                    st.session_state.user[field] = str(value).lower() == "true"
                else:
                    st.session_state.user[field] = value
            return True
    except Exception as e: st.error(f"Erro ao atualizar usuário ({field}): {e}")
    return False

@st.cache_data
def carregar_analises_perguntas():
    try: 
        if os.path.exists(analises_perguntas_csv) and os.path.getsize(analises_perguntas_csv) > 0:
            return pd.read_csv(analises_perguntas_csv, encoding='utf-8')
    except Exception as e: st.warning(f"Erro ao carregar análises: {e}")
    return pd.DataFrame(columns=colunas_base_analises)

def obter_analise_para_resposta(pergunta_texto, resposta_valor, df_analises):
    if df_analises.empty: return None
    # ... (lógica mantida)
    return None


# --- Funções PDF (Corrigidas para pyfpdf 1.7.x - txt=, ln em cell(), sem ln em multi_cell()) ---
def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df, respostas_coletadas, medias_cat, analises_df):
    # ... (código da função como na última correção - usando txt= e pdf.ln() após multi_cell onde necessário)
    # Omitido para brevidade, mas certifique-se que está correto no seu script final.
    # Use a versão que você confirmou que o PDF do diagnóstico estava OK.
    st.info("Placeholder: gerar_pdf_diagnostico_completo")
    return None 

def gerar_pdf_historico(df_historico_filtrado, titulo="Histórico de Ações"):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(w=0, h=10, txt=pdf_safe_text_output(titulo), border=0, ln=1, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "B", 8) 
        col_widths_config = {"Data": 35, "CNPJ": 35, "Ação": 40, "Descrição": 0} 
        
        page_width_effective = pdf.w - pdf.l_margin - pdf.r_margin
        headers_to_print_hist = [col for col in ["Data", "CNPJ", "Ação", "Descrição"] if col in df_historico_filtrado.columns]
        
        current_total_width_for_others = sum(col_widths_config.get(h,0) for h in headers_to_print_hist if h != "Descrição")
        desc_width = page_width_effective - current_total_width_for_others
        if desc_width <= 0 : desc_width = page_width_effective * 0.3 
        col_widths_config["Descrição"] = max(20, desc_width) 

        pdf.set_fill_color(200, 220, 255) 

        for header in headers_to_print_hist:
            pdf.cell(w=col_widths_config.get(header, 30), h=7, txt=pdf_safe_text_output(header), border=1, ln=0, align="C", fill=True)
        pdf.ln(7) 
        
        pdf.set_font("Arial", "", 8)
        line_height_for_multicell = 5 

        for _, row_data in df_historico_filtrado.iterrows():
            y_start_current_row = pdf.get_y()
            max_cell_height_in_row = line_height_for_multicell

            for header_key_calc in headers_to_print_hist:
                cell_text_calc = str(row_data.get(header_key_calc, ""))
                cell_w_calc = col_widths_config.get(header_key_calc, 30)
                num_lines = 1
                if cell_w_calc > 0 and pdf.get_string_width(cell_text_calc) > cell_w_calc:
                    try:
                        words = cell_text_calc.split(' ')
                        temp_line_for_calc = ""
                        num_l_calc = 1
                        for word in words:
                            if pdf.get_string_width(temp_line_for_calc + word + " ") > cell_w_calc - 2 : 
                                num_l_calc +=1
                                temp_line_for_calc = word + " "
                            else:
                                temp_line_for_calc += word + " "
                        num_lines = num_l_calc
                    except: 
                        num_lines = int(pdf.get_string_width(cell_text_calc) / cell_w_calc) + 1 if cell_w_calc > 0 else 1
                
                current_cell_content_height = num_lines * line_height_for_multicell
                max_cell_height_in_row = max(max_cell_height_in_row, current_cell_content_height)
            
            current_row_total_height = max(max_cell_height_in_row, line_height_for_multicell)

            if y_start_current_row + current_row_total_height > pdf.page_break_trigger and not pdf.in_footer:
                pdf.add_page()
                y_start_current_row = pdf.get_y() 
                pdf.set_font("Arial", "B", 8)
                pdf.set_fill_color(200, 220, 255)
                for header_np in headers_to_print_hist:
                     pdf.cell(w=col_widths_config.get(header_np, 30), h=7, txt=pdf_safe_text_output(header_np), border=1, ln=0, align="C", fill=True)
                pdf.ln(7)
                pdf.set_font("Arial", "", 8)
            
            current_x = pdf.l_margin
            for header_key_draw in headers_to_print_hist:
                pdf.set_xy(current_x, y_start_current_row) 
                cell_content = str(row_data.get(header_key_draw, ""))
                cell_w = col_widths_config.get(header_key_draw, 30)
                
                pdf.rect(current_x, y_start_current_row, cell_w, current_row_total_height)
                pdf.multi_cell(w=cell_w, h=line_height_for_multicell, txt=pdf_safe_text_output(cell_content), border=0, align="L") 
                current_x += cell_w 
            
            pdf.set_y(y_start_current_row + current_row_total_height)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf_path = tmpfile.name
            pdf.output(name=pdf_path, dest='F') 
        return pdf_path
    except Exception as e_pdf_hist:
        st.error(f"Erro ao gerar PDF do histórico: {e_pdf_hist}")
        st.exception(e_pdf_hist) 
        return None
# --- FIM DAS FUNÇÕES PDF ---


# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): 
    st.session_state.trigger_rerun_global = False
    st.rerun()

st.sidebar.write(f"DEBUG (antes radio): admin_logado={st.session_state.get('admin_logado', False)}, cliente_logado={st.session_state.get('cliente_logado', False)}")

if not st.session_state.get("admin_logado", False) and not st.session_state.get("cliente_logado", False):
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key=f"tipo_usuario_radio_{ST_KEY_VERSION}") 
elif st.session_state.get("admin_logado", False): 
    aba = "Administrador"
else: 
    aba = "Cliente"

st.sidebar.write(f"DEBUG (após radio): aba='{aba}'")

# --- ÁREA DE LOGIN DO ADMINISTRADOR (RESTAURADA) ---
if aba == "Administrador" and not st.session_state.get("admin_logado", False):
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown(f'<h2 class="login-title">Login Administrador 🔑</h2>', unsafe_allow_html=True)
    with st.form(f"form_admin_login_{ST_KEY_VERSION}"): 
        u = st.text_input("Usuário", key=f"admin_u_{ST_KEY_VERSION}")
        p = st.text_input("Senha", type="password", key=f"admin_p_{ST_KEY_VERSION}") 
        if st.form_submit_button("Entrar"):
            try:
                if os.path.exists(admin_credenciais_csv) and os.path.getsize(admin_credenciais_csv) > 0:
                    df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                    admin_encontrado = df_creds[df_creds["Usuario"] == u]
                    if not admin_encontrado.empty and admin_encontrado.iloc[0]["Senha"] == p:
                        st.session_state.admin_logado = True
                        st.session_state.admin_user_login_identifier = u 
                        st.success("Login de administrador bem-sucedido! ✅"); st.rerun()
                    else: st.error("Usuário ou senha inválidos.")
                else:
                     st.error(f"Arquivo de credenciais '{admin_credenciais_csv}' não encontrado ou vazio.")
            except Exception as e: st.error(f"Erro no login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DE LOGIN DO CLIENTE (RESTAURADA) ---
if aba == "Cliente" and not st.session_state.get("cliente_logado", False):
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown(f'<h2 class="login-title">Login Cliente 🏢</h2>', unsafe_allow_html=True)
    with st.form(f"form_cliente_login_{ST_KEY_VERSION}"): 
        c = st.text_input("CNPJ", key=f"cli_c_{ST_KEY_VERSION}", value=st.session_state.get("last_cnpj_input","")) 
        s = st.text_input("Senha", type="password", key=f"cli_s_{ST_KEY_VERSION}") 
        if st.form_submit_button("Entrar"):
            st.session_state.last_cnpj_input = c
            try:
                # --- Início da Lógica de Login Cliente Restaurada ---
                if not os.path.exists(usuarios_csv) or os.path.getsize(usuarios_csv) == 0:
                    st.error(f"Arquivo de usuários '{usuarios_csv}' não encontrado ou vazio. Contate o administrador.")
                    st.stop()
                
                users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                
                # Garantir que colunas essenciais existam e tenham tipos corretos
                cols_to_check_cliente = {
                    "ConfirmouInstrucoesParaSlotAtual": ("False", str), 
                    "DiagnosticosDisponiveis": (1, int),
                    "TotalDiagnosticosRealizados": (0, int),
                    "LiberacoesExtrasConcedidas": (0, int)
                }
                for col_cliente, (default_val_cliente, col_type_cliente) in cols_to_check_cliente.items():
                    if col_cliente not in users_df.columns: 
                        users_df[col_cliente] = default_val_cliente
                    if col_type_cliente == int:
                        users_df[col_cliente] = pd.to_numeric(users_df[col_cliente], errors='coerce').fillna(default_val_cliente).astype(int)
                    else:
                        users_df[col_cliente] = users_df[col_cliente].astype(str)

                if not os.path.exists(usuarios_bloqueados_csv):
                    st.error(f"Arquivo de usuários bloqueados '{usuarios_bloqueados_csv}' não encontrado. Contate o administrador.")
                    st.stop()
                blocked_df = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                
                if c in blocked_df["CNPJ"].values: 
                    st.error("CNPJ bloqueado."); st.stop()

                match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == s)]
                if match.empty: 
                    st.error("CNPJ ou senha inválidos."); st.stop()

                st.session_state.cliente_logado = True; st.session_state.cnpj = c
                st.session_state.user = match.iloc[0].to_dict()
                st.session_state.user["ConfirmouInstrucoesParaSlotAtual"] = str(st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", "False")).lower() == "true"
                st.session_state.user["DiagnosticosDisponiveis"] = int(st.session_state.user.get("DiagnosticosDisponiveis", 1))
                st.session_state.user["TotalDiagnosticosRealizados"] = int(st.session_state.user.get("TotalDiagnosticosRealizados", 0))
                st.session_state.user["LiberacoesExtrasConcedidas"] = int(st.session_state.user.get("LiberacoesExtrasConcedidas", 0))

                st.session_state.inicio_sessao_cliente = time.time()
                # registrar_acao(c, "Login", "Usuário logou.") # Reativar se a função estiver completa

                pode_fazer_novo_login = st.session_state.user["DiagnosticosDisponiveis"] > st.session_state.user["TotalDiagnosticosRealizados"]
                if pode_fazer_novo_login and not st.session_state.user["ConfirmouInstrucoesParaSlotAtual"]: 
                    st.session_state.cliente_page = "Instruções"
                elif pode_fazer_novo_login and st.session_state.user["ConfirmouInstrucoesParaSlotAtual"]: 
                    st.session_state.cliente_page = "Novo Diagnóstico"
                else: 
                    st.session_state.cliente_page = "Painel Principal"

                st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                st.session_state.respostas_atuais_diagnostico = {}
                st.session_state.progresso_diagnostico_percentual = 0
                st.session_state.progresso_diagnostico_contagem = (0,0)
                st.session_state.feedbacks_respostas = {}
                st.session_state.diagnostico_enviado_sucesso = False
                st.session_state.confirmou_instrucoes_checkbox_cliente = False
                st.success("Login cliente OK! ✅"); st.rerun()
                # --- Fim da Lógica de Login Cliente Restaurada ---
            except FileNotFoundError as fnf_e:
                st.error(f"Erro de configuração: Arquivo {fnf_e.filename} não encontrado. Contate o administrador.")
            except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()


# --- ÁREA DO CLIENTE LOGADO (ESTRUTURA RESTAURADA) ---
if aba == "Cliente" and st.session_state.get("cliente_logado", False):
    # (Seu código completo da área do cliente aqui, com chaves ST_KEY_VERSION)
    # Por enquanto, um placeholder simples:
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}! 👋")
    if st.sidebar.button(f"Sair Cliente", key=f"logout_cli_{ST_KEY_VERSION}"):
        st.session_state.cliente_logado = False
        # Limpar outros estados de cliente
        st.rerun()
    st.header(f"Área Cliente: {st.session_state.get('cliente_page', 'Página Inicial')}")
    st.markdown(f"Conteúdo da página **{st.session_state.get('cliente_page', 'N/A')}** do cliente aqui.")
    # Você precisará restaurar a lógica do menu e das subpáginas do cliente aqui.

# --- ÁREA DO ADMINISTRADOR LOGADO (FOCO NA SEÇÃO HISTÓRICO) ---
if aba == "Administrador" and st.session_state.get("admin_logado", False):
    st.sidebar.write(f"[DEBUG ADMIN] PONTO S1 - Entrou no bloco admin_logado. Chave Sessão: {ST_KEY_VERSION}") 
    try:
        st.sidebar.success("🟢 Admin Logado")
        if st.sidebar.button(f"🚪 Sair do Painel Admin", key=f"logout_admin_{ST_KEY_VERSION}_adm"): 
            st.session_state.admin_logado = False
            if 'admin_user_login_identifier' in st.session_state:
                del st.session_state.admin_user_login_identifier
            st.rerun() 
        
        menu_admin_options = [
            "📊 Visão Geral e Diagnósticos", "🚦 Status dos Clientes", "📜 Histórico de Usuários",
            "📝 Gerenciar Perguntas", "💡 Gerenciar Análises de Perguntas",
            "✍️ Gerenciar Instruções Clientes", "👥 Gerenciar Clientes", 
            "👮 Gerenciar Administradores", "💾 Backup de Dados"
        ]
        menu_admin = st.sidebar.selectbox(
            "Funcionalidades Admin:", 
            menu_admin_options, 
            key=f"admin_menu_selectbox_{ST_KEY_VERSION}_adm" 
        )
        st.sidebar.info(f"[DEBUG Sidebar] Opção: '{menu_admin}'")
        
        admin_page_title_prefix = menu_admin.split(' ')[0] if isinstance(menu_admin, str) and menu_admin else "Admin"
        st.header(f"Painel Admin: {admin_page_title_prefix}")
        st.write(f"[DEBUG Main Panel] Renderizando: {menu_admin}") # Movido para antes do if/elif

        # Lógica de dispatch do menu admin
        if menu_admin == "📊 Visão Geral e Diagnósticos":
            st.subheader("📊 Visão Geral e Diagnósticos")
            st.markdown("Conteúdo para Visão Geral e Diagnósticos (em desenvolvimento).")
            # TODO: Adicionar a lógica real e carregamento de dados para esta seção
            
        elif menu_admin == "🚦 Status dos Clientes":
            st.subheader("🚦 Status dos Clientes")
            st.markdown("Conteúdo para Status dos Clientes (em desenvolvimento).")
            # TODO: Adicionar a lógica real e carregamento de dados para esta seção

        elif menu_admin == "📜 Histórico de Usuários":
            st.subheader("📜 Histórico de Usuários")
            
            # Carregamento de dados DENTRO da seção específica
            df_historico_completo_hu = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"]) # Default empty
            df_usuarios_para_filtro_hu = pd.DataFrame(columns=['CNPJ', 'Empresa', 'NomeContato']) # Default empty
            try:
                if os.path.exists(historico_csv) and os.path.getsize(historico_csv) > 0:
                    df_historico_completo_hu = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
                else:
                    st.info("Arquivo de histórico vazio ou não encontrado.")
                
                if os.path.exists(usuarios_csv) and os.path.getsize(usuarios_csv) > 0:
                    df_usuarios_para_filtro_hu = pd.read_csv(usuarios_csv, encoding='utf-8', usecols=['CNPJ', 'Empresa', 'NomeContato'], dtype={'CNPJ': str})
                else:
                    st.info("Arquivo de usuários vazio ou não encontrado (necessário para filtros de empresa).")

            except Exception as e_hu_load: 
                st.error(f"Erro ao carregar dados para a seção Histórico: {e_hu_load}")
            
            st.markdown("#### Filtros do Histórico")
            col_hu_f1, col_hu_f2 = st.columns(2)
            empresas_hist_list_hu = ["Todas"]
            if not df_usuarios_para_filtro_hu.empty and 'Empresa' in df_usuarios_para_filtro_hu.columns: 
                empresas_hist_list_hu.extend(sorted(df_usuarios_para_filtro_hu['Empresa'].astype(str).unique().tolist()))
            
            emp_sel_hu = col_hu_f1.selectbox("Filtrar por Empresa:", empresas_hist_list_hu, key=f"hist_emp_sel_{ST_KEY_VERSION}_hu_adm")
            termo_busca_hu = col_hu_f2.text_input("Buscar por Nome do Contato, CNPJ, Ação ou Descrição:", key=f"hist_termo_busca_{ST_KEY_VERSION}_hu_adm")
            
            df_historico_filtrado_view_hu = df_historico_completo_hu.copy() # Começa com tudo ou vazio
            cnpjs_da_empresa_selecionada_hu = []

            if emp_sel_hu != "Todas" and not df_usuarios_para_filtro_hu.empty: 
                cnpjs_da_empresa_selecionada_hu = df_usuarios_para_filtro_hu[df_usuarios_para_filtro_hu['Empresa'] == emp_sel_hu]['CNPJ'].tolist()
                if not df_historico_filtrado_view_hu.empty: # Só filtra se houver dados no histórico
                    df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_da_empresa_selecionada_hu)]
            
            if termo_busca_hu.strip() and not df_historico_filtrado_view_hu.empty :
                busca_lower_hu = termo_busca_hu.strip().lower()
                cnpjs_match_nome_hu = []
                if not df_usuarios_para_filtro_hu.empty and 'NomeContato' in df_usuarios_para_filtro_hu.columns:
                     cnpjs_match_nome_hu = df_usuarios_para_filtro_hu[df_usuarios_para_filtro_hu['NomeContato'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)]['CNPJ'].tolist()
                
                df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[
                    df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_match_nome_hu) | 
                    df_historico_filtrado_view_hu['CNPJ'].astype(str).str.lower().str.contains(busca_lower_hu) | 
                    df_historico_filtrado_view_hu['Ação'].astype(str).str.lower().str.contains(busca_lower_hu, na=False) | 
                    df_historico_filtrado_view_hu['Descrição'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)
                ]
            
            st.markdown("#### Registros do Histórico")
            if not df_historico_filtrado_view_hu.empty:
                st.dataframe(df_historico_filtrado_view_hu.sort_values(by="Data", ascending=False))
                if st.button("📄 Baixar Histórico Filtrado (PDF)", key=f"download_hist_filtrado_pdf_{ST_KEY_VERSION}_hu_adm"):
                    titulo_pdf_hist = f"Historico_Acoes_{sanitize_column_name(emp_sel_hu)}_{sanitize_column_name(termo_busca_hu) if termo_busca_hu else 'Todos'}_{datetime.now().strftime('%Y%m%d')}.pdf"
                    pdf_path_hist = gerar_pdf_historico(df_historico_filtrado_view_hu, titulo=f"Histórico ({emp_sel_hu} - Busca: {termo_busca_hu or 'N/A'})")
                    if pdf_path_hist:
                        with open(pdf_path_hist, "rb") as f_pdf_hist: 
                            st.download_button(label="Download Confirmado", data=f_pdf_hist, file_name=titulo_pdf_hist, mime="application/pdf", key=f"confirm_download_hist_pdf_{ST_KEY_VERSION}_hu_adm")
                        try: os.remove(pdf_path_hist) 
                        except: pass
                
                if emp_sel_hu != "Todas" and not df_historico_filtrado_view_hu.empty and cnpjs_da_empresa_selecionada_hu:
                    st.markdown("---")
                    st.markdown(f"#### 🗑️ Resetar Histórico da Empresa: {emp_sel_hu}")
                    with st.expander(f"⚠️ ATENÇÃO: Excluir TODO o histórico da Empresa '{emp_sel_hu}'"):
                        st.warning(f"Esta ação é irreversível e removerá TODOS os registros de histórico associados à empresa '{emp_sel_hu}' (CNPJs: {', '.join(cnpjs_da_empresa_selecionada_hu)}).")
                        confirm_text_delete_hist = st.text_input(f"Para confirmar, digite o nome da empresa '{emp_sel_hu}' exatamente como mostrado:", key=f"confirm_text_delete_hist_emp_{emp_sel_hu}_{ST_KEY_VERSION}").strip()
                        if st.button(f"🗑️ Excluir Histórico de '{emp_sel_hu}' AGORA", type="primary", key=f"btn_delete_hist_emp_{emp_sel_hu}_{ST_KEY_VERSION}", disabled=(confirm_text_delete_hist != emp_sel_hu)):
                            if confirm_text_delete_hist == emp_sel_hu:
                                try:
                                    if os.path.exists(historico_csv):
                                        df_hist_full_to_update = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
                                        df_hist_full_updated = df_hist_full_to_update[~df_hist_full_to_update['CNPJ'].isin(cnpjs_da_empresa_selecionada_hu)]
                                        df_hist_full_updated.to_csv(historico_csv, index=False, encoding='utf-8')
                                        # registrar_acao("ADMIN_ACTION", "Exclusão Histórico Empresa", f"Admin excluiu todo o histórico da empresa '{emp_sel_hu}' (CNPJs: {', '.join(cnpjs_da_empresa_selecionada_hu)}).") # Reativar quando registrar_acao estiver completa
                                        st.success(f"Todo o histórico da empresa '{emp_sel_hu}' foi excluído com sucesso.")
                                        st.rerun()
                                    else: st.error("Arquivo de histórico não encontrado para realizar a exclusão.")
                                except Exception as e_del_hist: st.error(f"Erro ao excluir o histórico da empresa: {e_del_hist}")
                            else: st.error("O nome da empresa digitado para confirmação está incorreto.")
            else:
                st.info("Nenhum registro de histórico encontrado para os filtros aplicados.")

        # Placeholders para outras seções
        elif menu_admin == "📝 Gerenciar Perguntas":
            st.subheader("📝 Gerenciar Perguntas")
            st.markdown("Conteúdo para Gerenciar Perguntas (em desenvolvimento).")
        elif menu_admin == "💡 Gerenciar Análises de Perguntas":
            st.subheader("💡 Gerenciar Análises de Perguntas")
            st.markdown("Conteúdo para Gerenciar Análises de Perguntas (em desenvolvimento).")
        # ... (adicione placeholders para TODAS as outras opções de menu_admin_options)
        else:
            st.warning(f"[DEBUG ADMIN Main Panel] Opção de menu '{menu_admin}' não corresponde a nenhum bloco if/elif.")
        
        st.write(f"[DEBUG ADMIN Main Panel] PONTO MP4 - Após dispatch do menu")

    except Exception as e_outer_admin_critical:
        st.error(f"Um erro crítico ocorreu na área administrativa: {e_outer_admin_critical}")
        st.exception(e_outer_admin_critical)
        st.write(f"[DEBUG ADMIN Main Panel] PONTO MP_EXCEPT - Dentro do except e_outer_admin_critical ({e_outer_admin_critical})") 

if not st.session_state.get("admin_logado", False) and not st.session_state.get("cliente_logado", False) and ('aba' not in locals() or aba is None):
    st.info("Fallback final: Selecione se você é Administrador ou Cliente para continuar.")