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
    "admin_user_details": None, # Para armazenar detalhes do admin logado, incluindo permissões
    "login_selection_aba": "Cliente" # Para o radio da tela de login
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
                for col, default_val in defaults.items():
                    if col in columns:
                        if pd.isna(default_val):
                            df_init[col] = pd.Series(dtype='object')
                        else:
                            df_init[col] = pd.Series(dtype=type(default_val))
                        if len(df_init[col]) == 0 and not pd.isna(default_val) : 
                            df_init.loc[0, col] = default_val
                            df_init = df_init.iloc[0:0] 
            df_init.to_csv(filepath, index=False, encoding='utf-8')
        else: # File exists and is not empty
            dtype_spec = {}
            if filepath == admin_credenciais_csv: # Specific handling for admin CSV
                dtype_spec = {'Usuario': str, 'Senha': str}
                for perm_key in ALL_ADMIN_PERMISSION_KEYS:
                    dtype_spec[perm_key] = bool # Explicitly bool for permissions
            elif filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, historico_csv, pesquisa_satisfacao_respostas_csv]:
                if 'CNPJ' in columns: dtype_spec['CNPJ'] = str
                if 'CNPJ_Cliente' in columns: dtype_spec['CNPJ_Cliente'] = str
            if filepath == notificacoes_csv and 'ID_Diagnostico_Relacionado' in columns:
                dtype_spec['ID_Diagnostico_Relacionado'] = str
            if filepath == arquivo_csv and 'ID_Diagnostico' in columns:
                dtype_spec['ID_Diagnostico'] = str
            if filepath == pesquisa_satisfacao_respostas_csv and 'ID_Diagnostico_Associado' in columns:
                dtype_spec['ID_Diagnostico_Associado'] = str
            
            try:
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)
            except ValueError as ve: 
                st.warning(f"Problema ao ler {filepath} com dtypes específicos ({ve}), tentando leitura genérica.")
                df_init = pd.read_csv(filepath, encoding='utf-8') 
            except Exception as read_e: 
                st.warning(f"Problema ao ler {filepath}, tentando recriar com colunas esperadas: {read_e}")
                df_init = pd.DataFrame(columns=columns) 
                if defaults: 
                    for col, default_val in defaults.items():
                        if col in columns:
                            if pd.isna(default_val): df_init[col] = pd.Series(dtype='object')
                            else: df_init[col] = pd.Series(dtype=type(default_val))
                            if len(df_init[col]) == 0 and not pd.isna(default_val):
                                df_init.loc[0, col] = default_val
                                df_init = df_init.iloc[0:0]
                df_init.to_csv(filepath, index=False, encoding='utf-8') 
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)

            made_changes = False
            current_cols = df_init.columns.tolist()
            for col_idx, col_name in enumerate(columns):
                if col_name not in current_cols:
                    default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                    
                    if len(df_init) > 0 and not df_init.empty: 
                        col_insert_dtype = object
                        if not pd.isna(default_val):
                            col_insert_dtype = type(default_val)
                        
                        insert_values = [default_val] * len(df_init)
                        try:
                            df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=pd.Series(insert_values, dtype=col_insert_dtype, index=df_init.index))
                        except Exception as e_insert: 
                            df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=insert_values)
                    else: 
                        df_init[col_name] = pd.Series(dtype=object if pd.isna(default_val) else type(default_val))
                        if not pd.isna(default_val) and df_init.empty: 
                            df_init.loc[0, col_name] = default_val
                            df_init = df_init.iloc[0:0]
                    made_changes = True
            if made_changes:
                # Se for o admin_credenciais_csv, garantir que as colunas de permissão são booleanas antes de salvar
                if filepath == admin_credenciais_csv:
                    for perm_col_save in ALL_ADMIN_PERMISSION_KEYS:
                        if perm_col_save in df_init.columns:
                            df_init[perm_col_save] = df_init[perm_col_save].fillna(False).astype(bool)
                df_init.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError: 
        df_init = pd.DataFrame(columns=columns)
        if defaults:
            for col, default_val in defaults.items():
                if col in columns:
                    if pd.isna(default_val): df_init[col] = pd.Series(dtype='object')
                    else: df_init[col] = pd.Series(dtype=type(default_val))
                    if len(df_init[col]) == 0 and not pd.isna(default_val):
                        df_init.loc[0, col] = default_val
                        df_init = df_init.iloc[0:0]
        df_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e: st.error(f"Erro crítico ao inicializar {filepath}: {e}"); raise

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    
    admin_defaults = {"Senha": "admin"} # Senha padrão inicial, deve ser mudada
    for perm_key in ALL_ADMIN_PERMISSION_KEYS:
        admin_defaults[perm_key] = True # Superadmin inicial tem todas as permissões
    inicializar_csv(admin_credenciais_csv, colunas_base_admin_credenciais, defaults=admin_defaults)

    # Verificar se o admin_credenciais_csv está realmente vazio (após criação inicial)
    # e adicionar um superadmin se necessário.
    try:
        df_admins_check_init = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
        if df_admins_check_init.empty:
            super_admin_data_init = {"Usuario": "admin"}
            super_admin_data_init.update(admin_defaults) # Inclui a senha e todas as permissões como True
            df_super_admin_init = pd.DataFrame([super_admin_data_init])
            df_super_admin_init.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
            print("INFO: Superadministrador padrão ('admin'/'admin') criado/verificado.")
        else: # Garantir que admins existentes tenham todas as colunas de permissão
            made_changes_admin_perms_init = False
            for perm_key_init in ALL_ADMIN_PERMISSION_KEYS:
                if perm_key_init not in df_admins_check_init.columns:
                    df_admins_check_init[perm_key_init] = False # Adiciona com False para admins existentes
                    made_changes_admin_perms_init = True
            if made_changes_admin_perms_init:
                df_admins_check_init.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')

    except Exception as e_admin_init_check:
        st.error(f"Erro ao verificar/criar superadministrador durante inicialização: {e_admin_init_check}")


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
    st.stop()

# --- Funções Utilitárias (registrar_acao, update_user_data, carregar_analises_perguntas, etc. mantidas como estavam) ---
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
        df["Ativa"] = df["Ativa"].fillna(True).astype(bool)
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

# --- (obter_analise_para_resposta e gerar_pdf_diagnostico_completo mantidas como estavam) ---
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
        with st.spinner("Gerando PDF do diagnóstico... Aguarde."):
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
                for cat, media in medias_cat.items(): pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat}: {media:.2f}")); pdf.ln(1)
                pdf.ln(5)

            for titulo, campo in [("Resumo (Cliente):", "Diagnóstico"), ("Análise (Cliente):", "Análise do Cliente"), ("Comentários (Consultor):", "Comentarios_Admin")]:
                valor = diag_data.get(campo, "")
                if valor and not pd.isna(valor) and str(valor).strip():
                    pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output(titulo))
                    pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(str(valor))); pdf.ln(3)

            pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 10, pdf_safe_text_output("Respostas Detalhadas e Análises:"))
            categorias = []
            if not perguntas_df.empty and "Categoria" in perguntas_df.columns:
                perguntas_df['Categoria'] = perguntas_df['Categoria'].astype(str).fillna('Geral')
                categorias = sorted(perguntas_df["Categoria"].unique())

            for categoria in categorias:
                pdf.set_font("Arial", 'B', 10); pdf.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria}")); pdf.set_font("Arial", size=9)
                perg_cat = perguntas_df[perguntas_df["Categoria"] == categoria]
                for _, p_row in perg_cat.iterrows():
                    p_texto = p_row["Pergunta"]
                    resp = respostas_coletadas.get(p_texto, diag_data.get(sanitize_column_name(p_texto), "N/R")) 
                    analise_texto = None
                    if "[Matriz GUT]" in p_texto:
                        g,u,t,score=0,0,0,0
                        if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                        elif isinstance(resp, str): 
                            try: 
                                data_gut=json.loads(resp.replace("'",'"'))
                                g,u,t=int(data_gut.get("G",0)),int(data_gut.get("U",0)),int(data_gut.get("T",0))
                            except: pass
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

            if "TimingsPerguntasJSON" in diag_data and pd.notna(diag_data["TimingsPerguntasJSON"]):
                try:
                    timings = json.loads(diag_data["TimingsPerguntasJSON"])
                    if timings:
                        pdf.add_page()
                        pdf.set_font("Arial", 'B', 12)
                        pdf.cell(0, 10, pdf_safe_text_output("Tempo Gasto por Pergunta no Diagnóstico"), 0, 1, 'C')
                        pdf.ln(5)
                        pdf.set_font("Arial", size=9)
                        for pergunta_pdf, tempo_seg_pdf in timings.items():
                                pdf.multi_cell(0, 5, pdf_safe_text_output(f"- {pergunta_pdf}: {float(tempo_seg_pdf):.2f} segundos"))
                        pdf.ln(3)
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass 

            pdf.add_page(); pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf.ln(5); pdf.set_font("Arial", size=10)
            gut_cards = []
            if not perguntas_df.empty:
                for _, p_row in perguntas_df.iterrows():
                    p_texto = p_row["Pergunta"]
                    if "[Matriz GUT]" in p_texto:
                        resp = respostas_coletadas.get(p_texto, diag_data.get(sanitize_column_name(p_texto))) 
                        g,u,t,score=0,0,0,0
                        if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                        elif isinstance(resp, str):
                            try:
                                data_gut=json.loads(resp.replace("'",'"'))
                                g,u,t=int(data_gut.get("G",0)),int(data_gut.get("U",0)),int(data_gut.get("T",0))
                            except: pass
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

# --- LOGIN AND MAIN NAVIGATION ---
# Shared placeholder for the top part (logo and radio)
top_login_placeholder = st.empty()

# Placeholders for admin and client forms, to be shown one at a time
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
            key="tipo_usuario_radio_v22_login_selection", 
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
            with st.form("form_admin_login_v22_final"):
                u = st.text_input("Usuário", key="admin_u_v22_final_input")
                p = st.text_input("Senha", type="password", key="admin_p_v22_final_input")
                if st.form_submit_button("Entrar", use_container_width=True, icon="🔑"):
                    try:
                        df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                        for perm_col_login in ALL_ADMIN_PERMISSION_KEYS: # Garantir colunas de permissão
                            if perm_col_login not in df_creds.columns:
                                df_creds[perm_col_login] = False 
                            df_creds[perm_col_login] = df_creds[perm_col_login].fillna(False).astype(bool)

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
            with st.form("form_cliente_login_v22_final"):
                c = st.text_input("CNPJ", key="cli_c_v22_final_input", value=st.session_state.get("last_cnpj_input",""))
                s = st.text_input("Senha", type="password", key="cli_s_v22_final_input")
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
                        if c in blocked_df["CNPJ"].values: 
                            st.error("CNPJ bloqueado.")
                        else:
                            match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == s)]
                            if not match.empty:
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
                                
                                st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                                # Resetar estados específicos do diagnóstico
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


# --- ÁREA DO CLIENTE LOGADO (Mantida como estava, pois não foi foco da alteração)---
if aba == "Cliente" and st.session_state.cliente_logado:
    # ... (Todo o código da área do cliente, como no original) ...
    if 'user' not in st.session_state or not st.session_state.user:
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
            df_notif_check = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Relacionado': str})
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
        "Suporte/FAQ": "💬 Suporte/FAQ", 
        "Pesquisa de Satisfação": "🌟 Pesquisa de Satisfação", 
        "Notificações": notificacoes_label
    }
    
    if not st.session_state.user.get("JaVisualizouInstrucoes", False):
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
        st.session_state.cliente_page = "Instruções" if not st.session_state.user.get("JaVisualizouInstrucoes", False) else "Painel Principal"

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

    selected_page_cli_raw = st.sidebar.radio("Menu Cliente", menu_options_cli_display, index=current_idx_cli, key="cli_menu_v21_final_conditional_key")
    
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

    if st.sidebar.button("Sair do Portal Cliente", icon="⬅️", key="logout_cliente_v21_final_btn", use_container_width=True):
        keys_to_clear = [k for k in st.session_state.keys() if k not in ['admin_logado', 'last_cnpj_input', 'login_selection_aba']] # Manter login_selection_aba
        for key_item in keys_to_clear: del st.session_state[key_item] 
        for key_d, value_d in default_session_state.items():
            if key_d not in ['admin_logado', 'last_cnpj_input', 'login_selection_aba']: st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False
        st.toast("Logout realizado.", icon="👋")
        st.rerun()
    
    # --- CLIENT PAGE CONTENT (Mantido como estava no original) ---
    if st.session_state.cliente_page == "Instruções":
        st.header("📖 Instruções do Portal")
        instrucoes_content = ""
        if os.path.exists(instrucoes_custom_path):
            with open(instrucoes_custom_path, "r", encoding="utf-8") as f:
                instrucoes_content = f.read()
        elif os.path.exists(instrucoes_default_path):
            with open(instrucoes_default_path, "r", encoding="utf-8") as f:
                instrucoes_content = f.read()
        else:
            instrucoes_content = "Bem-vindo ao Portal de Diagnóstico! Use o menu à esquerda para navegar. Se precisar de ajuda, contate o administrador."
        
        st.markdown(instrucoes_content, unsafe_allow_html=True)
        st.markdown("---")
        if not st.session_state.user.get("JaVisualizouInstrucoes", False):
            if st.button("Entendi, ir para o portal!", key="cliente_entendeu_instrucoes_v21", type="primary"):
                update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", "True")
                st.session_state.user["JaVisualizouInstrucoes"] = True
                pode_fazer_novo = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
                st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo else "Painel Principal"
                st.rerun()

    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.header("📋 Novo Diagnóstico Empresarial")
        if st.session_state.diagnostico_enviado_sucesso:
            st.success("Diagnóstico enviado com sucesso! Você pode visualizá-lo no Painel Principal.")
            st.markdown("---")
            st.subheader("🌟 Pesquisa de Satisfação")
            st.write("Gostaríamos de ouvir sua opinião sobre o processo de diagnóstico.")
            if st.button("Responder Pesquisa de Satisfação", key="responder_pesquisa_pos_diag_v21"):
                st.session_state.cliente_page = "Pesquisa de Satisfação"
                st.session_state.survey_id_diagnostico_associado = st.session_state.id_formulario_atual 
                st.rerun()

            if st.button("Voltar ao Painel Principal", key="novo_diag_voltar_painel_v21"):
                st.session_state.diagnostico_enviado_sucesso = False 
                st.session_state.cliente_page = "Painel Principal"
                st.rerun()
            st.stop()

        pode_fazer_novo = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
        if not pode_fazer_novo:
            st.warning("Você já utilizou todos os seus diagnósticos disponíveis. Entre em contato com o administrador para mais informações.")
            st.stop()
        
        try:
            perg_df = pd.read_csv(perguntas_csv, encoding='utf-8')
            if perg_df.empty:
                st.warning("Nenhuma pergunta de diagnóstico configurada. Contate o administrador.")
                st.stop()
        except FileNotFoundError:
            st.error(f"Arquivo de perguntas '{perguntas_csv}' não encontrado. Contate o administrador.")
            st.stop()

        total_perguntas = len(perg_df)
        st.session_state.progresso_diagnostico_contagem = (len(st.session_state.respostas_atuais_diagnostico), total_perguntas)

        st.progress(st.session_state.progresso_diagnostico_percentual / 100, 
                    text=f"Progresso: {st.session_state.progresso_diagnostico_contagem[0]}/{st.session_state.progresso_diagnostico_contagem[1]} perguntas")

        analises_df_cached = carregar_analises_perguntas()

        with st.form(key="diagnostico_form_v21"):
            respostas_cliente = st.session_state.respostas_atuais_diagnostico
            
            for index, row in perg_df.iterrows():
                pergunta = row["Pergunta"]
                categoria_pergunta = row.get("Categoria", "Geral")

                if st.session_state.previous_question_text_tracker != pergunta:
                    if st.session_state.current_question_start_time is not None and st.session_state.previous_question_text_tracker is not None:
                        time_spent = time.time() - st.session_state.current_question_start_time
                        st.session_state.diagnostic_question_timings[st.session_state.previous_question_text_tracker] = round(time_spent, 2)
                    
                    st.session_state.current_question_start_time = time.time()
                    st.session_state.previous_question_text_tracker = pergunta
                elif st.session_state.current_question_start_time is None : 
                    st.session_state.current_question_start_time = time.time()
                    st.session_state.previous_question_text_tracker = pergunta


                st.markdown(f"##### {pergunta}")
                st.caption(f"Categoria: {categoria_pergunta}")

                if "[Matriz GUT]" in pergunta:
                    default_gut = respostas_cliente.get(pergunta, {"G":1, "U":1, "T":1})
                    c1, c2, c3 = st.columns(3)
                    g = c1.radio("Gravidade", [1,2,3,4,5], index=default_gut["G"]-1, key=f"G_{index}_v21", horizontal=True)
                    u = c2.radio("Urgência", [1,2,3,4,5], index=default_gut["U"]-1, key=f"U_{index}_v21", horizontal=True)
                    t = c3.radio("Tendência", [1,2,3,4,5], index=default_gut["T"]-1, key=f"T_{index}_v21", horizontal=True)
                    respostas_cliente[pergunta] = {"G": g, "U": u, "T": t}
                else:
                    opcoes_escala = ["1 - Muito Ruim", "2 - Ruim", "3 - Regular", "4 - Bom", "5 - Excelente"]
                    default_value_escala = respostas_cliente.get(pergunta, opcoes_escala[2]) 
                    if not isinstance(default_value_escala, str) and default_value_escala in range(1,6): 
                        default_value_escala = opcoes_escala[default_value_escala -1]

                    resposta_escala = st.radio("Selecione sua avaliação:", opcoes_escala, 
                                            index=opcoes_escala.index(default_value_escala) if default_value_escala in opcoes_escala else 2, 
                                            key=f"R_{index}_v21", horizontal=True)
                    respostas_cliente[pergunta] = resposta_escala

                analise_imediata = obter_analise_para_resposta(pergunta, 
                                                            int(respostas_cliente[pergunta].split(" - ")[0]) if isinstance(respostas_cliente[pergunta], str) and " - " in respostas_cliente[pergunta] else (respostas_cliente[pergunta]['G']*respostas_cliente[pergunta]['U']*respostas_cliente[pergunta]['T'] if isinstance(respostas_cliente[pergunta], dict) else respostas_cliente[pergunta]), 
                                                            analises_df_cached)
                if analise_imediata:
                    st.markdown(f"<div class='analise-pergunta-cliente'>💡 <b>Análise Rápida:</b> {analise_imediata}</div>", unsafe_allow_html=True)
                st.markdown("---")
            
            st.session_state.respostas_atuais_diagnostico = respostas_cliente
            num_respondidas = len([r for r in respostas_cliente.values() if r is not None and r != ""])
            st.session_state.progresso_diagnostico_contagem = (num_respondidas, total_perguntas)
            if total_perguntas > 0:
                st.session_state.progresso_diagnostico_percentual = (num_respondidas / total_perguntas) * 100

            st.markdown("### Informações Adicionais")
            diagnostico_resumo = st.text_area("Resumo do Diagnóstico (sua percepção geral):", height=100, key="diag_resumo_v21", value=st.session_state.get("diag_resumo_val", ""))
            analise_cliente_txt = st.text_area("Sua Análise e Próximos Passos Sugeridos:", height=100, key="analise_cliente_v21", value=st.session_state.get("analise_cliente_val", ""))
            
            st.session_state.diag_resumo_val = diagnostico_resumo
            st.session_state.analise_cliente_val = analise_cliente_txt

            if st.form_submit_button("✅ Enviar Diagnóstico Completo", type="primary", use_container_width=True):
                if st.session_state.current_question_start_time is not None and st.session_state.previous_question_text_tracker is not None: 
                    time_spent_last = time.time() - st.session_state.current_question_start_time
                    st.session_state.diagnostic_question_timings[st.session_state.previous_question_text_tracker] = round(time_spent_last, 2)

                all_data = []
                medias_por_categoria = {}
                soma_geral = 0; contador_geral = 0
                soma_gut = 0; contador_gut = 0
                
                categorias_presentes = perg_df["Categoria"].unique()
                for cat_iter in categorias_presentes:
                    medias_por_categoria[cat_iter] = {"soma":0, "contador":0}

                nova_entrada = {
                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "CNPJ": st.session_state.cnpj,
                    "Nome": st.session_state.user.get("NomeContato", ""),
                    "Email": st.session_state.user.get("Email", ""), 
                    "Empresa": st.session_state.user.get("Empresa", ""),
                    "ID_Diagnostico": st.session_state.id_formulario_atual 
                }

                for pergunta_key, resposta_data in respostas_cliente.items():
                    col_name_sanitized = sanitize_column_name(pergunta_key)
                    nova_entrada[col_name_sanitized] = resposta_data

                    categoria_da_pergunta_atual = perg_df[perg_df["Pergunta"] == pergunta_key]["Categoria"].iloc[0] if not perg_df[perg_df["Pergunta"] == pergunta_key].empty else "Geral"

                    if isinstance(resposta_data, dict) and "G" in resposta_data: 
                        score_gut = resposta_data["G"] * resposta_data["U"] * resposta_data["T"]
                        nova_entrada[f"{col_name_sanitized}_Score"] = score_gut
                        soma_gut += score_gut; contador_gut +=1
                    elif isinstance(resposta_data, str) and " - " in resposta_data: 
                        try:
                            valor_numerico = int(resposta_data.split(" - ")[0])
                            soma_geral += valor_numerico; contador_geral +=1
                            medias_por_categoria[categoria_da_pergunta_atual]["soma"] += valor_numerico
                            medias_por_categoria[categoria_da_pergunta_atual]["contador"] += 1
                        except ValueError: pass 
                
                nova_entrada["Média Geral"] = f"{soma_geral/contador_geral:.2f}" if contador_geral > 0 else "N/A"
                nova_entrada["GUT Média"] = f"{soma_gut/contador_gut:.2f}" if contador_gut > 0 else "N/A"
                
                for cat_final, data_cat_final in medias_por_categoria.items():
                    media_cat_val = data_cat_final["soma"] / data_cat_final["contador"] if data_cat_final["contador"] > 0 else 0
                    nova_entrada[f"Media_Cat_{sanitize_column_name(cat_final)}"] = f"{media_cat_val:.2f}"

                nova_entrada["Diagnóstico"] = diagnostico_resumo
                nova_entrada["Análise do Cliente"] = analise_cliente_txt
                nova_entrada["Comentarios_Admin"] = "" 
                nova_entrada["TimingsPerguntasJSON"] = json.dumps(st.session_state.diagnostic_question_timings)

                try:
                    df_diagnosticos = pd.read_csv(arquivo_csv, dtype={'CNPJ': str, 'ID_Diagnostico':str}, encoding='utf-8')
                except (FileNotFoundError, pd.errors.EmptyDataError):
                    df_diagnosticos = pd.DataFrame(columns=colunas_base_diagnosticos) 

                for col_key_add in nova_entrada.keys():
                    if col_key_add not in df_diagnosticos.columns:
                        df_diagnosticos[col_key_add] = pd.NA 

                df_diagnosticos = pd.concat([df_diagnosticos, pd.DataFrame([nova_entrada])], ignore_index=True)
                df_diagnosticos.to_csv(arquivo_csv, index=False, encoding='utf-8')
                
                novo_total_realizados = st.session_state.user.get("TotalDiagnosticosRealizados", 0) + 1
                update_user_data(st.session_state.cnpj, "TotalDiagnosticosRealizados", novo_total_realizados)
                
                registrar_acao(st.session_state.cnpj, "Diagnóstico Enviado", f"ID: {st.session_state.id_formulario_atual}")
                st.session_state.diagnostico_enviado_sucesso = True
                
                st.session_state.respostas_atuais_diagnostico = {}
                st.session_state.progresso_diagnostico_percentual = 0
                st.session_state.progresso_diagnostico_contagem = (0, total_perguntas)
                st.session_state.diagnostic_question_timings = {}
                st.session_state.current_question_start_time = None
                st.session_state.previous_question_text_tracker = None
                st.session_state.diag_resumo_val = ""
                st.session_state.analise_cliente_val = ""
                st.rerun()

    elif st.session_state.cliente_page == "Painel Principal":
        st.header("🏠 Painel Principal do Cliente")
        st.markdown(f"Olá, **{st.session_state.user.get('NomeContato', 'Usuário')}**! Aqui você pode ver seus diagnósticos anteriores.")
        # ... (Resto do código do Painel Principal do Cliente, como no original)
        try:
            df_diagnosticos_cliente = pd.read_csv(arquivo_csv, dtype={'CNPJ': str, 'ID_Diagnostico':str}, encoding='utf-8')
            df_diagnosticos_cliente = df_diagnosticos_cliente[df_diagnosticos_cliente["CNPJ"] == st.session_state.cnpj].sort_values(by="Data", ascending=False)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df_diagnosticos_cliente = pd.DataFrame()
        
        if df_diagnosticos_cliente.empty:
            st.info("Você ainda não realizou nenhum diagnóstico.")
        else:
            st.subheader("Seus Diagnósticos Realizados:")
            df_display_cliente_cols = ["Data", "Média Geral", "GUT Média", "ID_Diagnostico"]
            for col_disp_check in df_display_cliente_cols:
                if col_disp_check not in df_diagnosticos_cliente.columns:
                    df_diagnosticos_cliente[col_disp_check] = "N/D" 

            df_display_cliente = df_diagnosticos_cliente[df_display_cliente_cols].copy()
            df_display_cliente.columns = ["Data da Realização", "Média Geral de Satisfação", "Média GUT de Prioridades", "ID do Diagnóstico"]
            
            if st.session_state.get("target_diag_data_for_expansion") is not None:
                target_id = st.session_state.target_diag_data_for_expansion.get("ID_Diagnostico")
                diag_data_expanded = st.session_state.target_diag_data_for_expansion 
                with st.expander(f"👇 Detalhes do Diagnóstico: {diag_data_expanded.get('Data')} (ID: {target_id}) - Expandido via Notificação", expanded=True):
                    st.markdown(f"**Data:** {diag_data_expanded.get('Data', 'N/A')}")
                    st.markdown(f"**Média Geral (Satisfação):** {diag_data_expanded.get('Média Geral', 'N/A')}")
                    st.markdown(f"**Média GUT (Prioridades):** {diag_data_expanded.get('GUT Média', 'N/A')}")
                    if pd.notna(diag_data_expanded.get('Diagnóstico')): st.markdown(f"**Resumo Cliente:** {diag_data_expanded.get('Diagnóstico')}")
                    if pd.notna(diag_data_expanded.get('Análise do Cliente')): st.markdown(f"**Análise Cliente:** {diag_data_expanded.get('Análise do Cliente')}")
                    if pd.notna(diag_data_expanded.get('Comentarios_Admin')): st.markdown(f"**Comentários do Consultor:** {diag_data_expanded.get('Comentarios_Admin')}", help="Feedback fornecido pelo administrador/consultor.")
                    else: st.caption("Nenhum comentário do consultor ainda.")

                    perg_df_painel = pd.read_csv(perguntas_csv, encoding='utf-8') if os.path.exists(perguntas_csv) else pd.DataFrame()
                    analises_df_painel = carregar_analises_perguntas()
                    
                    respostas_coletadas_painel = {}
                    medias_cat_painel = {} 
                    for col, val_expanded in diag_data_expanded.items():
                        original_col_name = None 
                        if not perg_df_painel.empty:
                            match_perg = perg_df_painel[perg_df_painel['Pergunta'].apply(sanitize_column_name) == col]
                            if not match_perg.empty:
                                original_col_name = match_perg['Pergunta'].iloc[0]
                        
                        if original_col_name and col not in colunas_base_diagnosticos and not col.startswith("Media_Cat_") and not col.endswith("_Score") and col != "TimingsPerguntasJSON":
                            respostas_coletadas_painel[original_col_name] = val_expanded 
                        if col.startswith("Media_Cat_"):
                            medias_cat_painel[col.replace("Media_Cat_","").replace("_"," ")] = float(val_expanded) if pd.notna(val_expanded) else 0.0

                    if st.button("Gerar PDF Completo deste Diagnóstico", key=f"pdf_expanded_{diag_data_expanded.get('ID_Diagnostico','exp')}", type="primary"):
                        pdf_path = gerar_pdf_diagnostico_completo(diag_data_expanded, st.session_state.user, perg_df_painel, respostas_coletadas_painel, medias_cat_painel, analises_df_painel)
                        if pdf_path:
                            with open(pdf_path, "rb") as fp:
                                st.download_button(label="Baixar PDF Gerado", data=fp, file_name=f"Diagnostico_{st.session_state.user.get('Empresa','Cliente')}_{str(diag_data_expanded.get('Data','')).split(' ')[0]}.pdf", mime="application/pdf")
                            try: os.remove(pdf_path) 
                            except: pass
                    st.markdown("---")
                st.session_state.target_diag_data_for_expansion = None

            for index_loop, row_diag in df_display_cliente.iterrows(): 
                diag_id_atual = row_diag["ID do Diagnóstico"]
                diag_data_completa_series = df_diagnosticos_cliente[df_diagnosticos_cliente["ID_Diagnostico"] == diag_id_atual]
                if diag_data_completa_series.empty: continue
                diag_data_completa = diag_data_completa_series.iloc[0].to_dict()

                with st.expander(f"Diagnóstico de {row_diag['Data da Realização']} (ID: {diag_id_atual})"):
                    st.markdown(f"**Data:** {diag_data_completa.get('Data', 'N/A')}")
                    st.metric("Média Geral (Satisfação)", value=diag_data_completa.get('Média Geral', "N/A"))
                    st.metric("Média GUT (Prioridades)", value=diag_data_completa.get('GUT Média', "N/A"))
                    
                    if pd.notna(diag_data_completa.get('Diagnóstico')): st.markdown(f"**Seu Resumo:** {diag_data_completa.get('Diagnóstico')}")
                    if pd.notna(diag_data_completa.get('Análise do Cliente')): st.markdown(f"**Sua Análise:** {diag_data_completa.get('Análise do Cliente')}")
                    
                    st.markdown("---")
                    if pd.notna(diag_data_completa.get('Comentarios_Admin')):
                        st.markdown(f"**Comentários do Consultor:**")
                        st.info(str(diag_data_completa.get('Comentarios_Admin')))
                    else:
                        st.caption("Nenhum comentário do consultor para este diagnóstico ainda.")

                    st.markdown("**Médias por Categoria:**")
                    cat_cols_data = {k.replace("Media_Cat_","").replace("_"," "): float(v) for k,v in diag_data_completa.items() if k.startswith("Media_Cat_") and pd.notna(v)} 
                    if cat_cols_data:
                        radar_fig_cliente = create_radar_chart(cat_cols_data, title="Performance por Categoria")
                        if radar_fig_cliente: st.plotly_chart(radar_fig_cliente, use_container_width=True)
                        else: 
                            for cat, media in cat_cols_data.items(): st.write(f"- {cat}: {media:.2f}")
                    else:
                        st.caption("Nenhuma média por categoria calculada para este diagnóstico.")

                    gut_scores_cliente = []
                    perg_df_loop = pd.read_csv(perguntas_csv, encoding='utf-8') if os.path.exists(perguntas_csv) else pd.DataFrame()
                    for _, p_row_loop in perg_df_loop.iterrows():
                        p_texto_loop = p_row_loop["Pergunta"]
                        p_texto_sanitized_loop = sanitize_column_name(p_texto_loop)
                        if "[Matriz GUT]" in p_texto_loop and f"{p_texto_sanitized_loop}_Score" in diag_data_completa:
                            score_val = diag_data_completa.get(f"{p_texto_sanitized_loop}_Score")
                            if pd.notna(score_val):
                                gut_scores_cliente.append({"Tarefa": p_texto_loop.replace(" [Matriz GUT]",""), "Score": int(score_val)})
                    
                    if gut_scores_cliente:
                        gut_chart_cliente = create_gut_barchart(gut_scores_cliente, title="Suas Prioridades (Matriz GUT)")
                        if gut_chart_cliente: st.plotly_chart(gut_chart_cliente, use_container_width=True)
                    
                    if "TimingsPerguntasJSON" in diag_data_completa and pd.notna(diag_data_completa["TimingsPerguntasJSON"]):
                        with st.expander("Ver tempo gasto por pergunta neste diagnóstico"):
                            try:
                                timings_diag = json.loads(diag_data_completa["TimingsPerguntasJSON"])
                                if timings_diag:
                                    for p_time, t_val in timings_diag.items():
                                        st.write(f"- *{p_time}*: {float(t_val):.2f} segundos")
                                else:
                                    st.caption("Nenhum dado de tempo registrado.")
                            except (json.JSONDecodeError, TypeError, ValueError):
                                st.caption("Não foi possível ler os dados de tempo.")
                    
                    perg_df_painel_dl = pd.read_csv(perguntas_csv, encoding='utf-8') if os.path.exists(perguntas_csv) else pd.DataFrame()
                    analises_df_painel_dl = carregar_analises_perguntas()
                    respostas_coletadas_painel_dl = {}
                    for col_key, val_col in diag_data_completa.items():
                        original_col_name_dl = None
                        if not perg_df_painel_dl.empty:
                            match_perg_dl = perg_df_painel_dl[perg_df_painel_dl['Pergunta'].apply(sanitize_column_name) == col_key]
                            if not match_perg_dl.empty:
                                original_col_name_dl = match_perg_dl['Pergunta'].iloc[0]
                        
                        if original_col_name_dl and col_key not in colunas_base_diagnosticos and \
                           not col_key.startswith("Media_Cat_") and \
                           not col_key.endswith("_Score") and \
                           col_key not in ["TimingsPerguntasJSON", "ID_Diagnostico"]:
                           respostas_coletadas_painel_dl[original_col_name_dl] = val_col

                    if st.button("Gerar PDF Completo deste Diagnóstico", key=f"pdf_{diag_id_atual}", type="primary"):
                        pdf_path = gerar_pdf_diagnostico_completo(diag_data_completa, st.session_state.user, perg_df_painel_dl, respostas_coletadas_painel_dl, cat_cols_data, analises_df_painel_dl)
                        if pdf_path:
                            with open(pdf_path, "rb") as fp:
                                st.download_button(label="Baixar PDF Gerado", data=fp, file_name=f"Diagnostico_{st.session_state.user.get('Empresa','Cliente')}_{str(row_diag['Data da Realização']).split(' ')[0]}.pdf", mime="application/pdf", key=f"dl_pdf_{diag_id_atual}")
                            try: os.remove(pdf_path)
                            except Exception as e_rem_pdf: print(f"Aviso: não foi possível remover o arquivo PDF temporário {pdf_path}: {e_rem_pdf}")
    # ... (Resto das páginas do cliente: Suporte/FAQ, Pesquisa de Satisfação, Notificações - mantidas como no original) ...
    elif st.session_state.cliente_page == "Suporte/FAQ":
        st.header("💬 Suporte e Perguntas Frequentes (FAQ)")
        df_faq = carregar_faq()

        if df_faq.empty:
            st.info("Nenhuma pergunta frequente cadastrada no momento.")
        else:
            col_filter1, col_filter2 = st.columns([1,2])
            categorias_faq = ["Todas"] + sorted(df_faq["CategoriaFAQ"].astype(str).unique())
            st.session_state.selected_faq_category = col_filter1.selectbox(
                "Filtrar por Categoria:", 
                categorias_faq, 
                index=categorias_faq.index(st.session_state.get("selected_faq_category", "Todas")),
                key="faq_cat_filter_v21"
            )

            st.session_state.search_faq_query = col_filter2.text_input(
                "Buscar na Pergunta:", 
                value=st.session_state.get("search_faq_query", ""),
                key="faq_search_query_v21"
            ).lower()

            df_filtrada_faq = df_faq.copy()
            if st.session_state.selected_faq_category != "Todas":
                df_filtrada_faq = df_filtrada_faq[df_filtrada_faq["CategoriaFAQ"] == st.session_state.selected_faq_category]
            
            if st.session_state.search_faq_query:
                df_filtrada_faq = df_filtrada_faq[df_filtrada_faq["PerguntaFAQ"].str.lower().str.contains(st.session_state.search_faq_query)]

            if df_filtrada_faq.empty:
                st.write("Nenhuma pergunta encontrada para os filtros aplicados.")
            else:
                st.markdown("---")
                for index, row_faq in df_filtrada_faq.iterrows():
                    faq_id = str(row_faq["ID_FAQ"])
                    pergunta_faq = row_faq["PerguntaFAQ"]
                    
                    if st.button(f"**{pergunta_faq}**", key=f"faq_q_{faq_id}_v21", use_container_width=True):
                        st.session_state.selected_faq_id = faq_id if st.session_state.selected_faq_id != faq_id else None 
                    
                    if st.session_state.selected_faq_id == faq_id:
                        st.markdown(f"<div class='faq-answer'>{row_faq['RespostaFAQ']}</div>", unsafe_allow_html=True)
                st.markdown("---")

    elif st.session_state.cliente_page == "Pesquisa de Satisfação":
        st.header("🌟 Pesquisa de Satisfação")
        df_perguntas_pesquisa = carregar_pesquisa_perguntas()
        df_perguntas_ativas = df_perguntas_pesquisa[df_perguntas_pesquisa["Ativa"] == True].sort_values(by="Ordem")

        if df_perguntas_ativas.empty:
            st.info("A pesquisa de satisfação não está disponível no momento.")
            st.stop()

        df_respostas_anteriores = carregar_pesquisa_respostas()
        cnpj_cliente_atual = st.session_state.cnpj
        id_diag_associado_atual = st.session_state.get("survey_id_diagnostico_associado") 

        ja_respondeu_esta_pesquisa_especifica = False
        if id_diag_associado_atual and not df_respostas_anteriores.empty:
            mask_resposta_especifica = (df_respostas_anteriores["CNPJ_Cliente"] == cnpj_cliente_atual) & \
                                       (df_respostas_anteriores["ID_Diagnostico_Associado"] == id_diag_associado_atual)
            if mask_resposta_especifica.any():
                ja_respondeu_esta_pesquisa_especifica = True
        
        if ja_respondeu_esta_pesquisa_especifica:
            st.success("Obrigado! Você já respondeu à pesquisa de satisfação referente a este diagnóstico.")
            if st.button("Voltar ao Painel Principal", key="pesquisa_ja_respondida_voltar_v21"):
                st.session_state.cliente_page = "Painel Principal"
                st.session_state.survey_id_diagnostico_associado = None 
                st.rerun()
            st.stop()
        elif st.session_state.get("survey_submitted_for_current_diag") and not id_diag_associado_atual : 
            st.info("Você já enviou uma pesquisa de satisfação recentemente. Obrigado!")
            if st.button("Voltar ao Painel Principal", key="pesquisa_recente_voltar_v21"):
                st.session_state.cliente_page = "Painel Principal"
                st.rerun()
            st.stop()

        st.markdown("Sua opinião é muito importante para nós! Por favor, dedique alguns momentos para responder.")
        
        with st.form("form_pesquisa_satisfacao_v21"):
            respostas_coletadas_pesquisa = {}
            for _, p_row in df_perguntas_ativas.iterrows():
                id_pergunta = str(p_row["ID_PerguntaPesquisa"])
                texto_pergunta = p_row["TextoPerguntaPesquisa"]
                tipo_resposta = p_row["TipoRespostaPesquisa"]
                opcoes_json_str = p_row.get("OpcoesRespostaJSON", "[]")
                try:
                    opcoes_lista = json.loads(opcoes_json_str) if pd.notna(opcoes_json_str) and isinstance(opcoes_json_str, str) and opcoes_json_str.strip() and opcoes_json_str != 'nan' else []
                except json.JSONDecodeError:
                    opcoes_lista = []

                st.markdown(f"##### {texto_pergunta}")
                if tipo_resposta == "Escala 1-5":
                    respostas_coletadas_pesquisa[id_pergunta] = st.radio("", [1,2,3,4,5], key=f"pesq_{id_pergunta}_v21", horizontal=True, label_visibility="collapsed")
                elif tipo_resposta == "Texto Livre":
                    respostas_coletadas_pesquisa[id_pergunta] = st.text_area("", key=f"pesq_{id_pergunta}_v21", height=100, label_visibility="collapsed")
                elif tipo_resposta == "Escolha Única" and opcoes_lista:
                    respostas_coletadas_pesquisa[id_pergunta] = st.radio("", opcoes_lista, key=f"pesq_{id_pergunta}_v21", label_visibility="collapsed")
                elif tipo_resposta == "Múltipla Escolha" and opcoes_lista:
                    respostas_coletadas_pesquisa[id_pergunta] = st.multiselect("", opcoes_lista, key=f"pesq_{id_pergunta}_v21", label_visibility="collapsed")
                else: 
                    respostas_coletadas_pesquisa[id_pergunta] = st.text_input("Resposta:", key=f"pesq_{id_pergunta}_v21", label_visibility="collapsed")
                st.markdown("---")

            if st.form_submit_button("Enviar Respostas da Pesquisa", type="primary", use_container_width=True):
                user_info_pesq = st.session_state.user
                nova_resposta_submissao = {
                    "ID_SessaoRespostaPesquisa": str(uuid.uuid4()),
                    "CNPJ_Cliente": cnpj_cliente_atual,
                    "TimestampPreenchimento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "NomeClientePreenchimento": user_info_pesq.get("NomeContato", "N/A"),
                    "TelefoneClientePreenchimento": user_info_pesq.get("Telefone", "N/A"),
                    "EmpresaClientePreenchimento": user_info_pesq.get("Empresa", "N/A"),
                    "ID_Diagnostico_Associado": id_diag_associado_atual if id_diag_associado_atual else "", 
                    "RespostasJSON": json.dumps(respostas_coletadas_pesquisa)
                }
                df_respostas_anteriores = pd.concat([df_respostas_anteriores, pd.DataFrame([nova_resposta_submissao])], ignore_index=True)
                salvar_pesquisa_respostas(df_respostas_anteriores)
                
                st.success("Obrigado por suas respostas! Sua opinião foi registrada.")
                registrar_acao(cnpj_cliente_atual, "Pesquisa Satisfação Enviada", f"ID Sessão: {nova_resposta_submissao['ID_SessaoRespostaPesquisa']}")
                st.session_state.survey_submitted_for_current_diag = True 
                st.session_state.current_survey_responses = {} 
                
                if st.button("Voltar ao Painel Principal", key="pesquisa_enviada_voltar_v21"):
                    st.session_state.cliente_page = "Painel Principal"
                    st.session_state.survey_id_diagnostico_associado = None 
                    st.rerun()

    elif st.session_state.cliente_page == "Notificações":
        st.header(notificacoes_label.replace(f"({notificacoes_nao_lidas_count} Nova(s))", "").strip()) 
        df_notif_cliente = pd.DataFrame()
        try:
            df_all_notifs = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente':str, 'ID_Diagnostico_Relacionado': str})
            if not df_all_notifs.empty:
                df_notif_cliente = df_all_notifs[df_all_notifs["CNPJ_Cliente"] == st.session_state.cnpj].sort_values(by="Timestamp", ascending=False)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            pass 

        if df_notif_cliente.empty:
            st.info("Você não tem nenhuma notificação no momento.")
        else:
            for index, notif_row in df_notif_cliente.iterrows():
                card_key = f"notif_card_{notif_row['ID_Notificacao']}_v21"
                container_notif = st.container()
                with container_notif: 
                    st.markdown(f"""
                    <div class="custom-card {'custom-card-unread' if not notif_row['Lida'] else ''}">
                        <h4>Notificação de {pd.to_datetime(notif_row['Timestamp']).strftime('%d/%m/%Y %H:%M')}</h4>
                        <p>{notif_row['Mensagem']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    cols_notif_actions = st.columns(2)
                    if not notif_row['Lida']:
                        if cols_notif_actions[0].button("Marcar como Lida", key=f"read_{notif_row['ID_Notificacao']}_v21", type="primary"):
                            df_all_notifs.loc[df_all_notifs["ID_Notificacao"] == notif_row['ID_Notificacao'], "Lida"] = True
                            df_all_notifs.to_csv(notificacoes_csv, index=False, encoding='utf-8')
                            st.session_state.force_sidebar_rerun_after_notif_read_v19 = True 
                            st.rerun()
                    
                    id_diag_rel_val = notif_row.get("ID_Diagnostico_Relacionado")
                    if pd.notna(id_diag_rel_val) and str(id_diag_rel_val).strip(): 
                        id_diag_rel = str(id_diag_rel_val)
                        action_button_col = cols_notif_actions[1] if not notif_row['Lida'] else cols_notif_actions[0] 

                        if action_button_col.button("Ver Detalhes do Diagnóstico", key=f"details_{notif_row['ID_Notificacao']}_v21"):
                            try:
                                df_diag_geral = pd.read_csv(arquivo_csv, dtype={'CNPJ':str, 'ID_Diagnostico':str})
                                diag_data_target = df_diag_geral[df_diag_geral["ID_Diagnostico"] == id_diag_rel]
                                if not diag_data_target.empty:
                                    st.session_state.target_diag_data_for_expansion = diag_data_target.iloc[0].to_dict()
                                    st.session_state.cliente_page = "Painel Principal" 
                                    if not notif_row['Lida']:
                                        df_all_notifs.loc[df_all_notifs["ID_Notificacao"] == notif_row['ID_Notificacao'], "Lida"] = True
                                        df_all_notifs.to_csv(notificacoes_csv, index=False, encoding='utf-8')
                                        st.session_state.force_sidebar_rerun_after_notif_read_v19 = True
                                    st.rerun()
                                else:
                                    st.error(f"Diagnóstico relacionado (ID: {id_diag_rel}) não encontrado.")
                            except FileNotFoundError: st.error(f"Arquivo de diagnósticos '{arquivo_csv}' não encontrado.")
                            except Exception as e_view_diag_notif: st.error(f"Erro ao tentar ver detalhes do diagnóstico: {e_view_diag_notif}")
                    st.markdown("<hr>", unsafe_allow_html=True)

        if st.session_state.get("force_sidebar_rerun_after_notif_read_v19"): 
            st.session_state.force_sidebar_rerun_after_notif_read_v19 = False
            st.rerun() 

# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    admin_logo_path_sidebar = CUSTOM_LOGIN_LOGO_PATH if os.path.exists(CUSTOM_LOGIN_LOGO_PATH) else DEFAULT_LOGIN_LOGO_PATH
    if os.path.exists(admin_logo_path_sidebar):
        st.sidebar.image(admin_logo_path_sidebar, use_container_width=True, width=150) 
    else:
        st.sidebar.markdown("### Painel Admin")

    st.sidebar.success(f"🟢 Admin Logado: {st.session_state.admin_user_details.get('Usuario', '')}")

    if st.sidebar.button("Sair do Painel Admin", icon="🚪", key="logout_admin_v21_final_button", use_container_width=True):
        # Limpar apenas o estado de admin, não o estado global da aplicação
        admin_keys_to_clear = ["admin_logado", "admin_user_details", SESSION_KEY_FOR_ADMIN_PAGE]
        for key in admin_keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        # Resetar para valores padrão, se necessário, ou deixar para o próximo login
        st.session_state.admin_logado = False
        st.session_state.admin_user_details = None

        st.toast("Logout de admin realizado.", icon="👋")
        st.rerun()

    # Definição do menu admin e suas permissões associadas
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

    # Filtrar opções do menu com base nas permissões do admin logado
    admin_user_perms = st.session_state.get("admin_user_details", {})
    allowed_admin_pages_map = {}
    for page_name, (emoji, perm_key) in menu_admin_options_map.items():
        if admin_user_perms.get(perm_key, False): # Verifica a permissão
            allowed_admin_pages_map[page_name] = emoji
    
    if not allowed_admin_pages_map: # Se não tiver nenhuma permissão, mostra uma mensagem e impede acesso
        st.error("Você não tem permissão para acessar nenhuma funcionalidade do painel de administração.")
        st.stop()

    admin_page_text_keys = list(allowed_admin_pages_map.keys())
    admin_options_for_display = [f"{allowed_admin_pages_map[key]} {key}" for key in admin_page_text_keys]

    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_text_key_v22_final_sess" 
    WIDGET_KEY_SB_ADMIN_MENU = "sb_admin_menu_v22_final_widget_key" 

    def admin_menu_on_change_final_v22(): 
        selected_display_value = st.session_state.get(WIDGET_KEY_SB_ADMIN_MENU) 
        if selected_display_value is None: return 

        new_text_key = None
        for text_key_iter, emoji_iter in allowed_admin_pages_map.items(): # Usar o mapa filtrado
            if f"{emoji_iter} {text_key_iter}" == selected_display_value:
                new_text_key = text_key_iter
                break
        if new_text_key and new_text_key != st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE):
            st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = new_text_key
            # st.rerun() # O on_change já causa um rerun se o valor do widget mudar

    if SESSION_KEY_FOR_ADMIN_PAGE not in st.session_state or \
       st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE) not in admin_page_text_keys: # Verificar contra as chaves permitidas
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0] if admin_page_text_keys else None

    current_admin_page_text_key_for_index = st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE)
    current_admin_menu_index = 0

    if current_admin_page_text_key_for_index and admin_options_for_display: # Checar se há opções
        try:
            expected_display_value_for_current_page = f"{allowed_admin_pages_map.get(current_admin_page_text_key_for_index, '')} {current_admin_page_text_key_for_index}"
            current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
        except (ValueError, KeyError): 
            st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0] 
            current_admin_page_text_key_for_index = admin_page_text_keys[0] 
            expected_display_value_for_current_page = f"{allowed_admin_pages_map[current_admin_page_text_key_for_index]} {current_admin_page_text_key_for_index}"
            current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
    
    if admin_options_for_display: # Somente mostrar o selectbox se houver opções permitidas
        st.sidebar.selectbox(
            "Funcionalidades Admin:",
            options=admin_options_for_display,
            index=current_admin_menu_index,
            key=WIDGET_KEY_SB_ADMIN_MENU,
            on_change=admin_menu_on_change_final_v22
        )
    
    menu_admin = st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE)

    if menu_admin and menu_admin in allowed_admin_pages_map: # Verificar se a página selecionada é permitida
        header_display_name = f"{allowed_admin_pages_map.get(menu_admin, '❓')} {menu_admin}"
        st.header(header_display_name)
    elif admin_page_text_keys : # Se a página atual não é permitida, mas há outras, redireciona para a primeira permitida
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]
        st.rerun()
    else: # Nenhuma página permitida (já tratado acima, mas como fallback)
        st.error("Acesso negado.")
        st.stop()

    # Função auxiliar para verificar permissão
    def has_admin_permission(permission_key):
        if 'admin_user_details' in st.session_state and st.session_state.admin_user_details is not None:
            return st.session_state.admin_user_details.get(permission_key, False)
        return False # Por padrão, nega se não encontrar detalhes do usuário

    df_usuarios_admin_geral = pd.DataFrame(columns=colunas_base_usuarios) 
    try:
        df_usuarios_admin_temp_load = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
        if "DiagnosticosDisponiveis" not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load["DiagnosticosDisponiveis"] = 1
        df_usuarios_admin_temp_load["DiagnosticosDisponiveis"] = pd.to_numeric(df_usuarios_admin_temp_load["DiagnosticosDisponiveis"], errors='coerce').fillna(1).astype(int)
        if "TotalDiagnosticosRealizados" not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load["TotalDiagnosticosRealizados"] = 0
        df_usuarios_admin_temp_load["TotalDiagnosticosRealizados"] = pd.to_numeric(df_usuarios_admin_temp_load["TotalDiagnosticosRealizados"], errors='coerce').fillna(0).astype(int)
        if "JaVisualizouInstrucoes" not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load["JaVisualizouInstrucoes"] = "False"
        df_usuarios_admin_temp_load["JaVisualizouInstrucoes"] = df_usuarios_admin_temp_load["JaVisualizouInstrucoes"].astype(str).str.lower().map({'true': True, 'false': False, 'nan':False, '':False}).fillna(False)
        df_usuarios_admin_geral = df_usuarios_admin_temp_load
    except FileNotFoundError:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Clientes", "Gerenciar Notificações", "Relatório de Engajamento", "Personalizar Aparência", "Resultados da Pesquisa de Satisfação"]:
            st.sidebar.warning(f"Arquivo '{usuarios_csv}' não encontrado. Algumas funcionalidades podem ser limitadas.")
    except Exception as e_load_users_adm_global:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Clientes", "Gerenciar Notificações", "Relatório de Engajamento", "Personalizar Aparência", "Resultados da Pesquisa de Satisfação"]:
            st.sidebar.error(f"Erro ao carregar usuários para admin: {e_load_users_adm_global}")

    # --- Admin Page Content ---
    if menu_admin == "Visão Geral e Diagnósticos":
        if not has_admin_permission("Perm_VisaoGeralDiagnosticos"):
            st.error("Você não tem permissão para acessar esta página.")
            st.stop()
        # (Seu código para Visão Geral e Diagnósticos aqui)
        st.subheader("Visão Geral dos Diagnósticos de Clientes")
        try:
            df_diagnosticos_admin = pd.read_csv(arquivo_csv, dtype={'CNPJ': str, 'ID_Diagnostico': str}, encoding='utf-8')
        except (FileNotFoundError, pd.errors.EmptyDataError):
            st.info("Nenhum diagnóstico encontrado.")
            df_diagnosticos_admin = pd.DataFrame()

        if not df_diagnosticos_admin.empty:
            empresas_com_diag = sorted(df_diagnosticos_admin["Empresa"].unique())
            empresa_selecionada_gv = st.selectbox("Filtrar por Empresa:", ["Todas"] + empresas_com_diag, key="admin_gv_empresa_filter_v21")

            df_filtrada_gv = df_diagnosticos_admin
            if empresa_selecionada_gv != "Todas":
                df_filtrada_gv = df_diagnosticos_admin[df_diagnosticos_admin["Empresa"] == empresa_selecionada_gv]
            
            df_filtrada_gv = df_filtrada_gv.sort_values(by="Data", ascending=False)
            
            cols_to_display_gv = colunas_base_diagnosticos[:] 
            dynamic_cols_gv = [col for col in df_filtrada_gv.columns if col.startswith("Media_Cat_") or col.endswith("_Score")]
            for dyn_col_gv in dynamic_cols_gv:
                if dyn_col_gv not in cols_to_display_gv : cols_to_display_gv.append(dyn_col_gv)
            
            final_cols_to_display_gv = [col for col in cols_to_display_gv if col in df_filtrada_gv.columns]
            st.dataframe(df_filtrada_gv[final_cols_to_display_gv], use_container_width=True, height=300)

            st.subheader("Detalhes e Ações por Diagnóstico")
            if not df_filtrada_gv.empty:
                id_options_map_gv = {"Nenhum": "Nenhum"}
                for _, row_opt_gv in df_filtrada_gv.iterrows():
                    id_options_map_gv[row_opt_gv["ID_Diagnostico"]] = f"ID: {row_opt_gv['ID_Diagnostico']} ({row_opt_gv.get('Data','N/D')} - {row_opt_gv.get('Empresa','N/D')})"
                
                id_diagnostico_selecionado = st.selectbox(
                    "Selecione um Diagnóstico para ver detalhes ou adicionar comentários:", 
                    options=list(id_options_map_gv.keys()),
                    format_func=lambda x: id_options_map_gv[x],
                    key="admin_select_diag_details_v21"
                )

                if id_diagnostico_selecionado != "Nenhum":
                    diag_selecionado_data = df_diagnosticos_admin[df_diagnosticos_admin["ID_Diagnostico"] == id_diagnostico_selecionado].iloc[0]
                    
                    with st.expander("Ver/Editar Comentários do Consultor", expanded=True):
                        comentario_atual = diag_selecionado_data.get("Comentarios_Admin", "")
                        comentario_novo = st.text_area("Seus Comentários/Feedback para o Cliente:", value=comentario_atual if pd.notna(comentario_atual) else "", height=150, key=f"com_admin_{id_diagnostico_selecionado}_v21")
                        if st.button("Salvar Comentário", key=f"save_com_admin_{id_diagnostico_selecionado}_v21"):
                            df_diagnosticos_admin.loc[df_diagnosticos_admin["ID_Diagnostico"] == id_diagnostico_selecionado, "Comentarios_Admin"] = comentario_novo
                            df_diagnosticos_admin.to_csv(arquivo_csv, index=False, encoding='utf-8')
                            st.success("Comentário salvo!")
                            st.rerun()
                    
                    st.markdown("---")
                    st.write(f"**Empresa:** {diag_selecionado_data.get('Empresa', 'N/A')}")
                    # ... (resto da exibição de detalhes do diagnóstico)
                    if "TimingsPerguntasJSON" in diag_selecionado_data and pd.notna(diag_selecionado_data["TimingsPerguntasJSON"]):
                        with st.expander("Tempo Gasto por Pergunta (Cliente)"):
                            try:
                                timings = json.loads(diag_selecionado_data["TimingsPerguntasJSON"])
                                if timings:
                                    for pergunta_t, tempo_t in timings.items():
                                        st.markdown(f"- `{pergunta_t}`: {float(tempo_t):.2f} segundos")
                                else:
                                    st.caption("Nenhum dado de tempo.")
                            except (json.JSONDecodeError, TypeError, ValueError):
                                st.caption("Não foi possível carregar os dados de tempo.")
            else:
                st.info("Nenhum diagnóstico para exibir com o filtro atual.")
        else:
            st.info("Ainda não há diagnósticos registrados no sistema.")

    elif menu_admin == "Relatório de Engajamento":
        if not has_admin_permission("Perm_RelatorioEngajamento"):
            st.error("Você não tem permissão para acessar esta página.")
            st.stop()
        # (Seu código para Relatório de Engajamento aqui)
        st.subheader("Relatório de Engajamento e Métricas Gerais")
        try:
            df_diagnosticos_eng = pd.read_csv(arquivo_csv, dtype={'CNPJ':str, 'ID_Diagnostico': str}, encoding='utf-8')
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df_diagnosticos_eng = pd.DataFrame()

        if not df_usuarios_admin_geral.empty:
            total_clientes = len(df_usuarios_admin_geral)
            clientes_com_diagnostico = 0
            if not df_diagnosticos_eng.empty:
                clientes_com_diagnostico = df_diagnosticos_eng["CNPJ"].nunique()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Clientes Cadastrados", total_clientes)
            col2.metric("Clientes com Diagnósticos", clientes_com_diagnostico)
            col3.metric("Total de Diagnósticos Realizados", len(df_diagnosticos_eng))

            st.markdown("---")
            # ... (resto da geração de gráficos)
        else:
            st.info("Nenhum usuário cadastrado para gerar relatórios.")


    elif menu_admin == "Gerenciar Administradores":
        if not has_admin_permission("Perm_GerenciarAdministradores"):
            st.error("Você não tem permissão para acessar esta página.")
            st.stop()
        
        st.subheader("Gerenciar Contas de Administrador")
        try:
            df_admins_ga = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            for perm_col in ALL_ADMIN_PERMISSION_KEYS: # Garantir colunas e tipo
                if perm_col not in df_admins_ga.columns:
                    df_admins_ga[perm_col] = False
                df_admins_ga[perm_col] = df_admins_ga[perm_col].fillna(False).astype(bool)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df_admins_ga = pd.DataFrame(columns=colunas_base_admin_credenciais)
            for perm_col in ALL_ADMIN_PERMISSION_KEYS: df_admins_ga[perm_col] = pd.Series(dtype=bool)

        st.info("Adicione, edite ou remova contas de administrador e suas permissões. Cuidado: A remoção é permanente.")

        with st.expander("➕ Adicionar Novo Administrador"):
            with st.form("form_add_new_admin_v23"):
                st.write("##### Detalhes do Novo Administrador")
                new_admin_user = st.text_input("Usuário*", key="new_admin_user_v23")
                new_admin_pass = st.text_input("Senha*", type="password", key="new_admin_pass_v23")

                st.write("##### Permissões")
                new_admin_permissions = {}
                num_perm_cols = 3
                perm_cols_widgets = st.columns(num_perm_cols)
                col_idx = 0
                for perm_key in ALL_ADMIN_PERMISSION_KEYS:
                    perm_label = perm_key.replace("Perm_", "").replace("Gerenciar", "Ger. ").replace("Diagnostico", "Diag.").replace("Resultados", "Res.")
                    new_admin_permissions[perm_key] = perm_cols_widgets[col_idx % num_perm_cols].checkbox(perm_label, key=f"new_perm_{perm_key}_v23", value= (perm_key == "Perm_GerenciarAdministradores")) # Default superadmin a True
                    col_idx += 1
                
                submitted_new_admin = st.form_submit_button("Adicionar Administrador")
                if submitted_new_admin:
                    if not new_admin_user or not new_admin_pass:
                        st.error("Usuário e Senha são obrigatórios.")
                    elif new_admin_user in df_admins_ga["Usuario"].values:
                        st.error("Este nome de usuário de administrador já existe.")
                    else:
                        new_admin_data = {"Usuario": new_admin_user, "Senha": new_admin_pass}
                        new_admin_data.update(new_admin_permissions)
                        df_new_admin_row = pd.DataFrame([new_admin_data])
                        df_admins_ga = pd.concat([df_admins_ga, df_new_admin_row], ignore_index=True)
                        # Garantir tipos corretos antes de salvar
                        for perm_key_save in ALL_ADMIN_PERMISSION_KEYS:
                            if perm_key_save in df_admins_ga.columns:
                                df_admins_ga[perm_key_save] = df_admins_ga[perm_key_save].astype(bool)
                        df_admins_ga.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                        st.success(f"Administrador '{new_admin_user}' adicionado com sucesso!")
                        st.rerun()

        st.markdown("---")
        st.write("##### Editar Administradores Existentes")
        
        column_config_admins = {
            "Usuario": st.column_config.TextColumn("Usuário", disabled=True),
            "Senha": st.column_config.TextColumn("Senha (oculta)", disabled=True, help="Use a seção 'Alterar Senha' abaixo."),
        }
        for perm_key in ALL_ADMIN_PERMISSION_KEYS:
            perm_label = perm_key.replace("Perm_", "").replace("Gerenciar", "Ger. ").replace("Diagnostico", "Diag.").replace("Resultados", "Res.")
            column_config_admins[perm_key] = st.column_config.CheckboxColumn(perm_label, default=False)

        # Criar uma cópia para o editor, mascarando a senha
        df_admins_display = df_admins_ga.copy()
        if "Senha" in df_admins_display.columns:
            df_admins_display["Senha"] = "********" 

        edited_df_admins_ga = st.data_editor(
            df_admins_display, # Mostra o DataFrame com senhas mascaradas
            key="editor_admins_ga_v23_permissions",
            column_config=column_config_admins,
            use_container_width=True,
            num_rows="dynamic",
            disabled=["Usuario", "Senha"] 
        )

        if st.button("Salvar Alterações nos Administradores", key="save_admins_ga_v23_permissions", type="primary"):
            if edited_df_admins_ga["Usuario"].isnull().any() or (edited_df_admins_ga["Usuario"] == "").any(): # Username não deve ser nulo
                st.error("Nome de usuário não pode ser vazio (verifique linhas adicionadas/removidas).")
            elif edited_df_admins_ga["Usuario"].duplicated().any():
                 st.error("Nomes de usuário de administrador devem ser únicos.")
            else:
                # Reconstruir o DataFrame para salvar, mantendo as senhas originais
                final_df_to_save = pd.DataFrame(columns=colunas_base_admin_credenciais)
                for _, edited_row in edited_df_admins_ga.iterrows():
                    original_admin_row = df_admins_ga[df_admins_ga['Usuario'] == edited_row['Usuario']]
                    if not original_admin_row.empty:
                        new_row_data = original_admin_row.iloc[0].to_dict() # Pega senha original
                        for perm_key_update in ALL_ADMIN_PERMISSION_KEYS: # Atualiza permissões
                            new_row_data[perm_key_update] = bool(edited_row.get(perm_key_update, False))
                        final_df_to_save = pd.concat([final_df_to_save, pd.DataFrame([new_row_data])], ignore_index=True)
                
                # Garantir que o admin logado não remova sua própria permissão de GerenciarAdministradores
                logged_admin_username = st.session_state.admin_user_details['Usuario']
                logged_admin_row_in_save = final_df_to_save[final_df_to_save['Usuario'] == logged_admin_username]
                if not logged_admin_row_in_save.empty and not logged_admin_row_in_save.iloc[0]['Perm_GerenciarAdministradores']:
                    # Se for o único admin com essa permissão, não permitir
                    admins_with_super_perm = final_df_to_save[final_df_to_save['Perm_GerenciarAdministradores'] == True]
                    if len(admins_with_super_perm) == 0 : # Ninguém teria a permissão
                         st.error(f"Não é possível remover a permissão 'Gerenciar Administradores' do usuário '{logged_admin_username}' pois seria o último com esta permissão.")
                         st.stop()
                    elif len(admins_with_super_perm) >=1 and logged_admin_username not in admins_with_super_perm['Usuario'].values: # Ele removeu de si mesmo, mas há outros
                        pass # Permitido se há outros superadmins

                final_df_to_save.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                st.success("Lista de administradores e suas permissões atualizada!")
                
                # Atualizar detalhes do admin logado na sessão
                updated_admin_details_row = final_df_to_save[final_df_to_save['Usuario'] == logged_admin_username]
                if not updated_admin_details_row.empty:
                    st.session_state.admin_user_details = updated_admin_details_row.iloc[0].to_dict()
                st.rerun()

        st.markdown("---")
        st.subheader("Alterar Senha de Administrador")
        with st.form("form_change_admin_password_v23"):
            df_admins_current_ga = pd.read_csv(admin_credenciais_csv, encoding='utf-8') # Ler a versão mais recente
            admins_list_cp = df_admins_current_ga["Usuario"].tolist()
            if not admins_list_cp:
                st.info("Nenhum administrador cadastrado para alterar senha.")
            else:
                selected_admin_for_pw_change = st.selectbox("Selecione o Administrador:", admins_list_cp, key="admin_select_pw_change_v23")
                new_password_for_admin = st.text_input("Nova Senha:", type="password", key="admin_new_pw_v23")
                confirm_new_password_for_admin = st.text_input("Confirme a Nova Senha:", type="password", key="admin_confirm_new_pw_v23")

                if st.form_submit_button("Alterar Senha"):
                    if not new_password_for_admin:
                        st.error("A nova senha não pode ser vazia.")
                    elif new_password_for_admin != confirm_new_password_for_admin:
                        st.error("As senhas não coincidem.")
                    else:
                        admin_index_to_update = df_admins_current_ga[df_admins_current_ga["Usuario"] == selected_admin_for_pw_change].index
                        if not admin_index_to_update.empty:
                            df_admins_current_ga.loc[admin_index_to_update, "Senha"] = new_password_for_admin
                            df_admins_current_ga.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                            st.success(f"Senha do administrador '{selected_admin_for_pw_change}' alterada com sucesso!")
                            st.rerun()
                        else:
                            st.error("Administrador não encontrado.")
    
    # Adicionar verificações de permissão para outras seções do admin:
    elif menu_admin == "Gerenciar Clientes":
        if not has_admin_permission("Perm_GerenciarClientes"):
            st.error("Você não tem permissão para acessar esta página.")
            st.stop()
        # ... (código da página Gerenciar Clientes)
    elif menu_admin == "Gerenciar Perguntas Diagnóstico":
        if not has_admin_permission("Perm_GerenciarPerguntasDiagnostico"):
            st.error("Você não tem permissão para acessar esta página.")
            st.stop()
        # ... (código da página)
    # ... e assim por diante para todas as outras seções do menu_admin

# Fallback final
if 'aba' not in locals() and not st.session_state.admin_logado and not st.session_state.cliente_logado:
    # Esta condição idealmente não deve ser atingida se a lógica de login estiver correta
    st.info("Por favor, selecione seu tipo de acesso para iniciar ou complete o login.")
    st.stop()