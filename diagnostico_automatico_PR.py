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

if "admin_logado" not in st.session_state:
    st.session_state.admin_logado = False

if not os.path.exists(admin_credenciais_csv):
    df_admin = pd.DataFrame([['admin', 'potencialize']], columns=['Usuario', 'Senha'])
    df_admin.to_csv(admin_credenciais_csv, index=False)

st.title("🔐 Portal de Acesso")

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
        if usuario == 'admin' and senha == 'potencialize':
            st.session_state.admin_logado = True
            st.success("Login de administrador MASTER realizado com sucesso!")
            st.rerun()

if aba == "Administrador" and st.session_state.admin_logado:
    st.success("🔓 Painel Administrativo Ativo")
    menu_admin = st.selectbox("Selecione a funcionalidade administrativa:", [
        "📊 Visualizar Diagnósticos",
        "🔁 Reautorizar Cliente",
        "👥 Gerenciar Usuários",
        "🛡️ Gerenciar Administradores"
    ])

    if st.sidebar.button("🔓 Sair do Painel Admin"):
        st.session_state.admin_logado = False
        st.rerun()

    if menu_admin == "📊 Visualizar Diagnósticos":
        if os.path.exists(arquivo_csv):
            if st.button("💾 Gerar Backup ZIP"):
                import zipfile
                from datetime import datetime
                zip_nome = f"backup_diagnosticos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                with zipfile.ZipFile(zip_nome, 'w') as zipf:
                    zipf.write(arquivo_csv)
                with open(zip_nome, "rb") as f:
                    st.download_button("⬇️ Baixar Backup ZIP", f, file_name=zip_nome, mime="application/zip")

                st.info("✉️ Você pode integrar envio por e-mail via SMTP aqui.")
                # Exemplo de envio por e-mail (estrutura pronta, sem SMTP real)
                if st.button("Simular Envio por E-mail"):
                    st.success(f"Backup '{zip_nome}' enviado com sucesso (simulado).")
                import zipfile
                from datetime import datetime
                zip_nome = f"backup_diagnosticos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                with zipfile.ZipFile(zip_nome, 'w') as zipf:
                    zipf.write(arquivo_csv)
                with open(zip_nome, "rb") as f:
                    st.download_button("⬇️ Baixar Backup ZIP", f, file_name=zip_nome, mime="application/zip")
        if os.path.exists(arquivo_csv):
            df = pd.read_csv(arquivo_csv)
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 Baixar todos os diagnósticos (CSV)", data=df.to_csv(index=False), file_name="diagnosticos.csv", mime="text/csv")
        else:
            st.warning("Nenhum diagnóstico enviado ainda.")

    elif menu_admin == "🔁 Reautorizar Cliente":
        if os.path.exists(arquivo_csv):
            df = pd.read_csv(arquivo_csv)
            cnpjs = df['CNPJ'].unique().tolist()
            cnpj_sel = st.selectbox("Selecione o CNPJ para reautorizar", options=cnpjs)
            if st.button("🔄 Remover Diagnóstico e Liberar Acesso"):
                df = df[df['CNPJ'] != cnpj_sel]
                df.to_csv(arquivo_csv, index=False)
                st.success(f"CNPJ {cnpj_sel} liberado para novo diagnóstico.")
        else:
            st.info("Nenhum diagnóstico enviado ainda para reautorização.")

    elif menu_admin == "👥 Gerenciar Usuários":
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

    elif menu_admin == "🛡️ Gerenciar Administradores":
        df_admins = pd.read_csv(admin_credenciais_csv)
        st.subheader("👥 Lista de Administradores")
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
        else:
            df_admins = pd.read_csv(admin_credenciais_csv)
            if not df_admins[(df_admins['Usuario'] == usuario) & (df_admins['Senha'] == senha)].empty:
                st.session_state.admin_logado = True
                st.success("Login de administrador realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha de administrador inválidos.")

if aba == "Cliente":
    with st.form("form_cliente"):
        cnpj = st.text_input("CNPJ")
        senha = st.text_input("Senha", type="password")
        acessar = st.form_submit_button("Entrar como Cliente")

    if acessar:
        if not os.path.exists(usuarios_csv):
            st.error("Base de usuários não encontrada.")
            st.stop()

        usuarios = pd.read_csv(usuarios_csv)
        user = usuarios[(usuarios['CNPJ'] == cnpj) & (usuarios['Senha'] == senha)]

        if user.empty:
            st.error("CNPJ ou senha inválidos.")
            st.stop()

        diagnosticos = pd.read_csv(arquivo_csv) if os.path.exists(arquivo_csv) else pd.DataFrame(columns=["CNPJ", "Nome", "Email", "Empresa", "Financeiro", "Processos", "Marketing", "Vendas", "Equipe", "Média Geral", "Observações", "Diagnóstico", "Data"])
        if 'CNPJ' in diagnosticos.columns and not diagnosticos[diagnosticos['CNPJ'] == cnpj].empty:
            st.warning("✅ Diagnóstico já preenchido. Agradecemos!")
            st.stop()

        st.success("Login realizado com sucesso!")

        st.subheader("📌 Instruções do Diagnóstico")
        st.markdown("""
        - Avalie cada item com uma nota de 0 a 10.
        - Seja honesto em suas respostas para que o diagnóstico seja o mais fiel possível.
        - Após o preenchimento, você poderá baixar um PDF com o resultado.
        """)

        
        with st.form("form_diagnostico"):
            logo_cliente = st.file_uploader("📎 Envie a logo da sua empresa (opcional)", type=["png", "jpg", "jpeg"])
            nome_empresa_custom = st.text_input("📝 Nome da sua empresa", value=user.iloc[0].get('Empresa', 'Nome da Empresa'))
