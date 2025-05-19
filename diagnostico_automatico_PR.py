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
LOGOS_DIR = "client_logos" # Pasta para logos

# --- Inicialização do Session State ---
if "admin_logado" not in st.session_state: st.session_state.admin_logado = False
if "cliente_logado" not in st.session_state: st.session_state.cliente_logado = False
if "diagnostico_enviado" not in st.session_state: st.session_state.diagnostico_enviado = False
if "inicio_sessao_cliente" not in st.session_state: st.session_state.inicio_sessao_cliente = None
if "cliente_page" not in st.session_state: st.session_state.cliente_page = "Painel Principal"
if "cnpj" not in st.session_state: st.session_state.cnpj = None
if "user" not in st.session_state: st.session_state.user = None # Armazenará o dict do usuário logado

# --- Funções Utilitárias ---
def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s) 
    return s

def pdf_safe_text_output(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def find_client_logo_path(cnpj):
    if not cnpj: return None
    for ext in ["png", "jpg", "jpeg"]:
        path = os.path.join(LOGOS_DIR, f"{str(cnpj)}_logo.{ext}")
        if os.path.exists(path):
            return path
    return None

# --- Criação e Verificação de Arquivos e Pastas ---
if not os.path.exists(LOGOS_DIR):
    try:
        os.makedirs(LOGOS_DIR)
    except OSError as e:
        st.error(f"Não foi possível criar o diretório de logos '{LOGOS_DIR}': {e}")

colunas_base_diagnosticos = [
    "Data", "CNPJ", "Nome", "Email", "Empresa",
    "Média Geral", "GUT Média", "Observações", "Diagnóstico", 
    "Análise do Cliente", "Comentarios_Admin"
]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone"] # PathLogo não é mais necessário aqui
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
            # Não adicionamos PathLogo aqui, pois dependerá do upload
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
except Exception as e_init_final_code:
    st.error(f"Falha crítica na inicialização de arquivos CSV base: {e_init_final_code}")
    st.exception(e_init_final_code)
    st.stop()


def registrar_acao(cnpj, acao, descricao):
    try:
        historico_df = pd.read_csv(historico_csv, encoding='utf-8') 
    except (FileNotFoundError, pd.errors.EmptyDataError): 
        historico_df = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    nova_data = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": descricao }
    historico_df = pd.concat([historico_df, pd.DataFrame([nova_data])], ignore_index=True)
    historico_df.to_csv(historico_csv, index=False, encoding='utf-8')


def gerar_pdf_diagnostico_completo(diagnostico_data, usuario_data, perguntas_df_geracao, respostas_coletadas_geracao, medias_categorias_geracao):
    try:
        pdf = FPDF()
        pdf.add_page()
        empresa_nome_pdf = usuario_data.get("Empresa", "N/D")
        cnpj_pdf = usuario_data.get("CNPJ", "N/D")
        nome_contato_pdf = usuario_data.get("NomeContato", "")
        telefone_pdf = usuario_data.get("Telefone", "")
        
        # Adicionar logo da empresa no PDF
        logo_path_pdf = find_client_logo_path(cnpj_pdf)
        if logo_path_pdf:
            try:
                pdf.image(logo_path_pdf, x=10, y=8, w=33) # Ajuste x, y, w conforme necessário
                pdf.ln(20) # Pular linha após a logo
            except Exception as e_logo_pdf:
                st.warning(f"Não foi possível adicionar a logo ao PDF: {e_logo_pdf}")


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
            for cat_pdf, media_cat_pdf in medias_categorias_geracao.items():
                pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat_pdf}: {media_cat_pdf}"))
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
        categorias_unicas_pdf = []
        if perguntas_df_geracao is not None and "Categoria" in perguntas_df_geracao.columns: 
            categorias_unicas_pdf = perguntas_df_geracao["Categoria"].unique()
        
        for categoria_pdf_det in categorias_unicas_pdf:
            pdf.set_font("Arial", 'B', 10); pdf.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria_pdf_det}"))
            pdf.set_font("Arial", size=9)
            perguntas_cat_pdf_det = perguntas_df_geracao[perguntas_df_geracao["Categoria"] == categoria_pdf_det]
            for _, p_row_pdf_det in perguntas_cat_pdf_det.iterrows():
                txt_p_pdf_det = p_row_pdf_det["Pergunta"]
                resp_p_pdf_det = respostas_coletadas_geracao.get(txt_p_pdf_det) 
                if resp_p_pdf_det is None: 
                    resp_p_pdf_det = diagnostico_data.get(txt_p_pdf_det, "N/R")

                if isinstance(txt_p_pdf_det, str) and "[Matriz GUT]" in txt_p_pdf_det: 
                    g_pdf, u_pdf, t_pdf = 0,0,0
                    score_gut_item_pdf = 0
                    if isinstance(resp_p_pdf_det, dict): 
                        g_pdf,u_pdf,t_pdf = resp_p_pdf_det.get("G",0), resp_p_pdf_det.get("U",0), resp_p_pdf_det.get("T",0)
                    elif isinstance(resp_p_pdf_det, str): 
                        try: 
                            gut_data_pdf = json.loads(resp_p_pdf_det.replace("'", "\""))
                            g_pdf,u_pdf,t_pdf = gut_data_pdf.get("G",0), gut_data_pdf.get("U",0), gut_data_pdf.get("T",0)
                        except: pass 
                    score_gut_item_pdf = g_pdf*u_pdf*t_pdf
                    pdf.multi_cell(0,6,pdf_safe_text_output(f"  - {txt_p_pdf_det.replace(' [Matriz GUT]','')}: G={g_pdf}, U={u_pdf}, T={t_pdf} (Score: {score_gut_item_pdf})"))
                elif isinstance(resp_p_pdf_det, (int, float, str)): 
                    pdf.multi_cell(0, 6, pdf_safe_text_output(f"  - {txt_p_pdf_det}: {resp_p_pdf_det}"))
            pdf.ln(2)
        pdf.ln(3)
        
        pdf.add_page(); pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf.ln(5)
        pdf.set_font("Arial", size=10)
        gut_cards_pdf = [] 
        for pergunta_pdf_k, resp_pdf_k_val in respostas_coletadas_geracao.items(): 
            if isinstance(pergunta_pdf_k, str) and "[Matriz GUT]" in pergunta_pdf_k:
                g_k, u_k, t_k = 0,0,0
                if isinstance(resp_pdf_k_val, dict):
                    g_k, u_k, t_k = resp_pdf_k_val.get("G",0), resp_pdf_k_val.get("U",0), resp_pdf_k_val.get("T",0)
                elif isinstance(resp_pdf_k_val, str): 
                    try: 
                        gut_data_k = json.loads(resp_pdf_k_val.replace("'", "\""))
                        g_k,u_k,t_k = gut_data_k.get("G",0), gut_data_k.get("U",0), gut_data_k.get("T",0)
                    except: pass
                
                score_gut_total_k_pdf = g_k * u_k * t_k
                prazo_k_pdf = "N/A"
                if score_gut_total_k_pdf >= 75: prazo_k_pdf = "15 dias"
                elif score_gut_total_k_pdf >= 40: prazo_k_pdf = "30 dias"
                elif score_gut_total_k_pdf >= 20: prazo_k_pdf = "45 dias"
                elif score_gut_total_k_pdf > 0: prazo_k_pdf = "60 dias"
                else: continue
                if prazo_k_pdf != "N/A":
                    gut_cards_pdf.append({"Tarefa": pergunta_pdf_k.replace(" [Matriz GUT]", ""),"Prazo": prazo_k_pdf, "Score": score_gut_total_k_pdf})
        if gut_cards_pdf:
            gut_cards_pdf_sorted = sorted(gut_cards_pdf, key=lambda x_pdf_sort: (int(x_pdf_sort["Prazo"].split(" ")[0]), -x_pdf_sort["Score"])) 
            for card_item_pdf in gut_cards_pdf_sorted: 
                 pdf.multi_cell(0, 6, pdf_safe_text_output(f"Prazo: {card_item_pdf['Prazo']} - Tarefa: {card_item_pdf['Tarefa']} (Score GUT: {card_item_pdf['Score']})"))
        else: pdf.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile_final_pdf_func:
            pdf_path_final_pdf_func = tmpfile_final_pdf_func.name
            pdf.output(pdf_path_final_pdf_func)
        return pdf_path_final_pdf_func
    except Exception as e_pdf_main_func:
        st.error(f"Erro crítico ao gerar PDF: {e_pdf_main_func}")
        st.exception(e_pdf_main_func)
        return None

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_final_v2")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_final_v2"): 
        usuario_admin_login_v2 = st.text_input("Usuário", key="admin_user_login_final_v2") 
        senha_admin_login_v2 = st.text_input("Senha", type="password", key="admin_pass_login_final_v2")
        entrar_admin_login_v2 = st.form_submit_button("Entrar")
    if entrar_admin_login_v2:
        try:
            df_admin_login_creds_v2 = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            admin_encontrado_v2 = df_admin_login_creds_v2[
                (df_admin_login_creds_v2["Usuario"] == usuario_admin_login_v2) & 
                (df_admin_login_creds_v2["Senha"] == senha_admin_login_v2)
            ]
            if not admin_encontrado_v2.empty:
                st.session_state.admin_logado = True
                st.success("Login de administrador bem-sucedido!")
                st.session_state.trigger_admin_rerun = True; st.rerun() 
            else: st.error("Usuário ou senha inválidos.")
        except FileNotFoundError: st.error(f"Arquivo {admin_credenciais_csv} não encontrado.")
        except pd.errors.EmptyDataError: st.error(f"Arquivo {admin_credenciais_csv} está vazio.")
        except Exception as e_login_admin_final_v2: st.error(f"Erro no login: {e_login_admin_final_v2}"); st.exception(e_login_admin_final_v2)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_final_v2"): 
        cnpj_cli_login_v2 = st.text_input("CNPJ", key="cli_cnpj_login_final_v2") 
        senha_cli_login_v2 = st.text_input("Senha", type="password", key="cli_pass_login_final_v2") 
        acessar_cli_login_v2 = st.form_submit_button("Entrar")
    if acessar_cli_login_v2:
        try:
            if not os.path.exists(usuarios_csv): st.error(f"Arquivo {usuarios_csv} não encontrado."); st.stop()
            usuarios_login_df_v2 = pd.read_csv(usuarios_csv, encoding='utf-8')
            if not os.path.exists(usuarios_bloqueados_csv): st.error(f"Arquivo {usuarios_bloqueados_csv} não encontrado."); st.stop()
            bloqueados_login_df_v2 = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
            
            if cnpj_cli_login_v2 in bloqueados_login_df_v2["CNPJ"].astype(str).values: 
                st.error("CNPJ bloqueado."); st.stop()
            user_match_li_v2 = usuarios_login_df_v2[(usuarios_login_df_v2["CNPJ"].astype(str) == str(cnpj_cli_login_v2)) & (usuarios_login_df_v2["Senha"] == senha_cli_login_v2)]
            if user_match_li_v2.empty: st.error("CNPJ ou senha inválidos."); st.stop()
            
            st.session_state.cliente_logado = True
            st.session_state.cnpj = str(cnpj_cli_login_v2) 
            st.session_state.user = user_match_li_v2.iloc[0].to_dict() 
            st.session_state.inicio_sessao_cliente = time.time()
            registrar_acao(st.session_state.cnpj, "Login", "Usuário realizou login.")
            st.session_state.cliente_page = "Painel Principal"
            st.success("Login realizado com sucesso!"); st.session_state.trigger_cliente_rerun = True; st.rerun() 
        except FileNotFoundError as e_login_cli_fnf_final_v2: st.error(f"Arquivo não encontrado: {e_login_cli_fnf_final_v2.filename}.")
        except pd.errors.EmptyDataError as e_login_cli_empty_final_v2: st.error(f"Arquivo de usuários ou bloqueados está vazio: {e_login_cli_empty_final_v2}")
        except Exception as e_login_cli_final_v2: st.error(f"Erro no login do cliente: {e_login_cli_final_v2}"); st.exception(e_login_cli_final_v2)
    st.markdown('</div>', unsafe_allow_html=True); st.stop() 


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    try:
        st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
        
        # Exibir Logo e Informações do Cliente no Sidebar
        with st.sidebar.expander("Meu Perfil", expanded=False):
            logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
            if logo_cliente_path:
                st.image(logo_cliente_path, width=100)
            st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
            st.write(f"**CNPJ:** {st.session_state.cnpj}")
            st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
            st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")

        DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME_FINAL = f"form_id_diagnostico_cliente_{st.session_state.cnpj}"

        st.session_state.cliente_page = st.sidebar.radio(
            "Menu Cliente", ["Painel Principal", "Novo Diagnóstico"],
            index=["Painel Principal", "Novo Diagnóstico"].index(st.session_state.cliente_page),
            key="cliente_menu_radio_final_v3"
        )
        if st.sidebar.button("⬅️ Sair do Portal Cliente"):
            keys_to_del_cli_logout_final_v2 = ['cliente_logado', 'cnpj', 'user', 'inicio_sessao_cliente', 
                                           'diagnostico_enviado', 'cliente_page', DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME_FINAL]
            temp_resp_key_logout_final_v2 = f"temp_respostas_{st.session_state.get(DIAGNOSTICO_FORM_ID_KEY_USER_RUNTIME_FINAL,'')}"
            if temp_resp_key_logout_final_v2 in st.session_state:
                keys_to_del_cli_logout_final_v2.append(temp_resp_key_logout_final_v2)
            for key_cd_lo_final_v2 in keys_to_del_cli_logout_final_v2:
                if key_cd_lo_final_v2 in st.session_state: del st.session_state[key_cd_lo_final_v2]
            st.rerun()

        if st.session_state.cliente_page == "Painel Principal":
            st.subheader("📌 Meu Painel de Diagnósticos")
            with st.expander("📖 Instruções e Informações", expanded=True):
                st.markdown("- Visualize seus diagnósticos anteriores e sua evolução.")
                st.markdown("- Acompanhe seu plano de ação no Kanban.")
                st.markdown("- Para um novo diagnóstico, selecione 'Novo Diagnóstico' no menu ao lado.")
            
            if st.session_state.get("diagnostico_enviado", False):
                st.success("🎯 Último diagnóstico enviado com sucesso!"); st.session_state.diagnostico_enviado = False
            
            st.subheader("📁 Diagnósticos Anteriores")
            try:
                df_antigos_cli_pp_final_v2 = pd.read_csv(arquivo_csv, encoding='utf-8')
                df_cliente_view_pp_final_v2 = df_antigos_cli_pp_final_v2[df_antigos_cli_pp_final_v2["CNPJ"].astype(str) == st.session_state.cnpj]
            except (FileNotFoundError, pd.errors.EmptyDataError): 
                df_cliente_view_pp_final_v2 = pd.DataFrame()
            
            if df_cliente_view_pp_final_v2.empty: 
                st.info("Nenhum diagnóstico anterior. Comece um novo no menu ao lado.")
            else:
                df_cliente_view_pp_final_v2 = df_cliente_view_pp_final_v2.sort_values(by="Data", ascending=False)
                for idx_cv_pp_final_v2, row_cv_pp_final_v2 in df_cliente_view_pp_final_v2.iterrows():
                    with st.expander(f"📅 {row_cv_pp_final_v2['Data']} - {row_cv_pp_final_v2['Empresa']}"):
                        cols_diag_cli_v2 = st.columns(2)
                        with cols_diag_cli_v2[0]:
                            st.metric("Média Geral", f"{row_cv_pp_final_v2.get('Média Geral', 0.0):.2f}")
                        with cols_diag_cli_v2[1]:
                            st.metric("GUT Média (G*U*T)", f"{row_cv_pp_final_v2.get('GUT Média', 0.0):.2f}")
                        
                        st.write(f"**Resumo (Cliente):** {row_cv_pp_final_v2.get('Diagnóstico', 'N/P')}")
                        
                        st.markdown("**Médias por Categoria:**")
                        found_cat_media_cv_final_v2 = False
                        cat_cols_v2 = [col for col in row_cv_pp_final_v2.index if str(col).startswith("Media_Cat_")]
                        if cat_cols_v2:
                            num_cat_cols_v2 = len(cat_cols_v2)
                            display_cols_v2 = st.columns(num_cat_cols_v2 if num_cat_cols_v2 <= 4 else 4) 
                            col_idx_v2 = 0
                            for col_name_cv_final_v2 in cat_cols_v2:
                                cat_name_display_cv_final_v2 = col_name_cv_final_v2.replace("Media_Cat_", "").replace("_", " ")
                                with display_cols_v2[col_idx_v2 % len(display_cols_v2)]: 
                                     st.metric(f"Média {cat_name_display_cv_final_v2}", f"{row_cv_pp_final_v2.get(col_name_cv_final_v2, 0.0):.2f}")
                                col_idx_v2 += 1
                                found_cat_media_cv_final_v2 = True
                        if not found_cat_media_cv_final_v2: st.caption("  Nenhuma média por categoria.")

                        analise_cli_val_cv_final_v2 = row_cv_pp_final_v2.get("Análise do Cliente", "")
                        analise_cli_cv_final_v2 = st.text_area("🧠 Minha Análise sobre este Diagnóstico:", value=analise_cli_val_cv_final_v2, key=f"analise_cv_final_v2_{row_cv_pp_final_v2.name}")
                        if st.button("💾 Salvar Minha Análise", key=f"salvar_analise_cv_final_v2_{row_cv_pp_final_v2.name}"):
                            try:
                                df_antigos_upd_cv_final_v2 = pd.read_csv(arquivo_csv, encoding='utf-8') 
                                df_antigos_upd_cv_final_v2.loc[row_cv_pp_final_v2.name, "Análise do Cliente"] = analise_cli_cv_final_v2 
                                df_antigos_upd_cv_final_v2.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                registrar_acao(st.session_state.cnpj, "Análise Cliente", f"Editou análise de {row_cv_pp_final_v2['Data']}")
                                st.success("Análise salva!"); st.rerun()
                            except Exception as e_save_analise_final_v2: st.error(f"Erro ao salvar análise: {e_save_analise_final_v2}")
                        
                        com_admin_val_cv_final_v2 = row_cv_pp_final_v2.get("Comentarios_Admin", "")
                        if com_admin_val_cv_final_v2 and not pd.isna(com_admin_val_cv_final_v2):
                            st.markdown("**Comentários do Consultor:**"); st.info(f"{com_admin_val_cv_final_v2}")
                        else: st.caption("Nenhum comentário do consultor.")
                        st.markdown("---")
                
                st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
                gut_cards_painel_final_v2 = []
                if not df_cliente_view_pp_final_v2.empty:
                    latest_diag_row_painel_final_v2 = df_cliente_view_pp_final_v2.iloc[0]
                    for pergunta_p_final_v2, resposta_p_val_str_final_v2 in latest_diag_row_painel_final_v2.items():
                        if isinstance(pergunta_p_final_v2, str) and "[Matriz GUT]" in pergunta_p_final_v2:
                            try:
                                if pd.notna(resposta_p_val_str_final_v2) and isinstance(resposta_p_val_str_final_v2, str):
                                    gut_data_final_v2 = json.loads(resposta_p_val_str_final_v2.replace("'", "\"")) 
                                    g_final_v2 = int(gut_data_final_v2.get("G", 0))
                                    u_final_v2 = int(gut_data_final_v2.get("U", 0))
                                    t_final_v2 = int(gut_data_final_v2.get("T", 0))
                                    score_gut_total_p_final_v2 = g_final_v2 * u_final_v2 * t_final_v2
                                    
                                    prazo_p_final_v2 = "N/A"
                                    if score_gut_total_p_final_v2 >= 75: prazo_p_final_v2 = "15 dias"
                                    elif score_gut_total_p_final_v2 >= 40: prazo_p_final_v2 = "30 dias"
                                    elif score_gut_total_p_final_v2 >= 20: prazo_p_final_v2 = "45 dias"
                                    elif score_gut_total_p_final_v2 > 0: prazo_p_final_v2 = "60 dias"
                                    else: continue 

                                    if prazo_p_final_v2 != "N/A":
                                        gut_cards_painel_final_v2.append({
                                            "Tarefa": pergunta_p_final_v2.replace(" [Matriz GUT]", ""), 
                                            "Prazo": prazo_p_final_v2, "Score": score_gut_total_p_final_v2, 
                                            "Responsável": st.session_state.user.get("Empresa", "N/D")
                                        })
                            except (json.JSONDecodeError, ValueError, TypeError) as e_k_final_v2:
                                st.warning(f"Erro ao processar GUT p/ Kanban: '{pergunta_p_final_v2}' ({resposta_p_val_str_final_v2}). Erro: {e_k_final_v2}")
                
                if gut_cards_painel_final_v2:
                    gut_cards_sorted_p_final_v2 = sorted(gut_cards_painel_final_v2, key=lambda x_final_v2: x_final_v2["Score"], reverse=True)
                    prazos_def_p_final_v2 = sorted(list(set(card_final_v2["Prazo"] for card_final_v2 in gut_cards_sorted_p_final_v2)), key=lambda x_d_final_v2: int(x_d_final_v2.split(" ")[0])) 
                    if prazos_def_p_final_v2:
                        cols_kanban_p_final_v2 = st.columns(len(prazos_def_p_final_v2))
                        for idx_kp_final_v2, prazo_col_kp_final_v2 in enumerate(prazos_def_p_final_v2):
                            with cols_kanban_p_final_v2[idx_kp_final_v2]:
                                st.markdown(f"#### ⏱️ {prazo_col_kp_final_v2}")
                                for card_item_kp_final_v2 in gut_cards_sorted_p_final_v2:
                                    if card_item_kp_final_v2["Prazo"] == prazo_col_kp_final_v2:
                                        st.markdown(f"""<div class="custom-card"><b>{card_item_kp_final_v2['Tarefa']}</b> (Score GUT: {card_item_kp_final_v2['Score']})<br><small><i>👤 {card_item_kp_final_v2['Responsável']}</i></small></div>""", unsafe_allow_html=True)
                else: st.info("Nenhuma ação prioritária para o Kanban (GUT).")
                
                st.subheader("📈 Comparativo de Evolução")
                if len(df_cliente_view_pp_final_v2) > 1:
                    grafico_comp_ev_final_v2 = df_cliente_view_pp_final_v2.sort_values(by="Data")
                    grafico_comp_ev_final_v2["Data"] = pd.to_datetime(grafico_comp_ev_final_v2["Data"])
                    colunas_plot_comp_final_v2 = ['Média Geral', 'GUT Média'] 
                    for col_g_comp_final_v2 in grafico_comp_ev_final_v2.columns:
                        if str(col_g_comp_final_v2).startswith("Media_Cat_") and pd.api.types.is_numeric_dtype(grafico_comp_ev_final_v2[col_g_comp_final_v2]):
                            colunas_plot_comp_final_v2.append(col_g_comp_final_v2)
                    for col_plot_c_final_v2 in colunas_plot_comp_final_v2:
                        if col_plot_c_final_v2 in grafico_comp_ev_final_v2.columns: grafico_comp_ev_final_v2[col_plot_c_final_v2] = pd.to_numeric(grafico_comp_ev_final_v2[col_plot_c_final_v2], errors='coerce')
                    
                    colunas_validas_plot_final_v2 = [c_final_v2 for c_final_v2 in colunas_plot_comp_final_v2 if c_final_v2 in grafico_comp_ev_final_v2.columns and pd.api.types.is_numeric_dtype(grafico_comp_ev_final_v2[c_final_v2])]
                    if colunas_validas_plot_final_v2:
                        st.line_chart(grafico_comp_ev_final_v2.set_index("Data")[colunas_validas_plot_final_v2].dropna(axis=1, how='all'))
                    
                    st.subheader("📊 Comparação Entre Diagnósticos") 
                    opcoes_cli_final_v2 = grafico_comp_ev_final_v2["Data"].astype(str).tolist()
                    if len(opcoes_cli_final_v2) >= 2:
                        diag_atual_idx_final_v2, diag_anterior_idx_final_v2 = len(opcoes_cli_final_v2)-1, len(opcoes_cli_final_v2)-2
                        diag_atual_sel_cli_final_v2 = st.selectbox("Diagnóstico mais recente:", opcoes_cli_final_v2, index=diag_atual_idx_final_v2, key="diag_atual_sel_cli_final_v2")
                        diag_anterior_sel_cli_final_v2 = st.selectbox("Diagnóstico anterior:", opcoes_cli_final_v2, index=diag_anterior_idx_final_v2, key="diag_anterior_sel_cli_final_v2")
                        atual_cli_final_v2 = grafico_comp_ev_final_v2[grafico_comp_ev_final_v2["Data"].astype(str) == diag_atual_sel_cli_final_v2].iloc[0]
                        anterior_cli_final_v2 = grafico_comp_ev_final_v2[grafico_comp_ev_final_v2["Data"].astype(str) == diag_anterior_sel_cli_final_v2].iloc[0]
                        st.write(f"### 📅 Comparando {diag_anterior_sel_cli_final_v2.split(' ')[0]} ⟶ {diag_atual_sel_cli_final_v2.split(' ')[0]}")
                        cols_excluir_comp_final_v2 = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
                        variaveis_comp_final_v2 = [col_f_v2 for col_f_v2 in grafico_comp_ev_final_v2.columns if col_f_v2 not in cols_excluir_comp_final_v2 and pd.api.types.is_numeric_dtype(grafico_comp_ev_final_v2[col_f_v2])]
                        if variaveis_comp_final_v2:
                            comp_data_final_v2 = []
                            for v_comp_final_v2 in variaveis_comp_final_v2:
                                val_ant_c_final_v2 = pd.to_numeric(anterior_cli_final_v2.get(v_comp_final_v2), errors='coerce')
                                val_atu_c_final_v2 = pd.to_numeric(atual_cli_final_v2.get(v_comp_final_v2), errors='coerce')
                                evolucao_c_final_v2 = "➖ Igual"
                                if pd.notna(val_ant_c_final_v2) and pd.notna(val_atu_c_final_v2):
                                    if val_atu_c_final_v2 > val_ant_c_final_v2: evolucao_c_final_v2 = "🔼 Melhorou"
                                    elif val_atu_c_final_v2 < val_ant_c_final_v2: evolucao_c_final_v2 = "🔽 Piorou"
                                display_name_comp_final_v2 = v_comp_final_v2.replace("Media_Cat_", "Média ").replace("_", " ")
                                if "[Pontuação (0-10)]" in display_name_comp_final_v2 or "[Pontuação (0-5) + Matriz GUT]" in display_name_comp_final_v2 or "[Matriz GUT]" in display_name_comp_final_v2:
                                    display_name_comp_final_v2 = display_name_comp_final_v2.split(" [")[0] 
                                comp_data_final_v2.append({"Indicador": display_name_comp_final_v2, "Anterior": val_ant_c_final_v2 if pd.notna(val_ant_c_final_v2) else "N/A", "Atual": val_atu_c_final_v2 if pd.notna(val_atu_c_final_v2) else "N/A", "Evolução": evolucao_c_final_v2})
                            st.dataframe(pd.DataFrame(comp_data_final_v2))
                        else: st.info("Sem dados numéricos para comparação.")
                    else: st.info("Pelo menos dois diagnósticos para comparação.")
                else: st.info("Pelo menos dois diagnósticos para comparativos.")

        elif st.session_state.cliente_page == "Novo Diagnóstico":
            st.subheader("📋 Formulário de Novo Diagnóstico")
            
            DIAGNOSTICO_FORM_ID_KEY_USER = f"form_id_diagnostico_cliente_{st.session_state.cnpj}" 
            if DIAGNOSTICO_FORM_ID_KEY_USER not in st.session_state:
                st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER] = datetime.now().strftime("%Y%m%d%H%M%S%f")
            form_id_sufixo_nd_final_v2 = st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER]

            temp_respostas_key_nd_final_v2 = f"temp_respostas_{form_id_sufixo_nd_final_v2}"
            if temp_respostas_key_nd_final_v2 not in st.session_state:
                st.session_state[temp_respostas_key_nd_final_v2] = {}
            
            respostas_form_coletadas_nd_final_v2 = st.session_state[temp_respostas_key_nd_final_v2]
            
            try:
                perguntas_df_diag_final_v2 = pd.read_csv(perguntas_csv, encoding='utf-8')
                if "Categoria" not in perguntas_df_diag_final_v2.columns: 
                    perguntas_df_diag_final_v2["Categoria"] = "Geral"
            except (FileNotFoundError, pd.errors.EmptyDataError): 
                st.error(f"Arquivo de perguntas ({perguntas_csv}) não encontrado ou vazio."); st.stop()
            
            if perguntas_df_diag_final_v2.empty: 
                st.warning("Nenhuma pergunta cadastrada."); st.stop()
            
            total_perguntas_diag_final_v2 = len(perguntas_df_diag_final_v2)
            respondidas_count_diag_final_v2 = 0 
            
            if "Categoria" not in perguntas_df_diag_final_v2.columns: 
                st.error("Coluna 'Categoria' não encontrada no arquivo de perguntas."); st.stop()

            categorias_unicas_diag_final_v2 = perguntas_df_diag_final_v2["Categoria"].unique()
            
            with st.form(key=f"diagnostico_form_completo_{form_id_sufixo_nd_final_v2}"):
                if total_perguntas_diag_final_v2 == 0:
                    st.warning("Nenhuma pergunta disponível.")
                else:
                    for categoria_diag_final_v2 in categorias_unicas_diag_final_v2:
                        st.markdown(f"#### Categoria: {categoria_diag_final_v2}")
                        perguntas_cat_diag_final_v2 = perguntas_df_diag_final_v2[perguntas_df_diag_final_v2["Categoria"] == categoria_diag_final_v2]
                        
                        if perguntas_cat_diag_final_v2.empty: continue

                        for idx_diag_f_final_v2, row_diag_f_final_v2 in perguntas_cat_diag_final_v2.iterrows():
                            texto_pergunta_diag_final_v2 = str(row_diag_f_final_v2["Pergunta"]) 
                            widget_base_key_final_v2 = f"q_form_final_v2_{idx_diag_f_final_v2}" 

                            if "[Matriz GUT]" in texto_pergunta_diag_final_v2:
                                st.markdown(f"**{texto_pergunta_diag_final_v2.replace(' [Matriz GUT]', '')}**")
                                cols_gut_final_v2 = st.columns(3)
                                gut_current_vals_final_v2 = respostas_form_coletadas_nd_final_v2.get(texto_pergunta_diag_final_v2, {"G":0, "U":0, "T":0})
                                with cols_gut_final_v2[0]: g_val_final_v2 = st.slider("Gravidade (0-5)", 0, 5, value=int(gut_current_vals_final_v2.get("G",0)), key=f"{widget_base_key_final_v2}_G")
                                with cols_gut_final_v2[1]: u_val_final_v2 = st.slider("Urgência (0-5)", 0, 5, value=int(gut_current_vals_final_v2.get("U",0)), key=f"{widget_base_key_final_v2}_U")
                                with cols_gut_final_v2[2]: t_val_final_v2 = st.slider("Tendência (0-5)", 0, 5, value=int(gut_current_vals_final_v2.get("T",0)), key=f"{widget_base_key_final_v2}_T")
                                respostas_form_coletadas_nd_final_v2[texto_pergunta_diag_final_v2] = {"G": g_val_final_v2, "U": u_val_final_v2, "T": t_val_final_v2}
                                if g_val_final_v2 > 0 or u_val_final_v2 > 0 or t_val_final_v2 > 0 : respondidas_count_diag_final_v2 +=1
                            elif "Pontuação (0-5)" in texto_pergunta_diag_final_v2: 
                                val_final_v2 = respostas_form_coletadas_nd_final_v2.get(texto_pergunta_diag_final_v2, 0)
                                respostas_form_coletadas_nd_final_v2[texto_pergunta_diag_final_v2] = st.slider(texto_pergunta_diag_final_v2, 0, 5, value=int(val_final_v2), key=widget_base_key_final_v2) 
                                if respostas_form_coletadas_nd_final_v2[texto_pergunta_diag_final_v2] != 0: respondidas_count_diag_final_v2 += 1
                            elif "Pontuação (0-10)" in texto_pergunta_diag_final_v2:
                                val_final_v2 = respostas_form_coletadas_nd_final_v2.get(texto_pergunta_diag_final_v2, 0)
                                respostas_form_coletadas_nd_final_v2[texto_pergunta_diag_final_v2] = st.slider(texto_pergunta_diag_final_v2, 0, 10, value=int(val_final_v2), key=widget_base_key_final_v2)
                                if respostas_form_coletadas_nd_final_v2[texto_pergunta_diag_final_v2] != 0: respondidas_count_diag_final_v2 += 1
                            elif "Texto Aberto" in texto_pergunta_diag_final_v2:
                                val_final_v2 = respostas_form_coletadas_nd_final_v2.get(texto_pergunta_diag_final_v2, "")
                                respostas_form_coletadas_nd_final_v2[texto_pergunta_diag_final_v2] = st.text_area(texto_pergunta_diag_final_v2, value=str(val_final_v2), key=widget_base_key_final_v2)
                                if respostas_form_coletadas_nd_final_v2[texto_pergunta_diag_final_v2].strip() != "": respondidas_count_diag_final_v2 += 1
                            elif "Escala" in texto_pergunta_diag_final_v2: 
                                opcoes_escala_diag_final_v2 = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"] 
                                val_final_v2 = respostas_form_coletadas_nd_final_v2.get(texto_pergunta_diag_final_v2, "Selecione")
                                idx_sel_final_v2 = opcoes_escala_diag_final_v2.index(val_final_v2) if val_final_v2 in opcoes_escala_diag_final_v2 else 0
                                respostas_form_coletadas_nd_final_v2[texto_pergunta_diag_final_v2] = st.selectbox(texto_pergunta_diag_final_v2, opcoes_escala_diag_final_v2, index=idx_sel_final_v2, key=widget_base_key_final_v2)
                                if respostas_form_coletadas_nd_final_v2[texto_pergunta_diag_final_v2] != "Selecione": respondidas_count_diag_final_v2 += 1
                            else: 
                                val_final_v2 = respostas_form_coletadas_nd_final_v2.get(texto_pergunta_diag_final_v2, 0)
                                respostas_form_coletadas_nd_final_v2[texto_pergunta_diag_final_v2] = st.slider(texto_pergunta_diag_final_v2, 0, 10, value=int(val_final_v2), key=widget_base_key_final_v2)
                                if respostas_form_coletadas_nd_final_v2[texto_pergunta_diag_final_v2] != 0: respondidas_count_diag_final_v2 += 1
                        st.divider()
                
                progresso_diag_final_v2 = round((respondidas_count_diag_final_v2 / total_perguntas_diag_final_v2) * 100) if total_perguntas_diag_final_v2 > 0 else 0
                st.info(f"📊 Progresso: {respondidas_count_diag_final_v2} de {total_perguntas_diag_final_v2} respondidas ({progresso_diag_final_v2}%)")
                
                obs_cli_diag_form_final_v2 = st.text_area("Sua Análise/Observações (opcional):", value=respostas_form_coletadas_nd_final_v2.get("__obs_cliente__", ""), key=f"obs_cli_diag_final_v2_{form_id_sufixo_nd_final_v2}")
                respostas_form_coletadas_nd_final_v2["__obs_cliente__"] = obs_cli_diag_form_final_v2
                
                diag_resumo_cli_diag_final_v2 = st.text_area("✍️ Resumo/principais insights (para PDF):", value=respostas_form_coletadas_nd_final_v2.get("__resumo_cliente__", ""), key=f"diag_resumo_diag_final_v2_{form_id_sufixo_nd_final_v2}")
                respostas_form_coletadas_nd_final_v2["__resumo_cliente__"] = diag_resumo_cli_diag_final_v2

                enviar_diagnostico_btn_final_v2 = st.form_submit_button("✔️ Enviar Diagnóstico")

            if enviar_diagnostico_btn_final_v2:
                if respondidas_count_diag_final_v2 < total_perguntas_diag_final_v2: st.warning("Responda todas as perguntas.")
                elif not respostas_form_coletadas_nd_final_v2["__resumo_cliente__"].strip(): st.error("O campo 'Resumo/principais insights (para PDF)' é obrigatório.")
                else:
                    soma_total_gut_scores_final_v2, count_gut_perguntas_final_v2 = 0, 0
                    respostas_finais_para_salvar_final_v2 = {}

                    for pergunta_env_final_v2, resposta_env_final_v2 in respostas_form_coletadas_nd_final_v2.items():
                        if pergunta_env_final_v2.startswith("__"): continue 
                        if isinstance(pergunta_env_final_v2, str) and "[Matriz GUT]" in pergunta_env_final_v2 and isinstance(resposta_env_final_v2, dict):
                            respostas_finais_para_salvar_final_v2[pergunta_env_final_v2] = json.dumps(resposta_env_final_v2) 
                            g_f_v2, u_f_v2, t_f_v2 = resposta_env_final_v2.get("G",0), resposta_env_final_v2.get("U",0), resposta_env_final_v2.get("T",0)
                            soma_total_gut_scores_final_v2 += (g_f_v2 * u_f_v2 * t_f_v2)
                            count_gut_perguntas_final_v2 +=1
                        else:
                            respostas_finais_para_salvar_final_v2[pergunta_env_final_v2] = resposta_env_final_v2

                    gut_media_calc_final_v2 = round(soma_total_gut_scores_final_v2 / count_gut_perguntas_final_v2, 2) if count_gut_perguntas_final_v2 > 0 else 0.0
                    numeric_resp_calc_final_v2 = [v_f_v2 for k_f_v2, v_f_v2 in respostas_finais_para_salvar_final_v2.items() if isinstance(v_f_v2, (int, float)) and ("Pontuação (0-10)" in k_f_v2 or "Pontuação (0-5)" in k_f_v2)] 
                    media_geral_calc_final_val_v2 = round(sum(numeric_resp_calc_final_v2) / len(numeric_resp_calc_final_v2), 2) if numeric_resp_calc_final_v2 else 0.0
                    empresa_nome_final_val_v2 = st.session_state.user.get("Empresa", "N/D")
                    
                    nova_linha_final_val_v2 = {
                        "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": st.session_state.cnpj,
                        "Nome": st.session_state.user.get("CNPJ", ""), "Email": "", "Empresa": empresa_nome_final_val_v2,
                        "Média Geral": media_geral_calc_final_val_v2, "GUT Média": gut_media_calc_final_v2, 
                        "Observações": "", 
                        "Análise do Cliente": respostas_form_coletadas_nd_final_v2.get("__obs_cliente__",""), 
                        "Diagnóstico": respostas_form_coletadas_nd_final_v2.get("__resumo_cliente__",""), 
                        "Comentarios_Admin": ""
                    }
                    nova_linha_final_val_v2.update(respostas_finais_para_salvar_final_v2)

                    medias_por_categoria_final_val_v2 = {}
                    for cat_final_calc_val_v2 in categorias_unicas_diag_final_v2:
                        perguntas_cat_final_df_val_v2 = perguntas_df_diag_final_v2[perguntas_df_diag_final_v2["Categoria"] == cat_final_calc_val_v2]
                        soma_cat_final_val_v2, cont_num_cat_final_val_v2 = 0, 0
                        for _, p_row_final_val_v2 in perguntas_cat_final_df_val_v2.iterrows():
                            txt_p_final_val_v2 = p_row_final_val_v2["Pergunta"]
                            resp_p_final_val_v2 = respostas_form_coletadas_nd_final_v2.get(txt_p_final_val_v2)
                            if isinstance(resp_p_final_val_v2, (int, float)) and \
                               (isinstance(txt_p_final_val_v2, str) and "[Matriz GUT]" not in txt_p_final_val_v2) and \
                               (isinstance(txt_p_final_val_v2, str) and ("Pontuação (0-10)" in txt_p_final_val_v2 or "Pontuação (0-5)" in txt_p_final_val_v2)):
                                soma_cat_final_val_v2 += resp_p_final_val_v2
                                cont_num_cat_final_val_v2 += 1
                        media_c_final_val_v2 = round(soma_cat_final_val_v2 / cont_num_cat_final_val_v2, 2) if cont_num_cat_final_val_v2 > 0 else 0.0
                        nome_col_media_cat_final_val_v2 = f"Media_Cat_{sanitize_column_name(cat_final_calc_val_v2)}"
                        nova_linha_final_val_v2[nome_col_media_cat_final_val_v2] = media_c_final_val_v2
                        medias_por_categoria_final_val_v2[cat_final_calc_val_v2] = media_c_final_val_v2

                    try: df_diag_todos_final_val_v2 = pd.read_csv(arquivo_csv, encoding='utf-8')
                    except (FileNotFoundError, pd.errors.EmptyDataError): df_diag_todos_final_val_v2 = pd.DataFrame() 
                    
                    for col_f_save_final_val_v2 in nova_linha_final_val_v2.keys(): 
                        if col_f_save_final_val_v2 not in df_diag_todos_final_val_v2.columns: df_diag_todos_final_val_v2[col_f_save_final_val_v2] = pd.NA 
                    df_diag_todos_final_val_v2 = pd.concat([df_diag_todos_final_val_v2, pd.DataFrame([nova_linha_final_val_v2])], ignore_index=True)
                    df_diag_todos_final_val_v2.to_csv(arquivo_csv, index=False, encoding='utf-8')
                    
                    st.success("Diagnóstico enviado com sucesso!")
                    registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", "Cliente enviou novo diagnóstico.")
                    
                    pdf_path_final_val_v2 = gerar_pdf_diagnostico_completo(
                        diagnostico_data=nova_linha_final_val_v2, 
                        usuario_data=st.session_state.user, 
                        perguntas_df_geracao=perguntas_df_diag_final_v2, 
                        respostas_coletadas_geracao=respostas_form_coletadas_nd_final_v2,
                        medias_categorias_geracao=medias_por_categoria_final_val_v2
                    )
                    if pdf_path_final_val_v2:
                        with open(pdf_path_final_val_v2, "rb") as f_pdf_final_val_v2:
                            st.download_button(label="📄 Baixar PDF do Diagnóstico", data=f_pdf_final_val_v2, 
                                           file_name=f"diagnostico_{sanitize_column_name(empresa_nome_final_val_v2)}_{datetime.now().strftime('%Y%m%d')}.pdf", 
                                           mime="application/pdf", key="download_pdf_cliente_final_v2")
                        registrar_acao(st.session_state.cnpj, "Download PDF", "Baixou PDF do novo diagnóstico.")
                    
                    if DIAGNOSTICO_FORM_ID_KEY_USER in st.session_state: del st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER]
                    if temp_respostas_key_nd_final_v2 in st.session_state: del st.session_state[temp_respostas_key_nd_final_v2]
                    
                    st.session_state.diagnostico_enviado = True
                    st.session_state.cliente_page = "Painel Principal" 
                    st.rerun()
    except Exception as e_cliente_area_final_v2:
        st.error(f"Ocorreu um erro na área do cliente: {e_cliente_area_final_v2}")
        st.exception(e_cliente_area_final_v2) 


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.admin_logado:
    st.sidebar.image("https://raw.githubusercontent.com/AndersonCRMG/AppDiagnostico/main/Logo%20Transparente%20(1).png", width=100)
    st.sidebar.success("🟢 Admin Logado")

    if st.sidebar.button("🚪 Sair do Painel Admin"):
        st.session_state.admin_logado = False; st.rerun() 

    menu_admin = st.sidebar.selectbox( 
        "Funcionalidades Admin:",
        ["Visão Geral e Diagnósticos", "Histórico de Usuários", "Gerenciar Perguntas", 
         "Gerenciar Clientes", "Gerenciar Administradores"],
        key="admin_menu_selectbox_final_v2" 
    )
    st.header(f"🔑 Painel Admin: {menu_admin}")

    try: 
        if menu_admin == "Visão Geral e Diagnósticos":
            # st.write("--- DEBUG: Entrando na seção 'Visão Geral e Diagnósticos' ---")  # DEBUG Opcional
            st.subheader("📊 Visão Geral dos Diagnósticos")

            diagnosticos_df_admin = None 
            admin_data_loaded = False

            try:
                if not os.path.exists(arquivo_csv):
                    st.warning(f"ARQUIVO NÃO ENCONTRADO: ({arquivo_csv}).")
                elif os.path.getsize(arquivo_csv) == 0:
                    st.warning(f"ARQUIVO VAZIO (0 bytes): ({arquivo_csv}).")
                else:
                    diagnosticos_df_admin = pd.read_csv(arquivo_csv, encoding='utf-8')
                    if diagnosticos_df_admin.empty:
                        st.info("INFO: Arquivo de diagnósticos lido, mas vazio (sem dados).")
                    else:
                        admin_data_loaded = True
            except pd.errors.EmptyDataError: 
                st.warning(f"AVISO (Pandas EmptyDataError): Arquivo ({arquivo_csv}) parece vazio ou mal formatado.")
            except Exception as e_load_diag_admin:
                st.error(f"ERRO AO CARREGAR DIAGNÓSTICOS: {e_load_diag_admin}")
                st.exception(e_load_diag_admin)
            
            if admin_data_loaded and diagnosticos_df_admin is not None and not diagnosticos_df_admin.empty:
                st.markdown("#### Indicadores Gerais")
                col_ig1, col_ig2, col_ig3 = st.columns(3)
                with col_ig1: st.metric("📦 Total de Diagnósticos", len(diagnosticos_df_admin))
                with col_ig2:
                    media_geral_todos = pd.to_numeric(diagnosticos_df_admin["Média Geral"], errors='coerce').mean()
                    st.metric("📈 Média Geral (Todos)", f"{media_geral_todos:.2f}" if pd.notna(media_geral_todos) else "N/A")
                with col_ig3:
                    if "GUT Média" in diagnosticos_df_admin.columns:
                        gut_media_todos = pd.to_numeric(diagnosticos_df_admin["GUT Média"], errors='coerce').mean()
                        st.metric("🔥 GUT Média (G*U*T)", f"{gut_media_todos:.2f}" if pd.notna(gut_media_todos) else "N/A")
                    else: st.metric("🔥 GUT Média (G*U*T)", "N/A")
                st.divider()

                st.markdown("#### Evolução Mensal dos Diagnósticos")
                df_diag_vis = diagnosticos_df_admin.copy()
                df_diag_vis["Data"] = pd.to_datetime(df_diag_vis["Data"], errors="coerce")
                df_diag_vis = df_diag_vis.dropna(subset=["Data"])
                if not df_diag_vis.empty:
                    df_diag_vis["Mês/Ano"] = df_diag_vis["Data"].dt.to_period("M").astype(str) 
                    df_diag_vis["Média Geral"] = pd.to_numeric(df_diag_vis["Média Geral"], errors='coerce')
                    df_diag_vis["GUT Média"] = pd.to_numeric(df_diag_vis.get("GUT Média"), errors='coerce') if "GUT Média" in df_diag_vis else pd.Series(dtype='float64', index=df_diag_vis.index)
                    
                    resumo_mensal = df_diag_vis.groupby("Mês/Ano").agg(
                        Diagnósticos_Realizados=("CNPJ", "count"), 
                        Média_Geral_Mensal=("Média Geral", "mean"),
                        GUT_Média_Mensal=("GUT Média", "mean")
                    ).reset_index().sort_values("Mês/Ano")
                    resumo_mensal["Mês/Ano_Display"] = pd.to_datetime(resumo_mensal["Mês/Ano"], errors='coerce').dt.strftime('%b/%y')
                    
                    if not resumo_mensal.empty:
                        fig_contagem = px.bar(resumo_mensal, x="Mês/Ano_Display", y="Diagnósticos_Realizados", title="Número de Diagnósticos por Mês", labels={'Diagnósticos_Realizados':'Total Diagnósticos', "Mês/Ano_Display": "Mês/Ano"})
                        st.plotly_chart(fig_contagem, use_container_width=True)
                        fig_medias = px.line(resumo_mensal, x="Mês/Ano_Display", y=["Média_Geral_Mensal", "GUT_Média_Mensal"], title="Médias Gerais e GUT por Mês", labels={'value':'Média', 'variable':'Indicador', "Mês/Ano_Display": "Mês/Ano"})
                        fig_medias.update_traces(mode='lines+markers')
                        st.plotly_chart(fig_medias, use_container_width=True)
                    else: st.info("Sem dados para gráficos de evolução mensal.")
                else: st.info("Sem diagnósticos com datas válidas para evolução mensal.")
                st.divider()
                
                st.markdown("#### Ranking das Empresas (Média Geral)")
                if "Empresa" in diagnosticos_df_admin.columns and "Média Geral" in diagnosticos_df_admin.columns:
                    diagnosticos_df_admin["Média Geral Num"] = pd.to_numeric(diagnosticos_df_admin["Média Geral"], errors='coerce')
                    ranking_df = diagnosticos_df_admin.dropna(subset=["Média Geral Num"])
                    if not ranking_df.empty:
                        ranking = ranking_df.groupby("Empresa")["Média Geral Num"].mean().sort_values(ascending=False).reset_index()
                        ranking.index = ranking.index + 1
                        st.dataframe(ranking.rename(columns={"Média Geral Num": "Média Geral (Ranking)"}))
                    else: st.info("Sem dados para ranking.")
                else: st.info("Colunas 'Empresa' ou 'Média Geral' ausentes para ranking.")
                st.divider()

                st.markdown("#### Todos os Diagnósticos Enviados")
                st.dataframe(diagnosticos_df_admin.sort_values(by="Data", ascending=False).reset_index(drop=True))
                csv_export_admin = diagnosticos_df_admin.to_csv(index=False).encode('utf-8') 
                st.download_button("⬇️ Exportar Todos (CSV)", csv_export_admin, file_name="diagnosticos_completos.csv", mime="text/csv", key="download_all_csv_admin_final_v2")
                st.divider()
                
                st.markdown("#### Detalhar, Comentar e Baixar PDF de Diagnóstico Específico")
                if "CNPJ" in diagnosticos_df_admin.columns:
                    empresas_unicas_adm = sorted(diagnosticos_df_admin["Empresa"].astype(str).unique().tolist())
                    empresa_selecionada_adm = st.selectbox("Selecione uma Empresa:", ["Selecione..."] + empresas_unicas_adm, key="admin_empresa_filter_detail_final_v2")

                    if empresa_selecionada_adm != "Selecione...":
                        diagnosticos_empresa_adm = diagnosticos_df_admin[diagnosticos_df_admin["Empresa"] == empresa_selecionada_adm].sort_values(by="Data", ascending=False)
                        if not diagnosticos_empresa_adm.empty:
                            datas_diagnosticos = ["Selecione Data..."] + diagnosticos_empresa_adm["Data"].tolist()
                            diagnostico_data_selecionada_adm = st.selectbox("Selecione a Data do Diagnóstico:", datas_diagnosticos, key="admin_data_diagnostico_select_final_v2")
                            
                            if diagnostico_data_selecionada_adm != "Selecione Data...":
                                diagnostico_selecionado_adm_row = diagnosticos_empresa_adm[diagnosticos_empresa_adm["Data"] == diagnostico_data_selecionada_adm].iloc[0]
                                
                                st.markdown(f"**Detalhes do Diagnóstico de {diagnostico_selecionado_adm_row['Data']}**")
                                # ... (Exibir Média Geral, GUT Média, etc. como antes) ...
                                
                                comentario_adm_atual_val = diagnostico_selecionado_adm_row.get("Comentarios_Admin", "")
                                if pd.isna(comentario_adm_atual_val): comentario_adm_atual_val = ""
                                novo_comentario_adm_val = st.text_area("Comentários do Consultor/Admin:", value=comentario_adm_atual_val, key=f"admin_comment_detail_final_v2_{diagnostico_selecionado_adm_row.name}")
                                if st.button("💾 Salvar Comentário", key=f"save_admin_comment_detail_final_v2_{diagnostico_selecionado_adm_row.name}"):
                                    df_diag_save_com_adm_det = pd.read_csv(arquivo_csv, encoding='utf-8')
                                    df_diag_save_com_adm_det.loc[diagnostico_selecionado_adm_row.name, "Comentarios_Admin"] = novo_comentario_adm_val
                                    df_diag_save_com_adm_det.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                    registrar_acao("ADMIN", "Comentário Admin", f"Admin comentou diag. de {diagnostico_selecionado_adm_row['Data']} para {empresa_selecionada_adm}")
                                    st.success("Comentário salvo!"); st.rerun()

                                if st.button("📄 Baixar PDF deste Diagnóstico", key=f"download_pdf_admin_final_v2_{diagnostico_selecionado_adm_row.name}"):
                                    try:
                                        perguntas_df_pdf_adm = pd.read_csv(perguntas_csv, encoding='utf-8')
                                        if "Categoria" not in perguntas_df_pdf_adm.columns: perguntas_df_pdf_adm["Categoria"] = "Geral"
                                    except: perguntas_df_pdf_adm = pd.DataFrame(columns=colunas_base_perguntas)

                                    respostas_para_pdf_adm = diagnostico_selecionado_adm_row.to_dict()
                                    medias_cat_pdf_adm = {}
                                    if not perguntas_df_pdf_adm.empty and "Categoria" in perguntas_df_pdf_adm.columns:
                                        cats_unicas_pdf_adm = perguntas_df_pdf_adm["Categoria"].unique()
                                        for cat_pdf_adm_calc in cats_unicas_pdf_adm:
                                            nome_col_media_cat_pdf = f"Media_Cat_{sanitize_column_name(cat_pdf_adm_calc)}"
                                            medias_cat_pdf_adm[cat_pdf_adm_calc] = diagnostico_selecionado_adm_row.get(nome_col_media_cat_pdf, 0.0)
                                    try:
                                        usuarios_df_pdf_adm = pd.read_csv(usuarios_csv, encoding='utf-8')
                                        usuario_data_pdf_adm = usuarios_df_pdf_adm[usuarios_df_pdf_adm["CNPJ"] == diagnostico_selecionado_adm_row["CNPJ"]].iloc[0].to_dict()
                                    except: usuario_data_pdf_adm = {"Empresa": diagnostico_selecionado_adm_row.get("Empresa", "N/D"), "CNPJ": diagnostico_selecionado_adm_row.get("CNPJ", "N/D")}

                                    pdf_path_admin_dl = gerar_pdf_diagnostico_completo(
                                        diagnostico_data=diagnostico_selecionado_adm_row.to_dict(), usuario_data=usuario_data_pdf_adm,
                                        perguntas_df_geracao=perguntas_df_pdf_adm, respostas_coletadas_geracao=respostas_para_pdf_adm, 
                                        medias_categorias_geracao=medias_cat_pdf_adm
                                    )
                                    if pdf_path_admin_dl:
                                        with open(pdf_path_admin_dl, "rb") as f_pdf_adm_dl:
                                            st.download_button(label="Download PDF Confirmado", data=f_pdf_adm_dl, 
                                                           file_name=f"diagnostico_{sanitize_column_name(empresa_selecionada_adm)}_{diagnostico_selecionado_adm_row['Data'].replace(':','-')}.pdf",
                                                           mime="application/pdf", key=f"confirm_dl_pdf_admin_final_v2_{diagnostico_selecionado_adm_row.name}")
                                        registrar_acao("ADMIN", "Download PDF Cliente", f"Admin baixou PDF de {diagnostico_selecionado_adm_row['Data']} para {empresa_selecionada_adm}")
                                    else: st.error("Falha ao gerar o PDF para download.")
                        else: st.info(f"Nenhum diagnóstico para a empresa {empresa_selecionada_adm}.")
                else: st.info("Coluna 'CNPJ' não encontrada para filtro.")
            else: 
                st.warning("AVISO: Nenhum dado de diagnóstico carregado. A 'Visão Geral' está limitada.")
            # st.write("--- DEBUG: FIM da seção 'Visão Geral e Diagnósticos' ---") # DEBUG Opcional

        elif menu_admin == "Histórico de Usuários":
            st.subheader("📜 Histórico de Ações dos Clientes")
            try:
                historico_df_adm = pd.read_csv(historico_csv, encoding='utf-8')
                if not historico_df_adm.empty:
                    st.dataframe(historico_df_adm.sort_values(by="Data", ascending=False))
                else: st.info("Nenhum histórico de ações encontrado.")
            except (FileNotFoundError, pd.errors.EmptyDataError): st.info("Arquivo de histórico não encontrado ou vazio.")
            except Exception as e_hist_adm: st.error(f"Erro ao carregar histórico: {e_hist_adm}")

        elif menu_admin == "Gerenciar Perguntas":
            st.subheader("📝 Gerenciar Perguntas do Diagnóstico")
            tabs_perg_admin = st.tabs(["📋 Perguntas Atuais", "➕ Adicionar Nova Pergunta"])
            with tabs_perg_admin[0]: 
                try:
                    perguntas_df_admin_edit = pd.read_csv(perguntas_csv, encoding='utf-8')
                    if "Categoria" not in perguntas_df_admin_edit.columns: perguntas_df_admin_edit["Categoria"] = "Geral"
                except (FileNotFoundError, pd.errors.EmptyDataError): 
                    st.info("Arquivo de perguntas não encontrado ou vazio.")
                    perguntas_df_admin_edit = pd.DataFrame(columns=colunas_base_perguntas)
                
                if perguntas_df_admin_edit.empty: st.info("Nenhuma pergunta cadastrada.")
                else:
                    for i_p_admin, row_p_admin in perguntas_df_admin_edit.iterrows():
                        cols_p_admin = st.columns([4, 2, 0.5, 0.5]) 
                        with cols_p_admin[0]:
                            nova_p_text_admin = st.text_input("Pergunta", value=str(row_p_admin["Pergunta"]), key=f"edit_p_txt_final_{i_p_admin}")
                        with cols_p_admin[1]:
                            nova_cat_text_admin = st.text_input("Categoria", value=str(row_p_admin.get("Categoria", "Geral")), key=f"edit_p_cat_final_{i_p_admin}")
                        with cols_p_admin[2]:
                            st.write("") # Espaçador para alinhar botão
                            if st.button("💾", key=f"salvar_p_adm_final_{i_p_admin}", help="Salvar pergunta e categoria"):
                                perguntas_df_admin_edit.loc[i_p_admin, "Pergunta"] = nova_p_text_admin # Atualiza o DataFrame localmente
                                perguntas_df_admin_edit.loc[i_p_admin, "Categoria"] = nova_cat_text_admin
                                perguntas_df_admin_edit.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                st.success(f"Pergunta {i_p_admin+1} atualizada."); st.rerun()
                        with cols_p_admin[3]:
                            st.write("") # Espaçador
                            if st.button("🗑️", key=f"deletar_p_adm_final_{i_p_admin}", help="Deletar pergunta"):
                                perguntas_df_admin_edit = perguntas_df_admin_edit.drop(i_p_admin).reset_index(drop=True)
                                perguntas_df_admin_edit.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                st.warning(f"Pergunta {i_p_admin+1} removida."); st.rerun()
                        st.divider()
            with tabs_perg_admin[1]: 
                with st.form("form_nova_pergunta_admin_final"):
                    st.subheader("➕ Adicionar Nova Pergunta")
                    nova_p_form_txt_admin = st.text_input("Texto da Pergunta", key="nova_p_input_admin_txt_final")
                    try:
                        perg_exist_df = pd.read_csv(perguntas_csv, encoding='utf-8')
                        cat_existentes = sorted(list(perg_exist_df['Categoria'].astype(str).unique())) if not perg_exist_df.empty and "Categoria" in perg_exist_df else []
                    except: cat_existentes = []
                    
                    cat_options = ["Nova Categoria"] + cat_existentes
                    cat_selecionada = st.selectbox("Selecionar Categoria Existente ou Criar Nova:", cat_options, key="cat_select_admin_new_q_final")
                    
                    if cat_selecionada == "Nova Categoria":
                        nova_cat_form_admin = st.text_input("Nome da Nova Categoria:", key="nova_cat_input_admin_new_q_final")
                    else:
                        nova_cat_form_admin = cat_selecionada

                    tipo_p_form_admin = st.selectbox("Tipo de Pergunta", 
                                                 ["Pontuação (0-10)", "Texto Aberto", "Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)", "[Matriz GUT]"], 
                                                 key="tipo_p_select_admin_new_q_final")
                    add_p_btn_admin = st.form_submit_button("Adicionar Pergunta")
                    if add_p_btn_admin:
                        if nova_p_form_txt_admin.strip() and nova_cat_form_admin.strip():
                            try: df_perg_add_admin = pd.read_csv(perguntas_csv, encoding='utf-8')
                            except (FileNotFoundError, pd.errors.EmptyDataError): df_perg_add_admin = pd.DataFrame(columns=colunas_base_perguntas)
                            if "Categoria" not in df_perg_add_admin.columns: df_perg_add_admin["Categoria"] = "Geral"
                            
                            p_completa_add_admin = f"{nova_p_form_txt_admin.strip()} {tipo_p_form_admin if tipo_p_form_admin == '[Matriz GUT]' else f'[{tipo_p_form_admin}]'}"
                            
                            nova_entrada_p_add_admin = pd.DataFrame([[p_completa_add_admin, nova_cat_form_admin.strip()]], columns=["Pergunta", "Categoria"])
                            df_perg_add_admin = pd.concat([df_perg_add_admin, nova_entrada_p_add_admin], ignore_index=True)
                            df_perg_add_admin.to_csv(perguntas_csv, index=False, encoding='utf-8')
                            st.success(f"Pergunta adicionada!"); st.rerun() 
                        else: st.warning("Texto da pergunta e categoria são obrigatórios.")

        elif menu_admin == "Gerenciar Clientes":
            st.subheader("👥 Gerenciar Clientes")
            try:
                usuarios_clientes_df = pd.read_csv(usuarios_csv, encoding='utf-8')
                for col_usr_check in colunas_base_usuarios: # Garante colunas
                    if col_usr_check not in usuarios_clientes_df.columns: usuarios_clientes_df[col_usr_check] = ""
            except (FileNotFoundError, pd.errors.EmptyDataError): 
                usuarios_clientes_df = pd.DataFrame(columns=colunas_base_usuarios)
            
            st.caption(f"Total de clientes: {len(usuarios_clientes_df)}")
            
            if not usuarios_clientes_df.empty:
                st.markdown("#### Editar Clientes Existentes")
                for idx_gc_final, row_gc_final in usuarios_clientes_df.iterrows():
                    with st.expander(f"{row_gc_final.get('Empresa','N/A')} (CNPJ: {row_gc_final['CNPJ']})"):
                        cols_edit_cli_final = st.columns(2) 
                        with cols_edit_cli_final[0]:
                            st.text_input("CNPJ (não editável)", value=row_gc_final['CNPJ'], disabled=True, key=f"cnpj_gc_final_{idx_gc_final}")
                            nova_senha_gc_final = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password", key=f"senha_gc_final_{idx_gc_final}")
                            nome_empresa_gc_final = st.text_input("Nome Empresa", value=row_gc_final.get('Empresa',""), key=f"empresa_gc_final_{idx_gc_final}")
                        with cols_edit_cli_final[1]:
                            nome_contato_gc_final = st.text_input("Nome Contato", value=row_gc_final.get("NomeContato", ""), key=f"nomec_gc_final_{idx_gc_final}")
                            telefone_gc_final = st.text_input("Telefone", value=row_gc_final.get("Telefone", ""), key=f"tel_gc_final_{idx_gc_final}")
                            logo_atual_path = find_client_logo_path(row_gc_final['CNPJ'])
                            if logo_atual_path: st.image(logo_atual_path, width=100, caption="Logo Atual")
                            uploaded_logo_gc = st.file_uploader("Alterar/Adicionar Logo", type=["png", "jpg", "jpeg"], key=f"logo_gc_final_{idx_gc_final}")

                        if st.button("💾 Salvar Alterações do Cliente", key=f"save_gc_final_{idx_gc_final}"):
                            if nova_senha_gc_final: usuarios_clientes_df.loc[idx_gc_final, "Senha"] = nova_senha_gc_final
                            usuarios_clientes_df.loc[idx_gc_final, "Empresa"] = nome_empresa_gc_final
                            usuarios_clientes_df.loc[idx_gc_final, "NomeContato"] = nome_contato_gc_final
                            usuarios_clientes_df.loc[idx_gc_final, "Telefone"] = telefone_gc_final
                            if uploaded_logo_gc is not None:
                                # Remover logo antiga se existir com outra extensão
                                for ext_old in ["png", "jpg", "jpeg"]:
                                    old_path = os.path.join(LOGOS_DIR, f"{str(row_gc_final['CNPJ'])}_logo.{ext_old}")
                                    if os.path.exists(old_path): os.remove(old_path)
                                # Salvar nova logo
                                file_extension = uploaded_logo_gc.name.split('.')[-1].lower()
                                logo_save_path_gc = os.path.join(LOGOS_DIR, f"{str(row_gc_final['CNPJ'])}_logo.{file_extension}")
                                with open(logo_save_path_gc, "wb") as f:
                                    f.write(uploaded_logo_gc.getbuffer())
                                st.success(f"Logo de {row_gc_final['Empresa']} atualizada!")
                            
                            usuarios_clientes_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
                            st.success(f"Dados de {row_gc_final['Empresa']} atualizados!"); st.rerun()
                st.divider()

            st.subheader("➕ Adicionar Novo Cliente")
            with st.form("form_novo_cliente_admin_final"):
                cols_add_cli_1 = st.columns(2)
                with cols_add_cli_1[0]:
                    novo_cnpj_gc_form_final = st.text_input("CNPJ do cliente *")
                    nova_senha_gc_form_final = st.text_input("Senha para o cliente *", type="password")
                    nova_empresa_gc_form_final = st.text_input("Nome da empresa cliente *")
                with cols_add_cli_1[1]:
                    novo_nomecontato_gc_form_final = st.text_input("Nome do Contato")
                    novo_telefone_gc_form_final = st.text_input("Telefone")
                    nova_logo_gc_form_final = st.file_uploader("Logo da Empresa", type=["png", "jpg", "jpeg"])
                
                adicionar_cliente_btn_gc_final = st.form_submit_button("Adicionar Cliente")

            if adicionar_cliente_btn_gc_final:
                if novo_cnpj_gc_form_final and nova_senha_gc_form_final and nova_empresa_gc_form_final:
                    if novo_cnpj_gc_form_final in usuarios_clientes_df["CNPJ"].astype(str).values:
                         st.error(f"CNPJ {novo_cnpj_gc_form_final} já cadastrado.")
                    else:
                        novo_usuario_data_gc_final = pd.DataFrame([[
                            novo_cnpj_gc_form_final, nova_senha_gc_form_final, nova_empresa_gc_form_final, 
                            novo_nomecontato_gc_form_final, novo_telefone_gc_form_final
                            ]], columns=colunas_base_usuarios)
                        usuarios_clientes_df = pd.concat([usuarios_clientes_df, novo_usuario_data_gc_final], ignore_index=True)
                        usuarios_clientes_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
                        
                        if nova_logo_gc_form_final is not None:
                            file_extension_new = nova_logo_gc_form_final.name.split('.')[-1].lower()
                            logo_save_path_new_gc = os.path.join(LOGOS_DIR, f"{str(novo_cnpj_gc_form_final)}_logo.{file_extension_new}")
                            with open(logo_save_path_new_gc, "wb") as f:
                                f.write(nova_logo_gc_form_final.getbuffer())
                        
                        st.success(f"Cliente '{nova_empresa_gc_form_final}' adicionado!"); st.rerun()
                else: st.warning("CNPJ, Senha e Nome da Empresa são obrigatórios.")
            
            st.markdown("---"); st.subheader("🚫 Gerenciar Bloqueios")
            try: bloqueados_df_adm_final = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
            except (FileNotFoundError, pd.errors.EmptyDataError): bloqueados_df_adm_final = pd.DataFrame(columns=["CNPJ"])
            st.write("CNPJs bloqueados:", bloqueados_df_adm_final["CNPJ"].tolist() if not bloqueados_df_adm_final.empty else "Nenhum")
            col_block_final, col_unblock_final = st.columns(2)
            with col_block_final:
                cnpj_para_bloquear_final = st.selectbox("Bloquear CNPJ:", [""] + usuarios_clientes_df["CNPJ"].astype(str).unique().tolist(), key="block_cnpj_final")
                if st.button("Bloquear Selecionado", key="btn_block_final") and cnpj_para_bloquear_final:
                    if cnpj_para_bloquear_final not in bloqueados_df_adm_final["CNPJ"].astype(str).values:
                        nova_block_final = pd.DataFrame([[cnpj_para_bloquear_final]], columns=["CNPJ"])
                        bloqueados_df_adm_final = pd.concat([bloqueados_df_adm_final, nova_block_final], ignore_index=True)
                        bloqueados_df_adm_final.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                        st.success(f"CNPJ {cnpj_para_bloquear_final} bloqueado."); st.rerun()
                    else: st.warning(f"CNPJ {cnpj_para_bloquear_final} já bloqueado.")
            with col_unblock_final:
                cnpj_para_desbloquear_final = st.selectbox("Desbloquear CNPJ:", [""] + bloqueados_df_adm_final["CNPJ"].astype(str).unique().tolist(), key="unblock_cnpj_final")
                if st.button("Desbloquear Selecionado", key="btn_unblock_final") and cnpj_para_desbloquear_final:
                    bloqueados_df_adm_final = bloqueados_df_adm_final[bloqueados_df_adm_final["CNPJ"].astype(str) != cnpj_para_desbloquear_final]
                    bloqueados_df_adm_final.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                    st.success(f"CNPJ {cnpj_para_desbloquear_final} desbloqueado."); st.rerun()
            
        elif menu_admin == "Gerenciar Administradores":
            st.subheader("👮 Gerenciar Administradores")
            try:
                admins_df_manage_final = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            except (FileNotFoundError, pd.errors.EmptyDataError): 
                admins_df_manage_final = pd.DataFrame(columns=["Usuario", "Senha"])
            
            st.dataframe(admins_df_manage_final[["Usuario"]]) 
            st.markdown("---"); st.subheader("➕ Adicionar Novo Admin")
            with st.form("form_novo_admin_manage_final"):
                novo_admin_user_manage_final = st.text_input("Usuário do Admin")
                novo_admin_pass_manage_final = st.text_input("Senha do Admin", type="password")
                adicionar_admin_btn_manage_final = st.form_submit_button("Adicionar Admin")
            if adicionar_admin_btn_manage_final:
                if novo_admin_user_manage_final and novo_admin_pass_manage_final:
                    if novo_admin_user_manage_final in admins_df_manage_final["Usuario"].values:
                        st.error(f"Usuário '{novo_admin_user_manage_final}' já existe.")
                    else:
                        novo_admin_data_manage_final = pd.DataFrame([[novo_admin_user_manage_final, novo_admin_pass_manage_final]], columns=["Usuario", "Senha"])
                        admins_df_manage_final = pd.concat([admins_df_manage_final, novo_admin_data_manage_final], ignore_index=True)
                        admins_df_manage_final.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                        st.success(f"Admin '{novo_admin_user_manage_final}' adicionado!"); st.rerun()
                else: st.warning("Preencha todos os campos.")
            st.markdown("---"); st.subheader("🗑️ Remover Admin")
            if not admins_df_manage_final.empty:
                admin_para_remover_manage_final = st.selectbox("Remover Admin:", options=[""] + admins_df_manage_final["Usuario"].tolist(), key="remove_admin_select_manage_final")
                if st.button("Remover Admin Selecionado", type="primary", key="btn_remove_admin_final") and admin_para_remover_manage_final:
                    if len(admins_df_manage_final) == 1 and admin_para_remover_manage_final == admins_df_manage_final["Usuario"].iloc[0]:
                        st.error("Não é possível remover o único administrador.")
                    else:
                        admins_df_manage_final = admins_df_manage_final[admins_df_manage_final["Usuario"] != admin_para_remover_manage_final]
                        admins_df_manage_final.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                        st.warning(f"Admin '{admin_para_remover_manage_final}' removido."); st.rerun()
            else: st.info("Nenhum administrador para remover.")

    except Exception as e_admin_area_final_full:
        st.error(f"Ocorreu um erro crítico na área administrativa: {e_admin_area_final_full}")
        st.exception(e_admin_area_final_full)

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()