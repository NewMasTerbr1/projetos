import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime

# Configuração da Página
st.set_page_config(
    page_title="Simulador & Gestor de Carteira",
    page_icon="💰",
    layout="wide"
)

# Estilo Personalizado
st.markdown("""
<style>
    .metric-card {
        background-color: #1e222d;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2e3545;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização do Histórico de Compras na Sessão
if 'transacoes' not in st.session_state:
    st.session_state.transacoes = pd.DataFrame(columns=[
        'Data', 'Ticker', 'Tipo', 'Quantidade', 'Preco_Pago'
    ])

# Função para buscar cotação e dividendo via yfinance
@st.cache_data(ttl=3600)
def obter_dados_ativo(ticker):
    try:
        ticker_b3 = f"{ticker.upper()}.SA" if not ticker.endswith(".SA") else ticker.upper()
        ativo = yf.Ticker(ticker_b3)
        info = ativo.info
        
        preco_atual = info.get('currentPrice') or info.get('regularMarketPrice') or 0.0
        dividendo_ultimo = info.get('lastDividendValue') or 0.0
        
        return float(preco_atual), float(dividendo_ultimo)
    except Exception:
        return 0.0, 0.0

st.title("💰 Gestor de Carteira & Simulador de Investimentos")

# Criação das 3 Abas
aba_carteira, aba_simulador, aba_metas = st.tabs([
    "📊 Minha Carteira", 
    "📈 Simulador de Juros Compostos", 
    "🎯 Minhas Metas & Bola de Neve"
])

# ==============================================================================
# ABA 1: MINHA CARTEIRA
# ==============================================================================
with aba_carteira:
    st.header("Acompanhamento de Patrimônio e Compras")
    
    col_form, col_resumo = st.columns([1, 2])
    
    with col_form:
        st.subheader("➕ Nova Compra / Registro")
        with st.form("form_compra", clear_on_submit=True):
            data_compra = st.date_input("Data da Compra", datetime.now())
            ticker_input = st.text_input("Código do Ativo (ex: MXRF11, B3SA3, PETR4)", "MXRF11").strip().upper()
            tipo_ativo = st.selectbox("Tipo de Ativo", ["FII", "Ação", "Renda Fixa/CDB"])
            qtd_cotas = st.number_input("Quantidade de Cotas Adquiridas", min_value=1, step=1, value=10)
            preco_pago = st.number_input("Preço Pago por Cota (R$)", min_value=0.01, step=0.01, value=10.00)
            
            submetido = st.form_submit_button("Registrar Compra")
            if submetido and ticker_input:
                nova_transacao = pd.DataFrame([{
                    'Data': data_compra.strftime("%d/%m/%Y"),
                    'Ticker': ticker_input,
                    'Tipo': tipo_ativo,
                    'Quantidade': int(qtd_cotas),
                    'Preco_Pago': float(preco_pago)
                }])
                st.session_state.transacoes = pd.concat([st.session_state.transacoes, nova_transacao], ignore_index=True)
                st.success(f"Registradas {qtd_cotas} cotas de {ticker_input} com sucesso!")
                st.rerun()

        # ÁREA DE GERENCIAMENTO / DELETAR
        st.markdown("---")
        st.subheader("⚙️ Gerenciar Lançamentos")
        
        if not st.session_state.transacoes.empty:
            # Opção 1: Excluir um item específico
            st.write("**Apagar um lançamento específico:**")
            opcoes_exclusao = [f"Linha {i}: {row['Ticker']} - {row['Quantidade']} cotas em {row['Data']}" 
                              for i, row in st.session_state.transacoes.iterrows()]
            item_para_excluir = st.selectbox("Selecione qual deseja remover:", opcoes_exclusao)
            
            if st.button("🗑️ Deletar Lançamento Selecionado", type="secondary"):
                idx_excluir = int(item_para_excluir.split(":")[0].replace("Linha ", ""))
                st.session_state.transacoes = st.session_state.transacoes.drop(idx_excluir).reset_index(drop=True)
                st.success("Lançamento removido!")
                st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            # Opção 2: Zerar toda a carteira
            st.write("**Zerar toda a carteira:**")
            if st.button("🚨 ZERAR CARTEIRA COMPLETA", type="primary"):
                st.session_state.transacoes = pd.DataFrame(columns=['Data', 'Ticker', 'Tipo', 'Quantidade', 'Preco_Pago'])
                st.warning("Carteira zerada com sucesso!")
                st.rerun()
        else:
            st.caption("Nenhum lançamento registrado para editar.")

    with col_resumo:
        if not st.session_state.transacoes.empty:
            st.subheader("📌 Resumo Consolidado")
            
            df_trans = st.session_state.transacoes
            resumo_list = []
            
            for ticker in df_trans['Ticker'].unique():
                df_ticker = df_trans[df_trans['Ticker'] == ticker]
                total_cotas = df_ticker['Quantidade'].sum()
                custo_total = (df_ticker['Quantidade'] * df_ticker['Preco_Pago']).sum()
                preco_medio = custo_total / total_cotas if total_cotas > 0 else 0
                
                preco_atual, ult_div = obter_dados_ativo(ticker)
                if preco_atual == 0.0:
                    preco_atual = preco_medio
                
                valor_atual_total = total_cotas * preco_atual
                provento_estimado_mes = total_cotas * ult_div
                
                resumo_list.append({
                    'Ticker': ticker,
                    'Tipo': df_ticker['Tipo'].iloc[-1],
                    'Cotas Totais': total_cotas,
                    'Preço Médio (R$)': round(preco_medio, 2),
                    'Preço Atual (R$)': round(preco_atual, 2),
                    'Valor Total (R$)': round(valor_atual_total, 2),
                    'Provento Estimado/Mês (R$)': round(provento_estimado_mes, 2)
                })
            
            df_resumo = pd.DataFrame(resumo_list)
            
            patrimonio_total = df_resumo['Valor Total (R$)'].sum()
            proventos_totais_mes = df_resumo['Provento Estimado/Mês (R$)'].sum()
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Patrimônio Total", f"R$ {patrimonio_total:,.2f}")
            col_m2.metric("Proventos Estimados/Mês", f"R$ {proventos_totais_mes:,.2f}")
            col_m3.metric("Ativos Diferentes", len(df_resumo))
            
            st.dataframe(df_resumo, use_container_width=True)
            
            fig_pizz = px.pie(
                df_resumo, values='Valor Total (R$)', names='Ticker',
                title="Distribuição do Patrimônio por Ativo",
                hole=0.4
            )
            st.plotly_chart(fig_pizz, use_container_width=True)
        else:
            st.info("Sua carteira está vazia. Registre sua primeira compra no formulário ao lado!")

    st.markdown("---")
    st.subheader("📜 Histórico de Lançamentos")
    st.dataframe(st.session_state.transacoes, use_container_width=True)

# ==============================================================================
# ABA 2: SIMULADOR DE JUROS COMPOSTOS
# ==============================================================================
with aba_simulador:
    st.header("Simulador de Investimentos Futuros")
    
    col_sim_p, col_sim_g = st.columns([1, 2])
    
    with col_sim_p:
        v_inicial = st.number_input("Valor Inicial (R$)", value=1000.0, step=500.0)
        v_mensal = st.number_input("Aporte Mensal (R$)", value=300.0, step=50.0)
        taxa_anual = st.number_input("Taxa de Juros Anual (%)", value=11.0, step=0.5)
        tempo_anos = st.slider("Tempo de Investimento (Anos)", 1, 30, 10)
        
    with col_sim_g:
        meses = tempo_anos * 12
        taxa_mensal = (1 + taxa_anual / 100) ** (1 / 12) - 1
        
        dados_simulacao = []
        acumulado = v_inicial
        total_investido = v_inicial
        
        for m in range(1, meses + 1):
            rendimento = acumulado * taxa_mensal
            acumulado += rendimento + v_mensal
            total_investido += v_mensal
            
            dados_simulacao.append({
                'Mês': m,
                'Total Acumulado': round(acumulado, 2),
                'Total Investido': round(total_investido, 2),
                'Total em Juros': round(acumulado - total_investido, 2)
            })
            
        df_sim = pd.DataFrame(dados_simulacao)
        
        fig_sim = go.Figure()
        fig_sim.add_trace(go.Scatter(x=df_sim['Mês'], y=df_sim['Total Acumulado'], name="Total Acumulado", line=dict(color='#00CC96', width=3)))
        fig_sim.add_trace(go.Scatter(x=df_sim['Mês'], y=df_sim['Total Investido'], name="Total Investido", line=dict(color='#636EFA', dash='dash')))
        fig_sim.update_layout(title="Evolução do Patrimônio ao Longo do Tempo", xaxis_title="Meses", yaxis_title="R$")
        
        st.plotly_chart(fig_sim, use_container_width=True)
        
        st.caption(f"Em {tempo_anos} anos você terá acumulado **R$ {acumulado:,.2f}** (Sendo **R$ {acumulado - total_investido:,.2f}** apenas em juros!).")

# ==============================================================================
# ABA 3: MINHAS METAS & BOLA DE NEVE
# ==============================================================================
with aba_metas:
    st.header("🎯 Metas & Indicador Bola de Neve")
    
    col_meta1, col_meta2 = st.columns(2)
    
    with col_meta1:
        st.subheader("🏆 Meta de Patrimônio")
        meta_patrimonio = st.number_input("Defina sua Meta de Patrimônio (R$)", value=50000.0, step=5000.0)
        
        if not st.session_state.transacoes.empty:
            patrimonio_atual = sum([
                row['Quantidade'] * obter_dados_ativo(row['Ticker'])[0] 
                if obter_dados_ativo(row['Ticker'])[0] > 0 else row['Quantidade'] * row['Preco_Pago']
                for _, row in st.session_state.transacoes.iterrows()
            ])
        else:
            patrimonio_atual = 0.0
            
        progresso = min(patrimonio_atual / meta_patrimonio, 1.0) if meta_patrimonio > 0 else 0.0
        st.progress(progresso)
        st.write(f"Progresso Atual: **{progresso*100:.1f}%** (R$ {patrimonio_atual:,.2f} de R$ {meta_patrimonio:,.2f})")
        
    with col_meta2:
        st.subheader("❄️ Efeito Bola de Neve (Reinvestimento)")
        st.write("Veja quantas cotas novas os seus dividendos já compram sozinhos todos os meses:")
        
        if not st.session_state.transacoes.empty and 'df_resumo' in locals():
            for _, row in df_resumo.iterrows():
                if row['Preço Atual (R$)'] > 0 and row['Provento Estimado/Mês (R$)'] > 0:
                    cotas_compradas = row['Provento Estimado/Mês (R$)'] / row['Preço Atual (R$)']
                    st.info(f"**{row['Ticker']}**: Seus dividendos compram **{cotas_compradas:.2f} cotas/mês** automaticamente.")
                else:
                    st.write(f"**{row['Ticker']}**: Proventos ainda insuficientes para comprar 1 cota inteira.")
        else:
            st.caption("Cadastre seus ativos na aba 'Minha Carteira' para ver o cálculo do Efeito Bola de Neve.")