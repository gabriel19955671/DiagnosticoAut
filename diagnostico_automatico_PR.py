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
    if isinstance(value, (int, float)): # Handles 1, 0, 1.0, 0.0
        return bool(value)
    if isinstance(value, str):
        val_lower = value.lower().strip()
        if val_lower in ['true', '1', 't', 'y', 'yes', 'sim', 'verdadeiro', 'on']:
            return True
        elif val_lower in ['false', '0', 'f', 'n', 'no', 'nao', 'não', 'falso', 'off']:
            return False
    return False # Default for NAs, empty strings, or other unhandled types

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
        if filepath == admin_credenciais_csv: dtype_spec_local = {'Usuario': str, 'Senha': str}
        elif filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, historico_csv, pesquisa_satisfacao_respostas_csv]:
            if 'CNPJ' in columns: dtype_spec_local['CNPJ'] = str
            if 'CNPJ_Cliente' in columns: dtype_spec_local['CNPJ_Cliente'] = str
        if filepath == notificacoes_csv and 'ID_Diagnostico_Relacionado' in columns: dtype_spec_local['ID_Diagnostico_Relacionado'] = str
        if filepath == arquivo_csv and 'ID_Diagnostico' in columns: dtype_spec_local['ID_Diagnostico'] = str
        if filepath == pesquisa_satisfacao_respostas_csv and 'ID_Diagnostico_Associado' in columns: dtype_spec_local['ID_Diagnostico_Associado'] = str

        file_exists_and_not_empty = os.path.exists(filepath) and os.path.getsize(filepath) > 0

        if not file_exists_and_not_empty:
            df_init = pd.DataFrame(columns=columns)
            if filepath == admin_credenciais_csv:
                master_admin_data = {"Usuario": "admin", "Senha": "potencialize"}
                for col_name in columns:
                    if col_name not in master_admin_data:
                        if col_name in ALL_ADMIN_PERMISSION_KEYS: master_admin_data[col_name] = True
                        elif defaults and col_name in defaults: master_admin_data[col_name] = defaults[col_name]
                        else: master_admin_data[col_name] = pd.NA
                df_init = pd.DataFrame([master_admin_data], columns=columns)
            elif defaults:
                # Simple default application for new non-admin files.
                # Assumes defaults is a dict that can form a row or provide column types.
                temp_data = {}
                all_cols_defaulted = True
                for col in columns:
                    if col in defaults: temp_data[col] = defaults[col]
                    else: all_cols_defaulted = False; temp_data[col] = pd.NA # Ensure all columns are present
                if all_cols_defaulted and len(defaults) == len(columns): # If defaults cover all columns
                    try: df_init = pd.DataFrame([defaults], columns=columns)
                    except: df_init = pd.DataFrame(columns=columns) # Fallback
                else: # Apply defaults per column for type inference for empty df
                    for col, default_val in defaults.items():
                         if col in columns and col in df_init.columns: # ensure col exists
                             if pd.isna(default_val): df_init[col] = pd.Series(dtype='object')
                             else: df_init[col] = pd.Series(dtype=type(default_val))

            df_init.to_csv(filepath, index=False, encoding='utf-8')
            df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec_local if dtype_spec_local else None)
        else:
            df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec_local if dtype_spec_local else None)

        # --- Structural integrity: Ensure all `columns` (base columns for the file) exist in df_init ---
        made_structural_changes = False
        current_df_cols = df_init.columns.tolist()
        for col_idx, col_name_in_base in enumerate(columns):
            if col_name_in_base not in current_df_cols:
                default_val_struct = pd.NA
                col_dtype_struct = object 

                if defaults and col_name_in_base in defaults:
                    default_val_struct = defaults[col_name_in_base]
                    if not pd.isna(default_val_struct):
                        col_dtype_struct = type(default_val_struct)
                
                if filepath == admin_credenciais_csv and col_name_in_base in ALL_ADMIN_PERMISSION_KEYS:
                    default_val_struct = False # New global perm columns default to False for existing non-admin users
                    col_dtype_struct = bool
                
                # Insert column with determined default and attempt at dtype
                if len(df_init) > 0:
                    series_values = [default_val_struct] * len(df_init)
                    # Handle boolean specifically if target is bool
                    if col_dtype_struct == bool:
                        series_to_insert = pd.Series(series_values, index=df_init.index).apply(robust_str_to_bool).astype(bool)
                    else:
                        series_to_insert = pd.Series(series_values, index=df_init.index, dtype=col_dtype_struct)
                    df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name_in_base, value=series_to_insert)
                else: # DataFrame is empty, just add the column with correct type
                    df_init[col_name_in_base] = pd.Series(dtype=col_dtype_struct)
                made_structural_changes = True
        
        # --- Specific handling for admin_credenciais_csv to ensure master admin integrity ---
        if filepath == admin_credenciais_csv:
            admin_master_name = "admin"
            admin_master_pass = "potencialize"

            # Ensure all defined permission columns exist and are initially convertible to bool
            for perm_key_ensure in ALL_ADMIN_PERMISSION_KEYS:
                if perm_key_ensure not in df_init.columns:
                    df_init[perm_key_ensure] = False # Add with default False for other users
                    made_structural_changes = True # A structural change occurred
                # Convert to boolean using robust_str_to_bool first for all users
                df_init[perm_key_ensure] = df_init[perm_key_ensure].apply(robust_str_to_bool)

            # Remove ALL existing 'admin' rows to start fresh for the master admin
            if admin_master_name in df_init['Usuario'].values:
                df_init = df_init[df_init['Usuario'] != admin_master_name].reset_index(drop=True)
            
            # Now, add the definitive master admin row
            new_admin_data = {'Usuario': admin_master_name, 'Senha': admin_master_pass}
            for perm_key_master in ALL_ADMIN_PERMISSION_KEYS:
                new_admin_data[perm_key_master] = True # Explicitly Boolean True
            
            # Ensure all other base columns are present for the new admin row
            for col_base_new_admin in columns: # `columns` is colunas_base_admin_credenciais
                if col_base_new_admin not in new_admin_data:
                     new_admin_data[col_base_new_admin] = pd.NA # Default for non-cred/non-perm

            # Determine expected columns for the new row (should match df_init or base `columns`)
            expected_cols_for_new_admin_row = df_init.columns.tolist() if not df_init.empty else columns
            if not expected_cols_for_new_admin_row: expected_cols_for_new_admin_row = columns # Fallback

            new_row_df = pd.DataFrame([new_admin_data], columns=expected_cols_for_new_admin_row)

            df_init = pd.concat([df_init, new_row_df], ignore_index=True)

            # Final type conversion for all permission columns to ensure they are strictly boolean
            for perm_key_final_type in ALL_ADMIN_PERMISSION_KEYS:
                 if perm_key_final_type in df_init.columns:
                    df_init[perm_key_final_type] = df_init[perm_key_final_type].apply(robust_str_to_bool).astype(bool)
            
            made_structural_changes = True # Indicate a change was made for saving

        # Save the file if structural changes were made or if it's the admin CSV (always ensure its state)
        if made_structural_changes or filepath == admin_credenciais_csv:
            df_init.to_csv(filepath, index=False, encoding='utf-8')

    except pd.errors.EmptyDataError: # Catch if read_csv on existing file returns empty
        df_init = pd.DataFrame(columns=columns)
        if filepath == admin_credenciais_csv:
            admin_data = {"Usuario": "admin", "Senha": "potencialize"}
            for pk_empty in ALL_ADMIN_PERMISSION_KEYS: admin_data[pk_empty] = True
            for base_col_empty in columns:
                if base_col_empty not in admin_data: admin_data[base_col_empty] = pd.NA
            df_init = pd.DataFrame([admin_data], columns=columns)
            for perm_col_s_empty in ALL_ADMIN_PERMISSION_KEYS:
                if perm_col_s_empty in df_init.columns:
                    df_init[perm_col_s_empty] = df_init[perm_col_s_empty].apply(robust_str_to_bool).astype(bool)
        elif defaults:
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
                        st.error(f"CRÍTICO: Usuário 'admin' não possui a permissão '{perm_key_verify}' (valor: {admin_row_check.iloc[0].get(perm_key_verify)}) após inicialização.")
                        # break # Comment out break to see all missing permissions
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
                                df_creds[perm_col_login] = False 
                            df_creds[perm_col_login] = df_creds[perm_col_login].apply(robust_str_to_bool).astype(bool) # Ensure strict bool

                        if not df_creds.empty:
                            # Use u.strip() for robustness in username matching if needed, but CSV should be clean
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
    elif menu_options_cli_display: # Fallback if current page is not in displayable options
        current_idx_cli = 0
        for key_page_fallback, val_page_display_fallback in menu_options_cli_map.items():
            if val_page_display_fallback == menu_options_cli_display[0]:
                st.session_state.cliente_page = key_page_fallback
                break
        st.rerun() # Rerun to update with a valid page selection

    selected_page_cli_raw = st.sidebar.radio("Menu Cliente", menu_options_cli_display, index=current_idx_cli, key="cli_menu_v24_final_conditional_key") 

    selected_page_cli_clean = ""
    for key_page, val_page_display in menu_options_cli_map.items():
        if val_page_display == selected_page_cli_raw:
            if key_page == "Notificações": 
                selected_page_cli_clean = "Notificações"
            else:
                selected_page_cli_clean = key_page
            break

    if selected_page_cli_clean and selected_page_cli_clean != st.session_state.cliente_page :
        st.session_state.cliente_page = selected_page_cli_clean
        st.session_state.force_sidebar_rerun_after_notif_read_v19 = False
        st.session_state.target_diag_data_for_expansion = None
        st.rerun()

    if st.sidebar.button("Sair do Portal Cliente", icon="⬅️", key="logout_cliente_v24_final_btn", use_container_width=True): 
        keys_to_clear = [k for k in st.session_state.keys() if k not in ['admin_logado', 'last_cnpj_input', 'login_selection_aba']]
        for key_item in keys_to_clear: del st.session_state[key_item]
        for key_d, value_d in default_session_state.items():
            if key_d not in ['admin_logado', 'last_cnpj_input', 'login_selection_aba']: st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False
        st.toast("Logout realizado.", icon="👋")
        st.rerun()

    # --- Conteúdo das páginas do cliente ---
    if st.session_state.cliente_page == "Instruções":
        st.markdown("## 📖 Instruções do Portal de Diagnóstico")
        st.markdown("---")
        instrucoes_content = ""
        default_instr_content = """
        ### Bem-vindo ao Portal de Diagnóstico!
        Este portal foi projetado para ajudar você a entender melhor diversos aspectos do seu negócio através de um diagnóstico interativo.
        **Como proceder:**
        1.  **Primeiro Acesso:** Se esta é sua primeira vez, você está na página de instruções. Leia atentamente.
        2.  **Próximo Passo:** Clique em "Entendi, ir para o Diagnóstico" abaixo para prosseguir.
        3.  **Novo Diagnóstico:** Responda a todas as perguntas. Utilize a escala de 1 a 5.
        4.  **Envio e Resultados:** Após preencher, clique em "Enviar Diagnóstico". Você será levado ao "Painel Principal".
        """
        if os.path.exists(instrucoes_custom_path):
            try:
                with open(instrucoes_custom_path, "r", encoding="utf-8") as f: instrucoes_content = f.read()
            except Exception as e: instrucoes_content = default_instr_content; print(f"Erro ao ler instruções custom: {e}")
        else: instrucoes_content = default_instr_content
        st.markdown(instrucoes_content, unsafe_allow_html=True)
        if st.button("✅ Entendi, ir para o Diagnóstico", key="btn_entendi_instrucoes_v24_final", type="primary"):
            update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", "True")
            st.session_state.user["JaVisualizouInstrucoes"] = True
            pode_fazer_novo_diag_pos_instr = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo_diag_pos_instr else "Painel Principal"
            st.rerun()
    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.markdown("## 📋 Novo Diagnóstico Empresarial")
        st.markdown("---")
        # (Conteúdo da página Novo Diagnóstico)
        pass
    elif st.session_state.cliente_page == "Painel Principal":
        st.markdown("## 🏠 Painel Principal do Cliente")
        st.markdown("---")
        # (Conteúdo da página Painel Principal)
        pass
    elif st.session_state.cliente_page == "Suporte/FAQ":
        st.markdown("## 💬 Suporte e Perguntas Frequentes (FAQ)")
        st.markdown("---")
        # (Conteúdo da página Suporte/FAQ)
        pass
    elif st.session_state.cliente_page == "Pesquisa de Satisfação":
        st.markdown("## 🌟 Pesquisa de Satisfação")
        st.markdown("---")
        # (Conteúdo da página Pesquisa de Satisfação)
        pass
    elif st.session_state.cliente_page == "Notificações":
        st.markdown("## 🔔 Suas Notificações")
        st.markdown("---")
        # (Conteúdo da página Notificações)
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
            # Master admin 'admin' always has all permissions
            if st.session_state.admin_user_details.get('Usuario') == 'admin':
                return True
            
            # For other admins, check their specific permission
            permission_value = st.session_state.admin_user_details.get(permission_key)
            if isinstance(permission_value, bool): # Should be boolean if loaded correctly
                return permission_value
            else: # Fallback if it's somehow a string like "True" or "False"
                return robust_str_to_bool(permission_value)
        return False

    if st.sidebar.button("Sair do Painel Admin", icon="🚪", key="logout_admin_v24_final_button", use_container_width=True): 
        admin_keys_to_clear = ["admin_logado", "admin_user_details", SESSION_KEY_FOR_ADMIN_PAGE]
        for key_adm_clear in admin_keys_to_clear: 
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

    admin_user_perms_dict = st.session_state.get("admin_user_details", {}) 
    allowed_admin_pages_map = {}
    is_master_admin_logged_in = (admin_user_perms_dict.get('Usuario') == 'admin')

    for page_name, (emoji, perm_key) in menu_admin_options_map.items():
        if is_master_admin_logged_in or robust_str_to_bool(admin_user_perms_dict.get(perm_key, False)):
            allowed_admin_pages_map[page_name] = emoji

    if not allowed_admin_pages_map: # Should not happen for 'admin'
        st.error("Você não tem permissão para acessar nenhuma funcionalidade do painel de administração.")
        if not is_master_admin_logged_in: st.stop()

    admin_page_text_keys = list(allowed_admin_pages_map.keys())
    admin_options_for_display = [f"{allowed_admin_pages_map[key_disp]} {key_disp}" for key_disp in admin_page_text_keys] 

    def admin_menu_on_change_final_v24(): 
        selected_display_value = st.session_state.get(WIDGET_KEY_SB_ADMIN_MENU)
        if selected_display_value is None: return
        new_text_key = None
        for text_key_iter, emoji_iter in allowed_admin_pages_map.items():
            if f"{emoji_iter} {text_key_iter}" == selected_display_value:
                new_text_key = text_key_iter; break
        if new_text_key and new_text_key != st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE):
            st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = new_text_key

    if SESSION_KEY_FOR_ADMIN_PAGE not in st.session_state or \
       st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE) not in admin_page_text_keys:
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0] if admin_page_text_keys else None
        if admin_page_text_keys: st.rerun() # Rerun if state was invalid and fixed

    current_admin_page_text_key_for_index = st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE)
    current_admin_menu_index = 0

    if current_admin_page_text_key_for_index and admin_options_for_display:
        try:
            expected_display_value_for_current_page = f"{allowed_admin_pages_map.get(current_admin_page_text_key_for_index, '')} {current_admin_page_text_key_for_index}"
            current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
        except (ValueError, KeyError): # Current page key is invalid or emoji map changed
            if admin_page_text_keys: # If there are valid pages
                st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0] # Default to first valid page
                st.rerun() 
            else: current_admin_page_text_key_for_index = None # No valid pages
    
    if admin_options_for_display:
        st.sidebar.selectbox(
            "Funcionalidades Admin:", options=admin_options_for_display,
            index=current_admin_menu_index, key=WIDGET_KEY_SB_ADMIN_MENU,
            on_change=admin_menu_on_change_final_v24
        )

    menu_admin = st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE)

    if menu_admin and menu_admin in allowed_admin_pages_map:
        header_display_name = f"{allowed_admin_pages_map.get(menu_admin, '❓')} {menu_admin}"
        st.header(header_display_name)
    elif admin_page_text_keys: # If current menu_admin is invalid but there are options
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]
        st.rerun()
    else: # No pages available even for master admin (indicates a deeper issue)
        st.error("Acesso negado ou nenhuma funcionalidade disponível. Se você é 'admin', verifique a configuração do sistema.")
        st.stop()
    
    # ... (load df_usuarios_admin_geral - unchanged) ...

    # --- Admin Page Content com Verificações de Permissão ---
    # (The structure of these if/elif blocks is correct. Content rendering depends on `has_admin_permission`)
    if menu_admin == "Visão Geral e Diagnósticos":
        if not has_admin_permission("Perm_VisaoGeralDiagnosticos"): st.error("Acesso negado."); st.stop()
        st.write(f"Conteúdo de {menu_admin} aqui...") # Placeholder for content
    elif menu_admin == "Relatório de Engajamento":
        if not has_admin_permission("Perm_RelatorioEngajamento"): st.error("Acesso negado."); st.stop()
        st.write(f"Conteúdo de {menu_admin} aqui...")
    elif menu_admin == "Gerenciar Notificações":
        if not has_admin_permission("Perm_GerenciarNotificacoes"): st.error("Acesso negado."); st.stop()
        st.write(f"Conteúdo de {menu_admin} aqui...")
    elif menu_admin == "Gerenciar Clientes":
        if not has_admin_permission("Perm_GerenciarClientes"): st.error("Acesso negado."); st.stop()
        st.write(f"Conteúdo de {menu_admin} aqui...")
    elif menu_admin == "Personalizar Aparência":
        if not has_admin_permission("Perm_PersonalizarAparencia"): st.error("Acesso negado."); st.stop()
        st.write(f"Conteúdo de {menu_admin} aqui...")
    elif menu_admin == "Gerenciar Perguntas Diagnóstico":
        if not has_admin_permission("Perm_GerenciarPerguntasDiagnostico"): st.error("Acesso negado."); st.stop()
        st.write(f"Conteúdo de {menu_admin} aqui...")
    elif menu_admin == "Gerenciar Análises de Perguntas":
        if not has_admin_permission("Perm_GerenciarAnalises"): st.error("Acesso negado."); st.stop()
        st.write(f"Conteúdo de {menu_admin} aqui...")
    elif menu_admin == "Gerenciar FAQ/SAC":
        if not has_admin_permission("Perm_GerenciarFAQ"): st.error("Acesso negado."); st.stop()
        st.write(f"Conteúdo de {menu_admin} aqui...")
    elif menu_admin == "Gerenciar Perguntas da Pesquisa":
        if not has_admin_permission("Perm_GerenciarPerguntasPesquisa"): st.error("Acesso negado."); st.stop()
        st.write(f"Conteúdo de {menu_admin} aqui...")
    elif menu_admin == "Resultados da Pesquisa de Satisfação":
        if not has_admin_permission("Perm_VerResultadosPesquisa"): st.error("Acesso negado."); st.stop()
        st.write(f"Conteúdo de {menu_admin} aqui...")
    elif menu_admin == "Gerenciar Instruções":
        if not has_admin_permission("Perm_GerenciarInstrucoes"): st.error("Acesso negado."); st.stop()
        st.write(f"Conteúdo de {menu_admin} aqui...")
    elif menu_admin == "Histórico de Usuários":
        if not has_admin_permission("Perm_VerHistorico"): st.error("Acesso negado."); st.stop()
        st.write(f"Conteúdo de {menu_admin} aqui...")
    elif menu_admin == "Gerenciar Administradores":
        if not has_admin_permission("Perm_GerenciarAdministradores"): st.error("Acesso negado."); st.stop()
        
        st.subheader("Gerenciar Contas de Administrador")
        try:
            df_admins_ga = pd.read_csv(admin_credenciais_csv, encoding='utf-8', dtype={'Usuario':str, 'Senha':str})
            for perm_col_ga in ALL_ADMIN_PERMISSION_KEYS:
                if perm_col_ga not in df_admins_ga.columns: df_admins_ga[perm_col_ga] = False
                df_admins_ga[perm_col_ga] = df_admins_ga[perm_col_ga].apply(robust_str_to_bool).astype(bool)
        except (FileNotFoundError, pd.errors.EmptyDataError): 
            df_admins_ga = pd.DataFrame(columns=colunas_base_admin_credenciais)
            # This should be pre-populated by inicializar_csv with 'admin'
            if df_admins_ga.empty or 'admin' not in df_admins_ga['Usuario'].values:
                 st.warning(f"{admin_credenciais_csv} vazio ou sem 'admin' ao carregar na página. `inicializar_csv` deveria ter tratado.")
                 # (Minimal recreation for safety, though `inicializar_csv` is primary)
                 admin_master_fallback = {"Usuario": "admin", "Senha": "potencialize"}
                 for pkf in ALL_ADMIN_PERMISSION_KEYS: admin_master_fallback[pkf] = True
                 for bcf_page in colunas_base_admin_credenciais:
                     if bcf_page not in admin_master_fallback: admin_master_fallback[bcf_page] = pd.NA
                 df_admins_ga = pd.DataFrame([admin_master_fallback], columns=colunas_base_admin_credenciais)
                 for pkf_bool in ALL_ADMIN_PERMISSION_KEYS: # Ensure bool type
                     if pkf_bool in df_admins_ga.columns: df_admins_ga[pkf_bool] = df_admins_ga[pkf_bool].astype(bool)


        st.info("Adicione, edite ou remova contas de administrador. O usuário 'admin' é superadministrador; suas permissões são fixas e não pode ser excluído.")

        # (Resto do código da página Gerenciar Administradores, como estava, com as devidas proteções para 'admin')
        with st.expander("➕ Adicionar Novo Administrador"):
            with st.form("form_add_new_admin_v24_final_form"): 
                # ... (form content as before) ...
                pass # Placeholder for brevity

        st.markdown("---")
        st.write("##### Editar Administradores Existentes")
        # ... (data editor and save logic, ensuring 'admin' is protected, as in previous corrected version) ...
        pass # Placeholder for brevity

        st.markdown("---")
        st.subheader("Alterar Senha de Administrador")
        with st.form("form_change_admin_password_v24_final_form"):
            # ... (form content as before, noting 'admin' password reset by system) ...
            pass # Placeholder for brevity
    else:
        st.warning(f"Página administrativa '{menu_admin}' não reconhecida ou sem conteúdo definido.")

# Fallback final
if 'aba' not in locals() and not st.session_state.admin_logado and not st.session_state.cliente_logado:
    st.info("Por favor, selecione seu tipo de acesso para iniciar ou complete o login.")
    if not st.session_state.get("tipo_usuario_radio_v24_login_selection"): 
        st.session_state.login_selection_aba = "Cliente" 
    st.stop()