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

# --- CSS (Complete CSS from your last working version) ---
st.markdown(f"""
<style>
body {{
    font-family: 'Segoe UI', sans-serif;
    background-color: #f0f2f5; 
}}
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

# --- Funções de Gráficos ---
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
                continue # Skip rows with invalid JSON or non-numeric times

    if not all_timings:
        return None

    df_times = pd.DataFrame(all_timings)
    if df_times.empty:
        return None

    avg_times = df_times.groupby('Pergunta')['TempoSegundos'].mean().reset_index()
    avg_times = avg_times.sort_values(by='TempoSegundos', ascending=False).head(15) # Top 15

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
    # Novos estados para as funcionalidades
    "current_question_start_time": None, 
    "diagnostic_question_timings": {},   
    "previous_question_text_tracker": None, # Adicionado para rastrear a pergunta atual para o timer
    "current_survey_responses": {},      
    "selected_faq_category": "Todas",    
    "search_faq_query": "",              
    "selected_faq_id": None,             
    "survey_submitted_for_current_diag": False,
    "survey_id_diagnostico_associado": None # Adicionado para o contexto da pesquisa
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
                        # Set dtype explicitly if default_val is provided
                        if pd.isna(default_val):
                             df_init[col] = pd.Series(dtype='object')
                        else:
                             df_init[col] = pd.Series(dtype=type(default_val))
                        # If df_init is still empty and default_val is not NA, assign to ensure type
                        if len(df_init[col]) == 0 and not pd.isna(default_val) : # Check length of specific series
                             df_init.loc[0, col] = default_val
                             df_init = df_init.iloc[0:0] # Keep df empty

            df_init.to_csv(filepath, index=False, encoding='utf-8')
        else:
            try:
                dtype_spec = {}
                if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, historico_csv, pesquisa_satisfacao_respostas_csv]:
                    if 'CNPJ' in columns: dtype_spec['CNPJ'] = str
                    if 'CNPJ_Cliente' in columns: dtype_spec['CNPJ_Cliente'] = str
                if filepath == notificacoes_csv and 'ID_Diagnostico_Relacionado' in columns:
                    dtype_spec['ID_Diagnostico_Relacionado'] = str
                if filepath == arquivo_csv and 'ID_Diagnostico' in columns:
                    dtype_spec['ID_Diagnostico'] = str
                if filepath == pesquisa_satisfacao_respostas_csv and 'ID_Diagnostico_Associado' in columns:
                     dtype_spec['ID_Diagnostico_Associado'] = str
                
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)

            except ValueError as ve: 
                st.warning(f"Problema ao ler {filepath} com dtypes específicos ({ve}), tentando leitura genérica.")
                df_init = pd.read_csv(filepath, encoding='utf-8') 
            except Exception as read_e: 
                st.warning(f"Problema ao ler {filepath}, tentando recriar com colunas esperadas: {read_e}")
                df_init = pd.DataFrame(columns=columns) 
                if defaults: # Apply defaults logic for recreation
                    for col, default_val in defaults.items():
                        if col in columns:
                            if pd.isna(default_val): df_init[col] = pd.Series(dtype='object')
                            else: df_init[col] = pd.Series(dtype=type(default_val))
                            if len(df_init[col]) == 0 and not pd.isna(default_val):
                                df_init.loc[0, col] = default_val
                                df_init = df_init.iloc[0:0]
                df_init.to_csv(filepath, index=False, encoding='utf-8') # Save recreated file
                # Try reading again after recreation
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)


            made_changes = False
            current_cols = df_init.columns.tolist()
            for col_idx, col_name in enumerate(columns):
                if col_name not in current_cols:
                    default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                    
                    if len(df_init) > 0 and not df_init.empty: 
                        # Determine dtype for insertion
                        col_insert_dtype = object
                        if not pd.isna(default_val):
                            col_insert_dtype = type(default_val)
                        
                        insert_values = [default_val] * len(df_init)
                        # Pandas insert can sometimes be tricky with dtypes of mixed None/values.
                        # It's often better to assign if possible or ensure Series has right dtype.
                        try:
                            df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=pd.Series(insert_values, dtype=col_insert_dtype, index=df_init.index))
                        except Exception as e_insert: # Fallback if insert with specific dtype fails (e.g. mixed types not allowed by dtype)
                             df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=insert_values)


                    else: # df_init is empty (0 rows)
                        # *** THIS IS THE CORRECTED LINE ***
                        df_init[col_name] = pd.Series(dtype=object if pd.isna(default_val) else type(default_val))
                        
                        # This block is to ensure that if a default value (like 0 or 1) is provided for an empty DataFrame,
                        # the column type is correctly set (e.g., to int) rather than just object.
                        if not pd.isna(default_val) and df_init.empty: # Check if df_init is truly empty (0 rows)
                             # Temporarily add a row to set the type based on the value, then remove it.
                             # This only applies if df_init has 0 rows.
                             df_init.loc[0, col_name] = default_val
                             df_init = df_init.iloc[0:0]
                            
                    made_changes = True
            if made_changes:
                df_init.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError: 
        # This means the file exists but is completely empty (not even headers). Treat as new.
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
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios,
                    defaults={"JaVisualizouInstrucoes": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos, defaults={"TimingsPerguntasJSON": None, "ID_Diagnostico": None}) 
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False, "ID_Diagnostico_Relacionado": None}) 
    # Inicializar novos CSVs
    inicializar_csv(faq_sac_csv, colunas_base_faq, defaults={"CategoriaFAQ": "Geral"})
    inicializar_csv(pesquisa_satisfacao_perguntas_csv, colunas_base_pesquisa_perguntas, defaults={"Ordem": 0, "Ativa": True, "OpcoesRespostaJSON": "[]"})
    inicializar_csv(pesquisa_satisfacao_respostas_csv, colunas_base_pesquisa_respostas, defaults={"ID_Diagnostico_Associado": None, "RespostasJSON": "{}"})

except Exception as e_init:
    st.error(f"Falha na inicialização de arquivos CSV: {e_init}")
    st.stop()

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

# Funções de CRUD para FAQ
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

# Funções de CRUD para Pesquisa de Satisfação - Perguntas
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
        
        # Garantir que IDs sejam strings se existirem
        if "ID_PerguntaPesquisa" in df.columns:
            df["ID_PerguntaPesquisa"] = df["ID_PerguntaPesquisa"].astype(str)

        # Re-save if corrections were made (like adding new columns with defaults)
        # This should be ideally handled by initializar_csv already, but as a safeguard:
        # current_cols = df.columns.tolist()
        # made_changes_load = False
        # for base_col in colunas_base_pesquisa_perguntas:
        #     if base_col not in current_cols:
        #         # Using defaults defined in inicializar_csv or general ones
        #         if base_col == "OpcoesRespostaJSON": df[base_col] = "[]"
        #         elif base_col == "Ativa": df[base_col] = True
        #         elif base_col == "Ordem": df[base_col] = 0
        #         else: df[base_col] = pd.NA
        #         made_changes_load = True
        # if made_changes_load:
        #     df.to_csv(pesquisa_satisfacao_perguntas_csv, index=False, encoding='utf-8')
        
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_pesquisa_perguntas)


def salvar_pesquisa_perguntas(df_perguntas):
    df_perguntas.to_csv(pesquisa_satisfacao_perguntas_csv, index=False, encoding='utf-8')
    st.cache_data.clear()

# Funções de CRUD para Pesquisa de Satisfação - Respostas
@st.cache_data(ttl=30)
def carregar_pesquisa_respostas():
    try:
        df = pd.read_csv(pesquisa_satisfacao_respostas_csv, encoding='utf-8', dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Associado': str})
        if "RespostasJSON" not in df.columns: df["RespostasJSON"] = "{}"
        df["RespostasJSON"] = df["RespostasJSON"].fillna("{}").astype(str)
        # Garantir IDs são strings
        if "ID_SessaoRespostaPesquisa" in df.columns: df["ID_SessaoRespostaPesquisa"] = df["ID_SessaoRespostaPesquisa"].astype(str)
        if "ID_Diagnostico_Associado" in df.columns: df["ID_Diagnostico_Associado"] = df["ID_Diagnostico_Associado"].astype(str).fillna("") # Use empty string for NA str

        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_pesquisa_respostas)


def salvar_pesquisa_respostas(df_respostas):
    df_respostas.to_csv(pesquisa_satisfacao_respostas_csv, index=False, encoding='utf-8')
    st.cache_data.clear()


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
                    resp = respostas_coletadas.get(p_texto, diag_data.get(sanitize_column_name(p_texto), "N/R")) # Use sanitized name for lookup in diag_data
                    analise_texto = None
                    if "[Matriz GUT]" in p_texto:
                        g,u,t,score=0,0,0,0
                        if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                        elif isinstance(resp, str): # Handle if GUT response was saved as stringified dict
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
                        resp = respostas_coletadas.get(p_texto, diag_data.get(sanitize_column_name(p_texto))) # Use sanitized name
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
if 'aba' not in st.session_state:
    st.session_state.aba = None 

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    login_logo_to_display = DEFAULT_LOGIN_LOGO_PATH
    if os.path.exists(CUSTOM_LOGIN_LOGO_PATH):
        login_logo_to_display = CUSTOM_LOGIN_LOGO_PATH
    
    login_form_placeholder = st.empty() 
    with login_form_placeholder.container():
        st.markdown('<div style="display: flex; justify-content: center; margin-bottom: 20px;">', unsafe_allow_html=True)
        if os.path.exists(login_logo_to_display):
            st.image(login_logo_to_display, width=200) 
        else:
            st.markdown("<h2 style='text-align: center;'>Portal de Diagnóstico</h2>", unsafe_allow_html=True)
            if not os.path.exists(DEFAULT_LOGIN_LOGO_PATH): 
                 st.caption(f"Logo padrão '{DEFAULT_LOGIN_LOGO_FILENAME}' não encontrada. Configure em Admin > Personalizar Aparência ou coloque o arquivo em '{ASSETS_DIR}/'.")

        st.markdown('</div>', unsafe_allow_html=True)
        
        st.session_state.aba = st.radio(
            "Você é:", 
            ["Administrador", "Cliente"], 
            horizontal=True, 
            key="tipo_usuario_radio_v21_styled_top_final", 
            label_visibility="collapsed" 
        )   
        st.markdown('<hr style="margin-top: 0; margin-bottom: 30px;">', unsafe_allow_html=True)

    if st.session_state.aba == "Administrador":
        with login_form_placeholder.container(): 
            st.markdown('<div class="login-container" style="border-top: 6px solid #c0392b;">', unsafe_allow_html=True) 
            if os.path.exists(login_logo_to_display): 
                st.image(login_logo_to_display, width=180)
            st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
            with st.form("form_admin_login_v21_final"):
                u = st.text_input("Usuário", key="admin_u_v21_final_input")
                p = st.text_input("Senha", type="password", key="admin_p_v21_final_input")
                if st.form_submit_button("Entrar", use_container_width=True, icon="🔑"):
                    try:
                        df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                        if not df_creds[(df_creds["Usuario"] == u) & (df_creds["Senha"] == p)].empty:
                            st.session_state.admin_logado = True
                            st.toast("Login de admin bem-sucedido!", icon="🎉")
                            login_form_placeholder.empty() 
                            st.rerun()
                        else: st.error("Usuário/senha admin inválidos.")
                    except Exception as e: st.error(f"Erro login admin: {e}")
            st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    elif st.session_state.aba == "Cliente":
        with login_form_placeholder.container(): 
            st.markdown('<div class="login-container">', unsafe_allow_html=True) 
            if os.path.exists(login_logo_to_display): 
                st.image(login_logo_to_display, width=180)
            st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
            with st.form("form_cliente_login_v21_final"):
                c = st.text_input("CNPJ", key="cli_c_v21_final_input", value=st.session_state.get("last_cnpj_input",""))
                s = st.text_input("Senha", type="password", key="cli_s_v21_final_input")
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


                        st.toast("Login de cliente bem-sucedido!", icon="👋")
                        login_form_placeholder.empty() 
                        st.rerun()
                    except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
            st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    if st.session_state.aba is None: 
        st.stop()

if st.session_state.admin_logado: 
    aba = "Administrador" 
elif st.session_state.cliente_logado: 
    aba = "Cliente"
else: 
    if 'aba' not in st.session_state or st.session_state.aba is None:
      st.error("Estado da aplicação indefinido. Por favor, recarregue.")
      st.stop()
    aba = st.session_state.aba


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
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
        keys_to_clear = [k for k in st.session_state.keys() if k not in ['admin_logado', 'last_cnpj_input']]
        for key_item in keys_to_clear: del st.session_state[key_item] 
        for key_d, value_d in default_session_state.items():
            if key_d not in ['admin_logado', 'last_cnpj_input']: st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False
        st.toast("Logout realizado.", icon="👋")
        st.rerun()
    
    # --- CLIENT PAGE CONTENT ---
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

                # --- Time Tracking Start ---
                # If this question's timing was already initiated (e.g. due to rerun for feedback), don't reset start time
                if st.session_state.previous_question_text_tracker != pergunta:
                    # If moving from a previous question, record its time
                    if st.session_state.current_question_start_time is not None and st.session_state.previous_question_text_tracker is not None:
                        time_spent = time.time() - st.session_state.current_question_start_time
                        st.session_state.diagnostic_question_timings[st.session_state.previous_question_text_tracker] = round(time_spent, 2)
                    
                    # Start timing for the new current question
                    st.session_state.current_question_start_time = time.time()
                    st.session_state.previous_question_text_tracker = pergunta
                elif st.session_state.current_question_start_time is None : # First question
                     st.session_state.current_question_start_time = time.time()
                     st.session_state.previous_question_text_tracker = pergunta
                # --- Time Tracking End ---


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
                # --- Final Time Tracking for the last question ---
                if st.session_state.current_question_start_time is not None and st.session_state.previous_question_text_tracker is not None: # Ensure it was set
                    time_spent_last = time.time() - st.session_state.current_question_start_time
                    st.session_state.diagnostic_question_timings[st.session_state.previous_question_text_tracker] = round(time_spent_last, 2)
                # --- End Final Time Tracking ---

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
                    df_diagnosticos = pd.DataFrame(columns=colunas_base_diagnosticos) # Use base columns for new DF

                # Garantir que todas as colunas de nova_entrada existam em df_diagnosticos
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
            # Ensure all display columns exist
            for col_disp_check in df_display_cliente_cols:
                if col_disp_check not in df_diagnosticos_cliente.columns:
                    df_diagnosticos_cliente[col_disp_check] = "N/D" # Placeholder if missing

            df_display_cliente = df_diagnosticos_cliente[df_display_cliente_cols].copy()
            df_display_cliente.columns = ["Data da Realização", "Média Geral de Satisfação", "Média GUT de Prioridades", "ID do Diagnóstico"]
            
            if st.session_state.get("target_diag_data_for_expansion") is not None:
                target_id = st.session_state.target_diag_data_for_expansion.get("ID_Diagnostico")
                diag_data_expanded = st.session_state.target_diag_data_for_expansion # Already a dict
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
                    medias_cat_painel = {} # Renamed to avoid conflict with cat_cols_data
                    for col, val_expanded in diag_data_expanded.items():
                        original_col_name = None # Find original question text for responses_coletadas_painel
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


            for index_loop, row_diag in df_display_cliente.iterrows(): # Use index_loop to avoid conflict
                diag_id_atual = row_diag["ID do Diagnóstico"]
                # Ensure we get the correct full row from the original df_diagnosticos_cliente
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
                    cat_cols_data = {k.replace("Media_Cat_","").replace("_"," "): float(v) for k,v in diag_data_completa.items() if k.startswith("Media_Cat_") and pd.notna(v)} # Corrected
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
            # Check if a generic survey was submitted in this session and we are not coming from a specific diagnostic link
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
                else: # Fallback or if no options for choice types
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
                    "ID_Diagnostico_Associado": id_diag_associado_atual if id_diag_associado_atual else "", # Store as empty string if None for CSV consistency
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
                    if pd.notna(id_diag_rel_val) and str(id_diag_rel_val).strip(): # Check it's not NaN and not empty string
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
# (Conteúdo do Admin permanece o mesmo da versão anterior, com as novas seções adicionadas)
if aba == "Administrador" and st.session_state.admin_logado:
    admin_logo_path_sidebar = CUSTOM_LOGIN_LOGO_PATH if os.path.exists(CUSTOM_LOGIN_LOGO_PATH) else DEFAULT_LOGIN_LOGO_PATH
    if os.path.exists(admin_logo_path_sidebar):
        st.sidebar.image(admin_logo_path_sidebar, use_container_width=True, width=150) 
    else:
        st.sidebar.markdown("### Painel Admin")

    st.sidebar.success("🟢 Admin Logado")

    if st.sidebar.button("Sair do Painel Admin", icon="🚪", key="logout_admin_v21_final_button", use_container_width=True):
        st.session_state.admin_logado = False
        st.toast("Logout de admin realizado.", icon="👋")
        st.rerun()

    menu_admin_options_map = {
        "Visão Geral e Diagnósticos": "📊",
        "Relatório de Engajamento": "📈", 
        "Gerenciar Notificações": "🔔",
        "Gerenciar Clientes": "👥",
        "Personalizar Aparência": "🎨", 
        "Gerenciar Perguntas Diagnóstico": "📝", 
        "Gerenciar Análises de Perguntas": "💡",
        "Gerenciar FAQ/SAC": "💬", 
        "Gerenciar Perguntas da Pesquisa": "🌟", 
        "Resultados da Pesquisa de Satisfação": "📋", 
        "Gerenciar Instruções": "⚙️",
        "Histórico de Usuários": "📜", 
        "Gerenciar Administradores": "👮"
    }
    admin_page_text_keys = list(menu_admin_options_map.keys())
    admin_options_for_display = [f"{menu_admin_options_map[key]} {key}" for key in admin_page_text_keys]

    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_text_key_v21_final_sess" 
    WIDGET_KEY_SB_ADMIN_MENU = "sb_admin_menu_v21_final_widget_key" 

    def admin_menu_on_change_final_v21(): 
        selected_display_value = st.session_state.get(WIDGET_KEY_SB_ADMIN_MENU) 
        if selected_display_value is None: return 

        new_text_key = None
        for text_key_iter, emoji_iter in menu_admin_options_map.items():
            if f"{emoji_iter} {text_key_iter}" == selected_display_value:
                new_text_key = text_key_iter
                break
        if new_text_key and new_text_key != st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE):
            st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = new_text_key
            # No rerun here

    if SESSION_KEY_FOR_ADMIN_PAGE not in st.session_state or \
       st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE) not in admin_page_text_keys:
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]

    current_admin_page_text_key_for_index = st.session_state[SESSION_KEY_FOR_ADMIN_PAGE]
    
    try:
        expected_display_value_for_current_page = f"{menu_admin_options_map.get(current_admin_page_text_key_for_index, '')} {current_admin_page_text_key_for_index}"
        current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
    except (ValueError, KeyError): 
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0] 
        current_admin_page_text_key_for_index = admin_page_text_keys[0] 
        expected_display_value_for_current_page = f"{menu_admin_options_map[current_admin_page_text_key_for_index]} {current_admin_page_text_key_for_index}"
        current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
        
    st.sidebar.selectbox(
        "Funcionalidades Admin:",
        options=admin_options_for_display,
        index=current_admin_menu_index,
        key=WIDGET_KEY_SB_ADMIN_MENU,
        on_change=admin_menu_on_change_final_v21
    )
    
    menu_admin = st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE, admin_page_text_keys[0])

    if menu_admin not in menu_admin_options_map: 
        menu_admin = admin_page_text_keys[0]
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = menu_admin

    header_display_name = f"{menu_admin_options_map.get(menu_admin, '❓')} {menu_admin}"
    st.header(header_display_name)
    
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
            st.sidebar.error(f"Arquivo '{usuarios_csv}' não encontrado. Funcionalidades limitadas.")
    except Exception as e_load_users_adm_global:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Clientes", "Gerenciar Notificações", "Relatório de Engajamento", "Personalizar Aparência", "Resultados da Pesquisa de Satisfação"]:
            st.sidebar.error(f"Erro ao carregar usuários para admin: {e_load_users_adm_global}")

    # --- Admin Page Content (abbreviated for brevity, use previous full content) ---
    if menu_admin == "Visão Geral e Diagnósticos":
        # (Full content from your "Visão Geral e Diagnósticos" section)
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
            
            cols_to_display_gv = colunas_base_diagnosticos[:] # Make a copy
            dynamic_cols_gv = [col for col in df_filtrada_gv.columns if col.startswith("Media_Cat_") or col.endswith("_Score")]
            for dyn_col_gv in dynamic_cols_gv:
                if dyn_col_gv not in cols_to_display_gv : cols_to_display_gv.append(dyn_col_gv)
            
            # Ensure all columns in cols_to_display_gv actually exist in df_filtrada_gv before trying to display them
            final_cols_to_display_gv = [col for col in cols_to_display_gv if col in df_filtrada_gv.columns]

            st.dataframe(df_filtrada_gv[final_cols_to_display_gv], use_container_width=True, height=300)


            st.subheader("Detalhes e Ações por Diagnóstico")
            if not df_filtrada_gv.empty:
                # Create a mapping of ID_Diagnostico to a more readable string
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
                    st.write(f"**Data:** {diag_selecionado_data.get('Data', 'N/A')}")
                    st.write(f"**Média Geral:** {diag_selecionado_data.get('Média Geral', 'N/A')}")
                    st.write(f"**GUT Média:** {diag_selecionado_data.get('GUT Média', 'N/A')}")
                    st.write(f"**Resumo Cliente:** {diag_selecionado_data.get('Diagnóstico', 'N/A')}")
                    st.write(f"**Análise Cliente:** {diag_selecionado_data.get('Análise do Cliente', 'N/A')}")

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
        # (Full content from your "Relatório de Engajamento" section, including time analysis chart)
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
            st.subheader("Visualizações Gráficas")
            
            c1_charts, c2_charts = st.columns(2)
            with c1_charts:
                if not df_diagnosticos_eng.empty:
                    fig_timeline = create_diagnostics_timeline_chart(df_diagnosticos_eng)
                    if fig_timeline: st.plotly_chart(fig_timeline, use_container_width=True)
                    else: st.caption("Não há dados suficientes para o gráfico de linha do tempo.")
                else: st.caption("Nenhum diagnóstico para gerar linha do tempo.")
            
            with c2_charts:
                fig_engagement_pie = create_client_engagement_pie(df_usuarios_admin_geral)
                if fig_engagement_pie: st.plotly_chart(fig_engagement_pie, use_container_width=True)
                else: st.caption("Não há dados suficientes para o gráfico de engajamento.")

            if not df_diagnosticos_eng.empty:
                fig_avg_cat_scores = create_avg_category_scores_chart(df_diagnosticos_eng)
                if fig_avg_cat_scores: st.plotly_chart(fig_avg_cat_scores, use_container_width=True)
                else: st.caption("Não há dados de categorias para o gráfico de médias.")
            
            st.markdown("---")
            st.subheader("Análise de Tempo de Resposta a Diagnósticos")
            if not df_diagnosticos_eng.empty and 'TimingsPerguntasJSON' in df_diagnosticos_eng.columns:
                fig_avg_time = create_avg_time_per_question_chart(df_diagnosticos_eng)
                if fig_avg_time:
                    st.plotly_chart(fig_avg_time, use_container_width=True)
                else:
                    st.caption("Não há dados de tempo suficientes ou válidos para exibir o gráfico de tempo médio por pergunta.")
                
                all_timings_list = []
                for _, row_diag_time in df_diagnosticos_eng.iterrows():
                    if pd.notna(row_diag_time['TimingsPerguntasJSON']):
                        try:
                            timings_dict_list = json.loads(row_diag_time['TimingsPerguntasJSON'])
                            for pergunta_list, tempo_list in timings_dict_list.items():
                                all_timings_list.append({'Pergunta': pergunta_list, 'TempoSegundos': float(tempo_list)})
                        except: continue
                
                if all_timings_list:
                    df_times_list = pd.DataFrame(all_timings_list)
                    if not df_times_list.empty:
                        avg_times_list = df_times_list.groupby('Pergunta')['TempoSegundos'].agg(['mean', 'count', 'sum']).reset_index()
                        avg_times_list.columns = ['Pergunta', 'Tempo Médio (s)', 'Nº Respostas Cronometradas', 'Tempo Total (s)']
                        avg_times_list = avg_times_list.sort_values(by='Tempo Médio (s)', ascending=False)
                        with st.expander("Ver todos os tempos médios por pergunta"):
                            st.dataframe(avg_times_list, use_container_width=True)
                    else: st.caption("Nenhum dado de tempo válido encontrado.")
                else: st.caption("Nenhum dado de tempo válido encontrado.")
            else:
                st.caption("Nenhum diagnóstico com dados de tempo de resposta encontrado.")
        else:
            st.info("Nenhum usuário cadastrado para gerar relatórios.")
    elif menu_admin == "Gerenciar Notificações":
        # (Full content from your "Gerenciar Notificações" section)
        st.subheader("Enviar e Gerenciar Notificações para Clientes")
        def criar_notificacao_admin(cnpj_cliente, mensagem, id_diagnostico_relacionado=None): # Renamed to avoid conflict if defined globally
            try:
                df_notif_admin = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente':str, 'ID_Diagnostico_Relacionado':str})
            except (FileNotFoundError, pd.errors.EmptyDataError):
                df_notif_admin = pd.DataFrame(columns=colunas_base_notificacoes)

            novo_id_notif_admin = str(uuid.uuid4())
            nova_notif_admin = pd.DataFrame([{
                "ID_Notificacao": novo_id_notif_admin,
                "CNPJ_Cliente": cnpj_cliente,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Mensagem": mensagem,
                "Lida": False,
                "ID_Diagnostico_Relacionado": id_diagnostico_relacionado if pd.notna(id_diagnostico_relacionado) and str(id_diagnostico_relacionado).strip() else ""
            }])
            df_notif_admin = pd.concat([df_notif_admin, nova_notif_admin], ignore_index=True)
            df_notif_admin.to_csv(notificacoes_csv, index=False, encoding='utf-8')
            return True
        
        st.subheader("Enviar Nova Notificação")
        with st.form("form_nova_notificacao_v21"):
            clientes_disp_notif = ["Todos"] + (df_usuarios_admin_geral["CNPJ"].tolist() if not df_usuarios_admin_geral.empty else [])
            
            map_cnpj_to_empresa_notif_form = {}
            if not df_usuarios_admin_geral.empty:
                map_cnpj_to_empresa_notif_form = pd.Series(df_usuarios_admin_geral.Empresa.values, index=df_usuarios_admin_geral.CNPJ).to_dict()

            def format_cnpj_empresa_notif_form(cnpj_val_form):
                if cnpj_val_form == "Todos": return "Todos os Clientes"
                return f"{cnpj_val_form} ({map_cnpj_to_empresa_notif_form.get(cnpj_val_form, 'Empresa Desconhecida')})"

            cnpj_alvo_notif_form = st.selectbox("Selecione o Cliente (CNPJ):", options=clientes_disp_notif, format_func=format_cnpj_empresa_notif_form, key="notif_cnpj_v21")
            mensagem_notif_form = st.text_area("Mensagem da Notificação:", key="notif_msg_v21", height=100)
            id_diag_rel_notif_input_form = None
            if cnpj_alvo_notif_form != "Todos" and cnpj_alvo_notif_form:
                try:
                    df_diags_notif_form = pd.read_csv(arquivo_csv, dtype={'CNPJ':str, 'ID_Diagnostico':str})
                    opcoes_diag_cliente_notif_form = ["Nenhum (Notificação Geral)"] + df_diags_notif_form[df_diags_notif_form["CNPJ"] == cnpj_alvo_notif_form]["ID_Diagnostico"].tolist()
                    
                    def format_diag_id_notif_form(diag_id_val_form):
                        if diag_id_val_form == "Nenhum (Notificação Geral)": return diag_id_val_form
                        data_diag_form = df_diags_notif_form[df_diags_notif_form["ID_Diagnostico"] == diag_id_val_form]["Data"].iloc[0]
                        return f"ID: {diag_id_val_form} (Data: {data_diag_form})"

                    id_diag_rel_notif_input_form = st.selectbox("Linkar a um Diagnóstico Específico (Opcional):", 
                                                           options=opcoes_diag_cliente_notif_form, 
                                                           format_func=format_diag_id_notif_form,
                                                           key="notif_diag_id_link_v21")
                    if id_diag_rel_notif_input_form == "Nenhum (Notificação Geral)":
                        id_diag_rel_notif_input_form = None 

                except (FileNotFoundError, pd.errors.EmptyDataError):
                    st.caption("Arquivo de diagnósticos não encontrado para linkar notificação.")

            if st.form_submit_button("Enviar Notificação", type="primary"):
                if not mensagem_notif_form.strip():
                    st.error("A mensagem da notificação não pode estar vazia.")
                else:
                    if cnpj_alvo_notif_form == "Todos":
                        for _, user_row_notif_form in df_usuarios_admin_geral.iterrows():
                            criar_notificacao_admin(user_row_notif_form["CNPJ"], mensagem_notif_form, None) 
                        st.success("Notificações enviadas para todos os clientes!")
                    elif cnpj_alvo_notif_form:
                        criar_notificacao_admin(cnpj_alvo_notif_form, mensagem_notif_form, id_diag_rel_notif_input_form)
                        st.success(f"Notificação enviada para o cliente {cnpj_alvo_notif_form}!")
                    else:
                        st.error("Selecione um cliente ou 'Todos'.")
                    st.rerun() # Rerun to clear form / update history
        
        st.subheader("Histórico de Notificações Enviadas")
        try:
            df_notif_hist_display = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente':str, 'ID_Diagnostico_Relacionado':str}).sort_values(by="Timestamp", ascending=False)
            st.dataframe(df_notif_hist_display, use_container_width=True)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            st.info("Nenhuma notificação enviada ainda.")
    elif menu_admin == "Gerenciar Clientes":
        # (Full content from your "Gerenciar Clientes" section)
        st.subheader("Gerenciamento de Clientes e Acessos")
        if df_usuarios_admin_geral.empty:
            st.info("Nenhum cliente cadastrado.")
        else:
            st.info(f"Total de clientes cadastrados: {len(df_usuarios_admin_geral)}")
            filtro_nome_empresa_gc = st.text_input("Filtrar por Nome da Empresa ou CNPJ:", key="filtro_cliente_v21").lower()
            status_instrucoes_options_gc = ["Todos", "Visualizou Instruções", "Não Visualizou Instruções"]
            filtro_status_instrucoes_gc = st.selectbox("Filtrar por Status das Instruções:", status_instrucoes_options_gc, key="filtro_instrucoes_v21")

            df_display_clientes_gc = df_usuarios_admin_geral.copy()
            if filtro_nome_empresa_gc:
                df_display_clientes_gc = df_display_clientes_gc[
                    df_display_clientes_gc["Empresa"].str.lower().str.contains(filtro_nome_empresa_gc) |
                    df_display_clientes_gc["CNPJ"].str.contains(filtro_nome_empresa_gc) 
                ]
            if filtro_status_instrucoes_gc == "Visualizou Instruções":
                df_display_clientes_gc = df_display_clientes_gc[df_display_clientes_gc["JaVisualizouInstrucoes"] == True]
            elif filtro_status_instrucoes_gc == "Não Visualizou Instruções":
                 df_display_clientes_gc = df_display_clientes_gc[df_display_clientes_gc["JaVisualizouInstrucoes"] == False]

            st.subheader(f"Clientes Filtrados ({len(df_display_clientes_gc)} de {len(df_usuarios_admin_geral)})")
            try:
                df_bloqueados_gc = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str})
                lista_cnpjs_bloqueados_gc = df_bloqueados_gc['CNPJ'].tolist()
            except (FileNotFoundError, pd.errors.EmptyDataError):
                lista_cnpjs_bloqueados_gc = []

            df_display_clientes_gc['StatusBloqueio'] = df_display_clientes_gc['CNPJ'].apply(lambda x: "Bloqueado" if x in lista_cnpjs_bloqueados_gc else "Ativo")
            
            cols_to_show_clientes_gc = ['CNPJ', 'Empresa', 'NomeContato', 'Telefone', 'DiagnosticosDisponiveis', 'TotalDiagnosticosRealizados', 'JaVisualizouInstrucoes', 'StatusBloqueio']
            
            # For adding new users, use a form
            with st.expander("Adicionar Novo Cliente"):
                with st.form("form_add_cliente_v21"):
                    new_cnpj = st.text_input("CNPJ do Novo Cliente*", key="add_cli_cnpj_v21")
                    new_senha = st.text_input("Senha Padrão*", type="password", key="add_cli_senha_v21", value="123456")
                    new_empresa = st.text_input("Nome da Empresa*", key="add_cli_empresa_v21")
                    new_nome_contato = st.text_input("Nome do Contato", key="add_cli_contato_v21")
                    new_telefone = st.text_input("Telefone", key="add_cli_tel_v21")
                    new_diag_disp = st.number_input("Diagnósticos Disponíveis", min_value=0, value=1, key="add_cli_diagdisp_v21")
                    if st.form_submit_button("Adicionar Cliente"):
                        if not new_cnpj or not new_senha or not new_empresa:
                            st.error("CNPJ, Senha e Nome da Empresa são obrigatórios.")
                        elif new_cnpj in df_usuarios_admin_geral['CNPJ'].values:
                            st.error("Este CNPJ já está cadastrado.")
                        else:
                            new_user_data = {
                                "CNPJ": new_cnpj, "Senha": new_senha, "Empresa": new_empresa,
                                "NomeContato": new_nome_contato, "Telefone": new_telefone,
                                "JaVisualizouInstrucoes": False, "DiagnosticosDisponiveis": new_diag_disp,
                                "TotalDiagnosticosRealizados": 0
                            }
                            df_usuarios_admin_geral = pd.concat([df_usuarios_admin_geral, pd.DataFrame([new_user_data])], ignore_index=True)
                            df_usuarios_admin_geral.to_csv(usuarios_csv, index=False, encoding='utf-8')
                            st.success(f"Cliente {new_empresa} adicionado com sucesso!")
                            st.rerun()
            
            st.markdown("#### Editar Clientes Existentes")
            # For editing existing, data_editor is fine for some fields
            # Editable fields directly in data_editor for existing users
            editable_cols_gc = ['Empresa', 'NomeContato', 'Telefone', 'DiagnosticosDisponiveis'] 
            
            # Create a temporary df for editing, only with relevant columns for display + key CNPJ
            df_for_editor_gc = df_display_clientes_gc[ ['CNPJ'] + editable_cols_gc ].copy()

            edited_df_clientes_gc = st.data_editor(
                df_for_editor_gc, 
                key="editor_clientes_gc_v21",
                use_container_width=True,
                disabled=['CNPJ'] # CNPJ should not be edited here
            )

            if st.button("Salvar Alterações nos Clientes Editados", key="save_clientes_edit_gc_v21"):
                # Merge changes back to the main df_usuarios_admin_geral
                # Ensure edited_df_clientes_gc CNPJ is string
                edited_df_clientes_gc['CNPJ'] = edited_df_clientes_gc['CNPJ'].astype(str)
                
                # Update df_usuarios_admin_geral based on the edits
                for index_edit, row_edit in edited_df_clientes_gc.iterrows():
                    cnpj_to_update = row_edit['CNPJ']
                    original_user_index = df_usuarios_admin_geral[df_usuarios_admin_geral['CNPJ'] == cnpj_to_update].index
                    if not original_user_index.empty:
                        for col_to_update in editable_cols_gc:
                            df_usuarios_admin_geral.loc[original_user_index, col_to_update] = row_edit[col_to_update]
                
                # Convert types before saving
                df_usuarios_admin_geral['DiagnosticosDisponiveis'] = pd.to_numeric(df_usuarios_admin_geral['DiagnosticosDisponiveis'], errors='coerce').fillna(1).astype(int)

                df_usuarios_admin_geral.to_csv(usuarios_csv, index=False, encoding='utf-8')
                st.success("Alterações nos clientes existentes salvas!")
                st.rerun()


            st.markdown("---")
            st.subheader("Bloquear/Desbloquear Cliente")
            map_cnpj_to_empresa_block = {}
            if not df_usuarios_admin_geral.empty:
                map_cnpj_to_empresa_block = pd.Series(df_usuarios_admin_geral.Empresa.values, index=df_usuarios_admin_geral.CNPJ).to_dict()

            cnpj_bloqueio_gc = st.selectbox("Selecione CNPJ para Bloquear/Desbloquear:", 
                                          options=["Nenhum"] + (df_usuarios_admin_geral["CNPJ"].tolist() if not df_usuarios_admin_geral.empty else []), 
                                          key="cnpj_block_gc_v21",
                                          format_func=lambda x: f"{x} ({map_cnpj_to_empresa_block.get(x, 'Empresa Desconhecida')})" if x != "Nenhum" else "Nenhum")

            if cnpj_bloqueio_gc != "Nenhum":
                if cnpj_bloqueio_gc in lista_cnpjs_bloqueados_gc:
                    if st.button(f"Desbloquear Cliente {cnpj_bloqueio_gc}", key=f"unblock_{cnpj_bloqueio_gc}_v21"):
                        df_bloqueados_gc = df_bloqueados_gc[df_bloqueados_gc["CNPJ"] != cnpj_bloqueio_gc]
                        df_bloqueados_gc.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                        registrar_acao(cnpj_bloqueio_gc, "Desbloqueio", "Admin desbloqueou cliente.")
                        st.success(f"Cliente {cnpj_bloqueio_gc} desbloqueado.")
                        st.rerun()
                else:
                    if st.button(f"Bloquear Cliente {cnpj_bloqueio_gc}", key=f"block_{cnpj_bloqueio_gc}_v21", type="warning"):
                        df_bloqueados_gc = pd.concat([df_bloqueados_gc, pd.DataFrame([{"CNPJ": cnpj_bloqueio_gc}])], ignore_index=True)
                        df_bloqueados_gc.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                        registrar_acao(cnpj_bloqueio_gc, "Bloqueio", "Admin bloqueou cliente.")
                        st.success(f"Cliente {cnpj_bloqueio_gc} bloqueado.")
                        st.rerun()
    elif menu_admin == "Personalizar Aparência":
        # (Full content from your "Personalizar Aparência" section)
        st.subheader("🎨 Personalizar Aparência do Portal")
        st.markdown("---")
        st.subheader("Logo da Tela de Login")
        st.markdown(f"""
        A logo exibida na tela de login é carregada na seguinte ordem de prioridade:
        1. **Logo Personalizada:** Se carregada aqui, será salva como `{CUSTOM_LOGIN_LOGO_PATH}`.
        2. **Logo Padrão:** Se nenhuma logo personalizada for carregada, o sistema tentará usar `{DEFAULT_LOGIN_LOGO_PATH}`. 
           Certifique-se de que este arquivo exista na pasta `{ASSETS_DIR}/` com sua logo principal.
        """)

        current_logo_path_for_login_admin_view = DEFAULT_LOGIN_LOGO_PATH
        status_logo_admin_view = f"Padrão ({DEFAULT_LOGIN_LOGO_FILENAME})"

        if os.path.exists(CUSTOM_LOGIN_LOGO_PATH):
            current_logo_path_for_login_admin_view = CUSTOM_LOGIN_LOGO_PATH
            status_logo_admin_view = f"Personalizada ({CUSTOM_LOGIN_LOGO_FILENAME})"
        
        st.write(f"**Logo Atualmente Ativa na Tela de Login:** {status_logo_admin_view}")
        if os.path.exists(current_logo_path_for_login_admin_view):
            st.image(current_logo_path_for_login_admin_view, width=200)
            if current_logo_path_for_login_admin_view == CUSTOM_LOGIN_LOGO_PATH:
                if st.button("Remover Logo Personalizada e Usar Padrão", key="remove_custom_login_logo_btn_final_key_v21"):
                    try:
                        os.remove(CUSTOM_LOGIN_LOGO_PATH)
                        st.success(f"Logo personalizada '{CUSTOM_LOGIN_LOGO_FILENAME}' removida. A página de login usará a logo padrão (se existir).")
                        st.rerun()
                    except Exception as e_remove_logo:
                        st.error(f"Erro ao remover logo personalizada: {e_remove_logo}")
        elif current_logo_path_for_login_admin_view == DEFAULT_LOGIN_LOGO_PATH: 
             st.warning(f"Logo padrão '{DEFAULT_LOGIN_LOGO_FILENAME}' não encontrada em '{ASSETS_DIR}/'. Por favor, adicione-a ou carregue uma logo personalizada abaixo.")
        else: 
             st.error(f"Erro: Logo personalizada '{CUSTOM_LOGIN_LOGO_FILENAME}' esperada mas não encontrada.")


        st.markdown("---")
        st.subheader("Carregar Nova Logo Personalizada para Tela de Login")
        st.caption("Recomendado: PNG com fundo transparente, dimensões aprox. 200-250px de largura e até 100px de altura.")
        
        uploaded_login_logo = st.file_uploader("Selecione o arquivo da nova logo:", type=["png", "jpg", "jpeg"], key="admin_login_logo_uploader_final_key_v21") 
        
        if uploaded_login_logo is not None:
            try:
                if not os.path.exists(ASSETS_DIR):
                    os.makedirs(ASSETS_DIR)
                with open(CUSTOM_LOGIN_LOGO_PATH, "wb") as f:
                    f.write(uploaded_login_logo.getbuffer())
                st.success(f"Nova logo para a tela de login salva como '{CUSTOM_LOGIN_LOGO_FILENAME}'! A mudança será visível no próximo acesso à tela de login por um usuário deslogado.")
                st.image(uploaded_login_logo, caption="Nova Logo Carregada", width=150)
                if "admin_login_logo_uploader_final_key_v21" in st.session_state:
                    del st.session_state["admin_login_logo_uploader_final_key_v21"] 
                st.rerun() 
            except Exception as e_upload_logo:
                st.error(f"Erro ao salvar a nova logo: {e_upload_logo}")
        
        st.markdown("---")
        st.subheader("Logos de Clientes (Exibidas no PDF e Painel do Cliente)")
        st.markdown(f"""
        Para adicionar uma logo específica para um cliente, nomeie o arquivo como `CNPJNUMEROS_logo.png` (ou `.jpg`/`.jpeg`) 
        e coloque-o na pasta `{LOGOS_DIR}/`. 
        Exemplo: para o CNPJ `12.345.678/0001-90`, o arquivo seria `12345678000190_logo.png`.
        """)
        if not os.path.exists(LOGOS_DIR):
            st.warning(f"O diretório `{LOGOS_DIR}` não existe. Crie-o para adicionar logos de clientes.")
        else:
            logos_encontrados = [f for f in os.listdir(LOGOS_DIR) if f.endswith(('.png', '.jpg', '.jpeg'))]
            if not logos_encontrados:
                st.info(f"Nenhuma logo de cliente encontrada em `{LOGOS_DIR}`.")
            else:
                with st.expander(f"Ver logos de clientes carregadas ({len(logos_encontrados)})"):
                    for logo_f in logos_encontrados:
                        st.image(os.path.join(LOGOS_DIR, logo_f), caption=logo_f, width=100)
    elif menu_admin == "Gerenciar Perguntas Diagnóstico":
        # (Full content from your "Gerenciar Perguntas Diagnóstico" section)
        st.subheader("Gerenciar Perguntas do Formulário de Diagnóstico")
        try:
            df_perg_diag = pd.read_csv(perguntas_csv, encoding='utf-8')
            if "Categoria" not in df_perg_diag.columns: df_perg_diag["Categoria"] = "Geral" 
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df_perg_diag = pd.DataFrame(columns=colunas_base_perguntas)
            df_perg_diag["Categoria"] = "Geral"

        st.info("Aqui você pode adicionar, editar ou remover as perguntas que aparecerão no diagnóstico do cliente. Use '[Matriz GUT]' no final da pergunta para que ela seja tratada como uma entrada da Matriz GUT (Gravidade, Urgência, Tendência).")
        
        edited_df_perg_diag = st.data_editor(
            df_perg_diag, 
            num_rows="dynamic", 
            key="editor_perguntas_diag_v21",
            use_container_width=True,
            column_config={
                "Pergunta": st.column_config.TextColumn("Texto da Pergunta", required=True, width="large"),
                "Categoria": st.column_config.TextColumn("Categoria da Pergunta", default="Geral", required=True)
            }
        )
        if st.button("Salvar Alterações nas Perguntas do Diagnóstico", key="save_perg_diag_edit_v21"):
            sanitized_questions_diag = [sanitize_column_name(q) for q in edited_df_perg_diag["Pergunta"].tolist()]
            if len(sanitized_questions_diag) != len(set(sanitized_questions_diag)):
                st.error("Existem perguntas que resultariam no mesmo nome de coluna após a sanitização (ex: 'Pergunta Teste?' e 'Pergunta Teste!'). Por favor, diferencie-as mais claramente.")
            elif edited_df_perg_diag["Pergunta"].isnull().any() or (edited_df_perg_diag["Pergunta"] == "").any():
                 st.error("O texto da pergunta não pode ser vazio.")
            else:
                edited_df_perg_diag.to_csv(perguntas_csv, index=False, encoding='utf-8')
                st.success("Perguntas do diagnóstico salvas com sucesso!")
                st.rerun()
    elif menu_admin == "Gerenciar Análises de Perguntas":
        # (Full content from your "Gerenciar Análises de Perguntas" section)
        st.subheader("Gerenciar Análises Automáticas para Respostas do Diagnóstico")
        df_analises_existentes_ga = carregar_analises_perguntas()
        try:
            df_perguntas_base_analise_ga = pd.read_csv(perguntas_csv, encoding='utf-8')
            lista_perguntas_para_analise_ga = df_perguntas_base_analise_ga["Pergunta"].unique().tolist()
        except:
            lista_perguntas_para_analise_ga = []

        if not lista_perguntas_para_analise_ga:
            st.warning("Cadastre perguntas no 'Gerenciar Perguntas Diagnóstico' antes de adicionar análises.")
        else:
            st.info("""
            Configure textos de análise que aparecerão para o cliente dinamicamente com base em suas respostas no diagnóstico.
            - **Faixa Numérica:** Para respostas de escala (1-5). Ex: Min=1, Max=2 -> análise para respostas muito ruins.
            - **Valor Exato Escala:** Para um valor específico da escala. Ex: CondicaoValorExato = '1 - Muito Ruim'.
            - **Score GUT:** Para perguntas [Matriz GUT]. Defina uma faixa de score (G*U*T). Ex: Min=75 (sem Max) -> alta prioridade.
            - **Default:** Uma análise padrão para a pergunta se nenhuma outra condição for atendida.
            """)

            edited_df_analises_ga = st.data_editor(
                df_analises_existentes_ga,
                num_rows="dynamic",
                key="editor_analises_ga_v21",
                use_container_width=True,
                column_config={
                    "ID_Analise": st.column_config.TextColumn("ID (gerado automaticamente)", disabled=True, default=""),
                    "TextoPerguntaOriginal": st.column_config.SelectboxColumn("Pergunta do Diagnóstico", options=lista_perguntas_para_analise_ga, required=True),
                    "TipoCondicao": st.column_config.SelectboxColumn("Tipo de Condição", options=["FaixaNumerica", "ValorExatoEscala", "ScoreGUT", "Default"], required=True),
                    "CondicaoValorMin": st.column_config.NumberColumn("Valor Mínimo (para Faixa/GUT)"),
                    "CondicaoValorMax": st.column_config.NumberColumn("Valor Máximo (para Faixa/GUT)"),
                    "CondicaoValorExato": st.column_config.TextColumn("Valor Exato (para Escala)"),
                    "TextoAnalise": st.column_config.TextColumn("Texto da Análise para o Cliente", required=True, width="large")
                }
            )

            if st.button("Salvar Análises", key="salvar_analises_ga_v21"):
                for i, row_ga in edited_df_analises_ga.iterrows():
                    if pd.isna(row_ga["ID_Analise"]) or row_ga["ID_Analise"] == "":
                        edited_df_analises_ga.loc[i, "ID_Analise"] = str(uuid.uuid4())
                
                edited_df_analises_ga.to_csv(analises_perguntas_csv, index=False, encoding='utf-8')
                st.cache_data.clear() 
                st.success("Análises salvas com sucesso!")
                st.rerun()
    elif menu_admin == "Gerenciar FAQ/SAC":
        # (Full content for "Gerenciar FAQ/SAC")
        st.subheader("Gerenciar Perguntas e Respostas do FAQ/SAC")
        df_faq_admin_gf = carregar_faq().copy() 

        edited_df_faq_admin_gf = st.data_editor(
            df_faq_admin_gf,
            num_rows="dynamic",
            key="editor_faq_gf_v21",
            use_container_width=True,
            column_config={
                "ID_FAQ": st.column_config.TextColumn("ID (Auto)", disabled=True, default=""),
                "CategoriaFAQ": st.column_config.TextColumn("Categoria", default="Geral", required=True),
                "PerguntaFAQ": st.column_config.TextColumn("Pergunta", required=True, width="large"),
                "RespostaFAQ": st.column_config.TextColumn("Resposta", required=True, width="large")
            }
        )

        if st.button("Salvar Alterações no FAQ", key="save_faq_gf_v21"):
            for i, row_faq_save_gf in edited_df_faq_admin_gf.iterrows():
                if pd.isna(row_faq_save_gf["ID_FAQ"]) or row_faq_save_gf["ID_FAQ"] == "":
                    edited_df_faq_admin_gf.loc[i, "ID_FAQ"] = str(uuid.uuid4())
            
            salvar_faq(edited_df_faq_admin_gf)
            st.success("FAQ salvo com sucesso!")
            st.rerun()
    elif menu_admin == "Gerenciar Perguntas da Pesquisa":
        # (Full content for "Gerenciar Perguntas da Pesquisa")
        st.subheader("Gerenciar Perguntas da Pesquisa de Satisfação")
        df_pesquisa_perg_admin_gpp = carregar_pesquisa_perguntas().copy()

        st.info("""
        Configure as perguntas para a pesquisa de satisfação do cliente.
        - **Tipo de Resposta:**
            - `Escala 1-5`: O cliente selecionará um número de 1 a 5.
            - `Texto Livre`: O cliente poderá digitar uma resposta em texto.
            - `Escolha Única`: O cliente selecionará uma opção de uma lista. Insira as opções em "Opções de Resposta", separadas por vírgula (ex: `Sim,Não,Talvez`).
            - `Múltipla Escolha`: O cliente poderá selecionar várias opções de uma lista. Insira as opções como acima.
        - **Ordem:** Define a ordem em que as perguntas aparecem (menor número primeiro).
        - **Ativa:** Marque para incluir a pergunta na pesquisa. Desmarque para ocultá-la.
        """)

        edited_df_pesq_perg_gpp = st.data_editor(
            df_pesquisa_perg_admin_gpp,
            num_rows="dynamic",
            key="editor_pesquisa_perguntas_gpp_v21",
            use_container_width=True,
            column_config={
                "ID_PerguntaPesquisa": st.column_config.TextColumn("ID (Auto)", disabled=True, default=""),
                "TextoPerguntaPesquisa": st.column_config.TextColumn("Texto da Pergunta", required=True, width="large"),
                "TipoRespostaPesquisa": st.column_config.SelectboxColumn("Tipo de Resposta", 
                                                                        options=["Escala 1-5", "Texto Livre", "Escolha Única", "Múltipla Escolha"], 
                                                                        required=True),
                "OpcoesRespostaJSON": st.column_config.TextColumn("Opções de Resposta (JSON list e.g. [\"Op1\", \"Op2\"] ou CSV para auto-conversão)"),
                "Ordem": st.column_config.NumberColumn("Ordem", min_value=0, default=0, format="%d"),
                "Ativa": st.column_config.CheckboxColumn("Ativa?", default=True)
            }
        )

        if st.button("Salvar Perguntas da Pesquisa", key="save_pesquisa_perg_gpp_v21"):
            for i, row_pp_save_gpp in edited_df_pesq_perg_gpp.iterrows():
                if pd.isna(row_pp_save_gpp["ID_PerguntaPesquisa"]) or str(row_pp_save_gpp["ID_PerguntaPesquisa"]).strip() == "":
                    edited_df_pesq_perg_gpp.loc[i, "ID_PerguntaPesquisa"] = str(uuid.uuid4())
                
                opcoes_raw_str_gpp = str(row_pp_save_gpp.get("OpcoesRespostaJSON", ""))
                if pd.notna(opcoes_raw_str_gpp) and opcoes_raw_str_gpp.strip():
                    if not (opcoes_raw_str_gpp.startswith('[') and opcoes_raw_str_gpp.endswith(']')):
                        opcoes_list_gpp = [opt.strip() for opt in opcoes_raw_str_gpp.split(',') if opt.strip()]
                        edited_df_pesq_perg_gpp.loc[i, "OpcoesRespostaJSON"] = json.dumps(opcoes_list_gpp)
                    elif opcoes_raw_str_gpp.lower() == 'nan' or not opcoes_raw_str_gpp.strip() : # Handle NaN string or empty
                         edited_df_pesq_perg_gpp.loc[i, "OpcoesRespostaJSON"] = json.dumps([])
                else: # If empty or NaN ensure it's a valid empty JSON array string
                    edited_df_pesq_perg_gpp.loc[i, "OpcoesRespostaJSON"] = json.dumps([])
            
            salvar_pesquisa_perguntas(edited_df_pesq_perg_gpp)
            st.success("Perguntas da pesquisa salvas com sucesso!")
            st.rerun()
    elif menu_admin == "Resultados da Pesquisa de Satisfação":
        # (Full content for "Resultados da Pesquisa de Satisfação")
        st.subheader("Resultados da Pesquisa de Satisfação dos Clientes")
        df_respostas_pesquisa_admin_rps = carregar_pesquisa_respostas()
        df_perguntas_pesquisa_admin_rps = carregar_pesquisa_perguntas()

        if df_respostas_pesquisa_admin_rps.empty:
            st.info("Nenhuma resposta à pesquisa de satisfação foi registrada ainda.")
        else:
            st.write(f"Total de submissões da pesquisa: {len(df_respostas_pesquisa_admin_rps)}")
            
            if not df_usuarios_admin_geral.empty:
                cnpjs_com_resposta_rps = df_respostas_pesquisa_admin_rps["CNPJ_Cliente"].unique()
                df_nao_responderam_rps = df_usuarios_admin_geral[~df_usuarios_admin_geral["CNPJ"].isin(cnpjs_com_resposta_rps)]
                with st.expander(f"Clientes que ainda não responderam ({len(df_nao_responderam_rps)})"):
                    if df_nao_responderam_rps.empty:
                        st.write("Todos os clientes cadastrados já enviaram ao menos uma resposta.")
                    else:
                        st.dataframe(df_nao_responderam_rps[["CNPJ", "Empresa", "NomeContato"]], use_container_width=True)
            
            st.markdown("---")
            st.subheader("Detalhes das Respostas:")

            map_id_para_texto_pergunta_rps = {}
            if not df_perguntas_pesquisa_admin_rps.empty:
                map_id_para_texto_pergunta_rps = pd.Series(
                    df_perguntas_pesquisa_admin_rps.TextoPerguntaPesquisa.values, 
                    index=df_perguntas_pesquisa_admin_rps.ID_PerguntaPesquisa.astype(str)
                ).to_dict()

            for index_rps, row_resp_rps in df_respostas_pesquisa_admin_rps.sort_values(by="TimestampPreenchimento", ascending=False).iterrows():
                exp_title_rps = f"Resposta de {row_resp_rps.get('EmpresaClientePreenchimento','N/A')} ({row_resp_rps.get('NomeClientePreenchimento','N/A')}) em {row_resp_rps.get('TimestampPreenchimento','N/A')}"
                id_diag_assoc_rps = row_resp_rps.get('ID_Diagnostico_Associado')
                if pd.notna(id_diag_assoc_rps) and str(id_diag_assoc_rps).strip():
                    exp_title_rps += f" (Associado ao Diag. ID: {id_diag_assoc_rps})"

                with st.expander(exp_title_rps):
                    st.write(f"**Cliente:** {row_resp_rps.get('EmpresaClientePreenchimento','N/A')} (CNPJ: {row_resp_rps.get('CNPJ_Cliente','N/A')})")
                    st.write(f"**Contato:** {row_resp_rps.get('NomeClientePreenchimento','N/A')}, {row_resp_rps.get('TelefoneClientePreenchimento','N/A')}")
                    st.write(f"**Data da Resposta:** {row_resp_rps.get('TimestampPreenchimento','N/A')}")
                    if pd.notna(id_diag_assoc_rps) and str(id_diag_assoc_rps).strip():
                         st.write(f"**Diagnóstico Associado (ID):** {id_diag_assoc_rps}")
                    
                    st.markdown("**Respostas:**")
                    try:
                        respostas_json_rps = json.loads(str(row_resp_rps.get("RespostasJSON","{}")))
                        if isinstance(respostas_json_rps, dict):
                            for id_p_rps, resp_dada_rps in respostas_json_rps.items():
                                pergunta_texto_display_rps = map_id_para_texto_pergunta_rps.get(str(id_p_rps), f"ID Pergunta: {id_p_rps} (Texto não encontrado)")
                                st.markdown(f"- **{pergunta_texto_display_rps}:** {resp_dada_rps}")
                        else:
                            st.error("Formato de respostas (JSON) inesperado.")
                    except json.JSONDecodeError:
                        st.error(f"Erro ao decodificar as respostas desta submissão: {row_resp_rps.get('RespostasJSON','{}')}")
                    except TypeError: 
                        st.error("Formato de respostas inválido para esta submissão.")
    elif menu_admin == "Gerenciar Instruções":
        # (Full content from your "Gerenciar Instruções" section)
        st.subheader("Personalizar Texto de Instruções do Portal para Clientes")
        default_instructions_text_gi = """
Bem-vindo(a) ao Portal de Diagnóstico Empresarial!
**Objetivo:** Este portal foi desenvolvido para ajudar você a realizar um diagnóstico completo da sua empresa...
Clique em "Entendi, ir para o portal!" abaixo quando estiver pronto para começar.
""" # (Use your full default text here)
        if not os.path.exists(instrucoes_default_path):
            with open(instrucoes_default_path, "w", encoding="utf-8") as f_default_gi:
                f_default_gi.write(default_instructions_text_gi)
        
        current_instructions_gi = ""
        path_to_use_instr_gi = instrucoes_custom_path if os.path.exists(instrucoes_custom_path) else instrucoes_default_path
        
        try:
            with open(path_to_use_instr_gi, "r", encoding="utf-8") as f_instr_gi:
                current_instructions_gi = f_instr_gi.read()
        except FileNotFoundError:
             current_instructions_gi = default_instructions_text_gi if path_to_use_instr_gi == instrucoes_default_path else "Erro ao carregar instruções."

        st.info(f"Editando o arquivo: `{instrucoes_custom_path if os.path.exists(instrucoes_custom_path) else 'Será salvo como ' + instrucoes_custom_path}`. Se o arquivo customizado for removido, o padrão (`{instrucoes_default_path}`) será usado.")
        edited_instructions_gi = st.text_area("Conteúdo das Instruções (Markdown permitido):", value=current_instructions_gi, height=500, key="instr_editor_gi_v21")
        col_instr1_gi, col_instr2_gi = st.columns(2)
        if col_instr1_gi.button("Salvar Instruções Personalizadas", key="save_instr_gi_v21", type="primary"):
            with open(instrucoes_custom_path, "w", encoding="utf-8") as f_save_instr_gi:
                f_save_instr_gi.write(edited_instructions_gi)
            st.success(f"Instruções personalizadas salvas em '{instrucoes_custom_path}'!")
            st.rerun()
        if os.path.exists(instrucoes_custom_path):
            if col_instr2_gi.button("Restaurar para Instruções Padrão", key="restore_instr_gi_v21"):
                try:
                    os.remove(instrucoes_custom_path)
                    st.success("Instruções personalizadas removidas. O portal usará o texto padrão.")
                    st.rerun()
                except Exception as e_rem_instr_gi:
                    st.error(f"Erro ao remover instruções personalizadas: {e_rem_instr_gi}")
    elif menu_admin == "Histórico de Usuários":
        # (Full content from your "Histórico de Usuários" section)
        st.subheader("Histórico de Ações dos Usuários")
        try:
            df_hist_hu = pd.read_csv(historico_csv, dtype={'CNPJ':str}).sort_values(by="Data", ascending=False)
            if df_hist_hu.empty:
                st.info("Nenhuma ação registrada no histórico.")
            else:
                col_hist_filt1_hu, col_hist_filt2_hu = st.columns(2)
                cnpjs_no_hist_hu = ["Todos"] + df_hist_hu["CNPJ"].unique().tolist()
                cnpj_filtro_hist_hu = col_hist_filt1_hu.selectbox("Filtrar por CNPJ:", cnpjs_no_hist_hu, key="hist_cnpj_filt_hu_v21")
                
                acoes_no_hist_hu = ["Todas"] + df_hist_hu["Ação"].unique().tolist()
                acao_filtro_hist_hu = col_hist_filt2_hu.selectbox("Filtrar por Ação:", acoes_no_hist_hu, key="hist_acao_filt_hu_v21")

                df_hist_filtrado_hu = df_hist_hu.copy()
                if cnpj_filtro_hist_hu != "Todos":
                    df_hist_filtrado_hu = df_hist_filtrado_hu[df_hist_filtrado_hu["CNPJ"] == cnpj_filtro_hist_hu]
                if acao_filtro_hist_hu != "Todos":
                    df_hist_filtrado_hu = df_hist_filtrado_hu[df_hist_filtrado_hu["Ação"] == acao_filtro_hist_hu]
                
                st.dataframe(df_hist_filtrado_hu, use_container_width=True, height=500)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            st.info("Arquivo de histórico não encontrado ou vazio.")
    elif menu_admin == "Gerenciar Administradores":
        # (Full content from your "Gerenciar Administradores" section)
        st.subheader("Gerenciar Contas de Administrador")
        try:
            df_admins_ga = pd.read_csv(admin_credenciais_csv)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df_admins_ga = pd.DataFrame(columns=["Usuario", "Senha"])

        st.info("Adicione ou remova contas de administrador. Cuidado: A remoção é permanente.")
        edited_df_admins_ga = st.data_editor(
            df_admins_ga,
            num_rows="dynamic",
            key="editor_admins_ga_v21",
            column_config={
                "Usuario": st.column_config.TextColumn("Nome de Usuário", required=True),
                "Senha": st.column_config.TextColumn("Senha", type="password", required=True)
            },
            use_container_width=True
        )
        if st.button("Salvar Alterações nos Administradores", key="save_admins_ga_v21", type="primary"):
            if edited_df_admins_ga["Usuario"].duplicated().any():
                st.error("Nomes de usuário de administrador devem ser únicos.")
            elif edited_df_admins_ga["Usuario"].isnull().any() or edited_df_admins_ga["Senha"].isnull().any() or \
                 (edited_df_admins_ga["Usuario"] == "").any() or (edited_df_admins_ga["Senha"] == "").any():
                st.error("Usuário e Senha não podem ser vazios.")
            else:
                edited_df_admins_ga.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                st.success("Lista de administradores atualizada!")
                st.rerun()

# Fallback
if 'aba' not in locals() and not st.session_state.admin_logado and not st.session_state.cliente_logado:
    st.info("Por favor, selecione seu tipo de acesso para iniciar.")
    st.stop()