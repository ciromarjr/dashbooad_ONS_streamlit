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
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Verifica se a resposta não está vazia
            if response.content and response.content.strip():
                try:
                    data = response.json()
                    if isinstance(data, list) and data:  # Verifica se os dados são uma lista não vazia
                        df = pd.DataFrame(data)
                        if not df.empty:
                            # Ajustando o formato da data
                            df['instante'] = pd.to_datetime(df['instante'], errors='coerce')
                            # Remover linhas com datas inválidas
                            df = df.dropna(subset=['instante'])
                            # Convertendo geração para MW (assumindo que os dados são originalmente em MWh)
                            df['geracao'] = df['geracao'] / 60  # Convertendo de MWh para MW
                            return df
                except ValueError:
                    print(f"Erro ao decodificar JSON de {url}")
    except Exception as e:
        print(f"Erro ao carregar dados de {url}: {e}")
    
    return None  # Se a requisição falhar ou os dados forem inválidos

@st.cache_data(ttl=20)
def get_balanco_energetico(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Erro ao carregar balanço energético: {e}")
    return None

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

# Definir a cor da fonte
font_color = 'white'  # Ou qualquer cor desejada

# Função para carregar e preparar os dados
def load_data():
    dataframes = {key: get_data(url) for key, url in urls.items()}
    # Remover entradas onde os dados são None
    dataframes = {key: df for key, df in dataframes.items() if df is not None}
    balanco = get_balanco_energetico(balanco_url)
    return dataframes, balanco

# Função para criar gráficos
def create_charts(dataframes):
    # Calcular o total de geração do SIN em GWh
    total_sin_gwh = sum(df['geracao'].iloc[-1] * 60 for df in dataframes.values()) / 1_000  # Convertendo de MWh para GWh

    # Preparar dados para o gráfico de rosca
    df_total_geracao = pd.DataFrame({
        'Fonte': list(dataframes.keys()),
        'Geração (MW)': [df['geracao'].iloc[-1] for df in dataframes.values()]
    })

    # Definindo cores personalizadas
    colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A']

    # Criar gráfico de rosca
    fig_rosca = go.Figure(data=[go.Pie(
        labels=[f'{row["Fonte"]}<br>{row["Geração (MW)"]:.2f} MW' for _, row in df_total_geracao.iterrows()], 
        values=df_total_geracao['Geração (MW)'], 
        hole=.6,
        hoverinfo='label+percent+value',
        textfont_size=50,  # Aumentar o tamanho do texto da porcentagem
        marker=dict(colors=colors)
    )])

    # Adicionar anotação no centro do gráfico
    fig_rosca.add_annotation(
        dict(
            text=f'{total_sin_gwh:.2f} GW',
            x=0.5,
            y=0.5,
            font_size=300,
            showarrow=False,
            font_color=font_color  # Aplicar a cor da fonte aqui
        )
    )

    # Configurar layout do gráfico
    fig_rosca.update_layout(
        title_text='Cenário de Geração do SIN',
        annotations=[dict(text=f'{total_sin_gwh:.2f} GW', x=0.5, y=0.5, font_size=80, showarrow=False, font_color=font_color)],
        height=700,
        width=700,
        legend=dict(
            font=dict(size=30, color=font_color),
            title="Fontes de Energia"
        ),
        margin=dict(t=50, b=50, l=50, r=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=font_color)  # Aplicar a cor da fonte no layout
    )

    # Função para adicionar a linha total de geração
    def add_total_line(fig, dataframes, name):
        df_total = pd.DataFrame(index=dataframes[list(dataframes.keys())[0]]['instante'])
        df_total['total'] = sum(df.set_index('instante')['geracao'] for df in dataframes.values())
        fig.add_trace(go.Scatter(x=df_total.index, y=df_total['total'], mode='lines', line=dict(color=font_color, dash='dash'), name=name))

    # Geração do SIN em um único gráfico
    fig_sin = go.Figure()
    for fonte, df in dataframes.items():
        fig_sin.add_trace(go.Scatter(x=df['instante'], y=df['geracao'], mode='lines', name=fonte))

    add_total_line(fig_sin, dataframes, 'Total')

    fig_sin.update_layout(
        legend=dict(font=dict(size=20, color=font_color)),
        title='Geração do SIN',
        xaxis_title='Instante',
        yaxis_title='Geração (MW)',
        margin=dict(t=50, b=50, l=50, r=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=font_color)  # Aplicar a cor da fonte no layout
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
        'Solar Sul': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Solar_json"),
        'Norte Hidráulica': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Hidraulica_json"),
        'Norte Nuclear': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Nuclear_json"),
        'Norte Térmica': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Termica_json"),
        'Nordeste Hidráulica': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Hidraulica_json"),
        'Nordeste Nuclear': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Nuclear_json"),
        'Nordeste Térmica': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Termica_json"),
        'Sudeste/Centro-Oeste Hidráulica': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Hidraulica_json"),
        'Sudeste/Centro-Oeste Nuclear': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Nuclear_json"),
        'Sudeste/Centro-Oeste Térmica': get_data("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Termica_json")
    }

    # Remover entradas com dados inválidos (None)
    df_region_dataframes = {key: df for key, df in df_region_dataframes.items() if df is not None}

    fig_regiao = go.Figure()
    for fonte, df in df_region_dataframes.items():
        fig_regiao.add_trace(go.Scatter(x=df['instante'], y=df['geracao'], mode='lines', name=fonte))

    add_total_line(fig_regiao, df_region_dataframes, 'Total')

    fig_regiao.update_layout(
        legend=dict(font=dict(size=19, color=font_color)),
        title='Geração por Região',
        xaxis_title='Instante',
        yaxis_title='Geração (MW)',
        margin=dict(t=50, b=50, l=50, r=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=font_color)  # Aplicar a cor da fonte no layout
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
    
    # Pegar a última data dos dados para exibir como horário de atualização
    if dataframes:
        ultima_data = max(df['instante'].max() for df in dataframes.values()).strftime('%d-%m-%Y %H:%M')
        ultima_atualizacao_placeholder.write(f"Última atualização dos dados: {ultima_data}")
    
    # Criar a tabela se o balanco estiver disponível
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
            font=dict(size=55, color=font_color)  # Aumentar o tamanho e aplicar a cor do texto da tabela
        )
        tabela_placeholder.plotly_chart(fig_tabela, use_container_width=True)

    time.sleep(10)
