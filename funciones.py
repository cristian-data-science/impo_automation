import pandas as pd
import os
import PyPDF2
import pandas as pd
import re
import numpy
import base64
import io


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

def extraer_texto_pdf(pdf_file: str) -> list:
    with open(pdf_file, 'rb') as f:
        read_pdf = PyPDF2.PdfFileReader(f)
        lista_pre = []

        for i in range(read_pdf.getNumPages()):
            page = read_pdf.getPage(i)
            page_content = page.extractText()
            table_list = page_content.split('\n')

            for i in table_list:
                lista_pre.append(i)
                
    return lista_pre

def procesar_datos_pdf(lista_pre):
    # Código refactorizado aquí
    
    ### Separar PO's e itemnumber en dataframe
    po_values = []
    itemnumber_values = []

    for line in lista_pre:
        if "0000" in line:
            parts = line.split("0000")
            po_value = parts[0].strip()
            if po_value.isnumeric():  # Verificar si la cadena contiene solo números
                po_values.append(po_value)
                if len(parts) > 1:
                    split_parts = parts[1].strip().split()
                    if len(split_parts) > 0:
                        itemnumber_values.append(split_parts[0])
                    else:
                        itemnumber_values.append('')
                else:
                    itemnumber_values.append('')

    po_style = pd.DataFrame({'po': po_values, 'itemnumber': itemnumber_values})
    #print(po_style)


    ### Se separa las lineas de la lista_pre que tienen desde colores hasta total, ademas de la que contiene style. con esto logramos segmentar la data a las variantes de cada codigo

    color_lines = []
    # no se esta usando este style, ya que lo hicimos anteriormente a prueba de fallos
    style_lines = []

    for i, line in enumerate(lista_pre):
        if line.startswith('Color'):
            start_idx = i
            end_idx = i + 1
            while end_idx < len(lista_pre) and not lista_pre[end_idx].startswith('Total'):
                end_idx += 1
            color_lines.append(lista_pre[start_idx:end_idx])
        elif line.startswith('Style'):
            style_lines.append(line)


    ### limpieza de listas de color, talla y style

    color_lines = []
    style_lines = []

    current_style = None
    for i, line in enumerate(lista_pre):
        if line.startswith('Color'):
            start_idx = i
            end_idx = i + 1
            while end_idx < len(lista_pre) and not lista_pre[end_idx].startswith('Total'):
                end_idx += 1
            color_lines.append(lista_pre[start_idx:end_idx])
            style_lines.append(current_style)
        elif line.startswith('Style'):
            current_style = line.split()[1]  # Guardar solo el valor después de 'Style'



    ### Crea df y concatena las listas con todos los datos

    color_values = []
    size_values = []
    qty_values = []
    unit_cost_values = []

    for row in color_lines:
        colors = []
        qtys = []
        unit_costs = []
        for i, item in enumerate(row):
            if i > 0:
                colors.append(item.split()[0])
                qty_list = item.split('QTY')[1].split('Each')[0].strip().split()
                qty_list = qty_list[:-1]  # Eliminar el último valor
                qty_str = ' '.join(qty_list)
                unit_cost_str = item.split('Each')[1].split()[0].strip()
                qtys.append(qty_str)
                unit_costs.append(unit_cost_str)
            if i == 0:
                size_str = item.split('Size')[1].split('Total')[0].strip()
                size_values.append(size_str)

        color_values.append(', '.join(colors))
        qty_values.append(', '.join(qtys))
        unit_cost_values.append(', '.join(unit_costs))

    # Asegurando que todas las listas tengan la misma longitud
    max_length = max(len(color_values), len(size_values), len(qty_values), len(unit_cost_values))
    color_values.extend([''] * (max_length - len(color_values)))
    size_values.extend([''] * (max_length - len(size_values)))
    qty_values.extend([''] * (max_length - len(qty_values)))
    unit_cost_values.extend([''] * (max_length - len(unit_cost_values)))
    # cambiando , por . dentro de las unidades
    for i in range(len(qty_values)):
        qty_values[i] = re.sub(r'(?<=\d),(?=\d)', '.', qty_values[i])
    # eliminando . de qty
    for i in range(len(qty_values)):
        qty_values[i] = qty_values[i].replace('.', '')

    df = pd.DataFrame({'Style': style_lines, 'Color': color_values, 'Size': size_values, 'Qty': qty_values, 'Unit Cost': unit_cost_values})
    df.index += 1
    df.index.name = 'indice'

    df['Qty'] = df['Qty'].replace(".", "")        



    ### Merge entre df y po_Style usando criterios de siguiente coincidencia

    po_style = po_style.rename(columns={'itemnumber': 'Style'})

    # Función auxiliar para realizar el merge
    def merge_with_next_match(row, po_style_df, used_matches):
        style = row['Style']
        matches = po_style_df[po_style_df['Style'] == style]

        for _, match in matches.iterrows():
            if match.name not in used_matches:
                used_matches.add(match.name)
                return match['po']
        return None

    # Inicializar un conjunto para almacenar las coincidencias utilizadas
    used_matches = set()

    # Realizar el merge utilizando la función auxiliar
    df['po'] = df.apply(merge_with_next_match, axis=1, args=(po_style, used_matches))

    # Rellenar los valores None en la columna 'po' con el valor anterior
    df['po'] = df['po'].fillna(method='ffill')

    # Reordenar las columnas
    columns = ['po'] + [col for col in df.columns if col != 'po']
    df = df[columns]


    ### Se expande los estilos a SKU con su respectivo qty y costo

    new_rows = []

    for index, row in df.iterrows():
        style = row['Style']
        po = row['po']
        color = row['Color'].split(', ')
        sizes = row['Size'].split()
        qtys = row['Qty'].split(', ')
        unit_costs = row['Unit Cost'].split(', ')

        for c, size_qty, unit_cost in zip(color, qtys, unit_costs):
            size_qty_split = size_qty.split()
            for size, qty in zip(sizes, size_qty_split):
                sku = f"{style}{c}{size}"
                new_rows.append([po, style, c, size, sku, int(qty), round(float(unit_cost), 2)]) 

    expanded_df = pd.DataFrame(new_rows, columns=['po','Style', 'Color', 'Size', 'sku', 'Qty', 'Unit Cost'])



    ### sku matrix

    sku_matrix = expanded_df
    sku_matrix['total_cost_pdf'] = sku_matrix['Qty'] * sku_matrix['Unit Cost']

    # Definir las funciones de agregación para cada columna
    aggregations = {
        'Qty': 'sum',
        'Unit Cost': 'first',  # Utilizar el primer valor en lugar de sumar
        'total_cost_pdf': 'sum'
    }

    # Agrupar por 'po' y aplicar las funciones de agregación a las columnas correspondientes
    sku_matrix_sum = sku_matrix.groupby(['po']).agg(aggregations)

    # Redondear la columna 'Unit Cost' a dos decimales
    sku_matrix_sum['Unit Cost'] = sku_matrix_sum['Unit Cost'].round(2)

    # Ordenar el DataFrame sku_matrix_sum por la columna 'po' de manera ascendente
    sku_matrix_sum = sku_matrix_sum.sort_values('po', ascending=True)

    # Cambiar el nombre de la columna 'Unit Cost' a 'costo_promedio'
    sku_matrix_sum = sku_matrix_sum.rename(columns={'Unit Cost': 'costo_promedio'})

    return sku_matrix_sum, expanded_df


def purchase_construct( sku_df, pat, status, warehouse):
    
    ALLOWEDOVERDELIVERYPERCENTAGE = "100"
    ALLOWEDUNDERDELIVERYPERCENTAGE = "100"
    CUSTOMERREQUISITIONNUMBER = ""
    DEFAULTLEDGERDIMENSIONDISPLAYVALUE = ""
    ITEMBATCHNUMBER = ""
    PRODUCTCONFIGURATIONID = "1ST"
    PRODUCTSTYLEID = "GEN"
    PURCHASEUNITSYMBOL = "un"
    RECEIVINGSITEID = "01"
    REQUESTERPERSONNELNUMBER = ""
    SALESTAXGROUPCODE = "Nacional"
    SALESTAXITEMGROUPCODE = "EXENTO"

    new_df = sku_df.assign(
        ALLOWEDOVERDELIVERYPERCENTAGE=ALLOWEDOVERDELIVERYPERCENTAGE,
        ALLOWEDUNDERDELIVERYPERCENTAGE=ALLOWEDUNDERDELIVERYPERCENTAGE,
        CUSTOMERREQUISITIONNUMBER=CUSTOMERREQUISITIONNUMBER,
        DEFAULTLEDGERDIMENSIONDISPLAYVALUE=DEFAULTLEDGERDIMENSIONDISPLAYVALUE,
        ITEMBATCHNUMBER=ITEMBATCHNUMBER,
        PRODUCTCONFIGURATIONID=PRODUCTCONFIGURATIONID,
        PRODUCTSTYLEID=PRODUCTSTYLEID,
        PURCHASEUNITSYMBOL=PURCHASEUNITSYMBOL,
        RECEIVINGSITEID=RECEIVINGSITEID,
        REQUESTERPERSONNELNUMBER=REQUESTERPERSONNELNUMBER,
        SALESTAXGROUPCODE=SALESTAXGROUPCODE,
        SALESTAXITEMGROUPCODE=SALESTAXITEMGROUPCODE,
        PAT=pat,
        STATUS=status,
        WAREHOUSE=warehouse
    )
    
    return new_df

def dataframe_to_excel_download(df, filename="data.xlsx"):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.save()
    excel_data = output.getvalue()
    return excel_data