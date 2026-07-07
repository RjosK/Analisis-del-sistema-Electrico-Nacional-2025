import os
import glob
import re
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# CONFIGURACIÓN DE LA PÁGINA (STREAMLIT)
# ==============================================================================
st.set_page_config(
    page_title="PLANEAS - Análisis Energías SEN 2025",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# ESTILOS CSS PREMIUM E INSTITUCIONALES (CONAHCYT PLANEAS STYLE)
# ==============================================================================
st.markdown("""
<style>
    /* Fuente e interfaz general */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&family=Outfit:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        color: #003049;
    }
    
    /* Contenedor principal y fondo */
    .main {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding-bottom: 3rem;
    }
    
    /* Tarjetas KPI de vidrio (Glassmorphism) */
    .kpi-card {
        background: rgba(255, 255, 255, 0.85);
        border: 1px solid rgba(0, 48, 73, 0.12);
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 48, 73, 0.07);
        backdrop-filter: blur(8px);
        transition: all 0.3s ease;
        margin-bottom: 1rem;
        border-left: 6px solid #003049;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px 0 rgba(0, 48, 73, 0.15);
        border-color: rgba(0, 48, 73, 0.3);
    }
    .kpi-title {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #6c757d;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #003049;
        font-family: 'Outfit', sans-serif;
    }
    .kpi-delta {
        font-size: 0.85rem;
        font-weight: 600;
        color: #2a9d8f;
        margin-top: 4px;
    }
    .kpi-delta.fossil {
        color: #ca6702;
    }
    
    /* Encabezado Banner */
    .banner {
        background: linear-gradient(135deg, #003049 0%, #005f73 50%, #0a9396 100%);
        padding: 30px 40px;
        border-radius: 20px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0, 48, 73, 0.2);
    }
    .banner h1 {
        color: white !important;
        margin: 0;
        font-size: 2.4rem;
        letter-spacing: -0.5px;
    }
    .banner p {
        color: #e9d8a6;
        margin-top: 8px;
        font-size: 1.1rem;
        font-weight: 400;
    }
    
    /* Estilo para pestañas y expanders */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        border-radius: 10px !important;
        border: 1px solid #dee2e6 !important;
        font-weight: 600 !important;
    }
    
    /* Sidebar custom */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e9ecef !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# MAPEO INSTITUCIONAL DE COLORES
# ==============================================================================
COLOR_MAP = {
    "Ciclo Combinado": "#003049",
    "Termica Convencional": "#005f73",
    "Carboelectrica": "#0A9396",
    "Combustion Interna": "#48cae4",
    "Turbo Gas": "#90e0ef",
    "Hidroelectrica": "#2a9d8f",
    "Fotovoltaica": "#ee9b00",
    "Eolica": "#ca6702",
    "Geotermoelectrica": "#bb3e03",
    "Nucleoelectrica": "#ae2012",
    "Biomasa": "#9b5de5"
}

FOSILES = ["Ciclo Combinado", "Combustion Interna", "Carboelectrica", "Termica Convencional", "Turbo Gas"]
RENOVABLES = ["Eolica", "Fotovoltaica", "Biomasa", "Geotermoelectrica", "Hidroelectrica", "Nucleoelectrica"]

# ==============================================================================
# FUNCIÓN DE CARGA DINÁMICA DE DATOS
# ==============================================================================
@st.cache_data
def load_data():
    base_dir = os.path.abspath(".")
    csv_consolidado = os.path.join(base_dir, "Consolidado_Energias_Generadas.csv")
    
    if os.path.exists(csv_consolidado):
        df = pd.read_csv(csv_consolidado)
        df["Fecha Hora"] = pd.to_datetime(df["Fecha Hora"], format="%d/%m/%Y %H:%M", errors="coerce")
        df["Mes_Nombre"] = df["Fecha Hora"].dt.strftime("%Y-%m")
        df["Hora"] = df["Fecha Hora"].dt.hour
        return df
    
    # Si no existe, extraer dinámicamente
    archivos_csv = glob.glob(os.path.join(base_dir, "**", "Generacion Liquidada*.csv"), recursive=True)
    if not archivos_csv:
        return pd.DataFrame()
        
    archivos_por_mes = {}
    for ruta in archivos_csv:
        nombre = os.path.basename(ruta)
        match = re.search(r"SEN\s+([a-z]+)\s+\d{4}", nombre, re.IGNORECASE)
        if match:
            mes = match.group(1).lower()
            archivos_por_mes.setdefault(mes, []).append(ruta)
            
    def obtener_prioridad(ruta):
        match = re.search(r"_L(\d+)", os.path.basename(ruta))
        return int(match.group(1)) if match else -1

    lista_dataframes = []
    tecnologias = list(COLOR_MAP.keys())
    
    for mes, rutas in archivos_por_mes.items():
        ruta_elegida = max(rutas, key=obtener_prioridad)
        try:
            df_sen = pd.read_csv(ruta_elegida, skiprows=7, sep=";")
            if len(df_sen.columns) <= 1:
                df_sen = pd.read_csv(ruta_elegida, skiprows=7, sep=",")
            df_sen.columns = df_sen.columns.str.strip()
            cols = df_sen.columns
            buscar = lambda texto: next((c for c in cols if texto.lower() in c.lower()), None)
            col_dia = buscar("dia")
            col_hora = buscar("hora")
            fecha_base = pd.to_datetime(df_sen[col_dia].astype(str).str.strip(), dayfirst=True, errors='coerce')
            horas_num = pd.to_numeric(df_sen[col_hora], errors='coerce').fillna(1).astype(int)
            df_procesado = pd.DataFrame()
            df_procesado["Fecha Hora"] = (fecha_base + pd.to_timedelta(horas_num, unit='h')).dt.floor("h")
            for tec in tecnologias:
                col_real = buscar(tec)
                df_procesado[tec] = pd.to_numeric(df_sen[col_real], errors='coerce').fillna(0.0) if col_real else 0.0
            lista_dataframes.append(df_procesado)
        except Exception:
            pass
            
    if not lista_dataframes:
        return pd.DataFrame()
        
    df = pd.concat(lista_dataframes, ignore_index=True)
    df = df.sort_values(by="Fecha Hora").reset_index(drop=True)
    df["Mes_Nombre"] = df["Fecha Hora"].dt.strftime("%Y-%m")
    df["Hora"] = df["Fecha Hora"].dt.hour
    return df

df_raw = load_data()

if df_raw.empty:
    st.error("❌ No se encontraron datos de generación eléctrica. Por favor verifica que los archivos CSV estén en la carpeta del proyecto.")
    st.stop()

# ==============================================================================
# SIDEBAR - FILTROS E INFORMACIÓN
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚡ PLANEAS CONAHCYT")
    st.caption("Plataforma Nacional de Análisis del Sistema Eléctrico")
    st.markdown("---")
    
    # Filtro de Meses
    meses_disponibles = sorted(df_raw["Mes_Nombre"].dropna().unique())
    mes_seleccionado = st.multiselect("📅 Filtrar por Mes:", options=meses_disponibles, default=meses_disponibles)
    
    # Filtro por Tipo de Fuente
    tipo_fuente = st.radio("🔋 Tipo de Fuente:", options=["Todas", "Limpias y Renovables", "Fósiles"], index=0)
    
    # Filtro de Tecnologías
    tecnologias_all = [c for c in COLOR_MAP.keys() if c in df_raw.columns]
    if tipo_fuente == "Limpias y Renovables":
        tecnologias_def = [t for t in tecnologias_all if t in RENOVABLES]
    elif tipo_fuente == "Fósiles":
        tecnologias_def = [t for t in tecnologias_all if t in FOSILES]
    else:
        tecnologias_def = tecnologias_all
        
    tecs_seleccionadas = st.multiselect("⚙️ Tecnologías a incluir:", options=tecnologias_all, default=tecnologias_def)
    
    st.markdown("---")
    st.markdown("### 📥 Descarga Rápida")
    pdf_path = os.path.join(os.path.abspath("."), "Analisis_Energias_SEN_2025.pdf")
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📄 Descargar Reporte PDF",
                data=f,
                file_name="Analisis_Energias_SEN_2025.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    
    st.markdown("---")
    st.caption("© 2026 CONAHCYT - Pronaces Energía y Cambio Climático")

# Aplicar filtros
df_filtered = df_raw[df_raw["Mes_Nombre"].isin(mes_seleccionado)].copy()
if not tecs_seleccionadas:
    st.warning("⚠️ Selecciona al menos una tecnología en el menú lateral para visualizar los datos.")
    st.stop()

# ==============================================================================
# ENCABEZADO PRINCIPAL (BANNER)
# ==============================================================================
st.markdown("""
<div class="banner">
    <h1>Plataforma Nacional de Energía, Ambiente y Sociedad</h1>
    <p>Análisis del Sistema Eléctrico Nacional (SEN) - Capacidad y Evolución de la Generación 2025</p>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# TARJETAS KPI (GLASSMORPHISM)
# ==============================================================================
totales_por_tec = df_filtered[tecs_seleccionadas].sum()
gen_total_mwh = totales_por_tec.sum()
gen_total_gwh = gen_total_mwh / 1e3

# Fósil vs Limpia
tecs_fosiles_sel = [t for t in tecs_seleccionadas if t in FOSILES]
tecs_limpias_sel = [t for t in tecs_seleccionadas if t in RENOVABLES]
gen_fosil = df_filtered[tecs_fosiles_sel].sum().sum() if tecs_fosiles_sel else 0
gen_limpia = df_filtered[tecs_limpias_sel].sum().sum() if tecs_limpias_sel else 0

pct_limpia = (gen_limpia / gen_total_mwh) * 100 if gen_total_mwh > 0 else 0
pct_fosil = (gen_fosil / gen_total_mwh) * 100 if gen_total_mwh > 0 else 0

tec_lider = totales_por_tec.idxmax() if not totales_por_tec.empty else "N/A"
val_lider = totales_por_tec.max() / 1e3 if not totales_por_tec.empty else 0
pct_lider = (totales_por_tec.max() / gen_total_mwh) * 100 if gen_total_mwh > 0 else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Generación Total (SEN)</div>
        <div class="kpi-value">{gen_total_gwh:,.1f} <span style="font-size:1.2rem; color:#6c757d;">GWh</span></div>
        <div class="kpi-delta">⚡ {gen_total_mwh:,.0f} MWh inyectados</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color: #2a9d8f;">
        <div class="kpi-title">Limpias y Renovables</div>
        <div class="kpi-value" style="color:#2a9d8f;">{pct_limpia:.1f}%</div>
        <div class="kpi-delta">🌱 {gen_limpia/1e3:,.1f} GWh generados</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color: #003049;">
        <div class="kpi-title">Fuentes Fósiles</div>
        <div class="kpi-value" style="color:#003049;">{pct_fosil:.1f}%</div>
        <div class="kpi-delta fossil">🔥 {gen_fosil/1e3:,.1f} GWh generados</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color: #ee9b00;">
        <div class="kpi-title">Tecnología Líder</div>
        <div class="kpi-value" style="font-size:1.6rem; padding-top:4px; color:#ee9b00;">{tec_lider}</div>
        <div class="kpi-delta" style="color:#6c757d;">🏆 {val_lider:,.1f} GWh ({pct_lider:.1f}%)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==============================================================================
# SECCIÓN 1: MATRIZ Y PARTICIPACIÓN DE LA GENERACIÓN (UNA SOLA PESTAÑA)
# ==============================================================================
st.markdown("## 📊 Matriz y Balance Energético 2025")
st.caption("Distribución porcentual por tecnología y comparación entre fuentes convencionales y limpias.")

col_pie1, col_pie2 = st.columns([3, 2])

with col_pie1:
    df_pie = pd.DataFrame({
        "Tecnología": totales_por_tec.index,
        "Generación (MWh)": totales_por_tec.values
    }).sort_values(by="Generación (MWh)", ascending=False)
    
    fig_pie = px.pie(
        df_pie,
        names="Tecnología",
        values="Generación (MWh)",
        color="Tecnología",
        color_discrete_map=COLOR_MAP,
        hole=0.45
    )
    fig_pie.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hoverinfo='label+value+percent',
        marker=dict(line=dict(color='#ffffff', width=2))
    )
    fig_pie.update_layout(
        title=dict(text="<b>Participación por Tecnología</b>", font=dict(size=18, color="#003049")),
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
        margin=dict(t=50, b=20, l=10, r=120),
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_pie2:
    df_fuentes_pie = pd.DataFrame({
        "Fuente": ["Fósiles", "Limpias y Renovables"],
        "Generación (MWh)": [gen_fosil, gen_limpia]
    })
    fig_fuentes = px.pie(
        df_fuentes_pie,
        names="Fuente",
        values="Generación (MWh)",
        color="Fuente",
        color_discrete_map={"Fósiles": "#003049", "Limpias y Renovables": "#2a9d8f"},
        hole=0.5
    )
    fig_fuentes.update_traces(
        textposition='inside',
        textinfo='percent+label',
        marker=dict(line=dict(color='#ffffff', width=3))
    )
    fig_fuentes.update_layout(
        title=dict(text="<b>Transición: Fósil vs Limpia</b>", font=dict(size=18, color="#003049")),
        showlegend=False,
        margin=dict(t=50, b=20, l=20, r=20),
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_fuentes, use_container_width=True)

with st.expander("📄 Ver tabla de participación anual detallada"):
    df_tabla_anual = df_pie.copy()
    df_tabla_anual["Participación (%)"] = (df_tabla_anual["Generación (MWh)"] / gen_total_mwh) * 100
    df_tabla_anual["Generación (GWh)"] = df_tabla_anual["Generación (MWh)"] / 1e3
    st.dataframe(df_tabla_anual.style.format({"Generación (MWh)": "{:,.2f}", "Generación (GWh)": "{:,.2f}", "Participación (%)": "{:.2f}%"}), use_container_width=True)

st.markdown("---")

# ==============================================================================
# SECCIÓN 2: EVOLUCIÓN MENSUAL Y ÁREA APILADA
# ==============================================================================
st.markdown("## 📈 Comportamiento y Evolución Mensual")
st.caption("Análisis de tendencia temporal en la inyección de energía al Sistema Eléctrico Nacional a lo largo del año.")

df_mensual = df_filtered.groupby("Mes_Nombre")[tecs_seleccionadas].sum().reset_index()
df_mensual_melted = df_mensual.melt(id_vars=["Mes_Nombre"], value_vars=tecs_seleccionadas, var_name="Tecnología", value_name="MWh")
df_mensual_melted["GWh"] = df_mensual_melted["MWh"] / 1e3

col_line, col_stack = st.columns(2)

with col_line:
    fig_line = px.line(
        df_mensual_melted,
        x="Mes_Nombre",
        y="GWh",
        color="Tecnología",
        color_discrete_map=COLOR_MAP,
        markers=True
    )
    fig_line.update_layout(
        title=dict(text="<b>Evolución de Generación por Tecnología (GWh)</b>", font=dict(size=18, color="#003049")),
        xaxis_title="Mes del Año",
        yaxis_title="Generación (GWh)",
        hovermode="x unified",
        margin=dict(t=50, b=30, l=20, r=20),
        height=450,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.6)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    fig_line.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.08)')
    fig_line.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.08)')
    st.plotly_chart(fig_line, use_container_width=True)

with col_stack:
    fig_area = px.area(
        df_mensual_melted,
        x="Mes_Nombre",
        y="GWh",
        color="Tecnología",
        color_discrete_map=COLOR_MAP
    )
    fig_area.update_layout(
        title=dict(text="<b>Volumen Acumulado Mensual Inyectado (GWh)</b>", font=dict(size=18, color="#003049")),
        xaxis_title="Mes del Año",
        yaxis_title="Generación Acumulada (GWh)",
        hovermode="x unified",
        margin=dict(t=50, b=30, l=20, r=20),
        height=450,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.6)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    fig_area.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.08)')
    fig_area.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.08)')
    st.plotly_chart(fig_area, use_container_width=True)

with st.expander("📄 Ver matriz de generación mensual (MWh)"):
    st.dataframe(df_mensual.set_index("Mes_Nombre").style.format("{:,.2f}"), use_container_width=True)

st.markdown("---")

# ==============================================================================
# SECCIÓN 3: CURVA DE DESPACHO Y PERFIL HORARIO PROMEDIO
# ==============================================================================
st.markdown("## 🕒 Curva de Despacho Promedio Diaria")
st.caption("Perfil horario continuo (00:00 - 23:00 hrs) que ilustra cómo se cubre la demanda en las horas base, el pico solar central y la punta nocturna.")

df_horario = df_filtered.groupby("Hora")[tecs_seleccionadas].mean().reset_index()
df_horario_melted = df_horario.melt(id_vars=["Hora"], value_vars=tecs_seleccionadas, var_name="Tecnología", value_name="MWh Promedio")

fig_hourly = px.area(
    df_horario_melted,
    x="Hora",
    y="MWh Promedio",
    color="Tecnología",
    color_discrete_map=COLOR_MAP
)
fig_hourly.update_layout(
    title=dict(text="<b>Curva de Despacho Promedio Diaria - Interacción Tecnológica (SEN 2025)</b>", font=dict(size=18, color="#003049")),
    xaxis=dict(title="Hora del Día (00:00 - 23:00)", tickmode="linear", tick0=0, dtick=1),
    yaxis_title="Demanda Cubierta Promedio (MWh)",
    hovermode="x unified",
    margin=dict(t=50, b=30, l=20, r=20),
    height=480,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.6)",
    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
)
fig_hourly.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.08)')
fig_hourly.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.08)')
st.plotly_chart(fig_hourly, use_container_width=True)

with st.expander("📄 Ver datos horarios promediados (MWh)"):
    st.dataframe(df_horario.set_index("Hora").style.format("{:,.2f}"), use_container_width=True)

st.markdown("---")

# ==============================================================================
# SECCIÓN 4: DESCARGA DE DATOS Y REPORTES
# ==============================================================================
st.markdown("## 📥 Centro de Descargas y Exportación")
st.caption("Obtén los archivos consolidados y el informe formal en formato PDF listo para su presentación.")

col_d1, col_d2, col_d3 = st.columns(3)

with col_d1:
    csv_consolidado_path = os.path.join(os.path.abspath("."), "Consolidado_Energias_Generadas.csv")
    if os.path.exists(csv_consolidado_path):
        with open(csv_consolidado_path, "rb") as f:
            st.download_button(
                label="📊 Descargar Consolidado SEN (CSV)",
                data=f,
                file_name="Consolidado_Energias_Generadas.csv",
                mime="text/csv",
                use_container_width=True
            )

with col_d2:
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📄 Descargar Reporte Formal (PDF)",
                data=f,
                file_name="Analisis_Energias_SEN_2025.pdf",
                mime="application/pdf",
                use_container_width=True
            )

with col_d3:
    tabla1_path = os.path.join(os.path.abspath("."), "tabla_1_participacion_anual.csv")
    if os.path.exists(tabla1_path):
        with open(tabla1_path, "rb") as f:
            st.download_button(
                label="📑 Descargar Resumen de Matriz (CSV)",
                data=f,
                file_name="tabla_1_participacion_anual.csv",
                mime="text/csv",
                use_container_width=True
            )
