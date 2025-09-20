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
[data-testid="stMetric"], .stDataFrame, [data-testid="stExpander"] {
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


# --- Carga de datos con cache para optimizar rendimiento ---
@st.cache_data
def load_data(file_path):
    """
    Carga y preprocesa los datos desde el archivo Excel.
    """
    try:
        df = pd.read_excel(file_path, sheet_name='masa_salarial', header=1) # Asumiendo que la fila 2 es el encabezado
        
        # Limpieza de nombres de columnas (quitar espacios, etc.)
        df.columns = df.columns.str.strip()
        
        # Eliminar la primera columna si no tiene nombre y es un índice no deseado
        if df.columns[0].startswith('Unnamed'):
            df = df.iloc[:, 1:]

        # --- PREPROCESAMIENTO DE DATOS ---
        # Convertir 'Período' a formato de fecha
        df['Período'] = pd.to_datetime(df['Período'], errors='coerce')
        
        # Extraer el mes y el nombre del mes para el filtro
        df['Mes_Num'] = df['Período'].dt.month
        
        # Mapeo de número de mes a nombre en español
        meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
        df['Mes'] = df['Mes_Num'].map(meses_es)

        # Seleccionar columnas relevantes y rellenar NaNs
        numeric_cols = ['Total Mensual', 'Dotación']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                st.error(f"La columna '{col}' no se encuentra en el archivo. Por favor, verifica el Excel.")
                return pd.DataFrame()
        
        string_cols = ['Gerencia', 'Nivel', 'Clasificación Ministerio de Hacienda', 'Relación']
        for col in string_cols:
             if col in df.columns:
                df[col] = df[col].astype(str).fillna('No Asignado')
             else:
                st.error(f"La columna '{col}' no se encuentra en el archivo. Por favor, verifica el Excel.")
                return pd.DataFrame()
        
        # Renombrar columnas para facilitar el acceso
        df.rename(columns={'Clasificación Ministerio de Hacienda': 'Clasificacion_Ministerio'}, inplace=True)

        return df
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo en la ruta '{file_path}'. Asegúrate de que el archivo 'masa_salarial_2025.xlsx' esté en el mismo directorio que la app.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocurrió un error al cargar o procesar el archivo Excel: {e}")
        return pd.DataFrame()

# --- Cargar los datos ---
df = load_data('masa_salarial_2025.xlsx')

# Si el dataframe está vacío, detenemos la ejecución
if df.empty:
    st.stop()
    
# --- Barra Lateral de Filtros ---
st.sidebar.header('Filtros del Dashboard')

# Filtro por Gerencia
selected_gerencia = st.sidebar.multiselect(
    'Gerencia',
    options=sorted(df['Gerencia'].unique()),
    default=df['Gerencia'].unique()
)

# Filtro por Nivel
selected_nivel = st.sidebar.multiselect(
    'Nivel',
    options=sorted(df['Nivel'].unique()),
    default=df['Nivel'].unique()
)

# Filtro por Clasificación Ministerio
selected_clasificacion = st.sidebar.multiselect(
    'Clasificación Ministerio',
    options=sorted(df['Clasificacion_Ministerio'].unique()),
    default=df['Clasificacion_Ministerio'].unique()
)

# Filtro por Relación
selected_relacion = st.sidebar.multiselect(
    'Relación',
    options=sorted(df['Relación'].unique()),
    default=df['Relación'].unique()
)

# Filtro por Mes
# Ordenar meses cronológicamente
meses_ordenados = df.sort_values('Mes_Num')['Mes'].unique()
selected_mes = st.sidebar.multiselect(
    'Mes',
    options=meses_ordenados,
    default=list(meses_ordenados)
)

# --- Aplicar filtros al DataFrame ---
df_filtered = df[
    df['Gerencia'].isin(selected_gerencia) &
    df['Nivel'].isin(selected_nivel) &
    df['Clasificacion_Ministerio'].isin(selected_clasificacion) &
    df['Relación'].isin(selected_relacion) &
    df['Mes'].isin(selected_mes)
]

# --- Título del Dashboard ---
st.title('📊 Dashboard de Masa Salarial 2025')
st.markdown("Análisis interactivo de los costos de la mano de obra de la compañía.")

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
    
st.markdown("---") # Separador visual

# --- Visualizaciones y Datos ---
st.header("Detalle de Datos Filtrados")

# Mensaje si no hay datos
if df_filtered.empty:
    st.warning("No hay datos que coincidan con los filtros seleccionados.")
else:
    # Gráfico de Evolución Mensual (Ejemplo)
    st.subheader("Evolución de la Masa Salarial Mensual")
    
    # Agrupar datos por mes para el gráfico
    masa_mensual = df_filtered.groupby('Mes_Num').agg({'Total Mensual': 'sum'}).reset_index()
    masa_mensual = masa_mensual.sort_values('Mes_Num')
    
    # Mapear de nuevo a nombres de mes para etiquetas correctas
    meses_es_map = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun', 
                    7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}
    masa_mensual['Mes'] = masa_mensual['Mes_Num'].map(meses_es_map)
    
    chart = alt.Chart(masa_mensual).mark_line(
        point=True,
        strokeWidth=3
    ).encode(
        x=alt.X('Mes_Num:O', title='Mes', axis=alt.Axis(labelExpr="datum.label")), # Ordena por número pero muestra nombre
        y=alt.Y('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0f')),
        tooltip=[
            alt.Tooltip('Mes:N', title='Mes'),
            alt.Tooltip('Total Mensual:Q', title='Masa Salarial', format='$,.0f')
        ]
    ).properties(
        height=300
    ).configure_view(
        stroke=None
    ).configure_point(
        size=100
    ).transform_calculate(
        label='"Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"[datum.Mes_Num-1]'
    )

    st.altair_chart(chart, use_container_width=True)

    # Tabla con datos filtrados
    st.subheader("Tabla de Datos")
    st.dataframe(df_filtered, use_container_width=True)
