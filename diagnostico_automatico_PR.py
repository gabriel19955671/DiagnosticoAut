import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
from fpdf import FPDF
import tempfile
import re 
import json
import plotly.express as px # Mantido, certifique-se de ter instalado com 'pip install plotly'

st.set_page_config(page_title="Portal de Diagnóstico", layout="wide") 

# CSS (mantido)
st.markdown("""
<style>
/* ... Seu CSS anterior aqui ... */
.login-container {
    max-width: 400px;
    margin: 60px auto 0 auto;
    padding: 40px;
    border-radius: 8px;
    background-color: #ffffff;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    font-family: 'Segoe UI', sans-serif;
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
    padding: 0.5rem 1.2rem;
    margin-top: 0.5rem;
}
.stDownloadButton>button {
    background-color: #10b981;
    color: white;
    font-weight: 600;
    border-radius: 6px;
    margin-top: 10px;
    padding: 0.5rem 1.2rem;
}
.stTextInput>div>input, .stTextArea>div>textarea {
    border-radius: 6px;
    padding: 0.4rem;
    border: 1px solid #d1d5db;
    background-color: #f9fafb;
}
.stTabs [data-baseweb="tab"] {
    font-size: 16px;
    font-weight: 600;
    padding: 10px 20px;
}
.custom-card {
    border: 1px solid #e0e0e0;
    border-left: 5px solid #2563eb; 
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 5px;
    background-color: #f9f9f9;
}
.custom-card h4 {
    margin-top: 0;
    color: #2563eb;
}
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

# --- Inicialização do Session State ---
if "admin_logado" not in st.session_state: st.session_state.admin_logado = False
if "cliente_logado" not in st.session_state: st.session_state.cliente_logado = False
if "diagnostico_enviado" not in st.session_state: st.session_state.diagnostico_enviado = False
if "inicio_sessao_cliente" not in st.session_state: st.session_state.inicio_sessao_cliente = None
if "cliente_page" not in st.session_state: st.session_state.cliente_page = "Painel Principal"
if "cnpj" not in st.session_state: st.session_state.cnpj = None
if "user" not in st.session_state: st.session_state.user = None
# A chave DIAGNOSTICO_FORM_ID_KEY será definida dinamicamente com base no CNPJ

# --- Funções Utilitárias ---
def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s) 
    return s

def pdf_safe_text_output(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# --- Criação e Verificação de Arquivos ---
colunas_base_diagnosticos = [
    "Data", "CNPJ", "Nome", "Email", "Empresa",
    "Média Geral", "GUT Média", "Observações", "Diagnóstico", 
    "Análise do Cliente", "Comentarios_Admin"
]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone"]
colunas_base_perguntas = ["Pergunta", "Categoria"]

def inicializar_csv(filepath, columns, is_perguntas_file=False):
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df = pd.DataFrame(columns=columns)
            df.to_csv(filepath, index=False, encoding='utf-8')
            # st.info(f"Arquivo {filepath} criado/inicializado.") # Opcional: menos verboso
        else:
            df = pd.read_csv(filepath, encoding='utf-8')
            missing_cols = [col for col in columns if col not in df.columns]
            made_changes = False
            if missing_cols:
                for col in missing_cols:
                    if is_perguntas_file and col == "Categoria":
                        df[col] = "Geral" # Default para Categoria em perguntas.csv
                    else:
                        df[col] = pd.NA 
                made_changes = True
            
            if is_perguntas_file and "Categoria" not in df.columns: # Dupla checagem para o caso de arquivo existente sem a coluna
                df["Categoria"] = "Geral"
                made_changes = True

            if made_changes:
                df.to_csv(filepath, index=False, encoding='utf-8')
                # st.info(f"Arquivo {filepath} verificado/atualizado.") # Opcional
    except pd.errors.EmptyDataError: # Se o arquivo existe mas está totalmente vazio
        pd.DataFrame(columns=columns).to_csv(filepath, index=False, encoding='utf-8')
        # st.info(f"Arquivo {filepath} estava vazio e foi reinicializado.") # Opcional
    except Exception as e:
        st.error(f"Erro crítico ao inicializar/verificar {filepath}: {e}. Verifique o arquivo manualmente ou delete-o para recriação.")
        st.stop() # Parar execução se arquivos base não puderem ser garantidos

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios)
    inicializar_csv(perguntas_csv, colunas_base_perguntas, is_perguntas_file=True)
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
except Exception as e_init: # Pega qualquer exceção da inicialização
    st.error(f"Falha na inicialização de arquivos CSV base: {e_init}")
    st.markdown("---")
    st.markdown("### Solução de Problemas:")
    st.markdown("""
    1. Verifique se você tem permissão de escrita na pasta onde o script está rodando.
    2. Tente deletar os arquivos CSV mencionados acima da pasta do script. Eles serão recriados na próxima execução.
    3. Se o problema persistir, pode haver um problema mais sério com o ambiente ou permissões.
    """)
    st.stop()

def registrar_acao(cnpj, acao, descricao):
    try:
        historico_df_ra = pd.read_csv(historico_csv, encoding='utf-8') 
    except (FileNotFoundError, pd.errors.EmptyDataError): 
        historico_df_ra = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    nova_data_ra = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao }
    historico_df_ra = pd.concat([historico_df_ra, pd.DataFrame([nova_data_ra])], ignore_index=True)
    historico_df_ra.to_csv(historico_csv, index=False, encoding='utf-8')

# --- Função Refatorada de Geração de PDF (mantida como antes) ---
def gerar_pdf_diagnostico_completo(diagnostico_data, usuario_data, perguntas_df_geracao, respostas_coletadas_geracao, medias_categorias_geracao):
    # ... (Código da função gerar_pdf_diagnostico_completo mantido da versão anterior) ...
    # (Certifique-se de que este código é robusto e não causa erros não capturados)
    try:
        pdf = FPDF()
        pdf.add_page()
        empresa_nome_pdf = usuario_data.get("Empresa", "N/D")
        cnpj_pdf = usuario_data.get("CNPJ", "N/D")
        nome_contato_pdf = usuario_data.get("NomeContato", "")
        telefone_pdf = usuario_data.get("Telefone", "")

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome_pdf}"), 0, 1, 'C')
        pdf.ln(5)

        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 7, pdf_safe_text_output(f"Data do Diagnóstico: {diagnostico_data.get('Data','N/D')}"))
        pdf.multi_cell(0, 7, pdf_safe_text_output(f"Empresa: {empresa_nome_pdf} (CNPJ: {cnpj_pdf})"))
        if nome_contato_pdf: pdf.multi_cell(0, 7, pdf_safe_text_output(f"Contato: {nome_contato_pdf}"))
        if telefone_pdf: pdf.multi_cell(0, 7, pdf_safe_text_output(f"Telefone: {telefone_pdf}"))
        pdf.ln(3)

        pdf.multi_cell(0, 7, pdf_safe_text_output(f"Média Geral (Numérica): {diagnostico_data.get('Média Geral','N/A')}"))
        pdf.multi_cell(0, 7, pdf_safe_text_output(f"Média Scores GUT (G*U*T): {diagnostico_data.get('GUT Média','N/A')}"))
        pdf.ln(3)

        if medias_categorias_geracao:
            pdf.set_font("Arial", 'B', 11); pdf.multi_cell(0, 7, pdf_safe_text_output("Médias por Categoria (Perguntas de Pontuação):"))
            pdf.set_font("Arial", size=10)
            for cat_pdf_g, media_cat_pdf_g in medias_categorias_geracao.items():
                pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat_pdf_g}: {media_cat_pdf_g}"))
            pdf.ln(5)

        resumo_cliente_pdf = diagnostico_data.get("Diagnóstico", "") 
        analise_cliente_pdf = diagnostico_data.get("Análise do Cliente", "") 
        
        if resumo_cliente_pdf:
            pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output("Resumo do Diagnóstico (Cliente):"))
            pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(resumo_cliente_pdf)); pdf.ln(3)
        if analise_cliente_pdf:
            pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output("Análise/Observações do Cliente:"))
            pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(analise_cliente_pdf)); pdf.ln(3)

        comentarios_admin_pdf = diagnostico_data.get("Comentarios_Admin", "")
        if comentarios_admin_pdf:
            pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output("Comentários do Consultor:"))
            pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(comentarios_admin_pdf)); pdf.ln(3)
            
        pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 10, pdf_safe_text_output("Respostas Detalhadas por Categoria:"))
        categorias_unicas_pdf_ger = []
        if "Categoria" in perguntas_df_geracao.columns: # Checagem importante
            categorias_unicas_pdf_ger = perguntas_df_geracao["Categoria"].unique()
        
        for categoria_pdf_g_det in categorias_unicas_pdf_ger:
            pdf.set_font("Arial", 'B', 10); pdf.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria_pdf_g_det}"))
            pdf.set_font("Arial", size=9)
            perguntas_cat_pdf_g_det = perguntas_df_geracao[perguntas_df_geracao["Categoria"] == categoria_pdf_g_det]
            for _, p_row_pdf_g_det in perguntas_cat_pdf_g_det.iterrows():
                txt_p_pdf_g_det = p_row_pdf_g_det["Pergunta"]
                resp_p_pdf_g_det = respostas_coletadas_geracao.get(txt_p_pdf_g_det)
                if resp_p_pdf_g_det is None: 
                    resp_p_pdf_g_det = diagnostico_data.get(txt_p_pdf_g_det, "N/R")

                if "[Matriz GUT]" in txt_p_pdf_g_det:
                    g_pdf, u_pdf, t_pdf = 0,0,0
                    score_gut_item_pdf = 0
                    if isinstance(resp_p_pdf_g_det, dict): 
                        g_pdf,u_pdf,t_pdf = resp_p_pdf_g_det.get("G",0), resp_p_pdf_g_det.get("U",0), resp_p_pdf_g_det.get("T",0)
                    elif isinstance(resp_p_pdf_g_det, str): 
                        try: 
                            gut_data_pdf = json.loads(resp_p_pdf_g_det.replace("'", "\""))
                            g_pdf,u_pdf,t_pdf = gut_data_pdf.get("G",0), gut_data_pdf.get("U",0), gut_data_pdf.get("T",0)
                        except: pass 
                    score_gut_item_pdf = g_pdf*u_pdf*t_pdf
                    pdf.multi_cell(0,6,pdf_safe_text_output(f"  - {txt_p_pdf_g_det.replace(' [Matriz GUT]','')}: G={g_pdf}, U={u_pdf}, T={t_pdf} (Score: {score_gut_item_pdf})"))
                elif isinstance(resp_p_pdf_g_det, (int, float, str)): 
                    pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {txt_p_pdf_g_det}: {resp_p_pdf_g_det}"))
            pdf.ln(2)
        pdf.ln(3)
        
        pdf.add_page(); pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf.ln(5)
        pdf.set_font("Arial", size=10)
        gut_cards_pdf_ger = []
        for pergunta_pdf_k_g, resp_pdf_k_g_val in respostas_coletadas_geracao.items(): 
            if isinstance(pergunta_pdf_k_g, str) and "[Matriz GUT]" in pergunta_pdf_k_g:
                g_k_g, u_k_g, t_k_g = 0,0,0
                if isinstance(resp_pdf_k_g_val, dict):
                    g_k_g, u_k_g, t_k_g = resp_pdf_k_g_val.get("G",0), resp_pdf_k_g_val.get("U",0), resp_pdf_k_g_val.get("T",0)
                elif isinstance(resp_pdf_k_g_val, str): 
                    try: 
                        gut_data_k_g = json.loads(resp_pdf_k_g_val.replace("'", "\""))
                        g_k_g,u_k_g,t_k_g = gut_data_k_g.get("G",0), gut_data_k_g.get("U",0), gut_data_k_g.get("T",0)
                    except: pass
                
                score_gut_total_k_g_pdf = g_k_g * u_k_g * t_k_g
                prazo_k_g_pdf = "N/A"
                if score_gut_total_k_g_pdf >= 75: prazo_k_g_pdf = "15 dias"
                elif score_gut_total_k_g_pdf >= 40: prazo_k_g_pdf = "30 dias"
                elif score_gut_total_k_g_pdf >= 20: prazo_k_g_pdf = "45 dias"
                elif score_gut_total_k_g_pdf > 0: prazo_k_g_pdf = "60 dias"
                else: continue
                if prazo_k_g_pdf != "N/A":
                    gut_cards_pdf_ger.append({"Tarefa": pergunta_pdf_k_g.replace(" [Matriz GUT]", ""),"Prazo": prazo_k_g_pdf, "Score": score_gut_total_k_g_pdf})
        if gut_cards_pdf_ger:
            gut_cards_pdf_ger_sorted = sorted(gut_cards_pdf_ger, key=lambda x_f_k_g_pdf: (int(x_f_k_g_pdf["Prazo"].split(" ")[0]), -x_f_k_g_pdf["Score"]))
            for card_item_f_k_g_pdf in gut_cards_pdf_ger_sorted:
                 pdf.multi_cell(0, 6, pdf_safe_text_output(f"Prazo: {card_item_f_k_g_pdf['Prazo']} - Tarefa: {card_item_f_k_g_pdf['Tarefa']} (Score GUT: {card_item_f_k_g_pdf['Score']})"))
        else: pdf.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile_g:
            pdf_path_g = tmpfile_g.name
            pdf.output(pdf_path_g)
        return pdf_path_g
    except Exception as e_pdf:
        st.error(f"Erro ao gerar PDF: {e_pdf}")
        return None


# --- Lógica de Login e Navegação Principal (Admin/Cliente) ---
if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_main_debug")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_page_debug"): 
        usuario_admin_login_page_d = st.text_input("Usuário", key="admin_user_login_page_d") 
        senha_admin_login_page_d = st.text_input("Senha", type="password", key="admin_pass_login_page_d")
        entrar_admin_login_page_d = st.form_submit_button("Entrar")
    if entrar_admin_login_page_d:
        try:
            df_admin_login_creds_page_d = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            if not df_admin_login_creds_page_d[(df_admin_login_creds_page_d["Usuario"] == usuario_admin_login_page_d) & (df_admin_login_creds_page_d["Senha"] == senha_admin_login_page_d)].empty:
                st.session_state.admin_logado = True; st.success("Login de administrador bem-sucedido!")
                st.session_state.trigger_admin_rerun = True; st.rerun() 
            else: st.error("Usuário ou senha inválidos.")
        except FileNotFoundError: st.error(f"Arquivo {admin_credenciais_csv} não encontrado.")
        except Exception as e_login_admin_d: st.error(f"Erro no login: {e_login_admin_d}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_page_debug"): 
        cnpj_cli_login_page_d = st.text_input("CNPJ", key="cli_cnpj_login_page_d") 
        senha_cli_login_page_d = st.text_input("Senha", type="password", key="cli_pass_login_page_d") 
        acessar_cli_login_page_d = st.form_submit_button("Entrar")
    if acessar_cli_login_page_d:
        try:
            if not os.path.exists(usuarios_csv): st.error("Base de usuários não encontrada."); st.stop()
            usuarios_login_df_page_d = pd.read_csv(usuarios_csv, encoding='utf-8')
            bloqueados_login_df_page_d = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
            if cnpj_cli_login_page_d in bloqueados_login_df_page_d["CNPJ"].astype(str).values: 
                st.error("CNPJ bloqueado."); st.stop()
            user_match_li_page_d = usuarios_login_df_page_d[(usuarios_login_df_page_d["CNPJ"].astype(str) == str(cnpj_cli_login_page_d)) & (usuarios_login_df_page_d["Senha"] == senha_cli_login_page_d)]
            if user_match_li_page_d.empty: st.error("CNPJ ou senha inválidos."); st.stop()
            st.session_state.cliente_logado = True
            st.session_state.cnpj = str(cnpj_cli_login_page_d) 
            st.session_state.user = user_match_li_page_d.iloc[0].to_dict() 
            st.session_state.inicio_sessao_cliente = time.time()
            registrar_acao(st.session_state.cnpj, "Login", "Usuário realizou login.")
            st.session_state.cliente_page = "Painel Principal"
            st.success("Login realizado com sucesso!"); st.session_state.trigger_cliente_rerun = True; st.rerun() 
        except FileNotFoundError as e_login_cli_fnf_d: st.error(f"Arquivo não encontrado: {e_login_cli_fnf_d.filename}.")
        except Exception as e_login_cli_d: st.error(f"Erro no login do cliente: {e_login_cli_d}")
    st.markdown('</div>', unsafe_allow_html=True); st.stop() 


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    try: # Try geral para a área do cliente
        st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
        
        DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME = f"form_id_diagnostico_cliente_{st.session_state.cnpj}" # Definida aqui

        st.session_state.cliente_page = st.sidebar.radio(
            "Menu Cliente", ["Painel Principal", "Novo Diagnóstico"],
            index=["Painel Principal", "Novo Diagnóstico"].index(st.session_state.cliente_page),
            key="cliente_menu_radio_main_debug"
        )
        if st.sidebar.button("⬅️ Sair do Portal Cliente"):
            keys_to_del_cli_logout_page_d = ['cliente_logado', 'cnpj', 'user', 'inicio_sessao_cliente', 
                                           'diagnostico_enviado', 'cliente_page', DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME]
            temp_resp_key_logout_page_d = f"temp_respostas_{st.session_state.get(DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME,'')}"
            if temp_resp_key_logout_page_d in st.session_state:
                keys_to_del_cli_logout_page_d.append(temp_resp_key_logout_page_d)
            for key_cd_lo_page_d in keys_to_del_cli_logout_page_d:
                if key_cd_lo_page_d in st.session_state: del st.session_state[key_cd_lo_page_d]
            st.rerun()

        if st.session_state.cliente_page == "Painel Principal":
            st.subheader("📌 Instruções Gerais")
            # ... (Instruções)
            
            st.subheader("📁 Diagnósticos Anteriores")
            # ... (Lógica de exibir históricos, Kanban, gráficos - como na versão anterior, mas com mais verificações se df estiver vazio)
            # Se o df_cliente_view_pp_page estiver vazio, a lógica de loops não será executada,
            # e o st.info("Nenhum diagnóstico anterior...") já trata isso.

        elif st.session_state.cliente_page == "Novo Diagnóstico":
            st.subheader("📋 Formulário de Novo Diagnóstico")
            
            if DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME not in st.session_state:
                st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME] = datetime.now().strftime("%Y%m%d%H%M%S%f")
            form_id_sufixo_nd_page_d = st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME]

            temp_respostas_key_nd_page_d = f"temp_respostas_{form_id_sufixo_nd_page_d}"
            if temp_respostas_key_nd_page_d not in st.session_state:
                st.session_state[temp_respostas_key_nd_page_d] = {}
            
            respostas_form_coletadas_nd_page_d = st.session_state[temp_respostas_key_nd_page_d]
            
            try:
                perguntas_df_diag_page_d = pd.read_csv(perguntas_csv, encoding='utf-8')
                if "Categoria" not in perguntas_df_diag_page_d.columns: 
                    st.warning(f"Arquivo {perguntas_csv} não possui a coluna 'Categoria'. Usando 'Geral' como padrão.")
                    perguntas_df_diag_page_d["Categoria"] = "Geral"
            except (FileNotFoundError, pd.errors.EmptyDataError): 
                st.error(f"Arquivo de perguntas ({perguntas_csv}) não encontrado ou está vazio. Não é possível carregar o formulário."); st.stop()
            
            if perguntas_df_diag_page_d.empty: 
                st.warning("Nenhuma pergunta cadastrada no sistema. Contate o administrador."); st.stop()
            
            # Debug: Mostrar informações sobre as perguntas carregadas
            # st.info(f"Perguntas carregadas: {len(perguntas_df_diag_page_d)} perguntas.")
            # if not perguntas_df_diag_page_d.empty:
            #     st.write("Amostra das perguntas:", perguntas_df_diag_page_d.head())


            total_perguntas_diag_page_d = len(perguntas_df_diag_page_d)
            respondidas_count_diag_page_d = 0 
            
            if "Categoria" not in perguntas_df_diag_page_d.columns: # Verificação final
                st.error("Falha crítica: Coluna 'Categoria' não está presente no DataFrame de perguntas após carregamento.")
                st.stop()

            categorias_unicas_diag_page_d = perguntas_df_diag_page_d["Categoria"].unique()
            if len(categorias_unicas_diag_page_d) == 0 and total_perguntas_diag_page_d > 0 :
                 st.warning("Perguntas existem, mas nenhuma categoria foi definida. Verifique o arquivo de perguntas.")


            with st.form(key=f"diagnostico_form_completo_{form_id_sufixo_nd_page_d}"):
                if total_perguntas_diag_page_d == 0:
                    st.warning("Nenhuma pergunta disponível para este diagnóstico.")
                else:
                    for categoria_diag_page_d in categorias_unicas_diag_page_d:
                        st.markdown(f"#### Categoria: {categoria_diag_page_d}")
                        perguntas_cat_diag_page_d = perguntas_df_diag_page_d[perguntas_df_diag_page_d["Categoria"] == categoria_diag_page_d]
                        
                        if perguntas_cat_diag_page_d.empty:
                            # st.caption(f"Nenhuma pergunta para a categoria '{categoria_diag_page_d}'.") # Opcional
                            continue

                        for idx_diag_f_page_d, row_diag_f_page_d in perguntas_cat_diag_page_d.iterrows():
                            texto_pergunta_diag_page_d = str(row_diag_f_page_d["Pergunta"]) 
                            widget_base_key_page_d = f"q_form_page_d_{idx_diag_f_page_d}" 
                            # ... (Lógica de renderização dos widgets como antes, usando _d como sufixo para variáveis)
                            if "[Matriz GUT]" in texto_pergunta_diag_page_d:
                                st.markdown(f"**{texto_pergunta_diag_page_d.replace(' [Matriz GUT]', '')}**")
                                cols_gut_page_d = st.columns(3)
                                gut_current_vals_page_d = respostas_form_coletadas_nd_page_d.get(texto_pergunta_diag_page_d, {"G":0, "U":0, "T":0})
                                with cols_gut_page_d[0]: g_val_page_d = st.slider("Gravidade (0-5)", 0, 5, value=int(gut_current_vals_page_d.get("G",0)), key=f"{widget_base_key_page_d}_G")
                                with cols_gut_page_d[1]: u_val_page_d = st.slider("Urgência (0-5)", 0, 5, value=int(gut_current_vals_page_d.get("U",0)), key=f"{widget_base_key_page_d}_U")
                                with cols_gut_page_d[2]: t_val_page_d = st.slider("Tendência (0-5)", 0, 5, value=int(gut_current_vals_page_d.get("T",0)), key=f"{widget_base_key_page_d}_T")
                                respostas_form_coletadas_nd_page_d[texto_pergunta_diag_page_d] = {"G": g_val_page_d, "U": u_val_page_d, "T": t_val_page_d}
                                if g_val_page_d > 0 or u_val_page_d > 0 or t_val_page_d > 0 : respondidas_count_diag_page_d +=1
                            elif "Pontuação (0-5)" in texto_pergunta_diag_page_d: 
                                val_page_d = respostas_form_coletadas_nd_page_d.get(texto_pergunta_diag_page_d, 0)
                                respostas_form_coletadas_nd_page_d[texto_pergunta_diag_page_d] = st.slider(texto_pergunta_diag_page_d, 0, 5, value=int(val_page_d), key=widget_base_key_page_d) 
                                if respostas_form_coletadas_nd_page_d[texto_pergunta_diag_page_d] != 0: respondidas_count_diag_page_d += 1
                            elif "Pontuação (0-10)" in texto_pergunta_diag_page_d:
                                val_page_d = respostas_form_coletadas_nd_page_d.get(texto_pergunta_diag_page_d, 0)
                                respostas_form_coletadas_nd_page_d[texto_pergunta_diag_page_d] = st.slider(texto_pergunta_diag_page_d, 0, 10, value=int(val_page_d), key=widget_base_key_page_d)
                                if respostas_form_coletadas_nd_page_d[texto_pergunta_diag_page_d] != 0: respondidas_count_diag_page_d += 1
                            elif "Texto Aberto" in texto_pergunta_diag_page_d:
                                val_page_d = respostas_form_coletadas_nd_page_d.get(texto_pergunta_diag_page_d, "")
                                respostas_form_coletadas_nd_page_d[texto_pergunta_diag_page_d] = st.text_area(texto_pergunta_diag_page_d, value=str(val_page_d), key=widget_base_key_page_d)
                                if respostas_form_coletadas_nd_page_d[texto_pergunta_diag_page_d].strip() != "": respondidas_count_diag_page_d += 1
                            elif "Escala" in texto_pergunta_diag_page_d: 
                                opcoes_escala_diag_page_d = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"] 
                                val_page_d = respostas_form_coletadas_nd_page_d.get(texto_pergunta_diag_page_d, "Selecione")
                                idx_sel_page_d = opcoes_escala_diag_page_d.index(val_page_d) if val_page_d in opcoes_escala_diag_page_d else 0
                                respostas_form_coletadas_nd_page_d[texto_pergunta_diag_page_d] = st.selectbox(texto_pergunta_diag_page_d, opcoes_escala_diag_page_d, index=idx_sel_page_d, key=widget_base_key_page_d)
                                if respostas_form_coletadas_nd_page_d[texto_pergunta_diag_page_d] != "Selecione": respondidas_count_diag_page_d += 1
                            else: 
                                val_page_d = respostas_form_coletadas_nd_page_d.get(texto_pergunta_diag_page_d, 0)
                                respostas_form_coletadas_nd_page_d[texto_pergunta_diag_page_d] = st.slider(texto_pergunta_diag_page_d, 0, 10, value=int(val_page_d), key=widget_base_key_page_d)
                                if respostas_form_coletadas_nd_page_d[texto_pergunta_diag_page_d] != 0: respondidas_count_diag_page_d += 1
                        st.divider()
                
                progresso_diag_page_d = round((respondidas_count_diag_page_d / total_perguntas_diag_page_d) * 100) if total_perguntas_diag_page_d > 0 else 0
                st.info(f"📊 Progresso: {respondidas_count_diag_page_d} de {total_perguntas_diag_page_d} respondidas ({progresso_diag_page_d}%)")
                
                obs_cli_diag_form_page_d = st.text_area("Sua Análise/Observações (opcional):", value=respostas_form_coletadas_nd_page_d.get("__obs_cliente__", ""), key=f"obs_cli_diag_page_d_{form_id_sufixo_nd_page_d}")
                respostas_form_coletadas_nd_page_d["__obs_cliente__"] = obs_cli_diag_form_page_d 
                
                diag_resumo_cli_diag_page_d = st.text_area("✍️ Resumo/principais insights (para PDF):", value=respostas_form_coletadas_nd_page_d.get("__resumo_cliente__", ""), key=f"diag_resumo_diag_page_d_{form_id_sufixo_nd_page_d}")
                respostas_form_coletadas_nd_page_d["__resumo_cliente__"] = diag_resumo_cli_diag_page_d

                enviar_diagnostico_btn_page_d = st.form_submit_button("✔️ Enviar Diagnóstico")

            if enviar_diagnostico_btn_page_d:
                # ... (Lógica de processamento e salvamento do formulário como na versão anterior)
                # Chamar gerar_pdf_diagnostico_completo
                # Limpar st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME] e st.session_state[temp_respostas_key_nd_page_d]
                pass # Código completo já fornecido anteriormente.

    except Exception as e_cliente_area:
        st.error(f"Ocorreu um erro na área do cliente: {e_cliente_area}")
        st.exception(e_cliente_area) # Mostra o traceback completo para depuração


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    try: # Try geral para a área do admin
        # ... (código do admin como na versão anterior, com as melhorias de PDF e Plotly)
        # Cada subseção do admin também pode ter seu próprio try-except se necessário
        pass # Código completo já fornecido anteriormente.
    except Exception as e_admin_area:
        st.error(f"Ocorreu um erro na área administrativa: {e_admin_area}")
        st.exception(e_admin_area)


if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()