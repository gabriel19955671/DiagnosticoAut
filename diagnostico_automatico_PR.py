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
import plotly.graph_objects as go # Adicionado para mais controle
import uuid # Para IDs de análise e SAC

# !!! st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT !!!
st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", page_icon="📊")

# --- CSS Melhorado ---
st.markdown("""
<style>
body {
    font-family: 'Segoe UI', sans-serif;
    background-color: #f0f2f5; /* Um fundo global suave */
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
    transition: background-color 0.3s ease, transform 0.1s ease;
}
.stButton>button:hover {
    background-color: #1d4ed8;
    transform: translateY(-1px);
}
.stButton>button:active {
    transform: translateY(0px);
}
.stButton>button.secondary {
    background-color: #e5e7eb;
    color: #374151;
}
.stButton>button.secondary:hover {
    background-color: #d1d5db;
}
/* Botões de feedback SAC */
.sac-feedback-button button {
    background-color: #f0f0f0;
    color: #333;
    border: 1px solid #ccc;
    margin-right: 5px;
    padding: 0.3rem 0.8rem; /* Menor padding */
    font-size: 0.85em;
}
.sac-feedback-button button:hover {
    background-color: #e0e0e0;
}
.sac-feedback-button button.active-util { /* Estilo para botão "Útil" ativo */
    background-color: #28a745; /* Verde */
    color: white;
    border-color: #28a745;
}
.sac-feedback-button button.active-nao-util { /* Estilo para botão "Não Útil" ativo */
    background-color: #dc3545; /* Vermelho */
    color: white;
    border-color: #dc3545;
}


.stDownloadButton>button {
    background-color: #10b981;
    color: white;
    font-weight: 600;
    border-radius: 6px;
    margin-top: 10px;
    padding: 0.6rem 1.3rem;
    border: none;
    transition: background-color 0.3s ease, transform 0.1s ease;
}
.stDownloadButton>button:hover {
    background-color: #059669;
    transform: translateY(-1px);
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
    transition: background-color 0.3s ease, color 0.3s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    background-color: #eef2ff; /* Leve destaque no hover da aba não selecionada */
    color: #2563eb;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #2563eb;
    color: white;
}
.custom-card { /* Card genérico usado em vários lugares */
    border: 1px solid #e0e0e0;
    border-left: 5px solid #2563eb; /* Cor primária como destaque */
    padding: 20px;
    margin-bottom: 15px;
    border-radius: 8px;
    background-color: #ffffff;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07);
    transition: box-shadow 0.3s ease;
}
.custom-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.custom-card h4 {
    margin-top: 0;
    color: #2563eb;
    font-size: 1.1em;
    font-weight: 600;
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
    background-color: #eef2ff; /* Cor suave relacionada ao primário */
    border-left: 3px solid #6366f1; /* Cor de destaque complementar */
    padding: 10px;
    margin-top: 8px;
    margin-bottom:12px;
    border-radius: 4px;
}
[data-testid="stMetric"] {
    background-color: #ffffff;
    border-radius: 8px;
    padding: 15px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    border: 1px solid #e0e0e0;
    transition: box-shadow 0.3s ease;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
[data-testid="stMetricLabel"] {
    font-weight: 500;
    color: #4b5563;
    font-size: 0.95em; /* Ajuste fino */
}
[data-testid="stMetricValue"] {
    font-size: 2em; /* Ajuste fino */
    font-weight: 600;
    color: #1f2937;
}
[data-testid="stMetricDelta"] { /* Estilo para o delta, positivo e negativo */
    font-size: 0.9em;
    font-weight: 500;
}
.metric-delta-positive [data-testid="stMetricDelta"] svg {
    fill: #10b981 !important; /* Verde para positivo */
}
.metric-delta-negative [data-testid="stMetricDelta"] svg {
    fill: #ef4444 !important; /* Vermelho para negativo */
}
.metric-delta-neutral [data-testid="stMetricDelta"] {
    color: #6b7280 !important; /* Cinza para neutro */
}

.stExpander {
    border: 1px solid #e0e0e0 !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07) !important;
    margin-bottom: 15px !important;
    background-color: #ffffff; /* Fundo branco para expander */
}
.stExpander header {
    font-weight: 600 !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 15px !important;
    background-color: #f9fafb; /* Fundo do header do expander */
    border-bottom: 1px solid #e0e0e0;
}
.dashboard-item { /* Item genérico para dashboards */
    background-color: #ffffff;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    margin-bottom: 20px;
    border: 1px solid #e0e0e0;
    height: 100%; /* Para colunas de mesma altura */
    display: flex;
    flex-direction: column;
}
.dashboard-item h5 {
    margin-top: 0;
    margin-bottom: 15px;
    color: #2563eb;
    font-size: 1.1em;
    border-bottom: 1px solid #eee;
    padding-bottom: 8px;
}
/* Kanban Styles */
.kanban-board {
    display: flex;
    gap: 20px;
    overflow-x: auto; /* Para rolagem horizontal se muitas colunas */
    padding-bottom: 10px;
}
.kanban-column {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    min-width: 280px; /* Largura mínima da coluna */
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    border: 1px solid #e9ecef;
}
.kanban-column h4 {
    margin-top: 0;
    margin-bottom: 15px;
    font-size: 1.2em;
    color: #343a40;
    border-bottom: 2px solid #dee2e6;
    padding-bottom: 8px;
}
.kanban-card {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    padding: 12px 15px;
    margin-bottom: 10px;
    border-radius: 6px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s ease-in-out;
}
.kanban-card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.kanban-card-title {
    font-weight: 600;
    font-size: 0.95em;
    color: #2563eb; /* Cor primária para o título da tarefa */
    margin-bottom: 5px;
}
.kanban-card-score {
    font-size: 0.85em;
    color: #6c757d;
    margin-bottom: 3px;
}
.kanban-card-responsavel {
    font-size: 0.8em;
    font-style: italic;
    color: #868e96;
}
/* Cores de borda para Kanban baseado no prazo */
.kanban-card-prazo-15 { border-left: 5px solid #dc3545; } /* Vermelho - urgente */
.kanban-card-prazo-30 { border-left: 5px solid #fd7e14; } /* Laranja */
.kanban-card-prazo-45 { border-left: 5px solid #ffc107; } /* Amarelo */
.kanban-card-prazo-60 { border-left: 5px solid #28a745; } /* Verde */
</style>
""", unsafe_allow_html=True)

# --- Funções de Gráficos (com tooltips melhorados onde aplicável) ---
def create_radar_chart(data_dict, title="Radar Chart", color='#2563eb'):
    if not data_dict: return None
    categories = list(data_dict.keys())
    values = list(data_dict.values())
    if not categories or not values or len(categories) < 3 : return None

    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]

    df_radar = pd.DataFrame(dict(r=values_closed, theta=categories_closed))
    fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True, template="seaborn")
    fig.update_traces(
        fill='toself',
        line=dict(color=color),
        hovertemplate = '<b>%{theta}</b><br>Score: %{r:.2f}<extra></extra>'
    )
    fig.update_layout(
        title={'text': title, 'x':0.5, 'xanchor': 'center', 'font': {'size': 18, 'family': "Segoe UI, sans-serif"}},
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        font=dict(family="Segoe UI, sans-serif"),
        margin=dict(l=50, r=50, t=70, b=50)
    )
    return fig

def create_gut_barchart(gut_data_list, title="Top Prioridades (GUT)"):
    if not gut_data_list: return None
    df_gut = pd.DataFrame(gut_data_list)
    df_gut = df_gut.sort_values(by="Score", ascending=False).head(10)
    if df_gut.empty: return None
    fig = px.bar(df_gut, x="Score", y="Tarefa", title=title, orientation='h',
                 color="Score", color_continuous_scale=px.colors.sequential.Blues_r,
                 labels={'Tarefa':'Tarefa/Pergunta', 'Score':'Score GUT'},
                 height=min(600, 200 + len(df_gut)*35)) # Ajuste dinâmico de altura
    fig.update_traces(hovertemplate='<b>%{y}</b><br>Score GUT: %{x}<extra></extra>')
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        xaxis_title="Score GUT", yaxis_title="",
        font=dict(family="Segoe UI, sans-serif"),
        margin=dict(l=max(100, df_gut['Tarefa'].str.len().max()*5), r=20, t=70, b=50) # Margem esquerda dinâmica
    )
    return fig

def create_diagnostics_timeline_chart(df_diagnostics, title="Diagnósticos Realizados ao Longo do Tempo"):
    if df_diagnostics.empty or 'Data' not in df_diagnostics.columns: return None
    df_diag_copy = df_diagnostics.copy()
    # A coluna 'Data' agora é Data_dt nos dataframes processados pelo admin. Se não, converter.
    if 'Data_dt' in df_diag_copy.columns:
      df_diag_copy['Data_Converted'] = pd.to_datetime(df_diag_copy['Data_dt'], errors='coerce')
    else:
      df_diag_copy['Data_Converted'] = pd.to_datetime(df_diag_copy['Data'], errors='coerce')

    diag_counts_monthly = df_diag_copy.groupby(pd.Grouper(key='Data_Converted', freq='M')).size().reset_index(name='Contagem')
    diag_counts_monthly['Mês'] = diag_counts_monthly['Data_Converted'].dt.strftime('%Y-%m')
    if diag_counts_monthly.empty: return None
    fig = px.line(diag_counts_monthly, x='Mês', y='Contagem', title=title, markers=True,
                  labels={'Mês':'Mês', 'Contagem':'Nº de Diagnósticos'}, line_shape="spline")
    fig.update_traces(line=dict(color='#2563eb'), hovertemplate='<b>Mês: %{x}</b><br>Diagnósticos: %{y}<extra></extra>')
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
    avg_scores = pd.DataFrame(avg_scores_data).sort_values(by="Média_Score", ascending=True) # Ascending for better bar chart viz
    fig = px.bar(avg_scores, y='Categoria', x='Média_Score', title=title, orientation='h',
                 color='Média_Score', color_continuous_scale=px.colors.sequential.Blues, # Adjusted scale
                 labels={'Categoria':'Categoria', 'Média_Score':'Média do Score'})
    fig.update_traces(hovertemplate='<b>%{y}</b><br>Média: %{x:.2f}<extra></extra>')
    fig.update_layout(
        xaxis_title="Média do Score", yaxis_title="",
        font=dict(family="Segoe UI, sans-serif"),
        xaxis=dict(range=[0,5.5]),
        height=min(700, 200 + len(avg_scores)*30) # Ajuste dinâmico de altura
    )
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
    fig.update_traces(textposition='outside', textinfo='percent+label', hovertemplate='<b>%{label}</b><br>Clientes: %{value}<extra></extra>')
    fig.update_layout(font=dict(family="Segoe UI, sans-serif"), legend_title_text='Nível de Engajamento')
    return fig

# Nova função para gráfico de feedback do SAC
def create_sac_feedback_chart(df_sac_feedback, title="Feedback de Utilidade das Respostas do SAC"):
    if df_sac_feedback.empty or 'Feedback_Util' not in df_sac_feedback.columns:
        return None
    # Mapear booleano/string para texto legível
    df_sac_feedback_copy = df_sac_feedback.copy()
    df_sac_feedback_copy['Feedback_Display'] = df_sac_feedback_copy['Feedback_Util'].map({
        True: '👍 Útil', False: '👎 Não Útil', pd.NA: '➖ Sem Feedback', # Adicionado pd.NA
        'True': '👍 Útil', 'False': '👎 Não Útil', 'nan': '➖ Sem Feedback', # Para strings
        '': '➖ Sem Feedback'
    }).fillna('➖ Sem Feedback')


    feedback_counts = df_sac_feedback_copy['Feedback_Display'].value_counts().reset_index()
    feedback_counts.columns = ['Feedback', 'Contagem']

    if feedback_counts.empty:
        return None

    fig = px.bar(feedback_counts, x='Feedback', y='Contagem', title=title,
                 color='Feedback',
                 color_discrete_map={'👍 Útil': '#28a745', '👎 Não Útil': '#dc3545', '➖ Sem Feedback': '#6c757d'},
                 labels={'Feedback':'Tipo de Feedback', 'Contagem':'Número de Avaliações'})
    fig.update_traces(hovertemplate='<b>%{x}</b><br>Avaliações: %{y}<extra></extra>')
    fig.update_layout(font=dict(family="Segoe UI, sans-serif"), showlegend=False)
    return fig


# --- Configuração de Arquivos e Variáveis Globais (sem alteração) ---
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
LOGOS_DIR = "client_logos"

# --- Inicialização do Session State (sem alteração significativa) ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {}, "sac_feedback_registrado": {},
    "force_sidebar_rerun_after_notif_read_v19": False,
    "target_diag_data_for_expansion": None
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias (exceto gráficos) (sem alteração significativa) ---
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
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype={'CNPJ': str, 'CNPJ_Cliente': str} if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, sac_uso_feedback_csv] else None)
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
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype={'CNPJ': str, 'CNPJ_Cliente': str} if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, sac_uso_feedback_csv] else None)

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
        # Convert Feedback_Util to boolean, explicitly handling string 'True'/'False' and nan/empty
        if 'Feedback_Util' in df.columns:
            df['Feedback_Util'] = df['Feedback_Util'].astype(str).str.lower().map(
                {'true': True, 'false': False, 'nan': pd.NA, '': pd.NA, 'none': pd.NA}
            ).astype('boolean')
        else:
            df['Feedback_Util'] = pd.NA
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_sac_uso_feedback)

# --- obter_analise_para_resposta (sem alterações significativas) ---
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
            is_max_ok = pd.isna(max_s) or (pd.notna(resp_s_gut) and resp_s_gut <= max_s) # Max is optional
            if is_min and is_max_ok: return analise_txt
    return default_analise


# --- gerar_pdf_diagnostico_completo (sem alterações significativas na estrutura, mas usa pdf_safe_text) ---
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
                    pdf.set_y(current_y + max_h + 5) # Move below logo
                except Exception: pass # Non-critical if logo fails

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

# --- Lógica de Login e Navegação Principal (sem alterações significativas) ---
if st.session_state.get("trigger_rerun_global"): st.session_state.trigger_rerun_global = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v19")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    # st.image("https://via.placeholder.com/200x80.png?text=Logo+do+Portal", width=200) # Placeholder
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
    # st.image("https://via.placeholder.com/200x80.png?text=Logo+do+Portal", width=200) # Placeholder
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

                st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                st.session_state.respostas_atuais_diagnostico = {}
                st.session_state.progresso_diagnostico_percentual = 0
                st.session_state.progresso_diagnostico_contagem = (0,0)
                st.session_state.feedbacks_respostas = {}
                st.session_state.sac_feedback_registrado = {}
                st.session_state.diagnostico_enviado_sucesso = False
                st.session_state.target_diag_data_for_expansion = None

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
        if logo_cliente_path: st.image(logo_cliente_path, width=100, use_column_width='auto')
        st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
        st.write(f"**CNPJ:** {st.session_state.cnpj}")
        st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
        st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")

        total_slots = st.session_state.user.get('DiagnosticosDisponiveis', 0)
        realizados = st.session_state.user.get('TotalDiagnosticosRealizados', 0)
        restantes = max(0, total_slots - realizados)
        st.markdown(f"**Diagnósticos Contratados:** `{total_slots}`")
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
        notificacoes_label = f"🔔 Notificações ({notificacoes_nao_lidas_count} Nova(s)) ✨"

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
            if key_page == "Notificações": selected_page_cli_clean = "Notificações"
            elif key_page == "SAC": selected_page_cli_clean = "SAC"
            else: selected_page_cli_clean = key_page
            break

    if selected_page_cli_clean and selected_page_cli_clean != st.session_state.cliente_page :
        st.session_state.cliente_page = selected_page_cli_clean
        st.session_state.force_sidebar_rerun_after_notif_read_v19 = False
        st.session_state.target_diag_data_for_expansion = None
        st.rerun()

    if st.sidebar.button("⬅️ Sair do Portal Cliente", key="logout_cliente_v19", use_container_width=True):
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
            with open(instrucoes_custom_path, "r", encoding="utf-8") as f: instrucoes_content_md = f.read()
        elif os.path.exists(instrucoes_default_path):
            with open(instrucoes_default_path, "r", encoding="utf-8") as f: instrucoes_content_md = f.read()
            st.caption("ℹ️ Exibindo instruções padrão. O administrador pode personalizar este texto.")
        else:
            instrucoes_content_md = ("# Bem-vindo ao Portal de Diagnóstico!\n\nSiga as instruções para completar seu diagnóstico...")
            st.info("Instruções padrão não encontradas. Exibindo texto base.")
        st.markdown(f'<div class="custom-card" style="background-color: #fff; padding: 25px;">{instrucoes_content_md}</div>', unsafe_allow_html=True)
        if st.button("👍 Entendi, prosseguir", key="btn_instrucoes_v19"):
            update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", "True")
            if st.session_state.user: st.session_state.user["JaVisualizouInstrucoes"] = True
            pode_fazer_novo_inst = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo_inst else "Painel Principal"
            st.rerun()

    elif st.session_state.cliente_page == "SAC":
        st.subheader(menu_options_cli_map_full["SAC"])
        df_sac_qa = carregar_sac_perguntas_respostas()
        if df_sac_qa.empty: st.info("ℹ️ Nenhuma pergunta frequente cadastrada no momento.")
        else:
            df_sac_qa_sorted = df_sac_qa.sort_values(by=["Categoria_SAC", "Pergunta_SAC"])
            search_term_sac = st.text_input("🔎 Procurar nas Perguntas Frequentes:", key="search_sac_cliente_v2")
            if search_term_sac:
                df_sac_qa_sorted = df_sac_qa_sorted[
                    df_sac_qa_sorted["Pergunta_SAC"].str.contains(search_term_sac, case=False, na=False) |
                    df_sac_qa_sorted["Resposta_SAC"].str.contains(search_term_sac, case=False, na=False) |
                    df_sac_qa_sorted["Categoria_SAC"].str.contains(search_term_sac, case=False, na=False)
                ]
            if df_sac_qa_sorted.empty and search_term_sac: st.info(f"Nenhuma pergunta encontrada para '{search_term_sac}'.")

            categorias_sac = df_sac_qa_sorted["Categoria_SAC"].unique()
            for categoria in categorias_sac:
                st.markdown(f"#### {categoria}")
                perguntas_na_categoria = df_sac_qa_sorted[df_sac_qa_sorted["Categoria_SAC"] == categoria]
                for idx_sac, row_sac in perguntas_na_categoria.iterrows():
                    with st.expander(f"💬 {row_sac['Pergunta_SAC']}"):
                        st.markdown(row_sac['Resposta_SAC'], unsafe_allow_html=True)
                        feedback_key_base = f"sac_feedback_{row_sac['ID_SAC_Pergunta']}"
                        feedback_dado_bool = st.session_state.sac_feedback_registrado.get(row_sac['ID_SAC_Pergunta'])

                        cols_feedback = st.columns([1,1,8]) # Ajuste para melhor espaçamento
                        # Botão Útil
                        btn_class_util = "active-util" if feedback_dado_bool is True else ""
                        if cols_feedback[0].button("👍 Útil", key=f"{feedback_key_base}_util_v2", help="Esta resposta foi útil", use_container_width=True,
                                                type="secondary" if feedback_dado_bool is not True else "primary"): # type muda para o botão ativo
                            try:
                                df_feedback_sac = carregar_sac_uso_feedback() # Carrega o df atualizado
                                # Remove feedback anterior para a mesma pergunta e usuário, se houver
                                df_feedback_sac = df_feedback_sac[~((df_feedback_sac['CNPJ_Cliente'] == st.session_state.cnpj) & (df_feedback_sac['ID_SAC_Pergunta'] == row_sac['ID_SAC_Pergunta']))]
                                novo_feedback = pd.DataFrame([{"ID_Uso_SAC": str(uuid.uuid4()), "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                             "CNPJ_Cliente": st.session_state.cnpj, "ID_SAC_Pergunta": row_sac['ID_SAC_Pergunta'], "Feedback_Util": True}])
                                df_feedback_sac = pd.concat([df_feedback_sac, novo_feedback], ignore_index=True)
                                df_feedback_sac.to_csv(sac_uso_feedback_csv, index=False, encoding='utf-8')
                                st.session_state.sac_feedback_registrado[row_sac['ID_SAC_Pergunta']] = True
                                st.cache_data.clear() # Limpa cache para refletir
                                st.toast("Obrigado pelo seu feedback!", icon="😊"); st.rerun()
                            except Exception as e_fb: st.error(f"Erro ao registrar feedback: {e_fb}")
                        # Botão Não Útil
                        btn_class_nao_util = "active-nao-util" if feedback_dado_bool is False else ""
                        if cols_feedback[1].button("👎 Não útil", key=f"{feedback_key_base}_nao_util_v2", help="Esta resposta não foi útil", use_container_width=True,
                                                  type="secondary" if feedback_dado_bool is not False else "primary"):
                            try:
                                df_feedback_sac = carregar_sac_uso_feedback()
                                df_feedback_sac = df_feedback_sac[~((df_feedback_sac['CNPJ_Cliente'] == st.session_state.cnpj) & (df_feedback_sac['ID_SAC_Pergunta'] == row_sac['ID_SAC_Pergunta']))]
                                novo_feedback = pd.DataFrame([{"ID_Uso_SAC": str(uuid.uuid4()), "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                             "CNPJ_Cliente": st.session_state.cnpj, "ID_SAC_Pergunta": row_sac['ID_SAC_Pergunta'], "Feedback_Util": False}])
                                df_feedback_sac = pd.concat([df_feedback_sac, novo_feedback], ignore_index=True)
                                df_feedback_sac.to_csv(sac_uso_feedback_csv, index=False, encoding='utf-8')
                                st.session_state.sac_feedback_registrado[row_sac['ID_SAC_Pergunta']] = False
                                st.cache_data.clear()
                                st.toast("Obrigado pelo seu feedback! Vamos melhorar.", icon="🛠️"); st.rerun()
                            except Exception as e_fb: st.error(f"Erro ao registrar feedback: {e_fb}")

                        if feedback_dado_bool is not None:
                            with cols_feedback[2]:
                                feedback_text = "'Útil'" if feedback_dado_bool else "'Não útil'"
                                st.markdown(f"<small style='margin-left:10px; padding-top:8px; display:inline-block;'>Feedback: {feedback_text}</small>", unsafe_allow_html=True)
                st.markdown("---")

    elif st.session_state.cliente_page == "Notificações":
        # ... (Seção de notificações, sem grandes alterações visuais além do custom-card) ...
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

            minhas_notificacoes = df_notificacoes_todas[df_notificacoes_todas["CNPJ_Cliente"] == st.session_state.cnpj].sort_values(by="Timestamp", ascending=False)

            if minhas_notificacoes.empty:
                st.info("Você não tem nenhuma notificação no momento.")
            else:
                st.caption("As notificações novas são marcadas como lidas ao serem exibidas nesta página.")
                for idx_notif, row_notif in minhas_notificacoes.iterrows():
                    cor_borda = "#2563eb" if not row_notif["Lida"] else "#adb5bd"
                    icon_lida = "✉️ Nova:" if not row_notif["Lida"] else "📨 Lida:"
                    st.markdown(f"""
                    <div class="custom-card" style="border-left: 5px solid {cor_borda}; margin-bottom: 10px;">
                        <p style="font-size: 0.8em; color: #6b7280;">{icon_lida} {row_notif["Timestamp"]}</p>
                        <p>{row_notif["Mensagem"]}</p>
                    </div>""", unsafe_allow_html=True)
                    diag_id_relacionado = row_notif.get("ID_Diagnostico_Relacionado")
                    if pd.notna(diag_id_relacionado) and str(diag_id_relacionado).strip():
                        if st.button("🔎 Ver Detalhes no Painel", key=f"ver_det_notif_{row_notif['ID_Notificacao']}_{idx_notif}", help="Ir para o diagnóstico mencionado"):
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
        st.subheader(f'{menu_options_cli_map_full["Painel Principal"]} dashboard-icon') # Adicionar ícone
        target_diag_to_expand = st.session_state.pop("target_diag_data_for_expansion", None)

        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu último diagnóstico foi enviado e processado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                with open(st.session_state.pdf_gerado_path, "rb") as f_pdf:
                    st.download_button(label="📄 Baixar PDF do Diagnóstico Recém-Enviado", data=f_pdf, file_name=st.session_state.pdf_gerado_filename, mime="application/pdf", key="dl_novo_diag_painel_v19")
                st.session_state.pdf_gerado_path = None; st.session_state.pdf_gerado_filename = None
            st.session_state.diagnostico_enviado_sucesso = False

        try:
            df_antigos = pd.read_csv(arquivo_csv, dtype={'CNPJ': str}, encoding='utf-8')
            df_cliente_diags_raw = df_antigos[df_antigos["CNPJ"] == st.session_state.cnpj]
            if 'Data' in df_cliente_diags_raw.columns:
                df_cliente_diags_raw['Data_dt'] = pd.to_datetime(df_cliente_diags_raw['Data'], errors='coerce')
                df_cliente_diags_raw = df_cliente_diags_raw.sort_values(by="Data_dt", ascending=False)
        except FileNotFoundError:
            st.error(f"Arquivo de diagnósticos '{arquivo_csv}' não encontrado."); df_cliente_diags_raw = pd.DataFrame()
        except Exception as e_load_diag:
            st.error(f"Erro ao carregar diagnósticos: {e_load_diag}"); df_cliente_diags_raw = pd.DataFrame()

        if not df_cliente_diags_raw.empty:
            latest_diag_data = df_cliente_diags_raw.iloc[0].to_dict()
            previous_diag_data = df_cliente_diags_raw.iloc[1].to_dict() if len(df_cliente_diags_raw) > 1 else None

            st.markdown("#### 📊 Visão Geral do Último Diagnóstico")
            col_metric1, col_metric2 = st.columns(2)
            mg_latest = pd.to_numeric(latest_diag_data.get("Média Geral"), errors='coerce')
            gut_latest = pd.to_numeric(latest_diag_data.get("GUT Média"), errors='coerce')
            delta_mg_css_class = "metric-delta-neutral"
            delta_gut_css_class = "metric-delta-neutral"

            if previous_diag_data:
                mg_previous = pd.to_numeric(previous_diag_data.get("Média Geral"), errors='coerce')
                gut_previous = pd.to_numeric(previous_diag_data.get("GUT Média"), errors='coerce')
                delta_mg = mg_latest - mg_previous if pd.notna(mg_latest) and pd.notna(mg_previous) else None
                delta_gut = gut_latest - gut_previous if pd.notna(gut_latest) and pd.notna(gut_previous) else None
                if delta_mg is not None: delta_mg_css_class = "metric-delta-positive" if delta_mg > 0 else ("metric-delta-negative" if delta_mg < 0 else "metric-delta-neutral")
                if delta_gut is not None: delta_gut_css_class = "metric-delta-positive" if delta_gut > 0 else ("metric-delta-negative" if delta_gut < 0 else "metric-delta-neutral")

                with col_metric1:
                    st.markdown(f'<div class="{delta_mg_css_class}">', unsafe_allow_html=True)
                    st.metric("Média Geral (Último)", f"{mg_latest:.2f}" if pd.notna(mg_latest) else "N/A",
                              delta=f"{delta_mg:.2f}" if delta_mg is not None else None, help="Comparado ao diagnóstico anterior")
                    st.markdown('</div>', unsafe_allow_html=True)
                with col_metric2:
                    st.markdown(f'<div class="{delta_gut_css_class}">', unsafe_allow_html=True)
                    st.metric("GUT Média (Último)", f"{gut_latest:.2f}" if pd.notna(gut_latest) else "N/A",
                              delta=f"{delta_gut:.2f}" if delta_gut is not None else None, help="Comparado ao diagnóstico anterior")
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                col_metric1.metric("Média Geral (Último)", f"{mg_latest:.2f}" if pd.notna(mg_latest) else "N/A")
                col_metric2.metric("GUT Média (Último)", f"{gut_latest:.2f}" if pd.notna(gut_latest) else "N/A")

            st.markdown("---")
            col_graph1, col_graph2 = st.columns(2)
            with col_graph1:
                st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
                st.markdown("<h5>Scores por Categoria (Último)</h5>", unsafe_allow_html=True)
                medias_cat_latest = {k.replace("Media_Cat_", "").replace("_", " "): pd.to_numeric(v, errors='coerce')
                                     for k, v in latest_diag_data.items() if k.startswith("Media_Cat_") and pd.notna(pd.to_numeric(v, errors='coerce'))}
                if medias_cat_latest:
                    fig_radar = create_radar_chart(medias_cat_latest, title="")
                    if fig_radar: st.plotly_chart(fig_radar, use_container_width=True)
                    else: st.caption("Não foi possível gerar o gráfico de radar.")
                else: st.caption("Sem dados de média por categoria para o último diagnóstico.")
                st.markdown('</div>', unsafe_allow_html=True)

            with col_graph2:
                st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
                st.markdown("<h5>Top Prioridades GUT (Último)</h5>", unsafe_allow_html=True)
                # ... (lógica GUT barchart como antes) ...
                gut_data_list_client = []
                for pergunta_key, resp_val_str in latest_diag_data.items():
                    if isinstance(pergunta_key, str) and "[Matriz GUT]" in pergunta_key:
                        try:
                            if pd.notna(resp_val_str) and isinstance(resp_val_str, str):
                                gut_data = json.loads(resp_val_str.replace("'", "\""))
                                g, u, t_val = int(gut_data.get("G", 0)), int(gut_data.get("U", 0)), int(gut_data.get("T", 0))
                                score = g * u * t_val
                                if score > 0:
                                    gut_data_list_client.append({"Tarefa": pergunta_key.replace(" [Matriz GUT]", ""), "Score": score})
                        except: pass
                if gut_data_list_client:
                    fig_gut_bar = create_gut_barchart(gut_data_list_client, title="")
                    if fig_gut_bar: st.plotly_chart(fig_gut_bar, use_container_width=True)
                    else: st.caption("Não foi possível gerar gráfico de prioridades GUT.")
                else: st.caption("Nenhuma prioridade GUT identificada no último diagnóstico.")
                st.markdown('</div>', unsafe_allow_html=True)
            st.divider()

            # PLANO DE AÇÃO KANBAN VISUAL
            st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
            latest_diag_kanban = latest_diag_data # Já é o último
            gut_cards_kanban_data = {} # Dicionário para agrupar por prazo

            for pergunta_k, resposta_k_str in latest_diag_kanban.items():
                if isinstance(pergunta_k, str) and "[Matriz GUT]" in pergunta_k:
                    try:
                        if pd.notna(resposta_k_str) and isinstance(resposta_k_str, str):
                            gut_data_k = json.loads(resposta_k_str.replace("'", "\""))
                            g_k, u_k, t_k = int(gut_data_k.get("G",0)), int(gut_data_k.get("U",0)), int(gut_data_k.get("T",0))
                            score_gut_k = g_k * u_k * t_k
                            prazo_k, prazo_css_class = "N/A", ""
                            if score_gut_k >= 75: prazo_k, prazo_css_class = "🎯 15 dias", "kanban-card-prazo-15"
                            elif score_gut_k >= 40: prazo_k, prazo_css_class = "⏳ 30 dias", "kanban-card-prazo-30"
                            elif score_gut_k >= 20: prazo_k, prazo_css_class = "🗓️ 45 dias", "kanban-card-prazo-45"
                            elif score_gut_k > 0: prazo_k, prazo_css_class = "🐌 60 dias", "kanban-card-prazo-60"
                            else: continue

                            if prazo_k != "N/A":
                                if prazo_k not in gut_cards_kanban_data: gut_cards_kanban_data[prazo_k] = []
                                gut_cards_kanban_data[prazo_k].append({
                                    "Tarefa": pergunta_k.replace(" [Matriz GUT]", ""), "Score": score_gut_k,
                                    "Responsavel": st.session_state.user.get("Empresa", "N/D"),
                                    "css_class": prazo_css_class
                                })
                    except: pass

            if gut_cards_kanban_data:
                prazos_ordenados = sorted(gut_cards_kanban_data.keys(), key=lambda x: int(x.split(" ")[1])) # Ordenar por número de dias
                st.markdown('<div class="kanban-board">', unsafe_allow_html=True)
                for prazo_col in prazos_ordenados:
                    st.markdown(f'<div class="kanban-column"><h4>{prazo_col}</h4>', unsafe_allow_html=True)
                    # Ordenar cards dentro da coluna por Score (maior primeiro)
                    cards_na_coluna = sorted(gut_cards_kanban_data[prazo_col], key=lambda x: x["Score"], reverse=True)
                    for card_item in cards_na_coluna:
                        st.markdown(f"""
                        <div class="kanban-card {card_item['css_class']}">
                            <div class="kanban-card-title">{card_item['Tarefa']}</div>
                            <div class="kanban-card-score">Score GUT: {card_item['Score']}</div>
                            <div class="kanban-card-responsavel">👤 {card_item['Responsavel']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True) # Fecha kanban-column
                st.markdown('</div>', unsafe_allow_html=True) # Fecha kanban-board
            else:
                st.info("ℹ️ Nenhuma ação prioritária (GUT > 0) identificada no último diagnóstico para o Kanban.")
            st.divider()


            st.markdown("#### 📁 Diagnósticos Anteriores")
            # ... (lógica de expander para diagnósticos anteriores como antes) ...
            # (Aprimoramento: dentro do expander, usar st.columns para melhor layout dos detalhes)
            try:
                perguntas_df_para_painel = pd.read_csv(perguntas_csv, encoding='utf-8')
                if "Categoria" not in perguntas_df_para_painel.columns: perguntas_df_para_painel["Categoria"] = "Geral"
            except FileNotFoundError: perguntas_df_para_painel = pd.DataFrame()
            analises_df_para_painel = carregar_analises_perguntas()

            for idx_row_diag, row_diag_data_series in df_cliente_diags_raw.iterrows():
                row_diag_data = row_diag_data_series.to_dict()
                expand_this_diag = (str(row_diag_data.get('Data_dt')) == str(target_diag_to_expand)) or \
                                   (str(row_diag_data.get('Data')) == str(target_diag_to_expand)) # Compatibilidade
                with st.expander(f"📅 {row_diag_data.get('Data','N/D')} - {row_diag_data.get('Empresa','N/D')}", expanded=expand_this_diag):
                    # ... (conteúdo do expander como antes, talvez com melhorias de layout se desejar) ...
                    st.markdown('<div class="custom-card" style="padding-top: 10px; padding-bottom: 10px;">', unsafe_allow_html=True)
                    cols_metricas_exp = st.columns(2)
                    cols_metricas_exp[0].metric("Média Geral", f"{pd.to_numeric(row_diag_data.get('Média Geral'), errors='coerce'):.2f}" if pd.notna(row_diag_data.get('Média Geral')) else "N/A")
                    cols_metricas_exp[1].metric("GUT Média", f"{pd.to_numeric(row_diag_data.get('GUT Média'), errors='coerce'):.2f}" if pd.notna(row_diag_data.get('GUT Média')) else "N/A")
                    st.write(f"**Resumo (Cliente):** {row_diag_data.get('Diagnóstico', 'N/P')}")
                    # ... (Resto do conteúdo do expander)
                    st.markdown('</div>', unsafe_allow_html=True)


            st.subheader("📈 Comparativo de Evolução das Médias")
            if len(df_cliente_diags_raw) > 1:
                # ... (Lógica do gráfico de linha como antes) ...
                df_evolucao = df_cliente_diags_raw.copy().sort_values(by="Data_dt", ascending=True)
                cols_plot_evol = ['Média Geral', 'GUT Média'] # Principais
                for col_ev in df_evolucao.columns:
                    if str(col_ev).startswith("Media_Cat_"):
                        df_evolucao[col_ev] = pd.to_numeric(df_evolucao[col_ev], errors='coerce')
                        if not df_evolucao[col_ev].isnull().all(): cols_plot_evol.append(col_ev)
                df_evolucao_plot = df_evolucao.set_index("Data_dt")[cols_plot_evol].dropna(axis=1, how='all')
                if not df_evolucao_plot.empty:
                    rename_map = {col: col.replace("Media_Cat_", "Média ").replace("_", " ") for col in df_evolucao_plot.columns}
                    df_evolucao_plot_renamed = df_evolucao_plot.rename(columns=rename_map)
                    st.line_chart(df_evolucao_plot_renamed)
                else: st.info("Não há dados suficientes para gráfico de evolução.")
            else: st.info("São necessários pelo menos dois diagnósticos para exibir o comparativo de evolução.")
            st.divider()

            st.subheader("📊 Comparação Detalhada Entre Dois Diagnósticos")
            if len(df_cliente_diags_raw) > 1:
                datas_opts_comp = df_cliente_diags_raw["Data"].astype(str).tolist() # Usa a Data original string para seleção
                idx_atual_comp = 0
                idx_anterior_comp = 1 if len(datas_opts_comp) > 1 else 0

                col_comp1, col_comp2 = st.columns(2)
                diag1_data_str_sel = col_comp1.selectbox("Diagnóstico 1 (Mais Recente):", datas_opts_comp, index=idx_atual_comp, key="comp_diag1_sel_v20")
                diag2_data_str_sel = col_comp2.selectbox("Diagnóstico 2 (Anterior):", datas_opts_comp, index=idx_anterior_comp, key="comp_diag2_sel_v20")

                if diag1_data_str_sel and diag2_data_str_sel and diag1_data_str_sel != diag2_data_str_sel:
                    diag1_comp_data = df_cliente_diags_raw[df_cliente_diags_raw["Data"] == diag1_data_str_sel].iloc[0]
                    diag2_comp_data = df_cliente_diags_raw[df_cliente_diags_raw["Data"] == diag2_data_str_sel].iloc[0]

                    # Gráficos Radar Comparativos
                    st.markdown(f"#### Comparativo Scores por Categoria: `{diag1_data_str_sel}` vs `{diag2_data_str_sel}`")
                    radar_col1, radar_col2 = st.columns(2)
                    medias_cat_d1 = {k.replace("Media_Cat_", "").replace("_"," "): pd.to_numeric(v, errors='coerce') for k,v in diag1_comp_data.items() if k.startswith("Media_Cat_") and pd.notna(pd.to_numeric(v, errors='coerce'))}
                    medias_cat_d2 = {k.replace("Media_Cat_", "").replace("_"," "): pd.to_numeric(v, errors='coerce') for k,v in diag2_comp_data.items() if k.startswith("Media_Cat_") and pd.notna(pd.to_numeric(v, errors='coerce'))}

                    with radar_col1:
                        if medias_cat_d1:
                            fig_r1 = create_radar_chart(medias_cat_d1, title=f"Diag. {diag1_data_str_sel.split(' ')[0]}", color="#2563eb") # Primário
                            if fig_r1: st.plotly_chart(fig_r1, use_container_width=True)
                        else: st.caption(f"Sem dados de categoria para {diag1_data_str_sel}")
                    with radar_col2:
                        if medias_cat_d2:
                            fig_r2 = create_radar_chart(medias_cat_d2, title=f"Diag. {diag2_data_str_sel.split(' ')[0]}", color="#fd7e14") # Laranja
                            if fig_r2: st.plotly_chart(fig_r2, use_container_width=True)
                        else: st.caption(f"Sem dados de categoria para {diag2_data_str_sel}")
                    # Tabela de Métricas como antes
                    # ...
                elif diag1_data_str_sel == diag2_data_str_sel: st.warning("Selecione dois diagnósticos diferentes.")
            else: st.info("São necessários pelo menos dois diagnósticos para comparação.")
        else:
            st.info("ℹ️ Nenhum diagnóstico encontrado para este cliente.")
        # ... (resto da página do cliente)

    elif st.session_state.cliente_page == "Novo Diagnóstico":
        # ... (Seção Novo Diagnóstico - sem grandes alterações visuais além das globais) ...
        st.subheader(menu_options_cli_map_full["Novo Diagnóstico"])

        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu diagnóstico foi enviado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                with open(st.session_state.pdf_gerado_path, "rb") as f_pdf_dl_sucesso:
                    st.download_button(label="📄 Baixar PDF do Diagnóstico Enviado", data=f_pdf_dl_sucesso, file_name=st.session_state.pdf_gerado_filename, mime="application/pdf", key="dl_pdf_sucesso_novo_diag_v19")
            if st.button("🏠 Ir para o Painel Principal", key="ir_painel_apos_envio_sucesso_v19"):
                st.session_state.cliente_page = "Painel Principal"
                st.session_state.diagnostico_enviado_sucesso = False; st.session_state.pdf_gerado_path = None; st.session_state.pdf_gerado_filename = None
                st.rerun()
            st.stop()
        # ... (Restante da lógica do formulário Novo Diagnóstico) ...

# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    try:
        # st.sidebar.image("https://via.placeholder.com/200x80.png?text=Logo+Admin", use_container_width=True) # Placeholder
        st.sidebar.markdown("## ⚙️ Painel Admin")
    except Exception as e_img_admin: st.sidebar.caption(f"Logo admin não carregada: {e_img_admin}")

    st.sidebar.success("🟢 Admin Logado")

    if st.sidebar.button("🚪 Sair do Painel Admin", key="logout_admin_v19", use_container_width=True):
        st.session_state.admin_logado = False
        st.toast("Logout de admin realizado.", icon="👋")
        st.rerun()

    menu_admin_options_map = {
        "Visão Geral e Diagnósticos": "📊", "Relatório de Engajamento": "📈",
        "Gerenciar Notificações": "🔔", "Gerenciar Clientes": "👥",
        "Gerenciar Perguntas": "📝", "Gerenciar Análises de Perguntas": "💡",
        "Gerenciar SAC": "📞", "Gerenciar Instruções": "⚙️",
        "Histórico de Usuários": "📜", "Gerenciar Administradores": "👮"
    }
    # ... (lógica do menu admin como antes) ...
    admin_page_text_keys = list(menu_admin_options_map.keys())
    admin_options_for_display = [f"{menu_admin_options_map[key]} {key}" for key in admin_page_text_keys]
    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_text_key_v19"
    WIDGET_KEY_SB_ADMIN_MENU = "sb_admin_menu_v19"
    def admin_menu_on_change(): # Callback para atualizar a página
        selected_display_value = st.session_state[WIDGET_KEY_SB_ADMIN_MENU]
        new_text_key = None
        for text_key, emoji in menu_admin_options_map.items():
            if f"{emoji} {text_key}" == selected_display_value: new_text_key = text_key; break
        if new_text_key and new_text_key != st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE):
            st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = new_text_key
    if SESSION_KEY_FOR_ADMIN_PAGE not in st.session_state or st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] not in admin_page_text_keys:
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]
    current_admin_page_text_key_for_index = st.session_state[SESSION_KEY_FOR_ADMIN_PAGE]
    try:
        expected_display_value_for_current_page = f"{menu_admin_options_map[current_admin_page_text_key_for_index]} {current_admin_page_text_key_for_index}"
        current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
    except (ValueError, KeyError): current_admin_menu_index = 0; st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]
    st.sidebar.selectbox("Funcionalidades Admin:", options=admin_options_for_display, index=current_admin_menu_index, key=WIDGET_KEY_SB_ADMIN_MENU, on_change=admin_menu_on_change)
    menu_admin = st.session_state[SESSION_KEY_FOR_ADMIN_PAGE]
    header_display_name = f"{menu_admin_options_map[menu_admin]} {menu_admin}"
    st.header(header_display_name)

    df_usuarios_admin_geral = pd.DataFrame(columns=colunas_base_usuarios)
    try:
        # ... (lógica de carregamento e tratamento de df_usuarios_admin_geral) ...
        df_usuarios_admin_temp_load = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
        if "DiagnosticosDisponiveis" not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load["DiagnosticosDisponiveis"] = 1
        df_usuarios_admin_temp_load["DiagnosticosDisponiveis"] = pd.to_numeric(df_usuarios_admin_temp_load["DiagnosticosDisponiveis"], errors='coerce').fillna(1).astype(int)
        if "TotalDiagnosticosRealizados" not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load["TotalDiagnosticosRealizados"] = 0
        df_usuarios_admin_temp_load["TotalDiagnosticosRealizados"] = pd.to_numeric(df_usuarios_admin_temp_load["TotalDiagnosticosRealizados"], errors='coerce').fillna(0).astype(int)
        if "JaVisualizouInstrucoes" not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load["JaVisualizouInstrucoes"] = "False"
        df_usuarios_admin_temp_load["JaVisualizouInstrucoes"] = df_usuarios_admin_temp_load["JaVisualizouInstrucoes"].astype(str).str.lower().map({'true': True, 'false': False, 'nan':False, '':False}).fillna(False)
        df_usuarios_admin_geral = df_usuarios_admin_temp_load
    except: pass # Simplificado para brevidade

    if menu_admin == "Visão Geral e Diagnósticos":
        # ... (Lógica de carregamento de diagnosticos_df_admin_orig_view como antes) ...
        admin_data_carregada_view_sucesso = False
        diagnosticos_df_admin_orig_view = pd.DataFrame()
        if os.path.exists(arquivo_csv) and os.path.getsize(arquivo_csv) > 0:
            try:
                diagnosticos_df_admin_orig_view = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                if 'Data' in diagnosticos_df_admin_orig_view.columns:
                    diagnosticos_df_admin_orig_view['Data_dt'] = pd.to_datetime(diagnosticos_df_admin_orig_view['Data'], errors='coerce')
                    diagnosticos_df_admin_orig_view['Data'] = diagnosticos_df_admin_orig_view['Data'].astype(str)
                if not diagnosticos_df_admin_orig_view.empty: admin_data_carregada_view_sucesso = True
            except: pass # Simplificado

        st.markdown("####  KPIs Gerais do Sistema")
        # ... (KPIs como antes) ...
        kpi_cols_v19 = st.columns(3)
        total_clientes_cadastrados_vg = len(df_usuarios_admin_geral) if not df_usuarios_admin_geral.empty else 0
        kpi_cols_v19[0].metric("👥 Clientes Cadastrados", total_clientes_cadastrados_vg)
        if admin_data_carregada_view_sucesso:
            total_diagnosticos_sistema_vg = len(diagnosticos_df_admin_orig_view)
            kpi_cols_v19[1].metric("📋 Diagnósticos Realizados", total_diagnosticos_sistema_vg)
            avg_geral_sistema = pd.to_numeric(diagnosticos_df_admin_orig_view.get("Média Geral"), errors='coerce').mean()
            kpi_cols_v19[2].metric("📈 Média Geral (Sistema)", f"{avg_geral_sistema:.2f}" if pd.notna(avg_geral_sistema) else "N/A")
        else:
            kpi_cols_v19[1].metric("📋 Diagnósticos Realizados", 0); kpi_cols_v19[2].metric("📈 Média Geral (Sistema)", "N/A")

        st.divider()
        # ... (Gráficos de admin como antes, dentro de .dashboard-item) ...
        st.markdown("#### Análises Gráficas do Sistema")
        dash_cols1_v19 = st.columns(2)
        with dash_cols1_v19[0]:
            st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
            st.markdown("<h5>Diagnósticos ao Longo do Tempo</h5>", unsafe_allow_html=True)
            if admin_data_carregada_view_sucesso and 'Data_dt' in diagnosticos_df_admin_orig_view.columns:
                fig_timeline = create_diagnostics_timeline_chart(diagnosticos_df_admin_orig_view) # Passa o DF com Data_dt
                if fig_timeline: st.plotly_chart(fig_timeline, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        # ... (outros gráficos do admin)

        st.divider()
        st.markdown("#### Filtros para Análise Detalhada de Diagnósticos")
        # ... (Filtros como antes) ...

        # Melhoria na exibição de diagnósticos filtrados
        if not df_diagnosticos_filtrados_view_final_vg.empty:
            st.markdown(f"##### Diagnósticos Detalhados (Seleção Filtrada)")
            df_display_admin = df_diagnosticos_filtrados_view_final_vg.copy()
            if 'Data_dt' in df_display_admin.columns:
                df_display_admin = df_display_admin.sort_values(by="Data_dt", ascending=False).reset_index(drop=True)

            try:
                perguntas_df_admin_view = pd.read_csv(perguntas_csv, encoding='utf-8')
                if "Categoria" not in perguntas_df_admin_view.columns: perguntas_df_admin_view["Categoria"] = "Geral"
            except: perguntas_df_admin_view = pd.DataFrame()
            analises_df_admin_view = carregar_analises_perguntas()

            for idx_diag_adm, row_diag_adm_series in df_display_admin.iterrows():
                row_diag_adm = row_diag_adm_series.to_dict() # Converter para dict
                diag_data_str = str(row_diag_adm.get('Data','N/A'))
                with st.expander(f"🔎 {diag_data_str} - {row_diag_adm.get('Empresa','N/A')} (CNPJ: {row_diag_adm.get('CNPJ','N/A')})"):
                    st.markdown('<div class="custom-card" style="padding-top:10px; padding-bottom:10px; border-left-color: #fd7e14;">', unsafe_allow_html=True) # Cor de destaque diferente
                    c1_exp, c2_exp, c3_exp = st.columns([2,3,3])
                    with c1_exp:
                        logo_path_exp = find_client_logo_path(row_diag_adm.get('CNPJ'))
                        if logo_path_exp: st.image(logo_path_exp, width=70)
                        else: st.caption("Sem logo")
                        st.metric("Média Geral", f"{pd.to_numeric(row_diag_adm.get('Média Geral'), errors='coerce'):.2f}" if pd.notna(row_diag_adm.get('Média Geral')) else "N/A")
                        st.metric("GUT Média", f"{pd.to_numeric(row_diag_adm.get('GUT Média'), errors='coerce'):.2f}" if pd.notna(row_diag_adm.get('GUT Média')) else "N/A")
                    with c2_exp:
                        st.caption(f"**Resumo (Cliente):** {row_diag_adm.get('Diagnóstico', 'N/P')}")
                        st.caption(f"**Análise (Cliente):** {row_diag_adm.get('Análise do Cliente', 'N/P')}")
                    with c3_exp:
                        com_admin_atual = row_diag_adm.get("Comentarios_Admin", "")
                        com_admin_input = st.text_area("Comentários do Consultor:", value=com_admin_atual, key=f"com_admin_input_v20_{idx_diag_adm}_{row_diag_adm.get('CNPJ')}", height=100)
                        if st.button("💬 Salvar Comentário", key=f"save_com_admin_v20_{idx_diag_adm}_{row_diag_adm.get('CNPJ')}"):
                            # ... (lógica de salvar comentário e notificar) ...
                            st.toast("Comentário salvo e cliente notificado!", icon="🔔"); st.rerun()
                    # ... (botão de download PDF) ...
                    st.markdown('</div>', unsafe_allow_html=True)


    elif menu_admin == "Relatório de Engajamento":
        # ... (Relatório de Engajamento como antes, mas pode usar os novos .info-card para métricas) ...
        st.markdown("#### Métricas de Engajamento dos Clientes")
        if df_usuarios_admin_geral.empty: st.info("Nenhum cliente cadastrado.")
        else:
            # ... (cálculos de engajamento como antes) ...
            c1,c2,c3,c4 = st.columns(4)
            # Exemplo de uso do info-card (aplicar a todos os KPIs)
            with c1: st.markdown(f"""<div class="info-card"><p class="stMetricLabel">Total de Clientes</p><p class="stMetricValue">{total_usuarios}</p></div>""", unsafe_allow_html=True)
            # ... (resto das métricas)


    elif menu_admin == "Gerenciar SAC":
        st.markdown("#### 📞 Gerenciamento do SAC - Perguntas e Respostas")
        df_sac_qa_admin = carregar_sac_perguntas_respostas().copy()
        df_sac_uso_admin = carregar_sac_uso_feedback().copy()
        sac_admin_tabs = st.tabs(["📝 Gerenciar Perguntas e Respostas SAC", "📊 Relatório de Uso e Feedback SAC"])

        with sac_admin_tabs[0]:
            # ... (Gerenciar Perguntas SAC como antes) ...
            pass
        with sac_admin_tabs[1]:
            st.subheader("Relatório de Interações e Feedback do SAC")
            if df_sac_uso_admin.empty: st.info("Nenhum feedback ou uso registrado no SAC ainda.")
            else:
                df_sac_uso_display = df_sac_uso_admin.copy()
                # ... (Merge com user data e SAC Q&A como antes) ...

                # GRÁFICOS DE FEEDBACK
                st.markdown("##### Visão Geral do Feedback")
                fig_feedback_geral = create_sac_feedback_chart(df_sac_uso_display, title="Distribuição Global de Feedback SAC")
                if fig_feedback_geral: st.plotly_chart(fig_feedback_geral, use_container_width=True)
                else: st.caption("Sem dados para gráfico de feedback geral.")

                st.markdown("##### Feedback por Pergunta")
                if not df_sac_qa_admin.empty:
                     # Assegurar que a coluna existe antes de tentar usá-la
                    df_sac_uso_display_merged = pd.merge(df_sac_uso_display, df_sac_qa_admin[['ID_SAC_Pergunta', 'Pergunta_SAC']], on='ID_SAC_Pergunta', how='left')
                    df_sac_uso_display_merged['Pergunta_SAC'] = df_sac_uso_display_merged['Pergunta_SAC'].fillna("N/D (Pergunta Excluída)")

                    # Re-mapeia Feedback_Util para ter certeza que está como string legível para o gráfico
                    df_sac_uso_display_merged['Feedback_Display'] = df_sac_uso_display_merged['Feedback_Util'].map({
                        True: '👍 Útil', False: '👎 Não Útil', pd.NA: '➖ Sem Feedback',
                        'True': '👍 Útil', 'False': '👎 Não Útil', 'nan': '➖ Sem Feedback',
                        '': '➖ Sem Feedback'
                    }).fillna('➖ Sem Feedback')


                    feedback_por_pergunta = df_sac_uso_display_merged.groupby(['Pergunta_SAC', 'Feedback_Display']).size().reset_index(name='Contagem')
                    if not feedback_por_pergunta.empty:
                        fig_feedback_perg = px.bar(feedback_por_pergunta, x='Pergunta_SAC', y='Contagem', color='Feedback_Display',
                                                   barmode='group', title="Feedback por Pergunta Específica",
                                                   color_discrete_map={'👍 Útil': '#28a745', '👎 Não Útil': '#dc3545', '➖ Sem Feedback': '#6c757d'},
                                                   labels={'Pergunta_SAC': 'Pergunta do SAC', 'Contagem': 'Número de Avaliações'})
                        fig_feedback_perg.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_feedback_perg, use_container_width=True)
                    else: st.caption("Sem dados para gráfico de feedback por pergunta.")
                else: st.caption("Dados de perguntas do SAC não carregados para detalhar feedback.")
                st.divider()
                st.markdown("##### Dados de Feedback Detalhados (Filtráveis)")
                # ... (Filtros e tabela de df_sac_uso_filtrado como antes) ...


    # ... (Outras seções do Admin: Gerenciar Instruções, Histórico, Clientes, Admins - sem grandes alterações visuais além das globais) ...

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()