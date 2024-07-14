import requests
import streamlit as st
import pandas as pd
import plotly.express as px


def get_data(url):
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data)
    
    # Ajustando o formato da data
    df['instante'] = pd.to_datetime(df['instante'])
    
    # Convertendo geração para MW (assumindo que os dados são originalmente em MWh)
    df['geracao'] = df['geracao'] / 60  # Convertendo de MWh para MW
    
    return df
    
# Geração do SIN
url_eolica = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Eolica_json"
df_eolica = get_data(url_eolica)

url_solar = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Solar_json"
df_solar = get_data(url_solar)

url_hidraulica = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Hidraulica_json"
df_hidraulica = get_data(url_hidraulica)

url_nuclear = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Nuclear_json"
df_nuclear = get_data(url_nuclear)

url_termica = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Termica_json"
df_termica = get_data(url_termica)

# Geração por Região
url_norte_eolica = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Eolica_json"
df_norte_eolica = get_data(url_norte_eolica)

url_norte_solar = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Solar_json"
df_norte_solar = get_data(url_norte_solar)

url_nordeste_eolica = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Eolica_json"
df_nordeste_eolica = get_data(url_nordeste_eolica)

url_nordeste_solar = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Solar_json"
df_nordeste_solar = get_data(url_nordeste_solar)

url_sudeste_e_centro_oeste_eolica = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Eolica_json"
df_sudeste_e_centro_oeste_eolica = get_data(url_sudeste_e_centro_oeste_eolica)

url_sudeste_e_centro_oeste_solar = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Solar_json"
df_sudeste_e_centro_oeste_solar = get_data(url_sudeste_e_centro_oeste_solar)

url_sul_eolica = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Eolica_json"
df_sul_eolica = get_data(url_sul_eolica)

url_sul_solar = "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Solar_json"
df_sul_solar = get_data(url_sul_solar)


col1, col2 = st.columns(2)
col3, col4, col5 = st.colmns(3)


# Geração do SIN em um único gráfico
st.subheader('Geração do SIN')
st.line_chart(df_eolica.set_index('instante'))
st.line_chart(df_solar.set_index('instante'))
st.line_chart(df_hidraulica.set_index('instante'))
st.line_chart(df_nuclear.set_index('instante'))
st.line_chart(df_termica.set_index('instante'))

# Geração por Região em um único gráfico
st.subheader('Geração por Região')
st.line_chart(df_norte_eolica.set_index('instante'))
st.line_chart(df_norte_solar.set_index('instante'))
st.line_chart(df_nordeste_eolica.set_index('instante'))
st.line_chart(df_nordeste_solar.set_index('instante'))
st.line_chart(df_sudeste_e_centro_oeste_eolica.set_index('instante'))
st.line_chart(df_sudeste_e_centro_oeste_solar.set_index('instante'))
st.line_chart(df_sul_eolica.set_index('instante'))
st.line_chart(df_sul_solar.set_index('instante'))
