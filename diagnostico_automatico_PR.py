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
import plotly.graph_objects as go
import uuid # Para IDs de análise e SAC

# !!! st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT !!!
st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", page_icon="📊")

# --- CSS Melhorado (mantido da versão anterior, com possíveis pequenos ajustes) ---
st.markdown("""
<style>
body {
    font-family: 'Segoe UI', sans-serif;
    background-color: #f0f2f5;
}
.login-container {
    max-width: 450px; margin: 40px auto 0 auto; padding: 40px;
    border-radius: 10px; background-color: #ffffff;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1); font-family: 'Segoe UI', sans-serif;
}
.login-container img { display: block; margin-left: auto; margin-right: auto; margin-bottom: 20px; }
.login-container h2 { text-align: center; margin-bottom: 30px; font-weight: 600; font-size: 26px; color: #2563eb; }
.stButton>button {
    border-radius: 6px; background-color: #2563eb; color: white;
    font-weight: 500; padding: 0.6rem 1.3rem; margin-top: 0.5rem;
    border: none; transition: background-color 0.3s ease, transform 0.1s ease;
}
.stButton>button:hover { background-color: #1d4ed8; transform: translateY(-1px); }
.stButton>button:active { transform: translateY(0px); }
.stButton>button.secondary { background-color: #e5e7eb; color: #374151; }
.stButton>button.secondary:hover { background-color: #d1d5db; }
.sac-feedback-button button {
    background-color: #f0f0f0; color: #333; border: 1px solid #ccc;
    margin-right: 5px; padding: 0.3rem 0.8rem; font-size: 0.85em;
}
.sac-feedback-button button:hover { background-color: #e0e0e0; }
.sac-feedback-button button.active-util { background-color: #28a745; color: white; border-color: #28a745; }
.sac-feedback-button button.active-nao-util { background-color: #dc3545; color: white; border-color: #dc3545; }
.stDownloadButton>button {
    background-color: #10b981; color: white; font-weight: 600;
    border-radius: 6px; margin-top: 10px; padding: 0.6rem 1.3rem;
    border: none; transition: background-color 0.3s ease, transform 0.1s ease;
}
.stDownloadButton>button:hover { background-color: #059669; transform: translateY(-1px); }
.stTextInput>div>input, .stTextArea>div>textarea, .stDateInput>div>input, .stSelectbox>div>div {
    border-radius: 6px; padding: 0.6rem; border: 1px solid #d1d5db;
    background-color: #f9fafb; transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.stTextInput>div>input:focus, .stTextArea>div>textarea:focus, .stDateInput>div>input:focus, .stSelectbox>div>div:focus-within {
    border-color: #2563eb; box-shadow: 0 0 0 0.1rem rgba(37, 99, 235, 0.25);
}
.stTabs [data-baseweb="tab"] {
    font-size: 16px; font-weight: 600; padding: 12px 22px;
    border-radius: 6px 6px 0 0; transition: background-color 0.3s ease, color 0.3s ease;
}
.stTabs [data-baseweb="tab"]:hover { background-color: #eef2ff; color: #2563eb; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #2563eb; color: white; }
.custom-card {
    border: 1px solid #e0e0e0; border-left: 5px solid #2563eb;
    padding: 20px; margin-bottom: 15px; border-radius: 8px;
    background-color: #ffffff; box-shadow: 0 2px 5px rgba(0,0,0,0.07);
    transition: box-shadow 0.3s ease;
}
.custom-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.custom-card h4 { margin-top: 0; color: #2563eb; font-size: 1.1em; font-weight: 600; }
.feedback-saved { font-size: 0.85em; color: #10b981; font-style: italic; margin-top: -8px; margin-bottom: 8px; }
.analise-pergunta-cliente {
    font-size: 0.9em; color: #333; background-color: #eef2ff;
    border-left: 3px solid #6366f1; padding: 10px;
    margin-top: 8px; margin-bottom:12px; border-radius: 4px;
}
[data-testid="stMetric"] {
    background-color: #ffffff; border-radius: 8px; padding: 15px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07); border: 1px solid #e0e0e0;
    transition: box-shadow 0.3s ease;
}
[data-testid="stMetric"]:hover { box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
[data-testid="stMetricLabel"] { font-weight: 500; color: #4b5563; font-size: 0.95em; }
[data-testid="stMetricValue"] { font-size: 2em; font-weight: 600; color: #1f2937; }
[data-testid="stMetricDelta"] { font-size: 0.9em; font-weight: 500; }
.metric-delta-positive [data-testid="stMetricDelta"] svg { fill: #10b981 !important; }
.metric-delta-negative [data-testid="stMetricDelta"] svg { fill: #ef4444 !important; }
.metric-delta-neutral [data-testid="stMetricDelta"] { color: #6b7280 !important; }
.stExpander {
    border: 1px solid #e0e0e0 !important; border-radius: 8px !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.07) !important; margin-bottom: 15px !important;
    background-color: #ffffff;
}
.stExpander header {
    font-weight: 600 !important; border-radius: 8px 8px 0 0 !important;
    padding: 10px 15px !important; background-color: #f9fafb;
    border-bottom: 1px solid #e0e0e0;
}
.dashboard-item {
    background-color: #ffffff; padding: 20px; border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07); margin-bottom: 20px;
    border: 1px solid #e0e0e0; height: 100%; display: flex; flex-direction: column;
}
.dashboard-item h5 {
    margin-top: 0; margin-bottom: 15px; color: #2563eb;
    font-size: 1.1em; border-bottom: 1px solid #eee; padding-bottom: 8px;
}
.kanban-board { display: flex; gap: 20px; overflow-x: auto; padding-bottom: 10px; }
.kanban-column {
    background-color: #f8f9fa; border-radius: 8px; padding: 15px;
    min-width: 280px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #e9ecef;
}
.kanban-column h4 {
    margin-top: 0; margin-bottom: 15px; font-size: 1.2em;
    color: #343a40; border-bottom: 2px solid #dee2e6; padding-bottom: 8px;
}
.kanban-card {
    background-color: #ffffff; border: 1px solid #dee2e6;
    padding: 12px 15px; margin-bottom: 10px; border-radius: 6px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.06); transition: box-shadow 0.2s ease-in-out;
}
.kanban-card:hover { box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
.kanban-card-title { font-weight: 600; font-size: 0.95em; color: #2563eb; margin-bottom: 5px; }
.kanban-card-score { font-size: 0.85em; color: #6c757d; margin-bottom: 3px; }
.kanban-card-responsavel { font-size: 0.8em; font-style: italic; color: #868e96; }
.kanban-card-prazo-15 { border-left: 5px solid #dc3545; }
.kanban-card-prazo-30 { border-left: 5px solid #fd7e14; }
.kanban-card-prazo-45 { border-left: 5px solid #ffc107; }
.kanban-card-prazo-60 { border-left: 5px solid #28a745; }
</style>
""", unsafe_allow_html=True)

# --- Funções de Gráficos (mantidas e novas adicionadas abaixo) ---
# ... (funções create_radar_chart, create_gut_barchart, etc. mantidas como na versão anterior) ...
def create_radar_chart(data_dict, title="Radar Chart", color='#2563eb'):
    if not data_dict: return None
    categories = list(data_dict.keys())
    values = list(data_dict.values())
    if not categories or not values or len(categories) < 3 : return None
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]
    df_radar = pd.DataFrame(dict(r=values_closed, theta=categories_closed))
    fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True, template="seaborn")
    fig.update_traces(fill='toself', line=dict(color=color), hovertemplate = '<b>%{theta}</b><br>Score: %{r:.2f}<extra></extra>')
    fig.update_layout(title={'text': title, 'x':0.5, 'xanchor': 'center', 'font': {'size': 18, 'family': "Segoe UI, sans-serif"}},
                      polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                      font=dict(family="Segoe UI, sans-serif"), margin=dict(l=50, r=50, t=70, b=50))
    return fig

def create_gut_barchart(gut_data_list, title="Top Prioridades (GUT)"):
    if not gut_data_list: return None
    df_gut = pd.DataFrame(gut_data_list).sort_values(by="Score", ascending=False).head(10)
    if df_gut.empty: return None
    fig = px.bar(df_gut, x="Score", y="Tarefa", title=title, orientation='h', color="Score",
                 color_continuous_scale=px.colors.sequential.Blues_r, labels={'Tarefa':'Tarefa/Pergunta', 'Score':'Score GUT'},
                 height=min(600, 200 + len(df_gut)*35))
    fig.update_traces(hovertemplate='<b>%{y}</b><br>Score GUT: %{x}<extra></extra>')
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Score GUT", yaxis_title="",
                      font=dict(family="Segoe UI, sans-serif"),
                      margin=dict(l=max(100, df_gut['Tarefa'].str.len().max()*5 if not df_gut.empty else 100), r=20, t=70, b=50))
    return fig

def create_diagnostics_timeline_chart(df_diagnostics, title="Diagnósticos Realizados ao Longo do Tempo"):
    if df_diagnostics.empty: return None
    df_diag_copy = df_diagnostics.copy()
    key_data_col = 'Data_dt' if 'Data_dt' in df_diag_copy.columns else 'Data'
    df_diag_copy[key_data_col] = pd.to_datetime(df_diag_copy[key_data_col], errors='coerce')
    if df_diag_copy[key_data_col].isnull().all(): return None # No valid dates

    diag_counts_monthly = df_diag_copy.groupby(pd.Grouper(key=key_data_col, freq='M')).size().reset_index(name='Contagem')
    diag_counts_monthly['Mês'] = diag_counts_monthly[key_data_col].dt.strftime('%Y-%m')
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
            avg_scores_data.append({'Categoria': col.replace("Media_Cat_", "").replace("_", " "), 'Média_Score': numeric_scores.mean()})
    if not avg_scores_data: return None
    avg_scores = pd.DataFrame(avg_scores_data).sort_values(by="Média_Score", ascending=True)
    fig = px.bar(avg_scores, y='Categoria', x='Média_Score', title=title, orientation='h', color='Média_Score',
                 color_continuous_scale=px.colors.sequential.Blues, labels={'Categoria':'Categoria', 'Média_Score':'Média do Score'})
    fig.update_traces(hovertemplate='<b>%{y}</b><br>Média: %{x:.2f}<extra></extra>')
    fig.update_layout(xaxis_title="Média do Score", yaxis_title="", font=dict(family="Segoe UI, sans-serif"),
                      xaxis=dict(range=[0,5.5]), height=min(700, 200 + len(avg_scores)*30))
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
    fig.update_traces(textposition='outside', textinfo='percent+label', hovertemplate='<b>%{label}</b><br>Clientes: %{value}<extra></extra>')
    fig.update_layout(font=dict(family="Segoe UI, sans-serif"), legend_title_text='Nível de Engajamento')
    return fig

def create_sac_feedback_chart(df_sac_feedback, title="Feedback de Utilidade das Respostas do SAC"):
    if df_sac_feedback.empty or 'Feedback_Util' not in df_sac_feedback.columns: return None
    df_sac_feedback_copy = df_sac_feedback.copy()
    df_sac_feedback_copy['Feedback_Display'] = df_sac_feedback_copy['Feedback_Util'].map({True: '👍 Útil', False: '👎 Não Útil', pd.NA: '➖ Sem Feedback'}).fillna('➖ Sem Feedback')
    feedback_counts = df_sac_feedback_copy['Feedback_Display'].value_counts().reset_index()
    feedback_counts.columns = ['Feedback', 'Contagem']
    if feedback_counts.empty: return None
    fig = px.bar(feedback_counts, x='Feedback', y='Contagem', title=title, color='Feedback',
                 color_discrete_map={'👍 Útil': '#28a745', '👎 Não Útil': '#dc3545', '➖ Sem Feedback': '#6c757d'},
                 labels={'Feedback':'Tipo de Feedback', 'Contagem':'Número de Avaliações'})
    fig.update_traces(hovertemplate='<b>%{x}</b><br>Avaliações: %{y}<extra></extra>')
    fig.update_layout(font=dict(family="Segoe UI, sans-serif"), showlegend=False)
    return fig

# --- NOVAS FUNÇÕES DE GRÁFICO PARA PESQUISA DE SATISFAÇÃO ---
def create_satisfaction_distribution_chart(df_respostas, pergunta_texto, tipo_pergunta):
    """Cria um gráfico de distribuição para respostas de pesquisa de satisfação."""
    if df_respostas.empty or 'Resposta_Pesquisa' not in df_respostas.columns:
        return None
    
    respostas_da_pergunta = df_respostas[df_respostas['Texto_Pergunta_Pesquisa'] == pergunta_texto]['Resposta_Pesquisa']
    if respostas_da_pergunta.empty:
        return None

    if tipo_pergunta == "Escala_1_5" or tipo_pergunta == "Escala_NPS_0_10":
        respostas_da_pergunta = pd.to_numeric(respostas_da_pergunta, errors='coerce').dropna()
        if respostas_da_pergunta.empty: return None
        
        # Contar a frequência de cada score
        counts = respostas_da_pergunta.value_counts().sort_index().reset_index()
        counts.columns = ['Score', 'Contagem']
        
        title_chart = f"Distribuição de Respostas: {pergunta_texto}"
        if tipo_pergunta == "Escala_NPS_0_10":
             # Definir categorias NPS
            def nps_category(score):
                if score <= 6: return "Detrator"
                elif score <= 8: return "Neutro"
                else: return "Promotor"
            counts['Categoria_NPS'] = counts['Score'].apply(nps_category)
            color_map = {"Detrator": "#dc3545", "Neutro": "#ffc107", "Promotor": "#28a745"}
            fig = px.bar(counts, x='Score', y='Contagem', title=title_chart, text='Contagem', color='Categoria_NPS', color_discrete_map=color_map)
            fig.update_traces(texttemplate='%{text}', textposition='outside')
        else: # Escala 1-5
            fig = px.bar(counts, x='Score', y='Contagem', title=title_chart, text='Contagem')
            fig.update_traces(marker_color='#2563eb', texttemplate='%{text}', textposition='outside')
        
        fig.update_layout(xaxis_title="Score", yaxis_title="Número de Respostas", font=dict(family="Segoe UI, sans-serif"))
        return fig
        
    elif tipo_pergunta == "Sim_Nao":
        counts = respostas_da_pergunta.value_counts().reset_index()
        counts.columns = ['Resposta', 'Contagem']
        fig = px.pie(counts, values='Contagem', names='Resposta', title=f"Distribuição: {pergunta_texto}",
                     color_discrete_map={"Sim": "#28a745", "Não": "#dc3545"})
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(font=dict(family="Segoe UI, sans-serif"))
        return fig
    return None


# --- Configuração de Arquivos e Variáveis Globais ---
# ... (arquivos CSV existentes mantidos) ...
pesquisa_satisfacao_perguntas_csv = "pesquisa_satisfacao_perguntas.csv"
pesquisa_satisfacao_respostas_csv = "pesquisa_satisfacao_respostas.csv"
# ... (LOGOS_DIR mantido)

# --- Inicialização do Session State (sem alterações diretas aqui) ---
# ... (default_session_state mantido)

# --- Funções Utilitárias (mantidas) ---
# ... (sanitize_column_name, pdf_safe_text_output, find_client_logo_path, etc.)

# --- Definição das Colunas Base ---
# ... (colunas base existentes mantidas) ...
colunas_base_pesquisa_perguntas = ["ID_Pesquisa_Pergunta", "Texto_Pergunta_Pesquisa", "Tipo_Pergunta_Pesquisa",
                                  "Categoria_Pesquisa", "Ordem_Exibicao", "Ativa", "DataCriacao"]
colunas_base_pesquisa_respostas = ["ID_Resposta_Pesquisa", "ID_Pesquisa_Pergunta", "CNPJ_Cliente",
                                   "ID_Diagnostico_Relacionado", "Resposta_Pesquisa", "Timestamp_Resposta",
                                   "Comentario_Adicional_Pesquisa"]

# --- Inicializar CSVs (adicionar novos arquivos) ---
try:
    # ... (inicialização de CSVs existentes mantida) ...
    inicializar_csv(pesquisa_satisfacao_perguntas_csv, colunas_base_pesquisa_perguntas,
                    defaults={"Ativa": True, "Categoria_Pesquisa": "Geral", "Ordem_Exibicao": 0, "DataCriacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    inicializar_csv(pesquisa_satisfacao_respostas_csv, colunas_base_pesquisa_respostas,
                    defaults={"ID_Diagnostico_Relacionado": None, "Comentario_Adicional_Pesquisa": ""})
except Exception as e_init:
    st.error(f"Falha na inicialização de arquivos CSV: {e_init}")
    st.stop()

# ... (registrar_acao, update_user_data, carregar_analises_perguntas, etc., mantidas) ...

# --- NOVAS FUNÇÕES DE CACHE PARA PESQUISA ---
@st.cache_data
def carregar_perguntas_pesquisa():
    try:
        df = pd.read_csv(pesquisa_satisfacao_perguntas_csv, encoding='utf-8')
        if 'Ativa' not in df.columns: df['Ativa'] = True # Default para True se coluna ausente
        else: df['Ativa'] = df['Ativa'].astype(str).str.lower().map({'true': True, 'false': False}).fillna(True)
        if 'Ordem_Exibicao' not in df.columns: df['Ordem_Exibicao'] = 0
        df['Ordem_Exibicao'] = pd.to_numeric(df['Ordem_Exibicao'], errors='coerce').fillna(0)
        return df.sort_values(by=['Ordem_Exibicao', 'DataCriacao'], ascending=[True, True])
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_pesquisa_perguntas)

@st.cache_data
def carregar_respostas_pesquisa():
    try:
        df = pd.read_csv(pesquisa_satisfacao_respostas_csv, encoding='utf-8', dtype={'CNPJ_Cliente': str})
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_pesquisa_respostas)

# ... (gerar_pdf_diagnostico_completo mantido) ...

# --- Lógica de Login e Navegação Principal (sem alterações diretas aqui) ---
# ... (lógica de login mantida) ...

# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    # ... (lógica do menu lateral do cliente como antes, mas com nova opção) ...
    menu_options_cli_map_full = {
        "Instruções": "📖 Instruções",
        "Novo Diagnóstico": "📋 Novo Diagnóstico",
        "Painel Principal": "🏠 Painel Principal",
        "Pesquisa de Satisfação": "🌟 Pesquisa de Satisfação", # NOVA OPÇÃO
        "Notificações": notificacoes_label,
        "SAC": "❓ SAC - Perguntas Frequentes"
    }
    # ... (restante da lógica de navegação do cliente ajustada para incluir a nova opção) ...

    if st.session_state.cliente_page == "Pesquisa de Satisfação":
        st.subheader("🌟 Pesquisa de Satisfação")
        st.markdown("Sua opinião é muito importante para nós! Por favor, reserve um momento para responder.")

        df_perguntas_pesquisa = carregar_perguntas_pesquisa()
        perguntas_ativas_pesquisa = df_perguntas_pesquisa[df_perguntas_pesquisa['Ativa'] == True