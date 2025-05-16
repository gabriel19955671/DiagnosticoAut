import streamlit as st
import pandas as pd
from datetime import datetime
import os
from fpdf import FPDF
import tempfile

st.set_page_config(page_title="Portal de Diagnóstico", layout="centered")

admin_credenciais_csv = "admins.csv"
usuarios_csv = "usuarios.csv"
arquivo_csv = "diagnosticos_clientes.csv"
usuarios_bloqueados_csv = "usuarios_bloqueados.csv"

if "admin_logado" not in st.session_state:
    st.session_state.admin_logado = False
if "cliente_logado" not in st.session_state:
    st.session_state.cliente_logado = False
if "diagnostico_enviado" not in st.session_state:
    st.session_state.diagnostico_enviado = False

# Criar arquivos se não existirem
for arquivo, colunas in [
    (usuarios_bloqueados_csv, ["CNPJ"]),
    (admin_credenciais_csv, ["Usuario", "Senha"]),
    (usuarios_csv, ["CNPJ", "Senha", "Empresa"]),
    (arquivo_csv, [
        "Data", "CNPJ", "Nome", "Email", "Empresa", "Financeiro",
        "Processos", "Marketing", "Vendas", "Equipe", "Média Geral",
        "Observações", "Diagnóstico"
    ])
]:
    if not os.path.exists(arquivo):
        pd.DataFrame(columns=colunas).to_csv(arquivo, index=False)

st.markdown("""
<style>
.css-1d391kg, .css-18e3th9 { padding-top: 0rem !important; padding-bottom: 0rem !important; }
div[data-testid="stHorizontalBlock"] > div:first-child { display: none !important; height: 0 !important; margin: 0 !important; padding: 0 !important; }
.login-container { background-color: #f0f2f6; padding: 40px; border-radius: 8px; max-width: 400px; margin: 40px auto; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
</style>
""", unsafe_allow_html=True)

st.markdown("## \U0001F512 Portal de Acesso")

if not st.session_state.admin_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True)
else:
    aba = "Administrador"

# LOGIN ADMINISTRADOR
if aba == "Administrador" and not st.session_state.admin_logado:
    with st.form("form_admin"):
        usuario = st.text_input("Usuário do Administrador")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar como Admin")
    if entrar:
        df_admin = pd.read_csv(admin_credenciais_csv)
        if not df_admin[(df_admin["Usuario"] == usuario) & (df_admin["Senha"] == senha)].empty:
            st.session_state.admin_logado = True
            st.success("Login de administrador realizado com sucesso!")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")

# PAINEL ADMINISTRATIVO
if aba == "Administrador" and st.session_state.admin_logado:
    st.success("\U0001F513 Painel Administrativo Ativo")
    menu_admin = st.selectbox(
        "Selecione a funcionalidade administrativa:",
        [
            "\U0001F4CA Visualizar Diagnósticos",
            "\U0001F501 Reautorizar Cliente",
            "\U0001F465 Gerenciar Usuários",
            "🔒 Gerenciar Bloqueios",
            "\U0001F6E1️ Gerenciar Administradores"
        ],
    )
    if st.sidebar.button("\U0001F513 Sair do Painel Admin"):
        st.session_state.admin_logado = False
        st.experimental_rerun()

    if menu_admin == "\U0001F4CA Visualizar Diagnósticos":
        df = pd.read_csv(arquivo_csv)
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Baixar Diagnósticos (CSV)", df.to_csv(index=False), file_name="diagnosticos.csv", mime="text/csv")

    elif menu_admin == "\U0001F501 Reautorizar Cliente":
        df = pd.read_csv(arquivo_csv)
        cnpjs = df["CNPJ"].unique().tolist()
        cnpj_sel = st.selectbox("Selecione o CNPJ para liberar novo diagnóstico:", options=cnpjs)
        if st.button("🔄 Reautorizar"):
            df = df[df["CNPJ"] != cnpj_sel]
            df.to_csv(arquivo_csv, index=False)
            st.success(f"CNPJ {cnpj_sel} reautorizado com sucesso.")

    elif menu_admin == "\U0001F465 Gerenciar Usuários":
        df_usuarios = pd.read_csv(usuarios_csv)
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
        df_bloqueados = pd.read_csv(usuarios_bloqueados_csv)
        st.subheader("Usuários Bloqueados")
        st.dataframe(df_bloqueados, use_container_width=True)

        st.subheader("Bloquear Usuário")
        with st.form("bloquear_usuario"):
            cnpj_bloq = st.text_input("CNPJ para bloquear")
            bloquear = st.form_submit_button("Bloquear")
        if bloquear:
            if cnpj_bloq and cnpj_bloq not in df_bloqueados["CNPJ"].values:
                df_bloqueados = pd.concat([df_bloqueados, pd.DataFrame([[cnpj_bloq]], columns=["CNPJ"])], ignore_index=True)
                df_bloqueados.to_csv(usuarios_bloqueados_csv, index=False)
                st.success(f"CNPJ {cnpj_bloq} bloqueado com sucesso!")

        st.subheader("Desbloquear Usuário")
        with st.form("desbloquear_usuario"):
            cnpj_desbloq = st.selectbox("Selecione CNPJ para desbloquear", options=df_bloqueados["CNPJ"].tolist())
            desbloquear = st.form_submit_button("Desbloquear")
        if desbloquear:
            df_bloqueados = df_bloqueados[df_bloqueados["CNPJ"] != cnpj_desbloq]
            df_bloqueados.to_csv(usuarios_bloqueados_csv, index=False)
