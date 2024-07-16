import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.figure_factory as ff
from datetime import datetime
import time

# Definir a paleta de cores
colors = [
    "#F44336",  # Red
    "#E91E63",  # Pink
    "#9C27B0",  # Purple
    "#673AB7",  # Deep Purple
    "#3F51B5",  # Indigo
    "#2196F3",  # Blue
    "#03A9F4",  # Light Blue
    "#00BCD4",  # Cyan
    "#009688",  # Teal
    "#4CAF50",  # Green
    "#8BC34A",  # Light Green
    "#CDDC39",  # Lime
    "#FFEB3B",  # Yellow
    "#FFC107",  # Amber
    "#FF9800",  # Orange
    "#FF5722",  # Deep Orange
    "#795548",  # Brown
    "#9E9E9E",  # Grey
    "#607D8B"   # Blue Grey
]

# Função para obter dados e cachear por 20 segundos
@st.cache_data(ttl=20)
def get_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Verifica se houve algum erro na requisição

        # Verifica se a resposta não está vazia
        if response.content:
            data = response.json()
        else:
            st.error(f"Erro: Resposta vazia para a URL {url}")
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Ajustando o formato da data
        df['instante'] = pd.to_datetime(df['instante'])

        # Convertendo geração para MW (assumindo que os dados são originalmente em MWh)
        df['geracao'] = df['geracao'] / 60  # Convertendo de MWh para MW

        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Erro na requisição para a URL {url}: {e}")
        return pd.DataFrame()
    except ValueError as e:
        st.error(f"Erro ao decodificar JSON para a URL {url}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=20)
def get_balanco_energetico(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        if response.content:
            data = response.json()
        else:
            st.error(f"Erro: Resposta vazia para a URL {url}")
            return {}

        return data

    except requests.exceptions.RequestException as e:
        st.error(f"Erro na requisição para a URL {url}: {e}")
        return {}
    except ValueError as e:
        st.error(f"Erro ao decodificar JSON para a URL {url}: {e}")
        return {}

st.set_page_config(layout="wide")

# URLs das fontes de dados
urls = {
    'Eólica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Eolica_json",
    'Solar': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Solar_json",
    'Hidráulica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Hidraulica_json",
    'Nuclear': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Nuclear_json",
    'Térmica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Termica_json"
}

balanco_url = "https://integra.ons.org.br/api/energiaagora/GetBalancoEnergetico/null"

# Função para carregar e preparar os dados
def load_data():
    dataframes = {key: get_data(url) for key, url in urls.items()}
    balanco = get_balanco_energetico(balanco_url)
    return dataframes, balanco

# Função para criar gráficos
def create_charts(dataframes):
    # Calcular o total de geração do SIN em GWh
    total_sin_gwh = sum(df['geracao'].iloc[-1] * 60 for df in dataframes.values() if not df.empty) / 1_000  # Convertendo de MWh para GWh

    # Preparar dados para o gráfico de rosca
    df_total_geracao = pd.DataFrame({
        'Fonte': list(dataframes.keys()),
        'Geração (MW)': [df['geracao'].iloc[-1] for df in dataframes.values() if not df.empty]
    })

    # Criar gráfico de rosca
    fig_rosca = go.Figure(data=[go.Pie(
        labels=[f'{row["Fonte"]}<br>{row["Geração (MW)"]:.2f} MW' for _, row in df_total_geracao.iterrows()], 
        values=df_total_geracao['Geração (MW)'], 
        hole=.6,
        hoverinfo='label+percent+value',
        textfont_size=20,  # Tamanho do texto da porcentagem
        marker=dict(colors=colors[:len(df_total_geracao)])
    )])

    # Adicionar anotação no centro do gráfico
    fig_rosca.add_annotation(
        dict(
            text=f'{total_sin_gwh:.2f} GW',
            x=0.5,
            y=0.5,
            font_size=30,
            showarrow=False
        )
    )

    # Configurar layout do gráfico
    fig_rosca.update_layout(
        title_text='Cenário de Geração do SIN',
        annotations=[dict(text=f'{total_sin_gwh:.2f} GW', x=0.5, y=0.5, font_size=30, showarrow=False)],
        height=700,
        width=700,
        legend=dict(
            font=dict(size=15),
            title="Fontes de Energia"
        ),
        margin=dict(t=50, b=50, l=50, r=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # Função para adicionar a linha total de geração
    def add_total_line(fig, dataframes, name):
        df_total = pd.DataFrame(index=dataframes[list(dataframes.keys())[0]]['instante'])
        df_total['total'] = sum(df.set_index('instante')['geracao'] for df in dataframes.values() if not df.empty)
        fig.add_trace(go.Scatter(x=df_total.index, y=df_total['total'], mode='lines', line=dict(color='white', dash='dash'), name=name))

    # Geração do SIN em um único gráfico
    fig_sin = go.Figure()
    for i, (fonte, df) in enumerate(dataframes.items()):
        if not df.empty:
            fig_sin.add_trace(go.Scatter(x=df['instante'], y=df['geracao'], mode='lines', name=fonte, line=dict(color=colors[i % len(colors)])))

    add_total_line(fig_sin, dataframes, 'Total')

    fig_sin.update_layout(
        legend=dict(font=dict(size=15)),
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
        'Hidráulica Norte': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Hidraulica_json"),
        'Nuclear Norte': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Nuclear_json"),
        'Solar Norte': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Solar_json"),
        'Térmica Norte': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Termica_json"),
        'Eólica Nordeste': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Eolica_json"),
        'Hidráulica Nordeste': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Hidraulica_json"),
        'Nuclear Nordeste': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Nuclear_json"),
        'Solar Nordeste': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Solar_json"),
        'Térmica Nordeste': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Termica_json"),
        'Eólica Sudeste/Centro-Oeste': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Eolica_json"),
        'Hidráulica Sudeste/Centro-Oeste': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Hidraulica_json"),
        'Nuclear Sudeste/Centro-Oeste': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Nuclear_json"),
        'Solar Sudeste/Centro-Oeste': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Solar_json"),
        'Térmica Sudeste/Centro-Oeste': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Termica_json"),
        'Eólica Sul': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Eolica_json"),
        'Hidráulica Sul': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Hidraulica_json"),
        'Nuclear Sul': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Nuclear_json"),
        'Solar Sul': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Solar_json"),
        'Térmica Sul': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Termica_json")
    }

    fig_regiao = go.Figure()
    for i, (fonte, df) in enumerate(df_region_dataframes.items()):
        if not df.empty:
            fig_regiao.add_trace(go.Scatter(x=df['instante'], y=df['geracao'], mode='lines', name=fonte, line=dict(color=colors[i % len(colors)])))

    add_total_line(fig_regiao, df_region_dataframes, 'Total')

    fig_regiao.update_layout(
        legend=dict(font=dict(size=15)),
        title='Geração por Região',
        xaxis_title='Instante',
        yaxis_title='Geração (MW)',
        margin=dict(t=50, b=50, l=50, r=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig_rosca, fig_sin, fig_regiao

col1, col2 = st.columns(2)
ultima_atualizacao_placeholder = col1.empty()
rosca_placeholder = col1.empty()
sin_placeholder = col2.empty()
regiao_placeholder = col2.empty()

tabela_placeholder = st.empty()

# Loop para atualizar os gráficos a cada 60 segundos
while True:
    dataframes, balanco = load_data()
    fig_rosca, fig_sin, fig_regiao = create_charts(dataframes)

    rosca_placeholder.plotly_chart(fig_rosca, use_container_width=True)
    sin_placeholder.plotly_chart(fig_sin, use_container_width=True)
    regiao_placeholder.plotly_chart(fig_regiao, use_container_width=True)
    
    # Atualizar a última atualização
    ultima_atualizacao = datetime.now().strftime('%d-%m-%Y %H:%M')
    ultima_atualizacao_placeholder.write(f"Última atualização: {ultima_atualizacao}")
    
    # Criar a tabela
    if balanco:
        df_table = pd.DataFrame({
            'Região': ['Sudeste/Centro-Oeste', 'Sul', 'Nordeste', 'Norte'],
            'Geração Total (MW)': [
                round(balanco['sudesteECentroOeste']['geracao']['total'] / 1000, 2),  # Ajustar para MW e formatar
                round(balanco['sul']['geracao']['total'] / 1000, 2),                  # Ajustar para MW e formatar
                round(balanco['nordeste']['geracao']['total'] / 1000, 2),             # Ajustar para MW e formatar
                round(balanco['norte']['geracao']['total'] / 1000, 2)                 # Ajustar para MW e formatar
            ],
            'Carga Verificada (MW)': [
                round(balanco['sudesteECentroOeste']['cargaVerificada'] / 1000, 2),
                round(balanco['sul']['cargaVerificada'] / 1000, 2),
                round(balanco['nordeste']['cargaVerificada'] / 1000, 2),
                round(balanco['norte']['cargaVerificada'] / 1000, 2)
            ],
            'Importação (MW)': [
                round(balanco['sudesteECentroOeste']['importacao']/ 1000, 2),
                round(balanco['sul']['importacao'] / 1000, 2),
                round(balanco['nordeste']['importacao'] / 1000, 2),
                round(balanco['norte']['importacao'] / 1000, 2)
            ],
            'Exportação (MW)': [
                round(balanco['sudesteECentroOeste']['exportacao'] / 1000, 2),
                round(balanco['sul']['exportacao'] / 1000, 2),
                round(balanco['nordeste']['exportacao'] / 1000, 2),
                round(balanco['norte']['exportacao'] / 1000, 2)
            ]
        })
        
        fig_tabela = ff.create_table(df_table)
        fig_tabela.update_layout(
            height=400,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=20)  # Aumentar o tamanho do texto da tabela
        )
        tabela_placeholder.plotly_chart(fig_tabela, use_container_width=True)

    time.sleep(60)
