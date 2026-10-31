# 📊 Análisis de Mortalidad en Colombia (2019) — Aplicación Web Interactiva

Este proyecto es una aplicación web interactiva desarrollada en **Python** utilizando **Dash**, **Plotly** y **Pandas**. Su objetivo principal es ofrecer una plataforma analítica y visual sobre los microdatos de mortalidad en Colombia correspondientes al año 2019, permitiendo explorar factores demográficos, geográficos y de causas de muerte a partir de la información oficial del DANE.

---

## 🚀 Características Principales

La aplicación integra 7 componentes visuales interactivos para el análisis integral de datos:

1. **🗺️ Mapa de Colombia (Distribución por Departamentos):** Visualización coroplética de la mortalidad total agrupada por departamento.
2. **📈 Serie Temporal de Defunciones:** Gráfico de líneas que expone la tendencia mensual de muertes durante el año 2019.
3. **💥 Ciudades más Afectadas por Homicidios:** Gráfico de barras destacando los municipios con mayor registro de muertes violentas (homicidios).
4. **📉 Menor Índice de Mortalidad:** Gráfico circular (Pie chart) con las 10 ciudades/municipios con menor cantidad de fallecimientos.
5. **📋 Top 10 Causas de Muerte:** Tabla interactiva (`dash_table.DataTable`) que cruza los códigos CIE-10 con sus descripciones oficiales para presentar las principales causas de defunción.
6. **👫 Comparativo por Sexo:** Gráfico de barras apiladas que analiza la distribución de mortalidad entre hombres y mujeres por departamento.
7. **📊 Distribución por Grupos Etarios:** Histograma estructurado que clasifica los fallecimientos según el rango de edad (neonatal, infancia, juventud, adultez, vejez, longevidad).

---

## 📂 Estructura del Repositorio


mi_dashboard_mortalidad/
│
├── data/
│   ├── Anexo1.NoFetal2019_CE_15-03-23.xlsx
│   ├── Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx
│   └── Divipola_CE_.xlsx
│   |___Poblacion_Municipal_DANE_2018_2042.xlsx
├── src/
│   ├
│   ├── app.py          # Punto de entrada de la aplicación Dash y configuración del servidor
│   
│
├── requirements.txt    # Librerías y dependencias para entorno local y producción
├── 
└── README.md           # Documentación técnica del proyecto


