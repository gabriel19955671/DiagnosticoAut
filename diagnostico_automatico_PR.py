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

def find_client_logo_path(cnpj_find): # Renomeado parâmetro
    if not cnpj_find: return None
    base_name = str(cnpj_find).replace('/', '').replace('.', '').replace('-', '') 
    for ext_find in ["png", "jpg", "jpeg"]: # Renomeado variável de loop
        path_find = os.path.join(LOGOS_DIR, f"{base_name}_logo.{ext_find}") # Renomeado variável
        if os.path.exists(path_find):
            return path_find
    return None

# --- Criação e Verificação de Arquivos e Pastas ---
if not os.path.exists(LOGOS_DIR):
    try:
        os.makedirs(LOGOS_DIR)
    except OSError as e_logo_dir_final: # Renomeado
        st.error(f"Não foi possível criar o diretório de logos '{LOGOS_DIR}': {e_logo_dir_final}")

colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone"]
colunas_base_perguntas = ["Pergunta", "Categoria"]

def inicializar_csv(filepath, columns, is_perguntas_file_init=False): # Renomeado parâmetro
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_create = pd.DataFrame(columns=columns) # Renomeado variável
            df_create.to_csv(filepath, index=False, encoding='utf-8')
        else:
            df_check = pd.read_csv(filepath, encoding='utf-8') # Renomeado variável
            missing_cols_check_init = [col_init for col_init in columns if col_init not in df_check.columns] # Renomeado
            made_changes_init = False # Renomeado
            if missing_cols_check_init:
                for col_m_init in missing_cols_check_init: # Renomeado
                    if is_perguntas_file_init and col_m_init == "Categoria": df_check[col_m_init] = "Geral"
                    else: df_check[col_m_init] = pd.NA 
                made_changes_init = True
            if is_perguntas_file_init and "Categoria" not in df_check.columns:
                df_check["Categoria"] = "Geral"; made_changes_init = True
            if made_changes_init:
                df_check.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError: 
        pd.DataFrame(columns=columns).to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e_init_csv_inner: # Renomeado
        st.error(f"Erro DENTRO de inicializar_csv para {filepath}: {e_init_csv_inner}")
        st.exception(e_init_csv_inner) 
        raise 

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios)
    inicializar_csv(perguntas_csv, colunas_base_perguntas, is_perguntas_file_init=True)
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
except Exception as e_init_all_final_v2: # Renomeado
    st.error(f"Falha crítica na inicialização de arquivos CSV base: {e_init_all_final_v2}")
    st.exception(e_init_all_final_v2)
    st.markdown("Verifique permissões de arquivo e a integridade dos CSVs. Delete-os para recriação se necessário.")
    st.stop()


def registrar_acao(cnpj_reg, acao_reg, descricao_reg): # Renomeado parâmetros
    try:
        historico_df_reg = pd.read_csv(historico_csv, encoding='utf-8') 
    except (FileNotFoundError, pd.errors.EmptyDataError): 
        historico_df_reg = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    nova_data_reg = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj_reg, "Ação": acao_reg, "Descrição": descricao_reg }
    historico_df_reg = pd.concat([historico_df_reg, pd.DataFrame([nova_data_reg])], ignore_index=True)
    historico_df_reg.to_csv(historico_csv, index=False, encoding='utf-8')


def gerar_pdf_diagnostico_completo(diagnostico_data_pdf, usuario_data_pdf, perguntas_df_pdf, respostas_coletadas_pdf, medias_categorias_pdf): # Renomeado parâmetros
    try:
        pdf_gen = FPDF() # Renomeado variável
        pdf_gen.add_page()
        empresa_nome_pdf_g = usuario_data_pdf.get("Empresa", "N/D") 
        cnpj_pdf_g = usuario_data_pdf.get("CNPJ", "N/D")
        nome_contato_pdf_g = usuario_data_pdf.get("NomeContato", "")
        telefone_pdf_g = usuario_data_pdf.get("Telefone", "")
        
        logo_path_pdf_g = find_client_logo_path(cnpj_pdf_g)
        if logo_path_pdf_g:
            try: 
                current_y_pdf_g = pdf_gen.get_y()
                max_logo_height_g = 20 
                pdf_gen.image(logo_path_pdf_g, x=10, y=current_y_pdf_g, h=max_logo_height_g) 
                pdf_gen.set_y(current_y_pdf_g + max_logo_height_g + 5) 
            except RuntimeError as e_fpdf_logo_rt_g: 
                st.warning(f"Não foi possível adicionar a logo ao PDF: {e_fpdf_logo_rt_g}")
            except Exception: pass 

        pdf_gen.set_font("Arial", 'B', 16)
        pdf_gen.cell(0, 10, pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome_pdf_g}"), 0, 1, 'C')
        pdf_gen.ln(5)

        pdf_gen.set_font("Arial", size=10)
        pdf_gen.multi_cell(0, 7, pdf_safe_text_output(f"Data do Diagnóstico: {diagnostico_data_pdf.get('Data','N/D')}"))
        pdf_gen.multi_cell(0, 7, pdf_safe_text_output(f"Empresa: {empresa_nome_pdf_g} (CNPJ: {cnpj_pdf_g})"))
        if nome_contato_pdf_g: pdf_gen.multi_cell(0, 7, pdf_safe_text_output(f"Contato: {nome_contato_pdf_g}"))
        if telefone_pdf_g: pdf_gen.multi_cell(0, 7, pdf_safe_text_output(f"Telefone: {telefone_pdf_g}"))
        pdf_gen.ln(3)

        pdf_gen.multi_cell(0, 7, pdf_safe_text_output(f"Média Geral (Numérica): {diagnostico_data_pdf.get('Média Geral','N/A')}"))
        pdf_gen.multi_cell(0, 7, pdf_safe_text_output(f"Média Scores GUT (G*U*T): {diagnostico_data_pdf.get('GUT Média','N/A')}"))
        pdf_gen.ln(3)

        if medias_categorias_pdf:
            pdf_gen.set_font("Arial", 'B', 11); pdf_gen.multi_cell(0, 7, pdf_safe_text_output("Médias por Categoria (Perguntas de Pontuação):"))
            pdf_gen.set_font("Arial", size=10)
            for cat_pdf_g_mc, media_cat_pdf_g_mc in medias_categorias_pdf.items(): # Renomeado
                pdf_gen.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat_pdf_g_mc}: {media_cat_pdf_g_mc}"))
            pdf_gen.ln(5)

        for titulo_pdf_g, campo_dado_pdf_g in [("Resumo do Diagnóstico (Cliente):", "Diagnóstico"), 
                                  ("Análise/Observações do Cliente:", "Análise do Cliente"),
                                  ("Comentários do Consultor:", "Comentarios_Admin")]:
            valor_campo_pdf_g = diagnostico_data_pdf.get(campo_dado_pdf_g, "")
            if valor_campo_pdf_g and not pd.isna(valor_campo_pdf_g): 
                pdf_gen.set_font("Arial", 'B', 12); pdf_gen.multi_cell(0, 7, pdf_safe_text_output(titulo_pdf_g))
                pdf_gen.set_font("Arial", size=10); pdf_gen.multi_cell(0, 7, pdf_safe_text_output(str(valor_campo_pdf_g))); pdf_gen.ln(3)
            
        pdf_gen.set_font("Arial", 'B', 12); pdf_gen.multi_cell(0, 10, pdf_safe_text_output("Respostas Detalhadas por Categoria:"))
        categorias_unicas_pdf_g = []
        if perguntas_df_pdf is not None and "Categoria" in perguntas_df_pdf.columns: 
            categorias_unicas_pdf_g = perguntas_df_pdf["Categoria"].unique()
        
        for categoria_pdf_det_g in categorias_unicas_pdf_g:
            pdf_gen.set_font("Arial", 'B', 10); pdf_gen.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria_pdf_det_g}"))
            pdf_gen.set_font("Arial", size=9)
            perguntas_cat_pdf_det_g = perguntas_df_pdf[perguntas_df_pdf["Categoria"] == categoria_pdf_det_g]
            for _, p_row_pdf_det_g in perguntas_cat_pdf_det_g.iterrows():
                txt_p_pdf_det_g = p_row_pdf_det_g["Pergunta"]
                resp_p_pdf_det_g = respostas_coletadas_pdf.get(txt_p_pdf_det_g) 
                if resp_p_pdf_det_g is None: 
                    resp_p_pdf_det_g = diagnostico_data_pdf.get(txt_p_pdf_det_g, "N/R")

                if isinstance(txt_p_pdf_det_g, str) and "[Matriz GUT]" in txt_p_pdf_det_g: 
                    g_pdf_v, u_pdf_v, t_pdf_v = 0,0,0 # Renomeado
                    score_gut_item_pdf_v = 0
                    if isinstance(resp_p_pdf_det_g, dict): 
                        g_pdf_v,u_pdf_v,t_pdf_v = resp_p_pdf_det_g.get("G",0), resp_p_pdf_det_g.get("U",0), resp_p_pdf_det_g.get("T",0)
                    elif isinstance(resp_p_pdf_det_g, str): 
                        try: 
                            gut_data_pdf_v = json.loads(resp_p_pdf_det_g.replace("'", "\""))
                            g_pdf_v,u_pdf_v,t_pdf_v = gut_data_pdf_v.get("G",0), gut_data_pdf_v.get("U",0), gut_data_pdf_v.get("T",0)
                        except: pass 
                    score_gut_item_pdf_v = g_pdf_v*u_pdf_v*t_pdf_v
                    pdf_gen.multi_cell(0,6,pdf_safe_text_output(f"  - {txt_p_pdf_det_g.replace(' [Matriz GUT]','')}: G={g_pdf_v}, U={u_pdf_v}, T={t_pdf_v} (Score: {score_gut_item_pdf_v})"))
                elif isinstance(resp_p_pdf_det_g, (int, float, str)): 
                    pdf_gen.multi_cell(0, 6, pdf_safe_text_output(f"  - {txt_p_pdf_det_g}: {resp_p_pdf_det_g}"))
            pdf_gen.ln(2)
        pdf_gen.ln(3)
        
        pdf_gen.add_page(); pdf_gen.set_font("Arial", 'B', 12)
        pdf_gen.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf_gen.ln(5)
        pdf_gen.set_font("Arial", size=10)
        gut_cards_pdf_g_list = [] 
        for pergunta_pdf_k_g_item, resp_pdf_k_val_g_item in respostas_coletadas_pdf.items(): # Renomeado
            if isinstance(pergunta_pdf_k_g_item, str) and "[Matriz GUT]" in pergunta_pdf_k_g_item:
                g_k_g_item, u_k_g_item, t_k_g_item = 0,0,0 # Renomeado
                if isinstance(resp_pdf_k_val_g_item, dict):
                    g_k_g_item, u_k_g_item, t_k_g_item = resp_pdf_k_val_g_item.get("G",0), resp_pdf_k_val_g_item.get("U",0), resp_pdf_k_val_g_item.get("T",0)
                elif isinstance(resp_pdf_k_val_g_item, str): 
                    try: 
                        gut_data_k_g_item = json.loads(resp_pdf_k_val_g_item.replace("'", "\""))
                        g_k_g_item,u_k_g_item,t_k_g_item = gut_data_k_g_item.get("G",0), gut_data_k_g_item.get("U",0), gut_data_k_g_item.get("T",0)
                    except: pass
                
                score_gut_total_k_pdf_g_item = g_k_g_item * u_k_g_item * t_k_g_item
                prazo_k_pdf_g_item = "N/A"
                if score_gut_total_k_pdf_g_item >= 75: prazo_k_pdf_g_item = "15 dias"
                elif score_gut_total_k_pdf_g_item >= 40: prazo_k_pdf_g_item = "30 dias"
                elif score_gut_total_k_pdf_g_item >= 20: prazo_k_pdf_g_item = "45 dias"
                elif score_gut_total_k_pdf_g_item > 0: prazo_k_pdf_g_item = "60 dias"
                else: continue
                if prazo_k_pdf_g_item != "N/A":
                    gut_cards_pdf_g_list.append({"Tarefa": pergunta_pdf_k_g_item.replace(" [Matriz GUT]", ""),"Prazo": prazo_k_pdf_g_item, "Score": score_gut_total_k_pdf_g_item})
        if gut_cards_pdf_g_list:
            gut_cards_pdf_g_sorted = sorted(gut_cards_pdf_g_list, key=lambda x_g_pdf: (int(x_g_pdf["Prazo"].split(" ")[0]), -x_g_pdf["Score"])) 
            for card_item_pdf_g_final in gut_cards_pdf_g_sorted: 
                 pdf_gen.multi_cell(0, 6, pdf_safe_text_output(f"Prazo: {card_item_pdf_g_final['Prazo']} - Tarefa: {card_item_pdf_g_final['Tarefa']} (Score GUT: {card_item_pdf_g_final['Score']})"))
        else: pdf_gen.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile_pdf_gerado_final:
            pdf_path_gerado_final = tmpfile_pdf_gerado_final.name
            pdf_gen.output(pdf_path_gerado_final)
        return pdf_path_gerado_final
    except Exception as e_pdf_main_gerar_final:
        st.error(f"Erro crítico ao gerar PDF: {e_pdf_main_gerar_final}")
        st.exception(e_pdf_main_gerar_final); return None

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_vfinal")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_vfinal"): 
        usuario_admin_login = st.text_input("Usuário", key="admin_user_login_vfinal") 
        senha_admin_login = st.text_input("Senha", type="password", key="admin_pass_login_vfinal")
        entrar_admin_login = st.form_submit_button("Entrar")
    if entrar_admin_login:
        try:
            df_admin_login_creds = pd.read_csv(admin_credenciais_csv, encoding='utf-8')
            admin_encontrado = df_admin_login_creds[(df_admin_login_creds["Usuario"] == usuario_admin_login) & (df_admin_login_creds["Senha"] == senha_admin_login)]
            if not admin_encontrado.empty:
                st.session_state.admin_logado = True; st.success("Login de administrador bem-sucedido!")
                st.session_state.trigger_admin_rerun = True; st.rerun() 
            else: st.error("Usuário ou senha inválidos.")
        except FileNotFoundError: st.error(f"Arquivo {admin_credenciais_csv} não encontrado.")
        except pd.errors.EmptyDataError: st.error(f"Arquivo {admin_credenciais_csv} está vazio.")
        except Exception as e_login_admin_vfinal: st.error(f"Erro no login: {e_login_admin_vfinal}"); st.exception(e_login_admin_vfinal)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_vfinal"): 
        cnpj_cli_login = st.text_input("CNPJ", key="cli_cnpj_login_vfinal") 
        senha_cli_login = st.text_input("Senha", type="password", key="cli_pass_login_vfinal") 
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
        except FileNotFoundError as e_login_cli_fnf_vfinal: st.error(f"Arquivo não encontrado: {e_login_cli_fnf_vfinal.filename}.")
        except pd.errors.EmptyDataError as e_login_cli_empty_vfinal: st.error(f"Arquivo de usuários ou bloqueados está vazio: {e_login_cli_empty_vfinal}")
        except Exception as e_login_cli_vfinal: st.error(f"Erro no login do cliente: {e_login_cli_vfinal}"); st.exception(e_login_cli_vfinal)
    st.markdown('</div>', unsafe_allow_html=True); st.stop() 


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    try:
        st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
        with st.sidebar.expander("Meu Perfil", expanded=False):
            logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
            if logo_cliente_path:
                try: st.image(logo_cliente_path, width=100)
                except Exception as e_logo_display: st.caption(f"Erro ao exibir logo: {e_logo_display}")
            st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
            st.write(f"**CNPJ:** {st.session_state.cnpj}")
            st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
            st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")

        DIAGNOSTICO_FORM_ID_KEY_USER = f"form_id_diagnostico_cliente_{st.session_state.cnpj}"

        st.session_state.cliente_page = st.sidebar.radio(
            "Menu Cliente", ["Painel Principal", "Novo Diagnóstico"],
            index=["Painel Principal", "Novo Diagnóstico"].index(st.session_state.cliente_page),
            key="cliente_menu_radio_vfinal_v2"
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
            with st.expander("📖 Instruções e Informações", expanded=True):
                st.markdown("- Visualize seus diagnósticos anteriores e sua evolução.")
                st.markdown("- Acompanhe seu plano de ação no Kanban.")
                st.markdown("- Para um novo diagnóstico, selecione 'Novo Diagnóstico' no menu ao lado.")
            
            if st.session_state.get("diagnostico_enviado", False):
                st.success("🎯 Último diagnóstico enviado com sucesso!"); st.session_state.diagnostico_enviado = False
            
            st.subheader("📁 Diagnósticos Anteriores")
            df_cliente_view_pp = pd.DataFrame() # Inicializa
            try:
                df_antigos_cli_pp = pd.read_csv(arquivo_csv, encoding='utf-8')
                if not df_antigos_cli_pp.empty:
                    df_cliente_view_pp = df_antigos_cli_pp[df_antigos_cli_pp["CNPJ"].astype(str) == st.session_state.cnpj]
            except (FileNotFoundError, pd.errors.EmptyDataError): 
                st.info("Arquivo de diagnósticos não encontrado ou vazio. Envie um diagnóstico para começar.")
            except Exception as e_read_diag_cli:
                st.error(f"Erro ao ler diagnósticos do cliente: {e_read_diag_cli}")
            
            if df_cliente_view_pp.empty: 
                st.info("Nenhum diagnóstico anterior encontrado para você. Selecione 'Novo Diagnóstico' no menu para começar.")
            else:
                df_cliente_view_pp = df_cliente_view_pp.sort_values(by="Data", ascending=False)
                for idx_cv_pp, row_cv_pp in df_cliente_view_pp.iterrows():
                    with st.expander(f"📅 {row_cv_pp['Data']} - {row_cv_pp['Empresa']}"):
                        # ... (Resto da lógica de exibição do histórico, como na versão anterior)
                        pass # Código completo já fornecido anteriormente
                
                st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
                # ... (Resto da lógica do Kanban, como na versão anterior)
                pass
                
                st.subheader("📈 Comparativo de Evolução")
                # ... (Resto da lógica dos Gráficos de Evolução e Comparação, como na versão anterior)
                pass

        elif st.session_state.cliente_page == "Novo Diagnóstico":
            st.subheader("📋 Formulário de Novo Diagnóstico")
            
            DIAGNOSTICO_FORM_ID_KEY_USER = f"form_id_diagnostico_cliente_{st.session_state.cnpj}" 
            if DIAGNOSTICO_FORM_ID_KEY_USER not in st.session_state:
                st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER] = datetime.now().strftime("%Y%m%d%H%M%S%f")
            form_id_sufixo_nd = st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER]

            temp_respostas_key_nd = f"temp_respostas_{form_id_sufixo_nd}"
            if temp_respostas_key_nd not in st.session_state:
                st.session_state[temp_respostas_key_nd] = {}
            
            respostas_form_coletadas_nd = st.session_state[temp_respostas_key_nd]
            
            perguntas_df_diag = pd.DataFrame() # Inicializa
            try:
                perguntas_df_diag = pd.read_csv(perguntas_csv, encoding='utf-8')
                if "Categoria" not in perguntas_df_diag.columns: 
                    perguntas_df_diag["Categoria"] = "Geral"
            except (FileNotFoundError, pd.errors.EmptyDataError): 
                st.error(f"Arquivo de perguntas ({perguntas_csv}) não encontrado ou vazio. Não é possível carregar o formulário."); st.stop()
            except Exception as e_read_perg:
                st.error(f"Erro ao ler arquivo de perguntas: {e_read_perg}"); st.stop()

            if perguntas_df_diag.empty: 
                st.warning("Nenhuma pergunta cadastrada no sistema. Contate o administrador."); st.stop()
            
            # ... (Resto da lógica do formulário de Novo Diagnóstico, como na versão anterior)
            #    Incluindo o st.form, loops de categoria/pergunta, GUT G*U*T, salvamento, e geração de PDF.
            pass

    except Exception as e_cliente_area_vfinal:
        st.error(f"Ocorreu um erro inesperado na área do cliente: {e_cliente_area_vfinal}")
        st.exception(e_cliente_area_vfinal) 


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
        key="admin_menu_selectbox_vfinal_v2" 
    )
    st.header(f"🔑 Painel Admin: {menu_admin}")

    try: 
        if menu_admin == "Visão Geral e Diagnósticos":
            st.subheader("📊 Visão Geral dos Diagnósticos")
            # st.write("DEBUG: Entrando na Visão Geral do Admin") # DEBUG opcional
            diagnosticos_df_admin = pd.DataFrame() # Inicializa para evitar NameError se a leitura falhar
            admin_data_loaded = False
            try:
                if not os.path.exists(arquivo_csv) or os.path.getsize(arquivo_csv) == 0:
                    st.warning(f"Arquivo de diagnósticos ({arquivo_csv}) não encontrado ou está vazio. Nenhum dado para exibir.")
                else:
                    diagnosticos_df_admin = pd.read_csv(arquivo_csv, encoding='utf-8')
                    if diagnosticos_df_admin.empty:
                        st.info("Arquivo de diagnósticos lido, mas não contém nenhuma linha de dados.")
                    else:
                        admin_data_loaded = True
            except Exception as e_load_diag_admin_vg_vfinal:
                st.error(f"ERRO AO CARREGAR DIAGNÓSTICOS (Visão Geral): {e_load_diag_admin_vg_vfinal}")
                st.exception(e_load_diag_admin_vg_vfinal)
            
            if admin_data_loaded and not diagnosticos_df_admin.empty:
                # st.write("DEBUG: Dados da Visão Geral do Admin carregados. Renderizando...") # DEBUG opcional
                empresas_disponiveis_vg = ["Todos os Clientes"] + sorted(diagnosticos_df_admin["Empresa"].astype(str).unique().tolist())
                empresa_selecionada_vg = st.selectbox(
                    "Filtrar Visão Geral por Empresa:", 
                    empresas_disponiveis_vg, 
                    key="admin_visao_geral_filtro_empresa_vfinal"
                )
                df_filtrado_vg = diagnosticos_df_admin.copy()
                if empresa_selecionada_vg != "Todos os Clientes":
                    df_filtrado_vg = df_filtrado_vg[df_filtrado_vg["Empresa"] == empresa_selecionada_vg]
                
                if df_filtrado_vg.empty:
                    st.info(f"Nenhum diagnóstico encontrado para '{empresa_selecionada_vg}'.")
                else:
                    # ... (Resto da lógica da Visão Geral, Rankings, Gráficos, Detalhar, etc., como na última versão completa) ...
                    pass # Substituir este 'pass' pelo código completo da seção "Visão Geral e Diagnósticos"
            else: 
                st.warning("AVISO: Nenhum dado de diagnóstico carregado ou o arquivo está vazio. A 'Visão Geral' não pode ser totalmente exibida.")
        
        elif menu_admin == "Histórico de Usuários":
            st.subheader("📜 Histórico de Ações dos Clientes")
            # ... (Código completo da seção Histórico de Usuários da versão anterior)
            pass
        elif menu_admin == "Gerenciar Perguntas":
            st.subheader("📝 Gerenciar Perguntas do Diagnóstico")
            # ... (Código completo da seção Gerenciar Perguntas da versão anterior)
            pass
        elif menu_admin == "Gerenciar Clientes":
            st.subheader("👥 Gerenciar Clientes")
            # ... (Código completo da seção Gerenciar Clientes da versão anterior)
            pass
        elif menu_admin == "Gerenciar Administradores":
            st.subheader("👮 Gerenciar Administradores")
            # ... (Código completo da seção Gerenciar Administradores da versão anterior)
            pass
    except Exception as e_admin_area_vfinal_full:
        st.error(f"Ocorreu um erro crítico na área administrativa: {e_admin_area_vfinal_full}")
        st.exception(e_admin_area_vfinal_full)

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()