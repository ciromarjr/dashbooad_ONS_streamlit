import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import numpy as np
import time

# Configuração da página
st.set_page_config(
    page_title="Sistema Elétrico Brasileiro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cores originais mantidas
BACKGROUND_COLOR = "#0f172a"  # Slate 900
CARD_COLOR = "#1e293b"        # Slate 800
TEXT_COLOR = "#f8fafc"        # Slate 50
GRID_COLOR = "#334155"        # Slate 700
ACCENT_COLOR = "#3b82f6"      # Blue 500

# Cores para fontes de energia
ENERGY_COLORS = {
    'Hidráulica': '#60A5FA',    # Blue 400
    'Eólica': '#34D399',        # Emerald 400
    'Solar': '#FBBF24',         # Amber 400
    'Térmica': '#F87171',       # Red 400
    'Nuclear': '#A78BFA',       # Purple 400
    'Carga': '#EC4899'          # Pink 400
}

# Funções de obtenção de dados melhoradas
@st.cache_data(ttl=20)
def get_data(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and response.content and response.content.strip():
            data = response.json()
            if isinstance(data, list) and data:
                df = pd.DataFrame(data)
                if not df.empty:
                    df['instante'] = pd.to_datetime(df['instante'], errors='coerce')
                    df = df.dropna(subset=['instante'])
                    return df
        return pd.DataFrame(columns=['instante', 'geracao'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(columns=['instante', 'geracao'])

@st.cache_data(ttl=20)
def get_carga_data():
    url = "https://integra.ons.org.br/api/energiaagora/Get/Carga_SIN_json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df['instante'] = pd.to_datetime(df['instante'])
            return df
        return pd.DataFrame(columns=['instante', 'carga'])
    except Exception as e:
        st.error(f"Erro ao carregar dados de carga: {e}")
        return pd.DataFrame(columns=['instante', 'carga'])

@st.cache_data(ttl=20)
def get_regional_carga_data(region):
    url = f"https://integra.ons.org.br/api/energiaagora/Get/Carga_{region}_json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df['instante'] = pd.to_datetime(df['instante'])
            return df
        return pd.DataFrame(columns=['instante', 'carga'])
    except Exception as e:
        st.error(f"Erro ao carregar dados de carga regional: {e}")
        return pd.DataFrame(columns=['instante', 'carga'])

@st.cache_data(ttl=20)
def get_situacao_reservatorios():
    url = "https://integra.ons.org.br/api/energiaagora/Get/SituacaoDosReservatorios"
    try:
        response = requests.get(url, timeout=5)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Erro ao carregar situação dos reservatórios: {e}")
        return None

# Função para calcular tendências
def calcular_tendencia(df, janela=10):
    if len(df) < janela or len(df) == 0:
        return 0, "stable"
    
    valores_recentes = df['geracao'].tail(janela).values if 'geracao' in df.columns else df['carga'].tail(janela).values
    if len(valores_recentes) < 2:
        return 0, "stable"
    
    try:
        # Calcular tendência usando regressão linear simples
        x = np.arange(len(valores_recentes))
        coef = np.polyfit(x, valores_recentes, 1)[0]
        
        # Classificar tendência
        if coef > 5:  # Aumento significativo
            return coef, "up"
        elif coef < -5:  # Diminuição significativa
            return coef, "down"
        else:
            return coef, "stable"
    except Exception:
        return 0, "stable"

@st.cache_data(ttl=20)
def process_reservatorio_data(data):
    if not data:
        return None
        
    # Agrupar por subsistema
    subsistemas = {}
    for reservatorio in data:
        subsistema = reservatorio.get('Subsistema')
        if subsistema not in subsistemas:
            subsistemas[subsistema] = {
                'valor_util_total': 0,
                'reservatorios': [],
                'quantidade': 0,
                'ear_verificada': 0,
                'ear_maxima': 0
            }
        
        # Adicionar informações do reservatório
        subsistemas[subsistema]['reservatorios'].append({
            'nome': reservatorio.get('Reservatorio'),
            'valor_util': reservatorio.get('ReservatorioValorUtil', 0),
            'porcentagem': reservatorio.get('ReservatorioPorcentagem', 0),
            'ear_verificada': reservatorio.get('ReservatorioEARVerificadaMWMes', 0),
            'ear_maxima': reservatorio.get('ReservatorioMax', 0),
            'bacia': reservatorio.get('Bacia')
        })
        
        # Atualizar totais do subsistema
        subsistemas[subsistema]['quantidade'] += 1
        subsistemas[subsistema]['ear_verificada'] += reservatorio.get('ReservatorioEARVerificadaMWMes', 0)
        subsistemas[subsistema]['ear_maxima'] += reservatorio.get('ReservatorioMax', 0)
        subsistemas[subsistema]['valor_util_total'] += reservatorio.get('ReservatorioValorUtil', 0)
    
    # Calcular médias para cada subsistema
    for subsistema in subsistemas:
        if subsistemas[subsistema]['quantidade'] > 0:
            subsistemas[subsistema]['valor_util_medio'] = (
                subsistemas[subsistema]['valor_util_total'] / 
                subsistemas[subsistema]['quantidade']
            )
            subsistemas[subsistema]['ear_porcentagem'] = (
                (subsistemas[subsistema]['ear_verificada'] / 
                subsistemas[subsistema]['ear_maxima']) * 100 
                if subsistemas[subsistema]['ear_maxima'] > 0 else 0
            )
    
    return subsistemas

def load_data():
    urls = {
        'Eólica': {
            'Norte': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Eolica_json",
            'Nordeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Eolica_json",
            'Sudeste/Centro-Oeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Eolica_json",
            'Sul': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Eolica_json"
        },
        'Solar': {
            'Norte': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Solar_json",
            'Nordeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Solar_json",
            'Sudeste/Centro-Oeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Solar_json",
            'Sul': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Solar_json"
        },
        'Hidráulica': {
            'Norte': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Hidraulica_json",
            'Nordeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Hidraulica_json",
            'Sudeste/Centro-Oeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Hidraulica_json",
            'Sul': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Hidraulica_json"
        },
        'Nuclear': {
            'Sudeste/Centro-Oeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Nuclear_json"
        },
        'Térmica': {
            'Norte': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Norte_Termica_json",
            'Nordeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Nordeste_Termica_json",
            'Sudeste/Centro-Oeste': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_SudesteECentroOeste_Termica_json",
            'Sul': "https://integra.ons.org.br/api/energiaagora/Get/Geracao_Sul_Termica_json"
        }
    }
    
    dataframes = {}
    for fonte, regioes in urls.items():
        for regiao, url in regioes.items():
            df = get_data(url)
            if df is not None and not df.empty:
                key = f'{fonte} - {regiao}'
                dataframes[key] = df
    
    reservatorios = get_situacao_reservatorios()
    
    return dataframes, reservatorios

def process_data(dataframes):
    if not dataframes:
        return {}, {}, {}
    
    # Agregar dados por fonte
    fonte_totals = {}
    for key, df in dataframes.items():
        if df.empty:
            continue
        fonte = key.split(' - ')[0]
        if fonte not in fonte_totals:
            fonte_totals[fonte] = df['geracao'].iloc[-1]
        else:
            fonte_totals[fonte] += df['geracao'].iloc[-1]
    
    # Preparar dados para gráfico de 24h
    timeline_data = {}
    for key, df in dataframes.items():
        if df.empty:
            continue
        fonte = key.split(' - ')[0]
        if fonte not in timeline_data:
            timeline_data[fonte] = df.copy()
        else:
            timeline_data[fonte]['geracao'] += df['geracao']
    
    # Preparar dados regionais
    regional_data = {}
    for key, df in dataframes.items():
        if df.empty:
            continue
        fonte, regiao = key.split(' - ')
        if regiao not in regional_data:
            regional_data[regiao] = {}
        
        if fonte not in regional_data[regiao]:
            regional_data[regiao][fonte] = df['geracao'].iloc[-1]
        else:
            regional_data[regiao][fonte] += df['geracao'].iloc[-1]
    
    return fonte_totals, timeline_data, regional_data

# CSS customizado melhorado
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
    }
    .stApp {
        background-color: #0f172a;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #334155);
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.4);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
        border: 1px solid #475569;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.5);
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #f8fafc;
        margin-bottom: 5px;
    }
    .metric-label {
        font-size: 14px;
        color: #94a3b8;
        margin-bottom: 8px;
    }
    .trend-indicator {
        font-size: 14px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .trend-up {
        color: #10b981;
    }
    .trend-down {
        color: #ef4444;
    }
    .trend-stable {
        color: #f59e0b;
    }
    .chart-container {
        background: linear-gradient(135deg, #1e293b, #334155);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.4);
        border: 1px solid #475569;
    }
    .section-header {
        color: #f8fafc;
        font-size: 20px;
        font-weight: bold;
        margin: 15px 0 10px 0;
        padding-bottom: 8px;
        border-bottom: 3px solid #3b82f6;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
    }
    .status-good {
        background-color: #10b981;
        color: white;
    }
    .status-warning {
        background-color: #f59e0b;
        color: white;
    }
    .status-critical {
        background-color: #ef4444;
        color: white;
    }
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    footer {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Obter hora atual para exibição
current_time = datetime.now().strftime('%H:%M:%S')
current_date_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

# Header otimizado para tela de monitoramento
st.markdown(f"""
    <div style='background: linear-gradient(135deg, #1e293b, #0f172a); padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 8px 16px rgba(0,0,0,0.4); border: 1px solid #475569;'>
        <h1 style='color: #f8fafc; margin: 0; display: flex; align-items: center; font-size: 28px; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>
            <span style='font-size: 32px; margin-right: 15px;'>⚡</span>
            Sistema Elétrico Brasileiro
            <span style='font-size: 16px; margin-left: auto; color: #94a3b8; background: rgba(59, 130, 246, 0.1); padding: 8px 16px; border-radius: 8px;'>
                🕐 {current_time}
            </span>
        </h1>
    </div>
""", unsafe_allow_html=True)

# Carregar dados
with st.spinner('🔄 Carregando dados do sistema...'):
    dataframes, reservatorios = load_data()
    carga_data = get_carga_data()
    fonte_totals, timeline_data, regional_data = process_data(dataframes)

# Carregar dados regionais de carga
norte_carga = get_regional_carga_data("Norte")
nordeste_carga = get_regional_carga_data("Nordeste")
sudeste_carga = get_regional_carga_data("SudesteECentroOeste")
sul_carga = get_regional_carga_data("Sul")

# Layout principal com duas colunas
col1, col2 = st.columns([1, 1])

# Coluna esquerda: Visão geral do sistema e dados regionais
with col1:
    # Métricas principais com indicadores de tendência
    if fonte_totals and not carga_data.empty:
        total_geracao = sum(fonte_totals.values())
        total_carga = carga_data['carga'].iloc[-1] if 'carga' in carga_data else 0
        renovaveis = (fonte_totals.get('Hidráulica', 0) + fonte_totals.get('Eólica', 0) + 
                      fonte_totals.get('Solar', 0))
        percentual_renovavel = (renovaveis / total_geracao * 100) if total_geracao > 0 else 0
        margem = ((total_geracao - total_carga) / total_geracao * 100) if total_geracao > 0 else 0
        
        # Calcular tendências
        trend_carga, tipo_trend_carga = calcular_tendencia(carga_data)
        
        # Calcular tendência total de geração
        df_total_temp = pd.DataFrame({'instante': timeline_data['Hidráulica']['instante'] if 'Hidráulica' in timeline_data else []})
        if not df_total_temp.empty:
            df_total_temp['geracao'] = sum(timeline_data[fonte]['geracao'] for fonte in timeline_data.keys())
            trend_total, tipo_trend_total = calcular_tendencia(df_total_temp)
        else:
            trend_total, tipo_trend_total = 0, "stable"
        
        metric_cols = st.columns(4)
        
        with metric_cols[0]:
            trend_icon_total = "📈" if tipo_trend_total == "up" else "📉" if tipo_trend_total == "down" else "➡️"
            trend_class_total = "trend-up" if tipo_trend_total == "up" else "trend-down" if tipo_trend_total == "down" else "trend-stable"
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-value'>💡 {total_geracao:,.0f} MW</div>
                    <div class='metric-label'>Geração Total</div>
                    <div class='trend-indicator {trend_class_total}'>
                        {trend_icon_total} {trend_total:.1f} MW/h
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with metric_cols[1]:
            trend_icon_carga = "📈" if tipo_trend_carga == "up" else "📉" if tipo_trend_carga == "down" else "➡️"
            trend_class_carga = "trend-up" if tipo_trend_carga == "up" else "trend-down" if tipo_trend_carga == "down" else "trend-stable"
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-value'>⚡ {total_carga:,.0f} MW</div>
                    <div class='metric-label'>Carga Total</div>
                    <div class='trend-indicator {trend_class_carga}'>
                        {trend_icon_carga} {trend_carga:.1f} MW/h
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with metric_cols[2]:
            renovaveis_status = "status-good" if percentual_renovavel > 80 else "status-warning" if percentual_renovavel > 60 else "status-critical"
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-value'>🌱 {percentual_renovavel:.1f}%</div>
                    <div class='metric-label'>Energia Renovável</div>
                    <div class='status-badge {renovaveis_status}'>
                        {"Excelente" if percentual_renovavel > 80 else "Bom" if percentual_renovavel > 60 else "Atenção"}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with metric_cols[3]:
            margem_status = "status-good" if margem > 5 else "status-warning" if margem > 0 else "status-critical"
            margem_color = "#10b981" if margem > 5 else "#f59e0b" if margem > 0 else "#ef4444"
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-value' style='color: {margem_color};'>📊 {margem:.1f}%</div>
                    <div class='metric-label'>Margem</div>
                    <div class='status-badge {margem_status}'>
                        {"Segura" if margem > 5 else "Alerta" if margem > 0 else "Crítica"}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    # Cards de geração por fonte com tendências
    st.markdown("<h3 class='section-header'>📊 Geração por Fonte</h3>", unsafe_allow_html=True)
    
    if fonte_totals:
        fonte_cols = st.columns(5)
        fontes_ordenadas = ['Hidráulica', 'Eólica', 'Solar', 'Térmica', 'Nuclear']
        
        for i, fonte in enumerate(fontes_ordenadas):
            if fonte in fonte_totals:
                col_idx = i % len(fonte_cols)
                with fonte_cols[col_idx]:
                    # Calcular tendência da fonte
                    if fonte in timeline_data:
                        trend_fonte, tipo_trend_fonte = calcular_tendencia(timeline_data[fonte])
                        trend_icon = "📈" if tipo_trend_fonte == "up" else "📉" if tipo_trend_fonte == "down" else "➡️"
                        trend_class = "trend-up" if tipo_trend_fonte == "up" else "trend-down" if tipo_trend_fonte == "down" else "trend-stable"
                    else:
                        trend_fonte, trend_icon, trend_class = 0, "➡️", "trend-stable"
                    
                    emoji_fonte = {"Hidráulica": "💧", "Eólica": "🌪️", "Solar": "☀️", "Térmica": "🔥", "Nuclear": "⚛️"}
                    st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-value'>{emoji_fonte.get(fonte, "⚡")} {fonte_totals[fonte]:,.0f} MW</div>
                            <div class='metric-label'>{fonte}</div>
                            <div class='trend-indicator {trend_class}'>
                                {trend_icon} {trend_fonte:.1f} MW/h
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
    
    # Matriz elétrica atual
    st.markdown("<h3 class='section-header'>🔋 Matriz Elétrica Atual</h3>", unsafe_allow_html=True)
    
    if fonte_totals:
        fig_matriz = go.Figure()
        
        # Ordenar para garantir que hidráulica fique na base
        sorted_keys = sorted(fonte_totals.keys(), key=lambda x: 0 if x == 'Hidráulica' else 1)
        
        # Criar uma única barra empilhada
        for fonte in sorted_keys:
            fig_matriz.add_trace(go.Bar(
                x=['Geração Atual'],
                y=[fonte_totals[fonte]],
                name=fonte,
                marker_color=ENERGY_COLORS[fonte],
                text=f"{fonte}: {fonte_totals[fonte]:,.0f} MW",
                textposition="inside",
                insidetextanchor="middle",
                width=0.6
            ))
        
        # Adicionar anotação total no topo
        fig_matriz.add_annotation(
            x='Geração Atual', y=sum(fonte_totals.values()) + (sum(fonte_totals.values()) * 0.05),
            text=f"Total: {sum(fonte_totals.values()):,.0f} MW",
            showarrow=False,
            font=dict(size=16, color="#f8fafc", family="Arial Black")
        )
        
        # Personalizar layout
        fig_matriz.update_layout(
            template='plotly_dark',
            paper_bgcolor=CARD_COLOR,
            plot_bgcolor=CARD_COLOR,
            margin=dict(t=40, b=40, l=40, r=40),
            height=350,
            barmode='stack',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(size=12, color=TEXT_COLOR)
            ),
            xaxis=dict(
                showgrid=False,
                showticklabels=False
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=GRID_COLOR,
                title="MW",
                titlefont=dict(color=TEXT_COLOR, size=14),
                tickfont=dict(color=TEXT_COLOR, size=12)
            )
        )
        
        st.plotly_chart(fig_matriz, use_container_width=True)

# Coluna direita: Geração vs Carga e status dos reservatórios
with col2:
    # Gráfico de Geração vs Carga
    st.markdown("<h3 class='section-header'>📈 Geração vs Carga (24h)</h3>", unsafe_allow_html=True)
    
    if timeline_data and not carga_data.empty:
        fig_gen_load = go.Figure()
        
        # Adicionar área empilhada para geração por fonte (Hidráulica na base)
        for fonte in sorted(timeline_data.keys(), key=lambda x: 0 if x == 'Hidráulica' else 1):
            df = timeline_data[fonte]
            fig_gen_load.add_trace(go.Scatter(
                x=df['instante'],
                y=df['geracao'],
                name=fonte,
                stackgroup='geracao',
                line=dict(width=0),
                fillcolor=ENERGY_COLORS.get(fonte, '#FFFFFF'),
                hovertemplate=f'<b>{fonte}</b><br>Hora: %{{x}}<br>Geração: %{{y:,.0f}} MW<extra></extra>'
            ))
        
        # Adicionar linha de carga sobre a área empilhada
        fig_gen_load.add_trace(go.Scatter(
            x=carga_data['instante'],
            y=carga_data['carga'],
            name='Carga Total',
            line=dict(color=ENERGY_COLORS['Carga'], width=4, dash='solid'),
            hovertemplate='<b>Carga Total</b><br>Hora: %{x}<br>Carga: %{y:,.0f} MW<extra></extra>'
        ))
        
        fig_gen_load.update_layout(
            template='plotly_dark',
            paper_bgcolor=CARD_COLOR,
            plot_bgcolor=CARD_COLOR,
            margin=dict(t=30, b=50, l=40, r=30),
            height=450,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=11, color=TEXT_COLOR)
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor=GRID_COLOR,
                title="Hora",
                titlefont=dict(color=TEXT_COLOR, size=14),
                tickfont=dict(color=TEXT_COLOR, size=12)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=GRID_COLOR,
                title="MW",
                titlefont=dict(color=TEXT_COLOR, size=14),
                tickfont=dict(color=TEXT_COLOR, size=12)
            )
        )
        
        st.plotly_chart(fig_gen_load, use_container_width=True)
    
    # Status dos reservatórios
    st.markdown("<h3 class='section-header'>🏞️ Reservatórios por Subsistema</h3>", unsafe_allow_html=True)
    
    if reservatorios:
        dados_reservatorios = process_reservatorio_data(reservatorios)
        
        # Criar grid para reservatórios
        if dados_reservatorios:
            num_subsistemas = len(dados_reservatorios)
            res_cols = st.columns(min(num_subsistemas, 4))  # Máximo 4 colunas
            
            for i, (subsistema, dados) in enumerate(dados_reservatorios.items()):
                col_idx = i % len(res_cols)
                with res_cols[col_idx]:
                    valor_util = dados['valor_util_medio']
                    ear_porcentagem = dados['ear_porcentagem']
                    
                    # Definir cor baseada no nível
                    if valor_util >= 70:
                        cor = '#10b981'  # Verde
                        status = 'status-good'
                        status_text = 'Ótimo'
                    elif valor_util >= 40:
                        cor = '#f59e0b'  # Amarelo
                        status = 'status-warning'
                        status_text = 'Atenção'
                    else:
                        cor = '#ef4444'  # Vermelho
                        status = 'status-critical'
                        status_text = 'Crítico'
                        
                    st.markdown(f"""
                        <div class='metric-card'>
                            <div style='font-size: 16px; font-weight: bold; color: #f8fafc; margin-bottom: 10px;'>{subsistema}</div>
                            <div style='display: flex; align-items: center; margin: 10px 0;'>
                                <div style='flex: 1; background: #334155; height: 16px; border-radius: 8px; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);'>
                                    <div style='width: {valor_util}%; background: linear-gradient(90deg, {cor}, {cor}CC); height: 100%; transition: width 0.5s ease;'></div>
                                </div>
                                <div style='margin-left: 12px; font-size: 18px; font-weight: bold; color: {cor};'>{valor_util:.1f}%</div>
                            </div>
                            <div style='color: #94a3b8; font-size: 12px; margin-bottom: 8px;'>EAR: {ear_porcentagem:.1f}%</div>
                            <div class='status-badge {status}'>{status_text}</div>
                        </div>
                    """, unsafe_allow_html=True)

# Seção de geração renovável por região (tela cheia)
st.markdown("<h3 class='section-header'>🌍 Geração Renovável por Região</h3>", unsafe_allow_html=True)

# Criar visualização para geração renovável por região
eolica_data = {k: v for k, v in dataframes.items() if 'Eólica' in k}
solar_data = {k: v for k, v in dataframes.items() if 'Solar' in k}

if eolica_data or solar_data:
    # Criar figura com subplots
    fig_renovaveis = make_subplots(rows=2, cols=1, 
                      subplot_titles=("🌪️ Geração Eólica por Região", "☀️ Geração Solar por Região"),
                      row_heights=[0.5, 0.5],
                      vertical_spacing=0.08)
    
    # Cores para regiões
    cores_regionais = {
        'Norte': '#60A5FA',
        'Nordeste': '#34D399', 
        'Sudeste/Centro-Oeste': '#F87171',
        'Sul': '#FBBF24'
    }
    
    # Adicionar traços de energia eólica
    if eolica_data:
        for regiao, df in eolica_data.items():
            if df.empty:
                continue
            regiao_nome = regiao.split(' - ')[1]
            fig_renovaveis.add_trace(
                go.Scatter(
                    x=df['instante'], 
                    y=df['geracao'],
                    name=f"Eólica - {regiao_nome}",
                    line=dict(color=cores_regionais.get(regiao_nome, '#94a3b8'), width=3),
                    opacity=1 if regiao_nome == 'Nordeste' else 0.8,
                    hovertemplate=f'<b>Eólica - {regiao_nome}</b><br>Hora: %{{x}}<br>Geração: %{{y:,.0f}} MW<extra></extra>'
                ),
                row=1, col=1
            )
    
    # Adicionar traços de energia solar
    if solar_data:
        for regiao, df in solar_data.items():
            if df.empty:
                continue
            regiao_nome = regiao.split(' - ')[1]
            fig_renovaveis.add_trace(
                go.Scatter(
                    x=df['instante'], 
                    y=df['geracao'],
                    name=f"Solar - {regiao_nome}",
                    line=dict(color=cores_regionais.get(regiao_nome, '#94a3b8'), width=3),
                    opacity=1 if regiao_nome == 'Nordeste' else 0.8,
                    hovertemplate=f'<b>Solar - {regiao_nome}</b><br>Hora: %{{x}}<br>Geração: %{{y:,.0f}} MW<extra></extra>'
                ),
                row=2, col=1
            )
    
    # Atualizar layout
    fig_renovaveis.update_layout(
        template='plotly_dark',
        paper_bgcolor=CARD_COLOR,
        plot_bgcolor=CARD_COLOR,
        margin=dict(t=50, b=60, l=40, r=30),
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color=TEXT_COLOR)
        )
    )
    
    fig_renovaveis.update_xaxes(showgrid=True, gridcolor=GRID_COLOR, tickfont=dict(color=TEXT_COLOR, size=11), row=1, col=1)
    fig_renovaveis.update_xaxes(showgrid=True, gridcolor=GRID_COLOR, title="Hora", titlefont=dict(color=TEXT_COLOR, size=14), 
                                tickfont=dict(color=TEXT_COLOR, size=11), row=2, col=1)
    
    fig_renovaveis.update_yaxes(showgrid=True, gridcolor=GRID_COLOR, title="MW", titlefont=dict(color=TEXT_COLOR, size=14), 
                                tickfont=dict(color=TEXT_COLOR, size=11), row=1, col=1)
    fig_renovaveis.update_yaxes(showgrid=True, gridcolor=GRID_COLOR, title="MW", titlefont=dict(color=TEXT_COLOR, size=14), 
                                tickfont=dict(color=TEXT_COLOR, size=11), row=2, col=1)
    
    st.plotly_chart(fig_renovaveis, use_container_width=True)
else:
    st.info("📊 Dados de geração renovável não disponíveis")

# Seção de carga por região
st.markdown("<h3 class='section-header'>⚡ Carga por Região</h3>", unsafe_allow_html=True)

col_carga1, col_carga2 = st.columns([1, 1])

with col_carga1:
    # Obter valores mais recentes para cada região
    region_data = {
        "Norte": norte_carga['carga'].iloc[-1] if not norte_carga.empty else 0,
        "Nordeste": nordeste_carga['carga'].iloc[-1] if not nordeste_carga.empty else 0,
        "Sudeste/Centro-Oeste": sudeste_carga['carga'].iloc[-1] if not sudeste_carga.empty else 0,
        "Sul": sul_carga['carga'].iloc[-1] if not sul_carga.empty else 0
    }
    
    # Criar visualização de carga regional
    fig_regions = go.Figure()
    regions = list(region_data.keys())
    values = list(region_data.values())
    colors = ['#60A5FA', '#34D399', '#F87171', '#FBBF24']
    
    fig_regions.add_trace(go.Bar(
        x=regions,
        y=values,
        marker_color=colors,
        text=[f"{v:,.0f} MW" for v in values],
        textposition="inside",
        textfont=dict(size=14, color='white'),
        hovertemplate='<b>%{x}</b><br>Carga: %{y:,.0f} MW<extra></extra>'
    ))
    
    fig_regions.update_layout(
        template='plotly_dark',
        paper_bgcolor=CARD_COLOR,
        plot_bgcolor=CARD_COLOR,
        margin=dict(t=20, b=40, l=40, r=30),
        height=350,
        xaxis=dict(
            title="Região",
            titlefont=dict(color=TEXT_COLOR, size=14),
            tickfont=dict(color=TEXT_COLOR, size=12)
        ),
        yaxis=dict(
            title="Carga (MW)",
            titlefont=dict(color=TEXT_COLOR, size=14),
            tickfont=dict(color=TEXT_COLOR, size=12),
            showgrid=True,
            gridcolor=GRID_COLOR
        )
    )
    
    st.plotly_chart(fig_regions, use_container_width=True)

with col_carga2:
    # Timeline de carga regional
    if not norte_carga.empty and not nordeste_carga.empty and not sudeste_carga.empty and not sul_carga.empty:
        fig_regional_timeline = go.Figure()
        
        # Adicionar um traço para cada região
        regioes_carga = [
            ("Norte", norte_carga, '#60A5FA'),
            ("Nordeste", nordeste_carga, '#34D399'),
            ("Sudeste/CO", sudeste_carga, '#F87171'),
            ("Sul", sul_carga, '#FBBF24')
        ]
        
        for nome, df, cor in regioes_carga:
            # Calcular tendência da carga regional
            trend_regional, tipo_trend_regional = calcular_tendencia(df)
            trend_icon = "↗️" if tipo_trend_regional == "up" else "↘️" if tipo_trend_regional == "down" else "➡️"
            
            fig_regional_timeline.add_trace(go.Scatter(
                x=df['instante'],
                y=df['carga'],
                name=f"{nome} {trend_icon}",
                line=dict(color=cor, width=3),
                hovertemplate=f'<b>{nome}</b><br>Hora: %{{x}}<br>Carga: %{{y:,.0f}} MW<br>Tendência: {trend_regional:.1f} MW/h<extra></extra>'
            ))
        
        fig_regional_timeline.update_layout(
            template='plotly_dark',
            paper_bgcolor=CARD_COLOR,
            plot_bgcolor=CARD_COLOR,
            margin=dict(t=20, b=50, l=40, r=30),
            height=350,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=11, color=TEXT_COLOR)
            ),
            xaxis=dict(
                title="Hora",
                titlefont=dict(color=TEXT_COLOR, size=14),
                tickfont=dict(color=TEXT_COLOR, size=12),
                showgrid=True,
                gridcolor=GRID_COLOR
            ),
            yaxis=dict(
                title="Carga (MW)",
                titlefont=dict(color=TEXT_COLOR, size=14),
                tickfont=dict(color=TEXT_COLOR, size=12),
                showgrid=True,
                gridcolor=GRID_COLOR
            )
        )
        
        st.plotly_chart(fig_regional_timeline, use_container_width=True)

# Footer compacto com informações do sistema
st.markdown(f"""
    <div style='background: linear-gradient(135deg, #1e293b, #0f172a); padding: 15px; border-radius: 12px; margin-top: 20px; box-shadow: 0 8px 16px rgba(0,0,0,0.4); border: 1px solid #475569;'>
        <div style='display: flex; justify-content: space-between; align-items: center; color: #94a3b8; font-size: 13px;'>
            <div>
                <span style='margin-right: 20px;'>📊 <strong>Fonte:</strong> ONS - Operador Nacional do Sistema</span>
                <span style='margin-right: 20px;'>🔄 <strong>Atualização:</strong> A cada 20 segundos</span>
            </div>
            <div style='background: rgba(59, 130, 246, 0.1); padding: 6px 12px; border-radius: 6px;'>
                <strong>🕐 Última atualização: {current_date_time}</strong>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Opção de atualização automática
if st.checkbox("🔄 Atualização automática (30s)", value=False):
    time.sleep(30)
    st.rerun()
