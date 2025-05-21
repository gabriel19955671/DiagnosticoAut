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
    "current_question_start_time": None, # Para timing de perguntas do diagnóstico
    "diagnostic_question_timings": {},   # Para armazenar timings durante o preenchimento
    "current_survey_responses": {},      # Para armazenar respostas da pesquisa de satisfação
    "selected_faq_category": "Todas",    # Para filtro de FAQ
    "search_faq_query": "",              # Para busca no FAQ
    "selected_faq_id": None,             # Para exibir resposta do FAQ
    "survey_submitted_for_current_diag": False # Flag para pesquisa após diagnóstico
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
                    if col in columns: df_init[col] = default_val
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
                    if len(df_init) > 0 and not df_init.empty: 
                        df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=[default_val] * len(df_init))
                    else: 
                        df_init[col_name] = pd.Series(dtype=object if default_val is pd.NA else type(default_val)) 
                        if not pd.isna(default_val) and len(df_init) == 0: 
                            df_init.loc[0, col_name] = default_val 
                            df_init = df_init.iloc[0:0] 
                            
                    made_changes = True
            if made_changes:
                df_init.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError: 
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
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos, defaults={"TimingsPerguntasJSON": None, "ID_Diagnostico": None}) 
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False, "ID_Diagnostico_Relacionado": None}) 
    # Inicializar novos CSVs
    inicializar_csv(faq_sac_csv, colunas_base_faq, defaults={"CategoriaFAQ": "Geral"})
    inicializar_csv(pesquisa_satisfacao_perguntas_csv, colunas_base_pesquisa_perguntas, defaults={"Ordem": 0, "Ativa": True})
    inicializar_csv(pesquisa_satisfacao_respostas_csv, colunas_base_pesquisa_respostas, defaults={"ID_Diagnostico_Associado": None})

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
@st.cache_data(ttl=60) # Cache por 60 segundos
def carregar_faq():
    try:
        df = pd.read_csv(faq_sac_csv, encoding='utf-8')
        if "ID_FAQ" not in df.columns: # Adiciona ID se não existir (para compatibilidade)
            df["ID_FAQ"] = [str(uuid.uuid4()) for _ in range(len(df))]
            df.to_csv(faq_sac_csv, index=False, encoding='utf-8')
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_faq)

def salvar_faq(df_faq):
    df_faq.to_csv(faq_sac_csv, index=False, encoding='utf-8')
    st.cache_data.clear() # Limpa o cache para recarregar

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
        # Garantir OpcoesRespostaJSON como string (para evitar problemas com NaN float)
        if "OpcoesRespostaJSON" in df.columns:
             df["OpcoesRespostaJSON"] = df["OpcoesRespostaJSON"].astype(str).fillna('[]')

        df.to_csv(pesquisa_satisfacao_perguntas_csv, index=False, encoding='utf-8') # Salva correções
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
        return pd.read_csv(pesquisa_satisfacao_respostas_csv, encoding='utf-8', dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Associado': str})
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
            logo_path = find_client_logo_path(cnpj_pdf) # Client-specific logo for PDF
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
                    resp = respostas_coletadas.get(p_texto, diag_data.get(p_texto, "N/R"))
                    analise_texto = None
                    if "[Matriz GUT]" in p_texto:
                        g,u,t,score=0,0,0,0
                        if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                        elif isinstance(resp, str):
                            try: data_gut=json.loads(resp.replace("'",'"'));g,u,t=int(data_gut.get("G",0)),int(data_gut.get("U",0)),int(data_gut.get("T",0))
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

            # Timings per question in PDF (optional, can be long)
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
                             pdf.multi_cell(0, 5, pdf_safe_text_output(f"- {pergunta_pdf}: {tempo_seg_pdf:.2f} segundos"))
                        pdf.ln(3)
                except (json.JSONDecodeError, TypeError):
                    pass # Ignore if timings are not valid JSON or not a dict


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
            if not os.path.exists(DEFAULT_LOGIN_LOGO_PATH): # More specific message if default is expected but missing
                 st.caption(f"Logo padrão '{DEFAULT_LOGIN_LOGO_FILENAME}' não encontrada. Configure em Admin > Personalizar Aparência ou coloque o arquivo em '{ASSETS_DIR}/'.")

        st.markdown('</div>', unsafe_allow_html=True)
        
        st.session_state.aba = st.radio(
            "Você é:", 
            ["Administrador", "Cliente"], 
            horizontal=True, 
            key="tipo_usuario_radio_v20_styled_top_final", 
            label_visibility="collapsed" 
        )   
        st.markdown('<hr style="margin-top: 0; margin-bottom: 30px;">', unsafe_allow_html=True)

    if st.session_state.aba == "Administrador":
        with login_form_placeholder.container(): 
            st.markdown('<div class="login-container" style="border-top: 6px solid #c0392b;">', unsafe_allow_html=True) 
            if os.path.exists(login_logo_to_display): 
                st.image(login_logo_to_display, width=180)
            st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
            with st.form("form_admin_login_v20_final"):
                u = st.text_input("Usuário", key="admin_u_v20_final_input")
                p = st.text_input("Senha", type="password", key="admin_p_v20_final_input")
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
            with st.form("form_cliente_login_v20_final"):
                c = st.text_input("CNPJ", key="cli_c_v20_final_input", value=st.session_state.get("last_cnpj_input",""))
                s = st.text_input("Senha", type="password", key="cli_s_v20_final_input")
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
                        
                        # Reset states related to a single diagnostic/survey session
                        st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                        st.session_state.respostas_atuais_diagnostico = {}
                        st.session_state.progresso_diagnostico_percentual = 0
                        st.session_state.progresso_diagnostico_contagem = (0,0)
                        st.session_state.feedbacks_respostas = {}
                        st.session_state.diagnostico_enviado_sucesso = False
                        st.session_state.target_diag_data_for_expansion = None 
                        st.session_state.diagnostic_question_timings = {}
                        st.session_state.current_question_start_time = None
                        st.session_state.previous_question_text = None # para timing
                        st.session_state.current_survey_responses = {}
                        st.session_state.survey_submitted_for_current_diag = False


                        st.toast("Login de cliente bem-sucedido!", icon="👋")
                        login_form_placeholder.empty() 
                        st.rerun()
                    except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
            st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    if st.session_state.aba is None: # Should not be reached if radio is always picked
        st.stop()

# Ensure 'aba' is defined if already logged in (for direct page access/refresh)
if st.session_state.admin_logado: 
    aba = "Administrador" 
elif st.session_state.cliente_logado: 
    aba = "Cliente"
else: # Should have been handled by login block, but as a fallback:
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
        "Suporte/FAQ": "💬 Suporte/FAQ", # Nova página
        "Pesquisa de Satisfação": "🌟 Pesquisa de Satisfação", # Nova página
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
        except ValueError: # Fallback if label with count changed and index is off
            current_idx_cli = 0 
            if menu_options_cli_display: # Default to first available if error
                for key_p, val_p in menu_options_cli_map.items():
                    if val_p == menu_options_cli_display[0]:
                        st.session_state.cliente_page = key_p
                        break


    elif menu_options_cli_display: # If default_display_option is None but list is not empty
        current_idx_cli = 0
        for key_page_fallback, val_page_display_fallback in menu_options_cli_map.items():
            if val_page_display_fallback == menu_options_cli_display[0]:
                st.session_state.cliente_page = key_page_fallback
                break

    selected_page_cli_raw = st.sidebar.radio("Menu Cliente", menu_options_cli_display, index=current_idx_cli, key="cli_menu_v20_final_conditional_key") # Unique key
    
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

    if st.sidebar.button("Sair do Portal Cliente", icon="⬅️", key="logout_cliente_v20_final_btn", use_container_width=True): # Unique key
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
            if st.button("Entendi, ir para o portal!", key="cliente_entendeu_instrucoes_v20", type="primary"):
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
            if st.button("Responder Pesquisa de Satisfação", key="responder_pesquisa_pos_diag_v20"):
                st.session_state.cliente_page = "Pesquisa de Satisfação"
                # Passar o ID do diagnóstico recém-concluído para a pesquisa
                st.session_state.survey_id_diagnostico_associado = st.session_state.id_formulario_atual 
                st.rerun()

            if st.button("Voltar ao Painel Principal", key="novo_diag_voltar_painel_v20"):
                st.session_state.diagnostico_enviado_sucesso = False # Reset flag
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

        with st.form(key="diagnostico_form_v20"):
            respostas_cliente = st.session_state.respostas_atuais_diagnostico
            
            for index, row in perg_df.iterrows():
                pergunta = row["Pergunta"]
                categoria_pergunta = row.get("Categoria", "Geral") # Adicionado para contexto

                # --- Time Tracking Start ---
                if st.session_state.current_question_start_time is not None and st.session_state.get("previous_question_text_tracker") == pergunta:
                    pass # Already started timing this question due to a previous rerun for feedback
                elif st.session_state.current_question_start_time is not None and st.session_state.get("previous_question_text_tracker"):
                    time_spent = time.time() - st.session_state.current_question_start_time
                    st.session_state.diagnostic_question_timings[st.session_state.previous_question_text_tracker] = round(time_spent, 2)
                
                st.session_state.current_question_start_time = time.time()
                st.session_state.previous_question_text_tracker = pergunta
                # --- Time Tracking End ---

                st.markdown(f"##### {pergunta}")
                st.caption(f"Categoria: {categoria_pergunta}")

                if "[Matriz GUT]" in pergunta:
                    default_gut = respostas_cliente.get(pergunta, {"G":1, "U":1, "T":1})
                    c1, c2, c3 = st.columns(3)
                    g = c1.radio("Gravidade", [1,2,3,4,5], index=default_gut["G"]-1, key=f"G_{index}_v20", horizontal=True)
                    u = c2.radio("Urgência", [1,2,3,4,5], index=default_gut["U"]-1, key=f"U_{index}_v20", horizontal=True)
                    t = c3.radio("Tendência", [1,2,3,4,5], index=default_gut["T"]-1, key=f"T_{index}_v20", horizontal=True)
                    respostas_cliente[pergunta] = {"G": g, "U": u, "T": t}
                else:
                    opcoes_escala = ["1 - Muito Ruim", "2 - Ruim", "3 - Regular", "4 - Bom", "5 - Excelente"]
                    # Garantir que o default_value seja uma string se as opções forem strings
                    default_value_escala = respostas_cliente.get(pergunta, opcoes_escala[2]) # Default to "Regular"
                    if not isinstance(default_value_escala, str) and default_value_escala in range(1,6): # Handle old numeric saves
                        default_value_escala = opcoes_escala[default_value_escala -1]

                    resposta_escala = st.radio("Selecione sua avaliação:", opcoes_escala, 
                                     index=opcoes_escala.index(default_value_escala) if default_value_escala in opcoes_escala else 2, 
                                     key=f"R_{index}_v20", horizontal=True)
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
            diagnostico_resumo = st.text_area("Resumo do Diagnóstico (sua percepção geral):", height=100, key="diag_resumo_v20", value=st.session_state.get("diag_resumo_val", ""))
            analise_cliente_txt = st.text_area("Sua Análise e Próximos Passos Sugeridos:", height=100, key="analise_cliente_v20", value=st.session_state.get("analise_cliente_val", ""))
            
            st.session_state.diag_resumo_val = diagnostico_resumo
            st.session_state.analise_cliente_val = analise_cliente_txt

            if st.form_submit_button("✅ Enviar Diagnóstico Completo", type="primary", use_container_width=True):
                # --- Final Time Tracking for the last question ---
                if st.session_state.current_question_start_time is not None and st.session_state.get("previous_question_text_tracker"):
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
                    "Email": st.session_state.user.get("Email", ""), # Supondo que email está no user_data
                    "Empresa": st.session_state.user.get("Empresa", ""),
                    "ID_Diagnostico": st.session_state.id_formulario_atual # Salvar ID único
                }

                for pergunta, resposta_data in respostas_cliente.items():
                    col_name = sanitize_column_name(pergunta)
                    nova_entrada[col_name] = resposta_data

                    # Achar categoria da pergunta
                    categoria_da_pergunta_atual = perg_df[perg_df["Pergunta"] == pergunta]["Categoria"].iloc[0] if not perg_df[perg_df["Pergunta"] == pergunta].empty else "Geral"

                    if isinstance(resposta_data, dict) and "G" in resposta_data: # Matriz GUT
                        score_gut = resposta_data["G"] * resposta_data["U"] * resposta_data["T"]
                        nova_entrada[f"{col_name}_Score"] = score_gut
                        soma_gut += score_gut; contador_gut +=1
                        # GUT não entra na média geral de satisfação, mas pode entrar na média da categoria se desejado
                        # medias_por_categoria[categoria_da_pergunta_atual]["soma"] += score_gut # Ou uma lógica diferente para GUT em categorias
                        # medias_por_categoria[categoria_da_pergunta_atual]["contador"] += 1
                    elif isinstance(resposta_data, str) and " - " in resposta_data: # Escala
                        try:
                            valor_numerico = int(resposta_data.split(" - ")[0])
                            soma_geral += valor_numerico; contador_geral +=1
                            medias_por_categoria[categoria_da_pergunta_atual]["soma"] += valor_numerico
                            medias_por_categoria[categoria_da_pergunta_atual]["contador"] += 1
                        except ValueError: pass # Ignora se não for número
                
                nova_entrada["Média Geral"] = f"{soma_geral/contador_geral:.2f}" if contador_geral > 0 else "N/A"
                nova_entrada["GUT Média"] = f"{soma_gut/contador_gut:.2f}" if contador_gut > 0 else "N/A"
                
                for cat_final, data_cat_final in medias_por_categoria.items():
                    media_cat_val = data_cat_final["soma"] / data_cat_final["contador"] if data_cat_final["contador"] > 0 else 0
                    nova_entrada[f"Media_Cat_{sanitize_column_name(cat_final)}"] = f"{media_cat_val:.2f}"

                nova_entrada["Diagnóstico"] = diagnostico_resumo
                nova_entrada["Análise do Cliente"] = analise_cliente_txt
                nova_entrada["Comentarios_Admin"] = "" # Placeholder
                nova_entrada["TimingsPerguntasJSON"] = json.dumps(st.session_state.diagnostic_question_timings)


                try:
                    df_diagnosticos = pd.read_csv(arquivo_csv, dtype={'CNPJ': str, 'ID_Diagnostico':str}, encoding='utf-8')
                except (FileNotFoundError, pd.errors.EmptyDataError):
                    df_diagnosticos = pd.DataFrame(columns=list(nova_entrada.keys()))

                # Garantir que todas as colunas de nova_entrada existam em df_diagnosticos
                for col_key in nova_entrada.keys():
                    if col_key not in df_diagnosticos.columns:
                        df_diagnosticos[col_key] = pd.NA # Ou um valor default apropriado

                df_diagnosticos = pd.concat([df_diagnosticos, pd.DataFrame([nova_entrada])], ignore_index=True)
                df_diagnosticos.to_csv(arquivo_csv, index=False, encoding='utf-8')
                
                # Atualizar contagem de diagnósticos do usuário
                novo_total_realizados = st.session_state.user.get("TotalDiagnosticosRealizados", 0) + 1
                update_user_data(st.session_state.cnpj, "TotalDiagnosticosRealizados", novo_total_realizados)
                
                registrar_acao(st.session_state.cnpj, "Diagnóstico Enviado", f"ID: {st.session_state.id_formulario_atual}")
                st.session_state.diagnostico_enviado_sucesso = True
                
                # Limpar estado para próximo diagnóstico
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
            df_display_cliente = df_diagnosticos_cliente[["Data", "Média Geral", "GUT Média", "ID_Diagnostico"]].copy()
            df_display_cliente.columns = ["Data da Realização", "Média Geral de Satisfação", "Média GUT de Prioridades", "ID do Diagnóstico"]
            
            # Se um diagnóstico específico foi alvo de uma notificação
            if st.session_state.get("target_diag_data_for_expansion") is not None:
                target_id = st.session_state.target_diag_data_for_expansion.get("ID_Diagnostico")
                with st.expander(f"👇 Detalhes do Diagnóstico: {st.session_state.target_diag_data_for_expansion.get('Data')} (ID: {target_id}) - Expandido via Notificação", expanded=True):
                    diag_data_expanded = st.session_state.target_diag_data_for_expansion
                    # ... (código de exibição detalhada, similar ao abaixo) ...
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
                    for col in diag_data_expanded.index:
                        if col not in colunas_base_diagnosticos and not col.startswith("Media_Cat_") and not col.endswith("_Score"):
                           respostas_coletadas_painel[col.replace("_"," ")] = diag_data_expanded[col] # Reverte sanitização
                        if col.startswith("Media_Cat_"):
                            medias_cat_painel[col.replace("Media_Cat_","").replace("_"," ")] = float(diag_data_expanded[col]) if pd.notna(diag_data_expanded[col]) else 0.0


                    if st.button("Gerar PDF Completo deste Diagnóstico", key=f"pdf_expanded_{diag_data_expanded.get('ID_Diagnostico','exp')}", type="primary"):
                        pdf_path = gerar_pdf_diagnostico_completo(diag_data_expanded, st.session_state.user, perg_df_painel, respostas_coletadas_painel, medias_cat_painel, analises_df_painel)
                        if pdf_path:
                            with open(pdf_path, "rb") as fp:
                                st.download_button(label="Baixar PDF Gerado", data=fp, file_name=f"Diagnostico_{st.session_state.user.get('Empresa','Cliente')}_{diag_data_expanded.get('Data').split(' ')[0]}.pdf", mime="application/pdf")
                            os.remove(pdf_path) # Clean up temp file
                    st.markdown("---")
                # Limpar para não reabrir sempre
                st.session_state.target_diag_data_for_expansion = None


            for index, row_diag in df_display_cliente.iterrows():
                diag_id_atual = row_diag["ID do Diagnóstico"]
                diag_data_completa = df_diagnosticos_cliente.loc[index].to_dict()

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

                    # Detalhes das categorias
                    st.markdown("**Médias por Categoria:**")
                    cat_cols_data = {k.replace("Media_Cat_","").replace("_"," "): float(v) for k,v in diag_data_completa.items() if k.startswith("Media_Cat_") and pd.notna(v)}
                    if cat_cols_data:
                        # Radar Chart
                        radar_fig_cliente = create_radar_chart(cat_cols_data, title="Performance por Categoria")
                        if radar_fig_cliente: st.plotly_chart(radar_fig_cliente, use_container_width=True)
                        else: 
                            for cat, media in cat_cols_data.items(): st.write(f"- {cat}: {media:.2f}")
                    else:
                        st.caption("Nenhuma média por categoria calculada para este diagnóstico.")

                    # Detalhes GUT
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
                    
                    # Timings
                    if "TimingsPerguntasJSON" in diag_data_completa and pd.notna(diag_data_completa["TimingsPerguntasJSON"]):
                        with st.expander("Ver tempo gasto por pergunta neste diagnóstico"):
                            try:
                                timings_diag = json.loads(diag_data_completa["TimingsPerguntasJSON"])
                                if timings_diag:
                                    for p_time, t_val in timings_diag.items():
                                        st.write(f"- *{p_time}*: {t_val:.2f} segundos")
                                else:
                                    st.caption("Nenhum dado de tempo registrado.")
                            except (json.JSONDecodeError, TypeError):
                                st.caption("Não foi possível ler os dados de tempo.")
                    
                    # PDF Download
                    perg_df_painel = pd.read_csv(perguntas_csv, encoding='utf-8') if os.path.exists(perguntas_csv) else pd.DataFrame()
                    analises_df_painel = carregar_analises_perguntas()
                    respostas_coletadas_painel = {}
                    for col_key in diag_data_completa.keys():
                         # Evita colunas base, de média ou de score GUT, pega só as respostas diretas
                        if col_key not in colunas_base_diagnosticos and \
                           not col_key.startswith("Media_Cat_") and \
                           not col_key.endswith("_Score") and \
                           col_key not in ["TimingsPerguntasJSON", "ID_Diagnostico"]:
                           respostas_coletadas_painel[col_key.replace("_"," ")] = diag_data_completa[col_key] # Reverte sanitização

                    if st.button("Gerar PDF Completo deste Diagnóstico", key=f"pdf_{diag_id_atual}", type="primary"):
                        pdf_path = gerar_pdf_diagnostico_completo(diag_data_completa, st.session_state.user, perg_df_painel, respostas_coletadas_painel, cat_cols_data, analises_df_painel)
                        if pdf_path:
                            with open(pdf_path, "rb") as fp:
                                st.download_button(label="Baixar PDF Gerado", data=fp, file_name=f"Diagnostico_{st.session_state.user.get('Empresa','Cliente')}_{row_diag['Data da Realização'].split(' ')[0]}.pdf", mime="application/pdf", key=f"dl_pdf_{diag_id_atual}")
                            try:
                                os.remove(pdf_path)
                            except Exception as e_rem_pdf:
                                print(f"Aviso: não foi possível remover o arquivo PDF temporário {pdf_path}: {e_rem_pdf}")


    elif st.session_state.cliente_page == "Suporte/FAQ":
        st.header("💬 Suporte e Perguntas Frequentes (FAQ)")
        df_faq = carregar_faq()

        if df_faq.empty:
            st.info("Nenhuma pergunta frequente cadastrada no momento.")
        else:
            col_filter1, col_filter2 = st.columns([1,2])
            # Filtro por Categoria
            categorias_faq = ["Todas"] + sorted(df_faq["CategoriaFAQ"].astype(str).unique())
            st.session_state.selected_faq_category = col_filter1.selectbox(
                "Filtrar por Categoria:", 
                categorias_faq, 
                index=categorias_faq.index(st.session_state.get("selected_faq_category", "Todas")),
                key="faq_cat_filter_v20"
            )

            # Busca por texto na pergunta
            st.session_state.search_faq_query = col_filter2.text_input(
                "Buscar na Pergunta:", 
                value=st.session_state.get("search_faq_query", ""),
                key="faq_search_query_v20"
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
                    
                    if st.button(f"**{pergunta_faq}**", key=f"faq_q_{faq_id}", use_container_width=True):
                        st.session_state.selected_faq_id = faq_id if st.session_state.selected_faq_id != faq_id else None # Toggle
                    
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

        # Verificar se já respondeu (pode ser mais complexo, ex: por período ou por diagnóstico)
        df_respostas_anteriores = carregar_pesquisa_respostas()
        cnpj_cliente_atual = st.session_state.cnpj
        id_diag_associado_atual = st.session_state.get("survey_id_diagnostico_associado") # Vem do botão pós-diagnóstico

        ja_respondeu_esta_pesquisa_especifica = False
        if id_diag_associado_atual: # Se a pesquisa foi iniciada a partir de um diagnóstico específico
            if not df_respostas_anteriores.empty:
                mask_resposta_especifica = (df_respostas_anteriores["CNPJ_Cliente"] == cnpj_cliente_atual) & \
                                           (df_respostas_anteriores["ID_Diagnostico_Associado"] == id_diag_associado_atual)
                if mask_resposta_especifica.any():
                    ja_respondeu_esta_pesquisa_especifica = True
        
        # Se o cliente já respondeu a pesquisa associada a este diagnóstico específico
        if ja_respondeu_esta_pesquisa_especifica:
            st.success("Obrigado! Você já respondeu à pesquisa de satisfação referente a este diagnóstico.")
            if st.button("Voltar ao Painel Principal", key="pesquisa_ja_respondida_voltar_v20"):
                st.session_state.cliente_page = "Painel Principal"
                st.session_state.survey_id_diagnostico_associado = None # Limpar
                st.rerun()
            st.stop()
        # Se o cliente já respondeu UMA VEZ (genérico, sem ID de diagnóstico), e tentou acessar de novo
        elif not id_diag_associado_atual and not df_respostas_anteriores.empty and \
             (df_respostas_anteriores["CNPJ_Cliente"] == cnpj_cliente_atual).any() and \
             st.session_state.get("survey_submitted_for_current_diag"): # Flag de submissão recente
            st.info("Você já enviou uma pesquisa de satisfação recentemente. Obrigado!")
            if st.button("Voltar ao Painel Principal", key="pesquisa_recente_voltar_v20"):
                st.session_state.cliente_page = "Painel Principal"
                st.rerun()
            st.stop()


        st.markdown("Sua opinião é muito importante para nós! Por favor, dedique alguns momentos para responder.")
        
        with st.form("form_pesquisa_satisfacao_v20"):
            respostas_coletadas_pesquisa = {}
            for _, p_row in df_perguntas_ativas.iterrows():
                id_pergunta = str(p_row["ID_PerguntaPesquisa"])
                texto_pergunta = p_row["TextoPerguntaPesquisa"]
                tipo_resposta = p_row["TipoRespostaPesquisa"]
                opcoes_json_str = p_row.get("OpcoesRespostaJSON", "[]")
                try:
                    opcoes_lista = json.loads(opcoes_json_str) if pd.notna(opcoes_json_str) and isinstance(opcoes_json_str, str) and opcoes_json_str.strip() else []
                except json.JSONDecodeError:
                    opcoes_lista = []


                st.markdown(f"##### {texto_pergunta}")
                if tipo_resposta == "Escala 1-5":
                    respostas_coletadas_pesquisa[id_pergunta] = st.radio("", [1,2,3,4,5], key=f"pesq_{id_pergunta}", horizontal=True, label_visibility="collapsed")
                elif tipo_resposta == "Texto Livre":
                    respostas_coletadas_pesquisa[id_pergunta] = st.text_area("", key=f"pesq_{id_pergunta}", height=100, label_visibility="collapsed")
                elif tipo_resposta == "Escolha Única" and opcoes_lista:
                    respostas_coletadas_pesquisa[id_pergunta] = st.radio("", opcoes_lista, key=f"pesq_{id_pergunta}", label_visibility="collapsed")
                elif tipo_resposta == "Múltipla Escolha" and opcoes_lista:
                    respostas_coletadas_pesquisa[id_pergunta] = st.multiselect("", opcoes_lista, key=f"pesq_{id_pergunta}", label_visibility="collapsed")
                else:
                    respostas_coletadas_pesquisa[id_pergunta] = st.text_input("Resposta:", key=f"pesq_{id_pergunta}", label_visibility="collapsed")
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
                    "ID_Diagnostico_Associado": id_diag_associado_atual, # Pode ser None se não veio de um diagnóstico
                    "RespostasJSON": json.dumps(respostas_coletadas_pesquisa)
                }
                df_respostas_anteriores = pd.concat([df_respostas_anteriores, pd.DataFrame([nova_resposta_submissao])], ignore_index=True)
                salvar_pesquisa_respostas(df_respostas_anteriores)
                
                st.success("Obrigado por suas respostas! Sua opinião foi registrada.")
                registrar_acao(cnpj_cliente_atual, "Pesquisa Satisfação Enviada", f"ID Sessão: {nova_resposta_submissao['ID_SessaoRespostaPesquisa']}")
                st.session_state.survey_submitted_for_current_diag = True # Flag
                st.session_state.current_survey_responses = {} # Limpar
                # st.session_state.survey_id_diagnostico_associado = None # Limpar após uso
                
                # Redirecionar ou dar opção de voltar
                if st.button("Voltar ao Painel Principal", key="pesquisa_enviada_voltar_v20"):
                    st.session_state.cliente_page = "Painel Principal"
                    st.session_state.survey_id_diagnostico_associado = None # Limpar
                    st.rerun()


    elif st.session_state.cliente_page == "Notificações":
        st.header(notificacoes_label.replace(f"({notificacoes_nao_lidas_count} Nova(s))", "").strip()) # Título limpo
        df_notif_cliente = pd.DataFrame()
        try:
            df_all_notifs = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente':str, 'ID_Diagnostico_Relacionado': str})
            if not df_all_notifs.empty:
                df_notif_cliente = df_all_notifs[df_all_notifs["CNPJ_Cliente"] == st.session_state.cnpj].sort_values(by="Timestamp", ascending=False)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            pass # df_notif_cliente continua vazio

        if df_notif_cliente.empty:
            st.info("Você não tem nenhuma notificação no momento.")
        else:
            for index, notif_row in df_notif_cliente.iterrows():
                card_key = f"notif_card_{notif_row['ID_Notificacao']}_v20"
                container_notif = st.container()
                with container_notif: # Usar container para melhor controle do layout do card
                    st.markdown(f"""
                    <div class="custom-card {'custom-card-unread' if not notif_row['Lida'] else ''}">
                        <h4>Notificação de {pd.to_datetime(notif_row['Timestamp']).strftime('%d/%m/%Y %H:%M')}</h4>
                        <p>{notif_row['Mensagem']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    cols_notif_actions = st.columns(2)
                    if not notif_row['Lida']:
                        if cols_notif_actions[0].button("Marcar como Lida", key=f"read_{notif_row['ID_Notificacao']}_v20", type="primary"):
                            df_all_notifs.loc[df_all_notifs["ID_Notificacao"] == notif_row['ID_Notificacao'], "Lida"] = True
                            df_all_notifs.to_csv(notificacoes_csv, index=False, encoding='utf-8')
                            st.session_state.force_sidebar_rerun_after_notif_read_v19 = True # Força atualização da contagem no sidebar
                            st.rerun()
                    
                    if pd.notna(notif_row.get("ID_Diagnostico_Relacionado")):
                        id_diag_rel = notif_row["ID_Diagnostico_Relacionado"]
                        action_button_col = cols_notif_actions[1] if not notif_row['Lida'] else cols_notif_actions[0] # Ajusta coluna do botão

                        if action_button_col.button("Ver Detalhes do Diagnóstico", key=f"details_{notif_row['ID_Notificacao']}_v20"):
                            try:
                                df_diag_geral = pd.read_csv(arquivo_csv, dtype={'CNPJ':str, 'ID_Diagnostico':str})
                                diag_data_target = df_diag_geral[df_diag_geral["ID_Diagnostico"] == id_diag_rel]
                                if not diag_data_target.empty:
                                    st.session_state.target_diag_data_for_expansion = diag_data_target.iloc[0].to_dict()
                                    st.session_state.cliente_page = "Painel Principal" # Mudar para página do painel
                                     # Marcar como lida ao clicar em ver detalhes
                                    if not notif_row['Lida']:
                                        df_all_notifs.loc[df_all_notifs["ID_Notificacao"] == notif_row['ID_Notificacao'], "Lida"] = True
                                        df_all_notifs.to_csv(notificacoes_csv, index=False, encoding='utf-8')
                                        st.session_state.force_sidebar_rerun_after_notif_read_v19 = True
                                    st.rerun()
                                else:
                                    st.error("Diagnóstico relacionado não encontrado.")
                            except FileNotFoundError: st.error(f"Arquivo de diagnósticos '{arquivo_csv}' não encontrado.")
                    st.markdown("<hr>", unsafe_allow_html=True)

        if st.session_state.get("force_sidebar_rerun_after_notif_read_v19"): # Se uma notif foi lida, força rerun para atualizar contagem
            st.session_state.force_sidebar_rerun_after_notif_read_v19 = False
            st.rerun() # Este rerun atualizará a contagem de notificações na sidebar


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    admin_logo_path_sidebar = CUSTOM_LOGIN_LOGO_PATH if os.path.exists(CUSTOM_LOGIN_LOGO_PATH) else DEFAULT_LOGIN_LOGO_PATH
    if os.path.exists(admin_logo_path_sidebar):
        st.sidebar.image(admin_logo_path_sidebar, use_container_width=True, width=150) 
    else:
        st.sidebar.markdown("### Painel Admin")

    st.sidebar.success("🟢 Admin Logado")

    if st.sidebar.button("Sair do Painel Admin", icon="🚪", key="logout_admin_v20_final_button", use_container_width=True): # Ensure key is unique
        st.session_state.admin_logado = False
        st.toast("Logout de admin realizado.", icon="👋")
        st.rerun()

    menu_admin_options_map = {
        "Visão Geral e Diagnósticos": "📊",
        "Relatório de Engajamento": "📈", 
        "Gerenciar Notificações": "🔔",
        "Gerenciar Clientes": "👥",
        "Personalizar Aparência": "🎨", 
        "Gerenciar Perguntas Diagnóstico": "📝", # Renomeado para clareza
        "Gerenciar Análises de Perguntas": "💡",
        "Gerenciar FAQ/SAC": "💬", # Novo
        "Gerenciar Perguntas da Pesquisa": "🌟", # Novo
        "Resultados da Pesquisa de Satisfação": "📋", # Novo
        "Gerenciar Instruções": "⚙️",
        "Histórico de Usuários": "📜", 
        "Gerenciar Administradores": "👮"
    }
    admin_page_text_keys = list(menu_admin_options_map.keys())
    admin_options_for_display = [f"{menu_admin_options_map[key]} {key}" for key in admin_page_text_keys]

    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_text_key_v20_final_sess" # Unique session key
    WIDGET_KEY_SB_ADMIN_MENU = "sb_admin_menu_v20_final_widget_key" # Unique widget key

    def admin_menu_on_change_final_v20(): # Unique function name
        selected_display_value = st.session_state.get(WIDGET_KEY_SB_ADMIN_MENU) # Use .get for safety
        if selected_display_value is None: return 

        new_text_key = None
        for text_key_iter, emoji_iter in menu_admin_options_map.items():
            if f"{emoji_iter} {text_key_iter}" == selected_display_value:
                new_text_key = text_key_iter
                break
        if new_text_key and new_text_key != st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE):
            st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = new_text_key
            # st.rerun() # Removido para evitar loop, mudança será pega no próximo rerun natural

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
        on_change=admin_menu_on_change_final_v20
    )
    
    menu_admin = st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE, admin_page_text_keys[0])

    if menu_admin not in menu_admin_options_map: 
        menu_admin = admin_page_text_keys[0]
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = menu_admin

    header_display_name = f"{menu_admin_options_map.get(menu_admin, '❓')} {menu_admin}"
    st.header(header_display_name)
    
    # --- Global Admin Data Loading (df_usuarios_admin_geral) ---
    df_usuarios_admin_geral = pd.DataFrame(columns=colunas_base_usuarios) # Initialize
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

    # --- Admin Page Content ---
    if menu_admin == "Visão Geral e Diagnósticos":
        st.subheader("Visão Geral dos Diagnósticos de Clientes")
        try:
            df_diagnosticos_admin = pd.read_csv(arquivo_csv, dtype={'CNPJ': str, 'ID_Diagnostico': str}, encoding='utf-8')
        except (FileNotFoundError, pd.errors.EmptyDataError):
            st.info("Nenhum diagnóstico encontrado.")
            df_diagnosticos_admin = pd.DataFrame()

        if not df_diagnosticos_admin.empty:
            empresas_com_diag = sorted(df_diagnosticos_admin["Empresa"].unique())
            empresa_selecionada_gv = st.selectbox("Filtrar por Empresa:", ["Todas"] + empresas_com_diag, key="admin_gv_empresa_filter_v20")

            df_filtrada_gv = df_diagnosticos_admin
            if empresa_selecionada_gv != "Todas":
                df_filtrada_gv = df_diagnosticos_admin[df_diagnosticos_admin["Empresa"] == empresa_selecionada_gv]
            
            df_filtrada_gv = df_filtrada_gv.sort_values(by="Data", ascending=False)

            st.dataframe(df_filtrada_gv[colunas_base_diagnosticos + [col for col in df_filtrada_gv.columns if col.startswith("Media_Cat_")]], 
                         use_container_width=True, height=300)

            st.subheader("Detalhes e Ações por Diagnóstico")
            if not df_filtrada_gv.empty:
                id_diagnostico_selecionado = st.selectbox(
                    "Selecione um Diagnóstico para ver detalhes ou adicionar comentários:", 
                    options=["Nenhum"] + df_filtrada_gv["ID_Diagnostico"].tolist(),
                    format_func=lambda x: f"ID: {x} ({df_filtrada_gv[df_filtrada_gv['ID_Diagnostico']==x]['Data'].iloc[0]} - {df_filtrada_gv[df_filtrada_gv['ID_Diagnostico']==x]['Empresa'].iloc[0]})" if x != "Nenhum" else "Nenhum",
                    key="admin_select_diag_details_v20"
                )

                if id_diagnostico_selecionado != "Nenhum":
                    diag_selecionado_data = df_diagnosticos_admin[df_diagnosticos_admin["ID_Diagnostico"] == id_diagnostico_selecionado].iloc[0]
                    
                    with st.expander("Ver/Editar Comentários do Consultor", expanded=True):
                        comentario_atual = diag_selecionado_data.get("Comentarios_Admin", "")
                        comentario_novo = st.text_area("Seus Comentários/Feedback para o Cliente:", value=comentario_atual if pd.notna(comentario_atual) else "", height=150, key=f"com_admin_{id_diagnostico_selecionado}_v20")
                        if st.button("Salvar Comentário", key=f"save_com_admin_{id_diagnostico_selecionado}_v20"):
                            df_diagnosticos_admin.loc[df_diagnosticos_admin["ID_Diagnostico"] == id_diagnostico_selecionado, "Comentarios_Admin"] = comentario_novo
                            df_diagnosticos_admin.to_csv(arquivo_csv, index=False, encoding='utf-8')
                            st.success("Comentário salvo!")
                            # Enviar notificação ao cliente (opcional)
                            # criar_notificacao(diag_selecionado_data['CNPJ'], f"Seu consultor adicionou comentários ao diagnóstico de {diag_selecionado_data['Data']}.", id_diagnostico_selecionado)
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
                                for pergunta_t, tempo_t in timings.items():
                                    st.markdown(f"- `{pergunta_t}`: {tempo_t:.2f} segundos")
                            except (json.JSONDecodeError, TypeError):
                                st.caption("Não foi possível carregar os dados de tempo.")
            else:
                st.info("Nenhum diagnóstico para exibir com o filtro atual.")
        else:
            st.info("Ainda não há diagnósticos registrados no sistema.")

    elif menu_admin == "Relatório de Engajamento":
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
            
            # Análise de Tempo de Resposta a Diagnósticos
            st.markdown("---")
            st.subheader("Análise de Tempo de Resposta a Diagnósticos")
            if not df_diagnosticos_eng.empty and 'TimingsPerguntasJSON' in df_diagnosticos_eng.columns:
                fig_avg_time = create_avg_time_per_question_chart(df_diagnosticos_eng)
                if fig_avg_time:
                    st.plotly_chart(fig_avg_time, use_container_width=True)
                else:
                    st.caption("Não há dados de tempo suficientes ou válidos para exibir o gráfico de tempo médio por pergunta.")
                
                # Listar todas as perguntas com tempo médio
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
                    avg_times_list = df_times_list.groupby('Pergunta')['TempoSegundos'].agg(['mean', 'count']).reset_index()
                    avg_times_list.columns = ['Pergunta', 'Tempo Médio (s)', 'Nº Respostas Cronometradas']
                    avg_times_list = avg_times_list.sort_values(by='Tempo Médio (s)', ascending=False)
                    with st.expander("Ver todos os tempos médios por pergunta"):
                        st.dataframe(avg_times_list, use_container_width=True)


            else:
                st.caption("Nenhum diagnóstico com dados de tempo de resposta encontrado.")


        else:
            st.info("Nenhum usuário cadastrado para gerar relatórios.")

    elif menu_admin == "Gerenciar Notificações":
        st.subheader("Enviar e Gerenciar Notificações para Clientes")
        # ... (código de Gerenciar Notificações, incluindo criar_notificacao)
        # Definição de criar_notificacao (se ainda não estiver global ou em utilitários)
        def criar_notificacao(cnpj_cliente, mensagem, id_diagnostico_relacionado=None):
            try:
                df_notif = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente':str, 'ID_Diagnostico_Relacionado':str})
            except (FileNotFoundError, pd.errors.EmptyDataError):
                df_notif = pd.DataFrame(columns=colunas_base_notificacoes)

            novo_id_notif = str(uuid.uuid4())
            nova_notif = pd.DataFrame([{
                "ID_Notificacao": novo_id_notif,
                "CNPJ_Cliente": cnpj_cliente,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Mensagem": mensagem,
                "Lida": False,
                "ID_Diagnostico_Relacionado": id_diagnostico_relacionado
            }])
            df_notif = pd.concat([df_notif, nova_notif], ignore_index=True)
            df_notif.to_csv(notificacoes_csv, index=False, encoding='utf-8')
            return True
        
        st.subheader("Enviar Nova Notificação")
        with st.form("form_nova_notificacao_v20"):
            clientes_disp = ["Todos"] + df_usuarios_admin_geral["CNPJ"].tolist() if not df_usuarios_admin_geral.empty else ["Todos"]
            
            # Melhorar a exibição do CNPJ com o nome da empresa
            map_cnpj_to_empresa_notif = {}
            if not df_usuarios_admin_geral.empty:
                map_cnpj_to_empresa_notif = pd.Series(df_usuarios_admin_geral.Empresa.values, index=df_usuarios_admin_geral.CNPJ).to_dict()

            def format_cnpj_empresa_notif(cnpj_val):
                if cnpj_val == "Todos": return "Todos os Clientes"
                return f"{cnpj_val} ({map_cnpj_to_empresa_notif.get(cnpj_val, 'Empresa Desconhecida')})"

            cnpj_alvo_notif = st.selectbox("Selecione o Cliente (CNPJ):", options=clientes_disp, format_func=format_cnpj_empresa_notif, key="notif_cnpj_v20")
            
            mensagem_notif = st.text_area("Mensagem da Notificação:", key="notif_msg_v20", height=100)
            
            # Opcional: Linkar a um diagnóstico específico
            id_diag_rel_notif_input = None
            if cnpj_alvo_notif != "Todos" and cnpj_alvo_notif:
                try:
                    df_diags_notif = pd.read_csv(arquivo_csv, dtype={'CNPJ':str, 'ID_Diagnostico':str})
                    opcoes_diag_cliente_notif = ["Nenhum (Notificação Geral)"] + df_diags_notif[df_diags_notif["CNPJ"] == cnpj_alvo_notif]["ID_Diagnostico"].tolist()
                    
                    def format_diag_id_notif(diag_id_val):
                        if diag_id_val == "Nenhum (Notificação Geral)": return diag_id_val
                        data_diag = df_diags_notif[df_diags_notif["ID_Diagnostico"] == diag_id_val]["Data"].iloc[0]
                        return f"ID: {diag_id_val} (Data: {data_diag})"

                    id_diag_rel_notif_input = st.selectbox("Linkar a um Diagnóstico Específico (Opcional):", 
                                                           options=opcoes_diag_cliente_notif, 
                                                           format_func=format_diag_id_notif,
                                                           key="notif_diag_id_link_v20")
                    if id_diag_rel_notif_input == "Nenhum (Notificação Geral)":
                        id_diag_rel_notif_input = None # Garantir que seja None se não selecionado

                except (FileNotFoundError, pd.errors.EmptyDataError):
                    st.caption("Arquivo de diagnósticos não encontrado para linkar notificação.")


            if st.form_submit_button("Enviar Notificação", type="primary"):
                if not mensagem_notif.strip():
                    st.error("A mensagem da notificação não pode estar vazia.")
                else:
                    if cnpj_alvo_notif == "Todos":
                        for idx_notif, user_row_notif in df_usuarios_admin_geral.iterrows():
                            criar_notificacao(user_row_notif["CNPJ"], mensagem_notif, None) # Notificações em massa geralmente são genéricas
                        st.success("Notificações enviadas para todos os clientes!")
                    elif cnpj_alvo_notif:
                        criar_notificacao(cnpj_alvo_notif, mensagem_notif, id_diag_rel_notif_input)
                        st.success(f"Notificação enviada para o cliente {cnpj_alvo_notif}!")
                    else:
                        st.error("Selecione um cliente ou 'Todos'.")
        
        st.subheader("Histórico de Notificações Enviadas")
        try:
            df_notif_hist = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente':str, 'ID_Diagnostico_Relacionado':str}).sort_values(by="Timestamp", ascending=False)
            st.dataframe(df_notif_hist, use_container_width=True)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            st.info("Nenhuma notificação enviada ainda.")


    elif menu_admin == "Gerenciar Clientes":
        st.subheader("Gerenciamento de Clientes e Acessos")
        # ... (código de Gerenciar Clientes, incluindo filtros, bloqueio, etc.)
        if df_usuarios_admin_geral.empty:
            st.info("Nenhum cliente cadastrado.")
        else:
            st.info(f"Total de clientes cadastrados: {len(df_usuarios_admin_geral)}")

            filtro_nome_empresa = st.text_input("Filtrar por Nome da Empresa ou CNPJ:", key="filtro_cliente_v20").lower()
            
            status_instrucoes_options = ["Todos", "Visualizou Instruções", "Não Visualizou Instruções"]
            filtro_status_instrucoes = st.selectbox("Filtrar por Status das Instruções:", status_instrucoes_options, key="filtro_instrucoes_v20")


            df_display_clientes = df_usuarios_admin_geral.copy()

            if filtro_nome_empresa:
                df_display_clientes = df_display_clientes[
                    df_display_clientes["Empresa"].str.lower().str.contains(filtro_nome_empresa) |
                    df_display_clientes["CNPJ"].str.contains(filtro_nome_empresa) # CNPJ é exato, mas o input é lower
                ]
            
            if filtro_status_instrucoes == "Visualizou Instruções":
                df_display_clientes = df_display_clientes[df_display_clientes["JaVisualizouInstrucoes"] == True]
            elif filtro_status_instrucoes == "Não Visualizou Instruções":
                 df_display_clientes = df_display_clientes[df_display_clientes["JaVisualizouInstrucoes"] == False]


            st.subheader(f"Clientes Filtrados ({len(df_display_clientes)} de {len(df_usuarios_admin_geral)})")
            
            # Carregar lista de bloqueados
            try:
                df_bloqueados = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str})
                lista_cnpjs_bloqueados = df_bloqueados['CNPJ'].tolist()
            except (FileNotFoundError, pd.errors.EmptyDataError):
                lista_cnpjs_bloqueados = []

            # Adicionar coluna de status de bloqueio para exibição
            df_display_clientes['StatusBloqueio'] = df_display_clientes['CNPJ'].apply(lambda x: "Bloqueado" if x in lista_cnpjs_bloqueados else "Ativo")
            
            cols_to_show_clientes = ['CNPJ', 'Empresa', 'NomeContato', 'Telefone', 'DiagnosticosDisponiveis', 'TotalDiagnosticosRealizados', 'JaVisualizouInstrucoes', 'StatusBloqueio']
            edited_df_clientes = st.data_editor(
                df_display_clientes[cols_to_show_clientes], 
                num_rows="dynamic", 
                key="editor_clientes_v20",
                use_container_width=True,
                # Desabilitar edição de algumas colunas diretamente no editor se necessário, ou tratar no save
                disabled=['CNPJ', 'TotalDiagnosticosRealizados', 'JaVisualizouInstrucoes', 'StatusBloqueio'] 
            )

            if st.button("Salvar Alterações nos Clientes", key="save_clientes_edit_v20"):
                # Este é um exemplo simplificado. Para um CRUD completo no data_editor,
                # você precisaria comparar 'edited_df_clientes' com 'df_usuarios_admin_geral'
                # para identificar adições, deleções e modificações.
                # Por ora, vamos focar em atualizar os existentes e adicionar novos.
                
                current_cnpjs_original = set(df_usuarios_admin_geral['CNPJ'])
                
                # Para simplificar, vamos iterar pelo editor e atualizar/adicionar
                # CUIDADO: st.data_editor pode reordenar, então é melhor usar CNPJ como chave para merge/update
                
                # Convert edited_df_clientes 'CNPJ' to string if it's not already
                edited_df_clientes['CNPJ'] = edited_df_clientes['CNPJ'].astype(str)


                # Atualizar df_usuarios_admin_geral com base no edited_df_clientes
                # Merge para encontrar correspondências e novos
                merged_df = df_usuarios_admin_geral.merge(edited_df_clientes[['CNPJ'] + [col for col in edited_df_clientes.columns if col in colunas_base_usuarios and col != 'CNPJ']], on='CNPJ', how='right', suffixes=('', '_edited'))

                for col in ['Empresa', 'NomeContato', 'Telefone', 'DiagnosticosDisponiveis']: # Colunas editáveis
                    edited_col = col + '_edited'
                    if edited_col in merged_df.columns:
                        # Atualiza a coluna original com o valor editado, se houver um valor editado (não NaN)
                        merged_df[col] = merged_df[edited_col].fillna(merged_df[col])
                        # Remove a coluna _edited
                        merged_df.drop(columns=[edited_col], inplace=True)

                # Adicionar novos usuários (aqueles em edited_df que não estavam em df_usuarios_admin_geral)
                # E preencher campos que não são diretamente editáveis no data_editor
                for index, row in merged_df.iterrows():
                    if row['CNPJ'] not in current_cnpjs_original: # Novo usuário
                        if pd.isna(row.get('Senha')): merged_df.loc[index, 'Senha'] = "123456" # Senha padrão para novos
                        if pd.isna(row.get('JaVisualizouInstrucoes')): merged_df.loc[index, 'JaVisualizouInstrucoes'] = False
                        if pd.isna(row.get('TotalDiagnosticosRealizados')): merged_df.loc[index, 'TotalDiagnosticosRealizados'] = 0
                        if pd.isna(row.get('DiagnosticosDisponiveis')): merged_df.loc[index, 'DiagnosticosDisponiveis'] = 1


                # Remover colunas que não pertencem a colunas_base_usuarios (como StatusBloqueio) antes de salvar
                final_df_to_save = merged_df[colunas_base_usuarios].copy()
                # Garantir tipos corretos
                final_df_to_save['DiagnosticosDisponiveis'] = pd.to_numeric(final_df_to_save['DiagnosticosDisponiveis'], errors='coerce').fillna(1).astype(int)
                final_df_to_save['TotalDiagnosticosRealizados'] = pd.to_numeric(final_df_to_save['TotalDiagnosticosRealizados'], errors='coerce').fillna(0).astype(int)
                final_df_to_save['JaVisualizouInstrucoes'] = final_df_to_save['JaVisualizouInstrucoes'].astype(bool)


                final_df_to_save.to_csv(usuarios_csv, index=False, encoding='utf-8')
                st.success("Alterações salvas!")
                st.rerun()


            st.markdown("---")
            st.subheader("Bloquear/Desbloquear Cliente")
            cnpj_bloqueio = st.selectbox("Selecione CNPJ para Bloquear/Desbloquear:", options=["Nenhum"] + df_usuarios_admin_geral["CNPJ"].tolist(), key="cnpj_block_v20",
                                        format_func=lambda x: f"{x} ({map_cnpj_to_empresa_notif.get(x, 'Empresa Desconhecida')})" if x != "Nenhum" else "Nenhum")

            if cnpj_bloqueio != "Nenhum":
                if cnpj_bloqueio in lista_cnpjs_bloqueados:
                    if st.button(f"Desbloquear Cliente {cnpj_bloqueio}", key=f"unblock_{cnpj_bloqueio}_v20"):
                        df_bloqueados = df_bloqueados[df_bloqueados["CNPJ"] != cnpj_bloqueio]
                        df_bloqueados.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                        registrar_acao(cnpj_bloqueio, "Desbloqueio", "Admin desbloqueou cliente.")
                        st.success(f"Cliente {cnpj_bloqueio} desbloqueado.")
                        st.rerun()
                else:
                    if st.button(f"Bloquear Cliente {cnpj_bloqueio}", key=f"block_{cnpj_bloqueio}_v20", type="warning"):
                        df_bloqueados = pd.concat([df_bloqueados, pd.DataFrame([{"CNPJ": cnpj_bloqueio}])], ignore_index=True)
                        df_bloqueados.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                        registrar_acao(cnpj_bloqueio, "Bloqueio", "Admin bloqueou cliente.")
                        st.success(f"Cliente {cnpj_bloqueio} bloqueado.")
                        st.rerun()

    elif menu_admin == "Personalizar Aparência":
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
                if st.button("Remover Logo Personalizada e Usar Padrão", key="remove_custom_login_logo_btn_final_key_v20"):
                    try:
                        os.remove(CUSTOM_LOGIN_LOGO_PATH)
                        st.success(f"Logo personalizada '{CUSTOM_LOGIN_LOGO_FILENAME}' removida. A página de login usará a logo padrão (se existir).")
                        st.rerun()
                    except Exception as e_remove_logo:
                        st.error(f"Erro ao remover logo personalizada: {e_remove_logo}")
        elif current_logo_path_for_login_admin_view == DEFAULT_LOGIN_LOGO_PATH: # Default was expected but not found
             st.warning(f"Logo padrão '{DEFAULT_LOGIN_LOGO_FILENAME}' não encontrada em '{ASSETS_DIR}/'. Por favor, adicione-a ou carregue uma logo personalizada abaixo.")
        else: # Custom was expected but not found (shouldn't happen if remove works)
             st.error(f"Erro: Logo personalizada '{CUSTOM_LOGIN_LOGO_FILENAME}' esperada mas não encontrada.")


        st.markdown("---")
        st.subheader("Carregar Nova Logo Personalizada para Tela de Login")
        st.caption("Recomendado: PNG com fundo transparente, dimensões aprox. 200-250px de largura e até 100px de altura.")
        
        uploaded_login_logo = st.file_uploader("Selecione o arquivo da nova logo:", type=["png", "jpg", "jpeg"], key="admin_login_logo_uploader_final_key_v20") # Unique key
        
        if uploaded_login_logo is not None:
            try:
                if not os.path.exists(ASSETS_DIR):
                    os.makedirs(ASSETS_DIR)
                with open(CUSTOM_LOGIN_LOGO_PATH, "wb") as f:
                    f.write(uploaded_login_logo.getbuffer())
                st.success(f"Nova logo para a tela de login salva como '{CUSTOM_LOGIN_LOGO_FILENAME}'! A mudança será visível no próximo acesso à tela de login por um usuário deslogado.")
                st.image(uploaded_login_logo, caption="Nova Logo Carregada", width=150)
                if "admin_login_logo_uploader_final_key_v20" in st.session_state:
                    del st.session_state["admin_login_logo_uploader_final_key_v20"] 
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
        st.subheader("Gerenciar Perguntas do Formulário de Diagnóstico")
        try:
            df_perg = pd.read_csv(perguntas_csv, encoding='utf-8')
            if "Categoria" not in df_perg.columns: df_perg["Categoria"] = "Geral" # Adiciona se não existir
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df_perg = pd.DataFrame(columns=colunas_base_perguntas)
            df_perg["Categoria"] = "Geral"

        st.info("Aqui você pode adicionar, editar ou remover as perguntas que aparecerão no diagnóstico do cliente. Use '[Matriz GUT]' no final da pergunta para que ela seja tratada como uma entrada da Matriz GUT (Gravidade, Urgência, Tendência).")
        
        edited_df_perg = st.data_editor(
            df_perg, 
            num_rows="dynamic", 
            key="editor_perguntas_v20",
            use_container_width=True,
            column_config={
                "Pergunta": st.column_config.TextColumn("Texto da Pergunta", required=True, width="large"),
                "Categoria": st.column_config.TextColumn("Categoria da Pergunta", default="Geral", required=True)
            }
        )
        if st.button("Salvar Alterações nas Perguntas", key="save_perg_edit_v20"):
            # Verificar se há perguntas duplicadas (após sanitização para nome de coluna)
            # Isso é importante porque nomes de colunas precisam ser únicos
            sanitized_questions = [sanitize_column_name(q) for q in edited_df_perg["Pergunta"].tolist()]
            if len(sanitized_questions) != len(set(sanitized_questions)):
                st.error("Existem perguntas que resultariam no mesmo nome de coluna após a sanitização (ex: 'Pergunta Teste?' e 'Pergunta Teste!'). Por favor, diferencie-as mais claramente.")
            else:
                edited_df_perg.to_csv(perguntas_csv, index=False, encoding='utf-8')
                st.success("Perguntas salvas com sucesso!")
                st.rerun()

    elif menu_admin == "Gerenciar Análises de Perguntas":
        st.subheader("Gerenciar Análises Automáticas para Respostas")
        # ... (código de Gerenciar Análises, como na versão anterior)
        df_analises_existentes = carregar_analises_perguntas()
        try:
            df_perguntas_base_analise = pd.read_csv(perguntas_csv, encoding='utf-8')
            lista_perguntas_para_analise = df_perguntas_base_analise["Pergunta"].unique().tolist()
        except:
            lista_perguntas_para_analise = []

        if not lista_perguntas_para_analise:
            st.warning("Cadastre perguntas no 'Gerenciar Perguntas Diagnóstico' antes de adicionar análises.")
        else:
            st.info("""
            Configure textos de análise que aparecerão para o cliente dinamicamente com base em suas respostas.
            - **Faixa Numérica:** Para respostas de escala (1-5). Ex: Min=1, Max=2 -> análise para respostas muito ruins.
            - **Valor Exato Escala:** Para um valor específico da escala. Ex: CondicaoValorExato = '1 - Muito Ruim'.
            - **Score GUT:** Para perguntas [Matriz GUT]. Defina uma faixa de score (G*U*T). Ex: Min=75 (sem Max) -> alta prioridade.
            - **Default:** Uma análise padrão para a pergunta se nenhuma outra condição for atendida.
            """)

            edited_df_analises = st.data_editor(
                df_analises_existentes,
                num_rows="dynamic",
                key="editor_analises_v20",
                use_container_width=True,
                column_config={
                    "ID_Analise": st.column_config.TextColumn("ID (gerado automaticamente)", disabled=True, default=""),
                    "TextoPerguntaOriginal": st.column_config.SelectboxColumn("Pergunta do Diagnóstico", options=lista_perguntas_para_analise, required=True),
                    "TipoCondicao": st.column_config.SelectboxColumn("Tipo de Condição", options=["FaixaNumerica", "ValorExatoEscala", "ScoreGUT", "Default"], required=True),
                    "CondicaoValorMin": st.column_config.NumberColumn("Valor Mínimo (para Faixa/GUT)"),
                    "CondicaoValorMax": st.column_config.NumberColumn("Valor Máximo (para Faixa/GUT)"),
                    "CondicaoValorExato": st.column_config.TextColumn("Valor Exato (para Escala)"),
                    "TextoAnalise": st.column_config.TextColumn("Texto da Análise para o Cliente", required=True, width="large")
                }
            )

            if st.button("Salvar Análises", key="salvar_analises_v20"):
                # Gerar ID_Analise se estiver faltando
                for i, row in edited_df_analises.iterrows():
                    if pd.isna(row["ID_Analise"]) or row["ID_Analise"] == "":
                        edited_df_analises.loc[i, "ID_Analise"] = str(uuid.uuid4())
                
                edited_df_analises.to_csv(analises_perguntas_csv, index=False, encoding='utf-8')
                st.cache_data.clear() # Limpar cache de analises_perguntas
                st.success("Análises salvas com sucesso!")
                st.rerun()

    elif menu_admin == "Gerenciar FAQ/SAC":
        st.subheader("Gerenciar Perguntas e Respostas do FAQ/SAC")
        df_faq_admin = carregar_faq().copy() # Trabalhar com uma cópia

        edited_df_faq_admin = st.data_editor(
            df_faq_admin,
            num_rows="dynamic",
            key="editor_faq_v20",
            use_container_width=True,
            column_config={
                "ID_FAQ": st.column_config.TextColumn("ID (Auto)", disabled=True, default=""),
                "CategoriaFAQ": st.column_config.TextColumn("Categoria", default="Geral", required=True),
                "PerguntaFAQ": st.column_config.TextColumn("Pergunta", required=True, width="large"),
                "RespostaFAQ": st.column_config.TextColumn("Resposta", required=True, width="large")
            }
        )

        if st.button("Salvar Alterações no FAQ", key="save_faq_v20"):
            for i, row_faq_save in edited_df_faq_admin.iterrows():
                if pd.isna(row_faq_save["ID_FAQ"]) or row_faq_save["ID_FAQ"] == "":
                    edited_df_faq_admin.loc[i, "ID_FAQ"] = str(uuid.uuid4())
            
            salvar_faq(edited_df_faq_admin)
            st.success("FAQ salvo com sucesso!")
            st.rerun()

    elif menu_admin == "Gerenciar Perguntas da Pesquisa":
        st.subheader("Gerenciar Perguntas da Pesquisa de Satisfação")
        df_pesquisa_perg_admin = carregar_pesquisa_perguntas().copy()

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

        edited_df_pesq_perg = st.data_editor(
            df_pesquisa_perg_admin,
            num_rows="dynamic",
            key="editor_pesquisa_perguntas_v20",
            use_container_width=True,
            column_config={
                "ID_PerguntaPesquisa": st.column_config.TextColumn("ID (Auto)", disabled=True, default=""),
                "TextoPerguntaPesquisa": st.column_config.TextColumn("Texto da Pergunta", required=True, width="large"),
                "TipoRespostaPesquisa": st.column_config.SelectboxColumn("Tipo de Resposta", 
                                                                        options=["Escala 1-5", "Texto Livre", "Escolha Única", "Múltipla Escolha"], 
                                                                        required=True),
                "OpcoesRespostaJSON": st.column_config.TextColumn("Opções de Resposta (separadas por vírgula, se aplicável)"),
                "Ordem": st.column_config.NumberColumn("Ordem", min_value=0, default=0, format="%d"),
                "Ativa": st.column_config.CheckboxColumn("Ativa?", default=True)
            }
        )

        if st.button("Salvar Perguntas da Pesquisa", key="save_pesquisa_perg_v20"):
            for i, row_pp_save in edited_df_pesq_perg.iterrows():
                if pd.isna(row_pp_save["ID_PerguntaPesquisa"]) or row_pp_save["ID_PerguntaPesquisa"] == "":
                    edited_df_pesq_perg.loc[i, "ID_PerguntaPesquisa"] = str(uuid.uuid4())
                
                # Converter opções de string para JSON list string
                if pd.notna(row_pp_save["OpcoesRespostaJSON"]) and isinstance(row_pp_save["OpcoesRespostaJSON"], str):
                    opcoes_raw_str = row_pp_save["OpcoesRespostaJSON"]
                    # Se não for já um JSON array válido (ex: "['Op1','Op2']"), converte de "Op1,Op2"
                    if not (opcoes_raw_str.startswith('[') and opcoes_raw_str.endswith(']')):
                        opcoes_list = [opt.strip() for opt in opcoes_raw_str.split(',') if opt.strip()]
                        edited_df_pesq_perg.loc[i, "OpcoesRespostaJSON"] = json.dumps(opcoes_list)
                    # Se for string vazia ou só espaços, ou NaN (que foi convertido para 'nan' string)
                    elif not opcoes_raw_str.strip() or opcoes_raw_str.lower() == 'nan':
                        edited_df_pesq_perg.loc[i, "OpcoesRespostaJSON"] = json.dumps([])


            salvar_pesquisa_perguntas(edited_df_pesq_perg)
            st.success("Perguntas da pesquisa salvas com sucesso!")
            st.rerun()

    elif menu_admin == "Resultados da Pesquisa de Satisfação":
        st.subheader("Resultados da Pesquisa de Satisfação dos Clientes")
        df_respostas_pesquisa_admin = carregar_pesquisa_respostas()
        df_perguntas_pesquisa_admin = carregar_pesquisa_perguntas()

        if df_respostas_pesquisa_admin.empty:
            st.info("Nenhuma resposta à pesquisa de satisfação foi registrada ainda.")
        else:
            st.write(f"Total de submissões da pesquisa: {len(df_respostas_pesquisa_admin)}")
            
            # Identificar clientes que não responderam
            if not df_usuarios_admin_geral.empty:
                cnpjs_com_resposta = df_respostas_pesquisa_admin["CNPJ_Cliente"].unique()
                df_nao_responderam = df_usuarios_admin_geral[~df_usuarios_admin_geral["CNPJ"].isin(cnpjs_com_resposta)]
                with st.expander(f"Clientes que ainda não responderam ({len(df_nao_responderam)})"):
                    if df_nao_responderam.empty:
                        st.write("Todos os clientes cadastrados já enviaram ao menos uma resposta.")
                    else:
                        st.dataframe(df_nao_responderam[["CNPJ", "Empresa", "NomeContato"]], use_container_width=True)
            
            st.markdown("---")
            st.subheader("Detalhes das Respostas:")

            # Mapear IDs de perguntas para texto para melhor visualização
            map_id_para_texto_pergunta = {}
            if not df_perguntas_pesquisa_admin.empty:
                map_id_para_texto_pergunta = pd.Series(df_perguntas_pesquisa_admin.TextoPerguntaPesquisa.values, 
                                                       index=df_perguntas_pesquisa_admin.ID_PerguntaPesquisa.astype(str)).to_dict()

            for index, row_resp in df_respostas_pesquisa_admin.sort_values(by="TimestampPreenchimento", ascending=False).iterrows():
                exp_title = f"Resposta de {row_resp['EmpresaClientePreenchimento']} ({row_resp['NomeClientePreenchimento']}) em {row_resp['TimestampPreenchimento']}"
                if pd.notna(row_resp.get('ID_Diagnostico_Associado')):
                    exp_title += f" (Associado ao Diag. ID: {row_resp['ID_Diagnostico_Associado']})"

                with st.expander(exp_title):
                    st.write(f"**Cliente:** {row_resp['EmpresaClientePreenchimento']} (CNPJ: {row_resp['CNPJ_Cliente']})")
                    st.write(f"**Contato:** {row_resp['NomeClientePreenchimento']}, {row_resp['TelefoneClientePreenchimento']}")
                    st.write(f"**Data da Resposta:** {row_resp['TimestampPreenchimento']}")
                    if pd.notna(row_resp.get('ID_Diagnostico_Associado')):
                         st.write(f"**Diagnóstico Associado (ID):** {row_resp['ID_Diagnostico_Associado']}")
                    
                    st.markdown("**Respostas:**")
                    try:
                        respostas_json = json.loads(row_resp["RespostasJSON"])
                        for id_p, resp_dada in respostas_json.items():
                            pergunta_texto_display = map_id_para_texto_pergunta.get(str(id_p), f"ID Pergunta: {id_p} (Texto não encontrado)")
                            st.markdown(f"- **{pergunta_texto_display}:** {resp_dada}")
                    except json.JSONDecodeError:
                        st.error("Erro ao decodificar as respostas desta submissão.")
                    except TypeError: # Se RespostasJSON for NaN ou algo não decodificável
                        st.error("Formato de respostas inválido para esta submissão.")

            # Aqui você pode adicionar gráficos agregados das respostas
            # Ex: Média para perguntas de escala, contagem para múltipla escolha, etc.
            # Isso exigiria processar o RespostasJSON de todas as linhas.

    elif menu_admin == "Gerenciar Instruções":
        st.subheader("Personalizar Texto de Instruções do Portal para Clientes")
        # ... (código de Gerenciar Instruções, como na versão anterior)
        default_instructions_text = """
Bem-vindo(a) ao Portal de Diagnóstico Empresarial!

**Objetivo:**
Este portal foi desenvolvido para ajudar você a realizar um diagnóstico completo da sua empresa, identificando pontos fortes, áreas de melhoria e oportunidades de crescimento.

**Como Funciona:**
1.  **Login:** Acesse com seu CNPJ e senha fornecidos.
2.  **Instruções (Esta Página):** Leia atentamente as instruções para entender o processo.
3.  **Novo Diagnóstico:** No menu, selecione "Novo Diagnóstico". Você será guiado por uma série de perguntas divididas em categorias. Responda com honestidade e baseando-se na realidade atual da sua empresa.
    * **Perguntas de Escala:** Avalie de 1 (Muito Ruim) a 5 (Excelente).
    * **Matriz GUT:** Para algumas questões, você avaliará Gravidade, Urgência e Tendência (também de 1 a 5) para priorizar ações.
4.  **Resumo e Análise:** Ao final, você terá a oportunidade de fornecer um resumo geral e sua análise inicial.
5.  **Envio:** Após preencher tudo, envie o diagnóstico.
6.  **Painel Principal:** Visualize seus diagnósticos enviados, o feedback do consultor (quando disponível) e baixe relatórios em PDF.
7.  **Notificações:** Fique atento às notificações para comunicados importantes ou atualizações sobre seus diagnósticos.
8.  **Suporte/FAQ:** Consulte perguntas frequentes ou entre em contato se precisar de ajuda.
9.  **Pesquisa de Satisfação:** Após concluir um diagnóstico, ou a qualquer momento pelo menu, sua opinião sobre o processo é valiosa!

**Dicas:**
* Reserve um tempo adequado para responder com calma e atenção.
* Envolva outras pessoas chave da sua empresa, se necessário, para obter respostas mais precisas.
* Utilize os resultados como base para discussões estratégicas e planejamento de ações.

Se precisar de ajuda ou tiver dúvidas, não hesite em contatar o administrador do portal.

Clique em "Entendi, ir para o portal!" abaixo quando estiver pronto para começar.
"""
        if not os.path.exists(instrucoes_default_path):
            with open(instrucoes_default_path, "w", encoding="utf-8") as f_default:
                f_default.write(default_instructions_text)
        
        current_instructions = ""
        path_to_use_instr = instrucoes_custom_path if os.path.exists(instrucoes_custom_path) else instrucoes_default_path
        
        try:
            with open(path_to_use_instr, "r", encoding="utf-8") as f_instr:
                current_instructions = f_instr.read()
        except FileNotFoundError:
             current_instructions = default_instructions_text if path_to_use_instr == instrucoes_default_path else "Erro ao carregar instruções."


        st.info(f"Editando o arquivo: `{instrucoes_custom_path if os.path.exists(instrucoes_custom_path) else 'Será salvo como ' + instrucoes_custom_path}`. Se o arquivo customizado for removido, o padrão (`{instrucoes_default_path}`) será usado.")

        edited_instructions = st.text_area("Conteúdo das Instruções (Markdown permitido):", value=current_instructions, height=500, key="instr_editor_v20")

        col_instr1, col_instr2 = st.columns(2)
        if col_instr1.button("Salvar Instruções Personalizadas", key="save_instr_v20", type="primary"):
            with open(instrucoes_custom_path, "w", encoding="utf-8") as f_save_instr:
                f_save_instr.write(edited_instructions)
            st.success(f"Instruções personalizadas salvas em '{instrucoes_custom_path}'!")
            st.rerun()

        if os.path.exists(instrucoes_custom_path):
            if col_instr2.button("Restaurar para Instruções Padrão", key="restore_instr_v20"):
                try:
                    os.remove(instrucoes_custom_path)
                    st.success("Instruções personalizadas removidas. O portal usará o texto padrão.")
                    st.rerun()
                except Exception as e_rem_instr:
                    st.error(f"Erro ao remover instruções personalizadas: {e_rem_instr}")

    elif menu_admin == "Histórico de Usuários":
        st.subheader("Histórico de Ações dos Usuários")
        # ... (código de Histórico de Usuários, como na versão anterior)
        try:
            df_hist = pd.read_csv(historico_csv, dtype={'CNPJ':str}).sort_values(by="Data", ascending=False)
            if df_hist.empty:
                st.info("Nenhuma ação registrada no histórico.")
            else:
                # Filtros
                col_hist_filt1, col_hist_filt2 = st.columns(2)
                cnpjs_no_hist = ["Todos"] + df_hist["CNPJ"].unique().tolist()
                cnpj_filtro_hist = col_hist_filt1.selectbox("Filtrar por CNPJ:", cnpjs_no_hist, key="hist_cnpj_filt_v20")
                
                acoes_no_hist = ["Todas"] + df_hist["Ação"].unique().tolist()
                acao_filtro_hist = col_hist_filt2.selectbox("Filtrar por Ação:", acoes_no_hist, key="hist_acao_filt_v20")

                df_hist_filtrado = df_hist.copy()
                if cnpj_filtro_hist != "Todos":
                    df_hist_filtrado = df_hist_filtrado[df_hist_filtrado["CNPJ"] == cnpj_filtro_hist]
                if acao_filtro_hist != "Todas":
                    df_hist_filtrado = df_hist_filtrado[df_hist_filtrado["Ação"] == acao_filtro_hist]
                
                st.dataframe(df_hist_filtrado, use_container_width=True, height=500)

        except (FileNotFoundError, pd.errors.EmptyDataError):
            st.info("Arquivo de histórico não encontrado ou vazio.")


    elif menu_admin == "Gerenciar Administradores":
        st.subheader("Gerenciar Contas de Administrador")
        # ... (código de Gerenciar Administradores, como na versão anterior)
        try:
            df_admins = pd.read_csv(admin_credenciais_csv)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df_admins = pd.DataFrame(columns=["Usuario", "Senha"])

        st.info("Adicione ou remova contas de administrador. Cuidado: A remoção é permanente.")
        
        edited_df_admins = st.data_editor(
            df_admins,
            num_rows="dynamic",
            key="editor_admins_v20",
            column_config={
                "Usuario": st.column_config.TextColumn("Nome de Usuário", required=True),
                "Senha": st.column_config.TextColumn("Senha", type="password", required=True)
            },
            use_container_width=True
        )

        if st.button("Salvar Alterações nos Administradores", key="save_admins_v20", type="primary"):
            if edited_df_admins["Usuario"].duplicated().any():
                st.error("Nomes de usuário de administrador devem ser únicos.")
            elif edited_df_admins["Usuario"].isnull().any() or edited_df_admins["Senha"].isnull().any() or \
                 (edited_df_admins["Usuario"] == "").any() or (edited_df_admins["Senha"] == "").any():
                st.error("Usuário e Senha não podem ser vazios.")
            else:
                edited_df_admins.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                st.success("Lista de administradores atualizada!")
                st.rerun()


# Fallback at the very end if 'aba' is still not defined (should be caught by login block)
if 'aba' not in locals() and not st.session_state.admin_logado and not st.session_state.cliente_logado:
    st.info("Por favor, selecione seu tipo de acesso para iniciar.")
    st.stop()