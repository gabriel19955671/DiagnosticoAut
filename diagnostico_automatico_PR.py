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

def find_client_logo_path(cnpj_find_logo):
    if not cnpj_find_logo: return None
    base_name = str(cnpj_find_logo).replace('/', '').replace('.', '').replace('-', '') 
    for ext_logo in ["png", "jpg", "jpeg"]:
        path_logo = os.path.join(LOGOS_DIR, f"{base_name}_logo.{ext_logo}")
        if os.path.exists(path_logo):
            return path_logo
    return None

# --- Criação e Verificação de Arquivos e Pastas ---
if not os.path.exists(LOGOS_DIR):
    try:
        os.makedirs(LOGOS_DIR)
    except OSError as e_logo_dir_final_v2:
        st.error(f"Não foi possível criar o diretório de logos '{LOGOS_DIR}': {e_logo_dir_final_v2}")

colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone"]
colunas_base_perguntas = ["Pergunta", "Categoria"]

def inicializar_csv(filepath, columns, is_perguntas_file=False):
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init_final = pd.DataFrame(columns=columns)
            df_init_final.to_csv(filepath, index=False, encoding='utf-8')
        else:
            df_init_final = pd.read_csv(filepath, encoding='utf-8')
            missing_cols_init_final = [col_final for col_final in columns if col_final not in df_init_final.columns]
            made_changes_init_final = False
            if missing_cols_init_final:
                for col_m_final in missing_cols_init_final:
                    if is_perguntas_file and col_m_final == "Categoria": df_init_final[col_m_final] = "Geral"
                    else: df_init_final[col_m_final] = pd.NA 
                made_changes_init_final = True
            if is_perguntas_file and "Categoria" not in df_init_final.columns:
                df_init_final["Categoria"] = "Geral"; made_changes_init_final = True
            if made_changes_init_final:
                df_init_final.to_csv(filepath, index=False, encoding='utf-8')
    except pd.errors.EmptyDataError: 
        pd.DataFrame(columns=columns).to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e_init_csv_final_v2:
        st.error(f"Erro ao inicializar/verificar {filepath}: {e_init_csv_final_v2}. O app pode não funcionar corretamente.")
        st.exception(e_init_csv_final_v2) 
        raise 

try:
    inicializar_csv(usuarios_bloqueados_csv, ["CNPJ"])
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios)
    inicializar_csv(perguntas_csv, colunas_base_perguntas, is_perguntas_file=True)
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    inicializar_csv(arquivo_csv, colunas_base_diagnosticos)
except Exception as e_init_all_final_v3:
    st.error(f"Falha crítica na inicialização de arquivos CSV base: {e_init_all_final_v3}")
    st.exception(e_init_all_final_v3)
    st.markdown("Verifique permissões de arquivo e a integridade dos CSVs. Delete-os para recriação se necessário.")
    st.stop()


def registrar_acao(cnpj_reg_v2, acao_reg_v2, descricao_reg_v2):
    try:
        historico_df_reg_v2 = pd.read_csv(historico_csv, encoding='utf-8') 
    except (FileNotFoundError, pd.errors.EmptyDataError): 
        historico_df_reg_v2 = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
    nova_data_reg_v2 = { "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj_reg_v2, "Ação": acao_reg_v2, "Descrição": descricao_reg_v2 }
    historico_df_reg_v2 = pd.concat([historico_df_reg_v2, pd.DataFrame([nova_data_reg_v2])], ignore_index=True)
    historico_df_reg_v2.to_csv(historico_csv, index=False, encoding='utf-8')


def gerar_pdf_diagnostico_completo(diagnostico_data_pdf_v2, usuario_data_pdf_v2, perguntas_df_pdf_v2, respostas_coletadas_pdf_v2, medias_categorias_pdf_v2):
    try:
        pdf_gen_v2 = FPDF() 
        pdf_gen_v2.add_page()
        empresa_nome_pdf_g_v2 = usuario_data_pdf_v2.get("Empresa", "N/D") 
        cnpj_pdf_g_v2 = usuario_data_pdf_v2.get("CNPJ", "N/D")
        nome_contato_pdf_g_v2 = usuario_data_pdf_v2.get("NomeContato", "")
        telefone_pdf_g_v2 = usuario_data_pdf_v2.get("Telefone", "")
        
        logo_path_pdf_g_v2 = find_client_logo_path(cnpj_pdf_g_v2)
        if logo_path_pdf_g_v2:
            try: 
                current_y_pdf_g_v2 = pdf_gen_v2.get_y()
                max_logo_height_g_v2 = 20 
                pdf_gen_v2.image(logo_path_pdf_g_v2, x=10, y=current_y_pdf_g_v2, h=max_logo_height_g_v2) 
                pdf_gen_v2.set_y(current_y_pdf_g_v2 + max_logo_height_g_v2 + 5) 
            except RuntimeError as e_fpdf_logo_rt_g_v2: 
                pass # st.warning(f"Não foi possível adicionar a logo ao PDF: {e_fpdf_logo_rt_g_v2}") # Opcional
            except Exception: pass 

        pdf_gen_v2.set_font("Arial", 'B', 16)
        pdf_gen_v2.cell(0, 10, pdf_safe_text_output(f"Diagnóstico Empresarial - {empresa_nome_pdf_g_v2}"), 0, 1, 'C')
        pdf_gen_v2.ln(5)

        pdf_gen_v2.set_font("Arial", size=10)
        pdf_gen_v2.multi_cell(0, 7, pdf_safe_text_output(f"Data do Diagnóstico: {diagnostico_data_pdf_v2.get('Data','N/D')}"))
        pdf_gen_v2.multi_cell(0, 7, pdf_safe_text_output(f"Empresa: {empresa_nome_pdf_g_v2} (CNPJ: {cnpj_pdf_g_v2})"))
        if nome_contato_pdf_g_v2: pdf_gen_v2.multi_cell(0, 7, pdf_safe_text_output(f"Contato: {nome_contato_pdf_g_v2}"))
        if telefone_pdf_g_v2: pdf_gen_v2.multi_cell(0, 7, pdf_safe_text_output(f"Telefone: {telefone_pdf_g_v2}"))
        pdf_gen_v2.ln(3)

        pdf_gen_v2.multi_cell(0, 7, pdf_safe_text_output(f"Média Geral (Numérica): {diagnostico_data_pdf_v2.get('Média Geral','N/A')}"))
        pdf_gen_v2.multi_cell(0, 7, pdf_safe_text_output(f"Média Scores GUT (G*U*T): {diagnostico_data_pdf_v2.get('GUT Média','N/A')}"))
        pdf_gen_v2.ln(3)

        if medias_categorias_pdf_v2:
            pdf_gen_v2.set_font("Arial", 'B', 11); pdf_gen_v2.multi_cell(0, 7, pdf_safe_text_output("Médias por Categoria (Perguntas de Pontuação):"))
            pdf_gen_v2.set_font("Arial", size=10)
            for cat_pdf_g_mc_v2, media_cat_pdf_g_mc_v2 in medias_categorias_pdf_v2.items(): 
                pdf_gen_v2.multi_cell(0, 6, pdf_safe_text_output(f"  - {cat_pdf_g_mc_v2}: {media_cat_pdf_g_mc_v2}"))
            pdf_gen_v2.ln(5)

        for titulo_pdf_g_v2, campo_dado_pdf_g_v2 in [("Resumo do Diagnóstico (Cliente):", "Diagnóstico"), 
                                  ("Análise/Observações do Cliente:", "Análise do Cliente"),
                                  ("Comentários do Consultor:", "Comentarios_Admin")]:
            valor_campo_pdf_g_v2 = diagnostico_data_pdf_v2.get(campo_dado_pdf_g_v2, "")
            if valor_campo_pdf_g_v2 and not pd.isna(valor_campo_pdf_g_v2): 
                pdf_gen_v2.set_font("Arial", 'B', 12); pdf_gen_v2.multi_cell(0, 7, pdf_safe_text_output(titulo_pdf_g_v2))
                pdf_gen_v2.set_font("Arial", size=10); pdf_gen_v2.multi_cell(0, 7, pdf_safe_text_output(str(valor_campo_pdf_g_v2))); pdf_gen_v2.ln(3)
            
        pdf_gen_v2.set_font("Arial", 'B', 12); pdf_gen_v2.multi_cell(0, 10, pdf_safe_text_output("Respostas Detalhadas por Categoria:"))
        categorias_unicas_pdf_g_v2 = []
        if perguntas_df_pdf_v2 is not None and "Categoria" in perguntas_df_pdf_v2.columns: 
            categorias_unicas_pdf_g_v2 = perguntas_df_pdf_v2["Categoria"].unique()
        
        for categoria_pdf_det_g_v2 in categorias_unicas_pdf_g_v2:
            pdf_gen_v2.set_font("Arial", 'B', 10); pdf_gen_v2.multi_cell(0, 7, pdf_safe_text_output(f"Categoria: {categoria_pdf_det_g_v2}"))
            pdf_gen_v2.set_font("Arial", size=9)
            perguntas_cat_pdf_det_g_v2 = perguntas_df_pdf_v2[perguntas_df_pdf_v2["Categoria"] == categoria_pdf_det_g_v2]
            for _, p_row_pdf_det_g_v2 in perguntas_cat_pdf_det_g_v2.iterrows():
                txt_p_pdf_det_g_v2 = p_row_pdf_det_g_v2["Pergunta"]
                resp_p_pdf_det_g_v2 = respostas_coletadas_pdf_v2.get(txt_p_pdf_det_g_v2) 
                if resp_p_pdf_det_g_v2 is None: 
                    resp_p_pdf_det_g_v2 = diagnostico_data_pdf_v2.get(txt_p_pdf_det_g_v2, "N/R")

                if isinstance(txt_p_pdf_det_g_v2, str) and "[Matriz GUT]" in txt_p_pdf_det_g_v2: 
                    g_pdf_v2, u_pdf_v2, t_pdf_v2 = 0,0,0 
                    score_gut_item_pdf_v2 = 0
                    if isinstance(resp_p_pdf_det_g_v2, dict): 
                        g_pdf_v2,u_pdf_v2,t_pdf_v2 = resp_p_pdf_det_g_v2.get("G",0), resp_p_pdf_det_g_v2.get("U",0), resp_p_pdf_det_g_v2.get("T",0)
                    elif isinstance(resp_p_pdf_det_g_v2, str): 
                        try: 
                            gut_data_pdf_v2 = json.loads(resp_p_pdf_det_g_v2.replace("'", "\""))
                            g_pdf_v2,u_pdf_v2,t_pdf_v2 = gut_data_pdf_v2.get("G",0), gut_data_pdf_v2.get("U",0), gut_data_pdf_v2.get("T",0)
                        except: pass 
                    score_gut_item_pdf_v2 = g_pdf_v2*u_pdf_v2*t_pdf_v2
                    pdf_gen_v2.multi_cell(0,6,pdf_safe_text_output(f"  - {txt_p_pdf_det_g_v2.replace(' [Matriz GUT]','')}: G={g_pdf_v2}, U={u_pdf_v2}, T={t_pdf_v2} (Score: {score_gut_item_pdf_v2})"))
                elif isinstance(resp_p_pdf_det_g_v2, (int, float, str)): 
                    pdf_gen_v2.multi_cell(0, 6, pdf_safe_text_output(f"  - {txt_p_pdf_det_g_v2}: {resp_p_pdf_det_g_v2}"))
            pdf_gen_v2.ln(2)
        pdf_gen_v2.ln(3)
        
        pdf_gen_v2.add_page(); pdf_gen_v2.set_font("Arial", 'B', 12)
        pdf_gen_v2.cell(0, 10, pdf_safe_text_output("Plano de Ação Sugerido (Kanban - GUT)"), 0, 1, 'C'); pdf_gen_v2.ln(5)
        pdf_gen_v2.set_font("Arial", size=10)
        gut_cards_pdf_g_list_v2 = [] 
        for pergunta_pdf_k_g_v2, resp_pdf_k_val_g_v2 in respostas_coletadas_pdf_v2.items(): 
            if isinstance(pergunta_pdf_k_g_v2, str) and "[Matriz GUT]" in pergunta_pdf_k_g_v2:
                g_k_g_v2, u_k_g_v2, t_k_g_v2 = 0,0,0 
                if isinstance(resp_pdf_k_val_g_v2, dict):
                    g_k_g_v2, u_k_g_v2, t_k_g_v2 = resp_pdf_k_val_g_v2.get("G",0), resp_pdf_k_val_g_v2.get("U",0), resp_pdf_k_val_g_v2.get("T",0)
                elif isinstance(resp_pdf_k_val_g_v2, str): 
                    try: 
                        gut_data_k_g_v2 = json.loads(resp_pdf_k_val_g_v2.replace("'", "\""))
                        g_k_g_v2,u_k_g_v2,t_k_g_v2 = gut_data_k_g_v2.get("G",0), gut_data_k_g_v2.get("U",0), gut_data_k_g_v2.get("T",0)
                    except: pass
                
                score_gut_total_k_pdf_g_v2 = g_k_g_v2 * u_k_g_v2 * t_k_g_v2
                prazo_k_pdf_g_v2 = "N/A"
                if score_gut_total_k_pdf_g_v2 >= 75: prazo_k_pdf_g_v2 = "15 dias"
                elif score_gut_total_k_pdf_g_v2 >= 40: prazo_k_pdf_g_v2 = "30 dias"
                elif score_gut_total_k_pdf_g_v2 >= 20: prazo_k_pdf_g_v2 = "45 dias"
                elif score_gut_total_k_pdf_g_v2 > 0: prazo_k_pdf_g_v2 = "60 dias"
                else: continue
                if prazo_k_pdf_g_v2 != "N/A":
                    gut_cards_pdf_g_list_v2.append({"Tarefa": pergunta_pdf_k_g_v2.replace(" [Matriz GUT]", ""),"Prazo": prazo_k_pdf_g_v2, "Score": score_gut_total_k_pdf_g_v2})
        if gut_cards_pdf_g_list_v2:
            gut_cards_pdf_g_sorted_v2 = sorted(gut_cards_pdf_g_list_v2, key=lambda x_g_pdf_v2: (int(x_g_pdf_v2["Prazo"].split(" ")[0]), -x_g_pdf_v2["Score"])) 
            for card_item_pdf_g_final_v2 in gut_cards_pdf_g_sorted_v2: 
                 pdf_gen_v2.multi_cell(0, 6, pdf_safe_text_output(f"Prazo: {card_item_pdf_g_final_v2['Prazo']} - Tarefa: {card_item_pdf_g_final_v2['Tarefa']} (Score GUT: {card_item_pdf_g_final_v2['Score']})"))
        else: pdf_gen_v2.multi_cell(0,6, pdf_safe_text_output("Nenhuma ação prioritária (GUT > 0) identificada."))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile_pdf_gerado_final_v2:
            pdf_path_gerado_final_v2 = tmpfile_pdf_gerado_final_v2.name
            pdf_gen_v2.output(pdf_path_gerado_final_v2)
        return pdf_path_gerado_final_v2
    except Exception as e_pdf_main_gerar_final_v2:
        st.error(f"Erro crítico ao gerar PDF: {e_pdf_main_gerar_final_v2}")
        st.exception(e_pdf_main_gerar_final_v2); return None

# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_cliente_rerun"): st.session_state.trigger_cliente_rerun = False; st.rerun()
if st.session_state.get("trigger_admin_rerun"): st.session_state.trigger_admin_rerun = False; st.rerun()

if not st.session_state.admin_logado and not st.session_state.cliente_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key="tipo_usuario_radio_vfinal_v2")
elif st.session_state.admin_logado: aba = "Administrador"
else: aba = "Cliente"

if aba == "Administrador" and not st.session_state.admin_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Administrador</h2>', unsafe_allow_html=True)
    with st.form("form_admin_login_vfinal_v2"): 
        usuario_admin_login = st.text_input("Usuário", key="admin_user_login_vfinal_v2") 
        senha_admin_login = st.text_input("Senha", type="password", key="admin_pass_login_vfinal_v2")
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
        except Exception as e_login_admin_vfinal_v2: st.error(f"Erro no login: {e_login_admin_vfinal_v2}"); st.exception(e_login_admin_vfinal_v2)
    st.markdown('</div>', unsafe_allow_html=True); st.stop()

if aba == "Cliente" and not st.session_state.cliente_logado:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-title">Login Cliente</h2>', unsafe_allow_html=True)
    with st.form("form_cliente_login_vfinal_v2"): 
        cnpj_cli_login = st.text_input("CNPJ", key="cli_cnpj_login_vfinal_v2") 
        senha_cli_login = st.text_input("Senha", type="password", key="cli_pass_login_vfinal_v2") 
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
        except FileNotFoundError as e_login_cli_fnf_vfinal_v2: st.error(f"Arquivo não encontrado: {e_login_cli_fnf_vfinal_v2.filename}.")
        except pd.errors.EmptyDataError as e_login_cli_empty_vfinal_v2: st.error(f"Arquivo de usuários ou bloqueados está vazio: {e_login_cli_empty_vfinal_v2}")
        except Exception as e_login_cli_vfinal_v2: st.error(f"Erro no login do cliente: {e_login_cli_vfinal_v2}"); st.exception(e_login_cli_vfinal_v2)
    st.markdown('</div>', unsafe_allow_html=True); st.stop() 


# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.cliente_logado:
    try:
        st.sidebar.markdown(f"### Bem-vindo(a), {st.session_state.user.get('Empresa', 'Cliente')}!")
        
        with st.sidebar.expander("Meu Perfil", expanded=False):
            logo_cliente_path = find_client_logo_path(st.session_state.cnpj)
            if logo_cliente_path:
                try: st.image(logo_cliente_path, width=100)
                except Exception as e_logo_display_cli: st.caption(f"Erro ao exibir logo: {e_logo_display_cli}")
            st.write(f"**Empresa:** {st.session_state.user.get('Empresa', 'N/D')}")
            st.write(f"**CNPJ:** {st.session_state.cnpj}")
            st.write(f"**Contato:** {st.session_state.user.get('NomeContato', 'N/D')}")
            st.write(f"**Telefone:** {st.session_state.user.get('Telefone', 'N/D')}")

        DIAGNOSTICO_FORM_ID_KEY_USER = f"form_id_diagnostico_cliente_{st.session_state.cnpj}"

        st.session_state.cliente_page = st.sidebar.radio(
            "Menu Cliente", ["Painel Principal", "Novo Diagnóstico"],
            index=["Painel Principal", "Novo Diagnóstico"].index(st.session_state.cliente_page),
            key="cliente_menu_radio_vfinal_v3"
        )
        if st.sidebar.button("⬅️ Sair do Portal Cliente"):
            keys_to_del_cli_logout_vfinal = ['cliente_logado', 'cnpj', 'user', 'inicio_sessao_cliente', 
                                           'diagnostico_enviado', 'cliente_page', DIAGNOSTICO_FORM_ID_KEY_USER]
            temp_resp_key_logout_vfinal = f"temp_respostas_{st.session_state.get(DIAGNOSTICO_FORM_ID_KEY_USER,'')}"
            if temp_resp_key_logout_vfinal in st.session_state:
                keys_to_del_cli_logout_vfinal.append(temp_resp_key_logout_vfinal)
            for key_cd_lo_vfinal in keys_to_del_cli_logout_vfinal:
                if key_cd_lo_vfinal in st.session_state: del st.session_state[key_cd_lo_vfinal]
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
            df_cliente_view_pp_vfinal = pd.DataFrame() 
            try:
                df_antigos_cli_pp_vfinal = pd.read_csv(arquivo_csv, encoding='utf-8')
                if not df_antigos_cli_pp_vfinal.empty:
                    df_cliente_view_pp_vfinal = df_antigos_cli_pp_vfinal[df_antigos_cli_pp_vfinal["CNPJ"].astype(str) == st.session_state.cnpj]
            except (FileNotFoundError, pd.errors.EmptyDataError): 
                pass # df_cliente_view_pp_vfinal já é um DataFrame vazio
            except Exception as e_read_diag_cli_vfinal:
                st.error(f"Erro ao ler diagnósticos do cliente: {e_read_diag_cli_vfinal}")
            
            if df_cliente_view_pp_vfinal.empty: 
                st.info("Nenhum diagnóstico anterior encontrado para você. Selecione 'Novo Diagnóstico' no menu para começar.")
            else:
                df_cliente_view_pp_vfinal = df_cliente_view_pp_vfinal.sort_values(by="Data", ascending=False)
                for idx_cv_pp_vfinal, row_cv_pp_vfinal in df_cliente_view_pp_vfinal.iterrows():
                    with st.expander(f"📅 {row_cv_pp_vfinal['Data']} - {row_cv_pp_vfinal['Empresa']}"):
                        cols_diag_cli_metrics_vfinal = st.columns(2)
                        with cols_diag_cli_metrics_vfinal[0]:
                            st.metric("Média Geral", f"{row_cv_pp_vfinal.get('Média Geral', 0.0):.2f}")
                        with cols_diag_cli_metrics_vfinal[1]:
                            st.metric("GUT Média (G*U*T)", f"{row_cv_pp_vfinal.get('GUT Média', 0.0):.2f}")
                        st.write(f"**Resumo (Cliente):** {row_cv_pp_vfinal.get('Diagnóstico', 'N/P')}")
                        st.markdown("**Médias por Categoria:**")
                        found_cat_media_cv_vfinal = False
                        cat_cols_display_vfinal = [col for col in row_cv_pp_vfinal.index if str(col).startswith("Media_Cat_")]
                        if cat_cols_display_vfinal:
                            num_cat_cols_display_vfinal = len(cat_cols_display_vfinal)
                            max_cols_per_row = 4 
                            display_cols_metrics_vfinal = st.columns(min(num_cat_cols_display_vfinal, max_cols_per_row))
                            col_idx_display_vfinal = 0
                            for col_name_cv_display_vfinal in cat_cols_display_vfinal:
                                cat_name_display_cv_vfinal = col_name_cv_display_vfinal.replace("Media_Cat_", "").replace("_", " ")
                                current_col_obj = display_cols_metrics_vfinal[col_idx_display_vfinal % min(num_cat_cols_display_vfinal, max_cols_per_row)]
                                current_col_obj.metric(f"Média {cat_name_display_cv_vfinal}", f"{row_cv_pp_vfinal.get(col_name_cv_display_vfinal, 0.0):.2f}")
                                col_idx_display_vfinal += 1
                                found_cat_media_cv_vfinal = True
                        if not found_cat_media_cv_vfinal: st.caption("  Nenhuma média por categoria.")

                        analise_cli_val_cv_vfinal = row_cv_pp_vfinal.get("Análise do Cliente", "")
                        analise_cli_cv_vfinal = st.text_area("🧠 Minha Análise sobre este Diagnóstico:", value=analise_cli_val_cv_vfinal, key=f"analise_cv_vfinal_{row_cv_pp_vfinal.name}")
                        if st.button("💾 Salvar Minha Análise", key=f"salvar_analise_cv_vfinal_{row_cv_pp_vfinal.name}"):
                            try:
                                df_antigos_upd_cv_vfinal = pd.read_csv(arquivo_csv, encoding='utf-8') 
                                df_antigos_upd_cv_vfinal.loc[row_cv_pp_vfinal.name, "Análise do Cliente"] = analise_cli_cv_vfinal 
                                df_antigos_upd_cv_vfinal.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                registrar_acao(st.session_state.cnpj, "Análise Cliente", f"Editou análise de {row_cv_pp_vfinal['Data']}")
                                st.success("Análise salva!"); st.rerun()
                            except Exception as e_save_analise_vfinal: st.error(f"Erro ao salvar análise: {e_save_analise_vfinal}")
                        
                        com_admin_val_cv_vfinal = row_cv_pp_vfinal.get("Comentarios_Admin", "")
                        if com_admin_val_cv_vfinal and not pd.isna(com_admin_val_cv_vfinal):
                            st.markdown("**Comentários do Consultor:**"); st.info(f"{com_admin_val_cv_vfinal}")
                        else: st.caption("Nenhum comentário do consultor.")
                        st.markdown("---")
                
                st.subheader("📌 Plano de Ação - Kanban (Baseado no Último Diagnóstico)")
                gut_cards_painel_vfinal = []
                if not df_cliente_view_pp_vfinal.empty:
                    latest_diag_row_painel_vfinal = df_cliente_view_pp_vfinal.iloc[0]
                    for pergunta_p_vfinal, resposta_p_val_str_vfinal in latest_diag_row_painel_vfinal.items():
                        if isinstance(pergunta_p_vfinal, str) and "[Matriz GUT]" in pergunta_p_vfinal:
                            try:
                                if pd.notna(resposta_p_val_str_vfinal) and isinstance(resposta_p_val_str_vfinal, str):
                                    gut_data_vfinal = json.loads(resposta_p_val_str_vfinal.replace("'", "\"")) 
                                    g_vfinal = int(gut_data_vfinal.get("G", 0)); u_vfinal = int(gut_data_vfinal.get("U", 0)); t_vfinal = int(gut_data_vfinal.get("T", 0))
                                    score_gut_total_p_vfinal = g_vfinal * u_vfinal * t_vfinal
                                    prazo_p_vfinal = "N/A"
                                    if score_gut_total_p_vfinal >= 75: prazo_p_vfinal = "15 dias"
                                    elif score_gut_total_p_vfinal >= 40: prazo_p_vfinal = "30 dias"
                                    elif score_gut_total_p_vfinal >= 20: prazo_p_vfinal = "45 dias"
                                    elif score_gut_total_p_vfinal > 0: prazo_p_vfinal = "60 dias"
                                    else: continue 
                                    if prazo_p_vfinal != "N/A":
                                        gut_cards_painel_vfinal.append({"Tarefa": pergunta_p_vfinal.replace(" [Matriz GUT]", ""), "Prazo": prazo_p_vfinal, "Score": score_gut_total_p_vfinal, "Responsável": st.session_state.user.get("Empresa", "N/D")})
                            except (json.JSONDecodeError, ValueError, TypeError) as e_k_pp_vfinal: st.warning(f"Erro processar GUT Kanban: '{pergunta_p_vfinal}'. Erro: {e_k_pp_vfinal}")
                
                if gut_cards_painel_vfinal:
                    gut_cards_sorted_p_vfinal = sorted(gut_cards_painel_vfinal, key=lambda x_vfinal: x_vfinal["Score"], reverse=True)
                    prazos_def_p_vfinal = sorted(list(set(card_vfinal["Prazo"] for card_vfinal in gut_cards_sorted_p_vfinal)), key=lambda x_d_vfinal: int(x_d_vfinal.split(" ")[0])) 
                    if prazos_def_p_vfinal:
                        cols_kanban_p_vfinal = st.columns(len(prazos_def_p_vfinal))
                        for idx_kp_vfinal, prazo_col_kp_vfinal in enumerate(prazos_def_p_vfinal):
                            with cols_kanban_p_vfinal[idx_kp_vfinal]:
                                st.markdown(f"#### ⏱️ {prazo_col_kp_vfinal}")
                                for card_item_kp_vfinal in gut_cards_sorted_p_vfinal:
                                    if card_item_kp_vfinal["Prazo"] == prazo_col_kp_vfinal:
                                        st.markdown(f"""<div class="custom-card"><b>{card_item_kp_vfinal['Tarefa']}</b> (Score GUT: {card_item_kp_vfinal['Score']})<br><small><i>👤 {card_item_kp_vfinal['Responsável']}</i></small></div>""", unsafe_allow_html=True)
                else: st.info("Nenhuma ação prioritária para o Kanban (GUT).")
                
                st.subheader("📈 Comparativo de Evolução")
                if len(df_cliente_view_pp_vfinal) > 1:
                    grafico_comp_ev_vfinal = df_cliente_view_pp_vfinal.sort_values(by="Data")
                    grafico_comp_ev_vfinal["Data"] = pd.to_datetime(grafico_comp_ev_vfinal["Data"])
                    colunas_plot_comp_vfinal = ['Média Geral', 'GUT Média'] 
                    for col_g_comp_vfinal in grafico_comp_ev_vfinal.columns:
                        if str(col_g_comp_vfinal).startswith("Media_Cat_") and pd.api.types.is_numeric_dtype(grafico_comp_ev_vfinal[col_g_comp_vfinal]):
                            colunas_plot_comp_vfinal.append(col_g_comp_vfinal)
                    for col_plot_c_vfinal in colunas_plot_comp_vfinal:
                        if col_plot_c_vfinal in grafico_comp_ev_vfinal.columns: grafico_comp_ev_vfinal[col_plot_c_vfinal] = pd.to_numeric(grafico_comp_ev_vfinal[col_plot_c_vfinal], errors='coerce')
                    
                    colunas_validas_plot_vfinal = [c_vfinal for c_vfinal in colunas_plot_comp_vfinal if c_vfinal in grafico_comp_ev_vfinal.columns and pd.api.types.is_numeric_dtype(grafico_comp_ev_vfinal[c_vfinal])]
                    if colunas_validas_plot_vfinal:
                        st.line_chart(grafico_comp_ev_vfinal.set_index("Data")[colunas_validas_plot_vfinal].dropna(axis=1, how='all'))
                    
                    st.subheader("📊 Comparação Entre Diagnósticos") 
                    opcoes_cli_vfinal = grafico_comp_ev_vfinal["Data"].astype(str).tolist()
                    if len(opcoes_cli_vfinal) >= 2:
                        diag_atual_idx_vfinal, diag_anterior_idx_vfinal = len(opcoes_cli_vfinal)-1, len(opcoes_cli_vfinal)-2
                        diag_atual_sel_cli_vfinal = st.selectbox("Diagnóstico mais recente:", opcoes_cli_vfinal, index=diag_atual_idx_vfinal, key="diag_atual_sel_cli_vfinal")
                        diag_anterior_sel_cli_vfinal = st.selectbox("Diagnóstico anterior:", opcoes_cli_vfinal, index=diag_anterior_idx_vfinal, key="diag_anterior_sel_cli_vfinal")
                        atual_cli_vfinal = grafico_comp_ev_vfinal[grafico_comp_ev_vfinal["Data"].astype(str) == diag_atual_sel_cli_vfinal].iloc[0]
                        anterior_cli_vfinal = grafico_comp_ev_vfinal[grafico_comp_ev_vfinal["Data"].astype(str) == diag_anterior_sel_cli_vfinal].iloc[0]
                        st.write(f"### 📅 Comparando {diag_anterior_sel_cli_vfinal.split(' ')[0]} ⟶ {diag_atual_sel_cli_vfinal.split(' ')[0]}")
                        cols_excluir_comp_vfinal = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
                        variaveis_comp_vfinal = [col_f_vfinal for col_f_vfinal in grafico_comp_ev_vfinal.columns if col_f_vfinal not in cols_excluir_comp_vfinal and pd.api.types.is_numeric_dtype(grafico_comp_ev_vfinal[col_f_vfinal])]
                        if variaveis_comp_vfinal:
                            comp_data_vfinal = []
                            for v_comp_vfinal in variaveis_comp_vfinal:
                                val_ant_c_vfinal = pd.to_numeric(anterior_cli_vfinal.get(v_comp_vfinal), errors='coerce')
                                val_atu_c_vfinal = pd.to_numeric(atual_cli_vfinal.get(v_comp_vfinal), errors='coerce')
                                evolucao_c_vfinal = "➖ Igual"
                                if pd.notna(val_ant_c_vfinal) and pd.notna(val_atu_c_vfinal):
                                    if val_atu_c_vfinal > val_ant_c_vfinal: evolucao_c_vfinal = "🔼 Melhorou"
                                    elif val_atu_c_vfinal < val_ant_c_vfinal: evolucao_c_vfinal = "🔽 Piorou"
                                display_name_comp_vfinal = v_comp_vfinal.replace("Media_Cat_", "Média ").replace("_", " ")
                                if "[Pontuação (0-10)]" in display_name_comp_vfinal or "[Pontuação (0-5) + Matriz GUT]" in display_name_comp_vfinal or "[Matriz GUT]" in display_name_comp_vfinal:
                                    display_name_comp_vfinal = display_name_comp_vfinal.split(" [")[0] 
                                comp_data_vfinal.append({"Indicador": display_name_comp_vfinal, "Anterior": val_ant_c_vfinal if pd.notna(val_ant_c_vfinal) else "N/A", "Atual": val_atu_c_vfinal if pd.notna(val_atu_c_vfinal) else "N/A", "Evolução": evolucao_c_vfinal})
                            st.dataframe(pd.DataFrame(comp_data_vfinal))
                        else: st.info("Sem dados numéricos para comparação.")
                    else: st.info("Pelo menos dois diagnósticos para comparação.")
                else: st.info("Pelo menos dois diagnósticos para comparativos.")

        elif st.session_state.cliente_page == "Novo Diagnóstico":
            st.subheader("📋 Formulário de Novo Diagnóstico")
            
            DIAGNOSTICO_FORM_ID_KEY_USER = f"form_id_diagnostico_cliente_{st.session_state.cnpj}" 
            if DIAGNOSTICO_FORM_ID_KEY_USER not in st.session_state:
                st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER] = datetime.now().strftime("%Y%m%d%H%M%S%f")
            form_id_sufixo_nd_vfinal = st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER] # Renomeado

            temp_respostas_key_nd_vfinal = f"temp_respostas_{form_id_sufixo_nd_vfinal}" # Renomeado
            if temp_respostas_key_nd_vfinal not in st.session_state:
                st.session_state[temp_respostas_key_nd_vfinal] = {}
            
            respostas_form_coletadas_nd_vfinal = st.session_state[temp_respostas_key_nd_vfinal] # Renomeado
            
            try:
                perguntas_df_diag_vfinal = pd.read_csv(perguntas_csv, encoding='utf-8') # Renomeado
                if "Categoria" not in perguntas_df_diag_vfinal.columns: 
                    perguntas_df_diag_vfinal["Categoria"] = "Geral"
            except (FileNotFoundError, pd.errors.EmptyDataError): 
                st.error(f"Arquivo de perguntas ({perguntas_csv}) não encontrado ou vazio."); st.stop()
            
            if perguntas_df_diag_vfinal.empty: 
                st.warning("Nenhuma pergunta cadastrada."); st.stop()
            
            total_perguntas_diag_vfinal = len(perguntas_df_diag_vfinal) # Renomeado
            respondidas_count_diag_vfinal = 0  # Renomeado
            
            if "Categoria" not in perguntas_df_diag_vfinal.columns: 
                st.error("Coluna 'Categoria' não encontrada no arquivo de perguntas."); st.stop()

            categorias_unicas_diag_vfinal = perguntas_df_diag_vfinal["Categoria"].unique() # Renomeado
            
            with st.form(key=f"diagnostico_form_completo_{form_id_sufixo_nd_vfinal}"):
                if total_perguntas_diag_vfinal == 0:
                    st.warning("Nenhuma pergunta disponível.")
                else:
                    for categoria_diag_vfinal in categorias_unicas_diag_vfinal: # Renomeado
                        st.markdown(f"#### Categoria: {categoria_diag_vfinal}")
                        perguntas_cat_diag_vfinal = perguntas_df_diag_vfinal[perguntas_df_diag_vfinal["Categoria"] == categoria_diag_vfinal] # Renomeado
                        
                        if perguntas_cat_diag_vfinal.empty: continue

                        for idx_diag_f_vfinal, row_diag_f_vfinal in perguntas_cat_diag_vfinal.iterrows(): # Renomeado
                            texto_pergunta_diag_vfinal = str(row_diag_f_vfinal["Pergunta"])  # Renomeado
                            widget_base_key_vfinal = f"q_form_vfinal_{idx_diag_f_vfinal}" # Renomeado

                            if "[Matriz GUT]" in texto_pergunta_diag_vfinal:
                                st.markdown(f"**{texto_pergunta_diag_vfinal.replace(' [Matriz GUT]', '')}**")
                                cols_gut_vfinal = st.columns(3) # Renomeado
                                gut_current_vals_vfinal = respostas_form_coletadas_nd_vfinal.get(texto_pergunta_diag_vfinal, {"G":0, "U":0, "T":0}) # Renomeado
                                with cols_gut_vfinal[0]: g_val_vfinal = st.slider("Gravidade (0-5)", 0, 5, value=int(gut_current_vals_vfinal.get("G",0)), key=f"{widget_base_key_vfinal}_G") # Renomeado
                                with cols_gut_vfinal[1]: u_val_vfinal = st.slider("Urgência (0-5)", 0, 5, value=int(gut_current_vals_vfinal.get("U",0)), key=f"{widget_base_key_vfinal}_U") # Renomeado
                                with cols_gut_vfinal[2]: t_val_vfinal = st.slider("Tendência (0-5)", 0, 5, value=int(gut_current_vals_vfinal.get("T",0)), key=f"{widget_base_key_vfinal}_T") # Renomeado
                                respostas_form_coletadas_nd_vfinal[texto_pergunta_diag_vfinal] = {"G": g_val_vfinal, "U": u_val_vfinal, "T": t_val_vfinal}
                                if g_val_vfinal > 0 or u_val_vfinal > 0 or t_val_vfinal > 0 : respondidas_count_diag_vfinal +=1
                            elif "Pontuação (0-5)" in texto_pergunta_diag_vfinal: 
                                val_vfinal = respostas_form_coletadas_nd_vfinal.get(texto_pergunta_diag_vfinal, 0) # Renomeado
                                respostas_form_coletadas_nd_vfinal[texto_pergunta_diag_vfinal] = st.slider(texto_pergunta_diag_vfinal, 0, 5, value=int(val_vfinal), key=widget_base_key_vfinal) 
                                if respostas_form_coletadas_nd_vfinal[texto_pergunta_diag_vfinal] != 0: respondidas_count_diag_vfinal += 1
                            elif "Pontuação (0-10)" in texto_pergunta_diag_vfinal:
                                val_vfinal = respostas_form_coletadas_nd_vfinal.get(texto_pergunta_diag_vfinal, 0)
                                respostas_form_coletadas_nd_vfinal[texto_pergunta_diag_vfinal] = st.slider(texto_pergunta_diag_vfinal, 0, 10, value=int(val_vfinal), key=widget_base_key_vfinal)
                                if respostas_form_coletadas_nd_vfinal[texto_pergunta_diag_vfinal] != 0: respondidas_count_diag_vfinal += 1
                            elif "Texto Aberto" in texto_pergunta_diag_vfinal:
                                val_vfinal = respostas_form_coletadas_nd_vfinal.get(texto_pergunta_diag_vfinal, "")
                                respostas_form_coletadas_nd_vfinal[texto_pergunta_diag_vfinal] = st.text_area(texto_pergunta_diag_vfinal, value=str(val_vfinal), key=widget_base_key_vfinal)
                                if respostas_form_coletadas_nd_vfinal[texto_pergunta_diag_vfinal].strip() != "": respondidas_count_diag_vfinal += 1
                            elif "Escala" in texto_pergunta_diag_vfinal: 
                                opcoes_escala_diag_vfinal = ["Selecione", "Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"] # Renomeado
                                val_vfinal = respostas_form_coletadas_nd_vfinal.get(texto_pergunta_diag_vfinal, "Selecione")
                                idx_sel_vfinal = opcoes_escala_diag_vfinal.index(val_vfinal) if val_vfinal in opcoes_escala_diag_vfinal else 0 # Renomeado
                                respostas_form_coletadas_nd_vfinal[texto_pergunta_diag_vfinal] = st.selectbox(texto_pergunta_diag_vfinal, opcoes_escala_diag_vfinal, index=idx_sel_vfinal, key=widget_base_key_vfinal)
                                if respostas_form_coletadas_nd_vfinal[texto_pergunta_diag_vfinal] != "Selecione": respondidas_count_diag_vfinal += 1
                            else: 
                                val_vfinal = respostas_form_coletadas_nd_vfinal.get(texto_pergunta_diag_vfinal, 0)
                                respostas_form_coletadas_nd_vfinal[texto_pergunta_diag_vfinal] = st.slider(texto_pergunta_diag_vfinal, 0, 10, value=int(val_vfinal), key=widget_base_key_vfinal)
                                if respostas_form_coletadas_nd_vfinal[texto_pergunta_diag_vfinal] != 0: respondidas_count_diag_vfinal += 1
                        st.divider()
                
                progresso_diag_vfinal = round((respondidas_count_diag_vfinal / total_perguntas_diag_vfinal) * 100) if total_perguntas_diag_vfinal > 0 else 0
                st.info(f"📊 Progresso: {respondidas_count_diag_vfinal} de {total_perguntas_diag_vfinal} respondidas ({progresso_diag_vfinal}%)")
                
                obs_cli_diag_form_vfinal = st.text_area("Sua Análise/Observações (opcional):", value=respostas_form_coletadas_nd_vfinal.get("__obs_cliente__", ""), key=f"obs_cli_diag_vfinal_{form_id_sufixo_nd_vfinal}")
                respostas_form_coletadas_nd_vfinal["__obs_cliente__"] = obs_cli_diag_form_vfinal
                
                diag_resumo_cli_diag_vfinal = st.text_area("✍️ Resumo/principais insights (para PDF):", value=respostas_form_coletadas_nd_vfinal.get("__resumo_cliente__", ""), key=f"diag_resumo_diag_vfinal_{form_id_sufixo_nd_vfinal}")
                respostas_form_coletadas_nd_vfinal["__resumo_cliente__"] = diag_resumo_cli_diag_vfinal

                enviar_diagnostico_btn_vfinal = st.form_submit_button("✔️ Enviar Diagnóstico")

            if enviar_diagnostico_btn_vfinal:
                if respondidas_count_diag_vfinal < total_perguntas_diag_vfinal: st.warning("Responda todas as perguntas.")
                elif not respostas_form_coletadas_nd_vfinal["__resumo_cliente__"].strip(): st.error("O campo 'Resumo/principais insights (para PDF)' é obrigatório.")
                else:
                    soma_total_gut_scores_vfinal, count_gut_perguntas_vfinal = 0, 0
                    respostas_finais_para_salvar_vfinal = {}

                    for pergunta_env_vfinal, resposta_env_vfinal in respostas_form_coletadas_nd_vfinal.items():
                        if pergunta_env_vfinal.startswith("__"): continue 
                        if isinstance(pergunta_env_vfinal, str) and "[Matriz GUT]" in pergunta_env_vfinal and isinstance(resposta_env_vfinal, dict):
                            respostas_finais_para_salvar_vfinal[pergunta_env_vfinal] = json.dumps(resposta_env_vfinal) 
                            g_f_vfinal, u_f_vfinal, t_f_vfinal = resposta_env_final.get("G",0), resposta_env_final.get("U",0), resposta_env_final.get("T",0) # Corrigido para resposta_env_final
                            soma_total_gut_scores_vfinal += (g_f_vfinal * u_f_vfinal * t_f_vfinal)
                            count_gut_perguntas_vfinal +=1
                        else:
                            respostas_finais_para_salvar_vfinal[pergunta_env_vfinal] = resposta_env_vfinal

                    gut_media_calc_vfinal = round(soma_total_gut_scores_vfinal / count_gut_perguntas_vfinal, 2) if count_gut_perguntas_vfinal > 0 else 0.0
                    numeric_resp_calc_vfinal = [v_f_vfinal for k_f_vfinal, v_f_vfinal in respostas_finais_para_salvar_vfinal.items() if isinstance(v_f_vfinal, (int, float)) and ("Pontuação (0-10)" in k_f_vfinal or "Pontuação (0-5)" in k_f_vfinal)] 
                    media_geral_calc_final_val_vfinal = round(sum(numeric_resp_calc_vfinal) / len(numeric_resp_calc_vfinal), 2) if numeric_resp_calc_vfinal else 0.0
                    empresa_nome_final_val_vfinal = st.session_state.user.get("Empresa", "N/D")
                    
                    nova_linha_final_val_vfinal = {
                        "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": st.session_state.cnpj,
                        "Nome": st.session_state.user.get("CNPJ", ""), "Email": "", "Empresa": empresa_nome_final_val_vfinal,
                        "Média Geral": media_geral_calc_final_val_vfinal, "GUT Média": gut_media_calc_vfinal, 
                        "Observações": "", 
                        "Análise do Cliente": respostas_form_coletadas_nd_vfinal.get("__obs_cliente__",""), 
                        "Diagnóstico": respostas_form_coletadas_nd_vfinal.get("__resumo_cliente__",""), 
                        "Comentarios_Admin": ""
                    }
                    nova_linha_final_val_vfinal.update(respostas_finais_para_salvar_vfinal)

                    medias_por_categoria_final_val_vfinal = {}
                    for cat_final_calc_val_vfinal in categorias_unicas_diag_vfinal:
                        perguntas_cat_final_df_val_vfinal = perguntas_df_diag_vfinal[perguntas_df_diag_vfinal["Categoria"] == cat_final_calc_val_vfinal]
                        soma_cat_final_val_vfinal, cont_num_cat_final_val_vfinal = 0, 0
                        for _, p_row_final_val_vfinal in perguntas_cat_final_df_val_vfinal.iterrows():
                            txt_p_final_val_vfinal = p_row_final_val_vfinal["Pergunta"]
                            resp_p_final_val_vfinal = respostas_form_coletadas_nd_vfinal.get(txt_p_final_val_vfinal)
                            if isinstance(resp_p_final_val_vfinal, (int, float)) and \
                               (isinstance(txt_p_final_val_vfinal, str) and "[Matriz GUT]" not in txt_p_final_val_vfinal) and \
                               (isinstance(txt_p_final_val_vfinal, str) and ("Pontuação (0-10)" in txt_p_final_val_vfinal or "Pontuação (0-5)" in txt_p_final_val_vfinal)):
                                soma_cat_final_val_vfinal += resp_p_final_val_vfinal
                                cont_num_cat_final_val_vfinal += 1
                        media_c_final_val_vfinal = round(soma_cat_final_val_vfinal / cont_num_cat_final_val_vfinal, 2) if cont_num_cat_final_val_vfinal > 0 else 0.0
                        nome_col_media_cat_final_val_vfinal = f"Media_Cat_{sanitize_column_name(cat_final_calc_val_vfinal)}"
                        nova_linha_final_val_vfinal[nome_col_media_cat_final_val_vfinal] = media_c_final_val_vfinal
                        medias_por_categoria_final_val_vfinal[cat_final_calc_val_vfinal] = media_c_final_val_vfinal

                    try: df_diag_todos_final_val_vfinal = pd.read_csv(arquivo_csv, encoding='utf-8')
                    except (FileNotFoundError, pd.errors.EmptyDataError): df_diag_todos_final_val_vfinal = pd.DataFrame() 
                    
                    for col_f_save_final_val_vfinal in nova_linha_final_val_vfinal.keys(): 
                        if col_f_save_final_val_vfinal not in df_diag_todos_final_val_vfinal.columns: df_diag_todos_final_val_vfinal[col_f_save_final_val_vfinal] = pd.NA 
                    df_diag_todos_final_val_vfinal = pd.concat([df_diag_todos_final_val_vfinal, pd.DataFrame([nova_linha_final_val_vfinal])], ignore_index=True)
                    df_diag_todos_final_val_vfinal.to_csv(arquivo_csv, index=False, encoding='utf-8')
                    
                    st.success("Diagnóstico enviado com sucesso!")
                    registrar_acao(st.session_state.cnpj, "Envio Diagnóstico", "Cliente enviou novo diagnóstico.")
                    
                    pdf_path_final_val_vfinal = gerar_pdf_diagnostico_completo(
                        diagnostico_data=nova_linha_final_val_vfinal, 
                        usuario_data=st.session_state.user, 
                        perguntas_df_geracao=perguntas_df_diag_vfinal, 
                        respostas_coletadas_geracao=respostas_form_coletadas_nd_vfinal,
                        medias_categorias_geracao=medias_por_categoria_final_val_vfinal
                    )
                    if pdf_path_final_val_vfinal:
                        with open(pdf_path_final_val_vfinal, "rb") as f_pdf_final_val_vfinal:
                            st.download_button(label="📄 Baixar PDF do Diagnóstico", data=f_pdf_final_val_vfinal, 
                                           file_name=f"diagnostico_{sanitize_column_name(empresa_nome_final_val_vfinal)}_{datetime.now().strftime('%Y%m%d')}.pdf", 
                                           mime="application/pdf", key="download_pdf_cliente_final_vfinal")
                        registrar_acao(st.session_state.cnpj, "Download PDF", "Baixou PDF do novo diagnóstico.")
                    
                    if DIAGNOSTICO_FORM_ID_KEY_USER in st.session_state: del st.session_state[DIAGNOSTICO_FORM_ID_KEY_USER]
                    if temp_respostas_key_nd_vfinal in st.session_state: del st.session_state[temp_respostas_key_nd_vfinal]
                    
                    st.session_state.diagnostico_enviado = True
                    st.session_state.cliente_page = "Painel Principal" 
                    st.rerun()
    except Exception as e_cliente_area_vfinal_v2:
        st.error(f"Ocorreu um erro na área do cliente: {e_cliente_area_vfinal_v2}")
        st.exception(e_cliente_area_vfinal_v2) 


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
        key="admin_menu_selectbox_vfinal_v3" 
    )
    st.header(f"🔑 Painel Admin: {menu_admin}")

    try: 
        if menu_admin == "Visão Geral e Diagnósticos":
            st.subheader("📊 Visão Geral dos Diagnósticos")
            # DEBUG: Adicionar uma mensagem simples para ver se esta seção é alcançada
            # st.write("DEBUG: Admin - Carregando Visão Geral e Diagnósticos...")

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
            except Exception as e_load_diag_admin_vg_vfinal_v2:
                st.error(f"ERRO AO CARREGAR DIAGNÓSTICOS (Visão Geral): {e_load_diag_admin_vg_vfinal_v2}")
                st.exception(e_load_diag_admin_vg_vfinal_v2)
            
            if admin_data_loaded and not diagnosticos_df_admin.empty:
                # st.write("DEBUG: Admin - Dados carregados para Visão Geral. Renderizando...") # DEBUG opcional
                empresas_disponiveis_vg = ["Todos os Clientes"] + sorted(diagnosticos_df_admin["Empresa"].astype(str).unique().tolist())
                empresa_selecionada_vg = st.selectbox(
                    "Filtrar Visão Geral por Empresa:", 
                    empresas_disponiveis_vg, 
                    key="admin_visao_geral_filtro_empresa_vfinal_v2"
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
                        st.download_button("⬇️ Exportar Todos os Diagnósticos (CSV)", csv_export_admin_vg, file_name=f"diagnosticos_completos.csv", mime="text/csv", key="download_todos_csv_admin_vfinal")
                    st.divider()
                    
                    st.markdown("#### Detalhar, Comentar e Baixar PDF de Diagnóstico Específico")
                    empresas_detalhe_vg = sorted(df_filtrado_vg["Empresa"].astype(str).unique().tolist())
                    if not empresas_detalhe_vg:
                        st.info("Nenhuma empresa na seleção atual para detalhar.")
                    else:
                        default_empresa_detalhe_idx_vg = 0
                        if empresa_selecionada_vg != "Todos os Clientes" and empresa_selecionada_vg in empresas_detalhe_vg:
                            default_empresa_detalhe_idx_vg = empresas_detalhe_vg.index(empresa_selecionada_vg)

                        empresa_selecionada_detalhe_vg = st.selectbox("Selecione uma Empresa para Detalhar:", empresas_detalhe_vg, index=default_empresa_detalhe_idx_vg, key="admin_empresa_filter_detail_vfinal")
                        
                        diagnosticos_empresa_detalhe_vg = df_filtrado_vg[df_filtrado_vg["Empresa"] == empresa_selecionada_detalhe_vg].sort_values(by="Data", ascending=False)
                        if not diagnosticos_empresa_detalhe_vg.empty:
                            datas_diagnosticos_detalhe_vg = ["Selecione Data..."] + diagnosticos_empresa_detalhe_vg["Data"].tolist()
                            diagnostico_data_selecionada_detalhe_vg = st.selectbox("Selecione a Data do Diagnóstico:", datas_diagnosticos_detalhe_vg, key="admin_data_diagnostico_select_vfinal")
                            if diagnostico_data_selecionada_detalhe_vg != "Selecione Data...":
                                diagnostico_selecionado_adm_row_vg = diagnosticos_empresa_detalhe_vg[diagnosticos_empresa_detalhe_vg["Data"] == diagnostico_data_selecionada_detalhe_vg].iloc[0]
                                
                                st.markdown(f"**Detalhes do Diagnóstico de {diagnostico_selecionado_adm_row_vg['Data']}**")
                                st.write(f"**Média Geral:** {diagnostico_selecionado_adm_row_vg.get('Média Geral', 'N/A')} | **GUT Média (G*U*T):** {diagnostico_selecionado_adm_row_vg.get('GUT Média', 'N/A')}")
                                
                                comentario_adm_atual_val_vg = diagnostico_selecionado_adm_row_vg.get("Comentarios_Admin", "")
                                if pd.isna(comentario_adm_atual_val_vg): comentario_adm_atual_val_vg = ""
                                novo_comentario_adm_val_vg = st.text_area("Comentários do Consultor/Admin:", value=comentario_adm_atual_val_vg, key=f"admin_comment_detail_vfinal_{diagnostico_selecionado_adm_row_vg.name}")
                                if st.button("💾 Salvar Comentário", key=f"save_admin_comment_detail_vfinal_{diagnostico_selecionado_adm_row_vg.name}"):
                                    df_diag_save_com_adm_det_vg = pd.read_csv(arquivo_csv, encoding='utf-8')
                                    df_diag_save_com_adm_det_vg.loc[diagnostico_selecionado_adm_row_vg.name, "Comentarios_Admin"] = novo_comentario_adm_val_vg
                                    df_diag_save_com_adm_det_vg.to_csv(arquivo_csv, index=False, encoding='utf-8')
                                    registrar_acao("ADMIN", "Comentário Admin", f"Admin comentou diag. de {diagnostico_selecionado_adm_row_vg['Data']} para {empresa_selecionada_detalhe_vg}")
                                    st.success("Comentário salvo!"); st.rerun()

                                if st.button("📄 Baixar PDF deste Diagnóstico", key=f"download_pdf_admin_vfinal_{diagnostico_selecionado_adm_row_vg.name}"):
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
                                                           mime="application/pdf", key=f"confirm_dl_pdf_admin_vfinal_{diagnostico_selecionado_adm_row_vg.name}")
                                        registrar_acao("ADMIN", "Download PDF Cliente", f"Admin baixou PDF de {diagnostico_selecionado_adm_row_vg['Data']} para {empresa_selecionada_detalhe_vg}")
                                    else: st.error("Falha ao gerar o PDF para download.")
                        else: st.info(f"Nenhum diagnóstico para a empresa {empresa_selecionada_detalhe_vg}.")
            else: 
                st.warning("AVISO: Nenhum dado de diagnóstico carregado. A 'Visão Geral' está limitada.")
        
        elif menu_admin == "Histórico de Usuários":
            st.subheader("📜 Histórico de Ações dos Clientes")
            try:
                historico_df = pd.read_csv(historico_csv, encoding='utf-8')
                if not historico_df.empty:
                    st.dataframe(historico_df.sort_values(by="Data", ascending=False))
                else: st.info("Nenhum histórico de ações encontrado.")
            except (FileNotFoundError, pd.errors.EmptyDataError): st.info("Arquivo de histórico não encontrado ou vazio.")
            except Exception as e_hist_vfinal: st.error(f"Erro ao carregar histórico: {e_hist_vfinal}")

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
                            nova_p_text_admin = st.text_input("Pergunta", value=str(row_p_admin["Pergunta"]), key=f"edit_p_txt_vfinal_{i_p_admin}")
                        with cols_p_admin[1]:
                            nova_cat_text_admin = st.text_input("Categoria", value=str(row_p_admin.get("Categoria", "Geral")), key=f"edit_p_cat_vfinal_{i_p_admin}")
                        with cols_p_admin[2]:
                            st.write("") 
                            if st.button("💾", key=f"salvar_p_adm_vfinal_{i_p_admin}", help="Salvar"):
                                perguntas_df_admin_edit.loc[i_p_admin, "Pergunta"] = nova_p_text_admin 
                                perguntas_df_admin_edit.loc[i_p_admin, "Categoria"] = nova_cat_text_admin
                                perguntas_df_admin_edit.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                st.success(f"Pergunta {i_p_admin+1} atualizada."); st.rerun()
                        with cols_p_admin[3]:
                            st.write("") 
                            if st.button("🗑️", key=f"deletar_p_adm_vfinal_{i_p_admin}", help="Deletar"):
                                perguntas_df_admin_edit = perguntas_df_admin_edit.drop(i_p_admin).reset_index(drop=True)
                                perguntas_df_admin_edit.to_csv(perguntas_csv, index=False, encoding='utf-8')
                                st.warning(f"Pergunta {i_p_admin+1} removida."); st.rerun()
                        st.divider()
            with tabs_perg_admin[1]: 
                with st.form("form_nova_pergunta_admin_vfinal"):
                    st.subheader("➕ Adicionar Nova Pergunta")
                    nova_p_form_txt_admin = st.text_input("Texto da Pergunta", key="nova_p_input_admin_txt_vfinal")
                    try:
                        perg_exist_df = pd.read_csv(perguntas_csv, encoding='utf-8')
                        cat_existentes = sorted(list(perg_exist_df['Categoria'].astype(str).unique())) if not perg_exist_df.empty and "Categoria" in perg_exist_df else []
                    except: cat_existentes = []
                    
                    cat_options = ["Nova Categoria"] + cat_existentes
                    cat_selecionada = st.selectbox("Categoria:", cat_options, key="cat_select_admin_new_q_vfinal")
                    
                    if cat_selecionada == "Nova Categoria":
                        nova_cat_form_admin = st.text_input("Nome da Nova Categoria:", key="nova_cat_input_admin_new_q_vfinal")
                    else: nova_cat_form_admin = cat_selecionada

                    tipo_p_form_admin = st.selectbox("Tipo de Pergunta", 
                                                 ["Pontuação (0-10)", "Texto Aberto", "Escala (Muito Baixo, Baixo, Médio, Alto, Muito Alto)", "[Matriz GUT]"], 
                                                 key="tipo_p_select_admin_new_q_vfinal")
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
                            st.text_input("CNPJ (não editável)", value=row_gc['CNPJ'], disabled=True, key=f"cnpj_gc_vfinal_{idx_gc}")
                            nova_senha_gc = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password", key=f"senha_gc_vfinal_{idx_gc}")
                            nome_empresa_gc = st.text_input("Nome Empresa", value=row_gc.get('Empresa',""), key=f"empresa_gc_vfinal_{idx_gc}")
                        with cols_edit_cli[1]:
                            nome_contato_gc = st.text_input("Nome Contato", value=row_gc.get("NomeContato", ""), key=f"nomec_gc_vfinal_{idx_gc}")
                            telefone_gc = st.text_input("Telefone", value=row_gc.get("Telefone", ""), key=f"tel_gc_vfinal_{idx_gc}")
                            logo_atual_path = find_client_logo_path(row_gc['CNPJ'])
                            if logo_atual_path: st.image(logo_atual_path, width=100, caption="Logo Atual")
                            uploaded_logo_gc = st.file_uploader("Alterar/Adicionar Logo", type=["png", "jpg", "jpeg"], key=f"logo_gc_vfinal_{idx_gc}")

                        if st.button("💾 Salvar Alterações do Cliente", key=f"save_gc_vfinal_{idx_gc}"):
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
                                        except Exception as e_remove_logo: st.warning(f"Não foi possível remover logo antiga {old_path}: {e_remove_logo}")
                                file_extension = uploaded_logo_gc.name.split('.')[-1].lower()
                                logo_save_path_gc = os.path.join(LOGOS_DIR, f"{clean_cnpj_gc_save}_logo.{file_extension}")
                                try:
                                    with open(logo_save_path_gc, "wb") as f: f.write(uploaded_logo_gc.getbuffer())
                                    st.success(f"Logo de {row_gc['Empresa']} atualizada!")
                                except Exception as e_save_logo_vfinal: st.error(f"Erro ao salvar logo: {e_save_logo_vfinal}")
                            
                            usuarios_clientes_df.to_csv(usuarios_csv, index=False, encoding='utf-8')
                            st.success(f"Dados de {row_gc['Empresa']} atualizados!"); st.rerun()
                st.divider()

            st.subheader("➕ Adicionar Novo Cliente")
            with st.form("form_novo_cliente_admin_vfinal"):
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
                            except Exception as e_save_new_logo_vfinal: st.error(f"Erro ao salvar nova logo: {e_save_new_logo_vfinal}")
                        
                        st.success(f"Cliente '{nova_empresa_gc_form}' adicionado!"); st.rerun()
                else: st.warning("CNPJ, Senha e Nome da Empresa são obrigatórios.")
            
            st.markdown("---"); st.subheader("🚫 Gerenciar Bloqueios")
            try: bloqueados_df_adm = pd.read_csv(usuarios_bloqueados_csv, encoding='utf-8')
            except (FileNotFoundError, pd.errors.EmptyDataError): bloqueados_df_adm = pd.DataFrame(columns=["CNPJ"])
            st.write("CNPJs bloqueados:", bloqueados_df_adm["CNPJ"].tolist() if not bloqueados_df_adm.empty else "Nenhum")
            col_block, col_unblock = st.columns(2)
            with col_block:
                cnpj_para_bloquear = st.selectbox("Bloquear CNPJ:", [""] + usuarios_clientes_df["CNPJ"].astype(str).unique().tolist(), key="block_cnpj_vfinal")
                if st.button("Bloquear Selecionado", key="btn_block_vfinal") and cnpj_para_bloquear:
                    if cnpj_para_bloquear not in bloqueados_df_adm["CNPJ"].astype(str).values:
                        nova_block = pd.DataFrame([[cnpj_para_bloquear]], columns=["CNPJ"])
                        bloqueados_df_adm = pd.concat([bloqueados_df_adm, nova_block], ignore_index=True)
                        bloqueados_df_adm.to_csv(usuarios_bloqueados_csv, index=False, encoding='utf-8')
                        st.success(f"CNPJ {cnpj_para_bloquear} bloqueado."); st.rerun()
                    else: st.warning(f"CNPJ {cnpj_para_bloquear} já bloqueado.")
            with col_unblock:
                cnpj_para_desbloquear = st.selectbox("Desbloquear CNPJ:", [""] + bloqueados_df_adm["CNPJ"].astype(str).unique().tolist(), key="unblock_cnpj_vfinal")
                if st.button("Desbloquear Selecionado", key="btn_unblock_vfinal") and cnpj_para_desbloquear:
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
            with st.form("form_novo_admin_manage_vfinal"):
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
                admin_para_remover_manage = st.selectbox("Remover Admin:", options=[""] + admins_df_manage["Usuario"].tolist(), key="remove_admin_select_manage_vfinal")
                if st.button("Remover Admin Selecionado", type="primary", key="btn_remove_admin_vfinal") and admin_para_remover_manage:
                    if len(admins_df_manage) == 1 and admin_para_remover_manage == admins_df_manage["Usuario"].iloc[0]:
                        st.error("Não é possível remover o único administrador.")
                    else:
                        admins_df_manage = admins_df_manage[admins_df_manage["Usuario"] != admin_para_remover_manage]
                        admins_df_manage.to_csv(admin_credenciais_csv, index=False, encoding='utf-8')
                        st.warning(f"Admin '{admin_para_remover_manage}' removido."); st.rerun()
            else: st.info("Nenhum administrador para remover.")

    except Exception as e_admin_area_vfinal_full_v2:
        st.error(f"Ocorreu um erro crítico na área administrativa: {e_admin_area_vfinal_full_v2}")
        st.exception(e_admin_area_vfinal_full_v2)

if not st.session_state.admin_logado and not st.session_state.cliente_logado and aba not in ["Administrador", "Cliente"]:
    st.info("Selecione se você é Administrador ou Cliente para continuar.")
    st.stop()