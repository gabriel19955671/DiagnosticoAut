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
import uuid # Para IDs de análise

# !!! st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT !!!
st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", page_icon="📊")

# --- Global Paths for Assets ---
ASSETS_DIR = "assets"
CUSTOM_LOGIN_LOGO_FILENAME = "portal_login_logo.png"
DEFAULT_LOGIN_LOGO_FILENAME = "default_login_logo.png"

CUSTOM_LOGIN_LOGO_PATH = os.path.join(ASSETS_DIR, CUSTOM_LOGIN_LOGO_FILENAME)
DEFAULT_LOGIN_LOGO_PATH = os.path.join(ASSETS_DIR, DEFAULT_LOGIN_LOGO_FILENAME)

if not os.path.exists(ASSETS_DIR):
    try:
        os.makedirs(ASSETS_DIR)
    except OSError as e:
        print(f"Aviso: Não foi possível criar o diretório de assets '{ASSETS_DIR}': {e}.")

# --- CSS ---
st.markdown(f"""
<style>
body {{
    font-family: 'Segoe UI', sans-serif;
    background-color: #f0f2f5; 
}}
/* ... (seu CSS completo aqui, mantido como estava) ... */
.login-page-background {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: #eef2f7; 
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: -1; 
}}
.login-container {{
    max-width: 420px; 
    margin: 60px auto; 
    padding: 35px; 
    background-color: #ffffff; 
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1); 
    border-top: 6px solid #2563eb; 
    text-align: center;
}}
.login-container .stImage img {{
    max-width: 200px; 
    max-height: 100px; 
    object-fit: contain; 
    margin-bottom: 25px;
    display: block;
    margin-left: auto;
    margin-right: auto;
}}
.login-container h2.login-title {{ 
    font-size: 24px; 
    color: #333; 
    margin-bottom: 30px;
    font-weight: 600;
}}
.login-container .stButton>button {{ 
    width: 100%;
    font-size: 16px;
    padding-top: 0.7rem;
    padding-bottom: 0.7rem;
    margin-top: 1rem; 
}}
div[data-testid="stRadio"] > label[data-baseweb="radio"] > div:first-child {{
    justify-content: center; 
}}
div[data-testid="stRadio"] > div[role="radiogroup"] {{ 
    display: flex;
    flex-direction: row !important; 
    justify-content: center;
    gap: 15px; 
    margin-bottom: 25px; 
}}
div[data-testid="stRadio"] label[data-baseweb="radio"] {{ 
    padding: 8px 16px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background-color: #f9fafb;
    transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
    cursor: pointer;
}}
div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {{
    background-color: #f0f2f5;
    border-color: #adb5bd;
}}
div[data-testid="stRadio"] input[type="radio"]:checked + div {{
    background-color: #2563eb !important; 
    color: white !important;
    border-color: #2563eb !important;
}}
div[data-testid="stRadio"] input[type="radio"]:checked + div > div > span {{
    color: white !important;
}}
.stButton>button {{
    border-radius: 6px;
    background-color: #2563eb;
    color: white;
    font-weight: 500;
    padding: 0.6rem 1.3rem;
    margin-top: 0.5rem;
    border: none;
    transition: background-color 0.3s ease;
}}
.stButton>button:hover {{
    background-color: #1d4ed8;
}}
.stButton>button.secondary {{
    background-color: #e5e7eb;
    color: #374151;
}}
.stButton>button.secondary:hover {{
    background-color: #d1d5db;
}}
.stDownloadButton>button {{
    background-color: #10b981;
    color: white;
    font-weight: 600;
    border-radius: 6px;
    margin-top: 10px;
    padding: 0.6rem 1.3rem;
    border: none;
    transition: background-color 0.3s ease;
}}
.stDownloadButton>button:hover {{
    background-color: #059669;
}}
.stTextInput>div>input, .stTextArea>div>textarea, .stDateInput>div>input, .stSelectbox>div>div {{
    border-radius: 6px;
    padding: 0.6rem;
    border: 1px solid #d1d5db;
    background-color: #f9fafb;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}}
.stTextInput>div>input:focus, .stTextArea>div>textarea:focus, .stDateInput>div>input:focus, .stSelectbox>div>div:focus-within {{
    border-color: #2563eb;
    box-shadow: 0 0 0 0.1rem rgba(37, 99, 235, 0.25);
}}
.stTabs [data-baseweb="tab"] {{
    font-size: 16px;
    font-weight: 600;
    padding: 12px 22px;
    border-radius: 6px 6px 0 0;
}}
.stTabs [data-baseweb="tab"][aria-selected="true"] {{
    background-color: #2563eb;
    color: white;
}}
.custom-card {{
    border: 1px solid #e0e0e0;
    border-left: 5px solid #2563eb;
    padding: 20px;
    margin-bottom: 15px;
    border-radius: 8px;
    background-color: #ffffff;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07);
}}
.custom-card h4 {{
    margin-top: 0;
    color: #2563eb;
    font-size: 1.1em;
}}
.feedback-saved {{
    font-size: 0.85em;
    color: #10b981;
    font-style: italic;
    margin-top: -8px;
    margin-bottom: 8px;
}}
.analise-pergunta-cliente {{
    font-size: 0.9em;
    color: #333;
    background-color: #eef2ff;
    border-left: 3px solid #6366f1;
    padding: 10px;
    margin-top: 8px;
    margin-bottom:12px;
    border-radius: 4px;
}}
[data-testid="stMetric"] {{
    background-color: #ffffff;
    border-radius: 8px;
    padding: 15px 20px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07);
    border: 1px solid #e0e0e0;
}}
[data-testid="stMetricLabel"] {{
    font-weight: 500;
    color: #4b5563;
}}
[data-testid="stMetricValue"] {{
    font-size: 1.8em;
}}
[data-testid="stMetricDelta"] {{
    font-size: 0.9em;
}}
.stExpander {{
    border: 1px solid #e0e0e0 !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07) !important;
    margin-bottom: 15px !important;
}}
.stExpander header {{
    font-weight: 600 !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 15px !important;
}}
.dashboard-item {{
    background-color: #ffffff;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07);
    margin-bottom: 20px;
    border: 1px solid #e0e0e0;
    height: 100%;
}}
.dashboard-item h5 {{
    margin-top: 0;
    margin-bottom: 15px;
    color: #2563eb;
    font-size: 1.1em;
    border-bottom: 1px solid #eee;
    padding-bottom: 8px;
}}
/* FAQ Styles */
.faq-question-selected {{
    background-color: #eef2ff;
    padding: 10px;
    border-left: 3px solid #4f46e5;
    margin-bottom: 5px;
    cursor: pointer;
}}
.faq-answer {{
    background-color: #f9fafb;
    padding: 15px;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    margin-top: 5px;
    margin-bottom: 15px;
}}
</style>
""", unsafe_allow_html=True)

# --- Funções de Gráficos (mantidas como estavam) ---
def create_radar_chart(data_dict, title="Radar Chart"):
    if not data_dict: return None
    categories = list(data_dict.keys())
    values = list(data_dict.values())
    if not categories or not values or len(categories) < 3 : return None
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]
    df_radar = pd.DataFrame(dict(r=values_closed, theta=categories_closed))
    fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True, template="seaborn")
    fig.update_traces(fill='toself', line=dict(color='#2563eb'))
    fig.update_layout(title={'text': title, 'x':0.5, 'xanchor': 'center'},
                        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                        font=dict(family="Segoe UI, sans-serif"),
                        margin=dict(l=50, r=50, t=70, b=50))
    return fig

def create_gut_barchart(gut_data_list, title="Top Prioridades (GUT)"):
    if not gut_data_list: return None
    df_gut = pd.DataFrame(gut_data_list)
    df_gut = df_gut.sort_values(by="Score", ascending=False).head(10)
    if df_gut.empty: return None
    fig = px.bar(df_gut, x="Score", y="Tarefa", title=title, orientation='h',
               color="Score", color_continuous_scale=px.colors.sequential.Blues_r,
               labels={'Tarefa':'Tarefa/Pergunta', 'Score':'Score GUT'})
    fig.update_layout(yaxis={'categoryorder':'total ascending'},
                        xaxis_title="Score GUT", yaxis_title="",
                        font=dict(family="Segoe UI, sans-serif"),
                        height=400 + len(df_gut)*20,
                        margin=dict(l=250, r=20, t=70, b=20))
    return fig

def create_diagnostics_timeline_chart(df_diagnostics, title="Diagnósticos Realizados ao Longo do Tempo"):
    if df_diagnostics.empty or 'Data' not in df_diagnostics.columns: return None
    df_diag_copy = df_diagnostics.copy()
    df_diag_copy['Data'] = pd.to_datetime(df_diag_copy['Data'], errors='coerce')
    df_diag_copy.dropna(subset=['Data'], inplace=True)
    if df_diag_copy.empty : return None
    diag_counts_monthly = df_diag_copy.groupby(pd.Grouper(key='Data', freq='M')).size().reset_index(name='Contagem')
    diag_counts_monthly['Mês'] = diag_counts_monthly['Data'].dt.strftime('%Y-%m')
    if diag_counts_monthly.empty: return None
    fig = px.line(diag_counts_monthly, x='Mês', y='Contagem', title=title, markers=True,
                  labels={'Mês':'Mês', 'Contagem':'Nº de Diagnósticos'}, line_shape="spline")
    fig.update_traces(line=dict(color='#2563eb'))
    fig.update_layout(font=dict(family="Segoe UI, sans-serif"))
    return fig

def create_avg_category_scores_chart(df_diagnostics, title="Média de Scores por Categoria (Todos Clientes)"):
    if df_diagnostics.empty: return None
    media_cols = [col for col in df_diagnostics.columns if col.startswith("Media_Cat_")]
    if not media_cols: return None
    avg_scores_data = []
    for col in media_cols:
        numeric_scores = pd.to_numeric(df_diagnostics[col], errors='coerce')
        if not numeric_scores.isnull().all():
            avg_scores_data.append({
                'Categoria': col.replace("Media_Cat_", "").replace("_", " "),
                'Média_Score': numeric_scores.mean()
            })
    if not avg_scores_data: return None
    avg_scores = pd.DataFrame(avg_scores_data)
    avg_scores = avg_scores.sort_values(by="Média_Score", ascending=False)
    fig = px.bar(avg_scores, x='Categoria', y='Média_Score', title=title,
               color='Média_Score', color_continuous_scale=px.colors.sequential.Blues_r,
               labels={'Categoria':'Categoria', 'Média_Score':'Média do Score'})
    fig.update_layout(xaxis_tickangle=-45, font=dict(family="Segoe UI, sans-serif"),
                        yaxis=dict(range=[0,5.5]))
    return fig

def create_client_engagement_pie(df_usuarios, title="Engajamento de Clientes (Nº de Diagnósticos)"):
    if df_usuarios.empty or 'TotalDiagnosticosRealizados' not in df_usuarios.columns: return None
    def categorize_diagnostics(count):
        if count == 0: return "0 Diagnósticos"
        if count == 1: return "1 Diagnóstico"
        if count == 2: return "2 Diagnósticos"
        return "3+ Diagnósticos"
    df_usuarios_copy = df_usuarios.copy()
    df_usuarios_copy['TotalDiagnosticosRealizados'] = pd.to_numeric(df_usuarios_copy['TotalDiagnosticosRealizados'], errors='coerce').fillna(0).astype(int)
    df_usuarios_copy['Engajamento'] = df_usuarios_copy['TotalDiagnosticosRealizados'].apply(categorize_diagnostics)
    engagement_counts = df_usuarios_copy['Engajamento'].value_counts().reset_index()
    engagement_counts.columns = ['Categoria_Engajamento', 'Numero_Clientes']
    if engagement_counts.empty: return None
    fig = px.pie(engagement_counts, values='Numero_Clientes', names='Categoria_Engajamento', title=title,
                 color_discrete_sequence=px.colors.sequential.Blues_r)
    fig.update_traces(textposition='inside', textinfo='percent+label', insidetextorientation='radial')
    fig.update_layout(font=dict(family="Segoe UI, sans-serif"), legend_title_text='Nível de Engajamento')
    return fig

def create_avg_time_per_question_chart(df_diagnostics_all, title="Tempo Médio de Resposta por Pergunta de Diagnóstico"):
    if df_diagnostics_all.empty or 'TimingsPerguntasJSON' not in df_diagnostics_all.columns:
        return None

    all_timings = []
    for _, row in df_diagnostics_all.iterrows():
        if pd.notna(row['TimingsPerguntasJSON']):
            try:
                timings_dict = json.loads(row['TimingsPerguntasJSON'])
                for pergunta, tempo in timings_dict.items():
                    all_timings.append({'Pergunta': pergunta, 'TempoSegundos': float(tempo)})
            except (json.JSONDecodeError, TypeError, ValueError):
                continue

    if not all_timings:
        return None

    df_times = pd.DataFrame(all_timings)
    if df_times.empty:
        return None

    avg_times = df_times.groupby('Pergunta')['TempoSegundos'].mean().reset_index()
    avg_times = avg_times.sort_values(by='TempoSegundos', ascending=False).head(15)

    if avg_times.empty:
        return None

    fig = px.bar(avg_times, x='TempoSegundos', y='Pergunta', title=title, orientation='h',
                 color='TempoSegundos', color_continuous_scale=px.colors.sequential.Oranges_r,
                 labels={'Pergunta': 'Pergunta do Diagnóstico', 'TempoSegundos': 'Tempo Médio (segundos)'})
    fig.update_layout(yaxis={'categoryorder':'total ascending'},
                        font=dict(family="Segoe UI, sans-serif"),
                        height=300 + len(avg_times)*25,
                        margin=dict(l=300, r=20, t=70, b=20))
    return fig

# --- Configuração de Arquivos e Variáveis Globais ---
admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv"
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv"
historico_csv = "historico_clientes.csv"
analises_perguntas_csv = "analises_perguntas.csv"
notificacoes_csv = "notificacoes.csv"
instrucoes_custom_path = "instrucoes_portal.md"
instrucoes_default_path = "instrucoes_portal_default.md"
LOGOS_DIR = "client_logos"

# Novos arquivos CSV
faq_sac_csv = "faq_sac.csv"
pesquisa_satisfacao_perguntas_csv = "pesquisa_satisfacao_perguntas.csv"
pesquisa_satisfacao_respostas_csv = "pesquisa_satisfacao_respostas.csv"

# Lista de todas as chaves de permissão possíveis
ALL_ADMIN_PERMISSION_KEYS = [
    "Perm_VisaoGeralDiagnosticos", "Perm_RelatorioEngajamento",
    "Perm_GerenciarNotificacoes", "Perm_GerenciarClientes",
    "Perm_PersonalizarAparencia", "Perm_GerenciarPerguntasDiagnostico",
    "Perm_GerenciarAnalises", "Perm_GerenciarFAQ",
    "Perm_GerenciarPerguntasPesquisa", "Perm_VerResultadosPesquisa",
    "Perm_GerenciarInstrucoes", "Perm_VerHistorico",
    "Perm_GerenciarAdministradores" # Super-admin permission
]
colunas_base_admin_credenciais = ["Usuario", "Senha"] + ALL_ADMIN_PERMISSION_KEYS


# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {},
    "force_sidebar_rerun_after_notif_read_v19": False,
    "target_diag_data_for_expansion": None,
    "current_question_start_time": None,
    "diagnostic_question_timings": {},
    "previous_question_text_tracker": None,
    "current_survey_responses": {},
    "selected_faq_category": "Todas",
    "search_faq_query": "",
    "selected_faq_id": None,
    "survey_submitted_for_current_diag": False,
    "survey_id_diagnostico_associado": None,
    "admin_user_details": None,
    "login_selection_aba": "Cliente"
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias ---
def robust_str_to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        val_lower = value.lower().strip()
        if val_lower in ['true', '1', 't', 'y', 'yes', 'sim', 'verdadeiro', 'on']: # Added 'on'
            return True
        elif val_lower in ['false', '0', 'f', 'n', 'no', 'nao', 'não', 'falso', 'off']: # Added 'off'
            return False
    return False

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

if not os.path.exists(LOGOS_DIR):
    try: os.makedirs(LOGOS_DIR)
    except OSError as e: st.error(f"Erro ao criar diretório de logos de cliente '{LOGOS_DIR}': {e}")


colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin", "TimingsPerguntasJSON", "ID_Diagnostico"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone",
                         "JaVisualizouInstrucoes", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]
colunas_base_perguntas = ["Pergunta", "Categoria"]
colunas_base_analises = ["ID_Analise", "TextoPerguntaOriginal", "TipoCondicao", "CondicaoValorMin", "CondicaoValorMax", "CondicaoValorExato", "TextoAnalise"]
colunas_base_notificacoes = ["ID_Notificacao", "CNPJ_Cliente", "Timestamp", "Mensagem", "Lida", "ID_Diagnostico_Relacionado"]

# Novas colunas base
colunas_base_faq = ["ID_FAQ", "CategoriaFAQ", "PerguntaFAQ", "RespostaFAQ"]
colunas_base_pesquisa_perguntas = ["ID_PerguntaPesquisa", "TextoPerguntaPesquisa", "TipoRespostaPesquisa", "OpcoesRespostaJSON", "Ordem", "Ativa"]
colunas_base_pesquisa_respostas = ["ID_SessaoRespostaPesquisa", "CNPJ_Cliente", "TimestampPreenchimento",
                                   "NomeClientePreenchimento", "TelefoneClientePreenchimento", "EmpresaClientePreenchimento",
                                   "ID_Diagnostico_Associado", "RespostasJSON"]

def inicializar_csv(filepath, columns, defaults=None):
    try:
        df_init = None
        dtype_spec_local = {}
        # Define dtype for specific columns to avoid issues, especially with CNPJ
        if filepath == admin_credenciais_csv: dtype_spec_local = {'Usuario': str, 'Senha': str}
        elif filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, historico_csv, pesquisa_satisfacao_respostas_csv]:
            if 'CNPJ' in columns: dtype_spec_local['CNPJ'] = str
            if 'CNPJ_Cliente' in columns: dtype_spec_local['CNPJ_Cliente'] = str
        if filepath == notificacoes_csv and 'ID_Diagnostico_Relacionado' in columns: dtype_spec_local['ID_Diagnostico_Relacionado'] = str
        if filepath == arquivo_csv and 'ID_Diagnostico' in columns: dtype_spec_local['ID_Diagnostico'] = str
        if filepath == pesquisa_satisfacao_respostas_csv and 'ID_Diagnostico_Associado' in columns: dtype_spec_local['ID_Diagnostico_Associado'] = str


        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init = pd.DataFrame(columns=columns)
            if filepath == admin_credenciais_csv:
                # For a brand new admin CSV, create the master admin directly
                master_admin_data = {"Usuario": "admin", "Senha": "potencialize"}
                for col_name in columns: # Ensure all base columns are considered
                    if col_name not in master_admin_data: # Not Usuario or Senha
                        if col_name in ALL_ADMIN_PERMISSION_KEYS:
                            master_admin_data[col_name] = True
                        elif defaults and col_name in defaults: # Other structural defaults
                             master_admin_data[col_name] = defaults[col_name]
                        else:
                             master_admin_data[col_name] = pd.NA
                df_init = pd.DataFrame([master_admin_data], columns=columns)
            elif defaults: # For other files being created fresh with defaults
                # This simple default row addition is more for non-admin files.
                # df_init = pd.DataFrame([defaults], columns=columns) # If defaults is a single dict row
                # More robust:
                default_row_data = {}
                has_actual_default = False
                for col_name in columns:
                    if defaults and col_name in defaults:
                        default_row_data[col_name] = defaults[col_name]
                        has_actual_default = True
                    else:
                        default_row_data[col_name] = pd.NA # Or some other placeholder if needed
                if has_actual_default : #Only add if there were actual defaults
                     # This part needs care if `defaults` is not a full row.
                     # The original code for non-admin defaults was more complex for type handling.
                     # For simplicity, let's assume if defaults are provided, they form a valid initial row.
                     # df_init = pd.DataFrame([default_row_data], columns=columns) # This might lead to type issues.
                     # Reverting to a safer way: initialize columns then potentially data if needed.
                     for col, default_val in defaults.items():
                         if col in columns:
                             if pd.isna(default_val): df_init[col] = pd.Series(dtype='object')
                             else: df_init[col] = pd.Series(dtype=type(default_val))
            df_init.to_csv(filepath, index=False, encoding='utf-8')
            df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec_local if dtype_spec_local else None) # Reload to ensure types
        else: # File exists
            df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec_local if dtype_spec_local else None)

        # --- Specific handling for admin_credenciais_csv to ensure master admin integrity ---
        if filepath == admin_credenciais_csv:
            admin_master_name = "admin"
            admin_master_pass = "potencialize"

            # Ensure all defined permission columns exist
            for perm_col_ensure in ALL_ADMIN_PERMISSION_KEYS:
                if perm_col_ensure not in df_init.columns:
                    df_init[perm_col_ensure] = False # Add with default False for other users

            # Ensure all base columns (Usuario, Senha, + Perms) exist
            for base_col_admin in colunas_base_admin_credenciais:
                if base_col_admin not in df_init.columns:
                    if base_col_admin == "Usuario": df_init[base_col_admin] = pd.NA
                    elif base_col_admin == "Senha": df_init[base_col_admin] = pd.NA
                    elif base_col_admin in ALL_ADMIN_PERMISSION_KEYS: df_init[base_col_admin] = False
                    else: df_init[base_col_admin] = pd.NA # Other potential base columns

            # Convert all permission columns to boolean type first
            for perm_key in ALL_ADMIN_PERMISSION_KEYS:
                if perm_key in df_init.columns:
                    df_init[perm_key] = df_init[perm_key].apply(robust_str_to_bool)

            admin_row_indices = df_init[df_init['Usuario'] == admin_master_name].index
            
            if not admin_row_indices.empty: # Master admin exists
                admin_idx = admin_row_indices[0]
                df_init.loc[admin_idx, 'Senha'] = admin_master_pass # Enforce password
                for perm_key in ALL_ADMIN_PERMISSION_KEYS: # Enforce all permissions
                    df_init.loc[admin_idx, perm_key] = True
            else: # Master admin is missing, add it
                new_admin_data = {'Usuario': admin_master_name, 'Senha': admin_master_pass}
                for perm_key in ALL_ADMIN_PERMISSION_KEYS:
                    new_admin_data[perm_key] = True
                
                # Ensure all base columns are present in the new_admin_data
                for col_name_new_admin in colunas_base_admin_credenciais:
                    if col_name_new_admin not in new_admin_data:
                         new_admin_data[col_name_new_admin] = pd.NA # Default for other base cols
                
                new_row_df = pd.DataFrame([new_admin_data])
                # Align columns with df_init before concat
                new_row_df = new_row_df.reindex(columns=df_init.columns).fillna(
                    {k:True for k in ALL_ADMIN_PERMISSION_KEYS if k in df_init.columns}
                )
                df_init = pd.concat([df_init, new_row_df], ignore_index=True).drop_duplicates(subset=['Usuario'], keep='first')

            # Final pass to ensure all permission columns are bool after any manipulation for 'admin'
            for perm_key in ALL_ADMIN_PERMISSION_KEYS:
                 if perm_key in df_init.columns:
                    df_init[perm_key] = df_init[perm_key].apply(robust_str_to_bool)
            
            df_init.to_csv(filepath, index=False, encoding='utf-8')
            # For admin_credenciais_csv, the specific handling above is comprehensive.
            # The generic column adding logic below should not conflict.
        # --- End of specific 'admin' user handling for admin_credenciais_csv ---

        # Generic column existence and type check for all files (from original code)
        made_generic_changes = False
        current_cols = df_init.columns.tolist()
        for col_idx, col_name in enumerate(columns): # `columns` is the definitive list for this file
            if col_name not in current_cols:
                default_val_generic = defaults.get(col_name, pd.NA) if defaults else pd.NA
                
                # Determine dtype, special care for bool for admin permission columns
                is_admin_perm_col = (filepath == admin_credenciais_csv and col_name in ALL_ADMIN_PERMISSION_KEYS)
                col_dtype_generic = bool if is_admin_perm_col else (object if pd.isna(default_val_generic) else type(default_val_generic))
                
                if col_dtype_generic == bool:
                    actual_default_val = robust_str_to_bool(default_val_generic if not is_admin_perm_col else False)
                else:
                    actual_default_val = default_val_generic

                if len(df_init) > 0:
                    insert_values = [actual_default_val] * len(df_init)
                    df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=pd.Series(insert_values, index=df_init.index).astype(col_dtype_generic if col_dtype_generic != bool else object))
                    if col_dtype_generic == bool:
                         df_init[col_name] = df_init[col_name].apply(robust_str_to_bool)
                else: # DataFrame is empty, just add the column with correct type
                    df_init[col_name] = pd.Series(dtype=col_dtype_generic)
                made_generic_changes = True
        
        if made_generic_changes:
            # If columns were added, and it's the admin file, re-run the master admin integrity check
            # to ensure any newly added permission columns are True for 'admin'.
            if filepath == admin_credenciais_csv:
                admin_master_name = "admin"
                admin_row_indices = df_init[df_init['Usuario'] == admin_master_name].index
                if not admin_row_indices.empty:
                    admin_idx = admin_row_indices[0]
                    for perm_key_recheck in ALL_ADMIN_PERMISSION_KEYS:
                        if perm_key_recheck in df_init.columns: # If the column now exists
                            df_init.loc[admin_idx, perm_key_recheck] = True
                            df_init[perm_key_recheck] = df_init[perm_key_recheck].apply(robust_str_to_bool) # ensure type
            df_init.to_csv(filepath, index=False, encoding='utf-8')

    except pd.errors.EmptyDataError: # Catch if read_csv on existing file returns empty
        df_init = pd.DataFrame(columns=columns)
        if filepath == admin_credenciais_csv:
            admin_data = {"Usuario": "admin", "Senha": "potencialize"}
            for pk in ALL_ADMIN_PERMISSION_KEYS: admin_data[pk] = True
            for base_col in columns:
                if base_col not in admin_data: admin_data[base_col] = pd.NA
            df_init = pd.DataFrame([admin_data], columns=columns)
            for perm_col_s in ALL_ADMIN_PERMISSION_KEYS:
                if perm_col_s in df_init.columns:
                    df_init[perm_col_s] = df_init[perm_col_s].apply(robust_str_to_bool)
        elif defaults: # For other files
            # Logic for applying defaults to a newly created empty DataFrame
            for col, default_val in defaults.items():
                if col in columns:
                    if pd.isna(default_val): df_init[col] = pd.Series(dtype='object')
                    else: df_init[col] = pd.Series(dtype=type(default_val))
        df_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e:
        st.error(f"Erro crítico ao inicializar {filepath}: {e}")
        st.exception(e)
        raise

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])

    admin_file_structural_defaults = {"Usuario": "admin", "Senha": "potencialize"}
    for perm_key in ALL_ADMIN_PERMISSION_KEYS:
        admin_file_structural_defaults[perm_key] = True 
    
    inicializar_csv(admin_credenciais_csv, colunas_base_admin_credenciais, defaults=admin_file_structural_defaults)

    # Simplified Post-initialization sanity check for admin file
    try:
        df_admins_final_check = pd.read_csv(admin_credenciais_csv, encoding='utf-8', dtype={'Usuario':str, 'Senha':str})
        if df_admins_final_check.empty:
            st.error(f"CRÍTICO: {admin_credenciais_csv} é VAZIO após a inicialização.")
        else:
            admin_row_check = df_admins_final_check[df_admins_final_check['Usuario'] == 'admin']
            if admin_row_check.empty:
                st.error(f"CRÍTICO: Usuário 'admin' NÃO ENCONTRADO em {admin_credenciais_csv} após inicialização.")
            else:
                if admin_row_check.iloc[0]['Senha'] != 'potencialize':
                     st.error(f"CRÍTICO: Senha do usuário 'admin' incorreta ('{admin_row_check.iloc[0]['Senha']}') após inicialização.")
                for perm_key_verify in ALL_ADMIN_PERMISSION_KEYS:
                    if perm_key_verify not in admin_row_check.columns or not robust_str_to_bool(admin_row_check.iloc[0][perm_key_verify]):
                        st.error(f"CRÍTICO: Usuário 'admin' não possui a permissão '{perm_key_verify}' após inicialização.")
                        break
    except Exception as e_post_init_admin_check:
        st.error(f"Erro durante a verificação pós-inicialização de {admin_credenciais_csv}: {e_post_init_admin_check}")


    inicializar_csv(usuarios_csv, colunas_base_usuarios,
                    defaults={"JaVisualizouInstrucoes": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos, defaults={"TimingsPerguntasJSON": None, "ID_Diagnostico": None})
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False, "ID_Diagnostico_Relacionado": None})
    inicializar_csv(faq_sac_csv, colunas_base_faq, defaults={"CategoriaFAQ": "Geral"})
    inicializar_csv(pesquisa_satisfacao_perguntas_csv, colunas_base_pesquisa_perguntas, defaults={"Ordem": 0, "Ativa": True, "OpcoesRespostaJSON": "[]"})
    inicializar_csv(pesquisa_satisfacao_respostas_csv, colunas_base_pesquisa_respostas, defaults={"ID_Diagnostico_Associado": None, "RespostasJSON": "{}"})

except Exception as e_init:
    st.error(f"Falha na inicialização de arquivos CSV: {e_init}")
    st.exception(e_init)
    st.stop()

# --- Funções Utilitárias (mantidas) ---
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
                if field in ["DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]:
                    st.session_state.user[field] = int(value)
                elif field == "JaVisualizouInstrucoes":
                    st.session_state.user[field] = robust_str_to_bool(value)
                else:
                    st.session_state.user[field] = value
            return True
    except Exception as e: st.error(f"Erro ao atualizar usuário ({field}): {e}")
    return False

@st.cache_data
def carregar_analises_perguntas():
    try: return pd.read_csv(analises_perguntas_csv, encoding='utf-8')
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame(columns=colunas_base_analises)

@st.cache_data(ttl=60)
def carregar_faq():
    try:
        df = pd.read_csv(faq_sac_csv, encoding='utf-8')
        if "ID_FAQ" not in df.columns:
            df["ID_FAQ"] = [str(uuid.uuid4()) for _ in range(len(df))]
            df.to_csv(faq_sac_csv, index=False, encoding='utf-8')
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_faq)

def salvar_faq(df_faq):
    df_faq.to_csv(faq_sac_csv, index=False, encoding='utf-8')
    st.cache_data.clear()

@st.cache_data(ttl=60)
def carregar_pesquisa_perguntas():
    try:
        df = pd.read_csv(pesquisa_satisfacao_perguntas_csv, encoding='utf-8')
        if "ID_PerguntaPesquisa" not in df.columns:
            df["ID_PerguntaPesquisa"] = [str(uuid.uuid4()) for _ in range(len(df))]
        if "Ativa" not in df.columns: df["Ativa"] = True
        df["Ativa"] = df["Ativa"].apply(robust_str_to_bool)
        if "Ordem" not in df.columns: df["Ordem"] = 0
        df["Ordem"] = pd.to_numeric(df["Ordem"], errors='coerce').fillna(0).astype(int)
        if "OpcoesRespostaJSON" not in df.columns: df["OpcoesRespostaJSON"] = "[]"
        df["OpcoesRespostaJSON"] = df["OpcoesRespostaJSON"].fillna("[]").astype(str)
        if "ID_PerguntaPesquisa" in df.columns:
            df["ID_PerguntaPesquisa"] = df["ID_PerguntaPesquisa"].astype(str)
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_pesquisa_perguntas)

def salvar_pesquisa_perguntas(df_perguntas):
    df_perguntas.to_csv(pesquisa_satisfacao_perguntas_csv, index=False, encoding='utf-8')
    st.cache_data.clear()

@st.cache_data(ttl=30)
def carregar_pesquisa_respostas():
    try:
        df = pd.read_csv(pesquisa_satisfacao_respostas_csv, encoding='utf-8', dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Associado': str})
        if "RespostasJSON" not in df.columns: df["RespostasJSON"] = "{}"
        df["RespostasJSON"] = df["RespostasJSON"].fillna("{}").astype(str)
        if "ID_SessaoRespostaPesquisa" in df.columns: df["ID_SessaoRespostaPesquisa"] = df["ID_SessaoRespostaPesquisa"].astype(str)
        if "ID_Diagnostico_Associado" in df.columns: df["ID_Diagnostico_Associado"] = df["ID_Diagnostico_Associado"].astype(str).fillna("")
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_pesquisa_respostas)

def salvar_pesquisa_respostas(df_respostas):
    df_respostas.to_csv(pesquisa_satisfacao_respostas_csv, index=False, encoding='utf-8')
    st.cache_data.clear()

# --- (obter_analise_para_resposta e gerar_pdf_diagnostico_completo mantidas) ---
def obter_analise_para_resposta(pergunta_texto, resposta_valor, df_analises):
    # ... (código mantido)
    relevant_analyses = df_analises[df_analises['TextoPerguntaOriginal'] == pergunta_texto]
    if relevant_analyses.empty:
        return None

    for _, row in relevant_analyses.iterrows():
        tipo_condicao = row['TipoCondicao']
        analise_texto = row['TextoAnalise']
        try:
            val_num = float(resposta_valor) # Assumindo que resposta_valor pode ser convertido para float
            min_val = pd.to_numeric(row['CondicaoValorMin'], errors='coerce')
            max_val = pd.to_numeric(row['CondicaoValorMax'], errors='coerce')
            exact_val = pd.to_numeric(row['CondicaoValorExato'], errors='coerce')

            if tipo_condicao == "Entre" and pd.notna(min_val) and pd.notna(max_val):
                if min_val <= val_num <= max_val: return analise_texto
            elif tipo_condicao == "Maior que" and pd.notna(min_val):
                if val_num > min_val: return analise_texto
            elif tipo_condicao == "Menor que" and pd.notna(max_val):
                if val_num < max_val: return analise_texto
            elif tipo_condicao == "Igual a" and pd.notna(exact_val):
                if val_num == exact_val: return analise_texto
        except ValueError: # Se resposta_valor não for numérico, não aplicar lógicas numéricas
            pass
        except Exception as e_cond:
            print(f"Erro ao processar condição de análise para '{pergunta_texto}': {e_cond}")
            continue # Tenta a próxima condição se houver
    return None


def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df, respostas_coletadas, medias_cat, analises_df):
    # ... (código mantido)
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            logo_path_pdf = find_client_logo_path(user_data.get('CNPJ'))
            if not logo_path_pdf: # Fallback to a default portal logo if client specific is not found
                 if os.path.exists(CUSTOM_LOGIN_LOGO_PATH): logo_path_pdf = CUSTOM_LOGIN_LOGO_PATH
                 elif os.path.exists(DEFAULT_LOGIN_LOGO_PATH): logo_path_pdf = DEFAULT_LOGIN_LOGO_PATH

            if logo_path_pdf and os.path.exists(logo_path_pdf):
                try: self.image(logo_path_pdf, 10, 8, 33)
                except Exception as e_img: print(f"Erro ao adicionar logo ao PDF: {e_img}")

            self.cell(0, 10, pdf_safe_text_output('Relatório de Diagnóstico'), 0, 1, 'C')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, pdf_safe_text_output(f'Página {self.page_no()}'), 0, 0, 'C')

        def chapter_title(self, title):
            self.set_font('Arial', 'B', 12)
            self.set_fill_color(200, 220, 255)
            self.cell(0, 10, pdf_safe_text_output(title), 0, 1, 'L', True)
            self.ln(4)

        def chapter_body(self, body_dict, is_respostas=False, analises_df_local=None):
            self.set_font('Arial', '', 10)
            for key, value in body_dict.items():
                bold_key = pdf_safe_text_output(f"{key}: ")
                regular_value = pdf_safe_text_output(str(value))
                
                self.set_font('Arial', 'B', 10)
                self.multi_cell(0, 7, bold_key, 0, 'L')
                self.set_font('Arial', '', 10)
                self.multi_cell(0, 7, regular_value, 0, 'L')
                
                if is_respostas and analises_df_local is not None:
                    analise_para_resposta = obter_analise_para_resposta(key, value, analises_df_local)
                    if analise_para_resposta:
                        self.set_font('Arial', 'I', 9)
                        self.set_text_color(0, 100, 0) # Verde escuro para análise
                        self.multi_cell(0, 6, pdf_safe_text_output(f"   Análise Sugerida: {analise_para_resposta}"), 0, 'L')
                        self.set_text_color(0,0,0) # Reset color
                self.ln(2)


    pdf = PDF()
    pdf.add_page()

    # Dados do Cliente e Diagnóstico
    pdf.chapter_title('Informações do Cliente e Diagnóstico')
    info_cliente = {
        "Empresa": user_data.get('Empresa', 'N/D'), "CNPJ": user_data.get('CNPJ', 'N/D'),
        "Nome do Contato": user_data.get('NomeContato', 'N/D'), "Email": diag_data.get('Email', 'N/D'),
        "Data do Diagnóstico": diag_data.get('Data', 'N/D'),
        "ID do Diagnóstico": diag_data.get('ID_Diagnostico', 'N/D')
    }
    pdf.chapter_body(info_cliente)
    pdf.ln(5)

    # Respostas do Diagnóstico
    pdf.chapter_title('Respostas do Diagnóstico')
    respostas_formatadas_pdf = {}
    # Garantir que as perguntas sejam listadas na ordem correta, se possível
    if not perguntas_df.empty:
        for _, row_pergunta in perguntas_df.iterrows():
            pergunta_texto = row_pergunta['Pergunta']
            if pergunta_texto in respostas_coletadas:
                 respostas_formatadas_pdf[pergunta_texto] = respostas_coletadas[pergunta_texto]
    else: # Fallback se perguntas_df estiver vazio, usar a ordem de respostas_coletadas
        respostas_formatadas_pdf = respostas_coletadas
    pdf.chapter_body(respostas_formatadas_pdf, is_respostas=True, analises_df_local=analises_df)
    pdf.ln(5)

    # Médias por Categoria
    if medias_cat:
        pdf.chapter_title('Médias por Categoria')
        medias_cat_formatado = {k.replace("Media_Cat_", "").replace("_", " "): f"{v:.2f}" for k,v in medias_cat.items()}
        pdf.chapter_body(medias_cat_formatado)
        pdf.ln(5)

    # Métricas Gerais
    pdf.chapter_title('Métricas Gerais do Diagnóstico')
    metricas_gerais = {
        "Média Geral do Diagnóstico": f"{diag_data.get('Média Geral', 0):.2f}",
        "Score GUT Médio (Priorização)": f"{diag_data.get('GUT Média', 0):.2f}"
    }
    pdf.chapter_body(metricas_gerais)
    pdf.ln(5)

    # Análise e Observações
    if pd.notna(diag_data.get('Diagnóstico')) and diag_data.get('Diagnóstico'):
        pdf.chapter_title('Diagnóstico Geral (Gerado pelo Sistema/Admin)')
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 7, pdf_safe_text_output(str(diag_data['Diagnóstico'])))
        pdf.ln(5)

    if pd.notna(diag_data.get('Análise do Cliente')) and diag_data.get('Análise do Cliente'):
        pdf.chapter_title('Comentários/Análise do Cliente')
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 7, pdf_safe_text_output(str(diag_data['Análise do Cliente'])))
        pdf.ln(5)
    
    if pd.notna(diag_data.get('Observações')) and diag_data.get('Observações'): # Observações gerais do formulário
        pdf.chapter_title('Observações Gerais (Preenchidas no Formulário)')
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 7, pdf_safe_text_output(str(diag_data['Observações'])))
        pdf.ln(5)

    if pd.notna(diag_data.get('Comentarios_Admin')) and diag_data.get('Comentarios_Admin'):
        pdf.chapter_title('Comentários Adicionais do Administrador')
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 7, pdf_safe_text_output(str(diag_data['Comentarios_Admin'])))
        pdf.ln(5)

    try:
        temp_dir = tempfile.mkdtemp()
        safe_empresa_name = sanitize_column_name(user_data.get('Empresa', 'Cliente')).replace('_', '')
        safe_cnpj = sanitize_column_name(user_data.get('CNPJ', 'SemCNPJ')).replace('_', '')
        timestamp_pdf = datetime.now().strftime("%Y%m%d%H%M%S")
        pdf_filename = f"Diagnostico_{safe_empresa_name}_{safe_cnpj}_{timestamp_pdf}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)
        pdf.output(pdf_path, 'F')
        return pdf_path, pdf_filename
    except Exception as e_pdf_gen:
        st.error(f"Erro ao gerar PDF: {e_pdf_gen}")
        return None, None


# --- LOGIN AND MAIN NAVIGATION ---
top_login_placeholder = st.empty()
admin_login_form_placeholder = st.empty()
client_login_form_placeholder = st.empty()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    login_logo_to_display = DEFAULT_LOGIN_LOGO_PATH
    if os.path.exists(CUSTOM_LOGIN_LOGO_PATH):
        login_logo_to_display = CUSTOM_LOGIN_LOGO_PATH

    with top_login_placeholder.container():
        st.markdown('<div style="display: flex; justify-content: center; margin-bottom: 20px;">', unsafe_allow_html=True)
        if os.path.exists(login_logo_to_display):
            st.image(login_logo_to_display, width=200)
        else:
            st.markdown("<h2 style='text-align: center;'>Portal de Diagnóstico</h2>", unsafe_allow_html=True)
            if not os.path.exists(DEFAULT_LOGIN_LOGO_PATH) and not os.path.exists(CUSTOM_LOGIN_LOGO_PATH):
                st.caption(f"Logo padrão '{DEFAULT_LOGIN_LOGO_FILENAME}' ou personalizada '{CUSTOM_LOGIN_LOGO_FILENAME}' não encontrada. Configure em Admin > Personalizar Aparência ou adicione os arquivos em '{ASSETS_DIR}/'.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.session_state.login_selection_aba = st.radio(
            "Você é:",
            ["Administrador", "Cliente"],
            horizontal=True,
            key="tipo_usuario_radio_v24_login_selection",
            index=["Administrador", "Cliente"].index(st.session_state.login_selection_aba),
            label_visibility="collapsed"
        )
        st.markdown('<hr style="margin-top: 0; margin-bottom: 30px;">', unsafe_allow_html=True)

    if st.session_state.login_selection_aba == "Administrador":
        client_login_form_placeholder.empty()
        with admin_login_form_placeholder.container():
            st.markdown('<div class="login-container" style="border-top: 6px solid #c0392b;">', unsafe_allow_html=True)
            if os.path.exists(login_logo_to_display):
                st.image(login_logo_to_display, width=180)
            st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
            with st.form("form_admin_login_v24_final"):
                u = st.text_input("Usuário", key="admin_u_v24_final_input")
                p = st.text_input("Senha", type="password", key="admin_p_v24_final_input")
                if st.form_submit_button("Entrar", use_container_width=True, icon="🔑"):
                    try:
                        df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8', dtype={'Usuario':str, 'Senha':str})
                        # Ensure all permission columns are boolean after loading
                        for perm_col_login in ALL_ADMIN_PERMISSION_KEYS:
                            if perm_col_login not in df_creds.columns:
                                df_creds[perm_col_login] = False # Should be handled by inicializar_csv
                            df_creds[perm_col_login] = df_creds[perm_col_login].apply(robust_str_to_bool)

                        if not df_creds.empty:
                            admin_match = df_creds[(df_creds["Usuario"] == u) & (df_creds["Senha"] == p)]
                            if not admin_match.empty:
                                st.session_state.admin_logado = True
                                st.session_state.admin_user_details = admin_match.iloc[0].to_dict()
                                st.session_state.aba = "Administrador"
                                st.toast("Login de admin bem-sucedido!", icon="🎉")
                                top_login_placeholder.empty()
                                admin_login_form_placeholder.empty()
                                client_login_form_placeholder.empty()
                                st.rerun()
                            else:
                                st.error("Usuário/senha admin inválidos.")
                        else:
                            st.error("Nenhum administrador cadastrado.")
                    except FileNotFoundError:
                        st.error(f"Arquivo de credenciais de administrador '{admin_credenciais_csv}' não encontrado.")
                    except Exception as e: st.error(f"Erro login admin: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.login_selection_aba == "Cliente":
        admin_login_form_placeholder.empty()
        with client_login_form_placeholder.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            if os.path.exists(login_logo_to_display):
                st.image(login_logo_to_display, width=180)
            st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
            with st.form("form_cliente_login_v24_final"):
                c = st.text_input("CNPJ", key="cli_c_v24_final_input", value=st.session_state.get("last_cnpj_input",""))
                s = st.text_input("Senha", type="password", key="cli_s_v24_final_input")
                if st.form_submit_button("Entrar", use_container_width=True, icon="👤"):
                    st.session_state.last_cnpj_input = c
                    try:
                        users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                        if "JaVisualizouInstrucoes" not in users_df.columns: users_df["JaVisualizouInstrucoes"] = "False"
                        users_df["JaVisualizouInstrucoes"] = users_df["JaVisualizouInstrucoes"].apply(robust_str_to_bool)
                        if "DiagnosticosDisponiveis" not in users_df.columns: users_df["DiagnosticosDisponiveis"] = 1
                        users_df["DiagnosticosDisponiveis"] = pd.to_numeric(users_df["DiagnosticosDisponiveis"], errors='coerce').fillna(1).astype(int)
                        if "TotalDiagnosticosRealizados" not in users_df.columns: users_df["TotalDiagnosticosRealizados"] = 0
                        users_df["TotalDiagnosticosRealizados"] = pd.to_numeric(users_df["TotalDiagnosticosRealizados"], errors='coerce').fillna(0).astype(int)

                        blocked_df = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                        if c in blocked_df["CNPJ"].values:
                            st.error("CNPJ bloqueado.")
                        else:
                            match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == s)]
                            if not match.empty:
                                st.session_state.cliente_logado = True; st.session_state.cnpj = c
                                st.session_state.user = match.iloc[0].to_dict()
                                st.session_state.user["JaVisualizouInstrucoes"] = robust_str_to_bool(st.session_state.user.get("JaVisualizouInstrucoes", "False"))
                                st.session_state.user["DiagnosticosDisponiveis"] = int(st.session_state.user.get("DiagnosticosDisponiveis", 1))
                                st.session_state.user["TotalDiagnosticosRealizados"] = int(st.session_state.user.get("TotalDiagnosticosRealizados", 0))
                                st.session_state.inicio_sessao_cliente = time.time()
                                registrar_acao(c, "Login", "Usuário logou.")

                                if not st.session_state.user["JaVisualizouInstrucoes"]:
                                    st.session_state.cliente_page = "Instruções"
                                else:
                                    pode_fazer_novo_login = st.session_state.user["DiagnosticosDisponiveis"] > st.session_state.user["TotalDiagnosticosRealizados"]
                                    st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo_login else "Painel Principal"

                                st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                                st.session_state.respostas_atuais_diagnostico = {}
                                st.session_state.progresso_diagnostico_percentual = 0
                                st.session_state.progresso_diagnostico_contagem = (0,0)
                                st.session_state.feedbacks_respostas = {}
                                st.session_state.diagnostico_enviado_sucesso = False
                                st.session_state.target_diag_data_for_expansion = None
                                st.session_state.diagnostic_question_timings = {}
                                st.session_state.current_question_start_time = None
                                st.session_state.previous_question_text_tracker = None
                                st.session_state.current_survey_responses = {}
                                st.session_state.survey_submitted_for_current_diag = False
                                st.session_state.survey_id_diagnostico_associado = None
                                st.session_state.aba = "Cliente"

                                st.toast("Login de cliente bem-sucedido!", icon="👋")
                                top_login_placeholder.empty()
                                admin_login_form_placeholder.empty()
                                client_login_form_placeholder.empty()
                                st.rerun()
                            else:
                                st.error("CNPJ/senha inválidos.")
                    except FileNotFoundError:
                        st.error(f"Arquivo de usuários '{usuarios_csv}' ou de bloqueados '{usuarios_bloqueados_csv}' não encontrado.")
                    except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
            st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.admin_logado and not st.session_state.cliente_logado:
        st.stop()

if st.session_state.admin_logado:
    aba = "Administrador"
elif st.session_state.cliente_logado:
    aba = "Cliente"
else:
    if 'login_selection_aba' in st.session_state :
        st.info("Por favor, complete o login.")
    else:
        st.error("Estado da aplicação indefinido. Por favor, recarregue.")
    st.stop()


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    if 'user' not in st.session_state or not st.session_state.user:
        st.error("Erro de sessão do usuário. Por favor, faça login novamente.")
        st.session_state.cliente_logado = False
        st.rerun()

    if not robust_str_to_bool(st.session_state.user.get("JaVisualizouInstrucoes", False)): # Usar conversão robusta
        st.session_state.cliente_page = "Instruções"

    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
    with st.sidebar.expander("👤 Meu Perfil", expanded=True):
        logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
        if logo_cliente_path: st.image(logo_cliente_path, width=100)
        st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
        st.write(f"**CNPJ:** {st.session_state.cnpj}")
        st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
        st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")

        total_slots = st.session_state.user.get('DiagnosticosDisponiveis', 0)
        realizados = st.session_state.user.get('TotalDiagnosticosRealizados', 0)
        restantes = max(0, total_slots - realizados)
        st.markdown(f"**Diagnósticos Contratados (Slots):** `{total_slots}`")
        st.markdown(f"**Diagnósticos Realizados:** `{realizados}`")
        st.markdown(f"**Diagnósticos Restantes:** `{restantes}`")

    notificacoes_nao_lidas_count = 0
    if os.path.exists(notificacoes_csv) and st.session_state.get("cnpj"):
        try:
            df_notif_check = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Relacionado': str})
            if not df_notif_check.empty and 'Lida' in df_notif_check.columns:
                df_notif_check['Lida'] = df_notif_check['Lida'].apply(robust_str_to_bool) # Usar conversão robusta
                notificacoes_nao_lidas_count = len(df_notif_check[
                    (df_notif_check["CNPJ_Cliente"] == st.session_state.cnpj) &
                    (df_notif_check["Lida"] == False)
                ])
        except pd.errors.EmptyDataError: notificacoes_nao_lidas_count = 0
        except Exception as e_notif_check: print(f"Erro ao verificar notificações: {e_notif_check}")

    notificacoes_label = "🔔 Notificações"
    if notificacoes_nao_lidas_count > 0:
        notificacoes_label = f"🔔 Notificações ({notificacoes_nao_lidas_count} Nova(s))"

    menu_options_cli_map_full = {
        "Instruções": "📖 Instruções",
        "Novo Diagnóstico": "📋 Novo Diagnóstico",
        "Painel Principal": "🏠 Painel Principal",
        "Suporte/FAQ": "💬 Suporte/FAQ",
        "Pesquisa de Satisfação": "🌟 Pesquisa de Satisfação",
        "Notificações": notificacoes_label
    }

    if not robust_str_to_bool(st.session_state.user.get("JaVisualizouInstrucoes", False)):
        menu_options_cli_map = {"Instruções": "📖 Instruções"}
        if st.session_state.cliente_page != "Instruções":
            st.session_state.cliente_page = "Instruções"
            st.rerun()
    else:
        menu_options_cli_map = menu_options_cli_map_full.copy()
        pode_fazer_novo = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
        if not pode_fazer_novo and "Novo Diagnóstico" in menu_options_cli_map:
            if st.session_state.cliente_page == "Novo Diagnóstico":
                st.session_state.cliente_page = "Painel Principal"
            del menu_options_cli_map["Novo Diagnóstico"]

    menu_options_cli_display = list(menu_options_cli_map.values())

    if st.session_state.cliente_page not in menu_options_cli_map.keys():
        st.session_state.cliente_page = "Instruções" if not robust_str_to_bool(st.session_state.user.get("JaVisualizouInstrucoes", False)) else "Painel Principal"

    default_display_option = menu_options_cli_map.get(st.session_state.cliente_page)
    current_idx_cli = 0
    if default_display_option and default_display_option in menu_options_cli_display:
        try:
            current_idx_cli = menu_options_cli_display.index(default_display_option)
        except ValueError:
            current_idx_cli = 0
            if menu_options_cli_display:
                for key_p, val_p in menu_options_cli_map.items():
                    if val_p == menu_options_cli_display[0]:
                        st.session_state.cliente_page = key_p
                        break
    elif menu_options_cli_display:
        current_idx_cli = 0
        for key_page_fallback, val_page_display_fallback in menu_options_cli_map.items():
            if val_page_display_fallback == menu_options_cli_display[0]:
                st.session_state.cliente_page = key_page_fallback
                break

    selected_page_cli_raw = st.sidebar.radio("Menu Cliente", menu_options_cli_display, index=current_idx_cli, key="cli_menu_v24_final_conditional_key") # CHAVE ATUALIZADA

    selected_page_cli_clean = ""
    for key_page, val_page_display in menu_options_cli_map.items():
        if val_page_display == selected_page_cli_raw:
            if key_page == "Notificações": # Handle the dynamic label
                selected_page_cli_clean = "Notificações"
            else:
                selected_page_cli_clean = key_page
            break

    if selected_page_cli_clean and selected_page_cli_clean != st.session_state.cliente_page :
        st.session_state.cliente_page = selected_page_cli_clean
        st.session_state.force_sidebar_rerun_after_notif_read_v19 = False
        st.session_state.target_diag_data_for_expansion = None
        st.rerun()

    if st.sidebar.button("Sair do Portal Cliente", icon="⬅️", key="logout_cliente_v24_final_btn", use_container_width=True): # CHAVE ATUALIZADA
        keys_to_clear = [k for k in st.session_state.keys() if k not in ['admin_logado', 'last_cnpj_input', 'login_selection_aba']]
        for key_item in keys_to_clear: del st.session_state[key_item]
        for key_d, value_d in default_session_state.items():
            if key_d not in ['admin_logado', 'last_cnpj_input', 'login_selection_aba']: st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False
        st.toast("Logout realizado.", icon="👋")
        st.rerun()

    # --- Conteúdo das páginas do cliente (mantido, apenas chaves de widgets podem precisar de atualização para v24 se houver conflito) ---
    if st.session_state.cliente_page == "Instruções":
        # ... (código da página Instruções)
        st.markdown("## 📖 Instruções do Portal de Diagnóstico")
        st.markdown("---")

        instrucoes_content = ""
        default_instr_content = """
        ### Bem-vindo ao Portal de Diagnóstico!

        Este portal foi projetado para ajudar você a entender melhor diversos aspectos do seu negócio através de um diagnóstico interativo.

        **Como proceder:**

        1.  **Primeiro Acesso:** Se esta é sua primeira vez, você está na página de instruções. Leia atentamente.
        2.  **Próximo Passo:** Clique em "Entendi, ir para o Diagnóstico" abaixo para prosseguir.
        3.  **Novo Diagnóstico:**
            * Você será direcionado para a página "Novo Diagnóstico".
            * Responda a todas as perguntas da forma mais precisa possível. Sua honestidade é crucial para a qualidade do diagnóstico.
            * Utilize a escala de 1 a 5, onde:
                * **1:** Discordo totalmente / Muito ruim / Inexistente
                * **2:** Discordo parcialmente / Ruim / Pouco desenvolvido
                * **3:** Neutro / Razoável / Em desenvolvimento
                * **4:** Concordo parcialmente / Bom / Bem desenvolvido
                * **5:** Concordo totalmente / Excelente / Totalmente implementado
            * Algumas perguntas podem ter um campo "GUT" (Gravidade, Urgência, Tendência). Preencha-os para ajudar na priorização de ações.
            * Ao final, você poderá adicionar observações gerais.
        4.  **Envio e Resultados:**
            * Após preencher tudo, clique em "Enviar Diagnóstico".
            * Você será levado ao "Painel Principal", onde poderá ver um resumo do seu diagnóstico e, se disponível, baixar um PDF completo.
        5.  **Painel Principal:** Aqui você pode revisitar seus diagnósticos anteriores (se houver mais de um permitido).
        6.  **Suporte/FAQ:** Tem dúvidas? Consulte nossa seção de Perguntas Frequentes.
        7.  **Pesquisa de Satisfação:** Após completar um diagnóstico, gostaríamos de ouvir seu feedback através da Pesquisa de Satisfação.
        8.  **Notificações:** Verifique esta seção para quaisquer atualizações ou mensagens importantes do administrador.

        **Importante:**
        * Seus diagnósticos são confidenciais.
        * Se precisar interromper o preenchimento, suas respostas parciais *não* serão salvas até que você clique em "Enviar Diagnóstico".

        Estamos à disposição para qualquer esclarecimento!
        """

        if os.path.exists(instrucoes_custom_path):
            try:
                with open(instrucoes_custom_path, "r", encoding="utf-8") as f:
                    instrucoes_content = f.read()
            except Exception as e:
                st.warning(f"Não foi possível carregar as instruções personalizadas: {e}")
                instrucoes_content = default_instr_content
        else:
            instrucoes_content = default_instr_content

        st.markdown(instrucoes_content, unsafe_allow_html=True)

        if st.button("✅ Entendi, ir para o Diagnóstico", key="btn_entendi_instrucoes_v24_final", type="primary"):
            update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", "True")
            st.session_state.user["JaVisualizouInstrucoes"] = True # Atualiza em tempo real na sessão

            # Determina a próxima página após as instruções
            pode_fazer_novo_diag_pos_instr = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            if pode_fazer_novo_diag_pos_instr:
                st.session_state.cliente_page = "Novo Diagnóstico"
            else:
                st.session_state.cliente_page = "Painel Principal"
            st.rerun()
        pass
    elif st.session_state.cliente_page == "Novo Diagnóstico":
        # ... (código da página Novo Diagnóstico)
        st.markdown("## 📋 Novo Diagnóstico Empresarial")
        st.markdown("---")

        pode_fazer_novo_check = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
        if not pode_fazer_novo_check:
            st.warning("Você já utilizou todos os seus diagnósticos disponíveis. Para realizar um novo, entre em contato com o administrador.")
            if st.button("Ir para o Painel Principal", key="goto_main_from_novo_diag_limit"):
                st.session_state.cliente_page = "Painel Principal"
                st.rerun()
            st.stop()

        try:
            perguntas_df = pd.read_csv(perguntas_csv, encoding='utf-8')
            if perguntas_df.empty:
                st.error("Nenhuma pergunta de diagnóstico configurada. Por favor, contate o administrador.")
                st.stop()
        except FileNotFoundError:
            st.error(f"Arquivo de perguntas '{perguntas_csv}' não encontrado. Contate o administrador.")
            st.stop()
        except Exception as e:
            st.error(f"Erro ao carregar perguntas: {e}")
            st.stop()

        total_perguntas = len(perguntas_df)
        if total_perguntas == 0:
            st.error("Erro: Nenhuma pergunta encontrada no arquivo de configuração.")
            st.stop()
        
        st.session_state.progresso_diagnostico_contagem = (len(st.session_state.respostas_atuais_diagnostico), total_perguntas)
        st.session_state.progresso_diagnostico_percentual = (len(st.session_state.respostas_atuais_diagnostico) / total_perguntas) if total_perguntas > 0 else 0

        st.progress(st.session_state.progresso_diagnostico_percentual, text=f"Progresso: {st.session_state.progresso_diagnostico_contagem[0]}/{st.session_state.progresso_diagnostico_contagem[1]} perguntas respondidas")

        df_analises_perguntas = carregar_analises_perguntas() # Carrega as análises para consulta

        with st.form(key="form_diagnostico_cliente_v24_final"):
            # Agrupar perguntas por categoria
            categorias = perguntas_df['Categoria'].unique()
            for categoria in categorias:
                st.markdown(f"### {categoria}")
                perguntas_categoria = perguntas_df[perguntas_df['Categoria'] == categoria]
                
                for index, row in perguntas_categoria.iterrows():
                    pergunta_texto = row['Pergunta']
                    form_key_base = f"resp_{st.session_state.id_formulario_atual}_{sanitize_column_name(pergunta_texto)}"

                    # Início do rastreamento de tempo para esta pergunta, se mudou
                    if st.session_state.previous_question_text_tracker != pergunta_texto:
                        if st.session_state.previous_question_text_tracker and st.session_state.current_question_start_time:
                            time_spent_on_prev_q = time.time() - st.session_state.current_question_start_time
                            st.session_state.diagnostic_question_timings[st.session_state.previous_question_text_tracker] = \
                                st.session_state.diagnostic_question_timings.get(st.session_state.previous_question_text_tracker, 0) + time_spent_on_prev_q
                        
                        st.session_state.current_question_start_time = time.time()
                        st.session_state.previous_question_text_tracker = pergunta_texto

                    cols_pergunta = st.columns([3, 1]) # Coluna para pergunta/slider, coluna para GUT
                    with cols_pergunta[0]:
                        st.session_state.respostas_atuais_diagnostico[pergunta_texto] = st.slider(
                            f"{pergunta_texto}", 1, 5, 
                            value=st.session_state.respostas_atuais_diagnostico.get(pergunta_texto, 3), 
                            key=f"{form_key_base}_slider",
                            help="Avalie de 1 (Muito Ruim/Discordo Totalmente) a 5 (Excelente/Concordo Totalmente)."
                        )
                    
                    with cols_pergunta[1]:
                        st.markdown("<div style='font-size: 0.9em; margin-top: 25px; text-align: center; color: #555;'>GUT</div>", unsafe_allow_html=True)
                        gut_cols = st.columns(3)
                        st.session_state.respostas_atuais_diagnostico[f"{pergunta_texto}_G"] = gut_cols[0].number_input("G", 1, 5, st.session_state.respostas_atuais_diagnostico.get(f"{pergunta_texto}_G", 1), key=f"{form_key_base}_G", label_visibility="collapsed", help="Gravidade (1-5)")
                        st.session_state.respostas_atuais_diagnostico[f"{pergunta_texto}_U"] = gut_cols[1].number_input("U", 1, 5, st.session_state.respostas_atuais_diagnostico.get(f"{pergunta_texto}_U", 1), key=f"{form_key_base}_U", label_visibility="collapsed", help="Urgência (1-5)")
                        st.session_state.respostas_atuais_diagnostico[f"{pergunta_texto}_T"] = gut_cols[2].number_input("T", 1, 5, st.session_state.respostas_atuais_diagnostico.get(f"{pergunta_texto}_T", 1), key=f"{form_key_base}_T", label_visibility="collapsed", help="Tendência (1-5)")

                    # Feedback dinâmico (análise)
                    analise_para_resposta = obter_analise_para_resposta(pergunta_texto, st.session_state.respostas_atuais_diagnostico.get(pergunta_texto), df_analises_perguntas)
                    if analise_para_resposta:
                        st.markdown(f"<div class='analise-pergunta-cliente'>{analise_para_resposta}</div>", unsafe_allow_html=True)
                    st.markdown("---")

            st.markdown("### Considerações Finais")
            observacoes_cliente = st.text_area("Observações ou comentários adicionais sobre o diagnóstico:", key=f"obs_cliente_{st.session_state.id_formulario_atual}")
            
            submit_button = st.form_submit_button("Enviar Diagnóstico", type="primary", use_container_width=True, icon="🚀")

            if submit_button:
                # Finalizar rastreamento de tempo para a última pergunta
                if st.session_state.previous_question_text_tracker and st.session_state.current_question_start_time:
                    time_spent_on_last_q = time.time() - st.session_state.current_question_start_time
                    st.session_state.diagnostic_question_timings[st.session_state.previous_question_text_tracker] = \
                        st.session_state.diagnostic_question_timings.get(st.session_state.previous_question_text_tracker, 0) + time_spent_on_last_q
                    st.session_state.current_question_start_time = None # Reset
                    st.session_state.previous_question_text_tracker = None # Reset

                if len(st.session_state.respostas_atuais_diagnostico) < total_perguntas * 4: # (pergunta + G + U + T)
                    st.warning("Parece que nem todas as perguntas foram totalmente respondidas (incluindo GUT). Verifique e tente novamente.")
                else:
                    try:
                        df_diagnosticos_existente = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str, 'ID_Diagnostico': str})
                    except (FileNotFoundError, pd.errors.EmptyDataError):
                        df_diagnosticos_existente = pd.DataFrame(columns=colunas_base_diagnosticos)

                    novo_diagnostico_data = {
                        "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "CNPJ": st.session_state.cnpj,
                        "Nome": st.session_state.user.get("NomeContato", ""),
                        "Email": st.session_state.user.get("Email", ""), # Supondo que email está no user_data
                        "Empresa": st.session_state.user.get("Empresa", ""),
                        "Observações": observacoes_cliente,
                        "ID_Diagnostico": str(uuid.uuid4()) # ID Único para este diagnóstico
                    }
                    st.session_state.survey_id_diagnostico_associado = novo_diagnostico_data["ID_Diagnostico"]


                    soma_respostas = 0; count_respostas = 0
                    soma_gut = 0; count_gut_perguntas = 0
                    respostas_coletadas_para_diagnostico = {}
                    
                    # Calcular médias por categoria
                    medias_por_categoria = {}
                    for categoria_iter in categorias:
                        soma_cat = 0; count_cat = 0
                        perguntas_da_categoria = perguntas_df[perguntas_df['Categoria'] == categoria_iter]
                        for _, pergunta_row_iter in perguntas_da_categoria.iterrows():
                            pergunta_texto_iter = pergunta_row_iter['Pergunta']
                            resp = st.session_state.respostas_atuais_diagnostico.get(pergunta_texto_iter)
                            if resp is not None:
                                soma_cat += int(resp)
                                count_cat += 1
                        if count_cat > 0:
                            media_cat_val = soma_cat / count_cat
                            medias_por_categoria[f"Media_Cat_{sanitize_column_name(categoria_iter)}"] = media_cat_val
                            novo_diagnostico_data[f"Media_Cat_{sanitize_column_name(categoria_iter)}"] = f"{media_cat_val:.2f}"


                    for pergunta_df_row in perguntas_df.itertuples():
                        pergunta_txt = pergunta_df_row.Pergunta
                        resp_key = pergunta_txt
                        
                        if resp_key in st.session_state.respostas_atuais_diagnostico:
                            resposta_valor = st.session_state.respostas_atuais_diagnostico[resp_key]
                            soma_respostas += int(resposta_valor)
                            count_respostas += 1
                            novo_diagnostico_data[sanitize_column_name(pergunta_txt)] = resposta_valor
                            respostas_coletadas_para_diagnostico[pergunta_txt] = resposta_valor # Para PDF

                            g_val = st.session_state.respostas_atuais_diagnostico.get(f"{pergunta_txt}_G", 1)
                            u_val = st.session_state.respostas_atuais_diagnostico.get(f"{pergunta_txt}_U", 1)
                            t_val = st.session_state.respostas_atuais_diagnostico.get(f"{pergunta_txt}_T", 1)
                            gut_score = int(g_val) * int(u_val) * int(t_val)
                            soma_gut += gut_score
                            count_gut_perguntas +=1
                            novo_diagnostico_data[f"GUT_{sanitize_column_name(pergunta_txt)}"] = gut_score
                            # Também salvar G, U, T individuais se necessário
                            novo_diagnostico_data[f"G_{sanitize_column_name(pergunta_txt)}"] = g_val
                            novo_diagnostico_data[f"U_{sanitize_column_name(pergunta_txt)}"] = u_val
                            novo_diagnostico_data[f"T_{sanitize_column_name(pergunta_txt)}"] = t_val

                    novo_diagnostico_data["Média Geral"] = (soma_respostas / count_respostas) if count_respostas > 0 else 0
                    novo_diagnostico_data["GUT Média"] = (soma_gut / count_gut_perguntas) if count_gut_perguntas > 0 else 0
                    
                    # Adicionar Timings JSON
                    novo_diagnostico_data["TimingsPerguntasJSON"] = json.dumps(st.session_state.diagnostic_question_timings)

                    # Garantir que todas as colunas base existem no novo_diagnostico_data
                    for col_base_diag in colunas_base_diagnosticos:
                        if col_base_diag not in novo_diagnostico_data:
                             novo_diagnostico_data[col_base_diag] = pd.NA # Ou um default apropriado

                    # Adicionar colunas de categoria de média se não existirem no df_diagnosticos_existente
                    for cat_col_key in medias_por_categoria.keys():
                        if cat_col_key not in df_diagnosticos_existente.columns:
                            df_diagnosticos_existente[cat_col_key] = pd.NA


                    # Garantir que todas as colunas do novo diagnóstico existam no DataFrame principal
                    for col_novo in novo_diagnostico_data.keys():
                        if col_novo not in df_diagnosticos_existente.columns:
                            df_diagnosticos_existente[col_novo] = pd.NA # Adiciona a coluna com NA se não existir

                    df_novo_diagnostico_linha = pd.DataFrame([novo_diagnostico_data])
                    df_diagnosticos_final = pd.concat([df_diagnosticos_existente, df_novo_diagnostico_linha], ignore_index=True)
                    
                    # Assegurar tipos corretos antes de salvar, especialmente para numéricos
                    cols_to_numeric_on_save = ['Média Geral', 'GUT Média'] + [col for col in df_diagnosticos_final.columns if col.startswith("Media_Cat_") or col.startswith("GUT_")]
                    for col_num_save in cols_to_numeric_on_save:
                        if col_num_save in df_diagnosticos_final.columns:
                            df_diagnosticos_final[col_num_save] = pd.to_numeric(df_diagnosticos_final[col_num_save], errors='coerce')

                    df_diagnosticos_final.to_csv(arquivo_csv, index=False, encoding='utf-8')
                    
                    # Atualizar contagem de diagnósticos realizados
                    current_total_realizados = st.session_state.user.get('TotalDiagnosticosRealizados', 0)
                    update_user_data(st.session_state.cnpj, "TotalDiagnosticosRealizados", current_total_realizados + 1)


                    st.session_state.diagnostico_enviado_sucesso = True
                    st.session_state.respostas_atuais_diagnostico = {} # Limpa para próximo
                    st.session_state.progresso_diagnostico_percentual = 0
                    st.session_state.progresso_diagnostico_contagem = (0, total_perguntas)
                    st.session_state.diagnostic_question_timings = {}


                    # Preparar para Pesquisa de Satisfação
                    st.session_state.survey_submitted_for_current_diag = False # Reset for new diag

                    st.success("Diagnóstico enviado com sucesso! Você será redirecionado.")
                    st.balloons()
                    time.sleep(1.5) # Pequena pausa para o usuário ver a mensagem

                    # Gerar PDF após salvar
                    pdf_path, pdf_filename_gen = gerar_pdf_diagnostico_completo(
                        novo_diagnostico_data, 
                        st.session_state.user, 
                        perguntas_df, 
                        respostas_coletadas_para_diagnostico,
                        medias_por_categoria, # Passar as médias calculadas
                        df_analises_perguntas
                    )
                    st.session_state.pdf_gerado_path = pdf_path
                    st.session_state.pdf_gerado_filename = pdf_filename_gen

                    # Redirecionar para Pesquisa de Satisfação se houver perguntas ativas
                    df_perguntas_pesquisa_ativas = carregar_pesquisa_perguntas()
                    df_perguntas_pesquisa_ativas = df_perguntas_pesquisa_ativas[df_perguntas_pesquisa_ativas['Ativa'] == True]
                    if not df_perguntas_pesquisa_ativas.empty:
                        st.session_state.cliente_page = "Pesquisa de Satisfação"
                    else:
                        st.session_state.cliente_page = "Painel Principal" # Ou direto para o painel
                    st.rerun()

        pass
    elif st.session_state.cliente_page == "Painel Principal":
        # ... (código da página Painel Principal)
        st.markdown("## 🏠 Painel Principal do Cliente")
        st.markdown("---")

        if st.session_state.get("diagnostico_enviado_sucesso") and st.session_state.get("pdf_gerado_path"):
            st.success("Seu diagnóstico mais recente foi processado!")
            try:
                with open(st.session_state.pdf_gerado_path, "rb") as pdf_file_rb:
                    st.download_button(
                        label=f"📄 Baixar PDF do Último Diagnóstico ({st.session_state.pdf_gerado_filename})",
                        data=pdf_file_rb,
                        file_name=st.session_state.pdf_gerado_filename,
                        mime="application/octet-stream",
                        key="download_pdf_pos_envio_v24"
                    )
            except Exception as e_dl:
                st.error(f"Erro ao disponibilizar PDF para download: {e_dl}")
            st.session_state.diagnostico_enviado_sucesso = False # Reset flag
            # st.session_state.pdf_gerado_path = None # Clear path after download attempt
            # st.session_state.pdf_gerado_filename = None

        st.markdown("### Seus Diagnósticos Realizados")
        try:
            df_diagnosticos_cliente = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str, 'ID_Diagnostico': str})
            df_diagnosticos_cliente = df_diagnosticos_cliente[df_diagnosticos_cliente['CNPJ'] == st.session_state.cnpj]
            df_diagnosticos_cliente['Data'] = pd.to_datetime(df_diagnosticos_cliente['Data']).dt.strftime('%d/%m/%Y %H:%M')
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df_diagnosticos_cliente = pd.DataFrame()
        except Exception as e_load_diag_cli:
            st.error(f"Erro ao carregar seus diagnósticos: {e_load_diag_cli}")
            df_diagnosticos_cliente = pd.DataFrame()

        if df_diagnosticos_cliente.empty:
            st.info("Você ainda não realizou nenhum diagnóstico.")
        else:
            df_display_cliente = df_diagnosticos_cliente[['Data', 'Média Geral', 'GUT Média', 'ID_Diagnostico']].copy()
            df_display_cliente.columns = ['Data Realização', 'Média Geral', 'Score Prioridade (GUT)', 'ID Diagnóstico']
            df_display_cliente = df_display_cliente.sort_values(by='Data Realização', ascending=False)
            
            st.dataframe(df_display_cliente, use_container_width=True, hide_index=True)

            diagnosticos_options = {f"{row['Data Realização']} (ID: ...{row['ID_Diagnostico'][-6:]})": row['ID_Diagnostico'] for index, row in df_display_cliente.iterrows()}
            
            if diagnosticos_options:
                selected_diag_display_name = st.selectbox(
                    "Selecione um diagnóstico para ver detalhes ou baixar o PDF:",
                    options=list(diagnosticos_options.keys()),
                    index=0,
                    key="select_diag_details_cli_v24"
                )
                selected_id_diagnostico_cli = diagnosticos_options[selected_diag_display_name]
                
                diag_data_selecionado_cli = df_diagnosticos_cliente[df_diagnosticos_cliente['ID_Diagnostico'] == selected_id_diagnostico_cli].iloc[0].to_dict()

                st.markdown(f"#### Detalhes do Diagnóstico: {selected_diag_display_name}")
                
                # Preparar dados para o radar chart e GUT bar chart
                perguntas_base_df_cli = pd.read_csv(perguntas_csv, encoding='utf-8')
                
                # Radar Chart (Médias por Categoria)
                medias_cat_selecionado = {
                    col.replace("Media_Cat_", "").replace("_", " "): pd.to_numeric(diag_data_selecionado_cli.get(col), errors='coerce')
                    for col in diag_data_selecionado_cli if col.startswith("Media_Cat_") and pd.notna(diag_data_selecionado_cli.get(col))
                }
                if medias_cat_selecionado:
                    radar_fig_cli = create_radar_chart(medias_cat_selecionado, title="Performance por Categoria")
                    if radar_fig_cli: st.plotly_chart(radar_fig_cli, use_container_width=True)
                    else: st.caption("Não foi possível gerar o gráfico radar (dados insuficientes).")

                # GUT Bar Chart (Top prioridades)
                gut_data_list_cli = []
                for _, p_row in perguntas_base_df_cli.iterrows():
                    p_col_name_gut = f"GUT_{sanitize_column_name(p_row['Pergunta'])}"
                    if p_col_name_gut in diag_data_selecionado_cli and pd.notna(diag_data_selecionado_cli[p_col_name_gut]):
                        gut_data_list_cli.append({'Tarefa': p_row['Pergunta'], 'Score': pd.to_numeric(diag_data_selecionado_cli[p_col_name_gut],errors='coerce')})
                
                if gut_data_list_cli:
                    gut_fig_cli = create_gut_barchart(gut_data_list_cli, title="Principais Pontos de Atenção (GUT)")
                    if gut_fig_cli: st.plotly_chart(gut_fig_cli, use_container_width=True)
                    else: st.caption("Não foi possível gerar o gráfico de prioridades GUT.")


                if st.button(f"📄 Gerar e Baixar PDF do Diagnóstico Selecionado", key=f"download_pdf_selecionado_{selected_id_diagnostico_cli}_v24"):
                    respostas_coletadas_pdf_cli = {}
                    for _, p_row_pdf in perguntas_base_df_cli.iterrows():
                        p_col_name_pdf = sanitize_column_name(p_row_pdf['Pergunta'])
                        if p_col_name_pdf in diag_data_selecionado_cli and pd.notna(diag_data_selecionado_cli[p_col_name_pdf]):
                            respostas_coletadas_pdf_cli[p_row_pdf['Pergunta']] = diag_data_selecionado_cli[p_col_name_pdf]
                    
                    df_analises_geral_pdf = carregar_analises_perguntas()
                    
                    pdf_path_sel, pdf_filename_sel = gerar_pdf_diagnostico_completo(
                        diag_data_selecionado_cli, 
                        st.session_state.user, 
                        perguntas_base_df_cli, 
                        respostas_coletadas_pdf_cli,
                        medias_cat_selecionado,
                        df_analises_geral_pdf
                    )
                    if pdf_path_sel and pdf_filename_sel:
                        with open(pdf_path_sel, "rb") as f_pdf_sel:
                            st.download_button(
                                label=f"Clique para baixar: {pdf_filename_sel}",
                                data=f_pdf_sel,
                                file_name=pdf_filename_sel,
                                mime="application/pdf",
                                key=f"dl_btn_sel_{selected_id_diagnostico_cli}_v24_exec"
                            )
                        st.success(f"PDF '{pdf_filename_sel}' pronto para download!")
                    else:
                        st.error("Não foi possível gerar o PDF para este diagnóstico.")

                with st.expander("Ver Respostas e Comentários Detalhados", expanded=False):
                    st.write(f"**ID do Diagnóstico:** {diag_data_selecionado_cli.get('ID_Diagnostico', 'N/A')}")
                    st.write(f"**Data:** {diag_data_selecionado_cli.get('Data', 'N/A')}")
                    st.write(f"**Média Geral:** {diag_data_selecionado_cli.get('Média Geral', 'N/A'):.2f}")
                    st.write(f"**GUT Médio:** {diag_data_selecionado_cli.get('GUT Média', 'N/A'):.2f}")
                    if pd.notna(diag_data_selecionado_cli.get('Diagnóstico')) and diag_data_selecionado_cli.get('Diagnóstico'):
                        st.markdown("**Diagnóstico (Admin/Sistema):**")
                        st.markdown(f"> _{diag_data_selecionado_cli['Diagnóstico']}_")
                    if pd.notna(diag_data_selecionado_cli.get('Análise do Cliente')) and diag_data_selecionado_cli.get('Análise do Cliente'):
                        st.markdown("**Sua Análise/Comentários:**")
                        st.markdown(f"> _{diag_data_selecionado_cli['Análise do Cliente']}_")
                    if pd.notna(diag_data_selecionado_cli.get('Observações')) and diag_data_selecionado_cli.get('Observações'):
                        st.markdown("**Observações Gerais (do formulário):**")
                        st.markdown(f"> _{diag_data_selecionado_cli['Observações']}_")
                    if pd.notna(diag_data_selecionado_cli.get('Comentarios_Admin')) and diag_data_selecionado_cli.get('Comentarios_Admin'):
                        st.markdown("**Comentários Adicionais do Administrador:**")
                        st.markdown(f"> _{diag_data_selecionado_cli['Comentarios_Admin']}_")
        pass
    elif st.session_state.cliente_page == "Suporte/FAQ":
        # ... (código da página Suporte/FAQ)
        st.markdown("## 💬 Suporte e Perguntas Frequentes (FAQ)")
        st.markdown("---")

        df_faq_full = carregar_faq()

        if df_faq_full.empty:
            st.info("Nenhuma pergunta frequente cadastrada no momento.")
        else:
            faq_categories = ["Todas"] + sorted(df_faq_full['CategoriaFAQ'].unique().tolist())
            
            col_filter1, col_filter2 = st.columns([1,2])
            with col_filter1:
                st.session_state.selected_faq_category = st.selectbox(
                    "Filtrar por Categoria:", 
                    options=faq_categories, 
                    index=faq_categories.index(st.session_state.get("selected_faq_category", "Todas")),
                    key="faq_cat_select_v24"
                )
            with col_filter2:
                st.session_state.search_faq_query = st.text_input(
                    "Buscar por palavra-chave:", 
                    value=st.session_state.get("search_faq_query", ""),
                    key="faq_search_v24"
                ).lower()

            df_faq_filtered = df_faq_full.copy()
            if st.session_state.selected_faq_category != "Todas":
                df_faq_filtered = df_faq_filtered[df_faq_filtered['CategoriaFAQ'] == st.session_state.selected_faq_category]
            
            if st.session_state.search_faq_query:
                df_faq_filtered = df_faq_filtered[
                    df_faq_filtered['PerguntaFAQ'].str.lower().str.contains(st.session_state.search_faq_query, na=False) |
                    df_faq_filtered['RespostaFAQ'].str.lower().str.contains(st.session_state.search_faq_query, na=False)
                ]

            if df_faq_filtered.empty:
                st.warning("Nenhuma pergunta encontrada para os filtros aplicados.")
            else:
                for _, row_faq in df_faq_filtered.iterrows():
                    faq_id = row_faq['ID_FAQ']
                    pergunta_faq = row_faq['PerguntaFAQ']
                    resposta_faq = row_faq['RespostaFAQ']
                    
                    is_selected = (st.session_state.get("selected_faq_id") == faq_id)
                    
                    if st.button(f"{'➖' if is_selected else '➕'} {pergunta_faq}", key=f"faq_btn_{faq_id}_v24", use_container_width=True):
                        if is_selected:
                            st.session_state.selected_faq_id = None # Desseleciona/Colapsa
                        else:
                            st.session_state.selected_faq_id = faq_id # Seleciona/Expande
                        st.rerun() # Rerun para atualizar o estado do botão e a exibição da resposta
                    
                    if is_selected:
                        st.markdown(f"<div class='faq-answer'>{resposta_faq}</div>", unsafe_allow_html=True)
        pass
    elif st.session_state.cliente_page == "Pesquisa de Satisfação":
        # ... (código da página Pesquisa de Satisfação)
        st.markdown("## 🌟 Pesquisa de Satisfação")
        st.markdown("---")
        
        id_diagnostico_para_pesquisa = st.session_state.get("survey_id_diagnostico_associado")

        if not id_diagnostico_para_pesquisa:
            st.info("Você precisa completar um diagnóstico primeiro para acessar a pesquisa de satisfação relacionada a ele.")
            if st.button("Voltar ao Painel", key="back_to_panel_from_survey_no_id"):
                st.session_state.cliente_page = "Painel Principal"
                st.rerun()
            st.stop()

        # Verificar se já respondeu para este diagnóstico
        df_respostas_anteriores = carregar_pesquisa_respostas()
        if not df_respostas_anteriores.empty and \
           id_diagnostico_para_pesquisa in df_respostas_anteriores['ID_Diagnostico_Associado'].astype(str).values:
            st.success("Obrigado! Você já respondeu à pesquisa de satisfação para este diagnóstico.")
            st.session_state.survey_submitted_for_current_diag = True # Marca como submetido
            if st.button("Ir para o Painel Principal", key="goto_main_from_survey_submitted"):
                st.session_state.cliente_page = "Painel Principal"
                st.rerun()
            st.stop()


        df_perguntas_pesquisa = carregar_pesquisa_perguntas()
        df_perguntas_pesquisa_ativas = df_perguntas_pesquisa[df_perguntas_pesquisa['Ativa'] == True].sort_values(by="Ordem")

        if df_perguntas_pesquisa_ativas.empty:
            st.info("Nenhuma pergunta de satisfação ativa no momento. Obrigado!")
            if st.button("Ir para o Painel Principal", key="goto_main_from_survey_no_active_q"):
                st.session_state.cliente_page = "Painel Principal"
                st.rerun()
            st.stop()

        st.markdown("Sua opinião é muito importante para nós! Por favor, dedique um momento para responder a esta breve pesquisa sobre sua experiência com o diagnóstico.")

        with st.form("form_pesquisa_satisfacao_cliente_v24"):
            for _, row_p_pesq in df_perguntas_pesquisa_ativas.iterrows():
                id_p_pesq = row_p_pesq['ID_PerguntaPesquisa']
                texto_p_pesq = row_p_pesq['TextoPerguntaPesquisa']
                tipo_resp_pesq = row_p_pesq['TipoRespostaPesquisa']
                opcoes_json_pesq = row_p_pesq['OpcoesRespostaJSON']
                
                st.markdown(f"**{texto_p_pesq}**")
                
                current_resp = st.session_state.current_survey_responses.get(id_p_pesq)

                if tipo_resp_pesq == "Escala (1-5)":
                    st.session_state.current_survey_responses[id_p_pesq] = st.slider("", 1, 5, value=current_resp if current_resp else 3, key=f"survey_{id_p_pesq}_slider", label_visibility="collapsed")
                elif tipo_resp_pesq == "Texto":
                    st.session_state.current_survey_responses[id_p_pesq] = st.text_area("", value=current_resp if current_resp else "", key=f"survey_{id_p_pesq}_text", label_visibility="collapsed")
                elif tipo_resp_pesq == "Múltipla Escolha (Única)" or tipo_resp_pesq == "Seleção Única":
                    try:
                        opcoes_list = json.loads(opcoes_json_pesq) if pd.notna(opcoes_json_pesq) else []
                        if opcoes_list:
                            st.session_state.current_survey_responses[id_p_pesq] = st.radio("", options=opcoes_list, index=opcoes_list.index(current_resp) if current_resp and current_resp in opcoes_list else 0, key=f"survey_{id_p_pesq}_radio", label_visibility="collapsed")
                        else: st.caption("Opções não configuradas.")
                    except json.JSONDecodeError: st.caption("Erro nas opções.")
                st.markdown("---")

            submitted_pesquisa = st.form_submit_button("Enviar Respostas da Pesquisa", type="primary", use_container_width=True)

            if submitted_pesquisa:
                user_info = st.session_state.user
                nova_resposta_pesquisa = {
                    "ID_SessaoRespostaPesquisa": str(uuid.uuid4()),
                    "CNPJ_Cliente": st.session_state.cnpj,
                    "TimestampPreenchimento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "NomeClientePreenchimento": user_info.get("NomeContato", "N/D"),
                    "TelefoneClientePreenchimento": user_info.get("Telefone", "N/D"),
                    "EmpresaClientePreenchimento": user_info.get("Empresa", "N/D"),
                    "ID_Diagnostico_Associado": id_diagnostico_para_pesquisa,
                    "RespostasJSON": json.dumps(st.session_state.current_survey_responses)
                }
                
                df_respostas_pesquisa_existente = carregar_pesquisa_respostas()
                df_nova_resposta_linha = pd.DataFrame([nova_resposta_pesquisa])
                df_respostas_final = pd.concat([df_respostas_pesquisa_existente, df_nova_resposta_linha], ignore_index=True)
                
                salvar_pesquisa_respostas(df_respostas_final)
                
                st.session_state.survey_submitted_for_current_diag = True
                st.session_state.current_survey_responses = {} # Limpar
                
                st.success("Obrigado por suas respostas! Sua opinião é valiosa.")
                st.balloons()
                time.sleep(1.5)
                st.session_state.cliente_page = "Painel Principal" # Redireciona
                st.rerun()
        pass
    elif st.session_state.cliente_page == "Notificações":
        # ... (código da página Notificações)
        st.markdown("## 🔔 Suas Notificações")
        st.markdown("---")

        try:
            df_notificacoes_todas = pd.read_csv(notificacoes_csv, encoding='utf-8', dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Relacionado': str})
            if 'Lida' in df_notificacoes_todas.columns:
                 df_notificacoes_todas['Lida'] = df_notificacoes_todas['Lida'].apply(robust_str_to_bool)
            else: # Adiciona a coluna Lida se não existir, default para False
                df_notificacoes_todas['Lida'] = False

            df_notificacoes_cliente = df_notificacoes_todas[df_notificacoes_todas['CNPJ_Cliente'] == st.session_state.cnpj].copy()
            df_notificacoes_cliente.sort_values(by="Timestamp", ascending=False, inplace=True)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df_notificacoes_cliente = pd.DataFrame()
        except Exception as e_load_notif:
            st.error(f"Erro ao carregar notificações: {e_load_notif}")
            df_notificacoes_cliente = pd.DataFrame()

        if df_notificacoes_cliente.empty:
            st.info("Você não tem nenhuma notificação no momento.")
        else:
            alguma_notificacao_marcada_como_lida = False
            for index, row_notif in df_notificacoes_cliente.iterrows():
                card_border_style = "border-left: 5px solid #2563eb;" # Azul para não lida
                if row_notif['Lida']:
                    card_border_style = "border-left: 5px solid #9ca3af;" # Cinza para lida
                
                st.markdown(f"""
                <div class="custom-card" style="{card_border_style}">
                    <p style="font-size:0.8em; color:#555;">{pd.to_datetime(row_notif['Timestamp']).strftime('%d/%m/%Y %H:%M')}
                        {' <span style="color:green; font-weight:bold;">(Nova)</span>' if not row_notif['Lida'] else ''}
                    </p>
                    <h4>{pdf_safe_text_output(row_notif.get('Mensagem', 'Mensagem indisponível'))}</h4>
                """, unsafe_allow_html=True)
                
                id_diag_rel = row_notif.get('ID_Diagnostico_Relacionado')
                if pd.notna(id_diag_rel) and id_diag_rel.strip():
                    if st.button(f"Ver Diagnóstico Relacionado (ID: ...{id_diag_rel[-6:]})", key=f"ver_diag_notif_{row_notif['ID_Notificacao']}_v24"):
                        # Lógica para ir ao painel e destacar o diagnóstico
                        st.session_state.target_diag_data_for_expansion = id_diag_rel 
                        st.session_state.cliente_page = "Painel Principal"
                        if not row_notif['Lida']:
                            df_notificacoes_todas.loc[df_notificacoes_todas['ID_Notificacao'] == row_notif['ID_Notificacao'], 'Lida'] = True
                            alguma_notificacao_marcada_como_lida = True
                        st.rerun()

                if not row_notif['Lida']:
                    if st.button("Marcar como Lida", key=f"mark_read_{row_notif['ID_Notificacao']}_v24", help="Remove o destaque de 'Nova'"):
                        df_notificacoes_todas.loc[df_notificacoes_todas['ID_Notificacao'] == row_notif['ID_Notificacao'], 'Lida'] = True
                        alguma_notificacao_marcada_como_lida = True
                        st.rerun() # Rerun para atualizar a exibição e o contador no menu
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            if alguma_notificacao_marcada_como_lida:
                df_notificacoes_todas.to_csv(notificacoes_csv, index=False, encoding='utf-8')
                st.session_state.force_sidebar_rerun_after_notif_read_v19 = True # Força atualização do contador na sidebar
                # O rerun já acontece dentro do botão "Marcar como Lida"

        if st.session_state.get("force_sidebar_rerun_after_notif_read_v19"):
            st.session_state.force_sidebar_rerun_after_notif_read_v19 = False # Reset flag
            # Este rerun é para garantir que o contador da sidebar atualize
            # Pode ser redundante se o rerun do botão já faz isso efetivamente.
            st.experimental_rerun() # Usar com cautela
        pass


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_text_key_v24_final_sess"
    WIDGET_KEY_SB_ADMIN_MENU = "sb_admin_menu_v24_final_widget_key"

    admin_logo_path_sidebar = CUSTOM_LOGIN_LOGO_PATH if os.path.exists(CUSTOM_LOGIN_LOGO_PATH) else DEFAULT_LOGIN_LOGO_PATH
    if os.path.exists(admin_logo_path_sidebar):
        st.sidebar.image(admin_logo_path_sidebar, use_container_width=True, width=150)
    else:
        st.sidebar.markdown("### Painel Admin")

    st.sidebar.success(f"🟢 Admin Logado: {st.session_state.admin_user_details.get('Usuario', '')}")

    def has_admin_permission(permission_key):
        if 'admin_user_details' in st.session_state and st.session_state.admin_user_details is not None:
            # For the master admin "admin", all permissions are always True conceptually.
            if st.session_state.admin_user_details.get('Usuario') == 'admin':
                return True
            return robust_str_to_bool(st.session_state.admin_user_details.get(permission_key, False))
        return False

    if st.sidebar.button("Sair do Painel Admin", icon="🚪", key="logout_admin_v24_final_button", use_container_width=True): # CHAVE ATUALIZADA
        admin_keys_to_clear = ["admin_logado", "admin_user_details", SESSION_KEY_FOR_ADMIN_PAGE]
        for key_adm_clear in admin_keys_to_clear: # Renomeada variável de loop
            if key_adm_clear in st.session_state:
                del st.session_state[key_adm_clear]
        st.session_state.admin_logado = False
        st.session_state.admin_user_details = None
        st.toast("Logout de admin realizado.", icon="👋")
        st.rerun()

    menu_admin_options_map = {
        "Visão Geral e Diagnósticos": ("📊", "Perm_VisaoGeralDiagnosticos"),
        "Relatório de Engajamento": ("📈", "Perm_RelatorioEngajamento"),
        "Gerenciar Notificações": ("🔔", "Perm_GerenciarNotificacoes"),
        "Gerenciar Clientes": ("👥", "Perm_GerenciarClientes"),
        "Personalizar Aparência": ("🎨", "Perm_PersonalizarAparencia"),
        "Gerenciar Perguntas Diagnóstico": ("📝", "Perm_GerenciarPerguntasDiagnostico"),
        "Gerenciar Análises de Perguntas": ("💡", "Perm_GerenciarAnalises"),
        "Gerenciar FAQ/SAC": ("💬", "Perm_GerenciarFAQ"),
        "Gerenciar Perguntas da Pesquisa": ("🌟", "Perm_GerenciarPerguntasPesquisa"),
        "Resultados da Pesquisa de Satisfação": ("📋", "Perm_VerResultadosPesquisa"),
        "Gerenciar Instruções": ("⚙️", "Perm_GerenciarInstrucoes"),
        "Histórico de Usuários": ("📜", "Perm_VerHistorico"),
        "Gerenciar Administradores": ("👮", "Perm_GerenciarAdministradores")
    }

    admin_user_perms_dict = st.session_state.get("admin_user_details", {}) # Renomeada variável
    allowed_admin_pages_map = {}
    
    # Master admin 'admin' bypasses permission check for menu population
    is_master_admin_logged_in = (admin_user_perms_dict.get('Usuario') == 'admin')

    for page_name, (emoji, perm_key) in menu_admin_options_map.items():
        if is_master_admin_logged_in or robust_str_to_bool(admin_user_perms_dict.get(perm_key, False)):
            allowed_admin_pages_map[page_name] = emoji

    if not allowed_admin_pages_map:
        st.error("Você não tem permissão para acessar nenhuma funcionalidade do painel de administração.")
        #This case should ideally not be hit if master admin 'admin' always has access.
        # If a non-master admin has no permissions, this is valid.
        if not is_master_admin_logged_in :
            st.stop()
        else: # Should not happen for master 'admin'
            st.warning("Superusuário 'admin' detectado mas sem páginas permitidas. Verifique a lógica de permissões.")


    admin_page_text_keys = list(allowed_admin_pages_map.keys())
    admin_options_for_display = [f"{allowed_admin_pages_map[key_disp]} {key_disp}" for key_disp in admin_page_text_keys] # Renomeada


    def admin_menu_on_change_final_v24(): # CHAVE ATUALIZADA
        selected_display_value = st.session_state.get(WIDGET_KEY_SB_ADMIN_MENU)
        if selected_display_value is None: return

        new_text_key = None
        for text_key_iter, emoji_iter in allowed_admin_pages_map.items():
            if f"{emoji_iter} {text_key_iter}" == selected_display_value:
                new_text_key = text_key_iter
                break
        if new_text_key and new_text_key != st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE):
            st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = new_text_key

    if SESSION_KEY_FOR_ADMIN_PAGE not in st.session_state or \
       st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE) not in admin_page_text_keys:
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0] if admin_page_text_keys else None

    current_admin_page_text_key_for_index = st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE)
    current_admin_menu_index = 0

    if current_admin_page_text_key_for_index and admin_options_for_display:
        try:
            expected_display_value_for_current_page = f"{allowed_admin_pages_map.get(current_admin_page_text_key_for_index, '')} {current_admin_page_text_key_for_index}"
            current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
        except (ValueError, KeyError):
            if admin_page_text_keys:
                st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]
                # current_admin_page_text_key_for_index = admin_page_text_keys[0] # No re-assignment here, rerun will pick it up
                # expected_display_value_for_current_page = f"{allowed_admin_pages_map[current_admin_page_text_key_for_index]} {current_admin_page_text_key_for_index}"
                # current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
                st.rerun() # Rerun if current page is somehow invalid
            else:
                current_admin_page_text_key_for_index = None


    if admin_options_for_display:
        st.sidebar.selectbox(
            "Funcionalidades Admin:",
            options=admin_options_for_display,
            index=current_admin_menu_index,
            key=WIDGET_KEY_SB_ADMIN_MENU,
            on_change=admin_menu_on_change_final_v24 # CHAVE ATUALIZADA
        )

    menu_admin = st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE)

    if menu_admin and menu_admin in allowed_admin_pages_map:
        header_display_name = f"{allowed_admin_pages_map.get(menu_admin, '❓')} {menu_admin}"
        st.header(header_display_name)
    elif admin_page_text_keys : # If current menu_admin is invalid but there are options
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]
        st.rerun()
    else: # No pages available at all (even after considering master admin)
        st.error("Acesso negado ou nenhuma funcionalidade disponível. Contate o suporte se você for 'admin'.")
        st.stop()

    df_usuarios_admin_geral = pd.DataFrame(columns=colunas_base_usuarios)
    try:
        df_usuarios_admin_temp_load = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
        if "DiagnosticosDisponiveis" not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load["DiagnosticosDisponiveis"] = 1
        df_usuarios_admin_temp_load["DiagnosticosDisponiveis"] = pd.to_numeric(df_usuarios_admin_temp_load["DiagnosticosDisponiveis"], errors='coerce').fillna(1).astype(int)
        if "TotalDiagnosticosRealizados" not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load["TotalDiagnosticosRealizados"] = 0
        df_usuarios_admin_temp_load["TotalDiagnosticosRealizados"] = pd.to_numeric(df_usuarios_admin_temp_load["TotalDiagnosticosRealizados"], errors='coerce').fillna(0).astype(int)
        if "JaVisualizouInstrucoes" not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load["JaVisualizouInstrucoes"] = "False"
        df_usuarios_admin_temp_load["JaVisualizouInstrucoes"] = df_usuarios_admin_temp_load["JaVisualizouInstrucoes"].apply(robust_str_to_bool)
        df_usuarios_admin_geral = df_usuarios_admin_temp_load
    except FileNotFoundError:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Clientes", "Gerenciar Notificações", "Relatório de Engajamento", "Personalizar Aparência", "Resultados da Pesquisa de Satisfação"]:
            st.sidebar.warning(f"Arquivo '{usuarios_csv}' não encontrado. Algumas funcionalidades podem ser limitadas.")
    except Exception as e_load_users_adm_global:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Clientes", "Gerenciar Notificações", "Relatório de Engajamento", "Personalizar Aparência", "Resultados da Pesquisa de Satisfação"]:
            st.sidebar.error(f"Erro ao carregar usuários para admin: {e_load_users_adm_global}")

    # --- Admin Page Content com Verificações de Permissão ---
    if menu_admin == "Visão Geral e Diagnósticos":
        if not has_admin_permission("Perm_VisaoGeralDiagnosticos"): st.error("Acesso negado."); st.stop()
        # ... (código da seção Visão Geral e Diagnósticos)
        pass
    elif menu_admin == "Relatório de Engajamento":
        if not has_admin_permission("Perm_RelatorioEngajamento"): st.error("Acesso negado."); st.stop()
        # ... (código da seção Relatório de Engajamento)
        pass
    elif menu_admin == "Gerenciar Notificações":
        if not has_admin_permission("Perm_GerenciarNotificacoes"): st.error("Acesso negado."); st.stop()
        # ... (código da seção Gerenciar Notificações)
        pass
    elif menu_admin == "Gerenciar Clientes":
        if not has_admin_permission("Perm_GerenciarClientes"): st.error("Acesso negado."); st.stop()
        # ... (código da seção Gerenciar Clientes)
        pass
    elif menu_admin == "Personalizar Aparência":
        if not has_admin_permission("Perm_PersonalizarAparencia"): st.error("Acesso negado."); st.stop()
        # ... (código da seção Personalizar Aparência)
        pass
    elif menu_admin == "Gerenciar Perguntas Diagnóstico":
        if not has_admin_permission("Perm_GerenciarPerguntasDiagnostico"): st.error("Acesso negado."); st.stop()
        # ... (código da seção Gerenciar Perguntas Diagnóstico)
        pass
    elif menu_admin == "Gerenciar Análises de Perguntas":
        if not has_admin_permission("Perm_GerenciarAnalises"): st.error("Acesso negado."); st.stop()
        # ... (código da seção Gerenciar Análises de Perguntas)
        pass
    elif menu_admin == "Gerenciar FAQ/SAC":
        if not has_admin_permission("Perm_GerenciarFAQ"): st.error("Acesso negado."); st.stop()
        # ... (código da seção Gerenciar FAQ/SAC)
        pass
    elif menu_admin == "Gerenciar Perguntas da Pesquisa":
        if not has_admin_permission("Perm_GerenciarPerguntasPesquisa"): st.error("Acesso negado."); st.stop()
        # ... (código da seção Gerenciar Perguntas da Pesquisa)
        pass
    elif menu_admin == "Resultados da Pesquisa de Satisfação":
        if not has_admin_permission("Perm_VerResultadosPesquisa"): st.error("Acesso negado."); st.stop()
        # ... (código da seção Resultados da Pesquisa de Satisfação)
        pass
    elif menu_admin == "Gerenciar Instruções":
        if not has_admin_permission("Perm_GerenciarInstrucoes"): st.error("Acesso negado."); st.stop()
        # ... (código da seção Gerenciar Instruções)
        pass
    elif menu_admin == "Histórico de Usuários":
        if not has_admin_permission("Perm_VerHistorico"): st.error("Acesso negado."); st.stop()
        # ... (código da seção Histórico de Usuários)
        pass
    elif menu_admin == "Gerenciar Administradores":
        if not has_admin_permission("Perm_GerenciarAdministradores"): st.error("Acesso negado."); st.stop()
        
        st.subheader("Gerenciar Contas de Administrador")
        try:
            df_admins_ga = pd.read_csv(admin_credenciais_csv, encoding='utf-8', dtype={'Usuario':str, 'Senha':str})
            # Ensure all permission columns are boolean after loading
            for perm_col_ga in ALL_ADMIN_PERMISSION_KEYS:
                if perm_col_ga not in df_admins_ga.columns:
                    df_admins_ga[perm_col_ga] = False # Should be handled by inicializar_csv
                df_admins_ga[perm_col_ga] = df_admins_ga[perm_col_ga].apply(robust_str_to_bool)
        except (FileNotFoundError, pd.errors.EmptyDataError): # Should be handled by inicializar_csv
            df_admins_ga = pd.DataFrame(columns=colunas_base_admin_credenciais)
            # If somehow empty, inicializar_csv should have created 'admin'
            # For safety, ensure 'admin' exists if df is empty here (though unlikely)
            if df_admins_ga.empty or 'admin' not in df_admins_ga['Usuario'].values:
                 admin_master_fallback = {"Usuario": "admin", "Senha": "potencialize"}
                 for pkf in ALL_ADMIN_PERMISSION_KEYS: admin_master_fallback[pkf] = True
                 for bcf in colunas_base_admin_credenciais:
                     if bcf not in admin_master_fallback: admin_master_fallback[bcf] = pd.NA
                 df_admins_ga = pd.DataFrame([admin_master_fallback], columns=colunas_base_admin_credenciais)


        st.info("Adicione, edite ou remova contas de administrador e suas permissões. "
                "O usuário 'admin' é o superadministrador e suas permissões não podem ser revogadas nem pode ser excluído.")

        with st.expander("➕ Adicionar Novo Administrador"):
            with st.form("form_add_new_admin_v24_final_form"): # Unique key for form
                st.write("##### Detalhes do Novo Administrador")
                new_admin_user = st.text_input("Usuário*", key="new_admin_user_v24_input")
                new_admin_pass = st.text_input("Senha*", type="password", key="new_admin_pass_v24_input")

                st.write("##### Permissões")
                new_admin_permissions = {}
                num_perm_cols = 3
                perm_cols_widgets = st.columns(num_perm_cols)
                col_idx = 0
                for perm_key_form in ALL_ADMIN_PERMISSION_KEYS: # Renamed var
                    perm_label = perm_key_form.replace("Perm_", "").replace("Gerenciar", "Ger. ").replace("Diagnostico", "Diag.").replace("Resultados", "Res.")
                    default_perm_val = False # New admins start with no permissions by default
                    # 'Perm_GerenciarAdministradores' should not be grantable to new users easily here if not master
                    if perm_key_form == "Perm_GerenciarAdministradores":
                         # Only allow setting this if the current user is the master 'admin' or has this perm
                         can_grant_super = (st.session_state.admin_user_details['Usuario'] == 'admin' or 
                                            robust_str_to_bool(st.session_state.admin_user_details.get("Perm_GerenciarAdministradores", False)))
                         new_admin_permissions[perm_key_form] = perm_cols_widgets[col_idx % num_perm_cols].checkbox(
                             perm_label, key=f"new_perm_{perm_key_form}_v24_cb", value=default_perm_val, disabled=not can_grant_super
                         )
                         if not can_grant_super and default_perm_val: # Should not happen with False default
                             st.caption(f"Você não pode conceder '{perm_label}'")
                    else:
                         new_admin_permissions[perm_key_form] = perm_cols_widgets[col_idx % num_perm_cols].checkbox(perm_label, key=f"new_perm_{perm_key_form}_v24_cb", value=default_perm_val)
                    col_idx += 1
                
                submitted_new_admin = st.form_submit_button("Adicionar Administrador")
                if submitted_new_admin:
                    if not new_admin_user or not new_admin_pass:
                        st.error("Usuário e Senha são obrigatórios.")
                    elif new_admin_user == 'admin':
                        st.error("O nome de usuário 'admin' é reservado para o superadministrador.")
                    elif new_admin_user in df_admins_ga["Usuario"].values:
                        st.error("Este nome de usuário de administrador já existe.")
                    else:
                        new_admin_data_row = {"Usuario": new_admin_user, "Senha": new_admin_pass} # Renamed var
                        new_admin_data_row.update(new_admin_permissions)
                        
                        # Ensure all base columns are present
                        for base_col_new in colunas_base_admin_credenciais:
                            if base_col_new not in new_admin_data_row: new_admin_data_row[base_col_new] = pd.NA
                        
                        df_new_admin_row_df = pd.DataFrame([new_admin_data_row], columns=colunas_base_admin_credenciais) # Renamed
                        df_admins_ga = pd.concat([df_admins_ga, df_new_admin_row_df], ignore_index=True)
                        
                        for perm_key_save_form in ALL_ADMIN_PERMISSION_KEYS: 
                            if perm_key_save_form in df_admins_ga.columns:
                                df_admins_ga[perm_key_save_form] = df_admins_ga[perm_key_save_form].apply(robust_str_to_bool)
                        df_admins_ga.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                        st.success(f"Administrador '{new_admin_user}' adicionado com sucesso!")
                        st.rerun()

        st.markdown("---")
        st.write("##### Editar Administradores Existentes")
        
        column_config_admins = {
            "Usuario": st.column_config.TextColumn("Usuário", disabled=True),
            "Senha": st.column_config.TextColumn("Senha (oculta)", disabled=True, help="Use a seção 'Alterar Senha' abaixo."),
        }
        # Dynamically build column_config for permissions, disabling for 'admin' user
        df_admins_display = df_admins_ga.copy()
        if "Senha" in df_admins_display.columns:
            df_admins_display["Senha"] = "********" 

        for perm_key_col_cfg in ALL_ADMIN_PERMISSION_KEYS:
            perm_label_cfg = perm_key_col_cfg.replace("Perm_", "").replace("Gerenciar", "Ger. ").replace("Diagnostico", "Diag.").replace("Resultados", "Res.")
            # Check if current user is 'admin' - this check is for display, backend will enforce
            # st.data_editor doesn't allow per-row disabling easily. So we disable for all, then enforce on save.
            # A better UX would be to show 'admin' perms as checked & disabled.
            # For now, they will appear editable but changes won't save for 'admin'.
            is_super_admin_perm_col = (perm_key_col_cfg == "Perm_GerenciarAdministradores")
            can_edit_super_perm = (st.session_state.admin_user_details['Usuario'] == 'admin' or 
                                   robust_str_to_bool(st.session_state.admin_user_details.get("Perm_GerenciarAdministradores",False)))


            column_config_admins[perm_key_col_cfg] = st.column_config.CheckboxColumn(
                perm_label_cfg, 
                default=False,
                # disabled=is_super_admin_perm_col and not can_edit_super_perm # Disabling column-wide, not row-wide
            )
        
        # Filter out the 'admin' user from direct editing in the table for permissions
        # It will be shown, but changes to its permissions will be overridden.
        # Or, create a separate display for 'admin' and editor for others.
        # For simplicity, show all, override 'admin' on save.

        edited_df_admins_ga = st.data_editor(
            df_admins_display, # Show all, including 'admin' (whose password is obfuscated)
            key="editor_admins_ga_v24_permissions_final_editor", # Unique key
            column_config=column_config_admins,
            use_container_width=True,
            num_rows="dynamic", # Allows deletion; adding new rows here is discouraged due to password
            disabled=["Usuario", "Senha"] 
        )

        if st.button("Salvar Alterações nos Administradores", key="save_admins_ga_v24_permissions_revised_button", type="primary"): # Unique key
            if edited_df_admins_ga["Usuario"].isnull().any() or (edited_df_admins_ga["Usuario"] == "").any():
                st.error("Nome de usuário não pode ser vazio (verifique linhas adicionadas/removidas).")
            elif edited_df_admins_ga["Usuario"].nunique() != len(edited_df_admins_ga["Usuario"]):
                st.error("Nomes de usuário de administrador devem ser únicos no editor.")
            else:
                processed_usernames = set()
                new_admin_list_save = [] # Renamed var
                admin_master_name_save = "admin" # Renamed var
                admin_master_pass_save = "potencialize" # Renamed var
                logged_admin_username_on_save = st.session_state.admin_user_details['Usuario'] # Renamed var
                
                # --- Start Master Admin Handling ---
                master_admin_data_save = {"Usuario": admin_master_name_save, "Senha": admin_master_pass_save}
                for perm_key_m in ALL_ADMIN_PERMISSION_KEYS: # Renamed var
                    master_admin_data_save[perm_key_m] = True # Master always has all perms
                
                original_master_row_for_cols = df_admins_ga[df_admins_ga['Usuario'] == admin_master_name_save]
                for base_col_m in colunas_base_admin_credenciais: # Renamed var
                    if base_col_m not in master_admin_data_save:
                        if not original_master_row_for_cols.empty and base_col_m in original_master_row_for_cols.columns:
                            master_admin_data_save[base_col_m] = original_master_row_for_cols.iloc[0][base_col_m]
                        else: master_admin_data_save[base_col_m] = pd.NA
                new_admin_list_save.append(master_admin_data_save)
                processed_usernames.add(admin_master_name_save)
                # --- End Master Admin Handling ---

                # Process other users from the editor
                for _, edited_row_item in edited_df_admins_ga.iterrows(): # Renamed var
                    username_item = edited_row_item['Usuario'] # Renamed var
                    if pd.isna(username_item) or username_item == "" or username_item == admin_master_name_save:
                        continue 
                    
                    if username_item in processed_usernames: continue

                    original_row_item = df_admins_ga[df_admins_ga['Usuario'] == username_item] # Renamed var
                    if original_row_item.empty:
                        st.error(f"Usuário '{username_item}' parece ter sido adicionado pelo editor. "
                                 "Use o formulário 'Adicionar Novo Administrador' para definir uma senha.")
                        st.stop()

                    current_admin_data_item = original_row_item.iloc[0].to_dict() # Renamed var
                    for perm_key_item in ALL_ADMIN_PERMISSION_KEYS: # Renamed var
                        # Critical: Perm_GerenciarAdministradores can only be removed by 'admin' or another superuser
                        is_this_super_perm = (perm_key_item == "Perm_GerenciarAdministradores")
                        edited_perm_value = robust_str_to_bool(edited_row_item.get(perm_key_item, False))

                        if is_this_super_perm and current_admin_data_item[perm_key_item] and not edited_perm_value: # Attempt to remove superuser
                            if logged_admin_username_on_save != admin_master_name_save and not robust_str_to_bool(st.session_state.admin_user_details.get("Perm_GerenciarAdministradores", False)):
                                st.warning(f"Você ({logged_admin_username_on_save}) não tem permissão para remover 'Perm_GerenciarAdministradores' de '{username_item}'. Alteração ignorada.")
                                current_admin_data_item[perm_key_item] = True # Keep it True
                                continue # Skip to next permission
                        current_admin_data_item[perm_key_item] = edited_perm_value
                    
                    new_admin_list_save.append(current_admin_data_item)
                    processed_usernames.add(username_item)

                final_df_to_save_admins = pd.DataFrame(new_admin_list_save, columns=colunas_base_admin_credenciais) # Renamed
                
                for perm_key_final_bool in ALL_ADMIN_PERMISSION_KEYS: # Renamed var
                    if perm_key_final_bool in final_df_to_save_admins.columns:
                         final_df_to_save_admins[perm_key_final_bool] = final_df_to_save_admins[perm_key_final_bool].apply(robust_str_to_bool)
                    else: final_df_to_save_admins[perm_key_final_bool] = False 

                # --- Safety check: Logged-in admin (if not master) losing their own super permission ---
                if logged_admin_username_on_save != admin_master_name_save:
                    logged_admin_row_after_edit_check = final_df_to_save_admins[final_df_to_save_admins['Usuario'] == logged_admin_username_on_save] # Renamed
                    if not logged_admin_row_after_edit_check.empty:
                        if not robust_str_to_bool(logged_admin_row_after_edit_check.iloc[0]['Perm_GerenciarAdministradores']):
                            # Check if any other superuser (including master) remains
                            any_other_super_admin_exists = final_df_to_save_admins[
                                final_df_to_save_admins['Perm_GerenciarAdministradores'].apply(robust_str_to_bool) == True
                            ]
                            if any_other_super_admin_exists.empty :
                                 st.error(f"Não é possível remover a permissão 'Gerenciar Administradores' de '{logged_admin_username_on_save}' "
                                         f"pois não haveria outros administradores com esta capacidade. A permissão do superadministrador '{admin_master_name_save}' é protegida.")
                                 st.stop()
                    # else: logged in admin was deleted - should be caught if it's the master. If not master, this is an issue.
                    # This case is less likely now as master deletion is prevented.
                # --- End safety check ---

                final_df_to_save_admins.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                st.success("Lista de administradores e suas permissões atualizada!")
                
                updated_admin_details_row_session = final_df_to_save_admins[final_df_to_save_admins['Usuario'] == logged_admin_username_on_save] # Renamed
                if not updated_admin_details_row_session.empty:
                    st.session_state.admin_user_details = updated_admin_details_row_session.iloc[0].to_dict()
                st.rerun()

        st.markdown("---")
        st.subheader("Alterar Senha de Administrador")
        with st.form("form_change_admin_password_v24_final_form"): # Unique key
            df_admins_current_ga_pw = pd.read_csv(admin_credenciais_csv, encoding='utf-8', dtype={'Usuario':str, 'Senha':str}) # Renamed
            admins_list_cp_pw = df_admins_current_ga_pw["Usuario"].tolist() # Renamed
            if not admins_list_cp_pw:
                st.info("Nenhum administrador cadastrado para alterar senha.")
            else:
                # Prevent changing 'admin' password here if logged-in user is not 'admin' itself.
                # 'admin's password is 'potencialize' and enforced by inicializar_csv and save logic above.
                # This form is more for other admins.
                options_for_pw_change = [u for u in admins_list_cp_pw if u != 'admin']
                if st.session_state.admin_user_details['Usuario'] == 'admin': # If master is logged in, they can change their own (it will be reset)
                    options_for_pw_change.insert(0, 'admin')


                if not options_for_pw_change:
                     st.info("Nenhum outro administrador disponível para alteração de senha por você, ou você é o único admin.")
                else:
                    selected_admin_for_pw_change = st.selectbox(
                        "Selecione o Administrador (a senha de 'admin' é protegida):", 
                        options_for_pw_change, 
                        key="admin_select_pw_change_v24_select" # Unique key
                    )
                    new_password_for_admin = st.text_input("Nova Senha:", type="password", key="admin_new_pw_v24_input_pw")
                    confirm_new_password_for_admin = st.text_input("Confirme a Nova Senha:", type="password", key="admin_confirm_new_pw_v24_input_pw_confirm")

                    if st.form_submit_button("Alterar Senha"):
                        if selected_admin_for_pw_change == 'admin' and st.session_state.admin_user_details['Usuario'] != 'admin':
                             st.error("Você não pode alterar a senha do superadministrador 'admin'.")
                        elif not new_password_for_admin:
                            st.error("A nova senha não pode ser vazia.")
                        elif new_password_for_admin != confirm_new_password_for_admin:
                            st.error("As senhas não coincidem.")
                        else:
                            admin_index_to_update_pw = df_admins_current_ga_pw[df_admins_current_ga_pw["Usuario"] == selected_admin_for_pw_change].index # Renamed
                            if not admin_index_to_update_pw.empty:
                                # If changing 'admin's password, it will be reset to 'potencialize' by other mechanisms.
                                # This change here would be temporary if 'admin' is selected.
                                df_admins_current_ga_pw.loc[admin_index_to_update_pw, "Senha"] = new_password_for_admin
                                df_admins_current_ga_pw.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                                st.success(f"Senha do administrador '{selected_admin_for_pw_change}' alterada com sucesso!")
                                if selected_admin_for_pw_change == 'admin':
                                    st.warning("A senha do usuário 'admin' foi alterada, mas será redefinida para 'potencialize' automaticamente para manter a segurança do superusuário.")
                                st.rerun()
                            else:
                                st.error("Administrador não encontrado.")
    else:
        st.warning(f"Página administrativa '{menu_admin}' não reconhecida ou sem conteúdo definido.")

# Fallback final
if 'aba' not in locals() and not st.session_state.admin_logado and not st.session_state.cliente_logado:
    st.info("Por favor, selecione seu tipo de acesso para iniciar ou complete o login.")
    if not st.session_state.get("tipo_usuario_radio_v24_login_selection"): #Check if radio was ever rendered
        st.session_state.login_selection_aba = "Cliente" # Default if state is completely lost
    st.stop()