import pi
import streamlit as st
import pandas as pd
import plotly.express as px
import time


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
# Geração do SIN
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

while True:
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

    # Exibir a última atualização
    st.write(f"Última atualização: {ultima_atualizacao.strftime('%Y-%m-%d %H:%M:%S')}")

    # Geração do SIN em um único gráfico
    st.subheader('Geração do SIN')
    fig_sin = px.line(df_eolica, x='instante', y='geracao', color_discrete_sequence=['blue'], labels={'geracao': 'Geração (MW)'})
    fig_sin.add_scatter(x=df_eolica['instante'], y=df_eolica['geracao'], mode='lines', line=dict(color='blue'), name='Eólica')
    fig_sin.add_scatter(x=df_solar['instante'], y=df_solar['geracao'], mode='lines', line=dict(color='green'), name='Solar')
    fig_sin.add_scatter(x=df_hidraulica['instante'], y=df_hidraulica['geracao'], mode='lines', line=dict(color='orange'), name='Hidráulica')
    fig_sin.add_scatter(x=df_nuclear['instante'], y=df_nuclear['geracao'], mode='lines', line=dict(color='red'), name='Nuclear')
    fig_sin.add_scatter(x=df_termica['instante'], y=df_termica['geracao'], mode='lines', line=dict(color='purple'), name='Térmica')
    st.plotly_chart(fig_sin, use_container_width=True)

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

    # Atualiza a cada 60 segundos
    time.sleep(60)
    st.experimental_rerun()
