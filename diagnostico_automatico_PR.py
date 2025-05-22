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
        if val_lower in ['true', '1', 't', 'y', 'yes', 'sim', 'verdadeiro']:
            return True
        elif val_lower in ['false', '0', 'f', 'n', 'no', 'nao', 'não', 'falso']:
            return False
    return False # Default para NaN, vazios ou outros tipos/strings não reconhecidas

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
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init = pd.DataFrame(columns=columns)
            if defaults:
                if filepath == admin_credenciais_csv:
                    default_row_data = {}
                    for col_name in columns:
                        val = defaults.get(col_name)
                        default_row_data[col_name] = robust_str_to_bool(val) if col_name in ALL_ADMIN_PERMISSION_KEYS else val
                    df_init = pd.DataFrame([default_row_data], columns=columns)
                else:
                    for col, default_val in defaults.items():
                        if col in columns:
                            if pd.isna(default_val): df_init[col] = pd.Series(dtype='object')
                            else: df_init[col] = pd.Series(dtype=type(default_val))
                            if len(df_init[col]) == 0 and not pd.isna(default_val) :
                                df_init.loc[0, col] = default_val; df_init = df_init.iloc[0:0]
            df_init.to_csv(filepath, index=False, encoding='utf-8')
        else:
            dtype_spec = {}
            if filepath == admin_credenciais_csv: dtype_spec = {'Usuario': str, 'Senha': str}
            elif filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, historico_csv, pesquisa_satisfacao_respostas_csv]:
                if 'CNPJ' in columns: dtype_spec['CNPJ'] = str
                if 'CNPJ_Cliente' in columns: dtype_spec['CNPJ_Cliente'] = str
            # ... outras dtypes
            try:
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)
            except Exception as read_e:
                st.warning(f"Problema ao ler {filepath} ({read_e}), tentando recriar.")
                df_init = pd.DataFrame(columns=columns)
                if defaults:
                    if filepath == admin_credenciais_csv:
                        default_row_data = {col: defaults.get(col) for col in columns}
                        df_init = pd.DataFrame([default_row_data], columns=columns)
                    else: # Lógica anterior para outros CSVs
                        for col, default_val in defaults.items():
                            if col in columns:
                                if pd.isna(default_val): df_init[col] = pd.Series(dtype='object')
                                else: df_init[col] = pd.Series(dtype=type(default_val))
                df_init.to_csv(filepath, index=False, encoding='utf-8')
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)

            if filepath == admin_credenciais_csv:
                for perm_col_load in ALL_ADMIN_PERMISSION_KEYS:
                    if perm_col_load in df_init.columns:
                        df_init[perm_col_load] = df_init[perm_col_load].apply(robust_str_to_bool)
                    else: df_init[perm_col_load] = False

            made_changes = False
            current_cols = df_init.columns.tolist()
            for col_idx, col_name in enumerate(columns):
                if col_name not in current_cols:
                    default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                    col_dtype = bool if filepath == admin_credenciais_csv and col_name in ALL_ADMIN_PERMISSION_KEYS else (object if pd.isna(default_val) else type(default_val))
                    
                    # Garantir que o valor padrão seja do tipo correto para colunas de permissão
                    if col_dtype == bool: default_val = robust_str_to_bool(default_val)

                    if len(df_init) > 0 and not df_init.empty:
                        insert_values = [default_val] * len(df_init)
                        df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=pd.Series(insert_values, index=df_init.index).astype(col_dtype))
                    else:
                        df_init[col_name] = pd.Series(dtype=col_dtype)
                    made_changes = True
            if made_changes:
                df_init.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError:
        df_init = pd.DataFrame(columns=columns)
        if defaults:
            if filepath == admin_credenciais_csv:
                default_row_data = {col: (robust_str_to_bool(defaults.get(col)) if col in ALL_ADMIN_PERMISSION_KEYS else defaults.get(col)) for col in columns}
                df_init = pd.DataFrame([default_row_data], columns=columns)
            else:
                for col, default_val in defaults.items():
                    if col in columns:
                        if pd.isna(default_val): df_init[col] = pd.Series(dtype='object')
                        else: df_init[col] = pd.Series(dtype=type(default_val))
        df_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e: st.error(f"Erro crítico ao inicializar {filepath}: {e}"); st.exception(e); raise

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])

    admin_defaults = {"Usuario": "admin", "Senha": "potencialize"} # CREDENCIAIS PADRÃO ATUALIZADAS
    for perm_key in ALL_ADMIN_PERMISSION_KEYS:
        admin_defaults[perm_key] = True
    inicializar_csv(admin_credenciais_csv, colunas_base_admin_credenciais, defaults=admin_defaults)

    try:
        df_admins_check_init = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
        if df_admins_check_init.empty:
            st.warning(f"Arquivo {admin_credenciais_csv} está vazio após inicialização. Recriando superadmin padrão ('admin'/'potencialize').")
            super_admin_data_init = {"Usuario": "admin", "Senha": "potencialize"} # CREDENCIAIS PADRÃO ATUALIZADAS
            for pk in ALL_ADMIN_PERMISSION_KEYS: super_admin_data_init[pk] = True
            df_super_admin_init = pd.DataFrame([super_admin_data_init], columns=colunas_base_admin_credenciais)
            for perm_col_s in ALL_ADMIN_PERMISSION_KEYS:
                 df_super_admin_init[perm_col_s] = df_super_admin_init[perm_col_s].apply(robust_str_to_bool)
            df_super_admin_init.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
            print("INFO: Superadministrador padrão ('admin'/'potencialize') recriado (arquivo estava vazio).") # MENSAGEM ATUALIZADA
        else:
            made_changes_admin_perms_init = False
            for perm_key_init in ALL_ADMIN_PERMISSION_KEYS:
                if perm_key_init not in df_admins_check_init.columns:
                    df_admins_check_init[perm_key_init] = False
                    made_changes_admin_perms_init = True
                df_admins_check_init[perm_key_init] = df_admins_check_init[perm_key_init].apply(robust_str_to_bool)
            if made_changes_admin_perms_init:
                df_admins_check_init.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError:
        st.warning(f"Arquivo {admin_credenciais_csv} causou EmptyDataError. Recriando superadmin padrão ('admin'/'potencialize').")
        super_admin_data_empty = {"Usuario": "admin", "Senha": "potencialize"} # CREDENCIAIS PADRÃO ATUALIZADAS
        for pk in ALL_ADMIN_PERMISSION_KEYS: super_admin_data_empty[pk] = True
        df_super_admin_empty = pd.DataFrame([super_admin_data_empty], columns=colunas_base_admin_credenciais)
        for perm_col_s in ALL_ADMIN_PERMISSION_KEYS:
            df_super_admin_empty[perm_col_s] = df_super_admin_empty[perm_col_s].apply(robust_str_to_bool)
        df_super_admin_empty.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
        print("INFO: Superadministrador padrão ('admin'/'potencialize') criado (EmptyDataError).") # MENSAGEM ATUALIZADA
    except Exception as e_admin_post_init:
        st.error(f"Erro na verificação pós-inicialização do {admin_credenciais_csv}: {e_admin_post_init}")

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

# --- Funções Utilitárias (registrar_acao, update_user_data, etc. mantidas) ---
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
        if "Ativa" not in df.columns: df["Ativa"] = True # Default
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
    if df_analises.empty: return None
    # ... (código mantido)
    return default_analise

def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df, respostas_coletadas, medias_cat, analises_df):
    try:
        # ... (código mantido)
        return pdf_path
    except Exception as e: st.error(f"Erro crítico ao gerar PDF: {e}"); return None

# --- LOGIN AND MAIN NAVIGATION ---
top_login_placeholder = st.empty()
admin_login_form_placeholder = st.empty()
client_login_form_placeholder = st.empty()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    login_logo_to_display = DEFAULT_LOGIN_LOGO_PATH
    if os.path.exists(CUSTOM_LOGIN_LOGO_PATH):
        login_logo_to_display = CUSTOM_LOGIN_LOGO_PATH

    with top_login_placeholder.container():
        # ... (código de login mantido, com chaves atualizadas para v24 se necessário)
        st.session_state.login_selection_aba = st.radio(
            "Você é:",
            ["Administrador", "Cliente"],
            horizontal=True,
            key="tipo_usuario_radio_v24_login_selection", # CHAVE ATUALIZADA
            index=["Administrador", "Cliente"].index(st.session_state.login_selection_aba),
            label_visibility="collapsed"
        )
        # ...

    if st.session_state.login_selection_aba == "Administrador":
        client_login_form_placeholder.empty()
        with admin_login_form_placeholder.container():
            # ...
            with st.form("form_admin_login_v24_final"): # CHAVE ATUALIZADA
                u = st.text_input("Usuário", key="admin_u_v24_final_input")
                p = st.text_input("Senha", type="password", key="admin_p_v24_final_input")
                if st.form_submit_button("Entrar", use_container_width=True, icon="🔑"):
                    try:
                        df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                        for perm_col_login in ALL_ADMIN_PERMISSION_KEYS:
                            if perm_col_login not in df_creds.columns:
                                df_creds[perm_col_login] = False
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
                            # ... (resto do login admin)
                    # ...
            # ...
    elif st.session_state.login_selection_aba == "Cliente":
        admin_login_form_placeholder.empty()
        with client_login_form_placeholder.container():
            # ...
            with st.form("form_cliente_login_v24_final"): # CHAVE ATUALIZADA
                c = st.text_input("CNPJ", key="cli_c_v24_final_input", value=st.session_state.get("last_cnpj_input",""))
                s = st.text_input("Senha", type="password", key="cli_s_v24_final_input")
                if st.form_submit_button("Entrar", use_container_width=True, icon="👤"):
                    # ... (lógica de login cliente)
                    pass # Mantida como antes
            # ...
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
    # ... (Código da área do cliente mantido, com chaves de widget atualizadas para v24 se necessário)
    # Exemplo de atualização de chave:
    # selected_page_cli_raw = st.sidebar.radio("Menu Cliente", ..., key="cli_menu_v24_final_conditional_key")
    # if st.sidebar.button("Sair...", key="logout_cliente_v24_final_btn", ...)
    # if st.button("Entendi...", key="cliente_entendeu_instrucoes_v24", type="primary"):
    # etc.
    pass


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_text_key_v24_final_sess" # CHAVE ATUALIZADA
    WIDGET_KEY_SB_ADMIN_MENU = "sb_admin_menu_v24_final_widget_key" # CHAVE ATUALIZADA

    admin_logo_path_sidebar = CUSTOM_LOGIN_LOGO_PATH if os.path.exists(CUSTOM_LOGIN_LOGO_PATH) else DEFAULT_LOGIN_LOGO_PATH
    if os.path.exists(admin_logo_path_sidebar):
        st.sidebar.image(admin_logo_path_sidebar, use_container_width=True, width=150)
    else:
        st.sidebar.markdown("### Painel Admin")

    st.sidebar.success(f"🟢 Admin Logado: {st.session_state.admin_user_details.get('Usuario', '')}")

    def has_admin_permission(permission_key):
        if 'admin_user_details' in st.session_state and st.session_state.admin_user_details is not None:
            return st.session_state.admin_user_details.get(permission_key, False)
        return False

    if st.sidebar.button("Sair do Painel Admin", icon="🚪", key="logout_admin_v24_final_button", use_container_width=True): # CHAVE ATUALIZADA
        admin_keys_to_clear = ["admin_logado", "admin_user_details", SESSION_KEY_FOR_ADMIN_PAGE]
        for key in admin_keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
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

    admin_user_perms = st.session_state.get("admin_user_details", {})
    allowed_admin_pages_map = {}
    for page_name, (emoji, perm_key) in menu_admin_options_map.items():
        if admin_user_perms.get(perm_key, False):
            allowed_admin_pages_map[page_name] = emoji

    if not allowed_admin_pages_map:
        st.error("Você não tem permissão para acessar nenhuma funcionalidade do painel de administração.")
        st.stop()

    admin_page_text_keys = list(allowed_admin_pages_map.keys())
    admin_options_for_display = [f"{allowed_admin_pages_map[key]} {key}" for key in admin_page_text_keys]


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
                current_admin_page_text_key_for_index = admin_page_text_keys[0]
                expected_display_value_for_current_page = f"{allowed_admin_pages_map[current_admin_page_text_key_for_index]} {current_admin_page_text_key_for_index}"
                current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
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
    elif admin_page_text_keys :
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]
        st.rerun()
    else:
        st.error("Acesso negado ou nenhuma funcionalidade disponível.")
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
        # ... (código da seção)
    elif menu_admin == "Relatório de Engajamento":
        if not has_admin_permission("Perm_RelatorioEngajamento"): st.error("Acesso negado."); st.stop()
        # ... (código da seção)
    elif menu_admin == "Gerenciar Notificações":
        if not has_admin_permission("Perm_GerenciarNotificacoes"): st.error("Acesso negado."); st.stop()
        # ... (código da seção)
    elif menu_admin == "Gerenciar Clientes":
        if not has_admin_permission("Perm_GerenciarClientes"): st.error("Acesso negado."); st.stop()
        # ... (código da seção)
    elif menu_admin == "Personalizar Aparência":
        if not has_admin_permission("Perm_PersonalizarAparencia"): st.error("Acesso negado."); st.stop()
        # ... (código da seção)
    elif menu_admin == "Gerenciar Perguntas Diagnóstico":
        if not has_admin_permission("Perm_GerenciarPerguntasDiagnostico"): st.error("Acesso negado."); st.stop()
        # ... (código da seção)
    elif menu_admin == "Gerenciar Análises de Perguntas":
        if not has_admin_permission("Perm_GerenciarAnalises"): st.error("Acesso negado."); st.stop()
        # ... (código da seção)
    elif menu_admin == "Gerenciar FAQ/SAC":
        if not has_admin_permission("Perm_GerenciarFAQ"): st.error("Acesso negado."); st.stop()
        # ... (código da seção)
    elif menu_admin == "Gerenciar Perguntas da Pesquisa":
        if not has_admin_permission("Perm_GerenciarPerguntasPesquisa"): st.error("Acesso negado."); st.stop()
        # ... (código da seção)
    elif menu_admin == "Resultados da Pesquisa de Satisfação":
        if not has_admin_permission("Perm_VerResultadosPesquisa"): st.error("Acesso negado."); st.stop()
        # ... (código da seção)
    elif menu_admin == "Gerenciar Instruções":
        if not has_admin_permission("Perm_GerenciarInstrucoes"): st.error("Acesso negado."); st.stop()
        # ... (código da seção)
    elif menu_admin == "Histórico de Usuários":
        if not has_admin_permission("Perm_VerHistorico"): st.error("Acesso negado."); st.stop()
        # ... (código da seção)
    elif menu_admin == "Gerenciar Administradores":
        if not has_admin_permission("Perm_GerenciarAdministradores"): st.error("Acesso negado."); st.stop()
        # --- Código da seção Gerenciar Administradores (já implementado com as correções anteriores) ---
        st.subheader("Gerenciar Contas de Administrador")
        try:
            df_admins_ga = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            for perm_col in ALL_ADMIN_PERMISSION_KEYS:
                if perm_col not in df_admins_ga.columns:
                    df_admins_ga[perm_col] = False
                df_admins_ga[perm_col] = df_admins_ga[perm_col].apply(robust_str_to_bool)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df_admins_ga = pd.DataFrame(columns=colunas_base_admin_credenciais)
            for perm_col in ALL_ADMIN_PERMISSION_KEYS: df_admins_ga[perm_col] = pd.Series(dtype=bool)

        st.info("Adicione, edite ou remova contas de administrador e suas permissões. Cuidado: A remoção é permanente.")

        with st.expander("➕ Adicionar Novo Administrador"):
            with st.form("form_add_new_admin_v24"): # Chave do formulário atualizada
                # ... (código para adicionar admin mantido)
                pass
        st.markdown("---")
        st.write("##### Editar Administradores Existentes")
        # ... (código para editar admin mantido)
        st.markdown("---")
        st.subheader("Alterar Senha de Administrador")
        with st.form("form_change_admin_password_v24"): # Chave atualizada
            # ... (código para alterar senha mantido)
            pass
    else:
        st.warning(f"Página administrativa '{menu_admin}' não reconhecida ou sem conteúdo definido.")


# Fallback final
if 'aba' not in locals() and not st.session_state.admin_logado and not st.session_state.cliente_logado:
    st.info("Por favor, selecione seu tipo de acesso para iniciar ou complete o login.")
    st.stop()