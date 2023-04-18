import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests



from funciones import *
from streamlit.components.v1 import html
from streamlit_option_menu import option_menu
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from streamlit_lottie import st_lottie


st.set_page_config(page_title="Impo Auto App", layout="wide")


def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


def main():
    col1 = st.sidebar
    col2, col3 = st.columns((3, 1))

    col2.title("Impo Automation App")
    col2.markdown("""
    Esta app automatiza el proceso de procesamiento de facturas de importación corrigiendo al costo real y ejecuta un post procesado de la data para cargarla al ERP
    """)

    with st.sidebar:
        selected = option_menu("Main Menu", ["Home", 'Carga de datos', 'Insights', 'Descarga de resultados'],
                               icons=['house', 'bi bi-upload', 'bi bi-file-bar-graph', 'bi bi-download'],
                               menu_icon="cast", default_index=0)

    if selected not in ["Carga de datos", "Insights", "Descarga de resultados"]:
        show_home(col1, col2)

    if selected == "Carga de datos":
        show_carga_de_datos(col1, col2)

    if selected == "Insights":
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
        st_lottie(lot1, key="loti1", height=200, width=200)

    loti2 = 'https://assets7.lottiefiles.com/packages/lf20_lphquaqr.json'
    lot2 = load_lottie_url(loti2)
    with col2:
        st_lottie(lot2, key="loti2")  # ,height=74, width=200)


def show_carga_de_datos(col1, col2):
    with col1:
        st.sidebar.markdown("Carga de facturas en pdf e international account sales en excel")
        
    with col2:
        st.markdown("### Carga de datos")
        upload_facturas = st.file_uploader("Subir facturas", type=["pdf"], accept_multiple_files=True, key="ias", help="Cargue las facturas en formato PDF.")
        upload_ias = st.file_uploader("Subir IAS", type=["xls", "xlsx", "csv"], key="pdf", help="Cargue el archivo IAS en formato Excel o CSV.")
        
        if upload_facturas:
            st.success("Facturas subidas y unificadas correctamente.")
            # Procesar las facturas aquí
            fusionar_pdfs(upload_facturas)
            archivo_salida = "unificado.pdf"

            with open(archivo_salida, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                label="Descargar unificado.pdf",
                data=pdf_bytes,
                file_name="unificado.pdf",
                mime="application/pdf"
            )

        if upload_ias is not None:
            st.success("IAS subidos exitosamente.")
            # Leer el archivo IAS de Excel y guardar los datos en un DataFrame # archivo funciones.py
            ias_df_sum = procesar_ias_excel(upload_ias)
            
            # Configurar y mostrar AgGrid con el DataFrame
            grid_options_builder = GridOptionsBuilder.from_dataframe(ias_df_sum)
            grid_options_builder.configure_default_column(groupable=True, filter=True, sortable=True, resizable=True)
            grid_options = grid_options_builder.build()
            AgGrid(ias_df_sum, gridOptions=grid_options)

def show_insights(col1, col2):
    with col1:
        st.sidebar.markdown("Data analytics de las importaciones")
        archivo_pdf = "unificado.pdf"
        contenido_pdf = extraer_texto_pdf(archivo_pdf)

        # Imprimir el contenido de la lista
        for linea in contenido_pdf:
            print("ZZZZZZ")
        result = procesar_datos_pdf(contenido_pdf)
        print(result)

def show_descarga_de_resultados(col1, col2):
    with col1:
        st.sidebar.markdown("Purchase Order Lines y Manual Invoice")
        

if __name__ == "__main__":
    main()
