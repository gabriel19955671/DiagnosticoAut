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
