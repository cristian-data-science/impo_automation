import pandas as pd
import os

from PyPDF2 import PdfFileMerger


def procesar_ias_excel(upload_ias):
    ias = pd.read_excel(upload_ias, header=1)
    ias_df = ias[['Purchase Order','Product number','Size','Color','Sales Quantity','Sales Amount']]
    ias_df.rename(columns={'Sales Amount': 'costo_IAS','Purchase Order': 'po'}, inplace=True)
    ias_df_sum = ias_df.groupby(['po'])[['costo_IAS']].sum()
    pd.DataFrame(ias_df_sum).reset_index(inplace=True, drop=False)
    
    return ias_df_sum


def fusionar_pdfs(upload_facturas: list, nombre_archivo_salida: str = 'unificado.pdf') -> None:
    # Crea un objeto fusionador de archivos PDF
    fusionador = PdfFileMerger()

    # Fusiona los archivos PDF cargados en el fusionador
    for pdf in upload_facturas:
        fusionador.append(pdf)

    # Guarda el archivo PDF fusionado en el nombre de archivo de salida
    with open(nombre_archivo_salida, 'wb') as salida:
        fusionador.write(salida)

    