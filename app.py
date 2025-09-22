import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
from fpdf import FPDF
import numpy as np

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


# --- INICIO CORRECCIÓN 1: Formato de Números ---

# Define una configuración regional para que los gráficos de Altair usen
# punto para miles y coma para decimales.
custom_format_locale = {
    "decimal": ",",
    "thousands": ".",
    "grouping": [3],
    "currency": ["$", ""]
}
# Registra la configuración para que todos los gráficos la usen.
alt.renderers.set_embed_options(formatLocale=custom_format_locale)


def format_number_es(num):
    """
    Formatea un número al estilo español (puntos para miles, coma para decimales).
    """
    if pd.isna(num) or not isinstance(num, (int, float, np.number)):
        return ""
    # Formatea a un string con dos decimales, usando el estándar de Python (coma de miles, punto decimal)
    s = f"{num:,.2f}"
    # Intercambia los separadores
    return s.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

# --- FIN CORRECCIÓN 1 ---


# --- FUNCIONES DE EXPORTACIÓN ---

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def to_pdf(df, periodo):
    periodo_str = ", ".join(periodo)
    html_table = df.to_html(index=False, border=0)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: "Arial", sans-serif; }}
        h2 {{ text-align: center; }}
        h3 {{ text-align: center; font-weight: normal; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 6px 5px; text-align: left; border: 1px solid #dddddd; font-size: 9px; }}
        thead th {{ background-color: #f2f2f2; font-size: 10px; font-weight: bold; }}
    </style>
    </head>
    <body>
        <h2>Reporte Resumido de Datos</h2>
        <h3>Período: {periodo_str}</h3>
        {html_table}
    </body>
    </html>
    """
    pdf = FPDF(orientation='L', unit='mm', format='A3')
    pdf.add_page()
    pdf.write_html(html_content)
    return bytes(pdf.output())

# --- CARGA DE DATOS ---
@st.cache_data
def load_data(url):
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
    meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df['Mes'] = df['Mes_Num'].map(meses_es)
    if 'Ceco' in df.columns:
        df['Ceco'] = pd.to_numeric(df['Ceco'], errors='coerce').astype('Int64')
    if 'Dotación' in df.columns:
        df['Dotación'] = pd.to_numeric(df['Dotación'], errors='coerce').fillna(0).astype(int)
    if 'Nro. de Legajo' in df.columns:
         df['Nro. de Legajo'] = pd.to_numeric(df['Nro. de Legajo'], errors='coerce').astype('Int64')
    df.rename(columns={'Clasificación Ministerio de Hacienda': 'Clasificacion_Ministerio'}, inplace=True)
    key_filter_columns = ['Gerencia', 'Nivel', 'Clasificacion_Ministerio', 'Relación']
    df.dropna(subset=key_filter_columns, inplace=True)
    for col in key_filter_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    df.reset_index(drop=True, inplace=True)
    return df

# --- INICIO CORRECCIÓN 2: Eliminar carga de datos de resumen estático ---
# La función load_summary_data() y su llamada se eliminan.
# El resumen se generará dinámicamente a partir de los datos filtrados más adelante.
# --- FIN CORRECCIÓN 2 ---

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

# Aplicar formato de número corregido a las métricas
col1.metric("Masa Salarial Total (Período)", f"${format_number_es(total_masa_salarial)}")
col2.metric(f"Empleados ({latest_month_name})", f"{int(cantidad_empleados)}")
col3.metric("Costo Medio por Empleado (Período)", f"${format_number_es(costo_medio)}")

st.markdown("---")
if df_filtered.empty:
    st.warning("No hay datos que coincidan con los filtros seleccionados.")
else:
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
        # Aplicar formato de número corregido a la tabla
        st.dataframe(masa_mensual_display.style.format({"Total Mensual": lambda x: f"${format_number_es(x)}"}).set_properties(subset=["Total Mensual"], **{'text-align': 'right'}), hide_index=True, use_container_width=True, height=chart_height1)
    st.write("")
    st.markdown("---")
    st.subheader("Masa Salarial por Gerencia")
    col_chart2, col_table2 = st.columns([3, 2])
    gerencia_data = df_filtered.groupby('Gerencia')['Total Mensual'].sum().sort_values(ascending=False).reset_index()
    chart_height2 = (len(gerencia_data) + 1) * 35 + 3
    with col_chart2:
        base_chart2 = alt.Chart(gerencia_data).transform_window(
            total_sum='sum(Total Mensual)'
        ).transform_calculate(
            percentage="datum['Total Mensual'] / datum.total_sum",
            label_text="format(datum['Total Mensual'] / 1000000000, ',.2f') + 'G (' + format(datum.percentage, '.1%') + ')'"
        )
        bar = base_chart2.mark_bar().encode(
            x=alt.X('Total Mensual:Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
            y=alt.Y('Gerencia:N', sort='-x', title=None, axis=alt.Axis(labelLimit=120)),
            tooltip=[alt.Tooltip('Gerencia:N', title='Gerencia'), alt.Tooltip('Total Mensual:Q', format='$,.2f')]
        )
        text = base_chart2.mark_text(align='left', baseline='middle', dx=5).encode(
            x='Total Mensual:Q', y=alt.Y('Gerencia:N', sort='-x'), text='label_text:N', color=alt.value('black')
        )
        bar_chart = (bar + text).properties(height=chart_height2, padding={'top': 25, 'left': 5, 'right': 5, 'bottom': 5}).configure(background='transparent').configure_view(fill='transparent')
        st.altair_chart(bar_chart, use_container_width=True)
    with col_table2:
        gerencia_data_display = gerencia_data.copy()
        if not gerencia_data_display.empty:
            total_row = pd.DataFrame([{'Gerencia': 'Total', 'Total Mensual': gerencia_data_display['Total Mensual'].sum()}])
            gerencia_data_display = pd.concat([gerencia_data_display, total_row], ignore_index=True)
        # Aplicar formato de número corregido a la tabla
        st.dataframe(gerencia_data_display.style.format({"Total Mensual": lambda x: f"${format_number_es(x)}"}).set_properties(subset=["Total Mensual"], **{'text-align': 'right'}), hide_index=True, use_container_width=True, height=chart_height2)
    st.write("")
    st.markdown("---")
    st.subheader("Distribución por Clasificación")
    col_chart3, col_table3 = st.columns([2, 1])
    clasificacion_data = df_filtered.groupby('Clasificacion_Ministerio')['Total Mensual'].sum().reset_index()
    
    with col_chart3:
        clasificacion_data = clasificacion_data.sort_values('Total Mensual', ascending=False)
        total = clasificacion_data['Total Mensual'].sum()
        if total > 0:
            clasificacion_data['Porcentaje'] = (clasificacion_data['Total Mensual'] / total)
        else:
            clasificacion_data['Porcentaje'] = 0

        base_chart = alt.Chart(clasificacion_data).encode(
            theta=alt.Theta(field="Total Mensual", type="quantitative", stack=True),
            color=alt.Color(field="Clasificacion_Ministerio", type="nominal", title="Clasificación",
                            sort=alt.EncodingSortField(field="Total Mensual", order="descending")),
            tooltip=[
                alt.Tooltip('Clasificacion_Ministerio', title='Clasificación'),
                alt.Tooltip('Total Mensual', format='$,.2f'),
                alt.Tooltip('Porcentaje', format='.2%')
            ]
        )
        pie = base_chart.mark_arc(innerRadius=70, outerRadius=110)
        text = base_chart.mark_text(radius=140, size=12, fill='black').encode(
            text=alt.condition(
                alt.datum.Porcentaje > 0.03,
                alt.Text('Porcentaje:Q', format='.1%'),
                alt.value('')
            )
        )
        final_chart = (pie + text).properties(height=400).configure_view(stroke=None).configure(background='transparent')
        st.altair_chart(final_chart, use_container_width=True)

    with col_table3:
        table_data = clasificacion_data.rename(columns={'Clasificacion_Ministerio': 'Clasificación'})
        table_display_data = table_data[['Clasificación', 'Total Mensual']]
        if not table_display_data.empty:
            total_row = pd.DataFrame([{'Clasificación': 'Total', 'Total Mensual': table_display_data['Total Mensual'].sum()}])
            table_display_data = pd.concat([table_display_data, total_row], ignore_index=True)
        table_height = (len(table_display_data) + 1) * 35 + 3
        # Aplicar formato de número corregido a la tabla
        st.dataframe(table_display_data.copy().style.format({"Total Mensual": lambda x: f"${format_number_es(x)}"}).set_properties(subset=["Total Mensual"], **{'text-align': 'right'}), hide_index=True, use_container_width=True, height=table_height)
    st.write("")
    
    st.markdown("---")
    st.subheader("Masa Salarial por Concepto")
    concept_columns_to_pivot = [
        'Nómina General con Aportes', 'Antigüedad', 'Horas Extras', 'Cs. Sociales s/Remunerativos',
        'Cargas Sociales Antigüedad', 'Cargas Sociales Horas Extras', 'Nómina General sin Aportes',
        'Gratificación Única y Extraordinaria', 'Gastos de Representación', 'Gratificación por Antigüedad',
        'Gratificación por Jubilación', 'SAC Horas Extras', 'Cargas Sociales SAC Hextras', 'SAC Pagado',
        'Cargas Sociales s/SAC Pagado', 'Vacaciones Pagadas', 'Cargas Sociales s/Vac. Pagadas',
        'Asignaciones Familiares 1.4.', 'Total Mensual'
    ]
    concept_cols_present = [col for col in concept_columns_to_pivot if col in df_filtered.columns]

    if concept_cols_present:
        df_melted = df_filtered.melt(id_vars=['Mes', 'Mes_Num'], value_vars=concept_cols_present, var_name='Concepto', value_name='Monto')
        pivot_table = pd.pivot_table(df_melted, values='Monto', index='Concepto', columns='Mes', aggfunc='sum', fill_value=0)
        
        meses_en_datos = df_filtered[['Mes', 'Mes_Num']].drop_duplicates().sort_values('Mes_Num')['Mes'].tolist()
        if all(mes in pivot_table.columns for mes in meses_en_datos):
            pivot_table = pivot_table[meses_en_datos]

        pivot_table['Total general'] = pivot_table.sum(axis=1)
        pivot_table = pivot_table.reindex(concept_cols_present).dropna(how='all')
        
        # Aplicar formato de número corregido a la tabla pivote
        st.dataframe(
            pivot_table.style.format(formatter=lambda x: f"${format_number_es(x)}").set_properties(**{'text-align': 'right'}), 
            use_container_width=True
        )
    else:
        st.info("No hay datos de conceptos para mostrar con los filtros seleccionados.")

    st.markdown("---")
    st.subheader("Resumen por Concepto (SIPAF)")
    df_filtered.columns = df_filtered.columns.str.strip().str.replace(r"\s+", " ", regex=True)
    concept_columns_sipaf = [
        'Retribución Cargo 1.1.1', 'Antigüedad 1.1.3', 'Retribuciones Extraordinarias 1.3.1',
        'Contribuciones Patronales 1.3.3', 'SAC 1.3.2', 'SAC 1.1.4',
        'Contribuciones Patronales 1.1.6', 'Complementos 1.1.7', 'Asignaciones Familiares 1.4'
    ]
    sipaf_cols_present = []
    for col in df_filtered.columns:
        for expected in concept_columns_sipaf:
            if expected.lower().replace(".", "") in col.lower().replace(".", ""):
                sipaf_cols_present.append(col)
    
    if sipaf_cols_present:
        df_melted_sipaf = df_filtered.melt(id_vars=['Mes', 'Mes_Num'], value_vars=sipaf_cols_present, var_name='Concepto', value_name='Monto')
        pivot_table_sipaf = pd.pivot_table(df_melted_sipaf, values='Monto', index='Concepto', columns='Mes', aggfunc='sum', fill_value=0)
        meses_en_datos_sipaf = df_filtered[['Mes', 'Mes_Num']].drop_duplicates().sort_values('Mes_Num')['Mes'].tolist()
        for mes in meses_en_datos_sipaf:
            if mes not in pivot_table_sipaf.columns:
                pivot_table_sipaf[mes] = 0
        if all(mes in pivot_table_sipaf.columns for mes in meses_en_datos_sipaf):
            pivot_table_sipaf = pivot_table_sipaf[meses_en_datos_sipaf]
        pivot_table_sipaf['Total general'] = pivot_table_sipaf.sum(axis=1)
        pivot_table_sipaf = pivot_table_sipaf.dropna(how='all')
        if not pivot_table_sipaf.empty:
            total_row = pivot_table_sipaf.sum().rename('Total general')
            pivot_table_sipaf = pd.concat([pivot_table_sipaf, total_row.to_frame().T])
        # Aplicar formato de número corregido a la tabla pivote
        st.dataframe(
            pivot_table_sipaf.style.format(formatter=lambda x: f"${format_number_es(x)}").set_properties(**{'text-align': 'right'}),
            use_container_width=True
        )
    else:
        st.info("No hay datos de conceptos SIPAF para mostrar con los filtros seleccionados.")

    st.markdown("---")
    st.subheader("Tabla de Datos Detallados")
    df_display = df_filtered.copy().reset_index(drop=True)
    if not df_display.empty:
        st.markdown("##### Descargar datos")
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            st.download_button(label="📥 CSV (Tabla Completa)", data=df_display.to_csv(index=False).encode('utf-8'), file_name='datos_detallados.csv', mime='text/csv', use_container_width=True)
        with col_btn2:
            st.download_button(label="📥 Excel (Tabla Completa)", data=to_excel(df_display), file_name='datos_detallados.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
        with col_btn3:
            pdf_summary_cols = ['Período', 'Nro. de Legajo', 'Apellido y Nombres', 'Gerencia', 'Clasificacion_Ministerio', 'Total Mensual']
            existing_pdf_cols = [col for col in pdf_summary_cols if col in df_display.columns]
            df_pdf_raw = df_display[existing_pdf_cols]
            df_pdf_formatted = df_pdf_raw.copy()
            df_pdf_formatted['Período'] = df_pdf_formatted['Período'].dt.strftime('%Y-%m')
            # Aplicar formato de número corregido para el PDF
            df_pdf_formatted['Total Mensual'] = df_pdf_formatted['Total Mensual'].apply(lambda x: f"${format_number_es(x)}")
            st.download_button(label="📥 PDF (Resumen)", data=to_pdf(df_pdf_formatted, selected_mes), file_name='resumen_detallado.pdf', mime='application/pdf', use_container_width=True)
        
        st.write("")
        if 'page_number' not in st.session_state: st.session_state.page_number = 0
        PAGE_SIZE = 50
        total_rows = len(df_display)
        num_pages = (total_rows // PAGE_SIZE) + (1 if total_rows % PAGE_SIZE > 0 else 0)
        st.write(f"Mostrando **{PAGE_SIZE}** filas por página. Total de filas: **{total_rows}**.")
        prev_col, page_col, next_col = st.columns([2, 8, 2])
        if prev_col.button("⬅️ Anterior", use_container_width=True):
            if st.session_state.page_number > 0: st.session_state.page_number -= 1
        if next_col.button("Siguiente ➡️", use_container_width=True):
            if st.session_state.page_number < num_pages - 1: st.session_state.page_number += 1
        page_col.write(f"Página **{st.session_state.page_number + 1}** de **{num_pages}**")
        start_idx = st.session_state.page_number * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, total_rows)
        df_page = df_display.iloc[start_idx:end_idx]
        currency_columns = ['Total Sujeto a Retención', 'Vacaciones', 'Alquiler', 'Horas Extras', 'Nómina General con Aportes', 'Cs. Sociales s/Remunerativos', 'Cargas Sociales Ant.', 'IC Pagado', 'Vacaciones Pagadas', 'Cargas Sociales s/Vac. Pagadas', 'Retribución Cargo 1.1.1.', 'Antigüedad 1.1.3.', 'Retribuciones Extraordinarias 1.3.1.', 'Contribuciones Patronales', 'Gratificación por Antigüedad', 'Gratificación por Jubilación', 'Total No Remunerativo', 'SAC Horas Extras', 'Cargas Sociales SAC Hextras', 'SAC Pagado', 'Cargas Sociales s/SAC Pagado', 'Cargas Sociales Antigüedad', 'Nómina General sin Aportes', 'Gratificación Única y Extraordinaria', 'Gastos de Representación', 'Contribuciones Patronales 1.3.3.', 'S.A.C. 1.3.2.', 'S.A.C. 1.1.4.', 'Contribuciones Patronales 1.1.6.', 'Complementos 1.1.7.', 'Asignaciones Familiares 1.4.', 'Total Mensual']
        integer_columns = ['Nro. de Legajo', 'Dotación', 'Ceco']
        
        # Aplicar formato de número corregido a la tabla detallada
        currency_formatter = lambda x: f"${format_number_es(x)}"
        format_mapper = {col: currency_formatter for col in currency_columns if col in df_page.columns}
        for col in integer_columns:
            if col in df_page.columns: format_mapper[col] = "{:,.0f}".replace(",", ".") # Para enteros, solo cambiar separador de miles
        
        columns_to_align_right = [col for col in currency_columns + integer_columns if col in df_page.columns]
        st.dataframe(df_page.style.format(format_mapper, na_rep="").set_properties(subset=columns_to_align_right, **{'text-align': 'right'}), use_container_width=True, hide_index=True)

    # --- INICIO CORRECCIÓN 2: Sección de Resumen Anual dinámica ---
    st.markdown("---")
    st.subheader("Resumen de Evolución Anual (Datos Filtrados)")
    
    # Se genera la tabla pivote de resumen a partir del dataframe ya filtrado (df_filtered)
    summary_df_filtered = pd.pivot_table(
        df_filtered,
        values='Total Mensual',
        index=['Mes_Num', 'Mes'],
        columns='Clasificacion_Ministerio',
        aggfunc='sum',
        fill_value=0
    ).sort_index(level='Mes_Num').reset_index(level='Mes_Num', drop=True)

    summary_df_display = summary_df_filtered.reset_index().copy()
    
    if not summary_df_display.empty:
        # Agregar columna y fila de totales
        numeric_cols = summary_df_display.select_dtypes(include=np.number).columns
        if 'Total general' not in summary_df_display.columns and len(numeric_cols) > 0:
            summary_df_display['Total general'] = summary_df_display[numeric_cols].sum(axis=1)

        total_row = summary_df_display.select_dtypes(include=np.number).sum().rename('Total')
        summary_df_display = pd.concat([summary_df_display, total_row.to_frame().T], ignore_index=True)
        # Asegurarse de que el índice -1 (la nueva fila total) tenga la etiqueta 'Total'
        summary_df_display.iloc[-1, summary_df_display.columns.get_loc('Mes')] = 'Total'

        # Aplicar formato de número corregido a la tabla de resumen
        summary_currency_cols = [col for col in summary_df_display.columns if col != 'Mes' and pd.api.types.is_numeric_dtype(summary_df_display[col])]
        summary_format_mapper = {col: lambda x: f"${format_number_es(x)}" for col in summary_currency_cols}
        st.dataframe(summary_df_display.style.format(summary_format_mapper, na_rep="").set_properties(subset=summary_currency_cols, **{'text-align': 'right'}), use_container_width=True, hide_index=True)
        
        # Gráfico de barras apiladas con los datos filtrados
        summary_chart_data = summary_df_filtered.reset_index().melt(id_vars='Mes', var_name='Clasificacion', value_name='Masa Salarial')
        
        # El orden de los meses se toma de los datos filtrados para mantener la consistencia
        mes_sort_order = summary_chart_data['Mes'].dropna().unique().tolist()

        bar_chart = alt.Chart(summary_chart_data).mark_bar().encode(
            x=alt.X('Mes:N', sort=mes_sort_order, title='Mes'),
            y=alt.Y('sum(Masa Salarial):Q', title='Masa Salarial ($)', axis=alt.Axis(format='$,.0s')),
            color=alt.Color('Clasificacion:N', title='Clasificación'),
            tooltip=[alt.Tooltip('Mes:N'), alt.Tooltip('Clasificacion:N'), alt.Tooltip('sum(Masa Salarial):Q', format='$,.2f', title='Masa Salarial')]
        )
        
        text_labels = alt.Chart(summary_chart_data).transform_aggregate(
            total_masa_salarial='sum(Masa Salarial)',
            groupby=['Mes']
        ).mark_text(
            dy=-8,
            align='center',
            color='black'
        ).encode(
            x=alt.X('Mes:N', sort=mes_sort_order),
            y=alt.Y('total_masa_salarial:Q'),
            text=alt.Text('total_masa_salarial:Q', format='$,.2s')
        )
        
        summary_chart = (bar_chart + text_labels).properties(
            height=350, padding={'top': 25, 'left': 5, 'right': 5, 'bottom': 5}
        ).configure(
            background='transparent'
        ).configure_view(
            fill='transparent'
        )
        st.altair_chart(summary_chart, use_container_width=True)
    # --- FIN CORRECCIÓN 2 ---
