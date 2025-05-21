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

# !!!!! BLOCO DE CSS REMOVIDO PARA GARANTIR VISIBILIDADE DO CONTEÚDO !!!!!
# Se o conteúdo aparecer agora, o CSS anterior era o problema.
# Para re-estilizar, adicione regras CSS gradualmente e teste.

st.title("🔒 Portal de Diagnóstico")

# --- Configurações de Arquivos ---
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
ST_KEY_VERSION = "v28_no_css" 

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0), # Adicionado de volta
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None, # Adicionado de volta
    "pdf_gerado_path": None, "pdf_gerado_filename": None, # Adicionado de volta
    "feedbacks_respostas": {}, # Adicionado de volta
    "confirmou_instrucoes_checkbox_cliente": False, # Adicionado de volta
    "admin_user_login_identifier": None, "last_cnpj_input": "" 
} 
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias ---
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
            try:
                # Verificar se todas as colunas existem, adicionar se faltar
                df_check = pd.read_csv(filepath, encoding='utf-8', nrows=0) 
                # Garantir que o dtype seja string para colunas de ID/chave ao ler completo
                dtype_map_read = {}
                if filepath == usuarios_csv or filepath == usuarios_bloqueados_csv or filepath == arquivo_csv or filepath == historico_csv:
                    dtype_map_read['CNPJ'] = str
                if filepath == notificacoes_csv:
                    dtype_map_read['CNPJ_Cliente'] = str
                
                temp_df_to_save = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_map_read if dtype_map_read else None)
                col_missing = False

                for col_idx, col_name in enumerate(columns):
                    if col_name not in df_check.columns:
                        default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                        # Adicionar coluna com tipo de dado consistente se possível
                        if pd.api.types.is_numeric_dtype(default_val) and defaults:
                             temp_df_to_save.insert(loc=min(col_idx, len(temp_df_to_save.columns)), column=col_name, value=pd.Series([default_val] * len(temp_df_to_save), dtype=type(default_val)))
                        else:
                             temp_df_to_save.insert(loc=min(col_idx, len(temp_df_to_save.columns)), column=col_name, value=default_val)
                        col_missing = True
                if col_missing:
                    temp_df_to_save.to_csv(filepath, index=False, encoding='utf-8')
            except pd.errors.EmptyDataError: 
                df_init = pd.DataFrame(columns=columns)
                if defaults:
                    for col, default_val in defaults.items():
                        if col in columns: df_init[col] = default_val
                df_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e:
        st.error(f"Erro Crítico ao inicializar ou ler o arquivo {filepath}: {e}")


try:
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    if not (os.path.exists(admin_credenciais_csv) and os.path.getsize(admin_credenciais_csv) > 0):
        pd.DataFrame([{"Usuario": "admin", "Senha": "admin"}]).to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
        st.sidebar.info("Admin padrão (admin/admin) criado para primeiro uso.")

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

# --- Funções Utilitárias Completas ---
def criar_notificacao(cnpj_cliente, mensagem, data_diag_ref=None):
    try:
        if os.path.exists(notificacoes_csv) and os.path.getsize(notificacoes_csv) > 0:
            df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
        else:
            df_notificacoes = pd.DataFrame(columns=colunas_base_notificacoes)
        msg_final = mensagem
        if data_diag_ref:
            msg_final = f"O consultor adicionou comentários ao seu diagnóstico de {data_diag_ref}."
        nova_notificacao = {"ID_Notificacao": str(uuid.uuid4()), "CNPJ_Cliente": str(cnpj_cliente), "Mensagem": msg_final, "DataHora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Lida": False}
        df_notificacoes = pd.concat([df_notificacoes, pd.DataFrame([nova_notificacao])], ignore_index=True)
        df_notificacoes.to_csv(notificacoes_csv, index=False, encoding='utf-8')
    except Exception as e: st.warning(f"Falha ao criar notificação: {e}")

def get_unread_notifications_count(cnpj_cliente):
    try:
        if os.path.exists(notificacoes_csv) and os.path.getsize(notificacoes_csv) > 0:
            df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
            unread_count = len(df_notificacoes[(df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente)) & (df_notificacoes['Lida'] == False)])
            return unread_count
    except Exception as e: st.warning(f"Falha ao ler notificações: {e}")
    return 0

def marcar_notificacoes_como_lidas(cnpj_cliente, ids_notificacoes=None):
    try:
        if os.path.exists(notificacoes_csv) and os.path.getsize(notificacoes_csv) > 0:
            df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
            if ids_notificacoes:
                df_notificacoes.loc[(df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente)) & (df_notificacoes['ID_Notificacao'].isin(ids_notificacoes)), 'Lida'] = True
            else:
                df_notificacoes.loc[df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente), 'Lida'] = True
            df_notificacoes.to_csv(notificacoes_csv, index=False, encoding='utf-8')
            return True
    except Exception as e: st.error(f"Erro ao marcar notificações como lidas: {e}"); 
    return False

def registrar_acao(cnpj, acao, desc):
    try:
        if os.path.exists(historico_csv) and os.path.getsize(historico_csv) > 0:
            hist_df = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
        else:
            hist_df = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
        new_entry = {"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": str(cnpj), "Ação": str(acao), "Descrição": str(desc)}
        hist_df = pd.concat([hist_df, pd.DataFrame([new_entry])], ignore_index=True)
        hist_df.to_csv(historico_csv, index=False, encoding='utf-8')
    except Exception as e: st.warning(f"Falha ao registrar ação no histórico: {e}")

def update_user_data(cnpj, field, value):
    try:
        if not (os.path.exists(usuarios_csv) and os.path.getsize(usuarios_csv) > 0) :
            st.error(f"Arquivo de usuários '{usuarios_csv}' não encontrado para atualização."); return False
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
    if df_analises is None or df_analises.empty: return None
    analises_da_pergunta = df_analises[df_analises['TextoPerguntaOriginal'] == pergunta_texto]
    if analises_da_pergunta.empty: return None
    # ... (resto da lógica como antes)
    return None

# --- Funções PDF (Use as versões que você confirmou que funcionam) ---
def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df, respostas_coletadas, medias_cat, analises_df):
    # ... (Use sua versão funcional desta função, garantindo txt=, ln em cell(), etc.)
    st.info("Placeholder para gerar_pdf_diagnostico_completo. Restaure sua lógica.")
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
                            else: temp_line_for_calc += word + " "
                        num_lines = num_l_calc
                    except: num_lines = int(pdf.get_string_width(cell_text_calc) / cell_w_calc) + 1 if cell_w_calc > 0 else 1
                current_cell_content_height = num_lines * line_height_for_multicell
                max_cell_height_in_row = max(max_cell_height_in_row, current_cell_content_height)
            current_row_total_height = max(max_cell_height_in_row, line_height_for_multicell)
            if y_start_current_row + current_row_total_height > pdf.page_break_trigger and not pdf.in_footer:
                pdf.add_page()
                y_start_current_row = pdf.get_y() 
                pdf.set_font("Arial", "B", 8); pdf.set_fill_color(200, 220, 255)
                for header_np in headers_to_print_hist:
                     pdf.cell(w=col_widths_config.get(header_np, 30), h=7, txt=pdf_safe_text_output(header_np), border=1, ln=0, align="C", fill=True)
                pdf.ln(7); pdf.set_font("Arial", "", 8)
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
            pdf_path = tmpfile.name; pdf.output(name=pdf_path, dest='F'); return pdf_path
    except Exception as e_pdf_hist:
        st.error(f"Erro ao gerar PDF do histórico: {e_pdf_hist}"); st.exception(e_pdf_hist); return None
# --- FIM DAS FUNÇÕES PDF ---


# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): 
    st.session_state.trigger_rerun_global = False; st.rerun()

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
    # Mantenha o CSS do login-container COMENTADO no st.markdown principal para este teste.
    # Use divs e h2 simples se o CSS estiver desabilitado.
    st.markdown('<div>', unsafe_allow_html=True) 
    st.markdown(f'<h2>Login Administrador 🔑</h2>', unsafe_allow_html=True)
    with st.form(f"form_admin_login_{ST_KEY_VERSION}"): 
        u = st.text_input("Usuário", key=f"admin_u_{ST_KEY_VERSION}")
        p = st.text_input("Senha", type="password", key=f"admin_p_{ST_KEY_VERSION}") 
        if st.form_submit_button("Entrar"):
            try:
                if os.path.exists(admin_credenciais_csv) and os.path.getsize(admin_credenciais_csv) > 0:
                    df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                    admin_encontrado = df_creds[df_creds["Usuario"] == u]
                    if not admin_encontrado.empty and str(admin_encontrado.iloc[0]["Senha"]) == str(p):
                        st.session_state.admin_logado = True
                        st.session_state.admin_user_login_identifier = u 
                        st.success("Login de administrador bem-sucedido! ✅"); st.rerun()
                    else: st.error("Usuário ou senha inválidos.")
                else: st.error(f"Arquivo de credenciais '{admin_credenciais