import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Sistema Elétrico Brasileiro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cores e estilos modernos
BACKGROUND_COLOR = "#0f172a"  # Slate 900
CARD_COLOR = "#1e293b"        # Slate 800
TEXT_COLOR = "#f8fafc"        # Slate 50
GRID_COLOR = "#334155"        # Slate 700
ACCENT_COLOR = "#3b82f6"      # Blue 500

# Cores para fontes de energia
ENERGY_COLORS = {
    'Hidráulica': '#60A5FA',    # Blue 400
    'Eólica': '#34D399',        # Emerald 400
    'Solar': '#FBBF24',         # Amber 400
    'Térmica': '#F87171',       # Red 400
    'Nuclear': '#A78BFA',       # Purple 400
    'Carga': '#EC4899'          # Pink 400
}

# Funções de obtenção de dados
@st.cache_data(ttl=20)
def get_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            if response.content and response.content.strip():
                data = response.json()
                if isinstance(data, list) and data:
                    df = pd.DataFrame(data)
                    if not df.empty:
                        df['instante'] = pd.to_datetime(df['instante'], errors='coerce')
                        df = df.dropna(subset=['instante'])
                        df['geracao'] = df['geracao']
                        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
    return None

@st.cache_data(ttl=20)
def get_carga_data():
    url = "https://integra.ons.org.br/api/energiaagora/Get/Carga_SIN_json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df['instante'] = pd.to_datetime(df['instante'])
            return df
    except Exception as e:
        st.error(f"Erro ao carregar dados de carga: {e}")
    return None

@st.cache_data(ttl=20)
def get_balanco_energetico():
    url = "https://integra.ons.org.br/api/energiaagora/GetBalancoEnergetico/null"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Erro ao carregar balanço energético: {e}")
    return None

@st.cache_data(ttl=20)
def get_situacao_reservatorios():
    url = "https://integra.ons.org.br/api/energiaagora/Get/SituacaoDosReservatorios"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Erro ao carregar situação dos reservatórios: {e}")
    return None

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
            if df is not None:
                key = f'{fonte} - {regiao}'
                dataframes[key] = df
    
    balanco = get_balanco_energetico()
    reservatorios = get_situacao_reservatorios()
    
    return dataframes, balanco, reservatorios

# Função para processar dados
def process_data(dataframes):
    if not dataframes:
        return None, None
    
    # Agregando dados por fonte
    fonte_totals = {}
    for key, df in dataframes.items():
        fonte = key.split(' - ')[0]
        if fonte not in fonte_totals:
            fonte_totals[fonte] = df['geracao'].iloc[-1] if not df.empty else 0
        else:
            fonte_totals[fonte] += df['geracao'].iloc[-1] if not df.empty else 0
    
    # Preparando dados para gráfico de 24h
    timeline_data = {}
    for key, df in dataframes.items():
        fonte = key.split(' - ')[0]
        if not df.empty:
            if fonte not in timeline_data:
                timeline_data[fonte] = df.copy()
            else:
                timeline_data[fonte]['geracao'] += df['geracao']
    
    return fonte_totals, timeline_data

# Estilo personalizado moderno
st.markdown("""
    <style>
    .main {
        background-color: #0f172a;
    }
    .stApp {
        background-color: #0f172a;
    }
    .metric-container {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }
    .metric-container:hover {
        transform: translateY(-2px);
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #f8fafc;
    }
    .metric-label {
        font-size: 14px;
        color: #94a3b8;
    }
    .chart-container {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .section-header {
        color: #f8fafc;
        font-size: 24px;
        font-weight: bold;
        margin: 20px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid #3b82f6;
    }
    </style>
""", unsafe_allow_html=True)

# Header moderno
st.markdown("""
    <div style='background: linear-gradient(90deg, #1e293b, #0f172a); padding: 30px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);'>
        <h1 style='color: #f8fafc; margin: 0; display: flex; align-items: center;'>
            <span style='font-size: 32px; margin-right: 10px;'>⚡</span>
            Sistema Elétrico Brasileiro
        </h1>
        <p style='color: #94a3b8; margin: 10px 0 0 0;'>Monitoramento em Tempo Real</p>
    </div>
""", unsafe_allow_html=True)

# Carregando dados
dataframes, balanco, reservatorios = load_data()
carga_data = get_carga_data()
fonte_totals, timeline_data = process_data(dataframes)

# Métricas principais em cards modernos
if fonte_totals and carga_data is not None:
    total_geracao = sum(fonte_totals.values())
    total_carga = carga_data['carga'].iloc[-1] if not carga_data.empty else 0
    renovaveis = (fonte_totals.get('Hidráulica', 0) + fonte_totals.get('Eólica', 0) + 
                  fonte_totals.get('Solar', 0))
    percentual_renovavel = (renovaveis / total_geracao * 100) if total_geracao > 0 else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown("""
            <div class='metric-container'>
                <div class='metric-value'>💡 {:,.0f} MW</div>
                <div class='metric-label'>Geração Total</div>
            </div>
        """.format(total_geracao), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class='metric-container'>
                <div class='metric-value'>⚡ {:,.0f} MW</div>
                <div class='metric-label'>Carga Total</div>
            </div>
        """.format(total_carga), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class='metric-container'>
                <div class='metric-value'>🌱 {:.1f}%</div>
                <div class='metric-label'>Energia Renovável</div>
            </div>
        """.format(percentual_renovavel), unsafe_allow_html=True)
    
    with col4:
        if reservatorios:
            nivel_medio = sum(r.get('valor', 0) for r in reservatorios) / len(reservatorios)
            st.markdown("""
                <div class='metric-container'>
                    <div class='metric-value'>💧 {:.1f}%</div>
                    <div class='metric-label'>Nível Reservatórios</div>
                </div>
            """.format(nivel_medio), unsafe_allow_html=True)
    
    with col5:
        margem = ((total_geracao - total_carga) / total_geracao * 100) if total_geracao > 0 else 0
        st.markdown("""
            <div class='metric-container'>
                <div class='metric-value'>📊 {:.1f}%</div>
                <div class='metric-label'>Margem de Capacidade</div>
            </div>
        """.format(margem), unsafe_allow_html=True)

# Gráfico de Geração vs Carga
st.markdown("<h3 class='section-header'>Geração vs Carga (24h)</h3>", unsafe_allow_html=True)
if timeline_data and carga_data is not None:
    fig = go.Figure()
    
    # Adicionando linha de carga
    fig.add_trace(go.Scatter(
        x=carga_data['instante'],
        y=carga_data['carga'],
        name='Carga Total',
        line=dict(color=ENERGY_COLORS['Carga'], width=3, dash='dot'),
    ))
    
    # Adicionando área empilhada de geração por fonte
    for fonte, df in timeline_data.items():
        fig.add_trace(go.Scatter(
            x=df['instante'],
            y=df['geracao'],
            name=fonte,
            stackgroup='geracao',
            line=dict(width=0),
            fillcolor=ENERGY_COLORS.get(fonte, '#FFFFFF')
        ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=CARD_COLOR,
        plot_bgcolor=CARD_COLOR,
        margin=dict(t=20, b=20, l=20, r=20),
        height=400,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            title="Hora"
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            title="MW"
        )
    )
    # Gráficos principais
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Matriz Elétrica Atual")
    if fonte_totals:
        # Gráfico de rosca com dados reais
        fig_rosca = go.Figure(data=[go.Pie(
            labels=list(fonte_totals.keys()),
            values=list(fonte_totals.values()),
            hole=.75,
            marker_colors=['#60A5FA', '#34D399', '#FBBF24', '#F87171', '#A78BFA'],
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(size=12, color=TEXT_COLOR)
        )])
        
        fig_rosca.add_annotation(
            text=f'Total<br>{total_geracao:,.0f}<br>MW',
            x=0.5, y=0.5,
            font=dict(size=16, color=TEXT_COLOR, family='Arial Black'),
            showarrow=False
        )
        
        fig_rosca.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(color=TEXT_COLOR)
            ),
            margin=dict(t=20, b=20, l=20, r=20),
            height=400,
            paper_bgcolor=CARD_COLOR,
            plot_bgcolor=CARD_COLOR
        )
        
        st.plotly_chart(fig_rosca, use_container_width=True)

with col2:
    st.markdown("### Geração por Fonte (24h)")
    if timeline_data:
        fig_linha = go.Figure()
        
        cores = {
            'Hidráulica': '#60A5FA',
            'Eólica': '#34D399',
            'Solar': '#FBBF24',
            'Térmica': '#F87171',
            'Nuclear': '#A78BFA'
        }
        
        for fonte, df in timeline_data.items():
            fig_linha.add_trace(go.Scatter(
                x=df['instante'],
                y=df['geracao'],
                name=fonte,
                line=dict(color=cores.get(fonte, '#FFFFFF'), width=2),
                fill='tonexty' if fonte == list(timeline_data.keys())[0] else 'none'
            ))
        
        fig_linha.update_layout(
            xaxis_title="Hora",
            yaxis_title="Geração (MW)",
            margin=dict(t=20, b=20, l=20, r=20),
            height=400,
            paper_bgcolor=CARD_COLOR,
            plot_bgcolor=CARD_COLOR,
            font=dict(color=TEXT_COLOR),
            xaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
            yaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(color=TEXT_COLOR)
            )
        )
        
        st.plotly_chart(fig_linha, use_container_width=True)

# Gráficos de fontes renováveis
st.markdown("### Geração Renovável por Região")
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Eólica")
    eolica_data = {k: v for k, v in dataframes.items() if 'Eólica' in k}
    if eolica_data:
        fig_eolica = go.Figure()
        
        for regiao, df in eolica_data.items():
            regiao_nome = regiao.split(' - ')[1]
            fig_eolica.add_trace(go.Scatter(
                x=df['instante'],
                y=df['geracao'],
                name=regiao_nome,
                line=dict(width=2)
            ))
        
        fig_eolica.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            height=300,
            paper_bgcolor=CARD_COLOR,
            plot_bgcolor=CARD_COLOR,
            font=dict(color=TEXT_COLOR),
            xaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
            yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, title="MW")
        )
        
        st.plotly_chart(fig_eolica, use_container_width=True)

with col2:
    st.markdown("#### Solar")
    solar_data = {k: v for k, v in dataframes.items() if 'Solar' in k}
    if solar_data:
        fig_solar = go.Figure()
        
        for regiao, df in solar_data.items():
            regiao_nome = regiao.split(' - ')[1]
            fig_solar.add_trace(go.Scatter(
                x=df['instante'],
                y=df['geracao'],
                name=regiao_nome,
                line=dict(width=2)
            ))
        
        fig_solar.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            height=300,
            paper_bgcolor=CARD_COLOR,
            plot_bgcolor=CARD_COLOR,
            font=dict(color=TEXT_COLOR),
            xaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
            yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, title="MW")
        )
        
        st.plotly_chart(fig_solar, use_container_width=True)

# Status dos Reservatórios
if reservatorios:
    st.markdown("### Status dos Reservatórios")
    cols = st.columns(len(reservatorios))
    for col, reservatorio in zip(cols, reservatorios):
        with col:
            st.markdown(f"""
                <div class="status-card">
                    <h4 style='color: #F9FAFB; margin: 0;'>{reservatorio.get('subsistema', '')}</h4>
                    <h2 style='color: #F9FAFB; margin: 10px 0;'>{reservatorio.get('valor', 0):.1f}%</h2>
                    <p style='color: #9CA3AF; margin: 0;'>Capacidade</p>
                </div>
            """, unsafe_allow_html=True)

# Informações de atualização
st.markdown(f"""
    <div style='background-color: {CARD_COLOR}; padding: 20px; border-radius: 12px; margin-top: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);'>
        <h4 style='color: {TEXT_COLOR}; margin-bottom: 12px;'>ℹ️ Informações do Sistema</h4>
        <p style='color: #9CA3AF; margin: 0;'>• Dados atualizados a cada 20 segundos</p>
        <p style='color: #9CA3AF; margin: 4px 0;'>• Fonte: ONS (Operador Nacional do Sistema Elétrico)</p>
        <p style='color: #9CA3AF; margin: 4px 0;'>• Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    </div>
""", unsafe_allow_html=True)
