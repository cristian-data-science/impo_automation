import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import plotly.express as px
import plotly.graph_objs as go
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import io


from funciones import *
from streamlit.components.v1 import html
from streamlit_option_menu import option_menu
from st_aggrid import AgGrid, ColumnsAutoSizeMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from streamlit_lottie import st_lottie



st.set_page_config(page_title="Impo Auto App", layout="wide")

#variables globales
ias_df_sum_global = None

def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


def main():
    col1 = st.sidebar
    col2, col3 = st.columns((4, 1))

    col2.title("Impo Automation App")
    col2.markdown("""
    Esta app automatiza el proceso de procesamiento de facturas de importación corrigiendo al costo real y ejecuta un post procesado de la data para cargarla al ERP
    """)

    with st.sidebar:
        selected = option_menu("Main Menu", ["Home", 'Carga de datos', 'Insights', 'Descarga de resultados'],
                               icons=['house', 'bi bi-upload', 'bi bi-file-bar-graph', 'bi bi-download'],
                               menu_icon="cast", default_index=0)


    if "ias_df_sum_global" not in st.session_state:
        st.session_state.ias_df_sum_global = None

    if selected not in ["Carga de datos", "Insights", "Descarga de resultados"]:
        show_home(col1, col2)

    if selected == "Carga de datos":
        show_carga_de_datos(col1, col2)

    if selected == "Insights" and st.session_state.ias_df_sum_global is not None:
        show_insights(col1, col2)

    if selected == "Descarga de resultados":
        show_descarga_de_resultados(col1, col2)

    hide_st_style = """
                <style>
                footer {visibility: hidden;}
    ;}
                </style>
                """
    st.markdown(hide_st_style, unsafe_allow_html=True)


def show_home(col1, col2):
    loti1 = 'https://assets10.lottiefiles.com/private_files/lf30_ig1wfilw.json'
    lot1 = load_lottie_url(loti1)
    with col1:
        st_lottie(lot1, key="loti1", height=200, width=280)

    loti2 = 'https://assets7.lottiefiles.com/packages/lf20_lphquaqr.json'
    lot2 = load_lottie_url(loti2)
    with col2:
        st_lottie(lot2, key="loti2")  # ,height=74, width=200)


def show_carga_de_datos(col1, col2):
    global ias_df_sum_global
    with col1:
        st.sidebar.markdown("Carga de facturas en pdf e international account sales en excel")

    loti1 = 'https://assets10.lottiefiles.com/private_files/lf30_ig1wfilw.json'
    lot1 = load_lottie_url(loti1)
    with col1:
        st_lottie(lot1, key="loti1", height=200, width=280)    

    with col2:
        st.markdown("### Carga de datos")
        col_ias,col_facturas  = st.columns(2)
        pdf_bytes = None

        with col_ias:
            upload_ias = st.file_uploader("Subir IAS", type=["xls", "xlsx", "csv"], key="pdf", help="Cargue el archivo IAS en formato Excel o CSV.")
            if upload_ias:
                try:
                    st.success("IAS subidos exitosamente.")
                    # Leer el archivo IAS de Excel y guardar los datos en un DataFrame # archivo funciones.py
                    ias_df_sum = procesar_ias_excel(upload_ias)
                    st.session_state.ias_df_sum_global = ias_df_sum
                except KeyError:
                    st.error("El formato del IAS no es correcto.")
                

        with col_facturas:
            upload_facturas = st.file_uploader("Subir facturas", type=["pdf"], accept_multiple_files=True, key="ias", help="Cargue las facturas en formato PDF.")
            if upload_facturas:
                st.success("Facturas subidas y unificadas correctamente.")
                
                fusionar_pdfs(upload_facturas)
                archivo_salida = "unificado.pdf"

                with open(archivo_salida, "rb") as f:
                    pdf_bytes = f.read()

        if pdf_bytes:
            st.download_button(
                label="Descargar unificado.pdf",
                data=pdf_bytes,
                file_name="unificado.pdf",
                mime="application/pdf"
            )
            

            
            # Configurar y mostrar AgGrid con el DataFrame
            #grid_options_builder = GridOptionsBuilder.from_dataframe(ias_df_sum)
            #grid_options_builder.configure_default_column(groupable=True, filter=True, sortable=True, resizable=True)
            #grid_options = grid_options_builder.build()
            #AgGrid(ias_df_sum, gridOptions=grid_options)

           

def show_insights(col1, col2):
    global ias_df_sum_global

    loti1 = 'https://assets10.lottiefiles.com/private_files/lf30_ig1wfilw.json'
    lot1 = load_lottie_url(loti1)
    with col1:
        st_lottie(lot1, key="loti1", height=200, width=280)

    with col2:
        st.sidebar.markdown("Data analytics de las importaciones")
        archivo_pdf = "unificado.pdf"
        contenido_pdf = extraer_texto_pdf(archivo_pdf)

        
        sku_df = pd.DataFrame(columns=['po', 'Style', 'Color', 'Size', 'sku', 'Qty', 'Unit Cost'])

        sku_matrix_sum, expanded_df = procesar_datos_pdf(contenido_pdf)
        #print(result)
        result = sku_matrix_sum.reset_index()
        sku_df = sku_df.append(expanded_df, ignore_index=True)
        #AgGrid(result)

        ias_df_sum = st.session_state.ias_df_sum_global
        sku_matrix_sum = result
        

        sku_matrix_sum = sku_matrix_sum.reset_index()
        sku_matrix_sum['po'] = sku_matrix_sum['po'].astype('int64')

        ias_df_sum['po'] = ias_df_sum['po'].astype('int64')
        

        # Realizar un merge entre sku_matrix_sum e ias_df_sum utilizando la columna 'po'
        merged_df = sku_matrix_sum.merge(ias_df_sum, on='po',how='left')
        merged_df['diferencias'] = merged_df['total_cost_pdf'] - merged_df['costo_IAS']

        # Redondear la columna 'diferencias' a dos decimales
        merged_df['diferencias'] = merged_df['diferencias'].round(2)

        # Ordenar el DataFrame de mayor a menor según la columna 'diferencias'
        merged_df = merged_df.sort_values('diferencias', ascending=False)
        merged_df = merged_df.drop(columns=['index'])

        # Eliminar las columnas 'level_0' e 'index'
        #merged_df = merged_df.drop(columns=['level_0', 'index'])
        merged_df = merged_df.reset_index(drop=True)
        merged_df = merged_df[['po','total_cost_pdf','costo_IAS','diferencias']]
        unique_po_count = merged_df['po'].nunique()


        st.markdown(f"**Las PO's identificadas en las facturas subidas son: {unique_po_count}**")

        # Contar cuántas PO de ias_df_sum están contenidas en sku_matrix_sum
        po_count_ias_in_sku = ias_df_sum['po'].isin(sku_matrix_sum['po']).sum()

        # Mostrar el conteo de PO de ias_df_sum contenidas en sku_matrix_sum
        st.markdown(f"**Las PO's de IAS contenidas en las facturas subidas son: {po_count_ias_in_sku}**")
        
        # Agregar botón para descargar merged_df como archivo de Excel
        st.markdown("## Diferencias de costo por PO's")
        towrite = io.BytesIO()
        downloaded_file = merged_df.to_excel(towrite, index=False, header=True)
        towrite.seek(0)
        b64 = base64.b64encode(towrite.read()).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="merged_df.xlsx">Descargar diferencias como archivo de Excel</a>'
        st.markdown(href, unsafe_allow_html=True)

        grid_options_builder = GridOptionsBuilder.from_dataframe(merged_df)
        #grid_options_builder.configure_default_column(groupable=True, filter=True, sortable=True, resizable=True, columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW)
        grid_options_builder.configure_column("po", min_width=50)
        grid_options = grid_options_builder.build()
        AgGrid(merged_df, gridOptions=grid_options)
        
        
        
        #if st.session_state.ias_df_sum_global is not None:
            #AgGrid(st.session_state.ias_df_sum_global)
        #else:
            #st.write("No hay datos para mostrar.")
        
        

        # experimental grafico con matplolib
        # Filtrar las filas con diferencias distintas de 0

        filtered_merged_df = merged_df[merged_df['diferencias'] != 0]
        filtered_merged_df['po'] = filtered_merged_df['po'].astype(str)

        # Configurar los índices de las barras y el ancho de las barras
        bar_width = 0.25
        indices = np.arange(len(filtered_merged_df['po']))

        # Crear las barras para total_cost_pdf y costo_IAS
        plt.bar(indices, filtered_merged_df['total_cost_pdf'], bar_width, label='Total Cost PDF', color='blue')
        plt.bar(indices + bar_width, filtered_merged_df['costo_IAS'], bar_width, label='Costo IAS', color='red')

        # Configurar las etiquetas y leyendas del gráfico
        plt.xlabel('Purchase Order')
        plt.ylabel('Costo')
        plt.title('Diferencias del costo de factura y costo del IAS por Purchase Order')
        plt.xticks(indices + bar_width / 2, filtered_merged_df['po'], rotation=45)
        plt.legend()

        # Ajustar el espacio entre el borde inferior y el gráfico para evitar que las etiquetas se corten
        plt.subplots_adjust(bottom=0.2)

        # Mostrar el gráfico en Streamlit
        st.pyplot(plt)




def show_descarga_de_resultados(col1, col2):
    with col1:
        st.sidebar.markdown("Purchase Order Lines y Manual Invoice")
    
    loti1 = 'https://assets10.lottiefiles.com/private_files/lf30_ig1wfilw.json'
    lot1 = load_lottie_url(loti1)
    with col1:
        st_lottie(lot1, key="loti1", height=200, width=280)

    with col2:

        # llamando a función para tener los df en este espacio 
        sku_df = pd.DataFrame(columns=['po', 'Style', 'Color', 'Size', 'sku', 'Qty', 'Unit Cost'])
        archivo_pdf = "unificado.pdf"
        contenido_pdf = extraer_texto_pdf(archivo_pdf)
        sku_matrix_sum, expanded_df = procesar_datos_pdf(contenido_pdf)
        #print(result)
        result = sku_matrix_sum.reset_index()
        sku_df = sku_df.append(expanded_df, ignore_index=True)

        # Botones para armar purchase order 
        # Ingresar PAT
        st.markdown("### Ingresar datos para construir Purchase order lines V2")

        # Crear 3 columnas
        col1, col2, col3 = st.columns(3)

        # Ingresar PAT en la primera columna
        pat = col1.text_input("Ingresar PAT:", value="PAT-")

        # Estado de inventario en la segunda columna
        status_options = ["BLOQ-RECEP", "Disponible"]
        status = col2.radio("Estado de inventario:", status_options)

        # Almacén en la tercera columna
        warehouse_options = ["CD", "ZONAFRANCA"]
        warehouse = col3.radio("Almacén:", warehouse_options)





        if st.button("Generar Purchase order lines V2"):

            
            new_df = purchase_construct(sku_df, pat, status, warehouse)

            # Filtrar las filas donde 'ORDEREDPURCHASEQUANTITY' no sea 0 ni vacío
            new_df = new_df.loc[new_df['ORDEREDPURCHASEQUANTITY'] != 0].dropna(subset=['ORDEREDPURCHASEQUANTITY'])

            # Muestra el nuevo DataFrame en la interfaz de Streamlit
            st.write(new_df)
            

            summary_df = pd.DataFrame(columns=["po's a cargar", "unidades a cargar", "Costo total"])

            # Calcular los valores necesarios
            unique_po_count = new_df['CUSTOMERREFERENCE'].nunique()
            total_units = new_df['ORDEREDPURCHASEQUANTITY'].sum()
            
            # Calcular el costo total multiplicando el costo por la cantidad
            new_df['line_cost'] = new_df['ORDEREDPURCHASEQUANTITY'] * new_df['PURCHASEPRICE']
            total_cost = new_df['line_cost'].sum()
            new_df = new_df.drop(columns=['line_cost'])

            # agregar tabla de resumen antes de descarga
            summary_df = summary_df.append({
                "po's a cargar": unique_po_count,
                "unidades a cargar": total_units,
                "Costo total": total_cost
            }, ignore_index=True)

            # Mostrar el nuevo DataFrame en la aplicación
            summary_df = summary_df.reset_index(drop=True)
            st.markdown("### Totales de Purchase order")
            st.write(summary_df)

            
            # Crear datos de descarga de Excel
            excel_download_data = dataframe_to_excel_download(new_df, filename="Purchase order lines V2.xlsx")

            with col2:
                # Agregar botón de descarga
                st.download_button(
                    label="Descargar Purchase order lines V2",
                    data=excel_download_data,
                    file_name="Purchase order lines V2.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        st.markdown("### Totales de factura comercial")
        invoice_total_lines = extract_invoice_data(contenido_pdf)    
        st.write(invoice_total_lines)
        sum_count = invoice_total_lines['Invoice_total'].sum()
        st.markdown(f"**El total de todas las facturas es: {sum_count}**")    
if __name__ == "__main__":
    main()
