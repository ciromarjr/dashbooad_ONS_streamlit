import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time


# Função para obter dados e cachear por 60 segundos
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
url_eolica = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Eolica_json"
url_solar = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Solar_json"
url_hidraulica = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Hidraulica_json"
url_nuclear = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Nuclear_json"
url_termica = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Termica_json"
url_norte_eolica = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Eolica_json"
url_norte_solar = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Solar_json"
url_nordeste_eolica = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Eolica_json"
url_nordeste_solar = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Solar_json"
url_sudeste_e_centro_oeste_eolica = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Eolica_json"
url_sudeste_e_centro_oeste_solar = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Solar_json"
url_sul_eolica = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Eolica_json"
url_sul_solar = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Solar_json"

# Obtenção dos dados
df_eolica = get_data(url_eolica)
df_solar = get_data(url_solar)
df_hidraulica = get_data(url_hidraulica)
df_nuclear = get_data(url_nuclear)
df_termica = get_data(url_termica)
df_norte_eolica = get_data(url_norte_eolica)
df_norte_solar = get_data(url_norte_solar)
df_nordeste_eolica = get_data(url_nordeste_eolica)
df_nordeste_solar = get_data(url_nordeste_solar)
df_sudeste_e_centro_oeste_eolica = get_data(url_sudeste_e_centro_oeste_eolica)
df_sudeste_e_centro_oeste_solar = get_data(url_sudeste_e_centro_oeste_solar)
df_sul_eolica = get_data(url_sul_eolica)
df_sul_solar = get_data(url_sul_solar)

# Encontrar a última atualização entre todos os DataFrames
ultima_atualizacao = max(
    df_eolica['instante'].max(),
    df_solar['instante'].max(),
    df_hidraulica['instante'].max(),
    df_nuclear['instante'].max(),
    df_termica['instante'].max(),
    df_norte_eolica['instante'].max(),
    df_norte_solar['instante'].max(),
    df_nordeste_eolica['instante'].max(),
    df_nordeste_solar['instante'].max(),
    df_sudeste_e_centro_oeste_eolica['instante'].max(),
    df_sudeste_e_centro_oeste_solar['instante'].max(),
    df_sul_eolica['instante'].max(),
    df_sul_solar['instante'].max()
)

# URLs das fontes de dados
urls = {
    'Eólica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Eolica_json",
    'Solar': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Solar_json",
    'Hidráulica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Hidraulica_json",
    'Nuclear': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Nuclear_json",
    'Térmica': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Termica_json"
}


# Exibir a última atualização
st.write(f"Última atualização: {ultima_atualizacao.strftime('%d-%m-%Y %H:%M')}")

col1, col2 = st.columns(2)

# Obter dados de cada fonte
dataframes = {key: get_data(url) for key, url in urls.items()}

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
        text=f'{total_sin_gwh:.2f} GWh',
        x=0.5,
        y=0.5,
        font_size=20,
        showarrow=False
    )
)

# Configurar layout do gráfico
fig_rosca.update_layout(
    title_text='Cenário de Geração do SIN',
    annotations=[dict(text=f'{total_sin_gwh:.2f} GW', x=0.5, y=0.5, font_size=20, showarrow=False)]
)

# Exibir o gráfico na aplicação Streamlit
col1.plotly_chart(fig_rosca, use_container_width=True)

# Geração do SIN em um único gráfico
col2.subheader('Geração do SIN')
fig_sin = px.line(df_eolica, x='instante', y='geracao', color_discrete_sequence=['blue'], labels={'geracao': 'Geração (MW)'})
fig_sin.add_scatter(x=df_total_geracao['instante'], y=df_total_geracao['geracao'], mode='lines', line=dict(color='white'), name='Total')
fig_sin.add_scatter(x=df_eolica['instante'], y=df_eolica['geracao'], mode='lines', line=dict(color='blue'), name='Eólica')
fig_sin.add_scatter(x=df_solar['instante'], y=df_solar['geracao'], mode='lines', line=dict(color='green'), name='Solar')
fig_sin.add_scatter(x=df_hidraulica['instante'], y=df_hidraulica['geracao'], mode='lines', line=dict(color='orange'), name='Hidráulica')
fig_sin.add_scatter(x=df_nuclear['instante'], y=df_nuclear['geracao'], mode='lines', line=dict(color='red'), name='Nuclear')
fig_sin.add_scatter(x=df_termica['instante'], y=df_termica['geracao'], mode='lines', line=dict(color='purple'), name='Térmica')
col2.plotly_chart(fig_sin, use_container_width=True)

# Geração por Região em um único gráfico
st.subheader('Geração por Região')
fig_regiao = px.line(df_norte_eolica, x='instante', y='geracao', color_discrete_sequence=['blue'], labels={'geracao': 'Geração (MW)'})
fig_regiao.add_scatter(x=df_norte_eolica['instante'], y=df_norte_eolica['geracao'], mode='lines', line=dict(color='blue'), name='Eólica Norte')
fig_regiao.add_scatter(x=df_norte_solar['instante'], y=df_norte_solar['geracao'], mode='lines', line=dict(color='green'), name='Solar Norte')
fig_regiao.add_scatter(x=df_nordeste_eolica['instante'], y=df_nordeste_eolica['geracao'], mode='lines', line=dict(color='orange'), name='Eólica Nordeste')
fig_regiao.add_scatter(x=df_nordeste_solar['instante'], y=df_nordeste_solar['geracao'], mode='lines', line=dict(color='red'), name='Solar Nordeste')
fig_regiao.add_scatter(x=df_sudeste_e_centro_oeste_eolica['instante'], y=df_sudeste_e_centro_oeste_eolica['geracao'], mode='lines', line=dict(color='purple'), name='Eólica Sudeste/Centro-Oeste')
fig_regiao.add_scatter(x=df_sudeste_e_centro_oeste_solar['instante'], y=df_sudeste_e_centro_oeste_solar['geracao'], mode='lines', line=dict(color='brown'), name='Solar Sudeste/Centro-Oeste')
fig_regiao.add_scatter(x=df_sul_eolica['instante'], y=df_sul_eolica['geracao'], mode='lines', line=dict(color='pink'), name='Eólica Sul')
fig_regiao.add_scatter(x=df_sul_solar['instante'], y=df_sul_solar['geracao'], mode='lines', line=dict(color='gray'), name='Solar Sul')
st.plotly_chart(fig_regiao, use_container_width=True)

# Pausar por 60 segundos antes da próxima atualização
time.sleep(60)
st.experimental_rerun()
