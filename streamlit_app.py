import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Sistema Elétrico Brasileiro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cores e estilos
BACKGROUND_COLOR = "#111827"
CARD_COLOR = "#1F2937"
TEXT_COLOR = "#F9FAFB"
GRID_COLOR = "#374151"

# API Configuration para obter previsão de geração
AUTH_URL = "https://integra.ons.org.br/api/autenticar"
PREV_GERACAO_URL = "https://integra.ons.org.br/api/programacao/repdoe/CargaMedioDiario?Ano=2024&Mes=11&Dia=15"
AUTH_PAYLOAD = {
    "usuario": "",
    "senha": ""
}
def chunk_list(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]
def get_usina_generation_forecast(token, date, usinas):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    all_data = []
    
    payload = {
            "Ano": date.year,
            "Mes": date.month,
            "Dia": date.day,
            
        }
    response = requests.post(PREV_GERACAO_URL, json=payload, headers=headers)
    if response.status_code == 200:
            all_data.extend(response.json().get("Usinas", []))
    else:
            print(f"Error in request: {response.status_code}")
            return None
            
    return all_data


# Funções de obtenção de dados Carga
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
                        df['carga'] = df['carga'] # / 60  Convertendo de MWh para MW
                        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
    return None

# Funções de obtenção de dados Geração
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
                        df['geracao'] = df['geracao'] # / 60  Convertendo de MWh para MW
                        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
    return None

@st.cache_data(ttl=20)
def get_carga_subsistema():
    url = "https://integra.ons.org.br/api/energiaagora/Get/Carga_SIN_json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Erro ao carregar Carga subsistema: {e}")
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
        return None, None, None, None
    
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

# Carregando dados
dataframes, balanco, reservatorios = load_data()
fonte_totals, timeline_data = process_data(dataframes)
# Estilo personalizado para o tema dark
st.markdown("""
    <style>
    .main {
        background-color: #111827;
    }
    .stApp {
        background-color: #111827;
    }
    .stMetric {
        background-color: #1F2937;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        color: #F9FAFB !important;
    }
    .css-1r6slb0 {
        background-color: #1F2937;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    h1, h2, h3, h4, h5, h6, .metric-label {
        color: #F9FAFB !important;
    }
    .metric-value {
        color: #F9FAFB !important;
    }
    div[data-testid="stMetricValue"] {
        color: #F9FAFB !important;
    }
    div[data-testid="stMetricLabel"] > label {
        color: #9CA3AF !important;
    }
    .stMetric:hover {
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }
    .plot-container {
        background-color: #1F2937;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .status-card {
        background-color: #1F2937;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .status-card:hover {
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }
    </style>
""", unsafe_allow_html=True)

# Header do Dashboard
st.markdown("""
    <div style='background-color: #1F2937; padding: 20px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);'>
        <h1 style='color: #F9FAFB; margin: 0;'>📊 Sistema Elétrico Brasileiro</h1>
        <p style='color: #9CA3AF; margin: 10px 0 0 0;'>Dados em Tempo Real do ONS</p>
    </div>
""", unsafe_allow_html=True)

# Métricas principais
if fonte_totals:
    total_geracao = sum(fonte_totals.values())
    renovaveis = (fonte_totals.get('Hidráulica', 0) + fonte_totals.get('Eólica', 0) + 
                  fonte_totals.get('Solar', 0))
    percentual_renovavel = (renovaveis / total_geracao * 100) if total_geracao > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Geração Total",
            f"{total_geracao:,.0f} MW",
            "Tempo Real"
        )
        
    with col2:
        st.metric(
            "Energia Renovável",
            f"{percentual_renovavel:.1f}%",
            f"{'+' if percentual_renovavel > 70 else ''}{percentual_renovavel-70:.1f}% vs meta"
        )
        
    with col3:
        if reservatorios:
            nivel_medio = sum(r.get('valor', 0) for r in reservatorios) / len(reservatorios)
            st.metric(
                "Nível Reservatórios",
                f"{nivel_medio:.1f}%",
                f"{'+' if nivel_medio > 50 else ''}{nivel_medio-50:.1f}% vs média"
            )
            
    with col4:
        max_geracao = max(fonte_totals.values())
        st.metric(
            "Pico de Geração",
            f"{max_geracao:,.0f} MW",
            "Última hora"
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
