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
import plotly.graph_objects as go # Para gráfico de radar
import uuid

# !!! st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT !!!
st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", initial_sidebar_state="expanded")

# CSS
st.markdown("""
<style>
.login-container { max-width: 400px; margin: 60px auto 0 auto; padding: 40px; border-radius: 8px; background-color: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.15); font-family: 'Segoe UI', sans-serif; }
.login-container h2 { text-align: center; margin-bottom: 30px; font-weight: 600; font-size: 26px; color: #2563eb; }
.stButton>button { border-radius: 6px; background-color: #2563eb; color: white; font-weight: 500; padding: 0.5rem 1.2rem; margin-top: 0.5rem; }
.stDownloadButton>button { background-color: #10b981; color: white; font-weight: 600; border-radius: 6px; margin-top: 10px; padding: 0.5rem 1.2rem; }
.stTextInput>div>input, .stTextArea>div>textarea { border-radius: 6px; padding: 0.4rem; border: 1px solid #d1d5db; background-color: #f9fafb; }
.stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; padding: 10px 20px; }
.custom-card { border: 1px solid #e0e0e0; border-left: 5px solid #2563eb; padding: 15px; margin-bottom: 15px; border-radius: 5px; background-color: #f9f9f9; }
.custom-card h4 { margin-top: 0; color: #2563eb; }
.feedback-saved { font-size: 0.85em; color: green; font-style: italic; margin-top: -8px; margin-bottom: 8px; }
.analise-pergunta-cliente { font-size: 0.9em; color: #555; background-color: #f0f8ff; border-left: 3px solid #1e90ff; padding: 8px; margin-top: 5px; margin-bottom:10px; border-radius: 3px;}
.notification-dot { height: 8px; width: 8px; background-color: red; border-radius: 50%; display: inline-block; margin-left: 5px; }
.kpi-card { background-color: #f9f9f9; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; text-align: center; margin-bottom: 10px; }
.kpi-card h4 { font-size: 1.1em; color: #333; margin-bottom: 5px; }
.kpi-card .value { font-size: 1.8em; font-weight: bold; color: #2563eb; }
</style>
""", unsafe_allow_html=True)

st.title("🔒 Portal de Diagnóstico")

# --- Configuração de Arquivos e Variáveis Globais ---
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

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {},
    "confirmou_instrucoes_checkbox_cliente": False
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias ---
def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_'); s = re.sub(r'(?u)[^-\w.]', '', s); return s
def pdf_safe_text_output(text): return str(text).encode('latin-1', 'replace').decode('latin-1')
def find_client_logo_path(cnpj_arg):
    if not cnpj_arg: return None
    base = str(cnpj_arg).replace('/', '').replace('.', '').replace('-', '')
    for ext in ["png", "jpg", "jpeg"]:
        path = os.path.join(LOGOS_DIR, f"{base}_logo.{ext}")
        if os.path.exists(path): return path
    return None

# --- Criação e Verificação de Arquivos e Pastas ---
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
            dtype_spec = {}
            if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, historico_csv]:
                if 'CNPJ' in columns: dtype_spec['CNPJ'] = str
                if 'CNPJ_Cliente' in columns: dtype_spec['CNPJ_Cliente'] = str
            
            df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)
            made_changes = False
            expected_cols_df = pd.DataFrame(columns=columns)
            for col_idx, col_name in enumerate(expected_cols_df.columns):
                if col_name not in df_init.columns:
                    default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                    df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=default_val)
                    made_changes = True
            if made_changes:
                df_init.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError:
        df_init = pd.DataFrame(columns=columns)
        if defaults:
            for col, default_val in defaults.items():
                if col in columns: df_init[col] = default_val
        df_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e:
        st.error(f"Erro ao inicializar ou ler o arquivo {filepath}: {e}")
        st.info(f"Verifique se o arquivo '{filepath}' não está corrompido ou se o programa tem permissão para acessá-lo.")
        raise

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios,
                    defaults={"ConfirmouInstrucoesParaSlotAtual": "False", "DiagnosticosDisponiveis": 1,
                              "TotalDiagnosticosRealizados": 0, "LiberacoesExtrasConcedidas": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False})

    if not os.path.exists(instrucoes_txt_file):
        with open(instrucoes_txt_file, "w", encoding="utf-8") as f:
            # Cole o texto completo das suas instruções aqui
            f.write("""**Bem-vindo ao Portal de Diagnóstico Empresarial!** (Conteúdo Padrão das Instruções - substitua pelo texto completo)""")
except Exception as e_init_global:
    st.error(f"⚠️ ERRO CRÍTICO NA INICIALIZAÇÃO DO APP:")
    st.error(f"Ocorreu um problema ao carregar ou criar os arquivos de dados necessários.")
    st.error(f"Verifique o console/terminal do Streamlit para o traceback completo do Python, se disponível.")
    st.error(f"Detalhes do erro: {e_init_global}")
    st.exception(e_init_global)
    st.warning("A aplicação não pode continuar até que este problema seja resolvido.")
    st.info("""
    Possíveis causas:
    - Um dos arquivos CSV (ex: 'usuarios.csv', 'diagnosticos_clientes.csv') está corrompido.
    - A aplicação não tem permissão para ler/escrever arquivos na pasta onde está rodando.
    - O disco pode estar cheio.
    - Verifique se todos os arquivos CSV esperados existem ou podem ser criados.
    """)
    st.stop()


# --- Funções de Notificação ---
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

# --- Demais Funções Utilitárias ---
def registrar_acao(cnpj, acao, desc):
    try: hist_df = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
    except (FileNotFoundError, pd.errors.EmptyDataError): hist_df = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    new_entry = {"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": desc}
    hist_df = pd.concat([hist_df, pd.DataFrame([new_entry])], ignore_index=True)
    hist_df.to_csv(historico_csv, index=False, encoding='utf-8')

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
    try: return pd.read_csv(analises_perguntas_csv, encoding='utf-8')
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame(columns=colunas_base_analises)

def obter_analise_para_resposta(pergunta_texto, resposta_valor, df_analises):
    if df_analises.empty: return None
    analises_da_pergunta = df_analises[df_analises['TextoPerguntaOriginal'] == pergunta_texto]
    if analises_da_pergunta.empty: return None
    default_analise = None
    for _, row_analise in analises_da_pergunta.iterrows():
        tipo_cond = row_analise['TipoCondicao']; analise_txt = row_analise['TextoAnalise']
        if tipo_cond == 'Default': default_analise = analise_txt; continue
        if tipo_cond == 'FaixaNumerica':
            min_val=pd.to_numeric(row_analise['CondicaoValorMin'],errors='coerce');max_val=pd.to_numeric(row_analise['CondicaoValorMax'],errors='coerce');resp_num=pd.to_numeric(resposta_valor,errors='coerce')
            if pd.notna(resp_num) and pd.notna(min_val) and pd.notna(max_val) and min_val <= resp_num <= max_val: return analise_txt
        elif tipo_cond == 'ValorExatoEscala':
            if str(resposta_valor).strip().lower() == str(row_analise['CondicaoValorExato']).strip().lower(): return analise_txt
        elif tipo_cond == 'ScoreGUT':
            min_s=pd.to_numeric(row_analise['CondicaoValorMin'],errors='coerce');max_s=pd.to_numeric(row_analise['CondicaoValorMax'],errors='coerce');resp_s_gut=pd.to_numeric(resposta_valor,errors='coerce')
            is_min = pd.notna(resp_s_gut) and pd.notna(min_s) and resp_s_gut >= min_s
            is_max_ok = pd.isna(max_s) or (pd.notna(resp_s_gut) and resp_s_gut <= max_s)
            if is_min and is_max_ok: return analise_txt
    return default_analise

def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df, respostas_coletadas, medias_cat, analises_df):
    try:
        pdf = FPDF()
        pdf.add_page()
        empresa_nome = user_data.get("Empresa", "N/D")
        cnpj_pdf = user_data.get("CNPJ", "N/D")
        logo_path = find_client_logo_path(cnpj_pdf)
        if logo_path:
            try:
                current_y = pdf.get_y(); max_h = 20
                pdf.image(logo_path, x=10, y=current_y, h=max_h)
                pdf.set_y(current_y + max_h + 5)
            except Exception: pass

        pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome}"), 0, 1, 'C'); pdf.ln(5)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 7, pdf_safe_text_output(f"Data: {diag_data.get('Data','N/D')} | Empresa: {empresa_nome} (CNPJ: {cnpj_pdf})"))
        if user_data.get("NomeContato"): pdf.multi_cell(0, 7, pdf_safe_text_output(f"Contato: {user_data.get('NomeContato')}"))
        if user_data.get("Telefone"): pdf.multi_cell(0, 7, pdf_safe_text_output(f"Telefone: {user_data.get('Telefone')}"))
        pdf.ln(3)
        pdf.multi_cell(0, 7, pdf_safe_text_output(f"Média Geral: {diag_data.get('Média Geral','N/A')} | GUT Média: {diag_data.get('GUT Média','N/A')}")); pdf.ln(3)

        if medias_cat:
            pdf.set_font("Arial", 'B', 11); pdf.multi_cell(0, 7, pdf_safe_text_output("Médias por Categoria:")); pdf.set_font("Arial", size=10)
            for cat, media in sorted(medias_cat.items()): pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat}: {media:.2f}")); pdf.ln(1)
            pdf.ln(5)

        for titulo, campo in [("Resumo (Cliente):", "Diagnóstico"), ("Análise (Cliente):", "Análise do Cliente"), ("Comentários (Consultor):", "Comentarios_Admin")]:
            valor = diag_data.get(campo, "")
            if valor and not pd.isna(valor) and str(valor).strip():
                pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output(titulo))
                pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(str(valor))); pdf.ln(3)

        pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 10, pdf_safe_text_output("Respostas Detalhadas e Análises:"))
        categorias = sorted(perguntas_df["Categoria"].unique()) if not perguntas_df.empty and "Categoria" in perguntas_df.columns else []
        for categoria in categorias:
            pdf.set_font("Arial", 'B', 10); pdf.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria}")); pdf.set_font("Arial", size=9)
            perg_cat = perguntas_df[perguntas_df["Categoria"] == categoria]
            for _, p_row in perg_cat.iterrows():
                p_texto = p_row["Pergunta"]
                resp = respostas_coletadas.get(p_texto, diag_data.get(p_texto, "N/R"))
                analise_texto = None
                if "[Matriz GUT]" in p_texto:
                    g,u,t,score=0,0,0,0
                    if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                    elif isinstance(resp, str):
                        try: data_gut=json.loads(resp.replace("'",'"'));g,u,t=int(data_gut.get("G",0)),int(data_gut.get("U",0)),int(data_gut.get("T",0))
                        except json.JSONDecodeError: pass
                    score = g*u*t
                    pdf.multi_cell(0,6,pdf_safe_text_output(f"  - {p_texto.replace(' [Matriz GUT]','')}: G={g}, U={u}, T={t} (Score: {score})"))
                    analise_texto = obter_analise_para_resposta(p_texto, score, analises_df)
                else:
                    pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {p_texto}: {resp}"))
                    analise_texto = obter_analise_para_resposta(p_texto, resp, analises_df)
                if analise_texto:
                    pdf.set_font("Arial", 'I', 8); pdf.set_text_color(100,100,100)
                    pdf.multi_cell(0, 5, pdf_safe_text_output(f"    Análise: {analise_texto}"))
                    pdf.set_text_color(0,0,0); pdf.set_font("Arial", size=9)
            pdf.ln(2)
        pdf.ln(3)
        pdf.add_page(); pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf.ln(5); pdf.set_font("Arial", size=10)
        gut_cards = []
        if not perguntas_df.empty:
            for _, p_row in perguntas_df.iterrows():
                p_texto = p_row["Pergunta"]
                if "[Matriz GUT]" in p_texto:
                    resp = respostas_coletadas.get(p_texto, diag_data.get(p_texto))
                    g,u,t,score=0,0,0,0
                    if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                    elif isinstance(resp, str):
                        try:data_gut=json.loads(resp.replace("'",'"'));g,u,t=int(data_gut.get("G",0)),int(data_gut.get("U",0)),int(data_gut.get("T",0))
                        except json.JSONDecodeError: pass
                    score = g*u*t
                    prazo = "N/A"
                    if score >= 75: prazo = "15 dias"
                    elif score >= 40: prazo = "30 dias"
                    elif score >= 20: prazo = "45 dias"
                    elif score > 0: prazo = "60 dias"
                    else: continue
                    if prazo != "N/A": gut_cards.append({"Tarefa": p_texto.replace(" [Matriz GUT]", ""),"Prazo": prazo, "Score": score})
        if gut_cards:
            sorted_cards = sorted(gut_cards, key=lambda x: (int(x["Prazo"].split(" ")[0]), -x["Score"]))
            for card in sorted_cards: pdf.multi_cell(0,6,pdf_safe_text_output(f"Prazo: {card['Prazo']} - Tarefa: {card['Tarefa']} (Score GUT: {card['Score']})"))
        else: pdf.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf_path = tmpfile.name; pdf.output(pdf_path)
        return pdf_path
    except Exception as e: st.error(f"Erro crítico ao gerar PDF: {e}"); return None

def gerar_pdf_historico(df_historico_filtrado, titulo="Histórico de Ações"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, pdf_safe_text_output(titulo), 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    col_widths = {"Data": 35, "CNPJ": 35, "Ação": 40, "Descrição": 75}
    headers_to_print_hist = [col for col in ["Data", "CNPJ", "Ação", "Descrição"] if col in df_historico_filtrado.columns]
    for header in headers_to_print_hist:
        pdf.cell(col_widths.get(header, 30), 10, pdf_safe_text_output(header), 1, 0, "C")
    pdf.ln()
    pdf.set_font("Arial", "", 8)
    line_height = 5
    for _, row in df_historico_filtrado.iterrows():
        current_y_hist = pdf.get_y()
        max_h_row_hist = line_height
        desc_text_hist = str(row.get("Descrição", ""))
        temp_fpdf_h = FPDF(); temp_fpdf_h.add_page(); temp_fpdf_h.set_font("Arial", "", 8)
        desc_lines = temp_fpdf_h.multi_cell(w=col_widths.get("Descrição", 75) - 2, h=line_height, txt=pdf_safe_text_output(desc_text_hist), border=0, align="L", split_only=True)
        max_h_row_hist = max(max_h_row_hist, len(desc_lines) * line_height) + 2
        current_x_for_cell = pdf.l_margin
        for header_idx, header in enumerate(headers_to_print_hist):
            cell_text = str(row.get(header, ""))
            pdf.set_xy(current_x_for_cell, current_y_hist)
            # CORREÇÃO APLICADA: Removido argumento 'ln' de multi_cell
            pdf.multi_cell(col_widths.get(header, 30), max_h_row_hist, pdf_safe_text_output(cell_text), border=1, align="L") 
            current_x_for_cell += col_widths.get(header, 30)
        pdf.set_y(current_y_hist + max_h_row_hist)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf_path = tmpfile.name; pdf.output(pdf_path)
    return pdf_path

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): st.session_state.trigger_rerun_global = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v15")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador 🔑</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v15"):
        u = st.text_input("Usuário", key="admin_u_v15"); p = st.text_input("Senha", type="password", key="admin_p_v15")
        if st.form_submit_button("Entrar"):
            try:
                df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                admin_encontrado = df_creds[df_creds["Usuario"] == u]
                if not admin_encontrado.empty and admin_encontrado.iloc[0]["Senha"] == p:
                    st.session_state.admin_logado = True; st.success("Login de administrador bem-sucedido! ✅"); st.rerun()
                else: st.error("Usuário ou senha inválidos.")
            except FileNotFoundError: st.error(f"Arquivo de credenciais de admin não encontrado: {admin_credenciais_csv}")
            except Exception as e: st.error(f"Erro no login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente 🏢</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_v15"):
        c = st.text_input("CNPJ", key="cli_c_v15", value=st.session_state.get("last_cnpj_input",""))
        s = st.text_input("Senha", type="password", key="cli_s_v15")
        if st.form_submit_button("Entrar"):
            st.session_state.last_cnpj_input = c
            try:
                users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                for col, default_val_user, col_type in [
                    ("ConfirmouInstrucoesParaSlotAtual", "False", str),
                    ("DiagnosticosDisponiveis", 1, int),
                    ("TotalDiagnosticosRealizados", 0, int),
                    ("LiberacoesExtrasConcedidas", 0, int)
                ]:
                    if col not in users_df.columns: users_df[col] = default_val_user
                    if col_type == int:
                        users_df[col] = pd.to_numeric(users_df[col], errors='coerce').fillna(default_val_user).astype(int)
                    else:
                        users_df[col] = users_df[col].astype(str)

                blocked_df = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                if c in blocked_df["CNPJ"].values: st.error("CNPJ bloqueado."); st.stop()

                match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == s)]
                if match.empty: st.error("CNPJ ou senha inválidos."); st.stop()

                st.session_state.cliente_logado = True; st.session_state.cnpj = c
                st.session_state.user = match.iloc[0].to_dict()
                st.session_state.user["ConfirmouInstrucoesParaSlotAtual"] = str(st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", "False")).lower() == "true"
                st.session_state.user["DiagnosticosDisponiveis"] = int(st.session_state.user.get("DiagnosticosDisponiveis", 1))
                st.session_state.user["TotalDiagnosticosRealizados"] = int(st.session_state.user.get("TotalDiagnosticosRealizados", 0))
                st.session_state.user["LiberacoesExtrasConcedidas"] = int(st.session_state.user.get("LiberacoesExtrasConcedidas", 0))

                st.session_state.inicio_sessao_cliente = time.time()
                registrar_acao(c, "Login", "Usuário logou.")

                pode_fazer_novo_login = st.session_state.user["DiagnosticosDisponiveis"] > st.session_state.user["TotalDiagnosticosRealizados"]
                if pode_fazer_novo_login and not st.session_state.user["ConfirmouInstrucoesParaSlotAtual"]:
                    st.session_state.cliente_page = "Instruções"
                elif pode_fazer_novo_login and st.session_state.user["ConfirmouInstrucoesParaSlotAtual"]:
                    st.session_state.cliente_page = "Novo Diagnóstico"
                else:
                    st.session_state.cliente_page = "Painel Principal"

                st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                st.session_state.respostas_atuais_diagnostico = {}; st.session_state.progresso_diagnostico_percentual = 0; st.session_state.progresso_diagnostico_contagem = (0,0); st.session_state.feedbacks_respostas = {}; st.session_state.diagnostico_enviado_sucesso = False; st.session_state.confirmou_instrucoes_checkbox_cliente = False
                st.success("Login cliente OK! ✅"); st.rerun()
            except FileNotFoundError as fnf_e:
                st.error(f"Erro de configuração: Arquivo {fnf_e.filename} não encontrado. Contate o administrador.")
            except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    if "user" not in st.session_state or st.session_state.user is None or \
       "cnpj" not in st.session_state or st.session_state.cnpj is None:
        st.error("Erro de sessão. Por favor, faça o login novamente.")
        keys_to_clear_on_error = ['cliente_logado', 'user', 'cnpj', 'cliente_page', 'respostas_atuais_diagnostico', 'id_formulario_atual', 'progresso_diagnostico_percentual', 'progresso_diagnostico_contagem']
        for key_to_clear in keys_to_clear_on_error:
            if key_to_clear in st.session_state: del st.session_state[key_to_clear]
        for key_d, value_d in default_session_state.items():
            st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False
        st.rerun()

    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}! 👋")
    with st.sidebar.expander("Meu Perfil", expanded=False):
        logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
        if logo_cliente_path: st.image(logo_cliente_path, width=100)
        st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
        st.write(f"**CNPJ:** {st.session_state.cnpj}")
        st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
        st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")
        diagnosticos_restantes_perfil = st.session_state.user.get('DiagnosticosDisponiveis', 0) - st.session_state.user.get('TotalDiagnosticosRealizados', 0)
        st.write(f"**Diagnósticos Restantes:** {max(0, diagnosticos_restantes_perfil)}")
        st.write(f"**Total Realizados:** {st.session_state.user.get('TotalDiagnosticosRealizados', 0)}")

    unread_notif_count_val = get_unread_notifications_count(st.session_state.cnpj)
    notif_menu_label_val = "🔔 Notificações"
    if unread_notif_count_val > 0: notif_menu_label_val = f"🔔 Notificações ({unread_notif_count_val})"
    menu_options_cli_val = ["📖 Instruções", "📝 Novo Diagnóstico", "📊 Painel Principal", notif_menu_label_val]
    
    pode_fazer_novo_sidebar_val = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
    confirmou_instrucoes_sidebar_val = st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", False)
    instrucoes_pendentes_obrigatorias_val = pode_fazer_novo_sidebar_val and not confirmou_instrucoes_sidebar_val

    st.sidebar.markdown("---")
    st.sidebar.caption(f"DEBUG INFO (Barra Lateral):")
    st.sidebar.write(f"`ss.cliente_page` (atual): `{st.session_state.cliente_page}`")
    st.sidebar.write(f"`pode_fazer_novo`: `{pode_fazer_novo_sidebar_val}`")
    st.sidebar.write(f"`confirmou_instr`: `{confirmou_instrucoes_sidebar_val}`")
    st.sidebar.write(f"`instr_pend_obrig`: `{instrucoes_pendentes_obrigatorias_val}`")
    
    effective_cliente_page_for_radio_default = st.session_state.cliente_page
    
    if instrucoes_pendentes_obrigatorias_val and st.session_state.cliente_page != "Instruções":
        st.sidebar.error("❗REDIRECIONAMENTO AUTOMÁTICO: Para 'Instruções' (pendência obrigatória).")
        effective_cliente_page_for_radio_default = "Instruções"
        if st.session_state.cliente_page != "Instruções":
            st.session_state.cliente_page = "Instruções" 

    st.sidebar.write(f"`effective_page_for_radio`: `{effective_cliente_page_for_radio_default}`")
    st.sidebar.markdown("---")
    st.sidebar.critical("PERGUNTA IMPORTANTE PARA VOCÊ: Ao tentar acessar 'Painel Principal' ou 'Novo Diagnóstico', você vê o 'ALERTA DE DEPURAÇÃO MÁXIMA' em vermelho na área de conteúdo principal da página?")


    current_page_for_radio_display = effective_cliente_page_for_radio_default
    if current_page_for_radio_display == "Notificações": current_page_for_radio_display = notif_menu_label_val
    
    try: current_idx_cli_val = menu_options_cli_val.index(current_page_for_radio_display)
    except ValueError:
        st.sidebar.warning(f"DEBUG: `current_page_for_radio_display` ('{current_page_for_radio_display}') não encontrada no menu. Default para Instruções.")
        current_idx_cli_val = 0
        if st.session_state.cliente_page != "Instruções":
            st.session_state.cliente_page = "Instruções"
    
    selected_page_cli_raw_val = st.sidebar.radio("Menu Cliente", menu_options_cli_val, index=current_idx_cli_val, key="cli_menu_v15_debug_radio")
    selected_page_cli_actual = "Notificações" if "Notificações" in selected_page_cli_raw_val else selected_page_cli_raw_val
    
    if selected_page_cli_actual != st.session_state.cliente_page: 
        if instrucoes_pendentes_obrigatorias_val and selected_page_cli_actual != "Instruções":
            st.sidebar.error("⚠️ ACESSO NEGADO! Você deve primeiro ler e confirmar as instruções na página '📖 Instruções' para acessar outras seções ou iniciar um novo diagnóstico.")
        else:
            st.session_state.cliente_page = selected_page_cli_actual
            st.rerun()

    if st.sidebar.button("⬅️ Sair do Portal Cliente", key="logout_cliente_v15"):
        client_keys_to_clear = [k for k in default_session_state.keys() if k not in ['admin_logado']]
        for key_to_clear in client_keys_to_clear:
            if key_to_clear in st.session_state: del st.session_state[key_to_clear]
        for key_d, value_d in default_session_state.items():
             if key_d not in ['admin_logado']: st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False
        st.rerun()

    st.markdown("---")
    st.subheader(f"DEBUG GLOBAL: Tentando renderizar conteúdo para: st.session_state.cliente_page = `{st.session_state.cliente_page}`")
    st.markdown("---")

    # --- Conteúdo da Página do Cliente ---
    if st.session_state.cliente_page == "Instruções":
        st.subheader("📖 Instruções do Sistema de Diagnóstico")
        default_instructions_text_content = """**Bem-vindo ao Portal de Diagnóstico Empresarial!** (Substitua pelo texto completo das suas instruções)""" 
        instructions_to_display = default_instructions_text_content
        try:
            if os.path.exists(instrucoes_txt_file) and os.path.getsize(instrucoes_txt_file) > 0:
                with open(instrucoes_txt_file, "r", encoding="utf-8") as f:
                    custom_instructions = f.read()
                    if custom_instructions.strip(): instructions_to_display = custom_instructions
        except Exception as e: st.warning(f"Não foi possível carregar as instruções personalizadas: {e}. Exibindo instruções padrão.")
        st.markdown(instructions_to_display)

        if st.session_state.user:
            pode_fazer_novo_inst_page_val = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            confirmou_inst_atual = st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", False)
            
            if pode_fazer_novo_inst_page_val and not confirmou_inst_atual:
                 st.error("🛑 **AÇÃO NECESSÁRIA:** Para prosseguir para um NOVO DIAGNÓSTICO, você DEVE marcar a caixa de confirmação abaixo e clicar em 'Prosseguir para o Diagnóstico'.")

            if pode_fazer_novo_inst_page_val:
                st.session_state.confirmou_instrucoes_checkbox_cliente = st.checkbox("Declaro que li e compreendi todas as instruções fornecidas para a realização deste diagnóstico.", value=st.session_state.get("confirmou_instrucoes_checkbox_cliente", False), key="confirma_leitura_inst_v15_final_cb")
                if st.button("Prosseguir para o Diagnóstico", key="btn_instrucoes_v15_final_prosseguir", disabled=not st.session_state.confirmou_instrucoes_checkbox_cliente):
                    if st.session_state.confirmou_instrucoes_checkbox_cliente:
                        update_user_data(st.session_state.cnpj, "ConfirmouInstrucoesParaSlotAtual", "True")
                        st.session_state.cliente_page = "Novo Diagnóstico"; st.session_state.confirmou_instrucoes_checkbox_cliente = False; st.rerun()
            else:
                st.info("Você não possui diagnósticos disponíveis no momento para iniciar.")
            
            if st.button("Ir para o Painel Principal", key="ir_painel_inst_v15_final_geral"):
                _pode_fazer_novo_check = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
                _confirmou_instr_check = st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", False)
                _instr_pendentes_check = _pode_fazer_novo_check and not _confirmou_instr_check
                if _instr_pendentes_check:
                     st.error("⚠️ Você precisa confirmar as instruções acima antes de ir para o Painel Principal, pois um novo diagnóstico está disponível e pendente de confirmação.")
                else:
                    st.session_state.cliente_page = "Painel Principal"; st.rerun()
        else: st.error("Erro de sessão do usuário. Por favor, faça login novamente.")


    elif st.session_state.cliente_page == "Painel Principal":
        st.error(f"ALERTA DE DEPURAÇÃO MÁXIMA: BLOCO 'Painel Principal' ALCANÇADO!")
        st.subheader("📊 Painel Principal do Cliente (Versão de Teste SUPER SIMPLIFICADA)")
        st.write(f"DEBUG: Ponto PP_A - Início do Painel Principal (SIMPLIFICADO)")
        st.write("Se você está vendo esta mensagem, o código entrou corretamente na seção do Painel Principal.")
        st.write("O conteúdo original foi comentado para ajudar a isolar o problema.")
        st.write("Se esta mensagem aparecer, o problema está no código que foi comentado na versão anterior (procure o bloco comentado).")
        st.balloons()
        st.write("DEBUG: Ponto PP_K - FIM do Painel Principal (SIMPLIFICADO)")


    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.error(f"ALERTA DE DEPURAÇÃO MÁXIMA: BLOCO 'Novo Diagnóstico' ALCANÇADO!")
        st.subheader("📝 Formulário de Novo Diagnóstico (Versão de Teste SUPER SIMPLIFICADA)")
        st.write(f"DEBUG: Ponto ND_A - Início de Novo Diagnóstico (SIMPLIFICADO)")
        
        # Verificações de permissão (essas precisam rodar para testar o fluxo)
        if not st.session_state.user: st.error("Erro: Dados do usuário não encontrados. Faça login novamente."); st.stop()
        pode_fazer_novo_form = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
        confirmou_inst_form = st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", False)

        if not pode_fazer_novo_form:
            st.warning("❌ Você não tem diagnósticos disponíveis no momento.")
            if st.button("Voltar ao Painel Principal", key="voltar_painel_novo_diag_bloq_v14_final_nd_simp"): st.session_state.cliente_page = "Painel Principal"; st.rerun()
            st.stop()
        elif not confirmou_inst_form:
            st.warning("⚠️ Por favor, confirme a leitura das instruções na página '📖 Instruções' antes de iniciar um novo diagnóstico.")
            if st.button("Ir para Instruções", key="ir_instrucoes_novo_diag_v14_final_nd_simp"): st.session_state.cliente_page = "Instruções"; st.rerun()
            st.stop()
        
        st.write("DEBUG: Ponto ND_B - Após checagens de permissão (SIMPLIFICADO)")
        st.write("Se você vê estas mensagens, as checagens de permissão passaram.")
        st.write("O formulário de diagnóstico original foi comentado. Se esta página está 'em branco' (além destas mensagens), o problema residia no código original do formulário.")
        st.balloons()
        st.write("DEBUG: Ponto ND_J - FIM de Novo Diagnóstico (SIMPLIFICADO)")

    elif st.session_state.cliente_page == "Notificações":
        st.subheader("🔔 Minhas Notificações")
        # (Código de Notificações como antes)
        try:
            df_notif_cliente_view = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
            df_notif_cliente_view = df_notif_cliente_view[df_notif_cliente_view['CNPJ_Cliente'] == st.session_state.cnpj]
            if not df_notif_cliente_view.empty: df_notif_cliente_view['DataHora'] = pd.to_datetime(df_notif_cliente_view['DataHora']); df_notif_cliente_view = df_notif_cliente_view.sort_values(by="DataHora", ascending=False)
        except (FileNotFoundError, pd.errors.EmptyDataError): df_notif_cliente_view = pd.DataFrame()
        if df_notif_cliente_view.empty: st.info("Você não tem nenhuma notificação no momento.")
        else:
            ids_nao_lidas_para_marcar_view = []
            for _, row_notif_view in df_notif_cliente_view.iterrows():
                lida_status_view = "Lida" if row_notif_view['Lida'] else "Nova!"; cor_status_view = "green" if row_notif_view['Lida'] else "red"
                st.markdown(f"""<div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-bottom: 10px; {'font-weight: bold;' if not row_notif_view['Lida'] else ''}"> <small>{pd.to_datetime(row_notif_view['DataHora']).strftime('%d/%m/%Y %H:%M')} - <span style="color:{cor_status_view};">{lida_status_view}</span></small><br> {row_notif_view['Mensagem']} </div> """, unsafe_allow_html=True)
                if not row_notif_view['Lida']: ids_nao_lidas_para_marcar_view.append(row_notif_view['ID_Notificacao'])
            if ids_nao_lidas_para_marcar_view:
                if 'notif_page_loaded_once_v14_final_c' not in st.session_state:
                    if marcar_notificacoes_como_lidas(st.session_state.cnpj, ids_notificacoes=ids_nao_lidas_para_marcar_view):
                        st.session_state.notif_page_loaded_once_v14_final_c = True;
                        st.rerun()
            elif 'notif_page_loaded_once_v14_final_c' in st.session_state and not ids_nao_lidas_para_marcar_view:
                 del st.session_state.notif_page_loaded_once_v14_final_c

# --- ÁREA DO ADMINISTRADOR LOGADO ---
# O código do administrador foi omitido aqui para focar no problema do cliente.
# Certifique-se de que seu código completo do administrador está presente no seu arquivo.
if aba == "Administrador" and st.session_state.admin_logado:
    # COLE SEU CÓDIGO DE ADMIN COMPLETO AQUI (o código fornecido anteriormente é extenso)
    st.header("Área Administrativa (Conteúdo Omitido para Teste do Cliente)")
    st.info("O código completo da área do administrador deve ser inserido aqui.")
    # Exemplo de como estava:
    # try:
    #     try: st.sidebar.image("https://via.placeholder.com/150x75.png?text=Sua+Logo+Admin", width=150)
    #     # ... e assim por diante ...
    # except Exception as e_outer_admin_critical:
    #     st.error(f"Um erro crítico e inesperado ocorreu na área administrativa: {e_outer_admin_critical}")
    #     st.exception(e_outer_admin_critical)
    pass


if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")