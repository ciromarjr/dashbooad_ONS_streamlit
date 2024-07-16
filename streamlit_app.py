import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.figure_factory as ff
from datetime import datetime
import time

# Função para obter dados e cachear por 20 segundos
@st.cache_data(ttl=20)
def get_data(url):
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data)
    
    # Ajustando o formato da data
    df['instante'] = pd.to_datetime(df['instante'])
    
    # Convertendo geração para MW (assumindo que os dados são originalmente em MWh)
    df['geracao'] = df['geracao'] / 60  # Convertendo de MWh para MW
    
    return df

st.set_page_config(layout="wide")

# URLs das fontes de dados
urls = {
    'Eólica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Eolica_json",
    'Solar': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Solar_json",
    'Hidráulica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Hidraulica_json",
    'Nuclear': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Nuclear_json",
    'Térmica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Termica_json"
}

# Função para carregar e preparar os dados
def load_data():
    dataframes = {key: get_data(url) for key, url in urls.items()}
    return dataframes

# Função para criar gráficos
def create_charts(dataframes):
    # Calcular o total de geração do SIN em GWh
    total_sin_gwh = sum(df['geracao'].iloc[-1] * 60 for df in dataframes.values()) / 1_000  # Convertendo de MWh para GWh

    # Preparar dados para o gráfico de rosca
    df_total_geracao = pd.DataFrame({
        'Fonte': list(dataframes.keys()),
        'Geração (MW)': [df['geracao'].iloc[-1] for df in dataframes.values()]
    })

    # Criar gráfico de rosca
    fig_rosca = go.Figure(data=[go.Pie(
        labels=[f'{row["Fonte"]}<br>{row["Geração (MW)"]:.2f} MW' for _, row in df_total_geracao.iterrows()], 
        values=df_total_geracao['Geração (MW)'], 
        hole=.6,
        hoverinfo='label+percent+value'
    )])

    # Adicionar anotação no centro do gráfico
    fig_rosca.add_annotation(
        dict(
            text=f'{total_sin_gwh:.2f} GWh',
            x=0.5,
            y=0.5,
            font_size=30,
            showarrow=False
        )
    )

    # Configurar layout do gráfico
    fig_rosca.update_layout(
        title_text='Cenário de Geração do SIN',
        annotations=[dict(text=f'{total_sin_gwh:.2f} GWh', x=0.5, y=0.5, font_size=30, showarrow=False)],
        height=700,
        width=700,
        legend=dict(
            font=dict(size=16),
            title="Fontes de Energia"
        ),
        margin=dict(t=50, b=50, l=50, r=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # Função para adicionar a linha total de geração
    def add_total_line(fig, dataframes, name):
        df_total = pd.DataFrame(index=dataframes[list(dataframes.keys())[0]]['instante'])
        df_total['total'] = sum(df.set_index('instante')['geracao'] for df in dataframes.values())
        fig.add_trace(go.Scatter(x=df_total.index, y=df_total['total'], mode='lines', line=dict(color='black', dash='dash'), name=name))

    # Geração do SIN em um único gráfico
    fig_sin = go.Figure()
    for fonte, df in dataframes.items():
        fig_sin.add_trace(go.Scatter(x=df['instante'], y=df['geracao'], mode='lines', name=fonte))

    add_total_line(fig_sin, dataframes, 'Total')

    fig_sin.update_layout(
        legend=dict(font=dict(size=16)),
        title='Geração do SIN',
        xaxis_title='Instante',
        yaxis_title='Geração (MW)',
        margin=dict(t=50, b=50, l=50, r=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # Geração por Região em um único gráfico
    df_region_dataframes = {
        'Eólica Norte': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Eolica_json"),
        'Solar Norte': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Solar_json"),
        'Eólica Nordeste': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Eolica_json"),
        'Solar Nordeste': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Solar_json"),
        'Eólica Sudeste/Centro-Oeste': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Eolica_json"),
        'Solar Sudeste/Centro-Oeste': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Solar_json"),
        'Eólica Sul': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Eolica_json"),
        'Solar Sul': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Solar_json")
    }

    fig_regiao = go.Figure()
    for fonte, df in df_region_dataframes.items():
        fig_regiao.add_trace(go.Scatter(x=df['instante'], y=df['geracao'], mode='lines', name=fonte))

    add_total_line(fig_regiao, df_region_dataframes, 'Total')

    fig_regiao.update_layout(
        legend=dict(font=dict(size=16)),
        title='Geração por Região',
        xaxis_title='Instante',
        yaxis_title='Geração (MW)',
        margin=dict(t=50, b=50, l=50, r=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig_rosca, fig_sin, fig_regiao

col1, col2 = st.columns(2)
rosca_placeholder = col1.empty()
sin_placeholder = col2.empty()
regiao_placeholder = col2.empty()
ultima_atualizacao_placeholder = col1.empty()
tabela_placeholder = st.empty()

# Loop para atualizar os gráficos a cada 60 segundos
while True:
    dataframes = load_data()
    fig_rosca, fig_sin, fig_regiao = create_charts(dataframes)

    rosca_placeholder.plotly_chart(fig_rosca, use_container_width=True)
    sin_placeholder.plotly_chart(fig_sin, use_container_width=True)
    regiao_placeholder.plotly_chart(fig_regiao, use_container_width=True)
    
    # Atualizar a última atualização
    ultima_atualizacao = datetime.now().strftime('%d-%m-%Y %H:%M')
    ultima_atualizacao_placeholder.write(f"Última atualização: {ultima_atualizacao}")
    
    # Criar a tabela
    df_table = pd.DataFrame({
        'Fonte': list(dataframes.keys()),
        'Geração (MW)': [f"{df['geracao'].iloc[-1]:,.1f}" for df in dataframes.values()]
    })
    
    fig_tabela = ff.create_table(df_table)
    fig_tabela.update_layout(
        height=400,
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)'
    )
    tabela_placeholder.plotly_chart(fig_tabela, use_container_width=True)

    time.sleep(60)
