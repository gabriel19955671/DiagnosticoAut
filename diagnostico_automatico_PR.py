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

# !!! st.set_page_config() DEVE SER O PRIMEIRO COMANDO STREAMLIT !!!
st.set_page_config(page_title="Portal de Diagnóstico", layout="wide") 

# CSS
st.markdown("""
<style>
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
LOGOS_DIR = "client_logos" 

# --- Inicialização do Session State ---
if "admin_logado" not in st.session_state: st.session_state.admin_logado = False
if "cliente_logado" not in st.session_state: st.session_state.cliente_logado = False
if "diagnostico_enviado" not in st.session_state: st.session_state.diagnostico_enviado = False
if "inicio_sessao_cliente" not in st.session_state: st.session_state.inicio_sessao_cliente = None
if "cliente_page" not in st.session_state: st.session_state.cliente_page = "Painel Principal"
if "cnpj" not in st.session_state: st.session_state.cnpj = None
if "user" not in st.session_state: st.session_state.user = None

# --- Funções Utilitárias ---
def sanitize_column_name(name):
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s) 
    return s

def pdf_safe_text_output(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def find_client_logo_path(cnpj):
    if not cnpj: return None
    base_name = str(cnpj).replace('/', '').replace('.', '').replace('-', '') 
    for ext in ["png", "jpg", "jpeg"]:
        path = os.path.join(LOGOS_DIR, f"{base_name}_logo.{ext}")
        if os.path.exists(path):
            return path
    return None

# --- Criação e Verificação de Arquivos e Pastas ---
if not os.path.exists(LOGOS_DIR):
    try:
        os.makedirs(LOGOS_DIR)
    except OSError as e_logo_dir_create_final:
        st.error(f"Não foi possível criar o diretório de logos '{LOGOS_DIR}': {e_logo_dir_create_final}")

colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
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
    except Exception as e_init_csv_final:
        st.error(f"Erro ao inicializar/verificar {filepath}: {e_init_csv_final}. O app pode não funcionar corretamente.")
        st.exception(e_init_csv_final) 
        # Não usamos st.stop() aqui para permitir que outros erros sejam vistos,
        # mas a chamada principal da inicialização terá um st.stop() se falhar.

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios)
    inicializar_csv(perguntas_csv, colunas_base_perguntas, is_perguntas_file=True)
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
except Exception as e_init_all_final_clean:
    st.error(f"Falha crítica na inicialização de arquivos CSV base: {e_init_all_final_clean}")
    st.exception(e_init_all_final_clean)
    st.markdown("Verifique permissões de arquivo e a integridade dos CSVs. Delete-os para recriação se necessário.")
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
        
        logo_path_pdf = find_client_logo_path(cnpj_pdf)
        if logo_path_pdf:
            try: 
                current_y_pdf = pdf.get_y()
                max_logo_height = 20 
                pdf.image(logo_path_pdf, x=10, y=current_y_pdf, h=max_logo_height) 
                pdf.set_y(current_y_pdf + max_logo_height + 5) 
            except RuntimeError as e_fpdf_logo_runtime: 
                st.warning(f"Não foi possível adicionar a logo ao PDF (formato/corrupção?): {e_fpdf_logo_runtime}")
            except Exception: pass 

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

        for titulo_pdf, campo_dado_pdf in [("Resumo do Diagnóstico (Cliente):", "Diagnóstico"), 
                                  ("Análise/Observações do Cliente:", "Análise do Cliente"),
                                  ("Comentários do Consultor:", "Comentarios_Admin")]:
            valor_campo_pdf = diagnostico_data.get(campo_dado_pdf, "")
            if valor_campo_pdf and not pd.isna(valor_campo_pdf): 
                pdf.set_font("Arial", 'B', 12); pdf.multi_cell(0, 7, pdf_safe_text_output(titulo_pdf))
                pdf.set_font("Arial", size=10); pdf.multi_cell(0, 7, pdf_safe_text_output(str(valor_campo_pdf))); pdf.ln(3)
            
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
            gut_cards_pdf_sorted = sorted(gut_cards_pdf, key=lambda x_pdf_s_clean: (int(x_pdf_s_clean["Prazo"].split(" ")[0]), -x_pdf_s_clean["Score"])) 
            for card_item_pdf_clean in gut_cards_pdf_sorted: 
                 pdf.multi_cell(0, 6, pdf_safe_text_output(f"Prazo: {card_item_pdf_clean['Prazo']} - Tarefa: {card_item_pdf_clean['Tarefa']} (Score GUT: {card_item_pdf_clean['Score']})"))
        else: pdf.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile_pdf_final_gen_clean:
            pdf_path_final_pdf_gen_clean = tmpfile_pdf_final_gen_clean.name
            pdf.output(pdf_path_final_pdf_gen_clean)
        return pdf_path_final_pdf_gen_clean
    except Exception as e_pdf_main_clean:
        st.error(f"Erro crítico ao gerar PDF: {e_pdf_main_clean}")
        st.exception(e_pdf_main_clean); return None

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_clean_final")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_clean_final"): 
        usuario_admin_login = st.text_input("Usuário", key="admin_user_login_clean_final") 
        senha_admin_login = st.text_input("Senha", type="password", key="admin_pass_login_clean_final")
        entrar_admin_login = st.form_submit_button("Entrar")
    if entrar_admin_login:
        try:
            df_admin_login_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            admin_encontrado = df_admin_login_creds[
                (df_admin_login_creds["Usuario"] == usuario_admin_login) & 
                (df_admin_login_creds["Senha"] == senha_admin_login)
            ]
            if not admin_encontrado.empty:
                st.session_state.admin_logado = True
                st.success("Login de administrador bem-sucedido!")
                st.session_state.trigger_admin_rerun = True; st.rerun() 
            else: st.error("Usuário ou senha inválidos.")
        except FileNotFoundError: st.error(f"Arquivo {admin_credenciais_csv} não encontrado.")
        except pd.errors.EmptyDataError: st.error(f"Arquivo {admin_credenciais_csv} está vazio.")
        except Exception as e_login_admin_clean_final: st.error(f"Erro no login: {e_login_admin_clean_final}"); st.exception(e_login_admin_clean_final)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_clean_final"): 
        cnpj_cli_login = st.text_input("CNPJ", key="cli_cnpj_login_clean_final") 
        senha_cli_login = st.text_input("Senha", type="password", key="cli_pass_login_clean_final") 
        acessar_cli_login = st.form_submit_button("Entrar")
    if acessar_cli_login:
        try:
            if not os.path.exists(usuarios_csv): st.error(f"Arquivo {usuarios_csv} não encontrado."); st.stop()
            usuarios_login_df = pd.read_csv(usuarios_csv, encoding='utf-8')
            if not os.path.exists(usuarios_bloqueados_csv): st.error(f"Arquivo {usuarios_bloqueados_csv} não encontrado."); st.stop()
            bloqueados_login_df = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
            
            if cnpj_cli_login in bloqueados_login_df["CNPJ"].astype(str).values: 
                st.error("CNPJ bloqueado."); st.stop()
            user_match_li = usuarios_login_df[(usuarios_login_df["CNPJ"].astype(str) == str(cnpj_cli_login)) & (usuarios_login_df["Senha"] == senha_cli_login)]
            if user_match_li.empty: st.error("CNPJ ou senha inválidos."); st.stop()
            
            st.session_state.cliente_logado = True; st.session_state.cnpj = str(cnpj_cli_login) 
            st.session_state.user = user_match_li.iloc[0].to_dict() 
            st.session_state.inicio_sessao_cliente = time.time()
            registrar_acao(st.session_state.cnpj, "Login", "Usuário realizou login.")
            st.session_state.cliente_page = "Painel Principal"
            st.success("Login realizado com sucesso!"); st.session_state.trigger_cliente_rerun = True; st.rerun() 
        except FileNotFoundError as e_login_cli_fnf_clean_final: st.error(f"Arquivo não encontrado: {e_login_cli_fnf_clean_final.filename}.")
        except pd.errors.EmptyDataError as e_login_cli_empty_clean_final: st.error(f"Arquivo de usuários ou bloqueados está vazio: {e_login_cli_empty_clean_final}")
        except Exception as e_login_cli_clean_final: st.error(f"Erro no login do cliente: {e_login_cli_clean_final}"); st.exception(e_login_cli_clean_final)
    st.markdown('</div>', unsafe_allow_html=True); st.stop() 


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    try:
        st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
        
        with st.sidebar.expander("Meu Perfil", expanded=False):
            logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
            if logo_cliente_path:
                st.image(logo_cliente_path, width=100)
            st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
            st.write(f"**CNPJ:** {st.session_state.cnpj}")
            st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
            st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")

        DIAGNOSTICO_FORM_ID_KEY_USER = f"form_id_diagnostico_cliente_{st.session_state.cnpj}"

        st.session_state.cliente_page = st.sidebar.radio(
            "Menu Cliente", ["Painel Principal", "Novo Diagnóstico"],
            index=["Painel Principal", "Novo Diagnóstico"].index(st.session_state.cliente_page),
            key="cliente_menu_radio_clean_final_v2"
        )
        if st.sidebar.button("⬅️ Sair do Portal Cliente"):
            keys_to_del_cli_logout = ['cliente_logado', 'cnpj', 'user', 'inicio_sessao_cliente', 
                                           'diagnostico_enviado', 'cliente_page', DIAGNOSTICO_FORM_ID_KEY_USER]
            temp_resp_key_logout = f"temp_respostas_{st.session_state.get(DIAGNOSTICO_FORM_ID_KEY_USER,'')}"
            if temp_resp_key_logout in st.session_state:
                keys_to_del_cli_logout.append(temp_resp_key_logout)
            for key_cd_lo in keys_to_del_cli_logout:
                if key_cd_lo in st.session_state: del st.session_state[key_cd_lo]
            st.rerun()

        if st.session_state.cliente_page == "Painel Principal":
            st.subheader("📌 Meu Painel de Diagnósticos")
            # ... (Restante da lógica do Painel Principal do Cliente, como na versão anterior) ...

        elif st.session_state.cliente_page == "Novo Diagnóstico":
            st.subheader("📋 Formulário de Novo Diagnóstico")
            # ... (Restante da lógica do Novo Diagnóstico do Cliente, como na versão anterior) ...

    except Exception as e_cliente_area_clean_final:
        st.error(f"Ocorreu um erro na área do cliente: {e_cliente_area_clean_final}")
        st.exception(e_cliente_area_clean_final) 

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
        key="admin_menu_selectbox_clean_final_v2" 
    )
    st.header(f"🔑 Painel Admin: {menu_admin}")

    try: 
        if menu_admin == "Visão Geral e Diagnósticos":
            st.subheader("📊 Visão Geral dos Diagnósticos")
            # st.write("DEBUG: Entrando na Visão Geral do Admin") # MANTENHA ESTE SE O PROBLEMA PERSISTIR AQUI

            diagnosticos_df_admin = None 
            admin_data_loaded = False
            try:
                if not os.path.exists(arquivo_csv) or os.path.getsize(arquivo_csv) == 0:
                    st.warning(f"Arquivo de diagnósticos ({arquivo_csv}) não encontrado ou vazio. Nenhum dado para exibir.")
                else:
                    diagnosticos_df_admin = pd.read_csv(arquivo_csv, encoding='utf-8')
                    if diagnosticos_df_admin.empty:
                        st.info("Arquivo de diagnósticos lido, mas não contém dados.")
                    else:
                        admin_data_loaded = True
            except Exception as e_load_diag_admin_vg_clean:
                st.error(f"ERRO AO CARREGAR DIAGNÓSTICOS (Visão Geral): {e_load_diag_admin_vg_clean}")
                st.exception(e_load_diag_admin_vg_clean)
            
            if admin_data_loaded and diagnosticos_df_admin is not None and not diagnosticos_df_admin.empty:
                # st.write("DEBUG: Dados da Visão Geral do Admin carregados. Renderizando...") # MANTENHA ESTE SE O PROBLEMA PERSISTIR
                # --- Filtro de Cliente/Empresa para Visão Geral ---
                empresas_disponiveis_vg = ["Todos os Clientes"] + sorted(diagnosticos_df_admin["Empresa"].astype(str).unique().tolist())
                empresa_selecionada_vg = st.selectbox(
                    "Filtrar Visão Geral por Empresa:", 
                    empresas_disponiveis_vg, 
                    key="admin_visao_geral_filtro_empresa_clean"
                )

                df_filtrado_vg = diagnosticos_df_admin.copy()
                if empresa_selecionada_vg != "Todos os Clientes":
                    df_filtrado_vg = df_filtrado_vg[df_filtrado_vg["Empresa"] == empresa_selecionada_vg]
                
                if df_filtrado_vg.empty:
                    st.info(f"Nenhum diagnóstico encontrado para '{empresa_selecionada_vg}'.")
                else:
                    st.markdown(f"#### Indicadores Gerais para: {empresa_selecionada_vg}")
                    # ... (Resto da lógica da Visão Geral, Rankings, Gráficos, Detalhar, etc., como na última versão funcional)
                    # Vou colar aqui a estrutura completa desta seção para garantir.

                    # Indicadores Gerais
                    col_ig1_vg, col_ig2_vg, col_ig3_vg = st.columns(3)
                    with col_ig1_vg: st.metric("📦 Diagnósticos Selecionados", len(df_filtrado_vg))
                    with col_ig2_vg:
                        media_geral_todos_vg = pd.to_numeric(df_filtrado_vg["Média Geral"], errors='coerce').mean()
                        st.metric("📈 Média Geral", f"{media_geral_todos_vg:.2f}" if pd.notna(media_geral_todos_vg) else "N/A")
                    with col_ig3_vg:
                        if "GUT Média" in df_filtrado_vg.columns:
                            gut_media_todos_vg = pd.to_numeric(df_filtrado_vg["GUT Média"], errors='coerce').mean()
                            st.metric("🔥 GUT Média (G*U*T)", f"{gut_media_todos_vg:.2f}" if pd.notna(gut_media_todos_vg) else "N/A")
                        else: st.metric("🔥 GUT Média (G*U*T)", "N/A")
                    st.divider()

                    # Evolução Mensal
                    st.markdown(f"#### Evolução Mensal ({empresa_selecionada_vg})")
                    df_diag_vis_vg = df_filtrado_vg.copy()
                    df_diag_vis_vg["Data"] = pd.to_datetime(df_diag_vis_vg["Data"], errors="coerce")
                    df_diag_vis_vg = df_diag_vis_vg.dropna(subset=["Data"])
                    if not df_diag_vis_vg.empty:
                        df_diag_vis_vg["Mês/Ano"] = df_diag_vis_vg["Data"].dt.to_period("M").astype(str) 
                        df_diag_vis_vg["Média Geral"] = pd.to_numeric(df_diag_vis_vg["Média Geral"], errors='coerce')
                        df_diag_vis_vg["GUT Média"] = pd.to_numeric(df_diag_vis_vg.get("GUT Média"), errors='coerce') if "GUT Média" in df_diag_vis_vg else pd.Series(dtype='float64', index=df_diag_vis_vg.index)
                        
                        resumo_mensal_vg = df_diag_vis_vg.groupby("Mês/Ano").agg(
                            Diagnósticos_Realizados=("CNPJ", "count"), 
                            Média_Geral_Mensal=("Média Geral", "mean"),
                            GUT_Média_Mensal=("GUT Média", "mean")
                        ).reset_index().sort_values("Mês/Ano")
                        resumo_mensal_vg["Mês/Ano_Display"] = pd.to_datetime(resumo_mensal_vg["Mês/Ano"], errors='coerce').dt.strftime('%b/%y')
                        
                        if not resumo_mensal_vg.empty:
                            fig_contagem_vg = px.bar(resumo_mensal_vg, x="Mês/Ano_Display", y="Diagnósticos_Realizados", title="Diagnósticos por Mês", height=350, labels={'Diagnósticos_Realizados':'Total', "Mês/Ano_Display": "Mês"})
                            st.plotly_chart(fig_contagem_vg, use_container_width=True)
                            fig_medias_vg = px.line(resumo_mensal_vg, x="Mês/Ano_Display", y=["Média_Geral_Mensal", "GUT_Média_Mensal"], title="Médias Gerais e GUT por Mês", height=350, labels={'value':'Média', 'variable':'Indicador', "Mês/Ano_Display": "Mês"})
                            fig_medias_vg.update_traces(mode='lines+markers')
                            st.plotly_chart(fig_medias_vg, use_container_width=True)
                        else: st.info("Sem dados para gráficos de evolução mensal.")
                    else: st.info("Sem diagnósticos com datas válidas para evolução.")
                    st.divider()
                
                    # Rankings
                    if empresa_selecionada_vg == "Todos os Clientes":
                        st.markdown("#### Ranking das Empresas (Média Geral)")
                        if "Empresa" in df_filtrado_vg.columns and "Média Geral" in df_filtrado_vg.columns:
                            df_filtrado_vg["Média Geral Num"] = pd.to_numeric(df_filtrado_vg["Média Geral"], errors='coerce')
                            ranking_df_vg = df_filtrado_vg.dropna(subset=["Média Geral Num"])
                            if not ranking_df_vg.empty:
                                ranking_vg = ranking_df_vg.groupby("Empresa")["Média Geral Num"].mean().sort_values(ascending=False).reset_index()
                                ranking_vg.index = ranking_vg.index + 1
                                st.dataframe(ranking_vg.rename(columns={"Média Geral Num": "Média Geral (Ranking)"}))
                            else: st.info("Sem dados para ranking de Média Geral.")
                        st.divider()

                        st.markdown("#### Ranking das Empresas (Média GUT G*U*T)")
                        if "Empresa" in df_filtrado_vg.columns and "GUT Média" in df_filtrado_vg.columns:
                            df_filtrado_vg["GUT Média Num"] = pd.to_numeric(df_filtrado_vg["GUT Média"], errors='coerce')
                            ranking_gut_df_vg = df_filtrado_vg.dropna(subset=["GUT Média Num"])
                            if not ranking_gut_df_vg.empty and not ranking_gut_df_vg[ranking_gut_df_vg["GUT Média Num"] > 0].empty : 
                                ranking_gut_vg = ranking_gut_df_vg[ranking_gut_df_vg["GUT Média Num"] > 0].groupby("Empresa")["GUT Média Num"].mean().sort_values(ascending=False).reset_index()
                                ranking_gut_vg.index = ranking_gut_vg.index + 1
                                st.dataframe(ranking_gut_vg.rename(columns={"GUT Média Num": "Média Score GUT (Ranking)"}))
                            else: st.info("Sem dados ou scores GUT válidos (>0) para ranking GUT.")
                        st.divider()

                    # Tabela de Diagnósticos
                    st.markdown(f"#### Diagnósticos Enviados ({empresa_selecionada_vg})")
                    st.dataframe(df_filtrado_vg.sort_values(by="Data", ascending=False).reset_index(drop=True))
                    if empresa_selecionada_vg == "Todos os Clientes":
                        csv_export_admin_vg = df_filtrado_vg.to_csv(index=False).encode('utf-8') 
                        st.download_button("⬇️ Exportar Todos os Diagnósticos (CSV)", csv_export_admin_vg, file_name=f"diagnosticos_completos.csv", mime="text/csv", key="download_todos_csv_admin_clean")
                    st.divider()
                    
                    # Detalhar, Comentar e Baixar PDF
                    st.markdown("#### Detalhar, Comentar e Baixar PDF de Diagnóstico Específico")
                    empresas_detalhe_vg = sorted(df_filtrado_vg["Empresa"].astype(str).unique().tolist())
                    if not empresas_detalhe_vg:
                        st.info("Nenhuma empresa na seleção atual para detalhar.")
                    else:
                        default_empresa_detalhe_idx_vg = 0
                        if empresa_selecionada_vg != "Todos os Clientes" and empresa_selecionada_vg in empresas_detalhe_vg:
                            default_empresa_detalhe_idx_vg = empresas_detalhe_vg.index(empresa_selecionada_vg)

                        empresa_selecionada_detalhe_vg = st.selectbox("Selecione uma Empresa para Detalhar:", empresas_detalhe_vg, index=default_empresa_detalhe_idx_vg, key="admin_empresa_filter_detail_clean")
                        
                        diagnosticos_empresa_detalhe_vg = df_filtrado_vg[df_filtrado_vg["Empresa"] == empresa_selecionada_detalhe_vg].sort_values(by="Data", ascending=False)
                        if not diagnosticos_empresa_detalhe_vg.empty:
                            datas_diagnosticos_detalhe_vg = ["Selecione Data..."] + diagnosticos_empresa_detalhe_vg["Data"].tolist()
                            diagnostico_data_selecionada_detalhe_vg = st.selectbox("Selecione a Data do Diagnóstico:", datas_diagnosticos_detalhe_vg, key="admin_data_diagnostico_select_clean")
                            if diagnostico_data_selecionada_detalhe_vg != "Selecione Data...":
                                diagnostico_selecionado_adm_row_vg = diagnosticos_empresa_detalhe_vg[diagnosticos_empresa_detalhe_vg["Data"] == diagnostico_data_selecionada_detalhe_vg].iloc[0]
                                
                                st.markdown(f"**Detalhes do Diagnóstico de {diagnostico_selecionado_adm_row_vg['Data']}**")
                                st.write(f"**Média Geral:** {diagnostico_selecionado_adm_row_vg.get('Média Geral', 'N/A')} | **GUT Média (G*U*T):** {diagnostico_selecionado_adm_row_vg.get('GUT Média', 'N/A')}")
                                
                                comentario_adm_atual_val_vg = diagnostico_selecionado_adm_row_vg.get("Comentarios_Admin", "")
                                if pd.isna(comentario_adm_atual_val_vg): comentario_adm_atual_val_vg = ""
                                novo_comentario_adm_val_vg = st.text_area("Comentários do Consultor/Admin:", value=comentario_adm_atual_val_vg, key=f"admin_comment_detail_clean_{diagnostico_selecionado_adm_row_vg.name}")
                                if st.button("💾 Salvar Comentário", key=f"save_admin_comment_detail_clean_{diagnostico_selecionado_adm_row_vg.name}"):
                                    df_diag_save_com_adm_det_vg = pd.read_csv(arquivo_csv, encoding='utf-8')
                                    df_diag_save_com_adm_det_vg.loc[diagnostico_selecionado_adm_row_vg.name, "Comentarios_Admin"] = novo_comentario_adm_val_vg
                                    df_diag_save_com_adm_det_vg.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                    registrar_acao("ADMIN", "Comentário Admin", f"Admin comentou diag. de {diagnostico_selecionado_adm_row_vg['Data']} para {empresa_selecionada_detalhe_vg}")
                                    st.success("Comentário salvo!"); st.rerun()

                                if st.button("📄 Baixar PDF deste Diagnóstico", key=f"download_pdf_admin_clean_{diagnostico_selecionado_adm_row_vg.name}"):
                                    try:
                                        perguntas_df_pdf_adm_vg = pd.read_csv(perguntas_csv, encoding='utf-8')
                                        if "Categoria" not in perguntas_df_pdf_adm_vg.columns: perguntas_df_pdf_adm_vg["Categoria"] = "Geral"
                                    except: perguntas_df_pdf_adm_vg = pd.DataFrame(columns=colunas_base_perguntas)

                                    respostas_para_pdf_adm_vg = diagnostico_selecionado_adm_row_vg.to_dict()
                                    medias_cat_pdf_adm_vg = {}
                                    if not perguntas_df_pdf_adm_vg.empty and "Categoria" in perguntas_df_pdf_adm_vg.columns:
                                        cats_unicas_pdf_adm_vg = perguntas_df_pdf_adm_vg["Categoria"].unique()
                                        for cat_pdf_adm_calc_vg in cats_unicas_pdf_adm_vg:
                                            nome_col_media_cat_pdf_vg = f"Media_Cat_{sanitize_column_name(cat_pdf_adm_calc_vg)}"
                                            medias_cat_pdf_adm_vg[cat_pdf_adm_calc_vg] = diagnostico_selecionado_adm_row_vg.get(nome_col_media_cat_pdf_vg, 0.0)
                                    try:
                                        usuarios_df_pdf_adm_vg = pd.read_csv(usuarios_csv, encoding='utf-8')
                                        usuario_data_pdf_adm_vg = usuarios_df_pdf_adm_vg[usuarios_df_pdf_adm_vg["CNPJ"] == diagnostico_selecionado_adm_row_vg["CNPJ"]].iloc[0].to_dict()
                                    except: usuario_data_pdf_adm_vg = {"Empresa": diagnostico_selecionado_adm_row_vg.get("Empresa", "N/D"), 
                                                                     "CNPJ": diagnostico_selecionado_adm_row_vg.get("CNPJ", "N/D"),
                                                                     "NomeContato": diagnostico_selecionado_adm_row_vg.get("NomeContato","N/D"),
                                                                     "Telefone": diagnostico_selecionado_adm_row_vg.get("Telefone","N/D")}

                                    pdf_path_admin_dl_vg = gerar_pdf_diagnostico_completo(
                                        diagnostico_data=diagnostico_selecionado_adm_row_vg.to_dict(), usuario_data=usuario_data_pdf_adm_vg,
                                        perguntas_df_geracao=perguntas_df_pdf_adm_vg, respostas_coletadas_geracao=respostas_para_pdf_adm_vg, 
                                        medias_categorias_geracao=medias_cat_pdf_adm_vg
                                    )
                                    if pdf_path_admin_dl_vg:
                                        with open(pdf_path_admin_dl_vg, "rb") as f_pdf_adm_dl_vg:
                                            st.download_button(label="Download PDF Confirmado", data=f_pdf_adm_dl_vg, 
                                                           file_name=f"diagnostico_{sanitize_column_name(empresa_selecionada_detalhe_vg)}_{diagnostico_selecionado_adm_row_vg['Data'].replace(':','-')}.pdf",
                                                           mime="application/pdf", key=f"confirm_dl_pdf_admin_clean_{diagnostico_selecionado_adm_row_vg.name}")
                                        registrar_acao("ADMIN", "Download PDF Cliente", f"Admin baixou PDF de {diagnostico_selecionado_adm_row_vg['Data']} para {empresa_selecionada_detalhe_vg}")
                                    else: st.error("Falha ao gerar o PDF para download.")
                        else: st.info(f"Nenhum diagnóstico para a empresa {empresa_selecionada_detalhe_vg}.")
            else: 
                st.warning("AVISO: Nenhum dado de diagnóstico carregado. A seção 'Visão Geral' está limitada.")
        
        elif menu_admin == "Histórico de Usuários":
            st.subheader("📜 Histórico de Ações dos Clientes")
            try:
                historico_df = pd.read_csv(historico_csv, encoding='utf-8')
                if not historico_df.empty:
                    st.dataframe(historico_df.sort_values(by="Data", ascending=False))
                else: st.info("Nenhum histórico de ações encontrado.")
            except (FileNotFoundError, pd.errors.EmptyDataError): st.info("Arquivo de histórico não encontrado ou vazio.")
            except Exception as e_hist_clean: st.error(f"Erro ao carregar histórico: {e_hist_clean}")

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
                            nova_p_text_admin = st.text_input("Pergunta", value=str(row_p_admin["Pergunta"]), key=f"edit_p_txt_clean_{i_p_admin}")
                        with cols_p_admin[1]:
                            nova_cat_text_admin = st.text_input("Categoria", value=str(row_p_admin.get("Categoria", "Geral")), key=f"edit_p_cat_clean_{i_p_admin}")
                        with cols_p_admin[2]:
                            st.write("") 
                            if st.button("💾", key=f"salvar_p_adm_clean_{i_p_admin}", help="Salvar"):
                                perguntas_df_admin_edit.loc[i_p_admin, "Pergunta"] = nova_p_text_admin 
                                perguntas_df_admin_edit.loc[i_p_admin, "Categoria"] = nova_cat_text_admin
                                perguntas_df_admin_edit.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                st.success(f"Pergunta {i_p_admin+1} atualizada."); st.rerun()
                        with cols_p_admin[3]:
                            st.write("") 
                            if st.button("🗑️", key=f"deletar_p_adm_clean_{i_p_admin}", help="Deletar"):
                                perguntas_df_admin_edit = perguntas_df_admin_edit.drop(i_p_admin).reset_index(drop=True)
                                perguntas_df_admin_edit.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                st.warning(f"Pergunta {i_p_admin+1} removida."); st.rerun()
                        st.divider()
            with tabs_perg_admin[1]: 
                with st.form("form_nova_pergunta_admin_clean"):
                    st.subheader("➕ Adicionar Nova Pergunta")
                    nova_p_form_txt_admin = st.text_input("Texto da Pergunta", key="nova_p_input_admin_txt_clean")
                    try:
                        perg_exist_df = pd.read_csv(perguntas_csv, encoding='utf-8')
                        cat_existentes = sorted(list(perg_exist_df['Categoria'].astype(str).unique())) if not perg_exist_df.empty and "Categoria" in perg_exist_df else []
                    except: cat_existentes = []
                    
                    cat_options = ["Nova Categoria"] + cat_existentes
                    cat_selecionada = st.selectbox("Categoria:", cat_options, key="cat_select_admin_new_q_clean")
                    
                    if cat_selecionada == "Nova Categoria":
                        nova_cat_form_admin = st.text_input("Nome da Nova Categoria:", key="nova_cat_input_admin_new_q_clean")
                    else: nova_cat_form_admin = cat_selecionada

                    tipo_p_form_admin = st.selectbox("Tipo de Pergunta", 
                                                 ["Pontuação (0-10)", "Texto Aberto", "Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)", "[Matriz GUT]"], 
                                                 key="tipo_p_select_admin_new_q_clean")
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
                for col_usr_check in colunas_base_usuarios: 
                    if col_usr_check not in usuarios_clientes_df.columns: usuarios_clientes_df[col_usr_check] = ""
            except (FileNotFoundError, pd.errors.EmptyDataError): 
                usuarios_clientes_df = pd.DataFrame(columns=colunas_base_usuarios)
            
            st.caption(f"Total de clientes: {len(usuarios_clientes_df)}")
            
            if not usuarios_clientes_df.empty:
                st.markdown("#### Editar Clientes Existentes")
                for idx_gc, row_gc in usuarios_clientes_df.iterrows():
                    with st.expander(f"{row_gc.get('Empresa','N/A')} (CNPJ: {row_gc['CNPJ']})"):
                        cols_edit_cli = st.columns(2) 
                        with cols_edit_cli[0]:
                            st.text_input("CNPJ (não editável)", value=row_gc['CNPJ'], disabled=True, key=f"cnpj_gc_clean_{idx_gc}")
                            nova_senha_gc = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password", key=f"senha_gc_clean_{idx_gc}")
                            nome_empresa_gc = st.text_input("Nome Empresa", value=row_gc.get('Empresa',""), key=f"empresa_gc_clean_{idx_gc}")
                        with cols_edit_cli[1]:
                            nome_contato_gc = st.text_input("Nome Contato", value=row_gc.get("NomeContato", ""), key=f"nomec_gc_clean_{idx_gc}")
                            telefone_gc = st.text_input("Telefone", value=row_gc.get("Telefone", ""), key=f"tel_gc_clean_{idx_gc}")
                            logo_atual_path = find_client_logo_path(row_gc['CNPJ'])
                            if logo_atual_path: st.image(logo_atual_path, width=100, caption="Logo Atual")
                            uploaded_logo_gc = st.file_uploader("Alterar/Adicionar Logo", type=["png", "jpg", "jpeg"], key=f"logo_gc_clean_{idx_gc}")

                        if st.button("💾 Salvar Alterações do Cliente", key=f"save_gc_clean_{idx_gc}"):
                            if nova_senha_gc: usuarios_clientes_df.loc[idx_gc, "Senha"] = nova_senha_gc
                            usuarios_clientes_df.loc[idx_gc, "Empresa"] = nome_empresa_gc
                            usuarios_clientes_df.loc[idx_gc, "NomeContato"] = nome_contato_gc
                            usuarios_clientes_df.loc[idx_gc, "Telefone"] = telefone_gc
                            if uploaded_logo_gc is not None:
                                if not os.path.exists(LOGOS_DIR): os.makedirs(LOGOS_DIR)
                                clean_cnpj_gc_save = sanitize_column_name(str(row_gc['CNPJ'])) 
                                for ext_old in ["png", "jpg", "jpeg"]: 
                                    old_path = os.path.join(LOGOS_DIR, f"{clean_cnpj_gc_save}_logo.{ext_old}")
                                    if os.path.exists(old_path): os.remove(old_path)
                                file_extension = uploaded_logo_gc.name.split('.')[-1].lower()
                                logo_save_path_gc = os.path.join(LOGOS_DIR, f"{clean_cnpj_gc_save}_logo.{file_extension}")
                                try:
                                    with open(logo_save_path_gc, "wb") as f: f.write(uploaded_logo_gc.getbuffer())
                                    st.success(f"Logo de {row_gc['Empresa']} atualizada!")
                                except Exception as e_save_logo: st.error(f"Erro ao salvar logo: {e_save_logo}")
                            
                            usuarios_clientes_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
                            st.success(f"Dados de {row_gc['Empresa']} atualizados!"); st.rerun()
                st.divider()

            st.subheader("➕ Adicionar Novo Cliente")
            with st.form("form_novo_cliente_admin_clean"):
                cols_add_cli_1 = st.columns(2)
                with cols_add_cli_1[0]:
                    novo_cnpj_gc_form = st.text_input("CNPJ do cliente *")
                    nova_senha_gc_form = st.text_input("Senha para o cliente *", type="password")
                    nova_empresa_gc_form = st.text_input("Nome da empresa cliente *")
                with cols_add_cli_1[1]:
                    novo_nomecontato_gc_form = st.text_input("Nome do Contato")
                    novo_telefone_gc_form = st.text_input("Telefone")
                    nova_logo_gc_form = st.file_uploader("Logo da Empresa", type=["png", "jpg", "jpeg"])
                
                adicionar_cliente_btn_gc = st.form_submit_button("Adicionar Cliente")

            if adicionar_cliente_btn_gc:
                if novo_cnpj_gc_form and nova_senha_gc_form and nova_empresa_gc_form:
                    if novo_cnpj_gc_form in usuarios_clientes_df["CNPJ"].astype(str).values:
                         st.error(f"CNPJ {novo_cnpj_gc_form} já cadastrado.")
                    else:
                        novo_usuario_data_gc = pd.DataFrame([[
                            novo_cnpj_gc_form, nova_senha_gc_form, nova_empresa_gc_form, 
                            novo_nomecontato_gc_form, novo_telefone_gc_form
                            ]], columns=colunas_base_usuarios)
                        usuarios_clientes_df = pd.concat([usuarios_clientes_df, novo_usuario_data_gc], ignore_index=True)
                        usuarios_clientes_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
                        
                        if nova_logo_gc_form is not None:
                            if not os.path.exists(LOGOS_DIR): os.makedirs(LOGOS_DIR)
                            clean_cnpj_new_gc_save = sanitize_column_name(str(novo_cnpj_gc_form))
                            file_extension_new = nova_logo_gc_form.name.split('.')[-1].lower()
                            logo_save_path_new_gc = os.path.join(LOGOS_DIR, f"{clean_cnpj_new_gc_save}_logo.{file_extension_new}")
                            try:
                                with open(logo_save_path_new_gc, "wb") as f: f.write(nova_logo_gc_form.getbuffer())
                            except Exception as e_save_new_logo: st.error(f"Erro ao salvar nova logo: {e_save_new_logo}")
                        
                        st.success(f"Cliente '{nova_empresa_gc_form}' adicionado!"); st.rerun()
                else: st.warning("CNPJ, Senha e Nome da Empresa são obrigatórios.")
            
            st.markdown("---"); st.subheader("🚫 Gerenciar Bloqueios")
            try: bloqueados_df_adm = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
            except (FileNotFoundError, pd.errors.EmptyDataError): bloqueados_df_adm = pd.DataFrame(columns=["CNPJ"])
            st.write("CNPJs bloqueados:", bloqueados_df_adm["CNPJ"].tolist() if not bloqueados_df_adm.empty else "Nenhum")
            col_block, col_unblock = st.columns(2)
            with col_block:
                cnpj_para_bloquear = st.selectbox("Bloquear CNPJ:", [""] + usuarios_clientes_df["CNPJ"].astype(str).unique().tolist(), key="block_cnpj_clean")
                if st.button("Bloquear Selecionado", key="btn_block_clean") and cnpj_para_bloquear:
                    if cnpj_para_bloquear not in bloqueados_df_adm["CNPJ"].astype(str).values:
                        nova_block = pd.DataFrame([[cnpj_para_bloquear]], columns=["CNPJ"])
                        bloqueados_df_adm = pd.concat([bloqueados_df_adm, nova_block], ignore_index=True)
                        bloqueados_df_adm.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                        st.success(f"CNPJ {cnpj_para_bloquear} bloqueado."); st.rerun()
                    else: st.warning(f"CNPJ {cnpj_para_bloquear} já bloqueado.")
            with col_unblock:
                cnpj_para_desbloquear = st.selectbox("Desbloquear CNPJ:", [""] + bloqueados_df_adm["CNPJ"].astype(str).unique().tolist(), key="unblock_cnpj_clean")
                if st.button("Desbloquear Selecionado", key="btn_unblock_clean") and cnpj_para_desbloquear:
                    bloqueados_df_adm = bloqueados_df_adm[bloqueados_df_adm["CNPJ"].astype(str) != cnpj_para_desbloquear]
                    bloqueados_df_adm.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                    st.success(f"CNPJ {cnpj_para_desbloquear} desbloqueado."); st.rerun()
            
        elif menu_admin == "Gerenciar Administradores":
            st.subheader("👮 Gerenciar Administradores")
            try:
                admins_df_manage = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            except (FileNotFoundError, pd.errors.EmptyDataError): 
                admins_df_manage = pd.DataFrame(columns=["Usuario", "Senha"])
            
            st.dataframe(admins_df_manage[["Usuario"]]) 
            st.markdown("---"); st.subheader("➕ Adicionar Novo Admin")
            with st.form("form_novo_admin_manage_clean"):
                novo_admin_user_manage = st.text_input("Usuário do Admin")
                novo_admin_pass_manage = st.text_input("Senha do Admin", type="password")
                adicionar_admin_btn_manage = st.form_submit_button("Adicionar Admin")
            if adicionar_admin_btn_manage:
                if novo_admin_user_manage and novo_admin_pass_manage:
                    if novo_admin_user_manage in admins_df_manage["Usuario"].values:
                        st.error(f"Usuário '{novo_admin_user_manage}' já existe.")
                    else:
                        novo_admin_data_manage = pd.DataFrame([[novo_admin_user_manage, novo_admin_pass_manage]], columns=["Usuario", "Senha"])
                        admins_df_manage = pd.concat([admins_df_manage, novo_admin_data_manage], ignore_index=True)
                        admins_df_manage.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                        st.success(f"Admin '{novo_admin_user_manage}' adicionado!"); st.rerun()
                else: st.warning("Preencha todos os campos.")
            st.markdown("---"); st.subheader("🗑️ Remover Admin")
            if not admins_df_manage.empty:
                admin_para_remover_manage = st.selectbox("Remover Admin:", options=[""] + admins_df_manage["Usuario"].tolist(), key="remove_admin_select_manage_clean")
                if st.button("Remover Admin Selecionado", type="primary", key="btn_remove_admin_clean") and admin_para_remover_manage:
                    if len(admins_df_manage) == 1 and admin_para_remover_manage == admins_df_manage["Usuario"].iloc[0]:
                        st.error("Não é possível remover o único administrador.")
                    else:
                        admins_df_manage = admins_df_manage[admins_df_manage["Usuario"] != admin_para_remover_manage]
                        admins_df_manage.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                        st.warning(f"Admin '{admin_para_remover_manage}' removido."); st.rerun()
            else: st.info("Nenhum administrador para remover.")

    except Exception as e_admin_area_clean_final:
        st.error(f"Ocorreu um erro crítico na área administrativa: {e_admin_area_clean_final}")
        st.exception(e_admin_area_clean_final)

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()