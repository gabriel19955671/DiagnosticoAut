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

if aba == "Administrador" and st.session_state.admin_logado:
    st.success("\U0001F513 Painel Administrativo Ativo")
    menu_admin = st.selectbox("Selecione a funcionalidade administrativa:", [
        "\U0001F4CA Visualizar Diagnósticos",
        "\U0001F501 Reautorizar Cliente",
        "\U0001F465 Gerenciar Usuários",
        "🔒 Gerenciar Bloqueios",
        "\U0001F6E1️ Gerenciar Administradores"
    ])

    if st.sidebar.button("\U0001F513 Sair do Painel Admin"):
        st.session_state.admin_logado = False
        st.rerun()

    if menu_admin == "\U0001F4CA Visualizar Diagnósticos":
        if os.path.exists(arquivo_csv):
            df = pd.read_csv(arquivo_csv)
            st.dataframe(df, use_container_width=True)
            st.download_button("\U0001F4E5 Baixar Diagnósticos (CSV)", data=df.to_csv(index=False), file_name="diagnosticos.csv", mime="text/csv")
        else:
            st.info("Nenhum diagnóstico encontrado.")

    elif menu_admin == "\U0001F501 Reautorizar Cliente":
        if os.path.exists(arquivo_csv):
            df = pd.read_csv(arquivo_csv)
            cnpjs = df['CNPJ'].unique().tolist()
            cnpj_sel = st.selectbox("Selecione o CNPJ para liberar novo diagnóstico:", options=cnpjs)
            if st.button("\U0001F504 Reautorizar"):
                df = df[df['CNPJ'] != cnpj_sel]
                df.to_csv(arquivo_csv, index=False)
                st.success(f"CNPJ {cnpj_sel} reautorizado com sucesso.")
        else:
            st.info("Nenhum diagnóstico para reautorizar.")

    elif menu_admin == "\U0001F465 Gerenciar Usuários":
        if os.path.exists(usuarios_csv):
            df_usuarios = pd.read_csv(usuarios_csv)
        else:
            df_usuarios = pd.DataFrame(columns=["CNPJ", "Senha", "Empresa"])

        st.subheader("Lista de Usuários")
        st.dataframe(df_usuarios, use_container_width=True)

        st.subheader("Adicionar Novo Usuário")
        with st.form("novo_usuario"):
            novo_cnpj = st.text_input("Novo CNPJ")
            nova_senha = st.text_input("Senha")
            nova_empresa = st.text_input("Empresa")
            confirmar = st.form_submit_button("Adicionar")
        if confirmar:
            if novo_cnpj and nova_senha and nova_empresa:
                novo = pd.DataFrame([[novo_cnpj, nova_senha, nova_empresa]], columns=["CNPJ", "Senha", "Empresa"])
                df_usuarios = pd.concat([df_usuarios, novo], ignore_index=True)
                df_usuarios.to_csv(usuarios_csv, index=False)
                st.success("Usuário adicionado com sucesso!")

    elif menu_admin == "🔒 Gerenciar Bloqueios":
        if os.path.exists(usuarios_bloqueados_csv):
            bloqueados = pd.read_csv(usuarios_bloqueados_csv)
        else:
            bloqueados = pd.DataFrame(columns=["CNPJ"])

        if os.path.exists(usuarios_csv):
            df_usuarios = pd.read_csv(usuarios_csv)
            cnpjs = df_usuarios['CNPJ'].tolist()
        else:
            cnpjs = []

        st.subheader("Usuários Bloqueados")
        st.dataframe(bloqueados, use_container_width=True)

        st.subheader("Desbloquear CNPJ")
        desbloquear = st.selectbox("Selecionar CNPJ para desbloquear:", options=bloqueados['CNPJ'].tolist() if not bloqueados.empty else [])
        if st.button("✅ Desbloquear"):
            bloqueados = bloqueados[bloqueados['CNPJ'] != desbloquear]
            bloqueados.to_csv(usuarios_bloqueados_csv, index=False)
            st.success(f"CNPJ {desbloquear} desbloqueado com sucesso.")
            st.experimental_rerun()

        st.subheader("Bloquear novo CNPJ")
        bloquear = st.selectbox("Selecionar CNPJ para bloquear:", options=[c for c in cnpjs if c not in bloqueados['CNPJ'].tolist()] if cnpjs else [])
        if st.button("🚫 Bloquear"):
            bloqueados = pd.concat([bloqueados, pd.DataFrame([[bloquear]], columns=["CNPJ"])]).drop_duplicates()
            bloqueados.to_csv(usuarios_bloqueados_csv, index=False)
            st.success(f"CNPJ {bloquear} bloqueado com sucesso.")
            st.experimental_rerun()

    elif menu_admin == "\U0001F6E1️ Gerenciar Administradores":
        df_admin = pd.read_csv(admin_credenciais_csv)
        st.subheader("Administradores Cadastrados")
        st.dataframe(df_admin, use_container_width=True)

        st.subheader("Adicionar Novo Administrador")
        with st.form("novo_admin"):
            novo_user = st.text_input("Usuário")
            nova_senha = st.text_input("Senha")
            confirmar = st.form_submit_button("Adicionar")
        if confirmar:
            if novo_user and nova_senha:
                novo = pd.DataFrame([[novo_user, nova_senha]], columns=["Usuario", "Senha"])
                df_admin = pd.concat([df_admin, novo], ignore_index=True)
                df_admin.to_csv(admin_credenciais_csv, index=False)
                st.success("Administrador adicionado com sucesso!")

# ... o restante do código cliente permanece igual (login, formulário diagnóstico, geração PDF etc.)
