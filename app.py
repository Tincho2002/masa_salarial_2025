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
[data-testid="stMetric"], .stDataFrame, .st-emotion-cache-1n7693g, [data-testid="stExpander"] {
    background-color: var(--secondary-background-color);
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}
[data-testid="stMetricLabel"] {
    color: #555;
    font-size: 1rem;
    font-weight: 500;
}
h1, h2, h3 {
    color: var(--primary-color);
    font-family: var(--font);
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
        # --- MÉTODO DE LECTURA CORREGIDO Y DEFINITIVO ---
        # 1. Leer el excel indicando que la cabecera es la PRIMERA fila (índice 0)
        df = pd.read_excel(url, sheet_name='masa_salarial', header=0, engine='openpyxl')
        
        # 2. Limpiar los nombres de las columnas para eliminar espacios invisibles
        df.columns = [str(col).strip() for col in df.columns]

        # 3. La primera columna está vacía, la eliminamos si existe
        if 'Unnamed: 0' in df.columns:
            df = df.drop(columns=['Unnamed: 0'])
            
        # --- PREPROCESAMIENTO ROBUSTO ---
        if 'Período' not in df.columns:
            st.error("Error Crítico: La columna 'Período' no se encuentra.")
            st.info("Columnas encontradas:")
            st.write(df.columns.tolist())
            return pd.DataFrame()
        
        # 4. Convertir 'Período' a fecha. Las filas con fechas inválidas se marcarán como NaT.
        df['Período'] = pd.to_datetime(df['Período'], errors='coerce')

        # 5. PASO CRÍTICO: Eliminar cualquier fila donde la fecha no se pudo procesar.
        df.dropna(subset=['Período'], inplace=True)
        
        # 6. Ahora que las fechas son válidas, crear columnas de mes de forma segura.
        df['Mes_Num'] = df['Período'].dt.month.astype(int)
        
        meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
        df['Mes'] = df['Mes_Num'].map(meses_es)

        # 7. Procesar el resto de las columnas
        for col in ['Total Mensual', 'Dotación']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        df.rename(columns={'Clasificación Ministerio de Hacienda': 'Clasificacion_Ministerio'}, inplace=True)

        # --- CORRECCIÓN FINAL PARA FILTROS LIMPIOS ---
        # Se eliminan las filas que no tienen datos en las columnas de filtro principales
        # para que no aparezcan opciones 'nan' o 'No Asignado' en los filtros.
        key_filter_columns = ['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación']
        df.dropna(subset=key_filter_columns, inplace=True)

        # Se procesan las columnas para asegurar que sean de tipo texto y no tengan espacios extra
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
selected_gerencia = st.sidebar.multiselect('Gerencia', options=sorted(df['Gerencia'].unique()), default=df['Gerencia'].unique())
selected_nivel = st.sidebar.multiselect('Nivel', options=sorted(df['Nivel'].unique()), default=df['Nivel'].unique())
selected_clasificacion = st.sidebar.multiselect('Clasificación Ministerio', options=sorted(df['Clasificacion_Ministerio'].unique()), default=df['Clasificacion_Ministerio'].unique())
selected_relacion = st.sidebar.multiselect('Relación', options=sorted(df['Relación'].unique()), default=df['Relación'].unique())
meses_ordenados = df.sort_values('Mes_Num')['Mes'].unique()
selected_mes = st.sidebar.multiselect('Mes', options=meses_ordenados, default=list(meses_ordenados))

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
# MODIFICACIÓN: Formato de KPIs a dos decimales
col1.metric("Masa Salarial Total (Período)", f"${total_masa_salarial:,.2f}")
col2.metric(f"Empleados ({latest_month_name})", f"{int(cantidad_empleados)}")
col3.metric("Costo Medio por Empleado (Período)", f"${costo_medio:,.2f}")
    
st.markdown("---")

# --- Visualizaciones ---
if df_filtered.empty:
    st.warning("No hay datos que coincidan con los filtros seleccionados.")
else:
    st.subheader("Evolución Mensual de la Masa Salarial (Datos Detallados)")
    masa_mensual = df_filtered.groupby('Mes').agg({'Total Mensual': 'sum', 'Mes_Num': 'first'}).reset_index().sort_values('Mes_Num')
    
    # MODIFICACIÓN: Layout en columnas para gráfico y tabla
    col_evo1, col_evo2 = st.columns([2, 1]) # Gráfico más ancho que la tabla

    with col_evo1:
        line_chart = alt.Chart(masa_mensual).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X('Mes:N', sort=meses_ordenados.tolist(), title='Mes'),
            y=alt.Y('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
            # MODIFICACIÓN: Formato de tooltip a dos decimales
            tooltip=[alt.Tooltip('Mes:N'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
        ).properties(height=350)
        st.altair_chart(line_chart, use_container_width=True)
    
    with col_evo2:
        st.write("Datos de Evolución")
        # MODIFICACIÓN: Mostrar tabla con formato
        st.dataframe(
            masa_mensual[['Mes', 'Total Mensual']],
            column_config={
                "Total Mensual": st.column_config.NumberColumn(
                    label="Masa Salarial ($)",
                    format="$ {:,.2f}"
                )
            },
            use_container_width=True,
            hide_index=True
        )

    col_grafico1, col_grafico2 = st.columns(2)
    with col_grafico1:
        st.subheader("Masa Salarial por Gerencia")
        gerencia_data = df_filtered.groupby('Gerencia')['Total Mensual'].sum().sort_values(ascending=False).reset_index()
        bar_chart = alt.Chart(gerencia_data).mark_bar().encode(
            x=alt.X('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
            y=alt.Y('Gerencia:N', sort='-x', title=None),
            # MODIFICACIÓN: Formato de tooltip a dos decimales
            tooltip=[alt.Tooltip('Gerencia:N'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
        ).properties(height=400)
        st.altair_chart(bar_chart, use_container_width=True)
        # MODIFICACIÓN: Añadir tabla correspondiente al gráfico
        st.write("Datos por Gerencia")
        st.dataframe(
            gerencia_data,
            column_config={
                "Total Mensual": st.column_config.NumberColumn(
                    label="Masa Salarial ($)",
                    format="$ {:,.2f}"
                )
            },
            use_container_width=True,
            hide_index=True
        )

    with col_grafico2:
        st.subheader("Distribución por Clasificación")
        clasificacion_data = df_filtered.groupby('Clasificacion_Ministerio')['Total Mensual'].sum().reset_index()
        donut_chart = alt.Chart(clasificacion_data).mark_arc(innerRadius=80).encode(
            theta=alt.Theta("Total Mensual:Q"),
            color=alt.Color("Clasificacion_Ministerio:N", title="Clasificación"),
            # MODIFICACIÓN: Formato de tooltip a dos decimales
            tooltip=[alt.Tooltip('Clasificacion_Ministerio:N'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
        ).properties(height=400)
        st.altair_chart(donut_chart, use_container_width=True)
        # MODIFICACIÓN: Añadir tabla correspondiente al gráfico
        st.write("Datos por Clasificación")
        st.dataframe(
            clasificacion_data,
            column_config={
                "Clasificacion_Ministerio": "Clasificación",
                "Total Mensual": st.column_config.NumberColumn(
                    label="Masa Salarial ($)",
                    format="$ {:,.2f}"
                )
            },
            use_container_width=True,
            hide_index=True
        )


    st.subheader("Tabla de Datos Detallados")
    # MODIFICACIÓN: Aplicar formato de moneda a la tabla detallada
    st.dataframe(
        df_filtered, 
        column_config={
             "Total Mensual": st.column_config.NumberColumn(
                label="Total Mensual ($)",
                format="$ {:,.2f}"
            )
        },
        use_container_width=True
    )

# --- Sección de Resumen Anual ---
if summary_df is not None:
    with st.expander("Ver Resumen de Evolución Anual (Datos de Control de la Hoja Excel)"):
        st.subheader("Tabla de Resumen Anual por Clasificación")
        
        # MODIFICACIÓN: Crear config dinámicamente para formato de moneda
        summary_column_config = {
            col: st.column_config.NumberColumn(format="$ {:,.2f}")
            for col in summary_df.columns if pd.api.types.is_numeric_dtype(summary_df[col])
        }
        st.dataframe(summary_df, column_config=summary_column_config, use_container_width=True)
        
        # Preparar datos para el gráfico de barras apiladas
        summary_chart_data = summary_df.drop(columns=['Total general'], errors='ignore').reset_index().melt(
            id_vars='Mes',
            var_name='Clasificacion',
            value_name='Masa Salarial'
        )
        
        st.subheader("Gráfico de Resumen Anual")
        summary_chart = alt.Chart(summary_chart_data).mark_bar().encode(
            x=alt.X('Mes:N', sort=summary_chart_data['Mes'].dropna().unique().tolist(), title='Mes'),
            y=alt.Y('sum(Masa Salarial):Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
            color=alt.Color('Clasificacion:N', title='Clasificación'),
            tooltip=[
                alt.Tooltip('Mes:N'),
                alt.Tooltip('Clasificacion:N'),
                # MODIFICACIÓN: Formato de tooltip a dos decimales
                alt.Tooltip('sum(Masa Salarial):Q', format='$,.2f', title='Masa Salarial')
            ]
        ).properties(
            height=400
        )
        st.altair_chart(summary_chart, use_container_width=True)
