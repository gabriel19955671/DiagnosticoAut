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
import uuid
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# Configuração da página - DEVE SER O PRIMEIRO COMANDO
st.set_page_config(
    page_title="Portal de Diagnóstico Empresarial",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# --- CSS Modernizado ---
st.markdown("""
<style>
:root {
    --primary: #2563eb;
    --primary-hover: #1d4ed8;
    --secondary: #f0f0f0;
    --secondary-hover: #e0e0e0;
    --success: #10b981;
    --success-hover: #059669;
    --danger: #ef4444;
    --danger-hover: #dc2626;
    --warning: #f59e0b;
    --warning-hover: #d97706;
    --info: #3b82f6;
    --info-hover: #2563eb;
    --dark: #1f2937;
    --light: #f9fafb;
    --text: #374151;
    --text-light: #6b7280;
    --border: #e5e7eb;
    --border-dark: #d1d5db;
    --bg: #ffffff;
    --bg-secondary: #f3f4f6;
    --radius: 0.5rem;
}

/* Base Styles */
body {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    background-color: var(--bg-secondary);
    color: var(--text);
    line-height: 1.5;
}

/* Login Container */
.login-container {
    max-width: 480px;
    margin: 2rem auto 0 auto;
    padding: 2.5rem;
    border-radius: var(--radius);
    background-color: var(--bg);
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border: 1px solid var(--border);
}

.login-container img {
    display: block;
    margin: 0 auto 1.5rem auto;
    max-width: 180px;
}

.login-container h2 {
    text-align: center;
    margin-bottom: 1.5rem;
    font-weight: 600;
    font-size: 1.625rem;
    color: var(--primary);
}

/* Buttons */
.stButton>button {
    border-radius: var(--radius);
    padding: 0.65rem 1.25rem;
    font-weight: 500;
    transition: all 0.2s ease;
    border: none;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.stButton>button.primary {
    background-color: var(--primary);
    color: white;
}

.stButton>button.primary:hover {
    background-color: var(--primary-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.stButton>button.secondary {
    background-color: var(--secondary);
    color: var(--text);
}

.stButton>button.secondary:hover {
    background-color: var(--secondary-hover);
}

.stButton>button.success {
    background-color: var(--success);
    color: white;
}

.stButton>button.success:hover {
    background-color: var(--success-hover);
}

.stButton>button.danger {
    background-color: var(--danger);
    color: white;
}

.stButton>button.danger:hover {
    background-color: var(--danger-hover);
}

.stButton>button.warning {
    background-color: var(--warning);
    color: white;
}

.stButton>button.warning:hover {
    background-color: var(--warning-hover);
}

/* Inputs */
.stTextInput>div>input, 
.stTextArea>div>textarea, 
.stDateInput>div>input, 
.stSelectbox>div>div {
    border-radius: var(--radius);
    padding: 0.65rem;
    border: 1px solid var(--border);
    background-color: var(--bg);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.stTextInput>div>input:focus, 
.stTextArea>div>textarea:focus, 
.stDateInput>div>input:focus, 
.stSelectbox>div>div:focus-within {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
    outline: none;
}

/* Cards */
.custom-card {
    border: 1px solid var(--border);
    border-left: 4px solid var(--primary);
    padding: 1.25rem;
    margin-bottom: 1rem;
    border-radius: var(--radius);
    background-color: var(--bg);
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.custom-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.custom-card h4 {
    margin-top: 0;
    color: var(--primary);
    font-size: 1.1rem;
    font-weight: 600;
}

/* Feedback */
.feedback-saved {
    font-size: 0.85rem;
    color: var(--success);
    font-style: italic;
    margin-top: -0.5rem;
    margin-bottom: 0.5rem;
}

.analise-pergunta-cliente {
    font-size: 0.9rem;
    color: var(--text);
    background-color: #f0f9ff;
    border-left: 3px solid #93c5fd;
    padding: 0.75rem;
    margin: 0.5rem 0 0.75rem 0;
    border-radius: 0.25rem;
}

/* Metrics */
[data-testid="stMetric"] {
    background-color: var(--bg);
    border-radius: var(--radius);
    padding: 1rem 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    border: 1px solid var(--border);
}

[data-testid="stMetricLabel"] {
    font-weight: 500;
    color: var(--text-light);
    font-size: 0.9rem;
}

[data-testid="stMetricValue"] {
    font-size: 1.75rem;
    font-weight: 700;
}

[data-testid="stMetricDelta"] {
    font-size: 0.9rem;
    font-weight: 500;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    font-size: 0.95rem;
    font-weight: 500;
    padding: 0.75rem 1.25rem;
    border-radius: var(--radius) var(--radius) 0 0;
    margin-right: 0.5rem;
    transition: all 0.2s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: var(--bg-secondary);
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: var(--primary);
    color: white;
}

/* Dashboard Items */
.dashboard-item {
    background-color: var(--bg);
    padding: 1.25rem;
    border-radius: var(--radius);
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    margin-bottom: 1.25rem;
    border: 1px solid var(--border);
    height: 100%;
}

.dashboard-item h5 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: var(--primary);
    font-size: 1.1rem;
    font-weight: 600;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
}

/* Satisfaction Survey */
.satisfaction-emoji {
    font-size: 2rem;
    cursor: pointer;
    transition: transform 0.2s ease;
}

.satisfaction-emoji:hover {
    transform: scale(1.2);
}

.satisfaction-emoji.selected {
    transform: scale(1.3);
    filter: drop-shadow(0 0 4px rgba(37, 99, 235, 0.3));
}

/* NPS Dashboard */
.nps-detractors {
    background-color: #fee2e2;
    color: #b91c1c;
}

.nps-passives {
    background-color: #fef3c7;
    color: #92400e;
}

.nps-promoters {
    background-color: #dcfce7;
    color: #166534;
}

/* Tooltips */
.tooltip-icon {
    display: inline-block;
    width: 16px;
    height: 16px;
    background-color: var(--text-light);
    color: white;
    border-radius: 50%;
    text-align: center;
    line-height: 16px;
    font-size: 12px;
    margin-left: 5px;
    cursor: help;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
    .login-container {
        padding: 1.5rem;
        margin: 1rem auto;
    }
    
    .dashboard-item {
        padding: 1rem;
    }
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.animate-fade {
    animation: fadeIn 0.3s ease-out forwards;
}

/* Progress Bar */
.stProgress > div > div > div {
    background-color: var(--primary) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: var(--bg) !important;
    border-right: 1px solid var(--border) !important;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--border-dark);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--text-light);
}
</style>
""", unsafe_allow_html=True)

# --- Funções de Gráficos Aprimoradas ---
def create_radar_chart(data_dict, title="Radar Chart"):
    if not data_dict: return None
    categories = list(data_dict.keys())
    values = list(data_dict.values())
    if not categories or not values or len(categories) < 3: return None

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Score',
        line=dict(color='#2563eb'),
        fillcolor='rgba(37, 99, 235, 0.2)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickfont=dict(size=10),
                gridcolor='rgba(0,0,0,0.1)'
            ),
            angularaxis=dict(
                gridcolor='rgba(0,0,0,0.1)',
                linecolor='rgba(0,0,0,0.1)'
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=14)
        ),
        margin=dict(l=50, r=50, t=50, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=350,
        showlegend=False
    )

    return fig

def create_gut_barchart(gut_data_list, title="Top Prioridades (GUT)"):
    if not gut_data_list: return None
    df_gut = pd.DataFrame(gut_data_list)
    df_gut = df_gut.sort_values(by="Score", ascending=False).head(10)
    if df_gut.empty: return None
    
    # Color mapping based on score
    colors = []
    for score in df_gut['Score']:
        if score >= 75:
            colors.append('#ef4444')  # Red for high priority
        elif score >= 40:
            colors.append('#f59e0b')  # Yellow for medium priority
        else:
            colors.append('#10b981')  # Green for lower priority

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_gut['Score'],
        y=df_gut['Tarefa'],
        orientation='h',
        marker_color=colors,
        hovertemplate='<b>%{y}</b><br>Score: %{x}<extra></extra>',
        text=df_gut['Score'],
        textposition='auto',
        texttemplate='%{text:.0f}'
    ))

    fig.update_layout(
        title=dict(text=title, x=0.5),
        yaxis=dict(
            categoryorder='total ascending',
            tickfont=dict(size=10)
        ),
        xaxis_title="Score GUT",
        yaxis_title="",
        margin=dict(l=150, r=20, t=60, b=20),
        height=400 + len(df_gut)*15,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return fig

def create_diagnostics_timeline_chart(df_diagnostics, title="Diagnósticos Realizados"):
    if df_diagnostics.empty or 'Data' not in df_diagnostics.columns: return None
    
    df_diag_copy = df_diagnostics.copy()
    df_diag_copy['Data'] = pd.to_datetime(df_diag_copy['Data'])
    diag_counts_monthly = df_diag_copy.groupby(pd.Grouper(key='Data', freq='M')).size().reset_index(name='Contagem')
    diag_counts_monthly['Mês'] = diag_counts_monthly['Data'].dt.strftime('%Y-%m')
    
    if diag_counts_monthly.empty: return None

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=diag_counts_monthly['Mês'],
        y=diag_counts_monthly['Contagem'],
        mode='lines+markers',
        line=dict(color='#2563eb', width=2.5),
        marker=dict(size=8, color='#2563eb', line=dict(width=1, color='white')),
        hovertemplate='<b>%{x}</b><br>Diagnósticos: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title=dict(text=title, x=0.5),
        xaxis_title="Mês",
        yaxis_title="Nº de Diagnósticos",
        margin=dict(l=50, r=30, t=60, b=50),
        height=350,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return fig

def create_avg_category_scores_chart(df_diagnostics, title="Média por Categoria"):
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

    # Create color scale based on score
    colors = []
    for score in avg_scores['Média_Score']:
        if score >= 4:
            colors.append('#10b981')  # Green for good scores
        elif score >= 2.5:
            colors.append('#f59e0b')  # Yellow for average scores
        else:
            colors.append('#ef4444')  # Red for low scores

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=avg_scores['Categoria'],
        y=avg_scores['Média_Score'],
        marker_color=colors,
        text=avg_scores['Média_Score'].round(2),
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Média: %{y:.2f}<extra></extra>'
    ))

    fig.update_layout(
        title=dict(text=title, x=0.5),
        xaxis=dict(tickangle=-45),
        yaxis=dict(range=[0,5.5]),
        margin=dict(l=50, r=30, t=60, b=100),
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return fig

def create_client_engagement_pie(df_usuarios, title="Engajamento de Clientes"):
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

    # Custom colors for each category
    color_map = {
        "0 Diagnósticos": '#ef4444',
        "1 Diagnóstico": '#f59e0b',
        "2 Diagnósticos": '#93c5fd',
        "3+ Diagnósticos": '#10b981'
    }
    colors = [color_map.get(cat, '#6b7280') for cat in engagement_counts['Categoria_Engajamento']]

    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=engagement_counts['Categoria_Engajamento'],
        values=engagement_counts['Numero_Clientes'],
        marker=dict(colors=colors),
        textinfo='percent+label',
        insidetextorientation='radial',
        hovertemplate='<b>%{label}</b><br>Clientes: %{value}<br>%{percent}<extra></extra>',
        hole=0.4
    ))

    fig.update_layout(
        title=dict(text=title, x=0.5),
        showlegend=False,
        margin=dict(l=30, r=30, t=60, b=30),
        height=350,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return fig

def create_nps_chart(nps_score, detractors, passives, promoters):
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode = "number+gauge",
        value = nps_score,
        number = dict(suffix=" NPS", font=dict(size=24)),
        domain = {'x': [0.25, 1], 'y': [0.7, 0.9]},
        gauge = {
            'shape': "bullet",
            'axis': {'range': [-100, 100]},
            'threshold': {
                'line': {'color': "black", 'width': 2},
                'thickness': 0.75,
                'value': nps_score},
            'steps': [
                {'range': [-100, 0], 'color': "#fee2e2"},
                {'range': [0, 100], 'color': "#dcfce7"}],
            'bar': {'color': "#3b82f6"}}
    ))

    fig.add_trace(go.Indicator(
        mode = "number",
        value = detractors,
        number = dict(font=dict(color="#b91c1c")),
        title = dict(text="Detratores", font=dict(size=14)),
        domain = {'x': [0, 0.25], 'y': [0.5, 0.6]}
    ))

    fig.add_trace(go.Indicator(
        mode = "number",
        value = passives,
        number = dict(font=dict(color="#92400e")),
        title = dict(text="Passivos", font=dict(size=14)),
        domain = {'x': [0.35, 0.65], 'y': [0.5, 0.6]}
    ))

    fig.add_trace(go.Indicator(
        mode = "number",
        value = promoters,
        number = dict(font=dict(color="#166534")),
        title = dict(text="Promotores", font=dict(size=14)),
        domain = {'x': [0.75, 1], 'y': [0.5, 0.6]}
    ))

    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=30, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
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
instrucoes_default_path = "instrucoes_portal_default.md"
sac_perguntas_respostas_csv = "sac_perguntas_respostas.csv"
sac_uso_feedback_csv = "sac_uso_feedback.csv"
pesquisa_satisfacao_csv = "pesquisa_satisfacao.csv"
LOGOS_DIR = "client_logos"

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, 
    "cliente_logado": False, 
    "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, 
    "cliente_page": "Instruções", 
    "cnpj": None, 
    "user": None,
    "progresso_diagnostico_percentual": 0, 
    "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, 
    "id_formulario_atual": None,
    "pdf_gerado_path": None, 
    "pdf_gerado_filename": None,
    "feedbacks_respostas": {}, 
    "sac_feedback_registrado": {},
    "force_sidebar_rerun_after_notif_read_v19": False,
    "target_diag_data_for_expansion": None,
    "satisfaction_survey_submitted": False,
    "satisfaction_rating": None,
    "satisfaction_comments": ""
}

for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias ---
def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s)
    return s

def pdf_safe_text_output(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

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
colunas_base_pesquisa_satisfacao = ["ID_Pesquisa", "CNPJ_Cliente", "Data", "Rating", "Comentarios", "Recomendaria"]

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
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype={'CNPJ': str, 'CNPJ_Cliente': str} if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, sac_uso_feedback_csv, pesquisa_satisfacao_csv] else None)
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
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype={'CNPJ': str, 'CNPJ_Cliente': str} if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, sac_uso_feedback_csv, pesquisa_satisfacao_csv] else None)

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
    inicializar_csv(pesquisa_satisfacao_csv, colunas_base_pesquisa_satisfacao, defaults={"Recomendaria": None})
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

@