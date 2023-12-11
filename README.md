# Impo App

Esta aplicación automatiza el procesamiento de facturas de importación, corrigiendo el costo real y ejecutando un post procesamiento de la data para cargarla al ERP.

## Descripción

La aplicación está construida con Python y utiliza varias librerías como Streamlit, Pandas, Plotly, entre otras, para realizar diversas tareas automatizadas en el procesamiento de facturas de importación.

## Requisitos

- Python 3.x
- Instalación de las siguientes librerías: Streamlit, Pandas, Plotly, Requests, Matplotlib, Seaborn, gspread, oauth2client, google

## Instalación

1. Clona o descarga el repositorio.
2. Asegúrate de tener Python instalado.
3. Instala las dependencias ejecutando: `pip install -r requirements.txt`.

## Uso

1. Abre un terminal o línea de comandos.
2. Navega al directorio donde se encuentra la aplicación.
3. Ejecuta la aplicación con el comando: `streamlit run app.py`.
4. Se abrirá una ventana del navegador con la interfaz de la aplicación.
5. La aplicación consta de varios menús y opciones, tales como:
   - **Home:** Muestra una descripción general de la app.
   - **Carga de datos:** Permite cargar archivos de facturas en PDF e International Account Sales (IAS) en Excel.
   - **Insights:** Proporciona análisis de los datos de importaciones y visualizaciones.
   - **Descarga de resultados:** Permite descargar los resultados generados por la aplicación.
   - **Envío de PL a EIT:** Facilita el envío de Packing List a EIT.

## Estructura de Archivos

- **app.py:** Contiene el código principal de la aplicación.
- **funciones.py:** Contiene funciones adicionales utilizadas en la aplicación para procesamiento de datos.
- **requirements.txt:** Lista de las librerías y sus versiones requeridas.

## Créditos

- Este proyecto fue desarrollado por Cris.

## Contribución

Si deseas contribuir a este proyecto, sigue estos pasos:

1. Haz un fork del repositorio.
2. Crea una nueva rama para tu funcionalidad: `git checkout -b nueva-funcionalidad`.
3. Realiza tus cambios y haz commit: `git commit -am 'Agregar nueva funcionalidad'`.
4. Sube los cambios a tu repositorio: `git push origin nueva-funcionalidad`.
5. Crea un pull request en el repositorio original.


