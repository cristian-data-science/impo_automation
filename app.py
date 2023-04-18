import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

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
        upload_facturas = st.file_uploader("Subir facturas", type=["pdf"], accept_multiple_files=True)
        upload_ias = st.file_uploader("Subir IAS", type=["xls", "xlsx", "csv"])
        
        if upload_facturas:
            st.success("Facturas subidas exitosamente.")
            # Procesar las facturas aquí
            for factura in upload_facturas:
                # Procesar cada factura individualmente
                print(factura)
                print("procesandoooooooo")

        if upload_ias is not None:
            st.success("IAS subidos exitosamente.")
            # Procesar los IAS aquí

            # Leer el archivo IAS de Excel y guardar los datos en un DataFrame
            ias_df = pd.read_excel(upload_ias, header=1)
            ias_df = ias[['Purchase Order','Product number','Size','Color','Sales Quantity','Sales Amount']]
            ias_df.rename(columns={'Sales Amount': 'costo_IAS','Purchase Order': 'po'}, inplace=True)
            ias_df_sum = ias_df.groupby(['po'])[['costo_IAS']].sum()
            pd.DataFrame(ias_df_sum).reset_index(inplace=True, drop=False)
            ias_df_sum['po'] = ias_df_sum['po'].astype(int)

            st.write(ias_df_sum)  # Muestra el contenido del DataFrame en la app

def show_insights(col1, col2):
    with col1:
        st.sidebar.markdown("Data analytics de las importaciones")


def show_descarga_de_resultados(col1, col2):
    with col1:
        st.sidebar.markdown("Purchase Order Lines y Manual Invoice")


if __name__ == "__main__":
    main()
