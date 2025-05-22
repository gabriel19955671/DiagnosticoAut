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

# --- CSS Melhorado ---
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

# --- Funções de Gráficos ---
def create_radar_chart(data_dict, title="Radar Chart"):
    if not data_dict or not isinstance(data_dict, dict): return None
    categories = []
    values = []
    for k, v in data_dict.items():
        val_num = pd.to_numeric(v, errors='coerce')
        if pd.notna(val_num):
            categories.append(k)
            values.append(val_num)

    if not categories or not values or len(categories) < 3: return None
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]
    df_radar = pd.DataFrame(dict(r=values_closed, theta=categories_closed))
    fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True, template="seaborn")
    fig.update_traces(fill='toself', line=dict(color='#2563eb'))
    fig.update_layout(title={'text': title, 'x':0.5, 'xanchor': 'center'}, polar=dict(radialaxis=dict(visible=True, range=[0, 5])), font=dict(family="Segoe UI, sans-serif"), margin=dict(l=50, r=50, t=70, b=50))
    return fig

def create_gut_barchart(gut_data_list, title="Top Prioridades (GUT)"):
    if not gut_data_list: return None
    df_gut = pd.DataFrame(gut_data_list)
    if df_gut.empty or not all(col in df_gut.columns for col in ["Tarefa", "Score"]): return None
    df_gut["Score"] = pd.to_numeric(df_gut["Score"], errors='coerce')
    df_gut.dropna(subset=["Score"], inplace=True)
    df_gut = df_gut.sort_values(by="Score", ascending=False).head(10)
    if df_gut.empty: return None
    fig = px.bar(df_gut, x="Score", y="Tarefa", title=title, orientation='h', color="Score", color_continuous_scale=px.colors.sequential.Blues_r, labels={'Tarefa':'Tarefa/Pergunta', 'Score':'Score GUT'})
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Score GUT", yaxis_title="", font=dict(family="Segoe UI, sans-serif"), height=max(400, 200 + len(df_gut)*30), margin=dict(l=max(150, df_gut['Tarefa'].astype(str).map(len).max() * 7 if not df_gut.empty else 150), r=20, t=70, b=20))
    return fig

def create_diagnostics_timeline_chart(df_diagnostics, title="Diagnósticos Realizados ao Longo do Tempo"):
    if df_diagnostics.empty or 'Data_dt' not in df_diagnostics.columns: return None
    df_diag_copy = df_diagnostics.dropna(subset=['Data_dt']).copy()
    if df_diag_copy.empty : return None
    diag_counts_monthly = df_diag_copy.groupby(pd.Grouper(key='Data_dt', freq='M')).size().reset_index(name='Contagem')
    diag_counts_monthly['Mês'] = diag_counts_monthly['Data_dt'].dt.strftime('%Y-%m')
    if diag_counts_monthly.empty: return None
    fig = px.line(diag_counts_monthly, x='Mês', y='Contagem', title=title, markers=True, labels={'Mês':'Mês', 'Contagem':'Nº de Diagnósticos'}, line_shape="spline")
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
            avg_scores_data.append({'Categoria': col.replace("Media_Cat_", "").replace("_", " "), 'Média_Score': numeric_scores.mean()})
    if not avg_scores_data: return None
    avg_scores = pd.DataFrame(avg_scores_data)
    if avg_scores.empty : return None
    avg_scores = avg_scores.sort_values(by="Média_Score", ascending=False)
    fig = px.bar(avg_scores, x='Categoria', y='Média_Score', title=title, color='Média_Score', color_continuous_scale=px.colors.sequential.Blues_r, labels={'Categoria':'Categoria', 'Média_Score':'Média do Score'})
    fig.update_layout(xaxis_tickangle=-45, font=dict(family="Segoe UI, sans-serif"), yaxis=dict(range=[0,max(5.5, avg_scores['Média_Score'].max() + 0.5 if not avg_scores.empty else 5.5)]))
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
    fig = px.pie(engagement_counts, values='Numero_Clientes', names='Categoria_Engajamento', title=title, color_discrete_sequence=px.colors.sequential.Blues_r)
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
pesquisa_satisfacao_perguntas_csv = "pesquisa_satisfacao_perguntas.csv"
pesquisa_satisfacao_respostas_csv = "pesquisa_satisfacao_respostas.csv"
LOGOS_DIR = "client_logos"

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
    "id_diagnostico_concluido_para_satisfacao": None,
    "respostas_pesquisa_satisfacao_atual": {},
    "pesquisa_satisfacao_enviada": False,
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
    except OSError as e: st.error(f"Erro ao criar diretório de logos '{LOGOS_DIR}': {e}")

colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone", "JaVisualizouInstrucoes", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]
colunas_base_perguntas = ["Pergunta", "Categoria"]
colunas_base_analises = ["ID_Analise", "TextoPerguntaOriginal", "TipoCondicao", "CondicaoValorMin", "CondicaoValorMax", "CondicaoValorExato", "TextoAnalise"]
colunas_base_notificacoes = ["ID_Notificacao", "CNPJ_Cliente", "Timestamp", "Mensagem", "Lida", "ID_Diagnostico_Relacionado"]
colunas_base_sac_perguntas = ["ID_SAC_Pergunta", "Pergunta_SAC", "Resposta_SAC", "Categoria_SAC", "DataCriacao"]
colunas_base_sac_uso_feedback = ["ID_Uso_SAC", "Timestamp", "CNPJ_Cliente", "ID_SAC_Pergunta", "Feedback_Util"]
colunas_base_pesquisa_satisfacao_perguntas = ["ID_Pergunta_Satisfacao", "Texto_Pergunta", "Tipo_Pergunta", "Opcoes_Pergunta", "Ordem", "Ativa"]
colunas_base_pesquisa_satisfacao_respostas = ["ID_Resposta_Satisfacao", "ID_Diagnostico_Cliente", "ID_Pergunta_Satisfacao", "CNPJ_Cliente", "Timestamp_Resposta", "Resposta_Valor"]

def inicializar_csv(filepath, columns, defaults=None):
    try:
        dtype_spec = {}
        str_cols_map = {
            usuarios_csv: ['CNPJ'],
            usuarios_bloqueados_csv: ['CNPJ'],
            arquivo_csv: ['CNPJ', 'Data'], # Data (ID do diagnóstico) é string
            notificacoes_csv: ['CNPJ_Cliente', 'ID_Diagnostico_Relacionado'],
            sac_uso_feedback_csv: ['CNPJ_Cliente'],
            pesquisa_satisfacao_respostas_csv: ['CNPJ_Cliente', 'ID_Diagnostico_Cliente', 'ID_Pergunta_Satisfacao', 'Resposta_Valor']
        }
        if filepath in str_cols_map:
            for col_str in str_cols_map[filepath]:
                if col_str in columns: dtype_spec[col_str] = str

        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init = pd.DataFrame(columns=columns)
            if defaults:
                for col, default_val in defaults.items():
                    if col in columns: df_init[col] = default_val
            df_init.to_csv(filepath, index=False, encoding='utf-8')
        else:
            try:
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)
            except (ValueError, TypeError) as ve:
                st.warning(f"Problema ao ler {filepath} com dtypes ({ve}), tentando leitura genérica.")
                df_init = pd.read_csv(filepath, encoding='utf-8') # Fallback
            except Exception as read_e:
                st.error(f"Erro crítico ao ler {filepath}: {read_e}. Verifique o arquivo. App pode não funcionar.")
                return pd.DataFrame(columns=columns)

            made_changes = False
            current_df_cols = df_init.columns.tolist()
            for col_idx, col_name in enumerate(columns):
                if col_name not in current_df_cols:
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
    except Exception as e:
        st.error(f"Erro fatal na função inicializar_csv para {filepath}: {e}. A aplicação pode parar.")
        st.stop()

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios, defaults={"JaVisualizouInstrucoes": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False, "ID_Diagnostico_Relacionado": None})
    inicializar_csv(sac_perguntas_respostas_csv, colunas_base_sac_perguntas, defaults={"Categoria_SAC": "Geral", "DataCriacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    inicializar_csv(sac_uso_feedback_csv, colunas_base_sac_uso_feedback, defaults={"Feedback_Util": None})
    inicializar_csv(pesquisa_satisfacao_perguntas_csv, colunas_base_pesquisa_satisfacao_perguntas, defaults={"Ordem": 0, "Ativa": True, "Opcoes_Pergunta": None})
    inicializar_csv(pesquisa_satisfacao_respostas_csv, colunas_base_pesquisa_satisfacao_respostas)
except Exception as e_init:
    st.error(f"Falha crítica na inicialização de arquivos CSV: {e_init}. A aplicação pode não funcionar corretamente.")
    st.stop()

def registrar_acao(cnpj, acao, desc):
    try: hist_df = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ':str})
    except (FileNotFoundError, pd.errors.EmptyDataError): hist_df = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    new_entry = {"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": str(cnpj), "Ação": acao, "Descrição": desc}
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
            st.cache_data.clear() # Limpar cache de usuários se eles forem carregados com cache
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
            df['Feedback_Util'] = df['Feedback_Util'].astype(str).str.lower().map({'true': True, 'false': False, 'nan': pd.NA, 'none': pd.NA, '': pd.NA}).astype('boolean')
        else:
            df['Feedback_Util'] = pd.Series(dtype='boolean')
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_sac_uso_feedback)

@st.cache_data
def carregar_perguntas_satisfacao(apenas_ativas=True):
    try:
        df = pd.read_csv(pesquisa_satisfacao_perguntas_csv, encoding='utf-8')
        if df.empty: return pd.DataFrame(columns=colunas_base_pesquisa_satisfacao_perguntas)
        for col, default in [('Ativa', True), ('Ordem', 0), ('Opcoes_Pergunta', None)]:
            if col not in df.columns: df[col] = default
        df['Ativa'] = df['Ativa'].fillna(True).astype(bool)
        df['Ordem'] = pd.to_numeric(df['Ordem'], errors='coerce').fillna(0).astype(int)
        if apenas_ativas: df = df[df['Ativa'] == True]
        return df.sort_values(by="Ordem", ascending=True)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_pesquisa_satisfacao_perguntas)

@st.cache_data
def carregar_respostas_satisfacao(cnpj_cliente=None, id_diagnostico=None):
    try:
        df = pd.read_csv(pesquisa_satisfacao_respostas_csv, encoding='utf-8',
                         dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Cliente': str, 'ID_Pergunta_Satisfacao': str, 'Resposta_Valor':str})
        if cnpj_cliente: df = df[df['CNPJ_Cliente'] == str(cnpj_cliente)]
        if id_diagnostico: df = df[df['ID_Diagnostico_Cliente'] == str(id_diagnostico)]
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_pesquisa_satisfacao_respostas)

def verificar_pesquisa_satisfacao_pendente(cnpj_cliente, id_diagnostico_cliente):
    respostas_existentes = carregar_respostas_satisfacao(cnpj_cliente=cnpj_cliente, id_diagnostico=id_diagnostico_cliente)
    return respostas_existentes.empty

def obter_analise_para_resposta(pergunta_texto, resposta_valor, df_analises):
    if df_analises.empty: return None
    analises_da_pergunta = df_analises[df_analises['TextoPerguntaOriginal'] == pergunta_texto]
    if analises_da_pergunta.empty: return None
    default_analise = None
    for _, row_analise in analises_da_pergunta.iterrows():
        tipo_cond = row_analise.get('TipoCondicao'); analise_txt = row_analise.get('TextoAnalise')
        if pd.isna(tipo_cond) or pd.isna(analise_txt): continue
        if tipo_cond == 'Default': default_analise = analise_txt; continue
        try:
            if tipo_cond == 'FaixaNumerica':
                min_val=pd.to_numeric(row_analise.get('CondicaoValorMin'),errors='raise'); max_val=pd.to_numeric(row_analise.get('CondicaoValorMax'),errors='raise'); resp_num=pd.to_numeric(resposta_valor,errors='raise')
                if min_val <= resp_num <= max_val: return analise_txt
            elif tipo_cond == 'ValorExatoEscala':
                cond_exato = row_analise.get('CondicaoValorExato')
                if pd.notna(cond_exato) and str(resposta_valor).strip().lower() == str(cond_exato).strip().lower(): return analise_txt
            elif tipo_cond == 'ScoreGUT':
                min_s=pd.to_numeric(row_analise.get('CondicaoValorMin'),errors='raise'); max_s_raw=row_analise.get('CondicaoValorMax'); max_s=pd.to_numeric(max_s_raw,errors='coerce') if pd.notna(max_s_raw) else pd.NA; resp_s_gut=pd.to_numeric(resposta_valor,errors='raise')
                is_min = resp_s_gut >= min_s; is_max_ok = pd.isna(max_s) or (resp_s_gut <= max_s)
                if is_min and is_max_ok: return analise_txt
        except: continue
    return default_analise

def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df_diagnostico, respostas_coletadas, medias_cat, analises_df):
    try:
        with st.spinner("Gerando PDF do diagnóstico... Aguarde."):
            pdf = FPDF()
            pdf.add_page()
            empresa_nome = user_data.get("Empresa", "N/D"); cnpj_pdf = user_data.get("CNPJ", "N/D")
            logo_path = find_client_logo_path(cnpj_pdf)
            if logo_path:
                try: current_y = pdf.get_y(); pdf.image(logo_path, x=10, y=current_y, h=20); pdf.set_y(current_y + 20 + 5)
                except Exception as e_logo_pdf: st.warning(f"PDF: Logo não adicionado: {e_logo_pdf}")
            pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome}"), 0, 1, 'C'); pdf.ln(5)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 7, pdf_safe_text_output(f"ID/Data Diagnóstico: {diag_data.get('Data','N/D')} | Empresa: {empresa_nome} (CNPJ: {cnpj_pdf})"))
            if user_data.get("NomeContato"): pdf.multi_cell(0, 7, pdf_safe_text_output(f"Contato: {user_data.get('NomeContato')}"))
            if user_data.get("Telefone"): pdf.multi_cell(0, 7, pdf_safe_text_output(f"Telefone: {user_data.get('Telefone')}"))
            pdf.ln(3)
            mg_pdf = diag_data.get('Média Geral'); gut_pdf = diag_data.get('GUT Média')
            pdf.multi_cell(0, 7, pdf_safe_text_output(f"Média Geral: {mg_pdf:.2f if pd.notna(mg_pdf) else 'N/A'} | GUT Média: {gut_pdf:.2f if pd.notna(gut_pdf) else 'N/A'}")); pdf.ln(3)
            if medias_cat:
                pdf.set_font("Arial", 'B', 11); pdf.multi_cell(0, 7, pdf_safe_text_output("Médias por Categoria:"))
                pdf.set_font("Arial", size=10)
                for cat, media_val in medias_cat.items():
                    media_str = f"{media_val:.2f}" if isinstance(media_val, (int, float)) and pd.notna(media_val) else str(media_val)
                    pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat}: {media_str}"))
                pdf.ln(1); pdf.ln(5)
            for titulo, campo in [("Resumo (Cliente):", "Diagnóstico"), ("Análise (Cliente):", "Análise do Cliente"), ("Comentários (Consultor):", "Comentarios_Admin")]:
                valor = diag_data.get(campo, "")
                if valor and not pd.isna(valor) and str(valor).strip():
                    pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output(titulo))
                    pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(str(valor))); pdf.ln(3)
            pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 10, pdf_safe_text_output("Respostas Detalhadas e Análises:"))
            if perguntas_df_diagnostico.empty or not all(col in perguntas_df_diagnostico.columns for col in ["Pergunta", "Categoria"]):
                 pdf.set_font("Arial", 'I', 10); pdf.multi_cell(0, 7, pdf_safe_text_output("Perguntas do diagnóstico não disponíveis.")); pdf.ln(3)
            else:
                for categoria in perguntas_df_diagnostico["Categoria"].unique():
                    pdf.set_font("Arial", 'B', 10); pdf.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria}")); pdf.set_font("Arial", size=9)
                    for _, p_row in perguntas_df_diagnostico[perguntas_df_diagnostico["Categoria"] == categoria].iterrows():
                        p_texto = p_row["Pergunta"]; resp = respostas_coletadas.get(p_texto, diag_data.get(p_texto, "N/R")); analise_texto = None
                        if "[Matriz GUT]" in p_texto:
                            g,u,t,score=0,0,0,0
                            if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                            elif isinstance(resp, str) and resp.strip().startswith("{") and resp.strip().endswith("}"):
                                try: data_gut=json.loads(resp.replace("'",'"'));g,u,t=int(data_gut.get("G",0)),int(data_gut.get("U",0)),int(data_gut.get("T",0))
                                except: pass
                            score = g*u*t
                            pdf.multi_cell(0,6,pdf_safe_text_output(f"  - {p_texto.replace(' [Matriz GUT]','')}: G={g}, U={u}, T={t} (Score: {score})"))
                            analise_texto = obter_analise_para_resposta(p_texto, score, analises_df)
                        else:
                            pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {p_texto}: {resp}"))
                            analise_texto = obter_analise_para_resposta(p_texto, resp, analises_df)
                        if analise_texto: pdf.set_font("Arial", 'I', 8); pdf.set_text_color(100,100,100); pdf.multi_cell(0, 5, pdf_safe_text_output(f"    Análise: {analise_texto}")); pdf.set_text_color(0,0,0); pdf.set_font("Arial", size=9)
                    pdf.ln(2)
                pdf.ln(3)
            if not perguntas_df_diagnostico.empty:
                pdf.add_page(); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf.ln(5); pdf.set_font("Arial", size=10)
                gut_cards = []
                for _, p_row in perguntas_df_diagnostico.iterrows():
                    p_texto = p_row["Pergunta"]
                    if "[Matriz GUT]" in p_texto:
                        resp = respostas_coletadas.get(p_texto, diag_data.get(p_texto)); g,u,t,score=0,0,0,0
                        if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                        elif isinstance(resp, str) and resp.strip().startswith("{") and resp.strip().endswith("}"):
                            try:data_gut=json.loads(resp.replace("'",'"'));g,u,t=int(data_gut.get("G",0)),int(data_gut.get("U",0)),int(data_gut.get("T",0))
                            except: pass
                        score = g*u*t; prazo = "N/A"
                        if score >= 75: prazo = "15 dias"; elif score >= 40: prazo = "30 dias"; elif score >= 20: prazo = "45 dias"; elif score > 0: prazo = "60 dias"
                        else: continue
                        if prazo != "N/A": gut_cards.append({"Tarefa": p_texto.replace(" [Matriz GUT]", ""),"Prazo": prazo, "Score": score})
                if gut_cards:
                    for card in sorted(gut_cards, key=lambda x: (int(x["Prazo"].split(" ")[0]), -x["Score"])): pdf.multi_cell(0,6,pdf_safe_text_output(f"Prazo: {card['Prazo']} - Tarefa: {card['Tarefa']} (Score GUT: {card['Score']})"))
                else: pdf.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile: pdf_path = tmpfile.name; pdf.output(pdf_path)
        return pdf_path
    except Exception as e: st.error(f"Erro crítico ao gerar PDF: {e}"); return None

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): st.session_state.trigger_rerun_global = False; st.rerun()
if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v19_final")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.image("https://via.placeholder.com/200x80.png?text=Logo+do+Portal", width=200)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v19_final"):
        u = st.text_input("Usuário", key="admin_u_v19_final"); p = st.text_input("Senha", type="password", key="admin_p_v19_final")
        if st.form_submit_button("Entrar", use_container_width=True, icon="🔑"):
            try:
                df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                if not df_creds[(df_creds["Usuario"] == u) & (df_creds["Senha"] == p)].empty:
                    st.session_state.admin_logado = True; st.toast("Login de admin bem-sucedido!", icon="🎉"); st.rerun()
                else: st.error("Usuário/senha admin inválidos.")
            except Exception as e: st.error(f"Erro login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.image("https://via.placeholder.com/200x80.png?text=Logo+do+Portal", width=200)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_v19_final"):
        c = st.text_input("CNPJ", key="cli_c_v19_final", value=st.session_state.get("last_cnpj_input",""))
        s = st.text_input("Senha", type="password", key="cli_s_v19_final")
        if st.form_submit_button("Entrar", use_container_width=True, icon="👤"):
            st.session_state.last_cnpj_input = c
            try:
                users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                for col, default, dtype_func in [("JaVisualizouInstrucoes", "False", lambda x: str(x).lower() == 'true'),
                                                 ("DiagnosticosDisponiveis", 1, int),
                                                 ("TotalDiagnosticosRealizados", 0, int)]:
                    if col not in users_df.columns: users_df[col] = default
                    if dtype_func == int: users_df[col] = pd.to_numeric(users_df[col], errors='coerce').fillna(default).astype(int)
                    elif dtype_func == bool or (isinstance(default, str) and default.lower() in ['true', 'false']): users_df[col] = users_df[col].astype(str).str.lower().map({'true': True, 'false': False, 'nan':False,'none':False,'':False}).fillna(default.lower()=='true' if isinstance(default,str) else False)


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
                st.session_state.cliente_page = "Instruções" if not st.session_state.user["JaVisualizouInstrucoes"] else ("Novo Diagnóstico" if st.session_state.user["DiagnosticosDisponiveis"] > st.session_state.user["TotalDiagnosticosRealizados"] else "Painel Principal")
                st.session_state.id_formulario_atual = f"{st.session_state.cnpj}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                st.session_state.respostas_atuais_diagnostico = {}; st.session_state.progresso_diagnostico_percentual = 0; st.session_state.progresso_diagnostico_contagem = (0,0)
                st.session_state.feedbacks_respostas = {}; st.session_state.sac_feedback_registrado = {}
                st.session_state.diagnostico_enviado_sucesso = False; st.session_state.target_diag_data_for_expansion = None
                st.session_state.id_diagnostico_concluido_para_satisfacao = None; st.session_state.respostas_pesquisa_satisfacao_atual = {}; st.session_state.pesquisa_satisfacao_enviada = False
                st.toast("Login de cliente bem-sucedido!", icon="👋"); st.rerun()
            except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    if not st.session_state.user.get("JaVisualizouInstrucoes", False): st.session_state.cliente_page = "Instruções"
    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
    with st.sidebar.expander("👤 Meu Perfil", expanded=True):
        # ... (Código do perfil do cliente, igual ao anterior) ...
        pass
    # ... (Lógica do menu da sidebar do cliente, igual ao anterior) ...

    # Páginas do Cliente
    if st.session_state.cliente_page == "Instruções":
        st.subheader("📖 Instruções")
        # ... (código da página de Instruções, como antes) ...
        pass
    elif st.session_state.cliente_page == "SAC":
        st.subheader("❓ SAC - Perguntas Frequentes")
        # ... (código da página SAC, como antes) ...
        pass
    elif st.session_state.cliente_page == "Notificações":
        st.subheader("🔔 Notificações")
        # ... (código da página Notificações, como antes) ...
        pass
    elif st.session_state.cliente_page == "Painel Principal":
        st.subheader("🏠 Painel Principal")
        target_diag_to_expand = st.session_state.pop("target_diag_data_for_expansion", None)

        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu último diagnóstico foi enviado e processado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                try:
                    with open(st.session_state.pdf_gerado_path, "rb") as f_pdf:
                        st.download_button(label="Baixar PDF do Diagnóstico Recém-Enviado", data=f_pdf, file_name=st.session_state.pdf_gerado_filename, mime="application/pdf", key="dl_novo_diag_painel_final", icon="📄")
                    st.session_state.pdf_gerado_path = None; st.session_state.pdf_gerado_filename = None
                except Exception as e_pdf_dl: st.warning(f"Erro ao disponibilizar PDF: {e_pdf_dl}")

            if st.session_state.id_diagnostico_concluido_para_satisfacao and not st.session_state.pesquisa_satisfacao_enviada:
                id_diag_atual_satisfacao = st.session_state.id_diagnostico_concluido_para_satisfacao
                if verificar_pesquisa_satisfacao_pendente(st.session_state.cnpj, id_diag_atual_satisfacao):
                    st.markdown("---"); st.subheader("⭐ Pesquisa de Satisfação Rápida")
                    st.caption("Sua opinião é muito importante para nós!")
                    perguntas_satisfacao_df = carregar_perguntas_satisfacao(apenas_ativas=True)
                    if not perguntas_satisfacao_df.empty:
                         with st.form(key="form_pesquisa_satisfacao_cliente_final_submit"):
                            for idx_ps, row_ps in perguntas_satisfacao_df.iterrows():
                                p_id = row_ps["ID_Pergunta_Satisfacao"]; p_texto = row_ps["Texto_Pergunta"]; p_tipo = row_ps["Tipo_Pergunta"]; p_opcoes_str = row_ps.get("Opcoes_Pergunta")
                                widget_key_ps = f"satisfacao_{p_id}_final"
                                st.markdown(f"**{p_texto}**")
                                if p_tipo == "escala_1_5": st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.radio(" ", list(range(1, 6)), key=widget_key_ps, horizontal=True, label_visibility="collapsed")
                                elif p_tipo == "texto_aberto": st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.text_area(" ", key=widget_key_ps, label_visibility="collapsed")
                                elif p_tipo == "sim_nao": st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.radio(" ", ["Sim", "Não"], key=widget_key_ps, horizontal=True, label_visibility="collapsed")
                                elif p_tipo == "multipla_escolha_unica":
                                    opcoes_ps = []
                                    if pd.notna(p_opcoes_str):
                                        try: opcoes_ps = json.loads(p_opcoes_str).get("opcoes", [])
                                        except: st.warning(f"Opções mal formatadas para: {p_texto}")
                                    if opcoes_ps: st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.radio(" ", opcoes_ps, key=widget_key_ps, label_visibility="collapsed")
                                    else: st.caption(" (Opções não configuradas)")
                                st.write("") # Espaçamento
                            if st.form_submit_button("Enviar Feedback de Satisfação", use_container_width=True, icon="💖"):
                                respostas_finais_s = [{"ID_Resposta_Satisfacao": str(uuid.uuid4()), "ID_Diagnostico_Cliente": id_diag_atual_satisfacao, "ID_Pergunta_Satisfacao": pid, "CNPJ_Cliente": st.session_state.cnpj, "Timestamp_Resposta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Resposta_Valor": str(rval)} for pid, rval in st.session_state.respostas_pesquisa_satisfacao_atual.items() if rval is not None and str(rval).strip() != ""]
                                if respostas_finais_s:
                                    df_respostas_s_todas = carregar_respostas_satisfacao(); df_novas_s = pd.DataFrame(respostas_finais_s)
                                    df_respostas_s_upd = pd.concat([df_respostas_s_todas, df_novas_s], ignore_index=True)
                                    df_respostas_s_upd.to_csv(pesquisa_satisfacao_respostas_csv, index=False, encoding='utf-8')
                                    st.cache_data.clear(); st.session_state.pesquisa_satisfacao_enviada = True; st.session_state.respostas_pesquisa_satisfacao_atual = {}; st.success("Obrigado pelo seu feedback!"); time.sleep(1); st.rerun()
                                else: st.warning("Nenhuma resposta fornecida.")
                    else: st.info("Pesquisa de satisfação sem perguntas ativas.")
                elif not st.session_state.pesquisa_satisfacao_enviada and st.session_state.id_diagnostico_concluido_para_satisfacao:
                     st.success("Você já respondeu à pesquisa de satisfação para este diagnóstico. Obrigado!")
            st.session_state.diagnostico_enviado_sucesso = False

        df_cliente_diags_raw = pd.DataFrame()
        try:
            df_antigos_cliente = pd.read_csv(arquivo_csv, dtype={'CNPJ': str, 'Data': str}, encoding='utf-8')
            cols_num = ['Média Geral', 'GUT Média'] + [col for col in df_antigos_cliente.columns if col.startswith("Media_Cat_")]
            for col_n in cols_num:
                if col_n in df_antigos_cliente.columns: df_antigos_cliente[col_n] = pd.to_numeric(df_antigos_cliente[col_n], errors='coerce')
            df_cliente_diags_raw = df_antigos_cliente[df_antigos_cliente["CNPJ"] == st.session_state.cnpj].copy()
        except Exception as e: st.error(f"Erro ao carregar diagnósticos do cliente: {e}")

        if not df_cliente_diags_raw.empty:
            df_cliente_diags = df_cliente_diags_raw.sort_values(by="Data", ascending=False).reset_index(drop=True)
            # ... (Restante do código para exibir diagnósticos, gráficos, etc. no Painel Principal) ...
        else: st.info("Nenhum diagnóstico anterior encontrado para este cliente.")


    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.subheader("📋 Novo Diagnóstico")
        if st.session_state.diagnostico_enviado_sucesso: # Deve ter sido redirecionado, mas como fallback
            st.session_state.cliente_page = "Painel Principal"; st.rerun()

        try: perguntas_df_formulario = pd.read_csv(perguntas_csv, encoding='utf-8')
        except Exception as e: st.error(f"Erro ao carregar perguntas do formulário: {e}"); st.stop()
        if perguntas_df_formulario.empty: st.warning("Nenhuma pergunta de diagnóstico cadastrada."); st.stop()
        if "Categoria" not in perguntas_df_formulario.columns: perguntas_df_formulario["Categoria"] = "Geral"

        total_perguntas_form = len(perguntas_df_formulario)
        # ... (código do formulário de Novo Diagnóstico, incluindo calcular_e_mostrar_progresso_novo, on_change_resposta_novo) ...
        # DENTRO DO BOTÃO "Concluir e Enviar Diagnóstico"
        if st.button("Concluir e Enviar Diagnóstico", key="enviar_diag_final_cliente_v19_final_submit", icon="✔️", use_container_width=True):
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
                    num_resp_n = [v_n for k_n,v_n in respostas_finais_envio_novo.items() if not k_n.startswith("__") and isinstance(v_n,(int,float)) and ("[Matriz GUT]" not in k_n) and ("Pontuação" in k_n)] # Filtro para apenas pontuações
                    media_geral_n = round(sum(num_resp_n)/len(num_resp_n),2) if num_resp_n else 0.0
                    emp_nome_n = st.session_state.user.get("Empresa","N/D")
                    id_diagnostico_salvo = st.session_state.id_formulario_atual # ID único do diagnóstico

                    nova_linha_diag_final_n = {
                        "Data": str(id_diagnostico_salvo), "CNPJ": str(st.session_state.cnpj),
                        "Nome": str(st.session_state.user.get("NomeContato", st.session_state.cnpj)),
                        "Email": str(st.session_state.user.get("Email", "")), "Empresa": str(emp_nome_n),
                        "Média Geral": media_geral_n, "GUT Média": gut_media_n,
                        "Observações": str(respostas_finais_envio_novo.get("__obs_cliente__","")),
                        "Diagnóstico": str(respostas_finais_envio_novo.get("__resumo_cliente__","")),
                        "Análise do Cliente": str(respostas_finais_envio_novo.get("__obs_cliente__","")), # Pode ser diferente se houver campo específico
                        "Comentarios_Admin": ""
                    }
                    nova_linha_diag_final_n.update(respostas_csv_n)
                    medias_cat_final_n = {}
                    for cat_iter_n in perguntas_df_formulario["Categoria"].unique():
                        soma_c_n, cont_c_n = 0,0
                        for _,pr_n in perguntas_df_formulario[perguntas_df_formulario["Categoria"]==cat_iter_n].iterrows():
                            pt_n = pr_n["Pergunta"]; rv_n = respostas_finais_envio_novo.get(pt_n)
                            # Considerar apenas respostas numéricas para cálculo da média da categoria
                            if isinstance(rv_n,(int,float)) and ("[Matriz GUT]" not in pt_n) and ("Pontuação" in pt_n): # Se for pontuação numérica
                                soma_c_n+=rv_n; cont_c_n+=1
                            elif isinstance(rv_n, str) and "Escala" in pt_n: # Se for escala, mapear para número se necessário
                                map_escala_num = {"Muito Baixo": 1, "Baixo": 2, "Médio": 3, "Alto": 4, "Muito Alto": 5}
                                if rv_n in map_escala_num: soma_c_n+=map_escala_num[rv_n]; cont_c_n+=1
                        mc_n = round(soma_c_n/cont_c_n,2) if cont_c_n>0 else 0.0
                        nova_linha_diag_final_n[f"Media_Cat_{sanitize_column_name(cat_iter_n)}"] = mc_n
                        medias_cat_final_n[cat_iter_n] = mc_n
                    try:
                        df_todos_diags_n_leitura = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str, 'Data': str})
                    except (FileNotFoundError, pd.errors.EmptyDataError):
                        df_todos_diags_n_leitura = pd.DataFrame(columns=list(nova_linha_diag_final_n.keys()))
                    for col_add in nova_linha_diag_final_n.keys():
                        if col_add not in df_todos_diags_n_leitura.columns: df_todos_diags_n_leitura[col_add] = pd.NA
                    df_todos_diags_n_escrita = pd.concat([df_todos_diags_n_leitura, pd.DataFrame([nova_linha_diag_final_n])], ignore_index=True)
                    df_todos_diags_n_escrita.to_csv(arquivo_csv, index=False, encoding='utf-8')
                    st.cache_data.clear() # Limpa cache que possa ter o arquivo_csv antigo

                    total_realizados_atual = st.session_state.user.get("TotalDiagnosticosRealizados", 0)
                    update_user_data(st.session_state.cnpj, "TotalDiagnosticosRealizados", total_realizados_atual + 1)
                    registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", f"Cliente enviou novo diagnóstico (ID: {id_diagnostico_salvo}).")
                    analises_df_para_pdf_n = carregar_analises_perguntas() # Carrega para o PDF
                    perguntas_df_diagnostico_para_pdf = pd.read_csv(perguntas_csv, encoding='utf-8') # Carrega perguntas do diagnóstico para o PDF

                    pdf_path_gerado_n = gerar_pdf_diagnostico_completo(nova_linha_diag_final_n, st.session_state.user, perguntas_df_diagnostico_para_pdf, respostas_finais_envio_novo, medias_cat_final_n, analises_df_para_pdf_n)
                    st.session_state.diagnostico_enviado_sucesso = True
                    st.session_state.id_diagnostico_concluido_para_satisfacao = id_diagnostico_salvo
                    st.session_state.pesquisa_satisfacao_enviada = False
                    if pdf_path_gerado_n: st.session_state.pdf_gerado_path = pdf_path_gerado_n; st.session_state.pdf_gerado_filename = f"diagnostico_{sanitize_column_name(emp_nome_n)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.session_state.respostas_atuais_diagnostico = {}; st.session_state.progresso_diagnostico_percentual = 0; st.session_state.progresso_diagnostico_contagem = (0,total_perguntas_form); st.session_state.feedbacks_respostas = {}; st.session_state.sac_feedback_registrado = {}
                    st.session_state.cliente_page = "Painel Principal"; st.rerun()


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    # ... (Código da sidebar do admin, definição de menu_admin - como na resposta anterior) ...
    try: st.sidebar.image("https://via.placeholder.com/200x80.png?text=Logo+Admin", use_container_width=True)
    except: st.sidebar.caption("Logo admin não carregada")
    st.sidebar.success("🟢 Admin Logado")
    if st.sidebar.button("Sair do Painel Admin", icon="🚪", key="logout_admin_v19_final_recheck", use_container_width=True):
        st.session_state.admin_logado = False; st.toast("Logout de admin realizado.", icon="👋"); st.rerun()

    menu_admin_options_map = {
        "Visão Geral e Diagnósticos": "📊", "Relatório de Engajamento": "📈", "Gerenciar Notificações": "🔔",
        "Gerenciar Clientes": "👥", "Gerenciar Perguntas (Diagnóstico)": "📝", "Gerenciar Análises de Perguntas": "💡",
        "Gerenciar SAC": "📞", "⭐ Gerenciar Pesquisa de Satisfação": "⭐", "📊 Relatório Pesquisa de Satisfação": "📊",
        "Gerenciar Instruções": "⚙️", "Histórico de Usuários": "📜", "Gerenciar Administradores": "👮"
    }
    admin_page_text_keys = list(menu_admin_options_map.keys())
    admin_options_for_display = [f"{menu_admin_options_map[key]} {key}" for key in admin_page_text_keys]
    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_text_key_v19_final_recheck"
    WIDGET_KEY_SB_ADMIN_MENU = "sb_admin_menu_v19_final_recheck"

    def admin_menu_on_change(): # ... (função on_change como antes)
        pass
    if SESSION_KEY_FOR_ADMIN_PAGE not in st.session_state or st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE) not in admin_page_text_keys:
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]
    # ... (cálculo de current_admin_menu_index e selectbox como antes)
    # Definição de menu_admin (crucial)
    menu_admin = st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE, admin_page_text_keys[0])
    if menu_admin not in menu_admin_options_map: # Fallback se a chave for inválida
        menu_admin = admin_page_text_keys[0]
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = menu_admin

    st.header(f"{menu_admin_options_map.get(menu_admin, '❓')} {menu_admin}")
    # ... (Carregamento de df_usuarios_admin_geral como antes)

    if menu_admin == "Visão Geral e Diagnósticos":
        # ... (código da Visão Geral, garantindo que diagnosticos_df_admin_orig_view é carregado com 'Data' como str e 'Data_dt' como datetime)
        pass
    # ... (elif para todas as outras seções do admin, incluindo as novas de pesquisa de satisfação, como detalhado na resposta anterior) ...

# Fallback final
elif not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()