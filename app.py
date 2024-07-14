import requests
import streamlit
import pandas as pd
import json



#Geração do SIN
Geracao_SIN_Eolica = requests.get("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Eolica_json")

Geracao_SIN_Solar = requests.get("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Solar_json")

Geracao_SIN_Hidraulica = requests.get("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Hidraulica_json")

Geracao_SIN_Nuclear = requests.get("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Nuclear_json")

Geracao_SIN_Termica = requests.get("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SIN_Termica_json")

#Geração por Região
geracao_eolica_norte = requests.get("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Eolica_json")
geracao_solar_norte = requests.get("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Solar_json")

Geracao_Nordeste_Eolica = requests.get("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Eolica_json")
Geracao_Nordeste_Solar = requests.get("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Solar_json")

Geracao_SudesteECentroOeste_Eolica = requests.get("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Eolica_jso")
Geracao_SudesteECentroOeste_Solar = requests.get("https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Solar_json")
Geracao_Sul_Eolica = requests.get("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Eolica_json")
Geracao_Sul_Solar = requests.get("https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Solar_json")


