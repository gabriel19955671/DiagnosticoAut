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

def find_client_logo_path(cnpj_find_logo_arg): 
    if not cnpj_find_logo_arg: return None
    base_name = str(cnpj_find_logo_arg).replace('/', '').replace('.', '').replace('-', '') 
    for ext_logo_arg in ["png", "jpg", "jpeg"]: 
        path_logo_arg = os.path.join(LOGOS_DIR, f"{base_name}_logo.{ext_logo_arg}") 
        if os.path.exists(path_logo_arg):
            return path_logo_arg
    return None

# --- Criação e Verificação de Arquivos e Pastas ---
if not os.path.exists(LOGOS_DIR):
    try:
        os.makedirs(LOGOS_DIR)
    except OSError as e_logo_dir_final_v3: 
        st.error(f"Não foi possível criar o diretório de logos '{LOGOS_DIR}': {e_logo_dir_final_v3}")

colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone"]
colunas_base_perguntas = ["Pergunta", "Categoria"]

def inicializar_csv(filepath, columns, is_perguntas_file=False):
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init_final_v2 = pd.DataFrame(columns=columns)
            df_init_final_v2.to_csv(filepath, index=False, encoding='utf-8')
        else:
            df_init_final_v2 = pd.read_csv(filepath, encoding='utf-8')
            missing_cols_init_final_v2 = [col_final_v2 for col_final_v2 in columns if col_final_v2 not in df_init_final_v2.columns]
            made_changes_init_final_v2 = False
            if missing_cols_init_final_v2:
                for col_m_final_v2 in missing_cols_init_final_v2:
                    if is_perguntas_file and col_m_final_v2 == "Categoria": df_init_final_v2[col_m_final_v2] = "Geral"
                    else: df_init_final_v2[col_m_final_v2] = pd.NA 
                made_changes_init_final_v2 = True
            if is_perguntas_file and "Categoria" not in df_init_final_v2.columns:
                df_init_final_v2["Categoria"] = "Geral"; made_changes_init_final_v2 = True
            if made_changes_init_final_v2:
                df_init_final_v2.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError: 
        pd.DataFrame(columns=columns).to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e_init_csv_final_v3:
        st.error(f"Erro ao inicializar/verificar {filepath}: {e_init_csv_final_v3}. O app pode não funcionar corretamente.")
        st.exception(e_init_csv_final_v3) 
        raise 

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios)
    inicializar_csv(perguntas_csv, colunas_base_perguntas, is_perguntas_file=True)
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
except Exception as e_init_all_final_v4:
    st.error(f"Falha crítica na inicialização de arquivos CSV base: {e_init_all_final_v4}")
    st.exception(e_init_all_final_v4)
    st.markdown("Verifique permissões de arquivo e a integridade dos CSVs. Delete-os para recriação se necessário.")
    st.stop()


def registrar_acao(cnpj_reg_corr_v2, acao_reg_corr_v2, descricao_reg_corr_v2): 
    try:
        historico_df_reg_corr_v2 = pd.read_csv(historico_csv, encoding='utf-8') 
    except (FileNotFoundError, pd.errors.EmptyDataError): 
        historico_df_reg_corr_v2 = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    nova_data_reg_corr_v2 = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj_reg_corr_v2, "Ação": acao_reg_corr_v2, "Descrição": descricao_reg_corr_v2 }
    historico_df_reg_corr_v2 = pd.concat([historico_df_reg_corr_v2, pd.DataFrame([nova_data_reg_corr_v2])], ignore_index=True)
    historico_df_reg_corr_v2.to_csv(historico_csv, index=False, encoding='utf-8')

# CORRIGIDO: Nomes dos parâmetros da função de gerar PDF
def gerar_pdf_diagnostico_completo(diagnostico_data_pdf_param, usuario_data_pdf_param, 
                                   perguntas_df_pdf_param, respostas_coletadas_pdf_param, 
                                   medias_categorias_pdf_param):
    try:
        pdf_gen_param = FPDF() 
        pdf_gen_param.add_page()
        empresa_nome_pdf_g_param = usuario_data_pdf_param.get("Empresa", "N/D") 
        cnpj_pdf_g_param = usuario_data_pdf_param.get("CNPJ", "N/D")
        nome_contato_pdf_g_param = usuario_data_pdf_param.get("NomeContato", "")
        telefone_pdf_g_param = usuario_data_pdf_param.get("Telefone", "")
        
        logo_path_pdf_g_param = find_client_logo_path(cnpj_pdf_g_param)
        if logo_path_pdf_g_param:
            try: 
                current_y_pdf_g_param = pdf_gen_param.get_y()
                max_logo_height_g_param = 20 
                pdf_gen_param.image(logo_path_pdf_g_param, x=10, y=current_y_pdf_g_param, h=max_logo_height_g_param) 
                pdf_gen_param.set_y(current_y_pdf_g_param + max_logo_height_g_param + 5) 
            except RuntimeError as e_fpdf_logo_rt_g_param: 
                pass 
            except Exception: pass 

        pdf_gen_param.set_font("Arial", 'B', 16)
        pdf_gen_param.cell(0, 10, pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome_pdf_g_param}"), 0, 1, 'C')
        pdf_gen_param.ln(5)

        pdf_gen_param.set_font("Arial", size=10)
        pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(f"Data do Diagnóstico: {diagnostico_data_pdf_param.get('Data','N/D')}"))
        pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(f"Empresa: {empresa_nome_pdf_g_param} (CNPJ: {cnpj_pdf_g_param})"))
        if nome_contato_pdf_g_param: pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(f"Contato: {nome_contato_pdf_g_param}"))
        if telefone_pdf_g_param: pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(f"Telefone: {telefone_pdf_g_param}"))
        pdf_gen_param.ln(3)

        pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(f"Média Geral (Numérica): {diagnostico_data_pdf_param.get('Média Geral','N/A')}"))
        pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(f"Média Scores GUT (G*U*T): {diagnostico_data_pdf_param.get('GUT Média','N/A')}"))
        pdf_gen_param.ln(3)

        if medias_categorias_pdf_param:
            pdf_gen_param.set_font("Arial", 'B', 11); pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output("Médias por Categoria (Perguntas de Pontuação):"))
            pdf_gen_param.set_font("Arial", size=10)
            for cat_pdf_g_mc_param, media_cat_pdf_g_mc_param in medias_categorias_pdf_param.items(): 
                pdf_gen_param.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat_pdf_g_mc_param}: {media_cat_pdf_g_mc_param}"))
            pdf_gen_param.ln(5)

        for titulo_pdf_g_param, campo_dado_pdf_g_param in [("Resumo do Diagnóstico (Cliente):", "Diagnóstico"), 
                                  ("Análise/Observações do Cliente:", "Análise do Cliente"),
                                  ("Comentários do Consultor:", "Comentarios_Admin")]:
            valor_campo_pdf_g_param = diagnostico_data_pdf_param.get(campo_dado_pdf_g_param, "")
            if valor_campo_pdf_g_param and not pd.isna(valor_campo_pdf_g_param): 
                pdf_gen_param.set_font("Arial", 'B', 12); pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(titulo_pdf_g_param))
                pdf_gen_param.set_font("Arial", size=10); pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(str(valor_campo_pdf_g_param))); pdf_gen_param.ln(3)
            
        pdf_gen_param.set_font("Arial", 'B', 12); pdf_gen_param.multi_cell(0, 10, pdf_safe_text_output("Respostas Detalhadas por Categoria:"))
        categorias_unicas_pdf_g_param = []
        if perguntas_df_pdf_param is not None and "Categoria" in perguntas_df_pdf_param.columns: 
            categorias_unicas_pdf_g_param = perguntas_df_pdf_param["Categoria"].unique()
        
        for categoria_pdf_det_g_param in categorias_unicas_pdf_g_param:
            pdf_gen_param.set_font("Arial", 'B', 10); pdf_gen_param.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria_pdf_det_g_param}"))
            pdf_gen_param.set_font("Arial", size=9)
            perguntas_cat_pdf_det_g_param = perguntas_df_pdf_param[perguntas_df_pdf_param["Categoria"] == categoria_pdf_det_g_param]
            for _, p_row_pdf_det_g_param in perguntas_cat_pdf_det_g_param.iterrows():
                txt_p_pdf_det_g_param = p_row_pdf_det_g_param["Pergunta"]
                resp_p_pdf_det_g_param = respostas_coletadas_pdf_param.get(txt_p_pdf_det_g_param) 
                if resp_p_pdf_det_g_param is None: 
                    resp_p_pdf_det_g_param = diagnostico_data_pdf_param.get(txt_p_pdf_det_g_param, "N/R")

                if isinstance(txt_p_pdf_det_g_param, str) and "[Matriz GUT]" in txt_p_pdf_det_g_param: 
                    g_pdf_v_param, u_pdf_v_param, t_pdf_v_param = 0,0,0 
                    score_gut_item_pdf_v_param = 0
                    if isinstance(resp_p_pdf_det_g_param, dict): 
                        g_pdf_v_param,u_pdf_v_param,t_pdf_v_param = resp_p_pdf_det_g_param.get("G",0), resp_p_pdf_det_g_param.get("U",0), resp_p_pdf_det_g_param.get("T",0)
                    elif isinstance(resp_p_pdf_det_g_param, str): 
                        try: 
                            gut_data_pdf_v_param = json.loads(resp_p_pdf_det_g_param.replace("'", "\""))
                            g_pdf_v_param,u_pdf_v_param,t_pdf_v_param = gut_data_pdf_v_param.get("G",0), gut_data_pdf_v_param.get("U",0), gut_data_pdf_v_param.get("T",0)
                        except: pass 
                    score_gut_item_pdf_v_param = g_pdf_v_param*u_pdf_v_param*t_pdf_v_param
                    pdf_gen_param.multi_cell(0,6,pdf_safe_text_output(f"  - {txt_p_pdf_det_g_param.replace(' [Matriz GUT]','')}: G={g_pdf_v_param}, U={u_pdf_v_param}, T={t_pdf_v_param} (Score: {score_gut_item_pdf_v_param})"))
                elif isinstance(resp_p_pdf_det_g_param, (int, float, str)): 
                    pdf_gen_param.multi_cell(0, 6, pdf_safe_text_output(f"  - {txt_p_pdf_det_g_param}: {resp_p_pdf_det_g_param}"))
            pdf_gen_param.ln(2)
        pdf_gen_param.ln(3)
        
        pdf_gen_param.add_page(); pdf_gen_param.set_font("Arial", 'B', 12)
        pdf_gen_param.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf_gen_param.ln(5)
        pdf_gen_param.set_font("Arial", size=10)
        gut_cards_pdf_g_list_param = [] 
        for pergunta_pdf_k_g_item_param, resp_pdf_k_val_g_item_param in respostas_coletadas_pdf_param.items(): 
            if isinstance(pergunta_pdf_k_g_item_param, str) and "[Matriz GUT]" in pergunta_pdf_k_g_item_param:
                g_k_g_item_param, u_k_g_item_param, t_k_g_item_param = 0,0,0 
                if isinstance(resp_pdf_k_val_g_item_param, dict):
                    g_k_g_item_param, u_k_g_item_param, t_k_g_item_param = resp_pdf_k_val_g_item_param.get("G",0), resp_pdf_k_val_g_item_param.get("U",0), resp_pdf_k_val_g_item_param.get("T",0)
                elif isinstance(resp_pdf_k_val_g_item_param, str): 
                    try: 
                        gut_data_k_g_item_param = json.loads(resp_pdf_k_val_g_item_param.replace("'", "\""))
                        g_k_g_item_param,u_k_g_item_param,t_k_g_item_param = gut_data_k_g_item_param.get("G",0), gut_data_k_g_item_param.get("U",0), gut_data_k_g_item_param.get("T",0)
                    except: pass
                
                score_gut_total_k_pdf_g_item_param = g_k_g_item_param * u_k_g_item_param * t_k_g_item_param
                prazo_k_pdf_g_item_param = "N/A"
                if score_gut_total_k_pdf_g_item_param >= 75: prazo_k_pdf_g_item_param = "15 dias"
                elif score_gut_total_k_pdf_g_item_param >= 40: prazo_k_pdf_g_item_param = "30 dias"
                elif score_gut_total_k_pdf_g_item_param >= 20: prazo_k_pdf_g_item_param = "45 dias"
                elif score_gut_total_k_pdf_g_item_param > 0: prazo_k_pdf_g_item_param = "60 dias"
                else: continue
                if prazo_k_pdf_g_item_param != "N/A":
                    gut_cards_pdf_g_list_param.append({"Tarefa": pergunta_pdf_k_g_item_param.replace(" [Matriz GUT]", ""),"Prazo": prazo_k_pdf_g_item_param, "Score": score_gut_total_k_pdf_g_item_param})
        if gut_cards_pdf_g_list_param:
            gut_cards_pdf_g_sorted_param = sorted(gut_cards_pdf_g_list_param, key=lambda x_g_pdf_param: (int(x_g_pdf_param["Prazo"].split(" ")[0]), -x_g_pdf_param["Score"])) 
            for card_item_pdf_g_final_param in gut_cards_pdf_g_sorted_param: 
                 pdf_gen_param.multi_cell(0, 6, pdf_safe_text_output(f"Prazo: {card_item_pdf_g_final_param['Prazo']} - Tarefa: {card_item_pdf_g_final_param['Tarefa']} (Score GUT: {card_item_pdf_g_final_param['Score']})"))
        else: pdf_gen_param.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile_pdf_gerado_final_param:
            pdf_path_gerado_final_param = tmpfile_pdf_gerado_final_param.name
            pdf_gen_param.output(pdf_path_gerado_final_param)
        return pdf_path_gerado_final_param
    except Exception as e_pdf_main_gerar_final_param:
        st.error(f"Erro crítico ao gerar PDF: {e_pdf_main_gerar_final_param}")
        st.exception(e_pdf_main_gerar_final_param); return None

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_corrected_v2")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_corrected_v2"): 
        usuario_admin_login = st.text_input("Usuário", key="admin_user_login_corrected_v2") 
        senha_admin_login = st.text_input("Senha", type="password", key="admin_pass_login_corrected_v2")
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
        except Exception as e_login_admin_corrected_v2: st.error(f"Erro no login: {e_login_admin_corrected_v2}"); st.exception(e_login_admin_corrected_v2)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_corrected_v2"): 
        cnpj_cli_login = st.text_input("CNPJ", key="cli_cnpj_login_corrected_v2") 
        senha_cli_login = st.text_input("Senha", type="password", key="cli_pass_login_corrected_v2") 
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
        except FileNotFoundError as e_login_cli_fnf_corrected_v2: st.error(f"Arquivo não encontrado: {e_login_cli_fnf_corrected_v2.filename}.")
        except pd.errors.EmptyDataError as e_login_cli_empty_corrected_v2: st.error(f"Arquivo de usuários ou bloqueados está vazio: {e_login_cli_empty_corrected_v2}")
        except Exception as e_login_cli_corrected_v2: st.error(f"Erro no login do cliente: {e_login_cli_corrected_v2}"); st.exception(e_login_cli_corrected_v2)
    st.markdown('</div>', unsafe_allow_html=True); st.stop() 


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    try:
        st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
        
        with st.sidebar.expander("Meu Perfil", expanded=False):
            logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
            if logo_cliente_path:
                try: st.image(logo_cliente_path, width=100)
                except Exception as e_logo_display_cli_final: st.caption(f"Erro ao exibir logo: {e_logo_display_cli_final}")
            st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
            st.write(f"**CNPJ:** {st.session_state.cnpj}")
            st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
            st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")

        DIAGNOSTICO_FORM_ID_KEY_USER = f"form_id_diagnostico_cliente_{st.session_state.cnpj}"

        st.session_state.cliente_page = st.sidebar.radio(
            "Menu Cliente", ["Painel Principal", "Novo Diagnóstico"],
            index=["Painel Principal", "Novo Diagnóstico"].index(st.session_state.cliente_page),
            key="cliente_menu_radio_final_v3_corr"
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
            df_cliente_view_pp = pd.DataFrame() 
            try:
                df_antigos_cli_pp = pd.read_csv(arquivo_csv, encoding='utf-8')
                if not df_antigos_cli_pp.empty:
                    df_cliente_view_pp = df_antigos_cli_pp[df_antigos_cli_pp["CNPJ"].astype(str) == st.session_state.cnpj]
            except (FileNotFoundError, pd.errors.EmptyDataError): pass
            except Exception as e_read_diag_cli_final: st.error(f"Erro ao ler diagnósticos do cliente: {e_read_diag_cli_final}")
            
            if df_cliente_view_pp.empty: 
                st.info("Nenhum diagnóstico anterior. Selecione 'Novo Diagnóstico' no menu.")
            else:
                df_cliente_view_pp = df_cliente_view_pp.sort_values(by="Data", ascending=False)
                for idx_cv_pp, row_cv_pp in df_cliente_view_pp.iterrows():
                    with st.expander(f"📅 {row_cv_pp['Data']} - {row_cv_pp['Empresa']}"):
                        cols_diag_cli_metrics = st.columns(2)
                        with cols_diag_cli_metrics[0]: st.metric("Média Geral", f"{row_cv_pp.get('Média Geral', 0.0):.2f}")
                        with cols_diag_cli_metrics[1]: st.metric("GUT Média (G*U*T)", f"{row_cv_pp.get('GUT Média', 0.0):.2f}")
                        st.write(f"**Resumo (Cliente):** {row_cv_pp.get('Diagnóstico', 'N/P')}")
                        st.markdown("**Médias por Categoria:**")
                        found_cat_media_cv = False
                        cat_cols_display = [col for col in row_cv_pp.index if str(col).startswith("Media_Cat_")]
                        if cat_cols_display:
                            num_cat_cols_display = len(cat_cols_display); max_cols_per_row = 4 
                            display_cols_metrics = st.columns(min(num_cat_cols_display, max_cols_per_row))
                            col_idx_display = 0
                            for col_name_cv_display in cat_cols_display:
                                cat_name_display_cv = col_name_cv_display.replace("Media_Cat_", "").replace("_", " ")
                                current_col_obj = display_cols_metrics[col_idx_display % min(num_cat_cols_display, max_cols_per_row)]
                                current_col_obj.metric(f"Média {cat_name_display_cv}", f"{row_cv_pp.get(col_name_cv_display, 0.0):.2f}")
                                col_idx_display += 1; found_cat_media_cv = True
                        if not found_cat_media_cv: st.caption("  Nenhuma média por categoria.")
                        analise_cli_val_cv = row_cv_pp.get("Análise do Cliente", "")
                        analise_cli_cv = st.text_area("🧠 Minha Análise sobre este Diagnóstico:", value=analise_cli_val_cv, key=f"analise_cv_final_corr_{row_cv_pp.name}")
                        if st.button("💾 Salvar Minha Análise", key=f"salvar_analise_cv_final_corr_{row_cv_pp.name}"):
                            try:
                                df_antigos_upd_cv = pd.read_csv(arquivo_csv, encoding='utf-8') 
                                df_antigos_upd_cv.loc[row_cv_pp.name, "Análise do Cliente"] = analise_cli_cv 
                                df_antigos_upd_cv.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                registrar_acao(st.session_state.cnpj, "Análise Cliente", f"Editou análise de {row_cv_pp['Data']}")
                                st.success("Análise salva!"); st.rerun()
                            except Exception as e_save_analise_final_corr: st.error(f"Erro ao salvar análise: {e_save_analise_final_corr}")
                        com_admin_val_cv = row_cv_pp.get("Comentarios_Admin", "")
                        if com_admin_val_cv and not pd.isna(com_admin_val_cv):
                            st.markdown("**Comentários do Consultor:**"); st.info(f"{com_admin_val_cv}")
                        else: st.caption("Nenhum comentário do consultor.")
                        st.markdown("---")
                
                st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
                gut_cards_painel = []
                if not df_cliente_view_pp.empty:
                    latest_diag_row_painel = df_cliente_view_pp.iloc[0]
                    for pergunta_p, resposta_p_val_str in latest_diag_row_painel.items():
                        if isinstance(pergunta_p, str) and "[Matriz GUT]" in pergunta_p:
                            try:
                                if pd.notna(resposta_p_val_str) and isinstance(resposta_p_val_str, str):
                                    gut_data = json.loads(resposta_p_val_str.replace("'", "\"")) 
                                    g = int(gut_data.get("G", 0)); u = int(gut_data.get("U", 0)); t_final_val = int(gut_data.get("T", 0)) # Corrigido 't'
                                    score_gut_total_p = g * u * t_final_val # Corrigido 't'
                                    prazo_p = "N/A"
                                    if score_gut_total_p >= 75: prazo_p = "15 dias"
                                    elif score_gut_total_p >= 40: prazo_p = "30 dias"
                                    elif score_gut_total_p >= 20: prazo_p = "45 dias"
                                    elif score_gut_total_p > 0: prazo_p = "60 dias"
                                    else: continue 
                                    if prazo_p != "N/A":
                                        gut_cards_painel.append({"Tarefa": pergunta_p.replace(" [Matriz GUT]", ""), "Prazo": prazo_p, "Score": score_gut_total_p, "Responsável": st.session_state.user.get("Empresa", "N/D")})
                            except (json.JSONDecodeError, ValueError, TypeError) as e_k_pp_final_corr: st.warning(f"Erro processar GUT Kanban: '{pergunta_p}'. Erro: {e_k_pp_final_corr}")
                
                if gut_cards_painel:
                    gut_cards_sorted_p = sorted(gut_cards_painel, key=lambda x_pp_final_corr: x_pp_final_corr["Score"], reverse=True)
                    prazos_def_p = sorted(list(set(card_pp_final_corr["Prazo"] for card_pp_final_corr in gut_cards_sorted_p)), key=lambda x_d_pp_final_corr: int(x_d_pp_final_corr.split(" ")[0])) 
                    if prazos_def_p:
                        cols_kanban_p = st.columns(len(prazos_def_p))
                        for idx_kp, prazo_col_kp in enumerate(prazos_def_p):
                            with cols_kanban_p[idx_kp]:
                                st.markdown(f"#### ⏱️ {prazo_col_kp}")
                                for card_item_kp in gut_cards_sorted_p:
                                    if card_item_kp["Prazo"] == prazo_col_kp:
                                        st.markdown(f"""<div class="custom-card"><b>{card_item_kp['Tarefa']}</b> (Score GUT: {card_item_kp['Score']})<br><small><i>👤 {card_item_kp['Responsável']}</i></small></div>""", unsafe_allow_html=True)
                else: st.info("Nenhuma ação prioritária para o Kanban (GUT).")
                
                st.subheader("📈 Comparativo de Evolução")
                if len(df_cliente_view_pp) > 1:
                    grafico_comp_ev = df_cliente_view_pp.sort_values(by="Data")
                    grafico_comp_ev["Data"] = pd.to_datetime(grafico_comp_ev["Data"])
                    colunas_plot_comp = ['Média Geral', 'GUT Média'] 
                    for col_g_comp in grafico_comp_ev.columns:
                        if str(col_g_comp).startswith("Media_Cat_") and pd.api.types.is_numeric_dtype(grafico_comp_ev[col_g_comp]):
                            colunas_plot_comp.append(col_g_comp)
                    for col_plot_c in colunas_plot_comp:
                        if col_plot_c in grafico_comp_ev.columns: grafico_comp_ev[col_plot_c] = pd.to_numeric(grafico_comp_ev[col_plot_c], errors='coerce')
                    
                    colunas_validas_plot = [c for c in colunas_plot_comp if c in grafico_comp_ev.columns and pd.api.types.is_numeric_dtype(grafico_comp_ev[c])]
                    if colunas_validas_plot:
                        st.line_chart(grafico_comp_ev.set_index("Data")[colunas_validas_plot].dropna(axis=1, how='all'))
                    
                    st.subheader("📊 Comparação Entre Diagnósticos") 
                    opcoes_cli = grafico_comp_ev["Data"].astype(str).tolist()
                    if len(opcoes_cli) >= 2:
                        diag_atual_idx, diag_anterior_idx = len(opcoes_cli)-1, len(opcoes_cli)-2
                        diag_atual_sel_cli = st.selectbox("Diagnóstico mais recente:", opcoes_cli, index=diag_atual_idx, key="diag_atual_sel_cli_final_corr")
                        diag_anterior_sel_cli = st.selectbox("Diagnóstico anterior:", opcoes_cli, index=diag_anterior_idx, key="diag_anterior_sel_cli_final_corr")
                        atual_cli = grafico_comp_ev[grafico_comp_ev["Data"].astype(str) == diag_atual_sel_cli].iloc[0]
                        anterior_cli = grafico_comp_ev[grafico_comp_ev["Data"].astype(str) == diag_anterior_sel_cli].iloc[0]
                        st.write(f"### 📅 Comparando {diag_anterior_sel_cli.split(' ')[0]} ⟶ {diag_atual_sel_cli.split(' ')[0]}")
                        cols_excluir_comp = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
                        variaveis_comp = [col for col in grafico_comp_ev.columns if col not in cols_excluir_comp and pd.api.types.is_numeric_dtype(grafico_comp_ev[col])]
                        if variaveis_comp:
                            comp_data = []
                            for v_comp in variaveis_comp:
                                val_ant_c = pd.to_numeric(anterior_cli.get(v_comp), errors='coerce')
                                val_atu_c = pd.to_numeric(atual_cli.get(v_comp), errors='coerce')
                                evolucao_c = "➖ Igual"
                                if pd.notna(val_ant_c) and pd.notna(val_atu_c):
                                    if val_atu_c > val_ant_c: evolucao_c = "🔼 Melhorou"
                                    elif val_atu_c < val_ant_c: evolucao_c = "🔽 Piorou"
                                display_name_comp = v_comp.replace("Media_Cat_", "Média ").replace("_", " ")
                                if "[Pontuação (0-10)]" in display_name_comp or "[Pontuação (0-5) + Matriz GUT]" in display_name_comp or "[Matriz GUT]" in display_name_comp:
                                    display_name_comp = display_name_comp.split(" [")[0] 
                                comp_data.append({"Indicador": display_name_comp, "Anterior": val_ant_c if pd.notna(val_ant_c) else "N/A", "Atual": val_atu_c if pd.notna(val_atu_c) else "N/A", "Evolução": evolucao_c})
                            st.dataframe(pd.DataFrame(comp_data))
                        else: st.info("Sem dados numéricos para comparação.")
                    else: st.info("Pelo menos dois diagnósticos para comparação.")
                else: st.info("Pelo menos dois diagnósticos para comparativos.")

        elif st.session_state.cliente_page == "Novo Diagnóstico":
            st.subheader("📋 Formulário de Novo Diagnóstico")
            
            DIAGNOSTICO_FORM_ID_KEY_USER = f"form_id_diagnostico_cliente_{st.session_state.cnpj}" 
            if DIAGNOSTICO_FORM_ID_KEY_USER not in st.session_state:
                st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER] = datetime.now().strftime("%Y%m%d%H%M%S%f")
            form_id_sufixo_nd_final_corr = st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER]

            temp_respostas_key_nd_final_corr = f"temp_respostas_{form_id_sufixo_nd_final_corr}"
            if temp_respostas_key_nd_final_corr not in st.session_state:
                st.session_state[temp_respostas_key_nd_final_corr] = {}
            
            respostas_form_coletadas_nd_final_corr = st.session_state[temp_respostas_key_nd_final_corr]
            
            try:
                perguntas_df_diag_final_corr = pd.read_csv(perguntas_csv, encoding='utf-8')
                if "Categoria" not in perguntas_df_diag_final_corr.columns: 
                    perguntas_df_diag_final_corr["Categoria"] = "Geral"
            except (FileNotFoundError, pd.errors.EmptyDataError): 
                st.error(f"Arquivo de perguntas ({perguntas_csv}) não encontrado ou vazio."); st.stop()
            except Exception as e_read_perg_form_corr:
                 st.error(f"Erro ao ler arquivo de perguntas: {e_read_perg_form_corr}"); st.stop()

            if perguntas_df_diag_final_corr.empty: 
                st.warning("Nenhuma pergunta cadastrada."); st.stop()
            
            total_perguntas_diag_final_corr = len(perguntas_df_diag_final_corr)
            respondidas_count_diag_final_corr = 0 
            
            if "Categoria" not in perguntas_df_diag_final_corr.columns: 
                st.error("Coluna 'Categoria' não encontrada no arquivo de perguntas."); st.stop()

            categorias_unicas_diag_final_corr = perguntas_df_diag_final_corr["Categoria"].unique()
            
            with st.form(key=f"diagnostico_form_completo_{form_id_sufixo_nd_final_corr}"):
                if total_perguntas_diag_final_corr == 0:
                    st.warning("Nenhuma pergunta disponível.")
                else:
                    for categoria_diag_final_corr in categorias_unicas_diag_final_corr:
                        st.markdown(f"#### Categoria: {categoria_diag_final_corr}")
                        perguntas_cat_diag_final_corr = perguntas_df_diag_final_corr[perguntas_df_diag_final_corr["Categoria"] == categoria_diag_final_corr]
                        
                        if perguntas_cat_diag_final_corr.empty: continue

                        for idx_diag_f_final_corr, row_diag_f_final_corr in perguntas_cat_diag_final_corr.iterrows():
                            texto_pergunta_diag_final_corr = str(row_diag_f_final_corr["Pergunta"]) 
                            widget_base_key_final_corr = f"q_form_final_corr_{idx_diag_f_final_corr}" 

                            if "[Matriz GUT]" in texto_pergunta_diag_final_corr:
                                st.markdown(f"**{texto_pergunta_diag_final_corr.replace(' [Matriz GUT]', '')}**")
                                cols_gut_final_corr = st.columns(3)
                                gut_current_vals_final_corr = respostas_form_coletadas_nd_final_corr.get(texto_pergunta_diag_final_corr, {"G":0, "U":0, "T":0})
                                with cols_gut_final_corr[0]: g_val_final_corr = st.slider("Gravidade (0-5)", 0, 5, value=int(gut_current_vals_final_corr.get("G",0)), key=f"{widget_base_key_final_corr}_G")
                                with cols_gut_final_corr[1]: u_val_final_corr = st.slider("Urgência (0-5)", 0, 5, value=int(gut_current_vals_final_corr.get("U",0)), key=f"{widget_base_key_final_corr}_U")
                                with cols_gut_final_corr[2]: t_val_final_corr = st.slider("Tendência (0-5)", 0, 5, value=int(gut_current_vals_final_corr.get("T",0)), key=f"{widget_base_key_final_corr}_T")
                                respostas_form_coletadas_nd_final_corr[texto_pergunta_diag_final_corr] = {"G": g_val_final_corr, "U": u_val_final_corr, "T": t_val_final_corr}
                                if g_val_final_corr > 0 or u_val_final_corr > 0 or t_val_final_corr > 0 : respondidas_count_diag_final_corr +=1
                            elif "Pontuação (0-5)" in texto_pergunta_diag_final_corr: 
                                val_final_corr = respostas_form_coletadas_nd_final_corr.get(texto_pergunta_diag_final_corr, 0)
                                respostas_form_coletadas_nd_final_corr[texto_pergunta_diag_final_corr] = st.slider(texto_pergunta_diag_final_corr, 0, 5, value=int(val_final_corr), key=widget_base_key_final_corr) 
                                if respostas_form_coletadas_nd_final_corr[texto_pergunta_diag_final_corr] != 0: respondidas_count_diag_final_corr += 1
                            elif "Pontuação (0-10)" in texto_pergunta_diag_final_corr:
                                val_final_corr = respostas_form_coletadas_nd_final_corr.get(texto_pergunta_diag_final_corr, 0)
                                respostas_form_coletadas_nd_final_corr[texto_pergunta_diag_final_corr] = st.slider(texto_pergunta_diag_final_corr, 0, 10, value=int(val_final_corr), key=widget_base_key_final_corr)
                                if respostas_form_coletadas_nd_final_corr[texto_pergunta_diag_final_corr] != 0: respondidas_count_diag_final_corr += 1
                            elif "Texto Aberto" in texto_pergunta_diag_final_corr:
                                val_final_corr = respostas_form_coletadas_nd_final_corr.get(texto_pergunta_diag_final_corr, "")
                                respostas_form_coletadas_nd_final_corr[texto_pergunta_diag_final_corr] = st.text_area(texto_pergunta_diag_final_corr, value=str(val_final_corr), key=widget_base_key_final_corr)
                                if respostas_form_coletadas_nd_final_corr[texto_pergunta_diag_final_corr].strip() != "": respondidas_count_diag_final_corr += 1
                            elif "Escala" in texto_pergunta_diag_final_corr: 
                                opcoes_escala_diag_final_corr = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"] 
                                val_final_corr = respostas_form_coletadas_nd_final_corr.get(texto_pergunta_diag_final_corr, "Selecione")
                                idx_sel_final_corr = opcoes_escala_diag_final_corr.index(val_final_corr) if val_final_corr in opcoes_escala_diag_final_corr else 0
                                respostas_form_coletadas_nd_final_corr[texto_pergunta_diag_final_corr] = st.selectbox(texto_pergunta_diag_final_corr, opcoes_escala_diag_final_corr, index=idx_sel_final_corr, key=widget_base_key_final_corr)
                                if respostas_form_coletadas_nd_final_corr[texto_pergunta_diag_final_corr] != "Selecione": respondidas_count_diag_final_corr += 1
                            else: 
                                val_final_corr = respostas_form_coletadas_nd_final_corr.get(texto_pergunta_diag_final_corr, 0)
                                respostas_form_coletadas_nd_final_corr[texto_pergunta_diag_final_corr] = st.slider(texto_pergunta_diag_final_corr, 0, 10, value=int(val_final_corr), key=widget_base_key_final_corr)
                                if respostas_form_coletadas_nd_final_corr[texto_pergunta_diag_final_corr] != 0: respondidas_count_diag_final_corr += 1
                        st.divider()
                
                progresso_diag_final_corr = round((respondidas_count_diag_final_corr / total_perguntas_diag_final_corr) * 100) if total_perguntas_diag_final_corr > 0 else 0
                st.info(f"📊 Progresso: {respondidas_count_diag_final_corr} de {total_perguntas_diag_final_corr} respondidas ({progresso_diag_final_corr}%)")
                
                obs_cli_diag_form_final_corr = st.text_area("Sua Análise/Observações (opcional):", value=respostas_form_coletadas_nd_final_corr.get("__obs_cliente__", ""), key=f"obs_cli_diag_final_corr_{form_id_sufixo_nd_final_corr}")
                respostas_form_coletadas_nd_final_corr["__obs_cliente__"] = obs_cli_diag_form_final_corr
                
                diag_resumo_cli_diag_final_corr = st.text_area("✍️ Resumo/principais insights (para PDF):", value=respostas_form_coletadas_nd_final_corr.get("__resumo_cliente__", ""), key=f"diag_resumo_diag_final_corr_{form_id_sufixo_nd_final_corr}")
                respostas_form_coletadas_nd_final_corr["__resumo_cliente__"] = diag_resumo_cli_diag_final_corr

                enviar_diagnostico_btn_final_corr = st.form_submit_button("✔️ Enviar Diagnóstico")

            if enviar_diagnostico_btn_final_corr:
                if respondidas_count_diag_final_corr < total_perguntas_diag_final_corr: st.warning("Responda todas as perguntas.")
                elif not respostas_form_coletadas_nd_final_corr["__resumo_cliente__"].strip(): st.error("O campo 'Resumo/principais insights (para PDF)' é obrigatório.")
                else:
                    soma_total_gut_scores_final_corr, count_gut_perguntas_final_corr = 0, 0
                    respostas_finais_para_salvar_final_corr = {}

                    for pergunta_env_final_corr, resposta_env_final_corr in respostas_form_coletadas_nd_final_corr.items():
                        if pergunta_env_final_corr.startswith("__"): continue 
                        if isinstance(pergunta_env_final_corr, str) and "[Matriz GUT]" in pergunta_env_final_corr and isinstance(resposta_env_final_corr, dict):
                            respostas_finais_para_salvar_final_corr[pergunta_env_final_corr] = json.dumps(resposta_env_final_corr) 
                            g_f_final_corr, u_f_final_corr, t_f_final_corr = resposta_env_final_corr.get("G",0), resposta_env_final_corr.get("U",0), resposta_env_final_corr.get("T",0)
                            soma_total_gut_scores_final_corr += (g_f_final_corr * u_f_final_corr * t_f_final_corr)
                            count_gut_perguntas_final_corr +=1
                        else:
                            respostas_finais_para_salvar_final_corr[pergunta_env_final_corr] = resposta_env_final_corr # CORRIGIDO AQUI

                    gut_media_calc_final_corr = round(soma_total_gut_scores_final_corr / count_gut_perguntas_final_corr, 2) if count_gut_perguntas_final_corr > 0 else 0.0
                    numeric_resp_calc_final_corr = [v_f_final_corr for k_f_final_corr, v_f_final_corr in respostas_finais_para_salvar_final_corr.items() if isinstance(v_f_final_corr, (int, float)) and ("Pontuação (0-10)" in k_f_final_corr or "Pontuação (0-5)" in k_f_final_corr)] 
                    media_geral_calc_final_val_final_corr = round(sum(numeric_resp_calc_final_corr) / len(numeric_resp_calc_final_corr), 2) if numeric_resp_calc_final_corr else 0.0
                    empresa_nome_final_val_final_corr = st.session_state.user.get("Empresa", "N/D")
                    
                    nova_linha_final_val_final_corr = {
                        "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": st.session_state.cnpj,
                        "Nome": st.session_state.user.get("CNPJ", ""), "Email": "", "Empresa": empresa_nome_final_val_final_corr,
                        "Média Geral": media_geral_calc_final_val_final_corr, "GUT Média": gut_media_calc_final_corr, 
                        "Observações": "", 
                        "Análise do Cliente": respostas_form_coletadas_nd_final_corr.get("__obs_cliente__",""), 
                        "Diagnóstico": respostas_form_coletadas_nd_final_corr.get("__resumo_cliente__",""), 
                        "Comentarios_Admin": ""
                    }
                    nova_linha_final_val_final_corr.update(respostas_finais_para_salvar_final_corr)

                    medias_por_categoria_final_val_final_corr = {}
                    for cat_final_calc_val_final_corr in categorias_unicas_diag_final_corr:
                        perguntas_cat_final_df_val_final_corr = perguntas_df_diag_final_corr[perguntas_df_diag_final_corr["Categoria"] == cat_final_calc_val_final_corr]
                        soma_cat_final_val_final_corr, cont_num_cat_final_val_final_corr = 0, 0
                        for _, p_row_final_val_final_corr in perguntas_cat_final_df_val_final_corr.iterrows():
                            txt_p_final_val_final_corr = p_row_final_val_final_corr["Pergunta"]
                            resp_p_final_val_final_corr = respostas_form_coletadas_nd_final_corr.get(txt_p_final_val_final_corr)
                            if isinstance(resp_p_final_val_final_corr, (int, float)) and \
                               (isinstance(txt_p_final_val_final_corr, str) and "[Matriz GUT]" not in txt_p_final_val_final_corr) and \
                               (isinstance(txt_p_final_val_final_corr, str) and ("Pontuação (0-10)" in txt_p_final_val_final_corr or "Pontuação (0-5)" in txt_p_final_val_final_corr)):
                                soma_cat_final_val_final_corr += resp_p_final_val_final_corr
                                cont_num_cat_final_val_final_corr += 1
                        media_c_final_val_final_corr = round(soma_cat_final_val_final_corr / cont_num_cat_final_val_final_corr, 2) if cont_num_cat_final_val_final_corr > 0 else 0.0
                        nome_col_media_cat_final_val_final_corr = f"Media_Cat_{sanitize_column_name(cat_final_calc_val_final_corr)}"
                        nova_linha_final_val_final_corr[nome_col_media_cat_final_val_final_corr] = media_c_final_val_final_corr
                        medias_por_categoria_final_val_final_corr[cat_final_calc_val_final_corr] = media_c_final_val_final_corr

                    try: df_diag_todos_final_val_final_corr = pd.read_csv(arquivo_csv, encoding='utf-8')
                    except (FileNotFoundError, pd.errors.EmptyDataError): df_diag_todos_final_val_final_corr = pd.DataFrame() 
                    
                    for col_f_save_final_val_final_corr in nova_linha_final_val_final_corr.keys(): 
                        if col_f_save_final_val_final_corr not in df_diag_todos_final_val_final_corr.columns: df_diag_todos_final_val_final_corr[col_f_save_final_val_final_corr] = pd.NA 
                    df_diag_todos_final_val_final_corr = pd.concat([df_diag_todos_final_val_final_corr, pd.DataFrame([nova_linha_final_val_final_corr])], ignore_index=True)
                    df_diag_todos_final_val_final_corr.to_csv(arquivo_csv, index=False, encoding='utf-8')
                    
                    st.success("Diagnóstico enviado com sucesso!")
                    registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", "Cliente enviou novo diagnóstico.")
                    
                    pdf_path_final_val_final_corr = gerar_pdf_diagnostico_completo(
                        diagnostico_data_pdf_param=nova_linha_final_val_final_corr,  # CORRIGIDO
                        usuario_data_pdf_param=st.session_state.user,              # CORRIGIDO
                        perguntas_df_pdf_param=perguntas_df_diag_final_corr,     # CORRIGIDO
                        respostas_coletadas_pdf_param=respostas_form_coletadas_nd_final_corr, # CORRIGIDO
                        medias_categorias_pdf_param=medias_por_categoria_final_val_final_corr # CORRIGIDO
                    )
                    if pdf_path_final_val_final_corr:
                        with open(pdf_path_final_val_final_corr, "rb") as f_pdf_final_val_final_corr:
                            st.download_button(label="📄 Baixar PDF do Diagnóstico", data=f_pdf_final_val_final_corr, 
                                           file_name=f"diagnostico_{sanitize_column_name(empresa_nome_final_val_final_corr)}_{datetime.now().strftime('%Y%m%d')}.pdf", 
                                           mime="application/pdf", key="download_pdf_cliente_final_corrected_v2")
                        registrar_acao(st.session_state.cnpj, "Download PDF", "Baixou PDF do novo diagnóstico.")
                    
                    if DIAGNOSTICO_FORM_ID_KEY_USER in st.session_state: del st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER]
                    if temp_respostas_key_nd_final_corr in st.session_state: del st.session_state[temp_respostas_key_nd_final_corr]
                    
                    st.session_state.diagnostico_enviado = True
                    st.session_state.cliente_page = "Painel Principal" 
                    st.rerun()
    except Exception as e_cliente_area_corrected_final_v2:
        st.error(f"Ocorreu um erro na área do cliente: {e_cliente_area_corrected_final_v2}")
        st.exception(e_cliente_area_corrected_final_v2) 


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
        key="admin_menu_selectbox_corrected_final_v2" 
    )
    st.header(f"🔑 Painel Admin: {menu_admin}")

    try: 
        if menu_admin == "Visão Geral e Diagnósticos":
            st.subheader("📊 Visão Geral dos Diagnósticos")
            # st.write("DEBUG: Admin - Carregando Visão Geral e Diagnósticos...") # DEBUG Opcional

            diagnosticos_df_admin = pd.DataFrame() 
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
            except Exception as e_load_diag_admin_vg_corrected_v2:
                st.error(f"ERRO AO CARREGAR DIAGNÓSTICOS (Visão Geral): {e_load_diag_admin_vg_corrected_v2}")
                st.exception(e_load_diag_admin_vg_corrected_v2)
            
            if admin_data_loaded and not diagnosticos_df_admin.empty:
                # st.write("DEBUG: Admin - Dados carregados para Visão Geral. Renderizando...") # DEBUG Opcional
                empresas_disponiveis_vg = ["Todos os Clientes"] + sorted(diagnosticos_df_admin["Empresa"].astype(str).unique().tolist())
                empresa_selecionada_vg = st.selectbox(
                    "Filtrar Visão Geral por Empresa:", 
                    empresas_disponiveis_vg, 
                    key="admin_visao_geral_filtro_empresa_corrected_v2"
                )

                df_filtrado_vg = diagnosticos_df_admin.copy()
                if empresa_selecionada_vg != "Todos os Clientes":
                    df_filtrado_vg = df_filtrado_vg[df_filtrado_vg["Empresa"] == empresa_selecionada_vg]
                
                if df_filtrado_vg.empty:
                    st.info(f"Nenhum diagnóstico encontrado para '{empresa_selecionada_vg}'.")
                else:
                    st.markdown(f"#### Indicadores Gerais para: {empresa_selecionada_vg}")
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

                    st.markdown(f"#### Diagnósticos Enviados ({empresa_selecionada_vg})")
                    st.dataframe(df_filtrado_vg.sort_values(by="Data", ascending=False).reset_index(drop=True))
                    if empresa_selecionada_vg == "Todos os Clientes":
                        csv_export_admin_vg = df_filtrado_vg.to_csv(index=False).encode('utf-8') 
                        st.download_button("⬇️ Exportar Todos os Diagnósticos (CSV)", csv_export_admin_vg, file_name=f"diagnosticos_completos.csv", mime="text/csv", key="download_todos_csv_admin_corrected_v2")
                    st.divider()
                    
                    st.markdown("#### Detalhar, Comentar e Baixar PDF de Diagnóstico Específico")
                    empresas_detalhe_vg = sorted(df_filtrado_vg["Empresa"].astype(str).unique().tolist())
                    if not empresas_detalhe_vg:
                        st.info("Nenhuma empresa na seleção atual para detalhar.")
                    else:
                        default_empresa_detalhe_idx_vg = 0
                        if empresa_selecionada_vg != "Todos os Clientes" and empresa_selecionada_vg in empresas_detalhe_vg:
                            default_empresa_detalhe_idx_vg = empresas_detalhe_vg.index(empresa_selecionada_vg)

                        empresa_selecionada_detalhe_vg = st.selectbox("Selecione uma Empresa para Detalhar:", empresas_detalhe_vg, index=default_empresa_detalhe_idx_vg, key="admin_empresa_filter_detail_corrected_v2")
                        
                        diagnosticos_empresa_detalhe_vg = df_filtrado_vg[df_filtrado_vg["Empresa"] == empresa_selecionada_detalhe_vg].sort_values(by="Data", ascending=False)
                        if not diagnosticos_empresa_detalhe_vg.empty:
                            datas_diagnosticos_detalhe_vg = ["Selecione Data..."] + diagnosticos_empresa_detalhe_vg["Data"].tolist()
                            diagnostico_data_selecionada_detalhe_vg = st.selectbox("Selecione a Data do Diagnóstico:", datas_diagnosticos_detalhe_vg, key="admin_data_diagnostico_select_corrected_v2")
                            if diagnostico_data_selecionada_detalhe_vg != "Selecione Data...":
                                diagnostico_selecionado_adm_row_vg = diagnosticos_empresa_detalhe_vg[diagnosticos_empresa_detalhe_vg["Data"] == diagnostico_data_selecionada_detalhe_vg].iloc[0]
                                
                                st.markdown(f"**Detalhes do Diagnóstico de {diagnostico_selecionado_adm_row_vg['Data']}**")
                                st.write(f"**Média Geral:** {diagnostico_selecionado_adm_row_vg.get('Média Geral', 'N/A')} | **GUT Média (G*U*T):** {diagnostico_selecionado_adm_row_vg.get('GUT Média', 'N/A')}")
                                
                                comentario_adm_atual_val_vg = diagnostico_selecionado_adm_row_vg.get("Comentarios_Admin", "")
                                if pd.isna(comentario_adm_atual_val_vg): comentario_adm_atual_val_vg = ""
                                novo_comentario_adm_val_vg = st.text_area("Comentários do Consultor/Admin:", value=comentario_adm_atual_val_vg, key=f"admin_comment_detail_corrected_v2_{diagnostico_selecionado_adm_row_vg.name}")
                                if st.button("💾 Salvar Comentário", key=f"save_admin_comment_detail_corrected_v2_{diagnostico_selecionado_adm_row_vg.name}"):
                                    df_diag_save_com_adm_det_vg = pd.read_csv(arquivo_csv, encoding='utf-8')
                                    df_diag_save_com_adm_det_vg.loc[diagnostico_selecionado_adm_row_vg.name, "Comentarios_Admin"] = novo_comentario_adm_val_vg
                                    df_diag_save_com_adm_det_vg.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                    registrar_acao("ADMIN", "Comentário Admin", f"Admin comentou diag. de {diagnostico_selecionado_adm_row_vg['Data']} para {empresa_selecionada_detalhe_vg}")
                                    st.success("Comentário salvo!"); st.rerun()

                                if st.button("📄 Baixar PDF deste Diagnóstico", key=f"download_pdf_admin_corrected_v2_{diagnostico_selecionado_adm_row_vg.name}"):
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
                                        diagnostico_data_pdf_param=diagnostico_selecionado_adm_row_vg.to_dict(), # CORRIGIDO
                                        usuario_data_pdf_param=usuario_data_pdf_adm_vg, # CORRIGIDO
                                        perguntas_df_pdf_param=perguntas_df_pdf_adm_vg, # CORRIGIDO
                                        respostas_coletadas_pdf_param=respostas_para_pdf_adm_vg,  # CORRIGIDO
                                        medias_categorias_pdf_param=medias_cat_pdf_adm_vg # CORRIGIDO
                                    )
                                    if pdf_path_admin_dl_vg:
                                        with open(pdf_path_admin_dl_vg, "rb") as f_pdf_adm_dl_vg:
                                            st.download_button(label="Download PDF Confirmado", data=f_pdf_adm_dl_vg, 
                                                           file_name=f"diagnostico_{sanitize_column_name(empresa_selecionada_detalhe_vg)}_{diagnostico_selecionado_adm_row_vg['Data'].replace(':','-')}.pdf",
                                                           mime="application/pdf", key=f"confirm_dl_pdf_admin_corrected_v2_{diagnostico_selecionado_adm_row_vg.name}")
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
            except Exception as e_hist_corrected_v2: st.error(f"Erro ao carregar histórico: {e_hist_corrected_v2}")

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
                            nova_p_text_admin = st.text_input("Pergunta", value=str(row_p_admin["Pergunta"]), key=f"edit_p_txt_corrected_v2_{i_p_admin}")
                        with cols_p_admin[1]:
                            nova_cat_text_admin = st.text_input("Categoria", value=str(row_p_admin.get("Categoria", "Geral")), key=f"edit_p_cat_corrected_v2_{i_p_admin}")
                        with cols_p_admin[2]:
                            st.write("") 
                            if st.button("💾", key=f"salvar_p_adm_corrected_v2_{i_p_admin}", help="Salvar"):
                                perguntas_df_admin_edit.loc[i_p_admin, "Pergunta"] = nova_p_text_admin 
                                perguntas_df_admin_edit.loc[i_p_admin, "Categoria"] = nova_cat_text_admin
                                perguntas_df_admin_edit.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                st.success(f"Pergunta {i_p_admin+1} atualizada."); st.rerun()
                        with cols_p_admin[3]:
                            st.write("") 
                            if st.button("🗑️", key=f"deletar_p_adm_corrected_v2_{i_p_admin}", help="Deletar"):
                                perguntas_df_admin_edit = perguntas_df_admin_edit.drop(i_p_admin).reset_index(drop=True)
                                perguntas_df_admin_edit.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                st.warning(f"Pergunta {i_p_admin+1} removida."); st.rerun()
                        st.divider()
            with tabs_perg_admin[1]: 
                with st.form("form_nova_pergunta_admin_corrected_v2"):
                    st.subheader("➕ Adicionar Nova Pergunta")
                    nova_p_form_txt_admin = st.text_input("Texto da Pergunta", key="nova_p_input_admin_txt_corrected_v2")
                    try:
                        perg_exist_df = pd.read_csv(perguntas_csv, encoding='utf-8')
                        cat_existentes = sorted(list(perg_exist_df['Categoria'].astype(str).unique())) if not perg_exist_df.empty and "Categoria" in perg_exist_df else []
                    except: cat_existentes = []
                    
                    cat_options = ["Nova Categoria"] + cat_existentes
                    cat_selecionada = st.selectbox("Categoria:", cat_options, key="cat_select_admin_new_q_corrected_v2")
                    
                    if cat_selecionada == "Nova Categoria":
                        nova_cat_form_admin = st.text_input("Nome da Nova Categoria:", key="nova_cat_input_admin_new_q_corrected_v2")
                    else: nova_cat_form_admin = cat_selecionada

                    tipo_p_form_admin = st.selectbox("Tipo de Pergunta", 
                                                 ["Pontuação (0-10)", "Texto Aberto", "Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)", "[Matriz GUT]"], 
                                                 key="tipo_p_select_admin_new_q_corrected_v2")
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
                            st.text_input("CNPJ (não editável)", value=row_gc['CNPJ'], disabled=True, key=f"cnpj_gc_corrected_v2_{idx_gc}")
                            nova_senha_gc = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password", key=f"senha_gc_corrected_v2_{idx_gc}")
                            nome_empresa_gc = st.text_input("Nome Empresa", value=row_gc.get('Empresa',""), key=f"empresa_gc_corrected_v2_{idx_gc}")
                        with cols_edit_cli[1]:
                            nome_contato_gc = st.text_input("Nome Contato", value=row_gc.get("NomeContato", ""), key=f"nomec_gc_corrected_v2_{idx_gc}")
                            telefone_gc = st.text_input("Telefone", value=row_gc.get("Telefone", ""), key=f"tel_gc_corrected_v2_{idx_gc}")
                            logo_atual_path = find_client_logo_path(row_gc['CNPJ'])
                            if logo_atual_path: st.image(logo_atual_path, width=100, caption="Logo Atual")
                            uploaded_logo_gc = st.file_uploader("Alterar/Adicionar Logo", type=["png", "jpg", "jpeg"], key=f"logo_gc_corrected_v2_{idx_gc}")

                        if st.button("💾 Salvar Alterações do Cliente", key=f"save_gc_corrected_v2_{idx_gc}"):
                            if nova_senha_gc: usuarios_clientes_df.loc[idx_gc, "Senha"] = nova_senha_gc
                            usuarios_clientes_df.loc[idx_gc, "Empresa"] = nome_empresa_gc
                            usuarios_clientes_df.loc[idx_gc, "NomeContato"] = nome_contato_gc
                            usuarios_clientes_df.loc[idx_gc, "Telefone"] = telefone_gc
                            if uploaded_logo_gc is not None:
                                if not os.path.exists(LOGOS_DIR): os.makedirs(LOGOS_DIR)
                                clean_cnpj_gc_save = sanitize_column_name(str(row_gc['CNPJ'])) 
                                for ext_old in ["png", "jpg", "jpeg"]: 
                                    old_path = os.path.join(LOGOS_DIR, f"{clean_cnpj_gc_save}_logo.{ext_old}")
                                    if os.path.exists(old_path): 
                                        try: os.remove(old_path)
                                        except Exception as e_remove_logo_final_corr: st.warning(f"Não foi possível remover logo antiga {old_path}: {e_remove_logo_final_corr}")
                                file_extension = uploaded_logo_gc.name.split('.')[-1].lower()
                                logo_save_path_gc = os.path.join(LOGOS_DIR, f"{clean_cnpj_gc_save}_logo.{file_extension}")
                                try:
                                    with open(logo_save_path_gc, "wb") as f: f.write(uploaded_logo_gc.getbuffer())
                                    st.success(f"Logo de {row_gc['Empresa']} atualizada!")
                                except Exception as e_save_logo_corrected_v2: st.error(f"Erro ao salvar logo: {e_save_logo_corrected_v2}")
                            
                            usuarios_clientes_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
                            st.success(f"Dados de {row_gc['Empresa']} atualizados!"); st.rerun()
                st.divider()

            st.subheader("➕ Adicionar Novo Cliente")
            with st.form("form_novo_cliente_admin_corrected_v2"):
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
                            except Exception as e_save_new_logo_corrected_v2: st.error(f"Erro ao salvar nova logo: {e_save_new_logo_corrected_v2}")
                        
                        st.success(f"Cliente '{nova_empresa_gc_form}' adicionado!"); st.rerun()
                else: st.warning("CNPJ, Senha e Nome da Empresa são obrigatórios.")
            
            st.markdown("---"); st.subheader("🚫 Gerenciar Bloqueios")
            try: bloqueados_df_adm = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
            except (FileNotFoundError, pd.errors.EmptyDataError): bloqueados_df_adm = pd.DataFrame(columns=["CNPJ"])
            st.write("CNPJs bloqueados:", bloqueados_df_adm["CNPJ"].tolist() if not bloqueados_df_adm.empty else "Nenhum")
            col_block, col_unblock = st.columns(2)
            with col_block:
                cnpj_para_bloquear = st.selectbox("Bloquear CNPJ:", [""] + usuarios_clientes_df["CNPJ"].astype(str).unique().tolist(), key="block_cnpj_corrected_v2")
                if st.button("Bloquear Selecionado", key="btn_block_corrected_v2") and cnpj_para_bloquear:
                    if cnpj_para_bloquear not in bloqueados_df_adm["CNPJ"].astype(str).values:
                        nova_block = pd.DataFrame([[cnpj_para_bloquear]], columns=["CNPJ"])
                        bloqueados_df_adm = pd.concat([bloqueados_df_adm, nova_block], ignore_index=True)
                        bloqueados_df_adm.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                        st.success(f"CNPJ {cnpj_para_bloquear} bloqueado."); st.rerun()
                    else: st.warning(f"CNPJ {cnpj_para_bloquear} já bloqueado.")
            with col_unblock:
                cnpj_para_desbloquear = st.selectbox("Desbloquear CNPJ:", [""] + bloqueados_df_adm["CNPJ"].astype(str).unique().tolist(), key="unblock_cnpj_corrected_v2")
                if st.button("Desbloquear Selecionado", key="btn_unblock_corrected_v2") and cnpj_para_desbloquear:
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
            with st.form("form_novo_admin_manage_corrected_v2"):
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
                admin_para_remover_manage = st.selectbox("Remover Admin:", options=[""] + admins_df_manage["Usuario"].tolist(), key="remove_admin_select_manage_corrected_v2")
                if st.button("Remover Admin Selecionado", type="primary", key="btn_remove_admin_corrected_v2") and admin_para_remover_manage:
                    if len(admins_df_manage) == 1 and admin_para_remover_manage == admins_df_manage["Usuario"].iloc[0]:
                        st.error("Não é possível remover o único administrador.")
                    else:
                        admins_df_manage = admins_df_manage[admins_df_manage["Usuario"] != admin_para_remover_manage]
                        admins_df_manage.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                        st.warning(f"Admin '{admin_para_remover_manage}' removido."); st.rerun()
            else: st.info("Nenhum administrador para remover.")

    except Exception as e_admin_area_corrected_final_v2:
        st.error(f"Ocorreu um erro crítico na área administrativa: {e_admin_area_corrected_final_v2}")
        st.exception(e_admin_area_corrected_final_v2)

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()