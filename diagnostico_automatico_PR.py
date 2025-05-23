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
import uuid # Para IDs de análise, SAC e Pesquisa de Satisfação

# !!! st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT !!!
st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", page_icon="📊")

# --- Diretórios de Assets ---
PORTAL_ASSETS_DIR = "portal_assets"
LOGOS_DIR = "client_logos" # Já definido
PORTAL_LOGO_FILENAME = "portal_logo.png"
PORTAL_LOGO_PLACEHOLDER = "https://via.placeholder.com/200x80.png?text=Logo+do+Portal"

# Criar diretórios se não existirem
if not os.path.exists(PORTAL_ASSETS_DIR):
    try: os.makedirs(PORTAL_ASSETS_DIR)
    except OSError as e: st.error(f"Erro ao criar diretório '{PORTAL_ASSETS_DIR}': {e}")
if not os.path.exists(LOGOS_DIR):
    try: os.makedirs(LOGOS_DIR)
    except OSError as e: st.error(f"Erro ao criar diretório '{LOGOS_DIR}': {e}")


# --- CSS Melhorado ---
st.markdown("""
<style>
body {
    font-family: 'Segoe UI', sans-serif;
    background-color: #f0f2f5; /* Um fundo suave para a página toda */
}
.login-container {
    max-width: 450px;
    margin: 60px auto 0 auto; /* Aumentar margem superior */
    padding: 40px;
    border-radius: 12px; /* Bordas mais arredondadas */
    background-color: #ffffff;
    box-shadow: 0 8px 25px rgba(0,0,0,0.1); /* Sombra mais pronunciada */
    font-family: 'Segoe UI', sans-serif;
}
.login-container img.portal-logo-login { /* Classe específica para logo no login */
    display: block;
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 25px; /* Mais espaço abaixo da logo */
    max-height: 80px; /* Limitar altura da logo */
    width: auto; /* Manter proporção */
}
.login-container h2 {
    text-align: center;
    margin-bottom: 30px;
    font-weight: 600;
    font-size: 28px; /* Tamanho de fonte maior */
    color: #1e3a8a; /* Azul mais escuro e corporativo */
}
.stButton>button {
    border-radius: 8px; /* Bordas mais arredondadas */
    background-color: #2563eb; /* Azul primário */
    color: white;
    font-weight: 600; /* Fonte mais forte */
    padding: 0.7rem 1.5rem; /* Mais padding */
    margin-top: 0.8rem; /* Mais margem */
    border: none;
    transition: background-color 0.3s ease, transform 0.1s ease; /* Adicionar transição de transform */
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.stButton>button:hover {
    background-color: #1d4ed8; /* Azul mais escuro no hover */
    transform: translateY(-2px); /* Efeito de levantar no hover */
}
.stButton>button:disabled {
    background-color: #9ca3af; 
    color: #e5e7eb;
    cursor: not-allowed;
    transform: none; /* Remover efeito de levantar para desabilitado */
    box-shadow: none;
}
.stButton>button.secondary {
    background-color: #e5e7eb;
    color: #374151;
}
.stButton>button.secondary:hover {
    background-color: #d1d5db;
}
.stButton>button.secondary:disabled {
    background-color: #d1d5db;
    color: #9ca3af;
}
.stDownloadButton>button {
    background-color: #10b981; /* Verde para download */
    color: white;
    font-weight: 600;
    border-radius: 8px;
    margin-top: 10px;
    padding: 0.7rem 1.5rem;
    border: none;
    transition: background-color 0.3s ease, transform 0.1s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.stDownloadButton>button:hover {
    background-color: #059669;
    transform: translateY(-2px);
}
.stTextInput>div>input, .stTextArea>div>textarea, .stDateInput>div>input, .stSelectbox>div>div, .stNumberInput>div>input, .stFileUploader>div>button {
    border-radius: 8px;
    padding: 0.7rem; /* Mais padding interno */
    border: 1px solid #d1d5db;
    background-color: #f9fafb;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.stTextInput>div>input:focus, .stTextArea>div>textarea:focus, .stDateInput>div>input:focus, .stSelectbox>div>div:focus-within, .stNumberInput>div>input:focus {
    border-color: #2563eb;
    box-shadow: 0 0 0 0.15rem rgba(37, 99, 235, 0.25); /* Sombra de foco mais pronunciada */
}
.stTextInput>div>input:disabled, .stTextArea>div>textarea:disabled, .stDateInput>div>input:disabled, .stSelectbox>div>div[aria-disabled="true"], .stNumberInput>div>input:disabled, .stFileUploader>div>button:disabled {
    background-color: #e5e7eb;
    color: #9ca3af;
    cursor: not-allowed;
}
.stFileUploader>div>button { /* Estilizar botão do file uploader */
    background-color: #f0f0f0;
    color: #333;
    border: 1px dashed #ccc;
}
.stFileUploader>div>button:hover {
    background-color: #e0e0e0;
    border-color: #bbb;
}
.stTabs [data-baseweb="tab"] {
    font-size: 16px;
    font-weight: 600;
    padding: 12px 22px;
    border-radius: 8px 8px 0 0; /* Bordas mais arredondadas para abas */
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #2563eb;
    color: white;
}
.custom-card {
    border: 1px solid #e0e0e0;
    border-left: 5px solid #2563eb;
    padding: 20px;
    margin-bottom: 15px;
    border-radius: 10px; /* Bordas mais arredondadas */
    background-color: #ffffff;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05); /* Sombra suave */
}
.custom-card h4 {
    margin-top: 0;
    color: #1e3a8a; /* Azul mais escuro */
    font-size: 1.2em; /* Fonte maior para títulos de card */
}
.feedback-saved {
    font-size: 0.85em;
    color: #10b981;
    font-style: italic;
    margin-top: -8px;
    margin-bottom: 8px;
}
.analise-pergunta-cliente {
    font-size: 0.9em;
    color: #333;
    background-color: #eef2ff; /* Fundo suave para análise */
    border-left: 3px solid #6366f1; /* Cor de destaque */
    padding: 12px; /* Mais padding */
    margin-top: 8px;
    margin-bottom:12px;
    border-radius: 6px;
}
[data-testid="stMetric"] {
    background-color: #ffffff;
    border-radius: 10px;
    padding: 20px; /* Mais padding para métricas */
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    border: 1px solid #e0e0e0;
}
[data-testid="stMetricLabel"] {
    font-weight: 500;
    color: #4b5563;
    font-size: 0.95em; /* Ajuste de tamanho */
}
[data-testid="stMetricValue"] {
    font-size: 2em; /* Valor da métrica maior */
    color: #1e3a8a; /* Azul mais escuro */
}
[data-testid="stMetricDelta"] {
    font-size: 0.9em;
}
.stExpander {
    border: 1px solid #e0e0e0 !important;
    border-radius: 10px !important; /* Bordas mais arredondadas */
    box-shadow: 0 4px 10px rgba(0,0,0,0.05) !important;
    margin-bottom: 15px !important;
}
.stExpander header {
    font-weight: 600 !important;
    border-radius: 10px 10px 0 0 !important;
    padding: 12px 18px !important; /* Mais padding para header do expander */
    background-color: #f9fafb; /* Fundo suave para header */
}
.dashboard-item {
    background-color: #ffffff;
    padding: 25px; /* Mais padding */
    border-radius: 10px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    margin-bottom: 20px;
    border: 1px solid #e0e0e0;
    height: 100%;
}
.dashboard-item h5 {
    margin-top: 0;
    margin-bottom: 18px; /* Mais espaço abaixo do título */
    color: #1e3a8a; /* Azul mais escuro */
    font-size: 1.2em;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}
.sac-feedback-button button {
    background-color: #f0f0f0;
    color: #333;
    border: 1px solid #ccc;
    margin-right: 5px;
    padding: 0.3rem 0.8rem;
}
.sac-feedback-button button:hover {
    background-color: #e0e0e0;
}
.sac-feedback-button button.active {
    background-color: #2563eb;
    color: white;
    border-color: #2563eb;
}
.survey-question-container {
    background-color: #f9fafb;
    padding: 18px; /* Mais padding */
    border-radius: 8px;
    margin-bottom: 18px; /* Mais margem */
    border: 1px solid #e5e7eb;
}
.survey-question-container label { /* Streamlit não permite estilizar label diretamente assim */
    font-weight: 600;
    color: #374151;
    display: block;
    margin-bottom: 8px;
}
/* Estilo para o sidebar */
[data-testid="stSidebar"] {
    background-color: #f8f9fa; /* Cor de fundo suave para sidebar */
    padding: 15px;
}
[data-testid="stSidebar"] .stImage img {
    border-radius: 8px; /* Arredondar logos no sidebar */
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# --- Funções de Gráficos (sem alterações diretas, mas podem ser melhoradas visualmente no futuro) ---
# ... (código das funções de gráfico existente) ...
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
    df_diag_copy['Data'] = pd.to_datetime(df_diag_copy['Data'])
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

def create_satisfaction_score_distribution_chart(df_respostas, pergunta_texto, title_prefix="Distribuição de Scores"):
    if df_respostas.empty or 'Resposta_Numerica' not in df_respostas.columns: return None
    df_scores = df_respostas[pd.notna(df_respostas['Resposta_Numerica'])].copy()
    if df_scores.empty: return None
    
    df_scores['Resposta_Numerica'] = pd.to_numeric(df_scores['Resposta_Numerica'], errors='coerce')
    df_scores.dropna(subset=['Resposta_Numerica'], inplace=True)

    score_counts = df_scores['Resposta_Numerica'].value_counts().sort_index().reset_index()
    score_counts.columns = ['Score', 'Contagem']
    
    fig = px.bar(score_counts, x='Score', y='Contagem', 
                 title=f"{title_prefix}: {pergunta_texto}",
                 labels={'Score': 'Score de Satisfação', 'Contagem': 'Número de Respostas'},
                 color='Contagem', color_continuous_scale=px.colors.sequential.Blues)
    fig.update_layout(font=dict(family="Segoe UI, sans-serif"))
    return fig

def create_satisfaction_choice_distribution_chart(df_respostas, pergunta_texto, title_prefix="Distribuição de Respostas"):
    if df_respostas.empty or 'Resposta_Opcao_Selecionada' not in df_respostas.columns: return None
    df_choices = df_respostas[pd.notna(df_respostas['Resposta_Opcao_Selecionada'])].copy()
    if df_choices.empty: return None

    choice_counts = df_choices['Resposta_Opcao_Selecionada'].value_counts().reset_index()
    choice_counts.columns = ['Opção', 'Contagem']
    
    fig = px.pie(choice_counts, values='Contagem', names='Opção', 
                 title=f"{title_prefix}: {pergunta_texto}",
                 color_discrete_sequence=px.colors.sequential.Blues_r)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(font=dict(family="Segoe UI, sans-serif"))
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
sac_perguntas_respostas_csv = "sac_perguntas_respostas.csv"
sac_uso_feedback_csv = "sac_uso_feedback.csv"
satisfacao_perguntas_csv = "satisfacao_perguntas.csv" 
satisfacao_respostas_csv = "satisfacao_respostas.csv" 

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {}, "sac_feedback_registrado": {},
    "force_sidebar_rerun_after_notif_read_v19": False, 
    "target_diag_data_for_expansion": None,
    "respostas_atuais_satisfacao": {}, 
    "pesquisa_satisfacao_enviada": False,
    "admin_username": None, 
    "admin_permissions": "visualizacao" 
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias (exceto gráficos) ---
def sanitize_filename(name): # Mais robusto para nomes de arquivo
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s)
    return s if s else "arquivo_sem_nome"

def pdf_safe_text_output(text): return str(text).encode('latin-1', 'replace').decode('latin-1')

def get_portal_logo_path():
    return os.path.join(PORTAL_ASSETS_DIR, PORTAL_LOGO_FILENAME)

def find_client_logo_path(cnpj_arg):
    if not cnpj_arg: return None
    base = sanitize_filename(str(cnpj_arg)) # Usar sanitize_filename
    for ext in ["png", "jpg", "jpeg"]:
        path = os.path.join(LOGOS_DIR, f"{base}_logo.{ext}")
        if os.path.exists(path): return path
    return None


colunas_base_admin_credenciais = ["Usuario", "Senha", "Permissoes"] 
colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone",
                         "JaVisualizouInstrucoes", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados", "LogoPath"] # Adicionado LogoPath
colunas_base_perguntas = ["Pergunta", "Categoria"]
colunas_base_analises = ["ID_Analise", "TextoPerguntaOriginal", "TipoCondicao", "CondicaoValorMin", "CondicaoValorMax", "CondicaoValorExato", "TextoAnalise"]
colunas_base_notificacoes = ["ID_Notificacao", "CNPJ_Cliente", "Timestamp", "Mensagem", "Lida", "ID_Diagnostico_Relacionado"] 
colunas_base_sac_perguntas = ["ID_SAC_Pergunta", "Pergunta_SAC", "Resposta_SAC", "Categoria_SAC", "DataCriacao"]
colunas_base_sac_uso_feedback = ["ID_Uso_SAC", "Timestamp", "CNPJ_Cliente", "ID_SAC_Pergunta", "Feedback_Util"]
colunas_base_satisfacao_perguntas = ["ID_Pergunta_Satisfacao", "Texto_Pergunta", "Tipo_Pergunta", "Opcoes_Pergunta", "Ordem", "Ativa"]
colunas_base_satisfacao_respostas = ["ID_Resposta_Satisfacao", "ID_Pergunta_Satisfacao", "CNPJ_Cliente", 
                                     "ID_Diagnostico_Relacionado", "Timestamp_Resposta", 
                                     "Resposta_Texto", "Resposta_Numerica", "Resposta_Opcao_Selecionada"]

def is_admin_total():
    return st.session_state.get("admin_permissions") == "total"

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
                dtype_spec = None
                if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, sac_uso_feedback_csv, satisfacao_respostas_csv]:
                    dtype_spec = {'CNPJ': str, 'CNPJ_Cliente': str, 'ID_Diagnostico_Relacionado': str}
                    temp_df_check_cols = pd.read_csv(filepath, encoding='utf-8', nrows=0) 
                    dtype_spec = {k: v for k, v in dtype_spec.items() if k in temp_df_check_cols.columns}
                
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec)

                if filepath == admin_credenciais_csv and "Permissoes" not in df_init.columns:
                    df_init["Permissoes"] = "total" 
                    df_init.to_csv(filepath, index=False, encoding='utf-8')
                    df_init = pd.read_csv(filepath, encoding='utf-8') 
                
                if filepath == usuarios_csv and "LogoPath" not in df_init.columns: # Adicionar LogoPath se não existir
                    df_init["LogoPath"] = None
                    df_init.to_csv(filepath, index=False, encoding='utf-8')
                    df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec)


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
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec)


            made_changes = False
            for col_idx, col_name in enumerate(columns):
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
    except Exception as e: st.error(f"Erro crítico ao inicializar {filepath}: {e}"); raise

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, colunas_base_admin_credenciais, defaults={"Permissoes": "total"}) 
    inicializar_csv(usuarios_csv, colunas_base_usuarios,
                    defaults={"JaVisualizouInstrucoes": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0, "LogoPath": None})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos) 
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False, "ID_Diagnostico_Relacionado": None}) 
    inicializar_csv(sac_perguntas_respostas_csv, colunas_base_sac_perguntas, defaults={"Categoria_SAC": "Geral", "DataCriacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    inicializar_csv(sac_uso_feedback_csv, colunas_base_sac_uso_feedback, defaults={"Feedback_Util": None})
    inicializar_csv(satisfacao_perguntas_csv, colunas_base_satisfacao_perguntas, 
                    defaults={"Tipo_Pergunta": "Texto_Aberto", "Opcoes_Pergunta": None, "Ordem": 0, "Ativa": True})
    inicializar_csv(satisfacao_respostas_csv, colunas_base_satisfacao_respostas,
                    defaults={"ID_Diagnostico_Relacionado": None, "Resposta_Texto": None, "Resposta_Numerica": None, "Resposta_Opcao_Selecionada": None})

except Exception as e_init:
    st.error(f"Falha na inicialização de arquivos CSV: {e_init}")
    st.stop()

def registrar_acao(cnpj, acao, desc):
    try: hist_df = pd.read_csv(historico_csv, encoding='utf-8')
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

@st.cache_data
def carregar_sac_perguntas_respostas():
    try:
        df = pd.read_csv(sac_perguntas_respostas_csv, encoding='utf-8')
        if "Categoria_SAC" not in df.columns: df["Categoria_SAC"] = "Geral"
        if "DataCriacao" not in df.columns: df["DataCriacao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_sac_perguntas)

@st.cache_data
def carregar_sac_uso_feedback():
    try:
        df = pd.read_csv(sac_uso_feedback_csv, encoding='utf-8', dtype={'CNPJ_Cliente': str})
        if 'Feedback_Util' in df.columns:
                df['Feedback_Util'] = df['Feedback_Util'].astype(str).str.lower().map({'true': True, 'false': False, 'nan': pd.NA, '': pd.NA}).astype('boolean') 
        else:
            df['Feedback_Util'] = pd.NA
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_sac_uso_feedback)

@st.cache_data
def carregar_satisfacao_perguntas():
    try:
        df = pd.read_csv(satisfacao_perguntas_csv, encoding='utf-8')
        if "Ordem" not in df.columns: df["Ordem"] = 0
        if "Ativa" not in df.columns: df["Ativa"] = True
        df["Ativa"] = df["Ativa"].astype(bool)
        df["Ordem"] = pd.to_numeric(df["Ordem"], errors='coerce').fillna(0).astype(int)
        return df.sort_values(by="Ordem")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_satisfacao_perguntas)

@st.cache_data
def carregar_satisfacao_respostas():
    try:
        df = pd.read_csv(satisfacao_respostas_csv, encoding='utf-8', 
                         dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Relacionado': str})
        if 'Timestamp_Resposta' in df.columns:
            df['Timestamp_Resposta'] = pd.to_datetime(df['Timestamp_Resposta'], errors='coerce')
        for col_num in ['Resposta_Numerica']: 
            if col_num in df.columns:
                df[col_num] = pd.to_numeric(df[col_num], errors='coerce')
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_satisfacao_respostas)


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

# --- Classe PDF Personalizada ---
class PDF(FPDF):
    def __init__(self, portal_logo_path=None, client_logo_path=None, client_name=""):
        super().__init__()
        self.portal_logo_path = portal_logo_path
        self.client_logo_path = client_logo_path
        self.client_name = client_name
        self.set_auto_page_break(auto=True, margin=15)
        self.add_font('Arial', '', 'arial.ttf', uni=True) # Adicionar fonte Arial padrão
        self.add_font('Arial', 'B', 'arial_bold.ttf', uni=True)
        self.add_font('Arial', 'I', 'arial_italic.ttf', uni=True)
        self.add_font('Arial', 'BI', 'arial_bold_italic.ttf', uni=True)


    def header(self):
        # Logo do Portal (se existir)
        if self.portal_logo_path and os.path.exists(self.portal_logo_path):
            try:
                self.image(self.portal_logo_path, x=10, y=8, h=15)
            except Exception as e:
                print(f"Erro ao adicionar logo do portal ao PDF: {e}")
        
        # Logo do Cliente (se existir)
        if self.client_logo_path and os.path.exists(self.client_logo_path):
            try:
                self.image(self.client_logo_path, x=self.w - 10 - 30, y=8, h=15) # Alinhar à direita
            except Exception as e:
                print(f"Erro ao adicionar logo do cliente ao PDF: {e}")

        self.set_font('Arial', 'B', 18)
        self.set_text_color(30, 58, 138) # Azul escuro corporativo
        title_w = self.get_string_width("Relatório de Diagnóstico") + 6
        self.set_x((self.w - title_w) / 2) # Centralizar título
        self.cell(title_w, 10, "Relatório de Diagnóstico", 0, 0, 'C')
        self.ln(10) # Espaço após título principal
        
        if self.client_name:
            self.set_font('Arial', 'I', 12)
            self.set_text_color(75, 85, 99) # Cinza para subtítulo
            client_title_w = self.get_string_width(self.client_name) + 6
            self.set_x((self.w - client_title_w) / 2)
            self.cell(client_title_w, 10, pdf_safe_text_output(self.client_name), 0, 1, 'C')
        
        self.ln(10) # Espaço maior após o cabeçalho
        # Linha horizontal abaixo do cabeçalho
        self.set_line_width(0.3)
        self.set_draw_color(200, 200, 200) # Cinza claro para linha
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(5)


    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
        # Adicionar data de geração no rodapé
        self.set_x(10)
        self.cell(0,10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 0,0, 'L')


    def section_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(230, 230, 250) # Lavanda suave para fundo do título da seção
        self.set_text_color(30, 58, 138) # Azul escuro
        self.cell(0, 10, pdf_safe_text_output(f" {title} "), 0, 1, 'L', fill=True) # Adicionar espaço antes do título
        self.ln(5)

    def chapter_body(self, text_content):
        self.set_font('Arial', '', 10)
        self.set_text_color(50, 50, 50) # Cinza escuro para corpo do texto
        self.multi_cell(0, 7, pdf_safe_text_output(text_content))
        self.ln()

    def key_value_pair(self, key, value, indent=False):
        self.set_font('Arial', 'B', 10)
        self.set_text_color(55, 65, 81) # Cinza mais escuro para chaves
        key_text = f"   {key}: " if indent else f"{key}: "
        self.cell(self.get_string_width(key_text) + 2, 7, pdf_safe_text_output(key_text))
        self.set_font('Arial', '', 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 7, pdf_safe_text_output(str(value))) # Multi_cell para valor, caso seja longo
        self.ln(1) # Pequeno espaço após par chave-valor

def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df, respostas_coletadas, medias_cat, analises_df):
    try:
        with st.spinner("Gerando PDF do diagnóstico... Aguarde."):
            portal_logo_p = get_portal_logo_path()
            client_logo_p = find_client_logo_path(user_data.get("CNPJ"))
            
            pdf = PDF(portal_logo_path=portal_logo_p, client_logo_path=client_logo_p, client_name=user_data.get("Empresa", "N/D"))
            pdf.alias_nb_pages()
            pdf.add_page()

            # Informações Gerais
            pdf.section_title("Informações Gerais do Diagnóstico")
            pdf.key_value_pair("Data da Realização", diag_data.get('Data','N/D'))
            pdf.key_value_pair("Empresa", user_data.get("Empresa", "N/D"))
            pdf.key_value_pair("CNPJ", user_data.get("CNPJ", "N/D"))
            if user_data.get("NomeContato"): pdf.key_value_pair("Contato Principal", user_data.get("NomeContato"))
            if user_data.get("Telefone"): pdf.key_value_pair("Telefone", user_data.get("Telefone"))
            pdf.ln(5)

            # Resumo dos Scores
            pdf.section_title("Resumo dos Indicadores Chave")
            pdf.key_value_pair("Média Geral do Diagnóstico", f"{pd.to_numeric(diag_data.get('Média Geral'), errors='coerce'):.2f}" if pd.notna(diag_data.get('Média Geral')) else "N/A")
            pdf.key_value_pair("Score Médio da Matriz GUT", f"{pd.to_numeric(diag_data.get('GUT Média'), errors='coerce'):.2f}" if pd.notna(diag_data.get('GUT Média')) else "N/A")
            pdf.ln(2)
            if medias_cat:
                pdf.set_font("Arial", 'B', 10); pdf.multi_cell(0, 7, pdf_safe_text_output("Médias por Categoria:")); pdf.set_font("Arial", size=10)
                for cat, media_val in medias_cat.items():
                     pdf.key_value_pair(f"  - {cat}", f"{media_val:.2f}", indent=True)
                pdf.ln(5)

            # Observações e Análises do Cliente e Consultor
            for titulo_pdf, campo_dados in [("Diagnóstico e Insights (Cliente)", "Diagnóstico"), 
                                     ("Análise Adicional (Cliente)", "Análise do Cliente"), 
                                     ("Comentários do Consultor", "Comentarios_Admin")]:
                valor_obs = diag_data.get(campo_dados, "")
                if valor_obs and not pd.isna(valor_obs) and str(valor_obs).strip():
                    pdf.section_title(titulo_pdf)
                    pdf.chapter_body(str(valor_obs))
            
            # Respostas Detalhadas
            pdf.add_page()
            pdf.section_title("Respostas Detalhadas e Análises por Pergunta")
            categorias = perguntas_df["Categoria"].unique() if not perguntas_df.empty and "Categoria" in perguntas_df.columns else []
            
            for categoria_pdf in categorias:
                pdf.set_font("Arial", 'B', 11); 
                pdf.set_fill_color(240, 240, 240) # Fundo levemente diferente para título de categoria
                pdf.cell(0, 8, pdf_safe_text_output(f" Categoria: {categoria_pdf} "), 0, 1, 'L', fill=True)
                pdf.ln(3)
                
                perg_cat_pdf = perguntas_df[perguntas_df["Categoria"] == categoria_pdf]
                for _, p_row_pdf in perg_cat_pdf.iterrows():
                    p_texto_pdf = p_row_pdf["Pergunta"]
                    resp_pdf = respostas_coletadas.get(p_texto_pdf, diag_data.get(p_texto_pdf, "N/R"))
                    
                    pdf.set_font("Arial", 'B', 9); 
                    pdf.set_text_color(60,60,60)
                    pdf.multi_cell(0, 6, pdf_safe_text_output(f"  • {p_texto_pdf.split('[')[0].strip()}:")) # Usar bullet point

                    pdf.set_font("Arial", '', 9); 
                    pdf.set_text_color(80,80,80)
                    pdf.set_fill_color(248,249,250) # Fundo muito claro para a resposta
                    
                    resp_display_pdf = str(resp_pdf)
                    analise_texto_pdf = None

                    if "[Matriz GUT]" in p_texto_pdf:
                        g,u,t,score_gut_pdf=0,0,0,0
                        if isinstance(resp_pdf, dict): g,u,t=int(resp_pdf.get("G",0)),int(resp_pdf.get("U",0)),int(resp_pdf.get("T",0))
                        elif isinstance(resp_pdf, str):
                            try: data_gut_pdf=json.loads(resp_pdf.replace("'",'"'));g,u,t=int(data_gut_pdf.get("G",0)),int(data_gut_pdf.get("U",0)),int(data_gut_pdf.get("T",0))
                            except: pass
                        score_gut_pdf = g*u*t
                        resp_display_pdf = f"G={g}, U={u}, T={t} (Score Total: {score_gut_pdf})"
                        analise_texto_pdf = obter_analise_para_resposta(p_texto_pdf, score_gut_pdf, analises_df)
                    else:
                        analise_texto_pdf = obter_analise_para_resposta(p_texto_pdf, resp_pdf, analises_df)
                    
                    pdf.multi_cell(0, 6, pdf_safe_text_output(f"    Resposta: {resp_display_pdf}"),0, 'L', fill=True)
                    
                    if analise_texto_pdf:
                        pdf.set_font("Arial", 'I', 8.5); pdf.set_text_color(100,100,100)
                        pdf.set_fill_color(252,252,252) # Fundo ainda mais claro para análise
                        pdf.multi_cell(0, 5, pdf_safe_text_output(f"      Análise Consultor: {analise_texto_pdf}"),0, 'L', fill=True)
                    pdf.ln(3) # Espaço entre perguntas
                pdf.ln(5) # Espaço entre categorias

            # Plano de Ação GUT
            pdf.add_page()
            pdf.section_title("Plano de Ação Sugerido (Matriz GUT)")
            gut_cards_pdf = []
            if not perguntas_df.empty:
                for _, p_row_pdf_gut in perguntas_df.iterrows():
                    p_texto_pdf_gut = p_row_pdf_gut["Pergunta"]
                    if "[Matriz GUT]" in p_texto_pdf_gut:
                        resp_gut = respostas_coletadas.get(p_texto_pdf_gut, diag_data.get(p_texto_pdf_gut))
                        g_pdf,u_pdf,t_pdf,score_pdf=0,0,0,0
                        if isinstance(resp_gut, dict): g_pdf,u_pdf,t_pdf=int(resp_gut.get("G",0)),int(resp_gut.get("U",0)),int(resp_gut.get("T",0))
                        elif isinstance(resp_gut, str):
                            try:data_gut_val_pdf=json.loads(resp_gut.replace("'",'"'));g_pdf,u_pdf,t_pdf=int(data_gut_val_pdf.get("G",0)),int(data_gut_val_pdf.get("U",0)),int(data_gut_val_pdf.get("T",0))
                            except: pass
                        score_pdf = g_pdf*u_pdf*t_pdf
                        prazo_pdf = "N/A"
                        if score_pdf >= 75: prazo_pdf = "Curto Prazo (até 15 dias)"
                        elif score_pdf >= 40: prazo_pdf = "Médio Prazo (até 30 dias)"
                        elif score_pdf >= 20: prazo_pdf = "Longo Prazo (até 45 dias)"
                        elif score_pdf > 0: prazo_pdf = "Considerar (até 60 dias)"
                        else: continue
                        if prazo_pdf != "N/A": gut_cards_pdf.append({"Tarefa": p_texto_pdf_gut.replace(" [Matriz GUT]", ""),"Prazo": prazo_pdf, "Score": score_pdf, "G":g_pdf, "U":u_pdf, "T":t_pdf})
            
            if gut_cards_pdf:
                sorted_cards_pdf = sorted(gut_cards_pdf, key=lambda x: x["Score"], reverse=True)
                # Cabeçalho da tabela
                pdf.set_font('Arial', 'B', 10)
                pdf.set_fill_color(220, 220, 220) # Cinza claro para cabeçalho da tabela
                pdf.cell(90, 8, 'Tarefa Prioritária', 1, 0, 'C', True)
                pdf.cell(25, 8, 'G', 1, 0, 'C', True)
                pdf.cell(25, 8, 'U', 1, 0, 'C', True)
                pdf.cell(25, 8, 'T', 1, 0, 'C', True)
                pdf.cell(25, 8, 'Score', 1, 1, 'C', True)
                
                pdf.set_font('Arial', '', 9)
                for card_pdf in sorted_cards_pdf:
                    pdf.set_fill_color(255,255,255) # Branco para linhas
                    # Lidar com quebra de linha na tarefa
                    x_before = pdf.get_x()
                    y_before = pdf.get_y()
                    pdf.multi_cell(90, 7, pdf_safe_text_output(card_pdf['Tarefa']), 1, 'L', True)
                    y_after_multi = pdf.get_y()
                    h_multi = y_after_multi - y_before
                    
                    pdf.set_xy(x_before + 90, y_before) # Voltar para a mesma linha, após a multi_cell
                    pdf.cell(25, h_multi, str(card_pdf['G']), 1, 0, 'C', True)
                    pdf.cell(25, h_multi, str(card_pdf['U']), 1, 0, 'C', True)
                    pdf.cell(25, h_multi, str(card_pdf['T']), 1, 0, 'C', True)
                    pdf.cell(25, h_multi, str(card_pdf['Score']), 1, 1, 'C', True)
            else: 
                pdf.chapter_body("Nenhuma ação prioritária (GUT > 0) identificada com base nas respostas fornecidas.")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                pdf_path = tmpfile.name; pdf.output(pdf_path)
        return pdf_path
    except Exception as e: st.error(f"Erro crítico ao gerar PDF: {e}"); return None

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): st.session_state.trigger_rerun_global = False; st.rerun()

# Exibir logo do portal na página de login
portal_logo_path_login = get_portal_logo_path()
if not os.path.exists(portal_logo_path_login):
    portal_logo_path_login = PORTAL_LOGO_PLACEHOLDER # Fallback se não existir

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v21")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.image(portal_logo_path_login, width=200, use_column_width='auto', output_format='PNG', 
             caption="" if portal_logo_path_login == PORTAL_LOGO_PLACEHOLDER else "Logo do Portal", 
             channels="RGB" if portal_logo_path_login != PORTAL_LOGO_PLACEHOLDER else "RGBA")
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v21"):
        u = st.text_input("Usuário", key="admin_u_v21"); p = st.text_input("Senha", type="password", key="admin_p_v21")
        if st.form_submit_button("Entrar", use_container_width=True, icon="🔑"):
            try:
                df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                admin_match = df_creds[(df_creds["Usuario"] == u) & (df_creds["Senha"] == p)]
                if not admin_match.empty:
                    st.session_state.admin_logado = True
                    st.session_state.admin_username = u
                    if "Permissoes" in admin_match.columns and pd.notna(admin_match.iloc[0]["Permissoes"]):
                        st.session_state.admin_permissions = admin_match.iloc[0]["Permissoes"]
                    else:
                        st.session_state.admin_permissions = "total" 
                        idx_to_update = df_creds[(df_creds["Usuario"] == u)].index
                        if not idx_to_update.empty:
                            if "Permissoes" not in df_creds.columns: 
                                df_creds["Permissoes"] = "total"
                            else: 
                                df_creds.loc[idx_to_update, "Permissoes"] = "total"
                            df_creds.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                    
                    st.toast(f"Login de admin ({st.session_state.admin_permissions}) bem-sucedido!", icon="🎉")
                    st.rerun()
                else: st.error("Usuário/senha admin inválidos.")
            except Exception as e: st.error(f"Erro login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.image(portal_logo_path_login, width=200, use_column_width='auto', output_format='PNG', 
             caption="" if portal_logo_path_login == PORTAL_LOGO_PLACEHOLDER else "Logo do Portal", 
             channels="RGB" if portal_logo_path_login != PORTAL_LOGO_PLACEHOLDER else "RGBA")
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_v21"):
        c = st.text_input("CNPJ", key="cli_c_v21", value=st.session_state.get("last_cnpj_input",""))
        s = st.text_input("Senha", type="password", key="cli_s_v21")
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
                st.session_state.sac_feedback_registrado = {}
                st.session_state.diagnostico_enviado_sucesso = False
                st.session_state.target_diag_data_for_expansion = None 
                st.session_state.respostas_atuais_satisfacao = {} 
                st.session_state.pesquisa_satisfacao_enviada = False 

                st.toast("Login de cliente bem-sucedido!", icon="👋")
                st.rerun()
            except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    if not st.session_state.user.get("JaVisualizouInstrucoes", False):
        st.session_state.cliente_page = "Instruções"

    # Mostrar logo do portal no topo do sidebar do cliente
    portal_logo_sidebar_cli = get_portal_logo_path()
    if os.path.exists(portal_logo_sidebar_cli):
        st.sidebar.image(portal_logo_sidebar_cli, use_column_width='auto')
    else:
        st.sidebar.markdown(f"### {st.session_state.user.get('Empresa', 'Cliente')}")


    # st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!") # Movido para baixo da logo
    with st.sidebar.expander("👤 Meu Perfil", expanded=True):
        client_logo_display_path = st.session_state.user.get("LogoPath") # Usar o caminho do CSV
        if client_logo_display_path and os.path.exists(client_logo_display_path): 
            st.image(client_logo_display_path, width=100)
        elif find_client_logo_path(st.session_state.cnpj): # Fallback para função antiga se LogoPath não estiver no CSV ou inválido
             st.image(find_client_logo_path(st.session_state.cnpj), width=100)

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
    if os.path.exists(notificacoes_csv):
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
        "Pesquisa de Satisfação": "📝 Pesquisa de Satisfação", 
        "Notificações": notificacoes_label,
        "SAC": "❓ SAC - Perguntas Frequentes"
    }
    
    if not st.session_state.user.get("JaVisualizouInstrucoes", False):
        menu_options_cli_map = {"Instruções": "📖 Instruções"}
        st.session_state.cliente_page = "Instruções"
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

    selected_page_cli_raw = st.sidebar.radio("Menu Cliente", menu_options_cli_display, index=current_idx_cli, key="cli_menu_v21_conditional")
    
    selected_page_cli_clean = ""
    for key_page, val_page_display in menu_options_cli_map.items(): 
        if val_page_display == selected_page_cli_raw: 
            if key_page == "Notificações": 
                selected_page_cli_clean = "Notificações"
            elif key_page == "SAC":
                selected_page_cli_clean = "SAC"
            elif key_page == "Pesquisa de Satisfação": 
                selected_page_cli_clean = "Pesquisa de Satisfação"
            else:
                selected_page_cli_clean = key_page
            break
    
    if selected_page_cli_clean and selected_page_cli_clean != st.session_state.cliente_page :
        st.session_state.cliente_page = selected_page_cli_clean
        st.session_state.force_sidebar_rerun_after_notif_read_v19 = False 
        st.session_state.target_diag_data_for_expansion = None 
        st.rerun()

    if st.sidebar.button("Sair do Portal Cliente", icon="⬅️", key="logout_cliente_v21", use_container_width=True):
        keys_to_clear = [k for k in st.session_state.keys() if k not in ['admin_logado', 'last_cnpj_input']]
        for key_item in keys_to_clear: del st.session_state[key_item] 
        for key_d, value_d in default_session_state.items():
            if key_d not in ['admin_logado', 'last_cnpj_input']: st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False
        st.toast("Logout realizado.", icon="👋")
        st.rerun()

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

        if st.button("Entendi, prosseguir", key="btn_instrucoes_v21", icon="👍"):
            update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", "True")
            if st.session_state.user: st.session_state.user["JaVisualizouInstrucoes"] = True
            
            pode_fazer_novo_inst = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo_inst else "Painel Principal"
            st.rerun()

    elif st.session_state.cliente_page == "Pesquisa de Satisfação": 
        st.subheader(menu_options_cli_map_full["Pesquisa de Satisfação"])
        
        if st.session_state.get("pesquisa_satisfacao_enviada", False):
            st.success("✅ Obrigado por seu feedback! Sua pesquisa de satisfação foi enviada.")
            if st.button("Voltar ao Painel Principal", key="voltar_painel_apos_satisfacao_v21"):
                st.session_state.pesquisa_satisfacao_enviada = False
                st.session_state.cliente_page = "Painel Principal"
                st.rerun()
            st.stop()

        df_perguntas_satisfacao = carregar_satisfacao_perguntas()
        perguntas_ativas_satisfacao = df_perguntas_satisfacao[df_perguntas_satisfacao["Ativa"] == True]

        if perguntas_ativas_satisfacao.empty:
            st.info("Nenhuma pesquisa de satisfação disponível no momento.")
        else:
            st.info("Sua opinião é muito importante para nós! Por favor, responda à pesquisa abaixo.")
            
            num_perguntas_satisfacao = len(perguntas_ativas_satisfacao)
            respostas_satisfacao = st.session_state.respostas_atuais_satisfacao
            
            with st.form("form_pesquisa_satisfacao_v21"):
                for idx_sat, row_sat in perguntas_ativas_satisfacao.iterrows():
                    id_pergunta_sat = row_sat["ID_Pergunta_Satisfacao"]
                    texto_pergunta_sat = row_sat["Texto_Pergunta"]
                    tipo_pergunta_sat = row_sat["Tipo_Pergunta"]
                    opcoes_sat_json = row_sat.get("Opcoes_Pergunta")
                    
                    st.markdown(f"<div class='survey-question-container'>", unsafe_allow_html=True)
                    st.markdown(f"**{texto_pergunta_sat}**")

                    widget_key_sat = f"satisfacao_v21_{id_pergunta_sat}"

                    if tipo_pergunta_sat == "Pontuacao_0_5":
                        respostas_satisfacao[id_pergunta_sat] = st.slider("", 0, 5, value=int(respostas_satisfacao.get(id_pergunta_sat, 0)), key=widget_key_sat, help="0 = Muito Ruim, 5 = Excelente")
                    elif tipo_pergunta_sat == "Pontuacao_0_10":
                        respostas_satisfacao[id_pergunta_sat] = st.slider("", 0, 10, value=int(respostas_satisfacao.get(id_pergunta_sat, 0)), key=widget_key_sat, help="0 = Muito Ruim, 10 = Excelente")
                    elif tipo_pergunta_sat == "Texto_Aberto":
                        respostas_satisfacao[id_pergunta_sat] = st.text_area("", value=str(respostas_satisfacao.get(id_pergunta_sat, "")), key=widget_key_sat, height=100)
                    elif tipo_pergunta_sat == "Escolha_Unica":
                        opcoes_list_sat = []
                        if pd.notna(opcoes_sat_json):
                            try: opcoes_list_sat = json.loads(opcoes_sat_json)
                            except json.JSONDecodeError: st.warning(f"Opções mal formatadas para pergunta ID {id_pergunta_sat}")
                        
                        if opcoes_list_sat:
                            current_val_sat = respostas_satisfacao.get(id_pergunta_sat)
                            default_idx_sat = 0
                            if current_val_sat in opcoes_list_sat:
                                default_idx_sat = opcoes_list_sat.index(current_val_sat)
                            elif opcoes_list_sat: 
                                respostas_satisfacao[id_pergunta_sat] = opcoes_list_sat[0] 

                            respostas_satisfacao[id_pergunta_sat] = st.radio("", options=opcoes_list_sat, index=default_idx_sat, key=widget_key_sat, horizontal=True)
                        else:
                            st.caption("Nenhuma opção configurada para esta pergunta de escolha única.")
                    else:
                        st.warning(f"Tipo de pergunta não suportado: {tipo_pergunta_sat}")
                    st.markdown(f"</div>", unsafe_allow_html=True)
                
                st.session_state.respostas_atuais_satisfacao = respostas_satisfacao 

                if st.form_submit_button("Enviar Pesquisa de Satisfação", icon="✔️", use_container_width=True):
                    df_respostas_salvar = carregar_satisfacao_respostas()
                    novas_entradas_respostas = []
                    timestamp_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    for id_p_sat, resp_val_sat in respostas_satisfacao.items():
                        pergunta_info_sat = df_perguntas_satisfacao[df_perguntas_satisfacao["ID_Pergunta_Satisfacao"] == id_p_sat].iloc[0]
                        tipo_p_sat_submit = pergunta_info_sat["Tipo_Pergunta"]
                        
                        entrada_base_sat = {
                            "ID_Resposta_Satisfacao": str(uuid.uuid4()),
                            "ID_Pergunta_Satisfacao": id_p_sat,
                            "CNPJ_Cliente": st.session_state.cnpj,
                            "ID_Diagnostico_Relacionado": None, 
                            "Timestamp_Resposta": timestamp_atual,
                            "Resposta_Texto": None, "Resposta_Numerica": None, "Resposta_Opcao_Selecionada": None
                        }
                        if tipo_p_sat_submit in ["Pontuacao_0_5", "Pontuacao_0_10"]:
                            entrada_base_sat["Resposta_Numerica"] = resp_val_sat
                        elif tipo_p_sat_submit == "Texto_Aberto":
                            entrada_base_sat["Resposta_Texto"] = str(resp_val_sat).strip()
                        elif tipo_p_sat_submit == "Escolha_Unica":
                            entrada_base_sat["Resposta_Opcao_Selecionada"] = str(resp_val_sat)
                        
                        novas_entradas_respostas.append(entrada_base_sat)
                    
                    if novas_entradas_respostas:
                        df_novas_respostas_sat = pd.DataFrame(novas_entradas_respostas)
                        df_respostas_salvar = pd.concat([df_respostas_salvar, df_novas_respostas_sat], ignore_index=True)
                        df_respostas_salvar.to_csv(satisfacao_respostas_csv, index=False, encoding='utf-8')
                        st.session_state.pesquisa_satisfacao_enviada = True
                        st.session_state.respostas_atuais_satisfacao = {} 
                        st.cache_data.clear() 
                        registrar_acao(st.session_state.cnpj, "Envio Pesquisa Satisfacao", "Cliente enviou pesquisa de satisfação.")
                        st.rerun()
                    else:
                        st.warning("Nenhuma resposta para salvar.")


    elif st.session_state.cliente_page == "SAC":
        st.subheader(menu_options_cli_map_full["SAC"])
        df_sac_qa = carregar_sac_perguntas_respostas()

        if df_sac_qa.empty:
            st.info("Nenhuma pergunta frequente cadastrada no momento.")
        else:
            df_sac_qa_sorted = df_sac_qa.sort_values(by=["Categoria_SAC", "Pergunta_SAC"])
            categorias_sac = df_sac_qa_sorted["Categoria_SAC"].unique()

            search_term_sac = st.text_input("🔎 Procurar nas Perguntas Frequentes:", key="search_sac_cliente_v21")
            if search_term_sac:
                df_sac_qa_sorted = df_sac_qa_sorted[
                    df_sac_qa_sorted["Pergunta_SAC"].str.contains(search_term_sac, case=False, na=False) |
                    df_sac_qa_sorted["Resposta_SAC"].str.contains(search_term_sac, case=False, na=False) |
                    df_sac_qa_sorted["Categoria_SAC"].str.contains(search_term_sac, case=False, na=False)
                ]
                categorias_sac = df_sac_qa_sorted["Categoria_SAC"].unique()


            if df_sac_qa_sorted.empty and search_term_sac:
                    st.info(f"Nenhuma pergunta encontrada para '{search_term_sac}'.")


            for categoria in categorias_sac:
                st.markdown(f"#### {categoria}")
                perguntas_na_categoria = df_sac_qa_sorted[df_sac_qa_sorted["Categoria_SAC"] == categoria]
                for idx_sac, row_sac in perguntas_na_categoria.iterrows():
                    with st.expander(f"{row_sac['Pergunta_SAC']}"):
                        st.markdown(row_sac['Resposta_SAC'], unsafe_allow_html=True) 
                        
                        feedback_key_base = f"sac_feedback_v21_{row_sac['ID_SAC_Pergunta']}"
                        feedback_dado = st.session_state.sac_feedback_registrado.get(row_sac['ID_SAC_Pergunta'])

                        cols_feedback = st.columns([1,1,8])
                        with cols_feedback[0]:
                            btn_class_util = "active" if feedback_dado == "util" else ""
                            if st.button("👍 Útil", key=f"{feedback_key_base}_util", help="Esta resposta foi útil", use_container_width=True,
                                        type="secondary" if feedback_dado != "util" else "primary"):
                                try:
                                    df_feedback_file = carregar_sac_uso_feedback() 
                                    novo_feedback = pd.DataFrame([{
                                        "ID_Uso_SAC": str(uuid.uuid4()), "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "CNPJ_Cliente": st.session_state.cnpj, "ID_SAC_Pergunta": row_sac['ID_SAC_Pergunta'],
                                        "Feedback_Util": True
                                    }])
                                    df_feedback_file = pd.concat([df_feedback_file, novo_feedback], ignore_index=True)
                                    df_feedback_file.to_csv(sac_uso_feedback_csv, index=False, encoding='utf-8')
                                    st.session_state.sac_feedback_registrado[row_sac['ID_SAC_Pergunta']] = "util"
                                    st.cache_data.clear() 
                                    st.toast("Obrigado pelo seu feedback!", icon="😊")
                                    st.rerun() 
                                except Exception as e_fb:
                                    st.error(f"Erro ao registrar feedback: {e_fb}")
                        with cols_feedback[1]:
                            btn_class_nao_util = "active" if feedback_dado == "nao_util" else ""
                            if st.button("👎 Não útil", key=f"{feedback_key_base}_nao_util", help="Esta resposta não foi útil", use_container_width=True,
                                        type="secondary" if feedback_dado != "nao_util" else "primary"):
                                try:
                                    df_feedback_file = carregar_sac_uso_feedback() 
                                    novo_feedback = pd.DataFrame([{
                                        "ID_Uso_SAC": str(uuid.uuid4()), "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "CNPJ_Cliente": st.session_state.cnpj, "ID_SAC_Pergunta": row_sac['ID_SAC_Pergunta'],
                                        "Feedback_Util": False
                                    }])
                                    df_feedback_file = pd.concat([df_feedback_file, novo_feedback], ignore_index=True)
                                    df_feedback_file.to_csv(sac_uso_feedback_csv, index=False, encoding='utf-8')
                                    st.session_state.sac_feedback_registrado[row_sac['ID_SAC_Pergunta']] = "nao_util"
                                    st.cache_data.clear() 
                                    st.toast("Obrigado pelo seu feedback! Vamos melhorar.", icon="🛠️")
                                    st.rerun() 
                                except Exception as e_fb:
                                    st.error(f"Erro ao registrar feedback: {e_fb}")
                        
                        if feedback_dado:
                            with cols_feedback[2]:
                                st.caption(f"Seu feedback ('{feedback_dado.replace('_', ' ').capitalize()}') foi registrado.")
                st.markdown("---")

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
                        if st.button("Ver Detalhes no Painel", key=f"ver_det_notif_v21_{row_notif['ID_Notificacao']}_{idx_notif}", help="Ir para o diagnóstico mencionado"):
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
            st.exception(e_notif_display)


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
                                        key="dl_novo_diag_painel_v21", icon="📄")
                st.session_state.pdf_gerado_path = None
                st.session_state.pdf_gerado_filename = None
            st.session_state.diagnostico_enviado_sucesso = False

        with st.expander("ℹ️ Informações Importantes", expanded=False):
            st.markdown("- Visualize seus diagnósticos anteriores e sua evolução.")
            st.markdown("- Acompanhe seu plano de ação no Kanban.")
            st.markdown("- Para um novo diagnóstico (se liberado), selecione 'Novo Diagnóstico' no menu ao lado.")
            st.markdown("- Responda à nossa 'Pesquisa de Satisfação' para nos ajudar a melhorar!")


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


        if not df_cliente_diags_raw.empty:
            df_cliente_diags = df_cliente_diags_raw.sort_values(by="Data", ascending=False)
            latest_diag_data_row = df_cliente_diags.iloc[0]
            latest_diag_data = latest_diag_data_row.to_dict()


            st.markdown("#### 📊 Visão Geral do Último Diagnóstico")
            col_graph1, col_graph2 = st.columns(2)

            with col_graph1:
                st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
                st.markdown("##### Scores por Categoria")
                medias_cat_latest = {
                    k.replace("Media_Cat_", "").replace("_", " "): pd.to_numeric(v, errors='coerce')
                    for k, v in latest_diag_data.items()
                    if k.startswith("Media_Cat_") and pd.notna(pd.to_numeric(v, errors='coerce'))
                }
                if medias_cat_latest:
                    fig_radar = create_radar_chart(medias_cat_latest, title="")
                    if fig_radar:
                        st.plotly_chart(fig_radar, use_container_width=True)
                    else:
                        st.caption("Não foi possível gerar o gráfico de radar.")
                else:
                    st.caption("Sem dados de média por categoria para o último diagnóstico.")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_graph2:
                st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
                st.markdown("##### Top Prioridades (Matriz GUT)")
                gut_data_list_client = []
                for pergunta_key, resp_val_str in latest_diag_data.items():
                    if isinstance(pergunta_key, str) and "[Matriz GUT]" in pergunta_key:
                        try:
                            if pd.notna(resp_val_str) and isinstance(resp_val_str, str):
                                gut_data = json.loads(resp_val_str.replace("'", "\""))
                                g, u, t_val = int(gut_data.get("G", 0)), int(gut_data.get("U", 0)), int(gut_data.get("T", 0))
                                score = g * u * t_val
                                if score > 0:
                                    gut_data_list_client.append({
                                        "Tarefa": pergunta_key.replace(" [Matriz GUT]", ""),
                                        "Score": score
                                    })
                        except (json.JSONDecodeError, ValueError, TypeError):
                            pass
                
                if gut_data_list_client:
                    fig_gut_bar = create_gut_barchart(gut_data_list_client, title="")
                    if fig_gut_bar:
                        st.plotly_chart(fig_gut_bar, use_container_width=True)
                    else:
                        st.caption("Não foi possível gerar gráfico de prioridades GUT.")
                else:
                    st.caption("Nenhuma prioridade GUT identificada no último diagnóstico.")
                st.markdown('</div>', unsafe_allow_html=True)
            st.divider()

        st.markdown("#### 📁 Diagnósticos Anteriores")
        try:
            if df_cliente_diags_raw.empty: st.info("Nenhum diagnóstico anterior.")
            else:
                try:
                    perguntas_df_para_painel = pd.read_csv(perguntas_csv, encoding='utf-8')
                    if "Categoria" not in perguntas_df_para_painel.columns: perguntas_df_para_painel["Categoria"] = "Geral"
                except FileNotFoundError:
                    st.error(f"Arquivo de perguntas '{perguntas_csv}' não encontrado para detalhar diagnósticos.")
                    perguntas_df_para_painel = pd.DataFrame()

                analises_df_para_painel = carregar_analises_perguntas()

                for idx_row_diag, row_diag_data in df_cliente_diags.iterrows(): 
                    expand_this_diag = (str(row_diag_data['Data']) == str(target_diag_to_expand))

                    with st.expander(f"📅 {row_diag_data['Data']} - {row_diag_data['Empresa']}", expanded=expand_this_diag):
                        st.markdown('<div class="custom-card" style="padding-top: 10px; padding-bottom: 10px;">', unsafe_allow_html=True) 
                        cols_metricas = st.columns(2)
                        cols_metricas[0].metric("Média Geral", f"{pd.to_numeric(row_diag_data.get('Média Geral'), errors='coerce'):.2f}" if pd.notna(row_diag_data.get('Média Geral')) else "N/A")
                        cols_metricas[1].metric("GUT Média (G*U*T)", f"{pd.to_numeric(row_diag_data.get('GUT Média'), errors='coerce'):.2f}" if pd.notna(row_diag_data.get('GUT Média')) else "N/A")
                        st.write(f"**Resumo (Cliente):** {row_diag_data.get('Diagnóstico', 'N/P')}")

                        st.markdown("**Respostas e Análises Detalhadas:**")
                        if not perguntas_df_para_painel.empty:
                            for cat_loop in sorted(perguntas_df_para_painel["Categoria"].unique()):
                                st.markdown(f"##### Categoria: {cat_loop}")
                                perg_cat_loop = perguntas_df_para_painel[perguntas_df_para_painel["Categoria"] == cat_loop]
                                for _, p_row_loop in perg_cat_loop.iterrows():
                                    p_texto_loop = p_row_loop["Pergunta"]
                                    resp_loop = row_diag_data.get(p_texto_loop, "N/R (Não Respondido ou Pergunta Nova)")
                                    st.markdown(f"**{p_texto_loop.split('[')[0].strip()}:**")
                                    st.markdown(f"> {resp_loop}")
                                    valor_para_analise = resp_loop
                                    if "[Matriz GUT]" in p_texto_loop:
                                        g_val,u_val,t_val,score_gut_loop=0,0,0,0
                                        if isinstance(resp_loop, dict):
                                            g_val,u_val,t_val=int(resp_loop.get("G",0)),int(resp_loop.get("U",0)),int(resp_loop.get("T",0))
                                        elif isinstance(resp_loop, str):
                                            try:
                                                data_gut_loop=json.loads(resp_loop.replace("'",'"'))
                                                g_val,u_val,t_val=int(data_gut_loop.get("G",0)),int(data_gut_loop.get("U",0)),int(data_gut_loop.get("T",0))
                                            except (json.JSONDecodeError, TypeError): pass
                                        score_gut_loop = g_val*u_val*t_val
                                        valor_para_analise = score_gut_loop
                                        st.caption(f"G={g_val}, U={u_val}, T={t_val} (Score GUT: {score_gut_loop})")
                                    analise_texto_painel = obter_analise_para_resposta(p_texto_loop, valor_para_analise, analises_df_para_painel)
                                    if analise_texto_painel:
                                        st.markdown(f"<div class='analise-pergunta-cliente'><b>Análise Consultor:</b> {analise_texto_painel}</div>", unsafe_allow_html=True)
                                st.markdown("---")
                        else: st.caption("Estrutura de perguntas não carregada para detalhar respostas.")

                        analise_cli_val_cv_painel = row_diag_data.get("Análise do Cliente", "")
                        analise_cli_cv_input = st.text_area("🧠 Minha Análise sobre este Diagnóstico:", value=analise_cli_val_cv_painel, key=f"analise_cv_painel_v21_{idx_row_diag}")
                        if st.button("Salvar Minha Análise", key=f"salvar_analise_cv_painel_v21_{idx_row_diag}", icon="💾"):
                            try:
                                df_antigos_upd = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                                df_antigos_upd['Data'] = df_antigos_upd['Data'].astype(str)
                                match_index = df_antigos_upd[(df_antigos_upd['CNPJ'] == row_diag_data['CNPJ']) & (df_antigos_upd['Data'] == str(row_diag_data['Data']))].index

                                if not match_index.empty:
                                    df_antigos_upd.loc[match_index[0], "Análise do Cliente"] = analise_cli_cv_input
                                    df_antigos_upd.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                    registrar_acao(st.session_state.cnpj, "Análise Cliente (Edição Painel)", f"Editou análise do diagnóstico de {row_diag_data['Data']}")
                                    st.toast("Sua análise foi salva!", icon="🎉"); st.rerun()
                                else:
                                    st.error("Não foi possível encontrar o diagnóstico para atualizar a análise.")
                            except Exception as e_save_analise_painel: st.error(f"Erro ao salvar sua análise: {e_save_analise_painel}")


                        com_admin_val_cv_painel = row_diag_data.get("Comentarios_Admin", "")
                        if com_admin_val_cv_painel and not pd.isna(com_admin_val_cv_painel) and str(com_admin_val_cv_painel).strip():
                            st.markdown("##### Comentários do Consultor:")
                            st.info(f"{com_admin_val_cv_painel}")
                            if expand_this_diag: 
                                st.markdown("<small><i>(Você foi direcionado para este comentário)</i></small>", unsafe_allow_html=True)
                        else: st.caption("Nenhum comentário do consultor para este diagnóstico.")

                        if st.button("Baixar PDF deste Diagnóstico", key=f"dl_pdf_antigo_v21_{idx_row_diag}", icon="📄"):
                            medias_cat_pdf_antigo = {k.replace("Media_Cat_","").replace("_"," "):v for k,v in row_diag_data.items() if "Media_Cat_" in k and pd.notna(v)}
                            pdf_path_antigo = gerar_pdf_diagnostico_completo(row_diag_data.to_dict(), st.session_state.user, perguntas_df_para_painel, row_diag_data.to_dict(), medias_cat_pdf_antigo, analises_df_para_painel)
                            if pdf_path_antigo:
                                with open(pdf_path_antigo, "rb") as f_antigo:
                                    st.download_button("Clique para Baixar", f_antigo,
                                                        file_name=f"diag_{sanitize_filename(row_diag_data['Empresa'])}_{str(row_diag_data['Data']).replace(':','-').replace(' ','_')}.pdf", # Usar sanitize_filename
                                                        mime="application/pdf",
                                                        key=f"dl_confirm_antigo_v21_{idx_row_diag}_{time.time()}",
                                                        icon="📄")
                                registrar_acao(st.session_state.cnpj, "Download PDF (Painel)", f"Baixou PDF de {row_diag_data['Data']}")
                            else: st.error("Erro ao gerar PDF para este diagnóstico.")
                        st.markdown('</div>', unsafe_allow_html=True)

                st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
                if not df_cliente_diags.empty:
                    latest_diag_kanban = df_cliente_diags.iloc[0]
                    gut_cards_kanban = []
                    for pergunta_k, resposta_k_str in latest_diag_kanban.items():
                        if isinstance(pergunta_k, str) and "[Matriz GUT]" in pergunta_k:
                            try:
                                if pd.notna(resposta_k_str) and isinstance(resposta_k_str, str):
                                    gut_data_k = json.loads(resposta_k_str.replace("'", "\""))
                                    g_k, u_k, t_k = int(gut_data_k.get("G", 0)), int(gut_data_k.get("U", 0)), int(gut_data_k.get("T", 0))
                                    score_gut_k = g_k * u_k * t_k
                                    prazo_k = "N/A"
                                    if score_gut_k >= 75: prazo_k = "15 dias"
                                    elif score_gut_k >= 40: prazo_k = "30 dias"
                                    elif score_gut_k >= 20: prazo_k = "45 dias"
                                    elif score_gut_k > 0: prazo_k = "60 dias"
                                    else: continue
                                    if prazo_k != "N/A":
                                        gut_cards_kanban.append({"Tarefa": pergunta_k.replace(" [Matriz GUT]", ""), "Prazo": prazo_k, "Score": score_gut_k, "Responsável": st.session_state.user.get("Empresa", "N/D")})
                            except (json.JSONDecodeError, ValueError, TypeError) as e_kanban_painel: st.warning(f"Erro ao processar GUT para Kanban '{pergunta_k}': {e_kanban_painel}")

                    if gut_cards_kanban:
                        gut_cards_sorted_kanban = sorted(gut_cards_kanban, key=lambda x: x["Score"], reverse=True)
                        prazos_unicos_kanban = sorted(list(set(card["Prazo"] for card in gut_cards_sorted_kanban)), key=lambda x_prazo: int(x_prazo.split(" ")[0]))
                        if prazos_unicos_kanban:
                            cols_kanban = st.columns(len(prazos_unicos_kanban))
                            for idx_col_k, prazo_k_col in enumerate(prazos_unicos_kanban):
                                with cols_kanban[idx_col_k]:
                                    st.markdown(f"#### ⏱️ {prazo_k_col}")
                                    for card_k_item in gut_cards_sorted_kanban:
                                        if card_k_item["Prazo"] == prazo_k_col:
                                            st.markdown(f"""<div class="custom-card"><b>{card_k_item['Tarefa']}</b> (Score GUT: {card_k_item['Score']})<br><small><i>👤 {card_k_item['Responsável']}</i></small></div>""", unsafe_allow_html=True)
                        else:
                            st.info("Nenhuma ação prioritária (GUT > 0) identificada no último diagnóstico para o Kanban.")
                    else:
                        st.info("Nenhuma ação prioritária (GUT > 0) identificada no último diagnóstico para o Kanban.")
                else:
                    st.info("Nenhum diagnóstico para gerar o Kanban.")
                st.divider()

                st.subheader("📈 Comparativo de Evolução das Médias")
                if not df_cliente_diags.empty and len(df_cliente_diags) > 1:
                    df_evolucao = df_cliente_diags.copy()
                    df_evolucao['Data'] = pd.to_datetime(df_evolucao['Data'])
                    df_evolucao = df_evolucao.sort_values(by="Data")

                    cols_plot_evol = ['Média Geral', 'GUT Média']
                    for col_ev in df_evolucao.columns:
                        if str(col_ev).startswith("Media_Cat_"):
                            df_evolucao[col_ev] = pd.to_numeric(df_evolucao[col_ev], errors='coerce')
                            if not df_evolucao[col_ev].isnull().all():
                                cols_plot_evol.append(col_ev)

                    df_evolucao_plot = df_evolucao.set_index("Data")[cols_plot_evol].dropna(axis=1, how='all')
                    if not df_evolucao_plot.empty:
                        rename_map = {col: col.replace("Media_Cat_", "Média ").replace("_", " ") for col in df_evolucao_plot.columns}
                        df_evolucao_plot_renamed = df_evolucao_plot.rename(columns=rename_map)
                        st.line_chart(df_evolucao_plot_renamed)
                    else:
                        st.info("Não há dados suficientes ou válidos nas colunas de médias para plotar o gráfico de evolução.")
                else:
                    st.info("São necessários pelo menos dois diagnósticos para exibir o comparativo de evolução.")
                st.divider()

                st.subheader("📊 Comparação Detalhada Entre Dois Diagnósticos")
                if not df_cliente_diags.empty and len(df_cliente_diags) > 1:
                    datas_opts_comp = df_cliente_diags["Data"].astype(str).tolist() 
                    idx_atual_comp = 0
                    idx_anterior_comp = 1 if len(datas_opts_comp) > 1 else 0

                    col_comp1, col_comp2 = st.columns(2)
                    diag1_data_str = col_comp1.selectbox("Selecione o Diagnóstico 1 (Mais Recente):", datas_opts_comp, index=idx_atual_comp, key="comp_diag1_sel_v21")
                    diag2_data_str = col_comp2.selectbox("Selecione o Diagnóstico 2 (Anterior):", datas_opts_comp, index=idx_anterior_comp, key="comp_diag2_sel_v21")

                    if diag1_data_str and diag2_data_str and diag1_data_str != diag2_data_str:
                        diag1_comp = df_cliente_diags[df_cliente_diags["Data"] == diag1_data_str].iloc[0]
                        diag2_comp = df_cliente_diags[df_cliente_diags["Data"] == diag2_data_str].iloc[0]

                        st.markdown(f"#### Comparando: `{diag1_data_str}` vs `{diag2_data_str}`")
                        metricas_comparacao = []
                        cols_interesse_comp = ["Média Geral", "GUT Média"] + [col for col in df_cliente_diags.columns if str(col).startswith("Media_Cat_")]

                        for metrica in cols_interesse_comp:
                            if metrica in diag1_comp and metrica in diag2_comp:
                                val1 = pd.to_numeric(diag1_comp.get(metrica), errors='coerce')
                                val2 = pd.to_numeric(diag2_comp.get(metrica), errors='coerce')
                                evolucao_txt = "➖"
                                delta_val = None
                                if pd.notna(val1) and pd.notna(val2):
                                    delta = val1 - val2
                                    delta_val = f"{delta:+.2f}"
                                    if val1 > val2: evolucao_txt = f"🔼 Melhorou"
                                    elif val1 < val2: evolucao_txt = f"🔽 Piorou"
                                metricas_comparacao.append({
                                    "Métrica": metrica.replace("Media_Cat_", "Média ").replace("_", " "),
                                    diag1_data_str.split(" ")[0]: f"{val1:.2f}" if pd.notna(val1) else "N/A",
                                    diag2_data_str.split(" ")[0]: f"{val2:.2f}" if pd.notna(val2) else "N/A",
                                    "Diferença": delta_val if delta_val else "N/A",
                                    "Evolução": evolucao_txt
                                })
                        if metricas_comparacao:
                            st.dataframe(pd.DataFrame(metricas_comparacao), use_container_width=True)
                        else:
                            st.info("Não foi possível gerar a tabela de comparação para as métricas selecionadas.")
                    elif diag1_data_str == diag2_data_str and len(df_cliente_diags)>1 :
                        st.warning("Selecione dois diagnósticos diferentes para comparação.")
                else:
                    st.info("São necessários pelo menos dois diagnósticos para fazer uma comparação detalhada.")

        except Exception as e: st.error(f"Erro ao carregar painel do cliente: {e}"); st.exception(e)


    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.subheader(menu_options_cli_map_full["Novo Diagnóstico"]) 
        
        if st.session_state.diagnostico_enviado_sucesso: 
            st.success("🎯 Seu diagnóstico foi enviado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                with open(st.session_state.pdf_gerado_path, "rb") as f_pdf_dl_sucesso:
                    st.download_button(label="Baixar PDF do Diagnóstico Enviado", data=f_pdf_dl_sucesso,
                                        file_name=st.session_state.pdf_gerado_filename, mime="application/pdf",
                                        key="dl_pdf_sucesso_novo_diag_v21", icon="📄")
            if st.button("Ir para o Painel Principal", key="ir_painel_apos_envio_sucesso_v21", icon="🏠"):
                st.session_state.cliente_page = "Painel Principal"
                st.session_state.diagnostico_enviado_sucesso = False; st.session_state.pdf_gerado_path = None; st.session_state.pdf_gerado_filename = None
                st.rerun()
            st.stop()

        try: perguntas_df_formulario = pd.read_csv(perguntas_csv, encoding='utf-8')
        except Exception as e: st.error(f"Erro ao carregar perguntas: {e}"); st.stop()
        if perguntas_df_formulario.empty: st.warning("Nenhuma pergunta cadastrada."); st.stop()
        if "Categoria" not in perguntas_df_formulario.columns: perguntas_df_formulario["Categoria"] = "Geral"

        total_perguntas_form = len(perguntas_df_formulario)
        if st.session_state.progresso_diagnostico_contagem[1] != total_perguntas_form:
            st.session_state.progresso_diagnostico_contagem = (st.session_state.progresso_diagnostico_contagem[0], total_perguntas_form)

        progresso_ph_novo = st.empty()

        def calcular_e_mostrar_progresso_novo():
            respondidas_novo = 0
            total_q_novo = st.session_state.progresso_diagnostico_contagem[1]
            if total_q_novo == 0:
                st.session_state.progresso_diagnostico_percentual = 0
                progresso_ph_novo.info(f"📊 Progresso: 0 de 0 respondidas (0%)")
                return

            for _, p_row_prog_novo in perguntas_df_formulario.iterrows():
                p_texto_prog_novo = p_row_prog_novo["Pergunta"]
                resp_prog_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_prog_novo)
                if resp_prog_novo is not None:
                    if "[Matriz GUT]" in p_texto_prog_novo:
                        if isinstance(resp_prog_novo, dict) and (int(resp_prog_novo.get("G",0)) > 0 or int(resp_prog_novo.get("U",0)) > 0 or int(resp_prog_novo.get("T",0)) > 0): respondidas_novo +=1
                    elif "Escala" in p_texto_prog_novo:
                        if resp_prog_novo != "Selecione": respondidas_novo +=1
                    elif isinstance(resp_prog_novo, str):
                        if resp_prog_novo.strip() : respondidas_novo +=1
                    elif isinstance(resp_prog_novo, (int,float)): 
                        if pd.notna(resp_prog_novo): respondidas_novo +=1 

            st.session_state.progresso_diagnostico_contagem = (respondidas_novo, total_q_novo)
            st.session_state.progresso_diagnostico_percentual = round((respondidas_novo / total_q_novo) * 100) if total_q_novo > 0 else 0
            progresso_ph_novo.progress(st.session_state.progresso_diagnostico_percentual / 100,
                                        text=f"📊 Progresso: {respondidas_novo} de {total_q_novo} respondidas ({st.session_state.progresso_diagnostico_percentual}%)")


        def on_change_resposta_novo(pergunta_txt_key_novo, widget_st_key_novo, tipo_pergunta_onchange_novo):
            valor_widget_novo = st.session_state.get(widget_st_key_novo)
            if tipo_pergunta_onchange_novo == "GUT_G":
                current_gut_novo = st.session_state.respostas_atuais_diagnostico.get(pergunta_txt_key_novo, {"G":0,"U":0,"T":0})
                current_gut_novo["G"] = valor_widget_novo
                st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = current_gut_novo
            elif tipo_pergunta_onchange_novo == "GUT_U":
                current_gut_novo = st.session_state.respostas_atuais_diagnostico.get(pergunta_txt_key_novo, {"G":0,"U":0,"T":0})
                current_gut_novo["U"] = valor_widget_novo
                st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = current_gut_novo
            elif tipo_pergunta_onchange_novo == "GUT_T":
                current_gut_novo = st.session_state.respostas_atuais_diagnostico.get(pergunta_txt_key_novo, {"G":0,"U":0,"T":0})
                current_gut_novo["T"] = valor_widget_novo
                st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = current_gut_novo
            else: st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = valor_widget_novo
            st.session_state.feedbacks_respostas[pergunta_txt_key_novo] = "✓" 
            calcular_e_mostrar_progresso_novo()

        calcular_e_mostrar_progresso_novo()

        for categoria_novo in sorted(perguntas_df_formulario["Categoria"].unique()):
            st.markdown(f"#### Categoria: {categoria_novo}")
            perg_cat_df_novo = perguntas_df_formulario[perguntas_df_formulario["Categoria"] == categoria_novo]
            for idx_novo, row_q_novo in perg_cat_df_novo.iterrows():
                p_texto_novo = str(row_q_novo["Pergunta"])
                w_key_novo = f"q_v21_{st.session_state.id_formulario_atual}_{idx_novo}"

                with st.container():
                    cols_q_feedback = st.columns([0.95, 0.05])
                    with cols_q_feedback[0]:
                        if "[Matriz GUT]" in p_texto_novo:
                            st.markdown(f"**{p_texto_novo.replace(' [Matriz GUT]', '')}**")
                            cols_gut_w_novo = st.columns(3)
                            gut_vals_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_novo, {"G":0,"U":0,"T":0})
                            key_g_n, key_u_n, key_t_n = f"{w_key_novo}_G", f"{w_key_novo}_U", f"{w_key_novo}_T"
                            cols_gut_w_novo[0].slider("Gravidade (0-5)",0,5,value=int(gut_vals_novo.get("G",0)), key=key_g_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_g_n, "GUT_G"))
                            cols_gut_w_novo[1].slider("Urgência (0-5)",0,5,value=int(gut_vals_novo.get("U",0)), key=key_u_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_u_n, "GUT_U"))
                            cols_gut_w_novo[2].slider("Tendência (0-5)",0,5,value=int(gut_vals_novo.get("T",0)), key=key_t_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_t_n, "GUT_T"))
                        elif "Pontuação (0-5)" in p_texto_novo:
                            st.slider(p_texto_novo,0,5,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Slider05"))
                        elif "Pontuação (0-10)" in p_texto_novo:
                            st.slider(p_texto_novo,0,10,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Slider010"))
                        elif "Texto Aberto" in p_texto_novo:
                            st.text_area(p_texto_novo,value=str(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,"")), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Texto"))
                        elif "Escala" in p_texto_novo:
                            opts_novo = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"]
                            curr_val_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_novo, "Selecione")
                            st.selectbox(p_texto_novo, opts_novo, index=opts_novo.index(curr_val_novo) if curr_val_novo in opts_novo else 0, key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Escala"))
                        else: 
                            st.slider(p_texto_novo,0,10,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "SliderDefault"))
                    with cols_q_feedback[1]:
                        if st.session_state.feedbacks_respostas.get(p_texto_novo):
                            st.markdown(f'<div class="feedback-saved" style="text-align: center; padding-top: 25px;">{st.session_state.feedbacks_respostas[p_texto_novo]}</div>', unsafe_allow_html=True)
                st.divider()

        key_obs_cli_n = f"obs_cli_diag_v21_{st.session_state.id_formulario_atual}"
        st.text_area("Sua Análise/Observações (opcional):", value=st.session_state.respostas_atuais_diagnostico.get("__obs_cliente__", ""),
                        key=key_obs_cli_n, on_change=on_change_resposta_novo, args=("__obs_cliente__", key_obs_cli_n, "ObsCliente"))
        key_res_cli_n = f"diag_resumo_diag_v21_{st.session_state.id_formulario_atual}"
        st.text_area("✍️ Resumo/principais insights (para PDF):", value=st.session_state.respostas_atuais_diagnostico.get("__resumo_cliente__", ""),
                        key=key_res_cli_n, on_change=on_change_resposta_novo, args=("__resumo_cliente__", key_res_cli_n, "ResumoCliente"))

        if st.button("Concluir e Enviar Diagnóstico", key="enviar_diag_final_cliente_v21", icon="✔️", use_container_width=True):
            with st.spinner("Processando e salvando seu diagnóstico..."):
                respostas_finais_envio_novo = st.session_state.respostas_atuais_diagnostico
                cont_resp_n, total_para_resp_n = st.session_state.progresso_diagnostico_contagem

                if cont_resp_n < total_para_resp_n:
                    st.warning("Por favor, responda todas as perguntas para um diagnóstico completo.")
                elif not respostas_finais_envio_novo.get("__resumo_cliente__","").strip():
                    st.error("O campo 'Resumo/principais insights (para PDF)' é obrigatório.")
                else:
                    soma_gut_n, count_gut_n = 0,0; respostas_csv_n = {}
                    for p_n,r_n in respostas_finais_envio_novo.items():
                        if p_n.startswith("__"): continue
                        if "[Matriz GUT]" in p_n and isinstance(r_n, dict):
                            respostas_csv_n[p_n] = json.dumps(r_n)
                            g_n_val,u_n_val,t_n_val = int(r_n.get("G",0)), int(r_n.get("U",0)), int(r_n.get("T",0)); soma_gut_n += (g_n_val*u_n_val*t_n_val); count_gut_n +=1
                        else: respostas_csv_n[p_n] = r_n
                    gut_media_n = round(soma_gut_n/count_gut_n,2) if count_gut_n > 0 else 0.0
                    num_resp_n = [v_n for k_n,v_n in respostas_finais_envio_novo.items() if not k_n.startswith("__") and isinstance(v_n,(int,float)) and ("[Matriz GUT]" not in k_n) and ("Pontuação" in k_n)]
                    media_geral_n = round(sum(num_resp_n)/len(num_resp_n),2) if num_resp_n else 0.0
                    emp_nome_n = st.session_state.user.get("Empresa","N/D")

                    nova_linha_diag_final_n = {
                        "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": st.session_state.cnpj,
                        "Nome": st.session_state.user.get("NomeContato", st.session_state.cnpj), "Email": "", "Empresa": emp_nome_n,
                        "Média Geral": media_geral_n, "GUT Média": gut_media_n, "Observações": "",
                        "Análise do Cliente": respostas_finais_envio_novo.get("__obs_cliente__",""),
                        "Diagnóstico": respostas_finais_envio_novo.get("__resumo_cliente__",""), "Comentarios_Admin": ""
                    }
                    nova_linha_diag_final_n.update(respostas_csv_n)
                    medias_cat_final_n = {}
                    for cat_iter_n in perguntas_df_formulario["Categoria"].unique():
                        soma_c_n, cont_c_n = 0,0
                        for _,pr_n in perguntas_df_formulario[perguntas_df_formulario["Categoria"]==cat_iter_n].iterrows():
                            pt_n = pr_n["Pergunta"]; rv_n = respostas_finais_envio_novo.get(pt_n)
                            if isinstance(rv_n,(int,float)) and ("[Matriz GUT]" not in pt_n) and ("Pontuação" in pt_n): soma_c_n+=rv_n; cont_c_n+=1
                        mc_n = round(soma_c_n/cont_c_n,2) if cont_c_n>0 else 0.0
                        nova_linha_diag_final_n[f"Media_Cat_{sanitize_column_name(cat_iter_n)}"] = mc_n
                        medias_cat_final_n[cat_iter_n] = mc_n

                    try: df_todos_diags_n = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                    except (FileNotFoundError, pd.errors.EmptyDataError): df_todos_diags_n = pd.DataFrame()
                    
                    for col_n_n in nova_linha_diag_final_n.keys():
                        if col_n_n not in df_todos_diags_n.columns: 
                            df_todos_diags_n[col_n_n] = pd.NA 
                    
                    df_todos_diags_n = pd.concat([df_todos_diags_n, pd.DataFrame([nova_linha_diag_final_n])], ignore_index=True)
                    df_todos_diags_n.to_csv(arquivo_csv, index=False, encoding='utf-8')

                    total_realizados_atual = st.session_state.user.get("TotalDiagnosticosRealizados", 0)
                    update_user_data(st.session_state.cnpj, "TotalDiagnosticosRealizados", total_realizados_atual + 1)
                    if st.session_state.user: st.session_state.user["TotalDiagnosticosRealizados"] = total_realizados_atual + 1

                    registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", "Cliente enviou novo diagnóstico.")
                    analises_df_para_pdf_n = carregar_analises_perguntas()
                    pdf_path_gerado_n = gerar_pdf_diagnostico_completo(nova_linha_diag_final_n, st.session_state.user, perguntas_df_formulario, respostas_finais_envio_novo, medias_cat_final_n, analises_df_para_pdf_n)

                    st.session_state.diagnostico_enviado_sucesso = True
                    if pdf_path_gerado_n:
                        st.session_state.pdf_gerado_path = pdf_path_gerado_n
                        st.session_state.pdf_gerado_filename = f"diagnostico_{sanitize_filename(emp_nome_n)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf" # Usar sanitize_filename

                    st.session_state.respostas_atuais_diagnostico = {}
                    st.session_state.progresso_diagnostico_percentual = 0
                    st.session_state.progresso_diagnostico_contagem = (0,total_perguntas_form)
                    st.session_state.feedbacks_respostas = {}
                    st.session_state.sac_feedback_registrado = {} 
                    st.session_state.cliente_page = "Painel Principal" 
                    st.rerun()

# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    portal_logo_sidebar_adm = get_portal_logo_path()
    if os.path.exists(portal_logo_sidebar_adm):
        st.sidebar.image(portal_logo_sidebar_adm, use_column_width='auto')
    else:
        st.sidebar.markdown(f"### Painel Admin")


    st.sidebar.success(f"🟢 Admin: {st.session_state.get('admin_username', '')} ({st.session_state.get('admin_permissions', 'N/D')})")


    if st.sidebar.button("Sair do Painel Admin", icon="🚪", key="logout_admin_v21", use_container_width=True):
        st.session_state.admin_logado = False
        st.session_state.admin_username = None
        st.session_state.admin_permissions = "visualizacao" 
        st.toast("Logout de admin realizado.", icon="👋")
        st.rerun()

    menu_admin_options_map = {
        "Visão Geral e Diagnósticos": "📊",
        "Relatório de Engajamento": "📈", 
        "Gerenciar Notificações": "🔔",
        "Gerenciar Clientes": "👥",
        "Gerenciar Perguntas (Diagnóstico)": "📝", 
        "Gerenciar Análises de Perguntas": "💡",
        "Gerenciar Pesquisa de Satisfação": "🧐", 
        "Gerenciar SAC": "📞",
        "Configurações do Portal": "⚙️", # Renomeado e movido
        "Histórico de Usuários": "📜", 
        "Gerenciar Administradores": "👮"
    }
    admin_page_text_keys = list(menu_admin_options_map.keys())
    admin_options_for_display = [f"{menu_admin_options_map[key]} {key}" for key in admin_page_text_keys]

    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_text_key_v21" 
    WIDGET_KEY_SB_ADMIN_MENU = "sb_admin_menu_v21" 

    def admin_menu_on_change():
        selected_display_value = st.session_state[WIDGET_KEY_SB_ADMIN_MENU]
        new_text_key = None
        for text_key, emoji in menu_admin_options_map.items():
            if f"{emoji} {text_key}" == selected_display_value:
                new_text_key = text_key
                break
        if new_text_key and new_text_key != st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE):
            st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = new_text_key

    if SESSION_KEY_FOR_ADMIN_PAGE not in st.session_state or \
       st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] not in admin_page_text_keys:
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]

    current_admin_page_text_key_for_index = st.session_state[SESSION_KEY_FOR_ADMIN_PAGE]
    try:
        expected_display_value_for_current_page = f"{menu_admin_options_map[current_admin_page_text_key_for_index]} {current_admin_page_text_key_for_index}"
        current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
    except (ValueError, KeyError):
        current_admin_menu_index = 0
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]

    st.sidebar.selectbox(
        "Funcionalidades Admin:",
        options=admin_options_for_display,
        index=current_admin_menu_index,
        key=WIDGET_KEY_SB_ADMIN_MENU,
        on_change=admin_menu_on_change
    )

    menu_admin = st.session_state[SESSION_KEY_FOR_ADMIN_PAGE]
    header_display_name = f"{menu_admin_options_map[menu_admin]} {menu_admin}"
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
        if "LogoPath" not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load["LogoPath"] = None # Garantir coluna
        
        df_usuarios_admin_geral = df_usuarios_admin_temp_load
    except FileNotFoundError:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Clientes", "Gerenciar Notificações", "Relatório de Engajamento", "Gerenciar SAC", "Gerenciar Pesquisa de Satisfação"]:
            st.sidebar.error(f"Arquivo '{usuarios_csv}' não encontrado. Funcionalidades limitadas.")
    except Exception as e_load_users_adm_global:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Cliente