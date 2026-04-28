import streamlit as st
from fpdf import FPDF
from datetime import datetime
import re

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Ensaio DCP - Corsan",
    page_icon="🏗️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ==================== ESTILOS CSS PERSONALIZADOS ====================
st.markdown("""
<style>
    /* Cabeçalhos */
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
    /* Cards e métricas */
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 0.75rem;
        padding: 0.8rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .status-approved {
        background-color: #DCFCE7;
        border-left: 6px solid #22C55E;
        padding: 0.8rem;
        border-radius: 0.5rem;
        font-weight: 600;
    }
    .status-reject {
        background-color: #FEE2E2;
        border-left: 6px solid #EF4444;
        padding: 0.8rem;
        border-radius: 0.5rem;
        font-weight: 600;
    }
    /* Botões customizados */
    .stButton > button {
        border-radius: 0.5rem;
        font-weight: 500;
    }
    /* Inputs com foco */
    .stTextInput > div > div > input:focus, .stNumberInput > div > div > input:focus {
        border-color: #0F4C81;
        box-shadow: 0 0 0 2px rgba(15,76,129,0.2);
    }
</style>
""", unsafe_allow_html=True)

# ==================== FUNÇÕES AUXILIARES ====================
def parse_float(valor_str: str) -> float:
    """Converte string com vírgula ou ponto para float."""
    if not valor_str:
        return 0.0
    valor_limpo = valor_str.strip().replace(',', '.')
    try:
        return float(valor_limpo)
    except ValueError:
        return 0.0

def calcular_ipd(marco_zero: float, leituras: list) -> dict:
    """Calcula IPD final e status com base no limite fornecido."""
    if not leituras:
        return {"ipd": 0.0, "golpes": 0, "status": "SEM DADOS"}
    ultima = leituras[-1]
    golpes_total = len(leituras) * 3
    ipd = (ultima - marco_zero) / golpes_total if golpes_total > 0 else 0.0
    return {"ipd": ipd, "golpes": golpes_total, "ultima_leitura": ultima}

def gerar_pdf(dados: dict) -> bytes:
    """Gera relatório profissional em PDF."""
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
    pdf.ln(4)
    
    # Parâmetros de referência
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 8, "PARÂMETROS DE REFERÊNCIA", border=1, ln=True, fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 8, f"Limite aceitável (IPD máx): {dados['limite_ref']:.2f} mm/golpe", border=1)
    pdf.cell(95, 8, f"Penetração inicial (marco zero): {dados['marco_zero']:.1f} mm", border=1, ln=True)
    pdf.ln(4)
    
    # Tabela de leituras
    pdf.set_font("Arial", "B", 11)
    pdf.cell(45, 10, "Golpes", border=1, align='C')
    pdf.cell(55, 10, "Penetração (mm)", border=1, align='C')
    pdf.cell(90, 10, "IPD Parcial (mm/golpe)", border=1, align='C', ln=True)
    
    pdf.set_font("Arial", "", 10)
    # Linha do marco zero
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

# ==================== INICIALIZAÇÃO DO SESSION STATE ====================
if 'leituras' not in st.session_state:
    st.session_state.leituras = []  # armazena floats
if 'material' not in st.session_state:
    st.session_state.material = "BGS"
if 'limites' not in st.session_state:
    st.session_state.limites = {"BGS": 6.0, "Solo": 17.0, "Areia": 22.0}

# ==================== BARRA LATERAL (CONFIGURAÇÕES) ====================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2286/2286093.png", width=50)  # opcional
    st.markdown("## ⚙️ Configurações")
    st.markdown("Ajuste os limites de IPD aceitáveis para cada material:")
    
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
        if st.button("🔄 Resetar padrões", use_container_width=True):
            st.session_state.limites["BGS"] = 6.0
            st.session_state.limites["Solo"] = 17.0
            st.session_state.limites["Areia"] = 22.0
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📋 Sobre o ensaio")
    st.caption("O Índice de Penetração Dinâmico (IPD) mede a resistência do solo. Valores baixos indicam maior compactação. O limite aceitável varia conforme o material.")

# ==================== INTERFACE PRINCIPAL ====================
st.markdown('<div class="main-title">🏗️ Ensaio de Compactação DCP</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Corsan - Controle de qualidade de aterros e bases</div>', unsafe_allow_html=True)

# --- 1. INFORMAÇÕES DA OBRA ---
st.markdown('<div class="section-header">📋 1. Identificação da obra</div>', unsafe_allow_html=True)
col_os, col_local = st.columns(2)
with col_os:
    os_id = st.text_input("Número da OS / Contrato", placeholder="Ex: 2025-001")
with col_local:
    endereco = st.text_input("Local / Endereço", placeholder="Rua, obra, trecho...")

# --- 2. TIPO DE MATERIAL ---
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
marco_zero_input = st.text_input("Penetração inicial (mm)", value="0.0")
marco_zero = parse_float(marco_zero_input)

# --- 4. LEITURAS A CADA 3 GOLPES ---
st.markdown('<div class="section-header">📊 4. Leituras de penetração</div>', unsafe_allow_html=True)
st.caption("Registre a profundidade total (mm) a cada 3 golpes, sem zerar o equipamento.")

# Exibir leituras existentes com botão de remoção
for idx, leitura in enumerate(st.session_state.leituras):
    col_val, col_del = st.columns([5, 1])
    with col_val:
        novo_val = st.text_input(
            f"Leitura aos {(idx+1)*3} golpes (mm)",
            value=f"{leitura:.1f}",
            key=f"leitura_{idx}"
        )
        st.session_state.leituras[idx] = parse_float(novo_val)
    with col_del:
        st.write("")
        st.write("")
        if st.button("🗑️", key=f"del_{idx}"):
            st.session_state.leituras.pop(idx)
            st.rerun()

# Botão para adicionar nova leitura
col_add, col_clear = st.columns(2)
with col_add:
    if st.button("➕ Adicionar leitura (3 golpes)", use_container_width=True):
        st.session_state.leituras.append(0.0)
        st.rerun()


# --- 5. RESULTADO E CÁLCULOS ---
if st.session_state.leituras:
    calculo = calcular_ipd(marco_zero, st.session_state.leituras)
    ipd_final = calculo["ipd"]
    golpes_total = calculo["golpes"]
    status = "APROVADO" if ipd_final <= limite_atual else "RECOMPACTAR"
    
    st.divider()
    st.markdown('<div class="section-header">📈 5. Resultado da compactação</div>', unsafe_allow_html=True)
    
    col_metric1, col_metric2, col_metric3 = st.columns(3)
    with col_metric1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("IPD Final", f"{ipd_final:.2f} mm/golpe")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_metric2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total de golpes", f"{golpes_total}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_metric3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Penetração final", f"{calculo['ultima_leitura']:.1f} mm")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Status visual
    if status == "APROVADO":
        st.markdown(f'<div class="status-approved">✅ STATUS: {status} - O IPD está dentro do limite aceitável para {st.session_state.material}.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-reject">⚠️ STATUS: {status} - O IPD excede o limite máximo de {limite_atual:.2f} mm/golpe. Recomenda-se nova compactação e reensaio.</div>', unsafe_allow_html=True)
    
    # Botão de gerar PDF
    if os_id and endereco:
        dados_pdf = {
            "os": os_id,
            "endereco": endereco,
            "material": st.session_state.material,
            "marco_zero": marco_zero,
            "leituras": st.session_state.leituras,
            "ipd_final": ipd_final,
            "status": status,
            "limite_ref": limite_atual
        }
        pdf_bytes = gerar_pdf(dados_pdf)
        st.download_button(
            label="📄 Baixar Relatório em PDF",
            data=pdf_bytes,
            file_name=f"DCP_{st.session_state.material}_OS_{os_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.warning("⚠️ Preencha o número da OS e o local/endereço para habilitar o download do relatório.")
else:
    st.info("👆 Adicione pelo menos uma leitura de penetração para calcular o IPD.")

# Pequeno rodapé informativo na página
st.markdown("---")
st.caption("Ensaio de Cone Dinâmico (DCP) conforme normas técnicas. O Índice de Penetração Dinâmico (IPD) é calculado pela diferença de penetração dividida pelo número de golpes.")
