# app.py (versión corregida — preserva gráficos y alineación $ a la derecha)

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from io import BytesIO

# --- Config página ---
st.set_page_config(layout="wide", page_title="Masa Salarial 2025")

# --- CSS personalizado (igual que el tuyo) ---
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

# --- Fuente de datos ---
FILE_URL = "https://raw.githubusercontent.com/Tincho2002/masa_salarial_2025/main/masa_salarial_2025.xlsx"

# --- Funciones de carga (cached) ---
@st.cache_data
def load_data(url):
    try:
        df = pd.read_excel(url, sheet_name='masa_salarial', header=0, engine='openpyxl')
        df.columns = [str(col).strip() for col in df.columns]

        if 'Unnamed: 0' in df.columns:
            df = df.drop(columns=['Unnamed: 0'])
        if 'Período' not in df.columns:
            st.error("Error crítico: la columna 'Período' no se encuentra en la hoja 'masa_salarial'.")
            return pd.DataFrame()

        df['Período'] = pd.to_datetime(df['Período'], errors='coerce')
        df.dropna(subset=['Período'], inplace=True)
        df['Mes_Num'] = df['Período'].dt.month.astype(int)

        meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
        df['Mes'] = df['Mes_Num'].map(meses_es)

        # columnas monetarias: convertir a numérico si existen
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
    except Exception as e:
        st.error(f"Ocurrió un error al cargar la hoja 'masa_salarial': {e}")
        return pd.DataFrame()

@st.cache_data
def load_summary_data(url):
    try:
        summary_df = pd.read_excel(url, sheet_name='Evolución Anual', header=3, index_col=0, engine='openpyxl')
        summary_df.dropna(how='all', axis=0, inplace=True)
        summary_df.dropna(how='all', axis=1, inplace=True)
        if 'Total general' in summary_df.index:
            summary_df = summary_df.drop('Total general')
        summary_df.index.name = 'Mes'
        return summary_df
    except Exception as e:
        st.warning(f"No se pudo cargar la hoja de resumen 'Evolución Anual': {e}")
        return None

# --- Carga datos ---
df = load_data(FILE_URL)
summary_df = load_summary_data(FILE_URL)

if df.empty:
    st.error("La carga de datos detallados ha fallado. El dashboard no puede continuar.")
    st.stop()

# --- Título ---
st.title('📊 Dashboard de Masa Salarial 2025')
st.markdown("Análisis interactivo de los costos de la mano de obra de la compañía.")

# --- Sidebar filtros ---
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

# --- Aplicar filtros robusto ---
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

# --- Visualizaciones (mantenidas igual a tu original) ---
if df_filtered.empty:
    st.warning("No hay datos que coincidan con los filtros seleccionados.")
else:
    # Evolución mensual
    st.subheader("Evolución Mensual de la Masa Salarial")
    col_chart1, col_table1 = st.columns([2, 1])
    chart_height1 = 350

    with col_chart1:
        masa_mensual = df_filtered.groupby('Mes').agg({'Total Mensual': 'sum', 'Mes_Num': 'first'}).reset_index().sort_values('Mes_Num')
        line_chart = alt.Chart(masa_mensual).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X('Mes:N', sort=meses_ordenados, title='Mes'),
            y=alt.Y('Total Mensual:Q',
                    title='Masa Salarial ($)',
                    axis=alt.Axis(format='$,.0s'),
                    scale=alt.Scale(domainMin=3000000000, domainMax=8000000000)
                   ),
            tooltip=[alt.Tooltip('Mes:N'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
        ).properties(
            height=chart_height1,
            padding={'top': 20, 'bottom': 20, 'left': 15, 'right': 15}
        ).configure_view(
            fill='transparent'
        )
        st.altair_chart(line_chart, use_container_width=True)

    with col_table1:
        # ---- Mostrar tabla pequeña con números (no convertir a string) para que Streamlit alinee numéricos a la derecha ----
        masa_mensual_display = masa_mensual[['Mes', 'Total Mensual']].copy()
        # No convertir a string: dejamos Total Mensual numérico (st.dataframe alineará a la derecha)
        # Pero para preservar formato visual mostramos un Styler (si tu versión de Streamlit lo soporta)
        masa_mensual_styled = masa_mensual_display.style.format({"Total Mensual": "${:,.2f}"}).set_properties(subset=['Total Mensual'], **{'text-align': 'right'}).hide(axis="index")
        try:
            st.dataframe(masa_mensual_styled, use_container_width=True, height=chart_height1 - 10)
        except Exception:
            # Si Streamlit no soporta Styler en st.dataframe, mostrar el DataFrame numérico (alineado por st) con float_format global temporal
            with pd.option_context('display.float_format', '{:,.2f}'.format):
                st.dataframe(masa_mensual_display, use_container_width=True, height=chart_height1 - 10)

    st.markdown("---")

    # Masa por gerencia
    st.subheader("Masa Salarial por Gerencia")
    col_chart2, col_table2 = st.columns([3, 2])
    gerencia_data = df_filtered.groupby('Gerencia')['Total Mensual'].sum().sort_values(ascending=False).reset_index()
    chart_height2 = 500

    with col_chart2:
        bar_chart = alt.Chart(gerencia_data).mark_bar().encode(
            x=alt.X('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
            y=alt.Y('Gerencia:N', sort='-x', title=None,
                    axis=alt.Axis(labelLimit=120)
                   ),
            tooltip=[alt.Tooltip('Gerencia:N', title='Gerencia'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
        ).properties(
            height=chart_height2,
            padding={'top': 20, 'bottom': 20, 'left': 15, 'right': 15}
        ).configure_view(
            fill='transparent'
        )
        st.altair_chart(bar_chart, use_container_width=True)

    with col_table2:
        gerencia_display = gerencia_data.copy()
        gerencia_styled = gerencia_display.style.format({"Total Mensual": "${:,.2f}"}).set_properties(subset=['Total Mensual'], **{'text-align': 'right'}).hide(axis="index")
        try:
            st.dataframe(gerencia_styled, use_container_width=True, height=chart_height2 - 10)
        except Exception:
            with pd.option_context('display.float_format', '{:,.2f}'.format):
                st.dataframe(gerencia_display, use_container_width=True, height=chart_height2 - 10)

    st.markdown("---")

    # Distribución por clasificación
    st.subheader("Distribución por Clasificación")
    col_chart3, col_table3 = st.columns([2, 1])
    clasificacion_data = df_filtered.groupby('Clasificacion_Ministerio')['Total Mensual'].sum().reset_index()
    chart_height3 = 350

    with col_chart3:
        donut_chart = alt.Chart(clasificacion_data).mark_arc(innerRadius=80).encode(
            theta=alt.Theta("Total Mensual:Q"),
            color=alt.Color("Clasificacion_Ministerio:N", title="Clasificación"),
            tooltip=[alt.Tooltip('Clasificacion_Ministerio:N'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
        ).properties(
            height=chart_height3,
            padding={'top': 20, 'bottom': 20, 'left': 15, 'right': 15}
        ).configure_view(
            fill='transparent'
        )
        st.altair_chart(donut_chart, use_container_width=True)

    with col_table3:
        clasificacion_display = clasificacion_data.rename(columns={'Clasificacion_Ministerio': 'Clasificación'}).copy()
        clasificacion_styled = clasificacion_display.style.format({"Total Mensual": "${:,.2f}"}).set_properties(subset=['Total Mensual'], **{'text-align': 'right'}).hide(axis="index")
        try:
            st.dataframe(clasificacion_styled, use_container_width=True, height=chart_height3 - 10)
        except Exception:
            with pd.option_context('display.float_format', '{:,.2f}'.format):
                st.dataframe(clasificacion_display, use_container_width=True, height=chart_height3 - 10)

    st.markdown("---")

    # --- Tabla detallada: PREVIEW (por defecto) + opción voluntaria de render completo (HTML) con advertencia ---
    st.subheader("Tabla de Datos Detallados")

    st.info("Mostrar la tabla completa como HTML puede colgar el navegador si el dataset es grande. Usá la vista previa o descargá el CSV.")

    st.write(f"Filas filtradas: {len(df_filtered):,d} — Columnas: {len(df_filtered.columns):,d}")

    # Formateo por columnas (sólo para las que existen)
    detailed_table_cols = [
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
    formatters = {col: "${:,.2f}" for col in detailed_table_cols if col in df_filtered.columns}
    if 'Dotación' in df_filtered.columns:
        formatters['Dotación'] = "{:,.0f}"

    columns_to_align_right = [col for col in detailed_table_cols if col in df_filtered.columns]
    if 'Dotación' in df_filtered.columns:
        columns_to_align_right.append('Dotación')

    # Preview rows control
    preview_default = 200 if len(df_filtered) > 200 else len(df_filtered)
    preview_rows = st.number_input("Filas en vista previa", min_value=10, max_value=1000, value=preview_default, step=10)
    df_preview = df_filtered.head(int(preview_rows)).copy()

    # Mostrar preview con Styler (alineado a la derecha para columnas monetarias)
    try:
        df_preview_styled = df_preview.style.format(formatters).set_properties(subset=columns_to_align_right, **{'text-align': 'right'}).hide(axis="index")
        st.dataframe(df_preview_styled, use_container_width=True, height=400)
    except Exception:
        # fallback: mostrar el DataFrame numérico (st.dataframe alinea numéricos a la derecha)
        with pd.option_context('display.float_format', '{:,.2f}'.format):
            st.dataframe(df_preview, use_container_width=True, height=400)

    # Descarga CSV del filtrado completo
    csv_bytes = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar dataset filtrado (CSV)", data=csv_bytes, file_name="masa_salarial_filtrada.csv", mime="text/csv")

    # Opción de render HTML completo (solo si el usuario confirma)
    show_full_html = st.checkbox("Renderizar tabla completa como HTML (Peligro: puede colgar navegador) — solo si sabés lo que hacés", value=False)
    if show_full_html:
        max_rows_html = len(df_filtered)
        if max_rows_html > 2000:
            st.warning("El dataset tiene muchas filas. Por seguridad limitamos a 2.000 filas al renderizar HTML. Si querés el dataset completo, descargalo en CSV.")
            max_rows_html = 2000
        st.warning(f"Renderizando {max_rows_html:,d} filas como HTML. Esto puede tardar o colgar el navegador.")
        try:
            df_html = df_filtered.head(int(max_rows_html)).copy()
            df_html_styled = df_html.style.format(formatters).set_properties(subset=columns_to_align_right, **{'text-align': 'right'}).hide(axis="index")
            st.markdown(df_html_styled.to_html(), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error al renderizar HTML: {e}")
            st.info("Fallback: mostrar primeras filas con st.dataframe")
            with pd.option_context('display.float_format', '{:,.2f}'.format):
                st.dataframe(df_html.head(500), use_container_width=True, height=500)

# --- Sección Resumen Anual (si existe) ---
if summary_df is not None:
    st.markdown("---")
    st.subheader("Resumen de Evolución Anual (Datos de Control)")

    try:
        summary_formatters = {col: "${:,.2f}" for col in summary_df.columns if pd.api.types.is_numeric_dtype(summary_df[col])}
        st.dataframe(summary_df.style.format(summary_formatters).hide(axis="index"), use_container_width=True, height=300)
    except Exception:
        s_df = summary_df.reset_index().copy()
        num_cols = s_df.select_dtypes(include=[np.number]).columns.tolist()
        for c in num_cols:
            s_df[c] = s_df[c].map(lambda x: "${:,.2f}".format(x) if pd.notnull(x) else "")
        st.dataframe(s_df, use_container_width=True, height=300)

    # gráfico resumen
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
    except Exception:
        st.error("Error al dibujar gráfico de resumen.")
