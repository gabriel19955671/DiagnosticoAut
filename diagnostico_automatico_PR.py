import streamlit as st
import pandas as pd
from datetime import datetime
import os
from fpdf import FPDF

st.set_page_config(page_title="Diagnóstico Automático", layout="wide")

if "admin_logado" not in st.session_state:
    st.session_state.admin_logado = False

admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv"
arquivo_csv = "diagnosticos_clientes.csv"

# Verifica se existe arquivo de admins, senão cria admin padrão
if not os.path.exists(admin_credenciais_csv):
    df_admin = pd.DataFrame([["admin", "potencialize"]], columns=["Usuario", "Senha"])
    df_admin.to_csv(admin_credenciais_csv, index=False)

# Define menu
opcoes = ["Cliente - Preencher Diagnóstico"]
if st.session_state.admin_logado:
    opcoes.extend([
        "Admin - Visualizar Diagnósticos",
        "Admin - Reautorizar Cliente",
        "Admin - Buscar e Filtrar Diagnósticos",
        "Admin - Gerenciar Usuários",
        "Admin - Gerenciar Administradores"
    ])
else:
    opcoes.append("🔐 Login Administrador")

menu = st.sidebar.selectbox("Selecione a visão", opcoes)

# LOGIN ADMIN
if menu == "🔐 Login Administrador":
    st.title("🔐 Acesso Administrativo")
    with st.form("form_admin"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        df_admins = pd.read_csv(admin_credenciais_csv)
        credencial_ok = df_admins[(df_admins["Usuario"] == usuario) & (df_admins["Senha"] == senha)]
        if not credencial_ok.empty:
            st.session_state.admin_logado = True
            st.success("Login realizado com sucesso!")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")

# CLIENTE - FORMULÁRIO
elif menu == "Cliente - Preencher Diagnóstico":
    pass  # permanece o mesmo

# ADMIN - VISUALIZAR
elif menu == "Admin - Visualizar Diagnósticos" and st.session_state.admin_logado:
    pass

# ADMIN - REAUTORIZAR
elif menu == "Admin - Reautorizar Cliente" and st.session_state.admin_logado:
    pass

# ADMIN - FILTRO
elif menu == "Admin - Buscar e Filtrar Diagnósticos" and st.session_state.admin_logado:
    pass

# ADMIN - GERENCIAR USUÁRIOS
elif menu == "Admin - Gerenciar Usuários" and st.session_state.admin_logado:
    st.title("👥 Gerenciar Usuários (Clientes)")
    if os.path.exists(usuarios_csv):
        df_usuarios = pd.read_csv(usuarios_csv)
    else:
        df_usuarios = pd.DataFrame(columns=["CNPJ", "Senha", "Empresa"])

    st.subheader("📋 Lista de Usuários")
    st.dataframe(df_usuarios, use_container_width=True)

    st.subheader("➕ Adicionar Novo Usuário")
    with st.form("form_novo_usuario"):
        novo_cnpj = st.text_input("CNPJ")
        nova_senha = st.text_input("Senha")
        nova_empresa = st.text_input("Nome da Empresa")
        adicionar = st.form_submit_button("Adicionar Usuário")

    if adicionar:
        if novo_cnpj and nova_senha and nova_empresa:
            if novo_cnpj in df_usuarios["CNPJ"].values:
                st.warning("CNPJ já cadastrado.")
            else:
                novo_usuario = pd.DataFrame([[novo_cnpj, nova_senha, nova_empresa]], columns=["CNPJ", "Senha", "Empresa"])
                df_usuarios = pd.concat([df_usuarios, novo_usuario], ignore_index=True)
                df_usuarios.to_csv(usuarios_csv, index=False)
                st.success("Usuário adicionado com sucesso!")
        else:
            st.warning("Preencha todos os campos.")

    st.subheader("🗑️ Remover Usuário")
    cnpjs_disponiveis = df_usuarios["CNPJ"].tolist()
    cnpj_remover = st.selectbox("Selecione o CNPJ para remover", options=cnpjs_disponiveis)
    if st.button("Remover Usuário"):
        df_usuarios = df_usuarios[df_usuarios["CNPJ"] != cnpj_remover]
        df_usuarios.to_csv(usuarios_csv, index=False)
        st.success(f"Usuário com CNPJ {cnpj_remover} removido com sucesso!")

# ADMIN - GERENCIAR ADMINISTRADORES
elif menu == "Admin - Gerenciar Administradores" and st.session_state.admin_logado:
    st.title("🛡️ Gerenciar Administradores")
    df_admins = pd.read_csv(admin_credenciais_csv)
    st.dataframe(df_admins, use_container_width=True)

    st.subheader("➕ Adicionar Novo Administrador")
    with st.form("form_novo_admin"):
        novo_user = st.text_input("Novo Usuário")
        nova_senha = st.text_input("Nova Senha")
        add_admin = st.form_submit_button("Adicionar Admin")

    if add_admin:
        if novo_user and nova_senha:
            if novo_user in df_admins["Usuario"].values:
                st.warning("Usuário já cadastrado.")
            else:
                novo_admin = pd.DataFrame([[novo_user, nova_senha]], columns=["Usuario", "Senha"])
                df_admins = pd.concat([df_admins, novo_admin], ignore_index=True)
                df_admins.to_csv(admin_credenciais_csv, index=False)
                st.success("Administrador adicionado com sucesso!")
        else:
            st.warning("Preencha todos os campos.")

    st.subheader("🗑️ Remover Administrador")
    admins_disponiveis = df_admins["Usuario"].tolist()
    admin_remover = st.selectbox("Selecione o administrador para remover", options=admins_disponiveis)
    if st.button("Remover Administrador"):
        df_admins = df_admins[df_admins["Usuario"] != admin_remover]
        df_admins.to_csv(admin_credenciais_csv, index=False)
        st.success(f"Administrador '{admin_remover}' removido com sucesso!")
