import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import pytz
from plotly.subplots import make_subplots

# Configuração da página
st.set_page_config(
    page_title="Monitor SIN",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Moderno
st.markdown("""
     <style>
    /* Tema escuro aprimorado */
    .main {
        background-color: #0f1116;
        padding: 0 !important;
    }
    .block-container {
        padding: 2rem !important;
        max-width: 100% !important;
    }
    
    /* Cards modernos */
    .metric-container {
        background: linear-gradient(145deg, #1a1d24, #2a2d34);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0,0,0,0.37);
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 1rem;
    }
    
    /* Métricas estilizadas */
    div[data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        text-shadow: 0 0 10px rgba(255,255,255,0.3);
        font-family: 'Inter', sans-serif;
    }
    
    div[data-testid="stMetricDelta"] {
        font-size: 1.2rem !important;
        color: #00ff88 !important;
        font-weight: 500 !important;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 1.3rem !important;
        color: #a0aec0 !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* Títulos estilizados */
    h1 {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 2.5rem !important;
        margin-bottom: 2rem !important;
        text-shadow: 0 0 10px rgba(255,255,255,0.2);
        font-family: 'Inter', sans-serif;
    }
    
    h2, h3 {
        color: #ffffff !important;
        font-weight: 600 !important;
        margin-top: 2rem !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Status de atualização */
    .updating {
        color: #00ff88;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        background: rgba(0,255,136,0.1);
        border: 1px solid rgba(0,255,136,0.2);
        font-weight: 500;
        display: inline-block;
        animation: pulse 2s infinite;
    }
    
    /* Containers de gráficos */
    .chart-container {
        background: linear-gradient(145deg, #1a1d24, #2a2d34);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0,0,0,0.37);
        border: 1px solid rgba(255,255,255,0.1);
        margin: 1rem 0;
    }
    
    /* Animações */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1d24;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #4a4d54;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #5a5d64;
    }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# Constantes
BRAZIL_TZ = pytz.timezone('America/Sao_Paulo')

# URLs do SIN
URLS = {
    'SIN Eólica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Eolica_json",
    'SIN Hidráulica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Hidraulica_json",
    'SIN Nuclear': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Nuclear_json",
    'SIN Solar': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Solar_json",
    'SIN Térmica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Termica_json"
}

# Cores
COLORS = {
    'SIN Eólica': '#3498db',      # Azul vibrante
    'SIN Hidráulica': '#2ecc71',  # Verde esmeralda
    'SIN Nuclear': '#9b59b6',     # Roxo vibrante
    'SIN Solar': '#f1c40f',       # Amarelo dourado
    'SIN Térmica': '#e74c3c',     # Vermelho coral
    'background': '#0f1116',      # Fundo escuro
    'text': '#ffffff',            # Texto branco
    'grid': '#2a2d34'            # Grade escura
}

@st.cache_data(ttl=10)
def get_data(url):
    """Busca dados com tratamento de erros melhorado"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        }
        
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return pd.DataFrame(columns=['instante', 'geracao'])
            
        data = response.json()
        if not data:
            return pd.DataFrame(columns=['instante', 'geracao'])
            
        df = pd.DataFrame(data)
        
        if 'instante' not in df.columns or 'geracao' not in df.columns:
            return pd.DataFrame(columns=['instante', 'geracao'])
            
        # Converter instante para datetime com timezone
        df['instante'] = pd.to_datetime(df['instante']).dt.tz_convert(BRAZIL_TZ)
        
        # Converter geração para numérico
        df['geracao'] = pd.to_numeric(df['geracao'], errors='coerce').fillna(0) / 60
        
        return df
        
    except Exception as e:
        print(f"Erro ao buscar dados: {str(e)}")
        return pd.DataFrame(columns=['instante', 'geracao'])

def format_power(value, unit='MW'):
    """Formatação de valores de potência"""
    try:
        value = float(value)
        if pd.isna(value):
            return "N/A"
        if value >= 1000:
            return f"{value/1000:.2f} G{unit}"
        return f"{value:.2f} {unit}"
    except:
        return "N/A"

def calculate_trend(values):
    """Cálculo de tendência"""
    try:
        if len(values) >= 2:
            return (values.iloc[-1] - values.iloc[-2]) / values.iloc[-2] * 100
    except:
        pass
    return 0.0

def create_metrics(dataframes):
    """Criação de métricas"""
    sin_data = {k: v for k, v in dataframes.items() if k.startswith('SIN') and not v.empty}
    
    if not sin_data:
        st.error("Sem dados disponíveis no momento")
        return
        
    total_current = sum(df['geracao'].iloc[-1] for df in sin_data.values())
    
    cols = st.columns(len(sin_data) + 1)
    
    with cols[0]:
        st.metric(
            "Total SIN",
            format_power(total_current),
            ""
        )
    
    for i, (fonte, df) in enumerate(sin_data.items(), 1):
        with cols[i]:
            current = df['geracao'].iloc[-1]
            trend = calculate_trend(df['geracao'])
            st.metric(
                fonte.replace('SIN ', ''),
                format_power(current),
                f"{trend:.1f}%"
            )

def create_generation_chart(dataframes):
    """Criação do gráfico de geração com visual aprimorado"""
    fig = go.Figure()
    
    for fonte, df in dataframes.items():
        if not df.empty:
            fig.add_trace(go.Scatter(
                x=df['instante'],
                y=df['geracao'],
                name=fonte.replace('SIN ', ''),
                line=dict(
                    color=COLORS[fonte],
                    width=3,
                    shape='spline',
                    smoothing=0.3
                ),
                hovertemplate="<b>%{y:.2f} MW</b><br>%{x}<extra></extra>",
                fill='tonexty',
                fillcolor=f"rgba{tuple(list(int(COLORS[fonte].lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + [0.1])}"
            ))
    
    fig.update_layout(
        title={
            'text': "Geração por Fonte",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24, 'color': '#ffffff', 'family': 'Inter'}
        },
        height=600,
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(0,0,0,0.5)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1
        ),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(255,255,255,0.1)',
            showline=True,
            linewidth=1,
            linecolor='rgba(255,255,255,0.2)'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(255,255,255,0.1)',
            showline=True,
            linewidth=1,
            linecolor='rgba(255,255,255,0.2)'
        )
    )
    
    return fig

def create_pie_chart(dataframes):
    """Criação do gráfico de pizza com visual aprimorado"""
    values = []
    labels = []
    colors = []
    
    for fonte, df in dataframes.items():
        if not df.empty:
            values.append(df['geracao'].iloc[-1])
            labels.append(fonte.replace('SIN ', ''))
            colors.append(COLORS[fonte])
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.6,
        marker=dict(
            colors=colors,
            line=dict(color='rgba(255,255,255,0.2)', width=2)
        ),
        textinfo='label+percent',
        textfont=dict(size=14, family='Inter'),
        hovertemplate="<b>%{label}</b><br>%{value:.2f} MW<br>%{percent}<extra></extra>"
    )])
    
    fig.update_layout(
        title={
            'text': "Composição da Geração",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24, 'color': '#ffffff', 'family': 'Inter'}
        },
        height=600,
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(0,0,0,0.5)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1,
            font=dict(family='Inter')
        )
    )
    
    # Adicionar valor total no centro
    total = sum(values)
    fig.add_annotation(
        text=f'{format_power(total)}',
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=24, color='#ffffff', family='Inter')
    )
    
    return fig

def main():
    # Cabeçalho com ícone
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1>⚡ Monitor do Sistema Interligado Nacional</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Container para métricas
    st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
    
    # Carregar e exibir dados
    with st.spinner("⚡ Atualizando dados do sistema..."):
        dataframes = {}
        for fonte, url in URLS.items():
            df = get_data(url)
            if not df.empty:
                dataframes[fonte] = df
    
    if not dataframes:
        st.error("⚠️ Não foi possível carregar os dados. Tentando novamente...")
        return
    
    # Métricas
    create_metrics(dataframes)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Gráficos em containers estilizados
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.plotly_chart(create_generation_chart(dataframes), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.plotly_chart(create_pie_chart(dataframes), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Status de atualização
    st.markdown("---")
    st.markdown(
        f'<div style="text-align: center;"><span class="updating">🔄 Última atualização: {datetime.now(BRAZIL_TZ).strftime("%d/%m/%Y %H:%M:%S")}</span></div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
