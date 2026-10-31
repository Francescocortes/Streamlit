#  Análisis de Mortalidad en Colombia (2019) — Aplicación Web Interactiva

Este repositorio contiene el código fuente, la estructura de datos y las configuraciones necesarias para la ejecución y despliegue de una **aplicación web interactiva desarrollada en Python con Dash y Plotly**, orientada al análisis demográfico y regional de la mortalidad en Colombia durante el año 2019.

##  1. Introducción del Proyecto

El análisis de datos vitales representa un insumo estratégico para la toma de decisiones en salud pública y el entendimiento de fenómenos demográficos. Esta aplicación transforma datos complejos sobre defunciones en representaciones visuales dinámicas e intuitivas, permitiendo identificar patrones regionales, causas principales de muerte y disparidades por género y grupo etario en el territorio nacional.

## 2. Objetivo

Diseñar, implementar y desplegar un *dashboard* analítico e interactivo accesible en la nube (PaaS) que permita explorar y correlacionar la información de mortalidad no fetal en Colombia (2019) a partir de los microdatos del DANE.

## 3. Estructura del Proyecto

mi_dashboard_mortalidad/
│
├── data/                                      # Datos fuente en formato Excel
│   ├── Anexo1.NoFetal2019_CE_15-03-23.xlsx    # Microdatos de defunciones no fetales (2019)
│   ├── Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx # Diccionario de causas de muerte (CIE-10)
│   └── Divipola_CE_.xlsx                     # División Político-Administrativa de Colombia
│
├── src/                                       # Código fuente modular de la aplicación
│   ├── app.py                                 # Punto de entrada de la aplicación y servidor Flask
│   ├── callbacks.py                           # Lógica de interactividad y eventos
│   ├── init.py                                # Archivo de inicialización del paquete src
│   └── layout.py                              # Definición de la interfaz visual y componentes
│
├── venv/                                      # Entorno virtual de Python
├── readme.md                                  # Documentación técnica e informe del proyecto
└── requirements.txt                           # Librerías y versiones requeridas


## 4. Software y Tecnologías Utilizadas

* **Lenguaje de Programación:** Python 3.11+
* **Procesamiento de Datos:** `Pandas`, `OpenPyXL`
* **Visualización Interactiva:** `Plotly Express`, `Plotly Graph Objects`
* **Framework Web Analítico:** `Dash` (`dash-core-components`, `dash-html-components`, `dash-table`)
* **Servidor WSGI para Producción:** `Gunicorn`
* **Entorno de Despliegue:** Render (Platform as a Service - PaaS)
* **Control de Versiones:** Git y GitHub

## 5. Requisitos y Dependencias

El proyecto requiere las siguientes librerías especificadas en `requirements.txt`:

```text
dash>=2.14.0
pandas>=2.1.1
openpyxl>=3.1.2
plotly>=5.17.0
gunicorn>=21.2.0
requests>=2.31.0


