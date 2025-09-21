# app.py (versión optimizada — evita cuelgues al mostrar tablas grandes)

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from io import BytesIO
import warnings

# Intentar importar requests (normalmente disponible)
try:
    import requests
except Exception:
    requests = None

warnings.filterwarnings("ignore")

# --- Configuración de la página ---
st.set_page_config(layout="wide", page_title="Masa Salarial 2025")

# --- CSS (igual al tuyo) ---
st.markdown("""
<style>
:root {
    --primary-color: #0062ff;
    --background-color: #f0f2f6;
    --secondary-background-color: #ffffff;
    --text-color: #333333;
    --font: 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
}
body, .stApp {
    background-color: var(--background-color) !important;
    color: var(--text-color) !important;
}
[data-testid="stSidebar"] {
    background-color: var(--secondary-background-color);
    border-right: 1px solid #e0e0e0;
}
[data-testid="stMetric"], .stDataFrame {
    background-color: var(--secondary-background-color);
    border: 1px solid #e0e0e0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    border-radius: 10px !important;
    padding: 20px;
}
div[data-testid="stAltairChart"] {
    background-color: var(--secondary-background-color);
    border: 1px solid #e0e0e0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    border-radius: 10px !important;
    overflow: hidden !important;
}
h1, h2, h3 {
    color: var(--primary-color);
    font-family: var(--font);
}
.custom-html-table-container {
    height: 500px;
    overflow: auto;
}
.custom-html-table {
    width: 100%;
    border-collapse: collapse;
    color: var(--text-color);
}
.custom-html-table th, .custom-html-table td {
    padding: 8px 12px;
    border: 1px solid #e0e0e0;
    text-align: left;
    white-space: nowrap;
}
.custom-html-table thead th {
    background-color: #f0f2f6;
    font-weight: bold;
    position: sticky;
    top: 0;
    z-index: 1;
}
</style>
""", unsafe_allow_html=True)

# --- URL del archivo Excel en GitHub ---
FILE_URL = "https://raw.githubusercontent.com/Tincho2002/masa_salarial_2025/main/masa_salarial_2025.xlsx"

# --- Función para descargar bytes del archivo (cached) ---
@st.cache_data(show_spinner=False)
def fetch_file_bytes(url: str):
    if requests is None:
        raise RuntimeError("La librería 'requests' no está disponible en este entorno.")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content

# --- Carga y preprocesado de datos (cached) ---
@st.cache_data(show_spinner=False)
def load_data_from_bytes(bytes_content: bytes):
    df = pd.read_excel(BytesIO(bytes_content), sheet_name='masa_salarial', header=0, engine='openpyxl')
    # limpieza básica y preprocesado (igual que el original)
    df.columns = [str(col).strip() for col in df.columns]
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
    if 'Período' not in df.columns:
        raise ValueError("La columna 'Período' no se encuentra en la hoja 'masa_salarial'.")
    df['Período'] = pd.to_datetime(df['Período'], errors='coerce')
    df.dropna(subset=['Período'], inplace=True)
    df['Mes_Num'] = df['Período'].dt.month.astype(int)
    meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df['Mes'] = df['Mes_Num'].map(meses_es)

    # columnas monetarias (convertir si existen)
    currency_cols = [
        'Total Sujeto a Retención', 'Vacaciones', 'Alquiler', 'Horas Extras', 'Nómina General con Aportes',
        'Cs. Sociales s/Remunerativos', 'Cargas Sociales Ant.', 'IC Pagado', 'Vacaciones Pagadas',
        'Cargas Sociales s/Vac. Pagadas', 'Retribución Cargo 1.1.1.', 'Antigüedad 1.1.3.',
        'Retribuciones Extraordinarias 1.3.1.', 'Contribuciones Patronales', 'Gratificación por Antigüedad',
        'Gratificación por Jubilación', 'Total No Remunerativo', 'SAC Horas Extras', 'Cargas Sociales SAC Hextras',
        'SAC Pagado', 'Cargas Sociales s/SAC Pagado', 'Cargas Sociales Antigüedad', 'Nómina General sin Aportes',
        'Gratificación Única y Extraordinaria', 'Gastos de Representación', 'Contribuciones Patronales 1.3.3.',
        'S.A.C. 1.3.2.', 'S.A.C. 1.1.4.', 'Contribuciones Patronales 1.1.6.', 'Complementos 1.1.7.',
        'Asignaciones Familiares 1.4.', 'Total Mensual'
    ]
    for col in currency_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    if 'Dotación' in df.columns:
        df['Dotación'] = pd.to_numeric(df['Dotación'], errors='coerce').fillna(0)
    df.rename(columns={'Clasificación Ministerio de Hacienda': 'Clasificacion_Ministerio'}, inplace=True)
    key_filter_columns = ['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación']
    existing_key_cols = [c for c in key_filter_columns if c in df.columns]
    if existing_key_cols:
        df.dropna(subset=existing_key_cols, inplace=True)
        for col in existing_key_cols:
            df[col] = df[col].astype(str).str.strip()
    if 'Nro. de Legajo' in df.columns:
        df['Nro. de Legajo'] = df['Nro. de Legajo'].astype(str).str.strip()
    df.reset_index(drop=True, inplace=True)
    return df

# --- Carga segura con mensajes ---
with st.spinner("Descargando y cargando datos..."):
    try:
        file_bytes = fetch_file_bytes(FILE_URL)
        df = load_data_from_bytes(file_bytes)
    except Exception as e:
        st.error(f"Error al obtener/leer el archivo: {e}")
        st.stop()

# --- Cargar resumen 'Evolución Anual' (opcional) ---
@st.cache_data(show_spinner=False)
def load_summary_bytes(bytes_content: bytes):
    try:
        summary_df = pd.read_excel(BytesIO(bytes_content), sheet_name='Evolución Anual', header=3, index_col=0, engine='openpyxl')
        summary_df.dropna(how='all', axis=0, inplace=True)
        summary_df.dropna(how='all', axis=1, inplace=True)
        if 'Total general' in summary_df.index:
            summary_df = summary_df.drop('Total general')
        summary_df.index.name = 'Mes'
        return summary_df
    except Exception:
        return None

summary_df = load_summary_bytes(file_bytes)

# Información sobre tamaño de datos (útil si la app "cuelga")
st.sidebar.markdown("**Información del dataset**")
st.sidebar.write(f"Filas: {len(df):,d}")
st.sidebar.write(f"Columnas: {len(df.columns):,d}")

# --- Título ---
st.title('📊 Dashboard de Masa Salarial 2025')
st.markdown("Análisis interactivo de los costos de la mano de obra de la compañía.")

# --- Barra lateral de filtros (robusta) ---
st.sidebar.header('Filtros del Dashboard')

def safe_unique(colname):
    return sorted(df[colname].dropna().unique().tolist()) if colname in df.columns else []

gerencia_options = safe_unique('Gerencia')
selected_gerencia = st.sidebar.multiselect('Gerencia', options=gerencia_options, default=gerencia_options)

nivel_options = safe_unique('Nivel')
selected_nivel = st.sidebar.multiselect('Nivel', options=nivel_options, default=nivel_options)

clasificacion_options = safe_unique('Clasificacion_Ministerio')
selected_clasificacion = st.sidebar.multiselect('Clasificación Ministerio', options=clasificacion_options, default=clasificacion_options)

relacion_options = safe_unique('Relación')
selected_relacion = st.sidebar.multiselect('Relación', options=relacion_options, default=relacion_options)

meses_ordenados = df.sort_values('Mes_Num')['Mes'].unique().tolist() if 'Mes_Num' in df.columns else []
selected_mes = st.sidebar.multiselect('Mes', options=meses_ordenados, default=meses_ordenados)

# --- Aplicar filtros ---
df_filtered = df.copy()
if 'Gerencia' in df.columns:
    df_filtered = df_filtered[df_filtered['Gerencia'].isin(selected_gerencia)]
if 'Nivel' in df.columns:
    df_filtered = df_filtered[df_filtered['Nivel'].isin(selected_nivel)]
if 'Clasificacion_Ministerio' in df.columns:
    df_filtered = df_filtered[df_filtered['Clasificacion_Ministerio'].isin(selected_clasificacion)]
if 'Relación' in df.columns:
    df_filtered = df_filtered[df_filtered['Relación'].isin(selected_relacion)]
if 'Mes' in df.columns:
    df_filtered = df_filtered[df_filtered['Mes'].isin(selected_mes)]

# --- KPIs ---
total_masa_salarial = df_filtered['Total Mensual'].sum() if 'Total Mensual' in df_filtered.columns else 0
cantidad_empleados = 0
latest_month_name = "N/A"
if not df_filtered.empty and 'Mes_Num' in df_filtered.columns:
    latest_month_num = df_filtered['Mes_Num'].max()
    df_latest_month = df_filtered[df_filtered['Mes_Num'] == latest_month_num]
    if 'Dotación' in df_latest_month.columns:
        cantidad_empleados = df_latest_month['Dotación'].sum()
    if not df_latest_month.empty and 'Mes' in df_latest_month.columns:
        latest_month_name = df_latest_month['Mes'].iloc[0]

costo_medio = total_masa_salarial / cantidad_empleados if cantidad_empleados > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Masa Salarial Total (Período)", f"${total_masa_salarial:,.2f}")
col2.metric(f"Empleados ({latest_month_name})", f"{int(cantidad_empleados):,d}")
col3.metric("Costo Medio por Empleado (Período)", f"${costo_medio:,.2f}")

st.markdown("---")

# --- Visualizaciones (idénticas a tu lógica, con pequeñas defensas) ---
if df_filtered.empty:
    st.warning("No hay datos que coincidan con los filtros seleccionados.")
else:
    # Evolución mensual
    st.subheader("Evolución Mensual de la Masa Salarial")
    col_chart1, col_table1 = st.columns([2, 1])
    masa_mensual = df_filtered.groupby('Mes').agg({'Total Mensual': 'sum', 'Mes_Num': 'first'}).reset_index().sort_values('Mes_Num')
    with col_chart1:
        try:
            line_chart = alt.Chart(masa_mensual).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X('Mes:N', sort=meses_ordenados, title='Mes'),
                y=alt.Y('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                tooltip=[alt.Tooltip('Mes:N'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
            ).properties(height=350)
            st.altair_chart(line_chart, use_container_width=True)
        except Exception as e:
            st.error(f"Error al dibujar gráfico: {e}")

    with col_table1:
        masa_mensual_display = masa_mensual[['Mes', 'Total Mensual']].copy()
        masa_mensual_display['Total Mensual'] = masa_mensual_display['Total Mensual'].map('${:,.2f}'.format)
        st.dataframe(masa_mensual_display.reset_index(drop=True), use_container_width=True, height=300)

    st.markdown("---")

    # Masa por gerencia
    st.subheader("Masa Salarial por Gerencia")
    col_chart2, col_table2 = st.columns([3, 2])
    gerencia_data = df_filtered.groupby('Gerencia')['Total Mensual'].sum().sort_values(ascending=False).reset_index()
    with col_chart2:
        try:
            bar_chart = alt.Chart(gerencia_data).mark_bar().encode(
                x=alt.X('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
                y=alt.Y('Gerencia:N', sort='-x', title=None),
                tooltip=[alt.Tooltip('Gerencia:N'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
            ).properties(height=450)
            st.altair_chart(bar_chart, use_container_width=True)
        except Exception as e:
            st.error(f"Error al dibujar gráfico por gerencia: {e}")

    with col_table2:
        gerencia_display = gerencia_data.copy()
        gerencia_display['Total Mensual'] = gerencia_display['Total Mensual'].map('${:,.2f}'.format)
        st.dataframe(gerencia_display.reset_index(drop=True), use_container_width=True, height=420)

    st.markdown("---")

    # Distribución por clasificación
    st.subheader("Distribución por Clasificación")
    col_chart3, col_table3 = st.columns([2, 1])
    clasificacion_data = df_filtered.groupby('Clasificacion_Ministerio')['Total Mensual'].sum().reset_index()
    with col_chart3:
        try:
            donut_chart = alt.Chart(clasificacion_data).mark_arc(innerRadius=80).encode(
                theta=alt.Theta("Total Mensual:Q"),
                color=alt.Color("Clasificacion_Ministerio:N", title="Clasificación"),
                tooltip=[alt.Tooltip('Clasificacion_Ministerio:N'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
            ).properties(height=350)
            st.altair_chart(donut_chart, use_container_width=True)
        except Exception as e:
            st.error(f"Error al dibujar donut: {e}")

    with col_table3:
        clasificacion_display = clasificacion_data.rename(columns={'Clasificacion_Ministerio': 'Clasificación'}).copy()
        clasificacion_display['Total Mensual'] = clasificacion_display['Total Mensual'].map('${:,.2f}'.format)
        st.dataframe(clasificacion_display.reset_index(drop=True), use_container_width=True, height=320)

    st.markdown("---")

    # ---------------------------
    # TABLA DETALLADA (PREVIEW + DESCARGA)
    # ---------------------------
    st.subheader("Tabla de Datos Detallados")

    st.info("⚠️ Mostrar la tabla completa en el navegador puede colgar la aplicación si el dataset es muy grande. "
            "Por eso mostramos una vista previa y ofrecemos descarga del dataset completo.")

    # Mostrar número de filas/columnas filtradas
    st.write(f"Filas filtradas: {len(df_filtered):,d} — Columnas: {len(df_filtered.columns):,d}")

    # Opciones de visualización
    preview_default_rows = 200 if len(df_filtered) > 200 else len(df_filtered)
    preview_rows = st.number_input("Cantidad de filas en vista previa (recomendado)", min_value=10, max_value=2000, value=preview_default_rows, step=10)
    show_full_html = st.checkbox("Forzar render HTML (máx 500 filas) — riesgo de cuelgue", value=False)

    # Botón descargar CSV (dataset completo)
    csv_bytes = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar dataset filtrado (CSV)", data=csv_bytes, file_name="masa_salarial_filtrada.csv", mime="text/csv")

    # Mostrar vista previa (con formateo)
    df_preview = df_filtered.head(int(preview_rows)).copy()
    numeric_cols = df_preview.select_dtypes(include=[np.number]).columns.tolist()
    for c in numeric_cols:
        if c == 'Dotación':
            # sin decimales
            df_preview[c] = df_preview[c].map(lambda x: "{:,.0f}".format(x) if pd.notnull(x) else "")
        else:
            df_preview[c] = df_preview[c].map(lambda x: "${:,.2f}".format(x) if pd.notnull(x) else "")
    st.dataframe(df_preview.reset_index(drop=True), use_container_width=True, height=400)

    # Si el usuario quiere el HTML forzado (limitado a 500 filas)
    if show_full_html:
        max_html_rows = min(500, len(df_filtered))
        st.warning(f"Renderizando como HTML las primeras {max_html_rows} filas (máx 500). Esto puede ser pesado.")
        with st.spinner("Generando HTML (primera porción)..."):
            df_html = df_filtered.head(max_html_rows).copy()
            # Reaplicar formateo en subset para evitar trabajo excesivo
            display_cols = df_html.columns.tolist()
            formatters = {}
            for col in display_cols:
                if col in numeric_cols and col != 'Dotación':
                    formatters[col] = "${:,.2f}"
                if col == 'Dotación':
                    formatters[col] = "{:,.0f}"
            try:
                st.markdown(df_html.style.format(formatters).to_html(), unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error al renderizar HTML (fallback a st.dataframe): {e}")
                # Fallback: convertir a strings y mostrar con st.dataframe
                for c in numeric_cols:
                    if c == 'Dotación':
                        df_html[c] = df_html[c].map(lambda x: "{:,.0f}".format(x) if pd.notnull(x) else "")
                    else:
                        df_html[c] = df_html[c].map(lambda x: "${:,.2f}".format(x) if pd.notnull(x) else "")
                st.dataframe(df_html.reset_index(drop=True), use_container_width=True, height=500)

# --- Resumen Anual (si existe) ---
if summary_df is not None:
    st.markdown("---")
    st.subheader("Resumen de Evolución Anual (Datos de Control)")
    # Mostrar pequeña tabla formateada (no completa en HTML)
    try:
        s_df = summary_df.reset_index().copy()
        num_cols = s_df.select_dtypes(include=[np.number]).columns.tolist()
        for c in num_cols:
            s_df[c] = s_df[c].map(lambda x: "${:,.2f}".format(x) if pd.notnull(x) else "")
        st.dataframe(s_df, use_container_width=True, height=300)
    except Exception as e:
        st.error(f"Error mostrando resumen: {e}")

    # Gráfico resumen
    try:
        summary_chart_data = summary_df.reset_index().melt(id_vars='Mes', var_name='Clasificacion', value_name='Masa Salarial')
        summary_chart = alt.Chart(summary_chart_data).mark_bar().encode(
            x=alt.X('Mes:N', sort=summary_chart_data['Mes'].dropna().unique().tolist(), title='Mes'),
            y=alt.Y('sum(Masa Salarial):Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
            color=alt.Color('Clasificacion:N', title='Clasificación'),
            tooltip=[
                alt.Tooltip('Mes:N'),
                alt.Tooltip('Clasificacion:N'),
                alt.Tooltip('sum(Masa Salarial):Q', format='$,.2f', title='Masa Salarial')
            ]
        ).properties(height=350)
        st.altair_chart(summary_chart, use_container_width=True)
    except Exception as e:
        st.error(f"Error gráfico resumen: {e}")
