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

# --- CSS Melhorado ---
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

# --- Funções de Gráficos ---
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
    if df_diag_copy[key_data_col].isnull().all(): return None

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

def create_satisfaction_distribution_chart(df_respostas, pergunta_texto, tipo_pergunta):
    if df_respostas.empty or 'Resposta_Pesquisa' not in df_respostas.columns:
        return None
    
    respostas_da_pergunta_raw = df_respostas[df_respostas['Texto_Pergunta_Pesquisa'] == pergunta_texto]['Resposta_Pesquisa']
    if respostas_da_pergunta_raw.empty:
        return None

    if tipo_pergunta == "Escala_1_5" or tipo_pergunta == "Escala_NPS_0_10":
        respostas_da_pergunta = pd.to_numeric(respostas_da_pergunta_raw, errors='coerce').dropna()
        if respostas_da_pergunta.empty: return None
        
        counts = respostas_da_pergunta.value_counts().sort_index().reset_index()
        counts.columns = ['Score', 'Contagem']
        
        title_chart = f"Distribuição: {pergunta_texto}"
        if tipo_pergunta == "Escala_NPS_0_10":
            def nps_category(score):
                if score <= 6: return "Detrator"
                elif score <= 8: return "Neutro"
                else: return "Promotor"
            counts['Categoria_NPS'] = counts['Score'].apply(nps_category)
            color_map = {"Detrator": "#dc3545", "Neutro": "#ffc107", "Promotor": "#28a745"}
            fig = px.bar(counts, x='Score', y='Contagem', title=title_chart, text='Contagem', color='Categoria_NPS', color_discrete_map=color_map,
                         labels={'Score': 'Nota (0-10)', 'Contagem': 'Nº de Respostas'})
            fig.update_traces(texttemplate='%{text}', textposition='outside')
        else: # Escala 1-5
            fig = px.bar(counts, x='Score', y='Contagem', title=title_chart, text='Contagem',
                         labels={'Score': 'Nota (1-5)', 'Contagem': 'Nº de Respostas'})
            fig.update_traces(marker_color='#2563eb', texttemplate='%{text}', textposition='outside')
        
        fig.update_layout(xaxis_title="Score", yaxis_title="Número de Respostas", font=dict(family="Segoe UI, sans-serif"))
        return fig
        
    elif tipo_pergunta == "Sim_Nao":
        counts = respostas_da_pergunta_raw.value_counts().reset_index()
        counts.columns = ['Resposta', 'Contagem']
        fig = px.pie(counts, values='Contagem', names='Resposta', title=f"Distribuição: {pergunta_texto}",
                     color_discrete_map={"Sim": "#28a745", "Não": "#dc3545"})
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(font=dict(family="Segoe UI, sans-serif"))
        return fig
    return None

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

# --- Definição das Colunas Base ---
colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone",
                         "JaVisualizouInstrucoes", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]
colunas_base_perguntas = ["Pergunta", "Categoria"]
colunas_base_analises = ["ID_Analise", "TextoPerguntaOriginal", "TipoCondicao", "CondicaoValorMin", "CondicaoValorMax", "CondicaoValorExato", "TextoAnalise"]
colunas_base_notificacoes = ["ID_Notificacao", "CNPJ_Cliente", "Timestamp", "Mensagem", "Lida", "ID_Diagnostico_Relacionado"]
colunas_base_sac_perguntas = ["ID_SAC_Pergunta", "Pergunta_SAC", "Resposta_SAC", "Categoria_SAC", "DataCriacao"]
colunas_base_sac_uso_feedback = ["ID_Uso_SAC", "Timestamp", "CNPJ_Cliente", "ID_SAC_Pergunta", "Feedback_Util"]
colunas_base_pesquisa_perguntas = ["ID_Pesquisa_Pergunta", "Texto_Pergunta_Pesquisa", "Tipo_Pergunta_Pesquisa",
                                  "Categoria_Pesquisa", "Ordem_Exibicao", "Ativa", "DataCriacao"]
colunas_base_pesquisa_respostas = ["ID_Resposta_Pesquisa", "ID_Pesquisa_Pergunta", "CNPJ_Cliente",
                                   "ID_Diagnostico_Relacionado", "Resposta_Pesquisa", "Timestamp_Resposta",
                                   "Comentario_Adicional_Pesquisa"]

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
                df_init = pd.read_csv(filepath, encoding='utf-8',
                                      dtype={'CNPJ': str, 'CNPJ_Cliente': str} if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, sac_uso_feedback_csv, pesquisa_satisfacao_respostas_csv] else None)
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
                df_init = pd.read_csv(filepath, encoding='utf-8',
                                      dtype={'CNPJ': str, 'CNPJ_Cliente': str} if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, sac_uso_feedback_csv, pesquisa_satisfacao_respostas_csv] else None)

            made_changes = False
            current_cols = df_init.columns.tolist()
            for col_idx, col_name in enumerate(columns):
                if col_name not in current_cols:
                    default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                    insert_loc = min(col_idx, len(df_init.columns))
                    df_init.insert(loc=insert_loc, column=col_name, value=default_val)
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

# --- Funções de Cache ---
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
             df['Feedback_Util'] = df['Feedback_Util'].astype(str).str.lower().map({'true': True, 'false': False, 'nan': pd.NA, '': pd.NA, 'none':pd.NA}).astype('boolean')
        else: df['Feedback_Util'] = pd.NA
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_sac_uso_feedback)

@st.cache_data
def carregar_perguntas_pesquisa():
    try:
        df = pd.read_csv(pesquisa_satisfacao_perguntas_csv, encoding='utf-8')
        if 'Ativa' not in df.columns: df['Ativa'] = True
        else: df['Ativa'] = df['Ativa'].astype(str).str.lower().map({'true': True, 'false': False, 'nan': True, '': True}).fillna(True).astype(bool)
        if 'Ordem_Exibicao' not in df.columns: df['Ordem_Exibicao'] = 0
        else: df['Ordem_Exibicao'] = pd.to_numeric(df['Ordem_Exibicao'], errors='coerce').fillna(0).astype(int)
        if 'Categoria_Pesquisa' not in df.columns: df['Categoria_Pesquisa'] = "Geral"
        else: df['Categoria_Pesquisa'] = df['Categoria_Pesquisa'].fillna("Geral")
        if 'DataCriacao' not in df.columns: df['DataCriacao'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return df.sort_values(by=['Ordem_Exibicao', 'DataCriacao'], ascending=[True, True])
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_pesquisa_perguntas)

@st.cache_data
def carregar_respostas_pesquisa():
    try:
        df = pd.read_csv(pesquisa_satisfacao_respostas_csv, encoding='utf-8', dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Relacionado': str})
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_pesquisa_respostas)

# --- obter_analise_para_resposta ---
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

# --- gerar_pdf_diagnostico_completo ---
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
    "respostas_pesquisa_satisfacao_atual": {}
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Inicializar CSVs ---
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
    inicializar_csv(pesquisa_satisfacao_perguntas_csv, colunas_base_pesquisa_perguntas,
                    defaults={"Ativa": True, "Categoria_Pesquisa": "Geral", "Ordem_Exibicao": 0, "DataCriacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    inicializar_csv(pesquisa_satisfacao_respostas_csv, colunas_base_pesquisa_respostas,
                    defaults={"ID_Diagnostico_Relacionado": None, "Comentario_Adicional_Pesquisa": ""})
except Exception as e_init:
    st.error(f"Falha na inicialização de arquivos CSV: {e_init}")
    st.exception(e_init)
    st.stop()


# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"):
    st.session_state.trigger_rerun_global = False
    st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v22") # Key atualizada
elif st.session_state.admin_logado:
    aba = "Administrador"
else:
    aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v22"): # Key atualizada
        u = st.text_input("Usuário", key="admin_u_v22")
        p = st.text_input("Senha", type="password", key="admin_p_v22")
        if st.form_submit_button("Entrar", use_container_width=True, icon="🔑"):
            try:
                df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                if not df_creds[(df_creds["Usuario"] == u) & (df_creds["Senha"] == p)].empty:
                    st.session_state.admin_logado = True
                    st.toast("Login de admin bem-sucedido!", icon="🎉")
                    st.rerun()
                else:
                    st.error("Usuário/senha admin inválidos.")
            except Exception as e:
                st.error(f"Erro login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_v22"): # Key atualizada
        c = st.text_input("CNPJ", key="cli_c_v22", value=st.session_state.get("last_cnpj_input",""))
        s = st.text_input("Senha", type="password", key="cli_s_v22")
        if st.form_submit_button("Entrar", use_container_width=True, icon="👤"):
            st.session_state.last_cnpj_input = c
            try:
                users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                # Garantir colunas default no users_df
                if "JaVisualizouInstrucoes" not in users_df.columns: users_df["JaVisualizouInstrucoes"] = "False"
                users_df["JaVisualizouInstrucoes"] = users_df["JaVisualizouInstrucoes"].astype(str).str.lower().map({'true': True, 'false': False, 'nan': False, '':False}).fillna(False)
                if "DiagnosticosDisponiveis" not in users_df.columns: users_df["DiagnosticosDisponiveis"] = 1
                users_df["DiagnosticosDisponiveis"] = pd.to_numeric(users_df["DiagnosticosDisponiveis"], errors='coerce').fillna(1).astype(int)
                if "TotalDiagnosticosRealizados" not in users_df.columns: users_df["TotalDiagnosticosRealizados"] = 0
                users_df["TotalDiagnosticosRealizados"] = pd.to_numeric(users_df["TotalDiagnosticosRealizados"], errors='coerce').fillna(0).astype(int)

                blocked_df = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                if c in blocked_df["CNPJ"].values:
                    st.error("CNPJ bloqueado.")
                    st.stop()
                match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == s)]
                if match.empty:
                    st.error("CNPJ/senha inválidos.")
                    st.stop()

                st.session_state.cliente_logado = True
                st.session_state.cnpj = c
                st.session_state.user = match.iloc[0].to_dict()
                # Certificar tipos corretos no session_state.user
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

                # Reset de estados específicos da sessão do cliente
                st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                st.session_state.respostas_atuais_diagnostico = {}
                st.session_state.progresso_diagnostico_percentual = 0
                st.session_state.progresso_diagnostico_contagem = (0,0)
                st.session_state.feedbacks_respostas = {}
                st.session_state.sac_feedback_registrado = {}
                st.session_state.respostas_pesquisa_satisfacao_atual = {}
                st.session_state.diagnostico_enviado_sucesso = False
                st.session_state.target_diag_data_for_expansion = None

                st.toast("Login de cliente bem-sucedido!", icon="👋")
                st.rerun()
            except Exception as e:
                st.error(f"Erro login cliente: {e}")
                st.exception(e) # Para depuração
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    if not st.session_state.user.get("JaVisualizouInstrucoes", False):
        st.session_state.cliente_page = "Instruções"

    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
    with st.sidebar.expander("👤 Meu Perfil", expanded=True):
        logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
        if logo_cliente_path:
            st.image(logo_cliente_path, width=100, use_column_width='auto')
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
    try:
        if os.path.exists(notificacoes_csv):
            df_notif_check = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str})
            if not df_notif_check.empty and 'Lida' in df_notif_check.columns:
                df_notif_check['Lida'] = df_notif_check['Lida'].astype(str).str.lower().map({'true': True, 'false': False, 'nan': False, '': False}).fillna(False)
                notificacoes_nao_lidas_count = len(df_notif_check[
                    (df_notif_check["CNPJ_Cliente"] == st.session_state.cnpj) &
                    (df_notif_check["Lida"] == False)
                ])
    except Exception: pass # Silencioso

    notificacoes_label = "🔔 Notificações"
    if notificacoes_nao_lidas_count > 0:
        notificacoes_label = f"🔔 Notificações ({notificacoes_nao_lidas_count} Nova(s)) ✨"

    menu_options_cli_map_full = {
        "Instruções": "📖 Instruções",
        "Novo Diagnóstico": "📋 Novo Diagnóstico",
        "Painel Principal": "🏠 Painel Principal",
        "Pesquisa de Satisfação": "🌟 Pesquisa de Satisfação",
        "Notificações": notificacoes_label,
        "SAC": "❓ SAC - Perguntas Frequentes"
    }

    if not st.session_state.user.get("JaVisualizouInstrucoes", False):
        menu_options_cli_map = {"Instruções": "📖 Instruções"}
        if st.session_state.cliente_page != "Instruções": st.session_state.cliente_page = "Instruções" # Forçar se não visualizou
    else:
        menu_options_cli_map = menu_options_cli_map_full.copy()
        pode_fazer_novo = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
        if not pode_fazer_novo and "Novo Diagnóstico" in menu_options_cli_map:
            if st.session_state.cliente_page == "Novo Diagnóstico":
                st.session_state.cliente_page = "Painel Principal" # Redireciona se estava em "Novo" e não pode mais
            del menu_options_cli_map["Novo Diagnóstico"]

    menu_options_cli_display = list(menu_options_cli_map.values())

    # Garantir que cliente_page seja uma chave válida
    if st.session_state.cliente_page not in menu_options_cli_map.keys():
        st.session_state.cliente_page = "Instruções" if not st.session_state.user.get("JaVisualizouInstrucoes", False) else "Painel Principal"

    default_display_option_cli = menu_options_cli_map.get(st.session_state.cliente_page)
    current_idx_cli = 0
    if default_display_option_cli and default_display_option_cli in menu_options_cli_display:
        current_idx_cli = menu_options_cli_display.index(default_display_option_cli)
    elif menu_options_cli_display: # Fallback
        current_idx_cli = 0
        for key_pf, val_pf in menu_options_cli_map.items():
            if val_pf == menu_options_cli_display[0]:
                st.session_state.cliente_page = key_pf
                break

    selected_page_cli_raw = st.sidebar.radio("Menu Cliente", menu_options_cli_display, index=current_idx_cli, key="cli_menu_v22_conditional") # Key atualizada

    selected_page_cli_clean = ""
    for key_page_cli, val_page_display_cli in menu_options_cli_map.items():
        if val_page_display_cli == selected_page_cli_raw:
            selected_page_cli_clean = "Notificações" if "Notificações" in key_page_cli else key_page_cli
            break
    
    if selected_page_cli_clean and selected_page_cli_clean != st.session_state.cliente_page:
        st.session_state.cliente_page = selected_page_cli_clean
        st.session_state.force_sidebar_rerun_after_notif_read_v19 = False # Manter nome ou atualizar se necessário
        st.session_state.target_diag_data_for_expansion = None
        st.rerun()

    if st.sidebar.button("⬅️ Sair do Portal Cliente", key="logout_cliente_v22", use_container_width=True): # Key atualizada
        keys_to_clear = [k for k in st.session_state.keys() if k not in ['admin_logado', 'last_cnpj_input']]
        for key_item_clear in keys_to_clear:
            del st.session_state[key_item_clear]
        for key_d_clear, value_d_clear in default_session_state.items():
            if key_d_clear not in ['admin_logado', 'last_cnpj_input']:
                st.session_state[key_d_clear] = value_d_clear
        st.session_state.cliente_logado = False
        st.toast("Logout realizado.", icon="👋")
        st.rerun()

    # --- PÁGINAS DO CLIENTE ---
    if st.session_state.cliente_page == "Instruções":
        st.subheader(menu_options_cli_map_full["Instruções"])
        instrucoes_content_md = ""
        try:
            if os.path.exists(instrucoes_custom_path):
                with open(instrucoes_custom_path, "r", encoding="utf-8") as f: instrucoes_content_md = f.read()
            elif os.path.exists(instrucoes_default_path):
                with open(instrucoes_default_path, "r", encoding="utf-8") as f: instrucoes_content_md = f.read()
                st.caption("ℹ️ Exibindo instruções padrão. O administrador pode personalizar este texto.")
            else:
                instrucoes_content_md = ("# Bem-vindo ao Portal de Diagnóstico!\n\nSiga as instruções para completar seu diagnóstico...")
                st.info("Instruções padrão não encontradas. Exibindo texto base.")
            st.markdown(f'<div class="custom-card" style="background-color: #fff; padding: 25px;">{instrucoes_content_md}</div>', unsafe_allow_html=True)
        except Exception as e_instr:
            st.error(f"Erro ao carregar instruções: {e_instr}")
        
        if st.button("👍 Entendi, prosseguir", key="btn_instrucoes_v22"): # Key atualizada
            update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", "True")
            if st.session_state.user: st.session_state.user["JaVisualizouInstrucoes"] = True
            pode_fazer_novo_inst_cli = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo_inst_cli else "Painel Principal"
            st.rerun()

    elif st.session_state.cliente_page == "Pesquisa de Satisfação":
        st.subheader(menu_options_cli_map_full["Pesquisa de Satisfação"])
        st.markdown("Sua opinião é muito importante para nós! Por favor, reserve um momento para responder.")

        df_perguntas_pesquisa_cliente = carregar_perguntas_pesquisa()
        perguntas_ativas_pesquisa_cliente = df_perguntas_pesquisa_cliente[df_perguntas_pesquisa_cliente['Ativa'] == True]

        if perguntas_ativas_pesquisa_cliente.empty:
            st.info("🔍 Nenhuma pesquisa de satisfação disponível no momento.")
        else:
            id_diag_recente_cliente_pesq = None
            try:
                if os.path.exists(arquivo_csv):
                    df_todos_diags_cli_pesq = pd.read_csv(arquivo_csv, dtype={'CNPJ': str}, encoding='utf-8')
                    df_diags_cliente_pesq = df_todos_diags_cli_pesq[df_todos_diags_cli_pesq["CNPJ"] == st.session_state.cnpj].copy()
                    if not df_diags_cliente_pesq.empty:
                        df_diags_cliente_pesq['Data_dt'] = pd.to_datetime(df_diags_cliente_pesq['Data'], errors='coerce')
                        df_diags_cliente_pesq.sort_values(by='Data_dt', ascending=False, inplace=True)
                        id_diag_recente_cliente_pesq = df_diags_cliente_pesq.iloc[0]['Data']
            except Exception: pass
            
            df_respostas_anteriores_pesq_cli = carregar_respostas_pesquisa()
            id_diag_para_pesquisa_atual_cli = None
            pesquisa_label_cli = "Pesquisa de Satisfação Geral"
            pode_responder_cli = True

            if id_diag_recente_cliente_pesq:
                ja_respondeu_diag_recente_cli = not df_respostas_anteriores_pesq_cli[
                    (df_respostas_anteriores_pesq_cli['CNPJ_Cliente'] == st.session_state.cnpj) &
                    (df_respostas_anteriores_pesq_cli['ID_Diagnostico_Relacionado'] == id_diag_recente_cliente_pesq)
                ].empty
                if not ja_respondeu_diag_recente_cli:
                    id_diag_para_pesquisa_atual_cli = id_diag_recente_cliente_pesq
                    pesquisa_label_cli = f"Pesquisa sobre o Diagnóstico de {id_diag_recente_cliente_pesq}"
                else:
                    ja_respondeu_geral_cli = not df_respostas_anteriores_pesq_cli[
                        (df_respostas_anteriores_pesq_cli['CNPJ_Cliente'] == st.session_state.cnpj) &
                        (df_respostas_anteriores_pesq_cli['ID_Diagnostico_Relacionado'].isnull())
                    ].empty
                    if ja_respondeu_geral_cli:
                        st.success("✅ Você já respondeu à pesquisa de satisfação para seu último diagnóstico e também à pesquisa geral. Obrigado!")
                        pode_responder_cli = False
            else:
                ja_respondeu_geral_cli = not df_respostas_anteriores_pesq_cli[
                    (df_respostas_anteriores_pesq_cli['CNPJ_Cliente'] == st.session_state.cnpj) &
                    (df_respostas_anteriores_pesq_cli['ID_Diagnostico_Relacionado'].isnull())
                ].empty
                if ja_respondeu_geral_cli:
                    st.success("✅ Você já respondeu à nossa pesquisa de satisfação geral. Obrigado!")
                    pode_responder_cli = False
            
            if pode_responder_cli:
                st.info(pesquisa_label_cli)
                with st.form("form_pesquisa_satisfacao_cliente_v22_submit"): # Key atualizada
                    if "respostas_pesquisa_satisfacao_atual" not in st.session_state:
                        st.session_state.respostas_pesquisa_satisfacao_atual = {}

                    for _, row_pergunta_cli_pesq in perguntas_ativas_pesquisa_cliente.iterrows():
                        id_p_cli_pesq = row_pergunta_cli_pesq['ID_Pesquisa_Pergunta']
                        texto_p_cli_pesq = row_pergunta_cli_pesq['Texto_Pergunta_Pesquisa']
                        tipo_p_cli_pesq = row_pergunta_cli_pesq['Tipo_Pergunta_Pesquisa']
                        key_widget_cli_pesq = f"resp_pesq_cli_{id_p_cli_pesq}_v22" # Key atualizada

                        st.markdown(f"##### {texto_p_cli_pesq}")
                        if tipo_p_cli_pesq == "Escala_1_5":
                            current_val_1_5_cli = st.session_state.respostas_pesquisa_satisfacao_atual.get(id_p_cli_pesq, 3)
                            st.session_state.respostas_pesquisa_satisfacao_atual[id_p_cli_pesq] = st.radio("", options=[1,2,3,4,5], index=current_val_1_5_cli -1 , key=key_widget_cli_pesq, horizontal=True, help="1=Péssimo, 5=Excelente")
                        elif tipo_p_cli_pesq == "Escala_NPS_0_10":
                            current_val_0_10_cli = st.session_state.respostas_pesquisa_satisfacao_atual.get(id_p_cli_pesq, 5)
                            st.session_state.respostas_pesquisa_satisfacao_atual[id_p_cli_pesq] = st.radio("", options=list(range(11)), index=current_val_0_10_cli, key=key_widget_cli_pesq, horizontal=True, help="0=Pouco Provável, 10=Muito Provável")
                        elif tipo_p_cli_pesq == "Texto_Aberto":
                            st.session_state.respostas_pesquisa_satisfacao_atual[id_p_cli_pesq] = st.text_area("Sua resposta:", key=key_widget_cli_pesq, height=100, value=st.session_state.respostas_pesquisa_satisfacao_atual.get(id_p_cli_pesq,""))
                        elif tipo_p_cli_pesq == "Sim_Nao":
                            current_val_sim_nao_cli = st.session_state.respostas_pesquisa_satisfacao_atual.get(id_p_cli_pesq)
                            index_sim_nao_cli = ["Sim", "Não"].index(current_val_sim_nao_cli) if current_val_sim_nao_cli in ["Sim", "Não"] else None
                            st.session_state.respostas_pesquisa_satisfacao_atual[id_p_cli_pesq] = st.radio("", options=["Sim", "Não"], index=index_sim_nao_cli, key=key_widget_cli_pesq, horizontal=True)
                        st.markdown("---")

                    comentario_geral_pesq_val_cli = st.text_area("Comentários adicionais (opcional):", key="comentario_geral_pesq_cli_v22_val", value=st.session_state.respostas_pesquisa_satisfacao_atual.get("__comentario_geral__","")) # Key atualizada
                    st.session_state.respostas_pesquisa_satisfacao_atual["__comentario_geral__"] = comentario_geral_pesq_val_cli
                    
                    submit_pesquisa_cliente_final = st.form_submit_button("✔️ Enviar Respostas da Pesquisa", use_container_width=True)

                    if submit_pesquisa_cliente_final:
                        novas_entradas_respostas_final_cli = []
                        ts_resposta_final_cli = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        all_mandatory_answered_cli = True
                        for _, row_p_check_cli in perguntas_ativas_pesquisa_cliente.iterrows():
                            id_p_c_cli = row_p_check_cli['ID_Pesquisa_Pergunta']
                            if row_p_check_cli['Tipo_Pergunta_Pesquisa'] != "Texto_Aberto" and st.session_state.respostas_pesquisa_satisfacao_atual.get(id_p_c_cli) is None:
                                all_mandatory_answered_cli = False
                                st.warning(f"Por favor, responda a pergunta: '{row_p_check_cli['Texto_Pergunta_Pesquisa']}'")
                                break
                        
                        if all_mandatory_answered_cli:
                            for id_pergunta_final_cli, resposta_val_final_cli in st.session_state.respostas_pesquisa_satisfacao_atual.items():
                                if id_pergunta_final_cli.startswith("__"): continue
                                if resposta_val_final_cli is not None:
                                    novas_entradas_respostas_final_cli.append({
                                        "ID_Resposta_Pesquisa": str(uuid.uuid4()), "ID_Pesquisa_Pergunta": id_pergunta_final_cli,
                                        "CNPJ_Cliente": st.session_state.cnpj, "ID_Diagnostico_Relacionado": id_diag_para_pesquisa_atual_cli,
                                        "Resposta_Pesquisa": str(resposta_val_final_cli), "Timestamp_Resposta": ts_resposta_final_cli,
                                        "Comentario_Adicional_Pesquisa": st.session_state.respostas_pesquisa_satisfacao_atual.get("__comentario_geral__", "") if id_pergunta_final_cli == perguntas_ativas_pesquisa_cliente.iloc[0]['ID_Pesquisa_Pergunta'] else ""
                                    })
                            
                            if novas_entradas_respostas_final_cli:
                                df_respostas_atual_final_cli = carregar_respostas_pesquisa()
                                df_novas_respostas_final_cli = pd.DataFrame(novas_entradas_respostas_final_cli)
                                df_respostas_concat_final_cli = pd.concat([df_respostas_atual_final_cli, df_novas_respostas_final_cli], ignore_index=True)
                                df_respostas_concat_final_cli.to_csv(pesquisa_satisfacao_respostas_csv, index=False, encoding='utf-8')
                                st.cache_data.clear()
                                st.success("✅ Pesquisa enviada com sucesso! Agradecemos seu feedback.")
                                registrar_acao(st.session_state.cnpj, "Pesquisa Satisfação", f"Cliente respondeu (Diag: {id_diag_para_pesquisa_atual_cli if id_diag_para_pesquisa_atual_cli else 'Geral'}).")
                                st.session_state.respostas_pesquisa_satisfacao_atual = {}
                                st.session_state.cliente_page = "Painel Principal"
                                st.rerun()
                            else: st.warning("⚠️ Nenhuma resposta foi fornecida para salvar.")


    # --- PARA AS OUTRAS PÁGINAS DO CLIENTE (SAC, Notificações, Painel Principal, Novo Diagnóstico) ---
    # --- COLE O CÓDIGO DESSAS SEÇÕES AQUI, CONFORME AS VERSÕES ANTERIORES ---
    # Exemplo (você precisará preencher com o código real de cada seção):
    elif st.session_state.cliente_page == "SAC":
        st.subheader(menu_options_cli_map_full["SAC"])
        # ... SEU CÓDIGO PARA A PÁGINA SAC AQUI ...
        st.write("Conteúdo da página SAC do cliente.")

    elif st.session_state.cliente_page == "Notificações":
        st.subheader(menu_options_cli_map_full["Notificações"])
        # ... SEU CÓDIGO PARA A PÁGINA NOTIFICAÇÕES AQUI ...
        st.write("Conteúdo da página Notificações do cliente.")

    elif st.session_state.cliente_page == "Painel Principal":
        st.subheader(menu_options_cli_map_full["Painel Principal"])
        # ... SEU CÓDIGO PARA A PÁGINA PAINEL PRINCIPAL AQUI ...
        st.write("Conteúdo da página Painel Principal do cliente.")

    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.subheader(menu_options_cli_map_full["Novo Diagnóstico"])
        # ... SEU CÓDIGO PARA A PÁGINA NOVO DIAGNÓSTICO AQUI ...
        st.write("Conteúdo da página Novo Diagnóstico do cliente.")


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    try:
        st.sidebar.markdown("## ⚙️ Painel Admin")
    except Exception as e_img_admin_sidebar:
        st.sidebar.caption(f"Logo admin não carregada: {e_img_admin_sidebar}")

    st.sidebar.success("🟢 Admin Logado")

    if st.sidebar.button("🚪 Sair do Painel Admin", key="logout_admin_v22", use_container_width=True): # Key atualizada
        st.session_state.admin_logado = False
        st.toast("Logout de admin realizado.", icon="👋")
        st.rerun()

    menu_admin_options_map = {
        "Visão Geral e Diagnósticos": "📊",
        "Relatório de Engajamento": "📈",
        "Gerenciar Notificações": "🔔",
        "Gerenciar Clientes": "👥",
        "Gerenciar Perguntas Diagnóstico": "📝",
        "Gerenciar Análises de Perguntas": "💡",
        "Gerenciar SAC": "📞",
        "🌟 Gerenciar Pesquisa de Satisfação": "🌟",
        "Gerenciar Instruções": "⚙️",
        "Histórico de Usuários": "📜",
        "Gerenciar Administradores": "👮"
    }
    admin_page_text_keys = list(menu_admin_options_map.keys())
    admin_options_for_display = [f"{menu_admin_options_map[key_admin_disp]} {key_admin_disp}" for key_admin_disp in admin_page_text_keys]

    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_text_key_v22" # Key atualizada
    WIDGET_KEY_SB_ADMIN_MENU = "sb_admin_menu_v22" # Key atualizada

    def admin_menu_on_change():
        selected_display_value_admin = st.session_state[WIDGET_KEY_SB_ADMIN_MENU]
        new_text_key_admin = None
        for text_key_adm_change, emoji_adm_change in menu_admin_options_map.items():
            if f"{emoji_adm_change} {text_key_adm_change}" == selected_display_value_admin:
                new_text_key_admin = text_key_adm_change
                break
        if new_text_key_admin and new_text_key_admin != st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE):
            st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = new_text_key_admin

    if SESSION_KEY_FOR_ADMIN_PAGE not in st.session_state or \
       st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] not in admin_page_text_keys:
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]

    current_admin_page_text_key_for_index = st.session_state[SESSION_KEY_FOR_ADMIN_PAGE]
    try:
        expected_display_value_for_current_page_admin = f"{menu_admin_options_map[current_admin_page_text_key_for_index]} {current_admin_page_text_key_for_index}"
        current_admin_menu_index = admin_options_for_display.index(expected_display_value_for_current_page_admin)
    except (ValueError, KeyError):
        current_admin_menu_index = 0
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]

    st.sidebar.selectbox(
        "Funcionalidades Admin:", options=admin_options_for_display, index=current_admin_menu_index,
        key=WIDGET_KEY_SB_ADMIN_MENU, on_change=admin_menu_on_change
    )

    menu_admin = st.session_state[SESSION_KEY_FOR_ADMIN_PAGE]
    header_display_name = f"{menu_admin_options_map.get(menu_admin, '')} {menu_admin}"
    st.header(header_display_name)

    # --- PÁGINAS DO ADMIN ---
    # --- COLE O CÓDIGO DAS SEÇÕES DO ADMIN AQUI, GARANTINDO QUE AS chaves `elif menu_admin == "CHAVE_EXATA_DO_MAPA":` ESTEJAM CORRETAS ---
    if menu_admin == "Visão Geral e Diagnósticos":
        st.write("Conteúdo da Visão Geral e Diagnósticos do Admin.")
        # ... SEU CÓDIGO PARA ESTA SEÇÃO ...
        pass
    elif menu_admin == "Relatório de Engajamento":
        st.write("Conteúdo do Relatório de Engajamento do Admin.")
        # ... SEU CÓDIGO PARA ESTA SEÇÃO ...
        pass
    elif menu_admin == "Gerenciar Notificações":
        st.write("Conteúdo de Gerenciar Notificações do Admin.")
        # ... SEU CÓDIGO PARA ESTA SEÇÃO ...
        pass
    elif menu_admin == "Gerenciar Clientes":
        st.write("Conteúdo de Gerenciar Clientes do Admin.")
        # ... SEU CÓDIGO PARA ESTA SEÇÃO ...
        pass
    elif menu_admin == "Gerenciar Perguntas Diagnóstico":
        st.write("Conteúdo de Gerenciar Perguntas do Diagnóstico do Admin.")
        # ... SEU CÓDIGO PARA ESTA SEÇÃO ...
        pass
    elif menu_admin == "Gerenciar Análises de Perguntas":
        st.write("Conteúdo de Gerenciar Análises de Perguntas do Admin.")
        # ... SEU CÓDIGO PARA ESTA SEÇÃO ...
        pass
    elif menu_admin == "Gerenciar SAC":
        st.write("Conteúdo de Gerenciar SAC do Admin.")
        # ... SEU CÓDIGO PARA ESTA SEÇÃO ...
        pass
    
    elif menu_admin == "🌟 Gerenciar Pesquisa de Satisfação":
        st.markdown("#### 🌟 Gerenciamento da Pesquisa de Satisfação")
        df_pesquisa_perguntas_admin = carregar_perguntas_pesquisa().copy()
        df_pesquisa_respostas_admin = carregar_respostas_pesquisa().copy()

        tabs_admin_pesquisa = st.tabs(["🔧 Gerenciar Perguntas", "📈 Resultados da Pesquisa"])

        with tabs_admin_pesquisa[0]: # GERENCIAR PERGUNTAS DA PESQUISA
            st.subheader("Adicionar Nova Pergunta para a Pesquisa de Satisfação")
            with st.form("form_nova_pergunta_pesquisa_admin_v22", clear_on_submit=True): # Key atualizada
                nova_texto_p_pesquisa_adm = st.text_input("Texto da Pergunta:", key="txt_nova_p_pesq_adm_v22") # Key atualizada
                tipos_disponiveis_pesquisa_adm = ["Escala_1_5", "Escala_NPS_0_10", "Texto_Aberto", "Sim_Nao"]
                novo_tipo_p_pesquisa_adm = st.selectbox("Tipo da Pergunta:", tipos_disponiveis_pesquisa_adm, key="tipo_nova_p_pesq_adm_v22") # Key atualizada
                nova_cat_p_pesquisa_adm = st.text_input("Categoria (opcional, ex: Geral, Atendimento):", value="Geral", key="cat_nova_p_pesq_adm_v22") # Key atualizada
                nova_ordem_p_pesquisa_adm = st.number_input("Ordem de Exibição (menor aparece primeiro):", min_value=0, value=0, step=1, key="ordem_nova_p_pesq_adm_v22") # Key atualizada
                nova_ativa_p_pesquisa_adm = st.checkbox("Pergunta Ativa?", value=True, key="ativa_nova_p_pesq_adm_v22") # Key atualizada
                
                submit_nova_p_pesquisa_adm = st.form_submit_button("➕ Adicionar Pergunta à Pesquisa")
                if submit_nova_p_pesquisa_adm:
                    if nova_texto_p_pesquisa_adm.strip():
                        nova_id_p_adm = str(uuid.uuid4())
                        nova_entrada_adm = pd.DataFrame([{
                            "ID_Pesquisa_Pergunta": nova_id_p_adm,
                            "Texto_Pergunta_Pesquisa": nova_texto_p_pesquisa_adm.strip(),
                            "Tipo_Pergunta_Pesquisa": novo_tipo_p_pesquisa_adm,
                            "Categoria_Pesquisa": nova_cat_p_pesquisa_adm.strip() if nova_cat_p_pesquisa_adm.strip() else "Geral",
                            "Ordem_Exibicao": nova_ordem_p_pesquisa_adm,
                            "Ativa": nova_ativa_p_pesquisa_adm,
                            "DataCriacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }])
                        df_pesquisa_perguntas_existente_adm = carregar_perguntas_pesquisa()
                        df_pesquisa_perguntas_final_adm = pd.concat([df_pesquisa_perguntas_existente_adm, nova_entrada_adm], ignore_index=True)
                        df_pesquisa_perguntas_final_adm.to_csv(pesquisa_satisfacao_perguntas_csv, index=False, encoding='utf-8')
                        st.cache_data.clear()
                        st.success(f"Pergunta '{nova_texto_p_pesquisa_adm[:30]}...' adicionada!"); st.rerun()
                    else:
                        st.warning("O texto da pergunta é obrigatório.")
            
            st.divider()
            st.subheader("Perguntas Cadastradas na Pesquisa")
            if df_pesquisa_perguntas_admin.empty:
                st.info("Nenhuma pergunta de pesquisa cadastrada.")
            else:
                for i_adm_pesq, row_adm_pesq in df_pesquisa_perguntas_admin.sort_values(by=['Ordem_Exibicao', 'DataCriacao']).iterrows():
                    unique_suffix_pesq_adm_edit = f"_pesq_edit_adm_{row_adm_pesq['ID_Pesquisa_Pergunta']}" # Key atualizada
                    status_icon_pesq_adm = "✅ Ativa" if row_adm_pesq['Ativa'] else "❌ Inativa"
                    st.markdown(f"""<div class="custom-card" style="border-left-color: {'#10b981' if row_adm_pesq['Ativa'] else '#dc3545'};">
                                    <b>{row_adm_pesq['Texto_Pergunta_Pesquisa']}</b><br>
                                    <small><i>ID: {row_adm_pesq['ID_Pesquisa_Pergunta']} | Tipo: {row_adm_pesq['Tipo_Pergunta_Pesquisa']} | Cat: {row_adm_pesq.get('Categoria_Pesquisa','Geral')} | Ordem: {row_adm_pesq.get('Ordem_Exibicao',0)} | Status: {status_icon_pesq_adm}</i></small>
                                </div>""", unsafe_allow_html=True)
                    with st.expander("✏️ Editar / 🗑️ Deletar Pergunta"):
                        with st.form(f"form_edit_pesq_p_adm{unique_suffix_pesq_adm_edit}"): # Key atualizada
                            edited_texto_pesq_adm = st.text_input("Texto:", value=row_adm_pesq['Texto_Pergunta_Pesquisa'], key=f"txt_edit_adm{unique_suffix_pesq_adm_edit}") # Key atualizada
                            edited_tipo_pesq_adm = st.selectbox("Tipo:", tipos_disponiveis_pesquisa_adm, index=tipos_disponiveis_pesquisa_adm.index(row_adm_pesq['Tipo_Pergunta_Pesquisa']) if row_adm_pesq['Tipo_Pergunta_Pesquisa'] in tipos_disponiveis_pesquisa_adm else 0, key=f"tipo_edit_adm{unique_suffix_pesq_adm_edit}") # Key atualizada
                            edited_cat_pesq_adm = st.text_input("Categoria:", value=row_adm_pesq.get('Categoria_Pesquisa','Geral'), key=f"cat_edit_adm{unique_suffix_pesq_adm_edit}") # Key atualizada
                            edited_ordem_pesq_adm = st.number_input("Ordem:", value=int(row_adm_pesq.get('Ordem_Exibicao',0)), min_value=0, step=1, key=f"ordem_edit_adm{unique_suffix_pesq_adm_edit}") # Key atualizada
                            edited_ativa_pesq_adm = st.checkbox("Ativa?", value=bool(row_adm_pesq['Ativa']), key=f"ativa_edit_adm{unique_suffix_pesq_adm_edit}") # Key atualizada
                            
                            col_b1_pesq_edit_adm, col_b2_pesq_edit_adm = st.columns(2)
                            if col_b1_pesq_edit_adm.form_submit_button("💾 Salvar Alterações", use_container_width=True, key=f"save_btn_adm{unique_suffix_pesq_adm_edit}"): # Key atualizada
                                df_pesquisa_perguntas_admin.loc[i_adm_pesq, "Texto_Pergunta_Pesquisa"] = edited_texto_pesq_adm
                                df_pesquisa_perguntas_admin.loc[i_adm_pesq, "Tipo_Pergunta_Pesquisa"] = edited_tipo_pesq_adm
                                df_pesquisa_perguntas_admin.loc[i_adm_pesq, "Categoria_Pesquisa"] = edited_cat_pesq_adm if edited_cat_pesq_adm.strip() else "Geral"
                                df_pesquisa_perguntas_admin.loc[i_adm_pesq, "Ordem_Exibicao"] = edited_ordem_pesq_adm
                                df_pesquisa_perguntas_admin.loc[i_adm_pesq, "Ativa"] = edited_ativa_pesq_adm
                                df_pesquisa_perguntas_admin.to_csv(pesquisa_satisfacao_perguntas_csv, index=False, encoding='utf-8')
                                st.cache_data.clear(); st.success("Pergunta atualizada!"); st.rerun()
                            
                            if col_b2_pesq_edit_adm.form_submit_button("🗑️ Deletar Pergunta", type="primary", use_container_width=True, key=f"del_btn_adm{unique_suffix_pesq_adm_edit}"): # Key atualizada
                                df_pesquisa_perguntas_admin = df_pesquisa_perguntas_admin.drop(index=i_adm_pesq)
                                df_pesquisa_perguntas_admin.to_csv(pesquisa_satisfacao_perguntas_csv, index=False, encoding='utf-8')
                                st.cache_data.clear(); st.warning("Pergunta deletada!"); st.rerun()
                    st.markdown("---")

        with tabs_admin_pesquisa[1]: # RESULTADOS DA PESQUISA
            st.subheader("Resultados e Dashboards da Pesquisa de Satisfação")
            if df_pesquisa_respostas_admin.empty:
                st.info("Nenhuma resposta de pesquisa para analisar ainda.")
            else:
                df_perguntas_pesq_para_merge_adm = carregar_perguntas_pesquisa()
                df_respostas_detalhadas_pesq_adm = pd.merge(df_pesquisa_respostas_admin, df_perguntas_pesq_para_merge_adm[['ID_Pesquisa_Pergunta', 'Texto_Pergunta_Pesquisa', 'Tipo_Pergunta_Pesquisa', 'Categoria_Pesquisa']], on="ID_Pesquisa_Pergunta", how="left")
                
                df_usuarios_admin_geral_load_pesq = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                if not df_usuarios_admin_geral_load_pesq.empty:
                    df_respostas_detalhadas_pesq_adm = pd.merge(df_respostas_detalhadas_pesq_adm, df_usuarios_admin_geral_load_pesq[['CNPJ', 'Empresa']], left_on="CNPJ_Cliente", right_on="CNPJ", how="left")
                    df_respostas_detalhadas_pesq_adm.rename(columns={'Empresa': 'Empresa_Cliente_Pesq_Adm'}, inplace=True) # Key atualizada
                    df_respostas_detalhadas_pesq_adm['Empresa_Cliente_Pesq_Adm'] = df_respostas_detalhadas_pesq_adm['Empresa_Cliente_Pesq_Adm'].fillna("N/D")
                else: df_respostas_detalhadas_pesq_adm['Empresa_Cliente_Pesq_Adm'] = "N/D"
                df_respostas_detalhadas_pesq_adm.fillna({'Texto_Pergunta_Pesquisa': 'Pergunta Excluída', 'Tipo_Pergunta_Pesquisa': 'Desconhecido'}, inplace=True)

                st.sidebar.markdown("---"); st.sidebar.subheader("🔎 Filtros - Pesquisa")
                lista_empresas_pesq_admin_filt = ["Todas"] + sorted(df_respostas_detalhadas_pesq_adm['Empresa_Cliente_Pesq_Adm'].unique().tolist())
                emp_sel_pesq_admin_filt = st.sidebar.selectbox("Empresa (Pesquisa):", lista_empresas_pesq_admin_filt, key="f_emp_pesq_admin_v22_filt") # Key atualizada
                
                lista_perguntas_pesq_admin_filt = ["Todas"] + sorted(df_respostas_detalhadas_pesq_adm['Texto_Pergunta_Pesquisa'].unique().tolist())
                perg_sel_pesq_admin_filt = st.sidebar.selectbox("Pergunta da Pesquisa:", lista_perguntas_pesq_admin_filt, key="f_perg_pesq_admin_v22_filt") # Key atualizada
                
                dt_ini_pesq_admin_filt = st.sidebar.date_input("Data Início Resposta Pesquisa:", None, key="f_dt_ini_pesq_admin_v22_filt") # Key atualizada
                dt_fim_pesq_admin_filt = st.sidebar.date_input("Data Fim Resposta Pesquisa:", None, key="f_dt_fim_pesq_admin_v22_filt") # Key atualizada

                df_filtrado_pesq_admin_final = df_respostas_detalhadas_pesq_adm.copy()
                if emp_sel_pesq_admin_filt != "Todas": df_filtrado_pesq_admin_final = df_filtrado_pesq_admin_final[df_filtrado_pesq_admin_final['Empresa_Cliente_Pesq_Adm'] == emp_sel_pesq_admin_filt]
                if perg_sel_pesq_admin_filt != "Todas": df_filtrado_pesq_admin_final = df_filtrado_pesq_admin_final[df_filtrado_pesq_admin_final['Texto_Pergunta_Pesquisa'] == perg_sel_pesq_admin_filt]
                if dt_ini_pesq_admin_filt:
                    df_filtrado_pesq_admin_final['Timestamp_Resposta_dt'] = pd.to_datetime(df_filtrado_pesq_admin_final['Timestamp_Resposta'])
                    df_filtrado_pesq_admin_final = df_filtrado_pesq_admin_final[df_filtrado_pesq_admin_final['Timestamp_Resposta_dt'] >= pd.to_datetime(dt_ini_pesq_admin_filt)]
                if dt_fim_pesq_admin_filt:
                    if 'Timestamp_Resposta_dt' not in df_filtrado_pesq_admin_final: df_filtrado_pesq_admin_final['Timestamp_Resposta_dt'] = pd.to_datetime(df_filtrado_pesq_admin_final['Timestamp_Resposta'])
                    df_filtrado_pesq_admin_final = df_filtrado_pesq_admin_final[df_filtrado_pesq_admin_final['Timestamp_Resposta_dt'] < pd.to_datetime(dt_fim_pesq_admin_filt) + pd.Timedelta(days=1)]

                if df_filtrado_pesq_admin_final.empty: st.info("Nenhuma resposta encontrada para os filtros aplicados.")
                else:
                    st.metric("Total de Respostas (Considerando Filtros)", df_filtrado_pesq_admin_final['ID_Resposta_Pesquisa'].nunique())
                    
                    perguntas_para_plotar_admin_pesq_final = []
                    if perg_sel_pesq_admin_filt != "Todas": perguntas_para_plotar_admin_pesq_final = [perg_sel_pesq_admin_filt]
                    else:
                        perguntas_para_plotar_admin_pesq_final = df_filtrado_pesq_admin_final[df_filtrado_pesq_admin_final['Tipo_Pergunta_Pesquisa'].isin(["Escala_1_5", "Escala_NPS_0_10", "Sim_Nao"])]['Texto_Pergunta_Pesquisa'].unique().tolist()

                    for pergunta_txt_plot_adm_pesq_f in perguntas_para_plotar_admin_pesq_final:
                        tipo_da_pergunta_plot_adm_pesq_f = df_filtrado_pesq_admin_final[df_filtrado_pesq_admin_final['Texto_Pergunta_Pesquisa'] == pergunta_txt_plot_adm_pesq_f]['Tipo_Pergunta_Pesquisa'].iloc[0]
                        fig_dist_adm_pesq_f = create_satisfaction_distribution_chart(df_filtrado_pesq_admin_final, pergunta_txt_plot_adm_pesq_f, tipo_da_pergunta_plot_adm_pesq_f)
                        if fig_dist_adm_pesq_f: st.plotly_chart(fig_dist_adm_pesq_f, use_container_width=True)
                    
                    st.divider()
                    st.subheader("Respostas Detalhadas (Filtradas)")
                    cols_show_resp_adm_pesq_f = ['Timestamp_Resposta', 'Empresa_Cliente_Pesq_Adm', 'CNPJ_Cliente', 'Texto_Pergunta_Pesquisa', 'Resposta_Pesquisa', 'Comentario_Adicional_Pesquisa', 'ID_Diagnostico_Relacionado']
                    st.dataframe(df_filtrado_pesq_admin_final[cols_show_resp_adm_pesq_f].sort_values(by="Timestamp_Resposta", ascending=False), use_container_width=True)
                    
                    csv_export_resp_adm_data_f = df_filtrado_pesq_admin_final[cols_show_resp_adm_pesq_f].to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Baixar Respostas Filtradas (CSV)", data=csv_export_resp_adm_data_f,
                                       file_name=f"respostas_pesquisa_satisfacao_filtrado_{datetime.now().strftime('%Y%m%d')}.csv", mime='text/csv', key="dl_pesq_admin_v22_final") # Key atualizada

    elif menu_admin == "Gerenciar Instruções":
        st.write("Conteúdo de Gerenciar Instruções do Admin.")
        # ... SEU CÓDIGO PARA ESTA SEÇÃO ...
        pass
    elif menu_admin == "Histórico de Usuários":
        st.write("Conteúdo de Histórico de Usuários do Admin.")
        # ... SEU CÓDIGO PARA ESTA SEÇÃO ...
        pass
    elif menu_admin == "Gerenciar Administradores":
        st.write("Conteúdo de Gerenciar Administradores do Admin.")
        # ... SEU CÓDIGO PARA ESTA SEÇÃO ...
        pass
    else:
        st.warning(f"Página admin '{menu_admin}' não reconhecida ou ainda não implementada.")


# --- Rodapé ou final do script ---
if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()