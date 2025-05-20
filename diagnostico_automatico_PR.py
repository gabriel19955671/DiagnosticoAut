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
import plotly.graph_objects as go # Para gráfico de radar
import uuid

# !!! st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT !!!
st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", initial_sidebar_state="expanded")

# CSS
st.markdown("""
<style>
.login-container { max-width: 400px; margin: 60px auto 0 auto; padding: 40px; border-radius: 8px; background-color: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.15); font-family: 'Segoe UI', sans-serif; }
.login-container h2 { text-align: center; margin-bottom: 30px; font-weight: 600; font-size: 26px; color: #2563eb; }
.stButton>button { border-radius: 6px; background-color: #2563eb; color: white; font-weight: 500; padding: 0.5rem 1.2rem; margin-top: 0.5rem; }
.stDownloadButton>button { background-color: #10b981; color: white; font-weight: 600; border-radius: 6px; margin-top: 10px; padding: 0.5rem 1.2rem; }
.stTextInput>div>input, .stTextArea>div>textarea { border-radius: 6px; padding: 0.4rem; border: 1px solid #d1d5db; background-color: #f9fafb; }
.stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; padding: 10px 20px; }
.custom-card { border: 1px solid #e0e0e0; border-left: 5px solid #2563eb; padding: 15px; margin-bottom: 15px; border-radius: 5px; background-color: #f9f9f9; }
.custom-card h4 { margin-top: 0; color: #2563eb; }
.feedback-saved { font-size: 0.85em; color: green; font-style: italic; margin-top: -8px; margin-bottom: 8px; }
.analise-pergunta-cliente { font-size: 0.9em; color: #555; background-color: #f0f8ff; border-left: 3px solid #1e90ff; padding: 8px; margin-top: 5px; margin-bottom:10px; border-radius: 3px;}
.notification-dot { height: 8px; width: 8px; background-color: red; border-radius: 50%; display: inline-block; margin-left: 5px; }
.kpi-card { background-color: #f9f9f9; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; text-align: center; margin-bottom: 10px; }
.kpi-card h4 { font-size: 1.1em; color: #333; margin-bottom: 5px; }
.kpi-card .value { font-size: 1.8em; font-weight: bold; color: #2563eb; }
</style>
""", unsafe_allow_html=True)

st.title("🔒 Portal de Diagnóstico")

# --- Configuração de Arquivos e Variáveis Globais ---
admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv"
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"
perguntas_csv = "perguntas_formulario.csv"
historico_csv = "historico_clientes.csv"
analises_perguntas_csv = "analises_perguntas.csv"
notificacoes_csv = "notificacoes.csv"
instrucoes_txt_file = "instrucoes_clientes.txt"
LOGOS_DIR = "client_logos"

# --- Inicialização do Session State ---
default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {},
    "confirmou_instrucoes_checkbox_cliente": False
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

# --- Criação e Verificação de Arquivos e Pastas ---
if not os.path.exists(LOGOS_DIR):
    try: os.makedirs(LOGOS_DIR)
    except OSError as e: st.error(f"Erro ao criar diretório de logos '{LOGOS_DIR}': {e}")

colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone",
                         "ConfirmouInstrucoesParaSlotAtual", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados", "LiberacoesExtrasConcedidas"]
colunas_base_perguntas = ["Pergunta", "Categoria"]
colunas_base_analises = ["ID_Analise", "TextoPerguntaOriginal", "TipoCondicao", "CondicaoValorMin", "CondicaoValorMax", "CondicaoValorExato", "TextoAnalise"]
colunas_base_notificacoes = ["ID_Notificacao", "CNPJ_Cliente", "Mensagem", "DataHora", "Lida"]

def inicializar_csv(filepath, columns, defaults=None):
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init = pd.DataFrame(columns=columns)
            if defaults:
                for col, default_val in defaults.items():
                    if col in columns: df_init[col] = default_val
            df_init.to_csv(filepath, index=False, encoding='utf-8')
        else:
            dtype_spec = {}
            if filepath in [usuarios_csv, usuarios_bloqueados_csv, arquivo_csv, notificacoes_csv, historico_csv]:
                if 'CNPJ' in columns: dtype_spec['CNPJ'] = str
                if 'CNPJ_Cliente' in columns: dtype_spec['CNPJ_Cliente'] = str
            
            df_init = pd.read_csv(filepath, encoding='utf-8', dtype=dtype_spec if dtype_spec else None)
            made_changes = False
            expected_cols_df = pd.DataFrame(columns=columns)
            for col_idx, col_name in enumerate(expected_cols_df.columns):
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
    except Exception as e:
        st.error(f"Erro ao inicializar ou ler o arquivo {filepath}: {e}")
        st.info(f"Verifique se o arquivo '{filepath}' não está corrompido ou se o programa tem permissão para acessá-lo.")
        raise

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios,
                    defaults={"ConfirmouInstrucoesParaSlotAtual": "False", "DiagnosticosDisponiveis": 1,
                              "TotalDiagnosticosRealizados": 0, "LiberacoesExtrasConcedidas": 0})
    inicializar_csv(perguntas_csv, colunas_base_perguntas, defaults={"Categoria": "Geral"})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
    inicializar_csv(analises_perguntas_csv, colunas_base_analises)
    inicializar_csv(notificacoes_csv, colunas_base_notificacoes, defaults={"Lida": False})

    if not os.path.exists(instrucoes_txt_file):
        with open(instrucoes_txt_file, "w", encoding="utf-8") as f:
            f.write("""**Bem-vindo ao Portal de Diagnóstico Empresarial!**

Este sistema foi projetado para ajudar a sua empresa a identificar pontos fortes e áreas de melhoria através de um questionário estruturado. Por favor, leia as seguintes instruções cuidadosamente antes de iniciar:

1.  **Preparação**:
    * Reserve um tempo adequado para responder todas as perguntas com atenção. A qualidade das suas respostas impactará diretamente a precisão do diagnóstico.
    * Tenha em mãos informações relevantes sobre os diversos setores da sua empresa (Finanças, Marketing, Operações, RH, etc.), se aplicável.

2.  **Respondendo ao Questionário**:
    * O questionário é dividido em categorias. Procure responder todas as perguntas de cada categoria.
    * **Perguntas de Pontuação (0-5 ou 0-10)**: Avalie o item da pergunta de acordo com a realidade da sua empresa, onde 0 geralmente representa "Não se aplica" ou "Muito Ruim" e a pontuação máxima (5 ou 10) representa "Excelente" ou "Totalmente Implementado".
    * **Matriz GUT (Gravidade, Urgência, Tendência)**: Para estas perguntas, você avaliará três aspectos:
        * **Gravidade (G)**: O quão sério é o impacto do problema/item se não for tratado? (0=Nenhum, 5=Extremamente Grave)
        * **Urgência (U)**: Com que rapidez uma ação precisa ser tomada? (0=Pode esperar, 5=Imediata)
        * **Tendência (T)**: Se nada for feito, o problema tende a piorar, manter-se estável ou melhorar? (0=Melhorar sozinho, 5=Piorar rapidamente)
        * O sistema calculará um score (G x U x T) para priorização.
    * **Perguntas de Texto Aberto**: Forneça respostas claras e concisas, detalhando a situação conforme solicitado.
    * **Perguntas de Escala**: Selecione a opção que melhor descreve a situação na sua empresa (ex: Muito Baixo, Baixo, Médio, Alto, Muito Alto).

3.  **Progresso e Envio**:
    * Seu progresso é salvo automaticamente à medida que você responde.
    * Você pode ver uma barra de progresso indicando quantas perguntas foram respondidas.
    * Ao final, revise suas respostas antes de clicar em "Concluir e Enviar Diagnóstico".
    * **O campo "Resumo/principais insights (para PDF)" é obrigatório.** Preencha com suas considerações gerais sobre o diagnóstico realizado.

4.  **Pós-Diagnóstico**:
    * Após o envio, um PDF do seu diagnóstico será gerado e disponibilizado para download.
    * Você poderá visualizar seus diagnósticos anteriores e acompanhar a evolução no "Painel Principal".
    * O consultor poderá adicionar comentários e análises ao seu diagnóstico, que ficarão visíveis no seu painel.

5.  **Confirmação**:
    * Ao marcar a caixa de seleção abaixo e prosseguir, você declara que leu, compreendeu e concorda em seguir estas instruções para a realização do diagnóstico.

Em caso de dúvidas, entre em contato com o consultor responsável.
""")
except Exception as e_init_global:
    st.error(f"⚠️ ERRO CRÍTICO NA INICIALIZAÇÃO DO APP:")
    st.error(f"Ocorreu um problema ao carregar ou criar os arquivos de dados necessários.")
    st.error(f"Verifique o console/terminal do Streamlit para o traceback completo do Python, se disponível.")
    st.error(f"Detalhes do erro: {e_init_global}")
    st.exception(e_init_global)
    st.warning("A aplicação não pode continuar até que este problema seja resolvido.")
    st.info("""
    Possíveis causas:
    - Um dos arquivos CSV (ex: 'usuarios.csv', 'diagnosticos_clientes.csv') está corrompido.
    - A aplicação não tem permissão para ler/escrever arquivos na pasta onde está rodando.
    - O disco pode estar cheio.
    - Verifique se todos os arquivos CSV esperados existem ou podem ser criados.
    """)
    st.stop()


# --- Funções de Notificação ---
def criar_notificacao(cnpj_cliente, mensagem, data_diag_ref=None):
    try:
        df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df_notificacoes = pd.DataFrame(columns=colunas_base_notificacoes)
    msg_final = mensagem
    if data_diag_ref:
        msg_final = f"O consultor adicionou comentários ao seu diagnóstico de {data_diag_ref}."
    nova_notificacao = {"ID_Notificacao": str(uuid.uuid4()), "CNPJ_Cliente": str(cnpj_cliente), "Mensagem": msg_final, "DataHora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Lida": False}
    df_notificacoes = pd.concat([df_notificacoes, pd.DataFrame([nova_notificacao])], ignore_index=True)
    df_notificacoes.to_csv(notificacoes_csv, index=False, encoding='utf-8')

def get_unread_notifications_count(cnpj_cliente):
    try:
        df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
        unread_count = len(df_notificacoes[(df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente)) & (df_notificacoes['Lida'] == False)])
        return unread_count
    except: return 0

def marcar_notificacoes_como_lidas(cnpj_cliente, ids_notificacoes=None):
    try:
        df_notificacoes = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
        if ids_notificacoes:
            df_notificacoes.loc[(df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente)) & (df_notificacoes['ID_Notificacao'].isin(ids_notificacoes)), 'Lida'] = True
        else:
            df_notificacoes.loc[df_notificacoes['CNPJ_Cliente'] == str(cnpj_cliente), 'Lida'] = True
        df_notificacoes.to_csv(notificacoes_csv, index=False, encoding='utf-8')
        return True
    except Exception as e: st.error(f"Erro ao marcar notificações como lidas: {e}"); return False

# --- Demais Funções Utilitárias ---
def registrar_acao(cnpj, acao, desc):
    try: hist_df = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
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
                if field in ["DiagnosticosDisponiveis", "TotalDiagnosticosRealizados", "LiberacoesExtrasConcedidas"]:
                    st.session_state.user[field] = int(value)
                elif field == "ConfirmouInstrucoesParaSlotAtual":
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
            for cat, media in sorted(medias_cat.items()): pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat}: {media:.2f}")); pdf.ln(1)
            pdf.ln(5)

        for titulo, campo in [("Resumo (Cliente):", "Diagnóstico"), ("Análise (Cliente):", "Análise do Cliente"), ("Comentários (Consultor):", "Comentarios_Admin")]:
            valor = diag_data.get(campo, "")
            if valor and not pd.isna(valor) and str(valor).strip():
                pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output(titulo))
                pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(str(valor))); pdf.ln(3)

        pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 10, pdf_safe_text_output("Respostas Detalhadas e Análises:"))
        categorias = sorted(perguntas_df["Categoria"].unique()) if not perguntas_df.empty and "Categoria" in perguntas_df.columns else []
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
                        except json.JSONDecodeError: pass
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
                        except json.JSONDecodeError: pass
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

def gerar_pdf_historico(df_historico_filtrado, titulo="Histórico de Ações"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, pdf_safe_text_output(titulo), 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    col_widths = {"Data": 35, "CNPJ": 35, "Ação": 40, "Descrição": 75}
    headers_to_print_hist = [col for col in ["Data", "CNPJ", "Ação", "Descrição"] if col in df_historico_filtrado.columns]
    for header in headers_to_print_hist:
        pdf.cell(col_widths.get(header, 30), 10, pdf_safe_text_output(header), 1, 0, "C")
    pdf.ln()
    pdf.set_font("Arial", "", 8)
    line_height = 5
    for _, row in df_historico_filtrado.iterrows():
        current_y_hist = pdf.get_y()
        max_h_row_hist = line_height
        desc_text_hist = str(row.get("Descrição", ""))
        temp_fpdf_h = FPDF(); temp_fpdf_h.add_page(); temp_fpdf_h.set_font("Arial", "", 8)
        desc_lines = temp_fpdf_h.multi_cell(w=col_widths.get("Descrição", 75) - 2, h=line_height, txt=pdf_safe_text_output(desc_text_hist), border=0, align="L", split_only=True)
        max_h_row_hist = max(max_h_row_hist, len(desc_lines) * line_height) + 2
        current_x_for_cell = pdf.l_margin
        for header_idx, header in enumerate(headers_to_print_hist):
            cell_text = str(row.get(header, ""))
            pdf.set_xy(current_x_for_cell, current_y_hist)
            pdf.multi_cell(col_widths.get(header, 30), max_h_row_hist, pdf_safe_text_output(cell_text), border=1, align="L", ln=0)
            current_x_for_cell += col_widths.get(header, 30)
        pdf.set_y(current_y_hist + max_h_row_hist)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf_path = tmpfile.name; pdf.output(pdf_path)
    return pdf_path

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): st.session_state.trigger_rerun_global = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_v15")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador 🔑</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_v15"):
        u = st.text_input("Usuário", key="admin_u_v15"); p = st.text_input("Senha", type="password", key="admin_p_v15")
        if st.form_submit_button("Entrar"):
            try:
                df_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                admin_encontrado = df_creds[df_creds["Usuario"] == u]
                if not admin_encontrado.empty and admin_encontrado.iloc[0]["Senha"] == p:
                    st.session_state.admin_logado = True; st.success("Login de administrador bem-sucedido! ✅"); st.rerun()
                else: st.error("Usuário ou senha inválidos.")
            except FileNotFoundError: st.error(f"Arquivo de credenciais de admin não encontrado: {admin_credenciais_csv}")
            except Exception as e: st.error(f"Erro no login admin: {e}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente 🏢</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_v15"):
        c = st.text_input("CNPJ", key="cli_c_v15", value=st.session_state.get("last_cnpj_input",""))
        s = st.text_input("Senha", type="password", key="cli_s_v15")
        if st.form_submit_button("Entrar"):
            st.session_state.last_cnpj_input = c
            try:
                users_df = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                for col, default_val_user, col_type in [
                    ("ConfirmouInstrucoesParaSlotAtual", "False", str),
                    ("DiagnosticosDisponiveis", 1, int),
                    ("TotalDiagnosticosRealizados", 0, int),
                    ("LiberacoesExtrasConcedidas", 0, int)
                ]:
                    if col not in users_df.columns: users_df[col] = default_val_user
                    if col_type == int:
                        users_df[col] = pd.to_numeric(users_df[col], errors='coerce').fillna(default_val_user).astype(int)
                    else:
                        users_df[col] = users_df[col].astype(str)

                blocked_df = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                if c in blocked_df["CNPJ"].values: st.error("CNPJ bloqueado."); st.stop()

                match = users_df[(users_df["CNPJ"] == c) & (users_df["Senha"] == s)]
                if match.empty: st.error("CNPJ ou senha inválidos."); st.stop()

                st.session_state.cliente_logado = True; st.session_state.cnpj = c
                st.session_state.user = match.iloc[0].to_dict()
                st.session_state.user["ConfirmouInstrucoesParaSlotAtual"] = str(st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", "False")).lower() == "true"
                st.session_state.user["DiagnosticosDisponiveis"] = int(st.session_state.user.get("DiagnosticosDisponiveis", 1))
                st.session_state.user["TotalDiagnosticosRealizados"] = int(st.session_state.user.get("TotalDiagnosticosRealizados", 0))
                st.session_state.user["LiberacoesExtrasConcedidas"] = int(st.session_state.user.get("LiberacoesExtrasConcedidas", 0))

                st.session_state.inicio_sessao_cliente = time.time()
                registrar_acao(c, "Login", "Usuário logou.")

                pode_fazer_novo_login = st.session_state.user["DiagnosticosDisponiveis"] > st.session_state.user["TotalDiagnosticosRealizados"]
                if pode_fazer_novo_login and not st.session_state.user["ConfirmouInstrucoesParaSlotAtual"]:
                    st.session_state.cliente_page = "Instruções"
                elif pode_fazer_novo_login and st.session_state.user["ConfirmouInstrucoesParaSlotAtual"]:
                    st.session_state.cliente_page = "Novo Diagnóstico"
                else:
                    st.session_state.cliente_page = "Painel Principal"

                st.session_state.id_formulario_atual = f"{c}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                st.session_state.respostas_atuais_diagnostico = {}; st.session_state.progresso_diagnostico_percentual = 0; st.session_state.progresso_diagnostico_contagem = (0,0); st.session_state.feedbacks_respostas = {}; st.session_state.diagnostico_enviado_sucesso = False; st.session_state.confirmou_instrucoes_checkbox_cliente = False
                st.success("Login cliente OK! ✅"); st.rerun()
            except FileNotFoundError as fnf_e:
                st.error(f"Erro de configuração: Arquivo {fnf_e.filename} não encontrado. Contate o administrador.")
            except Exception as e: st.error(f"Erro login cliente: {e}"); st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    if "user" not in st.session_state or st.session_state.user is None or \
       "cnpj" not in st.session_state or st.session_state.cnpj is None:
        st.error("Erro de sessão. Por favor, faça o login novamente.")
        keys_to_clear_on_error = ['cliente_logado', 'user', 'cnpj', 'cliente_page', 'respostas_atuais_diagnostico', 'id_formulario_atual', 'progresso_diagnostico_percentual', 'progresso_diagnostico_contagem']
        for key_to_clear in keys_to_clear_on_error:
            if key_to_clear in st.session_state: del st.session_state[key_to_clear]
        for key_d, value_d in default_session_state.items():
            st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False
        st.rerun()

    st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}! 👋")
    with st.sidebar.expander("Meu Perfil", expanded=False):
        logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
        if logo_cliente_path: st.image(logo_cliente_path, width=100)
        st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
        st.write(f"**CNPJ:** {st.session_state.cnpj}")
        st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
        st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")
        diagnosticos_restantes_perfil = st.session_state.user.get('DiagnosticosDisponiveis', 0) - st.session_state.user.get('TotalDiagnosticosRealizados', 0)
        st.write(f"**Diagnósticos Restantes:** {max(0, diagnosticos_restantes_perfil)}")
        st.write(f"**Total Realizados:** {st.session_state.user.get('TotalDiagnosticosRealizados', 0)}")

    unread_notif_count_val = get_unread_notifications_count(st.session_state.cnpj)
    notif_menu_label_val = "🔔 Notificações"
    if unread_notif_count_val > 0: notif_menu_label_val = f"🔔 Notificações ({unread_notif_count_val})"
    menu_options_cli_val = ["📖 Instruções", "📝 Novo Diagnóstico", "📊 Painel Principal", notif_menu_label_val]
    
    pode_fazer_novo_sidebar_val = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
    confirmou_instrucoes_sidebar_val = st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", False)
    instrucoes_pendentes_obrigatorias_val = pode_fazer_novo_sidebar_val and not confirmou_instrucoes_sidebar_val

    st.sidebar.markdown("---")
    st.sidebar.caption(f"DEBUG INFO:")
    st.sidebar.write(f"`ss.cliente_page` (atual): `{st.session_state.cliente_page}`")
    st.sidebar.write(f"`pode_fazer_novo`: `{pode_fazer_novo_sidebar_val}`")
    st.sidebar.write(f"`confirmou_instr`: `{confirmou_instrucoes_sidebar_val}`")
    st.sidebar.write(f"`instr_pend_obrig`: `{instrucoes_pendentes_obrigatorias_val}`")
    
    effective_cliente_page_for_radio_default = st.session_state.cliente_page # Page that radio *should* show as selected initially
    
    if instrucoes_pendentes_obrigatorias_val and st.session_state.cliente_page != "Instruções":
        st.sidebar.error("❗REDIRECIONAMENTO: Para 'Instruções' (pendência obrigatória).")
        effective_cliente_page_for_radio_default = "Instruções"
        # Logic to ensure actual page is also instructions if this override happens before radio interaction
        if st.session_state.cliente_page != "Instruções":
            st.session_state.cliente_page = "Instruções" # Make the override sticky for this run
            # No rerun here, let the current script execution reflect this change.

    st.sidebar.write(f"`effective_page_for_radio`: `{effective_cliente_page_for_radio_default}`")
    st.sidebar.markdown("---")

    current_page_for_radio_display = effective_cliente_page_for_radio_default
    if current_page_for_radio_display == "Notificações": current_page_for_radio_display = notif_menu_label_val
    
    try: current_idx_cli_val = menu_options_cli_val.index(current_page_for_radio_display)
    except ValueError:
        st.sidebar.warning(f"DEBUG: `current_page_for_radio_display` ('{current_page_for_radio_display}') não encontrada no menu. Default para Instruções.")
        current_idx_cli_val = 0
        st.session_state.cliente_page = "Instruções" # Force actual page state as well
    
    selected_page_cli_raw_val = st.sidebar.radio("Menu Cliente", menu_options_cli_val, index=current_idx_cli_val, key="cli_menu_v15_debug")
    selected_page_cli_actual = "Notificações" if "Notificações" in selected_page_cli_raw_val else selected_page_cli_raw_val
    
    # Navigation logic based on user's click
    # Compare clicked value with the current session state page
    if selected_page_cli_actual != st.session_state.cliente_page:
        if instrucoes_pendentes_obrigatorias_val and selected_page_cli_actual != "Instruções":
            st.sidebar.error("⚠️ ACESSO NEGADO! Você deve primeiro ler e confirmar as instruções na página '📖 Instruções' para acessar outras seções ou iniciar um novo diagnóstico.")
            # User is blocked, st.session_state.cliente_page is NOT changed, no rerun. They stay on current page.
        else:
            st.session_state.cliente_page = selected_page_cli_actual
            st.rerun()

    if st.sidebar.button("⬅️ Sair do Portal Cliente", key="logout_cliente_v15"):
        client_keys_to_clear = [k for k in default_session_state.keys() if k not in ['admin_logado']]
        for key_to_clear in client_keys_to_clear:
            if key_to_clear in st.session_state: del st.session_state[key_to_clear]
        for key_d, value_d in default_session_state.items():
             if key_d not in ['admin_logado']: st.session_state[key_d] = value_d
        st.session_state.cliente_logado = False
        st.rerun()

    # --- Conteúdo da Página do Cliente ---
    if st.session_state.cliente_page == "Instruções":
        st.subheader("📖 Instruções do Sistema de Diagnóstico")
        default_instructions_text = """**Bem-vindo ao Portal de Diagnóstico Empresarial!** (Conteúdo completo das instruções aqui...)"""
        instructions_to_display = default_instructions_text
        try:
            if os.path.exists(instrucoes_txt_file) and os.path.getsize(instrucoes_txt_file) > 0:
                with open(instrucoes_txt_file, "r", encoding="utf-8") as f:
                    custom_instructions = f.read()
                    if custom_instructions.strip(): instructions_to_display = custom_instructions
        except Exception as e: st.warning(f"Não foi possível carregar as instruções personalizadas: {e}. Exibindo instruções padrão.")
        st.markdown(instructions_to_display)

        if st.session_state.user:
            pode_fazer_novo_inst_page_val = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            confirmou_inst_atual = st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", False)
            
            if pode_fazer_novo_inst_page_val and not confirmou_inst_atual:
                 st.error("🛑 **AÇÃO NECESSÁRIA:** Para prosseguir para um NOVO DIAGNÓSTICO, você DEVE marcar a caixa de confirmação abaixo e clicar em 'Prosseguir para o Diagnóstico'.")

            if pode_fazer_novo_inst_page_val:
                st.session_state.confirmou_instrucoes_checkbox_cliente = st.checkbox("Declaro que li e compreendi todas as instruções fornecidas para a realização deste diagnóstico.", value=st.session_state.get("confirmou_instrucoes_checkbox_cliente", False), key="confirma_leitura_inst_v15_final_cb")
                if st.button("Prosseguir para o Diagnóstico", key="btn_instrucoes_v15_final_prosseguir", disabled=not st.session_state.confirmou_instrucoes_checkbox_cliente):
                    if st.session_state.confirmou_instrucoes_checkbox_cliente:
                        update_user_data(st.session_state.cnpj, "ConfirmouInstrucoesParaSlotAtual", "True")
                        st.session_state.cliente_page = "Novo Diagnóstico"; st.session_state.confirmou_instrucoes_checkbox_cliente = False; st.rerun()
            else:
                st.info("Você não possui diagnósticos disponíveis no momento para iniciar.")
            
            # Allow navigation to Painel Principal from Instrucoes, respecting pending instructions for *other* pages
            if st.button("Ir para o Painel Principal", key="ir_painel_inst_v15_final_geral"):
                if instrucoes_pendentes_obrigatorias_val: # If still pending for new diag
                     st.sidebar.error("⚠️ ACESSO NEGADO! Finalize as pendências na página '📖 Instruções' (confirme a leitura) para acessar outras seções.")
                     # No rerun, no page change
                else:
                    st.session_state.cliente_page = "Painel Principal"; st.rerun()
        else: st.error("Erro de sessão do usuário. Por favor, faça login novamente.")


    elif st.session_state.cliente_page == "Painel Principal":
        st.success(f"DEBUG: Tentando carregar página: {st.session_state.cliente_page}")
        st.write("DEBUG: Ponto A - Início do Painel Principal")
        st.subheader("📊 Painel Principal do Cliente")
        try: # Wrap entire page content
            if st.session_state.diagnostico_enviado_sucesso:
                st.success("🎯 Seu último diagnóstico foi enviado e processado com sucesso!")
                if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                    try:
                        with open(st.session_state.pdf_gerado_path, "rb") as f_pdf:
                            st.download_button(label="📄 Baixar PDF do Diagnóstico Recém-Enviado", data=f_pdf, file_name=st.session_state.pdf_gerado_filename, mime="application/pdf", key="dl_novo_diag_painel_v15_final_pp")
                    except FileNotFoundError: st.error("Arquivo PDF do diagnóstico recente não encontrado.")
                    except Exception as e_pdf_dl: st.error(f"Erro ao preparar download do PDF: {e_pdf_dl}")
                st.session_state.pdf_gerado_path = None; st.session_state.pdf_gerado_filename = None
                st.session_state.diagnostico_enviado_sucesso = False
            with st.expander("📖 Instruções e Informações", expanded=False):
                st.markdown("- Visualize seus diagnósticos anteriores e sua evolução.\n- Acompanhe seu plano de ação no Kanban.\n- Para um novo diagnóstico (se liberado), selecione 'Novo Diagnóstico' no menu ao lado.")
            st.write("DEBUG: Ponto B - Antes de carregar diagnósticos anteriores")
            st.markdown("#### 📁 Diagnósticos Anteriores")
            df_cliente_diags = pd.DataFrame()
            try:
                if st.session_state.get("cnpj") is None:
                    st.error("Erro: CNPJ do cliente não identificado.")
                elif not os.path.exists(arquivo_csv):
                    st.warning(f"Arquivo de diagnósticos ('{arquivo_csv}') não encontrado.")
                else:
                    df_antigos = pd.read_csv(arquivo_csv, dtype={'CNPJ': str}, encoding='utf-8')
                    if not df_antigos.empty:
                         df_cliente_diags = df_antigos[df_antigos["CNPJ"] == str(st.session_state.cnpj)].copy()
            except pd.errors.EmptyDataError: st.info(f"O arquivo de diagnósticos ('{arquivo_csv}') está vazio.")
            except Exception as e: st.error(f"Erro ao carregar dados para o painel do cliente: {e}"); st.exception(e)

            if df_cliente_diags.empty:
                    if st.session_state.get("cnpj"): st.info("Nenhum diagnóstico anterior encontrado para sua empresa.")
                    st.write("DEBUG: Ponto J - Nenhum diagnóstico para o cliente.")
            else:
                st.write(f"DEBUG: Ponto C - {len(df_cliente_diags)} diagnósticos carregados para o cliente.")
                df_cliente_diags = df_cliente_diags.sort_values(by="Data", ascending=False)
                perguntas_df_para_painel = pd.DataFrame()
                try:
                    if os.path.exists(perguntas_csv):
                        perguntas_df_para_painel = pd.read_csv(perguntas_csv, encoding='utf-8')
                        if "Categoria" not in perguntas_df_para_painel.columns: perguntas_df_para_painel["Categoria"] = "Geral"
                except Exception as e_perg: st.warning(f"Erro ao carregar arquivo de perguntas: {e_perg}")
                analises_df_para_painel = carregar_analises_perguntas()
                for idx_row_diag_original, row_diag_data in df_cliente_diags.iterrows():
                    idx_row_diag = str(idx_row_diag_original) 
                    st.write(f"DEBUG: Ponto D - Processando diagnóstico índice original {idx_row_diag_original}")
                    try:
                        with st.expander(f"📅 {row_diag_data.get('Data','Data Indisp.')} - {row_diag_data.get('Empresa','Empresa Indisp.')}"):
                            # ... (rest of expander content from previous version)
                            cols_metricas = st.columns(2) # Example of content
                            media_geral_val = pd.to_numeric(row_diag_data.get('Média Geral'), errors='coerce')
                            cols_metricas[0].metric("Média Geral", f"{media_geral_val:.2f}" if pd.notna(media_geral_val) else "N/A")
                            # ... (ensure ALL content of the expander is within this try)
                        st.write(f"DEBUG: Ponto E - Fim do expander para diagnóstico índice {idx_row_diag_original}")
                    except Exception as e_diag_expander:
                        st.error(f"Erro ao renderizar detalhes do diagnóstico de {row_diag_data.get('Data', 'data desconhecida')}: {e_diag_expander}")
                        st.exception(e_diag_expander)
                
                st.write("DEBUG: Ponto F - Após loop de diagnósticos")
                # ... (Kanban, Evolução, Comparação - ensure they have try-except or are very robust)
                # For brevity, assuming these sections are robust or have their own try-excepts as in prior versions
                try:
                    st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
                    # ... (Kanban logic) ...
                except Exception as e_kanban: st.error(f"Erro no Kanban: {e_kanban}"); st.exception(e_kanban)
                st.write("DEBUG: Ponto G - Após Kanban")
                
                try:
                    st.subheader("📈 Comparativo de Evolução das Médias")
                    # ... (Evolução logic) ...
                except Exception as e_evol: st.error(f"Erro na Evolução: {e_evol}"); st.exception(e_evol)
                st.write("DEBUG: Ponto H - Após Evolução")

                try:
                    st.subheader("📊 Comparação Detalhada Entre Diagnósticos")
                    # ... (Comparação Detalhada logic) ...
                except Exception as e_comp: st.error(f"Erro na Comparação: {e_comp}"); st.exception(e_comp)
                st.write("DEBUG: Ponto I - Após Comparação Detalhada")
            st.write("DEBUG: Ponto K - FIM do Painel Principal")
        except Exception as e_painel_outer:
            st.error(f"ERRO GERAL NO PAINEL PRINCIPAL: {e_painel_outer}")
            st.exception(e_painel_outer)


    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.success(f"DEBUG: Tentando carregar página: {st.session_state.cliente_page}")
        st.write("DEBUG: Ponto ND_A - Início de Novo Diagnóstico")
        st.subheader("📝 Formulário de Novo Diagnóstico")
        try: # Wrap entire page content
            if not st.session_state.user: st.error("Erro: Dados do usuário não encontrados. Faça login novamente."); st.stop()

            pode_fazer_novo_form = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
            confirmou_inst_form = st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", False)

            if not pode_fazer_novo_form:
                st.warning("❌ Você não tem diagnósticos disponíveis no momento. Para realizar um novo, por favor, entre em contato com o administrador para liberação.")
                if st.button("Voltar ao Painel Principal", key="voltar_painel_novo_diag_bloq_v14_final_nd"): st.session_state.cliente_page = "Painel Principal"; st.rerun()
                st.stop()
            elif not confirmou_inst_form:
                st.warning("⚠️ Por favor, confirme a leitura das instruções na página '📖 Instruções' antes de iniciar um novo diagnóstico.")
                if st.button("Ir para Instruções", key="ir_instrucoes_novo_diag_v14_final_nd"): st.session_state.cliente_page = "Instruções"; st.rerun()
                st.stop()
            st.write("DEBUG: Ponto ND_B - Após checagens de permissão")

            if st.session_state.diagnostico_enviado_sucesso:
                st.success("🎯 Seu diagnóstico foi enviado com sucesso!")
                if st.session_state.pdf_gerado_path and st.session_state.pdf_gerado_filename:
                    try:
                        with open(st.session_state.pdf_gerado_path, "rb") as f_pdf_dl_sucesso:
                            st.download_button(label="📄 Baixar PDF do Diagnóstico Enviado", data=f_pdf_dl_sucesso, file_name=st.session_state.pdf_gerado_filename, mime="application/pdf", key="dl_pdf_sucesso_novo_diag_v14_final_nd")
                    except FileNotFoundError: st.error("Arquivo PDF gerado não encontrado para download.")
                    except Exception as e_dl_new_diag: st.error(f"Erro ao preparar download do PDF: {e_dl_new_diag}")
                if st.button("Ir para o Painel Principal", key="ir_painel_apos_envio_sucesso_v14_final_nd"):
                    st.session_state.cliente_page = "Painel Principal";
                    st.session_state.diagnostico_enviado_sucesso = False;
                    st.session_state.pdf_gerado_path = None;
                    st.session_state.pdf_gerado_filename = None;
                    st.rerun()
                st.stop()
            st.write("DEBUG: Ponto ND_C - Antes de carregar perguntas_df_formulario")

            perguntas_df_formulario = pd.DataFrame()
            try:
                if not os.path.exists(perguntas_csv): st.error(f"Arquivo de perguntas ('{perguntas_csv}') não encontrado. Não é possível iniciar um novo diagnóstico."); st.stop()
                perguntas_df_formulario = pd.read_csv(perguntas_csv, encoding='utf-8')
                if perguntas_df_formulario.empty: st.warning("Nenhuma pergunta cadastrada no sistema. Não é possível iniciar um novo diagnóstico."); st.stop()
                if "Categoria" not in perguntas_df_formulario.columns: perguntas_df_formulario["Categoria"] = "Geral"
            except pd.errors.EmptyDataError: st.error(f"O arquivo de perguntas ('{perguntas_csv}') está vazio ou contém apenas cabeçalhos. Não é possível iniciar um novo diagnóstico."); st.stop()
            except Exception as e: st.error(f"Erro crítico ao carregar formulário de perguntas: {e}"); st.exception(e); st.stop()

            if not perguntas_df_formulario.empty:
                st.write(f"DEBUG: Ponto ND_D - {len(perguntas_df_formulario)} perguntas carregadas.")
                total_perguntas_form = len(perguntas_df_formulario)
                if st.session_state.progresso_diagnostico_contagem[1] != total_perguntas_form: st.session_state.progresso_diagnostico_contagem = (st.session_state.progresso_diagnostico_contagem[0], total_perguntas_form)
                progresso_ph_novo = st.empty()
                def calcular_e_mostrar_progresso_novo():
                    respondidas_novo = 0; total_q_novo = st.session_state.progresso_diagnostico_contagem[1]
                    if total_q_novo == 0: st.session_state.progresso_diagnostico_percentual = 0; progresso_ph_novo.info(f"📊 Progresso: 0 de 0 respondidas (0%)"); return
                    for _, p_row_prog_novo in perguntas_df_formulario.iterrows():
                        p_texto_prog_novo = p_row_prog_novo["Pergunta"]; resp_prog_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_prog_novo)
                        if resp_prog_novo is not None:
                            if "[Matriz GUT]" in p_texto_prog_novo:
                                if isinstance(resp_prog_novo, dict) and (len(resp_prog_novo) == 3 or int(resp_prog_novo.get("G",0)) > 0 or int(resp_prog_novo.get("U",0)) > 0 or int(resp_prog_novo.get("T",0)) > 0): respondidas_novo +=1
                            elif "Escala" in p_texto_prog_novo:
                                if resp_prog_novo != "Selecione": respondidas_novo +=1
                            elif "Texto Aberto" in p_texto_prog_novo:
                                if isinstance(resp_prog_novo, str) and resp_prog_novo.strip() : respondidas_novo +=1
                            elif isinstance(resp_prog_novo, (int,float)) and (any(keyword in p_texto_prog_novo for keyword in ["Pontuação (0-5)", "Pontuação (0-10)"])):
                                 if resp_prog_novo != 0 : respondidas_novo +=1
                    st.session_state.progresso_diagnostico_contagem = (respondidas_novo, total_q_novo); st.session_state.progresso_diagnostico_percentual = round((respondidas_novo / total_q_novo) * 100) if total_q_novo > 0 else 0
                    progresso_ph_novo.info(f"📊 Progresso: {respondidas_novo} de {total_q_novo} respondidas ({st.session_state.progresso_diagnostico_percentual}%)")
                def on_change_resposta_novo(pergunta_txt_key_novo, widget_st_key_novo, tipo_pergunta_onchange_novo):
                    valor_widget_novo = st.session_state.get(widget_st_key_novo)
                    current_gut_novo = st.session_state.respostas_atuais_diagnostico.get(pergunta_txt_key_novo, {"G":0,"U":0,"T":0})
                    if tipo_pergunta_onchange_novo == "GUT_G": current_gut_novo["G"] = valor_widget_novo; st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = current_gut_novo
                    elif tipo_pergunta_onchange_novo == "GUT_U": current_gut_novo["U"] = valor_widget_novo; st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = current_gut_novo
                    elif tipo_pergunta_onchange_novo == "GUT_T": current_gut_novo["T"] = valor_widget_novo; st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = current_gut_novo
                    else: st.session_state.respostas_atuais_diagnostico[pergunta_txt_key_novo] = valor_widget_novo
                    st.session_state.feedbacks_respostas[pergunta_txt_key_novo] = "Resposta registrada ✓"; calcular_e_mostrar_progresso_novo()
                calcular_e_mostrar_progresso_novo()
                for categoria_novo in sorted(perguntas_df_formulario["Categoria"].unique()):
                    st.write(f"DEBUG: Ponto ND_E - Processando categoria {categoria_novo}")
                    st.markdown(f"#### Categoria: {categoria_novo}")
                    perg_cat_df_novo = perguntas_df_formulario[perguntas_df_formulario["Categoria"] == categoria_novo]
                    for idx_novo, row_q_novo in perg_cat_df_novo.iterrows():
                        p_texto_novo = str(row_q_novo["Pergunta"]); w_key_novo = f"q_{st.session_state.id_formulario_atual}_{idx_novo}"; cols_q_feedback = st.columns([0.9, 0.1])
                        st.write(f"DEBUG: Ponto ND_F - Processando pergunta índice {idx_novo}: {p_texto_novo[:30]}...")
                        try:
                            with cols_q_feedback[0]:
                                if "[Matriz GUT]" in p_texto_novo:
                                    st.markdown(f"**{p_texto_novo.replace(' [Matriz GUT]', '')}**"); cols_gut_w_novo = st.columns(3); gut_vals_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_novo, {"G":0,"U":0,"T":0}); key_g_n, key_u_n, key_t_n = f"{w_key_novo}_G", f"{w_key_novo}_U", f"{w_key_novo}_T"
                                    cols_gut_w_novo[0].slider("Gravidade (0-5)",0,5,value=int(gut_vals_novo.get("G",0)), key=key_g_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_g_n, "GUT_G"))
                                    cols_gut_w_novo[1].slider("Urgência (0-5)",0,5,value=int(gut_vals_novo.get("U",0)), key=key_u_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_u_n, "GUT_U"))
                                    cols_gut_w_novo[2].slider("Tendência (0-5)",0,5,value=int(gut_vals_novo.get("T",0)), key=key_t_n, on_change=on_change_resposta_novo, args=(p_texto_novo, key_t_n, "GUT_T"))
                                elif "Pontuação (0-5)" in p_texto_novo: st.slider(p_texto_novo,0,5,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Slider05"))
                                elif "Pontuação (0-10)" in p_texto_novo: st.slider(p_texto_novo,0,10,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Slider010"))
                                elif "Texto Aberto" in p_texto_novo: st.text_area(p_texto_novo,value=str(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,"")), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Texto"))
                                elif "Escala" in p_texto_novo:
                                    opts_novo = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"]; curr_val_novo = st.session_state.respostas_atuais_diagnostico.get(p_texto_novo, "Selecione")
                                    st.selectbox(p_texto_novo, opts_novo, index=opts_novo.index(curr_val_novo) if curr_val_novo in opts_novo else 0, key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "Escala"))
                                else:
                                    st.slider(p_texto_novo.replace("[]","").strip(),0,10,value=int(st.session_state.respostas_atuais_diagnostico.get(p_texto_novo,0)), key=w_key_novo, on_change=on_change_resposta_novo, args=(p_texto_novo, w_key_novo, "SliderDefault"))
                            with cols_q_feedback[1]:
                                if st.session_state.feedbacks_respostas.get(p_texto_novo): st.caption(f'<p class="feedback-saved" style="white-space: nowrap;">{st.session_state.feedbacks_respostas[p_texto_novo]}</p>', unsafe_allow_html=True)
                            st.divider()
                            st.write(f"DEBUG: Ponto ND_G - Fim da pergunta índice {idx_novo}")
                        except Exception as e_widget_creation:
                            st.error(f"Erro ao criar widget para pergunta '{row_q_novo.get('Pergunta', 'desconhecida')}': {e_widget_creation}")
                            st.exception(e_widget_creation)
                st.write("DEBUG: Ponto ND_H - Após loop de perguntas")
                key_obs_cli_n = f"obs_cli_diag_{st.session_state.id_formulario_atual}"; st.text_area("Sua Análise/Observações (opcional):", value=st.session_state.respostas_atuais_diagnostico.get("__obs_cliente__", ""), key=key_obs_cli_n, on_change=on_change_resposta_novo, args=("__obs_cliente__", key_obs_cli_n, "ObsCliente"))
                key_res_cli_n = f"diag_resumo_diag_{st.session_state.id_formulario_atual}"; st.text_area("✍️ Resumo/principais insights (para PDF):", value=st.session_state.respostas_atuais_diagnostico.get("__resumo_cliente__", ""), key=key_res_cli_n, on_change=on_change_resposta_novo, args=("__resumo_cliente__", key_res_cli_n, "ResumoCliente"))
                if st.button("✔️ Concluir e Enviar Diagnóstico", key="enviar_diag_final_cliente_v14_final_nd"):
                    respostas_finais_envio_novo = st.session_state.respostas_atuais_diagnostico; cont_resp_n, total_para_resp_n = st.session_state.progresso_diagnostico_contagem
                    if cont_resp_n < total_para_resp_n: st.warning("Por favor, responda todas as perguntas para um diagnóstico completo.")
                    elif not respostas_finais_envio_novo.get("__resumo_cliente__","").strip(): st.error("O campo 'Resumo/principais insights (para PDF)' é obrigatório.")
                    else:
                        # ... (submission logic as before) ...
                        soma_gut_n, count_gut_n = 0,0; respostas_csv_n = {}
                        for p_n,r_n in respostas_finais_envio_novo.items():
                            if p_n.startswith("__"): continue
                            if "[Matriz GUT]" in p_n and isinstance(r_n, dict): respostas_csv_n[p_n] = json.dumps(r_n); g_n,u_n,t_n = int(r_n.get("G",0)), int(r_n.get("U",0)), int(r_n.get("T",0)); soma_gut_n += (g_n*u_n*t_n); count_gut_n +=1
                            else: respostas_csv_n[p_n] = r_n
                        gut_media_n = round(soma_gut_n/count_gut_n,2) if count_gut_n > 0 else 0.0;
                        num_resp_n = [v_n for k_n,v_n in respostas_finais_envio_novo.items() if not k_n.startswith("__") and isinstance(v_n,(int,float)) and ("[Matriz GUT]" not in k_n) and (any(keyword in k_n for keyword in ["Pontuação (0-5)", "Pontuação (0-10)"]))];
                        media_geral_n = round(sum(num_resp_n)/len(num_resp_n),2) if num_resp_n else 0.0; emp_nome_n = st.session_state.user.get("Empresa","N/D")
                        nova_linha_diag_final_n = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": st.session_state.cnpj, "Nome": st.session_state.user.get("NomeContato", st.session_state.cnpj), "Email": "", "Empresa": emp_nome_n, "Média Geral": media_geral_n, "GUT Média": gut_media_n, "Observações": "", "Análise do Cliente": respostas_finais_envio_novo.get("__obs_cliente__",""), "Diagnóstico": respostas_finais_envio_novo.get("__resumo_cliente__",""), "Comentarios_Admin": "" }; nova_linha_diag_final_n.update(respostas_csv_n); medias_cat_final_n = {}
                        for cat_iter_n in perguntas_df_formulario["Categoria"].unique():
                            soma_c_n, cont_c_n = 0,0
                            for _,pr_n in perguntas_df_formulario[perguntas_df_formulario["Categoria"]==cat_iter_n].iterrows():
                                pt_n = pr_n["Pergunta"]; rv_n = respostas_finais_envio_novo.get(pt_n)
                                if isinstance(rv_n,(int,float)) and ("[Matriz GUT]" not in pt_n) and (any(keyword in pt_n for keyword in ["Pontuação (0-5)", "Pontuação (0-10)"])): soma_c_n+=rv_n; cont_c_n+=1
                            mc_n = round(soma_c_n/cont_c_n,2) if cont_c_n>0 else 0.0; nova_linha_diag_final_n[f"Media_Cat_{sanitize_column_name(cat_iter_n)}"] = mc_n; medias_cat_final_n[cat_iter_n] = mc_n
                        try: df_todos_diags_n = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                        except (FileNotFoundError, pd.errors.EmptyDataError): df_todos_diags_n = pd.DataFrame()
                        for col_n_n in nova_linha_diag_final_n.keys():
                            if col_n_n not in df_todos_diags_n.columns: df_todos_diags_n[col_n_n] = pd.NA
                        df_todos_diags_n = pd.concat([df_todos_diags_n, pd.DataFrame([nova_linha_diag_final_n])], ignore_index=True); df_todos_diags_n.to_csv(arquivo_csv, index=False, encoding='utf-8')
                        total_realizados_atual = st.session_state.user.get("TotalDiagnosticosRealizados", 0); update_user_data(st.session_state.cnpj, "TotalDiagnosticosRealizados", total_realizados_atual + 1)
                        update_user_data(st.session_state.cnpj, "ConfirmouInstrucoesParaSlotAtual", "False")
                        registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", "Cliente enviou novo diagnóstico."); analises_df_para_pdf_n = carregar_analises_perguntas()
                        pdf_path_gerado_n = gerar_pdf_diagnostico_completo(nova_linha_diag_final_n, st.session_state.user, perguntas_df_formulario, respostas_finais_envio_novo, medias_cat_final_n, analises_df_para_pdf_n)
                        st.session_state.diagnostico_enviado_sucesso = True
                        if pdf_path_gerado_n: st.session_state.pdf_gerado_path = pdf_path_gerado_n; st.session_state.pdf_gerado_filename = f"diagnostico_{sanitize_column_name(emp_nome_n)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        else: st.warning("Diagnóstico salvo, mas houve um erro ao gerar o PDF.")
                        st.session_state.respostas_atuais_diagnostico = {}; st.session_state.progresso_diagnostico_percentual = 0; st.session_state.progresso_diagnostico_contagem = (0,total_perguntas_form); st.session_state.feedbacks_respostas = {}; st.rerun()
            else:
                st.write("DEBUG: Ponto ND_I - Nenhuma pergunta de formulário (este ponto não deveria ser alcançado se o st.stop() anterior funcionou).")
            st.write("DEBUG: Ponto ND_J - FIM de Novo Diagnóstico")
        except Exception as e_novo_diag_outer:
            st.error(f"ERRO GERAL NO NOVO DIAGNÓSTICO: {e_novo_diag_outer}")
            st.exception(e_novo_diag_outer)


    elif st.session_state.cliente_page == "Notificações":
        st.subheader("🔔 Minhas Notificações")
        try:
            df_notif_cliente_view = pd.read_csv(notificacoes_csv, dtype={'CNPJ_Cliente': str}, encoding='utf-8')
            df_notif_cliente_view = df_notif_cliente_view[df_notif_cliente_view['CNPJ_Cliente'] == st.session_state.cnpj]
            if not df_notif_cliente_view.empty: df_notif_cliente_view['DataHora'] = pd.to_datetime(df_notif_cliente_view['DataHora']); df_notif_cliente_view = df_notif_cliente_view.sort_values(by="DataHora", ascending=False)
        except (FileNotFoundError, pd.errors.EmptyDataError): df_notif_cliente_view = pd.DataFrame()
        if df_notif_cliente_view.empty: st.info("Você não tem nenhuma notificação no momento.")
        else:
            ids_nao_lidas_para_marcar_view = []
            for _, row_notif_view in df_notif_cliente_view.iterrows():
                lida_status_view = "Lida" if row_notif_view['Lida'] else "Nova!"; cor_status_view = "green" if row_notif_view['Lida'] else "red"
                st.markdown(f"""<div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-bottom: 10px; {'font-weight: bold;' if not row_notif_view['Lida'] else ''}"> <small>{pd.to_datetime(row_notif_view['DataHora']).strftime('%d/%m/%Y %H:%M')} - <span style="color:{cor_status_view};">{lida_status_view}</span></small><br> {row_notif_view['Mensagem']} </div> """, unsafe_allow_html=True)
                if not row_notif_view['Lida']: ids_nao_lidas_para_marcar_view.append(row_notif_view['ID_Notificacao'])
            if ids_nao_lidas_para_marcar_view:
                if 'notif_page_loaded_once_v14_final_c' not in st.session_state:
                    if marcar_notificacoes_como_lidas(st.session_state.cnpj, ids_notificacoes=ids_nao_lidas_para_marcar_view):
                        st.session_state.notif_page_loaded_once_v14_final_c = True;
                        st.rerun()
            elif 'notif_page_loaded_once_v14_final_c' in st.session_state and not ids_nao_lidas_para_marcar_view:
                 del st.session_state.notif_page_loaded_once_v14_final_c

# --- ÁREA DO ADMINISTRADOR LOGADO ---
# (Restante do código do admin permanece o mesmo, não incluído aqui para brevidade, mas deve ser mantido no seu script)
if aba == "Administrador" and st.session_state.admin_logado:
    # ... (Todo o seu código da área do administrador aqui) ...
    # (Certifique-se de que ele está completo e correto)
    # Exemplo de placeholder para o código do admin:
    st.header("Área Administrativa")
    st.write("Funcionalidades do administrador seriam exibidas aqui.")
    # Cole o código completo do seu admin aqui. Eu omiti para não exceder o limite de tamanho,
    # mas ele deve estar presente no seu arquivo final.
    # O código do admin fornecido anteriormente é extenso e deve ser reinserido aqui.
    # Por exemplo, começando com:
    # try:
    #     try: st.sidebar.image("https://via.placeholder.com/150x75.png?text=Sua+Logo+Admin", width=150)
    #     # ... e assim por diante ...
    # except Exception as e_outer_admin_critical:
    #     st.error(f"Um erro crítico e inesperado ocorreu na área administrativa: {e_outer_admin_critical}")
    #     st.exception(e_outer_admin_critical)
    # (COLE SEU CÓDIGO DE ADMIN COMPLETO AQUI)
    pass # Placeholder para o código do admin

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")