import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
from fpdf import FPDF
import numpy as np
import time # Importar la librería time para la animación

# --- Configuración de la página ---
st.set_page_config(layout="wide")

# --- CSS Personalizado ---
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
</style>
""", unsafe_allow_html=True)


# --- Formato de Números ---
custom_format_locale = {
    "decimal": ",", "thousands": ".", "grouping": [3], "currency": ["$", ""]
}
alt.renderers.set_embed_options(formatLocale=custom_format_locale)

def format_number_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    s = f"{num:,.2f}"
    return s.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

def format_integer_es(num):
    if pd.isna(num) or not isinstance(num, (int, float, np.number)): return ""
    s = f"{int(num):,}"
    return s.replace(",", ".")

# --- INICIO: FUNCIÓN PARA MÉTRICAS ANIMADAS ---
def animated_metric(container, label, new_value, session_key, formatter_func, prefix=""):
    """
    Muestra una métrica con una animación de recuento ascendente/descendente.
    """
    # Inicializa el estado si no existe
    if session_key not in st.session_state:
        st.session_state[session_key] = new_value

    old_value = st.session_state[session_key]
    placeholder = container.empty()

    if new_value != old_value:
        steps = 20
        sleep_time = 0.02
        step_diff = (new_value - old_value) / steps

        for i in range(steps + 1):
            current_value = old_value + (step_diff * i)
            formatted_value = f"{prefix}{formatter_func(current_value)}"
            placeholder.metric(label, formatted_value)
            time.sleep(sleep_time)
    else:
        formatted_value = f"{prefix}{formatter_func(new_value)}"
        placeholder.metric(label, formatted_value)
    
    st.session_state[session_key] = new_value
# --- FIN: FUNCIÓN PARA MÉTRICAS ANIMADAS ---


# --- Funciones de Exportación ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def to_pdf(df, periodo):
    periodo_str = ", ".join(periodo)
    html_table = df.to_html(index=False, border=0)
    html_content = f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><style>
        body {{ font-family: "Arial", sans-serif; }} h2 {{ text-align: center; }}
        h3 {{ text-align: center; font-weight: normal; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 6px 5px; text-align: left; border: 1px solid #dddddd; font-size: 9px; }}
        thead th {{ background-color: #f2f2f2; font-size: 10px; font-weight: bold; }}
    </style></head><body><h2>Reporte Resumido de Datos</h2><h3>Período: {periodo_str}</h3>{html_table}</body></html>
    """
    pdf = FPDF(orientation='L', unit='mm', format='A3')
    pdf.add_page()
    pdf.write_html(html_content)
    return bytes(pdf.output())

# --- Carga de Datos ---
@st.cache_data
def load_data(url):
    df = pd.read_excel(url, sheet_name='masa_salarial', header=0, engine='openpyxl')
    df.columns = [str(col).strip() for col in df.columns]
    if 'Unnamed: 0' in df.columns: df = df.drop(columns=['Unnamed: 0'])
    if 'Período' not in df.columns:
        st.error("Error Crítico: La columna 'Período' no se encuentra.")
        return pd.DataFrame()
    df['Período'] = pd.to_datetime(df['Período'], errors='coerce')
    df.dropna(subset=['Período'], inplace=True)
    df['Mes_Num'] = df['Período'].dt.month.astype(int)
    meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df['Mes'] = df['Mes_Num'].map(meses_es)
    if 'Ceco' in df.columns: df['Ceco'] = pd.to_numeric(df['Ceco'], errors='coerce').astype('Int64')
    if 'Dotación' in df.columns: df['Dotación'] = pd.to_numeric(df['Dotación'], errors='coerce').fillna(0).astype(int)
    if 'Nro. de Legajo' in df.columns: df['Nro. de Legajo'] = pd.to_numeric(df['Nro. de Legajo'], errors='coerce').astype('Int64')
    df.rename(columns={'Clasificación Ministerio de Hacienda': 'Clasificacion_Ministerio'}, inplace=True)
    key_filter_columns = ['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación']
    df.dropna(subset=key_filter_columns, inplace=True)
    for col in key_filter_columns:
        if col in df.columns: df[col] = df[col].astype(str).str.strip()
    df.reset_index(drop=True, inplace=True)
    return df

FILE_URL = "https://raw.githubusercontent.com/Tincho2002/masa_salarial_2025/main/masa_salarial_2025.xlsx"
df = load_data(FILE_URL)

if df.empty:
    st.error("La carga de datos detallados ha fallado. El dashboard no puede continuar.")
    st.stop()
    
st.title('📊 Dashboard de Masa Salarial 2025')
st.markdown("Análisis interactivo de los costos de la mano de obra de la compañía.")
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
df_filtered = df[df['Gerencia'].isin(selected_gerencia) & df['Nivel'].isin(selected_nivel) & df['Clasificacion_Ministerio'].isin(selected_clasificacion) & df['Relación'].isin(selected_relacion) & df['Mes'].isin(selected_mes)].copy()

# --- Cálculo de KPIs ---
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

# --- APLICACIÓN DE MÉTRICAS ANIMADAS ---
animated_metric(col1, "Masa Salarial Total (Período)", total_masa_salarial, "masa_salarial_total", format_number_es, prefix="$")
animated_metric(col2, f"Empleados ({latest_month_name})", cantidad_empleados, "cantidad_empleados", lambda x: f"{int(x):,}".replace(",", "."), prefix="")
animated_metric(col3, "Costo Medio por Empleado (Período)", costo_medio, "costo_medio", format_number_es, prefix="$")

st.markdown("---")
if df_filtered.empty:
    st.warning("No hay datos que coincidan con los filtros seleccionados.")
else:
    # El resto del código de los gráficos y tablas permanece exactamente igual...
    # (se omite por brevedad, ya que no ha cambiado)
    st.subheader("Evolución Mensual de la Masa Salarial")
    col_chart1, col_table1 = st.columns([2, 1])
    masa_mensual = df_filtered.groupby('Mes').agg({'Total Mensual': 'sum', 'Mes_Num': 'first'}).reset_index().sort_values('Mes_Num')
    
    y_domain = [0, 1] 
    if not masa_mensual.empty:
        min_val = masa_mensual['Total Mensual'].min()
        max_val = masa_mensual['Total Mensual'].max()
        padding = (max_val - min_val) * 0.2
        y_domain = [min_val - padding, max_val + padding]
        if y_domain[0] < 0 and min_val >= 0: y_domain[0] = 0
    y_scale = alt.Scale(domain=y_domain)

    chart_height1 = (len(masa_mensual) + 1) * 35 + 3
    with col_chart1:
        base_chart1 = alt.Chart(masa_mensual).transform_window(
            total_sum='sum(Total Mensual)'
        ).transform_calculate(
            percentage="datum['Total Mensual'] / datum.total_sum",
            label_text="format(datum['Total Mensual'] / 1000000000, ',.2f') + 'G (' + format(datum.percentage, '.1%') + ')'"
        )
        line = base_chart1.mark_line(point=True, strokeWidth=3).encode(
            x=alt.X('Mes:N', sort=meses_ordenados, title='Mes'), 
            y=alt.Y('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s'), scale=y_scale), 
            tooltip=[alt.Tooltip('Mes:N'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
        )
        text = base_chart1.mark_text(align='center', baseline='bottom', dy=-10).encode(
            x=alt.X('Mes:N', sort=meses_ordenados), y=alt.Y('Total Mensual:Q', scale=y_scale), text='label_text:N'
        )
        line_chart = (line + text).properties(height=chart_height1, padding={'top': 35, 'left': 5, 'right': 5, 'bottom': 5}).configure(background='transparent').configure_view(fill='transparent')
        st.altair_chart(line_chart, use_container_width=True)
    with col_table1:
        masa_mensual_display = masa_mensual[['Mes', 'Total Mensual']].copy()
        if not masa_mensual_display.empty:
            total_row = pd.DataFrame([{'Mes': 'Total', 'Total Mensual': masa_mensual_display['Total Mensual'].sum()}])
            masa_mensual_display = pd.concat([masa_mensual_display, total_row], ignore_index=True)
        st.dataframe(masa_mensual_display.style.format({"Total Mensual": lambda x: f"${format_number_es(x)}"}).set_properties(subset=["Total Mensual"], **{'text-align': 'right'}), hide_index=True, use_container_width=True, height=chart_height1)
    
    st.write("")
    col_dl_1, col_dl_2 = st.columns(2)
    with col_dl_1:
        st.download_button(label="📥 Descargar CSV", data=masa_mensual_display.to_csv(index=False).encode('utf-8'), file_name='evolucion_mensual.csv', mime='text/csv', use_container_width=True)
    with col_dl_2:
        st.download_button(label="📥 Descargar Excel", data=to_excel(masa_mensual_display), file_name='evolucion_mensual.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)

    # ... (El resto del código sigue aquí sin cambios) ...
    # (Rest of the original code for charts and tables follows here)
