# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os # Importa il modulo os per verificare l'esistenza del file

# --- Configurazione Pagina ---
st.set_page_config(
    page_title="Analisi Dividendi FDJ",
    page_icon="💰",
    layout="wide", # Utilizza l'intera larghezza della pagina
    initial_sidebar_state="collapsed"
)

# Funzione per migliorare l'aspetto visivo
def set_page_style():
    st.markdown("""
    <style>
    .main {
        background-color: #F5F7F9;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px;
        padding: 10px 15px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4F8BF9;
        color: white;
    }
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    h1, h2, h3 {
        color: #1E3A8A;
    }
    </style>
    """, unsafe_allow_html=True)

set_page_style()

# --- Dati Chiave Estratti (da Testo e PDF) ---
TICKER = "FDJ.PA"
NOME_SOCIETA = "Française des Jeux"
ULTIMO_DPS_PAGATO_VAL = 1.78 # Relativo all'esercizio 2023 [source: 4]
ANNO_ULTIMO_DPS = 2023
PREZZO_RIFERIMENTO_APPROX = 30.0 # Prezzo approssimativo menzionato nel testo [source: 13]
POLITICA_PAYOUT = "80-90% Utile Netto (dal 2022)" # [source: 3]
DPS_ATTESO_2024_VAL = 2.05 # [source: 54]
CRESCITA_ATTESA_DPS_2024 = "+15%" # [source: 54]
IMPATTO_KINDRED_DIVIDENDO = "+10% addizionale dal 2026 (utile 2025)" # [source: 57]
RISCHIO_TASSE_2025 = "€90M impatto EBITDA/anno da metà 2025" # [source: 180, 181]
MITIGAZIONE_TASSE = "Piani per compensare impatto entro 2027" # [source: 183]

# Dati storici Dividendo Per Azione (DPS) [source: 4, 5, 6]
dps_storico_data = {
    'Anno Esercizio': [2019, 2020, 2021, 2022, 2023],
    'DPS (€)': [0.45, 0.90, 1.24, 1.37, 1.78]
}
df_dps = pd.DataFrame(dps_storico_data)

# Dati Finanziari Chiave (Estratti da PDF - 31/12 date) [source: 300, 306, 307]
# Usiamo 2021, 2022, 2023, LTM (che nel PDF è colonna 31/12/24)
fin_data = {
    'Metrica': [
        'Ricavi Totali (€M)',
        'Utile Netto (€M)',
        'EPS Diluito (€)',
        'Cash Flow Operativo (CFO, €M)',
        'Capex (€M)',
        'Free Cash Flow (FCF, €M)',
        'Debito Netto / EBITDA (Leva)',
        'Dividendo per Azione (DPS, €)'
    ],
    '2021': [
        2255.7, # Revenue
        294.2,  # Net Income
        1.54,   # Diluted EPS
        602.9,  # CFO
        -75.5,  # Capex (negativo nel PDF Cash Flow, ma è un outflow)
        527.4,  # FCF (CFO + Capex - assumendo Capex sia negativo)
        "Cassa Netta", # FDJ aveva cassa netta fino a fine 2023 [source: 254]
        1.24    # DPS [source: 9]
        ],
    '2022': [
        2461.1, # Revenue
        307.9,  # Net Income
        1.61,   # Diluted EPS
        406.1,  # CFO
        -104.1, # Capex
        302.0,  # FCF
        "Cassa Netta", # [source: 254]
        1.37    # DPS [source: 9]
        ],
    '2023': [
        2621.5, # Revenue
        425.1,  # Net Income
        2.23,   # Diluted EPS
        628.9,  # CFO
        -124.7, # Capex
        504.2,  # FCF
        "Cassa Netta", # Fine 2023 [source: 254]
        1.78    # DPS [source: 10]
        ],
     # LTM nel PDF corrisponde alla colonna 31/12/24
     # Nota: L'utile netto 2024 LTM nel PDF (398.8) è inferiore al 2023 (425.1).
     # La leva è indicata come ~2x post-Kindred (2025) [source: 263]
    'LTM (31/12/24 PDF)': [
        3065.1, # Revenue
        398.8,  # Net Income
        2.16,   # Diluted EPS
        577.0,  # CFO
        -149.9, # Capex
        427.1,  # FCF
        "~2.0-2.2x (prospettico post-Kindred)", # [source: 263]
        "2.05 (atteso ex. 2024)" # [source: 54]
        ]
}
df_fin = pd.DataFrame(fin_data)

# Nuovi dati per grafici aggiuntivi

# 1. Dati Payout Ratio
payout_data = {
    'Anno': [2019, 2020, 2021, 2022, 2023, 2024],
    'Payout Ratio (%)': [80, 80, 83, 80, 80, 82],  # Stime basate sul testo [source: 9, 10]
    'Note': ['~80% (stima)', '~80% (stima)', '~80-85% (stima)', '~80%', '80%', '~82% (stima)']
}
df_payout = pd.DataFrame(payout_data)

# 2. Dati Dividend Yield comparativo
yield_comp_data = {
    'Società': ['FDJ', 'OPAP', 'Entain', 'Flutter', 'Media Mercato FR'],
    'Dividend Yield (%)': [6.0, 7.5, 3.0, 0.5, 3.2],  # Basato su [source: 245, 247]
    'Tipo': ['Lotterie & Scommesse', 'Lotterie & Scommesse', 'Scommesse Online', 'Scommesse Online', 'Indice']
}
df_yield_comp = pd.DataFrame(yield_comp_data)

# 3. Dati Proiezione Dividendi
forecast_data = {
    'Anno': [2023, 2024, 2025, 2026],
    'DPS (€)': [1.78, 2.05, 2.15, 2.37],  # 2025-2026 sono stime basate su testo [source: 57]
    'Tipo': ['Storico', 'Stima Consenso', 'Proiezione', 'Proiezione Post-Kindred'],
    'Note': ['Pagato', 'Consenso Analisti', 'Pre-effetto Kindred', 'Con effetto Kindred (+10%)']
}
df_forecast = pd.DataFrame(forecast_data)

# 4. Dati Composizione Ricavi
business_mix_data = {
    'Segmento': ['Lotterie Francia', 'Scommesse Sportive & Online', 'Lotteria Irlanda', 'Altre Attività'],
    'Percentuale (%)': [80, 15, 3, 2],  # Basato su [source: 95, 97, 98]
    'Margine Op. (%)': [30, 20, 28, 15]  # Stime margini operativi dalle descrizioni
}
df_business_mix = pd.DataFrame(business_mix_data)

# 5. Dati per Mappa di Calore Rischi
risk_data = {
    'Categoria': ['Rischio Normativo (Tasse)', 'Rischio Integrazione M&A', 
                 'Rischio Leva Finanziaria', 'Rischio Concorrenza Online', 
                 'Rischio Rinnovo Concessioni'],
    'Livello (1-10)': [8, 6, 4, 7, 2],  # Basato sull'analisi testuale
    'Impatto Dividendo': ['Alto', 'Medio', 'Basso', 'Medio', 'Basso'],
    'Orizzonte': ['Breve (2025)', 'Medio (2025-26)', 'Medio (2025-26)', 'Continuo', 'Lungo (2040+)']
}
df_risk = pd.DataFrame(risk_data)

# 6. Dati per Evoluzione Debito e Impatto
debt_data = {
    'Anno': [2021, 2022, 2023, 2024, 2025, 2026, 2027],
    'Debito Netto (€M)': [-450, -350, -671, 300, 1850, 1650, 1450],  # Negativo = cassa netta
    'EBITDA (€M)': [522, 580, 657, 750, 850, 920, 970],  # Basati su testo e trend
    'Leva (Debt/EBITDA)': [0, 0, 0, 0.4, 2.2, 1.8, 1.5]  # 0 = cassa netta
}
df_debt = pd.DataFrame(debt_data)

# Calcolo Trailing Dividend Yield
trailing_yield = (ULTIMO_DPS_PAGATO_VAL / PREZZO_RIFERIMENTO_APPROX) * 100 if PREZZO_RIFERIMENTO_APPROX else None

# --- Titolo e Header ---
st.title(f"💰 Analisi Dividendi: {NOME_SOCIETA} ({TICKER})")
st.caption(f"Analisi aggiornata al: April 15, 2024. Dati finanziari storici fino a LTM (31/12/2024 dal PDF).")
st.markdown("---")

# --- Metriche Chiave Dividendo ---
st.subheader("📊 Indicatori Chiave del Dividendo")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        label=f"Ultimo DPS Pagato (Esercizio {ANNO_ULTIMO_DPS})",
        value=f"€ {ULTIMO_DPS_PAGATO_VAL:.2f}",
        help="Dividendo pagato nel 2024 relativo all'esercizio 2023."
    )
with col2:
    st.metric(
        label=f"Dividend Yield (Trailing Approx.)",
        value=f"{trailing_yield:.1f}%" if trailing_yield is not None else "N/A",
        help=f"Basato sull'ultimo DPS (€{ULTIMO_DPS_PAGATO_VAL:.2f}) e un prezzo di riferimento approssimativo di €{PREZZO_RIFERIMENTO_APPROX:.2f}. Il testo menziona stime forward yield del 6-7% [source: 13, 14]."
    )
with col3:
    st.metric(
        label="Politica di Payout",
        value=POLITICA_PAYOUT,
        help="Politica dichiarata dalla società per la distribuzione degli utili netti. [source: 3]"
    )
with col4:
    st.metric(
        label="DPS Atteso (Esercizio 2024)",
        value=f"€ {DPS_ATTESO_2024_VAL:.2f} ({CRESCITA_ATTESA_DPS_2024})",
        help=f"Previsione basata su analisi [source: 54]. Ulteriore potenziale rialzo {IMPATTO_KINDRED_DIVIDENDO} [source: 57]."
    )
st.markdown("---")

# --- Tab per organizzare i grafici ---
tabs = st.tabs(["Dividendi Storici", "Proiezioni Future", "Mix di Business", "Analisi Comparativa", "Rischi e Debito"])

# TAB 1: Dividendi Storici
with tabs[0]:
    col1, col2 = st.columns(2)
    
    with col1:
        # --- Grafico Storico DPS ---
        st.subheader("📈 Crescita Storica del Dividendo per Azione")
        fig_dps = px.line(
            df_dps,
            x='Anno Esercizio',
            y='DPS (€)',
            title="Andamento DPS FDJ (Esercizi 2019-2023)",
            markers=True,
            text='DPS (€)'  # Mostra i valori sul grafico
        )
        fig_dps.update_traces(textposition="top center", line=dict(width=3, color='#1f77b4'))
        fig_dps.update_layout(xaxis_title="Anno Esercizio Fiscale", yaxis_title="Dividendo per Azione (€)",
                            hovermode="x unified", height=400)
        st.plotly_chart(fig_dps, use_container_width=True)
        st.caption("Fonte: Dati estratti da Analisi_FDJ.txt [source: 4, 5, 6] e TIKR PDF [source: 300]. Nota la forte crescita post-IPO.")
    
    with col2:
        # NUOVO GRAFICO 1: Payout Ratio
        st.subheader("🔄 Evoluzione del Payout Ratio")
        fig_payout = px.bar(
            df_payout,
            x='Anno',
            y='Payout Ratio (%)',
            text='Payout Ratio (%)',
            color='Payout Ratio (%)',
            color_continuous_scale='Blues',
            title="Payout Ratio FDJ (% Utile Netto Distribuito)",
            hover_data=['Note']
        )
        fig_payout.update_layout(coloraxis_showscale=False)
        fig_payout.update_traces(texttemplate='%{text}%', textposition='inside')
        fig_payout.update_layout(yaxis_range=[0, 100], height=400)
        st.plotly_chart(fig_payout, use_container_width=True)
        st.caption("Fonte: Analisi del testo e dati finanziari. FDJ ha mantenuto un payout ratio consistente nell'intervallo 80-85% in linea con la politica dichiarata.")
    
    # --- Tabella Finanziaria Riassuntiva ---
    st.subheader("🔢 Tabella Finanziaria Riassuntiva")
    st.dataframe(df_fin.set_index('Metrica'), use_container_width=True)
    st.caption("Fonte: Dati estratti da TIKR PDF (colonna 31/12/24 usata come LTM) [source: 300, 303, 306]. FCF calcolato come CFO - Capex. Leva Finanziaria indicata come da testo analisi. L'Utile Netto LTM 2024 è risultato inferiore al 2023 nel PDF.")


# TAB 2: Proiezioni Future
with tabs[1]:
    col1, col2 = st.columns(2)
    
    with col1:
        # NUOVO GRAFICO 2: Proiezione Futura Dividendi
        st.subheader("🔮 Proiezione Dividendi 2023-2026")
        fig_forecast = px.line(
            df_forecast,
            x='Anno',
            y='DPS (€)',
            color='Tipo',
            title="Proiezione Dividendi FDJ 2023-2026",
            markers=True,
            text='DPS (€)',
            hover_data=['Note']
        )
        fig_forecast.update_traces(textposition="top right")
        
        # Aggiungiamo l'annotazione per l'impatto Kindred
        fig_forecast.add_annotation(
            x=2026, y=2.37,
            text="Effetto Kindred (+10%)",
            showarrow=True,
            arrowhead=1,
            ax=-40, ay=-40
        )
        
        # Aggiungiamo l'annotazione per le nuove tasse
        fig_forecast.add_annotation(
            x=2025, y=2.15,
            text="Impatto nuove tasse 2025",
            showarrow=True,
            arrowhead=1,
            ax=40, ay=40
        )
        
        fig_forecast.update_layout(height=450)
        st.plotly_chart(fig_forecast, use_container_width=True)
        st.caption("Fonte: Analisi del testo e comunicazioni societarie. Il valore 2024 basato su consenso analisti, 2025-2026 sono proiezioni che considerano l'impatto delle nuove tasse e l'acquisizione di Kindred (effetto +10% atteso dal 2026).")
    
    with col2:
        # NUOVO GRAFICO 3: Crescita CAGR
        st.subheader("📊 Tasso di Crescita Composto (CAGR)")
        
        # Calcoliamo CAGR per diversi periodi
        cagr_data = {
            'Periodo': ['2019-2023', '2021-2023', '2023-2026E'],
            'CAGR (%)': [
                ((df_dps['DPS (€)'].iloc[-1] / df_dps['DPS (€)'].iloc[0]) ** (1/4) - 1) * 100,
                ((df_dps['DPS (€)'].iloc[-1] / df_dps['DPS (€)'].iloc[2]) ** (1/2) - 1) * 100,
                ((df_forecast['DPS (€)'].iloc[-1] / df_forecast['DPS (€)'].iloc[0]) ** (1/3) - 1) * 100
            ],
            'Descrizione': [
                'CAGR dall\'IPO',
                'CAGR ultimi 2 anni',
                'CAGR proiettato'
            ]
        }
        df_cagr = pd.DataFrame(cagr_data)
        
        # Grafico CAGR
        fig_cagr = px.bar(
            df_cagr,
            y='Periodo',
            x='CAGR (%)',
            text='CAGR (%)',
            color='CAGR (%)',
            color_continuous_scale='Greens',
            orientation='h',
            title="Tasso di Crescita Composto (CAGR) Dividendo FDJ",
            hover_data=['Descrizione']
        )
        fig_cagr.update_traces(texttemplate='%{x:.1f}%', textposition='outside')
        fig_cagr.update_layout(coloraxis_showscale=False, height=450)
        st.plotly_chart(fig_cagr, use_container_width=True)
        st.caption("Fonte: Calcoli basati sui dati dividendi storici e proiezioni. Il CAGR dall'IPO (2019) è influenzato dal raddoppio iniziale del dividendo.")
        
    # Analisi impatto tasse e acquisizione Kindred
    st.subheader("⚠️ Impatto delle Nuove Tasse 2025 e Acquisizione Kindred")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.info(f"**Rischio Tasse 2025**\n\n{RISCHIO_TASSE_2025}\n\nImpatto semestrale 2025: €45M\nImpatto annuo pieno: €90M", icon="⚠️")
    with col2:
        st.success(f"**Mitigazione Tasse**\n\n{MITIGAZIONE_TASSE}\n\nLa società ha annunciato un piano per compensare completamente l'effetto entro il 2027.", icon="✅")
    with col3:
        st.info(f"**Effetto Kindred sul Dividendo**\n\n{IMPATTO_KINDRED_DIVIDENDO}\n\nL'acquisizione dovrebbe generare sinergie e flussi di cassa aggiuntivi che supporteranno la crescita del dividendo.", icon="📈")


# TAB 3: Mix di Business
with tabs[2]:
    col1, col2 = st.columns(2)
    
    with col1:
        # NUOVO GRAFICO 4: Composizione del Business
        st.subheader("🧩 Composizione del Business FDJ")
        fig_mix = px.pie(
            df_business_mix,
            values='Percentuale (%)',
            names='Segmento',
            title="Mix di Business FDJ (% Ricavi)",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_mix.update_traces(textposition='inside', textinfo='percent+label')
        fig_mix.update_layout(height=450)
        st.plotly_chart(fig_mix, use_container_width=True)
        st.caption("Fonte: Analisi del testo. Le lotterie francesi costituiscono ancora la maggioranza dei ricavi. Con l'integrazione di Kindred, la componente scommesse e online aumenterà significativamente.")
    
    with col2:
        # NUOVO GRAFICO 5: Profittabilità per Segmento
        st.subheader("💹 Margine Operativo per Segmento")
        fig_margin = px.bar(
            df_business_mix,
            x='Segmento',
            y='Margine Op. (%)',
            text='Margine Op. (%)',
            color='Segmento',
            title="Margini Operativi Stimati per Segmento",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_margin.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_margin.update_layout(height=450)
        st.plotly_chart(fig_margin, use_container_width=True)
        st.caption("Fonte: Stime basate sull'analisi del testo. Le lotterie offrono margini operativi più elevati grazie al regime di monopolio, mentre il segmento delle scommesse online presenta maggiore concorrenza e margini inferiori.")
    
    # Timeline acquisizioni e tappe strategiche
    st.subheader("📅 Timeline Strategica FDJ")
    
    timeline_data = {
        'Anno': ['2019', '2023 (Q2)', '2023 (Q4)', '2024-25', '2025 (H2)', '2027'],
        'Evento': ['IPO e Concessione Lotterie fino 2044', 
                  'Acquisizione ZEturf (€175M)', 
                  'Acquisizione Lotteria Irlanda (€350M)', 
                  'OPA Kindred (€2,6Mld EV)', 
                  'Aumento tasse gioco in Francia', 
                  'Compensazione completa impatto tasse'],
        'Tipo': ['Milestone', 'M&A', 'M&A', 'M&A', 'Regolatorio', 'Strategia'],
        'Descrizione': [
            'Quotazione in borsa e ottenimento concessione esclusiva fino al 2044 per €380M',
            'Ingresso nel segmento scommesse ippiche online',
            'Acquisizione del 100% di Premier Lotteries Ireland (PLI), operatore in esclusiva fino al 2034',
            'Acquisizione trasformativa: creazione di un campione europeo del gioco, diversificazione geografica',
            'Aumento tasse sui giochi d\'azzardo in Francia - impatto €90M/anno',
            'Obiettivo di neutralizzare completamente l\'impatto fiscale attraverso efficienze e sinergie'
        ]
    }
    df_timeline = pd.DataFrame(timeline_data)
    
    # Visualizzazione della timeline
    fig_timeline = px.scatter(
        df_timeline, 
        x='Anno', 
        y='Tipo',
        color='Tipo',
        size=[15]*len(df_timeline),
        text='Evento',
        hover_data=['Descrizione'],
        title="Timeline Strategica di FDJ (2019-2027)"
    )
    
    # Aggiungere connettori tra i punti
    fig_timeline.update_traces(marker=dict(symbol='diamond', opacity=0.8), selector=dict(mode='markers'))
    fig_timeline.add_shape(type="line", x0="2019", y0="Milestone", x1="2027", y1="Strategia", 
                          line=dict(color="lightgrey", width=1, dash="dot"))
    
    # Formattare il layout
    fig_timeline.update_layout(
        height=300,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True)
    st.caption("Fonte: Eventi chiave menzionati nell'analisi testuale. La timeline evidenzia la strategia di trasformazione di FDJ da operatore nazionale di lotterie a gruppo diversificato europeo.")


# TAB 4: Analisi Comparativa
with tabs[3]:
    col1, col2 = st.columns(2)
    
    with col1:
        # NUOVO GRAFICO 6: Dividend Yield Comparativo
        st.subheader("📊 Dividend Yield Comparativo")
        fig_yield = px.bar(
            df_yield_comp,
            x='Società',
            y='Dividend Yield (%)',
            text='Dividend Yield (%)',
            color='Tipo',
            title="Confronto Dividend Yield vs. Competitors",
            hover_data=['Tipo']
        )
        fig_yield.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_yield.update_layout(height=450)
        
        # Aggiungere linea per la media
        fig_yield.add_shape(
            type='line',
            x0=-0.5,
            y0=df_yield_comp['Dividend Yield (%)'].mean(),
            x1=len(df_yield_comp)-0.5,
            y1=df_yield_comp['Dividend Yield (%)'].mean(),
            line=dict(color='red', width=2, dash='dash')
        )
        
        fig_yield.add_annotation(
            x=len(df_yield_comp)-1,
            y=df_yield_comp['Dividend Yield (%)'].mean(),
            text=f"Media: {df_yield_comp['Dividend Yield (%)'].mean():.1f}%",
            showarrow=False,
            yshift=10
        )
        
        st.plotly_chart(fig_yield, use_container_width=True)
        st.caption("Fonte: Dati comparativi menzionati nell'analisi testuale. FDJ offre un yield significativamente superiore ai peer delle scommesse online (Entain, Flutter) e leggermente inferiore a OPAP.")
    
    with col2:
        # NUOVO GRAFICO 7: Multipli Valutativi (EV/EBITDA)
        st.subheader("🔍 Multipli Valutativi Comparativi")
        
        valuation_data = {
            'Società': ['FDJ', 'OPAP', 'Entain', 'Flutter', 'Media Settore'],
            'EV/EBITDA': [9.8, 8.5, 10.0, 12.5, 10.2],
            'P/E': [15.0, 13.5, 18.0, 22.0, 17.1],
            'Tipo': ['Lotterie & Scommesse', 'Lotterie & Scommesse', 'Scommesse Online', 'Scommesse Online', 'Indice']
        }
        df_valuation = pd.DataFrame(valuation_data)
        
        # Grafico multipli
        fig_multiples = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig_multiples.add_trace(
            go.Bar(
                x=df_valuation['Società'],
                y=df_valuation['EV/EBITDA'],
                name='EV/EBITDA',
                marker_color='royalblue',
                text=df_valuation['EV/EBITDA'],
                textposition='outside'
            ),
            secondary_y=False
        )
        
        fig_multiples.add_trace(
            go.Scatter(
                x=df_valuation['Società'],
                y=df_valuation['P/E'],
                name='P/E',
                mode='markers+lines+text',
                marker=dict(size=12, color='firebrick'),
                line=dict(width=2, dash='dot'),
                text=df_valuation['P/E'],
                textposition='top center'
            ),
            secondary_y=True
        )
        
        fig_multiples.update_layout(
            title='Confronto Multipli Valutativi',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            height=450
        )
        
        fig_multiples.update_yaxes(title_text="EV/EBITDA", secondary_y=False)
        fig_multiples.update_yaxes(title_text="P/E", secondary_y=True)
        
        st.plotly_chart(fig_multiples, use_container_width=True)
        st.caption("Fonte: Stime basate sull'analisi testuale e dati di mercato menzionati. FDJ scambia a multipli ragionevoli rispetto al settore, rappresentando un mix di difensività (lotterie) e crescita (espansione digitale/internazionale).")
    
    # Analisi competitiva
    st.subheader("🔎 Posizionamento Competitivo di FDJ")
    
    # Definizione dei dati per la radar chart
    competitive_data = {
        'Dimensione': ['Stabilità Flussi di Cassa', 'Rendimento Dividendo', 'Crescita', 'Diversificazione Geografica', 'Barriere all\'Entrata', 'Innovazione Digitale'],
        'FDJ': [9, 8, 7, 5, 9, 6],
        'OPAP': [8, 9, 5, 3, 8, 5],
        'Entain': [6, 4, 8, 8, 4, 8],
        'Flutter': [5, 1, 9, 9, 4, 9]
    }
    df_competitive = pd.DataFrame(competitive_data)
    
    # Conversione a formato "lungo" per radar chart
    df_comp_long = pd.melt(df_competitive, id_vars=['Dimensione'], var_name='Società', value_name='Punteggio')
    
    # Creazione radar chart
    fig_radar = px.line_polar(
        df_comp_long, 
        r='Punteggio', 
        theta='Dimensione', 
        color='Società', 
        line_close=True,
        range_r=[0, 10],
        title="Analisi Competitiva Radar (Scala 1-10)"
    )
    fig_radar.update_traces(fill='toself', opacity=0.4)
    
    # Layout
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        height=500
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)
    st.caption("Fonte: Analisi qualitativa basata sul testo. FDJ eccelle in stabilità dei flussi di cassa e barriere all'entrata grazie al monopolio delle lotterie, mentre le società più focalizzate sulle scommesse online hanno maggiori punti di forza nella crescita e nell'espansione geografica.")


# TAB 5: Rischi e Debito
with tabs[4]:
    col1, col2 = st.columns(2)
    
    with col1:
        # NUOVO GRAFICO 8: Heatmap Rischi
        st.subheader("🔥 Mappa di Calore dei Rischi")
        
        # Conversione valori categorici in numerici
        impact_map = {'Basso': 1, 'Medio': 2, 'Alto': 3}
        df_risk['Impatto_Num'] = df_risk['Impatto Dividendo'].map(impact_map)
        
        # Creazione heatmap
        fig_heatmap = px.imshow(
            df_risk[['Livello (1-10)', 'Impatto_Num']].T,
            x=df_risk['Categoria'],
            y=['Probabilità', 'Impatto Dividendo'],
            color_continuous_scale='Reds',
            labels=dict(color="Intensità"),
            title="Mappa di Calore dei Rischi per il Dividendo",
            text_auto=True
        )
        
        fig_heatmap.update_layout(height=450)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        st.caption("Fonte: Analisi qualitativa dei rischi menzionati nel testo. L'aumento delle tasse nel 2025 rappresenta il rischio più rilevante a breve termine per il dividendo.")
    
    with col2:
        # NUOVO GRAFICO 9: Evoluzione del Debito e Leva Finanziaria
        st.subheader("💰 Evoluzione Debito e Leva Finanziaria")
        
        # Creazione grafico debito e leva
        fig_debt = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Aggiungiamo barre per il debito netto
        fig_debt.add_trace(
            go.Bar(
                x=df_debt['Anno'],
                y=df_debt['Debito Netto (€M)'],
                name='Debito Netto (€M)',
                marker_color=['green' if x < 0 else 'orangered' for x in df_debt['Debito Netto (€M)']],
                text=[f"Cassa: {-x}M" if x < 0 else f"Debito: {x}M" for x in df_debt['Debito Netto (€M)']],
                textposition='outside'
            ),
            secondary_y=False
        )
        
        # Aggiungiamo linea per la leva
        fig_debt.add_trace(
            go.Scatter(
                x=df_debt['Anno'],
                y=df_debt['Leva (Debt/EBITDA)'],
                name='Leva (Debt/EBITDA)',
                mode='lines+markers+text',
                marker=dict(size=10),
                line=dict(width=3, color='navy'),
                text=df_debt['Leva (Debt/EBITDA)'],
                textposition='top center'
            ),
            secondary_y=True
        )
        
        # Aggiungiamo linea EBITDA
        fig_debt.add_trace(
            go.Scatter(
                x=df_debt['Anno'],
                y=df_debt['EBITDA (€M)'],
                name='EBITDA (€M)',
                mode='lines+markers',
                marker=dict(size=8),
                line=dict(width=2, color='green', dash='dash')
            ),
            secondary_y=False
        )
        
        # Evidenziamo l'effetto Kindred
        fig_debt.add_annotation(
            x=2024.5, 
            y=1500,
            text="Acquisizione<br>Kindred",
            showarrow=True,
            arrowhead=1,
            ax=0, 
            ay=-40
        )
        
        # Evidenziamo l'effetto tasse
        fig_debt.add_annotation(
            x=2025, 
            y=850,
            text="Impatto<br>Tasse<br>-€90M",
            showarrow=True,
            arrowhead=1,
            ax=0, 
            ay=-70
        )
        
        # Layout
        fig_debt.update_layout(
            title="Evoluzione Debito Netto, EBITDA e Leva Finanziaria (2021-2027E)",
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            height=450
        )
        
        fig_debt.update_yaxes(title_text="€ Milioni", secondary_y=False)
        fig_debt.update_yaxes(title_text="Leva (Debt/EBITDA)", secondary_y=True, range=[0, 3])
        
        st.plotly_chart(fig_debt, use_container_width=True)
        st.caption("Fonte: Dati storici e proiezioni basate sull'analisi del testo. FDJ passerà da una posizione di cassa netta a una leva di ~2.2x post-acquisizione di Kindred, per poi ridurla progressivamente nei anni successivi.")
    
    # Impatto sul Dividendo
    st.subheader("⚖️ Analisi dell'Indebitamento e Sostenibilità del Dividendo")
    
    # Dati sostenibilità dividendo
    sustainability_data = {
        'Anno': [2023, 2024, 2025, 2026, 2027],
        'Utile Netto (€M)': [425, 399, 380, 430, 470],  # Considerando impatto tasse 2025
        'DPS (€)': [1.78, 2.05, 2.15, 2.37, 2.50],      # Proiezioni dal testo
        'Payout Ratio (%)': [80, 82, 85, 83, 80],        # Stimato
        'Dividendo Totale (€M)': [340, 380, 395, 440, 465]  # Stime approssimative
    }
    df_sustain = pd.DataFrame(sustainability_data)
    
    # Calcolo FCF - Dividendi
    df_sustain['FCF (€M)'] = [504, 427, 400, 450, 500]  # Basato su trend e impatto tasse
    df_sustain['FCF post-Dividendo (€M)'] = df_sustain['FCF (€M)'] - df_sustain['Dividendo Totale (€M)']
    df_sustain['FCF/Dividendo (x)'] = df_sustain['FCF (€M)'] / df_sustain['Dividendo Totale (€M)']
    
    # Visualizzazione grafico sostenibilità
    fig_sustainability = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Barre FCF e Dividendo
    fig_sustainability.add_trace(
        go.Bar(
            x=df_sustain['Anno'],
            y=df_sustain['FCF (€M)'],
            name='Free Cash Flow (€M)',
            marker_color='lightblue',
            opacity=0.7
        ),
        secondary_y=False
    )
    
    fig_sustainability.add_trace(
        go.Bar(
            x=df_sustain['Anno'],
            y=df_sustain['Dividendo Totale (€M)'],
            name='Dividendo Totale (€M)',
            marker_color='darkblue'
        ),
        secondary_y=False
    )
    
    # Linea Payout Ratio
    fig_sustainability.add_trace(
        go.Scatter(
            x=df_sustain['Anno'],
            y=df_sustain['Payout Ratio (%)'],
            name='Payout Ratio (%)',
            mode='lines+markers+text',
            marker=dict(size=8, color='red'),
            line=dict(width=2, color='red'),
            text=df_sustain['Payout Ratio (%)'],
            textposition='top center'
        ),
        secondary_y=True
    )
    
    # Layout
    fig_sustainability.update_layout(
        title="Analisi Sostenibilità Dividendo: FCF vs Dividendo Totale",
        barmode='overlay',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        height=450
    )
    
    fig_sustainability.update_yaxes(title_text="€ Milioni", secondary_y=False)
    fig_sustainability.update_yaxes(title_text="Payout Ratio (%)", secondary_y=True, range=[0, 100])
    
    st.plotly_chart(fig_sustainability, use_container_width=True)
    st.caption("Fonte: Dati storici 2023 (testo) e proiezioni basate sull'analisi. Anche con l'impatto delle nuove tasse nel 2025, FDJ mantiene un free cash flow ampiamente sufficiente a coprire il dividendo atteso.")

# --- Legge il contenuto del file di analisi ---
st.markdown("---")
st.subheader("📝 Analisi Dettagliata (dal file Analisi_FDJ.txt)")

analysis_file_path = 'Analisi_FDJ.txt'
analysis_content = ""
# Verifica se il file esiste prima di provare a leggerlo
if os.path.exists(analysis_file_path):
    try:
        with open(analysis_file_path, 'r', encoding='utf-8') as f:
            analysis_content = f.read()
            # Sostituisce i tag [source: ...] con un formato più leggibile o li rimuove
            import re
            analysis_content = re.sub(r'\s*\[source:\s*\d+.*?\]', '', analysis_content) # Rimuove i tag source
    except FileNotFoundError:
        st.error(f"Errore: File '{analysis_file_path}' non trovato. Assicurati che sia nella stessa cartella dello script.")
        analysis_content = "Contenuto dell'analisi non disponibile."
    except Exception as e:
        st.error(f"Errore nella lettura del file '{analysis_file_path}': {e}")
        analysis_content = "Errore nel caricamento del contenuto dell'analisi."
else:
    st.warning(f"Attenzione: File '{analysis_file_path}' non trovato. L'analisi testuale non può essere visualizzata.")
    analysis_content = "Contenuto dell'analisi non disponibile (file non trovato)."


# Suddivisione approssimativa del contenuto basata sui titoli nell'analisi
# Nota: Questa è una suddivisione euristica, potrebbe necessitare aggiustamenti
sections = {}
current_section = "Introduzione"
sections[current_section] = ""

# Regex per trovare i titoli principali (## Titolo o # Titolo) e i sottotitoli numerati (## N. Titolo)
title_pattern = re.compile(r"^(#+\s*\d*\.?\s*\*?.*?\*?)$", re.MULTILINE)

last_index = 0
for match in title_pattern.finditer(analysis_content):
    title = match.group(1).strip().replace('#', '').replace('*','').strip()
    start_index = match.start()

    # Aggiunge il testo precedente alla sezione corrente
    sections[current_section] += analysis_content[last_index:start_index].strip()

    # Pulisce il titolo da eventuali numeri iniziali e punti per creare la chiave
    clean_title = re.sub(r"^\d+\.\s+", "", title)
    current_section = clean_title
    sections[current_section] = "" # Inizia una nuova sezione
    last_index = match.end()

# Aggiunge l'ultimo pezzo di testo all'ultima sezione
sections[current_section] += analysis_content[last_index:].strip()

# Visualizza le sezioni con expander
for title, content in sections.items():
    if content.strip(): # Mostra solo sezioni con contenuto
        with st.expander(f"**{title}**", expanded=(title=="Introduzione" or "Dividendi storici" in title)): # Espande le prime sezioni di default
            st.markdown(content, unsafe_allow_html=True)


# --- Conclusioni Specifiche per Investitore Dividend ---
st.markdown("---")
st.subheader("🎯 Conclusioni per l'Investitore Orientato ai Dividendi")
st.markdown(f"""
Basato sull'analisi fornita:

**Punti di Forza (Pro-Dividendo):**
* ✅ **Politica Dividendi Generosa:** Payout target 80-90% dell'utile netto. [source: 3]
* ✅ **Storico di Crescita Robusto:** Il DPS è aumentato significativamente dall'IPO (da €0.45 a €1.78). [source: 4, 5]
* ✅ **Yield Attraente:** Rendimento attuale (trailing ~5.9%, forward stimato 6-7%) superiore alla media di mercato. [source: 13, 14, 15]
* ✅ **Flussi di Cassa Stabili:** Il core business delle lotterie (monopolio fino 2044) garantisce cassa prevedibile e resiliente. [source: 65, 67, 69, 79]
* ✅ **Prospettive di Crescita Dividendo:** Atteso aumento per il 2024 (€2.05) e potenziale boost da Kindred nel 2026. [source: 54, 57]
* ✅ **Solidità Finanziaria:** Rating Investment Grade (Baa1 Moody's) [source: 78, 259] e leva finanziaria gestibile post-acquisizioni (~2x). [source: 263, 266]

**Rischi e Considerazioni (Contro-Dividendo):**
* ⚠️ **Nuove Tasse 2025:** Impatto negativo atteso di **€90M/anno sull'EBITDA** da metà 2025, che potrebbe temporaneamente frenare la crescita degli utili/dividendi. [source: 173, 180, 181, 185]
* ⚠️ **Piani di Mitigazione Tasse:** La società punta a compensare l'impatto fiscale entro il 2027, ma l'efficacia è da verificare. [source: 183]
* ⚠️ **Rischi Integrazione M&A:** L'acquisizione di Kindred è trasformativa ma comporta rischi di esecuzione e integrazione. [source: 45, 117, 118]
* ⚠️ **Concorrenza Online:** Il segmento scommesse/giochi online è competitivo e ha margini più bassi e volatili rispetto alle lotterie. [source: 102, 105, 110]
* ⚠️ **Rischio Normativo:** Oltre alle tasse, il settore è soggetto a cambiamenti regolatori in Francia e UE (es. restrizioni pubblicità, revisione concessioni). [source: 112, 191, 198]

**In Sintesi:** FDJ presenta un profilo interessante per l'investitore da dividendo grazie a yield elevato, crescita storica e solidità del business principale. Tuttavia, l'impatto delle nuove tasse nel 2025 è un fattore chiave da monitorare attentamente, così come il successo dell'integrazione di Kindred per sostenere la crescita futura del dividendo.
""", unsafe_allow_html=True)

# Footer con disclaimer
st.markdown("---")
with st.container():
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; font-size: 0.9em;">
        <h3 style="color: #d32f2f;">DISCLAIMER</h3>
        <p>Le informazioni contenute in questa presentazione sono fornite esclusivamente a scopo informativo generale e/o educativo. Non costituiscono e non devono essere interpretate come consulenza finanziaria, legale, fiscale o di investimento.</p>
        <p>Investire nei mercati finanziari comporta rischi significativi, inclusa la possibilità di perdere l'intero capitale investito. Le performance passate non sono indicative né garanzia di risultati futuri.</p>
        <p>Si raccomanda vivamente di condurre la propria analisi approfondita (due diligence) e di consultare un consulente finanziario indipendente e qualificato prima di prendere qualsiasi decisione di investimento.</p>
        <p style="text-align: right; margin-top: 10px;"><em>Realizzazione a cura della Barba Sparlante</em></p>
    </div>
    """, unsafe_allow_html=True)
