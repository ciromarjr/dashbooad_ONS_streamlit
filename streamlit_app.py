import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Sistema Elétrico Brasileiro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Keep original colors and styles
BACKGROUND_COLOR = "#0f172a"  # Slate 900
CARD_COLOR = "#1e293b"        # Slate 800
TEXT_COLOR = "#f8fafc"        # Slate 50
GRID_COLOR = "#334155"        # Slate 700
ACCENT_COLOR = "#3b82f6"      # Blue 500

# Original colors for energy sources
ENERGY_COLORS = {
    'Hidráulica': '#60A5FA',    # Blue 400
    'Eólica': '#34D399',        # Emerald 400
    'Solar': '#FBBF24',         # Amber 400
    'Térmica': '#F87171',       # Red 400
    'Nuclear': '#A78BFA',       # Purple 400
    'Carga': '#EC4899'          # Pink 400
}

# Data retrieval functions (improved)
@st.cache_data(ttl=20)
def get_data(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and response.content and response.content.strip():
            data = response.json()
            if isinstance(data, list) and data:
                df = pd.DataFrame(data)
                if not df.empty:
                    df['instante'] = pd.to_datetime(df['instante'], errors='coerce')
                    df = df.dropna(subset=['instante'])
                    return df
        return pd.DataFrame(columns=['instante', 'geracao'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
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
    except Exception as e:
        st.error(f"Erro ao carregar dados de carga: {e}")
        return pd.DataFrame(columns=['instante', 'carga'])
    
@st.cache_data(ttl=20)
def get_regional_carga_data(region):
    url = f"https://integra.ons.org.br/api/energiaagora/Get/Carga_{region}_json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df['instante'] = pd.to_datetime(df['instante'])
            return df
        return pd.DataFrame(columns=['instante', 'carga'])
    except Exception as e:
        st.error(f"Erro ao carregar dados de carga regional: {e}")
        return pd.DataFrame(columns=['instante', 'carga'])

@st.cache_data(ttl=20)
def get_balanco_energetico():
    url = "https://integra.ons.org.br/api/energiaagora/GetBalancoEnergetico/null"
    try:
        response = requests.get(url, timeout=5)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Erro ao carregar balanço energético: {e}")
        return None

@st.cache_data(ttl=20)
def get_situacao_reservatorios():
    url = "https://integra.ons.org.br/api/energiaagora/Get/SituacaoDosReservatorios"
    try:
        response = requests.get(url, timeout=5)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Erro ao carregar situação dos reservatórios: {e}")
        return None

@st.cache_data(ttl=20)
def process_reservatorio_data(data):
    if not data:
        return None
        
    # Group by subsystem
    subsistemas = {}
    for reservatorio in data:
        subsistema = reservatorio.get('Subsistema')
        if subsistema not in subsistemas:
            subsistemas[subsistema] = {
                'valor_util_total': 0,
                'reservatorios': [],
                'quantidade': 0,
                'ear_verificada': 0,
                'ear_maxima': 0
            }
        
        # Add reservoir information
        subsistemas[subsistema]['reservatorios'].append({
            'nome': reservatorio.get('Reservatorio'),
            'valor_util': reservatorio.get('ReservatorioValorUtil', 0),
            'porcentagem': reservatorio.get('ReservatorioPorcentagem', 0),
            'ear_verificada': reservatorio.get('ReservatorioEARVerificadaMWMes', 0),
            'ear_maxima': reservatorio.get('ReservatorioMax', 0),
            'bacia': reservatorio.get('Bacia')
        })
        
        # Update subsystem totals
        subsistemas[subsistema]['quantidade'] += 1
        subsistemas[subsistema]['ear_verificada'] += reservatorio.get('ReservatorioEARVerificadaMWMes', 0)
        subsistemas[subsistema]['ear_maxima'] += reservatorio.get('ReservatorioMax', 0)
        subsistemas[subsistema]['valor_util_total'] += reservatorio.get('ReservatorioValorUtil', 0)
    
    # Calculate averages for each subsystem
    for subsistema in subsistemas:
        if subsistemas[subsistema]['quantidade'] > 0:
            subsistemas[subsistema]['valor_util_medio'] = (
                subsistemas[subsistema]['valor_util_total'] / 
                subsistemas[subsistema]['quantidade']
            )
            subsistemas[subsistema]['ear_porcentagem'] = (
                (subsistemas[subsistema]['ear_verificada'] / 
                subsistemas[subsistema]['ear_maxima']) * 100 
                if subsistemas[subsistema]['ear_maxima'] > 0 else 0
            )
    
    return subsistemas

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
    
    balanco = get_balanco_energetico()
    reservatorios = get_situacao_reservatorios()
    
    return dataframes, balanco, reservatorios

def process_data(dataframes):
    if not dataframes:
        return {}, {}, {}
    
    # Aggregate data by source
    fonte_totals = {}
    for key, df in dataframes.items():
        if df.empty:
            continue
        fonte = key.split(' - ')[0]
        if fonte not in fonte_totals:
            fonte_totals[fonte] = df['geracao'].iloc[-1]
        else:
            fonte_totals[fonte] += df['geracao'].iloc[-1]
    
    # Prepare data for 24h chart
    timeline_data = {}
    for key, df in dataframes.items():
        if df.empty:
            continue
        fonte = key.split(' - ')[0]
        if fonte not in timeline_data:
            timeline_data[fonte] = df.copy()
        else:
            timeline_data[fonte]['geracao'] += df['geracao']
    
    # Prepare regional data for the new regional view
    regional_data = {}
    for key, df in dataframes.items():
        if df.empty:
            continue
        fonte, regiao = key.split(' - ')
        if regiao not in regional_data:
            regional_data[regiao] = {}
        
        if fonte not in regional_data[regiao]:
            regional_data[regiao][fonte] = df['geracao'].iloc[-1]
        else:
            regional_data[regiao][fonte] += df['geracao'].iloc[-1]
    
    return fonte_totals, timeline_data, regional_data

# Custom style keeping original colors
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
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
        height: 100%;
    }
    .metric-value {
        font-size: 20px;
        font-weight: bold;
        color: #f8fafc;
    }
    .metric-label {
        font-size: 12px;
        color: #94a3b8;
    }
    .chart-container {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 15px;
        margin: 5px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .section-header {
        color: #f8fafc;
        font-size: 18px;
        font-weight: bold;
        margin: 10px 0;
        padding-bottom: 5px;
        border-bottom: 2px solid #3b82f6;
    }
    .reservoir-card {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        height: 100%;
    }
    .region-card {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        height: 100%;
    }
    /* Reduce spacing for better fit */
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    .stPlotlyChart {
        padding: 0 !important;
    }
    /* Hide "Made with Streamlit" footer */
    footer {
        display: none;
    }
    .stHeading, .stMarkdown p {
        padding-bottom: 0.25rem !important;
        margin-bottom: 0.25rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# Get current time for display
current_time = datetime.now().strftime('%H:%M:%S')
current_date_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

# Streamlined header for monitoring screen
st.markdown(f"""
    <div style='background: linear-gradient(90deg, #1e293b, #0f172a); padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);'>
        <h1 style='color: #f8fafc; margin: 0; display: flex; align-items: center; font-size: 24px;'>
            <span style='font-size: 24px; margin-right: 10px;'>⚡</span>
            Sistema Elétrico Brasileiro
            <span style='font-size: 14px; margin-left: auto; color: #94a3b8;'>
                Atualizado: {current_time}
            </span>
        </h1>
    </div>
""", unsafe_allow_html=True)

# Load data
dataframes, balanco, reservatorios = load_data()
carga_data = get_carga_data()
fonte_totals, timeline_data, regional_data = process_data(dataframes)

# Load regional load data
norte_carga = get_regional_carga_data("Norte")
nordeste_carga = get_regional_carga_data("Nordeste")
sudeste_carga = get_regional_carga_data("SudesteECentroOeste")
sul_carga = get_regional_carga_data("Sul")

# Main layout with two columns
col1, col2 = st.columns([1, 1])

# Left column: System overview and regional data
with col1:
    # Key metrics at the top
    if fonte_totals and not carga_data.empty:
        total_geracao = sum(fonte_totals.values())
        total_carga = carga_data['carga'].iloc[-1] if 'carga' in carga_data else 0
        renovaveis = (fonte_totals.get('Hidráulica', 0) + fonte_totals.get('Eólica', 0) + 
                      fonte_totals.get('Solar', 0))
        percentual_renovavel = (renovaveis / total_geracao * 100) if total_geracao > 0 else 0
        margem = ((total_geracao - total_carga) / total_geracao * 100) if total_geracao > 0 else 0
        margem_color = "#34D399" if margem > 5 else "#FBBF24" if margem > 0 else "#F87171"
        
        metric_cols = st.columns(4)
        
        with metric_cols[0]:
            st.markdown(f"""
                <div class='metric-container'>
                    <div class='metric-value'>💡 {total_geracao:,.0f} MW</div>
                    <div class='metric-label'>Geração Total</div>
                </div>
            """, unsafe_allow_html=True)
        
        with metric_cols[1]:
            st.markdown(f"""
                <div class='metric-container'>
                    <div class='metric-value'>⚡ {total_carga:,.0f} MW</div>
                    <div class='metric-label'>Carga Total</div>
                </div>
            """, unsafe_allow_html=True)
        
        with metric_cols[2]:
            st.markdown(f"""
                <div class='metric-container'>
                    <div class='metric-value'>🌱 {percentual_renovavel:.1f}%</div>
                    <div class='metric-label'>Energia Renovável</div>
                </div>
            """, unsafe_allow_html=True)
        
        with metric_cols[3]:
            st.markdown(f"""
                <div class='metric-container'>
                    <div class='metric-value' style='color: {margem_color};'>📊 {margem:.1f}%</div>
                    <div class='metric-label'>Margem</div>
                </div>
            """, unsafe_allow_html=True)
    
    # Matrix with sources breakdown
    st.markdown("<h3 class='section-header'>Matriz Elétrica Atual</h3>", unsafe_allow_html=True)
    
    if fonte_totals:
        fig_matriz = go.Figure()
        
        # Sort to ensure Hydro is at the base (first)
        sorted_keys = sorted(fonte_totals.keys(), key=lambda x: 0 if x == 'Hidráulica' else 1)
        
        # Create a single stacked bar
        for fonte in sorted_keys:
            fig_matriz.add_trace(go.Bar(
                x=['Geração Atual'],
                y=[fonte_totals[fonte]],
                name=fonte,
                marker_color=ENERGY_COLORS[fonte],
                text=f"{fonte}: {fonte_totals[fonte]:,.0f} MW",
                textposition="inside",
                insidetextanchor="middle",
                width=0.6
            ))
        
        # Add total annotation at the top
        fig_matriz.add_annotation(
            x='Geração Atual', y=sum(fonte_totals.values()) + (sum(fonte_totals.values()) * 0.05),
            text=f"Total: {sum(fonte_totals.values()):,.0f} MW",
            showarrow=False,
            font=dict(size=14, color="#f8fafc")
        )
        
        # Customize layout
        fig_matriz.update_layout(
            template='plotly_dark',
            paper_bgcolor=CARD_COLOR,
            plot_bgcolor=CARD_COLOR,
            margin=dict(t=30, b=30, l=30, r=30),
            height=300,
            barmode='stack',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(size=11, color=TEXT_COLOR)
            ),
            xaxis=dict(
                showgrid=False,
                showticklabels=False
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=GRID_COLOR,
                title="MW",
                titlefont=dict(color=TEXT_COLOR, size=12),
                tickfont=dict(color=TEXT_COLOR, size=10)
            )
        )
        
        st.plotly_chart(fig_matriz, use_container_width=True)
    
    # Regional load section
    st.markdown("<h3 class='section-header'>Carga por Região</h3>", unsafe_allow_html=True)
    
    # Get latest values for each region
    region_data = {
        "Norte": norte_carga['carga'].iloc[-1] if not norte_carga.empty else 0,
        "Nordeste": nordeste_carga['carga'].iloc[-1] if not nordeste_carga.empty else 0,
        "Sudeste/Centro-Oeste": sudeste_carga['carga'].iloc[-1] if not sudeste_carga.empty else 0,
        "Sul": sul_carga['carga'].iloc[-1] if not sul_carga.empty else 0
    }
    
    # Create regional load visualization
    fig_regions = go.Figure()
    regions = list(region_data.keys())
    values = list(region_data.values())
    colors = ['#60A5FA', '#34D399', '#F87171', '#FBBF24']
    
    fig_regions.add_trace(go.Bar(
        x=regions,
        y=values,
        marker_color=colors,
        text=[f"{v:,.0f} MW" for v in values],
        textposition="inside"
    ))
    
    fig_regions.update_layout(
        template='plotly_dark',
        paper_bgcolor=CARD_COLOR,
        plot_bgcolor=CARD_COLOR,
        margin=dict(t=20, b=30, l=30, r=30),
        height=300,
        xaxis=dict(
            title="Região",
            titlefont=dict(color=TEXT_COLOR, size=12),
            tickfont=dict(color=TEXT_COLOR, size=10)
        ),
        yaxis=dict(
            title="Carga (MW)",
            titlefont=dict(color=TEXT_COLOR, size=12),
            tickfont=dict(color=TEXT_COLOR, size=10),
            showgrid=True,
            gridcolor=GRID_COLOR
        )
    )
    
    st.plotly_chart(fig_regions, use_container_width=True)
    
    # Regional load timeline
    if not norte_carga.empty and not nordeste_carga.empty and not sudeste_carga.empty and not sul_carga.empty:
        fig_regional_timeline = go.Figure()
        
        # Add a trace for each region
        fig_regional_timeline.add_trace(go.Scatter(
            x=norte_carga['instante'],
            y=norte_carga['carga'],
            name="Norte",
            line=dict(color='#60A5FA', width=2)
        ))
        
        fig_regional_timeline.add_trace(go.Scatter(
            x=nordeste_carga['instante'],
            y=nordeste_carga['carga'],
            name="Nordeste",
            line=dict(color='#34D399', width=2)
        ))
        
        fig_regional_timeline.add_trace(go.Scatter(
            x=sudeste_carga['instante'],
            y=sudeste_carga['carga'],
            name="Sudeste/CO",
            line=dict(color='#F87171', width=2)
        ))
        
        fig_regional_timeline.add_trace(go.Scatter(
            x=sul_carga['instante'],
            y=sul_carga['carga'],
            name="Sul",
            line=dict(color='#FBBF24', width=2)
        ))
        
        fig_regional_timeline.update_layout(
            template='plotly_dark',
            paper_bgcolor=CARD_COLOR,
            plot_bgcolor=CARD_COLOR,
            margin=dict(t=20, b=40, l=30, r=30),
            height=300,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=10, color=TEXT_COLOR)
            ),
            xaxis=dict(
                title="Hora",
                titlefont=dict(color=TEXT_COLOR, size=12),
                tickfont=dict(color=TEXT_COLOR, size=10),
                showgrid=True,
                gridcolor=GRID_COLOR
            ),
            yaxis=dict(
                title="Carga (MW)",
                titlefont=dict(color=TEXT_COLOR, size=12),
                tickfont=dict(color=TEXT_COLOR, size=10),
                showgrid=True,
                gridcolor=GRID_COLOR
            )
        )
        
        st.plotly_chart(fig_regional_timeline, use_container_width=True)

# Right column: Generation vs Load and Reservoirs status
with col2:
    # Generation vs Load graph
    st.markdown("<h3 class='section-header'>Geração vs Carga (24h)</h3>", unsafe_allow_html=True)
    
    if timeline_data and not carga_data.empty:
        fig_gen_load = go.Figure()
        
        # Add stacked area for generation by source (Hydro at the base)
        for fonte in sorted(timeline_data.keys(), key=lambda x: 0 if x == 'Hidráulica' else 1):
            df = timeline_data[fonte]
            fig_gen_load.add_trace(go.Scatter(
                x=df['instante'],
                y=df['geracao'],
                name=fonte,
                stackgroup='geracao',
                line=dict(width=0),
                fillcolor=ENERGY_COLORS.get(fonte, '#FFFFFF')
            ))
        
        # Add load line over the stacked area
        fig_gen_load.add_trace(go.Scatter(
            x=carga_data['instante'],
            y=carga_data['carga'],
            name='Carga Total',
            line=dict(color=ENERGY_COLORS['Carga'], width=3, dash='solid'),
        ))
        
        fig_gen_load.update_layout(
            template='plotly_dark',
            paper_bgcolor=CARD_COLOR,
            plot_bgcolor=CARD_COLOR,
            margin=dict(t=20, b=40, l=30, r=20),
            height=400,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=10, color=TEXT_COLOR)
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor=GRID_COLOR,
                title="Hora",
                titlefont=dict(color=TEXT_COLOR, size=12),
                tickfont=dict(color=TEXT_COLOR, size=10)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=GRID_COLOR,
                title="MW",
                titlefont=dict(color=TEXT_COLOR, size=12),
                tickfont=dict(color=TEXT_COLOR, size=10)
            )
        )
        
        st.plotly_chart(fig_gen_load, use_container_width=True)
    
    # Reservoirs status
    st.markdown("<h3 class='section-header'>Reservatórios por Subsistema</h3>", unsafe_allow_html=True)
    
    if reservatorios:
        dados_reservatorios = process_reservatorio_data(reservatorios)
        
        # Create grid for reservoirs
        num_subsistemas = len(dados_reservatorios)
        res_cols = st.columns(min(num_subsistemas, 4))  # Maximum 4 columns
        
        for i, (subsistema, dados) in enumerate(dados_reservatorios.items()):
            col_idx = i % len(res_cols)
            with res_cols[col_idx]:
                valor_util = dados['valor_util_medio']
                ear_porcentagem = dados['ear_porcentagem']
                
                # Define color based on level
                if valor_util >= 70:
                    cor = '#34D399'  # Green
                elif valor_util >= 40:
                    cor = '#FBBF24'  # Yellow
                else:
                    cor = '#F87171'  # Red
                    
                st.markdown(f"""
                    <div class='reservoir-card'>
                        <div style='font-size: 14px; font-weight: bold; color: #f8fafc;'>{subsistema}</div>
                        <div style='display: flex; align-items: center; margin: 8px 0;'>
                            <div style='flex: 1; background: #334155; height: 12px; border-radius: 6px; overflow: hidden;'>
                                <div style='width: {valor_util}%; background: {cor}; height: 100%;'></div>
                            </div>
                            <div style='margin-left: 8px; font-size: 16px; font-weight: bold; color: {cor};'>{valor_util:.1f}%</div>
                        </div>
                        <div style='color: #94a3b8; font-size: 12px;'>EAR: {ear_porcentagem:.1f}%</div>
                    </div>
                """, unsafe_allow_html=True)
    
    # Renewable generation by region
    st.markdown("<h3 class='section-header'>Geração Renovável por Região</h3>", unsafe_allow_html=True)
    
    # Create visualization for renewable generation by region
    eolica_data = {k: v for k, v in dataframes.items() if 'Eólica' in k}
    solar_data = {k: v for k, v in dataframes.items() if 'Solar' in k}
    
    if eolica_data or solar_data:
        # Create figure with subplots
        fig_renovaveis = make_subplots(rows=2, cols=1, 
                          subplot_titles=("Geração Eólica por Região", "Geração Solar por Região"),
                          row_heights=[0.5, 0.5],
                          vertical_spacing=0.08)
        
        # Add wind power traces
        if eolica_data:
            for regiao, df in eolica_data.items():
                if df.empty:
                    continue
                regiao_nome = regiao.split(' - ')[1]
                fig_renovaveis.add_trace(
                    go.Scatter(
                        x=df['instante'], 
                        y=df['geracao'],
                        name=f"Eólica - {regiao_nome}",
                        line=dict(width=2),
                        opacity=1 if regiao_nome == 'Nordeste' else 0.7
                    ),
                    row=1, col=1
                )
        
        # Add solar power traces
        if solar_data:
            for regiao, df in solar_data.items():
                if df.empty:
                    continue
                regiao_nome = regiao.split(' - ')[1]
                fig_renovaveis.add_trace(
                    go.Scatter(
                        x=df['instante'], 
                        y=df['geracao'],
                        name=f"Solar - {regiao_nome}",
                        line=dict(width=2),
                        opacity=1 if regiao_nome == 'Nordeste' else 0.7
                    ),
                    row=2, col=1
                )
        
        # Update layout
        fig_renovaveis.update_layout(
            template='plotly_dark',
            paper_bgcolor=CARD_COLOR,
            plot_bgcolor=CARD_COLOR,
            margin=dict(t=40, b=20, l=30, r=20),
            height=400,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=10, color=TEXT_COLOR)
            )
        )
        
        fig_renovaveis.update_xaxes(showgrid=True, gridcolor=GRID_COLOR, tickfont=dict(color=TEXT_COLOR, size=10), row=1, col=1)
        fig_renovaveis.update_xaxes(showgrid=True, gridcolor=GRID_COLOR, title="Hora", titlefont=dict(color=TEXT_COLOR, size=12), 
                                    tickfont=dict(color=TEXT_COLOR, size=10), row=2, col=1)
        
        fig_renovaveis.update_yaxes(showgrid=True, gridcolor=GRID_COLOR, title="MW", titlefont=dict(color=TEXT_COLOR, size=12), 
                                    tickfont=dict(color=TEXT_COLOR, size=10), row=1, col=1)
        fig_renovaveis.update_yaxes(showgrid=True, gridcolor=GRID_COLOR, title="MW", titlefont=dict(color=TEXT_COLOR, size=12), 
                                    tickfont=dict(color=TEXT_COLOR, size=10), row=2, col=1)
        
        st.plotly_chart(fig_renovaveis, use_container_width=True)
    else:
        st.info("Dados de geração renovável não disponíveis")

# Compact footer with system information
current_time = datetime.now().strftime('%H:%M:%S')
current_date_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
st.markdown(f"""
    <div style='background: linear-gradient(90deg, #1e293b, #0f172a); padding: 12px; border-radius: 8px; margin-top: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);'>
        <p style='color: #94a3b8; margin: 0; font-size: 12px;'>
            ℹ️ Dados: ONS | Atualização: {current_date_time} | Atualização automática a cada 20 segundos
        </p>
    </div>
""", unsafe_allow_html=True)
