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
import io # Para st.info(buf=...)

# !!! st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT !!!
st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", page_icon="📊")

# --- CSS Melhorado ---
st.markdown("""
<style>
body {font-family: 'Segoe UI', sans-serif;}
.login-container {max-width: 450px; margin: 40px auto 0 auto; padding: 40px; border-radius: 10px; background-color: #ffffff; box-shadow: 0 4px 20px rgba(0,0,0,0.1); font-family: 'Segoe UI', sans-serif;}
.login-container img {display: block; margin-left: auto; margin-right: auto; margin-bottom: 20px;}
.login-container h2 {text-align: center; margin-bottom: 30px; font-weight: 600; font-size: 26px; color: #2563eb;}
.stButton>button {border-radius: 6px; background-color: #2563eb; color: white; font-weight: 500; padding: 0.6rem 1.3rem; margin-top: 0.5rem; border: none; transition: background-color 0.3s ease;}
.stButton>button:hover {background-color: #1d4ed8;}
.stButton>button.secondary {background-color: #e5e7eb; color: #374151;}
.stButton>button.secondary:hover {background-color: #d1d5db;}
.stDownloadButton>button {background-color: #10b981; color: white; font-weight: 600; border-radius: 6px; margin-top: 10px; padding: 0.6rem 1.3rem; border: none; transition: background-color 0.3s ease;}
.stDownloadButton>button:hover {background-color: #059669;}
.stTextInput>div>input, .stTextArea>div>textarea, .stDateInput>div>input, .stSelectbox>div>div {border-radius: 6px; padding: 0.6rem; border: 1px solid #d1d5db; background-color: #f9fafb; transition: border-color 0.3s ease, box-shadow 0.3s ease;}
.stTextInput>div>input:focus, .stTextArea>div>textarea:focus, .stDateInput>div>input:focus, .stSelectbox>div>div:focus-within {border-color: #2563eb; box-shadow: 0 0 0 0.1rem rgba(37, 99, 235, 0.25);}
.stTabs [data-baseweb="tab"] {font-size: 16px; font-weight: 600; padding: 12px 22px; border-radius: 6px 6px 0 0;}
.stTabs [data-baseweb="tab"][aria-selected="true"] {background-color: #2563eb; color: white;}
.custom-card {border: 1px solid #e0e0e0; border-left: 5px solid #2563eb; padding: 20px; margin-bottom: 15px; border-radius: 8px; background-color: #ffffff; box-shadow: 0 2px 5px rgba(0,0,0,0.07);}
.custom-card h4 {margin-top: 0; color: #2563eb; font-size: 1.1em;}
.feedback-saved {font-size: 0.85em; color: #10b981; font-style: italic; margin-top: -8px; margin-bottom: 8px;}
.analise-pergunta-cliente {font-size: 0.9em; color: #333; background-color: #eef2ff; border-left: 3px solid #6366f1; padding: 10px; margin-top: 8px; margin-bottom:12px; border-radius: 4px;}
[data-testid="stMetric"] {background-color: #ffffff; border-radius: 8px; padding: 15px 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.07); border: 1px solid #e0e0e0;}
[data-testid="stMetricLabel"] {font-weight: 500; color: #4b5563;}
[data-testid="stMetricValue"] {font-size: 1.8em;}
[data-testid="stMetricDelta"] {font-size: 0.9em;}
.stExpander {border: 1px solid #e0e0e0 !important; border-radius: 8px !important; box-shadow: 0 2px 5px rgba(0,0,0,0.07) !important; margin-bottom: 15px !important;}
.stExpander header {font-weight: 600 !important; border-radius: 8px 8px 0 0 !important; padding: 10px 15px !important;}
.dashboard-item {background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.07); margin-bottom: 20px; border: 1px solid #e0e0e0; height: 100%;}
.dashboard-item h5 {margin-top: 0; margin-bottom: 15px; color: #2563eb; font-size: 1.1em; border-bottom: 1px solid #eee; padding-bottom: 8px;}
.sac-feedback-button button {background-color: #f0f0f0; color: #333; border: 1px solid #ccc; margin-right: 5px; padding: 0.3rem 0.8rem;}
.sac-feedback-button button:hover {background-color: #e0e0e0;}
.sac-feedback-button button.active {background-color: #2563eb; color: white; border-color: #2563eb;}
</style>
""", unsafe_allow_html=True)

# --- Funções de Gráficos ---
def create_radar_chart(data_dict, title="Radar Chart"):
    if not data_dict or not isinstance(data_dict, dict): return None
    categories = []
    values = []
    for k, v_raw in data_dict.items():
        val_num = pd.to_numeric(v_raw, errors='coerce')
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
    max_len_tarefa = df_gut['Tarefa'].astype(str).map(len).max() if not df_gut.empty else 20
    margin_l_dynamic = max(150, int(max_len_tarefa * 7.5))
    fig = px.bar(df_gut, x="Score", y="Tarefa", title=title, orientation='h', color="Score", color_continuous_scale=px.colors.sequential.Blues_r, labels={'Tarefa':'Tarefa/Pergunta', 'Score':'Score GUT'})
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Score GUT", yaxis_title="", font=dict(family="Segoe UI, sans-serif"), height=max(400, 200 + len(df_gut)*30), margin=dict(l=margin_l_dynamic, r=20, t=70, b=20))
    return fig

def create_diagnostics_timeline_chart(df_diagnostics, title="Diagnósticos Realizados ao Longo do Tempo"):
    if df_diagnostics.empty or 'Data_dt' not in df_diagnostics.columns:
        st.caption(f"Debug Timeline: DataFrame vazio ou sem 'Data_dt'. Shape: {df_diagnostics.shape if not df_diagnostics.empty else 'Vazio'}")
        return None
    df_diag_copy = df_diagnostics.dropna(subset=['Data_dt']).copy()
    if df_diag_copy.empty :
        st.caption(f"Debug Timeline: DataFrame vazio após dropna de 'Data_dt'.")
        return None
    diag_counts_monthly = df_diag_copy.groupby(pd.Grouper(key='Data_dt', freq='M')).size().reset_index(name='Contagem')
    diag_counts_monthly['Mês'] = diag_counts_monthly['Data_dt'].dt.strftime('%Y-%m')
    if diag_counts_monthly.empty:
        st.caption(f"Debug Timeline: Sem dados mensais para plotar.")
        return None
    fig = px.line(diag_counts_monthly, x='Mês', y='Contagem', title=title, markers=True, labels={'Mês':'Mês', 'Contagem':'Nº de Diagnósticos'}, line_shape="spline")
    fig.update_traces(line=dict(color='#2563eb'))
    fig.update_layout(font=dict(family="Segoe UI, sans-serif"))
    return fig

def create_avg_category_scores_chart(df_diagnostics, title="Média de Scores por Categoria (Todos Clientes)"):
    if df_diagnostics.empty:
        st.caption(f"Debug AvgCatScore: DataFrame de diagnósticos vazio. Shape: {df_diagnostics.shape if not df_diagnostics.empty else 'Vazio'}")
        return None
    media_cols = [col for col in df_diagnostics.columns if col.startswith("Media_Cat_")]
    if not media_cols:
        st.caption(f"Debug AvgCatScore: Nenhuma coluna 'Media_Cat_*' encontrada.")
        return None
    avg_scores_data = []
    for col in media_cols:
        numeric_scores = pd.to_numeric(df_diagnostics[col], errors='coerce')
        if not numeric_scores.isnull().all():
            avg_scores_data.append({'Categoria': col.replace("Media_Cat_", "").replace("_", " "), 'Média_Score': numeric_scores.mean()})
    if not avg_scores_data:
        st.caption(f"Debug AvgCatScore: Nenhum dado de score de categoria para agregar.")
        return None
    avg_scores = pd.DataFrame(avg_scores_data)
    if avg_scores.empty : return None
    avg_scores = avg_scores.sort_values(by="Média_Score", ascending=False)
    max_y_val = 5.5
    if not avg_scores.empty and 'Média_Score' in avg_scores.columns and avg_scores['Média_Score'].notna().any():
        max_y_val = max(5.5, avg_scores['Média_Score'].max() + 0.5)
    fig = px.bar(avg_scores, x='Categoria', y='Média_Score', title=title, color='Média_Score', color_continuous_scale=px.colors.sequential.Blues_r, labels={'Categoria':'Categoria', 'Média_Score':'Média do Score'})
    fig.update_layout(xaxis_tickangle=-45, font=dict(family="Segoe UI, sans-serif"), yaxis=dict(range=[0, max_y_val]))
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
admin_credenciais_csv = "admins.csv"; usuarios_csv = "usuarios.csv"; arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"; perguntas_csv = "perguntas_formulario.csv"; historico_csv = "historico_clientes.csv"
analises_perguntas_csv = "analises_perguntas.csv"; notificacoes_csv = "notificacoes.csv"; instrucoes_custom_path = "instrucoes_portal.md"
instrucoes_default_path = "instrucoes_portal_default.md"; sac_perguntas_respostas_csv = "sac_perguntas_respostas.csv"
sac_uso_feedback_csv = "sac_uso_feedback.csv"; pesquisa_satisfacao_perguntas_csv = "pesquisa_satisfacao_perguntas.csv"
pesquisa_satisfacao_respostas_csv = "pesquisa_satisfacao_respostas.csv"; LOGOS_DIR = "client_logos"

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None, "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {}, "sac_feedback_registrado": {}, "force_sidebar_rerun_after_notif_read_v19": False,
    "target_diag_data_for_expansion": None, "id_diagnostico_concluido_para_satisfacao": None,
    "respostas_pesquisa_satisfacao_atual": {}, "pesquisa_satisfacao_enviada": False,
}
for key, value in default_session_state.items():
    if key not in st.session_state: st.session_state[key] = value

# --- Funções Utilitárias ---
def sanitize_column_name(name): s = str(name).strip().replace(' ', '_'); s = re.sub(r'(?u)[^-\w.]', '', s); return s
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
        str_cols_map = {usuarios_csv: ['CNPJ'], usuarios_bloqueados_csv: ['CNPJ'], arquivo_csv: ['CNPJ', 'Data'], notificacoes_csv: ['CNPJ_Cliente', 'ID_Diagnostico_Relacionado'], sac_uso_feedback_csv: ['CNPJ_Cliente'], pesquisa_satisfacao_respostas_csv: ['CNPJ_Cliente', 'ID_Diagnostico_Cliente', 'ID_Pergunta_Satisfacao', 'Resposta_Valor']}
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
            try: df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)
            except (ValueError, TypeError): df_init = pd.read_csv(filepath, encoding='utf-8')
            except Exception as read_e: st.error(f"Erro crítico ao ler {filepath}: {read_e}."); return pd.DataFrame(columns=columns)
            made_changes = False; current_df_cols = df_init.columns.tolist()
            for col_idx, col_name in enumerate(columns):
                if col_name not in current_df_cols:
                    default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                    df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=default_val); made_changes = True
            if made_changes: df_init.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError:
        df_init = pd.DataFrame(columns=columns)
        if defaults:
            for col, default_val in defaults.items():
                if col in columns: df_init[col] = default_val
        df_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e: st.error(f"Erro fatal na inicializar_csv para {filepath}: {e}"); st.stop()

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"]); inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios, defaults={"JaVisualizouInstrucoes": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"}); inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos); inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False, "ID_Diagnostico_Relacionado": None})
    inicializar_csv(sac_perguntas_respostas_csv, colunas_base_sac_perguntas, defaults={"Categoria_SAC": "Geral", "DataCriacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    inicializar_csv(sac_uso_feedback_csv, colunas_base_sac_uso_feedback, defaults={"Feedback_Util": pd.NA})
    inicializar_csv(pesquisa_satisfacao_perguntas_csv, colunas_base_pesquisa_satisfacao_perguntas, defaults={"Ordem": 0, "Ativa": True, "Opcoes_Pergunta": None})
    inicializar_csv(pesquisa_satisfacao_respostas_csv, colunas_base_pesquisa_satisfacao_respostas)
except Exception as e_init: st.error(f"Falha crítica na inicialização de arquivos CSV: {e_init}."); st.stop()

def registrar_acao(cnpj, acao, desc):
    try: hist_df = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ':str})
    except (FileNotFoundError, pd.errors.EmptyDataError): hist_df = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    new_entry = {"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": str(cnpj), "Ação": acao, "Descrição": desc}
    hist_df = pd.concat([hist_df, pd.DataFrame([new_entry])], ignore_index=True); hist_df.to_csv(historico_csv, index=False, encoding='utf-8')

def update_user_data(cnpj, field, value):
    try:
        users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
        idx = users_df[users_df['CNPJ'] == str(cnpj)].index
        if not idx.empty:
            users_df.loc[idx, field] = value; users_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
            if 'user' in st.session_state and st.session_state.user and str(st.session_state.user.get('CNPJ')) == str(cnpj):
                if field in ["DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]: st.session_state.user[field] = int(value)
                elif field == "JaVisualizouInstrucoes": st.session_state.user[field] = str(value).lower() == "true"
                else: st.session_state.user[field] = value
            st.cache_data.clear(); return True
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
        for col, default in [("Categoria_SAC", "Geral"), ("DataCriacao", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))]:
            if col not in df.columns: df[col] = default
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame(columns=colunas_base_sac_perguntas)
@st.cache_data
def carregar_sac_uso_feedback():
    try:
        df = pd.read_csv(sac_uso_feedback_csv, encoding='utf-8', dtype={'CNPJ_Cliente': str})
        if 'Feedback_Util' in df.columns: df['Feedback_Util'] = df['Feedback_Util'].astype(str).str.lower().map({'true': True, 'false': False, 'nan': pd.NA, 'none': pd.NA, '': pd.NA}).astype('boolean')
        else: df['Feedback_Util'] = pd.Series(dtype='boolean')
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame(columns=colunas_base_sac_uso_feedback)
@st.cache_data
def carregar_perguntas_satisfacao(apenas_ativas=True):
    try:
        df = pd.read_csv(pesquisa_satisfacao_perguntas_csv, encoding='utf-8')
        if df.empty: return pd.DataFrame(columns=colunas_base_pesquisa_satisfacao_perguntas)
        for col, default in [('Ativa', True), ('Ordem', 0), ('Opcoes_Pergunta', None)]:
            if col not in df.columns: df[col] = default
        df['Ativa'] = df['Ativa'].fillna(True).astype(bool); df['Ordem'] = pd.to_numeric(df['Ordem'], errors='coerce').fillna(0).astype(int)
        if apenas_ativas: df = df[df['Ativa'] == True]
        return df.sort_values(by="Ordem", ascending=True)
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame(columns=colunas_base_pesquisa_satisfacao_perguntas)
@st.cache_data
def carregar_respostas_satisfacao(cnpj_cliente=None, id_diagnostico=None):
    try:
        df = pd.read_csv(pesquisa_satisfacao_respostas_csv, encoding='utf-8', dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Cliente': str, 'ID_Pergunta_Satisfacao': str, 'Resposta_Valor':str})
        if cnpj_cliente: df = df[df['CNPJ_Cliente'] == str(cnpj_cliente)]
        if id_diagnostico: df = df[df['ID_Diagnostico_Cliente'] == str(id_diagnostico)]
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError): return pd.DataFrame(columns=colunas_base_pesquisa_satisfacao_respostas)

def verificar_pesquisa_satisfacao_pendente(cnpj_cliente, id_diagnostico_cliente): return carregar_respostas_satisfacao(cnpj_cliente=cnpj_cliente, id_diagnostico=id_diagnostico_cliente).empty

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
            pdf = FPDF(); pdf.add_page()
            empresa_nome = user_data.get("Empresa", "N/D"); cnpj_pdf = user_data.get("CNPJ", "N/D")
            logo_path = find_client_logo_path(cnpj_pdf)
            if logo_path:
                try: current_y = pdf.get_y(); pdf.image(logo_path, x=10, y=current_y, h=20); pdf.set_y(current_y + 20 + 5)
                except Exception as e_logo_pdf: st.warning(f"PDF: Logo não pôde ser adicionado: {e_logo_pdf}")
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
                        if score >= 75: prazo = "15 dias"
                        elif score >= 40: prazo = "30 dias"
                        elif score >= 20: prazo = "45 dias"
                        elif score > 0: prazo = "60 dias"
                        if prazo != "N/A": gut_cards.append({"Tarefa": p_texto.replace(" [Matriz GUT]", ""),"Prazo": prazo, "Score": score})
                if gut_cards:
                    for card in sorted(gut_cards, key=lambda x: (int(x["Prazo"].split(" ")[0]), -x["Score"])): pdf.multi_cell(0,6,pdf_safe_text_output(f"Prazo: {card['Prazo']} - Tarefa: {card['Tarefa']} (Score GUT: {card['Score']})"))
                else: pdf.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile: pdf_path = tmpfile.name; pdf.output(pdf_path)
        return pdf_path
    except Exception as e: st.error(f"Erro crítico ao gerar PDF: {e}"); st.exception(e); return None

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): st.session_state.trigger_rerun_global = False; st.rerun()
if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v21")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.image("https://via.placeholder.com/200x80.png?text=Logo+do+Portal", width=200)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v21"):
        u_adm = st.text_input("Usuário", key="admin_u_v21"); p_adm = st.text_input("Senha", type="password", key="admin_p_v21")
        if st.form_submit_button("Entrar", use_container_width=True, icon="🔑"):
            try:
                df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                if not df_creds[(df_creds["Usuario"] == u_adm) & (df_creds["Senha"] == p_adm)].empty:
                    st.session_state.admin_logado = True; st.toast("Login de admin bem-sucedido!", icon="🎉"); st.rerun()
                else: st.error("Usuário/senha admin inválidos.")
            except Exception as e: st.error(f"Erro login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.image("https://via.placeholder.com/200x80.png?text=Logo+do+Portal", width=200)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_v21"):
        c_cli = st.text_input("CNPJ", key="cli_c_v21", value=st.session_state.get("last_cnpj_input",""))
        s_cli = st.text_input("Senha", type="password", key="cli_s_v21")
        if st.form_submit_button("Entrar", use_container_width=True, icon="👤"):
            st.session_state.last_cnpj_input = c_cli
            try:
                users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                for col, default, dtype_func_str in [("JaVisualizouInstrucoes", "False", "bool"), ("DiagnosticosDisponiveis", 1, "int"), ("TotalDiagnosticosRealizados", 0, "int")]:
                    if col not in users_df.columns: users_df[col] = default
                    if dtype_func_str == "int": users_df[col] = pd.to_numeric(users_df[col], errors='coerce').fillna(default).astype(int)
                    elif dtype_func_str == "bool": users_df[col] = users_df[col].astype(str).str.lower().map({'true': True, 'false': False, 'nan':False,'none':False,'':False}).fillna(default.lower()=='true' if isinstance(default,str) else False)
                blocked_df = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                if c_cli in blocked_df["CNPJ"].values: st.error("CNPJ bloqueado."); st.stop()
                match = users_df[(users_df["CNPJ"] == c_cli) & (users_df["Senha"] == s_cli)]
                if match.empty: st.error("CNPJ/senha inválidos."); st.stop()
                st.session_state.cliente_logado = True; st.session_state.cnpj = c_cli; st.session_state.user = match.iloc[0].to_dict()
                st.session_state.user["JaVisualizouInstrucoes"] = bool(st.session_state.user.get("JaVisualizouInstrucoes", False))
                st.session_state.user["DiagnosticosDisponiveis"] = int(st.session_state.user.get("DiagnosticosDisponiveis", 1))
                st.session_state.user["TotalDiagnosticosRealizados"] = int(st.session_state.user.get("TotalDiagnosticosRealizados", 0))
                st.session_state.inicio_sessao_cliente = time.time(); registrar_acao(c_cli, "Login", "Usuário logou.")
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
        logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
        if logo_cliente_path: st.image(logo_cliente_path, width=100)
        st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
        st.write(f"**CNPJ:** {st.session_state.cnpj}")
        st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
        st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")
        total_slots = st.session_state.user.get('DiagnosticosDisponiveis', 0); realizados = st.session_state.user.get('TotalDiagnosticosRealizados', 0); restantes = max(0, total_slots - realizados)
        st.markdown(f"**Diagnósticos Contratados (Slots):** `{total_slots}`\n\n**Diagnósticos Realizados:** `{realizados}`\n\n**Diagnósticos Restantes:** `{restantes}`")
    notificacoes_nao_lidas_count = 0
    if os.path.exists(notificacoes_csv):
        try:
            df_notif_check = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str})
            if not df_notif_check.empty and 'Lida' in df_notif_check.columns:
                df_notif_check['Lida'] = df_notif_check['Lida'].astype(str).str.lower().map({'true': True, 'false': False, 'nan': False, '': False}).fillna(False)
                notificacoes_nao_lidas_count = len(df_notif_check[(df_notif_check["CNPJ_Cliente"] == st.session_state.cnpj) & (df_notif_check["Lida"] == False)])
        except: pass
    notificacoes_label = "🔔 Notificações" + (f" ({notificacoes_nao_lidas_count} Nova(s))" if notificacoes_nao_lidas_count > 0 else "")
    menu_options_cli_map_full = {"Instruções": "📖 Instruções", "Novo Diagnóstico": "📋 Novo Diagnóstico", "Painel Principal": "🏠 Painel Principal", "Notificações": notificacoes_label, "SAC": "❓ SAC - Perguntas Frequentes"}
    menu_options_cli_map = menu_options_cli_map_full.copy()
    if not st.session_state.user.get("JaVisualizouInstrucoes", False): menu_options_cli_map = {"Instruções": "📖 Instruções"}; st.session_state.cliente_page = "Instruções"
    else:
        if not (st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)) and "Novo Diagnóstico" in menu_options_cli_map:
            if st.session_state.cliente_page == "Novo Diagnóstico": st.session_state.cliente_page = "Painel Principal"
            del menu_options_cli_map["Novo Diagnóstico"]
    menu_options_cli_display = list(menu_options_cli_map.values())
    if st.session_state.cliente_page not in menu_options_cli_map.keys(): st.session_state.cliente_page = "Instruções" if not st.session_state.user.get("JaVisualizouInstrucoes", False) else "Painel Principal"
    default_display_option = menu_options_cli_map.get(st.session_state.cliente_page)
    current_idx_cli = 0
    if default_display_option and default_display_option in menu_options_cli_display: current_idx_cli = menu_options_cli_display.index(default_display_option)
    elif menu_options_cli_display:
        current_idx_cli = 0
        try: st.session_state.cliente_page = [k for k,v in menu_options_cli_map.items() if v == menu_options_cli_display[0]][0]
        except IndexError: st.session_state.cliente_page = "Painel Principal" if st.session_state.user.get("JaVisualizouInstrucoes", False) else "Instruções"
    selected_page_cli_raw = st.sidebar.radio("Menu Cliente", menu_options_cli_display, index=current_idx_cli, key="cli_menu_v21_radio")
    selected_page_cli_clean = ""
    for key_page, val_page_display in menu_options_cli_map.items():
        if val_page_display == selected_page_cli_raw: selected_page_cli_clean = key_page; break
    if selected_page_cli_clean and selected_page_cli_clean != st.session_state.cliente_page :
        st.session_state.cliente_page = selected_page_cli_clean; st.rerun()
    if st.sidebar.button("Sair do Portal Cliente", icon="⬅️", key="logout_cliente_v21_btn", use_container_width=True):
        for key_item in list(st.session_state.keys()):
            if key_item not in ['admin_logado', 'last_cnpj_input']: del st.session_state[key_item]
        for key_d, value_d in default_session_state.items():
            if key_d not in ['admin_logado', 'last_cnpj_input']: st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False; st.toast("Logout realizado.", icon="👋"); st.rerun()

    if st.session_state.cliente_page == "Instruções":
        st.subheader(menu_options_cli_map_full["Instruções"])
        instrucoes_content_md = ("# Bem-vindo ao Portal de Diagnóstico!\n\nSiga as instruções para completar seu diagnóstico.\n\nEm caso de dúvidas, entre em contato com o administrador.")
        try:
            if os.path.exists(instrucoes_custom_path):
                with open(instrucoes_custom_path, "r", encoding="utf-8") as f: instrucoes_content_md = f.read()
            elif os.path.exists(instrucoes_default_path):
                with open(instrucoes_default_path, "r", encoding="utf-8") as f: instrucoes_content_md = f.read()
                st.caption("Exibindo instruções padrão. O administrador pode personalizar este texto.")
        except Exception as e_instr: st.warning(f"Erro ao carregar instruções: {e_instr}")
        st.markdown(instrucoes_content_md, unsafe_allow_html=True)
        if st.button("Entendi, prosseguir", key="btn_instrucoes_v21_btn", icon="👍"):
            update_user_data(st.session_state.cnpj, "JaVisualizouInstrucoes", "True")
            if st.session_state.user: st.session_state.user["JaVisualizouInstrucoes"] = True
            pode_fazer_novo_inst = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            st.session_state.cliente_page = "Novo Diagnóstico" if pode_fazer_novo_inst else "Painel Principal"
            st.rerun()

    elif st.session_state.cliente_page == "SAC":
        st.subheader(menu_options_cli_map_full["SAC"])
        df_sac_qa = carregar_sac_perguntas_respostas()
        if df_sac_qa.empty: st.info("Nenhuma pergunta frequente cadastrada no momento.")
        else:
            df_sac_qa_sorted = df_sac_qa.sort_values(by=["Categoria_SAC", "Pergunta_SAC"])
            categorias_sac = df_sac_qa_sorted["Categoria_SAC"].unique()
            search_term_sac = st.text_input("🔎 Procurar nas Perguntas Frequentes:", key="search_sac_cliente_v21")
            if search_term_sac:
                df_sac_qa_sorted = df_sac_qa_sorted[df_sac_qa_sorted["Pergunta_SAC"].str.contains(search_term_sac, case=False, na=False) | df_sac_qa_sorted["Resposta_SAC"].str.contains(search_term_sac, case=False, na=False) | df_sac_qa_sorted["Categoria_SAC"].str.contains(search_term_sac, case=False, na=False)]
                categorias_sac = df_sac_qa_sorted["Categoria_SAC"].unique()
            if df_sac_qa_sorted.empty and search_term_sac: st.info(f"Nenhuma pergunta encontrada para '{search_term_sac}'.")
            for categoria in categorias_sac:
                st.markdown(f"#### {categoria}")
                for idx_sac, row_sac in df_sac_qa_sorted[df_sac_qa_sorted["Categoria_SAC"] == categoria].iterrows():
                    with st.expander(f"{row_sac['Pergunta_SAC']}"):
                        st.markdown(row_sac['Resposta_SAC'], unsafe_allow_html=True)
                        feedback_key_base = f"sac_feedback_{row_sac['ID_SAC_Pergunta']}_v21"; feedback_dado = st.session_state.sac_feedback_registrado.get(row_sac['ID_SAC_Pergunta'])
                        cols_feedback = st.columns([1,1,8])
                        if cols_feedback[0].button("👍 Útil", key=f"{feedback_key_base}_util", type="secondary" if feedback_dado != "util" else "primary", use_container_width=True):
                            try:
                                df_feedback_sac = carregar_sac_uso_feedback(); novo_fb_sac = pd.DataFrame([{"ID_Uso_SAC": str(uuid.uuid4()), "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ_Cliente": st.session_state.cnpj, "ID_SAC_Pergunta": row_sac['ID_SAC_Pergunta'], "Feedback_Util": True}])
                                df_feedback_sac = pd.concat([df_feedback_sac, novo_fb_sac], ignore_index=True); df_feedback_sac.to_csv(sac_uso_feedback_csv, index=False, encoding='utf-8'); st.session_state.sac_feedback_registrado[row_sac['ID_SAC_Pergunta']] = "util"; st.toast("Obrigado pelo feedback!", icon="😊"); st.cache_data.clear(); st.rerun()
                            except Exception as e_fb_sac: st.error(f"Erro ao registrar feedback: {e_fb_sac}")
                        if cols_feedback[1].button("👎 Não útil", key=f"{feedback_key_base}_nao_util", type="secondary" if feedback_dado != "nao_util" else "primary", use_container_width=True):
                            try:
                                df_feedback_sac = carregar_sac_uso_feedback(); novo_fb_sac = pd.DataFrame([{"ID_Uso_SAC": str(uuid.uuid4()), "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ_Cliente": st.session_state.cnpj, "ID_SAC_Pergunta": row_sac['ID_SAC_Pergunta'], "Feedback_Util": False}])
                                df_feedback_sac = pd.concat([df_feedback_sac, novo_fb_sac], ignore_index=True); df_feedback_sac.to_csv(sac_uso_feedback_csv, index=False, encoding='utf-8'); st.session_state.sac_feedback_registrado[row_sac['ID_SAC_Pergunta']] = "nao_util"; st.toast("Feedback registrado. Vamos melhorar!", icon="🛠️"); st.cache_data.clear(); st.rerun()
                            except Exception as e_fb_sac: st.error(f"Erro ao registrar feedback: {e_fb_sac}")
                        if feedback_dado: cols_feedback[2].caption(f"Feedback ('{feedback_dado.replace('_', ' ').capitalize()}') registrado.")
                st.markdown("---")

    elif st.session_state.cliente_page == "Notificações":
        st.subheader(menu_options_cli_map_full["Notificações"].split(" (")[0])
        ids_para_marcar_como_lidas_on_display = []
        try:
            df_notificacoes_todas = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Relacionado': str})
            if not df_notificacoes_todas.empty and 'Lida' in df_notificacoes_todas.columns: df_notificacoes_todas['Lida'] = df_notificacoes_todas['Lida'].astype(str).str.lower().map({'true': True, 'false': False, '': False, 'nan': False}).fillna(False)
            else: df_notificacoes_todas = pd.DataFrame(columns=colunas_base_notificacoes)
            if 'ID_Diagnostico_Relacionado' not in df_notificacoes_todas.columns: df_notificacoes_todas['ID_Diagnostico_Relacionado'] = None
            minhas_notificacoes = df_notificacoes_todas[df_notificacoes_todas["CNPJ_Cliente"] == st.session_state.cnpj].sort_values(by="Timestamp", ascending=False)
            if minhas_notificacoes.empty: st.info("Você não tem nenhuma notificação no momento.")
            else:
                st.caption("As notificações novas são marcadas como lidas ao serem exibidas nesta página.")
                for idx_notif, row_notif in minhas_notificacoes.iterrows():
                    cor_borda = "#2563eb" if not row_notif["Lida"] else "#adb5bd"; icon_lida = "✉️" if not row_notif["Lida"] else "📨"; status_text = "Status: Nova" if not row_notif["Lida"] else "Status: Lida"
                    st.markdown(f"""<div class="custom-card" style="border-left: 5px solid {cor_borda}; margin-bottom: 10px;"><p style="font-size: 0.8em; color: #6b7280;">{icon_lida} {row_notif["Timestamp"]} | <b>{status_text}</b></p><p>{row_notif["Mensagem"]}</p></div>""", unsafe_allow_html=True)
                    diag_id_relacionado = row_notif.get("ID_Diagnostico_Relacionado")
                    if pd.notna(diag_id_relacionado) and str(diag_id_relacionado).strip():
                        if st.button("Ver Detalhes no Painel", key=f"ver_det_notif_{row_notif['ID_Notificacao']}_{idx_notif}_final_v21", help="Ir para o diagnóstico mencionado"):
                            st.session_state.target_diag_data_for_expansion = str(diag_id_relacionado); st.session_state.cliente_page = "Painel Principal"; st.rerun()
                    if not row_notif["Lida"]: ids_para_marcar_como_lidas_on_display.append(row_notif["ID_Notificacao"])
                if ids_para_marcar_como_lidas_on_display:
                    indices_para_atualizar = df_notificacoes_todas[df_notificacoes_todas["ID_Notificacao"].isin(ids_para_marcar_como_lidas_on_display)].index
                    df_notificacoes_todas.loc[indices_para_atualizar, "Lida"] = True; df_notificacoes_todas.to_csv(notificacoes_csv, index=False, encoding='utf-8'); st.session_state['force_sidebar_rerun_after_notif_read_v19'] = True; st.cache_data.clear()
        except (FileNotFoundError, pd.errors.EmptyDataError): st.info("Você não tem nenhuma notificação no momento.")
        except Exception as e_notif_display: st.error(f"Erro ao carregar suas notificações: {e_notif_display}")
        if st.session_state.get('force_sidebar_rerun_after_notif_read_v19'): del st.session_state['force_sidebar_rerun_after_notif_read_v19']; st.rerun()

    elif st.session_state.cliente_page == "Painel Principal":
        st.subheader(menu_options_cli_map_full["Painel Principal"])
        target_diag_to_expand = st.session_state.pop("target_diag_data_for_expansion", None)
        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu último diagnóstico foi enviado e processado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                try:
                    with open(st.session_state.pdf_gerado_path, "rb") as f_pdf: st.download_button(label="Baixar PDF do Diagnóstico", data=f_pdf, file_name=st.session_state.pdf_gerado_filename, mime="application/pdf", key="dl_novo_diag_painel_v21_dlbtn", icon="📄")
                    st.session_state.pdf_gerado_path = None; st.session_state.pdf_gerado_filename = None
                except Exception as e_pdf_dl: st.warning(f"Erro ao disponibilizar PDF: {e_pdf_dl}")
            if st.session_state.id_diagnostico_concluido_para_satisfacao and not st.session_state.pesquisa_satisfacao_enviada:
                id_diag_atual_s = st.session_state.id_diagnostico_concluido_para_satisfacao
                if verificar_pesquisa_satisfacao_pendente(st.session_state.cnpj, id_diag_atual_s):
                    st.markdown("---"); st.subheader("⭐ Pesquisa de Satisfação Rápida"); st.caption("Sua opinião é muito importante para nós!")
                    perguntas_s_df = carregar_perguntas_satisfacao(apenas_ativas=True)
                    if not perguntas_s_df.empty:
                         with st.form(key="form_pesquisa_s_cliente_final_submit_panel_v21_form"):
                            for idx_ps_form, row_ps_form in perguntas_s_df.iterrows():
                                p_id, p_txt, p_tipo, p_op_str = row_ps_form["ID_Pergunta_Satisfacao"], row_ps_form["Texto_Pergunta"], row_ps_form["Tipo_Pergunta"], row_ps_form.get("Opcoes_Pergunta")
                                widget_key_form = f"s_{p_id}_final_panel_form_{idx_ps_form}_v21"
                                st.markdown(f"**{p_txt}**")
                                if p_tipo == "escala_1_5": st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.radio(" ", list(range(1, 6)), key=widget_key_form, horizontal=True, label_visibility="collapsed")
                                elif p_tipo == "texto_aberto": st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.text_area(" ", key=widget_key_form, label_visibility="collapsed")
                                elif p_tipo == "sim_nao": st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.radio(" ", ["Sim", "Não"], key=widget_key_form, horizontal=True, label_visibility="collapsed")
                                elif p_tipo == "multipla_escolha_unica":
                                    opcoes_ps_list = []
                                    if pd.notna(p_op_str):
                                        try: opcoes_ps_list = json.loads(p_op_str).get("opcoes", [])
                                        except: st.warning(f"Opções mal formatadas: {p_txt}")
                                    if opcoes_ps_list: st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.radio(" ", opcoes_ps_list, key=widget_key_form, label_visibility="collapsed")
                                    else: st.caption(" (Opções não configuradas)")
                                st.write("")
                            if st.form_submit_button("Enviar Feedback de Satisfação", use_container_width=True, icon="💖"):
                                respostas_finais_s = [{"ID_Resposta_Satisfacao": str(uuid.uuid4()), "ID_Diagnostico_Cliente": id_diag_atual_s, "ID_Pergunta_Satisfacao": pid, "CNPJ_Cliente": st.session_state.cnpj, "Timestamp_Resposta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Resposta_Valor": str(rval)} for pid, rval in st.session_state.respostas_pesquisa_satisfacao_atual.items() if rval is not None and str(rval).strip() != ""]
                                if respostas_finais_s:
                                    df_respostas_s_todas = carregar_respostas_satisfacao(); df_novas_s = pd.DataFrame(respostas_finais_s)
                                    df_respostas_s_upd = pd.concat([df_respostas_s_todas, df_novas_s], ignore_index=True)
                                    df_respostas_s_upd.to_csv(pesquisa_satisfacao_respostas_csv, index=False, encoding='utf-8')
                                    st.cache_data.clear(); st.session_state.pesquisa_satisfacao_enviada = True; st.session_state.respostas_pesquisa_satisfacao_atual = {}; st.success("Obrigado pelo seu feedback!"); time.sleep(1); st.rerun()
                                else: st.warning("Nenhuma resposta fornecida.")
                    else: st.info("Pesquisa de satisfação sem perguntas ativas.")
                elif not st.session_state.pesquisa_satisfacao_enviada and st.session_state.id_diagnostico_concluido_para_satisfacao : st.success("Feedback de satisfação já recebido para este diagnóstico. Obrigado!")
            st.session_state.diagnostico_enviado_sucesso = False
        with st.expander("ℹ️ Informações Importantes", expanded=False): st.markdown("- Visualize seus diagnósticos anteriores e sua evolução.\n- Acompanhe seu plano de ação no Kanban.\n- Para um novo diagnóstico (se liberado), selecione 'Novo Diagnóstico' no menu ao lado.")
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
            latest_diag_data_row = df_cliente_diags.iloc[0]; latest_diag_data = latest_diag_data_row.to_dict()
            st.markdown("#### 📊 Visão Geral do Último Diagnóstico")
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown('<div class="dashboard-item"><h5>Scores por Categoria</h5>', unsafe_allow_html=True)
                medias_cat_latest = { k.replace("Media_Cat_", "").replace("_", " "): v for k, v in latest_diag_data.items() if k.startswith("Media_Cat_") and pd.notna(v) }
                if medias_cat_latest: fig_radar = create_radar_chart(medias_cat_latest, title=""); st.plotly_chart(fig_radar, use_container_width=True) if fig_radar else st.caption("Radar indisponível (verifique se há pelo menos 3 categorias com dados válidos).")
                else: st.caption("Sem dados de média por categoria para o último diagnóstico.")
                st.markdown('</div>', unsafe_allow_html=True)
            with col_g2:
                st.markdown('<div class="dashboard-item"><h5>Top Prioridades (Matriz GUT)</h5>', unsafe_allow_html=True)
                gut_data_list_cli = []
                for pergunta_key, resp_val_str in latest_diag_data.items():
                    if isinstance(pergunta_key, str) and "[Matriz GUT]" in pergunta_key and pd.notna(resp_val_str) and isinstance(resp_val_str, str):
                        try:
                            gut_data = json.loads(resp_val_str.replace("'", "\""))
                            g, u, t_val = int(gut_data.get("G",0)), int(gut_data.get("U",0)), int(gut_data.get("T",0))
                            score = g * u * t_val
                            if score > 0: gut_data_list_cli.append({"Tarefa": pergunta_key.replace(" [Matriz GUT]", ""), "Score": score})
                        except: pass
                if gut_data_list_cli: fig_gut_bar = create_gut_barchart(gut_data_list_cli, title=""); st.plotly_chart(fig_gut_bar, use_container_width=True) if fig_gut_bar else st.caption("Gráfico GUT indisponível.")
                else: st.caption("Nenhuma prioridade GUT identificada no último diagnóstico.")
                st.markdown('</div>', unsafe_allow_html=True)
            st.divider()
            st.markdown("#### 📁 Diagnósticos Anteriores")
            if df_cliente_diags.empty: st.info("Nenhum diagnóstico anterior.")
            else:
                try:
                    perguntas_df_painel = pd.read_csv(perguntas_csv, encoding='utf-8')
                    if "Categoria" not in perguntas_df_painel.columns: perguntas_df_painel["Categoria"] = "Geral"
                except FileNotFoundError: st.error(f"Arquivo '{perguntas_csv}' não encontrado."); perguntas_df_painel = pd.DataFrame()
                analises_df_painel = carregar_analises_perguntas()
                for idx_row_diag, row_diag_data_series in df_cliente_diags.iterrows():
                    row_diag_data = row_diag_data_series.to_dict()
                    expand_this_diag = (str(row_diag_data.get('Data')) == str(target_diag_to_expand))
                    with st.expander(f"📅 {row_diag_data.get('Data','N/D')} - {row_diag_data.get('Empresa','N/D')}", expanded=expand_this_diag):
                        st.markdown('<div class="custom-card" style="padding-top: 10px; padding-bottom: 10px;">', unsafe_allow_html=True)
                        cols_metricas = st.columns(2); mg = row_diag_data.get('Média Geral'); gutm = row_diag_data.get('GUT Média')
                        cols_metricas[0].metric("Média Geral", f"{mg:.2f}" if pd.notna(mg) else "N/A")
                        cols_metricas[1].metric("GUT Média (G*U*T)", f"{gutm:.2f}" if pd.notna(gutm) else "N/A")
                        st.write(f"**Resumo (Cliente):** {row_diag_data.get('Diagnóstico', 'N/P')}")
                        st.markdown("**Respostas e Análises Detalhadas:**")
                        if not perguntas_df_painel.empty:
                            for cat_loop in sorted(perguntas_df_painel["Categoria"].unique()):
                                st.markdown(f"##### Categoria: {cat_loop}")
                                for _, p_row_loop in perguntas_df_painel[perguntas_df_painel["Categoria"] == cat_loop].iterrows():
                                    p_texto_loop = p_row_loop["Pergunta"]; resp_loop = row_diag_data.get(p_texto_loop, "N/R")
                                    st.markdown(f"**{p_texto_loop.split('[')[0].strip()}:**\n> {resp_loop}")
                                    valor_para_analise = resp_loop
                                    if "[Matriz GUT]" in p_texto_loop:
                                        g_val,u_val,t_val_loop,score_gut_loop=0,0,0,0 # Renomeada t_val para t_val_loop
                                        if isinstance(resp_loop, dict): g_val,u_val,t_val_loop=int(resp_loop.get("G",0)),int(resp_loop.get("U",0)),int(resp_loop.get("T",0))
                                        elif isinstance(resp_loop, str) and resp_loop.strip().startswith("{"):
                                            try: data_gut_loop=json.loads(resp_loop.replace("'",'"')); g_val,u_val,t_val_loop=int(data_gut_loop.get("G",0)),int(data_gut_loop.get("U",0)),int(data_gut_loop.get("T",0))
                                            except: pass
                                        score_gut_loop = g_val*u_val*t_val_loop; valor_para_analise = score_gut_loop
                                        st.caption(f"G={g_val}, U={u_val}, T={t_val_loop} (Score GUT: {score_gut_loop})")
                                    analise_texto_painel = obter_analise_para_resposta(p_texto_loop, valor_para_analise, analises_df_painel)
                                    if analise_texto_painel: st.markdown(f"<div class='analise-pergunta-cliente'><b>Análise Consultor:</b> {analise_texto_painel}</div>", unsafe_allow_html=True)
                                st.markdown("---")
                        else: st.caption("Estrutura de perguntas não carregada.")
                        analise_cli_val_cv_painel = row_diag_data.get("Análise do Cliente", "")
                        analise_cli_cv_input = st.text_area("🧠 Minha Análise sobre este Diagnóstico:", value=analise_cli_val_cv_painel, key=f"analise_cv_painel_v21_{idx_row_diag}")
                        if st.button("Salvar Minha Análise", key=f"salvar_analise_cv_painel_v21_{idx_row_diag}", icon="💾"):
                            # ... (lógica de salvar análise do cliente)
                            pass
                        com_admin_val_cv_painel = row_diag_data.get("Comentarios_Admin", "")
                        if com_admin_val_cv_painel and not pd.isna(com_admin_val_cv_painel) and str(com_admin_val_cv_painel).strip():
                            st.markdown("##### Comentários do Consultor:"); st.info(f"{com_admin_val_cv_painel}")
                            if expand_this_diag: st.markdown("<small><i>(Você foi direcionado para este comentário)</i></small>", unsafe_allow_html=True)
                        # else: st.caption("Nenhum comentário do consultor para este diagnóstico.") # Removido para não poluir
                        if st.button("Baixar PDF deste Diagnóstico", key=f"dl_pdf_antigo_v21_{idx_row_diag}", icon="📄"):
                            # ... (lógica de gerar e baixar PDF antigo)
                            pass
                        st.markdown('</div>', unsafe_allow_html=True)
            st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)") # ... (Kanban)
            st.divider(); st.subheader("📈 Comparativo de Evolução das Médias") # ... (Evolução)
            st.divider(); st.subheader("📊 Comparação Detalhada Entre Dois Diagnósticos") # ... (Comparação)
        else: st.info("Nenhum diagnóstico anterior encontrado para este cliente.")

    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.subheader("📋 Novo Diagnóstico")
        if st.session_state.diagnostico_enviado_sucesso: st.session_state.cliente_page = "Painel Principal"; st.rerun()
        try: perguntas_df_formulario = pd.read_csv(perguntas_csv, encoding='utf-8')
        except Exception as e: st.error(f"Erro ao carregar perguntas: {e}"); st.stop()
        if perguntas_df_formulario.empty: st.warning("Nenhuma pergunta de diagnóstico cadastrada."); st.stop()
        if "Categoria" not in perguntas_df_formulario.columns: perguntas_df_formulario["Categoria"] = "Geral"
        total_perguntas_form = len(perguntas_df_formulario)
        if 'progresso_diagnostico_contagem' not in st.session_state or st.session_state.progresso_diagnostico_contagem[1] != total_perguntas_form:
             st.session_state.progresso_diagnostico_contagem = (st.session_state.get('progresso_diagnostico_contagem', (0,0))[0], total_perguntas_form)
        progresso_ph_novo = st.empty()
        def calcular_e_mostrar_progresso_novo():
            respondidas_novo = 0; total_q_novo = st.session_state.progresso_diagnostico_contagem[1]
            if total_q_novo == 0: st.session_state.progresso_diagnostico_percentual = 0; progresso_ph_novo.info(f"📊 Progresso: 0 de 0 (0%)"); return
            for _, p_row_prog_novo in perguntas_df_formulario.iterrows():
                p_texto_prog_novo = p_row_prog_novo["Pergunta"]; resp_prog_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_prog_novo)
                if resp_prog_novo is not None:
                    if "[Matriz GUT]" in p_texto_prog_novo:
                        if isinstance(resp_prog_novo, dict) and any(pd.to_numeric(v, errors='coerce') > 0 for v in resp_prog_novo.values()): respondidas_novo +=1
                    elif "Escala" in p_texto_prog_novo:
                        if resp_prog_novo != "Selecione": respondidas_novo +=1
                    elif isinstance(resp_prog_novo, str):
                        if resp_prog_novo.strip() : respondidas_novo +=1
                    elif isinstance(resp_prog_novo, (int,float)) and pd.notna(resp_prog_novo): respondidas_novo +=1
            st.session_state.progresso_diagnostico_contagem = (respondidas_novo, total_q_novo)
            st.session_state.progresso_diagnostico_percentual = round((respondidas_novo / total_q_novo) * 100) if total_q_novo > 0 else 0
            progresso_ph_novo.progress(st.session_state.progresso_diagnostico_percentual / 100, text=f"📊 Progresso: {respondidas_novo} de {total_q_novo} ({st.session_state.progresso_diagnostico_percentual}%)")
        def on_change_resposta_novo(pergunta_txt_key_novo, widget_st_key_novo, tipo_pergunta_onchange_novo):
            valor_widget_novo = st.session_state.get(widget_st_key_novo)
            current_gut_novo = st.session_state.respostas_atuais_diagnostico.get(pergunta_txt_key_novo, {"G":0,"U":0,"T":0}) # Garantir que é um dict
            if isinstance(current_gut_novo, str): current_gut_novo = {"G":0,"U":0,"T":0} # Correção se vier como string
            if tipo_pergunta_onchange_novo == "GUT_G": current_gut_novo["G"] = valor_widget_novo
            elif tipo_pergunta_onchange_novo == "GUT_U": current_gut_novo["U"] = valor_widget_novo
            elif tipo_pergunta_onchange_novo == "GUT_T": current_gut_novo["T"] = valor_widget_novo
            else: st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = valor_widget_novo; calcular_e_mostrar_progresso_novo(); return
            st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = current_gut_novo
            st.session_state.feedbacks_respostas[pergunta_txt_key_novo] = "✓"; calcular_e_mostrar_progresso_novo()
        calcular_e_mostrar_progresso_novo()
        for categoria_novo in sorted(perguntas_df_formulario["Categoria"].unique()):
            st.markdown(f"#### Categoria: {categoria_novo}")
            for idx_novo, row_q_novo in perguntas_df_formulario[perguntas_df_formulario["Categoria"] == categoria_novo].iterrows():
                p_texto_novo = str(row_q_novo["Pergunta"]); w_key_novo = f"q_v21_{st.session_state.id_formulario_atual}_{idx_novo}"
                with st.container():
                    cols_q_feedback = st.columns([0.95, 0.05])
                    with cols_q_feedback[0]:
                        default_val_diag = st.session_state.respostas_atuais_diagnostico.get(p_texto_novo)
                        if "[Matriz GUT]" in p_texto_novo:
                            st.markdown(f"**{p_texto_novo.replace(' [Matriz GUT]', '')}**"); cols_gut_w_novo = st.columns(3)
                            gut_vals_novo = default_val_diag if isinstance(default_val_diag, dict) else {"G":0,"U":0,"T":0}
                            key_g_n, key_u_n, key_t_n = f"{w_key_novo}_G", f"{w_key_novo}_U", f"{w_key_novo}_T"
                            cols_gut_w_novo[0].slider("Gravidade (0-5)",0,5,value=int(gut_vals_novo.get("G",0)), key=key_g_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_g_n, "GUT_G"))
                            cols_gut_w_novo[1].slider("Urgência (0-5)",0,5,value=int(gut_vals_novo.get("U",0)), key=key_u_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_u_n, "GUT_U"))
                            cols_gut_w_novo[2].slider("Tendência (0-5)",0,5,value=int(gut_vals_novo.get("T",0)), key=key_t_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_t_n, "GUT_T"))
                        elif "Pontuação (0-5)" in p_texto_novo: st.slider(p_texto_novo,0,5,value=int(default_val_diag if pd.notna(default_val_diag) else 0), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Slider05"))
                        elif "Pontuação (0-10)" in p_texto_novo: st.slider(p_texto_novo,0,10,value=int(default_val_diag if pd.notna(default_val_diag) else 0), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Slider010"))
                        elif "Texto Aberto" in p_texto_novo: st.text_area(p_texto_novo,value=str(default_val_diag if pd.notna(default_val_diag) else ""), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Texto"))
                        elif "Escala" in p_texto_novo:
                            opts_novo = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"]; curr_val_novo = default_val_diag if default_val_diag in opts_novo else "Selecione"
                            st.selectbox(p_texto_novo, opts_novo, index=opts_novo.index(curr_val_novo), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Escala"))
                        else: st.slider(p_texto_novo,0,10,value=int(default_val_diag if pd.notna(default_val_diag) else 0), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "SliderDefault")) # Fallback
                    with cols_q_feedback[1]:
                        if st.session_state.feedbacks_respostas.get(p_texto_novo): st.markdown(f'<div class="feedback-saved" style="text-align: center; padding-top: 25px;">{st.session_state.feedbacks_respostas[p_texto_novo]}</div>', unsafe_allow_html=True)
                st.divider()
        key_obs_cli_n = f"obs_cli_diag_v21_{st.session_state.id_formulario_atual}"; key_res_cli_n = f"diag_resumo_diag_v21_{st.session_state.id_formulario_atual}"
        st.text_area("Sua Análise/Observações (opcional):", value=st.session_state.respostas_atuais_diagnostico.get("__obs_cliente__", ""), key=key_obs_cli_n, on_change=on_change_resposta_novo, args=("__obs_cliente__", key_obs_cli_n, "ObsCliente"))
        st.text_area("✍️ Resumo/principais insights (para PDF):", value=st.session_state.respostas_atuais_diagnostico.get("__resumo_cliente__", ""), key=key_res_cli_n, on_change=on_change_resposta_novo, args=("__resumo_cliente__", key_res_cli_n, "ResumoCliente"))
        if st.button("Concluir e Enviar Diagnóstico", key="enviar_diag_final_cliente_v21_submit_btn_ND_actual", icon="✔️", use_container_width=True):
            with st.spinner("Processando e salvando seu diagnóstico..."):
                respostas_finais_envio_novo = st.session_state.respostas_atuais_diagnostico.copy()
                cont_resp_n, total_para_resp_n = st.session_state.progresso_diagnostico_contagem
                if cont_resp_n < total_para_resp_n: st.warning("Por favor, responda todas as perguntas.")
                elif not respostas_finais_envio_novo.get("__resumo_cliente__","").strip(): st.error("O campo 'Resumo/principais insights' é obrigatório.")
                else:
                    soma_gut_n, count_gut_n = 0,0; respostas_csv_n = {}
                    for p_n,r_n in respostas_finais_envio_novo.items():
                        if p_n.startswith("__"): continue
                        if "[Matriz GUT]" in p_n and isinstance(r_n, dict):
                            respostas_csv_n[p_n] = json.dumps(r_n); g,u,t_val = int(r_n.get("G",0)), int(r_n.get("U",0)), int(r_n.get("T",0)); soma_gut_n += (g*u*t_val); count_gut_n +=1
                        else: respostas_csv_n[p_n] = r_n
                    gut_media_n = round(soma_gut_n/count_gut_n,2) if count_gut_n > 0 else 0.0
                    num_resp_n_calc = []
                    for k_n,v_n in respostas_finais_envio_novo.items():
                        if not k_n.startswith("__") and ("[Matriz GUT]" not in k_n) and ("Pontuação" in k_n or "Escala" in k_n):
                            val_num_calc = pd.to_numeric(v_n, errors='coerce') # Tenta converter, incluindo mapeamento de Escala se necessário
                            if "Escala" in k_n and isinstance(v_n, str): # Mapear escala para número
                                map_escala_num_calc = {"Muito Baixo": 1, "Baixo": 2, "Médio": 3, "Alto": 4, "Muito Alto": 5}
                                val_num_calc = map_escala_num_calc.get(v_n, pd.NA)
                            if pd.notna(val_num_calc): num_resp_n_calc.append(val_num_calc)
                    media_geral_n = round(sum(num_resp_n_calc)/len(num_resp_n_calc),2) if num_resp_n_calc else 0.0
                    emp_nome_n = st.session_state.user.get("Empresa","N/D"); id_diagnostico_salvo = str(st.session_state.id_formulario_atual)
                    nova_linha_diag_final_n = {"Data": id_diagnostico_salvo, "CNPJ": str(st.session_state.cnpj), "Nome": str(st.session_state.user.get("NomeContato", "")), "Email": str(st.session_state.user.get("Email", "")), "Empresa": str(emp_nome_n), "Média Geral": media_geral_n, "GUT Média": gut_media_n, "Observações": str(respostas_finais_envio_novo.get("__obs_cliente__","")), "Diagnóstico": str(respostas_finais_envio_novo.get("__resumo_cliente__","")), "Análise do Cliente": str(respostas_finais_envio_novo.get("__obs_cliente__","")), "Comentarios_Admin": ""}
                    nova_linha_diag_final_n.update(respostas_csv_n); medias_cat_final_n = {}
                    for cat_iter_n in perguntas_df_formulario["Categoria"].unique():
                        soma_c_n, cont_c_n = 0,0
                        for _,pr_n in perguntas_df_formulario[perguntas_df_formulario["Categoria"]==cat_iter_n].iterrows():
                            pt_n = pr_n["Pergunta"]; rv_n = respostas_finais_envio_novo.get(pt_n); val_num_cat = pd.to_numeric(rv_n, errors='coerce')
                            if "Escala" in pt_n and isinstance(rv_n, str): val_num_cat = {"Muito Baixo": 1, "Baixo": 2, "Médio": 3, "Alto": 4, "Muito Alto": 5}.get(rv_n, pd.NA)
                            if pd.notna(val_num_cat) and ("[Matriz GUT]" not in pt_n): soma_c_n+=val_num_cat; cont_c_n+=1
                        mc_n = round(soma_c_n/cont_c_n,2) if cont_c_n>0 else 0.0
                        nova_linha_diag_final_n[f"Media_Cat_{sanitize_column_name(cat_iter_n)}"] = mc_n; medias_cat_final_n[cat_iter_n] = mc_n
                    try: df_todos_diags_n_leitura = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str, 'Data': str})
                    except (FileNotFoundError, pd.errors.EmptyDataError): df_todos_diags_n_leitura = pd.DataFrame(columns=list(nova_linha_diag_final_n.keys()))
                    for col_add in nova_linha_diag_final_n.keys():
                        if col_add not in df_todos_diags_n_leitura.columns: df_todos_diags_n_leitura[col_add] = pd.NA
                    df_todos_diags_n_escrita = pd.concat([df_todos_diags_n_leitura, pd.DataFrame([nova_linha_diag_final_n])], ignore_index=True)
                    df_todos_diags_n_escrita.to_csv(arquivo_csv, index=False, encoding='utf-8'); st.cache_data.clear()
                    update_user_data(st.session_state.cnpj, "TotalDiagnosticosRealizados", st.session_state.user.get("TotalDiagnosticosRealizados", 0) + 1)
                    registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", f"ID: {id_diagnostico_salvo}.")
                    analises_df_pdf = carregar_analises_perguntas(); perg_df_pdf = pd.read_csv(perguntas_csv, encoding='utf-8') if os.path.exists(perguntas_csv) else pd.DataFrame()
                    pdf_path_gerado_n = gerar_pdf_diagnostico_completo(nova_linha_diag_final_n, st.session_state.user, perg_df_pdf, respostas_finais_envio_novo, medias_cat_final_n, analises_df_pdf)
                    st.session_state.diagnostico_enviado_sucesso = True; st.session_state.id_diagnostico_concluido_para_satisfacao = id_diagnostico_salvo; st.session_state.pesquisa_satisfacao_enviada = False
                    if pdf_path_gerado_n: st.session_state.pdf_gerado_path = pdf_path_gerado_n; st.session_state.pdf_gerado_filename = f"diagnostico_{sanitize_column_name(emp_nome_n)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.session_state.respostas_atuais_diagnostico = {}; st.session_state.progresso_diagnostico_percentual = 0; st.session_state.progresso_diagnostico_contagem = (0,total_perguntas_form); st.session_state.feedbacks_respostas = {}; st.session_state.sac_feedback_registrado = {}
                    st.session_state.cliente_page = "Painel Principal"; st.rerun()

# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    try: st.sidebar.image("https://via.placeholder.com/200x80.png?text=Logo+Admin", use_container_width=True)
    except Exception as e_img_admin: st.sidebar.caption(f"Logo admin não carregada: {e_img_admin}")
    st.sidebar.success("🟢 Admin Logado")
    if st.sidebar.button("Sair do Painel Admin", icon="🚪", key="logout_admin_v21_final_btn_ADMIN", use_container_width=True):
        st.session_state.admin_logado = False; st.toast("Logout de admin realizado.", icon="👋"); st.rerun()

    menu_admin_options_map = {
        "Visão Geral e Diagnósticos": "📊", "Relatório de Engajamento": "📈", "Gerenciar Notificações": "🔔",
        "Gerenciar Clientes": "👥", "Gerenciar Perguntas (Diagnóstico)": "📝", "Gerenciar Análises de Perguntas": "💡",
        "Gerenciar SAC": "📞", "⭐ Gerenciar Pesquisa de Satisfação": "⭐", "📊 Relatório Pesquisa de Satisfação": "📊",
        "Gerenciar Instruções": "⚙️", "Histórico de Usuários": "📜", "Gerenciar Administradores": "👮"
    }
    admin_page_text_keys = list(menu_admin_options_map.keys())
    admin_options_for_display = [f"{menu_admin_options_map[key]} {key}" for key in admin_page_text_keys]
    SESSION_KEY_FOR_ADMIN_PAGE = "admin_current_page_key_v21_final_ADMIN"
    WIDGET_KEY_SB_ADMIN_MENU = "admin_sidebar_menu_v21_final_ADMIN"

    def admin_menu_on_change():
        selected_display_value = st.session_state.get(WIDGET_KEY_SB_ADMIN_MENU)
        if selected_display_value:
            new_text_key = next((text_key for text_key, emoji in menu_admin_options_map.items() if f"{emoji} {text_key}" == selected_display_value), None)
            if new_text_key and new_text_key != st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE):
                st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = new_text_key

    if SESSION_KEY_FOR_ADMIN_PAGE not in st.session_state or st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE) not in admin_page_text_keys:
        st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]
    current_admin_page_text_key_for_index = st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE, admin_page_text_keys[0])
    current_admin_menu_index = 0
    try:
        expected_display_value = f"{menu_admin_options_map[current_admin_page_text_key_for_index]} {current_admin_page_text_key_for_index}"
        current_admin_menu_index = admin_options_for_display.index(expected_display_value) if expected_display_value in admin_options_for_display else 0
    except (ValueError, KeyError): st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]; current_admin_menu_index = 0
    if current_admin_page_text_key_for_index not in admin_page_text_keys: st.session_state[SESSION_KEY_FOR_ADMIN_PAGE] = admin_page_text_keys[0]; current_admin_menu_index = 0

    st.sidebar.selectbox("Funcionalidades Admin:", options=admin_options_for_display, index=current_admin_menu_index, key=WIDGET_KEY_SB_ADMIN_MENU, on_change=admin_menu_on_change)
    menu_admin = st.session_state.get(SESSION_KEY_FOR_ADMIN_PAGE, admin_page_text_keys[0])
    if menu_admin not in menu_admin_options_map: menu_admin = admin_page_text_keys[0]
    st.header(f"{menu_admin_options_map.get(menu_admin, '❓')} {menu_admin}")

    df_usuarios_admin_geral = pd.DataFrame(columns=colunas_base_usuarios)
    try:
        df_temp_users = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
        for col, default, dtype_func_str in [("JaVisualizouInstrucoes", "False", "bool"), ("DiagnosticosDisponiveis", 1, "int"), ("TotalDiagnosticosRealizados", 0, "int")]:
            if col not in df_temp_users.columns: df_temp_users[col] = default
            if dtype_func_str == "int": df_temp_users[col] = pd.to_numeric(df_temp_users[col], errors='coerce').fillna(default).astype(int)
            elif dtype_func_str == "bool": df_temp_users[col] = df_temp_users[col].astype(str).str.lower().map({'true': True, 'false': False, 'nan': False, 'none': False, '': False}).fillna(default.lower() == 'true' if isinstance(default, str) else False)
        df_usuarios_admin_geral = df_temp_users
    except FileNotFoundError: st.sidebar.error(f"Arquivo '{usuarios_csv}' não encontrado.")
    except Exception as e_load_users_adm: st.sidebar.error(f"Erro ao carregar usuários para admin: {e_load_users_adm}")

    if menu_admin == "Visão Geral e Diagnósticos":
        st.markdown("--- DEBUG: Entrou em Visão Geral e Diagnósticos ---")
        diagnosticos_df_admin_orig_view = pd.DataFrame()
        admin_data_carregada_view_sucesso = False
        try:
            st.caption("Debug: Lendo arquivo_csv...")
            df_temp_admin_diag = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str, 'Data': str})
            st.caption(f"Debug: arquivo_csv lido. Shape: {df_temp_admin_diag.shape}")

            cols_numericas_diag_admin = ['Média Geral', 'GUT Média'] + [col for col in df_temp_admin_diag.columns if col.startswith("Media_Cat_")]
            for col_num_adm in cols_numericas_diag_admin:
                if col_num_adm in df_temp_admin_diag.columns:
                    df_temp_admin_diag[col_num_adm] = pd.to_numeric(df_temp_admin_diag[col_num_adm], errors='coerce')
            diagnosticos_df_admin_orig_view = df_temp_admin_diag.copy()

            if 'Data' in diagnosticos_df_admin_orig_view.columns:
                def extract_timestamp_from_data_id(data_id_str):
                    if isinstance(data_id_str, str) and '_' in data_id_str: return data_id_str.split('_')[-1]
                    return None # Retorna None se não puder extrair
                diagnosticos_df_admin_orig_view['Timestamp_str_from_Data'] = diagnosticos_df_admin_orig_view['Data'].apply(extract_timestamp_from_data_id)
                diagnosticos_df_admin_orig_view['Data_dt'] = pd.to_datetime(diagnosticos_df_admin_orig_view['Timestamp_str_from_Data'], format='%Y%m%d%H%M%S%f', errors='coerce')
                mask_failed_parse = diagnosticos_df_admin_orig_view['Data_dt'].isnull() & diagnosticos_df_admin_orig_view['Timestamp_str_from_Data'].notnull()
                if mask_failed_parse.any():
                    diagnosticos_df_admin_orig_view.loc[mask_failed_parse, 'Data_dt'] = pd.to_datetime(diagnosticos_df_admin_orig_view.loc[mask_failed_parse, 'Timestamp_str_from_Data'], errors='coerce')
            else: diagnosticos_df_admin_orig_view['Data_dt'] = pd.NaT
            if not diagnosticos_df_admin_orig_view.empty: admin_data_carregada_view_sucesso = True

            st.subheader("Debug Admin: diagnosticos_df_admin_orig_view")
            st.write(f"Carregado com sucesso: {admin_data_carregada_view_sucesso}")
            if admin_data_carregada_view_sucesso:
                st.write("Shape:", diagnosticos_df_admin_orig_view.shape)
                st.dataframe(diagnosticos_df_admin_orig_view.head(10))
                with st.expander("Info do DataFrame de Diagnósticos (Admin)"):
                    buffer = io.StringIO(); diagnosticos_df_admin_orig_view.info(buf=buffer); s = buffer.getvalue(); st.text(s)
                if 'Data_dt' in diagnosticos_df_admin_orig_view.columns:
                    st.write(f"Contagem de NaT em Data_dt: {diagnosticos_df_admin_orig_view['Data_dt'].isnull().sum()} de {len(diagnosticos_df_admin_orig_view)}")
                    st.write("Exemplo de 'Data':", diagnosticos_df_admin_orig_view['Data'].head())
                    st.write("Exemplo de 'Timestamp_str_from_Data':", diagnosticos_df_admin_orig_view['Timestamp_str_from_Data'].head())
                    st.write("Exemplo de 'Data_dt':", diagnosticos_df_admin_orig_view['Data_dt'].head())
            else: st.warning("diagnosticos_df_admin_orig_view não foi carregado ou está vazio após processamento.")
        except pd.errors.EmptyDataError: st.warning(f"Arquivo '{arquivo_csv}' está vazio ou contém apenas cabeçalhos.")
        except FileNotFoundError: st.error(f"Arquivo de diagnósticos '{arquivo_csv}' não encontrado.")
        except Exception as e_load_admin_diag: st.error(f"Erro ao carregar diagnósticos para admin: {e_load_admin_diag}"); st.exception(e_load_admin_diag)

        st.markdown("#### KPIs Gerais do Sistema") # ... (KPIs)
        st.divider(); st.markdown("#### Análises Gráficas do Sistema") # ... (Gráficos)
        st.divider(); st.markdown("#### Filtros para Análise Detalhada de Diagnósticos") # ... (Filtros e visão detalhada)

    # ... (Preencher os ELIFs para TODAS as outras seções do admin, como Gerenciar Clientes, etc.)
    # Por exemplo:
    elif menu_admin == "Gerenciar Clientes":
        st.subheader("👥 Gerenciar Clientes")
        # Seu código completo para Gerenciar Clientes aqui
        if df_usuarios_admin_geral.empty:
            st.info("Nenhum usuário cadastrado para gerenciar.")
        else:
            st.dataframe(df_usuarios_admin_geral) # Exemplo básico
            # Adicionar filtros, botões de ação, formulário de novo cliente etc.

    # ... (Restante das seções do Admin)

elif not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()