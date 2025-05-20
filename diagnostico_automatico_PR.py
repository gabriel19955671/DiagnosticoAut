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
    st.sidebar.caption(f"DEBUG INFO (Barra Lateral):")
    st.sidebar.write(f"`ss.cliente_page` (atual): `{st.session_state.cliente_page}`")
    st.sidebar.write(f"`pode_fazer_novo`: `{pode_fazer_novo_sidebar_val}`")
    st.sidebar.write(f"`confirmou_instr`: `{confirmou_instrucoes_sidebar_val}`")
    st.sidebar.write(f"`instr_pend_obrig`: `{instrucoes_pendentes_obrigatorias_val}`")
    
    effective_cliente_page_for_radio_default = st.session_state.cliente_page
    
    if instrucoes_pendentes_obrigatorias_val and st.session_state.cliente_page != "Instruções":
        st.sidebar.error("❗REDIRECIONAMENTO AUTOMÁTICO: Para 'Instruções' (pendência obrigatória).")
        effective_cliente_page_for_radio_default = "Instruções"
        if st.session_state.cliente_page != "Instruções":
            st.session_state.cliente_page = "Instruções" # Make the override sticky for this run's display logic

    st.sidebar.write(f"`effective_page_for_radio`: `{effective_cliente_page_for_radio_default}`")
    st.sidebar.markdown("---")

    current_page_for_radio_display = effective_cliente_page_for_radio_default
    if current_page_for_radio_display == "Notificações": current_page_for_radio_display = notif_menu_label_val
    
    try: current_idx_cli_val = menu_options_cli_val.index(current_page_for_radio_display)
    except ValueError:
        st.sidebar.warning(f"DEBUG: `current_page_for_radio_display` ('{current_page_for_radio_display}') não encontrada no menu. Default para Instruções.")
        current_idx_cli_val = 0
        if st.session_state.cliente_page != "Instruções":
            st.session_state.cliente_page = "Instruções"
            # Consider if a rerun is needed here if this state is unexpected.
            # For now, let the current script try to render "Instruções".

    selected_page_cli_raw_val = st.sidebar.radio("Menu Cliente", menu_options_cli_val, index=current_idx_cli_val, key="cli_menu_v15_debug_radio")
    selected_page_cli_actual = "Notificações" if "Notificações" in selected_page_cli_raw_val else selected_page_cli_raw_val
    
    if selected_page_cli_actual != st.session_state.cliente_page:
        if instrucoes_pendentes_obrigatorias_val and selected_page_cli_actual != "Instruções":
            st.sidebar.error("⚠️ ACESSO NEGADO! Você deve primeiro ler e confirmar as instruções na página '📖 Instruções' para acessar outras seções ou iniciar um novo diagnóstico.")
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
        default_instructions_text_content = """**Bem-vindo ao Portal de Diagnóstico Empresarial!** (Conteúdo completo das instruções aqui...)""" # Substitua pelo seu texto completo
        instructions_to_display = default_instructions_text_content
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
            
            if st.button("Ir para o Painel Principal", key="ir_painel_inst_v15_final_geral"):
                _pode_fazer_novo_check = st.session_state.user.get("DiagnosticosDisponiveis", 0) > st.session_state.user.get("TotalDiagnosticosRealizados", 0)
                _confirmou_instr_check = st.session_state.user.get("ConfirmouInstrucoesParaSlotAtual", False)
                _instr_pendentes_check = _pode_fazer_novo_check and not _confirmou_instr_check
                if _instr_pendentes_check:
                     st.error("⚠️ Você precisa confirmar as instruções acima antes de ir para o Painel Principal, pois um novo diagnóstico está disponível e pendente de confirmação.")
                else:
                    st.session_state.cliente_page = "Painel Principal"; st.rerun()
        else: st.error("Erro de sessão do usuário. Por favor, faça login novamente.")


    elif st.session_state.cliente_page == "Painel Principal":
        st.error(f"ALERTA DE DEPURAÇÃO: SE VOCÊ VÊ ISTO, O BLOCO DA PÁGINA 'Painel Principal' FOI ALCANÇADO!") # << NOVO
        st.success(f"DEBUG: Tentando carregar página: {st.session_state.cliente_page}")
        st.write("DEBUG: Ponto PP_A - Início do Painel Principal")
        st.subheader("📊 Painel Principal do Cliente")
        
        st.info("Conteúdo do Painel Principal está temporariamente SIMPLIFICADO para depuração.")
        st.write("Se você vê esta mensagem, significa que o código está entrando corretamente no bloco do Painel Principal.")
        st.write("O conteúdo original foi comentado para ajudar a isolar o problema.")
        st.write("Se esta mensagem aparecer, o problema está no código que foi comentado abaixo.")

        # ----- TODO O CONTEÚDO ORIGINAL DO PAINEL PRINCIPAL FOI COMENTADO ABAIXO -----
        # ----- DESCOMENTE SEÇÕES GRADUALMENTE PARA ENCONTRAR O ERRO -----
        """
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
        # ... (toda a lógica de carregamento e exibição de df_cliente_diags, incluindo o loop e gráficos) ...
        st.write("DEBUG: Ponto J - (localização aproximada)") 
        """
        st.write("DEBUG: Ponto PP_K - FIM do Painel Principal (simplificado)")


    elif st.session_state.cliente_page == "Novo Diagnóstico":
        st.error(f"ALERTA DE DEPURAÇÃO: SE VOCÊ VÊ ISTO, O BLOCO DA PÁGINA 'Novo Diagnóstico' FOI ALCANÇADO!") # << NOVO
        st.success(f"DEBUG: Tentando carregar página: {st.session_state.cliente_page}")
        st.write("DEBUG: Ponto ND_A - Início de Novo Diagnóstico")
        st.subheader("📝 Formulário de Novo Diagnóstico")

        st.info("Conteúdo do Novo Diagnóstico está temporariamente SIMPLIFICADO para depuração.")
        st.write("Se você vê esta mensagem, significa que o código está entrando corretamente no bloco do Novo Diagnóstico após as verificações de permissão.")
        st.write("O conteúdo original do formulário foi comentado para ajudar a isolar o problema.")
        
        # Verificações de permissão (essas precisam rodar)
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
        
        # ----- TODO O CONTEÚDO ORIGINAL DO FORMULÁRIO FOI COMENTADO ABAIXO -----
        # ----- DESCOMENTE SEÇÕES GRADUALMENTE PARA ENCONTRAR O ERRO -----
        """
        if st.session_state.diagnostico_enviado_sucesso:
            # ... (bloco do diagnostico_enviado_sucesso) ...
            st.stop()
        st.write("DEBUG: Ponto ND_C - Antes de carregar perguntas_df_formulario")
        
        perguntas_df_formulario = pd.DataFrame()
        # ... (lógica de carregamento de perguntas_df_formulario) ...

        if not perguntas_df_formulario.empty:
            st.write(f"DEBUG: Ponto ND_D - {len(perguntas_df_formulario)} perguntas carregadas.")
            # ... (barra de progresso, loop de categorias e perguntas para criar o formulário) ...
            st.write("DEBUG: Ponto ND_H - Após loop de perguntas (se existiu)")
            # ... (campos de texto para observações e resumo, botão de enviar) ...
        else:
            st.warning("DEBUG: Nenhuma pergunta de formulário encontrada (após tentativa de carga e checagens).")
            st.write("DEBUG: Ponto ND_I - Nenhuma pergunta de formulário.")
        """    
        st.write("DEBUG: Ponto ND_J - FIM de Novo Diagnóstico (simplificado)")


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
if aba == "Administrador" and st.session_state.admin_logado:
    try:
        try: st.sidebar.image("https://via.placeholder.com/150x75.png?text=Sua+Logo+Admin", width=150)
        except Exception as e_img_admin: st.sidebar.caption(f"Logo admin não carregada: {e_img_admin}")
        st.sidebar.success("🟢 Admin Logado")
        if st.sidebar.button("🚪 Sair do Painel Admin", key="logout_admin_v14_final_adm"): st.session_state.admin_logado = False; st.rerun()
        menu_admin_options = ["📊 Visão Geral e Diagnósticos", "🚦 Status dos Clientes", "📜 Histórico de Usuários",
                              "📝 Gerenciar Perguntas", "💡 Gerenciar Análises de Perguntas",
                              "✍️ Gerenciar Instruções Clientes",
                              "👥 Gerenciar Clientes", "👮 Gerenciar Administradores", "💾 Backup de Dados"]
        menu_admin = st.sidebar.selectbox("Funcionalidades Admin:", menu_admin_options, key="admin_menu_selectbox_v14_final_adm")
        st.header(f"{menu_admin.split(' ')[0]} {menu_admin.split(' ', 1)[1]}")
        df_usuarios_admin_geral = pd.DataFrame(columns=colunas_base_usuarios)
        try:
            df_usuarios_admin_temp_load = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
            for col, default, dtype_col in [("ConfirmouInstrucoesParaSlotAtual", "False", str), ("DiagnosticosDisponiveis", 1, int), ("TotalDiagnosticosRealizados", 0, int), ("LiberacoesExtrasConcedidas", 0, int)]:
                if col not in df_usuarios_admin_temp_load.columns: df_usuarios_admin_temp_load[col] = default
                if dtype_col == int: df_usuarios_admin_temp_load[col] = pd.to_numeric(df_usuarios_admin_temp_load[col], errors='coerce').fillna(default).astype(int)
                else: df_usuarios_admin_temp_load[col] = df_usuarios_admin_temp_load[col].astype(str)
            df_usuarios_admin_geral = df_usuarios_admin_temp_load
        except FileNotFoundError: st.sidebar.error(f"Arquivo de usuários '{usuarios_csv}' não encontrado.")
        except Exception as e_load_users_adm_global: st.sidebar.error(f"Erro ao carregar usuários para admin: {e_load_users_adm_global}")

        diagnosticos_df_admin_orig_view = pd.DataFrame()
        admin_data_carregada_view_sucesso = False
        if not os.path.exists(arquivo_csv): st.error(f"ATENÇÃO: O arquivo de diagnósticos '{arquivo_csv}' não foi encontrado.")
        elif os.path.getsize(arquivo_csv) == 0: st.warning(f"O arquivo de diagnósticos '{arquivo_csv}' está vazio.")
        else:
            try:
                diagnosticos_df_admin_orig_view = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ': str})
                if 'Data' in diagnosticos_df_admin_orig_view.columns: diagnosticos_df_admin_orig_view['Data'] = pd.to_datetime(diagnosticos_df_admin_orig_view['Data'], errors='coerce')
                if not diagnosticos_df_admin_orig_view.empty: admin_data_carregada_view_sucesso = True
            except pd.errors.EmptyDataError: st.warning(f"Arquivo de diagnósticos '{arquivo_csv}' parece vazio ou contém apenas cabeçalhos.")
            except Exception as e_adm_load_diag: st.error(f"ERRO AO CARREGAR ARQUIVO DE DIAGNÓSTICOS ('{arquivo_csv}'): {e_adm_load_diag}"); st.exception(e_adm_load_diag)

        try: # Admin menu dispatch
            if menu_admin == "📊 Visão Geral e Diagnósticos":
                st.subheader("Visão Geral e Indicadores de Diagnósticos")
                st.markdown("#### Métricas Gerais do Sistema (Todos os Clientes)")
                col_mg1_vg, col_mg2_vg, col_mg3_vg, col_mg4_vg = st.columns(4)
                total_clientes_cadastrados_vg = len(df_usuarios_admin_geral) if not df_usuarios_admin_geral.empty else 0
                with col_mg1_vg: st.markdown(f"<div class='kpi-card'><h4>👥 Clientes Cadastrados</h4><p class='value'>{total_clientes_cadastrados_vg}</p></div>", unsafe_allow_html=True)
                if admin_data_carregada_view_sucesso and not diagnosticos_df_admin_orig_view.empty:
                    total_diagnosticos_sistema_vg = len(diagnosticos_df_admin_orig_view); media_geral_global_adm_vg = pd.to_numeric(diagnosticos_df_admin_orig_view.get("Média Geral"), errors='coerce').mean(); gut_media_global_adm_vg = pd.to_numeric(diagnosticos_df_admin_orig_view.get("GUT Média"), errors='coerce').mean()
                    with col_mg2_vg: st.markdown(f"<div class='kpi-card'><h4>📋 Total de Diagnósticos</h4><p class='value'>{total_diagnosticos_sistema_vg}</p></div>", unsafe_allow_html=True)
                    with col_mg3_vg: st.markdown(f"<div class='kpi-card'><h4>📈 Média Geral Global</h4><p class='value'>{media_geral_global_adm_vg:.2f if pd.notna(media_geral_global_adm_vg) else 'N/A'}</p></div>", unsafe_allow_html=True)
                    with col_mg4_vg: st.markdown(f"<div class='kpi-card'><h4>🔥 GUT Média Global</h4><p class='value'>{gut_media_global_adm_vg:.2f if pd.notna(gut_media_global_adm_vg) else 'N/A'}</p></div>", unsafe_allow_html=True)
                else:
                    with col_mg2_vg: st.markdown(f"<div class='kpi-card'><h4>📋 Total de Diagnósticos</h4><p class='value'>0</p></div>", unsafe_allow_html=True)
                    with col_mg3_vg: st.markdown(f"<div class='kpi-card'><h4>📈 Média Geral Global</h4><p class='value'>N/A</p></div>", unsafe_allow_html=True)
                    with col_mg4_vg: st.markdown(f"<div class='kpi-card'><h4>🔥 GUT Média Global</h4><p class='value'>N/A</p></div>", unsafe_allow_html=True)
                st.divider()
                st.markdown("#### Filtros para Análise Detalhada de Diagnósticos")
                col_f1_vg, col_f2_vg, col_f3_vg = st.columns(3)
                empresas_lista_admin_filtro_vg = sorted(df_usuarios_admin_geral["Empresa"].astype(str).unique().tolist()) if not df_usuarios_admin_geral.empty and "Empresa" in df_usuarios_admin_geral.columns else []
                with col_f1_vg: emp_sel_admin_vg = st.selectbox("Filtrar por Empresa:", ["Todos os Clientes"] + empresas_lista_admin_filtro_vg, key="admin_filtro_emp_v14_final_vg")
                with col_f2_vg: dt_ini_admin_vg = st.date_input("Data Início dos Diagnósticos:", value=None, key="admin_dt_ini_v14_final_vg")
                with col_f3_vg: dt_fim_admin_vg = st.date_input("Data Fim dos Diagnósticos:", value=None, key="admin_dt_fim_v14_final_vg")
                st.divider()
                df_diagnosticos_contexto_filtro_vg = diagnosticos_df_admin_orig_view.copy() if admin_data_carregada_view_sucesso and not diagnosticos_df_admin_orig_view.empty else pd.DataFrame(columns=colunas_base_diagnosticos)
                df_usuarios_contexto_filtro_vg = df_usuarios_admin_geral.copy()
                if emp_sel_admin_vg != "Todos os Clientes":
                    if not df_diagnosticos_contexto_filtro_vg.empty: df_diagnosticos_contexto_filtro_vg = df_diagnosticos_contexto_filtro_vg[df_diagnosticos_contexto_filtro_vg["Empresa"] == emp_sel_admin_vg]
                    if not df_usuarios_contexto_filtro_vg.empty: df_usuarios_contexto_filtro_vg = df_usuarios_contexto_filtro_vg[df_usuarios_contexto_filtro_vg["Empresa"] == emp_sel_admin_vg]

                df_diagnosticos_filtrados_view_final_vg = df_diagnosticos_contexto_filtro_vg.copy()
                if not df_diagnosticos_filtrados_view_final_vg.empty and 'Data' in df_diagnosticos_filtrados_view_final_vg.columns:
                    if dt_ini_admin_vg: df_diagnosticos_filtrados_view_final_vg = df_diagnosticos_filtrados_view_final_vg[df_diagnosticos_filtrados_view_final_vg['Data'] >= pd.to_datetime(dt_ini_admin_vg)]
                    if dt_fim_admin_vg: df_diagnosticos_filtrados_view_final_vg = df_diagnosticos_filtrados_view_final_vg[df_diagnosticos_filtrados_view_final_vg['Data'] < pd.to_datetime(dt_fim_admin_vg) + pd.Timedelta(days=1)]
                st.markdown(f"#### Análise para: **{emp_sel_admin_vg}** (Período de Diagnósticos: {dt_ini_admin_vg or 'Início'} a {dt_fim_admin_vg or 'Fim'})")
                cnpjs_usuarios_no_contexto_empresa_vg = set(df_usuarios_contexto_filtro_vg['CNPJ'].unique()) if not df_usuarios_contexto_filtro_vg.empty else set()
                cnpjs_com_diagnostico_no_periodo_e_empresa_vg = set(df_diagnosticos_filtrados_view_final_vg['CNPJ'].unique()) if not df_diagnosticos_filtrados_view_final_vg.empty else set()
                clientes_sem_diagnostico_final_vg = len(cnpjs_usuarios_no_contexto_empresa_vg - cnpjs_com_diagnostico_no_periodo_e_empresa_vg)
                clientes_com_pelo_menos_um_diag_final_vg = len(cnpjs_com_diagnostico_no_periodo_e_empresa_vg)
                clientes_com_mais_de_um_diag_final_vg = 0
                if not df_diagnosticos_filtrados_view_final_vg.empty: contagem_diag_por_cliente_final_vg = df_diagnosticos_filtrados_view_final_vg.groupby('CNPJ').size(); clientes_com_mais_de_um_diag_final_vg = len(contagem_diag_por_cliente_final_vg[contagem_diag_por_cliente_final_vg > 1])
                col_pm1_f_vg, col_pm2_f_vg, col_pm3_f_vg = st.columns(3)
                with col_pm1_f_vg: st.markdown(f"<div class='kpi-card'><h4>Clientes SEM Diag. (filtro)</h4><p class='value'>{clientes_sem_diagnostico_final_vg}</p></div>", unsafe_allow_html=True)
                with col_pm2_f_vg: st.markdown(f"<div class='kpi-card'><h4>Clientes COM Diag. (filtro)</h4><p class='value'>{clientes_com_pelo_menos_um_diag_final_vg}</p></div>", unsafe_allow_html=True)
                with col_pm3_f_vg: st.markdown(f"<div class='kpi-card'><h4>Clientes COM MAIS DE 1 Diag. (filtro)</h4><p class='value'>{clientes_com_mais_de_um_diag_final_vg}</p></div>", unsafe_allow_html=True)
                st.divider()
                if not admin_data_carregada_view_sucesso or df_diagnosticos_admin_orig_view.empty : st.warning("Nenhum dado de diagnóstico foi carregado. Funcionalidades de visualização detalhada estão limitadas.")
                elif df_diagnosticos_filtrados_view_final_vg.empty: st.info(f"Nenhum diagnóstico encontrado para os filtros aplicados.")
                else:
                    st.markdown(f"##### Indicadores da Seleção Filtrada de Diagnósticos")
                    col_if_adm1_vg, col_if_adm2_vg, col_if_adm3_vg = st.columns(3)
                    with col_if_adm1_vg: st.markdown(f"<div class='kpi-card'><h4>📦 Diags. na Seleção</h4><p class='value'>{len(df_diagnosticos_filtrados_view_final_vg)}</p></div>", unsafe_allow_html=True)
                    media_geral_filtrada_adm_vg = pd.to_numeric(df_diagnosticos_filtrados_view_final_vg.get("Média Geral"), errors='coerce').mean()
                    with col_if_adm2_vg: st.markdown(f"<div class='kpi-card'><h4>📈 Média Geral Seleção</h4><p class='value'>{media_geral_filtrada_adm_vg:.2f if pd.notna(media_geral_filtrada_adm_vg) else 'N/A'}</p></div>", unsafe_allow_html=True)
                    gut_media_filtrada_adm_vg = pd.to_numeric(df_diagnosticos_filtrados_view_final_vg.get("GUT Média"), errors='coerce').mean()
                    with col_if_adm3_vg: st.markdown(f"<div class='kpi-card'><h4>🔥 GUT Média Seleção</h4><p class='value'>{gut_media_filtrada_adm_vg:.2f if pd.notna(gut_media_filtrada_adm_vg) else 'N/A'}</p></div>", unsafe_allow_html=True)
                    st.divider()
                    st.markdown(f"##### Diagnósticos Detalhados (Seleção Filtrada)")
                    st.dataframe(df_diagnosticos_filtrados_view_final_vg.sort_values(by="Data", ascending=False).reset_index(drop=True))
                    st.markdown("##### 🔍 Detalhar, Comentar e Baixar PDF de Diagnóstico Específico")
                    if not df_diagnosticos_filtrados_view_final_vg.empty:
                        diagnosticos_para_detalhe_admin = df_diagnosticos_filtrados_view_final_vg.apply(lambda row: f"{pd.to_datetime(row['Data']).strftime('%Y-%m-%d %H:%M') if pd.notna(row['Data']) else 'Data Inv.'} - {row.get('Empresa','N/A')} (Índice Original: {row.name})", axis=1).tolist()
                        diag_selecionado_str_admin = st.selectbox("Selecione um Diagnóstico para Detalhar:", [""] + diagnosticos_para_detalhe_admin, key="admin_select_diag_detalhe_v14_final")
                        if diag_selecionado_str_admin:
                            try:
                                diag_original_index_admin = int(diag_selecionado_str_admin.split("(Índice Original: ")[1].replace(")", ""))
                                diag_row_detalhe_admin = diagnosticos_df_admin_orig_view.loc[diag_original_index_admin]
                                st.markdown(f"###### Detalhes do Diagnóstico: {diag_row_detalhe_admin.get('Data','N/A')} - {diag_row_detalhe_admin.get('Empresa','N/A')}")
                                comentarios_admin_atuais_det = diag_row_detalhe_admin.get('Comentarios_Admin', "")
                                novos_comentarios_admin_det = st.text_area("Comentários do Consultor:", value=comentarios_admin_atuais_det if pd.notna(comentarios_admin_atuais_det) else "", key=f"com_admin_det_{diag_original_index_admin}")
                                if st.button("Salvar Comentários do Consultor 💬", key=f"save_com_admin_det_{diag_original_index_admin}"):
                                    df_all_diags_update = pd.read_csv(arquivo_csv, encoding='utf-8', dtype={'CNPJ':str}); df_all_diags_update.loc[diag_original_index_admin, 'Comentarios_Admin'] = novos_comentarios_admin_det; df_all_diags_update.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                    criar_notificacao(diag_row_detalhe_admin['CNPJ'], "Novos comentários do consultor disponíveis.", str(diag_row_detalhe_admin['Data'])); st.success("Comentários salvos e cliente notificado!"); st.rerun()
                                if st.button("📄 Baixar PDF deste Diagnóstico", key=f"dl_pdf_admin_detalhe_v14_final_{diag_original_index_admin}"):
                                    try: usuario_do_diag_pdf_adm = df_usuarios_admin_geral[df_usuarios_admin_geral['CNPJ'] == diag_row_detalhe_admin['CNPJ']].iloc[0].to_dict()
                                    except: usuario_do_diag_pdf_adm = {"Empresa": diag_row_detalhe_admin.get("Empresa","N/A"), "CNPJ": diag_row_detalhe_admin.get("CNPJ","N/A")}
                                    perguntas_df_pdf_admin_det = pd.read_csv(perguntas_csv, encoding='utf-8'); analises_df_pdf_admin_det = carregar_analises_perguntas(); medias_cat_pdf_admin_det = {k.replace("Media_Cat_","").replace("_"," "):v for k,v in diag_row_detalhe_admin.items() if "Media_Cat_" in k and pd.notna(v)}
                                    pdf_path_admin_det = gerar_pdf_diagnostico_completo(diag_row_detalhe_admin.to_dict(), usuario_do_diag_pdf_adm, perguntas_df_pdf_admin_det, diag_row_detalhe_admin.to_dict(), medias_cat_pdf_admin_det, analises_df_pdf_admin_det)
                                    if pdf_path_admin_det:
                                        with open(pdf_path_admin_det, "rb") as f_pdf_admin_det: st.download_button("Download PDF Confirmado", f_pdf_admin_det, file_name=f"diagnostico_admin_{sanitize_column_name(diag_row_detalhe_admin.get('Empresa','N_A'))}_{str(diag_row_detalhe_admin.get('Data','N_A')).replace(':','-').replace(' ','_')}.pdf", mime="application/pdf", key=f"dl_conf_admin_detalhe_v14_final_{diag_original_index_admin}")
                                        try: os.remove(pdf_path_admin_det)
                                        except: pass
                                    else: st.error("Falha ao gerar PDF.")
                            except (IndexError, KeyError, ValueError) as e_lookup: st.warning(f"Não foi possível carregar os detalhes do diagnóstico selecionado. Pode ter sido removido ou o índice é inválido. Erro: {e_lookup}")
                            except Exception as e_detalhe: st.error(f"Erro ao tentar detalhar diagnóstico: {e_detalhe}")
                    else: st.caption("Nenhum diagnóstico na seleção atual para detalhar.")
            
            elif menu_admin == "🚦 Status dos Clientes":
                st.subheader("Status de Diagnósticos dos Clientes")
                df_usuarios_status_view = df_usuarios_admin_geral.copy()
                df_diagnosticos_status_geral = diagnosticos_df_admin_orig_view.copy() if admin_data_carregada_view_sucesso and not diagnosticos_df_admin_orig_view.empty else pd.DataFrame()
                empresas_status_list_view = ["Todas"] + (sorted(df_usuarios_status_view['Empresa'].astype(str).unique().tolist()) if not df_usuarios_status_view.empty and "Empresa" in df_usuarios_status_view.columns else [])
                emp_sel_status_view = st.selectbox("Filtrar por Empresa:", empresas_status_list_view, key="status_emp_sel_v14_final")
                df_usuarios_status_filtrado = df_usuarios_status_view.copy()
                df_diagnosticos_status_filtrado_local = df_diagnosticos_status_geral.copy()
                if emp_sel_status_view != "Todas":
                    df_usuarios_status_filtrado = df_usuarios_status_view[df_usuarios_status_view["Empresa"] == emp_sel_status_view]
                    if not df_diagnosticos_status_filtrado_local.empty: df_diagnosticos_status_filtrado_local = df_diagnosticos_status_filtrado_local[df_diagnosticos_status_filtrado_local["Empresa"] == emp_sel_status_view]
                if df_usuarios_status_filtrado.empty: st.info(f"Nenhum cliente encontrado para a empresa '{emp_sel_status_view}'.")
                else:
                    st.markdown("##### Clientes que JÁ REALIZARAM pelo menos um diagnóstico (no contexto da empresa filtrada):")
                    if not df_diagnosticos_status_filtrado_local.empty:
                        cnpjs_com_diagnostico_status = df_diagnosticos_status_filtrado_local['CNPJ'].unique()
                        clientes_que_fizeram_status = df_usuarios_status_filtrado[df_usuarios_status_filtrado['CNPJ'].isin(cnpjs_com_diagnostico_status)]
                        if not clientes_que_fizeram_status.empty: st.dataframe(clientes_que_fizeram_status[['CNPJ', 'Empresa', 'NomeContato', 'TotalDiagnosticosRealizados', 'DiagnosticosDisponiveis']])
                        else: st.info(f"Nenhum cliente da empresa '{emp_sel_status_view}' realizou diagnósticos.")
                    elif admin_data_carregada_view_sucesso: st.info(f"Nenhum diagnóstico registrado para a empresa '{emp_sel_status_view}'.")
                    else: st.info("Dados de diagnóstico não disponíveis para consulta.")
                    st.markdown("---")
                    st.markdown("##### Clientes com Diagnósticos LIBERADOS e AINDA NÃO REALIZADOS (ou com slots pendentes):")
                    clientes_liberados_pendentes_status = df_usuarios_status_filtrado[df_usuarios_status_filtrado['DiagnosticosDisponiveis'] > df_usuarios_status_filtrado['TotalDiagnosticosRealizados']]
                    if not clientes_liberados_pendentes_status.empty: st.dataframe(clientes_liberados_pendentes_status[['CNPJ', 'Empresa', 'NomeContato', 'DiagnosticosDisponiveis', 'TotalDiagnosticosRealizados']])
                    else: st.info(f"Nenhum cliente da empresa '{emp_sel_status_view}' com diagnósticos liberados pendentes.")

            elif menu_admin == "📜 Histórico de Usuários":
                st.subheader("📜 Histórico de Ações")
                df_historico_completo_hu = pd.DataFrame()
                df_usuarios_para_filtro_hu = pd.DataFrame()
                try:
                    df_historico_completo_hu = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
                    df_usuarios_para_filtro_hu = pd.read_csv(usuarios_csv, encoding='utf-8', usecols=['CNPJ', 'Empresa', 'NomeContato'], dtype={'CNPJ': str})
                except FileNotFoundError: st.error("Arquivo de histórico ou usuários não encontrado."); df_historico_completo_hu = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"]); df_usuarios_para_filtro_hu = pd.DataFrame(columns=['CNPJ', 'Empresa', 'NomeContato'])
                except Exception as e_hu: st.error(f"Erro ao carregar dados para o histórico: {e_hu}"); df_historico_completo_hu = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"]); df_usuarios_para_filtro_hu = pd.DataFrame(columns=['CNPJ', 'Empresa', 'NomeContato'])
                st.markdown("#### Filtros do Histórico"); col_hu_f1, col_hu_f2 = st.columns(2); empresas_hist_list_hu = ["Todas"]
                if not df_usuarios_para_filtro_hu.empty and 'Empresa' in df_usuarios_para_filtro_hu.columns: empresas_hist_list_hu.extend(sorted(df_usuarios_para_filtro_hu['Empresa'].astype(str).unique().tolist()))
                emp_sel_hu = col_hu_f1.selectbox("Filtrar por Empresa:", empresas_hist_list_hu, key="hist_emp_sel_v14_final_hu_adm"); termo_busca_hu = col_hu_f2.text_input("Buscar por Nome do Contato, CNPJ, Ação ou Descrição:", key="hist_termo_busca_v14_final_hu_adm")
                df_historico_filtrado_view_hu = df_historico_completo_hu.copy()
                if emp_sel_hu != "Todas" and not df_usuarios_para_filtro_hu.empty: cnpjs_da_empresa_hu = df_usuarios_para_filtro_hu[df_usuarios_para_filtro_hu['Empresa'] == emp_sel_hu]['CNPJ'].tolist(); df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_da_empresa_hu)]
                if termo_busca_hu.strip():
                    busca_lower_hu = termo_busca_hu.strip().lower(); cnpjs_match_nome_hu = []
                    if not df_usuarios_para_filtro_hu.empty and 'NomeContato' in df_usuarios_para_filtro_hu.columns: cnpjs_match_nome_hu = df_usuarios_para_filtro_hu[df_usuarios_para_filtro_hu['NomeContato'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)]['CNPJ'].tolist()
                    df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_match_nome_hu) | df_historico_filtrado_view_hu['CNPJ'].astype(str).str.lower().str.contains(busca_lower_hu) | df_historico_filtrado_view_hu['Ação'].astype(str).str.lower().str.contains(busca_lower_hu, na=False) | df_historico_filtrado_view_hu['Descrição'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)]
                st.markdown("#### Registros do Histórico")
                if not df_historico_filtrado_view_hu.empty:
                    st.dataframe(df_historico_filtrado_view_hu.sort_values(by="Data", ascending=False))
                    if st.button("📄 Baixar Histórico Filtrado (PDF)", key="download_hist_filtrado_pdf_v14_final_hu_adm"):
                        titulo_pdf_hist = f"Historico_Acoes_{sanitize_column_name(emp_sel_hu)}_{sanitize_column_name(termo_busca_hu) if termo_busca_hu else 'Todos'}_{datetime.now().strftime('%Y%m%d')}.pdf"; pdf_path_hist = gerar_pdf_historico(df_historico_filtrado_view_hu, titulo=f"Histórico ({emp_sel_hu} - Busca: {termo_busca_hu or 'N/A'})")
                        if pdf_path_hist:
                            with open(pdf_path_hist, "rb") as f_pdf_hist: st.download_button(label="Download Confirmado", data=f_pdf_hist, file_name=titulo_pdf_hist, mime="application/pdf", key="confirm_download_hist_pdf_v14_final_hu_adm")
                            try: os.remove(pdf_path_hist)
                            except: pass
                else: st.info("Nenhum registro de histórico encontrado para os filtros aplicados.")

            elif menu_admin == "📝 Gerenciar Perguntas":
                st.subheader("Gerenciar Perguntas do Diagnóstico"); tabs_perg_admin = st.tabs(["📋 Perguntas Atuais", "➕ Adicionar Nova Pergunta"])
                try:
                    perguntas_df_admin_gp = pd.read_csv(perguntas_csv, encoding='utf-8')
                    if "Categoria" not in perguntas_df_admin_gp.columns:
                        perguntas_df_admin_gp["Categoria"] = "Geral"
                except (FileNotFoundError, pd.errors.EmptyDataError):
                    perguntas_df_admin_gp = pd.DataFrame(columns=colunas_base_perguntas)
                with tabs_perg_admin[0]:
                    if perguntas_df_admin_gp.empty: st.info("Nenhuma pergunta cadastrada.")
                    else:
                        for i_p_admin, row_p_admin in perguntas_df_admin_gp.iterrows():
                            cols_p_admin = st.columns([4, 2, 0.5, 0.5])
                            with cols_p_admin[0]: nova_p_text_admin = st.text_input("Pergunta", value=str(row_p_admin["Pergunta"]), key=f"edit_p_txt_v14_final_gp_{i_p_admin}")
                            with cols_p_admin[1]: nova_cat_text_admin = st.text_input("Categoria", value=str(row_p_admin.get("Categoria", "Geral")), key=f"edit_p_cat_v14_final_gp_{i_p_admin}")
                            with cols_p_admin[2]:
                                st.markdown("<br/>", unsafe_allow_html=True)
                                if st.button("💾", key=f"salvar_p_adm_v14_final_gp_{i_p_admin}", help="Salvar Alterações"):
                                    perguntas_df_admin_gp.loc[i_p_admin, "Pergunta"] = nova_p_text_admin
                                    perguntas_df_admin_gp.loc[i_p_admin, "Categoria"] = nova_cat_text_admin
                                    perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                    st.success(f"Pergunta {i_p_admin+1} atualizada."); st.rerun()
                            with cols_p_admin[3]:
                                st.markdown("<br/>", unsafe_allow_html=True)
                                if st.button("🗑️", key=f"deletar_p_adm_v14_final_gp_{i_p_admin}", help="Deletar Pergunta"):
                                    perguntas_df_admin_gp = perguntas_df_admin_gp.drop(i_p_admin).reset_index(drop=True)
                                    perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                    st.warning(f"Pergunta {i_p_admin+1} removida."); st.rerun()
                            st.divider()
                with tabs_perg_admin[1]:
                    with st.form("form_nova_pergunta_admin_v14_final_gp"):
                        st.subheader("➕ Adicionar Nova Pergunta"); nova_p_form_txt_admin = st.text_input("Texto da Pergunta (sem incluir o tipo, ex: 'Qual o nível de satisfação?')", key="nova_p_input_admin_txt_v14_final_gp")
                        cat_existentes_gp = sorted(list(perguntas_df_admin_gp['Categoria'].astype(str).unique())) if not perguntas_df_admin_gp.empty and "Categoria" in perguntas_df_admin_gp.columns else []; cat_options_gp = ["Nova Categoria"] + cat_existentes_gp; cat_selecionada_gp = st.selectbox("Categoria:", cat_options_gp, key="cat_select_admin_new_q_v14_final_gp")
                        nova_cat_form_admin_gp = st.text_input("Nome da Nova Categoria (se 'Nova Categoria' selecionada acima):", key="nova_cat_input_admin_new_q_v14_final_gp") if cat_selecionada_gp == "Nova Categoria" else cat_selecionada_gp
                        tipo_p_form_admin = st.selectbox("Tipo de Pergunta (será adicionado ao final do texto da pergunta):", ["Pontuação (0-10)", "Pontuação (0-5)", "Texto Aberto", "Escala", "[Matriz GUT]"], key="tipo_p_select_admin_new_q_v14_final_gp")
                        if st.form_submit_button("➕ Adicionar Pergunta"):
                            if nova_p_form_txt_admin.strip() and nova_cat_form_admin_gp.strip():
                                p_completa_add_admin = f"{nova_p_form_txt_admin.strip()} [{tipo_p_form_admin.replace('[','').replace(']','') if tipo_p_form_admin != 'Escala' else 'Escala'}]"
                                if tipo_p_form_admin == "Escala": p_completa_add_admin = f"{nova_p_form_txt_admin.strip()} [Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)]"
                                nova_entrada_p_add_admin = pd.DataFrame([[p_completa_add_admin, nova_cat_form_admin_gp.strip()]], columns=["Pergunta", "Categoria"]); perguntas_df_admin_gp = pd.concat([perguntas_df_admin_gp, nova_entrada_p_add_admin], ignore_index=True); perguntas_df_admin_gp.to_csv(perguntas_csv, index=False, encoding='utf-8'); st.success(f"Pergunta adicionada!"); st.rerun()
                            else: st.warning("Texto da pergunta e categoria são obrigatórios.")

            elif menu_admin == "💡 Gerenciar Análises de Perguntas":
                st.subheader("Gerenciar Análises Vinculadas às Perguntas"); df_analises_existentes_admin = carregar_analises_perguntas()
                try: df_perguntas_formulario_admin = pd.read_csv(perguntas_csv, encoding='utf-8')
                except: df_perguntas_formulario_admin = pd.DataFrame(columns=colunas_base_perguntas)
                st.markdown("#### Adicionar Nova Análise")
                if df_perguntas_formulario_admin.empty: st.warning("Nenhuma pergunta cadastrada no formulário. Adicione perguntas primeiro em 'Gerenciar Perguntas'.")
                else:
                    lista_perguntas_txt_admin = [""] + df_perguntas_formulario_admin["Pergunta"].unique().tolist(); pergunta_selecionada_analise_admin = st.selectbox("Selecione a Pergunta para adicionar análise:", lista_perguntas_txt_admin, key="sel_perg_analise_v14_final_ga")
                    if pergunta_selecionada_analise_admin:
                        st.caption(f"Pergunta selecionada: {pergunta_selecionada_analise_admin}"); tipo_condicao_analise_display_admin = st.selectbox("Tipo de Condição para a Análise:", ["Faixa Numérica (p/ Pontuação 0-X)", "Valor Exato (p/ Escala)", "Faixa de Score (p/ Matriz GUT)", "Análise Padrão (default para a pergunta)"], key="tipo_cond_analise_v14_final_ga")
                        map_tipo_cond_to_csv_admin = { "Faixa Numérica (p/ Pontuação 0-X)": "FaixaNumerica", "Valor Exato (p/ Escala)": "ValorExatoEscala", "Faixa de Score (p/ Matriz GUT)": "ScoreGUT", "Análise Padrão (default para a pergunta)": "Default" }; tipo_condicao_csv_val_admin = map_tipo_cond_to_csv_admin[tipo_condicao_analise_display_admin]
                        cond_val_min_ui_admin, cond_val_max_ui_admin, cond_val_exato_ui_admin = None, None, None
                        if tipo_condicao_csv_val_admin == "FaixaNumerica": cols_faixa_ui_admin = st.columns(2); cond_val_min_ui_admin = cols_faixa_ui_admin[0].number_input("Valor Mínimo da Faixa", step=1.0, format="%.2f", key="cond_min_analise_v14_final_ga"); cond_val_max_ui_admin = cols_faixa_ui_admin[1].number_input("Valor Máximo da Faixa", step=1.0, format="%.2f", key="cond_max_analise_v14_final_ga")
                        elif tipo_condicao_csv_val_admin == "ValorExatoEscala": cond_val_exato_ui_admin = st.text_input("Valor Exato da Escala (ex: Baixo, Médio, Alto)", key="cond_exato_analise_v14_final_ga")
                        elif tipo_condicao_csv_val_admin == "ScoreGUT": cols_faixa_gut_ui_admin = st.columns(2); cond_val_min_ui_admin = cols_faixa_gut_ui_admin[0].number_input("Score GUT Mínimo", step=1, key="cond_min_gut_analise_v14_final_ga"); cond_val_max_ui_admin = cols_faixa_gut_ui_admin[1].number_input("Score GUT Máximo (opcional, deixe 0 ou vazio se for 'acima de Mínimo')", value=0.0, step=1.0, format="%.0f", key="cond_max_gut_analise_v14_final_ga")
                        texto_analise_nova_ui_admin = st.text_area("Texto da Análise:", height=150, key="txt_analise_nova_v14_final_ga")
                        if st.button("💾 Salvar Nova Análise", key="salvar_analise_pergunta_v14_final_ga"):
                            if texto_analise_nova_ui_admin.strip(): nova_id_analise_admin = str(uuid.uuid4()); nova_entrada_analise_admin = { "ID_Analise": nova_id_analise_admin, "TextoPerguntaOriginal": pergunta_selecionada_analise_admin, "TipoCondicao": tipo_condicao_csv_val_admin, "CondicaoValorMin": cond_val_min_ui_admin if cond_val_min_ui_admin is not None else pd.NA, "CondicaoValorMax": cond_val_max_ui_admin if cond_val_max_ui_admin is not None and cond_val_max_ui_admin !=0 else pd.NA, "CondicaoValorExato": cond_val_exato_ui_admin if cond_val_exato_ui_admin else pd.NA, "TextoAnalise": texto_analise_nova_ui_admin }; df_analises_existentes_admin = pd.concat([df_analises_existentes_admin, pd.DataFrame([nova_entrada_analise_admin])], ignore_index=True); df_analises_existentes_admin.to_csv(analises_perguntas_csv, index=False, encoding='utf-8'); st.success(f"Nova análise salva!"); st.markdown(f"**Pergunta:** {pergunta_selecionada_analise_admin}"); st.markdown(f"**Análise:** {texto_analise_nova_ui_admin}"); st.rerun()
                            else: st.error("O texto da análise não pode estar vazio.")
                st.markdown("---"); st.subheader("📜 Análises Cadastradas")
                df_analises_para_exibir = carregar_analises_perguntas()
                if df_analises_para_exibir.empty: st.info("Nenhuma análise cadastrada.")
                else:
                    df_display_analises_view = df_analises_para_exibir.copy()
                    for col_num_format_view in ['CondicaoValorMin', 'CondicaoValorMax']:
                        if col_num_format_view in df_display_analises_view.columns: df_display_analises_view[col_num_format_view] = pd.to_numeric(df_display_analises_view[col_num_format_view], errors='coerce').fillna("")
                    st.dataframe(df_display_analises_view)
                    analise_del_id_admin_view = st.selectbox("Deletar Análise por ID:", [""] + df_analises_para_exibir["ID_Analise"].astype(str).tolist(), key="del_analise_id_v14_final_ga_view")
                    if st.button("🗑️ Deletar Análise Selecionada", key="btn_del_analise_v14_final_ga_view", type="primary") and analise_del_id_admin_view: df_analises_para_exibir = df_analises_para_exibir[df_analises_para_exibir["ID_Analise"] != analise_del_id_admin_view]; df_analises_para_exibir.to_csv(analises_perguntas_csv, index=False, encoding='utf-8'); st.warning("Análise deletada."); st.rerun()

            elif menu_admin == "✍️ Gerenciar Instruções Clientes":
                st.subheader("Gerenciar Instruções para Clientes")
                current_instructions = ""
                default_instr_text_full = """**Bem-vindo ao Portal de Diagnóstico Empresarial!**

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
"""
                try:
                    if os.path.exists(instrucoes_txt_file) and os.path.getsize(instrucoes_txt_file) > 0:
                        with open(instrucoes_txt_file, "r", encoding="utf-8") as f:
                            current_instructions = f.read()
                    elif not os.path.exists(instrucoes_txt_file):
                           with open(instrucoes_txt_file, "w", encoding="utf-8") as f:
                                f.write(default_instr_text_full)
                                current_instructions = default_instr_text_full
                except Exception as e: st.error(f"Erro ao ler arquivo de instruções: {e}")
                edited_instructions = st.text_area("Edite as instruções para os clientes (use Markdown para formatação):", value=current_instructions, height=400, key="admin_edit_instructions_ta")
                if st.button("💾 Salvar Instruções", key="admin_save_instructions_btn"):
                    try:
                        with open(instrucoes_txt_file, "w", encoding="utf-8") as f: f.write(edited_instructions)
                        st.success("Instruções salvas com sucesso!")
                    except Exception as e: st.error(f"Erro ao salvar instruções: {e}")

            elif menu_admin == "👥 Gerenciar Clientes":
                st.subheader("Gerenciar Clientes")
                try:
                    df_usuarios_gc = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                    for col, default, dtype_col in [("ConfirmouInstrucoesParaSlotAtual", "False", str), ("DiagnosticosDisponiveis", 1, int), ("TotalDiagnosticosRealizados", 0, int), ("LiberacoesExtrasConcedidas", 0, int)]:
                        if col not in df_usuarios_gc.columns: df_usuarios_gc[col] = default
                        if dtype_col == int: df_usuarios_gc[col] = pd.to_numeric(df_usuarios_gc[col], errors='coerce').fillna(default).astype(int)
                        else: df_usuarios_gc[col] = df_usuarios_gc[col].astype(str)
                except FileNotFoundError: st.error(f"Arquivo de usuários '{usuarios_csv}' não encontrado."); df_usuarios_gc = pd.DataFrame(columns=colunas_base_usuarios)
                except Exception as e_gc_load_full: st.error(f"Erro ao carregar usuários: {e_gc_load_full}"); df_usuarios_gc = pd.DataFrame(columns=colunas_base_usuarios)
                st.markdown("#### Lista de Clientes Cadastrados")
                if not df_usuarios_gc.empty:
                    cols_display_gc = ["CNPJ", "Empresa", "NomeContato", "Telefone", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados", "LiberacoesExtrasConcedidas", "ConfirmouInstrucoesParaSlotAtual"]; st.dataframe(df_usuarios_gc[cols_display_gc])
                    st.markdown("#### Ações de Cliente"); clientes_lista_gc_ops = df_usuarios_gc.apply(lambda row: f"{row['Empresa']} ({row['CNPJ']})", axis=1).tolist(); cliente_selecionado_str_gc = st.selectbox("Selecione o cliente para gerenciar:", [""] + clientes_lista_gc_ops, key="sel_cliente_gc_v14_final_adm")
                    if cliente_selecionado_str_gc:
                        cnpj_selecionado_gc_val = cliente_selecionado_str_gc.split('(')[-1].replace(')','').strip(); cliente_data_gc_val = df_usuarios_gc[df_usuarios_gc["CNPJ"] == cnpj_selecionado_gc_val].iloc[0]
                        st.write(f"**Empresa:** {cliente_data_gc_val['Empresa']}"); st.write(f"**Diagnósticos Disponíveis (Slots):** {cliente_data_gc_val['DiagnosticosDisponiveis']}"); st.write(f"**Diagnósticos Já Realizados:** {cliente_data_gc_val['TotalDiagnosticosRealizados']}"); st.write(f"**Liberações Extras Concedidas:** {cliente_data_gc_val['LiberacoesExtrasConcedidas']}")
                        st.write(f"**Confirmou Instruções para Slot Atual:** {cliente_data_gc_val['ConfirmouInstrucoesParaSlotAtual']}")
                        if st.button(f"➕ Conceder +1 Diagnóstico para {cliente_data_gc_val['Empresa']}", key=f"conceder_diag_gc_v14_final_adm_{cnpj_selecionado_gc_val}"):
                            novos_disponiveis = cliente_data_gc_val['DiagnosticosDisponiveis'] + 1; liberacoes_extras_atuais = cliente_data_gc_val.get('LiberacoesExtrasConcedidas', 0)
                            update_user_data(cnpj_selecionado_gc_val, "DiagnosticosDisponiveis", novos_disponiveis); update_user_data(cnpj_selecionado_gc_val, "LiberacoesExtrasConcedidas", liberacoes_extras_atuais + 1); update_user_data(cnpj_selecionado_gc_val, "ConfirmouInstrucoesParaSlotAtual", "False")
                            registrar_acao("ADMIN", "Concessão Diagnóstico", f"Admin concedeu +1 slot para {cliente_data_gc_val['Empresa']} ({cnpj_selecionado_gc_val}). Slots: {novos_disponiveis}. Extras: {liberacoes_extras_atuais + 1}."); st.success(f"+1 Slot concedido. Slots disponíveis: {novos_disponiveis}. Liberações extras: {liberacoes_extras_atuais + 1}. Instruções resetadas."); st.rerun()
                        if st.button(f"🔄 Resetar Confirmação de Instruções para {cliente_data_gc_val['Empresa']}", key=f"reset_inst_gc_{cnpj_selecionado_gc_val}"):
                            update_user_data(cnpj_selecionado_gc_val, "ConfirmouInstrucoesParaSlotAtual", "False")
                            registrar_acao("ADMIN", "Reset Instruções", f"Admin resetou confirmação de instruções para {cliente_data_gc_val['Empresa']} ({cnpj_selecionado_gc_val})."); st.success(f"Confirmação de instruções resetada para {cliente_data_gc_val['Empresa']}."); st.rerun()

                        try: bloqueados_df_gc_check = pd.read_csv(usuarios_bloqueados_csv, dtype={'CNPJ': str}, encoding='utf-8')
                        except FileNotFoundError: bloqueados_df_gc_check = pd.DataFrame(columns=["CNPJ"])
                        is_blocked_gc_check = cnpj_selecionado_gc_val in bloqueados_df_gc_check["CNPJ"].values
                        if is_blocked_gc_check:
                            if st.button(f"🔓 Desbloquear Acesso Total para {cliente_data_gc_val['Empresa']}", key=f"desbloq_total_gc_v14_final_adm_{cnpj_selecionado_gc_val}"): bloqueados_df_gc_check = bloqueados_df_gc_check[bloqueados_df_gc_check["CNPJ"] != cnpj_selecionado_gc_val]; bloqueados_df_gc_check.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8'); st.success(f"Acesso total desbloqueado."); st.rerun()
                        else:
                            if st.button(f"🚫 Bloquear Acesso Total para {cliente_data_gc_val['Empresa']}", type="primary", key=f"bloq_total_gc_v14_final_adm_{cnpj_selecionado_gc_val}"): nova_entrada_bloqueio_gc_val = pd.DataFrame([{"CNPJ": cnpj_selecionado_gc_val}]); bloqueados_df_gc_check = pd.concat([bloqueados_df_gc_check, nova_entrada_bloqueio_gc_val], ignore_index=True); bloqueados_df_gc_check.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8'); st.error(f"Acesso total bloqueado."); st.rerun()
                else: st.info("Nenhum cliente cadastrado para gerenciar.")
                st.markdown("---"); st.markdown("#### Adicionar Novo Cliente")
                with st.form("form_novo_cliente_v14_final_adm", clear_on_submit=True):
                    novo_cnpj_gc_form = st.text_input("CNPJ do Novo Cliente:"); nova_senha_gc_form = st.text_input("Senha para o Novo Cliente:", type="password"); nova_empresa_gc_form = st.text_input("Nome da Empresa do Novo Cliente:"); novo_contato_gc_form = st.text_input("Nome do Contato (opcional):"); novo_telefone_gc_form = st.text_input("Telefone do Contato (opcional):")
                    if st.form_submit_button("➕ Cadastrar Novo Cliente"):
                        if novo_cnpj_gc_form and nova_senha_gc_form and nova_empresa_gc_form:
                            try: current_users_df_for_check = pd.read_csv(usuarios_csv, dtype={'CNPJ': str}, encoding='utf-8')
                            except (FileNotFoundError, pd.errors.EmptyDataError): current_users_df_for_check = pd.DataFrame(columns=colunas_base_usuarios)

                            if current_users_df_for_check.empty or (novo_cnpj_gc_form not in current_users_df_for_check["CNPJ"].values):
                                nova_linha_cliente_form = pd.DataFrame([{"CNPJ": novo_cnpj_gc_form, "Senha": nova_senha_gc_form, "Empresa": nova_empresa_gc_form, "NomeContato": novo_contato_gc_form, "Telefone": novo_telefone_gc_form, "ConfirmouInstrucoesParaSlotAtual": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0, "LiberacoesExtrasConcedidas": 0}])
                                df_usuarios_gc_updated = pd.concat([current_users_df_for_check, nova_linha_cliente_form], ignore_index=True);
                                df_usuarios_gc_updated.to_csv(usuarios_csv, index=False, encoding='utf-8'); st.success(f"Cliente {nova_empresa_gc_form} cadastrado com sucesso!"); st.rerun()
                            else: st.error("CNPJ já cadastrado.")
                        else: st.error("CNPJ, Senha e Nome da Empresa são obrigatórios.")

            elif menu_admin == "👮 Gerenciar Administradores":
                st.subheader("Gerenciar Administradores");
                try: admins_df_mng = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
                except (FileNotFoundError, pd.errors.EmptyDataError): admins_df_mng = pd.DataFrame(columns=["Usuario", "Senha"])
                st.dataframe(admins_df_mng[["Usuario"]]); st.markdown("---"); st.subheader("➕ Adicionar Novo Admin")
                with st.form("form_novo_admin_mng_v14_final_adm"):
                    novo_admin_user_mng = st.text_input("Usuário do Admin"); novo_admin_pass_mng = st.text_input("Senha do Admin", type="password")
                    if st.form_submit_button("Adicionar Admin"):
                        if novo_admin_user_mng and novo_admin_pass_mng:
                            if novo_admin_user_mng in admins_df_mng["Usuario"].values: st.error(f"Usuário '{novo_admin_user_mng}' já existe.")
                            else: novo_admin_data_mng = pd.DataFrame([[novo_admin_user_mng, novo_admin_pass_mng]], columns=["Usuario", "Senha"]); admins_df_mng = pd.concat([admins_df_mng, novo_admin_data_mng], ignore_index=True); admins_df_mng.to_csv(admin_credenciais_csv, index=False, encoding='utf-8'); st.success(f"Admin '{novo_admin_user_mng}' adicionado!"); st.rerun()
                        else: st.warning("Preencha todos os campos.")
                st.markdown("---"); st.subheader("🗑️ Remover Admin")
                if not admins_df_mng.empty:
                    admin_para_remover_mng = st.selectbox("Remover Admin:", options=[""] + admins_df_mng["Usuario"].tolist(), key="remove_admin_select_mng_v14_final_adm")
                    if st.button("Remover Admin Selecionado", type="primary", key="btn_remove_admin_v14_final_adm") and admin_para_remover_mng:
                        if len(admins_df_mng) == 1 and admin_para_remover_mng == admins_df_mng["Usuario"].iloc[0]: st.error("Não é possível remover o único administrador.")
                        elif 'admin_u_v15' in st.session_state and admin_para_remover_mng == st.session_state.admin_u_v15 :
                             st.error("Não é possível remover a si mesmo.")
                        else: admins_df_mng = admins_df_mng[admins_df_mng["Usuario"] != admin_para_remover_mng]; admins_df_mng.to_csv(admin_credenciais_csv, index=False, encoding='utf-8'); st.warning(f"Admin '{admin_para_remover_mng}' removido."); st.rerun()
                else: st.info("Nenhum administrador para remover.")

            elif menu_admin == "💾 Backup de Dados":
                st.subheader("Backup de Dados do Sistema"); st.markdown("Clique nos botões abaixo para baixar cópias dos arquivos CSV do sistema.")
                arquivos_para_backup = { "Clientes (Usuários)": usuarios_csv, "Diagnósticos": arquivo_csv, "Perguntas do Formulário": perguntas_csv, "Análises das Perguntas": analises_perguntas_csv, "Histórico de Ações": historico_csv, "Administradores": admin_credenciais_csv, "Clientes Bloqueados": usuarios_bloqueados_csv, "Notificações": notificacoes_csv }
                for nome_amigavel, nome_arquivo in arquivos_para_backup.items():
                    if os.path.exists(nome_arquivo) and os.path.getsize(nome_arquivo) > 0:
                        with open(nome_arquivo, "rb") as fp: st.download_button(label=f"Baixar {nome_amigavel} ({os.path.getsize(nome_arquivo)} bytes)", data=fp, file_name=nome_arquivo, mime="text/csv", key=f"backup_btn_v14_final_{nome_arquivo.replace('.','_')}")
                    elif os.path.exists(nome_arquivo): st.warning(f"Arquivo '{nome_arquivo}' encontrado, mas está vazio. Backup não gerado.")
                    else: st.warning(f"Arquivo '{nome_arquivo}' não encontrado para backup.")
        except Exception as e_admin_menu_dispatch:
            st.error(f"Ocorreu um erro na funcionalidade '{menu_admin}': {e_admin_menu_dispatch}")
            st.exception(e_admin_menu_dispatch)
    except Exception as e_outer_admin_critical:
        st.error(f"Um erro crítico e inesperado ocorreu na área administrativa: {e_outer_admin_critical}")
        st.exception(e_outer_admin_critical)


if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")