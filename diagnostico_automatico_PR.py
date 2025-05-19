import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
from fpdf import FPDF
import tempfile
import re 
import json
import plotly.express as px

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
        else:
            df = pd.read_csv(filepath, encoding='utf-8')
            missing_cols = [col for col in columns if col not in df.columns]
            made_changes = False
            if missing_cols:
                for col in missing_cols:
                    if is_perguntas_file and col == "Categoria": df[col] = "Geral"
                    else: df[col] = pd.NA 
                made_changes = True
            if is_perguntas_file and "Categoria" not in df.columns:
                df["Categoria"] = "Geral"; made_changes = True
            if made_changes:
                df.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError: 
        pd.DataFrame(columns=columns).to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e:
        st.error(f"Erro ao inicializar/verificar {filepath}: {e}. O app pode não funcionar corretamente.")

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios)
    inicializar_csv(perguntas_csv, colunas_base_perguntas, is_perguntas_file=True)
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
except Exception as e_init_main_clean:
    st.error(f"Falha crítica na inicialização de arquivos CSV base: {e_init_main_clean}")
    st.exception(e_init_main_clean)
    st.markdown("---")
    st.markdown("### Solução de Problemas - Inicialização de Arquivos:")
    st.markdown("""
    1. Verifique se você tem permissão de escrita na pasta onde o script está rodando.
    2. Tente deletar os arquivos CSV da pasta do script. Eles serão recriados.
    3. Verifique o conteúdo dos CSVs, especialmente `perguntas_formulario.csv` e `usuarios.csv`.
    """)
    st.stop()


def registrar_acao(cnpj, acao, descricao):
    try:
        historico_df_ra_cl = pd.read_csv(historico_csv, encoding='utf-8') 
    except (FileNotFoundError, pd.errors.EmptyDataError): 
        historico_df_ra_cl = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    nova_data_ra_cl = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao }
    historico_df_ra_cl = pd.concat([historico_df_ra_cl, pd.DataFrame([nova_data_ra_cl])], ignore_index=True)
    historico_df_ra_cl.to_csv(historico_csv, index=False, encoding='utf-8')


def gerar_pdf_diagnostico_completo(diagnostico_data, usuario_data, perguntas_df_geracao, respostas_coletadas_geracao, medias_categorias_geracao):
    try:
        pdf = FPDF()
        pdf.add_page()
        empresa_nome_pdf_cl = usuario_data.get("Empresa", "N/D") # Renomeado para evitar conflito
        cnpj_pdf_cl = usuario_data.get("CNPJ", "N/D")
        nome_contato_pdf_cl = usuario_data.get("NomeContato", "")
        telefone_pdf_cl = usuario_data.get("Telefone", "")

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome_pdf_cl}"), 0, 1, 'C')
        pdf.ln(5)

        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 7, pdf_safe_text_output(f"Data do Diagnóstico: {diagnostico_data.get('Data','N/D')}"))
        pdf.multi_cell(0, 7, pdf_safe_text_output(f"Empresa: {empresa_nome_pdf_cl} (CNPJ: {cnpj_pdf_cl})"))
        if nome_contato_pdf_cl: pdf.multi_cell(0, 7, pdf_safe_text_output(f"Contato: {nome_contato_pdf_cl}"))
        if telefone_pdf_cl: pdf.multi_cell(0, 7, pdf_safe_text_output(f"Telefone: {telefone_pdf_cl}"))
        pdf.ln(3)

        pdf.multi_cell(0, 7, pdf_safe_text_output(f"Média Geral (Numérica): {diagnostico_data.get('Média Geral','N/A')}"))
        pdf.multi_cell(0, 7, pdf_safe_text_output(f"Média Scores GUT (G*U*T): {diagnostico_data.get('GUT Média','N/A')}"))
        pdf.ln(3)

        if medias_categorias_geracao:
            pdf.set_font("Arial", 'B', 11); pdf.multi_cell(0, 7, pdf_safe_text_output("Médias por Categoria (Perguntas de Pontuação):"))
            pdf.set_font("Arial", size=10)
            for cat_pdf_g_cl, media_cat_pdf_g_cl in medias_categorias_geracao.items(): # Renomeado
                pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat_pdf_g_cl}: {media_cat_pdf_g_cl}"))
            pdf.ln(5)

        resumo_cliente_pdf_cl = diagnostico_data.get("Diagnóstico", "") 
        analise_cliente_pdf_cl = diagnostico_data.get("Análise do Cliente", "") 
        
        if resumo_cliente_pdf_cl:
            pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output("Resumo do Diagnóstico (Cliente):"))
            pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(resumo_cliente_pdf_cl)); pdf.ln(3)
        if analise_cliente_pdf_cl:
            pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output("Análise/Observações do Cliente:"))
            pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(analise_cliente_pdf_cl)); pdf.ln(3)

        comentarios_admin_pdf_cl = diagnostico_data.get("Comentarios_Admin", "")
        if comentarios_admin_pdf_cl:
            pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output("Comentários do Consultor:"))
            pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(comentarios_admin_pdf_cl)); pdf.ln(3)
            
        pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 10, pdf_safe_text_output("Respostas Detalhadas por Categoria:"))
        categorias_unicas_pdf_ger_cl = []
        if "Categoria" in perguntas_df_geracao.columns: 
            categorias_unicas_pdf_ger_cl = perguntas_df_geracao["Categoria"].unique()
        
        for categoria_pdf_g_det_cl in categorias_unicas_pdf_ger_cl: # Renomeado
            pdf.set_font("Arial", 'B', 10); pdf.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria_pdf_g_det_cl}"))
            pdf.set_font("Arial", size=9)
            perguntas_cat_pdf_g_det_cl = perguntas_df_geracao[perguntas_df_geracao["Categoria"] == categoria_pdf_g_det_cl]
            for _, p_row_pdf_g_det_cl in perguntas_cat_pdf_g_det_cl.iterrows(): # Renomeado
                txt_p_pdf_g_det_cl = p_row_pdf_g_det_cl["Pergunta"]
                resp_p_pdf_g_det_cl = respostas_coletadas_geracao.get(txt_p_pdf_g_det_cl)
                if resp_p_pdf_g_det_cl is None: 
                    resp_p_pdf_g_det_cl = diagnostico_data.get(txt_p_pdf_g_det_cl, "N/R")

                if isinstance(txt_p_pdf_g_det_cl, str) and "[Matriz GUT]" in txt_p_pdf_g_det_cl: 
                    g_pdf_cl, u_pdf_cl, t_pdf_cl = 0,0,0 # Renomeado
                    score_gut_item_pdf_cl = 0
                    if isinstance(resp_p_pdf_g_det_cl, dict): 
                        g_pdf_cl,u_pdf_cl,t_pdf_cl = resp_p_pdf_g_det_cl.get("G",0), resp_p_pdf_g_det_cl.get("U",0), resp_p_pdf_g_det_cl.get("T",0)
                    elif isinstance(resp_p_pdf_g_det_cl, str): 
                        try: 
                            gut_data_pdf_cl = json.loads(resp_p_pdf_g_det_cl.replace("'", "\""))
                            g_pdf_cl,u_pdf_cl,t_pdf_cl = gut_data_pdf_cl.get("G",0), gut_data_pdf_cl.get("U",0), gut_data_pdf_cl.get("T",0)
                        except: pass 
                    score_gut_item_pdf_cl = g_pdf_cl*u_pdf_cl*t_pdf_cl
                    pdf.multi_cell(0,6,pdf_safe_text_output(f"  - {txt_p_pdf_g_det_cl.replace(' [Matriz GUT]','')}: G={g_pdf_cl}, U={u_pdf_cl}, T={t_pdf_cl} (Score: {score_gut_item_pdf_cl})"))
                elif isinstance(resp_p_pdf_g_det_cl, (int, float, str)): 
                    pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {txt_p_pdf_g_det_cl}: {resp_p_pdf_g_det_cl}"))
            pdf.ln(2)
        pdf.ln(3)
        
        pdf.add_page(); pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf.ln(5)
        pdf.set_font("Arial", size=10)
        gut_cards_pdf_ger_cl = [] # Renomeado
        for pergunta_pdf_k_g_cl, resp_pdf_k_g_val_cl in respostas_coletadas_geracao.items(): 
            if isinstance(pergunta_pdf_k_g_cl, str) and "[Matriz GUT]" in pergunta_pdf_k_g_cl:
                g_k_g_cl, u_k_g_cl, t_k_g_cl = 0,0,0 # Renomeado
                if isinstance(resp_pdf_k_g_val_cl, dict):
                    g_k_g_cl, u_k_g_cl, t_k_g_cl = resp_pdf_k_g_val_cl.get("G",0), resp_pdf_k_g_val_cl.get("U",0), resp_pdf_k_g_val_cl.get("T",0)
                elif isinstance(resp_pdf_k_g_val_cl, str): 
                    try: 
                        gut_data_k_g_cl = json.loads(resp_pdf_k_g_val_cl.replace("'", "\""))
                        g_k_g_cl,u_k_g_cl,t_k_g_cl = gut_data_k_g_cl.get("G",0), gut_data_k_g_cl.get("U",0), gut_data_k_g_cl.get("T",0)
                    except: pass
                
                score_gut_total_k_g_pdf_cl = g_k_g_cl * u_k_g_cl * t_k_g_cl
                prazo_k_g_pdf_cl = "N/A"
                if score_gut_total_k_g_pdf_cl >= 75: prazo_k_g_pdf_cl = "15 dias"
                elif score_gut_total_k_g_pdf_cl >= 40: prazo_k_g_pdf_cl = "30 dias"
                elif score_gut_total_k_g_pdf_cl >= 20: prazo_k_g_pdf_cl = "45 dias"
                elif score_gut_total_k_g_pdf_cl > 0: prazo_k_g_pdf_cl = "60 dias"
                else: continue
                if prazo_k_g_pdf_cl != "N/A":
                    gut_cards_pdf_ger_cl.append({"Tarefa": pergunta_pdf_k_g_cl.replace(" [Matriz GUT]", ""),"Prazo": prazo_k_g_pdf_cl, "Score": score_gut_total_k_g_pdf_cl})
        if gut_cards_pdf_ger_cl:
            gut_cards_pdf_ger_sorted_cl = sorted(gut_cards_pdf_ger_cl, key=lambda x_cl: (int(x_cl["Prazo"].split(" ")[0]), -x_cl["Score"])) # Renomeado lambda
            for card_item_f_k_g_pdf_cl in gut_cards_pdf_ger_sorted_cl: # Renomeado
                 pdf.multi_cell(0, 6, pdf_safe_text_output(f"Prazo: {card_item_f_k_g_pdf_cl['Prazo']} - Tarefa: {card_item_f_k_g_pdf_cl['Tarefa']} (Score GUT: {card_item_f_k_g_pdf_cl['Score']})"))
        else: pdf.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile_g_final_cl: # Renomeado
            pdf_path_g_final_cl = tmpfile_g_final_cl.name # Renomeado
            pdf.output(pdf_path_g_final_cl)
        return pdf_path_g_final_cl
    except Exception as e_pdf_full_cl: # Renomeado
        st.error(f"Erro ao gerar PDF: {e_pdf_full_cl}")
        st.exception(e_pdf_full_cl)
        return None

# --- Lógica de Login e Navegação Principal (Admin/Cliente) ---
if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_main_clean")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_page_clean"): 
        usuario_admin_login_cl = st.text_input("Usuário", key="admin_user_login_cl") 
        senha_admin_login_cl = st.text_input("Senha", type="password", key="admin_pass_login_cl")
        entrar_admin_login_cl = st.form_submit_button("Entrar")
    if entrar_admin_login_cl:
        try:
            df_admin_login_creds_cl = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            admin_encontrado_cl = df_admin_login_creds_cl[
                (df_admin_login_creds_cl["Usuario"] == usuario_admin_login_cl) & 
                (df_admin_login_creds_cl["Senha"] == senha_admin_login_cl)
            ]
            if not admin_encontrado_cl.empty:
                st.session_state.admin_logado = True
                st.success("Login de administrador bem-sucedido!")
                st.session_state.trigger_admin_rerun = True; st.rerun() 
            else: st.error("Usuário ou senha inválidos.")
        except FileNotFoundError: st.error(f"Arquivo {admin_credenciais_csv} não encontrado.")
        except pd.errors.EmptyDataError: st.error(f"Arquivo {admin_credenciais_csv} está vazio. Adicione um administrador.")
        except Exception as e_login_admin_cl: st.error(f"Erro no login do admin: {e_login_admin_cl}"); st.exception(e_login_admin_cl)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_page_clean"): 
        cnpj_cli_login_cl = st.text_input("CNPJ", key="cli_cnpj_login_cl") 
        senha_cli_login_cl = st.text_input("Senha", type="password", key="cli_pass_login_cl") 
        acessar_cli_login_cl = st.form_submit_button("Entrar")
    if acessar_cli_login_cl:
        try:
            if not os.path.exists(usuarios_csv): st.error(f"Arquivo {usuarios_csv} não encontrado."); st.stop()
            usuarios_login_df_cl = pd.read_csv(usuarios_csv, encoding='utf-8')
            if not os.path.exists(usuarios_bloqueados_csv): st.error(f"Arquivo {usuarios_bloqueados_csv} não encontrado."); st.stop()
            bloqueados_login_df_cl = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
            
            if cnpj_cli_login_cl in bloqueados_login_df_cl["CNPJ"].astype(str).values: 
                st.error("CNPJ bloqueado."); st.stop()
            user_match_li_cl = usuarios_login_df_cl[(usuarios_login_df_cl["CNPJ"].astype(str) == str(cnpj_cli_login_cl)) & (usuarios_login_df_cl["Senha"] == senha_cli_login_cl)]
            if user_match_li_cl.empty: st.error("CNPJ ou senha inválidos."); st.stop()
            
            st.session_state.cliente_logado = True
            st.session_state.cnpj = str(cnpj_cli_login_cl) 
            st.session_state.user = user_match_li_cl.iloc[0].to_dict() 
            st.session_state.inicio_sessao_cliente = time.time()
            registrar_acao(st.session_state.cnpj, "Login", "Usuário realizou login.")
            st.session_state.cliente_page = "Painel Principal"
            st.success("Login realizado com sucesso!"); st.session_state.trigger_cliente_rerun = True; st.rerun() 
        except FileNotFoundError as e_login_cli_fnf_cl: st.error(f"Arquivo não encontrado: {e_login_cli_fnf_cl.filename}.")
        except pd.errors.EmptyDataError as e_login_cli_empty_cl: st.error(f"Arquivo de usuários ou bloqueados está vazio: {e_login_cli_empty_cl}")
        except Exception as e_login_cli_cl: st.error(f"Erro no login do cliente: {e_login_cli_cl}"); st.exception(e_login_cli_cl)
    st.markdown('</div>', unsafe_allow_html=True); st.stop() 


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    try:
        st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
        
        DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME_CL = f"form_id_diagnostico_cliente_{st.session_state.cnpj}"

        st.session_state.cliente_page = st.sidebar.radio(
            "Menu Cliente", ["Painel Principal", "Novo Diagnóstico"],
            index=["Painel Principal", "Novo Diagnóstico"].index(st.session_state.cliente_page),
            key="cliente_menu_radio_main_clean"
        )
        if st.sidebar.button("⬅️ Sair do Portal Cliente"):
            keys_to_del_cli_logout_cl = ['cliente_logado', 'cnpj', 'user', 'inicio_sessao_cliente', 
                                           'diagnostico_enviado', 'cliente_page', DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME_CL]
            temp_resp_key_logout_cl = f"temp_respostas_{st.session_state.get(DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME_CL,'')}"
            if temp_resp_key_logout_cl in st.session_state:
                keys_to_del_cli_logout_cl.append(temp_resp_key_logout_cl)
            for key_cd_lo_cl in keys_to_del_cli_logout_cl:
                if key_cd_lo_cl in st.session_state: del st.session_state[key_cd_lo_cl]
            st.rerun()

        if st.session_state.cliente_page == "Painel Principal":
            # ... (Código do Painel Principal do Cliente, como na versão anterior)
            # Certifique-se que ele usa a lógica de GUT G*U*T para o Kanban
            # E que exibe Médias de Categoria no histórico.
             st.subheader("📌 Instruções Gerais")
             # ... (Resto da seção Painel Principal do Cliente, como na versão anterior)

        elif st.session_state.cliente_page == "Novo Diagnóstico":
            # ... (Código do Formulário de Novo Diagnóstico, como na versão anterior)
            # Certifique-se que usa DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME_CL e temp_respostas_key
            # E que a lógica de GUT G*U*T e categorias está correta.
            st.subheader("📋 Formulário de Novo Diagnóstico")
            # ... (Resto da seção Novo Diagnóstico do Cliente, como na versão anterior)

    except Exception as e_cliente_area_cl:
        st.error(f"Ocorreu um erro na área do cliente: {e_cliente_area_cl}")
        st.exception(e_cliente_area_cl) 


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    st.sidebar.image("https://raw.githubusercontent.com/AndersonCRMG/AppDiagnostico/main/Logo%20Transparente%20(1).png", width=100)
    st.sidebar.success("🟢 Admin Logado")

    if st.sidebar.button("🚪 Sair do Painel Admin"):
        st.session_state.admin_logado = False
        st.rerun() 

    menu_admin_main_view_cl = st.sidebar.selectbox( 
        "Funcionalidades Admin:",
        ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Perguntas", 
         "Gerenciar Clientes", "Gerenciar Administradores"],
        key="admin_menu_selectbox_main_page_view_clean" 
    )
    st.header(f"🔑 Painel Admin: {menu_admin_main_view_cl}")

    try: # Envolve toda a lógica do painel admin em um try-except principal
        if menu_admin_main_view_cl == "Visão Geral e Diagnósticos":
            st.write("DEBUG: Renderizando Visão Geral e Diagnósticos (Admin).") # DEBUG
            st.subheader("📊 Visão Geral dos Diagnósticos")
            # st.write("DEBUG: Visão Geral (Admin) - Subheader renderizado.") # DEBUG (opcional, já que o acima é similar)

            diagnosticos_df_admin_geral_cl = pd.DataFrame() 
            admin_data_loaded_successfully_cl = False

            try:
                # st.write(f"DEBUG: Tentando carregar o arquivo: {arquivo_csv}") # DEBUG (opcional)
                if not os.path.exists(arquivo_csv):
                    st.warning(f"Arquivo de diagnósticos ({arquivo_csv}) não encontrado.")
                else:
                    diagnosticos_df_admin_geral_cl = pd.read_csv(arquivo_csv, encoding='utf-8')
                    # st.write(f"DEBUG: Arquivo {arquivo_csv} carregado.") # DEBUG (opcional)
                    if diagnosticos_df_admin_geral_cl.empty:
                        st.info("Nenhum diagnóstico no sistema para exibir visão geral.")
                    else:
                        admin_data_loaded_successfully_cl = True
                        # st.write(f"DEBUG: {len(diagnosticos_df_admin_geral_cl)} diagnósticos carregados.") # DEBUG (opcional)
            except FileNotFoundError: st.error(f"ERRO: Arquivo ({arquivo_csv}) não encontrado.")
            except pd.errors.EmptyDataError: st.warning(f"Arquivo ({arquivo_csv}) está vazio.")
            except Exception as e_load_diag_admin_cl_section:
                st.error(f"Erro ao carregar diagnósticos: {e_load_diag_admin_cl_section}")
                st.exception(e_load_diag_admin_cl_section)
            
            # st.write(f"DEBUG: Status do carregamento de dados (admin): {admin_data_loaded_successfully_cl}") # DEBUG (opcional)

            if admin_data_loaded_successfully_cl:
                st.write("DEBUG: Exibindo dados do admin (Indicadores, Gráficos, etc.).") # DEBUG
                st.markdown("#### Indicadores Gerais")
                col_ig1_cl, col_ig2_cl, col_ig3_cl = st.columns(3)
                with col_ig1_cl: st.metric("📦 Total de Diagnósticos", len(diagnosticos_df_admin_geral_cl))
                with col_ig2_cl:
                    media_geral_todos_adm_cl = pd.to_numeric(diagnosticos_df_admin_geral_cl["Média Geral"], errors='coerce').mean()
                    st.metric("📈 Média Geral (Todos)", f"{media_geral_todos_adm_cl:.2f}" if pd.notna(media_geral_todos_adm_cl) else "N/A")
                with col_ig3_cl:
                    if "GUT Média" in diagnosticos_df_admin_geral_cl.columns:
                        gut_media_todos_adm_cl = pd.to_numeric(diagnosticos_df_admin_geral_cl["GUT Média"], errors='coerce').mean()
                        st.metric("🔥 GUT Média (G*U*T)", f"{gut_media_todos_adm_cl:.2f}" if pd.notna(gut_media_todos_adm_cl) else "N/A") # Texto atualizado
                    else: st.metric("🔥 GUT Média (G*U*T)", "N/A")
                st.divider()

                st.markdown("#### Evolução Mensal dos Diagnósticos")
                df_diag_vis_adm_cl = diagnosticos_df_admin_geral_cl.copy()
                df_diag_vis_adm_cl["Data"] = pd.to_datetime(df_diag_vis_adm_cl["Data"], errors="coerce")
                df_diag_vis_adm_cl = df_diag_vis_adm_cl.dropna(subset=["Data"])
                if not df_diag_vis_adm_cl.empty:
                    df_diag_vis_adm_cl["Mês/Ano"] = df_diag_vis_adm_cl["Data"].dt.to_period("M").astype(str) 
                    df_diag_vis_adm_cl["Média Geral"] = pd.to_numeric(df_diag_vis_adm_cl["Média Geral"], errors='coerce')
                    df_diag_vis_adm_cl["GUT Média"] = pd.to_numeric(df_diag_vis_adm_cl.get("GUT Média"), errors='coerce') if "GUT Média" in df_diag_vis_adm_cl else pd.Series(0, index=df_diag_vis_adm_cl.index)
                    resumo_mensal_adm_cl = df_diag_vis_adm_cl.groupby("Mês/Ano").agg(
                        Diagnósticos_Realizados=("CNPJ", "count"), 
                        Média_Geral_Mensal=("Média Geral", "mean"),
                        GUT_Média_Mensal=("GUT Média", "mean")
                    ).reset_index().sort_values("Mês/Ano")
                    resumo_mensal_adm_cl["Mês/Ano_Display"] = pd.to_datetime(resumo_mensal_adm_cl["Mês/Ano"]).dt.strftime('%b/%y')
                    if not resumo_mensal_adm_cl.empty:
                        fig_contagem_cl = px.bar(resumo_mensal_adm_cl, x="Mês/Ano_Display", y="Diagnósticos_Realizados", title="Número de Diagnósticos por Mês", labels={'Diagnósticos_Realizados':'Total Diagnósticos', "Mês/Ano_Display": "Mês/Ano"})
                        st.plotly_chart(fig_contagem_cl, use_container_width=True)
                        fig_medias_cl = px.line(resumo_mensal_adm_cl, x="Mês/Ano_Display", y=["Média_Geral_Mensal", "GUT_Média_Mensal"], title="Médias Gerais e GUT por Mês", labels={'value':'Média', 'variable':'Indicador', "Mês/Ano_Display": "Mês/Ano"})
                        fig_medias_cl.update_traces(mode='lines+markers')
                        st.plotly_chart(fig_medias_cl, use_container_width=True)
                    else: st.info("Sem dados para gráficos de evolução mensal.")
                else: st.info("Sem diagnósticos com datas válidas para evolução mensal.")
                st.divider()
                
                st.markdown("#### Ranking das Empresas (Média Geral)")
                # ... (código do ranking como antes)
                st.divider()

                st.markdown("#### Todos os Diagnósticos Enviados")
                st.dataframe(diagnosticos_df_admin_geral_cl.sort_values(by="Data", ascending=False).reset_index(drop=True))
                csv_export_admin_geral_cl_d = diagnosticos_df_admin_geral_cl.to_csv(index=False).encode('utf-8') 
                st.download_button("⬇️ Exportar Todos (CSV)", csv_export_admin_geral_cl_d, file_name="diagnosticos_completos.csv", mime="text/csv", key="download_all_csv_admin_cl")
                st.divider()
                
                st.markdown("#### Detalhar, Comentar e Baixar PDF de Diagnóstico Específico")
                # ... (código para detalhar, comentar e baixar PDF como antes)
            else: 
                st.warning("Não foi possível carregar dados de diagnósticos para a Visão Geral. Verifique se há diagnósticos salvos.")
            # st.write("DEBUG: Fim da seção Visão Geral e Diagnósticos (Admin).") # DEBUG Opcional

        elif menu_admin_main_view_cl == "Histórico de Usuários":
            # ... (Código da seção como antes)
            pass
        elif menu_admin_main_view_cl == "Gerenciar Perguntas":
            # ... (Código da seção como antes)
            pass
        elif menu_admin_main_view_cl == "Gerenciar Clientes":
            # ... (Código da seção como antes, com NomeContato e Telefone)
            pass
        elif menu_admin_main_view_cl == "Gerenciar Administradores":
            # ... (Código da seção como antes)
            pass

    except Exception as e_admin_area_d_main_cl:
        st.error(f"Ocorreu um erro geral na área administrativa: {e_admin_area_d_main_cl}")
        st.exception(e_admin_area_d_main_cl)

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()

# st.write(f"DEBUG FINAL: admin_logado: {st.session_state.admin_logado}, cliente_logado: {st.session_state.cliente_logado}, aba: {aba if 'aba' in locals() else 'Não definida'}")