import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Dashboard Geração Energética",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS customizado para melhorar a aparência
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        border: 1px solid #e1e5e9;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .trend-up {
        color: #00ff00;
    }
    .trend-down {
        color: #ff4444;
    }
    .trend-stable {
        color: #ffaa00;
    }
</style>
""", unsafe_allow_html=True)

# Função para obter dados e cachear por 20 segundos
@st.cache_data(ttl=20)
def get_data(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        
        # Ajustando o formato da data
        df['instante'] = pd.to_datetime(df['instante'])
        
        # Convertendo geração para MW
        df['geracao'] = df['geracao'] / 60
        
        return df
    except Exception as e:
        st.error(f"Erro ao obter dados: {e}")
        return pd.DataFrame()

# Função para calcular tendência
def calcular_tendencia(df, janela=10):
    if len(df) < janela:
        return 0, "stable"
    
    valores_recentes = df['geracao'].tail(janela).values
    if len(valores_recentes) < 2:
        return 0, "stable"
    
    # Calcular tendência usando regressão linear simples
    x = np.arange(len(valores_recentes))
    coef = np.polyfit(x, valores_recentes, 1)[0]
    
    # Classificar tendência
    if coef > 5:  # Aumento significativo
        return coef, "up"
    elif coef < -5:  # Diminuição significativa
        return coef, "down"
    else:
        return coef, "stable"

# URLs das fontes de dados
urls = {
    'Eólica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Eolica_json",
    'Solar': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Solar_json",
    'Hidráulica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Hidraulica_json",
    'Nuclear': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Nuclear_json",
    'Térmica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Termica_json"
}

urls_regionais = {
    'Norte Eólica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Eolica_json",
    'Norte Solar': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Solar_json",
    'Nordeste Eólica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Eolica_json",
    'Nordeste Solar': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Solar_json",
    'Sudeste/CO Eólica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Eolica_json",
    'Sudeste/CO Solar': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Solar_json",
    'Sul Eólica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Eolica_json",
    'Sul Solar': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Solar_json"
}

# Obter dados
with st.spinner('Carregando dados...'):
    dataframes = {key: get_data(url) for key, url in urls.items()}
    dataframes_regionais = {key: get_data(url) for key, url in urls_regionais.items()}

# Verificar se os dados foram carregados
if not any(len(df) > 0 for df in dataframes.values()):
    st.error("Não foi possível carregar os dados. Verifique a conexão.")
    st.stop()

# Calcular última atualização
ultima_atualizacao = max(
    df['instante'].max() for df in dataframes.values() if len(df) > 0
)

# Header do dashboard
st.markdown(f"""
<div style='background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 15px; margin-bottom: 20px;'>
    <h1 style='color: white; text-align: center; margin: 0;'>⚡ Dashboard de Geração Energética - SIN</h1>
    <p style='color: #e0e6ed; text-align: center; margin: 5px 0 0 0;'>Última atualização: {ultima_atualizacao.strftime('%d/%m/%Y %H:%M')}</p>
</div>
""", unsafe_allow_html=True)

# Calcular métricas e tendências
total_atual = sum(df['geracao'].iloc[-1] for df in dataframes.values() if len(df) > 0)
total_gwh = total_atual / 1000

# Cards de métricas principais
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    if len(dataframes['Eólica']) > 0:
        valor_eolica = dataframes['Eólica']['geracao'].iloc[-1]
        trend_eolica, tipo_trend = calcular_tendencia(dataframes['Eólica'])
        trend_icon = "📈" if tipo_trend == "up" else "📉" if tipo_trend == "down" else "➡️"
        st.metric("🌪️ Eólica", f"{valor_eolica:.0f} MW", f"{trend_eolica:.1f} MW/h {trend_icon}")

with col2:
    if len(dataframes['Solar']) > 0:
        valor_solar = dataframes['Solar']['geracao'].iloc[-1]
        trend_solar, tipo_trend = calcular_tendencia(dataframes['Solar'])
        trend_icon = "📈" if tipo_trend == "up" else "📉" if tipo_trend == "down" else "➡️"
        st.metric("☀️ Solar", f"{valor_solar:.0f} MW", f"{trend_solar:.1f} MW/h {trend_icon}")

with col3:
    if len(dataframes['Hidráulica']) > 0:
        valor_hidraulica = dataframes['Hidráulica']['geracao'].iloc[-1]
        trend_hidraulica, tipo_trend = calcular_tendencia(dataframes['Hidráulica'])
        trend_icon = "📈" if tipo_trend == "up" else "📉" if tipo_trend == "down" else "➡️"
        st.metric("💧 Hidráulica", f"{valor_hidraulica:.0f} MW", f"{trend_hidraulica:.1f} MW/h {trend_icon}")

with col4:
    if len(dataframes['Nuclear']) > 0:
        valor_nuclear = dataframes['Nuclear']['geracao'].iloc[-1]
        trend_nuclear, tipo_trend = calcular_tendencia(dataframes['Nuclear'])
        trend_icon = "📈" if tipo_trend == "up" else "📉" if tipo_trend == "down" else "➡️"
        st.metric("⚛️ Nuclear", f"{valor_nuclear:.0f} MW", f"{trend_nuclear:.1f} MW/h {trend_icon}")

with col5:
    if len(dataframes['Térmica']) > 0:
        valor_termica = dataframes['Térmica']['geracao'].iloc[-1]
        trend_termica, tipo_trend = calcular_tendencia(dataframes['Térmica'])
        trend_icon = "📈" if tipo_trend == "up" else "📉" if tipo_trend == "down" else "➡️"
        st.metric("🔥 Térmica", f"{valor_termica:.0f} MW", f"{trend_termica:.1f} MW/h {trend_icon}")

with col6:
    # Calcular tendência total
    df_total_temp = pd.DataFrame({'instante': dataframes['Eólica']['instante']})
    df_total_temp['geracao'] = sum(dataframes[fonte]['geracao'] for fonte in dataframes.keys())
    trend_total, tipo_trend_total = calcular_tendencia(df_total_temp)
    trend_icon = "📈" if tipo_trend_total == "up" else "📉" if tipo_trend_total == "down" else "➡️"
    st.metric("⚡ Total SIN", f"{total_gwh:.2f} GW", f"{trend_total:.1f} MW/h {trend_icon}")

# Layout principal com gráficos
col_left, col_right = st.columns([1, 1])

# Gráfico de composição (rosca)
with col_left:
    st.markdown("### 📊 Composição Atual da Geração")
    
    df_composicao = pd.DataFrame({
        'Fonte': list(urls.keys()),
        'Geração (MW)': [dataframes[fonte]['geracao'].iloc[-1] for fonte in urls.keys()]
    })
    
    # Cores personalizadas para cada fonte
    cores_fontes = {
        'Eólica': '#00a8ff',
        'Solar': '#fbc531', 
        'Hidráulica': '#44bd32',
        'Nuclear': '#e84118',
        'Térmica': '#8c7ae6'
    }
    
    fig_rosca = go.Figure(data=[go.Pie(
        labels=df_composicao['Fonte'],
        values=df_composicao['Geração (MW)'],
        hole=.6,
        marker=dict(colors=[cores_fontes[fonte] for fonte in df_composicao['Fonte']]),
        textinfo='label+percent',
        textfont=dict(size=12),
        hovertemplate='<b>%{label}</b><br>Geração: %{value:.0f} MW<br>Percentual: %{percent}<extra></extra>'
    )])
    
    fig_rosca.add_annotation(
        dict(
            text=f'<b>{total_gwh:.2f} GW</b><br>Total SIN',
            x=0.5, y=0.5,
            font=dict(size=18, color='#2c3e50'),
            showarrow=False
        )
    )
    
    fig_rosca.update_layout(
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        margin=dict(t=20, b=20, l=20, r=20)
    )
    
    st.plotly_chart(fig_rosca, use_container_width=True)

# Gráfico de evolução temporal
with col_right:
    st.markdown("### 📈 Evolução da Geração (Últimas 24h)")
    
    fig_evolucao = go.Figure()
    
    for fonte, df in dataframes.items():
        if len(df) > 0:
            fig_evolucao.add_trace(go.Scatter(
                x=df['instante'],
                y=df['geracao'],
                mode='lines',
                name=fonte,
                line=dict(color=cores_fontes[fonte], width=3),
                hovertemplate=f'<b>{fonte}</b><br>Hora: %{{x}}<br>Geração: %{{y:.0f}} MW<extra></extra>'
            ))
    
    fig_evolucao.update_layout(
        height=400,
        xaxis_title="Horário",
        yaxis_title="Geração (MW)",
        hovermode='x unified',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        margin=dict(t=20, b=60, l=50, r=20)
    )
    
    fig_evolucao.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    fig_evolucao.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    
    st.plotly_chart(fig_evolucao, use_container_width=True)

# Gráfico regional (tela cheia)
st.markdown("### 🗺️ Geração por Região")

fig_regional = go.Figure()

# Cores para regiões
cores_regionais = {
    'Norte Eólica': '#3742fa', 'Norte Solar': '#ffa502',
    'Nordeste Eólica': '#2ed573', 'Nordeste Solar': '#ff6348',
    'Sudeste/CO Eólica': '#5352ed', 'Sudeste/CO Solar': '#ff9f43',
    'Sul Eólica': '#2f3542', 'Sul Solar': '#ff3838'
}

for nome, df in dataframes_regionais.items():
    if len(df) > 0:
        fig_regional.add_trace(go.Scatter(
            x=df['instante'],
            y=df['geracao'],
            mode='lines',
            name=nome,
            line=dict(color=cores_regionais.get(nome, '#95a5a6'), width=2.5),
            hovertemplate=f'<b>{nome}</b><br>Hora: %{{x}}<br>Geração: %{{y:.0f}} MW<extra></extra>'
        ))

fig_regional.update_layout(
    height=500,
    xaxis_title="Horário",
    yaxis_title="Geração (MW)",
    hovermode='x unified',
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.2,
        xanchor="center",
        x=0.5,
        font=dict(size=10)
    ),
    margin=dict(t=20, b=80, l=50, r=20)
)

fig_regional.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
fig_regional.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')

st.plotly_chart(fig_regional, use_container_width=True)

# Footer com informações adicionais
st.markdown("""
<div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-top: 20px; border-left: 4px solid #007bff;'>
    <small>
    <b>📋 Informações:</b><br>
    • Os dados são atualizados a cada 20 segundos diretamente da API do ONS<br>
    • As tendências são calculadas com base nos últimos 10 pontos de dados<br>
    • Valores em MW (Megawatts) e GW (Gigawatts)<br>
    • 📈 = Tendência de aumento | 📉 = Tendência de diminuição | ➡️ = Estável
    </small>
</div>
""", unsafe_allow_html=True)

# Auto refresh (opcional)
if st.checkbox("🔄 Atualização automática (30s)", value=False):
    import time
    time.sleep(30)
    st.experimental_rerun()
