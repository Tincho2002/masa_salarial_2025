import streamlit as st
import pandas as pd
import altair as alt

# --- Configuración de la página ---
st.set_page_config(layout="wide")

# --- CSS Personalizado para un Estilo Profesional ---
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
/* Estilo para contenedores de métricas y tablas */
[data-testid="stMetric"], .stDataFrame {
    background-color: var(--secondary-background-color);
    border: 1px solid #e0e0e0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    border-radius: 10px !important;
    padding: 20px;
}
/* Estilo del contenedor del gráfico */
div[data-testid="stAltairChart"] {
    background-color: var(--secondary-background-color);
    border: 1px solid #e0e0e0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    border-radius: 10px !important;
    overflow: hidden !important; /* Obliga al contenido a respetar los bordes redondeados */
}
h1, h2, h3 {
    color: var(--primary-color);
    font-family: var(--font);
}
/* SOLUCIÓN DE ALINEACIÓN DEFINITIVA */
.stDataFrame table tbody td {
    text-align: right !important;
}
</style>
""", unsafe_allow_html=True)

# --- URL del archivo Excel en GitHub ---
FILE_URL = "https://raw.githubusercontent.com/Tincho2002/masa_salarial_2025/main/masa_salarial_2025.xlsx"

# --- Carga de datos con cache ---
@st.cache_data
def load_data(url):
    """
    Carga y preprocesa los datos detallados de la hoja 'masa_salarial'.
    """
    try:
        df = pd.read_excel(url, sheet_name='masa_salarial', header=0, engine='openpyxl')
        df.columns = [str(col).strip() for col in df.columns]

        if 'Unnamed: 0' in df.columns:
            df = df.drop(columns=['Unnamed: 0'])
            
        if 'Período' not in df.columns:
            st.error("Error Crítico: La columna 'Período' no se encuentra.")
            return pd.DataFrame()
        
        df['Período'] = pd.to_datetime(df['Período'], errors='coerce')
        df.dropna(subset=['Período'], inplace=True)
        df['Mes_Num'] = df['Período'].dt.month.astype(int)
        
        meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
        df['Mes'] = df['Mes_Num'].map(meses_es)

        # Se asegura que las columnas enteras sean del tipo correcto
        if 'Dotación' in df.columns:
            df['Dotación'] = pd.to_numeric(df['Dotación'], errors='coerce').fillna(0).astype(int)
        
        if 'Nro. de Legajo' in df.columns:
             df['Nro. de Legajo'] = pd.to_numeric(df['Nro. de Legajo'], errors='coerce')
             df['Nro. de Legajo'] = df['Nro. de Legajo'].astype('Int64')

        df.rename(columns={'Clasificación Ministerio de Hacienda': 'Clasificacion_Ministerio'}, inplace=True)

        key_filter_columns = ['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación']
        for col in key_filter_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        df.dropna(subset=key_filter_columns, inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
    except Exception as e:
        st.error(f"Ocurrió un error al cargar la hoja 'masa_salarial': {e}")
        return pd.DataFrame()

@st.cache_data
def load_summary_data(url):
    """
    Carga los datos de resumen de la hoja 'Evolución Anual'.
    """
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

# --- Carga de datos ---
df = load_data(FILE_URL)
summary_df = load_summary_data(FILE_URL)

if df.empty:
    st.error("La carga de datos detallados ha fallado. El dashboard no puede continuar.")
    st.stop()

# --- Título del Dashboard ---
st.title('📊 Dashboard de Masa Salarial 2025')
st.markdown("Análisis interactivo de los costos de la mano de obra de la compañía.")
    
# --- Barra Lateral de Filtros ---
st.sidebar.header('Filtros del Dashboard')
gerencia_options = sorted(df['Gerencia'].unique())
selected_gerencia = st.sidebar.multiselect('Gerencia', options=gerencia_options, default=gerencia_options)
nivel_options = sorted(df['Nivel'].unique())
selected_nivel = st.sidebar.multiselect('Nivel', options=nivel_options, default=nivel_options)
clasificacion_options = sorted(df['Clasificacion_Ministerio'].unique())
selected_clasificacion = st.sidebar.multiselect('Clasificación Ministerio', options=clasificacion_options, default=clasificacion_options)
relacion_options = sorted(df['Relación'].unique())
selected_relacion = st.sidebar.multiselect('Relación', options=relacion_options, default=relacion_options)
meses_ordenados = df.sort_values('Mes_Num')['Mes'].unique().tolist()
selected_mes = st.sidebar.multiselect('Mes', options=meses_ordenados, default=meses_ordenados)

# --- Aplicar filtros ---
df_filtered = df[
    df['Gerencia'].isin(selected_gerencia) &
    df['Nivel'].isin(selected_nivel) &
    df['Clasificacion_Ministerio'].isin(selected_clasificacion) &
    df['Relación'].isin(selected_relacion) &
    df['Mes'].isin(selected_mes)
].copy()

# --- KPIs Principales ---
total_masa_salarial = df_filtered['Total Mensual'].sum()
cantidad_empleados = 0
latest_month_name = "N/A"
if not df_filtered.empty:
    latest_month_num = df_filtered['Mes_Num'].max()
    df_latest_month = df_filtered[df_filtered['Mes_Num'] == latest_month_num]
    cantidad_empleados = df_latest_month['Dotación'].sum()
    if not df_latest_month.empty:
        latest_month_name = df_latest_month['Mes'].iloc[0]
costo_medio = total_masa_salarial / cantidad_empleados if cantidad_empleados > 0 else 0
col1, col2, col3 = st.columns(3)
col1.metric("Masa Salarial Total (Período)", f"${total_masa_salarial:,.2f}")
col2.metric(f"Empleados ({latest_month_name})", f"{int(cantidad_empleados)}")
col3.metric("Costo Medio por Empleado (Período)", f"${costo_medio:,.2f}")
st.markdown("---")

# --- Visualizaciones ---
if df_filtered.empty:
    st.warning("No hay datos que coincidan con los filtros seleccionados.")
else:
    # --- Formateadores universales ---
    currency_format = lambda x: f"${x:,.2f}"
    integer_format = lambda x: f"{int(x):,}" if pd.notna(x) else ""

    # --- Sección 1: Evolución Mensual ---
    st.subheader("Evolución Mensual de la Masa Salarial")
    col_chart1, col_table1 = st.columns([2, 1])
    chart_height1 = 350
    masa_mensual = df_filtered.groupby('Mes').agg({'Total Mensual': 'sum', 'Mes_Num': 'first'}).reset_index().sort_values('Mes_Num')
    with col_chart1:
        line_chart = alt.Chart(masa_mensual).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X('Mes:N', sort=meses_ordenados, title='Mes'),
            y=alt.Y('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s'), scale=alt.Scale(domainMin=3000000000, domainMax=8000000000)),
            tooltip=[alt.Tooltip('Mes:N'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
        ).properties(height=chart_height1).configure_view(fill='transparent')
        st.altair_chart(line_chart, use_container_width=True)
    with col_table1:
        masa_mensual_display = masa_mensual[['Mes', 'Total Mensual']].copy()
        masa_mensual_display['Total Mensual'] = masa_mensual_display['Total Mensual'].apply(currency_format)
        st.dataframe(masa_mensual_display, hide_index=True, use_container_width=True, height=chart_height1 - 10)

    st.markdown("---")
    # --- Sección 2: Masa Salarial por Gerencia ---
    st.subheader("Masa Salarial por Gerencia")
    col_chart2, col_table2 = st.columns([3, 2])
    gerencia_data = df_filtered.groupby('Gerencia')['Total Mensual'].sum().sort_values(ascending=False).reset_index()
    chart_height2 = 500
    with col_chart2:
        bar_chart = alt.Chart(gerencia_data).mark_bar().encode(
            x=alt.X('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
            y=alt.Y('Gerencia:N', sort='-x', title=None, axis=alt.Axis(labelLimit=120)),
            tooltip=[alt.Tooltip('Gerencia:N', title='Gerencia'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
        ).properties(height=chart_height2).configure_view(fill='transparent')
        st.altair_chart(bar_chart, use_container_width=True)
    with col_table2:
        gerencia_data_display = gerencia_data.copy()
        gerencia_data_display['Total Mensual'] = gerencia_data_display['Total Mensual'].apply(currency_format)
        st.dataframe(gerencia_data_display, hide_index=True, use_container_width=True, height=chart_height2 - 10)

    st.markdown("---")
    # --- Sección 3: Distribución por Clasificación ---
    st.subheader("Distribución por Clasificación")
    col_chart3, col_table3 = st.columns([2, 1])
    clasificacion_data = df_filtered.groupby('Clasificacion_Ministerio')['Total Mensual'].sum().reset_index()
    chart_height3 = 350
    with col_chart3:
        donut_chart = alt.Chart(clasificacion_data).mark_arc(innerRadius=80).encode(
            theta=alt.Theta("Total Mensual:Q"),
            color=alt.Color("Clasificacion_Ministerio:N", title="Clasificación"),
            tooltip=[alt.Tooltip('Clasificacion_Ministerio:N'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
        ).properties(height=chart_height3).configure_view(fill='transparent')
        st.altair_chart(donut_chart, use_container_width=True)
    with col_table3:
        clasificacion_data_display = clasificacion_data.rename(columns={'Clasificacion_Ministerio': 'Clasificación'}).copy()
        clasificacion_data_display['Total Mensual'] = clasificacion_data_display['Total Mensual'].apply(currency_format)
        st.dataframe(clasificacion_data_display, hide_index=True, use_container_width=True, height=chart_height3 - 10)

    st.markdown("---")
    # --- Tabla de Datos Detallados ---
    st.subheader("Tabla de Datos Detallados")
    df_display = df_filtered.copy()
    currency_columns = ['Total Sujeto a Retención', 'Vacaciones', 'Alquiler', 'Horas Extras', 'Nómina General con Aportes', 'Cs. Sociales s/Remunerativos', 'Cargas Sociales Ant.', 'IC Pagado', 'Vacaciones Pagadas', 'Cargas Sociales s/Vac. Pagadas', 'Retribución Cargo 1.1.1.', 'Antigüedad 1.1.3.', 'Retribuciones Extraordinarias 1.3.1.', 'Contribuciones Patronales', 'Gratificación por Antigüedad', 'Gratificación por Jubilación', 'Total No Remunerativo', 'SAC Horas Extras', 'Cargas Sociales SAC Hextras', 'SAC Pagado', 'Cargas Sociales s/SAC Pagado', 'Cargas Sociales Antigüedad', 'Nómina General sin Aportes', 'Gratificación Única y Extraordinaria', 'Gastos de Representación', 'Contribuciones Patronales 1.3.3.', 'S.A.C. 1.3.2.', 'S.A.C. 1.1.4.', 'Contribuciones Patronales 1.1.6.', 'Complementos 1.1.7.', 'Asignaciones Familiares 1.4.', 'Total Mensual']
    integer_columns = ['Nro. de Legajo', 'Dotación']
    for col in currency_columns:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(currency_format)
    for col in integer_columns:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(integer_format)
    st.dataframe(df_display, use_container_width=True)

# --- Sección de Resumen Anual ---
if summary_df is not None:
    st.markdown("---")
    st.subheader("Resumen de Evolución Anual (Datos de Control)")
    summary_df_display = summary_df.reset_index().copy()
    for col in summary_df_display.columns:
        if col != 'Mes' and pd.api.types.is_numeric_dtype(summary_df_display[col]):
            summary_df_display[col] = summary_df_display[col].apply(currency_format)
    st.dataframe(summary_df_display, use_container_width=True, hide_index=True)
    
    summary_chart_data = summary_df.drop(columns=['Total general'], errors='ignore').reset_index().melt(id_vars='Mes', var_name='Clasificacion', value_name='Masa Salarial')
    summary_chart = alt.Chart(summary_chart_data).mark_bar().encode(
        x=alt.X('Mes:N', sort=summary_chart_data['Mes'].dropna().unique().tolist(), title='Mes'),
        y=alt.Y('sum(Masa Salarial):Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
        color=alt.Color('Clasificacion:N', title='Clasificación'),
        tooltip=[alt.Tooltip('Mes:N'), alt.Tooltip('Clasificacion:N'), alt.Tooltip('sum(Masa Salarial):Q', format='$,.2f', title='Masa Salarial')]
    ).properties(height=350).configure_view(fill='transparent')
    st.altair_chart(summary_chart, use_container_width=True)

