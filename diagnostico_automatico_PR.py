import streamlit as st
import pandas as pd
from datetime import datetime
import os
from fpdf import FPDF
import tempfile
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Portal de Diagnóstico", layout="centered")

admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv"
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"

if "admin_logado" not in st.session_state:
    st.session_state.admin_logado = False
if 'cliente_logado' not in st.session_state:
    st.session_state.cliente_logado = False
if 'diagnostico_enviado' not in st.session_state:
    st.session_state.diagnostico_enviado = False

# Inicializar arquivo de bloqueio se não existir
if not os.path.exists(usuarios_bloqueados_csv):
    pd.DataFrame(columns=["CNPJ"]).to_csv(usuarios_bloqueados_csv, index=False)

if not os.path.exists(admin_credenciais_csv):
    df_admin = pd.DataFrame([["admin", "potencialize"]], columns=["Usuario", "Senha"])
    df_admin.to_csv(admin_credenciais_csv, index=False)

st.title("\U0001F512 Portal de Acesso")

if not st.session_state.admin_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True)
else:
    aba = "Administrador"

if aba == "Administrador" and not st.session_state.admin_logado:
    with st.form("form_admin"):
        usuario = st.text_input("Usuário do Administrador")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar como Admin")

    if entrar:
        df_admin = pd.read_csv(admin_credenciais_csv)
        if not df_admin[(df_admin['Usuario'] == usuario) & (df_admin['Senha'] == senha)].empty:
            st.session_state.admin_logado = True
            st.success("Login de administrador realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

if aba == "Administrador" and st.session_state.admin_logado:
    st.success("\U0001F513 Painel Administrativo Ativo")
    menu_admin = st.selectbox("Selecione a funcionalidade administrativa:", [
        "\U0001F4CA Visualizar Diagnósticos",
        "\U0001F501 Reautorizar Cliente",
        "\U0001F465 Gerenciar Usuários",
        "🔒 Gerenciar Bloqueios",
        "\U0001F6E1️ Gerenciar Administradores"])

    if st.sidebar.button("\U0001F513 Sair do Painel Admin"):
        st.session_state.admin_logado = False
        st.rerun()

    if menu_admin == "🔒 Gerenciar Bloqueios":
        bloqueados = pd.read_csv(usuarios_bloqueados_csv)
        if os.path.exists(usuarios_csv):
            df_usuarios = pd.read_csv(usuarios_csv)
            cnpjs = df_usuarios['CNPJ'].tolist()
            st.subheader("Desbloquear CNPJ")
            desbloquear = st.selectbox("Selecionar CNPJ para desbloquear:", options=bloqueados['CNPJ'].tolist())
            if st.button("✅ Desbloquear"):
                bloqueados = bloqueados[bloqueados['CNPJ'] != desbloquear]
                bloqueados.to_csv(usuarios_bloqueados_csv, index=False)
                st.success(f"CNPJ {desbloquear} desbloqueado com sucesso.")

            st.subheader("Bloquear novo CNPJ")
            bloquear = st.selectbox("Selecionar CNPJ para bloquear:", options=[c for c in cnpjs if c not in bloqueados['CNPJ'].tolist()])
            if st.button("🚫 Bloquear"):
                bloqueados = pd.concat([bloqueados, pd.DataFrame([[bloquear]], columns=["CNPJ"])]).drop_duplicates()
                bloqueados.to_csv(usuarios_bloqueados_csv, index=False)
                st.success(f"CNPJ {bloquear} bloqueado com sucesso.")
        else:
            st.warning("Nenhum usuário cadastrado.")

if aba == "Cliente" and not st.session_state.cliente_logado:
    with st.form("form_cliente"):
        cnpj = st.text_input("CNPJ")
        senha = st.text_input("Senha", type="password")
        acessar = st.form_submit_button("Entrar como Cliente")

    if acessar:
        if not os.path.exists(usuarios_csv):
            st.error("Base de usuários não encontrada.")
            st.stop()

        usuarios = pd.read_csv(usuarios_csv)
        bloqueados = pd.read_csv(usuarios_bloqueados_csv)

        if cnpj in bloqueados['CNPJ'].values:
            st.error("Este CNPJ está bloqueado. Solicite liberação ao administrador.")
            st.stop()

        user = usuarios[(usuarios['CNPJ'] == cnpj) & (usuarios['Senha'] == senha)]

        if user.empty:
            st.error("CNPJ ou senha inválidos.")
            st.stop()

        diagnosticos = pd.read_csv(arquivo_csv) if os.path.exists(arquivo_csv) else pd.DataFrame(columns=["CNPJ", "Nome", "Email", "Empresa", "Financeiro", "Processos", "Marketing", "Vendas", "Equipe", "Média Geral", "Observações", "Diagnóstico", "Data"])
        if 'CNPJ' in diagnosticos.columns and not diagnosticos[diagnosticos['CNPJ'] == cnpj].empty:
            # Bloqueia automaticamente após envio
            bloqueados = pd.concat([bloqueados, pd.DataFrame([[cnpj]], columns=["CNPJ"])]).drop_duplicates()
            bloqueados.to_csv(usuarios_bloqueados_csv, index=False)
            st.warning("✅ Diagnóstico já preenchido. Agradecemos! Este acesso foi bloqueado para novos envios.")
            st.stop()

        st.session_state.cliente_logado = True
        st.session_state.cnpj = cnpj
        st.session_state.user = user
        st.success("Login realizado com sucesso!")
        st.rerun()
