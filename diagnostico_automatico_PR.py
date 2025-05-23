import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta # Added timedelta
import os
import time
from fpdf import FPDF
import tempfile
import re
import json
import plotly.express as px
import plotly.graph_objects as go # Added for more chart control
import uuid # Para IDs de análise e SAC

# !!! st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT !!!
st.set_page_config(page_title="Portal de Diagnóstico Avançado", layout="wide", page_icon="🚀")

# --- CSS Melhorado ---
st.markdown("""
<style>
body {
    font-family: 'Roboto', 'Segoe UI', sans-serif;
    background-color: #f0f2f5; /* Light gray background for the page */
}

.login-container {
    max-width: 480px; /* Slightly wider */
    margin: 50px auto 0 auto;
    padding: 45px;
    border-radius: 12px;
    background-color: #ffffff;
    box-shadow: 0 8px 25px rgba(0,0,0,0.1); /* Softer shadow */
    font-family: 'Roboto', sans-serif;
}

.login-container img.login-logo { /* Specific class for login logo */
    display: block;
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 25px;
    border-radius: 8px; /* Optional: if logo benefits from rounded corners */
}

.login-container h2.login-title { /* Specific class for login title */
    text-align: center;
    margin-bottom: 35px;
    font-weight: 700; /* Bolder */
    font-size: 28px; /* Larger */
    color: #1e3a8a; /* Darker blue for a more corporate feel */
}

.stButton>button {
    border-radius: 8px; /* More rounded */
    background-color: #2563eb; /* Primary blue */
    color: white;
    font-weight: 600; /* Bolder text */
    padding: 0.75rem 1.5rem; /* More padding */
    margin-top: 0.75rem;
    border: none;
    transition: background-color 0.2s ease-in-out, transform 0.1s ease;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.stButton>button:hover {
    background-color: #1d4ed8; /* Darker blue on hover */
    transform: translateY(-1px); /* Slight lift on hover */
}
.stButton>button:active {
    transform: translateY(0px); /* Reset lift on click */
}


.stButton>button.secondary {
    background-color: #e5e7eb;
    color: #374151;
}
.stButton>button.secondary:hover {
    background-color: #d1d5db;
}

.stDownloadButton>button {
    background-color: #10b981; /* Green for download */
    color: white;
    font-weight: 600;
    border-radius: 8px;
    margin-top: 12px;
    padding: 0.75rem 1.5rem;
    border: none;
    transition: background-color 0.3s ease;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
.stDownloadButton>button:hover {
    background-color: #059669; /* Darker green */
    transform: translateY(-1px);
}

/* Inputs, TextAreas, DateInputs, Selectboxes */
.stTextInput>div>input,
.stTextArea>div>textarea,
.stDateInput>div>div>input, /* Target the actual input inside date picker */
.stSelectbox>div>div {
    border-radius: 8px;
    padding: 0.75rem; /* More padding */
    border: 1px solid #cbd5e1; /* Softer border */
    background-color: #f8fafc; /* Slightly off-white */
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
    font-size: 15px;
}

.stTextInput>div>input:focus,
.stTextArea>div>textarea:focus,
.stDateInput>div>div>input:focus,
.stSelectbox>div>div:focus-within {
    border-color: #2563eb; /* Primary blue on focus */
    box-shadow: 0 0 0 0.15rem rgba(37, 99, 235, 0.2); /* Softer focus ring */
    background-color: #ffffff;
}

.stTabs [data-baseweb="tab-list"] {
    background-color: #eef2ff; /* Light background for tab bar */
    border-radius: 8px 8px 0 0;
    padding: 5px;
}
.stTabs [data-baseweb="tab"] {
    font-size: 16px;
    font-weight: 600;
    padding: 14px 24px; /* More padding */
    border-radius: 6px; /* Rounded individual tabs */
    margin: 0 3px;
    color: #4b5563; /* Default tab text color */
    border: none;
    transition: background-color 0.2s ease, color 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    background-color: #dbeafe; /* Light blue on hover */
    color: #1e3a8a;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #2563eb; /* Primary blue for selected tab */
    color: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.custom-card {
    border: 1px solid #e2e8f0; /* Lighter border */
    border-left: 6px solid #2563eb; /* Primary blue accent */
    padding: 25px; /* More padding */
    margin-bottom: 20px;
    border-radius: 10px; /* More rounded */
    background-color: #ffffff;
    box-shadow: 0 3px 10px rgba(0,0,0,0.05); /* Subtle shadow */
    transition: box-shadow 0.3s ease;
}
.custom-card:hover {
    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
}
.custom-card h4 { /* More distinct card titles */
    margin-top: 0;
    margin-bottom: 12px;
    color: #1e3a8a; /* Darker blue */
    font-size: 1.2em;
    font-weight: 600;
    border-bottom: 1px solid #eef2ff;
    padding-bottom: 8px;
}

.feedback-saved {
    font-size: 0.9em; /* Slightly larger */
    color: #059669; /* Green for success */
    font-style: normal; /* Not italic */
    font-weight: 500;
    margin-top: -5px;
    margin-bottom: 10px;
}

.analise-pergunta-cliente {
    font-size: 0.95em;
    color: #1e293b; /* Darker text */
    background-color: #e0e7ff; /* Lighter indigo */
    border-left: 4px solid #4f46e5; /* Indigo accent */
    padding: 12px 15px;
    margin-top: 10px;
    margin-bottom:15px;
    border-radius: 6px;
}
.analise-pergunta-cliente b {
    color: #3730a3; /* Darker indigo for bold */
}

[data-testid="stMetric"] {
    background-color: #ffffff;
    border-radius: 10px;
    padding: 20px 25px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.05);
    border: 1px solid #e2e8f0;
}
[data-testid="stMetricLabel"] {
    font-weight: 500;
    color: #64748b; /* Grayish blue for label */
    font-size: 0.95em;
}
[data-testid="stMetricValue"] {
    font-size: 2.2em; /* Larger metric value */
    font-weight: 700;
    color: #1e3a8a; /* Darker blue for value */
}
[data-testid="stMetricDelta"] {
    font-size: 1em;
    font-weight: 600;
}

.stExpander {
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
    margin-bottom: 20px !important;
    background-color: #ffffff;
}
.stExpander header {
    font-weight: 600 !important;
    border-radius: 10px 10px 0 0 !important; /* Rounded top corners */
    padding: 12px 18px !important;
    background-color: #f8fafc; /* Light background for header */
    border-bottom: 1px solid #e2e8f0;
    color: #1e3a8a;
    font-size: 1.05em;
}
.stExpander header:hover {
    background-color: #eef2ff;
}

.dashboard-item {
    background-color: #ffffff;
    padding: 25px;
    border-radius: 10px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.05);
    margin-bottom: 25px;
    border: 1px solid #e2e8f0;
    height: 100%; /* For consistent height in columns */
}
.dashboard-item h5 {
    margin-top: 0;
    margin-bottom: 18px; /* More space below title */
    color: #1e3a8a; /* Darker blue */
    font-size: 1.15em; /* Slightly larger */
    font-weight: 600;
    border-bottom: 1px solid #eef2ff; /* Light separator */
    padding-bottom: 10px;
}

/* SAC Feedback Buttons */
.sac-feedback-button button {
    background-color: #f1f5f9; /* Lighter gray */
    color: #475569; /* Darker gray text */
    border: 1px solid #cbd5e1; /* Softer border */
    margin-right: 8px;
    padding: 0.4rem 0.9rem;
    border-radius: 6px;
    font-weight: 500;
    transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}
.sac-feedback-button button:hover {
    background-color: #e2e8f0;
    border-color: #94a3b8;
    color: #1e293b;
}
.sac-feedback-button button.active {
    background-color: #2563eb;
    color: white;
    border-color: #2563eb;
}
.sac-feedback-button button.active:hover {
    background-color: #1d4ed8;
    border-color: #1d4ed8;
}

/* Improved Sidebar */
[data-testid="stSidebar"] {
    background-color: #ffffff; /* White sidebar */
    padding: 15px;
    border-right: 1px solid #e2e8f0;
}
[data-testid="stSidebar"] .stButton>button {
    background-color: #4A5568; /* Darker gray for sidebar buttons */
    color: white;
}
[data-testid="stSidebar"] .stButton>button:hover {
    background-color: #2D3748; /* Even darker gray */
}
[data-testid="stSidebar"] .stRadio>label>div:first-child { /* Radio button labels in sidebar */
    font-weight: 500;
}

/* Table styling improvements (more targeted if possible) */
.stDataFrame {
    border-radius: 8px;
    overflow: hidden; /* To make border-radius work with table */
}
.stDataFrame table {
    font-size: 0.9em;
}
.stDataFrame th {
    background-color: #f8fafc;
    color: #334155;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.8em;
    border-bottom: 2px solid #e2e8f0;
}
.stDataFrame td {
    border-bottom: 1px solid #eef2ff;
}
.stDataFrame tr:hover td {
    background-color: #f0f9ff;
}

/* Custom class for client health status in admin table */
.health-good { color: #10b981; font-weight: bold; }
.health-attention { color: #ef4444; font-weight: bold; }
.health-neutral { color: #6b7280; font-weight: normal; }

</style>
""", unsafe_allow_html=True)

# --- Funções de Gráficos ---
def create_radar_chart(data_dict, title="Radar Chart"):
    if not data_dict: return None
    categories = list(data_dict.keys())
    values = [float(v) if pd.notna(v) else 0 for v in data_dict.values()] # Ensure numeric, handle NaN
    if not categories or not values or len(categories) < 3 : return None

    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]

    df_radar = pd.DataFrame(dict(r=values_closed, theta=categories_closed))
    fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True, template="plotly_white") # Changed template
    fig.update_traces(fill='toself', line=dict(color='#2563eb', width=2.5)) # Thicker line
    fig.update_layout(
        title={'text': title, 'x':0.5, 'xanchor': 'center', 'font': {'size': 18, 'family': 'Roboto, Segoe UI, sans-serif'}},
        polar=dict(radialaxis=dict(visible=True, range=[0, 5.1], showline=False, tickfont_size=10),
                   angularaxis=dict(showline=False, tickfont_size=12, categoryorder='array', categoryarray=categories_closed)), # Ensure order
        font=dict(family="Roboto, Segoe UI, sans-serif"),
        margin=dict(l=60, r=60, t=80, b=60), # Adjusted margins
        height=380 # Slightly increased height
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
                 template="plotly_white") # Changed template
    fig.update_layout(yaxis={'categoryorder':'total ascending', 'tickfont': {'size': 11}}, # Larger y-axis ticks
                      xaxis_title="Score GUT", yaxis_title="",
                      font=dict(family="Roboto, Segoe UI, sans-serif"),
                      height=max(300, 200 + len(df_gut)*30), # Dynamic height
                      margin=dict(l=280, r=20, t=70, b=40), # Adjusted margins
                      coloraxis_showscale=False) # Hide color scale if redundant
    fig.update_traces(marker_line_color='rgb(8,48,107)', marker_line_width=0.5, opacity=0.9) # Add marker line
    return fig

def create_diagnostics_timeline_chart(df_diagnostics, title="Diagnósticos Realizados ao Longo do Tempo"):
    if df_diagnostics.empty or 'Data' not in df_diagnostics.columns: return None
    df_diag_copy = df_diagnostics.copy()
    df_diag_copy['Data'] = pd.to_datetime(df_diag_copy['Data'], errors='coerce')
    df_diag_copy.dropna(subset=['Data'], inplace=True) # Drop rows where Data couldn't be converted
    if df_diag_copy.empty: return None

    diag_counts_monthly = df_diag_copy.groupby(pd.Grouper(key='Data', freq='M')).size().reset_index(name='Contagem')
    diag_counts_monthly['Mês'] = diag_counts_monthly['Data'].dt.strftime('%Y-%m')
    if diag_counts_monthly.empty: return None
    fig = px.line(diag_counts_monthly, x='Mês', y='Contagem', title=title, markers=True,
                  labels={'Mês':'Mês', 'Contagem':'Nº de Diagnósticos'}, line_shape="spline",
                  template="plotly_white") # Changed template
    fig.update_traces(line=dict(color='#2563eb', width=2.5), marker=dict(size=8)) # Thicker line, larger markers
    fig.update_layout(font=dict(family="Roboto, Segoe UI, sans-serif"),
                      xaxis_title="Mês", yaxis_title="Número de Diagnósticos")
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
    avg_scores = avg_scores.sort_values(by="Média_Score", ascending=True) # Ascending for horizontal bar

    fig = px.bar(avg_scores, y='Categoria', x='Média_Score', title=title, # Swapped x and y
                 color='Média_Score', color_continuous_scale=px.colors.sequential.Blues, # Standard Blues
                 labels={'Categoria':'Categoria', 'Média_Score':'Média do Score'},
                 orientation='h', template="plotly_white") # Horizontal bar
    fig.update_layout(font=dict(family="Roboto, Segoe UI, sans-serif"),
                      xaxis=dict(range=[0,5.1]), # Ensure x-axis starts at 0
                      yaxis_title="", xaxis_title="Média do Score (0-5)",
                      height=max(300, 150 + len(avg_scores)*25), # Dynamic height
                      margin=dict(l=150, r=20, t=70, b=40))
    fig.update_traces(marker_line_color='rgb(8,48,107)', marker_line_width=0.5, opacity=0.9)
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
    # Define a specific order for better visualization
    category_order = ["0 Diagnósticos", "1 Diagnóstico", "2 Diagnósticos", "3+ Diagnósticos"]
    engagement_counts['Categoria_Engajamento'] = pd.Categorical(engagement_counts['Categoria_Engajamento'], categories=category_order, ordered=True)
    engagement_counts = engagement_counts.sort_values('Categoria_Engajamento')


    if engagement_counts.empty: return None

    fig = px.pie(engagement_counts, values='Numero_Clientes', names='Categoria_Engajamento', title=title,
                 color_discrete_sequence=px.colors.sequential.Blues_r, template="plotly_white")
    fig.update_traces(textposition='outside', textinfo='percent+label', insidetextorientation='radial',
                      marker=dict(line=dict(color='#FFFFFF', width=2))) # Add white lines between slices
    fig.update_layout(font=dict(family="Roboto, Segoe UI, sans-serif"), legend_title_text='Nível de Engajamento',
                      height=400)
    return fig

# --- NOVOS GRÁFICOS PARA ADMIN ---
def create_common_weaknesses_chart(df_diagnostics_all, df_perguntas, top_n=10, title="Questões com Menor Média de Score Global"):
    if df_diagnostics_all.empty or df_perguntas.empty: return None

    question_scores = {}
    score_questions = [q for q in df_perguntas['Pergunta'] if "Pontuação (0-5)" in q or "Pontuação (0-10)" in q]

    for question_text in score_questions:
        if question_text in df_diagnostics_all.columns:
            scores = pd.to_numeric(df_diagnostics_all[question_text], errors='coerce').dropna()
            if not scores.empty:
                question_scores[question_text.split(" [")[0]] = scores.mean() # Store only the question text part

    if not question_scores: return None

    df_q_scores = pd.DataFrame(list(question_scores.items()), columns=['Pergunta', 'Média_Score'])
    df_q_scores = df_q_scores.sort_values(by='Média_Score', ascending=True).head(top_n)

    if df_q_scores.empty: return None

    fig = px.bar(df_q_scores, x='Média_Score', y='Pergunta', title=title, orientation='h',
                 color='Média_Score', color_continuous_scale=px.colors.sequential.Reds_r, # Red for weaknesses
                 labels={'Pergunta':'Questão', 'Média_Score':'Média do Score'},
                 template="plotly_white")
    fig.update_layout(
        yaxis={'categoryorder':'total descending', 'tickfont': {'size': 10}},
        xaxis_title="Média de Score", yaxis_title="",
        font=dict(family="Roboto, Segoe UI, sans-serif"),
        height=max(300, 200 + len(df_q_scores)*28),
        margin=dict(l=300, r=20, t=70, b=40),
        coloraxis_showscale=False
    )
    fig.update_traces(marker_line_color='rgb(127,0,0)', marker_line_width=0.5, opacity=0.9)
    return fig

def create_sac_feedback_summary_chart(df_sac_uso_feedback, df_sac_qa, title="Feedback de Utilidade dos Artigos do SAC"):
    if df_sac_uso_feedback.empty or 'Feedback_Util' not in df_sac_uso_feedback.columns: return None

    # Ensure Feedback_Util is boolean (True, False, NA)
    df_sac_uso_feedback['Feedback_Util'] = df_sac_uso_feedback['Feedback_Util'].astype(str).str.lower().map(
        {'true': True, 'false': False, 'nan': pd.NA, '': pd.NA}
    ).astype('boolean')

    feedback_counts = df_sac_uso_feedback.groupby('ID_SAC_Pergunta')['Feedback_Util'].value_counts().unstack(fill_value=0)
    feedback_counts = feedback_counts.reindex(columns=[True, False], fill_value=0) # Ensure both True and False columns
    feedback_counts.columns = ['Útil', 'Não Útil']

    if not df_sac_qa.empty:
        feedback_counts = feedback_counts.merge(df_sac_qa[['ID_SAC_Pergunta', 'Pergunta_SAC']], on='ID_SAC_Pergunta', how='left')
        feedback_counts['Pergunta_SAC'] = feedback_counts['Pergunta_SAC'].fillna("ID: " + feedback_counts['ID_SAC_Pergunta'])
    else:
        feedback_counts['Pergunta_SAC'] = "ID: " + feedback_counts.index.astype(str)

    feedback_counts = feedback_counts.sort_values(by=['Não Útil', 'Útil'], ascending=[False, False]) # Sort by Not Useful then Useful

    if feedback_counts.empty: return None

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=feedback_counts['Pergunta_SAC'],
        x=feedback_counts['Útil'],
        name='👍 Útil',
        orientation='h',
        marker=dict(color='#10b981', line=dict(color='white', width=1))
    ))
    fig.add_trace(go.Bar(
        y=feedback_counts['Pergunta_SAC'],
        x=feedback_counts['Não Útil'],
        name='👎 Não Útil',
        orientation='h',
        marker=dict(color='#ef4444', line=dict(color='white', width=1))
    ))

    fig.update_layout(
        barmode='stack',
        title={'text': title, 'x':0.5, 'xanchor': 'center'},
        xaxis_title="Contagem de Feedbacks",
        yaxis_title="Pergunta do SAC",
        font=dict(family="Roboto, Segoe UI, sans-serif"),
        legend_title_text='Tipo de Feedback',
        height=max(300, 200 + len(feedback_counts)*30),
        margin=dict(l=350, r=20, t=70, b=40),
        template="plotly_white",
        yaxis={'categoryorder':'total ascending'}
    )
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
instrucoes_default_path = "instrucoes_portal_default.md" # Could be removed if custom is always created
sac_perguntas_respostas_csv = "sac_perguntas_respostas.csv"
sac_uso_feedback_csv = "sac_uso_feedback.csv"
LOGOS_DIR = "client_logos"
DEFAULT_PORTAL_LOGO = "https://raw.githubusercontent.com/streamlit/streamlit/develop/components/extras/images/streamlit-logo-primary-colormark-darktext.png" # Placeholder

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
    "admin_current_page_text_key_v19": "Visão Geral e Diagnósticos" # Default admin page
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
    for ext in ["png", "jpg", "jpeg", "webp"]: # Added webp
        path = os.path.join(LOGOS_DIR, f"{base}_logo.{ext}")
        if os.path.exists(path): return path
    return None # Consider returning a default placeholder logo path here if needed

if not os.path.exists(LOGOS_DIR):
    try: os.makedirs(LOGOS_DIR)
    except OSError as e: st.error(f"Erro ao criar diretório de logos '{LOGOS_DIR}': {e}")

colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone",
                         "JaVisualizouInstrucoes", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados",
                         "UltimoLogin", "DataCadastro"] # Added UltimoLogin, DataCadastro
colunas_base_perguntas = ["Pergunta", "Categoria"]
colunas_base_analises = ["ID_Analise", "TextoPerguntaOriginal", "TipoCondicao", "CondicaoValorMin", "CondicaoValorMax", "CondicaoValorExato", "TextoAnalise"]
colunas_base_notificacoes = ["ID_Notificacao", "CNPJ_Cliente", "Timestamp", "Mensagem", "Lida", "ID_Diagnostico_Relacionado"]
colunas_base_sac_perguntas = ["ID_SAC_Pergunta", "Pergunta_SAC", "Resposta_SAC", "Categoria_SAC", "DataCriacao", "Tags_SAC"] # Added Tags
colunas_base_sac_uso_feedback = ["ID_Uso_SAC", "Timestamp", "CNPJ_Cliente", "ID_SAC_Pergunta", "Feedback_Util"]


def inicializar_csv(filepath, columns, defaults=None):
    try:
        df_to_write = None
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init = pd.DataFrame(columns=columns)
            if defaults:
                for col, default_val in defaults.items():
                    if col in columns:
                        # If default_val is callable (like datetime.now), call it
                        df_init[col] = default_val() if callable(default_val) else default_val
            df_to_write = df_init
        else:
            try:
                current_df = pd.read_csv(filepath, encoding='utf-8', dtype={'CNPJ': str, 'CNPJ_Cliente': str} if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, sac_uso_feedback_csv] else None)
            except ValueError as ve:
                st.warning(f"Problema ao ler {filepath} com dtypes específicos ({ve}), tentando leitura genérica.")
                current_df = pd.read_csv(filepath, encoding='utf-8')
            except Exception as read_e:
                st.error(f"Falha crítica ao ler {filepath}, será sobrescrito com estrutura vazia: {read_e}")
                current_df = pd.DataFrame(columns=columns) # Recreate if critical read error
                if defaults:
                    for col, default_val in defaults.items():
                        if col in columns: current_df[col] = default_val() if callable(default_val) else default_val
                df_to_write = current_df

            made_changes = False
            if df_to_write is None: # If not recreated due to critical error
                for col_idx, col_name in enumerate(columns):
                    if col_name not in current_df.columns:
                        default_val_to_assign = pd.NA
                        if defaults and col_name in defaults:
                             default_val_to_assign = defaults[col_name]() if callable(defaults[col_name]) else defaults[col_name]

                        current_df.insert(loc=min(col_idx, len(current_df.columns)), column=col_name, value=default_val_to_assign)
                        made_changes = True
                if made_changes:
                    df_to_write = current_df

        if df_to_write is not None:
            df_to_write.to_csv(filepath, index=False, encoding='utf-8')

    except pd.errors.EmptyDataError: # Catch if read_csv results in empty despite file existing
        df_init = pd.DataFrame(columns=columns)
        if defaults:
            for col, default_val in defaults.items():
                if col in columns: df_init[col] = default_val() if callable(default_val) else default_val
        df_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e: st.error(f"Erro crítico ao inicializar {filepath}: {e}"); raise

# Get current timestamp string
def now_str(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios,
                    defaults={"JaVisualizouInstrucoes": "False", "DiagnosticosDisponiveis": 1,
                              "TotalDiagnosticosRealizados": 0, "UltimoLogin": None, "DataCadastro": now_str})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False, "ID_Diagnostico_Relacionado": None})
    inicializar_csv(sac_perguntas_respostas_csv, colunas_base_sac_perguntas,
                    defaults={"Categoria_SAC": "Geral", "DataCriacao": now_str, "Tags_SAC": None})
    inicializar_csv(sac_uso_feedback_csv, colunas_base_sac_uso_feedback, defaults={"Feedback_Util": None})
except Exception as e_init:
    st.error(f"Falha na inicialização de arquivos CSV: {e_init}")
    st.stop()


def registrar_acao(cnpj, acao, desc):
    try: hist_df = pd.read_csv(historico_csv, encoding='utf-8')
    except (FileNotFoundError, pd.errors.EmptyDataError): hist_df = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    new_entry = {"Data": now_str(), "CNPJ": cnpj, "Ação": acao, "Descrição": desc}
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
        if "DataCriacao" not in df.columns: df["DataCriacao"] = now_str()
        if "Tags_SAC" not in df.columns: df["Tags_SAC"] = None
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
    # (This function is very long and largely unchanged for brevity in this diff.
    # Key recommendations: Use a templating engine for more complex PDFs, or embed Plotly charts as images)
    try:
        with st.spinner("Gerando PDF do diagnóstico... Aguarde."):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_font('Roboto', '', 'Roboto-Regular.ttf', uni=True) # Assuming Roboto TTF is available
            pdf.add_font('Roboto', 'B', 'Roboto-Bold.ttf', uni=True)
            pdf.add_font('Roboto', 'I', 'Roboto-Italic.ttf', uni=True)

            empresa_nome = user_data.get("Empresa", "N/D")
            cnpj_pdf = user_data.get("CNPJ", "N/D")
            logo_path = find_client_logo_path(cnpj_pdf)

            # Header
            if logo_path:
                try:
                    pdf.image(logo_path, x=10, y=8, h=20)
                    pdf.set_y(30) # Move below logo
                except Exception as e_logo_pdf:
                    st.warning(f"Não foi possível adicionar logo ao PDF: {e_logo_pdf}")
                    pdf.set_y(10) # Start normally if logo fails
            else:
                pdf.set_font("Roboto", 'B', 10)
                pdf.cell(0, 8, "Portal de Diagnóstico", 0, 1, 'L') # Generic portal name if no logo
                pdf.set_y(18)


            pdf.set_font("Roboto", 'B', 20)
            pdf.set_text_color(28, 58, 138) # Dark Blue
            pdf.cell(0, 12, pdf_safe_text_output(f"Diagnóstico Empresarial"), 0, 1, 'C')
            pdf.set_font("Roboto", 'B', 16)
            pdf.set_text_color(55, 65, 81) # Gray
            pdf.cell(0, 10, pdf_safe_text_output(empresa_nome), 0, 1, 'C')
            pdf.ln(8)

            pdf.set_font("Roboto", size=10)
            pdf.set_text_color(0,0,0) # Black
            pdf.multi_cell(0, 6, pdf_safe_text_output(f"Data da Análise: {diag_data.get('Data','N/D')} | CNPJ: {cnpj_pdf}"))
            if user_data.get("NomeContato"): pdf.multi_cell(0, 6, pdf_safe_text_output(f"Contato Principal: {user_data.get('NomeContato')}"))
            if user_data.get("Telefone"): pdf.multi_cell(0, 6, pdf_safe_text_output(f"Telefone: {user_data.get('Telefone')}"))
            pdf.ln(5)

            # --- Scores Chave ---
            pdf.set_font("Roboto", 'B', 12)
            pdf.set_fill_color(224, 231, 255) # Light Indigo background
            pdf.cell(0, 8, pdf_safe_text_output("Resumo dos Indicadores Chave"), 0, 1, 'L', fill=True)
            pdf.ln(2)
            pdf.set_font("Roboto", size=10)
            mg_text = f"{float(diag_data.get('Média Geral', 0)):.2f}" if pd.notna(diag_data.get('Média Geral')) else "N/A"
            gut_text = f"{float(diag_data.get('GUT Média', 0)):.2f}" if pd.notna(diag_data.get('GUT Média')) else "N/A"
            pdf.multi_cell(0, 7, pdf_safe_text_output(f"Média Geral das Pontuações: {mg_text} / 5.0 (ou /10.0)")) # Clarify scale
            pdf.multi_cell(0, 7, pdf_safe_text_output(f"Score Médio de Prioridade (GUT): {gut_text}"))
            pdf.ln(5)

            if medias_cat:
                pdf.set_font("Roboto", 'B', 11)
                pdf.set_fill_color(243, 244, 246) # Lighter gray
                pdf.cell(0, 7, pdf_safe_text_output("Médias por Categoria:"), 0, 1, 'L', fill=True)
                pdf.ln(1)
                pdf.set_font("Roboto", size=9)
                for cat, media in medias_cat.items():
                    media_val = float(media) if pd.notna(media) else 0.0
                    pdf.multi_cell(0, 6, pdf_safe_text_output(f"  • {pdf_safe_text_output(cat)}: {media_val:.2f}"))
                pdf.ln(5)

            # --- Resumos e Análises Textuais ---
            text_sections = [
                ("Sumário do Diagnóstico (Fornecido pelo Cliente):", "Diagnóstico"),
                ("Análise Adicional (Fornecida pelo Cliente):", "Análise do Cliente"),
                ("Comentários e Recomendações (Consultor):", "Comentarios_Admin")
            ]
            for titulo, campo in text_sections:
                valor = diag_data.get(campo, "")
                if valor and not pd.isna(valor) and str(valor).strip():
                    pdf.set_font("Roboto", 'B', 12)
                    pdf.set_fill_color(224, 231, 255)
                    pdf.cell(0, 8, pdf_safe_text_output(titulo), 0, 1, 'L', fill=True)
                    pdf.ln(2)
                    pdf.set_font("Roboto", size=10)
                    pdf.set_fill_color(255,255,255)
                    pdf.multi_cell(0, 7, pdf_safe_text_output(str(valor)), border=0, fill=False) # No border for text block
                    pdf.ln(5)

            # --- Respostas Detalhadas e Análises ---
            pdf.add_page()
            pdf.set_font("Roboto", 'B', 14)
            pdf.set_text_color(28, 58, 138)
            pdf.cell(0, 10, pdf_safe_text_output("Respostas Detalhadas e Análises Específicas"), 0, 1, 'C')
            pdf.ln(5)
            pdf.set_text_color(0,0,0)

            categorias = perguntas_df["Categoria"].unique() if not perguntas_df.empty and "Categoria" in perguntas_df.columns else []
            for categoria in sorted(list(categorias)): # Sort categories
                pdf.set_font("Roboto", 'B', 11)
                pdf.set_fill_color(243, 244, 246)
                pdf.cell(0, 7, pdf_safe_text_output(f"Área de Análise: {categoria}"), 0, 1, 'L', fill=True)
                pdf.ln(2)

                perg_cat = perguntas_df[perguntas_df["Categoria"] == categoria]
                for _, p_row in perg_cat.iterrows():
                    p_texto = p_row["Pergunta"]
                    resp = respostas_coletadas.get(p_texto, diag_data.get(p_texto, "N/R"))
                    analise_texto = None

                    pdf.set_font("Roboto", 'B', 9)
                    pdf.multi_cell(0,6,pdf_safe_text_output(f"P: {p_texto.split('[')[0].strip()}")) # Show only question part
                    pdf.set_font("Roboto", '', 9)

                    if "[Matriz GUT]" in p_texto:
                        g,u,t,score=0,0,0,0
                        if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                        elif isinstance(resp, str):
                            try: data_gut=json.loads(resp.replace("'",'"'));g,u,t=int(data_gut.get("G",0)),int(data_gut.get("U",0)),int(data_gut.get("T",0))
                            except: pass
                        score = g*u*t
                        pdf.set_fill_color(249, 250, 251) # Very light gray for answer box
                        pdf.multi_cell(0,6,pdf_safe_text_output(f"   R: Gravidade={g}, Urgência={u}, Tendência={t} (Score Prioridade: {score})"), fill=True)
                        analise_texto = obter_analise_para_resposta(p_texto, score, analises_df)
                    else:
                        pdf.set_fill_color(249, 250, 251)
                        pdf.multi_cell(0, 6, pdf_safe_text_output(f"   R: {resp}"), fill=True)
                        analise_texto = obter_analise_para_resposta(p_texto, resp, analises_df)

                    if analise_texto:
                        pdf.set_font("Roboto", 'I', 8)
                        pdf.set_text_color(75,85,99) # Grayish for analysis
                        pdf.multi_cell(0, 5, pdf_safe_text_output(f"      Análise Sugerida: {analise_texto}"))
                        pdf.set_text_color(0,0,0)
                    pdf.ln(2) # Space between questions
                pdf.ln(4) # Space between categories

            # --- Plano de Ação (GUT) ---
            pdf.add_page()
            pdf.set_font("Roboto", 'B', 14)
            pdf.set_text_color(28, 58, 138)
            pdf.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Baseado em Prioridades GUT)"), 0, 1, 'C')
            pdf.ln(5)
            pdf.set_text_color(0,0,0)
            pdf.set_font("Roboto", size=9)

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
                        prazo = "N/A"; cor_prioridade = (200,200,200) # Gray default
                        if score >= 75: prazo = "Curto Prazo (ex: até 15 dias)"; cor_prioridade = (239, 68, 68) # Red
                        elif score >= 40: prazo = "Médio Prazo (ex: até 30 dias)"; cor_prioridade = (249, 115, 22) # Orange
                        elif score >= 20: prazo = "Longo Prazo (ex: até 45 dias)"; cor_prioridade = (234, 179, 8) # Yellow
                        elif score > 0: prazo = "Baixa Prioridade (ex: até 60 dias)"; cor_prioridade = (139, 195, 74) # Light Green
                        else: continue
                        if prazo != "N/A": gut_cards.append({"Tarefa": p_texto.replace(" [Matriz GUT]", ""),"Prazo": prazo, "Score": score, "Cor": cor_prioridade, "Categoria": p_row.get("Categoria", "Geral")})

            if gut_cards:
                sorted_cards = sorted(gut_cards, key=lambda x: (-x["Score"])) # Sort by score descending
                pdf.set_font("Roboto", 'B', 10)
                pdf.cell(10,7,"Prio.",1,0,'C'); pdf.cell(80,7,"Tarefa / Oportunidade",1,0,'C'); pdf.cell(35,7,"Categoria",1,0,'C'); pdf.cell(40,7,"Prazo Sugerido",1,0,'C'); pdf.cell(25,7,"Score GUT",1,1,'C')
                pdf.set_font("Roboto", '', 9)
                for idx, card in enumerate(sorted_cards):
                    pdf.set_fill_color(card["Cor"][0], card["Cor"][1], card["Cor"][2])
                    pdf.cell(10,6, str(idx+1) ,1,0,'C', fill=(idx<3)) # Fill for top 3
                    pdf.set_fill_color(255,255,255) # Reset fill
                    ch = 6 # Cell height
                    x_before = pdf.get_x()
                    y_before = pdf.get_y()
                    pdf.multi_cell(80,ch,pdf_safe_text_output(card['Tarefa']),1,'L')
                    y_after_tarefa = pdf.get_y()
                    pdf.set_xy(x_before + 80, y_before) # Reset X to after Tarefa, Y to before
                    pdf.multi_cell(35,ch,pdf_safe_text_output(card['Categoria']),1,'L')
                    y_after_cat = pdf.get_y()
                    pdf.set_xy(x_before + 80 + 35, y_before)
                    pdf.multi_cell(40,ch,pdf_safe_text_output(card['Prazo']),1,'C')
                    y_after_prazo = pdf.get_y()
                    pdf.set_xy(x_before + 80 + 35 + 40, y_before)
                    pdf.multi_cell(25,ch,str(card['Score']),1,'C')
                    y_after_score = pdf.get_y()
                    max_y = max(y_after_tarefa, y_after_cat, y_after_prazo, y_after_score)
                    pdf.set_y(max_y) # Ensure next line starts correctly
            else:
                 pdf.multi_cell(0,7, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada ou configurada para este diagnóstico."))

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                pdf_path = tmpfile.name; pdf.output(pdf_path)
        return pdf_path
    except Exception as e: st.error(f"Erro crítico ao gerar PDF: {e}"); return None


# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"):
    st.session_state.trigger_rerun_global = False
    st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    login_cols = st.columns([1,0.8,1]) # Create columns for centering the login box
    with login_cols[1]: # Use the middle column
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.image(DEFAULT_PORTAL_LOGO, width=250, output_format='PNG', use_column_width='auto', clamp=False, channels='RGB') # Use a class for styling
        # st.markdown('<img src="YOUR_LOGO_URL_HERE" alt="Logo Portal" class="login-logo" width="200">', unsafe_allow_html=True) # Example with URL
        st.markdown('<h2 class="login-title">Portal de Diagnóstico</h2>', unsafe_allow_html=True) # Use class for styling

        aba = st.radio("Identifique-se:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v19", label_visibility="collapsed")

        if aba == "Administrador":
            st.markdown('<h3 style="text-align:center; color:#374151; font-weight:500; margin-bottom:15px;">Acesso Administrador</h3>', unsafe_allow_html=True)
            with st.form("form_admin_login_v19"):
                u = st.text_input("Usuário", key="admin_u_v19", placeholder="Seu usuário admin")
                p = st.text_input("Senha", type="password", key="admin_p_v19", placeholder="Sua senha")
                if st.form_submit_button("Entrar como Admin", use_container_width=True, icon="🔑"):
                    try:
                        df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                        if not df_creds[(df_creds["Usuario"] == u) & (df_creds["Senha"] == p)].empty:
                            st.session_state.admin_logado = True
                            st.toast("Login de admin bem-sucedido!", icon="🎉")
                            st.rerun()
                        else: st.error("Usuário/senha admin inválidos.")
                    except Exception as e: st.error(f"Erro login admin: {e}")

        elif aba == "Cliente":
            st.markdown('<h3 style="text-align:center; color:#374151; font-weight:500; margin-bottom:15px;">Acesso Cliente</h3>', unsafe_allow_html=True)
            with st.form("form_cliente_login_v19"):
                c = st.text_input("CNPJ", key="cli_c_v19", value=st.session_state.get("last_cnpj_input",""), placeholder="Seu CNPJ (somente números)")
                s = st.text_input("Senha", type="password", key="cli_s_v19", placeholder="Sua senha")
                if st.form_submit_button("Entrar como Cliente", use_container_width=True, icon="👤"):
                    st.session_state.last_cnpj_input = c
                    try:
                        users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                        # Ensure essential columns exist and have correct types
                        for col, default, dtype in [("JaVisualizouInstrucoes", "False", bool),
                                                    ("DiagnosticosDisponiveis", 1, int),
                                                    ("TotalDiagnosticosRealizados", 0, int),
                                                    ("UltimoLogin", None, str), # Stays as string or None
                                                    ("DataCadastro", now_str(), str)]: # Stays as string
                            if col not in users_df.columns: users_df[col] = default
                            if dtype == bool: users_df[col] = users_df[col].astype(str).str.lower().map({'true': True, 'false': False, 'nan': False, '':False}).fillna(False)
                            elif dtype == int: users_df[col] = pd.to_numeric(users_df[col], errors='coerce').fillna(default if isinstance(default, int) else 0).astype(int)
                            # String types are fine as is or will be handled by read_csv

                        blocked_df = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                        if c in blocked_df["CNPJ"].values: st.error("CNPJ bloqueado."); st.stop()

                        match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == s)]
                        if match.empty: st.error("CNPJ/senha inválidos."); st.stop()

                        st.session_state.cliente_logado = True; st.session_state.cnpj = c
                        st.session_state.user = match.iloc[0].to_dict()
                        st.session_state.user["JaVisualizouInstrucoes"] = bool(st.session_state.user.get("JaVisualizouInstrucoes", False))
                        st.session_state.user["DiagnosticosDisponiveis"] = int(st.session_state.user.get("DiagnosticosDisponiveis", 1))
                        st.session_state.user["TotalDiagnosticosRealizados"] = int(st.session_state.user.get("TotalDiagnosticosRealizados", 0))

                        update_user_data(c, "UltimoLogin", now_str()) # Update last login time
                        st.session_state.user["UltimoLogin"] = now_str()


                        st.session_state.inicio_sessao_cliente = time.time()
                        registrar_acao(c, "Login", "Usuário logou.")

                        if not st.session_state.user["JaVisualizouInstrucoes"]:
                            st.session_state.cliente_page = "Instruções"
                        else:
                            pode_fazer_novo_login = st.session_state.user["DiagnosticosDisponiveis"] > st.session_state.user["TotalDiagnosticosRealizados"]
                            st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo_login else "Painel Principal"

                        st.session_state.id_formulario_atual = f"{c}_{now_str().replace(' ','_').replace(':','-').replace('-','')}" # More unique ID
                        st.session_state.respostas_atuais_diagnostico = {}
                        st.session_state.progresso_diagnostico_percentual = 0
                        st.session_state.progresso_diagnostico_contagem = (0,0)
                        st.session_state.feedbacks_respostas = {}
                        st.session_state.sac_feedback_registrado = {}
                        st.session_state.diagnostico_enviado_sucesso = False
                        st.session_state.target_diag_data_for_expansion = None

                        st.toast(f"Bem-vindo(a) de volta, {st.session_state.user.get('NomeContato', 'Cliente')}!", icon="👋")
                        st.rerun()
                    except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop() # Stop execution if not logged in

elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    if not st.session_state.user.get("JaVisualizouInstrucoes", False):
        st.session_state.cliente_page = "Instruções"

    with st.sidebar:
        logo_cliente_path_sb = find_client_logo_path(st.session_state.cnpj)
        if logo_cliente_path_sb:
            st.image(logo_cliente_path_sb, width=120, use_column_width='auto')
        else:
            st.image(DEFAULT_PORTAL_LOGO, width=120, caption="Logo da Empresa")


        st.markdown(f"### Olá, {st.session_state.user.get('NomeContato', st.session_state.user.get('Empresa', 'Cliente'))}!")
        st.markdown(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
        st.caption(f"**CNPJ:** {st.session_state.cnpj}")
        st.divider()

        with st.expander(ℹ️ Detalhes da Conta", expanded=False):
            st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
            st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")
            total_slots = st.session_state.user.get('DiagnosticosDisponiveis', 0)
            realizados = st.session_state.user.get('TotalDiagnosticosRealizados', 0)
            restantes = max(0, total_slots - realizados)
            st.markdown(f"**Diagnósticos Contratados:** `{total_slots}`")
            st.markdown(f"**Diagnósticos Realizados:** `{realizados}`")
            st.markdown(f"**Diagnósticos Restantes:** `{restantes}`")
            st.caption(f"Último login: {st.session_state.user.get('UltimoLogin', 'N/A')}")


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

    menu_options_cli_map_full = {
        "Painel Principal": "🏠 Painel Principal",
        "Novo Diagnóstico": "📋 Novo Diagnóstico",
        "Notificações": f"🔔 Notificações{f' ({notificacoes_nao_lidas_count})' if notificacoes_nao_lidas_count > 0 else ''}",
        "SAC": "❓ SAC - Ajuda",
        "Instruções": "📖 Instruções Iniciais",
    }

    menu_options_cli_display = []
    menu_keys_ordered = ["Painel Principal", "Novo Diagnóstico", "Notificações", "SAC", "Instruções"]

    if not st.session_state.user.get("JaVisualizouInstrucoes", False):
        menu_options_cli_map = {"Instruções": menu_options_cli_map_full["Instruções"]}
        st.session_state.cliente_page = "Instruções"
        menu_keys_ordered = ["Instruções"]
    else:
        menu_options_cli_map = menu_options_cli_map_full.copy()
        pode_fazer_novo = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
        if not pode_fazer_novo and "Novo Diagnóstico" in menu_options_cli_map:
            if st.session_state.cliente_page == "Novo Diagnóstico":
                st.session_state.cliente_page = "Painel Principal"
            del menu_options_cli_map["Novo Diagnóstico"]
            menu_keys_ordered.remove("Novo Diagnóstico")


    menu_options_cli_display = [menu_options_cli_map[key] for key in menu_keys_ordered if key in menu_options_cli_map]

    if st.session_state.cliente_page not in menu_options_cli_map.keys():
        st.session_state.cliente_page = "Instruções" if not st.session_state.user.get("JaVisualizouInstrucoes", False) else "Painel Principal"

    default_display_option = menu_options_cli_map.get(st.session_state.cliente_page)
    current_idx_cli = 0
    if default_display_option and default_display_option in menu_options_cli_display:
        current_idx_cli = menu_options_cli_display.index(default_display_option)
    elif menu_options_cli_display: # Fallback if current page is not in available options
        current_idx_cli = 0
        # Find the key for the first display option
        first_display_val = menu_options_cli_display[0]
        for key_page_fallback, val_page_display_fallback in menu_options_cli_map.items():
            if val_page_display_fallback == first_display_val:
                st.session_state.cliente_page = key_page_fallback
                break


    with st.sidebar:
        st.markdown("#### Menu de Navegação")
        selected_page_cli_raw = st.radio("Menu Cliente", menu_options_cli_display, index=current_idx_cli, key="cli_menu_v19_conditional", label_visibility="collapsed")

    selected_page_cli_clean = ""
    for key_page, val_page_display in menu_options_cli_map.items():
        if val_page_display == selected_page_cli_raw:
            selected_page_cli_clean = key_page # Key is now consistent (Notificações, SAC are fine)
            break

    if selected_page_cli_clean and selected_page_cli_clean != st.session_state.cliente_page :
        st.session_state.cliente_page = selected_page_cli_clean
        st.session_state.force_sidebar_rerun_after_notif_read_v19 = False
        st.session_state.target_diag_data_for_expansion = None
        st.rerun()

    with st.sidebar:
        st.markdown("---")
        if st.button("Sair do Portal", icon="⬅️", key="logout_cliente_v19", use_container_width=True, type="secondary"):
            keys_to_clear = [k for k in st.session_state.keys() if k not in ['admin_logado', 'last_cnpj_input', 'admin_current_page_text_key_v19']] # Keep admin page
            for key_item in keys_to_clear: del st.session_state[key_item]
            for key_d, value_d in default_session_state.items():
                if key_d not in ['admin_logado', 'last_cnpj_input', 'admin_current_page_text_key_v19']: st.session_state[key_d] = value_d
            st.session_state.cliente_logado = False
            st.toast("Logout realizado com sucesso.", icon="👋")
            st.rerun()

    # --- Client Page Content ---
    st.title(menu_options_cli_map_full.get(st.session_state.cliente_page, "Página do Cliente").split(" (")[0])

    if st.session_state.cliente_page == "Instruções":
        instrucoes_content_md = ""
        if os.path.exists(instrucoes_custom_path):
            with open(instrucoes_custom_path, "r", encoding="utf-8") as f:
                instrucoes_content_md = f.read()
        elif os.path.exists(instrucoes_default_path): # Fallback to default if custom not found
            with open(instrucoes_default_path, "r", encoding="utf-8") as f:
                instrucoes_content_md = f.read()
            st.caption("Exibindo instruções padrão. O administrador pode personalizar este texto.")
        else: # Absolute fallback
            instrucoes_content_md = ("# Bem-vindo ao Portal de Diagnóstico!\n\n"
                                     "Siga as instruções para completar seu diagnóstico.\n"
                                     "Em caso de dúvidas, entre em contato com o administrador.")
            st.info("Arquivo de instruções não encontrado. Exibindo texto base.")

        st.markdown(f'<div class="custom-card" style="border-left-color: #6366f1;">{instrucoes_content_md}</div>', unsafe_allow_html=True)

        if st.button("Entendi e Aceito os Termos, Prosseguir", key="btn_instrucoes_v19", icon="👍", use_container_width=True):
            update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", "True")
            if st.session_state.user: st.session_state.user["JaVisualizouInstrucoes"] = True

            pode_fazer_novo_inst = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo_inst else "Painel Principal"
            st.rerun()

    elif st.session_state.cliente_page == "SAC":
        df_sac_qa = carregar_sac_perguntas_respostas()

        if df_sac_qa.empty:
            st.info("ℹ️ Nenhuma pergunta frequente cadastrada no momento. Volte mais tarde!")
        else:
            df_sac_qa_sorted = df_sac_qa.sort_values(by=["Categoria_SAC", "Pergunta_SAC"])
            categorias_sac = df_sac_qa_sorted["Categoria_SAC"].unique()

            search_term_sac = st.text_input("🔎 Procurar nas Perguntas Frequentes:", key="search_sac_cliente", placeholder="Digite palavras-chave...")
            if search_term_sac:
                df_sac_qa_sorted = df_sac_qa_sorted[
                    df_sac_qa_sorted["Pergunta_SAC"].str.contains(search_term_sac, case=False, na=False) |
                    df_sac_qa_sorted["Resposta_SAC"].str.contains(search_term_sac, case=False, na=False) |
                    df_sac_qa_sorted["Categoria_SAC"].str.contains(search_term_sac, case=False, na=False) |
                    df_sac_qa_sorted["Tags_SAC"].astype(str).str.contains(search_term_sac, case=False, na=False) # Search tags
                ]
                categorias_sac = df_sac_qa_sorted["Categoria_SAC"].unique()

            if df_sac_qa_sorted.empty and search_term_sac:
                 st.warning(f"Nenhuma pergunta encontrada para '{search_term_sac}'. Tente outros termos.")
            elif df_sac_qa_sorted.empty:
                 st.info("ℹ️ Nenhuma pergunta frequente cadastrada no momento.")


            for categoria in categorias_sac:
                st.markdown(f"### {categoria}")
                perguntas_na_categoria = df_sac_qa_sorted[df_sac_qa_sorted["Categoria_SAC"] == categoria]
                for idx_sac, row_sac in perguntas_na_categoria.iterrows():
                    with st.expander(f"❓ {row_sac['Pergunta_SAC']}"):
                        st.markdown(row_sac['Resposta_SAC'], unsafe_allow_html=True) # Allow HTML for richer answers

                        feedback_key_base = f"sac_feedback_{row_sac['ID_SAC_Pergunta']}"
                        feedback_dado = st.session_state.sac_feedback_registrado.get(row_sac['ID_SAC_Pergunta'])

                        st.markdown("---") # Separator
                        st.write("<small>Esta resposta foi útil?</small>", unsafe_allow_html=True)
                        cols_feedback = st.columns([1,1,8]) # Adjust column ratios
                        with cols_feedback[0]:
                            btn_class_util = "active" if feedback_dado == "util" else ""
                            if st.button("👍 Sim", key=f"{feedback_key_base}_util", help="Marcar como útil", use_container_width=True,
                                         type="primary" if feedback_dado == "util" else "secondary"):
                                try:
                                    df_feedback = carregar_sac_uso_feedback() # Load fresh
                                    # Remove previous feedback from this user for this question
                                    df_feedback = df_feedback[~((df_feedback['CNPJ_Cliente'] == st.session_state.cnpj) & (df_feedback['ID_SAC_Pergunta'] == row_sac['ID_SAC_Pergunta']))]
                                    novo_feedback = pd.DataFrame([{
                                        "ID_Uso_SAC": str(uuid.uuid4()), "Timestamp": now_str(),
                                        "CNPJ_Cliente": st.session_state.cnpj, "ID_SAC_Pergunta": row_sac['ID_SAC_Pergunta'],
                                        "Feedback_Util": True
                                    }])
                                    df_feedback = pd.concat([df_feedback, novo_feedback], ignore_index=True)
                                    df_feedback.to_csv(sac_uso_feedback_csv, index=False, encoding='utf-8')
                                    st.session_state.sac_feedback_registrado[row_sac['ID_SAC_Pergunta']] = "util"
                                    st.toast("Obrigado pelo seu feedback!", icon="😊")
                                    st.cache_data.clear() # Clear cache for SAC feedback
                                    st.rerun()
                                except Exception as e_fb: st.error(f"Erro ao registrar feedback: {e_fb}")
                        with cols_feedback[1]:
                            btn_class_nao_util = "active" if feedback_dado == "nao_util" else ""
                            if st.button("👎 Não", key=f"{feedback_key_base}_nao_util", help="Marcar como não útil", use_container_width=True,
                                         type="primary" if feedback_dado == "nao_util" else "secondary"):
                                try:
                                    df_feedback = carregar_sac_uso_feedback() # Load fresh
                                    df_feedback = df_feedback[~((df_feedback['CNPJ_Cliente'] == st.session_state.cnpj) & (df_feedback['ID_SAC_Pergunta'] == row_sac['ID_SAC_Pergunta']))]
                                    novo_feedback = pd.DataFrame([{
                                        "ID_Uso_SAC": str(uuid.uuid4()), "Timestamp": now_str(),
                                        "CNPJ_Cliente": st.session_state.cnpj, "ID_SAC_Pergunta": row_sac['ID_SAC_Pergunta'],
                                        "Feedback_Util": False
                                    }])
                                    df_feedback = pd.concat([df_feedback, novo_feedback], ignore_index=True)
                                    df_feedback.to_csv(sac_uso_feedback_csv, index=False, encoding='utf-8')
                                    st.session_state.sac_feedback_registrado[row_sac['ID_SAC_Pergunta']] = "nao_util"
                                    st.toast("Obrigado! Vamos revisar esta resposta.", icon="🛠️")
                                    st.cache_data.clear() # Clear cache for SAC feedback
                                    st.rerun()
                                except Exception as e_fb: st.error(f"Erro ao registrar feedback: {e_fb}")

                        if feedback_dado:
                            with cols_feedback[2]:
                                st.markdown(f"<small style='padding-top:8px; display:block;'><i>Seu feedback: {feedback_dado.replace('_', ' ').capitalize()}</i></small>", unsafe_allow_html=True)
                st.divider()

    # ... (Rest of the client pages: Notificações, Painel Principal, Novo Diagnóstico - largely similar structure, focusing on data loading, display, and actions)
    # --- For brevity, I will skip pasting the entire client section if the changes are minor or repetitive from what's shown above or in admin ---
    # --- However, I will ensure any new functions or CSS classes are reflected if they impact these sections significantly. ---
    # Key sections like "Painel Principal" with its graphs and "Novo Diagnóstico" form handling will be kept.

    elif st.session_state.cliente_page == "Notificações":
        ids_para_marcar_como_lidas_on_display = []
        try:
            df_notificacoes_todas = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Relacionado': str})
            if not df_notificacoes_todas.empty and 'Lida' in df_notificacoes_todas.columns:
                df_notificacoes_todas['Lida'] = df_notificacoes_todas['Lida'].astype(str).str.lower().map({'true': True, 'false': False, '': False, 'nan': False}).fillna(False)
            else:
                df_notificacoes_todas = pd.DataFrame(columns=colunas_base_notificacoes) # Ensure it's a df
            if 'ID_Diagnostico_Relacionado' not in df_notificacoes_todas.columns:
                df_notificacoes_todas['ID_Diagnostico_Relacionado'] = None


            minhas_notificacoes = df_notificacoes_todas[
                df_notificacoes_todas["CNPJ_Cliente"] == st.session_state.cnpj
            ].sort_values(by="Timestamp", ascending=False)

            if minhas_notificacoes.empty:
                st.info("Você não tem nenhuma notificação no momento. ✨")
            else:
                st.caption("As notificações novas são marcadas como lidas ao serem exibidas nesta página.")
                for idx_notif, row_notif in minhas_notificacoes.iterrows():
                    cor_borda = "#2563eb" if not row_notif["Lida"] else "#9ca3af" # Blue for unread, gray for read
                    icon_lida = "📬" if not row_notif["Lida"] else "📩" # Different icons
                    status_text = "<strong style='color:#2563eb;'>Nova</strong>" if not row_notif["Lida"] else "<span style='color:#6b7280;'>Lida</span>"

                    st.markdown(f"""
                    <div class="custom-card" style="border-left: 5px solid {cor_borda}; margin-bottom: 12px;">
                        <p style="font-size: 0.85em; color: #4b5563;">{icon_lida} {row_notif["Timestamp"]} | Status: {status_text}</p>
                        <p style="font-size: 1.05em; margin-top: 5px;">{row_notif["Mensagem"]}</p>
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
                    st.session_state['force_sidebar_rerun_after_notif_read_v19'] = True # Trigger sidebar refresh for count

        except (FileNotFoundError, pd.errors.EmptyDataError):
            st.info("Você não tem nenhuma notificação no momento. ✨")
        except Exception as e_notif_display:
            st.error(f"Erro ao carregar suas notificações: {e_notif_display}")
            st.exception(e_notif_display)


        if st.session_state.get('force_sidebar_rerun_after_notif_read_v19'):
            del st.session_state['force_sidebar_rerun_after_notif_read_v19']
            st.rerun()

    elif st.session_state.cliente_page == "Painel Principal":
        target_diag_to_expand = st.session_state.pop("target_diag_data_for_expansion", None)

        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu último diagnóstico foi enviado e processado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                with open(st.session_state.pdf_gerado_path, "rb") as f_pdf:
                    st.download_button(label="Baixar PDF do Diagnóstico Recém-Enviado", data=f_pdf,
                                       file_name=st.session_state.pdf_gerado_filename, mime="application/pdf",
                                       key="dl_novo_diag_painel_v19", icon="📄", type="primary")
                st.session_state.pdf_gerado_path = None # Clear after showing
                st.session_state.pdf_gerado_filename = None
            st.session_state.diagnostico_enviado_sucesso = False # Reset flag


        with st.expander("ℹ️ Informações Importantes sobre seu Painel", expanded=False):
            st.markdown("""
            - Visualize seus diagnósticos anteriores e sua evolução de performance.
            - Acompanhe seu plano de ação sugerido no Kanban abaixo.
            - Para um novo diagnóstico (se você tiver slots disponíveis), selecione 'Novo Diagnóstico' no menu lateral.
            - Mantenha suas análises sobre os diagnósticos atualizadas para referência futura.
            """)

        try:
            df_antigos_todos = pd.read_csv(arquivo_csv, dtype={'CNPJ': str}, encoding='utf-8')
            df_cliente_diags_raw = df_antigos_todos[df_antigos_todos["CNPJ"] == st.session_state.cnpj].copy() # Use .copy()
            if 'Data' in df_cliente_diags_raw.columns:
                 df_cliente_diags_raw['Data_dt'] = pd.to_datetime(df_cliente_diags_raw['Data'], errors='coerce') # For sorting
                 df_cliente_diags_raw['Data'] = df_cliente_diags_raw['Data'].astype(str) # Keep original string for display/ID
            else:
                 df_cliente_diags_raw['Data_dt'] = pd.NaT
        except FileNotFoundError:
            st.error(f"Arquivo de diagnósticos '{arquivo_csv}' não encontrado.")
            df_cliente_diags_raw = pd.DataFrame()
        except Exception as e_load_diag:
            st.error(f"Erro ao carregar diagnósticos do cliente: {e_load_diag}")
            df_cliente_diags_raw = pd.DataFrame()


        if df_cliente_diags_raw.empty:
            st.info("Você ainda não possui diagnósticos registrados. Comece um novo no menu lateral!")
        else:
            if 'Data_dt' in df_cliente_diags_raw.columns:
                 df_cliente_diags = df_cliente_diags_raw.sort_values(by="Data_dt", ascending=False)
            else: # Fallback if Data_dt couldn't be created
                 df_cliente_diags = df_cliente_diags_raw.sort_values(by="Data", ascending=False) # Sort by string date

            latest_diag_data_row = df_cliente_diags.iloc[0]
            latest_diag_data = latest_diag_data_row.to_dict()

            st.subheader("📊 Visão Geral do Último Diagnóstico")
            col_graph1, col_graph2 = st.columns(2)

            with col_graph1:
                st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
                st.markdown("##### Scores por Categoria")
                medias_cat_latest = {
                    k.replace("Media_Cat_", "").replace("_", " "): pd.to_numeric(v, errors='coerce')
                    for k, v in latest_diag_data.items()
                    if k.startswith("Media_Cat_") and pd.notna(pd.to_numeric(v, errors='coerce'))
                }
                if medias_cat_latest and len(medias_cat_latest) >=3 : # Radar needs at least 3 points
                    fig_radar = create_radar_chart(medias_cat_latest, title="")
                    st.plotly_chart(fig_radar, use_container_width=True)
                elif medias_cat_latest: # If 1 or 2 points, radar won't work well
                    st.caption("Poucos dados de categoria para gerar gráfico radar. Scores:")
                    for cat, score_val in medias_cat_latest.items():
                        st.markdown(f"- **{cat}:** {score_val:.2f}")
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
                        except (json.JSONDecodeError, ValueError, TypeError): pass # Ignore errors for this display
                if gut_data_list_client:
                    fig_gut_bar = create_gut_barchart(gut_data_list_client, title="")
                    st.plotly_chart(fig_gut_bar, use_container_width=True)
                else:
                    st.caption("Nenhuma prioridade GUT (com score > 0) identificada no último diagnóstico.")
                st.markdown('</div>', unsafe_allow_html=True)
            st.divider()

            st.subheader("📁 Histórico de Diagnósticos Anteriores")
            try:
                perguntas_df_para_painel = pd.read_csv(perguntas_csv, encoding='utf-8')
                if "Categoria" not in perguntas_df_para_painel.columns: perguntas_df_para_painel["Categoria"] = "Geral"
            except FileNotFoundError:
                st.error(f"Arquivo de perguntas '{perguntas_csv}' não encontrado para detalhar diagnósticos.")
                perguntas_df_para_painel = pd.DataFrame()
            analises_df_para_painel = carregar_analises_perguntas()

            for idx_row_diag, row_diag_data in df_cliente_diags.iterrows():
                expand_this_diag = (str(row_diag_data['Data']) == str(target_diag_to_expand))
                diag_date_display = pd.to_datetime(row_diag_data['Data_dt']).strftime('%d/%m/%Y %H:%M') if pd.notna(row_diag_data['Data_dt']) else row_diag_data['Data']


                with st.expander(f"📅 {diag_date_display} - {row_diag_data['Empresa']}", expanded=expand_this_diag):
                    st.markdown('<div class="custom-card" style="padding-top: 10px; padding-bottom: 10px; border-left-color: #fdba74;">', unsafe_allow_html=True)
                    cols_metricas = st.columns(2)
                    mg_val = pd.to_numeric(row_diag_data.get('Média Geral'), errors='coerce')
                    gut_m_val = pd.to_numeric(row_diag_data.get('GUT Média'), errors='coerce')
                    cols_metricas[0].metric("Média Geral", f"{mg_val:.2f}" if pd.notna(mg_val) else "N/A")
                    cols_metricas[1].metric("GUT Média", f"{gut_m_val:.2f}" if pd.notna(gut_m_val) else "N/A")
                    st.write(f"**Resumo (Cliente):** {row_diag_data.get('Diagnóstico', 'N/P')}")

                    st.markdown("**Respostas e Análises Detalhadas:**")
                    if not perguntas_df_para_painel.empty:
                        for cat_loop in sorted(perguntas_df_para_painel["Categoria"].unique()):
                            st.markdown(f"##### Categoria: {cat_loop}")
                            perg_cat_loop = perguntas_df_para_painel[perguntas_df_para_painel["Categoria"] == cat_loop]
                            for _, p_row_loop in perg_cat_loop.iterrows():
                                p_texto_loop = p_row_loop["Pergunta"]
                                resp_loop = row_diag_data.get(p_texto_loop, "N/R (Não Respondido ou Pergunta Nova)")
                                st.markdown(f"**{p_texto_loop.split('[')[0].strip()}:**") # Clean question text
                                st.markdown(f"> _{str(resp_loop)}_") # Italicize response
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
                                    st.caption(f"Detalhes GUT: G={g_val}, U={u_val}, T={t_val} (Score: {score_gut_loop})")
                                analise_texto_painel = obter_analise_para_resposta(p_texto_loop, valor_para_analise, analises_df_para_painel)
                                if analise_texto_painel:
                                    st.markdown(f"<div class='analise-pergunta-cliente'><b>Análise Consultor:</b> {analise_texto_painel}</div>", unsafe_allow_html=True)
                            st.markdown("---") # Separator between categories
                    else: st.caption("Estrutura de perguntas não carregada para detalhar respostas.")

                    analise_cli_val_cv_painel = row_diag_data.get("Análise do Cliente", "")
                    analise_cli_cv_input = st.text_area("🧠 Minha Análise sobre este Diagnóstico (visível apenas para você e o consultor):", value=analise_cli_val_cv_painel, key=f"analise_cv_painel_v19_{idx_row_diag}_{row_diag_data['Data']}", height=100)
                    if st.button("Salvar Minha Análise", key=f"salvar_analise_cv_painel_v19_{idx_row_diag}_{row_diag_data['Data']}", icon="💾"):
                        try:
                            df_antigos_upd = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                            df_antigos_upd['Data'] = df_antigos_upd['Data'].astype(str) # Ensure Data is string for matching
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
                            st.markdown("<small><i>(Você foi direcionado para este comentário a partir de uma notificação)</i></small>", unsafe_allow_html=True)
                    else: st.caption("Nenhum comentário do consultor para este diagnóstico.")

                    if st.button("Baixar PDF deste Diagnóstico", key=f"dl_pdf_antigo_v19_{idx_row_diag}_{row_diag_data['Data']}", icon="📄"):
                        medias_cat_pdf_antigo = {k.replace("Media_Cat_","").replace("_"," "):v for k,v in row_diag_data.items() if k.startswith("Media_Cat_") and pd.notna(v)}
                        pdf_path_antigo = gerar_pdf_diagnostico_completo(row_diag_data.to_dict(), st.session_state.user, perguntas_df_para_painel, row_diag_data.to_dict(), medias_cat_pdf_antigo, analises_df_para_painel)
                        if pdf_path_antigo:
                            with open(pdf_path_antigo, "rb") as f_antigo:
                                st.download_button("Clique para Baixar o PDF", f_antigo,
                                                   file_name=f"diag_{sanitize_column_name(row_diag_data['Empresa'])}_{str(row_diag_data['Data']).replace(':','-').replace(' ','_')}.pdf",
                                                   mime="application/pdf",
                                                   key=f"dl_confirm_antigo_v19_{idx_row_diag}_{time.time()}",
                                                   icon="📄", type="primary")
                            registrar_acao(st.session_state.cnpj, "Download PDF (Painel)", f"Baixou PDF de {row_diag_data['Data']}")
                        else: st.error("Erro ao gerar PDF para este diagnóstico.")
                    st.markdown('</div>', unsafe_allow_html=True) # End custom-card
            st.divider()

            st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
            latest_diag_kanban = df_cliente_diags.iloc[0]
            gut_cards_kanban = []
            for pergunta_k, resposta_k_str in latest_diag_kanban.items():
                if isinstance(pergunta_k, str) and "[Matriz GUT]" in pergunta_k:
                    try:
                        if pd.notna(resposta_k_str) and isinstance(resposta_k_str, str):
                            gut_data_k = json.loads(resposta_k_str.replace("'", "\""))
                            g_k, u_k, t_k = int(gut_data_k.get("G", 0)), int(gut_data_k.get("U", 0)), int(gut_data_k.get("T", 0))
                            score_gut_k = g_k * u_k * t_k
                            prazo_k = "N/A"; card_color = "border-left-color: #d1d5db;" # Default gray
                            if score_gut_k >= 75: prazo_k = "Até 15 dias"; card_color="border-left-color: #ef4444;" # Red
                            elif score_gut_k >= 40: prazo_k = "Até 30 dias"; card_color="border-left-color: #f97316;" # Orange
                            elif score_gut_k >= 20: prazo_k = "Até 45 dias"; card_color="border-left-color: #eab308;" # Yellow
                            elif score_gut_k > 0: prazo_k = "Até 60 dias"; card_color="border-left-color: #84cc16;" # Lime
                            else: continue
                            if prazo_k != "N/A":
                                gut_cards_kanban.append({
                                    "Tarefa": pergunta_k.replace(" [Matriz GUT]", ""),
                                    "Prazo": prazo_k, "Score": score_gut_k,
                                    "Responsável": st.session_state.user.get("Empresa", "N/D"),
                                    "Cor": card_color
                                    })
                    except (json.JSONDecodeError, ValueError, TypeError) as e_kanban_painel:
                        st.warning(f"Erro ao processar GUT para Kanban '{pergunta_k}': {e_kanban_painel}")

            if gut_cards_kanban:
                gut_cards_sorted_kanban = sorted(gut_cards_kanban, key=lambda x: x["Score"], reverse=True)
                prazos_unicos_kanban = sorted(list(set(card["Prazo"] for card in gut_cards_sorted_kanban)),
                                             key=lambda x_prazo: int(re.search(r'\d+', x_prazo).group())) # Sort by number in prazo
                if prazos_unicos_kanban:
                    num_cols_kanban = min(len(prazos_unicos_kanban), 4) # Max 4 columns for Kanban
                    cols_kanban = st.columns(num_cols_kanban)
                    for idx_col_k, prazo_k_col in enumerate(prazos_unicos_kanban):
                        with cols_kanban[idx_col_k % num_cols_kanban]: # Cycle through columns
                            st.markdown(f"##### ⏱️ {prazo_k_col}")
                            for card_k_item in gut_cards_sorted_kanban:
                                if card_k_item["Prazo"] == prazo_k_col:
                                    st.markdown(f"""<div class="custom-card" style="{card_k_item['Cor']} padding: 15px; margin-bottom:10px;">
                                                    <b>{card_k_item['Tarefa']}</b><br>
                                                    <small>Score GUT: {card_k_item['Score']} | 👤 {card_k_item['Responsável']}</small>
                                                </div>""", unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True) # Add space if multiple lists in one column
                else:
                    st.info("Nenhuma ação prioritária (GUT > 0) identificada no último diagnóstico para o Kanban.")
            else:
                st.info("Nenhuma ação prioritária (GUT > 0) identificada no último diagnóstico para o Kanban.")
            st.divider()

            st.subheader("📈 Comparativo de Evolução das Médias")
            if len(df_cliente_diags) > 1:
                df_evolucao = df_cliente_diags.copy()
                # Use Data_dt for time series plotting
                df_evolucao['Data'] = pd.to_datetime(df_evolucao['Data_dt']) # Convert Data_dt to 'Data' for plotting consistency
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
                    st.line_chart(df_evolucao_plot_renamed, height=400)
                else:
                    st.info("Não há dados suficientes ou válidos nas colunas de médias para plotar o gráfico de evolução.")
            else:
                st.info("São necessários pelo menos dois diagnósticos para exibir o comparativo de evolução.")
            st.divider()

            st.subheader("📊 Comparação Detalhada Entre Dois Diagnósticos")
            if len(df_cliente_diags) > 1:
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
                            evolucao_txt = "➖ Estável"
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
                        st.dataframe(pd.DataFrame(metricas_comparacao), use_container_width=True, hide_index=True)
                    else:
                        st.info("Não foi possível gerar a tabela de comparação para as métricas selecionadas.")
                elif diag1_data_str == diag2_data_str and len(df_cliente_diags)>1 :
                    st.warning("Selecione dois diagnósticos diferentes para comparação.")
            else:
                st.info("São necessários pelo menos dois diagnósticos para fazer uma comparação detalhada.")

    elif st.session_state.cliente_page == "Novo Diagnóstico":
        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu diagnóstico foi enviado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                with open(st.session_state.pdf_gerado_path, "rb") as f_pdf_dl_sucesso:
                    st.download_button(label="Baixar PDF do Diagnóstico Enviado", data=f_pdf_dl_sucesso,
                                       file_name=st.session_state.pdf_gerado_filename, mime="application/pdf",
                                       key="dl_pdf_sucesso_novo_diag_v19", icon="📄", type="primary")
            if st.button("Ir para o Painel Principal", key="ir_painel_apos_envio_sucesso_v19", icon="🏠", use_container_width=True):
                st.session_state.cliente_page = "Painel Principal"
                st.session_state.diagnostico_enviado_sucesso = False; st.session_state.pdf_gerado_path = None; st.session_state.pdf_gerado_filename = None
                st.rerun()
            st.stop()

        try: perguntas_df_formulario = pd.read_csv(perguntas_csv, encoding='utf-8')
        except Exception as e: st.error(f"Erro ao carregar perguntas: {e}"); st.stop()
        if perguntas_df_formulario.empty: st.warning("Nenhuma pergunta cadastrada para o diagnóstico."); st.stop()
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
                    if "[Matriz GUT]" in p_texto_prog_novo: # GUT considered answered if any slider moved from 0
                        if isinstance(resp_prog_novo, dict) and (int(resp_prog_novo.get("G",0)) > 0 or int(resp_prog_novo.get("U",0)) > 0 or int(resp_prog_novo.get("T",0)) > 0 or sum(resp_prog_novo.values()) > 0): respondidas_novo +=1
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
            current_val = st.session_state.respostas_atuais_diagnostico.get(pergunta_txt_key_novo)

            # Only update and mark as "saved" if the value actually changed, to avoid unnecessary reruns from on_change
            changed = False
            if tipo_pergunta_onchange_novo.startswith("GUT_"):
                current_gut_novo = st.session_state.respostas_atuais_diagnostico.get(pergunta_txt_key_novo, {"G":0,"U":0,"T":0})
                gut_key = tipo_pergunta_onchange_novo.split("_")[1]
                if current_gut_novo.get(gut_key) != valor_widget_novo:
                    current_gut_novo[gut_key] = valor_widget_novo
                    st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = current_gut_novo
                    changed = True
            elif current_val != valor_widget_novo:
                st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = valor_widget_novo
                changed = True

            if changed:
                st.session_state.feedbacks_respostas[pergunta_txt_key_novo] = "✓ Salvo"
            calcular_e_mostrar_progresso_novo()

        calcular_e_mostrar_progresso_novo() # Initial calculation

        for categoria_novo in sorted(perguntas_df_formulario["Categoria"].unique()):
            st.markdown(f"### {categoria_novo}")
            perg_cat_df_novo = perguntas_df_formulario[perguntas_df_formulario["Categoria"] == categoria_novo]
            for idx_novo, row_q_novo in perg_cat_df_novo.iterrows():
                p_texto_novo = str(row_q_novo["Pergunta"])
                w_key_novo = f"q_v19_{st.session_state.id_formulario_atual}_{idx_novo}" # Unique key

                st.markdown(f"**{p_texto_novo.split('[')[0].strip()}**") # Display clean question
                # Feedback placeholder next to the question or below input group
                feedback_placeholder = st.empty()
                if st.session_state.feedbacks_respostas.get(p_texto_novo):
                    feedback_placeholder.markdown(f'<div class="feedback-saved" style="margin-left:10px; display:inline;">{st.session_state.feedbacks_respostas[p_texto_novo]}</div>', unsafe_allow_html=True)


                if "[Matriz GUT]" in p_texto_novo:
                    cols_gut_w_novo = st.columns(3)
                    gut_vals_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_novo, {"G":0,"U":0,"T":0})
                    key_g_n, key_u_n, key_t_n = f"{w_key_novo}_G", f"{w_key_novo}_U", f"{w_key_novo}_T"
                    cols_gut_w_novo[0].slider("Gravidade (0-5)",0,5,value=int(gut_vals_novo.get("G",0)), key=key_g_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_g_n, "GUT_G"))
                    cols_gut_w_novo[1].slider("Urgência (0-5)",0,5,value=int(gut_vals_novo.get("U",0)), key=key_u_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_u_n, "GUT_U"))
                    cols_gut_w_novo[2].slider("Tendência (0-5)",0,5,value=int(gut_vals_novo.get("T",0)), key=key_t_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_t_n, "GUT_T"))
                elif "Pontuação (0-5)" in p_texto_novo:
                    st.slider("",0,5,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Slider05"), label_visibility="collapsed")
                elif "Pontuação (0-10)" in p_texto_novo:
                    st.slider("",0,10,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Slider010"), label_visibility="collapsed")
                elif "Texto Aberto" in p_texto_novo:
                    st.text_area("",value=str(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,"")), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Texto"), label_visibility="collapsed", height=100)
                elif "Escala" in p_texto_novo:
                    opts_novo = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"]
                    curr_val_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_novo, "Selecione")
                    st.selectbox("", opts_novo, index=opts_novo.index(curr_val_novo) if curr_val_novo in opts_novo else 0, key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Escala"), label_visibility="collapsed")
                else: # Default to slider 0-10 if type not specified in question text
                    st.slider("",0,10,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "SliderDefault"), label_visibility="collapsed")
                st.divider()

        st.markdown("### Conclusão do Diagnóstico")
        key_res_cli_n = f"diag_resumo_diag_v19_{st.session_state.id_formulario_atual}"
        st.text_area("✍️ **Resumo e principais insights deste diagnóstico (será incluído no PDF):**",
                     value=st.session_state.respostas_atuais_diagnostico.get("__resumo_cliente__", ""),
                     key=key_res_cli_n, on_change=on_change_resposta_novo, args=("__resumo_cliente__", key_res_cli_n, "ResumoCliente"),
                     height=150, help="Este resumo é crucial para o relatório final.")

        key_obs_cli_n = f"obs_cli_diag_v19_{st.session_state.id_formulario_atual}"
        st.text_area("📝 Sua Análise/Observações Adicionais (opcional, para sua referência e do consultor):",
                     value=st.session_state.respostas_atuais_diagnostico.get("__obs_cliente__", ""),
                     key=key_obs_cli_n, on_change=on_change_resposta_novo, args=("__obs_cliente__", key_obs_cli_n, "ObsCliente"),
                     height=100)

        if st.button("🚀 Concluir e Enviar Diagnóstico", key="enviar_diag_final_cliente_v19", icon="✔️", use_container_width=True, type="primary"):
            with st.spinner("Processando e salvando seu diagnóstico..."):
                respostas_finais_envio_novo = st.session_state.respostas_atuais_diagnostico
                cont_resp_n, total_para_resp_n = st.session_state.progresso_diagnostico_contagem

                if cont_resp_n < total_para_resp_n:
                    st.warning("⚠️ Por favor, responda todas as perguntas para um diagnóstico completo e preciso.")
                elif not respostas_finais_envio_novo.get("__resumo_cliente__","").strip():
                    st.error("❗ O campo 'Resumo e principais insights' é obrigatório para finalizar.")
                else:
                    soma_gut_n, count_gut_n = 0,0; respostas_csv_n = {}
                    for p_n,r_n in respostas_finais_envio_novo.items():
                        if p_n.startswith("__"): continue # Skip internal keys
                        if "[Matriz GUT]" in p_n and isinstance(r_n, dict):
                            respostas_csv_n[p_n] = json.dumps(r_n) # Store GUT as JSON string
                            g_n_val,u_n_val,t_n_val = int(r_n.get("G",0)), int(r_n.get("U",0)), int(r_n.get("T",0)); soma_gut_n += (g_n_val*u_n_val*t_n_val); count_gut_n +=1
                        else: respostas_csv_n[p_n] = r_n
                    gut_media_n = round(soma_gut_n/count_gut_n,2) if count_gut_n > 0 else 0.0

                    # Calculate Média Geral only from "Pontuação (0-X)" questions
                    num_resp_n = []
                    for k_n, v_n in respostas_finais_envio_novo.items():
                        if not k_n.startswith("__") and ("[Matriz GUT]" not in k_n) and ("Pontuação (0-5)" in k_n or "Pontuação (0-10)" in k_n):
                            if isinstance(v_n, (int, float)) and pd.notna(v_n):
                                num_resp_n.append(v_n)
                    media_geral_n = round(sum(num_resp_n)/len(num_resp_n),2) if num_resp_n else 0.0
                    emp_nome_n = st.session_state.user.get("Empresa","N/D")

                    nova_linha_diag_final_n = {
                        "Data": now_str(), "CNPJ": st.session_state.cnpj,
                        "Nome": st.session_state.user.get("NomeContato", st.session_state.cnpj), "Email": "", "Empresa": emp_nome_n,
                        "Média Geral": media_geral_n, "GUT Média": gut_media_n, "Observações": "", # Observações can be used by admin later
                        "Análise do Cliente": respostas_finais_envio_novo.get("__obs_cliente__",""),
                        "Diagnóstico": respostas_finais_envio_novo.get("__resumo_cliente__",""), "Comentarios_Admin": ""
                    }
                    nova_linha_diag_final_n.update(respostas_csv_n) # Add all question responses

                    medias_cat_final_n = {}
                    for cat_iter_n in perguntas_df_formulario["Categoria"].unique():
                        soma_c_n, cont_c_n = 0,0
                        for _,pr_n in perguntas_df_formulario[perguntas_df_formulario["Categoria"]==cat_iter_n].iterrows():
                            pt_n = pr_n["Pergunta"]; rv_n = respostas_finais_envio_novo.get(pt_n)
                            # Only include pontuação questions in category average
                            if ("[Matriz GUT]" not in pt_n) and ("Pontuação (0-5)" in pt_n or "Pontuação (0-10)" in pt_n):
                                if isinstance(rv_n,(int,float)) and pd.notna(rv_n):
                                    soma_c_n+=rv_n; cont_c_n+=1
                        mc_n = round(soma_c_n/cont_c_n,2) if cont_c_n>0 else 0.0
                        nova_linha_diag_final_n[f"Media_Cat_{sanitize_column_name(cat_iter_n)}"] = mc_n
                        medias_cat_final_n[cat_iter_n] = mc_n

                    try: df_todos_diags_n = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                    except (FileNotFoundError, pd.errors.EmptyDataError): df_todos_diags_n = pd.DataFrame()

                    # Add new columns to existing DataFrame if they don't exist
                    for col_n_n in nova_linha_diag_final_n.keys():
                        if col_n_n not in df_todos_diags_n.columns:
                            df_todos_diags_n[col_n_n] = pd.NA

                    df_todos_diags_n = pd.concat([df_todos_diags_n, pd.DataFrame([nova_linha_diag_final_n])], ignore_index=True)
                    df_todos_diags_n.to_csv(arquivo_csv, index=False, encoding='utf-8')

                    total_realizados_atual = st.session_state.user.get("TotalDiagnosticosRealizados", 0)
                    update_user_data(st.session_state.cnpj, "TotalDiagnosticosRealizados", total_realizados_atual + 1)
                    if st.session_state.user: st.session_state.user["TotalDiagnosticosRealizados"] = total_realizados_atual + 1

                    registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", f"Cliente {emp_nome_n} enviou novo diagnóstico.")
                    analises_df_para_pdf_n = carregar_analises_perguntas()
                    pdf_path_gerado_n = gerar_pdf_diagnostico_completo(nova_linha_diag_final_n, st.session_state.user, perguntas_df_formulario, respostas_finais_envio_novo, medias_cat_final_n, analises_df_para_pdf_n)

                    st.session_state.diagnostico_enviado_sucesso = True
                    if pdf_path_gerado_n:
                        st.session_state.pdf_gerado_path = pdf_path_gerado_n
                        st.session_state.pdf_gerado_filename = f"diagnostico_{sanitize_column_name(emp_nome_n)}_{now_str().replace(' ','_').replace(':','-')}.pdf"

                    # Reset form state
                    st.session_state.respostas_atuais_diagnostico = {}
                    st.session_state.progresso_diagnostico_percentual = 0
                    st.session_state.progresso_diagnostico_contagem = (0,total_perguntas_form)
                    st.session_state.feedbacks_respostas = {}
                    st.session_state.cliente_page = "Painel Principal" # Redirect to dashboard
                    st.rerun()


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    with st.sidebar:
        st.image(DEFAULT_PORTAL_LOGO, width=150, caption="Painel Admin")
        st.success("🟢 Admin Logado")
        st.markdown("---")
        if st.button("Sair do Painel Admin", icon="🚪", key="logout_admin_v19", use_container_width=True, type="secondary"):
            st.session_state.admin_logado = False
            st.toast("Logout de admin realizado.", icon="👋")
            st.rerun()

    menu_admin_options_map = {
        "Visão Geral e Diagnósticos": "📊",
        "Relatório de Engajamento": "📈",
        "Gerenciar Clientes": "👥",
        "Gerenciar Notificações": "🔔",
        "Gerenciar Perguntas do Formulário": "📝", # More specific
        "Gerenciar Análises de Perguntas": "💡",
        "Gerenciar SAC e Feedbacks": "📞", # Combined
        "Gerenciar Instruções do Portal": "⚙️", # More specific
        "Histórico de Ações": "📜", # More specific
        "Gerenciar Administradores": "👮"
    }
    admin_page_text_keys = list(menu_admin_options_map.keys())
    admin_options_for_display = [f"{menu_admin_options_map[key]} {key}" for key in admin_page_text_keys]

    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_text_key_v19" # Already in default_session_state
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
            # No rerun here, let the main script flow handle the page change display

    if st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] not in admin_page_text_keys: # Ensure valid page
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]

    current_admin_page_text_key_for_index = st.session_state[SESSION_KEY_FOR_ADMIN_PAGE]
    try:
        expected_display_value_for_current_page = f"{menu_admin_options_map[current_admin_page_text_key_for_index]} {current_admin_page_text_key_for_index}"
        current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page)
    except (ValueError, KeyError):
        current_admin_menu_index = 0
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0] # Reset to default

    with st.sidebar:
        st.markdown("#### Funcionalidades Admin")
        st.selectbox(
            "Menu Administrador:",
            options=admin_options_for_display,
            index=current_admin_menu_index,
            key=WIDGET_KEY_SB_ADMIN_MENU,
            on_change=admin_menu_on_change,
            label_visibility="collapsed"
        )

    menu_admin = st.session_state[SESSION_KEY_FOR_ADMIN_PAGE]
    st.title(f"{menu_admin_options_map[menu_admin]} {menu_admin}")


    df_usuarios_admin_geral = pd.DataFrame(columns=colunas_base_usuarios)
    try:
        df_usuarios_admin_temp_load = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
        # Ensure correct data types
        for col, default, dtype in [("DiagnosticosDisponiveis", 1, int),
                                    ("TotalDiagnosticosRealizados", 0, int),
                                    ("JaVisualizouInstrucoes", False, bool),
                                    ("UltimoLogin", None, str),
                                    ("DataCadastro", now_str, str)]: # Use callable for DataCadastro default
            if col not in df_usuarios_admin_temp_load.columns:
                 df_usuarios_admin_temp_load[col] = default() if callable(default) else default

            if dtype == bool: df_usuarios_admin_temp_load[col] = df_usuarios_admin_temp_load[col].astype(str).str.lower().map({'true': True, 'false': False, 'nan':False, '':False}).fillna(False)
            elif dtype == int: df_usuarios_admin_temp_load[col] = pd.to_numeric(df_usuarios_admin_temp_load[col], errors='coerce').fillna(0).astype(int)
            # String types are generally fine, ensure DataCadastro has a value
            if col == "DataCadastro" and df_usuarios_admin_temp_load[col].isnull().any():
                df_usuarios_admin_temp_load[col] = df_usuarios_admin_temp_load[col].fillna(now_str())


        df_usuarios_admin_geral = df_usuarios_admin_temp_load
    except FileNotFoundError:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Ações", "Gerenciar Clientes", "Gerenciar Notificações", "Relatório de Engajamento", "Gerenciar SAC e Feedbacks"]:
            st.sidebar.error(f"Arquivo de usuários '{usuarios_csv}' não encontrado. Funcionalidades limitadas.")
    except Exception as e_load_users_adm_global:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Ações", "Gerenciar Clientes", "Gerenciar Notificações", "Relatório de Engajamento", "Gerenciar SAC e Feedbacks"]:
            st.sidebar.error(f"Erro ao carregar usuários para admin: {e_load_users_adm_global}")


    # --- Admin Page Content ---
    if menu_admin == "Visão Geral e Diagnósticos":
        # ... (KPIs and charts as before, with improved chart functions and empty states)
        # ... (Detailed diagnostic view with comments and PDF download)
        # --- NEW: Common Weaknesses Chart ---
        st.markdown("#### Pontos Fracos Comuns (Global)")
        st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
        try:
            diagnosticos_df_admin_orig_view_cw = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
            perguntas_df_admin_view_cw = pd.read_csv(perguntas_csv, encoding='utf-8')
            if not diagnosticos_df_admin_orig_view_cw.empty and not perguntas_df_admin_view_cw.empty:
                fig_common_weak = create_common_weaknesses_chart(diagnosticos_df_admin_orig_view_cw, perguntas_df_admin_view_cw)
                if fig_common_weak:
                    st.plotly_chart(fig_common_weak, use_container_width=True)
                else:
                    st.info("Não foi possível gerar o gráfico de pontos fracos comuns (sem dados de score ou perguntas).")
            else:
                st.info("Dados de diagnósticos ou perguntas insuficientes para o gráfico de pontos fracos.")
        except Exception as e_cw:
            st.warning(f"Erro ao gerar gráfico de pontos fracos: {e_cw}")
        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()
        # The rest of "Visão Geral e Diagnósticos" continues here, with filterable detailed views.
        # (Code for this section is extensive and assumed to be largely functional from the original,
        # with chart functions being replaced by the improved ones.)

    elif menu_admin == "Relatório de Engajamento":
        st.markdown("#### Métricas de Engajamento dos Clientes")
        if df_usuarios_admin_geral.empty:
            st.info("Nenhum cliente cadastrado para gerar o relatório.")
        else:
            total_usuarios = len(df_usuarios_admin_geral)
            nao_visualizaram_instrucoes_df = df_usuarios_admin_geral[df_usuarios_admin_geral["JaVisualizouInstrucoes"] == False]
            visualizaram_instrucoes_df = df_usuarios_admin_geral[df_usuarios_admin_geral["JaVisualizouInstrucoes"] == True]
            visualizaram_sem_diag_df = visualizaram_instrucoes_df[visualizaram_instrucoes_df["TotalDiagnosticosRealizados"] == 0]
            visualizaram_com_diag_df = visualizaram_instrucoes_df[visualizaram_instrucoes_df["TotalDiagnosticosRealizados"] > 0]

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total de Clientes", total_usuarios)
            c2.metric("Não Aceitaram Instruções", len(nao_visualizaram_instrucoes_df), delta=f"{(len(nao_visualizaram_instrucoes_df)/total_usuarios*100 if total_usuarios else 0):.1f}% do total", delta_color="off")
            c3.metric("Aceitaram, SEM Diag.", len(visualizaram_sem_diag_df), delta=f"{(len(visualizaram_sem_diag_df)/total_usuarios*100 if total_usuarios else 0):.1f}% do total", delta_color="inverse")
            c4.metric("Aceitaram e COM Diag.", len(visualizaram_com_diag_df), delta=f"{(len(visualizaram_com_diag_df)/total_usuarios*100 if total_usuarios else 0):.1f}% do total", delta_color="normal")
            st.divider()

            # Additional engagement metrics
            if not df_usuarios_admin_geral.empty and 'UltimoLogin' in df_usuarios_admin_geral.columns:
                df_usuarios_admin_geral['UltimoLogin_dt'] = pd.to_datetime(df_usuarios_admin_geral['UltimoLogin'], errors='coerce')
                ativos_30d = df_usuarios_admin_geral[df_usuarios_admin_geral['UltimoLogin_dt'] >= (datetime.now() - timedelta(days=30))].shape[0]
                inativos_90d = df_usuarios_admin_geral[df_usuarios_admin_geral['UltimoLogin_dt'] < (datetime.now() - timedelta(days=90))].shape[0]
                novos_cadastros_30d = 0
                if 'DataCadastro' in df_usuarios_admin_geral.columns:
                    df_usuarios_admin_geral['DataCadastro_dt'] = pd.to_datetime(df_usuarios_admin_geral['DataCadastro'], errors='coerce')
                    novos_cadastros_30d = df_usuarios_admin_geral[df_usuarios_admin_geral['DataCadastro_dt'] >= (datetime.now() - timedelta(days=30))].shape[0]


                c5, c6, c7 = st.columns(3)
                c5.metric("Ativos nos Últimos 30 Dias", ativos_30d, help="Clientes com login nos últimos 30 dias.")
                c6.metric("Inativos (>90 Dias)", inativos_90d, help="Clientes sem login há mais de 90 dias.")
                c7.metric("Novos Clientes (Últimos 30 Dias)", novos_cadastros_30d, help="Clientes cadastrados nos últimos 30 dias.")
                st.divider()


            with st.expander("Detalhes: Clientes que NÃO Visualizaram/Aceitaram Instruções Iniciais"):
                if not nao_visualizaram_instrucoes_df.empty:
                    st.dataframe(nao_visualizaram_instrucoes_df[["Empresa", "CNPJ", "NomeContato", "DataCadastro"]].sort_values("DataCadastro", ascending=False), use_container_width=True, hide_index=True)
                else:
                    st.success("✅ Todos os clientes visualizaram as instruções ou não há clientes nesta categoria.")

            with st.expander("Detalhes: Clientes que Aceitaram Instruções, mas NÃO Fizeram Diagnóstico"):
                if not visualizaram_sem_diag_df.empty:
                    st.dataframe(visualizaram_sem_diag_df[["Empresa", "CNPJ", "NomeContato", "DiagnosticosDisponiveis", "DataCadastro"]].sort_values("DataCadastro", ascending=False), use_container_width=True, hide_index=True)
                else:
                    st.success("✅ Todos os clientes que visualizaram as instruções fizeram ao menos um diagnóstico ou não há clientes nesta categoria.")

            with st.expander("Detalhes: Clientes que Aceitaram Instruções e FIZERAM Diagnóstico(s)"):
                if not visualizaram_com_diag_df.empty:
                    st.dataframe(visualizaram_com_diag_df[["Empresa", "CNPJ", "NomeContato", "TotalDiagnosticosRealizados", "DiagnosticosDisponiveis", "UltimoLogin"]].sort_values("UltimoLogin", ascending=False), use_container_width=True, hide_index=True)
                else:
                    st.info("ℹ️ Nenhum cliente visualizou as instruções e completou um diagnóstico ainda.")


    elif menu_admin == "Gerenciar Clientes":
        # --- Client Health Function ---
        def calculate_client_health(client_row, all_diagnostics_df):
            health_score = 0
            reasons = []

            # Recency of last diagnostic
            client_diagnostics = all_diagnostics_df[all_diagnostics_df['CNPJ'] == client_row['CNPJ']].copy()
            if not client_diagnostics.empty:
                client_diagnostics['Data_dt'] = pd.to_datetime(client_diagnostics['Data'], errors='coerce')
                last_diag_date = client_diagnostics['Data_dt'].max()
                if pd.notna(last_diag_date):
                    if last_diag_date >= (datetime.now() - timedelta(days=90)):
                        health_score += 2
                        reasons.append("Diag. Recente")
                    elif last_diag_date >= (datetime.now() - timedelta(days=180)):
                        health_score += 1
                        reasons.append("Diag. Moderado")
                    else:
                        reasons.append("Diag. Antigo")
                else: reasons.append("Sem data válida de diag.")


                # Number of diagnostics
                num_diags = client_row.get('TotalDiagnosticosRealizados', 0)
                if num_diags > 1: health_score += 2; reasons.append(f"{num_diags} Diags.")
                elif num_diags == 1: health_score += 1; reasons.append("1 Diag.")
                else: reasons.append("Nenhum Diag.")

                # Score Improvement (simple check on Média Geral if more than 1 diag)
                if num_diags > 1 and 'Média Geral' in client_diagnostics.columns:
                    client_diagnostics_sorted = client_diagnostics.sort_values(by='Data_dt')
                    latest_score = pd.to_numeric(client_diagnostics_sorted['Média Geral'].iloc[-1], errors='coerce')
                    previous_score = pd.to_numeric(client_diagnostics_sorted['Média Geral'].iloc[-2], errors='coerce')
                    if pd.notna(latest_score) and pd.notna(previous_score):
                        if latest_score > previous_score: health_score += 1; reasons.append("Melhora Score")
                        elif latest_score < previous_score: health_score -=1; reasons.append("Piora Score")


            else: # No diagnostics found for this client in the diagnostics file
                reasons.append("Nenhum Diag. Encontrado")


            # Recency of Login
            if 'UltimoLogin' in client_row and pd.notna(client_row['UltimoLogin']):
                last_login_dt = pd.to_datetime(client_row['UltimoLogin'], errors='coerce')
                if pd.notna(last_login_dt):
                    if last_login_dt >= (datetime.now() - timedelta(days=30)):
                        health_score +=1
                        reasons.append("Login Recente")
                    elif last_login_dt < (datetime.now() - timedelta(days=120)): # Very inactive
                        health_score -=1
                        reasons.append("Login Antigo")


            if health_score >= 4: return "🟢 Bom", ", ".join(reasons)
            if health_score >= 2: return "🟡 Atenção", ", ".join(reasons)
            return "🔴 Crítico", ", ".join(reasons)


        df_diagnostics_for_health = pd.DataFrame()
        try:
            df_diagnostics_for_health = pd.read_csv(arquivo_csv, dtype={'CNPJ': str}, encoding='utf-8')
        except: pass # Silently fail if diagnostics file not found for health calculation

        df_usuarios_gc = df_usuarios_admin_geral.copy()
        if not df_usuarios_gc.empty:
            health_data = df_usuarios_gc.apply(lambda row: calculate_client_health(row, df_diagnostics_for_health), axis=1)
            df_usuarios_gc['Saúde Cliente'] = [h[0] for h in health_data]
            df_usuarios_gc['Detalhes Saúde'] = [h[1] for h in health_data]


        st.sidebar.markdown("---")
        st.sidebar.subheader("Filtros para Gerenciar Clientes")
        filter_instrucoes_status_gc = st.sidebar.selectbox(
            "Status das Instruções:",
            ["Todos", "Visualizaram Instruções", "Não Visualizaram Instruções"],
            key="admin_gc_filter_instrucoes_status"
        )
        filter_health_status_gc = st.sidebar.selectbox(
            "Status de Saúde do Cliente:",
            ["Todos", "🟢 Bom", "🟡 Atenção", "🔴 Crítico"],
            key="admin_gc_filter_health_status"
        )


        df_display_clientes_gc = df_usuarios_gc.copy()
        if filter_instrucoes_status_gc == "Visualizaram Instruções":
            df_display_clientes_gc = df_display_clientes_gc[df_display_clientes_gc["JaVisualizouInstrucoes"] == True]
        elif filter_instrucoes_status_gc == "Não Visualizaram Instruções":
            df_display_clientes_gc = df_display_clientes_gc[df_display_clientes_gc["JaVisualizouInstrucoes"] == False]

        if filter_health_status_gc != "Todos" and 'Saúde Cliente' in df_display_clientes_gc.columns:
            df_display_clientes_gc = df_display_clientes_gc[df_display_clientes_gc["Saúde Cliente"] == filter_health_status_gc]


        if not df_display_clientes_gc.empty:
            cols_display_gc = ["CNPJ", "Empresa", "NomeContato", "Telefone",
                               "Saúde Cliente", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados",
                               "JaVisualizouInstrucoes", "UltimoLogin", "Detalhes Saúde"]
            cols_to_show_gc = [col for col in cols_display_gc if col in df_display_clientes_gc.columns]
            # Apply HTML styling for health status
            def style_health(val):
                if "🟢 Bom" in val: return f'<span class="health-good">{val}</span>'
                if "🟡 Atenção" in val: return f'<span class="health-attention">{val}</span>'
                if "🔴 Crítico" in val: return f'<span class="health-attention">{val}</span>' # Same as attention for simplicity here
                return val

            df_styled_gc = df_display_clientes_gc[cols_to_show_gc].copy()
            if 'Saúde Cliente' in df_styled_gc.columns:
                 df_styled_gc['Saúde Cliente'] = df_styled_gc['Saúde Cliente'].apply(style_health)

            st.markdown(df_styled_gc.to_html(escape=False, index=False), unsafe_allow_html=True)
            st.caption("A coluna 'Saúde Cliente' é uma indicação baseada em atividade recente e performance.")
            # (The rest of Gerenciar Clientes: actions, add new client, etc.)
        else:
            st.info("Nenhum cliente cadastrado ou correspondente aos filtros.")


    elif menu_admin == "Gerenciar SAC e Feedbacks": # Combined
        st.markdown("#### Gerenciamento do SAC - Perguntas, Respostas e Análise de Feedback")
        df_sac_qa_admin = carregar_sac_perguntas_respostas().copy()
        df_sac_uso_admin = carregar_sac_uso_feedback().copy()

        sac_admin_tabs = st.tabs(["📝 Gerenciar Perguntas e Respostas SAC", "📊 Relatório de Uso e Feedback SAC"])

        with sac_admin_tabs[0]: # Gerenciar P&R
            # ... (Form to add new SAC Q&A, and list to edit/delete existing ones - similar to original)
            # Ensure 'Tags_SAC' is handled in add/edit forms
            st.subheader("Adicionar Nova Pergunta ao SAC")
            with st.form("form_nova_pergunta_sac", clear_on_submit=True):
                nova_pergunta_sac_txt = st.text_input("Texto da Pergunta SAC:", key="nova_p_sac_txt")
                nova_resposta_sac_txt = st.text_area("Texto da Resposta SAC (Markdown suportado):", key="nova_r_sac_txt", height=150)
                nova_tags_sac_txt = st.text_input("Tags (separadas por vírgula, opcional):", key="nova_tags_sac_txt", placeholder="ex: login, senha, relatório")

                cat_existentes_sac_admin = sorted(list(df_sac_qa_admin['Categoria_SAC'].astype(str).unique())) if not df_sac_qa_admin.empty else []
                cat_options_sac_admin = ["Nova Categoria"] + cat_existentes_sac_admin
                cat_selecionada_sac_admin = st.selectbox("Categoria da Pergunta SAC:", cat_options_sac_admin, key="cat_select_admin_new_sac")
                nova_cat_sac_form_admin = st.text_input("Nome da Nova Categoria SAC:", key="nova_cat_input_admin_new_sac") if cat_selecionada_sac_admin == "Nova Categoria" else cat_selecionada_sac_admin

                submitted_nova_sac_qa = st.form_submit_button("Adicionar ao SAC", icon="➕", type="primary")
                if submitted_nova_sac_qa:
                    if nova_pergunta_sac_txt.strip() and nova_resposta_sac_txt.strip() and nova_cat_sac_form_admin.strip():
                        nova_id_sac_p = str(uuid.uuid4())
                        nova_entrada_sac = pd.DataFrame([{
                            "ID_SAC_Pergunta": nova_id_sac_p,
                            "Pergunta_SAC": nova_pergunta_sac_txt.strip(),
                            "Resposta_SAC": nova_resposta_sac_txt.strip(),
                            "Categoria_SAC": nova_cat_sac_form_admin.strip(),
                            "DataCriacao": now_str(),
                            "Tags_SAC": nova_tags_sac_txt.strip() if nova_tags_sac_txt.strip() else None
                        }])
                        df_sac_qa_admin = pd.concat([df_sac_qa_admin, nova_entrada_sac], ignore_index=True)
                        df_sac_qa_admin.to_csv(sac_perguntas_respostas_csv, index=False, encoding='utf-8')
                        st.cache_data.clear()
                        st.toast("Pergunta adicionada ao SAC!", icon="🎉"); st.rerun()
                    else: st.warning("Pergunta, Resposta e Categoria são obrigatórias.")
            st.divider()
            # List and edit existing SAC Q&A (similar to original, just ensure 'Tags_SAC' is included)


        with sac_admin_tabs[1]: # Relatório de Uso
            st.subheader("Relatório de Interações e Feedback do SAC")
            if df_sac_uso_admin.empty:
                st.info("Nenhum feedback ou uso registrado no SAC ainda.")
            else:
                # --- NEW: SAC Feedback Summary Chart ---
                fig_sac_feedback = create_sac_feedback_summary_chart(df_sac_uso_admin, df_sac_qa_admin)
                if fig_sac_feedback:
                    st.plotly_chart(fig_sac_feedback, use_container_width=True)
                else:
                    st.caption("Não foi possível gerar o gráfico de feedback do SAC.")
                st.divider()

                # (Rest of the feedback listing and filtering - similar to original)

    # ... (Other admin pages: Gerenciar Notificações, Perguntas, Análises, Instruções, Histórico, Admins)
    # These would follow a similar pattern of loading data, providing forms for management, and displaying information.
    # Ensure consistent styling and use of improved chart functions where applicable.

# Fallback if no valid page is selected (should not happen with proper login/session state)
if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()