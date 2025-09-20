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
[data-testid="stMetric"], .stDataFrame, .st-emotion-cache-1n7693g {
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
    Carga y preprocesa los datos desde una URL de un archivo Excel.
    """
    try:
        # --- MÉTODO DE LECTURA ROBUSTO ---
        # 1. Leer el excel sin encabezado para tener control total
        df = pd.read_excel(url, sheet_name='masa_salarial', header=None, engine='openpyxl')
        
        # 2. Asignar explícitamente la segunda fila (índice 1) como los nombres de las columnas
        df.columns = df.iloc[1]
        
        # 3. Eliminar las filas superiores que no son datos (título y fila de encabezado original)
        df = df.drop([0, 1]).reset_index(drop=True)

        # --- Limpieza de nombres de columnas y datos ---
        # FORZAR a que todos los nombres de columna sean strings limpios.
        # Esto soluciona problemas con tipos mixtos (ej, nan) y espacios ocultos.
        df.columns = [str(col).strip() for col in df.columns]

        # La primera columna ahora es 'nan' (como string), la eliminamos.
        if 'nan' in df.columns:
            df = df.drop(columns=['nan'])

        # --- PREPROCESAMIENTO ---
        # Se verifica que la columna 'Período' exista antes de usarla
        if 'Período' not in df.columns:
            st.error("Error Crítico: La columna 'Período' no se encuentra. Revisa el archivo Excel.")
            st.info("Columnas encontradas por la aplicación (después de limpiar):")
            st.write(df.columns.tolist())
            return pd.DataFrame()

        df['Período'] = pd.to_datetime(df['Período'], errors='coerce')
        df['Mes_Num'] = df['Período'].dt.month
        
        meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
        df['Mes'] = df['Mes_Num'].map(meses_es)

        for col in ['Total Mensual', 'Dotación']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                st.error(f"Error Crítico: La columna requerida '{col}' no se encuentra en el archivo.")
                return pd.DataFrame()
        
        df.rename(columns={'Clasificación Ministerio de Hacienda': 'Clasificacion_Ministerio'}, inplace=True)

        for col in ['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación']:
             if col in df.columns:
                df[col] = df[col].astype(str).fillna('No Asignado')
             else:
                st.error(f"Error Crítico: La columna requerida '{col}' no se encuentra en el archivo.")
                return pd.DataFrame()
        
        return df
    except Exception as e:
        st.error(f"Ocurrió un error al cargar o procesar el archivo: {e}")
        return pd.DataFrame()

# --- Carga de datos ---
df = load_data(FILE_URL)

if df.empty:
    st.error("La carga de datos ha fallado. Por favor, revisa el error anterior y verifica la estructura del archivo Excel.")
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
cantidad_empleados = df_filtered['Dotación'].sum()
costo_medio = total_masa_salarial / cantidad_empleados if cantidad_empleados > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Masa Salarial Total", f"${total_masa_salarial:,.0f}")
col2.metric("Cantidad de Empleados (Dotación)", f"{cantidad_empleados:,.0f}")
col3.metric("Costo Medio por Empleado", f"${costo_medio:,.0f}")
    
st.markdown("---")

# --- Visualizaciones ---
if df_filtered.empty:
    st.warning("No hay datos que coincidan con los filtros seleccionados.")
else:
    st.subheader("Evolución Mensual de la Masa Salarial")
    masa_mensual = df_filtered.groupby('Mes').agg({'Total Mensual': 'sum', 'Mes_Num': 'first'}).reset_index().sort_values('Mes_Num')
    
    line_chart = alt.Chart(masa_mensual).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X('Mes:N', sort=meses_ordenados.tolist(), title='Mes'),
        y=alt.Y('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
        tooltip=[alt.Tooltip('Mes:N'), alt.Tooltip('Total Mensual:Q', format='$,.0f')]
    ).properties(height=350)
    st.altair_chart(line_chart, use_container_width=True)

    col_grafico1, col_grafico2 = st.columns(2)
    with col_grafico1:
        st.subheader("Masa Salarial por Gerencia")
        gerencia_data = df_filtered.groupby('Gerencia')['Total Mensual'].sum().reset_index()
        bar_chart = alt.Chart(gerencia_data).mark_bar().encode(
            x=alt.X('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
            y=alt.Y('Gerencia:N', sort='-x', title=None),
            tooltip=[alt.Tooltip('Gerencia:N'), alt.Tooltip('Total Mensual:Q', format='$,.0f')]
        ).properties(height=400)
        st.altair_chart(bar_chart, use_container_width=True)

    with col_grafico2:
        st.subheader("Distribución por Clasificación")
        clasificacion_data = df_filtered.groupby('Clasificacion_Ministerio')['Total Mensual'].sum().reset_index()
        donut_chart = alt.Chart(clasificacion_data).mark_arc(innerRadius=80).encode(
            theta=alt.Theta("Total Mensual:Q"),
            color=alt.Color("Clasificacion_Ministerio:N", title="Clasificación"),
            tooltip=[alt.Tooltip('Clasificacion_Ministerio:N'), alt.Tooltip('Total Mensual:Q', format='$,.0f')]
        ).properties(height=400)
        st.altair_chart(donut_chart, use_container_width=True)

    st.subheader("Tabla de Datos Detallados")
    st.dataframe(df_filtered, use_container_width=True)

