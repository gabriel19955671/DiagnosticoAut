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
import plotly.graph_objects as go 
import uuid

st.set_page_config(page_title="Portal de Diagnóstico", layout="wide", initial_sidebar_state="expanded")

# !!!!! LEMBRETE SOBRE O CSS !!!!!
# Se você descomentar a linha abaixo, certifique-se que seu CSS não está tornando o texto invisível.
# st.markdown(""" 
# <style>
# /* SEU CSS PERSONALIZADO AQUI */
# .login-container { max-width: 400px; margin: 60px auto 0 auto; padding: 40px; border-radius: 8px; background-color: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.15); font-family: 'Segoe UI', sans-serif; }
# .login-container h2 { text-align: center; margin-bottom: 30px; font-weight: 600; font-size: 26px; color: #2563eb; }
# .kpi-card .value { font-size: 1.8em; font-weight: bold; color: #2563eb; }
# /* ... (resto do seu CSS) ... */
# </style>
# """, unsafe_allow_html=True)

st.title("🔒 Portal de Diagnóstico")

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
ST_KEY_VERSION = "v25" 

default_session_state = {
    "admin_logado": False, "cliente_logado": False, "diagnostico_enviado_sucesso": False,
    "inicio_sessao_cliente": None, "cliente_page": "Instruções", "cnpj": None, "user": None,
    "progresso_diagnostico_percentual": 0, "progresso_diagnostico_contagem": (0,0),
    "respostas_atuais_diagnostico": {}, "id_formulario_atual": None,
    "pdf_gerado_path": None, "pdf_gerado_filename": None,
    "feedbacks_respostas": {},
    "confirmou_instrucoes_checkbox_cliente": False,
    "admin_user_login_identifier": None,
    "last_cnpj_input": "" 
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Funções Utilitárias (COLOQUE SUAS FUNÇÕES COMPLETAS AQUI) ---
def sanitize_column_name(name): return str(name).replace(" ","_") 
def pdf_safe_text_output(text): return str(text).encode('latin-1', 'replace').decode('latin-1')
def find_client_logo_path(cnpj_arg): return None 
def inicializar_csv(filepath, columns, defaults=None):
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            df_init = pd.DataFrame(columns=columns)
            if defaults:
                for col, default_val in defaults.items():
                    if col in columns: df_init[col] = default_val
            df_init.to_csv(filepath, index=False, encoding='utf-8')
    except Exception as e:
        st.error(f"Erro ao inicializar {filepath}: {e}")

colunas_base_diagnosticos = ["Data", "CNPJ", "Nome", "Email", "Empresa", "Média Geral", "GUT Média", "Observações", "Diagnóstico", "Análise do Cliente", "Comentarios_Admin"]
colunas_base_usuarios = ["CNPJ", "Senha", "Empresa", "NomeContato", "Telefone", "ConfirmouInstrucoesParaSlotAtual", "DiagnosticosDisponiveis", "TotalDiagnosticosRealizados", "LiberacoesExtrasConcedidas"]

try:
    inicializar_csv(admin_credenciais_csv, ["Usuario", "Senha"])
    inicializar_csv(usuarios_csv, colunas_base_usuarios, defaults={"ConfirmouInstrucoesParaSlotAtual": "False", "DiagnosticosDisponiveis": 1, "TotalDiagnosticosRealizados": 0, "LiberacoesExtrasConcedidas": 0})
    inicializar_csv(historico_csv, ["Data", "CNPJ", "Ação", "Descrição"])
    # ... (inicialize todos os seus CSVs) ...
except Exception as e_init:
    st.error(f"Erro fatal na inicialização dos arquivos CSV: {e_init}")
    st.exception(e_init); st.stop()

def registrar_acao(cnpj, acao, desc):
    try:
        if os.path.exists(historico_csv) and os.path.getsize(historico_csv) > 0:
            hist_df = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
        else:
            hist_df = pd.DataFrame(columns=["Data", "CNPJ", "Ação", "Descrição"])
        new_entry = {"Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CNPJ": cnpj, "Ação": acao, "Descrição": desc}
        hist_df = pd.concat([hist_df, pd.DataFrame([new_entry])], ignore_index=True)
        hist_df.to_csv(historico_csv, index=False, encoding='utf-8')
    except Exception as e_hist:
        st.error(f"Erro ao registrar ação no histórico: {e_hist}")
# --- (Mantenha suas outras funções utilitárias: update_user_data, carregar_analises, etc.) ---
def gerar_pdf_historico(df_historico_filtrado, titulo="Histórico de Ações"):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(w=0, h=10, txt=pdf_safe_text_output(titulo), border=0, ln=1, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "B", 8) 
        col_widths_config = {"Data": 35, "CNPJ": 35, "Ação": 40, "Descrição": 0} 
        
        page_width_effective = pdf.w - pdf.l_margin - pdf.r_margin
        headers_to_print_hist = [col for col in ["Data", "CNPJ", "Ação", "Descrição"] if col in df_historico_filtrado.columns]
        
        current_total_width_for_others = sum(col_widths_config.get(h,0) for h in headers_to_print_hist if h != "Descrição")
        desc_width = page_width_effective - current_total_width_for_others
        if desc_width <= 0 : desc_width = page_width_effective * 0.3 
        col_widths_config["Descrição"] = max(20, desc_width) 

        pdf.set_fill_color(200, 220, 255) 

        for header in headers_to_print_hist:
            pdf.cell(w=col_widths_config.get(header, 30), h=7, txt=pdf_safe_text_output(header), border=1, ln=0, align="C", fill=True)
        pdf.ln(7) 
        
        pdf.set_font("Arial", "", 8)
        line_height_for_multicell = 5 

        for _, row_data in df_historico_filtrado.iterrows():
            y_start_current_row = pdf.get_y()
            max_cell_height_in_row = line_height_for_multicell

            for header_key_calc in headers_to_print_hist:
                cell_text_calc = str(row_data.get(header_key_calc, ""))
                cell_w_calc = col_widths_config.get(header_key_calc, 30)
                num_lines = 1
                if cell_w_calc > 0 and pdf.get_string_width(cell_text_calc) > cell_w_calc:
                    try:
                        words = cell_text_calc.split(' ')
                        temp_line_for_calc = ""
                        num_l_calc = 1
                        for word in words:
                            if pdf.get_string_width(temp_line_for_calc + word + " ") > cell_w_calc - 2 : 
                                num_l_calc +=1
                                temp_line_for_calc = word + " "
                            else:
                                temp_line_for_calc += word + " "
                        num_lines = num_l_calc
                    except: 
                        num_lines = int(pdf.get_string_width(cell_text_calc) / cell_w_calc) + 1 if cell_w_calc > 0 else 1
                
                current_cell_content_height = num_lines * line_height_for_multicell
                max_cell_height_in_row = max(max_cell_height_in_row, current_cell_content_height)
            
            current_row_total_height = max(max_cell_height_in_row, line_height_for_multicell)

            if y_start_current_row + current_row_total_height > pdf.page_break_trigger and not pdf.in_footer:
                pdf.add_page()
                y_start_current_row = pdf.get_y() 
                pdf.set_font("Arial", "B", 8)
                pdf.set_fill_color(200, 220, 255)
                for header_np in headers_to_print_hist:
                     pdf.cell(w=col_widths_config.get(header_np, 30), h=7, txt=pdf_safe_text_output(header_np), border=1, ln=0, align="C", fill=True)
                pdf.ln(7)
                pdf.set_font("Arial", "", 8)
            
            current_x = pdf.l_margin
            for header_key_draw in headers_to_print_hist:
                pdf.set_xy(current_x, y_start_current_row) 
                cell_content = str(row_data.get(header_key_draw, ""))
                cell_w = col_widths_config.get(header_key_draw, 30)
                
                pdf.rect(current_x, y_start_current_row, cell_w, current_row_total_height)
                pdf.multi_cell(w=cell_w, h=line_height_for_multicell, txt=pdf_safe_text_output(cell_content), border=0, align="L") 
                current_x += cell_w 
            
            pdf.set_y(y_start_current_row + current_row_total_height)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf_path = tmpfile.name
            pdf.output(name=pdf_path, dest='F') 
        return pdf_path
    except Exception as e_pdf_hist:
        st.error(f"Erro ao gerar PDF do histórico: {e_pdf_hist}")
        st.exception(e_pdf_hist) 
        return None
# --- FIM DAS FUNÇÕES PDF ---


# --- Lógica de Login e Navegação Principal ---
if st.session_state.get("trigger_rerun_global"): 
    st.session_state.trigger_rerun_global = False
    st.rerun()

st.sidebar.write(f"DEBUG (antes radio): admin_logado={st.session_state.get('admin_logado', False)}, cliente_logado={st.session_state.get('cliente_logado', False)}")

if not st.session_state.get("admin_logado", False) and not st.session_state.get("cliente_logado", False):
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True, key=f"tipo_usuario_radio_{ST_KEY_VERSION}") 
elif st.session_state.get("admin_logado", False): 
    aba = "Administrador"
else: 
    aba = "Cliente"

st.sidebar.write(f"DEBUG (após radio): aba='{aba}'")

# --- ÁREA DE LOGIN DO ADMINISTRADOR ---
if aba == "Administrador" and not st.session_state.get("admin_logado", False):
    # (Seu código de login do admin completo aqui, com chaves _v25)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2>Login Administrador 🔑</h2>', unsafe_allow_html=True)
    with st.form(f"form_admin_login_{ST_KEY_VERSION}"):
        # ... (campos de login e lógica)
        if st.form_submit_button("Entrar"):
            st.session_state.admin_logado = True # Simulação de login para teste
            st.session_state.admin_user_login_identifier = "admin_test"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True); st.stop()


# --- ÁREA DE LOGIN DO CLIENTE ---
if aba == "Cliente" and not st.session_state.get("cliente_logado", False):
    # (Seu código de login do cliente completo aqui, com chaves _v25)
    st.markdown("Área de Login Cliente Placeholder") 
    st.stop()

# --- ÁREA DO CLIENTE LOGADO ---
if aba == "Cliente" and st.session_state.get("cliente_logado", False):
    # (Seu código da área do cliente completo aqui, com chaves _v25)
    st.header("Painel do Cliente")
    st.write("Conteúdo da área do cliente...")
    if st.sidebar.button(f"Logout Cliente_{ST_KEY_VERSION}"): # Exemplo de chave única
        st.session_state.cliente_logado = False
        # Limpar dados da sessão do cliente
        st.rerun()


# --- ÁREA DO ADMINISTRADOR LOGADO ---
if aba == "Administrador" and st.session_state.get("admin_logado", False):
    st.sidebar.write(f"[DEBUG ADMIN] PONTO S1 - Entrou no bloco admin_logado. Chave Sessão: {ST_KEY_VERSION}") 
    try:
        st.sidebar.success("🟢 Admin Logado")
        if st.sidebar.button(f"🚪 Sair do Painel Admin", key=f"logout_admin_{ST_KEY_VERSION}_adm"): 
            st.session_state.admin_logado = False
            if 'admin_user_login_identifier' in st.session_state:
                del st.session_state.admin_user_login_identifier
            st.rerun() 
        
        menu_admin_options = [
            "📊 Visão Geral e Diagnósticos", "🚦 Status dos Clientes", "📜 Histórico de Usuários",
            "📝 Gerenciar Perguntas", "💡 Gerenciar Análises de Perguntas",
            "✍️ Gerenciar Instruções Clientes", "👥 Gerenciar Clientes", 
            "👮 Gerenciar Administradores", "💾 Backup de Dados"
        ]
        menu_admin = st.sidebar.selectbox(
            "Funcionalidades Admin:", 
            menu_admin_options, 
            key=f"admin_menu_selectbox_{ST_KEY_VERSION}_adm" 
        )
        st.sidebar.info(f"[DEBUG Sidebar] Opção: '{menu_admin}'")
        
        admin_page_title_prefix = menu_admin.split(' ')[0] if isinstance(menu_admin, str) and menu_admin else "Admin"
        st.header(f"Painel Admin: {admin_page_title_prefix}")
        st.write(f"[DEBUG Main Panel] Renderizando: {menu_admin}")


        if menu_admin == "📊 Visão Geral e Diagnósticos":
            st.subheader("📊 Visão Geral e Diagnósticos")
            st.markdown("Conteúdo completo da Visão Geral e Diagnósticos aqui...")
            # TODO: Adicionar a lógica real e carregamento de dados para esta seção

        elif menu_admin == "🚦 Status dos Clientes":
            st.subheader("🚦 Status dos Clientes")
            st.markdown("Conteúdo completo do Status dos Clientes aqui...")
            # TODO: Adicionar a lógica real e carregamento de dados para esta seção

        elif menu_admin == "📜 Histórico de Usuários":
            st.subheader("📜 Histórico de Usuários")
            
            df_historico_completo_hu = pd.DataFrame()
            df_usuarios_para_filtro_hu = pd.DataFrame()
            try:
                if os.path.exists(historico_csv) and os.path.getsize(historico_csv) > 0:
                    df_historico_completo_hu = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
                else:
                    st.info("Arquivo de histórico vazio ou não encontrado.")
                
                if os.path.exists(usuarios_csv) and os.path.getsize(usuarios_csv) > 0:
                    df_usuarios_para_filtro_hu = pd.read_csv(usuarios_csv, encoding='utf-8', usecols=['CNPJ', 'Empresa', 'NomeContato'], dtype={'CNPJ': str})
                else:
                    st.info("Arquivo de usuários vazio ou não encontrado para filtros.")

            except Exception as e_hu_load: 
                st.error(f"Erro ao carregar dados para o histórico: {e_hu_load}")
            
            st.markdown("#### Filtros do Histórico")
            col_hu_f1, col_hu_f2 = st.columns(2)
            empresas_hist_list_hu = ["Todas"]
            if not df_usuarios_para_filtro_hu.empty and 'Empresa' in df_usuarios_para_filtro_hu.columns: 
                empresas_hist_list_hu.extend(sorted(df_usuarios_para_filtro_hu['Empresa'].astype(str).unique().tolist()))
            
            emp_sel_hu = col_hu_f1.selectbox("Filtrar por Empresa:", empresas_hist_list_hu, key=f"hist_emp_sel_{ST_KEY_VERSION}_hu_adm")
            termo_busca_hu = col_hu_f2.text_input("Buscar por Nome do Contato, CNPJ, Ação ou Descrição:", key=f"hist_termo_busca_{ST_KEY_VERSION}_hu_adm")
            
            df_historico_filtrado_view_hu = df_historico_completo_hu.copy()
            cnpjs_da_empresa_selecionada_hu = []

            if emp_sel_hu != "Todas" and not df_usuarios_para_filtro_hu.empty: 
                cnpjs_da_empresa_selecionada_hu = df_usuarios_para_filtro_hu[df_usuarios_para_filtro_hu['Empresa'] == emp_sel_hu]['CNPJ'].tolist()
                if not df_historico_filtrado_view_hu.empty:
                    df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_da_empresa_selecionada_hu)]
            
            if termo_busca_hu.strip() and not df_historico_filtrado_view_hu.empty :
                busca_lower_hu = termo_busca_hu.strip().lower()
                cnpjs_match_nome_hu = []
                if not df_usuarios_para_filtro_hu.empty and 'NomeContato' in df_usuarios_para_filtro_hu.columns:
                     cnpjs_match_nome_hu = df_usuarios_para_filtro_hu[df_usuarios_para_filtro_hu['NomeContato'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)]['CNPJ'].tolist()
                
                df_historico_filtrado_view_hu = df_historico_filtrado_view_hu[
                    df_historico_filtrado_view_hu['CNPJ'].isin(cnpjs_match_nome_hu) | 
                    df_historico_filtrado_view_hu['CNPJ'].astype(str).str.lower().str.contains(busca_lower_hu) | 
                    df_historico_filtrado_view_hu['Ação'].astype(str).str.lower().str.contains(busca_lower_hu, na=False) | 
                    df_historico_filtrado_view_hu['Descrição'].astype(str).str.lower().str.contains(busca_lower_hu, na=False)
                ]
            
            st.markdown("#### Registros do Histórico")
            if not df_historico_filtrado_view_hu.empty:
                st.dataframe(df_historico_filtrado_view_hu.sort_values(by="Data", ascending=False))
                if st.button("📄 Baixar Histórico Filtrado (PDF)", key=f"download_hist_filtrado_pdf_{ST_KEY_VERSION}_hu_adm"):
                    titulo_pdf_hist = f"Historico_Acoes_{sanitize_column_name(emp_sel_hu)}_{sanitize_column_name(termo_busca_hu) if termo_busca_hu else 'Todos'}_{datetime.now().strftime('%Y%m%d')}.pdf"
                    pdf_path_hist = gerar_pdf_historico(df_historico_filtrado_view_hu, titulo=f"Histórico ({emp_sel_hu} - Busca: {termo_busca_hu or 'N/A'})")
                    if pdf_path_hist:
                        with open(pdf_path_hist, "rb") as f_pdf_hist: 
                            st.download_button(label="Download Confirmado", data=f_pdf_hist, file_name=titulo_pdf_hist, mime="application/pdf", key=f"confirm_download_hist_pdf_{ST_KEY_VERSION}_hu_adm")
                        try: os.remove(pdf_path_hist) 
                        except: pass
                
                if emp_sel_hu != "Todas" and not df_historico_filtrado_view_hu.empty and cnpjs_da_empresa_selecionada_hu:
                    st.markdown("---")
                    st.markdown(f"#### 🗑️ Resetar Histórico da Empresa: {emp_sel_hu}")
                    with st.expander(f"⚠️ ATENÇÃO: Excluir TODO o histórico da Empresa '{emp_sel_hu}'"):
                        st.warning(f"Esta ação é irreversível e removerá TODOS os registros de histórico associados à empresa '{emp_sel_hu}' (CNPJs: {', '.join(cnpjs_da_empresa_selecionada_hu)}).")
                        confirm_text_delete_hist = st.text_input(f"Para confirmar, digite o nome da empresa '{emp_sel_hu}' exatamente como mostrado:", key=f"confirm_text_delete_hist_emp_{emp_sel_hu}_{ST_KEY_VERSION}").strip()
                        if st.button(f"🗑️ Excluir Histórico de '{emp_sel_hu}' AGORA", type="primary", key=f"btn_delete_hist_emp_{emp_sel_hu}_{ST_KEY_VERSION}", disabled=(confirm_text_delete_hist != emp_sel_hu)):
                            if confirm_text_delete_hist == emp_sel_hu:
                                try:
                                    if os.path.exists(historico_csv):
                                        df_hist_full_to_update = pd.read_csv(historico_csv, encoding='utf-8', dtype={'CNPJ': str})
                                        df_hist_full_updated = df_hist_full_to_update[~df_hist_full_to_update['CNPJ'].isin(cnpjs_da_empresa_selecionada_hu)]
                                        df_hist_full_updated.to_csv(historico_csv, index=False, encoding='utf-8')
                                        registrar_acao("ADMIN_ACTION", "Exclusão Histórico Empresa", f"Admin excluiu todo o histórico da empresa '{emp_sel_hu}' (CNPJs: {', '.join(cnpjs_da_empresa_selecionada_hu)}).")
                                        st.success(f"Todo o histórico da empresa '{emp_sel_hu}' foi excluído com sucesso.")
                                        st.rerun()
                                    else: st.error("Arquivo de histórico não encontrado para realizar a exclusão.")
                                except Exception as e_del_hist: st.error(f"Erro ao excluir o histórico da empresa: {e_del_hist}")
                            else: st.error("O nome da empresa digitado para confirmação está incorreto.")
            else:
                st.info("Nenhum registro de histórico encontrado para os filtros aplicados.")

        elif menu_admin == "📝 Gerenciar Perguntas":
            st.subheader("📝 Gerenciar Perguntas")
            st.markdown("Conteúdo para Gerenciar Perguntas (em desenvolvimento).")
        elif menu_admin == "💡 Gerenciar Análises de Perguntas":
            st.subheader("💡 Gerenciar Análises de Perguntas")
            st.markdown("Conteúdo para Gerenciar Análises de Perguntas (em desenvolvimento).")
        elif menu_admin == "✍️ Gerenciar Instruções Clientes":
            st.subheader("✍️ Gerenciar Instruções Clientes")
            st.markdown("Conteúdo para Gerenciar Instruções Clientes (em desenvolvimento).")
        elif menu_admin == "👥 Gerenciar Clientes":
            st.subheader("👥 Gerenciar Clientes")
            st.markdown("Conteúdo para Gerenciar Clientes (em desenvolvimento).")
        elif menu_admin == "👮 Gerenciar Administradores":
            st.subheader("👮 Gerenciar Administradores")
            st.markdown("Conteúdo para Gerenciar Administradores (em desenvolvimento).")
        elif menu_admin == "💾 Backup de Dados":
            st.subheader("💾 Backup de Dados")
            st.markdown("Conteúdo para Backup de Dados (em desenvolvimento).")
        else:
            st.warning(f"[DEBUG ADMIN Main Panel] Opção de menu '{menu_admin}' não corresponde a nenhum bloco if/elif.")
        
        st.write(f"[DEBUG ADMIN Main Panel] PONTO MP4 - Após dispatch do menu")

    except Exception as e_outer_admin_critical:
        st.error(f"Um erro crítico ocorreu na área administrativa: {e_outer_admin_critical}")
        st.exception(e_outer_admin_critical)
        st.write(f"[DEBUG ADMIN Main Panel] PONTO MP_EXCEPT - Dentro do except e_outer_admin_critical ({e_outer_admin_critical})") 

if not st.session_state.get("admin_logado", False) and not st.session_state.get("cliente_logado", False) and ('aba' not in locals() or aba is None):
    st.info("Fallback final: Selecione se você é Administrador ou Cliente para continuar.")