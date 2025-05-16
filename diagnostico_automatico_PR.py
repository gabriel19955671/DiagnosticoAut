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
if "cliente_logado" not in st.session_state:
    st.session_state.cliente_logado = False
if "diagnostico_enviado" not in st.session_state:
    st.session_state.diagnostico_enviado = False

if not os.path.exists(usuarios_bloqueados_csv):
    pd.DataFrame(columns=["CNPJ"]).to_csv(usuarios_bloqueados_csv, index=False)

if not os.path.exists(admin_credenciais_csv):
    df_admin = pd.DataFrame([["admin", "potencialize"]], columns=["Usuario", "Senha"])
    df_admin.to_csv(admin_credenciais_csv, index=False)

# Título simples, sem st.title para evitar espaçamento extra
st.markdown("## \U0001F512 Portal de Acesso")

if not st.session_state.admin_logado:
    aba = st.radio("Você é:", ["Administrador", "Cliente"], horizontal=True)
else:
    aba = "Administrador"

# Login administrador
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

# Painel administrador (adicione aqui suas funcionalidades administrativas)

if aba == "Administrador" and st.session_state.admin_logado:
    st.success("\U0001F513 Painel Administrativo Ativo")
    menu_admin = st.selectbox(
        "Selecione a funcionalidade administrativa:",
        [
            "\U0001F4CA Visualizar Diagnósticos",
            "\U0001F501 Reautorizar Cliente",
            "\U0001F465 Gerenciar Usuários",
            "🔒 Gerenciar Bloqueios",
            "\U0001F6E1️ Gerenciar Administradores",
        ],
    )

    if st.sidebar.button("\U0001F513 Sair do Painel Admin"):
        st.session_state.admin_logado = False
        st.rerun()

    # Aqui você insere o código que já tinha para cada menu do admin

# LOGIN CLIENTE SEM ESPAÇO EXTRA
if aba == "Cliente":
    if not st.session_state.cliente_logado:

        # CSS para remover espaço em branco acima do login cliente
        st.markdown(
            """
            <style>
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
            """,
            unsafe_allow_html=True,
      
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
        # Cliente logado - formulário diagnóstico
        cnpj = st.session_state.cnpj
        user = st.session_state.user

        if st.session_state.diagnostico_enviado:
            st.success("✅ Diagnóstico já enviado. Obrigado!")
            if os.path.exists(f"diagnostico_{cnpj}.pdf"):
                with open(f"diagnostico_{cnpj}.pdf", "rb") as f:
                    st.download_button(
                        "📄 Baixar PDF do Diagnóstico",
                        f,
                        file_name="diagnostico.pdf",
                        mime="application/pdf",
                        key="download_pdf",
                    )

            if st.session_state.get("download_pdf"):
                st.session_state.cliente_logado = False
                st.session_state.diagnostico_enviado = False
                st.session_state.cnpj = None
                st.session_state.user = None
                streamlit_js_eval(js_expressions="parent.window.location.reload()")
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

            with open(pdf_output, "rb") as f:
                st.download_button(
                    "📄 Baixar PDF do Diagnóstico",
                    f,
                    file_name="diagnostico.pdf",
                    mime="application/pdf",
                )

            st.success("✅ Diagnóstico enviado, analisado e PDF gerado com sucesso!")
