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

# --- CSS (igual ao fornecido) ---
st.markdown("""
<style>
body {
    font-family: 'Segoe UI', sans-serif;
}
/* ... (seu CSS completo aqui) ... */
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

# --- Funções de Gráficos (sem alteração) ---
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
    fig.update_layout(title={'text': title, 'x':0.5, 'xanchor': 'center'}, polar=dict(radialaxis=dict(visible=True, range=[0, 5])), font=dict(family="Segoe UI, sans-serif"), margin=dict(l=50, r=50, t=70, b=50))
    return fig

def create_gut_barchart(gut_data_list, title="Top Prioridades (GUT)"):
    if not gut_data_list: return None
    df_gut = pd.DataFrame(gut_data_list)
    df_gut = df_gut.sort_values(by="Score", ascending=False).head(10)
    if df_gut.empty: return None
    fig = px.bar(df_gut, x="Score", y="Tarefa", title=title, orientation='h', color="Score", color_continuous_scale=px.colors.sequential.Blues_r, labels={'Tarefa':'Tarefa/Pergunta', 'Score':'Score GUT'})
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Score GUT", yaxis_title="", font=dict(family="Segoe UI, sans-serif"), height=400 + len(df_gut)*20, margin=dict(l=250, r=20, t=70, b=20))
    return fig

def create_diagnostics_timeline_chart(df_diagnostics, title="Diagnósticos Realizados ao Longo do Tempo"):
    if df_diagnostics.empty or 'Data_dt' not in df_diagnostics.columns: return None # ESPERA Data_dt
    df_diag_copy = df_diagnostics.copy()
    # df_diag_copy['Data'] = pd.to_datetime(df_diag_copy['Data']) # Data_dt já é datetime
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
    avg_scores = pd.DataFrame(avg_scores_data).sort_values(by="Média_Score", ascending=False)
    fig = px.bar(avg_scores, x='Categoria', y='Média_Score', title=title, color='Média_Score', color_continuous_scale=px.colors.sequential.Blues_r, labels={'Categoria':'Categoria', 'Média_Score':'Média do Score'})
    fig.update_layout(xaxis_tickangle=-45, font=dict(family="Segoe UI, sans-serif"), yaxis=dict(range=[0,5.5]))
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
arquivo_csv = "diagnosticos_clientes.csv" # Principal arquivo de diagnósticos
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv" # Perguntas do diagnóstico principal
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

# --- Inicialização do Session State (sem alteração) ---
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

# --- Funções Utilitárias (sem alteração aparente que cause o problema) ---
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

# COLUNAS BASE (sem alteração aparente que cause o problema)
colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone", "JaVisualizouInstrucoes", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados"]
colunas_base_perguntas = ["Pergunta", "Categoria"]
colunas_base_analises = ["ID_Analise", "TextoPerguntaOriginal", "TipoCondicao", "CondicaoValorMin", "CondicaoValorMax", "CondicaoValorExato", "TextoAnalise"]
colunas_base_notificacoes = ["ID_Notificacao", "CNPJ_Cliente", "Timestamp", "Mensagem", "Lida", "ID_Diagnostico_Relacionado"]
colunas_base_sac_perguntas = ["ID_SAC_Pergunta", "Pergunta_SAC", "Resposta_SAC", "Categoria_SAC", "DataCriacao"]
colunas_base_sac_uso_feedback = ["ID_Uso_SAC", "Timestamp", "CNPJ_Cliente", "ID_SAC_Pergunta", "Feedback_Util"]
colunas_base_pesquisa_satisfacao_perguntas = ["ID_Pergunta_Satisfacao", "Texto_Pergunta", "Tipo_Pergunta", "Opcoes_Pergunta", "Ordem", "Ativa"]
colunas_base_pesquisa_satisfacao_respostas = ["ID_Resposta_Satisfacao", "ID_Diagnostico_Cliente", "ID_Pergunta_Satisfacao", "CNPJ_Cliente", "Timestamp_Resposta", "Resposta_Valor"]

# FUNÇÃO inicializar_csv (sem alteração aparente que cause o problema, mas a lógica de recriação pode ser um ponto se a escrita falhar)
def inicializar_csv(filepath, columns, defaults=None):
    try:
        # Define dtypes para colunas específicas para evitar erros de tipo na leitura
        dtype_spec = {}
        if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, sac_uso_feedback_csv, pesquisa_satisfacao_respostas_csv]:
            dtype_spec['CNPJ'] = str
            dtype_spec['CNPJ_Cliente'] = str
        # Para o arquivo_csv, garanta que 'Data' (ID do diagnóstico) seja lido como string
        if filepath == arquivo_csv:
            dtype_spec['Data'] = str


        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init = pd.DataFrame(columns=columns)
            if defaults:
                for col, default_val in defaults.items():
                    if col in columns: df_init[col] = default_val
            df_init.to_csv(filepath, index=False, encoding='utf-8')
        else:
            try:
                # Aplicar dtype_spec se não for None
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)
            except (ValueError, TypeError) as ve:
                st.warning(f"Problema ao ler {filepath} com dtypes específicos ({ve}), tentando leitura genérica.")
                df_init = pd.read_csv(filepath, encoding='utf-8')
            except Exception as read_e:
                st.warning(f"Problema crítico ao ler {filepath}, tentando recriar com colunas esperadas: {read_e}. Verifique o arquivo.")
                # Em caso de erro crítico de leitura, evite sobrescrever com um arquivo vazio.
                # Melhor lançar o erro ou retornar um DataFrame vazio sem tentar recriar cegamente.
                # return pd.DataFrame(columns=columns) # Ou raise read_e
                df_init = pd.DataFrame(columns=columns) # Mantendo comportamento anterior para consistência, mas com cautela
                if defaults:
                    for col_d, val_d in defaults.items():
                        if col_d in columns: df_init[col_d] = val_d
                df_init.to_csv(filepath, index=False, encoding='utf-8')
                # Tentar reler após recriação
                df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)


            made_changes = False
            temp_df_columns = df_init.columns.tolist() # Evitar modificar durante iteração
            for col_idx, col_name in enumerate(columns):
                if col_name not in temp_df_columns:
                    default_val = defaults.get(col_name, pd.NA) if defaults else pd.NA
                    # Insere com tipo de dados consistente se possível, ou pd.NA
                    try:
                        if pd.isna(default_val) and defaults and col_name in defaults: # Tentar usar o tipo do default
                             df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=pd.Series(defaults[col_name], index=df_init.index, dtype=type(defaults[col_name])))
                        else:
                             df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=default_val)
                    except Exception as e_insert: # Fallback mais genérico
                         df_init.insert(loc=min(col_idx, len(df_init.columns)), column=col_name, value=default_val)

                    made_changes = True
            if made_changes:
                df_init.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError: # Arquivo existe mas está completamente vazio (sem cabeçalhos)
        df_init = pd.DataFrame(columns=columns)
        if defaults:
            for col, default_val in defaults.items():
                if col in columns: df_init[col] = default_val
        df_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e:
        st.error(f"Erro crítico na função inicializar_csv para {filepath}: {e}")
        # Em vez de raise, que pode parar a app, podemos logar e retornar um df vazio para tentar continuar
        # raise
        return pd.DataFrame(columns=columns)


# INICIALIZAÇÃO DOS ARQUIVOS (sem alteração aparente que cause o problema)
try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios, defaults={"JaVisualizouInstrucoes": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos) # Garanta que colunas_base_diagnosticos cubra o essencial
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False, "ID_Diagnostico_Relacionado": None})
    inicializar_csv(sac_perguntas_respostas_csv, colunas_base_sac_perguntas, defaults={"Categoria_SAC": "Geral", "DataCriacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    inicializar_csv(sac_uso_feedback_csv, colunas_base_sac_uso_feedback, defaults={"Feedback_Util": None})
    inicializar_csv(pesquisa_satisfacao_perguntas_csv, colunas_base_pesquisa_satisfacao_perguntas, defaults={"Ordem": 0, "Ativa": True, "Opcoes_Pergunta": None})
    inicializar_csv(pesquisa_satisfacao_respostas_csv, colunas_base_pesquisa_satisfacao_respostas)
except Exception as e_init:
    st.error(f"Falha crítica na inicialização de arquivos CSV: {e_init}. A aplicação pode não funcionar corretamente.")
    st.stop()


# --- Funções de Cache e Carregamento de Dados (sem alteração aparente que cause o problema) ---
# ... (registrar_acao, update_user_data, carregar_analises_perguntas, etc. - mantidas como no código anterior)
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
            df['Feedback_Util'] = pd.NA # Explicitamente boolean com NA
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_sac_uso_feedback)

@st.cache_data
def carregar_perguntas_satisfacao(apenas_ativas=True):
    try:
        df = pd.read_csv(pesquisa_satisfacao_perguntas_csv, encoding='utf-8')
        if 'Ativa' not in df.columns: df['Ativa'] = True
        else: df['Ativa'] = df['Ativa'].astype(bool) # Garante boolean
        if 'Ordem' not in df.columns: df['Ordem'] = 0
        else: df['Ordem'] = pd.to_numeric(df['Ordem'], errors='coerce').fillna(0).astype(int)
        if 'Opcoes_Pergunta' not in df.columns: df['Opcoes_Pergunta'] = None # Adiciona se faltar

        if apenas_ativas:
            df = df[df['Ativa'] == True]
        return df.sort_values(by="Ordem", ascending=True)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=colunas_base_pesquisa_satisfacao_perguntas)

@st.cache_data
def carregar_respostas_satisfacao(cnpj_cliente=None, id_diagnostico=None):
    try:
        df = pd.read_csv(pesquisa_satisfacao_respostas_csv, encoding='utf-8', dtype={'CNPJ_Cliente': str, 'ID_Diagnostico_Cliente': str})
        if cnpj_cliente:
            df = df[df['CNPJ_Cliente'] == str(cnpj_cliente)]
        if id_diagnostico: # id_diagnostico é o 'Data' do diagnóstico
            df = df[df['ID_Diagnostico_Cliente'] == str(id_diagnostico)]
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
        tipo_cond = row_analise['TipoCondicao']; analise_txt = row_analise['TextoAnalise']
        if tipo_cond == 'Default': default_analise = analise_txt; continue
        try: # Adicionado try-except para conversões numéricas
            if tipo_cond == 'FaixaNumerica':
                min_val=pd.to_numeric(row_analise['CondicaoValorMin'],errors='raise');max_val=pd.to_numeric(row_analise['CondicaoValorMax'],errors='raise');resp_num=pd.to_numeric(resposta_valor,errors='raise')
                if min_val <= resp_num <= max_val: return analise_txt
            elif tipo_cond == 'ValorExatoEscala':
                if str(resposta_valor).strip().lower() == str(row_analise['CondicaoValorExato']).strip().lower(): return analise_txt
            elif tipo_cond == 'ScoreGUT':
                min_s=pd.to_numeric(row_analise['CondicaoValorMin'],errors='raise');max_s=pd.to_numeric(row_analise['CondicaoValorMax'],errors='coerce');resp_s_gut=pd.to_numeric(resposta_valor,errors='raise')
                is_min = resp_s_gut >= min_s
                is_max_ok = pd.isna(max_s) or (resp_s_gut <= max_s)
                if is_min and is_max_ok: return analise_txt
        except (ValueError, TypeError):
            continue # Se a conversão falhar, a condição não é atendida
    return default_analise
# --- Geração de PDF (sem alteração aparente que cause o problema) ---
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
                except Exception as e_logo_pdf: st.warning(f"Não foi possível adicionar logo ao PDF: {e_logo_pdf}")

            pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome}"), 0, 1, 'C'); pdf.ln(5)
            pdf.set_font("Arial", size=10)
            # 'Data' aqui é o ID do diagnóstico
            pdf.multi_cell(0, 7, pdf_safe_text_output(f"ID/Data Diagnóstico: {diag_data.get('Data','N/D')} | Empresa: {empresa_nome} (CNPJ: {cnpj_pdf})"))
            if user_data.get("NomeContato"): pdf.multi_cell(0, 7, pdf_safe_text_output(f"Contato: {user_data.get('NomeContato')}"))
            if user_data.get("Telefone"): pdf.multi_cell(0, 7, pdf_safe_text_output(f"Telefone: {user_data.get('Telefone')}"))
            pdf.ln(3)
            pdf.multi_cell(0, 7, pdf_safe_text_output(f"Média Geral: {diag_data.get('Média Geral','N/A')} | GUT Média: {diag_data.get('GUT Média','N/A')}")); pdf.ln(3)

            if medias_cat:
                pdf.set_font("Arial", 'B', 11); pdf.multi_cell(0, 7, pdf_safe_text_output("Médias por Categoria:"))
                pdf.set_font("Arial", size=10)
                for cat, media_val in medias_cat.items():
                    media_str = f"{media_val:.2f}" if isinstance(media_val, (int, float)) else str(media_val)
                    pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat}: {media_str}"))
                pdf.ln(1); pdf.ln(5)

            for titulo, campo in [("Resumo (Cliente):", "Diagnóstico"), ("Análise (Cliente):", "Análise do Cliente"), ("Comentários (Consultor):", "Comentarios_Admin")]:
                valor = diag_data.get(campo, "")
                if valor and not pd.isna(valor) and str(valor).strip():
                    pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output(titulo))
                    pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(str(valor))); pdf.ln(3)

            pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 10, pdf_safe_text_output("Respostas Detalhadas e Análises:"))
            # Assegurar que perguntas_df é o DataFrame de perguntas do diagnóstico principal
            if perguntas_df.empty or "Pergunta" not in perguntas_df.columns or "Categoria" not in perguntas_df.columns:
                 pdf.set_font("Arial", 'I', 10); pdf.multi_cell(0, 7, pdf_safe_text_output("Estrutura de perguntas do diagnóstico não disponível para detalhamento no PDF.")); pdf.ln(3)
            else:
                categorias = perguntas_df["Categoria"].unique()
                for categoria in categorias:
                    pdf.set_font("Arial", 'B', 10); pdf.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria}")); pdf.set_font("Arial", size=9)
                    perg_cat = perguntas_df[perguntas_df["Categoria"] == categoria]
                    for _, p_row in perg_cat.iterrows():
                        p_texto = p_row["Pergunta"]
                        # Usar respostas_coletadas que deve ter as respostas do diagnóstico específico
                        resp = respostas_coletadas.get(p_texto, diag_data.get(p_texto, "N/R")) # diag_data também é uma fonte
                        analise_texto = None
                        if "[Matriz GUT]" in p_texto:
                            g,u,t,score=0,0,0,0
                            if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                            elif isinstance(resp, str) and resp.startswith("{"): # Checa se parece JSON
                                try: data_gut=json.loads(resp.replace("'",'"'));g,u,t=int(data_gut.get("G",0)),int(data_gut.get("U",0)),int(data_gut.get("T",0))
                                except: pass # Silencioso se falhar
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

            # Plano de Ação
            if not perguntas_df.empty:
                pdf.add_page(); pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf.ln(5); pdf.set_font("Arial", size=10)
                gut_cards = []
                for _, p_row in perguntas_df.iterrows():
                    p_texto = p_row["Pergunta"]
                    if "[Matriz GUT]" in p_texto:
                        resp = respostas_coletadas.get(p_texto, diag_data.get(p_texto))
                        g,u,t,score=0,0,0,0
                        if isinstance(resp, dict): g,u,t=int(resp.get("G",0)),int(resp.get("U",0)),int(resp.get("T",0))
                        elif isinstance(resp, str) and resp.startswith("{"):
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


# --- Lógica de Login e Navegação Principal (sem alteração aparente que cause o problema) ---
if st.session_state.get("trigger_rerun_global"): st.session_state.trigger_rerun_global = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v19")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    # ... (código de login admin - sem alterações relevantes)
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
    # ... (código de login cliente - sem alterações relevantes)
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
                # ESTE ID É CRUCIAL e será salvo como 'Data' no arquivo_csv
                st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                st.session_state.respostas_atuais_diagnostico = {}
                st.session_state.progresso_diagnostico_percentual = 0
                st.session_state.progresso_diagnostico_contagem = (0,0)
                st.session_state.feedbacks_respostas = {}
                st.session_state.sac_feedback_registrado = {}
                st.session_state.diagnostico_enviado_sucesso = False
                st.session_state.target_diag_data_for_expansion = None
                st.session_state.id_diagnostico_concluido_para_satisfacao = None
                st.session_state.respostas_pesquisa_satisfacao_atual = {}
                st.session_state.pesquisa_satisfacao_enviada = False

                st.toast("Login de cliente bem-sucedido!", icon="👋")
                st.rerun()
            except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    # ... (código da sidebar do cliente - sem alterações relevantes)
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
                notificacoes_nao_lidas_count = len(df_notif_check[(df_notif_check["CNPJ_Cliente"] == st.session_state.cnpj) & (df_notif_check["Lida"] == False)])
        except pd.errors.EmptyDataError: notificacoes_nao_lidas_count = 0
        except Exception as e_notif_check: print(f"Erro ao verificar notificações: {e_notif_check}")
    notificacoes_label = "🔔 Notificações"
    if notificacoes_nao_lidas_count > 0: notificacoes_label = f"🔔 Notificações ({notificacoes_nao_lidas_count} Nova(s))"

    menu_options_cli_map_full = {"Instruções": "📖 Instruções", "Novo Diagnóstico": "📋 Novo Diagnóstico", "Painel Principal": "🏠 Painel Principal", "Notificações": notificacoes_label, "SAC": "❓ SAC - Perguntas Frequentes"}
    if not st.session_state.user.get("JaVisualizouInstrucoes", False):
        menu_options_cli_map = {"Instruções": "📖 Instruções"}
        st.session_state.cliente_page = "Instruções"
    else:
        menu_options_cli_map = menu_options_cli_map_full.copy()
        pode_fazer_novo = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
        if not pode_fazer_novo and "Novo Diagnóstico" in menu_options_cli_map:
            if st.session_state.cliente_page == "Novo Diagnóstico": st.session_state.cliente_page = "Painel Principal"
            del menu_options_cli_map["Novo Diagnóstico"]
    menu_options_cli_display = list(menu_options_cli_map.values())
    if st.session_state.cliente_page not in menu_options_cli_map.keys():
        st.session_state.cliente_page = "Instruções" if not st.session_state.user.get("JaVisualizouInstrucoes", False) else "Painel Principal"
    default_display_option = menu_options_cli_map.get(st.session_state.cliente_page)
    current_idx_cli = 0
    if default_display_option and default_display_option in menu_options_cli_display: current_idx_cli = menu_options_cli_display.index(default_display_option)
    elif menu_options_cli_display:
        current_idx_cli = 0
        for key_page_fallback, val_page_display_fallback in menu_options_cli_map.items():
            if val_page_display_fallback == menu_options_cli_display[0]: st.session_state.cliente_page = key_page_fallback; break
    selected_page_cli_raw = st.sidebar.radio("Menu Cliente", menu_options_cli_display, index=current_idx_cli, key="cli_menu_v19_conditional")
    selected_page_cli_clean = ""
    for key_page, val_page_display in menu_options_cli_map.items():
        if val_page_display == selected_page_cli_raw:
            selected_page_cli_clean = key_page
            if key_page == "Notificações": selected_page_cli_clean = "Notificações" # Manter a chave limpa
            elif key_page == "SAC": selected_page_cli_clean = "SAC"
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
        st.toast("Logout realizado.", icon="👋"); st.rerun()


    if st.session_state.cliente_page == "Painel Principal":
        st.subheader(menu_options_cli_map_full["Painel Principal"])
        target_diag_to_expand = st.session_state.pop("target_diag_data_for_expansion", None)

        if st.session_state.diagnostico_enviado_sucesso:
            st.success("🎯 Seu último diagnóstico foi enviado e processado com sucesso!")
            if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                try:
                    with open(st.session_state.pdf_gerado_path, "rb") as f_pdf:
                        st.download_button(label="Baixar PDF do Diagnóstico Recém-Enviado", data=f_pdf,
                                           file_name=st.session_state.pdf_gerado_filename, mime="application/pdf",
                                           key="dl_novo_diag_painel_v19", icon="📄")
                    st.session_state.pdf_gerado_path = None
                    st.session_state.pdf_gerado_filename = None
                except FileNotFoundError:
                    st.warning("Arquivo PDF do diagnóstico recém-enviado não encontrado. Pode já ter sido baixado ou houve um erro.")
                except Exception as e_pdf_dl:
                    st.error(f"Erro ao preparar download do PDF: {e_pdf_dl}")

            # --- LÓGICA DA PESQUISA DE SATISFAÇÃO ---
            if st.session_state.id_diagnostico_concluido_para_satisfacao and not st.session_state.pesquisa_satisfacao_enviada:
                id_diag_atual_satisfacao = st.session_state.id_diagnostico_concluido_para_satisfacao
                if verificar_pesquisa_satisfacao_pendente(st.session_state.cnpj, id_diag_atual_satisfacao):
                    st.markdown("---"); st.subheader("⭐ Pesquisa de Satisfação Rápida")
                    st.caption("Sua opinião é muito importante para nós! Por favor, dedique um momento para responder.")
                    perguntas_satisfacao_df = carregar_perguntas_satisfacao(apenas_ativas=True)
                    if not perguntas_satisfacao_df.empty:
                        with st.form(key="form_pesquisa_satisfacao_cliente"):
                            for idx_ps, row_ps in perguntas_satisfacao_df.iterrows():
                                p_id = row_ps["ID_Pergunta_Satisfacao"]; p_texto = row_ps["Texto_Pergunta"]
                                p_tipo = row_ps["Tipo_Pergunta"]; p_opcoes_str = row_ps.get("Opcoes_Pergunta")
                                widget_key_ps = f"satisfacao_{p_id}"
                                st.markdown(f"**{p_texto}**")
                                if p_tipo == "escala_1_5":
                                    st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.radio(" ", list(range(1, 6)), key=widget_key_ps, horizontal=True, label_visibility="collapsed")
                                elif p_tipo == "texto_aberto":
                                    st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.text_area(" ", key=widget_key_ps, label_visibility="collapsed")
                                elif p_tipo == "sim_nao":
                                    st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.radio(" ", ["Sim", "Não"], key=widget_key_ps, horizontal=True, label_visibility="collapsed")
                                elif p_tipo == "multipla_escolha_unica":
                                    opcoes_ps = []
                                    if pd.notna(p_opcoes_str):
                                        try: opcoes_ps = json.loads(p_opcoes_str).get("opcoes", [])
                                        except json.JSONDecodeError: st.warning(f"Opções mal formatadas para: {p_texto}")
                                    if opcoes_ps: st.session_state.respostas_pesquisa_satisfacao_atual[p_id] = st.radio(" ", opcoes_ps, key=widget_key_ps, label_visibility="collapsed")
                                    else: st.caption(" (Opções não configuradas)")
                                st.write("")
                            if st.form_submit_button("Enviar Feedback de Satisfação", use_container_width=True, icon="💖"):
                                respostas_finais_satisfacao = []
                                timestamp_atual_satisfacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                for id_pergunta, resposta_val in st.session_state.respostas_pesquisa_satisfacao_atual.items():
                                    if resposta_val is not None and str(resposta_val).strip() != "":
                                        respostas_finais_satisfacao.append({"ID_Resposta_Satisfacao": str(uuid.uuid4()), "ID_Diagnostico_Cliente": id_diag_atual_satisfacao, "ID_Pergunta_Satisfacao": id_pergunta, "CNPJ_Cliente": st.session_state.cnpj, "Timestamp_Resposta": timestamp_atual_satisfacao, "Resposta_Valor": str(resposta_val)})
                                if respostas_finais_satisfacao:
                                    df_respostas_todas_satisfacao = carregar_respostas_satisfacao()
                                    df_novas_respostas_satisfacao = pd.DataFrame(respostas_finais_satisfacao)
                                    df_respostas_atualizadas_satisfacao = pd.concat([df_respostas_todas_satisfacao, df_novas_respostas_satisfacao], ignore_index=True)
                                    df_respostas_atualizadas_satisfacao.to_csv(pesquisa_satisfacao_respostas_csv, index=False, encoding='utf-8')
                                    st.cache_data.clear()
                                    st.session_state.pesquisa_satisfacao_enviada = True
                                    # st.session_state.id_diagnostico_concluido_para_satisfacao = None # Não resetar aqui, para não pedir de novo na mesma visualização
                                    st.session_state.respostas_pesquisa_satisfacao_atual = {}
                                    st.success("Obrigado pelo seu feedback de satisfação!"); time.sleep(1.5); st.rerun()
                                else: st.warning("Nenhuma resposta foi fornecida.")
                    else: st.info("A pesquisa de satisfação não possui perguntas ativas.")
                elif not st.session_state.pesquisa_satisfacao_enviada and st.session_state.id_diagnostico_concluido_para_satisfacao:
                    st.success("Você já respondeu à pesquisa de satisfação para este diagnóstico. Obrigado!")
            
            st.session_state.diagnostico_enviado_sucesso = False # Reset para não mostrar a msg de sucesso do diagnóstico de novo

        with st.expander("ℹ️ Informações Importantes", expanded=False):
            st.markdown("- Visualize seus diagnósticos anteriores e sua evolução.\n- Acompanhe seu plano de ação no Kanban.\n- Para um novo diagnóstico (se liberado), selecione 'Novo Diagnóstico' no menu ao lado.")

        df_cliente_diags_raw = pd.DataFrame() # Inicializa como vazio
        try:
            df_antigos_cliente = pd.read_csv(arquivo_csv, dtype={'CNPJ': str, 'Data': str}, encoding='utf-8') # Ler 'Data' como string
            cols_numericas_diag = ['Média Geral', 'GUT Média'] + [col for col in df_antigos_cliente.columns if col.startswith("Media_Cat_")]
            for col_num in cols_numericas_diag:
                if col_num in df_antigos_cliente.columns:
                    df_antigos_cliente[col_num] = pd.to_numeric(df_antigos_cliente[col_num], errors='coerce')

            df_cliente_diags_raw = df_antigos_cliente[df_antigos_cliente["CNPJ"] == st.session_state.cnpj].copy()
            if df_cliente_diags_raw.empty and not df_antigos_cliente[df_antigos_cliente["CNPJ"] == st.session_state.cnpj].empty:
                 st.warning("Diagnósticos encontrados, mas o filtro por CNPJ não retornou dados. Verifique o CNPJ em sessão.")


        except FileNotFoundError:
            st.error(f"Arquivo de diagnósticos '{arquivo_csv}' não encontrado.")
        except Exception as e_load_diag:
            st.error(f"Erro ao carregar diagnósticos do cliente: {e_load_diag}")

        if not df_cliente_diags_raw.empty:
            df_cliente_diags = df_cliente_diags_raw.sort_values(by="Data", ascending=False).reset_index(drop=True)
            latest_diag_data_row = df_cliente_diags.iloc[0]
            latest_diag_data = latest_diag_data_row.to_dict()

            # ... (Restante da exibição do Painel Principal do cliente, como gráficos, diagnósticos anteriores)
            # Esta parte do código parece ser extensa e relativamente estável, então não vou replicá-la inteira aqui
            # Apenas garanta que 'latest_diag_data' e 'df_cliente_diags' estão sendo povoados corretamente.
            # Se estas estiverem vazias, os gráficos e a lista de diagnósticos não aparecerão.

            st.markdown("#### 📊 Visão Geral do Último Diagnóstico")
            col_graph1, col_graph2 = st.columns(2)
            with col_graph1:
                st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
                st.markdown("##### Scores por Categoria")
                medias_cat_latest = { k.replace("Media_Cat_", "").replace("_", " "): v for k, v in latest_diag_data.items() if k.startswith("Media_Cat_") and pd.notna(v) }
                if medias_cat_latest:
                    fig_radar = create_radar_chart(medias_cat_latest, title="")
                    if fig_radar: st.plotly_chart(fig_radar, use_container_width=True)
                    else: st.caption("Não foi possível gerar o gráfico de radar (verifique se há pelo menos 3 categorias com dados).")
                else: st.caption("Sem dados de média por categoria para o último diagnóstico.")
                st.markdown('</div>', unsafe_allow_html=True)
            with col_graph2:
                st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
                st.markdown("##### Top Prioridades (Matriz GUT)")
                gut_data_list_client = []
                for pergunta_key, resp_val_str in latest_diag_data.items():
                    if isinstance(pergunta_key, str) and "[Matriz GUT]" in pergunta_key and pd.notna(resp_val_str) and isinstance(resp_val_str, str):
                        try:
                            gut_data = json.loads(resp_val_str.replace("'", "\""))
                            g, u, t_val = int(gut_data.get("G",0)), int(gut_data.get("U",0)), int(gut_data.get("T",0))
                            score = g * u * t_val
                            if score > 0: gut_data_list_client.append({"Tarefa": pergunta_key.replace(" [Matriz GUT]", ""), "Score": score})
                        except: pass
                if gut_data_list_client:
                    fig_gut_bar = create_gut_barchart(gut_data_list_client, title="")
                    if fig_gut_bar: st.plotly_chart(fig_gut_bar, use_container_width=True)
                    else: st.caption("Não foi possível gerar gráfico de prioridades GUT.")
                else: st.caption("Nenhuma prioridade GUT identificada no último diagnóstico.")
                st.markdown('</div>', unsafe_allow_html=True)
            st.divider()

            st.markdown("#### 📁 Diagnósticos Anteriores")
            # ... (código de exibição dos diagnósticos anteriores - verificar se df_cliente_diags tem dados)
            if df_cliente_diags.empty:
                st.info("Nenhum diagnóstico anterior encontrado para este cliente.")
            else:
                try:
                    perguntas_df_para_painel = pd.read_csv(perguntas_csv, encoding='utf-8')
                    if "Categoria" not in perguntas_df_para_painel.columns: perguntas_df_para_painel["Categoria"] = "Geral"
                except FileNotFoundError:
                    st.error(f"Arquivo de perguntas '{perguntas_csv}' não encontrado para detalhar diagnósticos.")
                    perguntas_df_para_painel = pd.DataFrame()
                analises_df_para_painel = carregar_analises_perguntas()

                for idx_row_diag, row_diag_data_series in df_cliente_diags.iterrows():
                    row_diag_data = row_diag_data_series.to_dict() # Trabalhar com dicionário
                    expand_this_diag = (str(row_diag_data.get('Data')) == str(target_diag_to_expand)) # .get() para segurança

                    with st.expander(f"📅 {row_diag_data.get('Data','N/D')} - {row_diag_data.get('Empresa','N/D')}", expanded=expand_this_diag):
                        # ... (conteúdo do expander, usando row_diag_data.get() para segurança)
                        st.markdown('<div class="custom-card" style="padding-top: 10px; padding-bottom: 10px;">', unsafe_allow_html=True)
                        cols_metricas = st.columns(2)
                        mg = row_diag_data.get('Média Geral')
                        gutm = row_diag_data.get('GUT Média')
                        cols_metricas[0].metric("Média Geral", f"{mg:.2f}" if pd.notna(mg) else "N/A")
                        cols_metricas[1].metric("GUT Média (G*U*T)", f"{gutm:.2f}" if pd.notna(gutm) else "N/A")
                        st.write(f"**Resumo (Cliente):** {row_diag_data.get('Diagnóstico', 'N/P')}")
                        # ... restante da lógica do expander, sempre usando .get() para os campos de row_diag_data ...
                        st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Nenhum diagnóstico encontrado para este cliente.")
            if st.session_state.user.get("TotalDiagnosticosRealizados", 0) > 0:
                st.warning("Há um registro de diagnósticos realizados, mas nenhum dado foi carregado. Verifique a consistência do arquivo de diagnósticos.")


    # --- Lógica para "Novo Diagnóstico", "SAC", "Notificações", "Instruções" (mantida como no código anterior)
    elif st.session_state.cliente_page == "Novo Diagnóstico":
        # ... (código da página Novo Diagnóstico - importante aqui é o salvamento e o st.session_state.id_diagnostico_concluido_para_satisfacao)
        st.subheader(menu_options_cli_map_full["Novo Diagnóstico"])
        if st.session_state.diagnostico_enviado_sucesso:
            st.info("Retornando ao painel principal...")
            st.session_state.cliente_page = "Painel Principal"
            st.rerun(); st.stop()
        try: perguntas_df_formulario = pd.read_csv(perguntas_csv, encoding='utf-8')
        except Exception as e: st.error(f"Erro ao carregar perguntas: {e}"); st.stop()
        if perguntas_df_formulario.empty: st.warning("Nenhuma pergunta cadastrada."); st.stop()
        if "Categoria" not in perguntas_df_formulario.columns: perguntas_df_formulario["Categoria"] = "Geral"
        total_perguntas_form = len(perguntas_df_formulario)
        if st.session_state.progresso_diagnostico_contagem[1] != total_perguntas_form:
            st.session_state.progresso_diagnostico_contagem = (st.session_state.progresso_diagnostico_contagem[0], total_perguntas_form)
        progresso_ph_novo = st.empty()
        # ... (funções calcular_e_mostrar_progresso_novo, on_change_resposta_novo) ...
        # (Renderização do formulário de diagnóstico)
        # Dentro do botão "Concluir e Enviar Diagnóstico":
        if st.button("Concluir e Enviar Diagnóstico", key="enviar_diag_final_cliente_v19", icon="✔️", use_container_width=True):
             with st.spinner("Processando e salvando seu diagnóstico..."):
                # ... (lógica de validação e coleta de respostas) ...
                if not respostas_finais_envio_novo.get("__resumo_cliente__","").strip(): # Exemplo de validação
                    st.error("O campo 'Resumo/principais insights (para PDF)' é obrigatório.")
                else:
                    # ... (cálculo de médias) ...
                    id_diagnostico_salvo = st.session_state.id_formulario_atual # Este é o ID do diagnóstico
                    nova_linha_diag_final_n = { # Certifique-se que todas as colunas base estão aqui
                        "Data": id_diagnostico_salvo, "CNPJ": st.session_state.cnpj,
                        "Nome": st.session_state.user.get("NomeContato", st.session_state.cnpj),
                        "Email": st.session_state.user.get("Email", ""), # Adicionar Email se tiver
                        "Empresa": emp_nome_n,
                        "Média Geral": media_geral_n, "GUT Média": gut_media_n,
                        "Observações": respostas_finais_envio_novo.get("__obs_cliente__",""), # Observações do cliente
                        "Diagnóstico": respostas_finais_envio_novo.get("__resumo_cliente__",""), # Resumo do cliente
                        "Análise do Cliente": respostas_finais_envio_novo.get("__obs_cliente__",""), # Repetido? Ou usar outro campo?
                        "Comentarios_Admin": "" # Admin preenche depois
                    }
                    nova_linha_diag_final_n.update(respostas_csv_n)
                    # ... (adicionar Media_Cat_*) ...
                    # Salvar no CSV
                    try:
                        df_todos_diags_n_leitura = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str, 'Data': str})
                    except (FileNotFoundError, pd.errors.EmptyDataError):
                        df_todos_diags_n_leitura = pd.DataFrame(columns=list(nova_linha_diag_final_n.keys())) # Se vazio, usa chaves da nova linha

                    # Garantir que todas as colunas de nova_linha_diag_final_n existam em df_todos_diags_n_leitura
                    for col_add in nova_linha_diag_final_n.keys():
                        if col_add not in df_todos_diags_n_leitura.columns:
                            df_todos_diags_n_leitura[col_add] = pd.NA

                    df_todos_diags_n_escrita = pd.concat([df_todos_diags_n_leitura, pd.DataFrame([nova_linha_diag_final_n])], ignore_index=True)
                    df_todos_diags_n_escrita.to_csv(arquivo_csv, index=False, encoding='utf-8')

                    st.session_state.id_diagnostico_concluido_para_satisfacao = id_diagnostico_salvo
                    # ... (reset de session_state e rerun)
                    st.session_state.diagnostico_enviado_sucesso = True
                    st.session_state.pesquisa_satisfacao_enviada = False
                    st.session_state.cliente_page = "Painel Principal"
                    st.rerun()
    # ... (Outras páginas do cliente: SAC, Notificações, Instruções - mantidas como antes) ...

# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    # ... (código da sidebar e menu do admin - sem alterações relevantes) ...
    if menu_admin == "Visão Geral e Diagnósticos":
        diagnosticos_df_admin_orig_view = pd.DataFrame()
        admin_data_carregada_view_sucesso = False
        try:
            df_temp_admin_diag = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str, 'Data': str})
            cols_numericas_diag_admin = ['Média Geral', 'GUT Média'] + [col for col in df_temp_admin_diag.columns if col.startswith("Media_Cat_")]
            for col_num_adm in cols_numericas_diag_admin:
                if col_num_adm in df_temp_admin_diag.columns:
                    df_temp_admin_diag[col_num_adm] = pd.to_numeric(df_temp_admin_diag[col_num_adm], errors='coerce')
            
            diagnosticos_df_admin_orig_view = df_temp_admin_diag.copy() # Usar a cópia processada

            if 'Data' in diagnosticos_df_admin_orig_view.columns: # 'Data' é o ID string
                diagnosticos_df_admin_orig_view['Data_dt'] = pd.to_datetime(diagnosticos_df_admin_orig_view['Data'], errors='coerce', format='%Y%m%d%H%M%S%f', infer_datetime_format=True) # Tentar formato específico
                # Fallback se o formato específico falhar
                mask_failed_parse = diagnosticos_df_admin_orig_view['Data_dt'].isnull() & diagnosticos_df_admin_orig_view['Data'].notnull()
                if mask_failed_parse.any():
                     diagnosticos_df_admin_orig_view.loc[mask_failed_parse, 'Data_dt'] = pd.to_datetime(diagnosticos_df_admin_orig_view.loc[mask_failed_parse, 'Data'], errors='coerce')


            if not diagnosticos_df_admin_orig_view.empty:
                admin_data_carregada_view_sucesso = True
            else: st.info("Arquivo de diagnósticos lido, mas sem dados ou não pôde ser processado.")
        except pd.errors.EmptyDataError: st.warning(f"Arquivo '{arquivo_csv}' parece vazio ou só com cabeçalhos.")
        except FileNotFoundError: st.error(f"ATENÇÃO: O arquivo de diagnósticos '{arquivo_csv}' não foi encontrado.")
        except Exception as e: st.error(f"ERRO AO CARREGAR DIAGNÓSTICOS (Admin): {e}"); st.exception(e)

        # ... (Restante da Visão Geral do Admin, usando diagnosticos_df_admin_orig_view)
        # KPIs Gerais
        # Gráficos (timeline, engajamento, média de scores) - garantir que usem 'Data_dt' para eixos de tempo
        # Filtros e Análise Detalhada (usar 'Data_dt' para filtros de data)
        # Dentro do loop de expander para diagnósticos detalhados:
        #   df_display_admin = df_diagnosticos_filtrados_view_final_vg.copy()
        #   if 'Data_dt' in df_display_admin.columns:
        #       df_display_admin = df_display_admin.sort_values(by="Data_dt", ascending=False).reset_index(drop=True)
        #   else:
        #       df_display_admin = df_display_admin.sort_values(by="Data", ascending=False).reset_index(drop=True) # Fallback

    # ... (Outras seções do Admin, incluindo as novas para Pesquisa de Satisfação - como no código anterior)
    # Apenas no "Relatório Pesquisa de Satisfação", ao fazer o merge:
    elif menu_admin == "📊 Relatório Pesquisa de Satisfação":
        # ...
        df_diagnosticos_admin_completos_orig = pd.DataFrame()
        try:
            # Ler com 'Data' como string, pois é o ID
            df_diagnosticos_admin_completos_orig = pd.read_csv(arquivo_csv, dtype={'CNPJ': str, 'Data': str})
        except:
            st.error("Não foi possível carregar os diagnósticos para o relatório de satisfação.")

        if not df_diagnosticos_admin_completos_orig.empty:
            # Renomear 'Data' para 'ID_Diagnostico_Cliente' em uma cópia para o merge
            df_diagnosticos_para_merge_satisfacao = df_diagnosticos_admin_completos_orig.rename(
                columns={'Data': 'ID_Diagnostico_Cliente'}
            )
            clientes_com_diagnostico = df_diagnosticos_para_merge_satisfacao[['CNPJ', 'Empresa', 'ID_Diagnostico_Cliente']].drop_duplicates(subset=['CNPJ', 'ID_Diagnostico_Cliente'])
            # ... resto da lógica do relatório de satisfação usando clientes_com_diagnostico ...
    # ...

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()