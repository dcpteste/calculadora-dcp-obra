import streamlit as st
from fpdf import FPDF
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import io

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Ensaio DCP - Corsan",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== ESTILOS CSS PERSONALIZADOS ====================
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F4C81;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1rem;
        text-align: center;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1F2937;
        border-left: 5px solid #0F4C81;
        padding-left: 0.8rem;
        margin: 1.5rem 0 1rem 0;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 0.75rem;
        padding: 0.8rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-3px);
    }
    .status-approved {
        background-color: #DCFCE7;
        border-left: 6px solid #22C55E;
        padding: 1rem;
        border-radius: 0.5rem;
        font-weight: 600;
        font-size: 1.1rem;
    }
    .status-reject {
        background-color: #FEE2E2;
        border-left: 6px solid #EF4444;
        padding: 1rem;
        border-radius: 0.5rem;
        font-weight: 600;
        font-size: 1.1rem;
    }
    div[data-testid="stExpander"] details {
        border-radius: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== FUNÇÕES AUXILIARES ====================
def parse_float(valor) -> float:
    """Converte para float, aceitando string com vírgula ou ponto."""
    if valor is None or valor == "":
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    valor_limpo = str(valor).strip().replace(',', '.')
    try:
        return float(valor_limpo)
    except ValueError:
        return 0.0

def calcular_ipd(marco_zero: float, leituras: list) -> dict:
    """Calcula IPD final e evolução."""
    if not leituras:
        return {"ipd": 0.0, "golpes": 0, "ultima_leitura": 0.0, "ipd_evolucao": []}
    ultima = leituras[-1]
    golpes_total = len(leituras) * 3
    ipd_final = (ultima - marco_zero) / golpes_total if golpes_total > 0 else 0.0
    
    # Evolução do IPD a cada 3 golpes
    ipd_evolucao = []
    for i, leitura in enumerate(leituras, start=1):
        golpes = i * 3
        ipd_parcial = (leitura - marco_zero) / golpes
        ipd_evolucao.append({"golpes": golpes, "penetracao": leitura, "ipd": ipd_parcial})
    
    return {
        "ipd": ipd_final,
        "golpes": golpes_total,
        "ultima_leitura": ultima,
        "ipd_evolucao": ipd_evolucao
    }

def gerar_grafico_evolucao(ipd_evolucao: list, limite: float):
    """Cria gráfico de barras da evolução do IPD usando matplotlib."""
    if not ipd_evolucao:
        return None
    
    df = pd.DataFrame(ipd_evolucao)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(df["golpes"], df["ipd"], color='#0F4C81', alpha=0.7, edgecolor='black')
    
    # Adicionar valores nas barras
    for bar, ipd_val in zip(bars, df["ipd"]):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{ipd_val:.2f}', ha='center', va='bottom', fontsize=9)
    
    # Linha do limite
    ax.axhline(y=limite, color='red', linestyle='--', linewidth=2, label=f'Limite máximo: {limite:.2f} mm/golpe')
    
    ax.set_xlabel('Número de golpes acumulados', fontsize=12)
    ax.set_ylabel('IPD (mm/golpe)', fontsize=12)
    ax.set_title('Evolução do Índice de Penetração Dinâmico (IPD)', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)
    
    plt.tight_layout()
    return fig

def gerar_csv(leituras: list, marco_zero: float, ipd_evolucao: list) -> bytes:
    """Exporta dados em CSV."""
    dados = []
    for ponto in ipd_evolucao:
        dados.append({
            "Golpes": ponto["golpes"],
            "Penetração (mm)": ponto["penetracao"],
            "IPD Parcial (mm/golpe)": round(ponto["ipd"], 2)
        })
    df = pd.DataFrame(dados)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, sep=';', decimal=',')
    return csv_buffer.getvalue().encode('utf-8')

def gerar_pdf(dados: dict) -> bytes:
    """Gera relatório profissional em PDF com tabela e gráfico."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # Cabeçalho
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(15, 76, 129)
    pdf.cell(190, 12, "RELATÓRIO DE ENSAIO DCP", ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 6, f"Data do ensaio: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", ln=True, align='C')
    pdf.ln(8)
    
    # Dados da obra
    pdf.set_font("Arial", "B", 12)
    pdf.set_fill_color(240, 248, 255)
    pdf.cell(190, 8, "DADOS DA OBRA", border=1, ln=True, fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 8, f"OS / Contrato: {dados['os']}", border=1)
    pdf.cell(95, 8, f"Material: {dados['material']}", border=1, ln=True)
    pdf.multi_cell(190, 8, f"Local / Endereço: {dados['endereco']}", border=1)
    if dados.get('operador'):
        pdf.cell(190, 8, f"Operador: {dados['operador']}", border=1, ln=True)
    if dados.get('equipamento'):
        pdf.cell(190, 8, f"Equipamento: {dados['equipamento']}", border=1, ln=True)
    pdf.ln(4)
    
    # Parâmetros
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 8, "PARÂMETROS DE REFERÊNCIA", border=1, ln=True, fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 8, f"Limite aceitável (IPD máx): {dados['limite_ref']:.2f} mm/golpe", border=1)
    pdf.cell(95, 8, f"Penetração inicial: {dados['marco_zero']:.1f} mm", border=1, ln=True)
    pdf.ln(4)
    
    # Tabela de leituras
    pdf.set_font("Arial", "B", 11)
    pdf.cell(45, 10, "Golpes", border=1, align='C')
    pdf.cell(55, 10, "Penetração (mm)", border=1, align='C')
    pdf.cell(90, 10, "IPD Parcial (mm/golpe)", border=1, align='C', ln=True)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(45, 8, "0", border=1, align='C')
    pdf.cell(55, 8, f"{dados['marco_zero']:.1f}", border=1, align='C')
    pdf.cell(90, 8, "-", border=1, align='C', ln=True)
    
    for i, leitura in enumerate(dados['leituras'], start=1):
        golpes = i * 3
        ipd_parcial = (leitura - dados['marco_zero']) / golpes
        pdf.cell(45, 8, str(golpes), border=1, align='C')
        pdf.cell(55, 8, f"{leitura:.1f}", border=1, align='C')
        pdf.cell(90, 8, f"{ipd_parcial:.2f}", border=1, align='C', ln=True)
    
    # Resultado final
    pdf.ln(8)
    pdf.set_font("Arial", "B", 13)
    cor = (34, 197, 94) if dados['status'] == "APROVADO" else (239, 68, 68)
    pdf.set_text_color(*cor)
    pdf.cell(190, 10, f"STATUS: {dados['status']}", border=1, ln=True, align='C')
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 9, f"IPD FINAL: {dados['ipd_final']:.2f} mm/golpe", border=1, ln=True, align='C')
    
    # Rodapé
    pdf.ln(15)
    pdf.set_y(-20)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(190, 5, "Relatório gerado pelo sistema Corsan - Ensaio DCP", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1', errors='ignore')

# ==================== INICIALIZAÇÃO SESSION STATE ====================
if 'leituras' not in st.session_state:
    st.session_state.leituras = []
if 'material' not in st.session_state:
    st.session_state.material = "BGS"
if 'limites' not in st.session_state:
    st.session_state.limites = {"BGS": 6.0, "Solo": 17.0, "Areia": 22.0}

# ==================== BARRA LATERAL ====================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2286/2286093.png", width=50)
    st.markdown("## ⚙️ Configurações")
    
    st.markdown("### Limites de IPD por material")
    novo_bgs = st.number_input("🟤 BGS (mm/golpe)", value=st.session_state.limites["BGS"], step=0.1, format="%.2f")
    novo_solo = st.number_input("🟠 Solo (mm/golpe)", value=st.session_state.limites["Solo"], step=0.1, format="%.2f")
    novo_areia = st.number_input("🟡 Areia (mm/golpe)", value=st.session_state.limites["Areia"], step=0.1, format="%.2f")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("💾 Salvar", use_container_width=True):
            st.session_state.limites["BGS"] = novo_bgs
            st.session_state.limites["Solo"] = novo_solo
            st.session_state.limites["Areia"] = novo_areia
            st.success("Limites salvos!")
    with col_s2:
        if st.button("🔄 Padrões", use_container_width=True):
            st.session_state.limites["BGS"] = 6.0
            st.session_state.limites["Solo"] = 17.0
            st.session_state.limites["Areia"] = 22.0
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📘 Sobre o ensaio")
    st.caption("O Índice de Penetração Dinâmico (IPD) mede a resistência do solo. Valores baixos indicam maior compactação.")
    st.caption("**Cálculo:** IPD = (penetração final - inicial) / número total de golpes.")

# ==================== INTERFACE PRINCIPAL ====================
st.markdown('<div class="main-title">🏗️ Ensaio de Compactação DCP</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Corsan - Controle de qualidade de aterros e bases</div>', unsafe_allow_html=True)

# --- 1. IDENTIFICAÇÃO ---
with st.expander("📋 1. Dados da obra e operador", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        os_id = st.text_input("Número da OS / Contrato", placeholder="Ex: 2025-001")
        endereco = st.text_input("Local / Endereço", placeholder="Rua, obra, trecho...")
    with col2:
        operador = st.text_input("Nome do operador", placeholder="Responsável pelo ensaio")
        equipamento = st.text_input("Equipamento / Série", placeholder="DCP modelo, número de série")

# --- 2. MATERIAL ---
st.markdown('<div class="section-header">🧱 2. Material ensaiado</div>', unsafe_allow_html=True)
col_mat1, col_mat2, col_mat3 = st.columns(3)
with col_mat1:
    if st.button("🟤 BGS", use_container_width=True):
        st.session_state.material = "BGS"
with col_mat2:
    if st.button("🟠 Solo", use_container_width=True):
        st.session_state.material = "Solo"
with col_mat3:
    if st.button("🟡 Areia", use_container_width=True):
        st.session_state.material = "Areia"

limite_atual = st.session_state.limites[st.session_state.material]
st.info(f"📌 Material selecionado: **{st.session_state.material}** | **IPD máximo aceitável: ≤ {limite_atual:.2f} mm/golpe**")

# --- 3. MARCO ZERO ---
st.markdown('<div class="section-header">📍 3. Ponto inicial (Marco zero)</div>', unsafe_allow_html=True)
col_mz, col_ajuda = st.columns([2, 1])
with col_mz:
    marco_zero_input = st.text_input("Penetração inicial (mm)", value="0.0", help="Leitura antes de iniciar a cravação do DCP")
    marco_zero = parse_float(marco_zero_input)
with col_ajuda:
    st.caption("💡 Dica: normalmente inicia-se em 0 mm, mas pode ser ajustado se houver pré-cravação.")

# --- 4. LEITURAS ---
st.markdown('<div class="section-header">📊 4. Leituras a cada 3 golpes</div>', unsafe_allow_html=True)
st.caption("Registre a **penetração total acumulada** (mm) a cada 3 golpes. Ex: após 3 golpes, meça; após 6, meça; etc.")

# Exibir registros existentes
for idx, leitura in enumerate(st.session_state.leituras):
    col_val, col_del = st.columns([5, 1])
    with col_val:
        novo_val = st.text_input(
            f"Leitura aos {(idx+1)*3} golpes (mm)",
            value=f"{leitura:.1f}",
            key=f"leitura_{idx}"
        )
        nova_leitura = parse_float(novo_val)
        # Validação: penetração deve ser >= anterior e >= marco zero
        if idx > 0 and nova_leitura < st.session_state.leituras[idx-1]:
            st.warning(f"⚠️ A penetração não pode diminuir. Valor anterior: {st.session_state.leituras[idx-1]:.1f} mm")
        elif nova_leitura < marco_zero:
            st.warning(f"⚠️ A penetração não pode ser menor que o marco zero ({marco_zero:.1f} mm)")
        else:
            st.session_state.leituras[idx] = nova_leitura
    with col_del:
        st.write("")
        st.write("")
        if st.button("🗑️", key=f"del_{idx}"):
            st.session_state.leituras.pop(idx)
            st.rerun()

col_add, col_clear, col_export = st.columns(3)
with col_add:
    if st.button("➕ Adicionar leitura (3 golpes)", use_container_width=True):
        ultimo = st.session_state.leituras[-1] if st.session_state.leituras else marco_zero
        st.session_state.leituras.append(ultimo)
        st.rerun()
with col_clear:
    if st.button("🧹 Limpar todas", use_container_width=True):
        st.session_state.leituras.clear()
        st.rerun()
with col_export:
    if st.session_state.leituras:
        calculo_temp = calcular_ipd(marco_zero, st.session_state.leituras)
        csv_data = gerar_csv(st.session_state.leituras, marco_zero, calculo_temp["ipd_evolucao"])
        st.download_button(
            label="📎 Exportar CSV",
            data=csv_data,
            file_name=f"DCP_dados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# --- 5. RESULTADOS, GRÁFICO E PDF ---
if st.session_state.leituras:
    calculo = calcular_ipd(marco_zero, st.session_state.leituras)
    ipd_final = calculo["ipd"]
    golpes_total = calculo["golpes"]
    status = "APROVADO" if ipd_final <= limite_atual else "RECOMPACTAR"
    
    st.divider()
    st.markdown('<div class="section-header">📈 5. Resultado da compactação</div>', unsafe_allow_html=True)
    
    # Métricas em destaque
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("IPD Final", f"{ipd_final:.2f} mm/golpe", 
                  delta=f"Limite: {limite_atual:.2f}", delta_color="inverse")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total de golpes", f"{golpes_total}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_m3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Penetração final", f"{calculo['ultima_leitura']:.1f} mm")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Status com estilo
    if status == "APROVADO":
        st.markdown(f'<div class="status-approved">✅ STATUS: {status} - O IPD está dentro do limite aceitável para {st.session_state.material}.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-reject">⚠️ STATUS: {status} - O IPD excede o limite máximo de {limite_atual:.2f} mm/golpe. Recomenda-se nova compactação e reensaio.</div>', unsafe_allow_html=True)
    
    # Gráfico de evolução (matplotlib)
    st.markdown("### 📉 Evolução do IPD")
    fig = gerar_grafico_evolucao(calculo["ipd_evolucao"], limite_atual)
    if fig:
        st.pyplot(fig)
        plt.close(fig)  # Fechar figura para liberar memória
    
    # Tabela detalhada
    with st.expander("📋 Ver tabela detalhada de leituras"):
        df_table = pd.DataFrame(calculo["ipd_evolucao"])
        df_table = df_table.rename(columns={"golpes": "Golpes", "penetracao": "Penetração (mm)", "ipd": "IPD (mm/golpe)"})
        st.dataframe(df_table.style.format({"IPD (mm/golpe)": "{:.2f}", "Penetração (mm)": "{:.1f}"}), use_container_width=True)
    
    # Botões de relatório
    if os_id and endereco:
        dados_pdf = {
            "os": os_id,
            "endereco": endereco,
            "material": st.session_state.material,
            "marco_zero": marco_zero,
            "leituras": st.session_state.leituras,
            "ipd_final": ipd_final,
            "status": status,
            "limite_ref": limite_atual,
            "operador": operador,
            "equipamento": equipamento
        }
        pdf_bytes = gerar_pdf(dados_pdf)
        col_pdf, col_vazio = st.columns([1, 1])
        with col_pdf:
            st.download_button(
                label="📄 Baixar Relatório PDF",
                data=pdf_bytes,
                file_name=f"DCP_{st.session_state.material}_OS_{os_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    else:
        st.warning("⚠️ Preencha o número da OS e o local/endereço para gerar o relatório completo.")
else:
    st.info("👆 Adicione pelo menos uma leitura de penetração para calcular o IPD e visualizar o gráfico.")

# Rodapé
st.markdown("---")
st.caption("Ensaio de Cone Dinâmico (DCP) - Cálculo do IPD conforme normas. Em caso de dúvidas, consulte a supervisão técnica.")
