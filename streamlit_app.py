import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import numpy as np
import time

# Configuração da página
st.set_page_config(
    page_title="Sistema Elétrico Brasileiro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Paleta de cores minimalista
COLORS = {
    'background': '#FFFFFF',
    'surface': '#F8FAFC',
    'card': '#FFFFFF',
    'border': '#E2E8F0',
    'text_primary': '#1E293B',
    'text_secondary': '#64748B',
    'accent': '#3B82F6',
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444'
}

# Cores para fontes de energia - tons suaves
ENERGY_COLORS = {
    'Hidráulica': '#3B82F6',    # Azul
    'Eólica': '#10B981',        # Verde
    'Solar': '#F59E0B',         # Amarelo
    'Térmica': '#EF4444',       # Vermelho
    'Nuclear': '#8B5CF6',       # Roxo
    'Carga': '#1E293B'          # Cinza escuro
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

# CSS minimalista
st.markdown("""
<style>
    .main {
        background-color: #FFFFFF;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background-color: #FFFFFF;
    }
    
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 24px;
        margin: 8px 0;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transform: translateY(-1px);
    }
    
    .metric-value {
        font-size: 2.25rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 4px;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #64748B;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-trend {
        font-size: 0.75rem;
        margin-top: 8px;
        padding: 4px 8px;
        border-radius: 6px;
        display: inline-block;
        font-weight: 600;
    }
    
    .trend-up {
        background: #DCFCE7;
        color: #16A34A;
    }
    
    .trend-down {
        background: #FEE2E2;
        color: #DC2626;
    }
    
    .trend-stable {
        background: #F1F5F9;
        color: #64748B;
    }
    
    .source-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        margin: 4px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s ease;
    }
    
    .source-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .source-name {
        font-weight: 600;
        color: #1E293B;
    }
    
    .source-value {
        font-size: 1.125rem;
        font-weight: 700;
        color: #1E293B;
    }
    
    .chart-container {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid #F1F5F9;
    }
    
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 32px;
        border-radius: 16px;
        margin-bottom: 32px;
        color: white;
        text-align: center;
    }
    
    .header h1 {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .header p {
        font-size: 1.125rem;
        opacity: 0.9;
        margin: 8px 0 0 0;
    }
    
    .status-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    
    .status-good { background: #10B981; }
    .status-warning { background: #F59E0B; }
    .status-critical { background: #EF4444; }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    .stPlotlyChart {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Hide Streamlit elements */
    footer { display: none; }
    .stDeployButton { display: none; }
    #MainMenu { display: none; }
    header { display: none; }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #F1F5F9;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #CBD5E1;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #94A3B8;
    }
</style>
""", unsafe_allow_html=True)

# Header minimalista
current_time = datetime.now().strftime('%H:%M')
current_date = datetime.now().strftime('%d/%m/%Y')

st.markdown(f"""
<div class="header">
    <h1>⚡ Sistema Elétrico Brasileiro</h1>
    <p>Monitoramento em tempo real • {current_date} às {current_time}</p>
</div>
""", unsafe_allow_html=True)

# Carregar dados
with st.spinner('Carregando dados...'):
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
    
    # Cards de métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_geracao:,.0f}</div>
            <div class="metric-label">Geração Total (MW)</div>
            <div class="status-indicator status-good"></div>
            Sistema operando normalmente
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_carga:,.0f}</div>
            <div class="metric-label">Carga Total (MW)</div>
            <div class="status-indicator status-good"></div>
            Demanda estável
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{percentual_renovavel:.1f}%</div>
            <div class="metric-label">Energia Renovável</div>
            <div class="status-indicator status-good"></div>
            Matriz limpa
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        margem_status = "good" if margem > 1000 else "warning" if margem > 0 else "critical"
        status_text = "Reserva adequada" if margem > 1000 else "Atenção" if margem > 0 else "Crítico"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{margem:,.0f}</div>
            <div class="metric-label">Margem (MW)</div>
            <div class="status-indicator status-{margem_status}"></div>
            {status_text}
        </div>
        """, unsafe_allow_html=True)
    
    # Layout de duas colunas
    col_left, col_right = st.columns([2, 3])
    
    with col_left:
        # Geração por fonte - design minimalista
        st.markdown('<div class="section-title">Geração por Fonte</div>', unsafe_allow_html=True)
        
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
                
                st.markdown(f"""
                <div class="source-card">
                    <div>
                        <div class="source-name" style="color: {ENERGY_COLORS.get(fonte, '#64748B')}">
                            {fonte}
                        </div>
                        <div style="font-size: 0.875rem; color: #64748B; margin-top: 2px;">
                            {percentual:.1f}% do total
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div class="source-value">{valor:,.0f} MW</div>
                        <div class="metric-trend {trend_class}">
                            {trend_icon} {abs(trend_val):.1f}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Composição da matriz
        st.markdown('<div class="section-title" style="margin-top: 32px;">Composição da Matriz</div>', unsafe_allow_html=True)
        
        # Gráfico de rosca minimalista
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(fonte_totals.keys()),
            values=list(fonte_totals.values()),
            hole=0.6,
            marker=dict(
                colors=[ENERGY_COLORS.get(fonte, '#94A3B8') for fonte in fonte_totals.keys()],
                line=dict(color='#FFFFFF', width=2)
            ),
            textinfo='label+percent',
            textfont=dict(size=12, color='#1E293B'),
            hovertemplate='<b>%{label}</b><br>%{value:,.0f} MW<br>%{percent}<extra></extra>'
        )])
        
        fig_pie.add_annotation(
            text=f"<b>{total_geracao:,.0f}</b><br><span style='font-size:14px;'>MW</span>",
            x=0.5, y=0.5,
            font=dict(size=20, color='#1E293B'),
            showarrow=False
        )
        
        fig_pie.update_layout(
            height=350,
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_right:
        # Gráfico de Geração vs Carga (mantido do código original)
        st.markdown('<div class="section-title">Geração vs Carga (24h)</div>', unsafe_allow_html=True)
        
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
            
            # Adicionar linha de carga
            fig_gen_load.add_trace(go.Scatter(
                x=carga_data['instante'],
                y=carga_data['carga'],
                name='Carga Total',
                line=dict(color='#1E293B', width=3),
                hovertemplate='<b>Carga Total</b><br>%{x|%H:%M}<br>%{y:,.0f} MW<extra></extra>'
            ))
            
            fig_gen_load.update_layout(
                height=500,
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.15,
                    xanchor="center",
                    x=0.5,
                    bgcolor='rgba(255,255,255,0.9)',
                    bordercolor='#E2E8F0',
                    borderwidth=1
                ),
                xaxis=dict(
                    showgrid=True,
                    gridcolor='#F1F5F9',
                    gridwidth=1,
                    title="Horário",
                    titlefont=dict(color='#64748B', size=12),
                    tickfont=dict(color='#64748B', size=11),
                    linecolor='#E2E8F0'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='#F1F5F9',
                    gridwidth=1,
                    title="Potência (MW)",
                    titlefont=dict(color='#64748B', size=12),
                    tickfont=dict(color='#64748B', size=11),
                    linecolor='#E2E8F0'
                )
            )
            
            st.plotly_chart(fig_gen_load, use_container_width=True)
    
    # Footer minimalista
    st.markdown(f"""
    <div style="margin-top: 48px; padding: 24px; background: #F8FAFC; border-radius: 12px; border: 1px solid #E2E8F0;">
        <div style="display: flex; justify-content: between; align-items: center; color: #64748B; font-size: 0.875rem;">
            <div>
                <strong>Fonte:</strong> ONS (Operador Nacional do Sistema Elétrico) • 
                <strong>Atualização:</strong> A cada 20 segundos
            </div>
            <div style="margin-left: auto;">
                Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.error("❌ Não foi possível carregar os dados do sistema elétrico.")

# Opção de atualização automática
if st.checkbox("🔄 Atualização automática", value=False):
    time.sleep(30)
    st.rerun()
