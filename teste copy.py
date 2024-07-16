import streamlit as st
import matplotlib.pyplot as plt

# Configuração da página
st.set_page_config(layout="wide")

# Estilos CSS para o tema escuro
st.markdown("""
<style>
    body {
        background-color: #121212;
    }
    .stMarkdown h1, h2, h3, h4, p {
        color: #EAEAEA;
    }
    .stMarkdown div {
        color: #EAEAEA;
    }
    .stMetric {
        color: #EAEAEA;
    }
    .css-1d391kg {
        color: #EAEAEA;
    }
    .css-1d391kg div {
        color: #EAEAEA;
    }
    .css-1q8dd3e {
        background-color: #1E1E1E;
    }
    .css-1q8dd3e div {
        color: #EAEAEA;
    }
    .css-1q8dd3e h3 {
        color: #EAEAEA;
    }
    .css-1q8dd3e p {
        color: #EAEAEA;
    }
    .css-1q8dd3e h4 {
        color: #EAEAEA;
    }
</style>
""", unsafe_allow_html=True)

# Título
st.markdown("<h1 style='text-align: center; color: white;'>Geração total</h1>", unsafe_allow_html=True)

# Dados de geração
total_generation = 66504.8
datetime = "16/07 01:05"

# Exibição do total e data/hora
st.markdown(f"<h2 style='text-align: right; color: white;'>{total_generation} MW</h2>", unsafe_allow_html=True)
st.markdown(f"<h4 style='text-align: right; color: white;'>{datetime}</h4>", unsafe_allow_html=True)

# Dados detalhados de geração
generation_data = {
    "Eólica": 17057.4,
    "Hidraulica": 39272.7,
    "Térmica": 8161.8,
    "Nuclear": 2005.1,
    "Solar": 7.8,
    "Importação": 0.0
}

# Cálculo das porcentagens
total = sum(generation_data.values())
wind_percentage = (generation_data["Eólica"] / total) * 100

# Disposição dos dados em colunas
col1, col2, col3 = st.columns(3)

# Adicionando o gráfico de pizza na primeira coluna
with col1:
    # Gráfico de pizza para mostrar a porcentagem de Eólica
    fig, ax = plt.subplots(figsize=(4, 4))  # Diminuir o tamanho do gráfico
    fig.patch.set_facecolor('#121212')  # Definir fundo do gráfico
    ax.set_facecolor('#121212')  # Definir fundo do gráfico
    ax.pie([wind_percentage, 100 - wind_percentage], labels=["Eólica", ""], startangle=90, colors=["#FF5733", "#333333"], autopct='%1.1f%%', pctdistance=0.85, textprops={'color':"white"})
    centre_circle = plt.Circle((0, 0), 0.70, fc='#121212')  # Fundo escuro para o círculo central
    fig.gca().add_artist(centre_circle)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.text(0, 0, f"{wind_percentage:.1f}%", horizontalalignment='center', verticalalignment='center', fontsize=12, weight='bold', color='white')
    st.pyplot(fig)

with col2:
    st.markdown(f"<div style='background-color: #1e1e1e; padding: 10px; border-radius: 5px; text-align: center;'><h3 style='color: #FF5733;'>Ger. Eólica</h3><p style='color: white;'>{generation_data['Eólica']} MW</p></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='background-color: #1e1e1e; padding: 10px; border-radius: 5px; text-align: center;'><h3 style='color: white;'>Ger. Térmica</h3><p style='color: white;'>{generation_data['Térmica']} MW</p></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='background-color: #1e1e1e; padding: 10px; border-radius: 5px; text-align: center;'><h3 style='color: white;'>Ger. Solar</h3><p style='color: white;'>{generation_data['Solar']} MW</p></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div style='background-color: #1e1e1e; padding: 10px; border-radius: 5px; text-align: center;'><h3 style='color: white;'>Ger. Hidraulica</h3><p style='color: white;'>{generation_data['Hidraulica']} MW</p></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='background-color: #1e1e1e; padding: 10px; border-radius: 5px; text-align: center;'><h3 style='color: white;'>Ger. Nuclear</h3><p style='color: white;'>{generation_data['Nuclear']} MW</p></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='background-color: #1e1e1e; padding: 10px; border-radius: 5px; text-align: center;'><h3 style='color: white;'>Importação</h3><p style='color: white;'>{generation_data['Importação']} MW</p></div>", unsafe_allow_html=True)

