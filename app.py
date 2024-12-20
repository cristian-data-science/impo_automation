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
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
from gspread_pandas import Spread,Client
from datetime import datetime



from funciones import *
from streamlit.components.v1 import html
from streamlit_option_menu import option_menu
from st_aggrid import AgGrid, ColumnsAutoSizeMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from streamlit_lottie import st_lottie



st.set_page_config(page_title="Impo Auto App", layout="wide")

#variables globales
ias_df_sum_global = None
new_df = pd.DataFrame()

def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def reset_variables():
    global invoice_total_lines
    global total_adjustment_sum
    invoice_total_lines = None
    total_adjustment_sum = None

def main():
    col1 = st.sidebar
    col2, col3 = st.columns((4, 1))

    col2.title("Impo Automation App")
    col2.markdown("""
    Esta app automatiza el proceso de procesamiento de facturas de importación corrigiendo al costo real y ejecuta un post procesado de la data para cargarla al ERP
    """)

    with st.sidebar:
        selected = option_menu("Main Menu", ["Home", 'Carga de datos', 'Insights', 'Descarga de resultados', 'Envío de PL a EIT'],
                           icons=['house', 'bi bi-upload', 'bi bi-file-bar-graph', 'bi bi-download', 'bi bi-arrow-right-circle'],
                           menu_icon="cast", default_index=0)


    if "ias_df_sum_global" not in st.session_state:
        st.session_state.ias_df_sum_global = None

    if selected not in ["Carga de datos", "Insights", "Descarga de resultados","Envío de PL a EIT"]:
        show_home(col1, col2)

    if selected == "Carga de datos":
        show_carga_de_datos(col1, col2)

    if selected == "Insights" and st.session_state.ias_df_sum_global is not None:
        show_insights(col1, col2)

    if selected == "Descarga de resultados":
        show_descarga_de_resultados(col1, col2)

    if selected == "Envío de PL a EIT":
        show_envio_de_PL_a_EIT(col1, col2)

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
    reset_variables()
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
                    ias_df_sum
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
    reset_variables()
    global ias_df_sum_global

    loti1 = 'https://assets10.lottiefiles.com/private_files/lf30_ig1wfilw.json'
    lot1 = load_lottie_url(loti1)
    with col1:
        st_lottie(lot1, key="loti1", height=200, width=280)

    with col2:
        st.sidebar.markdown("Data analytics de las importaciones")
        archivo_pdf = "unificado.pdf"
        contenido_pdf = extraer_texto_pdf_con_plumber(archivo_pdf)

        
        sku_df = pd.DataFrame(columns=['po', 'Style', 'Color', 'Size', 'sku', 'Qty', 'Unit Cost'])

        sku_matrix_sum, expanded_df = procesar_datos_pdf(contenido_pdf)
        #print(result)
        result = sku_matrix_sum.reset_index()

        #sku_df = sku_df.append(expanded_df, ignore_index=True)
        # cambiar append por concat para evitar warnings en consola

        sku_df = pd.concat([sku_df, expanded_df], ignore_index=True)
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
    reset_variables()
    with col1:
        st.sidebar.markdown("Purchase Order Lines y Manual Invoice")
    
    loti1 = 'https://assets10.lottiefiles.com/private_files/lf30_ig1wfilw.json'
    lot1 = load_lottie_url(loti1)
    with col1:
        st_lottie(lot1, key="loti1", height=200, width=280)
    
    with col2:
        # Añadir el radio button para seleccionar la librería de extracción
        extraction_library = st.radio(
            "Seleccione la librería para extraer texto del PDF:",
            ('pdfplumber', 'PyPDF2'),
            index=0  # pdfplumber es la opción por defecto
        )
        
        # Inicializar el DataFrame
        sku_df = pd.DataFrame(columns=['po', 'Style', 'Color', 'Size', 'sku', 'Qty', 'Unit Cost'])
        archivo_pdf = "unificado.pdf"
        try:
            # Llamar a la función correspondiente según la selección del usuario
            if extraction_library == 'pdfplumber':
                contenido_pdf = extraer_texto_pdf_con_plumber(archivo_pdf)
            else:
                contenido_pdf = extraer_texto_pdf(archivo_pdf)
            
            if contenido_pdf:  # Verificando si contenido_pdf tiene datos antes de procesarlos
                sku_matrix_sum, expanded_df = procesar_datos_pdf(contenido_pdf)
                result = sku_matrix_sum.reset_index()

                #sku_df = sku_df.append(expanded_df, ignore_index=True)
                #cambiar append por concat
                sku_df = pd.concat([sku_df, expanded_df], ignore_index=True)

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
                warehouse_options = ["CD", "ZONAFRANCA", "BLOQUEADO"]
                warehouse = col3.radio("Almacén:", warehouse_options)


                if st.button("Generar Purchase order lines V2"):

                    global new_df
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

                    summary_df = pd.concat([summary_df, pd.DataFrame([{
                        "po's a cargar": unique_po_count,
                        "unidades a cargar": total_units,
                        "Costo total": total_cost
                    }])], ignore_index=True)
                                        
                    # Crear datos de descarga de Excel
                    excel_download_data = dataframe_to_excel_download(new_df, filename="Purchase order lines V2.xlsx")
        
                    # Agregar botón de descarga
                    st.download_button(
                        label="Descargar Purchase order lines V2",
                        data=excel_download_data,
                        file_name="Purchase order lines V2.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                    # Mostrar el nuevo DataFrame en la aplicación
                    summary_df = summary_df.reset_index(drop=True)
                    st.markdown("### Totales de Purchase order")
                    st.write(summary_df)

                    st.markdown("### Totales de factura comercial")
                    print("Contenido del PDF:")
                    for line in contenido_pdf:
                        print(f"'{line}'")

                    invoice_total_lines = 0
                    invoice_total_lines = extract_invoice_data(contenido_pdf)    
                    st.write(invoice_total_lines)
                    sum_count = round(invoice_total_lines['Invoice_total'].sum(), 2)
                    st.markdown(f"**El total de todas las facturas es: ${sum_count}**") 


                    #st.warning('This is a warning', icon="⚠️")   

                    total_adjustment_sum = 0
                    total_adjustment_sum = round(invoice_total_lines['Total_adjustment'].sum(), 2)

                    # Comprobar si la suma es mayor a 0 y mostrar el mensaje de advertencia
                    if total_adjustment_sum > 0:
                        st.warning(f'⚠️ Hay ${total_adjustment_sum} USD de handlings fees en las facturas comerciales')


                        col1, col2 = st.columns(2)
                        with col1:
                                                      
                            st.info("Prorrateo de siempre: Sumar al precio la división del handling fee por el total de unidades")
                            formula_v1 = r"Price'_i = Price_i + \frac{HF}{U}" # Fórmula para el prorrateo v1
                            st.markdown(f'$$ {formula_v1} $$')
                            # Actualizar el valor de la columna 'PURCHASEPRICE'
                            new_dfprov1 = new_df.copy()
                            new_dfprov1['PURCHASEPRICE'] = new_dfprov1['PURCHASEPRICE'].astype(float)
                            new_dfprov1['ORDEREDPURCHASEQUANTITY'] = new_dfprov1['ORDEREDPURCHASEQUANTITY'].astype(float)
                            total_order_qty = new_dfprov1['ORDEREDPURCHASEQUANTITY'].sum()
                            new_dfprov1['PURCHASEPRICE'] = new_dfprov1['PURCHASEPRICE'] + (total_adjustment_sum / total_order_qty)
                            
                            excel_download_data_prov1 = dataframe_to_excel_download(new_dfprov1, filename="Purchase order lines V2.xlsx")
                            
                            st.download_button(
                                label="Descargar Purchase order Prorrateado V1",
                                data=excel_download_data_prov1,
                                file_name="Purchase order lines V2.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            )                        
                        
                        with col2:

                            st.info("Prorrateo ponderado: Dividir cada p*q por su suma total, multiplicar por handling fee y sumar al precio")
                            formula_v2 = r"Price'_i = Price_i + HF \cdot \left(\frac{Price_i \cdot QTY_i}{\sum_{j=1}^{n} Price_j \cdot QTY_j}\right)"  # Fórmula para el prorrateo v2
                            st.markdown(f'$$ {formula_v2} $$')
                            new_dfprov2 = new_df.copy()
                            new_dfprov2['PURCHASEPRICE'] = new_dfprov2['PURCHASEPRICE'].astype(float)
                            new_dfprov2['ORDEREDPURCHASEQUANTITY'] = new_dfprov2['ORDEREDPURCHASEQUANTITY'].astype(float)
                            total_order_qty = new_dfprov2['ORDEREDPURCHASEQUANTITY'].sum()

                            # Paso 1: Calcular los valores totales y los factores de ponderación
                            new_dfprov2['total_value'] = new_dfprov2['PURCHASEPRICE'] * new_dfprov2['ORDEREDPURCHASEQUANTITY']
                            total_value_sum = new_dfprov2['total_value'].sum()
                            new_dfprov2['weight_factor'] = new_dfprov2['total_value'] / total_value_sum
                            
                            
                            excel_download_data_prov2 = dataframe_to_excel_download(new_dfprov2, filename="Purchase order lines V2.xlsx")
                            
                            st.download_button(
                                label="Descargar Purchase order Prorrateado V2",
                                data=excel_download_data_prov2,
                                file_name="Purchase order lines V2.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            )
                    
                    else:
                        st.info(f"""No hay handlings fees asociados a las facturas""")

                   
                    
                       
        except FileNotFoundError:
            st.warning("El archivo PDF no se encontró. Cargue un archivo PDF para continuar.")
    
    


def show_envio_de_PL_a_EIT(col1, col2):
    with col1:
   
        st.sidebar.markdown("Envío de Packing List a EIT")

        loti1 = 'https://assets10.lottiefiles.com/private_files/lf30_ig1wfilw.json'
        lot1 = load_lottie_url(loti1)
        with col1:
            st_lottie(lot1, key="loti1", height=200, width=280)
        
    with col2:
        # Aquí puedes agregar código para interactuar con el DataFrame new_df y enviarlo a EIT
        # Si necesitas que el usuario ingrese más datos o realice más acciones, puedes agregar más elementos de entrada aquí.
        

        st.markdown("### Envío de PL a EIT")
        


        try:
            sku_df = pd.DataFrame(columns=['po', 'Style', 'Color', 'Size', 'sku', 'Qty', 'Unit Cost'])
            archivo_pdf = "unificado.pdf"

            contenido_pdf = extraer_texto_pdf_con_plumber(archivo_pdf)
            if contenido_pdf:  # Verificando si contenido_pdf tiene datos antes de procesarlos
                sku_matrix_sum, expanded_df = procesar_datos_pdf(contenido_pdf)
                #print(result)
                result = sku_matrix_sum.reset_index()
                #sku_df = sku_df.append(expanded_df, ignore_index=True)
                #cambiar append por concat
                sku_df = pd.concat([sku_df, expanded_df], ignore_index=True)
                # Crear 3 columnas
                col1, col2, col3 = st.columns(3)
                # Ingresar PAT en la primera columna
                despacho= col1.text_input("Ingresar número de despacho:", key='unique_key_1')
                obs = col2.text_input("Ingresar Observación:", value= "PALLET_DISPONIBLE", key='unique_key_2')
                # Estado de inventario en la segunda columna
                # Almacén en la tercera columna
                
                warehouse = "N/A"
            
                #
                
                new_df2 = purchase_construct(sku_df, despacho, obs, warehouse)
                # Filtrar las filas donde 'ORDEREDPURCHASEQUANTITY' no sea 0 ni vacío
                new_df2 = new_df2.loc[new_df2['ORDEREDPURCHASEQUANTITY'] != 0].dropna(subset=['ORDEREDPURCHASEQUANTITY'])
                new_df2 = new_df2[['CUSTOMERREFERENCE','ITEMNUMBER','PRODUCTCOLORID','PRODUCTSIZEID','ORDEREDPURCHASEQUANTITY']]
                    # Crear new_df3 
                new_df3 = new_df2.copy()
                new_df3.rename(columns={'CUSTOMERREFERENCE': 'PO', 'ORDEREDPURCHASEQUANTITY': 'Solicitado'}, inplace=True)
                # Agregar columna "Nº Despacho" con valor estático de la variable despacho
                new_df3['Nº Despacho'] = despacho
                # Crear columna "Artículo" con la concatenación de 'ITEMNUMBER', 'PRODUCTCOLORID' y 'PRODUCTSIZEID'
                new_df3['Artículo'] = new_df3['ITEMNUMBER'] + new_df3['PRODUCTCOLORID'] + new_df3['PRODUCTSIZEID']
                # Agregar columna de observación con el valor de la variable obs
                new_df3['Observación'] = obs
                new_df3.drop(columns=['ITEMNUMBER', 'PRODUCTCOLORID', 'PRODUCTSIZEID'], inplace=True)
                new_df3 = new_df3[['PO', 'Nº Despacho', 'Artículo', 'Solicitado', 'Observación']]


            try:
                    if despacho.strip() != '': 
                        # Muestra el nuevo DataFrame en la interfaz de Streamlit
                        st.write(new_df3)
                        # Cantidad de PO distintas
                        num_unique_po = new_df3['PO'].nunique()
                        st.write(f'Hay {num_unique_po} PO distintas.')
                        # Cantidad de artículos únicos
                        num_unique_articles = new_df3['Artículo'].nunique()
                        st.write(f'Hay {num_unique_articles} artículos únicos.')
                        # Cantidad total solicitada
                        total_requested = new_df3['Solicitado'].sum()
                        st.write(f'La cantidad total solicitada es {total_requested}.')
                        # Número de despacho (suponiendo que todos los registros tienen el mismo número de despacho)
                        dispatch_number = new_df3['Nº Despacho'].unique()[0]
                        st.write(f'El número de despacho es {dispatch_number}.')
                            
                        # Setting up with the connection
                        # The json file downloaded needs to be in the same folder
                        if st.button("Publicar"):
                            # Código para generar el DataFrame new_df3 y realizar los cálculos previos
                            
                            # Setting up with the connection
                            # The json file downloaded needs to be in the same folder
                            import ssl
                            ssl._create_default_https_context = ssl._create_unverified_context
                            
                            scope = ['https://www.googleapis.com/auth/spreadsheets',
                                    'https://www.googleapis.com/auth/drive']
                            credentials = service_account.Credentials.from_service_account_info(
                                st.secrets["gcp_service_account"], scopes=scope)
                            
                            #gc = gspread.authorize(credentials)
                            client = Client(scope=scope,creds=credentials)
                            # Establish the connection
                            # database is the Google Spreadsheet name
                            # database = gc.create("PL_Patagonia")
                            # database.share('cgutierrez.infor@gmail.com', perm_type='user', role='writer')
                            spreadsheetname = "PL_Patagonia"
                            spread = Spread(spreadsheetname,client = client)
                            # Check the connection
                            st.write(spread.url)
                            database = client.open("PL_Patagonia")
                            wks = database.worksheet("PL")
                            #st.write(new_df3)
                            # Exportar el DataFrame new_df3 a la hoja de cálculo

                            # Obtén la fecha actual
                            fecha_actual = datetime.now().date()
                            new_df3['Fecha'] = fecha_actual.strftime('%Y-%m-%d')

                            data_to_append = new_df3.values.tolist() 
                            wks.append_rows(data_to_append)
                            st.balloons()
                        else:
                            pass
                
            except FileNotFoundError:
                st.warning("Revisar la información antes de continuar.")
        except FileNotFoundError:
                st.warning("No se han cargado facturas para correr la automatización.")
if __name__ == "__main__":
    main()
