import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

# Função para obter dados e cachear por 20 segundos
@st.cache_data(ttl=20)
def get_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            if response.content and response.content.strip():
                try:
                    data = response.json()
                    if isinstance(data, list) and data:
                        df = pd.DataFrame(data)
                        if not df.empty:
                            df['instante'] = pd.to_datetime(df['instante'], errors='coerce')
                            df = df.dropna(subset=['instante'])
                            df['geracao'] = df['geracao'] / 60  # Convertendo de MWh para MW
                            return df
                except ValueError:
                    print(f"Erro ao decodificar JSON de {url}")
    except Exception as e:
        print(f"Erro ao carregar dados de {url}: {e}")
    return None

@st.cache_data(ttl=20)
def get_balanco_energetico():
    url = "https://integra.ons.org.br/api/energiaagora/GetBalancoEnergetico/null"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Erro ao carregar balanço energético: {e}")
    return None

@st.cache_data(ttl=20)
def get_balanco_energetico_consolidado():
    url = "https://integra.ons.org.br/api/energiaagora/GetBalancoEnergeticoConsolidado/null"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Erro ao carregar balanço energético consolidado: {e}")
    return None

@st.cache_data(ttl=20)
def get_situacao_reservatorios():
    url = "https://integra.ons.org.br/api/energiaagora/Get/SituacaoDosReservatorios"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Erro ao carregar a situação dos reservatórios: {e}")
    return None

# Configuração da página
st.set_page_config(page_title="Geração Elétrica e Reservatórios", page_icon="⚡", layout="wide")

st.markdown("<h1 style='text-align: center;'>Dashboard de Carga e Geração do SIN</h1>", unsafe_allow_html=True)

# Função para carregar e preparar os dados
def load_data():
    urls = {
        'Eólica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Eolica_json",
        'Solar': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Solar_json",
        'Hidráulica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Hidraulica_json",
        'Nuclear': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Nuclear_json",
        'Térmica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Termica_json"
    }
    
    dataframes = {key: get_data(url) for key, url in urls.items()}
    dataframes = {key: df for key, df in dataframes.items() if df is not None}
    balanco = get_balanco_energetico()
    balanco_consolidado = get_balanco_energetico_consolidado()
    reservatorios = get_situacao_reservatorios()
    return dataframes, balanco, balanco_consolidado, reservatorios

# Função para criar gráficos
def create_charts(dataframes):
    total_sin_gwh = sum(df['geracao'].iloc[-1] * 60 for df in dataframes.values()) / 1_000

    df_total_geracao = pd.DataFrame({
        'Fonte': list(dataframes.keys()),
        'Geração (MW)': [df['geracao'].iloc[-1] for df in dataframes.values()]
    })

    colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A']

    fig_rosca = go.Figure(data=[go.Pie(
        labels=[f'{row["Fonte"]}<br>{row["Geração (MW)"]:.2f} MW' for _, row in df_total_geracao.iterrows()], 
        values=df_total_geracao['Geração (MW)'], 
        hole=.6,
        hoverinfo='label+percent+value',
        textfont_size=18,
        marker=dict(colors=colors)
    )])

    fig_rosca.add_annotation(
        dict(
            text=f'{total_sin_gwh:.2f} GW',
            x=0.5,
            y=0.5,
            font_size=40,
            showarrow=False
        )
    )

    fig_rosca.update_layout(
        title_text='Distribuição de Geração por Fonte',
        annotations=[dict(text=f'{total_sin_gwh:.2f} GW', x=0.5, y=0.5, font_size=30, showarrow=False)],
        height=400,
        margin=dict(t=50, b=50, l=50, r=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    fig_sin = go.Figure()

    for fonte, df in dataframes.items():
        fig_sin.add_trace(go.Scatter(x=df['instante'], y=df['geracao'], mode='lines', name=fonte))

    df_total = pd.DataFrame(index=dataframes['Eólica']['instante'])
    df_total['Total'] = sum(df['geracao'] for df in dataframes.values())

    fig_sin.add_trace(go.Scatter(
        x=df_total.index, 
        y=df_total['Total'], 
        mode='lines', 
        name='Total', 
        line=dict(color='black', dash='dash')
    ))

    fig_sin.update_layout(
        legend=dict(font=dict(size=14)),
        title='Evolução Temporal da Geração por Fonte',
        xaxis_title='Instante',
        yaxis_title='Geração (MW)',
        height=400,
        margin=dict(t=50, b=50, l=50, r=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    fig_barras = px.bar(
        df_total_geracao,
        x='Fonte',
        y='Geração (MW)',
        text='Geração (MW)',
        title="Comparação de Geração por Fonte",
        color='Fonte',
        height=400,
        color_discrete_sequence=colors
    )
    fig_barras.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_barras.update_layout(
        margin=dict(t=50, b=50, l=50, r=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig_rosca, fig_sin, fig_barras

# Função para atualizar os cards com o balanço energético
def create_balanco_cards(balanco):
    if balanco:
        st.markdown(f"**Última atualização dos dados**: {balanco['Data']}")
        col1, col2, col3, col4 = st.columns(4)

        # Sudeste/Centro-Oeste
        with col1:
            st.metric("Sudeste/Centro-Oeste - Geração Total", f"{round(balanco['sudesteECentroOeste']['geracao']['total'], 2)} MW")
            st.metric("Carga Verificada", f"{round(balanco['sudesteECentroOeste']['cargaVerificada'], 2)} MW")
            st.metric("Importação", f"{round(balanco['sudesteECentroOeste']['importacao'], 2)} MW")
            st.metric("Exportação", f"{round(balanco['sudesteECentroOeste']['exportacao'], 2)} MW")

        # Sul
        with col2:
            st.metric("Sul - Geração Total", f"{round(balanco['sul']['geracao']['total'], 2)} MW")
            st.metric("Carga Verificada", f"{round(balanco['sul']['cargaVerificada'], 2)} MW")
            st.metric("Importação", f"{round(balanco['sul']['importacao'], 2)} MW")
            st.metric("Exportação", f"{round(balanco['sul']['exportacao'], 2)} MW")

        # Nordeste
        with col3:
            st.metric("Nordeste - Geração Total", f"{round(balanco['nordeste']['geracao']['total'], 2)} MW")
            st.metric("Carga Verificada", f"{round(balanco['nordeste']['cargaVerificada'], 2)} MW")
            st.metric("Importação", f"{round(balanco['nordeste']['importacao'], 2)} MW")
            st.metric("Exportação", f"{round(balanco['nordeste']['exportacao'], 2)} MW")

        # Norte
        with col4:
            st.metric("Norte - Geração Total", f"{round(balanco['norte']['geracao']['total'], 2)} MW")
            st.metric("Carga Verificada", f"{round(balanco['norte']['cargaVerificada'], 2)} MW")
            st.metric("Importação", f"{round(balanco['norte']['importacao'], 2)} MW")
            st.metric("Exportação", f"{round(balanco['norte']['exportacao'], 2)} MW")

# Função para exibir gráficos da situação dos reservatórios
def create_reservatorios_charts(reservatorios):
    if reservatorios:
        df_reservatorios = pd.DataFrame(reservatorios)

        fig_reserv_percent = px.bar(
            df_reservatorios, 
            x="Reservatorio", 
            y="ReservatorioPorcentagem", 
            color="Subsistema", 
            title="Percentual de Ocupação dos Reservatórios",
            text="ReservatorioPorcentagem"
        )
        fig_reserv_percent.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig_reserv_percent.update_layout(
            xaxis_title="Reservatório",
            yaxis_title="Porcentagem (%)",
            height=400
        )

        fig_reserv_ear = px.bar(
            df_reservatorios, 
            x="Reservatorio", 
            y="ReservatorioEARVerificadaMWMes", 
            color="Subsistema", 
            title="EAR Verificada dos Reservatórios em MWmês",
            text="ReservatorioEARVerificadaMWMes"
        )
        fig_reserv_ear.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_reserv_ear.update_layout(
            xaxis_title="Reservatório",
            yaxis_title="MWmês",
            height=400
        )

        return fig_reserv_percent, fig_reserv_ear

# Layout principal
st.markdown("### Métricas Principais de Geração de Energia")
dataframes, balanco, balanco_consolidado, reservatorios = load_data()
create_balanco_cards(balanco)

st.markdown("### Distribuição e Evolução da Geração de Energia")
col1, col2 = st.columns(2)

# Gráfico de Rosca e Gráfico de Linhas
fig_rosca, fig_sin, fig_barras = create_charts(dataframes)
fig_reserv_percent, fig_reserv_ear = create_reservatorios_charts(reservatorios)

with col1:
    st.plotly_chart(fig_rosca, use_container_width=True)
    st.plotly_chart(fig_barras, use_container_width=True)

with col2:
    st.plotly_chart(fig_sin, use_container_width=True)
    st.plotly_chart(fig_reserv_percent, use_container_width=True)
    st.plotly_chart(fig_reserv_ear, use_container_width=True)

# Atualização automática a cada 10 minutos (600 segundos)
time.sleep(600)
st.experimental_rerun()
