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

if not os.path.exists(usuarios_bloqueados_csv):
    pd.DataFrame(columns=["CNPJ"]).to_csv(usuarios_bloqueados_csv, index=False)

if not os.path.exists(admin_credenciais_csv):
    df_admin = pd.DataFrame([["admin", "potencialize"]], columns=["Usuario", "Senha"])
    df_admin.to_csv(admin_credenciais_csv, index=False)

if not os.path.exists(usuarios_csv):
    df_usuarios = pd.DataFrame(columns=["CNPJ", "Senha", "Empresa"])
    df_usuarios.to_csv(usuarios_csv, index=False)

if not os.path.exists(arquivo_csv):
    df_diagnosticos = pd.DataFrame(
        columns=[
            "Data", "CNPJ", "Nome", "Email", "Empresa", "Financeiro", "Processos",
            "Marketing", "Vendas", "Equipe", "Média Geral", "Observações", "Diagnóstico"
        ]
    )
    df_diagnosticos.to_csv(arquivo_csv, index=False)

st.markdown(
    """
    <style>
    .css-1d391kg, .css-18e3th9 {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
    div[data-testid="stHorizontalBlock"] > div:first-child {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .login-container {
        background-color: #f0f2f6;
        padding: 40px;
        border-radius: 8px;
        max-width: 400px;
        margin: 40px auto;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    </style>
    """, unsafe_allow_html=True
)

st.markdown("## \U0001F512 Portal de Acesso")

if not st.session_state.admin_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True)
else:
    aba = "Administrador"

# Login Administrador
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
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

# Painel Admin
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
        st.rerun()

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
            st.success(f"CNPJ {cnpj_desbloq} desbloqueado com sucesso!")

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

# Login Cliente e diagnóstico
if aba == "Cliente":
    if not st.session_state.cliente_logado:
        st.markdown(
            """
            <style>
            .login-container {
                background-color: #f0f2f6;
                padding: 40px;
                border-radius: 8px;
                max-width: 400px;
                margin: 40px auto;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            div[data-testid="stHorizontalBlock"] > div:first-child {
                display: none !important;
                height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("<h2 style='margin-bottom:20px;'>Login Cliente</h2>", unsafe_allow_html=True)

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

            if cnpj in bloqueados["CNPJ"].values:
                st.error("Este CNPJ está bloqueado. Solicite liberação ao administrador.")
                st.stop()

            user = usuarios[(usuarios["CNPJ"] == cnpj) & (usuarios["Senha"] == senha)]

            if user.empty:
                st.error("CNPJ ou senha inválidos.")
                st.stop()

            st.session_state.cliente_logado = True
            st.session_state.cnpj = cnpj
            st.session_state.user = user
            st.success("Login realizado com sucesso!")
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        cnpj = st.session_state.cnpj
        user = st.session_state.user

        if st.session_state.diagnostico_enviado:
            st.success("✅ Diagnóstico já enviado. Obrigado!")
            with open(f"diagnostico_{cnpj}.pdf", "rb") as f:
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "📄 Baixar PDF do Diagnóstico",
                        f,
                        file_name="diagnostico.pdf",
                        mime="application/pdf",
                        key="download_pdf",
                    )
                with col2:
                    if st.button("Finalização do processo"):
                        st.session_state.cliente_logado = False
                        st.session_state.diagnostico_enviado = False
                        st.session_state.cnpj = None
                        st.session_state.user = None
                        st.experimental_rerun()

            st.stop()

        st.subheader("📌 Instruções do Diagnóstico")
        st.markdown(
            """
            - Avalie cada item com uma nota de 0 a 10.
            - Seja honesto em suas respostas para que o diagnóstico seja o mais fiel possível.
            - Após o preenchimento, você poderá baixar um PDF com o resultado.
            """
        )

        with st.form("form_diagnostico"):
            logo_cliente = st.file_uploader(
                "📎 Envie a logo da sua empresa (opcional)", type=["png", "jpg", "jpeg"]
            )
            nome_empresa_custom = st.text_input(
                "📝 Nome da sua empresa", value=user.iloc[0].get("Empresa", "Nome da Empresa")
            )
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
            st.session_state.diagnostico_enviado = True

            class PDF(FPDF):
                def header(self):
                    if hasattr(self, "logo_path") and self.logo_path:
                        self.image(self.logo_path, x=10, y=8, w=30)
                    self.set_font("Arial", "B", 16)
                    self.cell(
                        0,
                        10,
                        "Diagnóstico Empresarial - Potencialize Resultados",
                        ln=True,
                        align="C",
                    )
                    self.ln(10)

                def footer(self):
                    self.set_y(-15)
                    self.set_font("Arial", "I", 8)
                    self.set_text_color(128)
                    self.cell(
                        0,
                        10,
                        f"Potencialize Resultados - Diagnóstico Automático | Página {self.page_no()}",
                        align="C",
                    )

            media_geral = round(
                (financeiro + processos + marketing + vendas + equipe) / 5, 2
            )
            insights = []
            if financeiro < 6:
                insights.append("Controle financeiro necessita de atenção.")
            if processos < 6:
                insights.append("Processos internos abaixo do ideal.")
            if marketing < 6:
                insights.append("Estratégia de marketing pode ser melhorada.")
            if vendas < 6:
                insights.append("Resultados comerciais abaixo da média.")
            if equipe < 6:
                insights.append("Desempenho da equipe pode estar comprometido.")

            diagnostico_texto = (
                "\n".join(insights)
                if insights
                else "Nenhuma área crítica identificada. Excelente desempenho geral."
            )

            resposta = pd.DataFrame(
                [
                    {
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
                        "Diagnóstico": diagnostico_texto.replace("\n", " "),
                    }
                ]
            )

            if os.path.exists(arquivo_csv):
                antigo = pd.read_csv(arquivo_csv)
                resultado = pd.concat([antigo, resposta], ignore_index=True)
            else:
                resultado = resposta

            resultado.to_csv(arquivo_csv, index=False)

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
            texto_pdf = f"""Financeiro: {financeiro}
Processos: {processos}
Marketing: {marketing}
Vendas: {vendas}
Equipe: {equipe}

Média Geral: {media_geral}

Observações:
{observacoes}

Diagnóstico Automático:
{diagnostico_texto}"""
            texto_pdf = texto_pdf.encode("latin-1", "ignore").decode("latin-1")
            pdf.multi_cell(0, 10, texto_pdf)
            pdf_output = f"diagnostico_{cnpj}.pdf"
            pdf.output(pdf_output)

            st.experimental_rerun()
