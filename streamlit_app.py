import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import numpy as np
import time

# Configuração da página para TV widescreen
st.set_page_config(
    page_title="Sistema Elétrico Brasileiro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Paleta dark mode premium
COLORS = {
    'background': '#0B0F19',
    'surface': '#1A1F2E',
    'card': '#252B3A',
    'border': '#2A3441',
    'text_primary': '#F8FAFC',
    'text_secondary': '#94A3B8',
    'accent': '#3B82F6',
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'glow': '#4C1D95'
}

# Cores vibrantes para fontes de energia
ENERGY_COLORS = {
    'Hidráulica': '#06B6D4',    # Cyan vibrante
    'Eólica': '#10B981',        # Verde esmeralda
    'Solar': '#F59E0B',         # Amarelo dourado
    'Térmica': '#EF4444',       # Vermelho coral
    'Nuclear': '#8B5CF6',       # Roxo vibrante
    'Carga': '#E879F9'          # Rosa neon
}

# Funções de obtenção de dados
@st.cache_data(ttl=20)
def get_data(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and response.content:
            data = response.json()
            if isinstance(data, list) and data:
                df = pd.DataFrame(data)
                if not df.empty:
                    df['instante'] = pd.to_datetime(df['instante'], errors='coerce')
                    df = df.dropna(subset=['instante'])
                    return df
        return pd.DataFrame(columns=['instante', 'geracao'])
    except Exception:
        return pd.DataFrame(columns=['instante', 'geracao'])

@st.cache_data(ttl=20)
def get_carga_data():
    url = "https://integra.ons.org.br/api/energiaagora/Get/Carga_SIN_json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df['instante'] = pd.to_datetime(df['instante'])
            return df
        return pd.DataFrame(columns=['instante', 'carga'])
    except Exception:
        return pd.DataFrame(columns=['instante', 'carga'])

def calcular_tendencia(df, janela=10):
    if len(df) < janela or len(df) == 0:
        return 0, "stable"
    
    valores_recentes = df['geracao'].tail(janela).values if 'geracao' in df.columns else df['carga'].tail(janela).values
    if len(valores_recentes) < 2:
        return 0, "stable"
    
    try:
        x = np.arange(len(valores_recentes))
        coef = np.polyfit(x, valores_recentes, 1)[0]
        
        if coef > 5:
            return coef, "up"
        elif coef < -5:
            return coef, "down"
        else:
            return coef, "stable"
    except Exception:
        return 0, "stable"

def load_data():
    urls = {
        'Eólica': {
            'Norte': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Eolica_json",
            'Nordeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Eolica_json",
            'Sudeste/Centro-Oeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Eolica_json",
            'Sul': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Eolica_json"
        },
        'Solar': {
            'Norte': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Solar_json",
            'Nordeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Solar_json",
            'Sudeste/Centro-Oeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Solar_json",
            'Sul': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Solar_json"
        },
        'Hidráulica': {
            'Norte': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Hidraulica_json",
            'Nordeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Hidraulica_json",
            'Sudeste/Centro-Oeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Hidraulica_json",
            'Sul': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Hidraulica_json"
        },
        'Nuclear': {
            'Sudeste/Centro-Oeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Nuclear_json"
        },
        'Térmica': {
            'Norte': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Termica_json",
            'Nordeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Termica_json",
            'Sudeste/Centro-Oeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Termica_json",
            'Sul': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Termica_json"
        }
    }
    
    dataframes = {}
    for fonte, regioes in urls.items():
        for regiao, url in regioes.items():
            df = get_data(url)
            if df is not None and not df.empty:
                key = f'{fonte} - {regiao}'
                dataframes[key] = df
    
    return dataframes

def process_data(dataframes):
    if not dataframes:
        return {}, {}
    
    # Agregar dados por fonte
    fonte_totals = {}
    for key, df in dataframes.items():
        if df.empty:
            continue
        fonte = key.split(' - ')[0]
        if fonte not in fonte_totals:
            fonte_totals[fonte] = df['geracao'].iloc[-1]
        else:
            fonte_totals[fonte] += df['geracao'].iloc[-1]
    
    # Preparar dados para gráfico de 24h
    timeline_data = {}
    for key, df in dataframes.items():
        if df.empty:
            continue
        fonte = key.split(' - ')[0]
        if fonte not in timeline_data:
            timeline_data[fonte] = df.copy()
        else:
            timeline_data[fonte]['geracao'] += df['geracao']
    
    return fonte_totals, timeline_data

# CSS Dark Mode Premium
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .main {
        background: linear-gradient(135deg, #0B0F19 0%, #1A1F2E 100%);
        font-family: 'Inter', sans-serif;
        color: #F8FAFC;
        padding: 0;
        margin: 0;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0B0F19 0%, #1A1F2E 100%);
        padding: 0;
        margin: 0;
    }
    
    .block-container {
        padding: 1rem 2rem;
        max-width: none !important;
        width: 100vw;
        margin: 0;
    }
    
    /* TV Widescreen adjustments */
    .metric-card {
        background: linear-gradient(135deg, #252B3A 0%, #2A3441 100%);
        border: 1px solid #3B4252;
        border-radius: 16px;
        padding: 20px;
        margin: 6px 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 4px;
        line-height: 1;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #94A3B8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }
    
    .source-card {
        background: linear-gradient(135deg, #252B3A 0%, #2A3441 100%);
        border: 1px solid #3B4252;
        border-radius: 12px;
        padding: 16px;
        margin: 4px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        min-height: 70px;
    }
    
    .section-title {
        font-size: 1.3rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 16px;
        position: relative;
        padding-left: 16px;
    }
    
    /* Compact layout for TV */
    .chart-container {
        background: linear-gradient(135deg, #252B3A 0%, #2A3441 100%);
        border: 1px solid #3B4252;
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .footer {
        background: linear-gradient(135deg, #252B3A 0%, #2A3441 100%);
        border: 1px solid #3B4252;
        border-radius: 16px;
        padding: 16px 24px;
        margin-top: 20px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    }
    
    .footer-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #94A3B8;
        font-size: 0.8rem;
    }
    
    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 48px 32px;
        border-radius: 24px;
        margin-bottom: 40px;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
    }
    
    .hero-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        margin: 0;
        color: white;
        text-shadow: 0 4px 8px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .hero-subtitle {
        font-size: 1.25rem;
        margin: 16px 0 0 0;
        color: rgba(255,255,255,0.9);
        position: relative;
        z-index: 1;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #252B3A 0%, #2A3441 100%);
        border: 1px solid #3B4252;
        border-radius: 20px;
        padding: 32px;
        margin: 12px 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #3B82F6, #10B981, #F59E0B, #EF4444, #8B5CF6);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        border-color: #4C566A;
    }
    
    .metric-card:hover::before {
        opacity: 1;
    }
    
    .metric-value {
        font-size: 3rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 8px;
        line-height: 1;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #94A3B8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 12px;
    }
    
    .metric-status {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        box-shadow: 0 0 8px currentColor;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .status-good { color: #10B981; }
    .status-warning { color: #F59E0B; }
    .status-critical { color: #EF4444; }
    
    .source-card {
        background: linear-gradient(135deg, #252B3A 0%, #2A3441 100%);
        border: 1px solid #3B4252;
        border-radius: 16px;
        padding: 24px;
        margin: 8px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    .source-card::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background: var(--source-color);
        transition: width 0.3s ease;
    }
    
    .source-card:hover {
        transform: translateX(8px);
        border-color: var(--source-color);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }
    
    .source-card:hover::before {
        width: 8px;
    }
    
    .source-name {
        font-weight: 700;
        color: #F8FAFC;
        font-size: 1.1rem;
    }
    
    .source-percentage {
        font-size: 0.875rem;
        color: #94A3B8;
        margin-top: 4px;
    }
    
    .source-value {
        font-size: 1.5rem;
        font-weight: 800;
        color: var(--source-color);
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .trend-badge {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 4px 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 8px;
        display: inline-block;
        backdrop-filter: blur(10px);
    }
    
    .trend-up { 
        color: #10B981; 
        background: rgba(16, 185, 129, 0.1);
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
    }
    .trend-down { 
        color: #EF4444; 
        background: rgba(239, 68, 68, 0.1);
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
    }
    .trend-stable { 
        color: #94A3B8; 
        background: rgba(148, 163, 184, 0.1);
    }
    
    .chart-container {
        background: linear-gradient(135deg, #252B3A 0%, #2A3441 100%);
        border: 1px solid #3B4252;
        border-radius: 24px;
        padding: 32px;
        margin: 20px 0;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .chart-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #3B82F6, #10B981, #F59E0B);
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 24px;
        position: relative;
        padding-left: 20px;
    }
    
    .section-title::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 24px;
        background: linear-gradient(135deg, #3B82F6, #8B5CF6);
        border-radius: 2px;
    }
    
    .glass-effect {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .footer {
        background: linear-gradient(135deg, #252B3A 0%, #2A3441 100%);
        border: 1px solid #3B4252;
        border-radius: 20px;
        padding: 32px;
        margin-top: 48px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
    }
    
    .footer-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #94A3B8;
        font-size: 0.875rem;
    }
    
    .live-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(16, 185, 129, 0.1);
        padding: 8px 16px;
        border-radius: 20px;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .live-dot {
        width: 8px;
        height: 8px;
        background: #10B981;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
        box-shadow: 0 0 10px #10B981;
    }
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: none;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    .stPlotlyChart {
        border-radius: 16px;
        overflow: hidden;
    }
    
    /* Hide Streamlit elements */
    footer { display: none !important; }
    .stDeployButton { display: none !important; }
    #MainMenu { display: none !important; }
    header { display: none !important; }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1A1F2E;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #3B82F6, #8B5CF6);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #2563EB, #7C3AED);
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .hero-title { font-size: 2.5rem; }
        .metric-value { font-size: 2rem; }
        .source-value { font-size: 1.25rem; }
    }
</style>
""", unsafe_allow_html=True)

# Carregar dados com loading elegante
with st.spinner('🔄 Sincronizando dados em tempo real...'):
    dataframes = load_data()
    carga_data = get_carga_data()
    fonte_totals, timeline_data = process_data(dataframes)

# Layout principal
if fonte_totals and not carga_data.empty:
    # Métricas principais
    total_geracao = sum(fonte_totals.values())
    total_carga = carga_data['carga'].iloc[-1] if 'carga' in carga_data else 0
    renovaveis = (fonte_totals.get('Hidráulica', 0) + fonte_totals.get('Eólica', 0) + fonte_totals.get('Solar', 0))
    percentual_renovavel = (renovaveis / total_geracao * 100) if total_geracao > 0 else 0
    margem = total_geracao - total_carga
    
    # Cards de métricas principais com design premium
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_geracao:,.0f}</div>
            <div class="metric-label">Geração Total (MW)</div>
            <div class="metric-status">
                <div class="status-indicator status-good" style="background: #10B981;"></div>
                <span style="color: #10B981;">Sistema Operacional</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        trend_carga, tipo_trend_carga = calcular_tendencia(carga_data)
        trend_color = "#10B981" if tipo_trend_carga == "stable" else "#F59E0B" if tipo_trend_carga == "up" else "#EF4444"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_carga:,.0f}</div>
            <div class="metric-label">Carga Total (MW)</div>
            <div class="metric-status">
                <div class="status-indicator" style="background: {trend_color};"></div>
                <span style="color: {trend_color};">{"Estável" if tipo_trend_carga == "stable" else "Crescendo" if tipo_trend_carga == "up" else "Reduzindo"}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        renovavel_status = "good" if percentual_renovavel > 70 else "warning" if percentual_renovavel > 50 else "critical"
        renovavel_color = "#10B981" if percentual_renovavel > 70 else "#F59E0B" if percentual_renovavel > 50 else "#EF4444"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{percentual_renovavel:.1f}%</div>
            <div class="metric-label">Energia Renovável</div>
            <div class="metric-status">
                <div class="status-indicator" style="background: {renovavel_color};"></div>
                <span style="color: {renovavel_color};">{"Matriz Limpa" if percentual_renovavel > 70 else "Moderada" if percentual_renovavel > 50 else "Crítica"}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Layout otimizado para TV widescreen
    col_left, col_right = st.columns([1, 3])
    
    with col_left:
        # Geração por fonte - compacto para TV
        st.markdown('<div class="section-title">🔋 Fontes</div>', unsafe_allow_html=True)
        
        # Ordenar fontes por geração
        fontes_ordenadas = sorted(fonte_totals.items(), key=lambda x: x[1], reverse=True)
        
        for fonte, valor in fontes_ordenadas:
            if valor > 0:
                # Calcular tendência
                if fonte in timeline_data:
                    trend_val, trend_tipo = calcular_tendencia(timeline_data[fonte])
                    trend_icon = "↗" if trend_tipo == "up" else "↘" if trend_tipo == "down" else "→"
                    trend_class = f"trend-{trend_tipo}"
                else:
                    trend_icon = "→"
                    trend_class = "trend-stable"
                    trend_val = 0
                
                percentual = (valor / total_geracao * 100)
                source_color = ENERGY_COLORS.get(fonte, '#94A3B8')
                
                st.markdown(f"""
                <div class="source-card" style="--source-color: {source_color};">
                    <div>
                        <div class="source-name" style="font-size: 1rem;">{fonte}</div>
                        <div class="source-percentage" style="font-size: 0.8rem;">{percentual:.1f}%</div>
                    </div>
                    <div style="text-align: right;">
                        <div class="source-value" style="color: {source_color}; font-size: 1.3rem;">{valor:,.0f}</div>
                        <div class="trend-badge {trend_class}" style="font-size: 0.7rem;">
                            {trend_icon} {abs(trend_val):.0f}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Composição da matriz - mais compacta
        st.markdown('<div class="section-title" style="margin-top: 24px;">📊 Matriz</div>', unsafe_allow_html=True)
        
        # Gráfico de rosca menor para TV
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(fonte_totals.keys()),
            values=list(fonte_totals.values()),
            hole=0.65,
            marker=dict(
                colors=[ENERGY_COLORS.get(fonte, '#94A3B8') for fonte in fonte_totals.keys()],
                line=dict(color='#252B3A', width=2)
            ),
            textinfo='percent',
            textfont=dict(size=12, color='#F8FAFC', family='Inter'),
            hovertemplate='<b>%{label}</b><br>%{value:,.0f} MW<extra></extra>'
        )])
        
        fig_pie.add_annotation(
            text=f"<b>{total_geracao:,.0f}</b><br><span style='font-size:12px;'>MW</span>",
            x=0.5, y=0.5,
            font=dict(size=16, family='Inter', color='#F8FAFC'),
            showarrow=False
        )
        
        fig_pie.update_layout(
            height=280,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_right:
        # Gráfico principal maximizado para TV
        st.markdown('<div class="section-title">📈 Geração vs Carga (24h)</div>', unsafe_allow_html=True)
        
        if timeline_data and not carga_data.empty:
            fig_gen_load = go.Figure()
            
            # Adicionar área empilhada para geração por fonte
            fontes_disponiveis = list(timeline_data.keys())
            if 'Hidráulica' in fontes_disponiveis:
                fontes_ordenadas = sorted(fontes_disponiveis, key=lambda x: 0 if x == 'Hidráulica' else 1)
            else:
                fontes_ordenadas = fontes_disponiveis
            
            for fonte in fontes_ordenadas:
                df = timeline_data[fonte]
                if not df.empty:
                    fig_gen_load.add_trace(go.Scatter(
                        x=df['instante'],
                        y=df['geracao'],
                        name=fonte,
                        stackgroup='geracao',
                        line=dict(width=0),
                        fillcolor=ENERGY_COLORS.get(fonte, '#94A3B8'),
                        hovertemplate=f'<b>{fonte}</b><br>%{{x|%H:%M}}<br>%{{y:,.0f}} MW<extra></extra>'
                    ))
            
            # Adicionar linha de carga com efeito neon
            fig_gen_load.add_trace(go.Scatter(
                x=carga_data['instante'],
                y=carga_data['carga'],
                name='Carga Total',
                line=dict(color='#E879F9', width=4, dash='solid'),
                hovertemplate='<b>Carga Total</b><br>%{x|%H:%M}<br>%{y:,.0f} MW<extra></extra>'
            ))
            
            fig_gen_load.update_layout(
                height=600,  # Maior para TV
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(37, 43, 58, 0.3)',
                hovermode='x unified',
                hoverlabel=dict(
                    bgcolor='rgba(37, 43, 58, 0.95)',
                    bordercolor='#3B4252',
                    font=dict(color='#F8FAFC', family='Inter', size=12)
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.12,
                    xanchor="center",
                    x=0.5,
                    bgcolor='rgba(37, 43, 58, 0.8)',
                    bordercolor='#3B4252',
                    borderwidth=1,
                    font=dict(color='#F8FAFC', family='Inter', size=12)
                ),
                xaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(59, 66, 82, 0.3)',
                    gridwidth=1,
                    title="Horário",
                    titlefont=dict(color='#94A3B8', size=14, family='Inter'),
                    tickfont=dict(color='#94A3B8', size=12, family='Inter'),
                    linecolor='#3B4252'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(59, 66, 82, 0.3)',
                    gridwidth=1,
                    title="Potência (MW)",
                    titlefont=dict(color='#94A3B8', size=14, family='Inter'),
                    tickfont=dict(color='#94A3B8', size=12, family='Inter'),
                    linecolor='#3B4252'
                )
            )
            
            st.plotly_chart(fig_gen_load, use_container_width=True)
    
    # Estatísticas adicionais compactas para TV
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        eficiencia = (total_carga / total_geracao * 100) if total_geracao > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #06B6D4; font-size: 2rem;">{eficiencia:.1f}%</div>
            <div class="metric-label">Eficiência</div>
            <div class="metric-status">
                <div class="status-indicator" style="background: #06B6D4;"></div>
                <span style="color: #06B6D4; font-size: 0.8rem;">Otimizada</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_stat2:
        fonte_dominante = max(fonte_totals.items(), key=lambda x: x[1])
        percentual_dominante = (fonte_dominante[1] / total_geracao * 100)
        cor_dominante = ENERGY_COLORS.get(fonte_dominante[0], '#94A3B8')
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {cor_dominante}; font-size: 2rem;">{percentual_dominante:.1f}%</div>
            <div class="metric-label">Dominante</div>
            <div class="metric-status">
                <div class="status-indicator" style="background: {cor_dominante};"></div>
                <span style="color: {cor_dominante}; font-size: 0.8rem;">{fonte_dominante[0]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_stat3:
        margem = total_geracao - total_carga
        margem_color = "#10B981" if margem > 1000 else "#F59E0B" if margem > 0 else "#EF4444"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {margem_color}; font-size: 2rem;">{margem:,.0f}</div>
            <div class="metric-label">Reserva (MW)</div>
            <div class="metric-status">
                <div class="status-indicator" style="background: {margem_color};"></div>
                <span style="color: {margem_color}; font-size: 0.8rem;">{"Segura" if margem > 1000 else "Atenção" if margem > 0 else "Crítica"}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer premium com indicador ao vivo
    st.markdown(f"""
    <div class="footer">
        <div class="footer-content">
            <div>
                <strong style="color: #F8FAFC;">Fonte de Dados:</strong> 
                <span style="color: #94A3B8;">ONS (Operador Nacional do Sistema Elétrico)</span>
                <br>
                <strong style="color: #F8FAFC;">Frequência:</strong> 
                <span style="color: #94A3B8;">Atualização automática a cada 20 segundos</span>
            </div>
            <div class="live-indicator">
                <div class="live-dot"></div>
                <span style="color: #10B981; font-weight: 600;">
                    AO VIVO • {datetime.now().strftime('%H:%M:%S')}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # Estado de erro com design elegante
    st.markdown("""
    <div class="metric-card" style="text-align: center; padding: 64px;">
        <div style="font-size: 4rem; margin-bottom: 24px;">⚠️</div>
        <div class="metric-value" style="color: #EF4444;">Dados Indisponíveis</div>
        <div class="metric-label" style="margin-top: 16px;">
            Não foi possível conectar com os servidores do ONS.<br>
            Tentando reconectar automaticamente...
        </div>
        <div class="metric-status" style="margin-top: 24px; justify-content: center;">
            <div class="status-indicator status-critical" style="background: #EF4444;"></div>
            <span style="color: #EF4444;">Sistema Offline</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Atualização automática a cada 30 segundos
time.sleep(30)
st.rerun()
