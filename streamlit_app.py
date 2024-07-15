import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# Função para obter dados
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

def load_data():
    dataframes = {key: get_data(url) for key, url in urls.items()}
    
    # Encontrar a última atualização entre todos os DataFrames
    ultima_atualizacao = max(
        df['instante'].max() for df in dataframes.values()
    )

    return dataframes, ultima_atualizacao

def main():
    # Obter dados e última atualização
    dataframes, ultima_atualizacao = load_data()

    # Exibir a última atualização
    st.write(f"Última atualização: {ultima_atualizacao.strftime('%d-%m-%Y %H:%M')}")

    col1, col2 = st.columns(2)

    # Calcular o total de geração do SIN em GWh
    total_sin_gwh = sum(df['geracao'].iloc[-1] * 60 for df in dataframes.values()) / 1_000  # Convertendo de MWh para GWh

    # Preparar dados para o gráfico de rosca
    df_total_geracao = pd.DataFrame({
        'Fonte': list(urls.keys()),
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
            text=f'{total_sin_gwh:.2f} GW',
            x=0.5,
            y=0.5,
            font_size=500000,
            showarrow=False
        )
    )

    # Configurar layout do gráfico
    fig_rosca.update_layout(
        title_text='Cenário de Geração do SIN',
        annotations=[dict(text=f'{total_sin_gwh:.2f} GW', x=0.5, y=0.5, font_size=20, showarrow=False)],
        margin=dict(t=0, b=0, l=0, r=0),  # Remover margens para aproveitar melhor o espaço
        height=600,  # Aumentar a altura do gráfico
    )

    # Exibir o gráfico na aplicação Streamlit
    col1.plotly_chart(fig_rosca, use_container_width=True)

    # Geração do SIN em um único gráfico
    col2.subheader('Geração do SIN')
    fig_sin = go.Figure()
    for fonte, df in dataframes.items():
        fig_sin.add_trace(go.Scatter(x=df['instante'], y=df['geracao'], mode='lines', name=fonte))
    fig_sin.update_layout(
        title='Geração do SIN',
        xaxis_title='Instante',
        yaxis_title='Geração (MW)'
    )
    col2.plotly_chart(fig_sin, use_container_width=True)

    # Geração por Região em um único gráfico
    st.subheader('Geração por Região')
    fig_regiao = go.Figure()
    for fonte, df in dataframes.items():
        fig_regiao.add_trace(go.Scatter(x=df['instante'], y=df['geracao'], mode='lines', name=fonte))
    fig_regiao.update_layout(
        title='Geração por Região',
        xaxis_title='Instante',
        yaxis_title='Geração (MW)'
    )
    st.plotly_chart(fig_regiao, use_container_width=True)

# Auto-atualização a cada 60 minutos (3600 segundos)
st_autorefresh(interval=3600 * 1000, key="data_refresh")

if __name__ == "__main__":
    main()
