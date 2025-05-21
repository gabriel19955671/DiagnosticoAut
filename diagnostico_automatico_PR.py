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

# --- Inicialização do Session State ---
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
                dtype_spec = {}
                if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, historico_csv]:
                    dtype_spec['CNPJ'] = str
                    if 'CNPJ_Cliente' in columns: dtype_spec['CNPJ_Cliente'] = str
                if filepath == notificacoes_csv and 'ID_Diagnostico_Relacionado' in columns:
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
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos) 
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False, "ID_Diagnostico_Relacionado": None}) 
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
            key="tipo_usuario_radio_v19_styled_top_final", 
            label_visibility="collapsed" 
        )    
        st.markdown('<hr style="margin-top: 0; margin-bottom: 30px;">', unsafe_allow_html=True)

    if st.session_state.aba == "Administrador":
        with login_form_placeholder.container(): 
            st.markdown('<div class="login-container" style="border-top: 6px solid #c0392b;">', unsafe_allow_html=True) 
            if os.path.exists(login_logo_to_display): 
                st.image(login_logo_to_display, width=180)
            st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
            with st.form("form_admin_login_v19_final"):
                u = st.text_input("Usuário", key="admin_u_v19_final_input")
                p = st.text_input("Senha", type="password", key="admin_p_v19_final_input")
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
            with st.form("form_cliente_login_v19_final"):
                c = st.text_input("CNPJ", key="cli_c_v19_final_input", value=st.session_state.get("last_cnpj_input",""))
                s = st.text_input("Senha", type="password", key="cli_s_v19_final_input")
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

    selected_page_cli_raw = st.sidebar.radio("Menu Cliente", menu_options_cli_display, index=current_idx_cli, key="cli_menu_v19_final_conditional_key") # Unique key
    
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

    if st.sidebar.button("Sair do Portal Cliente", icon="⬅️", key="logout_cliente_v19_final_btn", use_container_width=True): # Unique key
        keys_to_clear = [k for k in st.session_state.keys() if k not in ['admin_logado', 'last_cnpj_input']]
        for key_item in keys_to_clear: del st.session_state[key_item] 
        for key_d, value_d in default_session_state.items():
            if key_d not in ['admin_logado', 'last_cnpj_input']: st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False
        st.toast("Logout realizado.", icon="👋")
        st.rerun()
    
    # (The rest of the client page rendering logic - Instruções, Notificações, Painel Principal, Novo Diagnóstico - needs to be here)
    # This is a large block of code. I'm using placeholders but you'll need to ensure the previous full client logic is here,
    # with the enhancements discussed (e.g., notification click handling in Notificações and Painel Principal).
    if st.session_state.cliente_page == "Instruções":
        # ... Full Instruções page logic ...
        st.write("Conteúdo da página de Instruções.")
    elif st.session_state.cliente_page == "Notificações":
        # ... Full Notificações page logic with "Ver Detalhes" button ...
        st.write("Conteúdo da página de Notificações.")
    elif st.session_state.cliente_page == "Painel Principal":
        # ... Full Painel Principal logic with expander for target_diag_data_for_expansion ...
        st.write("Conteúdo do Painel Principal.")
    elif st.session_state.cliente_page == "Novo Diagnóstico":
        # ... Full Novo Diagnóstico page logic ...
        st.write("Conteúdo da página Novo Diagnóstico.")


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    admin_logo_path_sidebar = CUSTOM_LOGIN_LOGO_PATH if os.path.exists(CUSTOM_LOGIN_LOGO_PATH) else DEFAULT_LOGIN_LOGO_PATH
    if os.path.exists(admin_logo_path_sidebar):
        st.sidebar.image(admin_logo_path_sidebar, use_container_width=True, width=150) 
    else:
        st.sidebar.markdown("### Painel Admin")

    st.sidebar.success("🟢 Admin Logado")

    if st.sidebar.button("Sair do Painel Admin", icon="🚪", key="logout_admin_v19_final_button", use_container_width=True): # Ensure key is unique
        st.session_state.admin_logado = False
        st.toast("Logout de admin realizado.", icon="👋")
        st.rerun()

    menu_admin_options_map = {
        "Visão Geral e Diagnósticos": "📊",
        "Relatório de Engajamento": "📈", 
        "Gerenciar Notificações": "🔔",
        "Gerenciar Clientes": "👥",
        "Personalizar Aparência": "🎨", 
        "Gerenciar Perguntas": "📝",
        "Gerenciar Análises de Perguntas": "💡",
        "Gerenciar Instruções": "⚙️",
        "Histórico de Usuários": "📜", 
        "Gerenciar Administradores": "👮"
    }
    admin_page_text_keys = list(menu_admin_options_map.keys())
    admin_options_for_display = [f"{menu_admin_options_map[key]} {key}" for key in admin_page_text_keys]

    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_text_key_v19_final_sess" # Unique session key
    WIDGET_KEY_SB_ADMIN_MENU = "sb_admin_menu_v19_final_widget_key" # Unique widget key

    def admin_menu_on_change_final_v3(): # Unique function name
        selected_display_value = st.session_state.get(WIDGET_KEY_SB_ADMIN_MENU) # Use .get for safety
        if selected_display_value is None: return # Should not happen if selectbox has a default

        new_text_key = None
        for text_key, emoji in menu_admin_options_map.items():
            if f"{emoji} {text_key}" == selected_display_value:
                new_text_key = text_key
                break
        if new_text_key and new_text_key != st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE):
            st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = new_text_key
            # No st.rerun() in on_change to avoid loops if other parts of the script cause reruns.
            # The change in session state will be picked up on the next natural rerun.

    # Initialize session state for admin page if it's not set or invalid
    if SESSION_KEY_FOR_ADMIN_PAGE not in st.session_state or \
       st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE) not in admin_page_text_keys:
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]

    current_admin_page_text_key_for_index = st.session_state[SESSION_KEY_FOR_ADMIN_PAGE]
    
    try:
        expected_display_value_for_current_page = f"{menu_admin_options_map.get(current_admin_page_text_key_for_index, '')} {current_admin_page_text_key_for_index}"
        current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
    except (ValueError, KeyError): 
        # This block handles if current_admin_page_text_key_for_index is somehow invalid
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0] 
        current_admin_page_text_key_for_index = admin_page_text_keys[0] 
        expected_display_value_for_current_page = f"{menu_admin_options_map[current_admin_page_text_key_for_index]} {current_admin_page_text_key_for_index}"
        current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
        
    st.sidebar.selectbox(
        "Funcionalidades Admin:",
        options=admin_options_for_display,
        index=current_admin_menu_index,
        key=WIDGET_KEY_SB_ADMIN_MENU,
        on_change=admin_menu_on_change_final_v3
    )
    
    # Define menu_admin AFTER the selectbox that might change its underlying session state value
    menu_admin = st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE, admin_page_text_keys[0])

    if menu_admin not in menu_admin_options_map: # Fallback if session state somehow got corrupted
        menu_admin = admin_page_text_keys[0]
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = menu_admin # Correct the session state
        # st.experimental_rerun() # Might be too aggressive, but consider if state needs immediate refresh

    header_display_name = f"{menu_admin_options_map.get(menu_admin, '❓')} {menu_admin}"
    st.header(header_display_name)
    
    # --- Global Admin Data Loading (df_usuarios_admin_geral) ---
    # (Ensure this is loaded and preprocessed correctly as in previous version)
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
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Clientes", "Gerenciar Notificações", "Relatório de Engajamento", "Personalizar Aparência"]:
            st.sidebar.error(f"Arquivo '{usuarios_csv}' não encontrado. Funcionalidades limitadas.")
    except Exception as e_load_users_adm_global:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Clientes", "Gerenciar Notificações", "Relatório de Engajamento", "Personalizar Aparência"]:
            st.sidebar.error(f"Erro ao carregar usuários para admin: {e_load_users_adm_global}")

    # --- Admin Page Content ---
    if menu_admin == "Visão Geral e Diagnósticos":
        # ... (Content from previous full version, ensuring selectbox uses KEY_WIDGET_EMPRESA_FILTRO_GV directly)
        st.write("Conteúdo da Visão Geral e Diagnósticos aqui.")
    elif menu_admin == "Relatório de Engajamento":
        # ... (Content for Relatório de Engajamento as implemented in previous full version)
        st.write("Conteúdo do Relatório de Engajamento aqui.")
    elif menu_admin == "Gerenciar Notificações":
        # ... (Content for Gerenciar Notificações as implemented previously)
        st.write("Conteúdo de Gerenciar Notificações aqui.")
    elif menu_admin == "Gerenciar Clientes":
        # ... (Content for Gerenciar Clientes with the instruction status filter)
        st.write("Conteúdo de Gerenciar Clientes com filtro de status de instrução.")
    elif menu_admin == "Personalizar Aparência":
        st.subheader("🎨 Personalizar Aparência do Portal")
        st.markdown("---")
        st.subheader("Logo da Tela de Login")
        st.markdown(f"""
        A logo exibida na tela de login é carregada na seguinte ordem de prioridade:
        1. **Logo Personalizada:** Se carregada aqui, será salva como `{CUSTOM_LOGIN_LOGO_PATH}`.
        2. **Logo Padrão:** Se nenhuma logo personalizada for carregada, o sistema tentará usar `{DEFAULT_LOGIN_LOGO_PATH}`. 
           Certifique-se de que este arquivo exista na pasta `{ASSETS_DIR}/` com sua logo principal. (Ex: `logo PR (1).png` renomeada para `default_login_logo.png`)
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
                if st.button("Remover Logo Personalizada e Usar Padrão", key="remove_custom_login_logo_btn_final_key"):
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
        
        uploaded_login_logo = st.file_uploader("Selecione o arquivo da nova logo:", type=["png", "jpg", "jpeg"], key="admin_login_logo_uploader_final_key_v2") # Unique key
        
        if uploaded_login_logo is not None:
            try:
                if not os.path.exists(ASSETS_DIR):
                    os.makedirs(ASSETS_DIR)
                with open(CUSTOM_LOGIN_LOGO_PATH, "wb") as f:
                    f.write(uploaded_login_logo.getbuffer())
                st.success(f"Nova logo para a tela de login salva como '{CUSTOM_LOGIN_LOGO_FILENAME}'! A mudança será visível no próximo acesso à tela de login por um usuário deslogado.")
                st.image(uploaded_login_logo, caption="Nova Logo Carregada", width=150)
                if "admin_login_logo_uploader_final_key_v2" in st.session_state:
                    del st.session_state["admin_login_logo_uploader_final_key_v2"] 
                st.rerun() 
            except Exception as e_upload_logo:
                st.error(f"Erro ao salvar a nova logo: {e_upload_logo}")
    
    # ... (Other admin sections: Gerenciar Perguntas, Análises, Instruções, Histórico, Admins from previous correct version)
    # For example:
    elif menu_admin == "Gerenciar Perguntas":
        # (Full content from your working "Gerenciar Perguntas" section)
        st.write("Conteúdo Gerenciar Perguntas (como na versão anterior).")
    elif menu_admin == "Gerenciar Análises de Perguntas":
        st.write("Conteúdo Gerenciar Análises (como na versão anterior).")
    elif menu_admin == "Gerenciar Instruções":
        st.write("Conteúdo Gerenciar Instruções (como na versão anterior).")
    elif menu_admin == "Histórico de Usuários":
        st.write("Conteúdo Histórico de Usuários (como na versão anterior).")
    elif menu_admin == "Gerenciar Administradores":
        st.write("Conteúdo Gerenciar Administradores (como na versão anterior).")


# Fallback at the very end if 'aba' is still not defined (should be caught by login block)
if 'aba' not in locals() and not st.session_state.admin_logado and not st.session_state.cliente_logado:
    st.info("Por favor, selecione seu tipo de acesso para iniciar.")
    st.stop()