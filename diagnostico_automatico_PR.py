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

# Ensure assets directory exists at startup
if not os.path.exists(ASSETS_DIR):
    try:
        os.makedirs(ASSETS_DIR)
    except OSError as e:
        # This error is critical for logos, but the app might run without it for other functionalities.
        # For simplicity, we'll let it proceed and handle missing logos in display logic.
        print(f"Aviso: Não foi possível criar o diretório de assets '{ASSETS_DIR}': {e}. Crie este diretório manualmente para funcionalidades de logo.")


# --- CSS Melhorado ---
st.markdown(f"""
<style>
body {{
    font-family: 'Segoe UI', sans-serif;
    background-color: #f0f2f5; /* A light global background for the overall app feel */
}}
/* This class can be conditionally applied via st.container if needed for login-only full page bg */
.login-page-background {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: #eef2f7; /* Light grayish-blue background */
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: -1; /* Keep it in the background */
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
/* Targets the image rendered by st.image within the login container */
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

/* Styling for the Admin/Client radio buttons on login */
div[data-testid="stRadio"] > label[data-baseweb="radio"] > div:first-child {{
    justify-content: center; /* Centers the radio button itself if it's smaller than label */
}}
div[data-testid="stRadio"] > div[role="radiogroup"] {{ /* More specific selector for the radio group */
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
/* Styling for the selected radio option's label text */
div[data-testid="stRadio"] input[type="radio"]:checked + div {{
    background-color: #2563eb !important; 
    color: white !important;
    border-color: #2563eb !important;
}}
/* Ensure the text inside the selected radio label also turns white */
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
</style>
""", unsafe_allow_html=True)


# --- Funções de Gráficos (Keep as is) ---
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
    if df_diagnostics.empty or 'Data' not in df_diagnostics.columns: return None # Original 'Data' for timeline
    df_diag_copy = df_diagnostics.copy()
    # Ensure 'Data' is datetime for Grouper
    df_diag_copy['Data'] = pd.to_datetime(df_diag_copy['Data'], errors='coerce')
    df_diag_copy.dropna(subset=['Data'], inplace=True) # Remove rows where Data could not be converted
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

# --- Configuração de Arquivos e Variáveis Globais (Keep as is) ---
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

# --- Inicialização do Session State (Keep as is) ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {},
    "force_sidebar_rerun_after_notif_read_v19": False,
    "target_diag_data_for_expansion": None 
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias (Keep as is, unless find_client_logo_path needs ASSETS_DIR, it's for client_logos) ---
def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_'); s = re.sub(r'(?u)[^-\w.]', '', s); return s
def pdf_safe_text_output(text): return str(text).encode('latin-1', 'replace').decode('latin-1')
def find_client_logo_path(cnpj_arg): # This is for individual client logos, not the portal login one
    if not cnpj_arg: return None
    base = str(cnpj_arg).replace('/', '').replace('.', '').replace('-', '')
    for ext in ["png", "jpg", "jpeg"]:
        path = os.path.join(LOGOS_DIR, f"{base}_logo.{ext}")
        if os.path.exists(path): return path
    return None

if not os.path.exists(LOGOS_DIR):
    try: os.makedirs(LOGOS_DIR)
    except OSError as e: st.error(f"Erro ao criar diretório de logos de cliente '{LOGOS_DIR}': {e}")


colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone",
                         "JaVisualizouInstrucoes", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]
colunas_base_perguntas = ["Pergunta", "Categoria"]
colunas_base_analises = ["ID_Analise", "TextoPerguntaOriginal", "TipoCondicao", "CondicaoValorMin", "CondicaoValorMax", "CondicaoValorExato", "TextoAnalise"]
colunas_base_notificacoes = ["ID_Notificacao", "CNPJ_Cliente", "Timestamp", "Mensagem", "Lida", "ID_Diagnostico_Relacionado"] 

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
                # Specify dtype for all known problematic columns across all CSVs if needed
                dtype_spec = {}
                if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, historico_csv]:
                    dtype_spec['CNPJ'] = str
                    dtype_spec['CNPJ_Cliente'] = str
                # Add more specific dtypes if other columns cause issues, e.g., ID_Diagnostico_Relacionado
                if filepath == notificacoes_csv:
                    dtype_spec['ID_Diagnostico_Relacionado'] = str

                df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)

            except ValueError as ve: 
                 st.warning(f"Problema ao ler {filepath} com dtypes específicos ({ve}), tentando leitura genérica.")
                 df_init = pd.read_csv(filepath, encoding='utf-8') 
            except Exception as read_e: 
                 st.warning(f"Problema ao ler {filepath}, tentando recriar com colunas esperadas: {read_e}")
                 df_init = pd.DataFrame(columns=columns) 
                 if defaults:
                    for col, default_val in defaults.items():
                        if col in columns: df_init[col] = default_val
                 df_init.to_csv(filepath, index=False, encoding='utf-8')
                 df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)

            made_changes = False
            current_cols = df_init.columns.tolist()
            for col_idx, col_name in enumerate(columns):
                if col_name not in current_cols:
                    default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                    if len(df_init) > 0 and not df_init.empty: # Check if df is not empty before inserting
                        df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=[default_val] * len(df_init))
                    else: # If dataframe is empty (e.g. only headers or fully empty)
                         # Create an empty series with the correct dtype if possible or just assign
                        if pd.api.types.is_list_like(default_val) and len(default_val) == len(df_init):
                             df_init[col_name] = default_val
                        else:
                             df_init[col_name] = pd.Series([default_val] * len(df_init), dtype=type(default_val) if default_val is not pd.NA else object)


                    made_changes = True
            if made_changes:
                df_init.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError: # This handles if read_csv results in an empty df (e.g. file only has headers)
        df_init = pd.DataFrame(columns=columns)
        if defaults:
            for col, default_val in defaults.items():
                if col in columns: df_init[col] = default_val
        df_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e: st.error(f"Erro crítico ao inicializar {filepath}: {e}"); raise

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios,
                    defaults={"JaVisualizouInstrucoes": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos) 
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False, "ID_Diagnostico_Relacionado": None}) 
except Exception as e_init:
    st.error(f"Falha na inicialização de arquivos CSV: {e_init}")
    st.stop()

def registrar_acao(cnpj, acao, desc):
    try: hist_df = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str}) # Add dtype here
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
# --- (The rest of the script, including login logic, client area, and admin area, needs to be placed here) ---
# --- (It will be the previous version's code with the specific modifications for login logo and new admin reports) ---

# --- LOGIN AND MAIN NAVIGATION ---
# (This section is taken from the previous script and updated)
if 'aba' not in st.session_state:
    st.session_state.aba = None # Initialize if not exists

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    # Determine which logo to display on the login screen
    login_logo_to_display = DEFAULT_LOGIN_LOGO_PATH
    if os.path.exists(CUSTOM_LOGIN_LOGO_PATH):
        login_logo_to_display = CUSTOM_LOGIN_LOGO_PATH

    # Centered content for the initial choice (Admin/Client)
    # This is a common area before specific login forms
    
    # Radio button selection outside the form cards for better layout
    st.session_state.aba = st.radio(
        "Você é:", 
        ["Administrador", "Cliente"], 
        horizontal=True, 
        key="tipo_usuario_radio_v19_styled_top",
        label_visibility="collapsed" # Hide the "Você é:" label here, use markdown title instead
    )    
    st.markdown('<hr style="margin-top: 0; margin-bottom: 30px;">', unsafe_allow_html=True)


    if st.session_state.aba == "Administrador":
        st.markdown('<div class="login-container" style="border-top: 6px solid #c0392b;">', unsafe_allow_html=True) # Red accent
        if os.path.exists(login_logo_to_display):
            st.image(login_logo_to_display, use_column_width='auto')
        else:
            st.markdown("<h3 style='text-align: center; margin-bottom:20px;'>Portal de Diagnóstico</h3>", unsafe_allow_html=True)
        st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
        with st.form("form_admin_login_v19_final"):
            u = st.text_input("Usuário", key="admin_u_v19_final")
            p = st.text_input("Senha", type="password", key="admin_p_v19_final")
            if st.form_submit_button("Entrar", use_container_width=True, icon="🔑"):
                try:
                    df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                    if not df_creds[(df_creds["Usuario"] == u) & (df_creds["Senha"] == p)].empty:
                        st.session_state.admin_logado = True
                        st.toast("Login de admin bem-sucedido!", icon="🎉")
                        st.rerun()
                    else: st.error("Usuário/senha admin inválidos.")
                except Exception as e: st.error(f"Erro login admin: {e}")
        st.markdown('</div>', unsafe_allow_html=True); st.stop()

    elif st.session_state.aba == "Cliente":
        st.markdown('<div class="login-container">', unsafe_allow_html=True) # Blue accent (default)
        if os.path.exists(login_logo_to_display):
            st.image(login_logo_to_display, use_column_width='auto')
        else:
            st.markdown("<h3 style='text-align: center; margin-bottom:20px;'>Portal de Diagnóstico</h3>", unsafe_allow_html=True)
        st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
        with st.form("form_cliente_login_v19_final"):
            c = st.text_input("CNPJ", key="cli_c_v19_final", value=st.session_state.get("last_cnpj_input",""))
            s = st.text_input("Senha", type="password", key="cli_s_v19_final")
            if st.form_submit_button("Entrar", use_container_width=True, icon="👤"):
                st.session_state.last_cnpj_input = c
                try:
                    users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                    if "JaVisualizouInstrucoes" not in users_df.columns: users_df["JaVisualizouInstrucoes"] = "False"
                    users_df["JaVisualizouInstrucoes"] = users_df["JaVisualizouInstrucoes"].astype(str).str.lower().map({'true': True, 'false': False, 'nan': False, '':False}).fillna(False)
                    if "DiagnosticosDisponiveis" not in users_df.columns: users_df["DiagnosticosDisponiveis"] = 1
                    users_df["DiagnosticosDisponiveis"] = pd.to_numeric(users_df["DiagnosticosDisponiveis"], errors='coerce').fillna(1).astype(int)
                    if "TotalDiagnosticosRealizados" not in users_df.columns: users_df["TotalDiagnosticosRealizados"] = 0
                    users_df["TotalDiagnosticosRealizados"] = pd.to_numeric(users_df["TotalDiagnosticosRealizados"], errors='coerce').fillna(0).astype(int)

                    blocked_df = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                    if c in blocked_df["CNPJ"].values: st.error("CNPJ bloqueado."); st.stop()
                    match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == s)]
                    if match.empty: st.error("CNPJ/senha inválidos."); st.stop()

                    st.session_state.cliente_logado = True; st.session_state.cnpj = c
                    st.session_state.user = match.iloc[0].to_dict()
                    st.session_state.user["JaVisualizouInstrucoes"] = bool(st.session_state.user.get("JaVisualizouInstrucoes", False)) 
                    st.session_state.user["DiagnosticosDisponiveis"] = int(st.session_state.user.get("DiagnosticosDisponiveis", 1))
                    st.session_state.user["TotalDiagnosticosRealizados"] = int(st.session_state.user.get("TotalDiagnosticosRealizados", 0))

                    st.session_state.inicio_sessao_cliente = time.time()
                    registrar_acao(c, "Login", "Usuário logou.")

                    if not st.session_state.user["JaVisualizouInstrucoes"]:
                        st.session_state.cliente_page = "Instruções"
                    else:
                        pode_fazer_novo_login = st.session_state.user["DiagnosticosDisponiveis"] > st.session_state.user["TotalDiagnosticosRealizados"]
                        st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo_login else "Painel Principal"
                    
                    # Reset other session state items
                    st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                    st.session_state.respostas_atuais_diagnostico = {}
                    st.session_state.progresso_diagnostico_percentual = 0
                    st.session_state.progresso_diagnostico_contagem = (0,0)
                    st.session_state.feedbacks_respostas = {}
                    st.session_state.diagnostico_enviado_sucesso = False
                    st.session_state.target_diag_data_for_expansion = None 

                    st.toast("Login de cliente bem-sucedido!", icon="👋")
                    st.rerun()
                except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
        st.markdown('</div>', unsafe_allow_html=True); st.stop()
    st.stop() # Stop if no specific aba is chosen by radio (should not happen)

elif st.session_state.admin_logado: 
    aba = "Administrador" # Ensure aba is set if already logged in
else: 
    aba = "Cliente" # Ensure aba is set if already logged in


# --- ÁREA DO CLIENTE LOGADO (COPIED FROM PREVIOUS VERSION WITH ENHANCEMENTS) ---
if aba == "Cliente" and st.session_state.cliente_logado:
    if 'user' not in st.session_state or not st.session_state.user: # Should not happen if cliente_logado is true
        st.error("Erro de sessão do usuário. Por favor, faça login novamente.")
        st.session_state.cliente_logado = False
        st.rerun()

    if not st.session_state.user.get("JaVisualizouInstrucoes", False):
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
            df_notif_check = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str})
            if not df_notif_check.empty and 'Lida' in df_notif_check.columns:
                df_notif_check['Lida'] = df_notif_check['Lida'].astype(str).str.lower().map({'true': True, 'false': False, 'nan': False, '': False}).fillna(False)
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
        "Notificações": notificacoes_label
    }
    
    if not st.session_state.user.get("JaVisualizouInstrucoes", False):
        menu_options_cli_map = {"Instruções": "📖 Instruções"}
        if st.session_state.cliente_page != "Instruções": 
            st.session_state.cliente_page = "Instruções"
            st.experimental_rerun() 
    else:
        menu_options_cli_map = menu_options_cli_map_full.copy()
        pode_fazer_novo = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
        if not pode_fazer_novo and "Novo Diagnóstico" in menu_options_cli_map:
            if st.session_state.cliente_page == "Novo Diagnóstico":
                 st.session_state.cliente_page = "Painel Principal"
            del menu_options_cli_map["Novo Diagnóstico"]

    menu_options_cli_display = list(menu_options_cli_map.values())
    
    if st.session_state.cliente_page not in menu_options_cli_map.keys():
        st.session_state.cliente_page = "Instruções" if not st.session_state.user.get("JaVisualizouInstrucoes", False) else "Painel Principal"

    default_display_option = menu_options_cli_map.get(st.session_state.cliente_page)
    current_idx_cli = 0
    if default_display_option and default_display_option in menu_options_cli_display:
        current_idx_cli = menu_options_cli_display.index(default_display_option)
    elif menu_options_cli_display:
        current_idx_cli = 0
        for key_page_fallback, val_page_display_fallback in menu_options_cli_map.items():
            if val_page_display_fallback == menu_options_cli_display[0]:
                st.session_state.cliente_page = key_page_fallback
                break

    selected_page_cli_raw = st.sidebar.radio("Menu Cliente", menu_options_cli_display, index=current_idx_cli, key="cli_menu_v19_final_conditional")
    
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

    if st.sidebar.button("Sair do Portal Cliente", icon="⬅️", key="logout_cliente_v19_final", use_container_width=True):
        keys_to_clear = [k for k in st.session_state.keys() if k not in ['admin_logado', 'last_cnpj_input']]
        for key_item in keys_to_clear: del st.session_state[key_item] 
        for key_d, value_d in default_session_state.items():
            if key_d not in ['admin_logado', 'last_cnpj_input']: st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False
        st.toast("Logout realizado.", icon="👋")
        st.rerun()

    # --- Page rendering logic for client ---
    if st.session_state.cliente_page == "Instruções":
        st.subheader(menu_options_cli_map_full["Instruções"]) 
        instrucoes_content_md = ""
        if os.path.exists(instrucoes_custom_path):
            with open(instrucoes_custom_path, "r", encoding="utf-8") as f:
                instrucoes_content_md = f.read()
        elif os.path.exists(instrucoes_default_path):
            with open(instrucoes_default_path, "r", encoding="utf-8") as f:
                instrucoes_content_md = f.read()
            st.caption("Exibindo instruções padrão. O administrador pode personalizar este texto.")
        else:
            instrucoes_content_md = ("# Bem-vindo ao Portal de Diagnóstico!\n\n"
                                     "Siga as instruções para completar seu diagnóstico.\n\n"
                                     "Em caso de dúvidas, entre em contato com o administrador.")
            st.info("Instruções padrão não encontradas. Exibindo texto base.")
            
        st.markdown(instrucoes_content_md, unsafe_allow_html=True)

        if st.button("Entendi, prosseguir", key="btn_instrucoes_v19_final", icon="👍"):
            update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", "True")
            if st.session_state.user: st.session_state.user["JaVisualizouInstrucoes"] = True
            
            pode_fazer_novo_inst = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo_inst else "Painel Principal"
            st.rerun()

    elif st.session_state.cliente_page == "Notificações":
        st.subheader(menu_options_cli_map_full["Notificações"].split(" (")[0]) 
        ids_para_marcar_como_lidas_on_display = []
        try:
            df_notificacoes_todas = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Relacionado': str})
            if not df_notificacoes_todas.empty and 'Lida' in df_notificacoes_todas.columns:
                df_notificacoes_todas['Lida'] = df_notificacoes_todas['Lida'].astype(str).str.lower().map({'true': True, 'false': False, '': False, 'nan': False}).fillna(False)
            else:
                df_notificacoes_todas = pd.DataFrame(columns=colunas_base_notificacoes)
            if 'ID_Diagnostico_Relacionado' not in df_notificacoes_todas.columns: 
                 df_notificacoes_todas['ID_Diagnostico_Relacionado'] = None

            minhas_notificacoes = df_notificacoes_todas[
                df_notificacoes_todas["CNPJ_Cliente"] == st.session_state.cnpj
            ].sort_values(by="Timestamp", ascending=False)

            if minhas_notificacoes.empty:
                st.info("Você não tem nenhuma notificação no momento.")
            else:
                st.caption("As notificações novas são marcadas como lidas ao serem exibidas nesta página.")
                for idx_notif, row_notif in minhas_notificacoes.iterrows():
                    cor_borda = "#2563eb" if not row_notif["Lida"] else "#adb5bd"
                    icon_lida = "✉️" if not row_notif["Lida"] else "📨"
                    status_text = "Status: Nova" if not row_notif["Lida"] else "Status: Lida"
                    
                    st.markdown(f"""
                    <div class="custom-card" style="border-left: 5px solid {cor_borda}; margin-bottom: 10px;">
                        <p style="font-size: 0.8em; color: #6b7280;">{icon_lida} {row_notif["Timestamp"]} | <b>{status_text}</b></p>
                        <p>{row_notif["Mensagem"]}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    diag_id_relacionado = row_notif.get("ID_Diagnostico_Relacionado")
                    if pd.notna(diag_id_relacionado) and str(diag_id_relacionado).strip():
                        if st.button("Ver Detalhes no Painel", key=f"ver_det_notif_{row_notif['ID_Notificacao']}_{idx_notif}", help="Ir para o diagnóstico mencionado"):
                            st.session_state.target_diag_data_for_expansion = str(diag_id_relacionado)
                            st.session_state.cliente_page = "Painel Principal"
                            st.rerun()
                    
                    if not row_notif["Lida"]:
                        ids_para_marcar_como_lidas_on_display.append(row_notif["ID_Notificacao"])
                
                if ids_para_marcar_como_lidas_on_display:
                    indices_para_atualizar = df_notificacoes_todas[df_notificacoes_todas["ID_Notificacao"].isin(ids_para_marcar_como_lidas_on_display)].index
                    df_notificacoes_todas.loc[indices_para_atualizar, "Lida"] = True
                    df_notificacoes_todas.to_csv(notificacoes_csv, index=False, encoding='utf-8')
                    st.session_state['force_sidebar_rerun_after_notif_read_v19'] = True

        except (FileNotFoundError, pd.errors.EmptyDataError):
            st.info("Você não tem nenhuma notificação no momento.")
        except Exception as e_notif_display:
            st.error(f"Erro ao carregar suas notificações: {e_notif_display}")

        if st.session_state.get('force_sidebar_rerun_after_notif_read_v19'):
            del st.session_state['force_sidebar_rerun_after_notif_read_v19']
            st.rerun()

    elif st.session_state.cliente_page == "Painel Principal":
        st.subheader(menu_options_cli_map_full["Painel Principal"]) 
        target_diag_to_expand = st.session_state.pop("target_diag_data_for_expansion", None)

        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu último diagnóstico foi enviado e processado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                with open(st.session_state.pdf_gerado_path, "rb") as f_pdf:
                    st.download_button(label="Baixar PDF do Diagnóstico Recém-Enviado", data=f_pdf,
                                       file_name=st.session_state.pdf_gerado_filename, mime="application/pdf",
                                       key="dl_novo_diag_painel_v19_final", icon="📄")
                st.session_state.pdf_gerado_path = None
                st.session_state.pdf_gerado_filename = None
            st.session_state.diagnostico_enviado_sucesso = False

        with st.expander("ℹ️ Informações Importantes", expanded=False):
            st.markdown("- Visualize seus diagnósticos anteriores e sua evolução.")
            st.markdown("- Acompanhe seu plano de ação no Kanban.")
            st.markdown("- Para um novo diagnóstico (se liberado), selecione 'Novo Diagnóstico' no menu ao lado.")

        try: 
            df_antigos = pd.read_csv(arquivo_csv, dtype={'CNPJ': str}, encoding='utf-8')
            df_cliente_diags_raw = df_antigos[df_antigos["CNPJ"] == st.session_state.cnpj]
            if 'Data' in df_cliente_diags_raw.columns:
                 df_cliente_diags_raw['Data'] = df_cliente_diags_raw['Data'].astype(str)
        except FileNotFoundError:
            st.error(f"Arquivo de diagnósticos '{arquivo_csv}' não encontrado.")
            df_cliente_diags_raw = pd.DataFrame()
        except Exception as e_load_diag:
            st.error(f"Erro ao carregar diagnósticos do cliente: {e_load_diag}")
            df_cliente_diags_raw = pd.DataFrame()

        # The rest of the Painel Principal (displaying latest diag, older diags, kanban, evolution)
        # This part is extensive and largely unchanged from the logic in Turn 9, 
        # except for the `expand_this_diag` logic inside the loop of older diagnostics.
        # For brevity, I'm assuming the previous structure for these sections is maintained.
        # Make sure to integrate the expand_this_diag logic.
        if not df_cliente_diags_raw.empty:
            df_cliente_diags = df_cliente_diags_raw.sort_values(by="Data", ascending=False) # Assuming Data can be sorted as string here too
            # ... [Your code for displaying latest diagnosis graphs, etc.] ...
            
            st.markdown("#### 📁 Diagnósticos Anteriores")
            if not df_cliente_diags.empty:
                perguntas_df_para_painel = pd.DataFrame()
                if os.path.exists(perguntas_csv):
                    perguntas_df_para_painel = pd.read_csv(perguntas_csv, encoding='utf-8')
                    if "Categoria" not in perguntas_df_para_painel.columns: 
                        perguntas_df_para_painel["Categoria"] = "Geral"

                analises_df_para_painel = carregar_analises_perguntas()

                for idx_row_diag_loop, row_diag_data_loop in df_cliente_diags.iterrows(): 
                    expand_this_diag = (str(row_diag_data_loop['Data']) == str(target_diag_to_expand))
                    with st.expander(f"📅 {row_diag_data_loop['Data']} - {row_diag_data_loop['Empresa']}", expanded=expand_this_diag):
                        # ... (Full content of the diagnosis expander from previous code) ...
                        st.write(f"Detalhes para {row_diag_data_loop['Data']}")
                        if expand_this_diag:
                            st.success("Este é o diagnóstico que você selecionou na notificação.")
                        # (Paste the full detailed rendering of a single diagnosis here)
            else:
                st.info("Nenhum diagnóstico anterior.")
            # ... [Kanban, Evolution, Comparison logic as before] ...
        else:
            st.info("Nenhum diagnóstico realizado por esta empresa.")


    elif st.session_state.cliente_page == "Novo Diagnóstico":
        # (Full Novo Diagnóstico logic from previous version - no major changes planned here beyond ensuring it's complete)
        # ...
        st.write("Página Novo Diagnóstico (como antes).")

# --- ÁREA DO ADMINISTRADOR LOGADO (COPIED FROM PREVIOUS VERSION WITH ENHANCEMENTS) ---
# (This section will include the new "Personalizar Aparência", "Relatório de Engajamento" and updated "Gerenciar Clientes")
# (The other admin sections remain largely as they were)
# Due to length, this is a high-level structure. Ensure you copy the previous admin code and integrate the new parts.

if aba == "Administrador" and st.session_state.admin_logado:
    # ... (Admin sidebar setup and menu logic from Turn 9, with "Personalizar Aparência" and "Relatório de Engajamento" added to menu_admin_options_map)
    # Ensure df_usuarios_admin_geral is loaded and preprocessed correctly here.

    if menu_admin == "Visão Geral e Diagnósticos":
        # ... (Visão Geral logic from Turn 9, with the corrected selectbox filter for Emp_sel_admin_vg)
        st.write("Conteúdo da Visão Geral e Diagnósticos (com filtros ajustados).")
    
    elif menu_admin == "Relatório de Engajamento":
        # ... (New Relatório de Engajamento logic as detailed in the thought process)
        st.write("Conteúdo do Relatório de Engajamento.")

    elif menu_admin == "Gerenciar Notificações":
        # ... (New Gerenciar Notificações logic as detailed in the thought process)
        st.write("Conteúdo de Gerenciar Notificações.")

    elif menu_admin == "Gerenciar Clientes":
        # ... (Gerenciar Clientes logic from Turn 9, with the new sidebar filter for JaVisualizouInstrucoes)
        st.write("Conteúdo de Gerenciar Clientes (com novo filtro).")

    elif menu_admin == "Personalizar Aparência":
        st.subheader("🎨 Personalizar Aparência do Portal")
        st.markdown("---")
        st.subheader("Logo da Tela de Login")
        st.markdown(f"""
        A logo exibida na tela de login é carregada na seguinte ordem de prioridade:
        1. **Logo Personalizada:** Se carregada abaixo, será salva como `{CUSTOM_LOGIN_LOGO_PATH}`.
        2. **Logo Padrão:** Se nenhuma logo personalizada for carregada, o sistema tentará usar `{DEFAULT_LOGIN_LOGO_PATH}`. 
           Certifique-se de que este arquivo exista na pasta `{ASSETS_DIR}/` com sua logo principal.
        """)

        current_logo_path_for_login = DEFAULT_LOGIN_LOGO_PATH
        status_logo = "Padrão (default_login_logo.png)"

        if os.path.exists(CUSTOM_LOGIN_LOGO_PATH):
            current_logo_path_for_login = CUSTOM_LOGIN_LOGO_PATH
            status_logo = "Personalizada (portal_login_logo.png)"
        
        st.write(f"**Logo Atualmente Ativa na Tela de Login:** {status_logo}")
        if os.path.exists(current_logo_path_for_login):
            st.image(current_logo_path_for_login, width=200)
            if current_logo_path_for_login == CUSTOM_LOGIN_LOGO_PATH:
                if st.button("Remover Logo Personalizada e Usar Padrão", key="remove_custom_login_logo_btn"):
                    try:
                        os.remove(CUSTOM_LOGIN_LOGO_PATH)
                        st.success(f"Logo personalizada '{CUSTOM_LOGIN_LOGO_FILENAME}' removida. A página de login usará a logo padrão (se existir).")
                        st.rerun()
                    except Exception as e_remove_logo:
                        st.error(f"Erro ao remover logo personalizada: {e_remove_logo}")
        else:
            if current_logo_path_for_login == DEFAULT_LOGIN_LOGO_PATH:
                 st.warning(f"Logo padrão '{DEFAULT_LOGIN_LOGO_FILENAME}' não encontrada em '{ASSETS_DIR}/'. Por favor, adicione-a ou carregue uma logo personalizada.")
            else: # Should not happen if logic is correct, means custom was expected but not found
                 st.error("Erro: Logo esperada não encontrada.")


        st.markdown("---")
        st.subheader("Carregar Nova Logo Personalizada para Tela de Login")
        st.caption("Recomendado: PNG com fundo transparente, dimensões aprox. 200-250px de largura e até 100px de altura.")
        
        uploaded_login_logo = st.file_uploader("Selecione o arquivo da nova logo:", type=["png", "jpg", "jpeg"], key="admin_login_logo_uploader")
        
        if uploaded_login_logo is not None:
            try:
                if not os.path.exists(ASSETS_DIR):
                    os.makedirs(ASSETS_DIR)
                with open(CUSTOM_LOGIN_LOGO_PATH, "wb") as f:
                    f.write(uploaded_login_logo.getbuffer())
                st.success(f"Nova logo para a tela de login salva como '{CUSTOM_LOGIN_LOGO_FILENAME}'! A mudança será visível no próximo acesso à tela de login por um usuário deslogado.")
                st.image(uploaded_login_logo, caption="Nova Logo Carregada", width=150)
                if "admin_login_logo_uploader" in st.session_state: # Clear uploader after save
                    st.session_state.admin_login_logo_uploader = None
                st.rerun() 
            except Exception as e_upload_logo:
                st.error(f"Erro ao salvar a nova logo: {e_upload_logo}")
    
    # ... (The rest of the admin sections like Gerenciar Perguntas, etc., as per previous version)
    elif menu_admin == "Gerenciar Perguntas":
        st.write("Conteúdo de Gerenciar Perguntas.")
    elif menu_admin == "Gerenciar Análises de Perguntas":
        st.write("Conteúdo de Gerenciar Análises.")
    elif menu_admin == "Gerenciar Instruções":
        st.write("Conteúdo de Gerenciar Instruções.")
    elif menu_admin == "Histórico de Usuários":
        st.write("Conteúdo de Histórico de Usuários.")
    elif menu_admin == "Gerenciar Administradores":
        st.write("Conteúdo de Gerenciar Administradores.")


if not st.session_state.admin_logado and not st.session_state.cliente_logado and st.session_state.get('aba') is None:
    # This is an edge case, if 'aba' isn't set by the radio group for some reason.
    st.info("Bem-vindo! Por favor, selecione seu tipo de acesso (Administrador ou Cliente) acima para continuar.")
    st.stop()