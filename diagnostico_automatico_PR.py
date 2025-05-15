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
