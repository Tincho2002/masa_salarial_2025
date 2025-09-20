import streamlit as st
import pandas as pd
import altair as alt
import io

# --- Configuración de la página ---
st.set_page_config(layout="wide")

# --- CSS Personalizado para un Estilo Profesional ---
st.markdown("""
<style>
/* --- TEMA PERSONALIZADO --- */
:root {
    --primary-color: #0062ff; /* Un azul corporativo */
    --background-color: #f0f2f6;
    --secondary-background-color: #ffffff;
    --text-color: #333333;
    --font: 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
}

body, .stApp {
    background-color: var(--background-color) !important;
    color: var(--text-color) !important;
}

/* --- Estilo de la Barra Lateral --- */
[data-testid="stSidebar"] {
    background-color: var(--secondary-background-color);
    border-right: 1px solid #e0e0e0;
}

/* --- Estilo para Contenedores y Tarjetas --- */
[data-testid="stMetric"], .stDataFrame, [data-testid="stExpander"], .st-emotion-cache-1n7693g {
    background-color: var(--secondary-background-color);
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}

/* --- Estilo para los Títulos de las Métricas --- */
[data-testid="stMetricLabel"] {
    color: #555;
    font-size: 1rem;
    font-weight: 500;
}

/* --- Tipografía --- */
h1, h2, h3 {
    color: var(--primary-color);
    font-family: var(--font);
}

/* --- Botones --- */
.stButton>button {
    background-color: var(--primary-color);
    color: white;
    border-radius: 8px;
    border: none;
    padding: 10px 20px;
}
.stButton>button:hover {
    background-color: #004ecb;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# --- URL del archivo en GitHub (RAW) - CORREGIDA ---
FILE_URL = "https://raw.githubusercontent.com/Fedesass/streamlit/main/masa_salarial_2025.xlsx"


# --- Carga de datos con cache para optimizar rendimiento ---
@st.cache_data
def load_data(url):
    """
    Carga y preprocesa los datos desde una URL de un archivo Excel.
    """
    try:
        # Usar header=1 para indicar que la segunda fila contiene los encabezados.
        df = pd.read_excel(url, sheet_name='masa_salarial', header=1)
        
        df.columns = df.columns.str.strip()
        
        if df.columns[0].startswith('Unnamed'):
            df = df.iloc[:, 1:]

        # --- PREPROCESAMIENTO ---
        df['Período'] = pd.to_datetime(df['Período'], errors='coerce')
        df['Mes_Num'] = df['Período'].dt.month
        
        meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
        df['Mes'] = df['Mes_Num'].map(meses_es)

        numeric_cols = ['Total Mensual', 'Dotación']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                st.error(f"La columna '{col}' no se encuentra en el archivo.")
                return pd.DataFrame()
        
        string_cols = ['Gerencia', 'Nivel', 'Clasificación Ministerio de Hacienda', 'Relación']
        for col in string_cols:
             if col in df.columns:
                df[col] = df[col].astype(str).fillna('No Asignado')
             else:
                st.error(f"La columna '{col}' no se encuentra en el archivo.")
                return pd.DataFrame()
        
        df.rename(columns={'Clasificación Ministerio de Hacienda': 'Clasificacion_Ministerio'}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Ocurrió un error al cargar o procesar el archivo desde la URL: {e}")
        st.error(f"Asegúrate de que la URL es correcta y es la versión 'Raw' del archivo.")
        return pd.DataFrame()

# --- Título del Dashboard ---
st.title('📊 Dashboard de Masa Salarial 2025')
st.markdown("Análisis interactivo de los costos de la mano de obra de la compañía.")

# --- Cargar y procesar datos ---
with st.spinner('Cargando datos desde GitHub...'):
    df = load_data(FILE_URL)

if df.empty:
    st.error("No se pudieron cargar los datos. Revisa los mensajes de error anteriores.")
    st.stop()
    
# --- Barra Lateral de Filtros ---
st.sidebar.header('Filtros del Dashboard')
selected_gerencia = st.sidebar.multoselect('Gerencia', options=sorted(df['Gerencia'].unique()), default=df['Gerencia'].unique())
selected_nivel = st.sidebar.multoselect('Nivel', options=sorted(df['Nivel'].unique()), default=df['Nivel'].unique())
selected_clasificacion = st.sidebar.multoselect('Clasificación Ministerio', options=sorted(df['Clasificacion_Ministerio'].unique()), default=df['Clasificacion_Ministerio'].unique())
selected_relacion = st.sidebar.multoselect('Relación', options=sorted(df['Relación'].unique()), default=df['Relación'].unique())
meses_ordenados = df.sort_values('Mes_Num')['Mes'].unique()
selected_mes = st.sidebar.multoselect('Mes', options=meses_ordenados, default=list(meses_ordenados))

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
cantidad_empleados = df_filtered['Dotación'].sum()
costo_medio = total_masa_salarial / cantidad_empleados if cantidad_empleados > 0 else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Masa Salarial Total", value=f"${total_masa_salarial:,.0f}")
with col2:
    st.metric(label="Cantidad de Empleados (Dotación)", value=f"{cantidad_empleados:,.0f}")
with col3:
    st.metric(label="Costo Medio por Empleado", value=f"${costo_medio:,.0f}")
    
st.markdown("---")

# --- Visualizaciones y Datos ---
st.header("Análisis de Datos")

if df_filtered.empty:
    st.warning("No hay datos que coincidan con los filtros seleccionados.")
else:
    # --- GRÁFICO DE EVOLUCIÓN MENSUAL ---
    st.subheader("Evolución de la Masa Salarial Mensual")
    masa_mensual = df_filtered.groupby('Mes_Num').agg({'Total Mensual': 'sum'}).reset_index().sort_values('Mes_Num')
    
    line_chart = alt.Chart(masa_mensual).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X('Mes_Num:O', title='Mes', axis=alt.Axis(
            values=list(range(1, 13)),
            labelExpr="['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'][datum.value - 1]"
        )),
        y=alt.Y('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
        tooltip=[
            alt.Tooltip('Mes_Num:N', title='Mes', format=''),
            alt.Tooltip('Total Mensual:Q', title='Masa Salarial', format='$,.0f')
        ]
    ).properties(height=350)
    st.altair_chart(line_chart, use_container_width=True)

    st.markdown("---")

    # --- GRÁFICOS DE DISTRIBUCIÓN ---
    col_grafico1, col_grafico2 = st.columns(2)

    with col_grafico1:
        st.subheader("Masa Salarial por Gerencia")
        gerencia_data = df_filtered.groupby('Gerencia')['Total Mensual'].sum().reset_index()
        
        bar_chart = alt.Chart(gerencia_data).mark_bar().encode(
            x=alt.X('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
            y=alt.Y('Gerencia:N', sort='-x', title='Gerencia'),
            tooltip=[
                alt.Tooltip('Gerencia:N', title='Gerencia'),
                alt.Tooltip('Total Mensual:Q', title='Masa Salarial', format='$,.0f')
            ]
        ).properties(
            height=400
        )
        st.altair_chart(bar_chart, use_container_width=True)

    with col_grafico2:
        st.subheader("Masa Salarial por Clasificación")
        clasificacion_data = df_filtered.groupby('Clasificacion_Ministerio')['Total Mensual'].sum().reset_index()
        
        donut_chart = alt.Chart(clasificacion_data).mark_arc(innerRadius=80).encode(
            theta=alt.Theta(field="Total Mensual", type="quantitative"),
            color=alt.Color(field="Clasificacion_Ministerio", type="nominal", title="Clasificación"),
            tooltip=[
                alt.Tooltip('Clasificacion_Ministerio:N', title='Clasificación'),
                alt.Tooltip('Total Mensual:Q', title='Masa Salarial', format='$,.0f')
            ]
        ).properties(
            height=400
        )
        st.altair_chart(donut_chart, use_container_width=True)

    st.markdown("---")

    # --- TABLA DE DATOS DETALLADOS ---
    st.subheader("Tabla de Datos Detallados")
    st.dataframe(df_filtered, use_container_width=True)

