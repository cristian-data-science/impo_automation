import pandas as pd
import os
import PyPDF2
import pandas as pd
import re
import numpy
import base64
import io
import pdfplumber


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
                lista_pre = [re.sub(r'(?<=[^\s])Style (?=[^\s])', ' Style ', item) for item in lista_pre]
                lista_pre.append(i)
                
    return lista_pre

def extraer_texto_pdf_con_plumber(pdf_file: str) -> list:
    lista_pre = []
    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_content = page.extract_text()
            if page_content:
                table_list = page_content.split('\n')
                for item in table_list:
                    item = re.sub(r'(?<=[^\s])Style(?=[^\s])', ' Style ', item)
                    lista_pre.append(item)
            else:
                print(f"No se extrajo texto de la página {page_num+1}")
    return lista_pre
def procesar_datos_pdf(lista_pre):
    # Código refactorizado aquí
    
    ### Separar PO's e itemnumber en dataframe
    """
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
    #print(po_style)"""


    # paso 1 funciones.py

    # Se separa las lineas de la lista_pre que tienen desde colores hasta total,
    # ademas de la que contiene style. con esto logramos segmentar la data a las variantes de cada codigo
    
    # limpieza de listas de color, talla y style
    color_lines = []
    style_lines = []

    current_style = None
    value_before_0000 = None
    previous_value_before_0000 = None

    for i, line in enumerate(lista_pre):
        if re.search(r'\b0000 \b', line):
            value_before_0000 = re.search(r'(\d+)\s+0000 ', line).group(1)

        if line.startswith('Color'):
            start_idx = i
            end_idx = i + 1
            while end_idx < len(lista_pre) and not lista_pre[end_idx].startswith('Total'):
                end_idx += 1

            color_block = lista_pre[start_idx:end_idx]

            # Limpiar específicamente la línea que contiene las tallas
            for j, cl in enumerate(color_block):
                if cl.startswith('Color Size'):
                    color_block[j] = ' '.join(cl.split())

            color_lines.append(color_block)

            # Añadir el valor antes de "0000" al estilo actual
            if value_before_0000 is not None:
                style_line = f"{value_before_0000},{current_style}"
                previous_value_before_0000 = value_before_0000
            elif ',' not in current_style:
                style_line = f"{previous_value_before_0000},{current_style}"
            else:
                style_line = current_style

            style_lines.append(style_line)

        elif re.search(r'\bStyle\b', line):
            current_style = line.split()[line.split().index('Style')+1]
    # eliminando espacio antes de QTY
    for sublist in color_lines:
        for index, line in enumerate(sublist):
            # Si la línea tiene "QTY", quitar espacios en el código de color
            if "QTY" in line:
                parts = line.split('QTY')
                parts[0] = parts[0].replace(' ', '')
                line = ' QTY'.join(parts)
            
            sublist[index] = line

    # paso 2 funciones.py

    style_data = []
    for style in style_lines:
        po, itemnumber = style.split(',')
        style_data.append({'po': po, 'itemnumber': itemnumber})

    # Crear un DataFrame a partir de la lista de diccionarios
    po_style = pd.DataFrame(style_data)

   
    # paso 3 funciones.py

    # Crea df y concatena las listas con todos los datos

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
                sizes = size_str.split()
                unique_sizes = sorted(set(sizes), key=sizes.index)  # Eliminar duplicados manteniendo el orden
                size_values.append(' '.join(unique_sizes))

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
    #df['Qty'] = df['Qty'].astype(int)  # Convertir los valores en la columna "Qty" a enteros

    # Dividir la columna "Style" en dos columnas separadas: "PO" y "Style"
    df[['PO', 'Style']] = df['Style'].str.split(',', expand=True)

    # Reordenar las columnas para que "PO" esté al principio del DataFrame
    df = df[['PO', 'Style', 'Color', 'Size', 'Qty', 'Unit Cost']]

    df.index += 1
    df.index.name = 'indice'

    df['Qty'] = df['Qty'].replace(".", "")        


    # paso 4 

    # Convertir la columna 'Style' en el primer DataFrame y 'itemnumber' en el segundo DataFrame a tipo str
    df['Style'] = df['Style'].astype(str)
    po_style['itemnumber'] = po_style['itemnumber'].astype(str)


    combined_df = df
    combined_df = combined_df.reset_index(drop=True)
    combined_df


    # paso 5
    ### Se expande los estilos a SKU con su respectivo qty y costo

    new_rows = []

    for index, row in df.iterrows():
        style = row['Style']
        po = row['PO']
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


    # paso 6
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


def purchase_construct(sku_df, pat, status, warehouse):
    # Asignar valores estáticos
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

    # Cambiar los nombres de las columnas
    sku_df = sku_df.rename(columns={
        'po': 'CUSTOMERREFERENCE',
        'Style': 'ITEMNUMBER',
        'Color': 'PRODUCTCOLORID',
        'Size': 'PRODUCTSIZEID',
        'Qty': 'ORDEREDPURCHASEQUANTITY',
        'Unit Cost': 'PURCHASEPRICE'
    })

    # Agregar campos estáticos a sku_df
    sku_df['ALLOWEDOVERDELIVERYPERCENTAGE'] = ALLOWEDOVERDELIVERYPERCENTAGE
    sku_df['ALLOWEDUNDERDELIVERYPERCENTAGE'] = ALLOWEDUNDERDELIVERYPERCENTAGE
    sku_df['CUSTOMERREQUISITIONNUMBER'] = CUSTOMERREQUISITIONNUMBER
    sku_df['DEFAULTLEDGERDIMENSIONDISPLAYVALUE'] = DEFAULTLEDGERDIMENSIONDISPLAYVALUE
    sku_df['ITEMBATCHNUMBER'] = ITEMBATCHNUMBER
    sku_df['PRODUCTCONFIGURATIONID'] = PRODUCTCONFIGURATIONID
    sku_df['PRODUCTSTYLEID'] = PRODUCTSTYLEID
    sku_df['PURCHASEUNITSYMBOL'] = PURCHASEUNITSYMBOL
    sku_df['RECEIVINGSITEID'] = RECEIVINGSITEID
    sku_df['REQUESTERPERSONNELNUMBER'] = REQUESTERPERSONNELNUMBER
    sku_df['SALESTAXGROUPCODE'] = SALESTAXGROUPCODE
    sku_df['SALESTAXITEMGROUPCODE'] = SALESTAXITEMGROUPCODE
    sku_df['PURCHASEORDERNUMBER'] = pat
    sku_df['ORDEREDINVENTORYSTATUSID'] = status
    sku_df['RECEIVINGWAREHOUSEID'] = warehouse
    

    # Eliminar columnas 'sku' y 'total_cost_pdf'
    sku_df = sku_df.drop(columns=['sku', 'total_cost_pdf'])

    # Agregar columna 'LINENUMBER' y asignar un contador de línea
    sku_df['LINENUMBER'] = range(1, len(sku_df) + 1)

    # Reordenar las columnas

    sku_df['PURCHASEPRICEQUANTITY'] = 1
    new_df = sku_df[[
        'PURCHASEORDERNUMBER', 'LINENUMBER', 'ALLOWEDOVERDELIVERYPERCENTAGE', 'ALLOWEDUNDERDELIVERYPERCENTAGE',
        'CUSTOMERREFERENCE', 'CUSTOMERREQUISITIONNUMBER', 'DEFAULTLEDGERDIMENSIONDISPLAYVALUE', 'ITEMBATCHNUMBER',
        'ITEMNUMBER', 'ORDEREDINVENTORYSTATUSID', 'ORDEREDPURCHASEQUANTITY', 'PRODUCTCOLORID', 'PRODUCTCONFIGURATIONID',
        'PRODUCTSIZEID', 'PRODUCTSTYLEID', 'PURCHASEPRICE', 'PURCHASEPRICEQUANTITY', 'PURCHASEUNITSYMBOL', 'RECEIVINGSITEID',
        'RECEIVINGWAREHOUSEID', 'REQUESTERPERSONNELNUMBER', 'SALESTAXGROUPCODE', 'SALESTAXITEMGROUPCODE']]

    return new_df

    
    return new_df

def dataframe_to_excel_download(df, filename="data.xlsx"):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    output.seek(0)
    excel_data = output.getvalue()
    return excel_data


def extract_invoice_data(lista_pre):
    invoice_data = []
    current_invoice = []
    flag = False
    invoice_number = None

    for line in lista_pre:
        line_stripped = line.strip()
        line_no_spaces = line_stripped.replace(' ', '').lower()
        print(f"Processing line: '{line_stripped}'")  # Depuración
        if 'invoicenumberinvoiceissuedate' in line_no_spaces:
            print("Found 'Invoice Number Invoice Issue Date' line")  # Depuración
            invoice_number = True
            continue
        if invoice_number is True:
            invoice_number = line_stripped
            print(f"Invoice number set to: {invoice_number}")  # Depuración
            continue
        if re.search(r'^merchandiseamount', line_no_spaces):
            print("Found 'Merchandise Amount' line")  # Depuración
            flag = True
            current_invoice = [invoice_number]
        if flag:
            print(f"Appending line to current_invoice: {line_stripped}")  # Depuración
            current_invoice.append(line_stripped)
        if re.search(r'^invoicetotal', line_no_spaces):
            print("Found 'Invoice Total' line")  # Depuración
            flag = False
            invoice_data.append(current_invoice)
            print(f"Current invoice appended: {current_invoice}")  # Depuración
            invoice_number = None

    print(f"Collected invoice data: {invoice_data}")  # Depuración

    invoice_total_lines = pd.DataFrame(columns=['Invoice_number', 'Merchandise_amount', 'Total_adjustment', 'Total_taxes', 'Invoice_total'])

    for invoice in invoice_data:
        print(f"Processing invoice: {invoice}")  # Depuración
        try:
            invoice_number = invoice[0]
            merchandise_line = invoice[1]
            total_adjustment_line = invoice[2]
            total_taxes_line = invoice[3]
            invoice_total_line = invoice[4]

            print(f"Merchandise line: {merchandise_line}")  # Depuración

            # Ajustamos las expresiones regulares para coincidir con las líneas reales
            merchandise_amount_match = re.search(r'MerchandiseAmount\s*([\d,\.]+)', merchandise_line.replace(' ', ''), re.IGNORECASE)
            total_adjustment_match = re.search(r'TotalAdjustment\s*([\d,\.]+)', total_adjustment_line.replace(' ', ''), re.IGNORECASE)
            total_taxes_match = re.search(r'TotalTaxes\s*([\d,\.]+)', total_taxes_line.replace(' ', ''), re.IGNORECASE)
            invoice_total_match = re.search(r'InvoiceTotal\s*([\d,\.]+)', invoice_total_line.replace(' ', ''), re.IGNORECASE)

            if not (merchandise_amount_match and total_adjustment_match and total_taxes_match and invoice_total_match):
                print(f"No se pudieron extraer los montos en la factura {invoice_number}")
                continue

            merchandise_amount = float(merchandise_amount_match.group(1).replace(',', ''))
            total_adjustment = float(total_adjustment_match.group(1).replace(',', ''))
            total_taxes = float(total_taxes_match.group(1).replace(',', ''))
            invoice_total = float(invoice_total_match.group(1).replace(',', ''))

            new_row = pd.DataFrame({
                'Invoice_number': [invoice_number],
                'Merchandise_amount': [merchandise_amount],
                'Total_adjustment': [total_adjustment],
                'Total_taxes': [total_taxes],
                'Invoice_total': [invoice_total]
            })

            invoice_total_lines = pd.concat([invoice_total_lines, new_row], ignore_index=True)
        except Exception as e:
            print(f"Error al procesar la factura {invoice_number}: {e}")
            print(f"Datos de la factura: {invoice}")
            continue

    # Procesamiento adicional si es necesario
    if not invoice_total_lines.empty:
        invoice_total_lines['Invoice_date'] = invoice_total_lines['Invoice_number'].apply(lambda x: x.split(' ')[1] if len(x.split(' ')) > 1 else '')
        invoice_total_lines['Invoice_number'] = invoice_total_lines['Invoice_number'].apply(lambda x: x.split(' ')[0])

        invoice_total_lines = invoice_total_lines[['Invoice_number', 'Invoice_date', 'Merchandise_amount', 'Total_adjustment', 'Total_taxes', 'Invoice_total']]

    return invoice_total_lines