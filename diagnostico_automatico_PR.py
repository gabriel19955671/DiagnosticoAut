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

        diagnosticos = pd.read_csv(arquivo_csv) if os.path.exists(arquivo_csv) else pd.DataFrame()
        if not diagnosticos[diagnosticos['CNPJ'] == cnpj].empty:
            st.warning("✅ Diagnóstico já preenchido. Agradecemos!")
            st.stop()

        st.success("Login realizado com sucesso!")

        st.subheader("📌 Instruções do Diagnóstico")
        st.markdown("""
        - Avalie cada item com uma nota de 0 a 10.
        - Seja honesto em suas respostas para que o diagnóstico seja o mais fiel possível.
        - Após o preenchimento, você poderá baixar um PDF com o resultado.
        """)

        logo_cliente = st.file_uploader("📎 Envie a logo da sua empresa (opcional)", type=["png", "jpg", "jpeg"])
        nome_empresa_custom = st.text_input("📝 Nome da sua empresa", value=user.iloc[0]['Empresa'])

        with st.form("form_diagnostico"):
            nome = st.text_input("Nome completo")
            email = st.text_input("E-mail")
            financeiro = st.slider("Controle financeiro da empresa", 0, 10)
            processos = st.slider("Eficiência dos processos internos", 0, 10)
            marketing = st.slider("Presença e estratégia de marketing", 0, 10)
            vendas = st.slider("Resultado comercial (vendas/negociação)", 0, 10)
            equipe = st.slider("Desempenho da equipe/colaboradores", 0, 10)
            observacoes = st.text_area("Observações adicionais (opcional)")
            enviado = st.form_submit_button("🚀 Enviar Diagnóstico")

        if enviado:
            media_geral = round((financeiro + processos + marketing + vendas + equipe) / 5, 2)

            insights = []
            if financeiro < 6:
                insights.append("Controle financeiro necessita de atencao.")
            if processos < 6:
                insights.append("Processos internos abaixo do ideal.")
            if marketing < 6:
                insights.append("Estrategia de marketing pode ser melhorada.")
            if vendas < 6:
                insights.append("Resultados comerciais abaixo da media.")
            if equipe < 6:
                insights.append("Desempenho da equipe pode estar comprometido.")

            diagnostico_texto = "\n".join(insights) if insights else "Nenhuma area critica identificada. Excelente desempenho geral."

            resposta = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "CNPJ": cnpj,
                "Nome": nome,
                "Email": email,
                "Empresa": nome_empresa_custom,
                "Financeiro": financeiro,
                "Processos": processos,
                "Marketing": marketing,
                "Vendas": vendas,
                "Equipe": equipe,
                "Média Geral": media_geral,
                "Observações": observacoes,
                "Diagnóstico": diagnostico_texto.replace("\n", " ")
            }])

            if os.path.exists(arquivo_csv):
                antigo = pd.read_csv(arquivo_csv)
                resultado = pd.concat([antigo, resposta], ignore_index=True)
            else:
                resultado = resposta

            resultado.to_csv(arquivo_csv, index=False)

            class PDF(FPDF):
                def header(self):
                    if hasattr(self, 'logo_path') and self.logo_path:
                        self.image(self.logo_path, x=10, y=8, w=30)
                    self.set_font("Arial", 'B', 16)
                    self.cell(0, 10, "Diagnóstico Empresarial - Potencialize Resultados", ln=True, align='C')
                    self.ln(10)

                def footer(self):
                    self.set_y(-15)
                    self.set_font("Arial", "I", 8)
                    self.set_text_color(128)
                    self.cell(0, 10, f"Potencialize Resultados - Diagnóstico Automático | Página {self.page_no()}", align='C')

            pdf = PDF()
            if logo_cliente is not None:
                img_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                img_temp.write(logo_cliente.read())
                img_temp.close()
                pdf.logo_path = img_temp.name
            else:
                pdf.logo_path = None

            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
            pdf.cell(0, 10, f"Nome: {nome}", ln=True)
            pdf.cell(0, 10, f"E-mail: {email}", ln=True)
            pdf.cell(0, 10, f"Empresa: {nome_empresa_custom}", ln=True)
            pdf.ln(5)
            texto_pdf = f"Financeiro: {financeiro}\nProcessos: {processos}\nMarketing: {marketing}\nVendas: {vendas}\nEquipe: {equipe}\n\nMedia Geral: {media_geral}\n\nObservacoes:\n{observacoes}\n\nDiagnostico Automatico:\n{diagnostico_texto}"
            texto_pdf = texto_pdf.encode("latin-1", "ignore").decode("latin-1")
            pdf.multi_cell(0, 10, texto_pdf)

            pdf_output = f"diagnostico_{cnpj}.pdf"
            pdf.output(pdf_output)

            with open(pdf_output, "rb") as f:
                st.download_button("📄 Baixar PDF do Diagnóstico", f, file_name="diagnostico.pdf", mime="application/pdf")

            st.success("✅ Diagnóstico enviado, analisado e PDF gerado com sucesso!")
