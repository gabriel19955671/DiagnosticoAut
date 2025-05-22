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

# --- CSS Melhorado (igual ao fornecido) ---
st.markdown("""
<style>
body {
    font-family: 'Segoe UI', sans-serif;
}
.login-container {
    max-width: 450px;
    margin: 40px auto 0 auto;
    padding: 40px;
    border-radius: 10px;
    background-color: #ffffff;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    font-family: 'Segoe UI', sans-serif;
}
.login-container img {
    display: block;
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 20px;
}
.login-container h2 {
    text-align: center;
    margin-bottom: 30px;
    font-weight: 600;
    font-size: 26px;
    color: #2563eb;
}
.stButton>button {
    border-radius: 6px;
    background-color: #2563eb;
    color: white;
    font-weight: 500;
    padding: 0.6rem 1.3rem;
    margin-top: 0.5rem;
    border: none;
    transition: background-color 0.3s ease;
}
.stButton>button:hover {
    background-color: #1d4ed8;
}
.stButton>button.secondary {
    background-color: #e5e7eb;
    color: #374151;
}
.stButton>button.secondary:hover {
    background-color: #d1d5db;
}
.stDownloadButton>button {
    background-color: #10b981;
    color: white;
    font-weight: 600;
    border-radius: 6px;
    margin-top: 10px;
    padding: 0.6rem 1.3rem;
    border: none;
    transition: background-color 0.3s ease;
}
.stDownloadButton>button:hover {
    background-color: #059669;
}
.stTextInput>div>input, .stTextArea>div>textarea, .stDateInput>div>input, .stSelectbox>div>div {
    border-radius: 6px;
    padding: 0.6rem;
    border: 1px solid #d1d5db;
    background-color: #f9fafb;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.stTextInput>div>input:focus, .stTextArea>div>textarea:focus, .stDateInput>div>input:focus, .stSelectbox>div>div:focus-within {
    border-color: #2563eb;
    box-shadow: 0 0 0 0.1rem rgba(37, 99, 235, 0.25);
}
.stTabs [data-baseweb="tab"] {
    font-size: 16px;
    font-weight: 600;
    padding: 12px 22px;
    border-radius: 6px 6px 0 0;
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
    border-radius: 8px;
    background-color: #ffffff;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07);
}
.custom-card h4 {
    margin-top: 0;
    color: #2563eb;
    font-size: 1.1em;
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
    background-color: #eef2ff;
    border-left: 3px solid #6366f1;
    padding: 10px;
    margin-top: 8px;
    margin-bottom:12px;
    border-radius: 4px;
}
[data-testid="stMetric"] {
    background-color: #ffffff;
    border-radius: 8px;
    padding: 15px 20px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07);
    border: 1px solid #e0e0e0;
}
[data-testid="stMetricLabel"] {
    font-weight: 500;
    color: #4b5563;
}
[data-testid="stMetricValue"] {
    font-size: 1.8em;
}
[data-testid="stMetricDelta"] {
    font-size: 0.9em;
}
.stExpander {
    border: 1px solid #e0e0e0 !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07) !important;
    margin-bottom: 15px !important;
}
.stExpander header {
    font-weight: 600 !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 15px !important;
}
.dashboard-item {
    background-color: #ffffff;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07);
    margin-bottom: 20px;
    border: 1px solid #e0e0e0;
    height: 100%;
}
.dashboard-item h5 {
    margin-top: 0;
    margin-bottom: 15px;
    color: #2563eb;
    font-size: 1.1em;
    border-bottom: 1px solid #eee;
    padding-bottom: 8px;
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

</style>
""", unsafe_allow_html=True)

# --- Funções de Gráficos (igual ao fornecido) ---
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
# NOVOS ARQUIVOS PARA PESQUISA DE SATISFAÇÃO
pesquisa_satisfacao_perguntas_csv = "pesquisa_satisfacao_perguntas.csv"
pesquisa_satisfacao_respostas_csv = "pesquisa_satisfacao_respostas.csv"
LOGOS_DIR = "client_logos"

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None, # ID do formulário de diagnóstico
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {}, "sac_feedback_registrado": {},
    "force_sidebar_rerun_after_notif_read_v19": False,
    "target_diag_data_for_expansion": None,
    "id_diagnostico_concluido_para_satisfacao": None, # Novo: Para rastrear qual diagnóstico precisa de pesquisa
    "respostas_pesquisa_satisfacao_atual": {}, # Novo
    "pesquisa_satisfacao_enviada": False, # Novo
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias (exceto gráficos) ---
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
    except OSError as e: st.error(f"Erro ao criar diretório de logos '{LOGOS_DIR}': {e}")

colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone",
                         "JaVisualizouInstrucoes", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]
colunas_base_perguntas = ["Pergunta", "Categoria"]
colunas_base_analises = ["ID_Analise", "TextoPerguntaOriginal", "TipoCondicao", "CondicaoValorMin", "CondicaoValorMax", "CondicaoValorExato", "TextoAnalise"]
colunas_base_notificacoes = ["ID_Notificacao", "CNPJ_Cliente", "Timestamp", "Mensagem", "Lida", "ID_Diagnostico_Relacionado"] 
colunas_base_sac_perguntas = ["ID_SAC_Pergunta", "Pergunta_SAC", "Resposta_SAC", "Categoria_SAC", "DataCriacao"]
colunas_base_sac_uso_feedback = ["ID_Uso_SAC", "Timestamp", "CNPJ_Cliente", "ID_SAC_Pergunta", "Feedback_Util"]
# NOVAS COLUNAS BASE
colunas_base_pesquisa_satisfacao_perguntas = ["ID_Pergunta_Satisfacao", "Texto_Pergunta", "Tipo_Pergunta", "Opcoes_Pergunta", "Ordem", "Ativa"]
colunas_base_pesquisa_satisfacao_respostas = ["ID_Resposta_Satisfacao", "ID_Diagnostico_Cliente", "ID_Pergunta_Satisfacao", "CNPJ_Cliente", "Timestamp_Resposta", "Resposta_Valor"]


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
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype={'CNPJ': str, 'CNPJ_Cliente': str} if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, sac_uso_feedback_csv, pesquisa_satisfacao_respostas_csv] else None)
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
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype={'CNPJ': str, 'CNPJ_Cliente': str} if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, sac_uso_feedback_csv, pesquisa_satisfacao_respostas_csv] else None)

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
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios,
                    defaults={"JaVisualizouInstrucoes": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos) 
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False, "ID_Diagnostico_Relacionado": None}) 
    inicializar_csv(sac_perguntas_respostas_csv, colunas_base_sac_perguntas, defaults={"Categoria_SAC": "Geral", "DataCriacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    inicializar_csv(sac_uso_feedback_csv, colunas_base_sac_uso_feedback, defaults={"Feedback_Util": None})
    # INICIALIZAÇÃO DOS NOVOS ARQUIVOS
    inicializar_csv(pesquisa_satisfacao_perguntas_csv, colunas_base_pesquisa_satisfacao_perguntas, defaults={"Ordem": 0, "Ativa": True, "Opcoes_Pergunta": None})
    inicializar_csv(pesquisa_satisfacao_respostas_csv, colunas_base_pesquisa_satisfacao_respostas)
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

# NOVAS FUNÇÕES PARA PESQUISA DE SATISFAÇÃO
@st.cache_data
def carregar_perguntas_satisfacao(apenas_ativas=True):
    try:
        df = pd.read_csv(pesquisa_satisfacao_perguntas_csv, encoding='utf-8')
        if 'Ativa' not in df.columns: df['Ativa'] = True # Default para True se coluna não existir
        else: df['Ativa'] = df['Ativa'].astype(bool)
        if 'Ordem' not in df.columns: df['Ordem'] = 0
        else: df['Ordem'] = pd.to_numeric(df['Ordem'], errors='coerce').fillna(0).astype(int)
        
        if apenas_ativas:
            df = df[df['Ativa'] == True]
        return df.sort_values(by="Ordem", ascending=True)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_pesquisa_satisfacao_perguntas)

@st.cache_data
def carregar_respostas_satisfacao(cnpj_cliente=None, id_diagnostico=None):
    try:
        df = pd.read_csv(pesquisa_satisfacao_respostas_csv, encoding='utf-8', dtype={'CNPJ_Cliente': str})
        if cnpj_cliente:
            df = df[df['CNPJ_Cliente'] == str(cnpj_cliente)]
        if id_diagnostico:
            df = df[df['ID_Diagnostico_Cliente'] == str(id_diagnostico)]
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_pesquisa_satisfacao_respostas)

def verificar_pesquisa_satisfacao_pendente(cnpj_cliente, id_diagnostico_cliente):
    """Verifica se o cliente já respondeu à pesquisa para este diagnóstico específico."""
    respostas_existentes = carregar_respostas_satisfacao(cnpj_cliente=cnpj_cliente, id_diagnostico=id_diagnostico_cliente)
    return respostas_existentes.empty # Pendente se não houver respostas para este diagnóstico


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
            categorias = perguntas_df["Categoria"].unique() if not perguntas_df.empty and "Categoria" in perguntas_df.columns else []
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

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): st.session_state.trigger_rerun_global = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v19")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.image("https://via.placeholder.com/200x80.png?text=Logo+do+Portal", width=200)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v19"):
        u = st.text_input("Usuário", key="admin_u_v19"); p = st.text_input("Senha", type="password", key="admin_p_v19")
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

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.image("https://via.placeholder.com/200x80.png?text=Logo+do+Portal", width=200)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_v19"):
        c = st.text_input("CNPJ", key="cli_c_v19", value=st.session_state.get("last_cnpj_input",""))
        s = st.text_input("Senha", type="password", key="cli_s_v19")
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

                # ID do diagnóstico em andamento (será usado para vincular pesquisa de satisfação)
                st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                st.session_state.respostas_atuais_diagnostico = {}
                st.session_state.progresso_diagnostico_percentual = 0
                st.session_state.progresso_diagnostico_contagem = (0,0)
                st.session_state.feedbacks_respostas = {}
                st.session_state.sac_feedback_registrado = {}
                st.session_state.diagnostico_enviado_sucesso = False
                st.session_state.target_diag_data_for_expansion = None 
                st.session_state.id_diagnostico_concluido_para_satisfacao = None # Reset
                st.session_state.respostas_pesquisa_satisfacao_atual = {} # Reset
                st.session_state.pesquisa_satisfacao_enviada = False # Reset


                st.toast("Login de cliente bem-sucedido!", icon="👋")
                st.rerun()
            except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
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

    selected_page_cli_raw = st.sidebar.radio("Menu Cliente", menu_options_cli_display, index=current_idx_cli, key="cli_menu_v19_conditional")
    
    selected_page_cli_clean = ""
    for key_page, val_page_display in menu_options_cli_map.items(): 
        if val_page_display == selected_page_cli_raw: 
            if key_page == "Notificações": 
                selected_page_cli_clean = "Notificações"
            elif key_page == "SAC":
                selected_page_cli_clean = "SAC"
            else:
                selected_page_cli_clean = key_page
            break
    
    if selected_page_cli_clean and selected_page_cli_clean != st.session_state.cliente_page :
        st.session_state.cliente_page = selected_page_cli_clean
        st.session_state.force_sidebar_rerun_after_notif_read_v19 = False 
        st.session_state.target_diag_data_for_expansion = None 
        st.rerun()

    if st.sidebar.button("Sair do Portal Cliente", icon="⬅️", key="logout_cliente_v19", use_container_width=True):
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

        if st.button("Entendi, prosseguir", key="btn_instrucoes_v19", icon="👍"):
            update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", "True")
            if st.session_state.user: st.session_state.user["JaVisualizouInstrucoes"] = True
            
            pode_fazer_novo_inst = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo_inst else "Painel Principal"
            st.rerun()

    elif st.session_state.cliente_page == "SAC":
        st.subheader(menu_options_cli_map_full["SAC"])
        df_sac_qa = carregar_sac_perguntas_respostas()

        if df_sac_qa.empty:
            st.info("Nenhuma pergunta frequente cadastrada no momento.")
        else:
            df_sac_qa_sorted = df_sac_qa.sort_values(by=["Categoria_SAC", "Pergunta_SAC"])
            categorias_sac = df_sac_qa_sorted["Categoria_SAC"].unique()

            search_term_sac = st.text_input("🔎 Procurar nas Perguntas Frequentes:", key="search_sac_cliente")
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
                        
                        feedback_key_base = f"sac_feedback_{row_sac['ID_SAC_Pergunta']}"
                        feedback_dado = st.session_state.sac_feedback_registrado.get(row_sac['ID_SAC_Pergunta'])

                        cols_feedback = st.columns([1,1,8])
                        with cols_feedback[0]:
                            btn_class_util = "active" if feedback_dado == "util" else ""
                            if st.button("👍 Útil", key=f"{feedback_key_base}_util", help="Esta resposta foi útil", use_container_width=True,
                                        type="secondary" if feedback_dado != "util" else "primary"):
                                try:
                                    df_feedback = carregar_sac_uso_feedback()
                                    novo_feedback = pd.DataFrame([{
                                        "ID_Uso_SAC": str(uuid.uuid4()), "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "CNPJ_Cliente": st.session_state.cnpj, "ID_SAC_Pergunta": row_sac['ID_SAC_Pergunta'],
                                        "Feedback_Util": True
                                    }])
                                    df_feedback = pd.concat([df_feedback, novo_feedback], ignore_index=True)
                                    df_feedback.to_csv(sac_uso_feedback_csv, index=False, encoding='utf-8')
                                    st.session_state.sac_feedback_registrado[row_sac['ID_SAC_Pergunta']] = "util"
                                    st.toast("Obrigado pelo seu feedback!", icon="😊")
                                    st.rerun() 
                                except Exception as e_fb:
                                    st.error(f"Erro ao registrar feedback: {e_fb}")
                        with cols_feedback[1]:
                            btn_class_nao_util = "active" if feedback_dado == "nao_util" else ""
                            if st.button("👎 Não útil", key=f"{feedback_key_base}_nao_util", help="Esta resposta não foi útil", use_container_width=True,
                                        type="secondary" if feedback_dado != "nao_util" else "primary"):
                                try:
                                    df_feedback = carregar_sac_uso_feedback()
                                    novo_feedback = pd.DataFrame([{
                                        "ID_Uso_SAC": str(uuid.uuid4()), "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "CNPJ_Cliente": st.session_state.cnpj, "ID_SAC_Pergunta": row_sac['ID_SAC_Pergunta'],
                                        "Feedback_Util": False
                                    }])
                                    df_feedback = pd.concat([df_feedback, novo_feedback], ignore_index=True)
                                    df_feedback.to_csv(sac_uso_feedback_csv, index=False, encoding='utf-8')
                                    st.session_state.sac_feedback_registrado[row_sac['ID_SAC_Pergunta']] = "nao_util"
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
                                       key="dl_novo_diag_painel_v19", icon="📄")
                st.session_state.pdf_gerado_path = None # Clear after download button is shown
                st.session_state.pdf_gerado_filename = None
            
            # --- INÍCIO: LÓGICA DA PESQUISA DE SATISFAÇÃO ---
            if st.session_state.id_diagnostico_concluido_para_satisfacao and not st.session_state.pesquisa_satisfacao_enviada:
                id_diag_atual_satisfacao = st.session_state.id_diagnostico_concluido_para_satisfacao
                
                # Verifica se já respondeu para este diagnóstico específico
                if verificar_pesquisa_satisfacao_pendente(st.session_state.cnpj, id_diag_atual_satisfacao):
                    st.markdown("---")
                    st.subheader("⭐ Pesquisa de Satisfação Rápida")
                    st.caption("Sua opinião é muito importante para nós! Por favor, dedique um momento para responder.")

                    perguntas_satisfacao_df = carregar_perguntas_satisfacao(apenas_ativas=True)
                    if not perguntas_satisfacao_df.empty:
                        with st.form(key="form_pesquisa_satisfacao_cliente"):
                            for idx_ps, row_ps in perguntas_satisfacao_df.iterrows():
                                p_id = row_ps["ID_Pergunta_Satisfacao"]
                                p_texto = row_ps["Texto_Pergunta"]
                                p_tipo = row_ps["Tipo_Pergunta"]
                                p_opcoes_str = row_ps.get("Opcoes_Pergunta")

                                widget_key_ps = f"satisfacao_{p_id}"
                                st.markdown(f"**{p_texto}**")

                                if p_tipo == "escala_1_5":
                                    st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.radio(
                                        label=" ", # Label vazia para não repetir pergunta
                                        options=list(range(1, 6)), 
                                        key=widget_key_ps, 
                                        horizontal=True,
                                        label_visibility="collapsed"
                                    )
                                elif p_tipo == "texto_aberto":
                                    st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.text_area(
                                        label=" ", key=widget_key_ps, label_visibility="collapsed"
                                    )
                                elif p_tipo == "sim_nao":
                                    st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.radio(
                                        label=" ", options=["Sim", "Não"], key=widget_key_ps, horizontal=True, label_visibility="collapsed"
                                    )
                                elif p_tipo == "multipla_escolha_unica":
                                    opcoes_ps = []
                                    if pd.notna(p_opcoes_str):
                                        try:
                                            opcoes_data = json.loads(p_opcoes_str)
                                            opcoes_ps = opcoes_data.get("opcoes", [])
                                        except json.JSONDecodeError:
                                            st.warning(f"Opções mal formatadas para pergunta: {p_texto}")
                                    
                                    if opcoes_ps:
                                        st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.radio(
                                            label=" ", options=opcoes_ps, key=widget_key_ps, label_visibility="collapsed"
                                        )
                                    else:
                                        st.caption(" (Opções não configuradas para esta pergunta)")
                                else:
                                    st.caption(f"(Tipo de pergunta '{p_tipo}' não suportado no momento)")
                                st.write("") # Espaçamento

                            submit_pesquisa_satisfacao = st.form_submit_button("Enviar Feedback de Satisfação", use_container_width=True, icon="💖")
                            if submit_pesquisa_satisfacao:
                                respostas_finais_satisfacao = []
                                timestamp_atual_satisfacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                for id_pergunta, resposta_val in st.session_state.respostas_pesquisa_satisfacao_atual.items():
                                    if resposta_val is not None: # Salva apenas se algo foi selecionado/digitado
                                        respostas_finais_satisfacao.append({
                                            "ID_Resposta_Satisfacao": str(uuid.uuid4()),
                                            "ID_Diagnostico_Cliente": id_diag_atual_satisfacao,
                                            "ID_Pergunta_Satisfacao": id_pergunta,
                                            "CNPJ_Cliente": st.session_state.cnpj,
                                            "Timestamp_Resposta": timestamp_atual_satisfacao,
                                            "Resposta_Valor": str(resposta_val) # Salva tudo como string
                                        })
                                
                                if respostas_finais_satisfacao:
                                    df_respostas_todas_satisfacao = carregar_respostas_satisfacao() # Carrega todas para append
                                    df_novas_respostas_satisfacao = pd.DataFrame(respostas_finais_satisfacao)
                                    df_respostas_atualizadas_satisfacao = pd.concat([df_respostas_todas_satisfacao, df_novas_respostas_satisfacao], ignore_index=True)
                                    df_respostas_atualizadas_satisfacao.to_csv(pesquisa_satisfacao_respostas_csv, index=False, encoding='utf-8')
                                    
                                    st.cache_data.clear() # Limpa cache de respostas
                                    st.session_state.pesquisa_satisfacao_enviada = True
                                    st.session_state.id_diagnostico_concluido_para_satisfacao = None # Marca como feita para este
                                    st.session_state.respostas_pesquisa_satisfacao_atual = {}
                                    st.success("Obrigado pelo seu feedback de satisfação!")
                                    time.sleep(1.5) # Pequena pausa para o usuário ver a mensagem
                                    st.rerun()
                                else:
                                    st.warning("Nenhuma resposta foi fornecida na pesquisa de satisfação.")
                    else:
                        st.info("A pesquisa de satisfação não possui perguntas ativas no momento.")
                elif not st.session_state.pesquisa_satisfacao_enviada: # Já respondeu para este diagnóstico, mas não foi a flag de "enviada nesta sessão"
                    st.success("Você já respondeu à pesquisa de satisfação para este diagnóstico. Obrigado!")
            # --- FIM: LÓGICA DA PESQUISA DE SATISFAÇÃO ---
            st.session_state.diagnostico_enviado_sucesso = False # Reset para não mostrar a msg de sucesso do diagnóstico de novo

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
                        analise_cli_cv_input = st.text_area("🧠 Minha Análise sobre este Diagnóstico:", value=analise_cli_val_cv_painel, key=f"analise_cv_painel_v19_{idx_row_diag}")
                        if st.button("Salvar Minha Análise", key=f"salvar_analise_cv_painel_v19_{idx_row_diag}", icon="💾"):
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

                        if st.button("Baixar PDF deste Diagnóstico", key=f"dl_pdf_antigo_v19_{idx_row_diag}", icon="📄"):
                            medias_cat_pdf_antigo = {k.replace("Media_Cat_","").replace("_"," "):v for k,v in row_diag_data.items() if "Media_Cat_" in k and pd.notna(v)}
                            pdf_path_antigo = gerar_pdf_diagnostico_completo(row_diag_data.to_dict(), st.session_state.user, perguntas_df_para_painel, row_diag_data.to_dict(), medias_cat_pdf_antigo, analises_df_para_painel)
                            if pdf_path_antigo:
                                with open(pdf_path_antigo, "rb") as f_antigo:
                                    st.download_button("Clique para Baixar", f_antigo,
                                                       file_name=f"diag_{sanitize_column_name(row_diag_data['Empresa'])}_{str(row_diag_data['Data']).replace(':','-').replace(' ','_')}.pdf",
                                                       mime="application/pdf",
                                                       key=f"dl_confirm_antigo_v19_{idx_row_diag}_{time.time()}",
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
                    diag1_data_str = col_comp1.selectbox("Selecione o Diagnóstico 1 (Mais Recente):", datas_opts_comp, index=idx_atual_comp, key="comp_diag1_sel_v19")
                    diag2_data_str = col_comp2.selectbox("Selecione o Diagnóstico 2 (Anterior):", datas_opts_comp, index=idx_anterior_comp, key="comp_diag2_sel_v19")

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
            # Esta lógica é movida para o Painel Principal para incluir a pesquisa de satisfação
            # Se chegou aqui e diagnostico_enviado_sucesso é True, algo deu errado no redirect, mas
            # o painel principal que agora lida com o pós-envio.
            st.info("Retornando ao painel principal...")
            st.session_state.cliente_page = "Painel Principal"
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
                w_key_novo = f"q_v19_{st.session_state.id_formulario_atual}_{idx_novo}"

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

        key_obs_cli_n = f"obs_cli_diag_v19_{st.session_state.id_formulario_atual}"
        st.text_area("Sua Análise/Observações (opcional):", value=st.session_state.respostas_atuais_diagnostico.get("__obs_cliente__", ""),
                     key=key_obs_cli_n, on_change=on_change_resposta_novo, args=("__obs_cliente__", key_obs_cli_n, "ObsCliente"))
        key_res_cli_n = f"diag_resumo_diag_v19_{st.session_state.id_formulario_atual}"
        st.text_area("✍️ Resumo/principais insights (para PDF):", value=st.session_state.respostas_atuais_diagnostico.get("__resumo_cliente__", ""),
                     key=key_res_cli_n, on_change=on_change_resposta_novo, args=("__resumo_cliente__", key_res_cli_n, "ResumoCliente"))

        if st.button("Concluir e Enviar Diagnóstico", key="enviar_diag_final_cliente_v19", icon="✔️", use_container_width=True):
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

                    # Usar o ID do formulário atual (que é o timestamp) como Data
                    id_diagnostico_salvo = st.session_state.id_formulario_atual 

                    nova_linha_diag_final_n = {
                        "Data": id_diagnostico_salvo, "CNPJ": st.session_state.cnpj, # "Data" é o ID do diagnóstico
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

                    registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", f"Cliente enviou novo diagnóstico (ID: {id_diagnostico_salvo}).")
                    analises_df_para_pdf_n = carregar_analises_perguntas()
                    pdf_path_gerado_n = gerar_pdf_diagnostico_completo(nova_linha_diag_final_n, st.session_state.user, perguntas_df_formulario, respostas_finais_envio_novo, medias_cat_final_n, analises_df_para_pdf_n)

                    st.session_state.diagnostico_enviado_sucesso = True
                    st.session_state.id_diagnostico_concluido_para_satisfacao = id_diagnostico_salvo # Seta para mostrar pesquisa no painel
                    st.session_state.pesquisa_satisfacao_enviada = False # Reseta flag de envio da pesquisa

                    if pdf_path_gerado_n:
                        st.session_state.pdf_gerado_path = pdf_path_gerado_n
                        st.session_state.pdf_gerado_filename = f"diagnostico_{sanitize_column_name(emp_nome_n)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

                    st.session_state.respostas_atuais_diagnostico = {}
                    st.session_state.progresso_diagnostico_percentual = 0
                    st.session_state.progresso_diagnostico_contagem = (0,total_perguntas_form)
                    st.session_state.feedbacks_respostas = {}
                    st.session_state.sac_feedback_registrado = {} 
                    st.session_state.cliente_page = "Painel Principal" 
                    st.rerun()

# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    try:
        st.sidebar.image("https://via.placeholder.com/200x80.png?text=Logo+Admin", use_container_width=True)
    except Exception as e_img_admin:
        st.sidebar.caption(f"Logo admin não carregada: {e_img_admin}")

    st.sidebar.success("🟢 Admin Logado")

    if st.sidebar.button("Sair do Painel Admin", icon="🚪", key="logout_admin_v19", use_container_width=True):
        st.session_state.admin_logado = False
        st.toast("Logout de admin realizado.", icon="👋")
        st.rerun()

    menu_admin_options_map = {
        "Visão Geral e Diagnósticos": "📊",
        "Relatório de Engajamento": "📈", 
        "Gerenciar Notificações": "🔔",
        "Gerenciar Clientes": "👥",
        "Gerenciar Perguntas (Diagnóstico)": "📝", # Renomeado para clareza
        "Gerenciar Análises de Perguntas": "💡",
        "Gerenciar SAC": "📞", 
        "⭐ Gerenciar Pesquisa de Satisfação": "⭐", # NOVO
        "📊 Relatório Pesquisa de Satisfação": "📊", # NOVO
        "Gerenciar Instruções": "⚙️",
        "Histórico de Usuários": "📜", 
        "Gerenciar Administradores": "👮"
    }
    admin_page_text_keys = list(menu_admin_options_map.keys())
    admin_options_for_display = [f"{menu_admin_options_map[key]} {key}" for key in admin_page_text_keys]

    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_text_key_v19"
    WIDGET_KEY_SB_ADMIN_MENU = "sb_admin_menu_v19"

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
        
        df_usuarios_admin_geral = df_usuarios_admin_temp_load
    except FileNotFoundError:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Clientes", "Gerenciar Notificações", "Relatório de Engajamento", "Gerenciar SAC", "⭐ Gerenciar Pesquisa de Satisfação", "📊 Relatório Pesquisa de Satisfação"]:
            st.sidebar.error(f"Arquivo '{usuarios_csv}' não encontrado. Funcionalidades limitadas.")
    except Exception as e_load_users_adm_global:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Clientes", "Gerenciar Notificações", "Relatório de Engajamento", "Gerenciar SAC", "⭐ Gerenciar Pesquisa de Satisfação", "📊 Relatório Pesquisa de Satisfação"]:
            st.sidebar.error(f"Erro ao carregar usuários para admin: {e_load_users_adm_global}")

    # ... (Restante do código do Admin para outras seções)
    # Mantive as seções anteriores do Admin. O novo código será adicionado abaixo:

    if menu_admin == "Gerenciar Perguntas (Diagnóstico)": # Renomeado para clareza
        tabs_perg_admin = st.tabs(["📋 Perguntas Atuais", "➕ Adicionar Nova Pergunta"])
        try:
            perguntas_df_admin_gp = pd.read_csv(perguntas_csv, encoding='utf-8')
            if "Categoria" not in perguntas_df_admin_gp.columns: perguntas_df_admin_gp["Categoria"] = "Geral"
        except (FileNotFoundError, pd.errors.EmptyDataError):
            perguntas_df_admin_gp = pd.DataFrame(columns=colunas_base_perguntas)

        with tabs_perg_admin[0]:
            if perguntas_df_admin_gp.empty: st.info("Nenhuma pergunta de diagnóstico cadastrada.")
            else:
                for i_p_admin, row_p_admin in perguntas_df_admin_gp.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div class="custom-card" style="margin-bottom: 15px;">
                            <p style="font-size: 0.8em; color: #6b7280; margin-bottom: 5px;">ID: {i_p_admin} | Categoria: <b>{row_p_admin.get("Categoria", "Geral")}</b></p>
                            <p style="font-weight: 500;">{row_p_admin["Pergunta"]}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        with st.expander("✏️ Editar Pergunta de Diagnóstico"):
                            cols_edit_perg = st.columns([3, 2])
                            novo_p_text_admin = cols_edit_perg[0].text_area("Texto da Pergunta:", value=str(row_p_admin["Pergunta"]), key=f"edit_p_txt_v19_gp_{i_p_admin}", height=100)
                            nova_cat_text_admin = cols_edit_perg[1].text_input("Categoria:", value=str(row_p_admin.get("Categoria", "Geral")), key=f"edit_p_cat_v19_gp_{i_p_admin}")

                            col_btn1, col_btn2 = st.columns([0.15, 0.85])
                            if col_btn1.button("Salvar", key=f"salvar_p_adm_v19_gp_{i_p_admin}", help="Salvar Alterações", icon="💾"):
                                perguntas_df_admin_gp.loc[i_p_admin, "Pergunta"] = novo_p_text_admin
                                perguntas_df_admin_gp.loc[i_p_admin, "Categoria"] = nova_cat_text_admin
                                perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                st.toast(f"Pergunta de diagnóstico {i_p_admin} atualizada.", icon="✅"); st.rerun()

                            if col_btn2.button("Deletar", type="primary", key=f"deletar_p_adm_v19_gp_{i_p_admin}", help="Deletar Pergunta", icon="🗑️"):
                                perguntas_df_admin_gp = perguntas_df_admin_gp.drop(i_p_admin).reset_index(drop=True)
                                perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                st.toast(f"Pergunta de diagnóstico {i_p_admin} removida.", icon="🗑️"); st.rerun()
                    st.divider()
        with tabs_perg_admin[1]:
            with st.form("form_nova_pergunta_admin_v19_gp"):
                st.subheader("➕ Adicionar Nova Pergunta de Diagnóstico")
                nova_p_form_txt_admin = st.text_input("Texto da Pergunta", key="nova_p_input_admin_txt_v19_gp")
                cat_existentes_gp = sorted(list(perguntas_df_admin_gp['Categoria'].astype(str).unique())) if not perguntas_df_admin_gp.empty else []
                cat_options_gp = ["Nova Categoria"] + cat_existentes_gp
                cat_selecionada_gp = st.selectbox("Categoria:", cat_options_gp, key="cat_select_admin_new_q_v19_gp")
                nova_cat_form_admin_gp = st.text_input("Nome da Nova Categoria:", key="nova_cat_input_admin_new_q_v19_gp") if cat_selecionada_gp == "Nova Categoria" else cat_selecionada_gp

                tipo_p_form_admin = st.selectbox("Tipo de Pergunta (será adicionado ao final do texto da pergunta):",
                                                 ["Pontuação (0-10)", "Pontuação (0-5)", "Texto Aberto", "Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)", "[Matriz GUT]"],
                                                 key="tipo_p_select_admin_new_q_v19_gp")
                add_p_btn_admin = st.form_submit_button("Adicionar Pergunta", icon="➕", use_container_width=True)
                if add_p_btn_admin:
                    if nova_p_form_txt_admin.strip() and nova_cat_form_admin_gp.strip():
                        p_completa_add_admin = f"{nova_p_form_txt_admin.strip()} [{tipo_p_form_admin.replace('[','').replace(']','')}]"
                        nova_entrada_p_add_admin = pd.DataFrame([[p_completa_add_admin, nova_cat_form_admin_gp.strip()]], columns=["Pergunta", "Categoria"])
                        perguntas_df_admin_gp = pd.concat([perguntas_df_admin_gp, nova_entrada_p_add_admin], ignore_index=True)
                        perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                        st.toast(f"Pergunta de diagnóstico adicionada!", icon="🎉"); st.rerun()
                    else: st.warning("Texto da pergunta e categoria são obrigatórios.")
    
    elif menu_admin == "⭐ Gerenciar Pesquisa de Satisfação":
        st.markdown("#### Gerenciamento das Perguntas da Pesquisa de Satisfação")
        df_perguntas_satisfacao_admin = carregar_perguntas_satisfacao(apenas_ativas=False).copy() # Carrega todas, ativas e inativas

        tab_view_ps, tab_add_ps = st.tabs(["📋 Ver/Editar Perguntas de Satisfação", "➕ Adicionar Nova Pergunta de Satisfação"])

        with tab_view_ps:
            if df_perguntas_satisfacao_admin.empty:
                st.info("Nenhuma pergunta de satisfação cadastrada ainda.")
            else:
                for idx_ps_admin, row_ps_admin in df_perguntas_satisfacao_admin.iterrows():
                    id_ps_admin = row_ps_admin["ID_Pergunta_Satisfacao"]
                    com_card_ps = st.container()
                    com_card_ps.markdown(f"""
                    <div class="custom-card" style="border-left-color: {'#10b981' if row_ps_admin['Ativa'] else '#f59e0b'};">
                        <small>ID: {id_ps_admin} | Ordem: {row_ps_admin['Ordem']} | Status: {'Ativa' if row_ps_admin['Ativa'] else 'Inativa'}</small>
                        <p><strong>Pergunta:</strong> {row_ps_admin['Texto_Pergunta']}</p>
                        <p><strong>Tipo:</strong> {row_ps_admin['Tipo_Pergunta']}</p>
                        {f"<p><strong>Opções:</strong> {row_ps_admin['Opcoes_Pergunta']}</p>" if pd.notna(row_ps_admin['Opcoes_Pergunta']) and row_ps_admin['Tipo_Pergunta'] == 'multipla_escolha_unica' else ""}
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander(f"✏️ Editar / 🗑️ Deletar Pergunta de Satisfação ID: {id_ps_admin[:8]}..."):
                        with st.form(key=f"form_edit_ps_{id_ps_admin}"):
                            edited_texto_ps = st.text_area("Texto da Pergunta:", value=row_ps_admin["Texto_Pergunta"], key=f"text_ps_edit_{id_ps_admin}")
                            tipos_pergunta_ps_opts = ['escala_1_5', 'texto_aberto', 'sim_nao', 'multipla_escolha_unica']
                            edited_tipo_ps = st.selectbox("Tipo da Pergunta:", tipos_pergunta_ps_opts, 
                                                          index=tipos_pergunta_ps_opts.index(row_ps_admin["Tipo_Pergunta"]) if row_ps_admin["Tipo_Pergunta"] in tipos_pergunta_ps_opts else 0,
                                                          key=f"tipo_ps_edit_{id_ps_admin}")
                            
                            edited_opcoes_ps_str = ""
                            if edited_tipo_ps == 'multipla_escolha_unica':
                                current_opcoes_list = []
                                if pd.notna(row_ps_admin["Opcoes_Pergunta"]):
                                    try: current_opcoes_list = json.loads(row_ps_admin["Opcoes_Pergunta"]).get("opcoes", [])
                                    except: pass
                                edited_opcoes_ps_str = st.text_area("Opções (uma por linha):", 
                                                                    value="\n".join(current_opcoes_list), 
                                                                    key=f"opcoes_ps_edit_{id_ps_admin}",
                                                                    help="Insira cada opção em uma nova linha.")
                            
                            edited_ordem_ps = st.number_input("Ordem de Exibição:", value=int(row_ps_admin["Ordem"]), step=1, key=f"ordem_ps_edit_{id_ps_admin}")
                            edited_ativa_ps = st.checkbox("Ativa?", value=bool(row_ps_admin["Ativa"]), key=f"ativa_ps_edit_{id_ps_admin}")

                            cols_btns_edit_ps = st.columns(2)
                            if cols_btns_edit_ps[0].form_submit_button("Salvar Alterações", icon="💾", use_container_width=True):
                                df_perguntas_satisfacao_admin.loc[idx_ps_admin, "Texto_Pergunta"] = edited_texto_ps
                                df_perguntas_satisfacao_admin.loc[idx_ps_admin, "Tipo_Pergunta"] = edited_tipo_ps
                                if edited_tipo_ps == 'multipla_escolha_unica':
                                    opcoes_list = [opt.strip() for opt in edited_opcoes_ps_str.split('\n') if opt.strip()]
                                    df_perguntas_satisfacao_admin.loc[idx_ps_admin, "Opcoes_Pergunta"] = json.dumps({"opcoes": opcoes_list}) if opcoes_list else None
                                else:
                                    df_perguntas_satisfacao_admin.loc[idx_ps_admin, "Opcoes_Pergunta"] = None
                                df_perguntas_satisfacao_admin.loc[idx_ps_admin, "Ordem"] = edited_ordem_ps
                                df_perguntas_satisfacao_admin.loc[idx_ps_admin, "Ativa"] = edited_ativa_ps
                                
                                df_perguntas_satisfacao_admin.to_csv(pesquisa_satisfacao_perguntas_csv, index=False, encoding='utf-8')
                                st.cache_data.clear()
                                st.toast(f"Pergunta de satisfação '{id_ps_admin[:8]}...' atualizada.", icon="✅")
                                st.rerun()

                            if cols_btns_edit_ps[1].form_submit_button("Deletar Pergunta", icon="🗑️", type="primary", use_container_width=True):
                                df_perguntas_satisfacao_admin = df_perguntas_satisfacao_admin.drop(index=idx_ps_admin)
                                df_perguntas_satisfacao_admin.to_csv(pesquisa_satisfacao_perguntas_csv, index=False, encoding='utf-8')
                                # Opcional: deletar respostas associadas
                                st.cache_data.clear()
                                st.toast(f"Pergunta de satisfação '{id_ps_admin[:8]}...' deletada.", icon="🗑️")
                                st.rerun()
                    st.markdown("---")


        with tab_add_ps:
            st.subheader("Adicionar Nova Pergunta à Pesquisa de Satisfação")
            with st.form("form_nova_pergunta_satisfacao", clear_on_submit=True):
                nova_ps_texto = st.text_input("Texto da Pergunta:")
                tipos_pergunta_ps_opts_novo = ['escala_1_5', 'texto_aberto', 'sim_nao', 'multipla_escolha_unica']
                nova_ps_tipo = st.selectbox("Tipo da Pergunta:", tipos_pergunta_ps_opts_novo)
                
                nova_ps_opcoes_str = ""
                if nova_ps_tipo == 'multipla_escolha_unica':
                    nova_ps_opcoes_str = st.text_area("Opções (uma por linha):", help="Insira cada opção em uma nova linha.")

                nova_ps_ordem = st.number_input("Ordem de Exibição:", value=0, step=1)
                nova_ps_ativa = st.checkbox("Ativa?", value=True)

                if st.form_submit_button("Adicionar Pergunta de Satisfação", icon="➕", use_container_width=True):
                    if nova_ps_texto.strip():
                        id_nova_ps = str(uuid.uuid4())
                        opcoes_finais_ps = None
                        if nova_ps_tipo == 'multipla_escolha_unica' and nova_ps_opcoes_str.strip():
                            opcoes_list_ps = [opt.strip() for opt in nova_ps_opcoes_str.split('\n') if opt.strip()]
                            if opcoes_list_ps:
                                opcoes_finais_ps = json.dumps({"opcoes": opcoes_list_ps})
                        
                        nova_entrada_ps = pd.DataFrame([{
                            "ID_Pergunta_Satisfacao": id_nova_ps,
                            "Texto_Pergunta": nova_ps_texto.strip(),
                            "Tipo_Pergunta": nova_ps_tipo,
                            "Opcoes_Pergunta": opcoes_finais_ps,
                            "Ordem": nova_ps_ordem,
                            "Ativa": nova_ps_ativa
                        }])
                        df_perguntas_satisfacao_admin = pd.concat([df_perguntas_satisfacao_admin, nova_entrada_ps], ignore_index=True)
                        df_perguntas_satisfacao_admin.to_csv(pesquisa_satisfacao_perguntas_csv, index=False, encoding='utf-8')
                        st.cache_data.clear()
                        st.toast("Nova pergunta de satisfação adicionada!", icon="🎉")
                        st.rerun()
                    else:
                        st.warning("O texto da pergunta é obrigatório.")

    elif menu_admin == "📊 Relatório Pesquisa de Satisfação":
        st.markdown("#### Análise das Respostas da Pesquisa de Satisfação")

        df_respostas_ps_admin = carregar_respostas_satisfacao()
        df_diagnosticos_admin_completos = pd.DataFrame()
        try:
            df_diagnosticos_admin_completos = pd.read_csv(arquivo_csv, dtype={'CNPJ': str})
            if 'Data' in df_diagnosticos_admin_completos.columns: # 'Data' é o ID do diagnóstico
                 df_diagnosticos_admin_completos.rename(columns={'Data': 'ID_Diagnostico_Cliente'}, inplace=True) # Renomear para merge
        except:
            st.error("Não foi possível carregar os diagnósticos para o relatório.")

        if df_diagnosticos_admin_completos.empty:
            st.info("Nenhum diagnóstico realizado no sistema para gerar relatório de participação.")
        else:
            # Clientes que realizaram pelo menos um diagnóstico
            clientes_com_diagnostico = df_diagnosticos_admin_completos[['CNPJ', 'Empresa', 'ID_Diagnostico_Cliente']].drop_duplicates(subset=['CNPJ', 'ID_Diagnostico_Cliente'])
            
            if df_respostas_ps_admin.empty:
                st.info("Nenhuma resposta à pesquisa de satisfação foi registrada ainda.")
                diagnosticos_sem_resposta_ps = clientes_com_diagnostico
                diagnosticos_com_resposta_ps = pd.DataFrame()
            else:
                # Merge para identificar diagnósticos com e sem resposta de satisfação
                df_merged_diag_respostas = pd.merge(
                    clientes_com_diagnostico,
                    df_respostas_ps_admin[['ID_Diagnostico_Cliente', 'CNPJ_Cliente']].drop_duplicates(), # Pega apenas uma linha por diagnóstico respondido
                    on=['ID_Diagnostico_Cliente', 'CNPJ_Cliente'], # Usa CNPJ_Cliente de respostas
                    how='left',
                    indicator=True
                )
                diagnosticos_com_resposta_ps = df_merged_diag_respostas[df_merged_diag_respostas['_merge'] == 'both']
                diagnosticos_sem_resposta_ps = df_merged_diag_respostas[df_merged_diag_respostas['_merge'] == 'left_only']
            
            num_com_resposta = len(diagnosticos_com_resposta_ps['ID_Diagnostico_Cliente'].unique())
            num_sem_resposta = len(diagnosticos_sem_resposta_ps['ID_Diagnostico_Cliente'].unique())
            total_diagnosticos_unicos = num_com_resposta + num_sem_resposta

            st.subheader("Participação na Pesquisa de Satisfação (por Diagnóstico)")
            if total_diagnosticos_unicos > 0:
                col_metric_ps1, col_metric_ps2, col_metric_ps3 = st.columns(3)
                col_metric_ps1.metric("Total de Diagnósticos Realizados", total_diagnosticos_unicos)
                col_metric_ps2.metric("Diagnósticos COM Pesquisa Respondida", num_com_resposta)
                col_metric_ps3.metric("Diagnósticos SEM Pesquisa Respondida", num_sem_resposta)

                if num_sem_resposta > 0:
                    with st.expander(f"Ver {num_sem_resposta} Diagnósticos Sem Resposta de Satisfação"):
                        st.dataframe(diagnosticos_sem_resposta_ps[['Empresa', 'CNPJ', 'ID_Diagnostico_Cliente']].rename(columns={'ID_Diagnostico_Cliente': 'Data/ID do Diagnóstico'}), use_container_width=True)
                if num_com_resposta > 0:
                     with st.expander(f"Ver {num_com_resposta} Diagnósticos Com Resposta de Satisfação"):
                        st.dataframe(diagnosticos_com_resposta_ps[['Empresa', 'CNPJ', 'ID_Diagnostico_Cliente']].rename(columns={'ID_Diagnostico_Cliente': 'Data/ID do Diagnóstico'}), use_container_width=True)
            else:
                st.info("Nenhum diagnóstico encontrado para análise de participação.")

            st.divider()
            st.subheader("Visualização Detalhada das Respostas")
            df_perguntas_satisfacao_todas = carregar_perguntas_satisfacao(apenas_ativas=False)
            if df_perguntas_satisfacao_todas.empty or df_respostas_ps_admin.empty:
                st.info("Não há perguntas de satisfação cadastradas ou nenhuma resposta para exibir.")
            else:
                # Filtro por pergunta
                lista_nomes_perguntas_ps = df_perguntas_satisfacao_todas.apply(lambda row: f"{row['Texto_Pergunta']} (ID: {row['ID_Pergunta_Satisfacao'][:8]}...)", axis=1).tolist()
                pergunta_selecionada_ps_report = st.selectbox("Selecione uma Pergunta de Satisfação para ver as respostas:", ["Todas"] + lista_nomes_perguntas_ps, key="admin_report_ps_pergunta_sel")

                df_respostas_filtradas_ps = df_respostas_ps_admin.copy()
                id_pergunta_filtro_ps = None
                if pergunta_selecionada_ps_report != "Todas":
                    try:
                        id_pergunta_filtro_ps = re.search(r"ID: ([\w-]+)", pergunta_selecionada_ps_report).group(1)
                        # Precisamos do ID completo, não apenas os primeiros 8 chars. Rebuscar no df.
                        for _, row_full_id in df_perguntas_satisfacao_todas.iterrows():
                            if row_full_id["ID_Pergunta_Satisfacao"].startswith(id_pergunta_filtro_ps):
                                id_pergunta_filtro_ps = row_full_id["ID_Pergunta_Satisfacao"]
                                break
                        df_respostas_filtradas_ps = df_respostas_filtradas_ps[df_respostas_filtradas_ps["ID_Pergunta_Satisfacao"] == id_pergunta_filtro_ps]
                    except:
                        st.warning("Não foi possível identificar a pergunta selecionada.")
                        id_pergunta_filtro_ps = None
                
                if df_respostas_filtradas_ps.empty:
                    st.info("Nenhuma resposta para os filtros selecionados.")
                else:
                    # Juntar com nome da empresa e texto da pergunta para melhor visualização
                    df_respostas_display_admin = pd.merge(df_respostas_filtradas_ps, df_usuarios_admin_geral[['CNPJ', 'Empresa']], left_on='CNPJ_Cliente', right_on='CNPJ', how='left')
                    df_respostas_display_admin = pd.merge(df_respostas_display_admin, df_perguntas_satisfacao_todas[['ID_Pergunta_Satisfacao', 'Texto_Pergunta', 'Tipo_Pergunta', 'Opcoes_Pergunta']], on='ID_Pergunta_Satisfacao', how='left')
                    
                    cols_to_show_admin_ps = ['Timestamp_Resposta', 'Empresa', 'CNPJ_Cliente', 'Texto_Pergunta', 'Resposta_Valor', 'ID_Diagnostico_Cliente']
                    st.dataframe(df_respostas_display_admin[cols_to_show_admin_ps].sort_values(by="Timestamp_Resposta", ascending=False), use_container_width=True)

                    # Gerar gráficos para a pergunta selecionada
                    if id_pergunta_filtro_ps:
                        dados_pergunta_especifica = df_perguntas_satisfacao_todas[df_perguntas_satisfacao_todas["ID_Pergunta_Satisfacao"] == id_pergunta_filtro_ps].iloc[0]
                        tipo_pergunta_grafico = dados_pergunta_especifica["Tipo_Pergunta"]
                        
                        if tipo_pergunta_grafico == 'escala_1_5':
                            counts = df_respostas_filtradas_ps['Resposta_Valor'].astype(int).value_counts().sort_index()
                            fig = px.bar(counts, x=counts.index, y=counts.values, labels={'x':'Nota', 'y':'Contagem'}, title=f"Distribuição de Respostas: {dados_pergunta_especifica['Texto_Pergunta']}")
                            st.plotly_chart(fig, use_container_width=True)
                        elif tipo_pergunta_grafico == 'sim_nao':
                            counts = df_respostas_filtradas_ps['Resposta_Valor'].value_counts()
                            fig = px.pie(counts, values=counts.values, names=counts.index, title=f"Respostas: {dados_pergunta_especifica['Texto_Pergunta']}")
                            st.plotly_chart(fig, use_container_width=True)
                        elif tipo_pergunta_grafico == 'multipla_escolha_unica':
                            counts = df_respostas_filtradas_ps['Resposta_Valor'].value_counts()
                            fig = px.bar(counts, x=counts.index, y=counts.values, labels={'x':'Opção', 'y':'Contagem'}, title=f"Respostas: {dados_pergunta_especifica['Texto_Pergunta']}")
                            st.plotly_chart(fig, use_container_width=True)
                        elif tipo_pergunta_grafico == 'texto_aberto':
                            st.markdown("##### Respostas Abertas:")
                            for _, row_resp_aberta in df_respostas_display_admin[df_respostas_display_admin["ID_Pergunta_Satisfacao"] == id_pergunta_filtro_ps].iterrows():
                                st.markdown(f"""
                                <div class="custom-card" style="border-left-color: #6366f1; margin-bottom: 8px; padding:10px;">
                                    <small>{row_resp_aberta.get('Empresa','N/A')} ({row_resp_aberta['Timestamp_Resposta']}):</small>
                                    <p>{row_resp_aberta['Resposta_Valor']}</p>
                                </div>
                                """, unsafe_allow_html=True)

    # --- Restante do código do Admin (Gerenciar Clientes, Admin, etc.)
    # ... (código original para as outras seções do admin, como Gerenciar Clientes, Gerenciar Administradores, etc.)
    # Este código foi omitido para brevidade, mas deve ser mantido conforme o original.
    # As seções "Gerenciar Clientes", "Gerenciar Análises de Perguntas", "Gerenciar SAC", "Gerenciar Instruções", 
    # "Histórico de Usuários", "Gerenciar Administradores", "Visão Geral e Diagnósticos", "Relatório de Engajamento",
    # "Gerenciar Notificações" devem ser incluídas aqui, conforme o código original.
    # Apenas "Gerenciar Perguntas" foi renomeado para "Gerenciar Perguntas (Diagnóstico)".

    # Exemplo de como ficaria a estrutura para Gerenciar Clientes (manter o código original)
    elif menu_admin == "Gerenciar Clientes":
        df_usuarios_gc = df_usuarios_admin_geral.copy()
        st.sidebar.markdown("---") 
        st.sidebar.subheader("Filtros para Gerenciar Clientes")
        filter_instrucoes_status_gc = st.sidebar.selectbox(
            "Status das Instruções:",
            ["Todos", "Visualizaram Instruções", "Não Visualizaram Instruções"],
            key="admin_gc_filter_instrucoes_status"
        )
        df_display_clientes_gc = df_usuarios_gc.copy()
        if filter_instrucoes_status_gc == "Visualizaram Instruções":
            df_display_clientes_gc = df_display_clientes_gc[df_display_clientes_gc["JaVisualizouInstrucoes"] == True]
        elif filter_instrucoes_status_gc == "Não Visualizaram Instruções":
            df_display_clientes_gc = df_display_clientes_gc[df_display_clientes_gc["JaVisualizouInstrucoes"] == False]

        st.markdown("#### Lista de Clientes Cadastrados")
        if not df_display_clientes_gc.empty:
            cols_display_gc = ["CNPJ", "Empresa", "NomeContato", "Telefone", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados", "JaVisualizouInstrucoes"]
            cols_to_show_gc = [col for col in cols_display_gc if col in df_display_clientes_gc.columns]
            st.dataframe(df_display_clientes_gc[cols_to_show_gc], use_container_width=True)

            st.markdown("#### Ações de Cliente (selecionado da lista filtrada acima)")
            
            if not df_display_clientes_gc.empty:
                clientes_lista_gc_ops = df_display_clientes_gc.apply(lambda row: f"{row['Empresa']} ({row['CNPJ']})", axis=1).tolist()
                cliente_selecionado_str_gc = st.selectbox("Selecione o cliente para gerenciar:", [""] + clientes_lista_gc_ops, key="sel_cliente_gc_v19_filtered")

                if cliente_selecionado_str_gc:
                    cnpj_selecionado_gc_val = cliente_selecionado_str_gc.split('(')[-1].replace(')','').strip()
                    cliente_data_gc_val_row = df_usuarios_gc[df_usuarios_gc["CNPJ"] == cnpj_selecionado_gc_val]
                    if not cliente_data_gc_val_row.empty:
                        cliente_data_gc_val = cliente_data_gc_val_row.iloc[0]

                        st.markdown(f"""
                        <div class="custom-card">
                            <h4>{cliente_data_gc_val['Empresa']}</h4>
                            <p><strong>CNPJ:</strong> {cliente_data_gc_val['CNPJ']}</p>
                            <p><strong>Diagnósticos Contratados (Slots):</strong> {cliente_data_gc_val['DiagnosticosDisponiveis']}</p>
                            <p><strong>Diagnósticos Já Realizados:</strong> {cliente_data_gc_val['TotalDiagnosticosRealizados']}</p>
                            <p><strong>Instruções Visualizadas:</strong> {'Sim' if cliente_data_gc_val['JaVisualizouInstrucoes'] else 'Não'}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        action_cols = st.columns(2)
                        with action_cols[0]:
                            if st.button(f"Conceder +1 Diagnóstico", key=f"conceder_diag_gc_v19_{cnpj_selecionado_gc_val}", icon="➕", use_container_width=True):
                                novos_disponiveis = cliente_data_gc_val['DiagnosticosDisponiveis'] + 1
                                if update_user_data(cnpj_selecionado_gc_val, "DiagnosticosDisponiveis", novos_disponiveis):
                                    registrar_acao("ADMIN", "Concessão Diagnóstico", f"Admin concedeu +1 slot para {cliente_data_gc_val['Empresa']} ({cnpj_selecionado_gc_val}). Total agora: {novos_disponiveis}")
                                    st.toast(f"+1 Slot de diagnóstico concedido. Total agora: {novos_disponiveis}.", icon="🎉"); st.rerun()
                                else:
                                    st.error("Falha ao conceder diagnóstico.")

                        with action_cols[1]:
                            try: bloqueados_df_gc_check = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                            except FileNotFoundError: bloqueados_df_gc_check = pd.DataFrame(columns=["CNPJ"])

                            is_blocked_gc_check = cnpj_selecionado_gc_val in bloqueados_df_gc_check["CNPJ"].values
                            if is_blocked_gc_check:
                                if st.button(f"Desbloquear Acesso", key=f"desbloq_total_gc_v19_{cnpj_selecionado_gc_val}", icon="🔓", use_container_width=True):
                                    bloqueados_df_gc_check = bloqueados_df_gc_check[bloqueados_df_gc_check["CNPJ"] != cnpj_selecionado_gc_val]
                                    bloqueados_df_gc_check.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                                    st.toast(f"Acesso total desbloqueado.", icon="✅"); st.rerun()
                            else:
                                if st.button(f"Bloquear Acesso", type="primary", key=f"bloq_total_gc_v19_{cnpj_selecionado_gc_val}", icon="🔒", use_container_width=True):
                                    nova_entrada_bloqueio_gc_val = pd.DataFrame([{"CNPJ": cnpj_selecionado_gc_val}])
                                    bloqueados_df_gc_check = pd.concat([bloqueados_df_gc_check, nova_entrada_bloqueio_gc_val], ignore_index=True)
                                    bloqueados_df_gc_check.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                                    st.toast(f"Acesso total bloqueado.", icon="🚫"); st.rerun()
                    else:
                        st.warning("Cliente selecionado não encontrado nos dados originais. Pode ter sido removido ou há uma inconsistência.")
            else:
                st.info("Nenhum cliente correspondente ao filtro para selecionar ações.")
        else:
            st.info("Nenhum cliente cadastrado para gerenciar ou exibir com os filtros atuais.")

        st.markdown("---")
        st.markdown("#### Adicionar Novo Cliente")
        with st.form("form_novo_cliente_v19", clear_on_submit=True):
            novo_cnpj_gc_form = st.text_input("CNPJ do Novo Cliente:")
            nova_senha_gc_form = st.text_input("Senha para o Novo Cliente:", type="password")
            nova_empresa_gc_form = st.text_input("Nome da Empresa do Novo Cliente:")
            novo_contato_gc_form = st.text_input("Nome do Contato (opcional):")
            novo_telefone_gc_form = st.text_input("Telefone do Contato (opcional):")
            submit_novo_cliente_gc_form = st.form_submit_button("Cadastrar Novo Cliente", icon="➕", use_container_width=True)

            if submit_novo_cliente_gc_form:
                if novo_cnpj_gc_form and nova_senha_gc_form and nova_empresa_gc_form:
                    if df_usuarios_admin_geral.empty or (novo_cnpj_gc_form not in df_usuarios_admin_geral["CNPJ"].values):
                        nova_linha_cliente_form = pd.DataFrame([{
                            "CNPJ": novo_cnpj_gc_form, "Senha": nova_senha_gc_form, "Empresa": nova_empresa_gc_form,
                            "NomeContato": novo_contato_gc_form, "Telefone": novo_telefone_gc_form,
                            "JaVisualizouInstrucoes": False, 
                            "DiagnosticosDisponiveis": 1, 
                            "TotalDiagnosticosRealizados": 0
                        }])
                        df_usuarios_gc_para_salvar = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                        for col in ["DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]:
                            if col in df_usuarios_gc_para_salvar.columns:
                                df_usuarios_gc_para_salvar[col] = pd.to_numeric(df_usuarios_gc_para_salvar[col], errors='coerce').fillna(0).astype(int)
                        if "JaVisualizouInstrucoes" in df_usuarios_gc_para_salvar.columns:
                            df_usuarios_gc_para_salvar["JaVisualizouInstrucoes"] = df_usuarios_gc_para_salvar["JaVisualizouInstrucoes"].astype(str).str.lower().map({'true': True, 'false': False, 'nan':False, '':False}).fillna(False)

                        df_usuarios_gc_updated = pd.concat([df_usuarios_gc_para_salvar, nova_linha_cliente_form], ignore_index=True)
                        df_usuarios_gc_updated.to_csv(usuarios_csv, index=False, encoding='utf-8')
                        st.toast(f"Cliente {nova_empresa_gc_form} cadastrado com sucesso!", icon="🎉"); st.rerun()
                    else: st.error("CNPJ já cadastrado.")
                else: st.error("CNPJ, Senha e Nome da Empresa são obrigatórios.")
    # ... (Incluir aqui as outras seções do admin que foram omitidas para brevidade) ...


if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()