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
/* SOLUCIÓN DEFINITIVA: Estilo del contenedor del gráfico */
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
/* Estilos para la tabla HTML renderizada manualmente */
.custom-html-table-container {
    height: 500px; /* Altura fija para la tabla detallada */
    overflow-y: auto; /* Scroll vertical si el contenido excede la altura */
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

        # Lista exhaustiva de todas las columnas de moneda
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
        
        # Se convierte cada columna a numérica, si existe en el dataframe
        for col in currency_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        if 'Dotación' in df.columns:
            df['Dotación'] = pd.to_numeric(df['Dotación'], errors='coerce').fillna(0)

        df.rename(columns={'Clasificación Ministerio de Hacienda': 'Clasificacion_Ministerio'}, inplace=True)

        key_filter_columns = ['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación']
        df.dropna(subset=key_filter_columns, inplace=True)

        for col in key_filter_columns:
            if col in df.columns:
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
]

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
    # --- Sección 1: Evolución Mensual ---
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
        masa_mensual_styled = masa_mensual[['Mes', 'Total Mensual']].style.format({
            "Total Mensual": "${:,.2f}"
        }).hide(axis="index")
        st.dataframe(masa_mensual_styled, use_container_width=True, height=chart_height1 - 10)

    st.markdown("---")

    # --- Sección 2: Masa Salarial por Gerencia (Gráfico a la Izquierda) ---
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
        gerencia_data_styled = gerencia_data.style.format({
            "Total Mensual": "${:,.2f}"
        }).hide(axis="index")
        st.dataframe(gerencia_data_styled, use_container_width=True, height=chart_height2 - 10)

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
        ).properties(
            height=chart_height3,
            padding={'top': 20, 'bottom': 20, 'left': 15, 'right': 15}
        ).configure_view(
            fill='transparent'
        )
        st.altair_chart(donut_chart, use_container_width=True)

    with col_table3:
        clasificacion_data_styled = clasificacion_data.rename(
            columns={'Clasificacion_Ministerio': 'Clasificación'}
        ).style.format({
            "Total Mensual": "${:,.2f}"
        }).hide(axis="index")
        st.dataframe(clasificacion_data_styled, use_container_width=True, height=chart_height3 - 10)


    st.markdown("---")
    st.subheader("Tabla de Datos Detallados")
    
    # --- SOLUCIÓN DEFINITIVA Y ROBUSTA ---
    # Se renderiza la tabla como HTML para un control total del formato,
    # evitando los errores de los componentes nativos de Streamlit.
    
    # 1. Lista de todas las columnas que deben tener formato de moneda.
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
    
    # 2. Crear un diccionario de formato para las columnas que existen.
    formatters = {
        col: "${:,.2f}"
        for col in detailed_table_cols if col in df_filtered.columns
    }
    if 'Dotación' in df_filtered.columns:
        formatters['Dotación'] = "{:d}"

    # 3. Identificar columnas a alinear a la derecha.
    columns_to_align_right = [col for col in detailed_table_cols if col in df_filtered.columns]
    if 'Dotación' in df_filtered.columns:
        columns_to_align_right.append('Dotación')
    
    # 4. Aplicar estilos y convertir a HTML.
    df_styled_html = (
        df_filtered.style
        .format(formatters)
        .set_properties(subset=columns_to_align_right, **{'text-align': 'right'})
        .hide(axis="index")
        .to_html(classes="custom-html-table")
    )
    
    # 5. Mostrar la tabla HTML dentro de un contenedor con estilo.
    st.markdown(f'<div class="stDataFrame custom-html-table-container">{df_styled_html}</div>', unsafe_allow_html=True)


# --- Sección de Resumen Anual ---
if summary_df is not None:
    st.markdown("---")
    st.subheader("Resumen de Evolución Anual (Datos de Control)")
    
    summary_formatters = {
        col: "${:,.2f}"
        for col in summary_df.columns if pd.api.types.is_numeric_dtype(summary_df[col])
    }
    st.dataframe(summary_df.style.format(summary_formatters), use_container_width=True)
    
    summary_chart_data = summary_df.drop(columns=['Total general'], errors='ignore').reset_index().melt(
        id_vars='Mes',
        var_name='Clasificacion',
        value_name='Masa Salarial'
    )
    
    summary_chart = alt.Chart(summary_chart_data).mark_bar().encode(
        x=alt.X('Mes:N', sort=summary_chart_data['Mes'].dropna().unique().tolist(), title='Mes'),
        y=alt.Y('sum(Masa Salarial):Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
        color=alt.Color('Clasificacion:N', title='Clasificación'),
        tooltip=[
            alt.Tooltip('Mes:N'),
            alt.Tooltip('Clasificacion:N'),
            alt.Tooltip('sum(Masa Salarial):Q', format='$,.2f', title='Masa Salarial')
        ]
    ).properties(
        height=350,
        padding={'top': 20, 'bottom': 20, 'left': 15, 'right': 15}
    ).configure_view(
        fill='transparent'
    )
    st.altair_chart(summary_chart, use_container_width=True)

