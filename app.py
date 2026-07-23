import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página e layout
st.set_page_config(
    page_title="Simulador de Investimentos", 
    page_icon="📈", 
    layout="wide"
)

st.title("📈 Simulador de Juros Compostos & Investimentos")
st.write("Ajuste os parâmetros na barra lateral para simular o crescimento do seu patrimônio.")

# --- BARRA LATERAL (INPUTS) ---
st.sidebar.header("⚙️ Parâmetros da Simulação")

# 1. Categoria do Investimento
categoria = st.sidebar.selectbox(
    "Categoria de Investimento",
    ["Renda Fixa", "Renda Variável"]
)

# Dados mockados/exemplo de ativos
fiis_populares = [
    {"ticker": "MXRF11", "nome": "Maxi Renda", "preco": 10.15, "dy_anual": 12.5},
    {"ticker": "CPTS11", "nome": "Capitânia Securities", "preco": 8.50, "dy_anual": 11.8},
    {"ticker": "VISC11", "nome": "Vinci Shopping Centers", "preco": 115.00, "dy_anual": 8.9},
    {"ticker": "HGLG11", "nome": "CSHG Logística", "preco": 162.00, "dy_anual": 8.5},
    {"ticker": "KNCR11", "nome": "Kinea Rendimentos", "preco": 104.00, "dy_anual": 12.1}
]

# Ordena os FIIs do menor preço para o maior preço
fiis_populares = sorted(fiis_populares, key=lambda x: x["preco"])

taxa_anual_sugerida = 10.0
aporte_mensal_calculado = 450.0

# 2. Lógica Dinâmica de Tipo de Ativo
if categoria == "Renda Fixa":
    tipo_rf = st.sidebar.selectbox(
        "Tipo de Ativo",
        ["CDB 100% CDI", "Poupança", "Tesouro Selic", "LCI/LCA (Isento)"]
    )
    
    # Estimativas de taxas médias anuais para sugestão
    if tipo_rf == "Poupança":
        taxa_anual_sugerida = 6.17
    elif tipo_rf == "CDB 100% CDI":
        taxa_anual_sugerida = 10.5
    elif tipo_rf == "Tesouro Selic":
        taxa_anual_sugerida = 10.75
    elif tipo_rf == "LCI/LCA (Isento)":
        taxa_anual_sugerida = 9.2

elif categoria == "Renda Variável":
    tipo_rv = st.sidebar.selectbox(
        "Tipo de Ativo",
        ["FIIs (Fundos Imobiliários)", "Ações Dividendos", "ETFs"]
    )
    
    if tipo_rv == "FIIs (Fundos Imobiliários)":
        # Opções formatadas do menor valor para o maior
        opcoes_fiis = [f"{f['ticker']} - R$ {f['preco']:.2f} (DY ~{f['dy_anual']}%)" for f in fiis_populares]
        fii_selecionado_str = st.sidebar.selectbox("Escolha o FII (Ordenado por preço)", opcoes_fiis)
        
        # Identifica o FII escolhido
        idx_fii = opcoes_fiis.index(fii_selecionado_str)
        fii_obj = fiis_populares[idx_fii]
        
        num_cotas = st.sidebar.number_input(
            f"Quantidade de Cotas/Mês ({fii_obj['ticker']})", 
            min_value=1, 
            value=10, 
            step=1
        )
        
        aporte_mensal_calculado = num_cotas * fii_obj["preco"]
        taxa_anual_sugerida = fii_obj["dy_anual"]
        
        st.sidebar.info(f"💡 **Aporte Mensal do FII:** R$ {aporte_mensal_calculado:.2f} ({num_cotas} cotas de {fii_obj['ticker']})")

st.sidebar.divider()

# Inputs Financeiros do Usuário
aporte_inicial = st.sidebar.number_input(
    "Aporte Inicial (R$)", 
    min_value=0.0, 
    value=1000.0, 
    step=500.0
)

# Se não for FIIs (onde o aporte é calculado pelas cotas), permite digitar o aporte mensal livremente
if categoria == "Renda Variável" and tipo_rv == "FIIs (Fundos Imobiliários)":
    aporte_mensal = aporte_mensal_calculado
else:
    aporte_mensal = st.sidebar.number_input(
        "Aporte Mensal (R$)", 
        min_value=0.0, 
        value=aporte_mensal_calculado, 
        step=50.0
    )

aporte_anual = st.sidebar.number_input(
    "Aporte Extra Anual (ex: 13º) (R$)", 
    min_value=0.0, 
    value=0.0, 
    step=500.0
)

taxa_anual = st.sidebar.slider(
    "Taxa/Retorno Anual Estimado (%)", 
    min_value=1.0, 
    max_value=30.0, 
    value=float(taxa_anual_sugerida), 
    step=0.5
)

anos = st.sidebar.slider(
    "Período (Anos)", 
    min_value=1, 
    max_value=40, 
    value=10
)

# --- CÁLCULOS DA SIMULAÇÃO ---
meses = anos * 12
taxa_mensal = (1 + taxa_anual / 100) ** (1 / 12) - 1

dados = []
saldo = aporte_inicial
total_investido = aporte_inicial

for m in range(1, meses + 1):
    juros_mes = saldo * taxa_mensal
    saldo += juros_mes + aporte_mensal
    total_investido += aporte_mensal
    
    if m % 12 == 0 and aporte_anual > 0:
        saldo += aporte_anual
        total_investido += aporte_anual

    dados.append({
        "Mês": m,
        "Ano": (m - 1) // 12 + 1,
        "Total Investido": round(total_investido, 2),
        "Total Juros": round(saldo - total_investido, 2),
        "Patrimônio Total": round(saldo, 2)
    })

df = pd.DataFrame(dados)

# --- MÉTRICAS PRINCIPAIS ---
total_final = df["Patrimônio Total"].iloc[-1]
investido_final = df["Total Investido"].iloc[-1]
juros_final = df["Total Juros"].iloc[-1]
rendimento_pct = (juros_final / investido_final) * 100 if investido_final > 0 else 0

col1, col2, col3 = st.columns(3)

col1.metric("Patrimônio Final", f"R$ {total_final:,.2f}")
col2.metric("Total Investido", f"R$ {investido_final:,.2f}")
col3.metric("Rendimento / Dividendos", f"R$ {juros_final:,.2f}", delta=f"{rendimento_pct:.1f}% de lucro")

st.divider()

# --- GRÁFICO INTERATIVO ---
fig = px.bar(
    df, 
    x="Mês", 
    y=["Total Investido", "Total Juros"], 
    title="Evolução do Patrimônio ao Longo do Tempo (Mês a Mês)",
    labels={"value": "Valor (R$)", "variable": "Composição"},
    color_discrete_map={
        "Total Investido": "#29b6f6", 
        "Total Juros": "#66bb6a"
    }
)

st.plotly_chart(fig, use_container_width=True)

# --- TABELA DE DADOS E DOWNLOAD ---
with st.expander("📄 Ver tabela de dados detalhada"):
    st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Planilha em CSV",
        data=csv,
        file_name="simulacao_investimento.csv",
        mime="text/csv"
    )