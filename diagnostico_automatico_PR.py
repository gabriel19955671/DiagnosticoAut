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
st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", page_icon=" ")

# Função para obter as permissões atuais do administrador
def get_admin_permissoes(usuario):
    df = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
    linha = df[df['Usuario'] == usuario]
    if not linha.empty:
        return str(linha.iloc[0]['Permissoes']).split(',')
    return []

# Função para definir permissões do administrador
def set_admin_permissoes(usuario, permissoes):
    df = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
    idx = df[df['Usuario'] == usuario].index
    if not idx.empty:
        df.loc[idx, 'Permissoes'] = ','.join(permissoes)
        df.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')

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
.login-container img.portal-logo { /* Estilo específico para o logo do portal no login */
    max-height: 80px; /* Ajuste a altura máxima conforme necessário */
    width: auto;    /* Mantém a proporção */
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
.stButton>button:disabled {
    background-color: #9ca3af !important;  
    color: #e5e7eb !important;
    cursor: not-allowed !important;
}
.stButton>button.secondary {
    background-color: #e5e7eb;
    color: #374151;
}
.stButton>button.secondary:hover {
    background-color: #d1d5db;
}
.stButton>button.secondary:disabled {
    background-color: #d1d5db !important;
    color: #9ca3af !important;
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
.stTextInput>div>input, .stTextArea>div>textarea, .stDateInput>div>input, .stSelectbox>div>div, .stNumberInput>div>input, .stFileUpload>div>button {
    border-radius: 6px;
    padding: 0.6rem;
    border: 1px solid #d1d5db;
    background-color: #f9fafb;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.stTextInput>div>input:focus, .stTextArea>div>textarea:focus, .stDateInput>div>input:focus, .stSelectbox>div>div:focus-within, .stNumberInput>div>input:focus {
    border-color: #2563eb;
    box-shadow: 0 0 0 0.1rem rgba(37, 99, 235, 0.25);
}
.stTextInput>div>input:disabled, 
.stTextArea>div>textarea:disabled, 
.stDateInput>div>input:disabled, 
.stSelectbox>div>div[aria-disabled="true"], 
.stNumberInput>div>input:disabled,
.stFileUpload>div>button:disabled { /* Estilo para botão de upload desabilitado */
    background-color: #e5e7eb !important;
    color: #9ca3af !important;
    cursor: not-allowed !important;
    border-color: #d1d5db !important;
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
.survey-question-container {
    background-color: #f9fafb;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 15px;
    border: 1px solid #e5e7eb;
}
.survey-question-container label {
    font-weight: 600;
    color: #374151;
    display: block;
    margin-bottom: 8px;
}
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
LOGOS_DIR = "client_logos"
PORTAL_ASSETS_DIR = "portal_assets" # Novo para logo do portal
PORTAL_LOGO_FILENAME = "portal_logo.png" # Nome padrão do logo do portal

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {}, "sac_feedback_registrado": {},
    "force_sidebar_rerun_after_notif_read_v19": False, # Mantido v19 para compatibilidade se necessário
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
def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_'); s = re.sub(r'(?u)[^-\w.]', '', s); return s
def pdf_safe_text_output(text): return str(text).encode('latin-1', 'replace').decode('latin-1')

def find_client_logo_path(cnpj_arg):
    if not cnpj_arg: return None
    base = str(cnpj_arg).replace('/', '').replace('.', '').replace('-', '')
    for ext in ["png", "jpg", "jpeg"]: # Adicionar mais extensões se necessário
        path = os.path.join(LOGOS_DIR, f"{base}_logo.{ext}")
        if os.path.exists(path): return path
    return None

def get_portal_logo_path():
    path = os.path.join(PORTAL_ASSETS_DIR, PORTAL_LOGO_FILENAME)
    if os.path.exists(path):
        return path
    return None # Ou um placeholder/default logo path

# Criar diretórios se não existirem
for dir_path in [LOGOS_DIR, PORTAL_ASSETS_DIR]:
    if not os.path.exists(dir_path):
        try: os.makedirs(dir_path)
        except OSError as e: st.error(f"Erro ao criar diretório '{dir_path}': {e}")


colunas_base_admin_credenciais = ["Usuario", "Senha", "Permissoes"]  
colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone",
                          "JaVisualizouInstrucoes", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]
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
                     defaults={"JaVisualizouInstrucoes": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0})
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

def gerar_pdf_diagnostico_completo(diag_data, user_data, perguntas_df, respostas_coletadas, medias_cat, analises_df):
    try:
        with st.spinner("Gerando PDF do diagnóstico... Aguarde."):
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            
            # Portal Logo (Header)
            portal_logo_path = get_portal_logo_path()
            if portal_logo_path:
                try:
                    pdf.image(portal_logo_path, x=170, y=8, h=15) # Posição no canto superior direito
                except Exception as e_pl:
                    print(f"Erro ao adicionar logo do portal ao PDF: {e_pl}")

            # Client Logo
            empresa_nome = user_data.get("Empresa", "N/D")
            cnpj_pdf = user_data.get("CNPJ", "N/D")
            client_logo_path_pdf = find_client_logo_path(cnpj_pdf)
            initial_y_after_portal_logo = pdf.get_y()

            if client_logo_path_pdf:
                try:
                    pdf.image(client_logo_path_pdf, x=10, y=initial_y_after_portal_logo, h=20) # Logo do cliente à esquerda
                    pdf.set_y(initial_y_after_portal_logo + 20 + 5) # Ajusta Y após logo do cliente
                except Exception as e_cl:
                    print(f"Erro ao adicionar logo do cliente ao PDF: {e_cl}")
                    pdf.set_y(initial_y_after_portal_logo) # Garante que Y está definido
            else:
                    pdf.set_y(initial_y_after_portal_logo)


            pdf.set_font("Arial", 'B', 18)
            pdf.cell(0, 10, pdf_safe_text_output(f"Diagnóstico Empresarial"), 0, 1, 'C')
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, pdf_safe_text_output(empresa_nome), 0, 1, 'C')
            pdf.ln(5)

            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 7, pdf_safe_text_output(f"Data: {diag_data.get('Data','N/D')} | CNPJ: {cnpj_pdf}"))
            if user_data.get("NomeContato"): pdf.multi_cell(0, 7, pdf_safe_text_output(f"Contato: {user_data.get('NomeContato')}"))
            if user_data.get("Telefone"): pdf.multi_cell(0, 7, pdf_safe_text_output(f"Telefone: {user_data.get('Telefone')}"))
            pdf.ln(3)
            
            # Summary Box
            pdf.set_fill_color(230, 230, 230) # Light grey
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, "Resumo dos Indicadores Chave", 1, 1, 'C', fill=True)
            pdf.set_font("Arial", size=10)
            pdf.cell(95, 8, pdf_safe_text_output(f"Média Geral do Diagnóstico: {diag_data.get('Média Geral','N/A')}"), 1, 0, 'L')
            pdf.cell(95, 8, pdf_safe_text_output(f"Score GUT Médio: {diag_data.get('GUT Média','N/A')}"), 1, 1, 'L')
            pdf.ln(5)

            if medias_cat:
                pdf.set_font("Arial", 'B', 11); pdf.multi_cell(0, 7, pdf_safe_text_output("Médias por Categoria:"))
                pdf.set_font("Arial", size=10)
                # Criar tabela para médias por categoria
                pdf.set_fill_color(240, 240, 240)
                col_width_cat = pdf.w / 2.2 # Ajustar largura
                line_height_cat = pdf.font_size * 1.5
                
                first_col = True
                for cat, media in medias_cat.items():
                    if first_col:
                        pdf.cell(col_width_cat, line_height_cat, pdf_safe_text_output(f"{cat}: {media:.2f}"), border=1, ln=0, fill=True)
                        first_col = False
                    else:
                        pdf.cell(col_width_cat, line_height_cat, pdf_safe_text_output(f"{cat}: {media:.2f}"), border=1, ln=1, fill=True)
                        first_col = True
                if not first_col: # Se o número de categorias for ímpar, fechar a linha
                    pdf.ln(line_height_cat)
                pdf.ln(5)


            for titulo, campo in [("Resumo do Diagnóstico (Cliente):", "Diagnóstico"),  
                                  ("Análise Adicional (Cliente):", "Análise do Cliente"),  
                                  ("Comentários do Consultor:", "Comentarios_Admin")]:
                valor = diag_data.get(campo, "")
                if valor and not pd.isna(valor) and str(valor).strip():
                    pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output(titulo), ln=1)
                    pdf.set_font("Arial", size=10);  
                    pdf.set_draw_color(200,200,200) # Cor da borda da caixa de texto
                    pdf.multi_cell(0, 7, pdf_safe_text_output(str(valor)), border=1, ln=1, align='J') # Justificado
                    pdf.set_draw_color(0,0,0) # Resetar cor da borda
                    pdf.ln(3)

            pdf.add_page() # Nova página para detalhes
            pdf.set_font("Arial", 'B', 14); pdf.cell(0, 10, pdf_safe_text_output("Respostas Detalhadas e Análises"), 0, 1, 'C'); pdf.ln(5)
            
            categorias = perguntas_df["Categoria"].unique() if not perguntas_df.empty and "Categoria" in perguntas_df.columns else []
            for categoria in categorias:
                pdf.set_font("Arial", 'B', 11);  
                pdf.set_fill_color(220, 220, 255) # Azul claro para cabeçalho de categoria
                pdf.cell(0, 8, pdf_safe_text_output(f"Categoria: {categoria}"), 0, 1, 'L', fill=True)
                pdf.set_font("Arial", size=9)
                pdf.ln(2)
                perg_cat = perguntas_df[perguntas_df["Categoria"] == categoria]
                for _, p_row in perg_cat.iterrows():
                    p_texto = p_row["Pergunta"]
                    resp = respostas_coletadas.get(p_texto, diag_data.get(p_texto, "N/R"))
                    analise_texto = None
                    
                    pdf.set_font("Arial", 'B', 9)
                    pdf.multi_cell(0, 6, pdf_safe_text_output(f"  • {p_texto.split('[')[0].strip()}:"))
                    pdf.set_font("Arial", '', 9)
                    
                    if "[Matriz GUT]" in p_texto:
                        g,u,t,score=0,0,0,0
                        if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                        elif isinstance(resp, str):
                            try: data_gut=json.loads(resp.replace("'",'"'));g,u,t=int(data_gut.get("G",0)),int(data_gut.get("U",0)),int(data_gut.get("T",0))
                            except: pass
                        score = g*u*t
                        pdf.multi_cell(0,6,pdf_safe_text_output(f"    Resposta: G={g}, U={u}, T={t} (Score: {score})"), ln=1)
                        analise_texto = obter_analise_para_resposta(p_texto, score, analises_df)
                    else:
                        pdf.multi_cell(0, 6, pdf_safe_text_output(f"    Resposta: {resp}"), ln=1)
                        analise_texto = obter_analise_para_resposta(p_texto, resp, analises_df)
                    
                    if analise_texto:
                        pdf.set_font("Arial", 'I', 8); pdf.set_text_color(70,70,70) # Cinza mais escuro
                        pdf.set_fill_color(245, 245, 245) # Fundo leve para análise
                        pdf.multi_cell(0, 5, pdf_safe_text_output(f"    Análise Consultor: {analise_texto}"), border=0, ln=1, fill=True, align='J')
                        pdf.set_text_color(0,0,0); pdf.set_font("Arial", size=9)
                    pdf.ln(2) # Espaço entre perguntas
                pdf.ln(4) # Espaço entre categorias

            pdf.add_page(); pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Matriz GUT)"), 0, 1, 'C'); pdf.ln(5);  
            
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
                sorted_cards = sorted(gut_cards, key=lambda x: x["Score"], reverse=True) # Ordenar por Score descendente
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(60, 7, "Prazo Sugerido", 1, 0, 'C')
                pdf.cell(100, 7, "Tarefa Prioritária", 1, 0, 'C')
                pdf.cell(30, 7, "Score GUT", 1, 1, 'C')
                pdf.set_font("Arial", size=9)
                for card in sorted_cards:
                    pdf.cell(60, 6, pdf_safe_text_output(card['Prazo']), 1, 0)
                    pdf.multi_cell(100, 6, pdf_safe_text_output(card['Tarefa']), 1, 'L', ln=3 if pdf.get_string_width(card['Tarefa']) > 90 else 0) # Multi_cell para tarefas longas
                    if pdf.get_string_width(card['Tarefa']) <= 90: # Se não quebrou linha, precisa de ln=1 no próximo cell
                            pdf.cell(30, 6, str(card['Score']), 1, 1, 'C')
                    else: # Se quebrou, o cursor já está na próxima linha
                            current_x_after_multicell = pdf.get_x()
                            pdf.set_xy(current_x_after_multicell + 100, pdf.get_y() - 6) # Ajustar X para alinhar
                            pdf.cell(30, 6, str(card['Score']), 1, 1, 'C')


            else:  
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))
            
            # Footer
            pdf.set_y(-15)
            pdf.set_font('Arial', 'I', 8)
            pdf.cell(0, 10, f'Página {pdf.page_no()}', 0, 0, 'C')


            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                pdf_path = tmpfile.name; pdf.output(pdf_path)
        return pdf_path
    except Exception as e: st.error(f"Erro crítico ao gerar PDF: {e}"); return None

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): st.session_state.trigger_rerun_global = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v21")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

# Exibir logo do portal na tela de login
portal_logo_login_path = get_portal_logo_path()

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    if portal_logo_login_path:
        st.image(portal_logo_login_path, use_column_width='auto', output_format='PNG', width=200)
    else: # Fallback se não houver logo
        st.image("https://via.placeholder.com/200x80.png?text=Logo+do+Portal", width=200)
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
    if portal_logo_login_path:
        st.image(portal_logo_login_path, use_column_width='auto', output_format='PNG', width=200)
    else: # Fallback
        st.image("https://via.placeholder.com/200x80.png?text=Logo+do+Portal", width=200)  
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

    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
    with st.sidebar.expander("👤 Meu Perfil", expanded=True):
        logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
        if logo_cliente_path:  
            st.image(logo_cliente_path, width=100, caption=st.session_state.user.get('Empresa', ''))
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
                                                         file_name=f"diag_{sanitize_column_name(row_diag_data['Empresa'])}_{str(row_diag_data['Data']).replace(':','-').replace(' ','_')}.pdf",
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
    portal_logo_admin_path = get_portal_logo_path()
    if portal_logo_admin_path:
        st.sidebar.image(portal_logo_admin_path, use_column_width='auto')
    else:
        st.sidebar.image("https://via.placeholder.com/200x80.png?text=Logo+Admin", use_container_width=True)  

    st.sidebar.success(f"🟢 Admin Logado: {st.session_state.get('admin_username', '')} ({st.session_state.get('admin_permissions', 'N/D')})")


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
        "Gerenciar Pesquisa de Satisfação": " ",  
        "Gerenciar SAC": "📞",
        "Configurações do Portal": "⚙️", # Renomeado de "Gerenciar Instruções"
        "Histórico de Usuários": "📜",  
        "Renovação de Prazos": "⏳",
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
        
        df_usuarios_admin_geral = df_usuarios_admin_temp_load
    except FileNotFoundError:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Clientes", "Gerenciar Notificações", "Relatório de Engajamento", "Gerenciar SAC", "Gerenciar Pesquisa de Satisfação"]:
            st.sidebar.error(f"Arquivo '{usuarios_csv}' não encontrado. Funcionalidades limitadas.")
    except Exception as e_load_users_adm_global:
        if menu_admin in ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Clientes", "Gerenciar Notificações", "Relatório de Engajamento", "Gerenciar SAC", "Gerenciar Pesquisa de Satisfação"]:
            st.sidebar.error(f"Erro ao carregar usuários para admin: {e_load_users_adm_global}")


if menu_admin == "Visão Geral e Diagnósticos":
        diagnosticos_df_admin_orig_view = pd.DataFrame()
        admin_data_carregada_view_sucesso = False

        if not os.path.exists(arquivo_csv):
            st.error(f"ATENÇÃO: O arquivo de diagnósticos '{arquivo_csv}' não foi encontrado.")
        elif os.path.getsize(arquivo_csv) == 0:
            st.warning(f"O arquivo de diagnósticos '{arquivo_csv}' está completamente vazio.")
        else:
            try:
                diagnosticos_df_admin_orig_view = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                if 'Data' in diagnosticos_df_admin_orig_view.columns:
                    diagnosticos_df_admin_orig_view['Data_dt'] = pd.to_datetime(diagnosticos_df_admin_orig_view['Data'], errors='coerce')  
                    diagnosticos_df_admin_orig_view['Data'] = diagnosticos_df_admin_orig_view['Data'].astype(str)  
                if not diagnosticos_df_admin_orig_view.empty:
                    admin_data_carregada_view_sucesso = True
                else: st.info("Arquivo de diagnósticos lido, mas sem dados.")
            except pd.errors.EmptyDataError: st.warning(f"Arquivo '{arquivo_csv}' parece vazio ou só com cabeçalhos.")
            except Exception as e: st.error(f"ERRO AO CARREGAR DIAGNÓSTICOS: {e}"); st.exception(e)
        
elif menu_admin == "Renovação de Prazos":
    st.header("⏳ Renovação Rápida de Prazo dos Clientes")

    df_todos = pd.read_csv(usuarios_csv, dtype={'CNPJ': str})
    df_todos["PrazoFimAcesso"] = pd.to_datetime(df_todos["PrazoFimAcesso"], errors="coerce")
    df_todos["DiasRestantes"] = df_todos["PrazoFimAcesso"].apply(
        lambda x: (x.date() - date.today()).days if pd.notna(x) else None
    )

    for idx, row in df_todos.iterrows():
        st.markdown(f"**{row['Empresa']}** — Dias Restantes: `{row['DiasRestantes']}`")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Adicionar 5 Dias", key=f"add5_{row['CNPJ']}_{idx}"):
                renovar_dias_usuario(row['CNPJ'], 5)
                st.experimental_rerun()
        with col2:
            if st.button("❌ Bloquear Cliente", key=f"block_{row['CNPJ']}_{idx}"):
                bloquear_usuario(row['CNPJ'])
                st.experimental_rerun()
        st.markdown("#### KPIs Gerais do Sistema")
        kpi_cols_v21 = st.columns(3)  
        total_clientes_cadastrados_vg = len(df_usuarios_admin_geral) if not df_usuarios_admin_geral.empty else 0
        kpi_cols_v21[0].metric("👥 Clientes Cadastrados", total_clientes_cadastrados_vg)

        if admin_data_carregada_view_sucesso:
            total_diagnosticos_sistema_vg = len(diagnosticos_df_admin_orig_view)
            kpi_cols_v21[1].metric("📋 Diagnósticos Realizados", total_diagnosticos_sistema_vg)
            avg_geral_sistema = pd.to_numeric(diagnosticos_df_admin_orig_view.get("Média Geral"), errors='coerce').mean()
            kpi_cols_v21[2].metric("📈 Média Geral (Sistema)", f"{avg_geral_sistema:.2f}" if pd.notna(avg_geral_sistema) else "N/A")
        else:
            kpi_cols_v21[1].metric("📋 Diagnósticos Realizados", 0)
            kpi_cols_v21[2].metric("📈 Média Geral (Sistema)", "N/A")
        st.divider()

        st.markdown("#### Análises Gráficas do Sistema")
        dash_cols1_v21 = st.columns(2)  
        with dash_cols1_v21[0]:
            st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
            st.markdown("##### Diagnósticos ao Longo do Tempo")
            if admin_data_carregada_view_sucesso and 'Data_dt' in diagnosticos_df_admin_orig_view.columns:
                df_for_timeline_chart = diagnosticos_df_admin_orig_view[['Data_dt']].rename(columns={'Data_dt': 'Data'})
                fig_timeline = create_diagnostics_timeline_chart(df_for_timeline_chart)
                if fig_timeline: st.plotly_chart(fig_timeline, use_container_width=True)
                else: st.caption("Não há dados suficientes para o gráfico de linha do tempo.")
            else: st.caption("Dados de diagnóstico não carregados ou coluna 'Data' não pode ser convertida para datetime.")
            st.markdown('</div>', unsafe_allow_html=True)

        with dash_cols1_v21[1]:
            st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
            st.markdown("##### Engajamento de Clientes (Nº de Diagnósticos)")
            if not df_usuarios_admin_geral.empty:
                fig_engagement = create_client_engagement_pie(df_usuarios_admin_geral)
                if fig_engagement: st.plotly_chart(fig_engagement, use_container_width=True)
                else: st.caption("Não há dados suficientes para o gráfico de engajamento.")
            else: st.caption("Dados de usuários não carregados.")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
        st.markdown("##### Média de Scores por Categoria (Global)")
        if admin_data_carregada_view_sucesso:
            fig_avg_cat = create_avg_category_scores_chart(diagnosticos_df_admin_orig_view)
            if fig_avg_cat: st.plotly_chart(fig_avg_cat, use_container_width=True)
            else: st.caption("Não há dados de categorias para exibir.")
        else: st.caption("Dados de diagnóstico não carregados.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()

        st.markdown("#### Filtros para Análise Detalhada de Diagnósticos")
        filter_cols_v21 = st.columns(3)  

        empresas_lista_admin_filtro_vg = []
        if not df_usuarios_admin_geral.empty and "Empresa" in df_usuarios_admin_geral.columns:
            empresas_lista_admin_filtro_vg = sorted(df_usuarios_admin_geral["Empresa"].astype(str).unique().tolist())
        options_empresa_filtro = ["Todos os Clientes"] + empresas_lista_admin_filtro_vg
        
        KEY_WIDGET_EMPRESA_FILTRO_GV = "admin_filtro_emp_gv_v21_widget_sel"  
        KEY_DT_INI_FILTRO_VALUE_GV = "admin_dt_ini_gv_v21_value_sel"  
        KEY_DT_FIM_FILTRO_VALUE_GV = "admin_dt_fim_gv_v21_value_sel"  

        if KEY_WIDGET_EMPRESA_FILTRO_GV not in st.session_state or \
           st.session_state[KEY_WIDGET_EMPRESA_FILTRO_GV] not in options_empresa_filtro:
            st.session_state[KEY_WIDGET_EMPRESA_FILTRO_GV] = options_empresa_filtro[0] if options_empresa_filtro else None

        emp_sel_admin_vg = filter_cols_v21[0].selectbox(
            "Filtrar por Empresa:",
            options=options_empresa_filtro,
            key=KEY_WIDGET_EMPRESA_FILTRO_GV
        )
        
        with filter_cols_v21[1]:
            dt_ini_admin_vg = st.date_input("Data Início:",
                                             value=st.session_state.get(KEY_DT_INI_FILTRO_VALUE_GV, None),  
                                             key=KEY_DT_INI_FILTRO_VALUE_GV)
        with filter_cols_v21[2]:
            dt_fim_admin_vg = st.date_input("Data Fim:",
                                             value=st.session_state.get(KEY_DT_FIM_FILTRO_VALUE_GV, None),  
                                             key=KEY_DT_FIM_FILTRO_VALUE_GV)
        st.divider()

        df_diagnosticos_contexto_filtro_vg = diagnosticos_df_admin_orig_view.copy() if admin_data_carregada_view_sucesso else pd.DataFrame(columns=colunas_base_diagnosticos + ['Data_dt'])
        df_usuarios_contexto_filtro_vg = df_usuarios_admin_geral.copy()

        if emp_sel_admin_vg != "Todos os Clientes":
            df_diagnosticos_contexto_filtro_vg = df_diagnosticos_contexto_filtro_vg[df_diagnosticos_contexto_filtro_vg["Empresa"] == emp_sel_admin_vg]
            df_usuarios_contexto_filtro_vg = df_usuarios_contexto_filtro_vg[df_usuarios_contexto_filtro_vg["Empresa"] == emp_sel_admin_vg]

        df_diagnosticos_filtrados_view_final_vg = df_diagnosticos_contexto_filtro_vg.copy()
        if dt_ini_admin_vg and 'Data_dt' in df_diagnosticos_filtrados_view_final_vg.columns:  
            df_diagnosticos_filtrados_view_final_vg = df_diagnosticos_filtrados_view_final_vg[
                df_diagnosticos_filtrados_view_final_vg['Data_dt'] >= pd.to_datetime(dt_ini_admin_vg)
            ]
        if dt_fim_admin_vg and 'Data_dt' in df_diagnosticos_filtrados_view_final_vg.columns:
            df_diagnosticos_filtrados_view_final_vg = df_diagnosticos_filtrados_view_final_vg[
                df_diagnosticos_filtrados_view_final_vg['Data_dt'] < pd.to_datetime(dt_fim_admin_vg) + pd.Timedelta(days=1)
            ]


        st.markdown(f"#### Análise para: **{emp_sel_admin_vg}** (Período de Diagnósticos: {dt_ini_admin_vg or 'Início'} a {dt_fim_admin_vg or 'Fim'})")

        kpi_cols_filt_v21 = st.columns(3)  
        cnpjs_usuarios_contexto_final_vg = set(df_usuarios_contexto_filtro_vg['CNPJ'].unique()) if not df_usuarios_contexto_filtro_vg.empty else set()
        cnpjs_com_diagnostico_contexto_final_vg = set(df_diagnosticos_filtrados_view_final_vg['CNPJ'].unique()) if not df_diagnosticos_filtrados_view_final_vg.empty else set()

        clientes_sem_diagnostico_final_vg = len(cnpjs_usuarios_contexto_final_vg - cnpjs_com_diagnostico_contexto_final_vg)
        clientes_com_pelo_menos_um_diag_final_vg = len(cnpjs_com_diagnostico_contexto_final_vg)

        clientes_com_mais_de_um_diag_final_vg = 0
        if not df_diagnosticos_filtrados_view_final_vg.empty:
            contagem_diag_por_cliente_final_vg = df_diagnosticos_filtrados_view_final_vg.groupby('CNPJ').size()
            clientes_com_mais_de_um_diag_final_vg = len(contagem_diag_por_cliente_final_vg[contagem_diag_por_cliente_final_vg > 1])

        kpi_cols_filt_v21[0].metric("Clientes SEM Diag. (Filtro)", clientes_sem_diagnostico_final_vg)
        kpi_cols_filt_v21[1].metric("Clientes COM Diag. (Filtro)", clientes_com_pelo_menos_um_diag_final_vg)
        kpi_cols_filt_v21[2].metric("Clientes COM +1 Diag. (Filtro)", clientes_com_mais_de_um_diag_final_vg)
        st.divider()

        if not admin_data_carregada_view_sucesso and os.path.exists(arquivo_csv) and os.path.getsize(arquivo_csv) > 0 :
            st.warning("Não foi possível processar os dados de diagnósticos para os indicadores filtrados.")
        elif df_diagnosticos_filtrados_view_final_vg.empty and admin_data_carregada_view_sucesso:
            st.info(f"Nenhum diagnóstico encontrado para os filtros aplicados.")
        elif not df_diagnosticos_filtrados_view_final_vg.empty:
            st.markdown(f"##### Indicadores da Seleção Filtrada de Diagnósticos")
            kpi_cols_sel_filt_v21 = st.columns(3)  
            kpi_cols_sel_filt_v21[0].metric("📦 Diagnósticos na Seleção", len(df_diagnosticos_filtrados_view_final_vg))
            media_geral_filtrada_adm_vg = pd.to_numeric(df_diagnosticos_filtrados_view_final_vg.get("Média Geral"), errors='coerce').mean()
            kpi_cols_sel_filt_v21[1].metric("📈 Média Geral da Seleção", f"{media_geral_filtrada_adm_vg:.2f}" if pd.notna(media_geral_filtrada_adm_vg) else "N/A")
            gut_media_filtrada_adm_vg = pd.to_numeric(df_diagnosticos_filtrados_view_final_vg.get("GUT Média"), errors='coerce').mean()
            kpi_cols_sel_filt_v21[2].metric("🔥 GUT Média da Seleção", f"{gut_media_filtrada_adm_vg:.2f}" if pd.notna(gut_media_filtrada_adm_vg) else "N/A")
            st.divider()

            st.markdown(f"##### Diagnósticos Detalhados (Seleção Filtrada)")
            df_display_admin = df_diagnosticos_filtrados_view_final_vg.copy()
            if 'Data_dt' in df_display_admin.columns:
                df_display_admin = df_display_admin.sort_values(by="Data_dt", ascending=False).reset_index(drop=True)
            else:  
                df_display_admin = df_display_admin.sort_values(by="Data", ascending=False).reset_index(drop=True)


            try:
                perguntas_df_admin_view = pd.read_csv(perguntas_csv, encoding='utf-8')
                if "Categoria" not in perguntas_df_admin_view.columns: perguntas_df_admin_view["Categoria"] = "Geral"
            except FileNotFoundError: perguntas_df_admin_view = pd.DataFrame()
            analises_df_admin_view = carregar_analises_perguntas()

            for idx_diag_adm, row_diag_adm in df_display_admin.iterrows():
                diag_data_str = str(row_diag_adm['Data'])  
                with st.expander(f"🔎 {diag_data_str} - {row_diag_adm['Empresa']} (CNPJ: {row_diag_adm['CNPJ']})"):
                    st.markdown('<div class="custom-card" style="padding-top:10px; padding-bottom:10px;">', unsafe_allow_html=True)

                    m1, m2 = st.columns(2)
                    m1.metric("Média Geral", f"{pd.to_numeric(row_diag_adm.get('Média Geral'), errors='coerce'):.2f}" if pd.notna(row_diag_adm.get('Média Geral')) else "N/A")
                    m2.metric("GUT Média", f"{pd.to_numeric(row_diag_adm.get('GUT Média'), errors='coerce'):.2f}" if pd.notna(row_diag_adm.get('GUT Média')) else "N/A")

                    st.write(f"**Resumo (Cliente):** {row_diag_adm.get('Diagnóstico', 'N/P')}")
                    st.write(f"**Análise (Cliente):** {row_diag_adm.get('Análise do Cliente', 'N/P')}")

                    com_admin_atual = row_diag_adm.get("Comentarios_Admin", "")
                    com_admin_input = st.text_area("Comentários do Consultor (visível para o cliente):",
                                                     value=com_admin_atual,
                                                     key=f"com_admin_input_v21_{idx_diag_adm}_{row_diag_adm['CNPJ']}_{diag_data_str.replace(' ','_')}",
                                                     disabled=not is_admin_total())  
                    if st.button("Salvar Comentário do Consultor", icon="💬",  
                                 key=f"save_com_admin_v21_{idx_diag_adm}_{row_diag_adm['CNPJ']}_{diag_data_str.replace(' ','_')}",
                                 disabled=not is_admin_total()):  
                        if is_admin_total():
                            if com_admin_input != com_admin_atual:
                                df_all_diags_update = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ':str})
                                df_all_diags_update['Data'] = df_all_diags_update['Data'].astype(str)
                                
                                match_indices = df_all_diags_update[
                                    (df_all_diags_update["CNPJ"] == row_diag_adm["CNPJ"]) &
                                    (df_all_diags_update["Data"] == diag_data_str)  
                                ].index
                                
                                if not match_indices.empty:
                                    original_index_to_update = match_indices[0]
                                    df_all_diags_update.loc[original_index_to_update, "Comentarios_Admin"] = com_admin_input
                                    df_all_diags_update.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                    
                                    try:
                                        df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Relacionado': str})
                                        if 'Lida' not in df_notificacoes.columns: df_notificacoes['Lida'] = False
                                        if 'ID_Diagnostico_Relacionado' not in df_notificacoes.columns: df_notificacoes['ID_Diagnostico_Relacionado'] = None
                                    except (FileNotFoundError, pd.errors.EmptyDataError):
                                        df_notificacoes = pd.DataFrame(columns=colunas_base_notificacoes)

                                    nova_notificacao = pd.DataFrame([{
                                        "ID_Notificacao": str(uuid.uuid4()),
                                        "CNPJ_Cliente": row_diag_adm["CNPJ"],
                                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "Mensagem": f"O consultor adicionou um novo comentário ao seu diagnóstico de {diag_data_str}.",
                                        "Lida": False,
                                        "ID_Diagnostico_Relacionado": diag_data_str  
                                    }])
                                    df_notificacoes = pd.concat([df_notificacoes, nova_notificacao], ignore_index=True)
                                    df_notificacoes.to_csv(notificacoes_csv, index=False, encoding='utf-8')
                                    st.toast("Comentário salvo e cliente notificado!", icon="🔔")
                                    df_display_admin.loc[df_display_admin.index == idx_diag_adm, "Comentarios_Admin"] = com_admin_input
                                    st.rerun()
                                else:
                                    st.error("Erro ao encontrar diagnóstico original para salvar comentário. Verifique a consistência dos dados.")
                            else:
                                st.info("Nenhuma alteração no comentário.")

                    if st.button("Baixar PDF Detalhado", icon="📄", key=f"dl_pdf_adm_diag_v21_{idx_diag_adm}_{row_diag_adm['CNPJ']}_{diag_data_str.replace(' ','_')}"):  
                        user_data_pdf_adm = {}
                        if not df_usuarios_admin_geral.empty:
                            match_user = df_usuarios_admin_geral[df_usuarios_admin_geral['CNPJ'] == row_diag_adm['CNPJ']]
                            if not match_user.empty:
                                user_data_pdf_adm = match_user.iloc[0].to_dict()

                        medias_cat_pdf_adm = {k.replace("Media_Cat_","").replace("_"," "):v for k,v in row_diag_adm.items() if "Media_Cat_" in k and pd.notna(v)}
                        pdf_path_adm_d = gerar_pdf_diagnostico_completo(row_diag_adm.to_dict(), user_data_pdf_adm, perguntas_df_admin_view, row_diag_adm.to_dict(), medias_cat_pdf_adm, analises_df_admin_view)
                        if pdf_path_adm_d:
                            with open(pdf_path_adm_d, "rb") as f_adm_d:
                                st.download_button("Download PDF Confirmado", f_adm_d,
                                                     file_name=f"diag_{sanitize_column_name(row_diag_adm['Empresa'])}_{str(row_diag_adm['Data']).replace(':','-').replace(' ','_')}.pdf",
                                                     mime="application/pdf",
                                                     key=f"dl_confirm_adm_diag_v21_{idx_diag_adm}_{time.time()}",  
                                                     icon="📄")
                        else:
                            st.error("Erro ao gerar PDF para este diagnóstico.")
                    st.markdown('</div>', unsafe_allow_html=True)

        elif not admin_data_carregada_view_sucesso:
            st.warning("Dados de diagnósticos não puderam ser carregados. Funcionalidades limitadas.")
    
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
            c1.metric("Total de Clientes Cadastrados", total_usuarios)
            c2.metric("Não Aceitaram Instruções", len(nao_visualizaram_instrucoes_df))
            c3.metric("Aceitaram Instruções, SEM Diagnóstico", len(visualizaram_sem_diag_df))
            c4.metric("Aceitaram Instruções e COM Diagnóstico(s)", len(visualizaram_com_diag_df))
            
            st.divider()
            
            with st.expander("Detalhes: Clientes que NÃO Visualizaram/Aceitaram Instruções"):
                if not nao_visualizaram_instrucoes_df.empty:
                    st.dataframe(nao_visualizaram_instrucoes_df[["Empresa", "CNPJ", "NomeContato"]], use_container_width=True)
                else:
                    st.info("Todos os clientes visualizaram as instruções ou não há clientes nesta categoria.")

            with st.expander("Detalhes: Clientes que Aceitaram Instruções, mas NÃO Fizeram Diagnóstico"):
                if not visualizaram_sem_diag_df.empty:
                    st.dataframe(visualizaram_sem_diag_df[["Empresa", "CNPJ", "NomeContato", "DiagnosticosDisponiveis"]], use_container_width=True)
                else:
                    st.info("Todos os clientes que visualizaram as instruções fizeram ao menos um diagnóstico ou não há clientes nesta categoria.")

            with st.expander("Detalhes: Clientes que Aceitaram Instruções e FIZERAM Diagnóstico(s)"):
                if not visualizaram_com_diag_df.empty:
                    st.dataframe(visualizaram_com_diag_df[["Empresa", "CNPJ", "NomeContato", "TotalDiagnosticosRealizados", "DiagnosticosDisponiveis"]], use_container_width=True)
                else:
                    st.info("Nenhum cliente visualizou as instruções e completou um diagnóstico ainda.")

elif menu_admin == "Gerenciar Notificações":
        st.markdown("#### Lista de Todas as Notificações do Sistema")
        try:
            df_notificacoes_admin = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Relacionado': str})
            if 'Lida' in df_notificacoes_admin.columns:
                df_notificacoes_admin['Lida'] = df_notificacoes_admin['Lida'].astype(str).str.lower().map({'true': True, 'false': False, 'nan': False, '': False}).fillna(False)
            else:
                df_notificacoes_admin['Lida'] = False  
            if 'ID_Diagnostico_Relacionado' not in df_notificacoes_admin.columns:
                df_notificacoes_admin['ID_Diagnostico_Relacionado'] = None


            if not df_usuarios_admin_geral.empty:
                df_notificacoes_admin = pd.merge(df_notificacoes_admin, df_usuarios_admin_geral[['CNPJ', 'Empresa']],  
                                                 left_on='CNPJ_Cliente', right_on='CNPJ', how='left')
                df_notificacoes_admin.drop(columns=['CNPJ'], inplace=True, errors='ignore')  
                df_notificacoes_admin.rename(columns={'Empresa': 'Empresa Cliente'}, inplace=True)
                df_notificacoes_admin['Empresa Cliente'] = df_notificacoes_admin['Empresa Cliente'].fillna("N/D (Usuário não encontrado)")

            else:
                df_notificacoes_admin['Empresa Cliente'] = "N/D (Dados de usuários não carregados)"


        except (FileNotFoundError, pd.errors.EmptyDataError):
            st.info("Nenhuma notificação encontrada.")
            df_notificacoes_admin = pd.DataFrame(columns=colunas_base_notificacoes + ['Empresa Cliente'])
        except Exception as e_notif_admin:
            st.error(f"Erro ao carregar notificações para admin: {e_notif_admin}")
            df_notificacoes_admin = pd.DataFrame(columns=colunas_base_notificacoes + ['Empresa Cliente'])

        st.sidebar.markdown("---")  
        st.sidebar.subheader("Filtros de Notificações")
        
        clientes_notif_list = ["Todos"]
        if "Empresa Cliente" in df_notificacoes_admin.columns:
            clientes_notif_list.extend(sorted(df_notificacoes_admin["Empresa Cliente"].astype(str).unique().tolist()))
        
        sel_cliente_notif = st.sidebar.selectbox("Filtrar por Cliente:", clientes_notif_list, key="admin_notif_cliente_filter_v21")  
        sel_lida_notif = st.sidebar.selectbox("Filtrar por Status:", ["Todas", "Lidas", "Não Lidas"], key="admin_notif_lida_filter_v21")
        
        dt_ini_notif = st.sidebar.date_input("Data Início Notificação:", None, key="admin_notif_dt_ini_v21")
        dt_fim_notif = st.sidebar.date_input("Data Fim Notificação:", None, key="admin_notif_dt_fim_v21")

        df_notificacoes_filtradas_admin = df_notificacoes_admin.copy()

        if sel_cliente_notif != "Todos" and "Empresa Cliente" in df_notificacoes_filtradas_admin.columns:
            df_notificacoes_filtradas_admin = df_notificacoes_filtradas_admin[df_notificacoes_filtradas_admin["Empresa Cliente"] == sel_cliente_notif]
        
        if sel_lida_notif == "Lidas" and "Lida" in df_notificacoes_filtradas_admin.columns:
            df_notificacoes_filtradas_admin = df_notificacoes_filtradas_admin[df_notificacoes_filtradas_admin["Lida"] == True]
        elif sel_lida_notif == "Não Lidas" and "Lida" in df_notificacoes_filtradas_admin.columns:
            df_notificacoes_filtradas_admin = df_notificacoes_filtradas_admin[df_notificacoes_filtradas_admin["Lida"] == False]

        if dt_ini_notif and 'Timestamp' in df_notificacoes_filtradas_admin.columns:
            try:
                df_notificacoes_filtradas_admin['Timestamp_dt'] = pd.to_datetime(df_notificacoes_filtradas_admin['Timestamp'])
                df_notificacoes_filtradas_admin = df_notificacoes_filtradas_admin[df_notificacoes_filtradas_admin['Timestamp_dt'] >= pd.to_datetime(dt_ini_notif)]
            except Exception as e_date_filter:
                st.warning(f"Não foi possível aplicar filtro de data inicial: {e_date_filter}")

        
        if dt_fim_notif and 'Timestamp' in df_notificacoes_filtradas_admin.columns:
            try:
                if 'Timestamp_dt' not in df_notificacoes_filtradas_admin.columns:
                    df_notificacoes_filtradas_admin['Timestamp_dt'] = pd.to_datetime(df_notificacoes_filtradas_admin['Timestamp'])
                df_notificacoes_filtradas_admin = df_notificacoes_filtradas_admin[df_notificacoes_filtradas_admin['Timestamp_dt'] < pd.to_datetime(dt_fim_notif) + pd.Timedelta(days=1)]
            except Exception as e_date_filter:
                st.warning(f"Não foi possível aplicar filtro de data final: {e_date_filter}")

        if 'Timestamp_dt' in df_notificacoes_filtradas_admin.columns:
            df_notificacoes_filtradas_admin = df_notificacoes_filtradas_admin.drop(columns=['Timestamp_dt'])


        if not df_notificacoes_filtradas_admin.empty:
            cols_to_show = ["Timestamp", "Empresa Cliente", "CNPJ_Cliente", "Mensagem", "Lida", "ID_Diagnostico_Relacionado", "ID_Notificacao"]
            final_cols_to_show = [col for col in cols_to_show if col in df_notificacoes_filtradas_admin.columns]
            
            st.dataframe(df_notificacoes_filtradas_admin[final_cols_to_show].sort_values(by="Timestamp", ascending=False), use_container_width=True)
        else:
            st.info("Nenhuma notificação encontrada para os filtros aplicados.")

elif menu_admin == "Gerenciar Pesquisa de Satisfação":  
        st.markdown("#### Gerenciamento da Pesquisa de Satisfação")
        df_satisfacao_perguntas_admin = carregar_satisfacao_perguntas().copy()
        df_satisfacao_respostas_admin = carregar_satisfacao_respostas().copy()

        admin_satisfacao_tabs = st.tabs(["📝 Gerenciar Perguntas da Pesquisa", "📊 Resultados da Pesquisa"])

        with admin_satisfacao_tabs[0]:  
            st.subheader("Adicionar Nova Pergunta de Satisfação")
            with st.form("form_nova_pergunta_satisfacao_v21", clear_on_submit=True):
                nova_pergunta_sat_texto = st.text_input("Texto da Pergunta:", key="nova_p_sat_texto_v21", disabled=not is_admin_total())
                
                tipos_pergunta_sat_opts = {
                    "Pontuação (0-5)": "Pontuacao_0_5",
                    "Pontuação (0-10)": "Pontuacao_0_10",
                    "Texto Aberto": "Texto_Aberto",
                    "Escolha Única (Likert, etc.)": "Escolha_Unica"
                }
                tipo_pergunta_sat_display = st.selectbox("Tipo da Pergunta:", list(tipos_pergunta_sat_opts.keys()), key="nova_p_sat_tipo_v21", disabled=not is_admin_total())
                tipo_pergunta_sat_valor = tipos_pergunta_sat_opts[tipo_pergunta_sat_display]

                opcoes_pergunta_sat_str = ""
                if tipo_pergunta_sat_valor == "Escolha_Unica":
                    opcoes_pergunta_sat_str = st.text_input("Opções (separadas por vírgula, ex: Ruim,Regular,Bom):", key="nova_p_sat_opcoes_v21", disabled=not is_admin_total())
                
                ordem_pergunta_sat = st.number_input("Ordem de Exibição:", min_value=0, step=1, value=len(df_satisfacao_perguntas_admin), key="nova_p_sat_ordem_v21", disabled=not is_admin_total())
                ativa_pergunta_sat = st.checkbox("Pergunta Ativa?", value=True, key="nova_p_sat_ativa_v21", disabled=not is_admin_total())

                submitted_nova_sat_p = st.form_submit_button("Adicionar Pergunta de Satisfação", icon="➕", disabled=not is_admin_total())
                if submitted_nova_sat_p and is_admin_total():
                    if nova_pergunta_sat_texto.strip():
                        opcoes_json_sat = None
                        if tipo_pergunta_sat_valor == "Escolha_Unica" and opcoes_pergunta_sat_str.strip():
                            opcoes_list = [opt.strip() for opt in opcoes_pergunta_sat_str.split(',')]
                            if opcoes_list:
                                opcoes_json_sat = json.dumps(opcoes_list)
                            else:
                                st.warning("Para 'Escolha Única', as opções são obrigatórias.")
                                st.stop()
                        elif tipo_pergunta_sat_valor == "Escolha_Unica" and not opcoes_pergunta_sat_str.strip():
                               st.warning("Para 'Escolha Única', as opções são obrigatórias.")
                               st.stop()


                        nova_id_sat_p = str(uuid.uuid4())
                        nova_entrada_sat_p = pd.DataFrame([{
                            "ID_Pergunta_Satisfacao": nova_id_sat_p,
                            "Texto_Pergunta": nova_pergunta_sat_texto.strip(),
                            "Tipo_Pergunta": tipo_pergunta_sat_valor,
                            "Opcoes_Pergunta": opcoes_json_sat,
                            "Ordem": int(ordem_pergunta_sat),
                            "Ativa": bool(ativa_pergunta_sat)
                        }])
                        df_satisfacao_perguntas_admin = pd.concat([df_satisfacao_perguntas_admin, nova_entrada_sat_p], ignore_index=True)
                        df_satisfacao_perguntas_admin.to_csv(satisfacao_perguntas_csv, index=False, encoding='utf-8')
                        st.cache_data.clear()  
                        st.toast("Pergunta de satisfação adicionada!", icon="🎉")
                        st.rerun()
                    else:
                        st.warning("O texto da pergunta é obrigatório.")
            
            st.divider()
            st.subheader("Perguntas de Satisfação Cadastradas")
            if df_satisfacao_perguntas_admin.empty:
                st.info("Nenhuma pergunta de satisfação cadastrada.")
            else:
                for i_sat_p, row_sat_p_item in df_satisfacao_perguntas_admin.sort_values(by="Ordem").iterrows():
                    st.markdown(f"""
                    <div class="custom-card" style="margin-bottom: 10px; border-left-color: {'#10b981' if row_sat_p_item['Ativa'] else '#f59e0b'};">
                        <small><i>ID: {row_sat_p_item['ID_Pergunta_Satisfacao']} | Ordem: {row_sat_p_item['Ordem']} | Ativa: {'Sim' if row_sat_p_item['Ativa'] else 'Não'}</i></small>
                        <h5>{row_sat_p_item['Texto_Pergunta']} (Tipo: {row_sat_p_item['Tipo_Pergunta']})</h5>
                        {f"<p>Opções: {row_sat_p_item['Opcoes_Pergunta']}</p>" if pd.notna(row_sat_p_item['Opcoes_Pergunta']) else ""}
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("✏️ Editar / 🗑️ Deletar esta Pergunta de Satisfação"):
                        form_key_edit_sat_p = f"form_edit_sat_p_v21_{row_sat_p_item['ID_Pergunta_Satisfacao']}"
                        with st.form(form_key_edit_sat_p):
                            edited_texto_sat_p = st.text_input("Editar Texto:", value=row_sat_p_item['Texto_Pergunta'], key=f"edit_texto_{form_key_edit_sat_p}", disabled=not is_admin_total())
                            
                            current_type_val_edit = row_sat_p_item['Tipo_Pergunta']
                            current_type_display_edit = next((k for k, v in tipos_pergunta_sat_opts.items() if v == current_type_val_edit), list(tipos_pergunta_sat_opts.keys())[0])
                            
                            edited_tipo_display_sat_p = st.selectbox("Editar Tipo:", list(tipos_pergunta_sat_opts.keys()),  
                                                                     index=list(tipos_pergunta_sat_opts.keys()).index(current_type_display_edit),  
                                                                     key=f"edit_tipo_{form_key_edit_sat_p}", disabled=not is_admin_total())
                            edited_tipo_valor_sat_p = tipos_pergunta_sat_opts[edited_tipo_display_sat_p]

                            edited_opcoes_str_sat_p = row_sat_p_item.get('Opcoes_Pergunta', "")
                            if pd.notna(edited_opcoes_str_sat_p) and isinstance(edited_opcoes_str_sat_p, str):
                                try:
                                    edited_opcoes_list = json.loads(edited_opcoes_str_sat_p)
                                    edited_opcoes_str_sat_p = ",".join(edited_opcoes_list)
                                except:  
                                    edited_opcoes_str_sat_p = "" if not isinstance(edited_opcoes_str_sat_p, str) else edited_opcoes_str_sat_p


                            if edited_tipo_valor_sat_p == "Escolha_Unica":
                                edited_opcoes_str_sat_p = st.text_input("Editar Opções (separadas por vírgula):", value=edited_opcoes_str_sat_p, key=f"edit_opcoes_{form_key_edit_sat_p}", disabled=not is_admin_total())
                            
                            edited_ordem_sat_p = st.number_input("Editar Ordem:", value=int(row_sat_p_item['Ordem']), min_value=0, step=1, key=f"edit_ordem_{form_key_edit_sat_p}", disabled=not is_admin_total())
                            edited_ativa_sat_p = st.checkbox("Ativa?", value=bool(row_sat_p_item['Ativa']), key=f"edit_ativa_{form_key_edit_sat_p}", disabled=not is_admin_total())

                            col_btn_sat_p1, col_btn_sat_p2 = st.columns(2)
                            if col_btn_sat_p1.form_submit_button("Salvar Alterações", icon="💾", use_container_width=True, disabled=not is_admin_total()):
                                if is_admin_total():
                                    df_satisfacao_perguntas_admin.loc[i_sat_p, "Texto_Pergunta"] = edited_texto_sat_p
                                    df_satisfacao_perguntas_admin.loc[i_sat_p, "Tipo_Pergunta"] = edited_tipo_valor_sat_p
                                    if edited_tipo_valor_sat_p == "Escolha_Unica" and edited_opcoes_str_sat_p.strip():
                                        df_satisfacao_perguntas_admin.loc[i_sat_p, "Opcoes_Pergunta"] = json.dumps([opt.strip() for opt in edited_opcoes_str_sat_p.split(',')])
                                    elif edited_tipo_valor_sat_p != "Escolha_Unica":
                                         df_satisfacao_perguntas_admin.loc[i_sat_p, "Opcoes_Pergunta"] = None  
                                    elif edited_tipo_valor_sat_p == "Escolha_Unica" and not edited_opcoes_str_sat_p.strip():
                                         st.warning("Opções são obrigatórias para tipo 'Escolha Única'. Não foram salvas.")


                                    df_satisfacao_perguntas_admin.loc[i_sat_p, "Ordem"] = int(edited_ordem_sat_p)
                                    df_satisfacao_perguntas_admin.loc[i_sat_p, "Ativa"] = bool(edited_ativa_sat_p)
                                    df_satisfacao_perguntas_admin.to_csv(satisfacao_perguntas_csv, index=False, encoding='utf-8')
                                    st.cache_data.clear()
                                    st.toast("Alterações na pergunta de satisfação salvas!", icon="✅")
                                    st.rerun()

                            if col_btn_sat_p2.form_submit_button("Deletar Pergunta", icon="🗑️", type="primary", use_container_width=True, disabled=not is_admin_total()):
                                if is_admin_total():
                                    df_satisfacao_perguntas_admin = df_satisfacao_perguntas_admin.drop(index=i_sat_p)
                                    df_satisfacao_perguntas_admin.to_csv(satisfacao_perguntas_csv, index=False, encoding='utf-8')
                                    st.cache_data.clear()
                                    st.toast("Pergunta de satisfação deletada!", icon="🗑️")
                                    st.rerun()
                    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)


        with admin_satisfacao_tabs[1]:  
            st.subheader("Resultados da Pesquisa de Satisfação")
            if df_satisfacao_respostas_admin.empty:
                st.info("Nenhuma resposta de satisfação registrada ainda.")
            else:
                df_respostas_display = df_satisfacao_respostas_admin.copy()
                if not df_usuarios_admin_geral.empty:
                    df_respostas_display = pd.merge(df_respostas_display, df_usuarios_admin_geral[['CNPJ', 'Empresa']],  
                                                     left_on='CNPJ_Cliente', right_on='CNPJ', how='left')
                    df_respostas_display.rename(columns={'Empresa': 'Empresa_Cliente_Nome'}, inplace=True)
                    df_respostas_display['Empresa_Cliente_Nome'] = df_respostas_display['Empresa_Cliente_Nome'].fillna("N/D")
                    df_respostas_display.drop(columns=['CNPJ'], inplace=True, errors='ignore')
                else:
                    df_respostas_display['Empresa_Cliente_Nome'] = "N/D"

                if not df_satisfacao_perguntas_admin.empty:
                    df_respostas_display = pd.merge(df_respostas_display, df_satisfacao_perguntas_admin[['ID_Pergunta_Satisfacao', 'Texto_Pergunta', 'Tipo_Pergunta']],
                                                     on='ID_Pergunta_Satisfacao', how='left')
                    df_respostas_display['Texto_Pergunta'] = df_respostas_display['Texto_Pergunta'].fillna("Pergunta Excluída/Desconhecida")
                    df_respostas_display['Tipo_Pergunta'] = df_respostas_display['Tipo_Pergunta'].fillna("N/D")
                else:
                    df_respostas_display['Texto_Pergunta'] = "N/D"
                    df_respostas_display['Tipo_Pergunta'] = "N/D"


                st.markdown("##### Filtros de Resultados")
                col_f1, col_f2, col_f3 = st.columns(3)
                
                perguntas_filtro_opts = ["Todas"] + sorted(df_respostas_display['Texto_Pergunta'].unique().tolist())
                pergunta_sel_filtro = col_f1.selectbox("Filtrar por Pergunta:", perguntas_filtro_opts, key="filtro_sat_pergunta_v21")
                
                clientes_filtro_opts = ["Todos"] + sorted(df_respostas_display['Empresa_Cliente_Nome'].unique().tolist())
                cliente_sel_filtro = col_f2.selectbox("Filtrar por Cliente:", clientes_filtro_opts, key="filtro_sat_cliente_v21")

                dt_ini_sat_resp = col_f3.date_input("Data Início Resposta:", None, key="filtro_sat_dt_ini_v21")
                dt_fim_sat_resp = col_f3.date_input("Data Fim Resposta:", None, key="filtro_sat_dt_fim_v21")

                df_respostas_filtrado = df_respostas_display.copy()
                if pergunta_sel_filtro != "Todas":
                    df_respostas_filtrado = df_respostas_filtrado[df_respostas_filtrado['Texto_Pergunta'] == pergunta_sel_filtro]
                if cliente_sel_filtro != "Todos":
                    df_respostas_filtrado = df_respostas_filtrado[df_respostas_filtrado['Empresa_Cliente_Nome'] == cliente_sel_filtro]
                if dt_ini_sat_resp:
                    df_respostas_filtrado = df_respostas_filtrado[df_respostas_filtrado['Timestamp_Resposta'] >= pd.to_datetime(dt_ini_sat_resp)]
                if dt_fim_sat_resp:
                    df_respostas_filtrado = df_respostas_filtrado[df_respostas_filtrado['Timestamp_Resposta'] < pd.to_datetime(dt_fim_sat_resp) + pd.Timedelta(days=1)]

                if df_respostas_filtrado.empty:
                    st.info("Nenhuma resposta encontrada para os filtros aplicados.")
                else:
                    st.markdown("##### Visualização dos Resultados Filtrados")
                    
                    if pergunta_sel_filtro != "Todas" and not df_respostas_filtrado.empty:
                        tipo_pergunta_selecionada = df_respostas_filtrado['Tipo_Pergunta'].iloc[0]
                        if tipo_pergunta_selecionada in ["Pontuacao_0_5", "Pontuacao_0_10"]:
                            avg_score = df_respostas_filtrado['Resposta_Numerica'].mean()
                            st.metric(f"Média de Score para '{pergunta_sel_filtro}'", f"{avg_score:.2f}" if pd.notna(avg_score) else "N/A")
                            fig_score_dist = create_satisfaction_score_distribution_chart(df_respostas_filtrado, pergunta_sel_filtro)
                            if fig_score_dist: st.plotly_chart(fig_score_dist, use_container_width=True)
                        elif tipo_pergunta_selecionada == "Escolha_Unica":
                            fig_choice_dist = create_satisfaction_choice_distribution_chart(df_respostas_filtrado, pergunta_sel_filtro)
                            if fig_choice_dist: st.plotly_chart(fig_choice_dist, use_container_width=True)
                        elif tipo_pergunta_selecionada == "Texto_Aberto":
                            st.markdown(f"**Respostas de Texto para '{pergunta_sel_filtro}':**")
                            for resp_texto in df_respostas_filtrado['Resposta_Texto'].dropna():
                                st.markdown(f"- {resp_texto}")
                    
                    cols_view_respostas = ['Timestamp_Resposta', 'Empresa_Cliente_Nome', 'CNPJ_Cliente', 'Texto_Pergunta',  
                                            'Resposta_Texto', 'Resposta_Numerica', 'Resposta_Opcao_Selecionada']
                    st.dataframe(df_respostas_filtrado[cols_view_respostas].sort_values(by="Timestamp_Resposta", ascending=False), use_container_width=True)


elif menu_admin == "Gerenciar Perguntas (Diagnóstico)":  
        tabs_perg_admin = st.tabs(["📋 Perguntas Atuais", "➕ Adicionar Nova Pergunta"])
        try:
            perguntas_df_admin_gp = pd.read_csv(perguntas_csv, encoding='utf-8')
            if "Categoria" not in perguntas_df_admin_gp.columns: perguntas_df_admin_gp["Categoria"] = "Geral"
        except (FileNotFoundError, pd.errors.EmptyDataError):
            perguntas_df_admin_gp = pd.DataFrame(columns=colunas_base_perguntas)

        with tabs_perg_admin[0]:
            if perguntas_df_admin_gp.empty: st.info("Nenhuma pergunta cadastrada.")
            else:
                for i_p_admin, row_p_admin in perguntas_df_admin_gp.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div class="custom-card" style="margin-bottom: 15px;">
                            <p style="font-size: 0.8em; color: #6b7280; margin-bottom: 5px;">ID: {i_p_admin} | Categoria: <b>{row_p_admin.get("Categoria", "Geral")}</b></p>
                            <p style="font-weight: 500;">{row_p_admin["Pergunta"]}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        with st.expander("✏️ Editar Pergunta"):
                            cols_edit_perg = st.columns([3, 2])
                            novo_p_text_admin = cols_edit_perg[0].text_area("Texto da Pergunta:", value=str(row_p_admin["Pergunta"]), key=f"edit_p_txt_v21_gp_{i_p_admin}", height=100, disabled=not is_admin_total())
                            nova_cat_text_admin = cols_edit_perg[1].text_input("Categoria:", value=str(row_p_admin.get("Categoria", "Geral")), key=f"edit_p_cat_v21_gp_{i_p_admin}", disabled=not is_admin_total())

                            col_btn1, col_btn2 = st.columns([0.15, 0.85])
                            if col_btn1.button("Salvar", key=f"salvar_p_adm_v21_gp_{i_p_admin}", help="Salvar Alterações", icon="💾", disabled=not is_admin_total()):
                                if is_admin_total():
                                    perguntas_df_admin_gp.loc[i_p_admin, "Pergunta"] = novo_p_text_admin
                                    perguntas_df_admin_gp.loc[i_p_admin, "Categoria"] = nova_cat_text_admin
                                    perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                    st.toast(f"Pergunta {i_p_admin} atualizada.", icon="✅"); st.rerun()

                            if col_btn2.button("Deletar", type="primary", key=f"deletar_p_adm_v21_gp_{i_p_admin}", help="Deletar Pergunta", icon="🗑️", disabled=not is_admin_total()):
                                if is_admin_total():
                                    perguntas_df_admin_gp = perguntas_df_admin_gp.drop(i_p_admin).reset_index(drop=True)
                                    perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                    st.toast(f"Pergunta {i_p_admin} removida.", icon="🗑️"); st.rerun()
                    st.divider()
        with tabs_perg_admin[1]:
            with st.form("form_nova_pergunta_admin_v21_gp"):
                st.subheader("➕ Adicionar Nova Pergunta (Diagnóstico)")
                nova_p_form_txt_admin = st.text_input("Texto da Pergunta", key="nova_p_input_admin_txt_v21_gp", disabled=not is_admin_total())
                cat_existentes_gp = sorted(list(perguntas_df_admin_gp['Categoria'].astype(str).unique())) if not perguntas_df_admin_gp.empty else []
                cat_options_gp = ["Nova Categoria"] + cat_existentes_gp
                cat_selecionada_gp = st.selectbox("Categoria:", cat_options_gp, key="cat_select_admin_new_q_v21_gp", disabled=not is_admin_total())
                nova_cat_form_admin_gp = st.text_input("Nome da Nova Categoria:", key="nova_cat_input_admin_new_q_v21_gp", disabled=not is_admin_total()) if cat_selecionada_gp == "Nova Categoria" else cat_selecionada_gp

                tipo_p_form_admin = st.selectbox("Tipo de Pergunta (será adicionado ao final do texto da pergunta):",
                                                 ["Pontuação (0-10)", "Pontuação (0-5)", "Texto Aberto", "Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)", "[Matriz GUT]"],
                                                 key="tipo_p_select_admin_new_q_v21_gp", disabled=not is_admin_total())
                add_p_btn_admin = st.form_submit_button("Adicionar Pergunta", icon="➕", use_container_width=True, disabled=not is_admin_total())
                if add_p_btn_admin and is_admin_total():
                    if nova_p_form_txt_admin.strip() and nova_cat_form_admin_gp.strip():
                        p_completa_add_admin = f"{nova_p_form_txt_admin.strip()} [{tipo_p_form_admin.replace('[','').replace(']','')}]"
                        nova_entrada_p_add_admin = pd.DataFrame([[p_completa_add_admin, nova_cat_form_admin_gp.strip()]], columns=["Pergunta", "Categoria"])
                        perguntas_df_admin_gp = pd.concat([perguntas_df_admin_gp, nova_entrada_p_add_admin], ignore_index=True)
                        perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                        st.toast(f"Pergunta adicionada!", icon="🎉"); st.rerun()
                    else: st.warning("Texto da pergunta e categoria são obrigatórios.")


elif menu_admin == "Gerenciar Análises de Perguntas":
        df_analises_existentes_admin = carregar_analises_perguntas()
        try: df_perguntas_formulario_admin = pd.read_csv(perguntas_csv, encoding='utf-8')
        except: df_perguntas_formulario_admin = pd.DataFrame(columns=colunas_base_perguntas)

        st.markdown("#### Adicionar Nova Análise")
        if df_perguntas_formulario_admin.empty:
            st.warning("Nenhuma pergunta cadastrada no formulário. Adicione perguntas primeiro em 'Gerenciar Perguntas (Diagnóstico)'.")
        else:
            lista_perguntas_txt_admin = [""] + df_perguntas_formulario_admin["Pergunta"].unique().tolist()
            pergunta_selecionada_analise_admin = st.selectbox("Selecione a Pergunta para adicionar análise:", lista_perguntas_txt_admin, key="sel_perg_analise_v21_ga", disabled=not is_admin_total())

            if pergunta_selecionada_analise_admin:
                st.caption(f"Pergunta selecionada: {pergunta_selecionada_analise_admin}")

                tipo_condicao_analise_display_admin = st.selectbox("Tipo de Condição para a Análise:",
                                                                    ["Faixa Numérica (p/ Pontuação 0-X)",
                                                                     "Valor Exato (p/ Escala)",
                                                                     "Faixa de Score (p/ Matriz GUT)",
                                                                     "Análise Padrão (default para a pergunta)"],
                                                                     key="tipo_cond_analise_v21_ga", disabled=not is_admin_total())

                map_tipo_cond_to_csv_admin = {
                    "Faixa Numérica (p/ Pontuação 0-X)": "FaixaNumerica",
                    "Valor Exato (p/ Escala)": "ValorExatoEscala",
                    "Faixa de Score (p/ Matriz GUT)": "ScoreGUT",
                    "Análise Padrão (default para a pergunta)": "Default"
                }
                tipo_condicao_csv_val_admin = map_tipo_cond_to_csv_admin[tipo_condicao_analise_display_admin]

                cond_val_min_ui_admin, cond_val_max_ui_admin, cond_val_exato_ui_admin = None, None, None
                if tipo_condicao_csv_val_admin == "FaixaNumerica":
                    cols_faixa_ui_admin = st.columns(2)
                    cond_val_min_ui_admin = cols_faixa_ui_admin[0].number_input("Valor Mínimo da Faixa", step=1.0, format="%.2f", key="cond_min_analise_v21_ga", disabled=not is_admin_total())
                    cond_val_max_ui_admin = cols_faixa_ui_admin[1].number_input("Valor Máximo da Faixa", step=1.0, format="%.2f", key="cond_max_analise_v21_ga", disabled=not is_admin_total())
                elif tipo_condicao_csv_val_admin == "ValorExatoEscala":
                    cond_val_exato_ui_admin = st.text_input("Valor Exato da Escala (ex: Baixo, Médio, Alto)", key="cond_exato_analise_v21_ga", disabled=not is_admin_total())
                elif tipo_condicao_csv_val_admin == "ScoreGUT":
                    cols_faixa_gut_ui_admin = st.columns(2)
                    cond_val_min_ui_admin = cols_faixa_gut_ui_admin[0].number_input("Score GUT Mínimo", step=1, key="cond_min_gut_analise_v21_ga", disabled=not is_admin_total())
                    cond_val_max_ui_admin = cols_faixa_gut_ui_admin[1].number_input("Score GUT Máximo (opcional, deixe 0 ou vazio se for 'acima de Mínimo')", value=0.0, step=1.0, format="%.0f", key="cond_max_gut_analise_v21_ga", disabled=not is_admin_total())

                texto_analise_nova_ui_admin = st.text_area("Texto da Análise:", height=150, key="txt_analise_nova_v21_ga", disabled=not is_admin_total())

                if st.button("Salvar Nova Análise", key="salvar_analise_pergunta_v21_ga", icon="💾", use_container_width=True, disabled=not is_admin_total()):
                    if is_admin_total():
                        if texto_analise_nova_ui_admin.strip():
                            nova_id_analise_admin = str(uuid.uuid4())
                            nova_entrada_analise_admin = {
                                "ID_Analise": nova_id_analise_admin,
                                "TextoPerguntaOriginal": pergunta_selecionada_analise_admin,
                                "TipoCondicao": tipo_condicao_csv_val_admin,
                                "CondicaoValorMin": cond_val_min_ui_admin if cond_val_min_ui_admin is not None else pd.NA,
                                "CondicaoValorMax": cond_val_max_ui_admin if cond_val_max_ui_admin is not None and cond_val_max_ui_admin !=0 else pd.NA,
                                "CondicaoValorExato": cond_val_exato_ui_admin if cond_val_exato_ui_admin else pd.NA,
                                "TextoAnalise": texto_analise_nova_ui_admin
                            }
                            df_analises_existentes_admin = pd.concat([df_analises_existentes_admin, pd.DataFrame([nova_entrada_analise_admin])], ignore_index=True)
                            df_analises_existentes_admin.to_csv(analises_perguntas_csv, index=False, encoding='utf-8')
                            st.cache_data.clear()  
                            st.toast("Nova análise salva!", icon="🎉"); st.rerun()
                        else: st.error("O texto da análise não pode estar vazio.")

        st.markdown("---"); st.subheader("📜 Análises Cadastradas")
        if df_analises_existentes_admin.empty: st.info("Nenhuma análise cadastrada.")
        else:
            df_display_analises = df_analises_existentes_admin.copy()
            for col_num_format in ['CondicaoValorMin', 'CondicaoValorMax']:
                if col_num_format in df_display_analises.columns:
                    df_display_analises[col_num_format] = pd.to_numeric(df_display_analises[col_num_format], errors='coerce').fillna("")  
            st.dataframe(df_display_analises, use_container_width=True)

            analise_del_id_admin = st.selectbox("Deletar Análise por ID:", [""] + df_analises_existentes_admin["ID_Analise"].astype(str).tolist(), key="del_analise_id_v21_ga", disabled=not is_admin_total())
            if st.button("Deletar Análise Selecionada", key="btn_del_analise_v21_ga", icon="🗑️", type="primary", disabled=not is_admin_total()):
                if is_admin_total():
                    if analise_del_id_admin:
                        df_analises_existentes_admin = df_analises_existentes_admin[df_analises_existentes_admin["ID_Analise"] != analise_del_id_admin]
                        df_analises_existentes_admin.to_csv(analises_perguntas_csv, index=False, encoding='utf-8')
                        st.cache_data.clear()  
                        st.toast("Análise deletada.", icon="🗑️"); st.rerun()
                    else:
                        st.warning("Selecione uma análise para deletar.")
    
elif menu_admin == "Gerenciar SAC":
        st.markdown("#### Gerenciamento do SAC - Perguntas e Respostas")
        df_sac_qa_admin = carregar_sac_perguntas_respostas().copy()  
        df_sac_uso_admin = carregar_sac_uso_feedback().copy()

        sac_admin_tabs = st.tabs(["📝 Gerenciar Perguntas e Respostas SAC", "📊 Relatório de Uso e Feedback SAC"])

        with sac_admin_tabs[0]:
            st.subheader("Adicionar Nova Pergunta ao SAC")
            with st.form("form_nova_pergunta_sac_v21", clear_on_submit=True):  
                nova_pergunta_sac_txt = st.text_input("Texto da Pergunta SAC:", key="nova_p_sac_txt_v21", disabled=not is_admin_total())
                nova_resposta_sac_txt = st.text_area("Texto da Resposta SAC:", key="nova_r_sac_txt_v21", height=150, disabled=not is_admin_total())
                
                cat_existentes_sac_admin = sorted(list(df_sac_qa_admin['Categoria_SAC'].astype(str).unique())) if not df_sac_qa_admin.empty else []
                cat_options_sac_admin = ["Nova Categoria"] + cat_existentes_sac_admin
                cat_selecionada_sac_admin = st.selectbox("Categoria da Pergunta SAC:", cat_options_sac_admin, key="cat_select_admin_new_sac_v21", disabled=not is_admin_total())
                nova_cat_sac_form_admin = st.text_input("Nome da Nova Categoria SAC:", key="nova_cat_input_admin_new_sac_v21", disabled=not is_admin_total()) if cat_selecionada_sac_admin == "Nova Categoria" else cat_selecionada_sac_admin

                submitted_nova_sac_qa = st.form_submit_button("Adicionar ao SAC", icon="➕", disabled=not is_admin_total())
                if submitted_nova_sac_qa and is_admin_total():
                    if nova_pergunta_sac_txt.strip() and nova_resposta_sac_txt.strip() and nova_cat_sac_form_admin.strip():
                        nova_id_sac_p = str(uuid.uuid4())
                        nova_entrada_sac = pd.DataFrame([{
                            "ID_SAC_Pergunta": nova_id_sac_p,
                            "Pergunta_SAC": nova_pergunta_sac_txt.strip(),
                            "Resposta_SAC": nova_resposta_sac_txt.strip(),
                            "Categoria_SAC": nova_cat_sac_form_admin.strip(),
                            "DataCriacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }])
                        df_sac_qa_admin = pd.concat([df_sac_qa_admin, nova_entrada_sac], ignore_index=True)
                        df_sac_qa_admin.to_csv(sac_perguntas_respostas_csv, index=False, encoding='utf-8')
                        st.cache_data.clear()  
                        st.toast("Pergunta adicionada ao SAC!", icon="🎉")
                        st.rerun()
                    else:
                        st.warning("Pergunta, Resposta e Categoria são obrigatórias.")
            
            st.divider()
            st.subheader("Perguntas e Respostas Atuais do SAC")
            if df_sac_qa_admin.empty:
                st.info("Nenhuma pergunta cadastrada no SAC.")
            else:
                for i_sac, row_sac_item in df_sac_qa_admin.iterrows():
                    st.markdown(f"""
                    <div class="custom-card" style="margin-bottom: 10px; border-left-color: #10b981;">
                        <small><i>ID: {row_sac_item['ID_SAC_Pergunta']} | Categoria: {row_sac_item['Categoria_SAC']} | Criado em: {row_sac_item.get('DataCriacao','N/A')}</i></small>
                        <h5>P: {row_sac_item['Pergunta_SAC']}</h5>
                        <p>R: {row_sac_item['Resposta_SAC'][:200] + ('...' if len(row_sac_item['Resposta_SAC']) > 200 else '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("✏️ Editar / 🗑️ Deletar esta Pergunta/Resposta SAC"):
                        form_key_edit_sac = f"form_edit_sac_v21_{row_sac_item['ID_SAC_Pergunta']}"  
                        with st.form(form_key_edit_sac):
                            edited_p_sac = st.text_input("Editar Pergunta:", value=row_sac_item['Pergunta_SAC'], key=f"edit_p_{form_key_edit_sac}", disabled=not is_admin_total())
                            edited_r_sac = st.text_area("Editar Resposta:", value=row_sac_item['Resposta_SAC'], height=100, key=f"edit_r_{form_key_edit_sac}", disabled=not is_admin_total())
                            
                            cat_edit_sac_opts = ["Manter Categoria Atual"] + sorted(list(df_sac_qa_admin['Categoria_SAC'].astype(str).unique())) + ["Nova Categoria (Editar Abaixo)"]
                            sel_cat_edit_sac = st.selectbox("Nova Categoria (ou manter):", cat_edit_sac_opts, key=f"sel_cat_edit_{form_key_edit_sac}", disabled=not is_admin_total())
                            
                            input_new_cat_edit_sac = ""
                            if sel_cat_edit_sac == "Nova Categoria (Editar Abaixo)":
                                input_new_cat_edit_sac = st.text_input("Digite a Nova Categoria:", key=f"input_new_cat_edit_{form_key_edit_sac}", disabled=not is_admin_total())
                            
                            final_cat_edit_sac = row_sac_item['Categoria_SAC']  
                            if sel_cat_edit_sac == "Nova Categoria (Editar Abaixo)":
                                if input_new_cat_edit_sac.strip(): final_cat_edit_sac = input_new_cat_edit_sac.strip()
                            elif sel_cat_edit_sac != "Manter Categoria Atual":
                                final_cat_edit_sac = sel_cat_edit_sac
                            
                            col_btn_sac1, col_btn_sac2 = st.columns(2)
                            if col_btn_sac1.form_submit_button("Salvar Alterações SAC", icon="💾", use_container_width=True, disabled=not is_admin_total()):
                                if is_admin_total():
                                    df_sac_qa_admin.loc[i_sac, "Pergunta_SAC"] = edited_p_sac
                                    df_sac_qa_admin.loc[i_sac, "Resposta_SAC"] = edited_r_sac
                                    df_sac_qa_admin.loc[i_sac, "Categoria_SAC"] = final_cat_edit_sac
                                    df_sac_qa_admin.loc[i_sac, "DataCriacao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
                                    df_sac_qa_admin.to_csv(sac_perguntas_respostas_csv, index=False, encoding='utf-8')
                                    st.cache_data.clear()
                                    st.toast("Alterações salvas no SAC!", icon="✅")
                                    st.rerun()

                            if col_btn_sac2.form_submit_button("Deletar do SAC", icon="🗑️", type="primary", use_container_width=True, disabled=not is_admin_total()):
                                if is_admin_total():
                                    df_sac_qa_admin = df_sac_qa_admin.drop(index=i_sac)
                                    df_sac_qa_admin.to_csv(sac_perguntas_respostas_csv, index=False, encoding='utf-8')
                                    st.cache_data.clear()
                                    st.toast("Pergunta/Resposta deletada do SAC!", icon="🗑️")
                                    st.rerun()
                    st.markdown("<hr>", unsafe_allow_html=True)


        with sac_admin_tabs[1]:
            st.subheader("Relatório de Interações e Feedback do SAC")
            if df_sac_uso_admin.empty:
                st.info("Nenhum feedback ou uso registrado no SAC ainda.")
            else:
                df_sac_uso_display = df_sac_uso_admin.copy()
                if not df_usuarios_admin_geral.empty:
                    df_sac_uso_display = pd.merge(df_sac_uso_display, df_usuarios_admin_geral[['CNPJ', 'Empresa']],
                                                     left_on='CNPJ_Cliente', right_on='CNPJ', how='left')
                    df_sac_uso_display.rename(columns={'Empresa': 'Empresa Cliente'}, inplace=True)
                    df_sac_uso_display['Empresa Cliente'] = df_sac_uso_display['Empresa Cliente'].fillna("N/D (Usuário Desconhecido)")
                    df_sac_uso_display.drop(columns=['CNPJ'], inplace=True, errors='ignore')
                else:
                    df_sac_uso_display['Empresa Cliente'] = "N/D (Dados de Usuários Não Carregados)"

                if not df_sac_qa_admin.empty:
                    df_sac_uso_display = pd.merge(df_sac_uso_display, df_sac_qa_admin[['ID_SAC_Pergunta', 'Pergunta_SAC', 'Categoria_SAC']],
                                                     on='ID_SAC_Pergunta', how='left')
                    df_sac_uso_display['Pergunta_SAC'] = df_sac_uso_display['Pergunta_SAC'].fillna("N/D (Pergunta SAC Excluída)")
                    df_sac_uso_display['Categoria_SAC'] = df_sac_uso_display['Categoria_SAC'].fillna("N/D")

                filt_col1, filt_col2, filt_col3 = st.columns(3)
                clientes_sac_uso_list = ["Todos"] + sorted(df_sac_uso_display["Empresa Cliente"].astype(str).unique().tolist())
                sel_cliente_sac_uso = filt_col1.selectbox("Filtrar por Cliente:", clientes_sac_uso_list, key="sac_uso_cliente_filt_v21")  

                perguntas_sac_uso_list = ["Todas"] + sorted(df_sac_uso_display["Pergunta_SAC"].astype(str).unique().tolist())
                sel_pergunta_sac_uso = filt_col2.selectbox("Filtrar por Pergunta SAC:", perguntas_sac_uso_list, key="sac_uso_pergunta_filt_v21")  

                feedback_options_map = {"Todos": None, "Útil": True, "Não Útil": False, "Sem Feedback": pd.NA}
                sel_feedback_sac_uso_display = filt_col3.selectbox("Filtrar por Feedback:", list(feedback_options_map.keys()), key="sac_uso_feedback_filt_v21")  
                sel_feedback_sac_uso_actual = feedback_options_map[sel_feedback_sac_uso_display]


                df_sac_uso_filtrado = df_sac_uso_display.copy()
                if sel_cliente_sac_uso != "Todos":
                    df_sac_uso_filtrado = df_sac_uso_filtrado[df_sac_uso_filtrado["Empresa Cliente"] == sel_cliente_sac_uso]
                if sel_pergunta_sac_uso != "Todas":
                    df_sac_uso_filtrado = df_sac_uso_filtrado[df_sac_uso_filtrado["Pergunta_SAC"] == sel_pergunta_sac_uso]
                
                if sel_feedback_sac_uso_actual is not None:  
                    if pd.isna(sel_feedback_sac_uso_actual):  
                        df_sac_uso_filtrado = df_sac_uso_filtrado[df_sac_uso_filtrado["Feedback_Util"].isna()]
                    else:  
                        df_sac_uso_filtrado = df_sac_uso_filtrado[df_sac_uso_filtrado["Feedback_Util"] == sel_feedback_sac_uso_actual]


                if df_sac_uso_filtrado.empty:
                    st.info("Nenhum registro de uso do SAC para os filtros aplicados.")
                else:
                    cols_show_sac_uso = ['Timestamp', 'Empresa Cliente', 'CNPJ_Cliente', 'Categoria_SAC', 'Pergunta_SAC', 'Feedback_Util', 'ID_Uso_SAC']
                    df_sac_uso_filtrado['Feedback_Util'] = df_sac_uso_filtrado['Feedback_Util'].map({True: '👍 Útil', False: '👎 Não Útil', pd.NA: '➖ Sem Feedback'}).fillna('➖ Sem Feedback')
                    st.dataframe(df_sac_uso_filtrado[cols_show_sac_uso].sort_values(by="Timestamp", ascending=False), use_container_width=True)

elif menu_admin == "Configurações do Portal": # Renomeado
        st.markdown("#### ⚙️ Configurações Gerais do Portal")
        
        st.subheader("🖼️ Logo do Portal")
        if not is_admin_total():
            st.warning("Apenas administradores com permissão 'total' podem alterar o logo do portal.")
        
        current_portal_logo = get_portal_logo_path()
        if current_portal_logo:
            st.image(current_portal_logo, caption="Logo Atual do Portal", width=200)
            if st.button("Remover Logo do Portal", key="remove_portal_logo_v21", disabled=not is_admin_total()):
                if is_admin_total():
                    try:
                        os.remove(current_portal_logo)
                        st.toast("Logo do portal removida!", icon="🗑️")
                        st.rerun()
                    except Exception as e_rem_logo:
                        st.error(f"Erro ao remover logo: {e_rem_logo}")
        else:
            st.info("Nenhuma logo do portal configurada.")

        uploaded_portal_logo = st.file_uploader("Carregar Nova Logo para o Portal (PNG recomendado, máx 2MB):", type=["png", "jpg", "jpeg"], key="upload_portal_logo_v21", disabled=not is_admin_total())
        if uploaded_portal_logo is not None and is_admin_total():
            try:
                # Salvar com nome fixo, substituindo se existir
                save_path = os.path.join(PORTAL_ASSETS_DIR, PORTAL_LOGO_FILENAME)
                with open(save_path, "wb") as f:
                    f.write(uploaded_portal_logo.getbuffer())
                st.toast("Nova logo do portal salva com sucesso!", icon="🖼️")
                st.rerun()
            except Exception as e_save_logo:
                st.error(f"Erro ao salvar nova logo: {e_save_logo}")
        
        st.divider()
        st.subheader("✍️ Editar Texto das Instruções para Clientes")
        
        current_instructions_text = ""
        instrucoes_loaded_source = None  

        if os.path.exists(instrucoes_custom_path):
            with open(instrucoes_custom_path, "r", encoding="utf-8") as f:
                current_instructions_text = f.read()
            instrucoes_loaded_source = instrucoes_custom_path
        elif os.path.exists(instrucoes_default_path):  
            with open(instrucoes_default_path, "r", encoding="utf-8") as f:  
                current_instructions_text = f.read()
            instrucoes_loaded_source = instrucoes_default_path
            try:
                with open(instrucoes_custom_path, "w", encoding="utf-8") as f_custom:
                    f_custom.write(current_instructions_text)
                st.info(f"Instruções carregadas de '{instrucoes_default_path}' e salvas como ponto de partida em '{instrucoes_custom_path}'.")
            except Exception as e_write_custom:
                st.warning(f"Instruções carregadas de '{instrucoes_default_path}', mas não foi possível criar '{instrucoes_custom_path}': {e_write_custom}")
        else:  
            st.warning(
                f"Nenhum arquivo de instruções ('{instrucoes_custom_path}' ou '{instrucoes_default_path}') encontrado. "
                f"Um texto base foi carregado. Edite e salve abaixo para criar '{instrucoes_custom_path}'."
            )
            current_instructions_text = (
                "# Bem-vindo ao Portal de Diagnóstico!\n\n"
                "Estas são as instruções padrão. Edite este texto conforme necessário.\n\n"
                "## Como usar o portal:\n"
                "1.  **Navegue pelo menu:** Utilize o menu lateral para acessar as diferentes seções.\n"
                "2.  **Novo Diagnóstico:** Se disponível, preencha o formulário para gerar um novo diagnóstico.\n"
                "3.  **Painel Principal:** Visualize seus diagnósticos anteriores, acompanhe sua evolução e o plano de ação.\n"
                "4.  **Notificações:** Verifique se há novas mensagens ou atualizações do consultor.\n\n"
                "Em caso de dúvidas, contate o administrador.\n\n"
                "*Este texto pode ser editado e salvo pelo administrador.*"
            )
            instrucoes_loaded_source = "in-script default"
            
        edited_text = st.text_area(
            "Edite o texto abaixo (suporta Markdown). Após salvar, este texto será usado como as instruções para os clientes:",
            value=current_instructions_text,
            height=600,
            key="instrucoes_editor_v21",  
            disabled=not is_admin_total()
        )

        if st.button("Salvar Instruções", key="save_instrucoes_v21", icon="💾", use_container_width=True, disabled=not is_admin_total()):  
            if is_admin_total():
                try:
                    with open(instrucoes_custom_path, "w", encoding="utf-8") as f:
                        f.write(edited_text)
                    st.toast("Instruções salvas com sucesso!", icon="🎉")
                    st.rerun()  
                except Exception as e_save_instr:
                    st.error(f"Erro ao salvar as instruções: {e_save_instr}")
                
elif menu_admin == "Histórico de Usuários":
        try:
            df_historico_completo_hu = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
            df_usuarios_para_filtro_hu = pd.read_csv(usuarios_csv, encoding='utf-8', usecols=['CNPJ', 'Empresa', 'NomeContato'], dtype={'CNPJ': str})
        except FileNotFoundError:
            st.error("Arquivo de histórico ou usuários não encontrado.")
            df_historico_completo_hu = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])  
            df_usuarios_para_filtro_hu = pd.DataFrame(columns=['CNPJ', 'Empresa', 'NomeContato'])
        except Exception as e_hu:
            st.error(f"Erro ao carregar dados para o histórico: {e_hu}")
            df_historico_completo_hu = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
            df_usuarios_para_filtro_hu = pd.DataFrame(columns=['CNPJ', 'Empresa', 'NomeContato'])

        st.markdown("#### Filtros do Histórico")
        col_hu_f1, col_hu_f2 = st.columns(2)
        empresas_hist_list_hu = ["Todas"]
        if not df_usuarios_para_filtro_hu.empty and 'Empresa' in df_usuarios_para_filtro_hu.columns:
            empresas_hist_list_hu.extend(sorted(df_usuarios_para_filtro_hu['Empresa'].astype(str).unique().tolist()))
        
        emp_sel_hu = col_hu_f1.selectbox("Filtrar por Empresa:", empresas_hist_list_hu, key="hist_emp_sel_v21")  
        termo_busca_hu = col_hu_f2.text_input("Buscar por Nome do Contato, CNPJ, Ação ou Descrição:", key="hist_termo_busca_v21")  

        df_historico_filtrado_view_hu = df_historico_completo_hu.copy()

        if emp_sel_hu != "Todas" and not df_usuarios_para_filtro_hu.empty:
            cnpjs_da_empresa_hu = df_usuarios_para_filtro_hu[df_usuarios_para_filtro_hu['Empresa'] == emp_sel_hu]['CNPJ'].tolist()
            df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_da_empresa_hu)]
        
        if termo_busca_hu.strip():
            busca_lower_hu = termo_busca_hu.strip().lower()
            cnpjs_match_nome_hu = []
            if not df_usuarios_para_filtro_hu.empty and 'NomeContato' in df_usuarios_para_filtro_hu.columns:
                cnpjs_match_nome_hu = df_usuarios_para_filtro_hu[
                    df_usuarios_para_filtro_hu['NomeContato'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)
                ]['CNPJ'].tolist()
            
            df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[
                df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_match_nome_hu) |  
                df_historico_filtrado_view_hu['CNPJ'].astype(str).str.lower().str.contains(busca_lower_hu) |
                df_historico_filtrado_view_hu['Ação'].astype(str).str.lower().str.contains(busca_lower_hu, na=False) |
                df_historico_filtrado_view_hu['Descrição'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)
            ]

        st.markdown("#### Registros do Histórico")
        if not df_historico_filtrado_view_hu.empty:
            st.dataframe(df_historico_filtrado_view_hu.sort_values(by="Data", ascending=False), use_container_width=True)
        else:
            st.info("Nenhum registro de histórico encontrado para os filtros aplicados.")

elif menu_admin == "Gerenciar Clientes":
        df_usuarios_gc = df_usuarios_admin_geral.copy()

        st.sidebar.markdown("---")  
        st.sidebar.subheader("Filtros para Gerenciar Clientes")
        filter_instrucoes_status_gc = st.sidebar.selectbox(
            "Status das Instruções:",
            ["Todos", "Visualizaram Instruções", "Não Visualizaram Instruções"],
            key="admin_gc_filter_instrucoes_status_v21"  
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
                cliente_selecionado_str_gc = st.selectbox("Selecione o cliente para gerenciar:", [""] + clientes_lista_gc_ops, key="sel_cliente_gc_v21_filtered")  

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
                        
                        # Upload de logo do cliente
                        st.markdown("##### Logo do Cliente")
                        client_logo_current_path = find_client_logo_path(cnpj_selecionado_gc_val)
                        if client_logo_current_path:
                            st.image(client_logo_current_path, width=150, caption="Logo Atual do Cliente")
                            if st.button("Remover Logo do Cliente", key=f"remove_client_logo_{cnpj_selecionado_gc_val}", disabled=not is_admin_total()):
                                if is_admin_total():
                                    try:
                                        os.remove(client_logo_current_path)
                                        st.toast("Logo do cliente removida!", icon="🗑️")
                                        st.rerun()
                                    except Exception as e_rem_cl_logo:
                                        st.error(f"Erro ao remover logo do cliente: {e_rem_cl_logo}")
                        
                        uploaded_client_logo = st.file_uploader("Carregar Nova Logo para este Cliente (PNG, JPG):", type=["png", "jpg", "jpeg"], key=f"upload_client_logo_{cnpj_selecionado_gc_val}", disabled=not is_admin_total())
                        if uploaded_client_logo is not None and is_admin_total():
                            try:
                                # Limpar logos antigas com mesmo CNPJ base mas extensão diferente
                                base_name = str(cnpj_selecionado_gc_val).replace('/', '').replace('.', '').replace('-', '')
                                for ext_old in ["png", "jpg", "jpeg"]:
                                    old_path = os.path.join(LOGOS_DIR, f"{base_name}_logo.{ext_old}")
                                    if os.path.exists(old_path):
                                        os.remove(old_path)

                                file_extension = os.path.splitext(uploaded_client_logo.name)[1].lower()
                                client_logo_filename = f"{base_name}_logo{file_extension}"
                                client_logo_save_path = os.path.join(LOGOS_DIR, client_logo_filename)
                                with open(client_logo_save_path, "wb") as f:
                                    f.write(uploaded_client_logo.getbuffer())
                                st.toast("Nova logo do cliente salva!", icon="🖼️")
                                st.rerun()
                            except Exception as e_save_cl_logo:
                                st.error(f"Erro ao salvar logo do cliente: {e_save_cl_logo}")
                        st.divider()


                        action_cols = st.columns(2)
                        with action_cols[0]:
                            if st.button(f"Conceder +1 Diagnóstico", key=f"conceder_diag_gc_v21_{cnpj_selecionado_gc_val}", icon="➕", use_container_width=True, disabled=not is_admin_total()):  
                                if is_admin_total():
                                    novos_disponiveis = int(cliente_data_gc_val['DiagnosticosDisponiveis']) + 1
                                    if update_user_data(cnpj_selecionado_gc_val, "DiagnosticosDisponiveis", novos_disponiveis):
                                        st.toast(f"1 Diagnóstico concedido para {cliente_data_gc_val['Empresa']}!", icon="✅")
                                        st.rerun()
                                    else:
                                        st.error("Erro ao conceder diagnóstico.")

                            if st.button(f"Resetar Senha", key=f"reset_senha_gc_v21_{cnpj_selecionado_gc_val}", icon="🔑", use_container_width=True, disabled=not is_admin_total()):
                                if is_admin_total():
                                    nova_senha_padrao = "12345" # Senha padrão para reset
                                    try:
                                        df_usuarios_reset = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                                        idx_reset = df_usuarios_reset[df_usuarios_reset['CNPJ'] == cnpj_selecionado_gc_val].index
                                        if not idx_reset.empty:
                                            df_usuarios_reset.loc[idx_reset, "Senha"] = nova_senha_padrao
                                            df_usuarios_reset.to_csv(usuarios_csv, index=False, encoding='utf-8')
                                            registrar_acao(cnpj_selecionado_gc_val, "Reset Senha", f"Senha resetada para {nova_senha_padrao}")
                                            st.toast(f"Senha de {cliente_data_gc_val['Empresa']} resetada para '{nova_senha_padrao}'!", icon="✅")
                                            st.rerun()
                                        else:
                                            st.error("Cliente não encontrado para reset de senha.")
                                    except Exception as e_reset_senha:
                                        st.error(f"Erro ao resetar senha: {e_reset_senha}")

                        with action_cols[1]:
                            is_blocked = False
                            try:
                                df_blocked = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                                is_blocked = cnpj_selecionado_gc_val in df_blocked["CNPJ"].values
                            except (FileNotFoundError, pd.errors.EmptyDataError):
                                pass # No blocked users file or empty

                            if is_blocked:
                                if st.button(f"Desbloquear Cliente", key=f"desbloquear_gc_v21_{cnpj_selecionado_gc_val}", icon="🔓", use_container_width=True, type="secondary", disabled=not is_admin_total()):
                                    if is_admin_total():
                                        try:
                                            df_blocked = df_blocked[df_blocked["CNPJ"] != cnpj_selecionado_gc_val]
                                            df_blocked.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                                            registrar_acao(cnpj_selecionado_gc_val, "Desbloqueio", "Cliente desbloqueado.")
                                            st.toast(f"Cliente {cliente_data_gc_val['Empresa']} desbloqueado!", icon="✅")
                                            st.rerun()
                                        except Exception as e_unblock:
                                            st.error(f"Erro ao desbloquear cliente: {e_unblock}")
                            else:
                                if st.button(f"Bloquear Cliente", key=f"bloquear_gc_v21_{cnpj_selecionado_gc_val}", icon="🔒", use_container_width=True, type="primary", disabled=not is_admin_total()):
                                    if is_admin_total():
                                        try:
                                            df_blocked = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                                            new_blocked_entry = pd.DataFrame([{"CNPJ": cnpj_selecionado_gc_val}])
                                            df_blocked = pd.concat([df_blocked, new_blocked_entry], ignore_index=True)
                                            df_blocked.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                                            registrar_acao(cnpj_selecionado_gc_val, "Bloqueio", "Cliente bloqueado.")
                                            st.toast(f"Cliente {cliente_data_gc_val['Empresa']} bloqueado!", icon="🚨")
                                            st.rerun()
                                        except Exception as e_block:
                                            st.error(f"Erro ao bloquear cliente: {e_block}")
                            
                            if st.button(f"Deletar Cliente", key=f"deletar_cliente_gc_v21_{cnpj_selecionado_gc_val}", icon="🗑️", use_container_width=True, type="primary", disabled=not is_admin_total()):
                                if is_admin_total():
                                    if st.checkbox(f"Confirmar exclusão de {cliente_data_gc_val['Empresa']} (irreversível)?", key=f"confirm_del_gc_v21_{cnpj_selecionado_gc_val}"):
                                        try:
                                            # Remover do CSV de usuários
                                            df_usuarios_gc = df_usuarios_gc[df_usuarios_gc['CNPJ'] != cnpj_selecionado_gc_val]
                                            df_usuarios_gc.to_csv(usuarios_csv, index=False, encoding='utf-8')

                                            # Remover diagnósticos relacionados
                                            df_diagnosticos_existentes = pd.read_csv(arquivo_csv, dtype={'CNPJ': str}, encoding='utf-8')
                                            df_diagnosticos_existentes = df_diagnosticos_existentes[df_diagnosticos_existentes['CNPJ'] != cnpj_selecionado_gc_val]
                                            df_diagnosticos_existentes.to_csv(arquivo_csv, index=False, encoding='utf-8')

                                            # Remover notificações relacionadas
                                            df_notificacoes_existentes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
                                            df_notificacoes_existentes = df_notificacoes_existentes[df_notificacoes_existentes['CNPJ_Cliente'] != cnpj_selecionado_gc_val]
                                            df_notificacoes_existentes.to_csv(notificacoes_csv, index=False, encoding='utf-8')

                                            # Remover SAC uso/feedback relacionado
                                            df_sac_uso_existente = pd.read_csv(sac_uso_feedback_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
                                            df_sac_uso_existente = df_sac_uso_existente[df_sac_uso_existente['CNPJ_Cliente'] != cnpj_selecionado_gc_val]
                                            df_sac_uso_existente.to_csv(sac_uso_feedback_csv, index=False, encoding='utf-8')

                                            # Remover respostas de satisfação relacionadas
                                            df_satisfacao_resp_existente = pd.read_csv(satisfacao_respostas_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
                                            df_satisfacao_resp_existente = df_satisfacao_resp_existente[df_satisfacao_resp_existente['CNPJ_Cliente'] != cnpj_selecionado_gc_val]
                                            df_satisfacao_resp_existente.to_csv(satisfacao_respostas_csv, index=False, encoding='utf-8')

                                            # Remover logo do cliente, se existir
                                            logo_to_remove = find_client_logo_path(cnpj_selecionado_gc_val)
                                            if logo_to_remove and os.path.exists(logo_to_remove):
                                                os.remove(logo_to_remove)

                                            registrar_acao(cnpj_selecionado_gc_val, "Deleção Cliente", "Cliente e todos os dados relacionados deletados.")
                                            st.toast(f"Cliente {cliente_data_gc_val['Empresa']} e todos os dados relacionados foram deletados!", icon="🗑️")
                                            st.cache_data.clear()
                                            st.rerun()
                                        except Exception as e_del_cliente:
                                            st.error(f"Erro ao deletar cliente e dados relacionados: {e_del_cliente}")
                                            st.exception(e_del_cliente)
            else:
                st.info("Nenhum cliente selecionado para gerenciar.")
        else:
            st.info("Nenhum cliente encontrado para os filtros aplicados.")
        
        st.markdown("#### Adicionar Novo Cliente")
        if not is_admin_total():
            st.warning("Apenas administradores com permissão 'total' podem adicionar novos clientes.")

        with st.form("form_add_cliente_admin_v21", clear_on_submit=True):
            new_cnpj = st.text_input("CNPJ do Novo Cliente:", key="new_cli_cnpj_v21", disabled=not is_admin_total())
            new_senha = st.text_input("Senha do Novo Cliente:", type="password", key="new_cli_senha_v21", disabled=not is_admin_total())
            new_empresa = st.text_input("Nome da Empresa:", key="new_cli_empresa_v21", disabled=not is_admin_total())
            new_contato = st.text_input("Nome do Contato:", key="new_cli_contato_v21", disabled=not is_admin_total())
            new_telefone = st.text_input("Telefone do Contato:", key="new_cli_telefone_v21", disabled=not is_admin_total())
            new_slots = st.number_input("Diagnósticos Disponíveis (Slots):", min_value=1, value=1, step=1, key="new_cli_slots_v21", disabled=not is_admin_total())

            if st.form_submit_button("Adicionar Cliente", icon="➕", use_container_width=True, disabled=not is_admin_total()):
                if is_admin_total():
                    if new_cnpj and new_senha and new_empresa and new_contato:
                        try:
                            users_df_add = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                            if new_cnpj in users_df_add["CNPJ"].values:
                                st.error("CNPJ já cadastrado.")
                            else:
                                new_user_data = {
                                    "CNPJ": new_cnpj,
                                    "Senha": new_senha,
                                    "Empresa": new_empresa,
                                    "NomeContato": new_contato,
                                    "Telefone": new_telefone,
                                    "JaVisualizouInstrucoes": False,
                                    "DiagnosticosDisponiveis": int(new_slots),
                                    "TotalDiagnosticosRealizados": 0
                                }
                                new_user_df = pd.DataFrame([new_user_data])
                                users_df_add = pd.concat([users_df_add, new_user_df], ignore_index=True)
                                users_df_add.to_csv(usuarios_csv, index=False, encoding='utf-8')
                                registrar_acao(new_cnpj, "Cadastro Cliente", f"Novo cliente '{new_empresa}' cadastrado.")
                                st.toast(f"Cliente {new_empresa} adicionado com sucesso!", icon="🎉")
                                st.cache_data.clear()
                                st.rerun()
                        except Exception as e_add_user:
                            st.error(f"Erro ao adicionar novo cliente: {e_add_user}")
                            st.exception(e_add_user)
                    else:
                        st.warning("Preencha todos os campos obrigatórios (CNPJ, Senha, Empresa, Nome do Contato).")
    
elif menu_admin == "Gerenciar Administradores":

    st.header("⏳ Renovação Rápida de Prazo dos Clientes")

    usuarios_csv = "usuarios.csv"  # ajuste conforme sua estrutura
    df_todos = pd.read_csv(usuarios_csv, dtype={'CNPJ': str})
    df_todos["PrazoFimAcesso"] = pd.to_datetime(df_todos["PrazoFimAcesso"], errors="coerce")
    df_todos["DiasRestantes"] = df_todos["PrazoFimAcesso"].apply(
        lambda x: (x.date() - date.today()).days if pd.notna(x) else None
    )

    for idx, row in df_todos.iterrows():
        st.markdown(f"**{row['Empresa']}** — Dias Restantes: `{row['DiasRestantes']}`")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Adicionar 5 Dias", key=f"add5_{row['CNPJ']}_{idx}"):
                renovar_dias_usuario(row['CNPJ'], 5)
                st.experimental_rerun()
        with col2:
            if st.button("❌ Bloquear Cliente", key=f"block_{row['CNPJ']}_{idx}"):
                bloquear_usuario(row['CNPJ'])
                st.experimental_rerun()
        st.markdown("#### Gerenciamento de Usuários Administradores")
        if not is_admin_total():
            st.warning("Apenas administradores com permissão 'total' podem gerenciar outros administradores.")
        
        try:
            df_admins = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            if "Permissoes" not in df_admins.columns:
                df_admins["Permissoes"] = "total" # Default to total if column is missing
                df_admins.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
        except (FileNotFoundError, pd.errors.EmptyDataError):
            st.info("Nenhum administrador cadastrado. Por favor, adicione um novo administrador abaixo.")
            df_admins = pd.DataFrame(columns=colunas_base_admin_credenciais)
        except Exception as e:
            st.error(f"Erro ao carregar dados de administradores: {e}")
            df_admins = pd.DataFrame(columns=colunas_base_admin_credenciais)

        st.subheader("Administradores Atuais")
        if not df_admins.empty:
            st.dataframe(df_admins, use_container_width=True)
        else:
            st.info("Nenhum administrador cadastrado.")

        st.subheader("Adicionar Novo Administrador")
        with st.form("form_add_admin_v21", clear_on_submit=True):
            new_admin_user = st.text_input("Usuário:", key="new_admin_user_v21", disabled=not is_admin_total())
            new_admin_pass = st.text_input("Senha:", type="password", key="new_admin_pass_v21", disabled=not is_admin_total())
            new_admin_perms = st.selectbox("Permissões:", ["visualizacao", "total"], key="new_admin_perms_v21", disabled=not is_admin_total())
            
            if st.form_submit_button("Adicionar Administrador", icon="➕", use_container_width=True, disabled=not is_admin_total()):
                if is_admin_total():
                    if new_admin_user.strip() and new_admin_pass.strip():
                        if new_admin_user in df_admins["Usuario"].values:
                            st.error("Usuário já existe.")
                        else:
                            new_admin_entry = pd.DataFrame([{
                                "Usuario": new_admin_user.strip(),
                                "Senha": new_admin_pass.strip(),
                                "Permissoes": new_admin_perms
                            }])
                            df_admins = pd.concat([df_admins, new_admin_entry], ignore_index=True)
                            df_admins.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                            st.toast("Novo administrador adicionado!", icon="🎉")
                            st.rerun()
                    else:
                        st.warning("Usuário e senha são obrigatórios.")

        st.subheader("Editar Administrador Existente")
        if not df_admins.empty:
            admin_to_edit_user = st.selectbox("Selecione o Administrador para Editar:", [""] + df_admins["Usuario"].tolist(), key="edit_admin_sel_user_v21", disabled=not is_admin_total())
            
            if admin_to_edit_user:
                current_admin_data = df_admins[df_admins["Usuario"] == admin_to_edit_user].iloc[0]
                
                with st.form(f"form_edit_admin_{admin_to_edit_user}_v21"):
                    edited_admin_pass = st.text_input("Nova Senha (deixe em branco para não alterar):", type="password", key=f"edited_admin_pass_{admin_to_edit_user}_v21", disabled=not is_admin_total())
                    
                    current_perms_idx = 0
                    if "Permissoes" in current_admin_data and current_admin_data["Permissoes"] in ["visualizacao", "total"]:
                        current_perms_idx = ["visualizacao", "total"].index(current_admin_data["Permissoes"])
                    
                    edited_admin_perms = st.selectbox("Permissões:", ["visualizacao", "total"], index=current_perms_idx, key=f"edited_admin_perms_{admin_to_edit_user}_v21", disabled=not is_admin_total())
                    
                    if st.form_submit_button("Salvar Alterações do Administrador", icon="💾", use_container_width=True, disabled=not is_admin_total()):
                        if is_admin_total():
                            idx_to_update = df_admins[df_admins["Usuario"] == admin_to_edit_user].index
                            if not idx_to_update.empty:
                                if edited_admin_pass.strip():
                                    df_admins.loc[idx_to_update, "Senha"] = edited_admin_pass.strip()
                                df_admins.loc[idx_to_update, "Permissoes"] = edited_admin_perms
                                df_admins.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                                st.toast(f"Administrador {admin_to_edit_user} atualizado!", icon="✅")
                                st.rerun()
                            else:
                                st.error("Erro: Administrador não encontrado.")
        else:
            st.info("Nenhum administrador para editar.")

        st.subheader("Deletar Administrador")
        if not df_admins.empty:
            admin_to_delete_user = st.selectbox("Selecione o Administrador para Deletar:", [""] + df_admins["Usuario"].tolist(), key="del_admin_sel_user_v21", disabled=not is_admin_total())
            
            if st.button("Deletar Administrador Selecionado", icon="🗑️", type="primary", use_container_width=True, disabled=not is_admin_total()):
                if is_admin_total():
                    if admin_to_delete_user:
                        if admin_to_delete_user == st.session_state.admin_username:
                            st.error("Você não pode deletar a si mesmo!")
                        elif len(df_admins) == 1:
                            st.error("Não é possível deletar o último administrador do sistema.")
                        else:
                            df_admins = df_admins[df_admins["Usuario"] != admin_to_delete_user]
                            df_admins.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                            st.toast(f"Administrador {admin_to_delete_user} deletado!", icon="🗑️")
                            st.rerun()
                    else:
                        st.warning("Selecione um administrador para deletar.")
        else:
            st.info("Nenhum administrador para deletar.")
 

# ========= FUNCIONALIDADES SOLICITADAS PELO USUÁRIO =========

# Função para prazo inicial padrão dos clientes (5 dias)
def prazo_inicial_cliente():
    return (date.today() + pd.Timedelta(days=5)).strftime('%Y-%m-%d')

# Inicialização da coluna 'DiagnosticosPermitidos' nos usuários
usuarios_csv = "usuarios.csv"
df_users = pd.read_csv(usuarios_csv, dtype={'CNPJ': str})
if "DiagnosticosPermitidos" not in df_users.columns:
    df_users["DiagnosticosPermitidos"] = "[]"
    df_users.to_csv(usuarios_csv, index=False)

# Permissões detalhadas do Administrador
permissoes_lista = ["SAC", "PerguntaSatisfacao", "GestaoClientes", "Relatorios", "Personalizacao"]

with st.sidebar.expander("Permissões do Administrador", expanded=True):
    df_admin = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
    admin_sel = st.selectbox("Selecionar admin", df_admin['Usuario'].tolist(), index=0)
    permissoes_atual = get_admin_permissoes(admin_sel)

    permissoes_novas = st.multiselect(
    "Permissões", 
    permissoes_lista, 
    default=[perm for perm in permissoes_atual if perm in permissoes_lista]
)


# Painel Cliente mostrando prazo restante
if 'cliente_logado' in st.session_state and st.session_state['cliente_logado']:
    df_users = pd.read_csv(usuarios_csv, dtype={'CNPJ': str})

    # Garante que a coluna exista
    if "PrazoFimAcesso" not in df_users.columns:
        df_users["PrazoFimAcesso"] = (date.today() + pd.Timedelta(days=5)).strftime('%Y-%m-%d')
        df_users.to_csv(usuarios_csv, index=False)

    df_users["PrazoFimAcesso"] = pd.to_datetime(df_users["PrazoFimAcesso"], errors="coerce")

    idx_cliente = df_users[df_users['CNPJ'] == st.session_state['cnpj']].index
    if not idx_cliente.empty:
        prazo = df_users.loc[idx_cliente[0], 'PrazoFimAcesso']
        if pd.notna(prazo):
            dias_restantes = (prazo.date() - date.today()).days
            st.info(f"⏳ Você possui **{dias_restantes} dias restantes** até o fim do seu acesso.")
        else:
            st.warning("⚠️ Seu prazo de acesso ainda não está definido.")
    else:
        st.error("Cliente não encontrado.")

# ========== CONTROLE DE PRAZO DE CLIENTES ==========
df_users = pd.read_csv(usuarios_csv, dtype={'CNPJ': str})

# Leitura e validação da base de usuários
df_users = pd.read_csv(usuarios_csv, dtype={'CNPJ': str})

# Garante coluna de status de diagnóstico (evita erro)
if "StatusDiag" not in df_users.columns:
    df_users["StatusDiag"] = "Não Enviado"

# Garante que a coluna de prazo exista
if "PrazoFimAcesso" not in df_users.columns:
    df_users["PrazoFimAcesso"] = (date.today() + pd.Timedelta(days=10)).strftime('%Y-%m-%d')
    df_users.to_csv(usuarios_csv, index=False)

df_users["PrazoFimAcesso"] = pd.to_datetime(df_users["PrazoFimAcesso"], errors="coerce")

df_users["DiasRestantes"] = df_users["PrazoFimAcesso"].apply(
    lambda x: (x.date() - date.today()).days if pd.notna(x) else None
)

def classificar_prazo(dias):
    if dias is None:
        return "Indefinido"
    elif dias <= 0:
        return "Expirado"
    elif dias <= 3:
        return "Crítico"
    elif dias <= 5:
        return "Encerrando"
    else:
        return "Ativo"

df_users["StatusPrazo"] = df_users["DiasRestantes"].apply(classificar_prazo)


# Garante que a coluna exista com prazo padrão de 10 dias
if "PrazoFimAcesso" not in df_users.columns:
    df_users["PrazoFimAcesso"] = (date.today() + pd.Timedelta(days=10)).strftime('%Y-%m-%d')
    df_users.to_csv(usuarios_csv, index=False)

# Conversão segura da coluna para datetime
df_users["PrazoFimAcesso"] = pd.to_datetime(df_users["PrazoFimAcesso"], errors="coerce")

# Calcula dias restantes para cada cliente
df_users["DiasRestantes"] = df_users["PrazoFimAcesso"].apply(
    lambda x: (x.date() - date.today()).days if pd.notna(x) else None
)

# Define o status com base no número de dias restantes
def classificar_prazo(dias):
    if dias is None:
        return "Indefinido"
    elif dias <= 0:
        return "Expirado"
    elif dias <= 3:
        return "Crítico"
    elif dias <= 5:
        return "Encerrando"
    else:
        return "Ativo"

df_users["StatusPrazo"] = df_users["DiasRestantes"].apply(classificar_prazo)

# Enviar notificações para clientes com 5 ou 3 dias restantes
notificacoes = []
for _, row in df_users.iterrows():
    if row["DiasRestantes"] == 5:
        notificacoes.append(f"⚠️ Cliente **{row['Empresa']}** está com 5 dias restantes de acesso.")
    elif row["DiasRestantes"] == 3:
        notificacoes.append(f"🔴 Cliente **{row['Empresa']}** está com 3 dias restantes (prazo crítico).")

# Exibir notificações na tela
for nota in notificacoes:
    st.warning(nota)

# Exibir métricas visuais no painel do administrador
col1, col2, col3 = st.columns(3)
col1.metric("✅ Ativos", df_users[df_users['StatusPrazo'] == 'Ativo'].shape[0])
col2.metric("🟡 Encerrando (≤ 5 dias)", df_users[df_users['StatusPrazo'] == 'Encerrando'].shape[0])
col3.metric("🔴 Críticos (≤ 3 dias)", df_users[df_users['StatusPrazo'] == 'Crítico'].shape[0])

# Painel Admin - Renovação rápida de prazo e bloqueio
st.subheader("Renovação Rápida de Prazo dos Clientes")
# Adiciona a coluna DiasRestantes ao DataFrame df_users
df_users["PrazoFimAcesso"] = pd.to_datetime(df_users["PrazoFimAcesso"], errors="coerce")
df_users["DiasRestantes"] = df_users["PrazoFimAcesso"].apply(lambda x: (x.date() - date.today()).days if pd.notna(x) else None)
for idx, row in df_users.iterrows():
    st.markdown(f"Cliente: {row['Empresa']} - Dias Restantes: {row['DiasRestantes']}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Adicionar 5 Dias", key=f"add5_{row['CNPJ']}_{idx}"):
            renovar_dias_usuario(row['CNPJ'], 5)
            st.experimental_rerun()
    with col2:
        if st.button("Bloquear Cliente", key=f"block_{row['CNPJ']}_{idx}"):
            bloquear_usuario(row['CNPJ'])
            st.experimental_rerun()


# Liberação de Diagnósticos específicos pelo Admin
with st.sidebar.expander("Liberação Diagnósticos Clientes"):
    cnpj_cliente = st.selectbox("CNPJ Cliente", df_users['CNPJ'])
    diagnosticos_disponiveis = ["Financeiro", "Operacional", "RH", "TI"]

    linha_cliente = df_users[df_users['CNPJ'] == cnpj_cliente]
    if not linha_cliente.empty:
        atuais = json.loads(linha_cliente['DiagnosticosPermitidos'].iloc[0] or '[]')
    else:
        atuais = []

    novos_diagnosticos = st.multiselect("Diagnósticos Permitidos", diagnosticos_disponiveis, default=atuais)

    if st.button("Salvar Diagnósticos Permitidos"):
        df_users.loc[df_users['CNPJ'] == cnpj_cliente, 'DiagnosticosPermitidos'] = json.dumps(novos_diagnosticos)
        df_users.to_csv(usuarios_csv, index=False)
        st.success("Diagnósticos atualizados!")

# Métricas adicionais para o administrador

st.subheader("Métricas Gerais")
st.metric("Clientes com Prazo Finalizando", df_users[df_users['StatusPrazo'] == 'Encerrando'].shape[0])
st.metric("Clientes Finalizando com Diagnóstico Enviado", df_users[(df_users['StatusPrazo'] == 'Encerrando') & (df_users['StatusDiag'] == 'Enviado')].shape[0])
