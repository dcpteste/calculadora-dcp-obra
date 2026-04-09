import streamlit as st
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="DCP Corsan", layout="centered")

# --- MEMÓRIA E CONFIGURAÇÕES ---
if 'material' not in st.session_state: st.session_state.material = "BGS"
if 'batidas' not in st.session_state: st.session_state.batidas = []
if 'limites' not in st.session_state:
    st.session_state.limites = {"BGS": 6.0, "Solo": 17.0, "Areia": 22.0}

# --- FUNÇÃO PARA GERAR PDF ---
def gerar_pdf(dados_ensaio):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # Cabeçalho
    pdf.cell(200, 10, "RELATORIO DE ENSAIO DCP", ln=True, align='C')
    pdf.set_font("Arial", "", 12)
    pdf.ln(5)
    
    # Informações da OS e Local
    pdf.set_font("Arial", "B", 10)
    pdf.cell(190, 8, "DADOS GERAIS", border="B", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 10, f"OS: {dados_ensaio['os']}", border=1)
    pdf.cell(95, 10, f"Data: {datetime.now().strftime('%d/%m/%Y')}", border=1, ln=True)
    pdf.multi_cell(190, 10, f"Local: {dados_ensaio['endereco']}", border=1)
    
    # --- NOVA SEÇÃO DE PARÂMETROS ---
    pdf.ln(2)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(190, 8, "PARAMETROS DE REFERENCIA", border="B", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 10, f"Material Selecionado: {dados_ensaio['material']}", border=1)
    pdf.cell(95, 10, f"Limite Aceitavel: <= {dados_ensaio['limite_ref']:.2f} mm/golpe", border=1, ln=True)
    pdf.ln(5)
    
    # Tabela de Batidas
    pdf.set_font("Arial", "B", 10)
    pdf.cell(60, 10, "N. de Golpes", border=1, align='C')
    pdf.cell(60, 10, "Penetracao (mm)", border=1, align='C')
    pdf.cell(70, 10, "IPD Acumulado", border=1, align='C', ln=True)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 10, "0", border=1, align='C')
    pdf.cell(60, 10, f"{dados_ensaio['m_zero']}", border=1, align='C')
    pdf.cell(70, 10, "-", border=1, align='C', ln=True)
    
    for i, leitura in enumerate(dados_ensaio['leituras']):
        golpes = (i+1)*3
        ipd_parcial = (leitura - dados_ensaio['m_zero']) / golpes
        pdf.cell(60, 10, f"{golpes}", border=1, align='C')
        pdf.cell(60, 10, f"{leitura}", border=1, align='C')
        pdf.cell(70, 10, f"{ipd_parcial:.2f} mm/g", border=1, align='C', ln=True)
    
    # Resultado Final
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    # Cor de fundo no resultado (opcional)
    if dados_ensaio['status'] == "APROVADO":
        pdf.set_text_color(0, 128, 0) # Verde
    else:
        pdf.set_text_color(255, 0, 0) # Vermelho
        
    pdf.cell(190, 12, f"STATUS FINAL: {dados_ensaio['status']}", border=1, ln=True, align='C')
    pdf.set_text_color(0, 0, 0) # Volta pra preto
    pdf.cell(190, 12, f"IPD CALCULADO: {dados_ensaio['ipd_final']:.2f} mm/golpe", border=1, ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')
# --- INTERFACE PRINCIPAL ---
st.title("🏗️ Registro DCP ")

# Passo 1
st.header("1. Identificação")
num_os = st.text_input("Número da OS")
endereco = st.text_area("Local/Endereço")

st.write("**Selecione o Material:**")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("BGS", use_container_width=True): st.session_state.material = "BGS"
with c2:
    if st.button("Solo", use_container_width=True): st.session_state.material = "Solo"
with c3:
    if st.button("Areia", use_container_width=True): st.session_state.material = "Areia"

# --- AQUI VOLTOU A LINHA DE INFORMAÇÃO DO MATERIAL ---
limite_v = st.session_state.limites[st.session_state.material]
st.info(f"Material Selecionado: **{st.session_state.material}** | Valor Aceitável: **≤ {limite_v} mm/golpe**")

# Passo 2
st.header("2. Marco Zero")
val_marco = st.text_input("Penetração Inicial (mm)", value="0")
try: marco_zero = float(val_marco.replace(',', '.'))
except: marco_zero = 0.0

# Passo 3
st.header("3. Leituras (3 em 3)")
for i, valor in enumerate(st.session_state.batidas):
    col_c, col_l = st.columns([0.8, 0.2])
    with col_c:
        st.session_state.batidas[i] = st.text_input(f"Leitura aos {(i+1)*3} golpes (mm)", value=valor, key=f"b_{i}")
    with col_l:
        st.write(""); st.write("")
        if st.button("🗑️", key=f"d_{i}"):
            st.session_state.batidas.pop(i)
            st.rerun()

if st.button("➕ Adicionar Batidas", use_container_width=True):
    st.session_state.batidas.append("")
    st.rerun()

# Passo 4 - Resultado
leituras_validas = []
for b in st.session_state.batidas:
    if b.strip() != "":
        try: leituras_validas.append(float(b.replace(',', '.')))
        except: pass

if leituras_validas:
    st.divider()
    ultima = leituras_validas[-1]
    golpes_total = len(leituras_validas) * 3
    ipd = (ultima - marco_zero) / golpes_total
    status = "APROVADO" if ipd <= limite_v else "RECOMPACTAR"
    
    col_res1, col_res2 = st.columns(2)
    col_res1.metric("IPD Final", f"{ipd:.2f} mm/g")
    col_res2.metric("Total de Golpes", f"{golpes_total}")

    if status == "APROVADO": st.success(f"✅ {status}")
    else: st.error(f"⚠️ {status}")

    dados = {
        "os": num_os, 
        "endereco": endereco, 
        "material": st.session_state.material,
        "m_zero": marco_zero, 
        "leituras": leituras_validas, 
        "ipd_final": ipd, 
        "status": status,
        "limite_ref": limite_v
    }
    
    pdf_bytes = gerar_pdf(dados)
    st.download_button(label="📥 Baixar Relatório PDF", data=pdf_bytes, file_name=f"DCP_OS_{num_os}.pdf", mime="application/pdf", use_container_width=True)