# Plataforma de Análisis del Sistema Eléctrico Nacional (SEN) 2025

Este repositorio contiene un análisis integral, dinámico y visual de la capacidad de generación eléctrica en México durante el año 2025. El proyecto procesa liquidaciones del Sistema Eléctrico Nacional (SEN) y presenta los datos a través de cuadernos de Jupyter, reportes formales en PDF y un **Dashboard interactivo en Streamlit**, inspirados en el diseño institucional de **CONAHCYT PLANEAS**.

## Características Principales
* **Procesamiento Dinámico de Datos:** Identifica automáticamente los archivos CSV de liquidaciones del SEN en cualquier subcarpeta, seleccionando la liquidación más reciente disponible (`L3 > L2 > L1 > L0`).
* **Corrección Temporal Precisa:** Implementa lógica para procesar la "Hora 24", transformándola correctamente a la hora 00:00 del día siguiente.
* **Diseño Institucional:** Visualizaciones con una paleta de colores cuidadosamente seleccionada para contrastar fuentes fósiles vs. energías limpias y renovables.
* **Dashboard Interactivo:** Aplicación de Streamlit de una sola pestaña (single-page application) con filtrado interactivo por meses, tipos de fuentes y tecnologías específicas, integrando librerías como *Plotly*.
* **Generación de PDF automatizada:** Incluye un script (basado en `reportlab`) para generar un reporte ejecutivo consolidado en PDF con formato profesional.

## Cómo empezar

### 1. Requisitos Previos
Asegúrate de contar con Python 3.8+ instalado en tu sistema.
Es recomendable crear un entorno virtual para el proyecto.
```bash
pip install pandas numpy matplotlib seaborn streamlit plotly reportlab
```

### 2. Estructura del Proyecto
* `Consolidado_Energias_Generadas.csv`: Base de datos final procesada y limpia.
* `análisis de energías 2025 méxico - Refactorizado.ipynb`: Análisis original refactorizado y optimizado.
* `app.py`: Dashboard interactivo desarrollado en Streamlit.
* `Analisis_Energias_SEN_2025.pdf`: Reporte ejecutivo en PDF de la generación anual.
* Archivos `.png`, `.svg` y `.csv`: Gráficas en alta resolución y tablas de resumen extraídas del análisis.
* Carpetas de `Generacion Liquidada_...`: Repositorio local de archivos CSV crudos descargados del SEN.

### 3. Ejecutar el Dashboard (Streamlit)
Abre tu terminal en la carpeta principal del proyecto y ejecuta:
```bash
streamlit run app.py
```
Esto lanzará un servidor local y abrirá la plataforma automáticamente en tu navegador web.

## Visualizaciones Incluidas
1. Matriz y Participación de la Generación Eléctrica Anual 2025.
2. Transición Energética: Comparativa Fuentes Fósiles vs. Limpias.
3. Evolución Mensual de Producción Energética (Gráficas de líneas y áreas apiladas).
4. Curva de Despacho Promedio Diaria (Interacción tecnológica 00:00 - 23:00 hrs).

## Herramientas Utilizadas
Python, Pandas, NumPy, Streamlit, Plotly, Seaborn, Matplotlib, ReportLab.
