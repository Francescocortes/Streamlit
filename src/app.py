from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

# Inicializar la aplicación Dash
app = Dash(__name__)
server = app.server  # ¡Indispensable para el despliegue en Render!

# Carga y preprocesamiento eficiente de datos (evita sobrecargar memoria)
# df_mortalidad = pd.read_excel('data/Anexo1.NoFetal2019_CE_15-03-23.xlsx', sheet_name='No_Fetales_2019')
# df_divipola = pd.read_excel('data/Divipola_CE_.xlsx', sheet_name='Hoja1')
# df_codigos = pd.read_excel('data/Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx', sheet_name='Final', skiprows=8)

# Ejemplo de diseño base (Layout)
app.layout = html.Div([
    html.H1("Análisis de Mortalidad en Colombia (2019)", style={'textAlign': 'center', 'color': '#2c3e50'}),
    html.P("Dashboard interactivo desarrollado con Dash y Plotly para el análisis demográfico y regional.", style={'textAlign': 'center'}),
    
    html.Div([
        html.Label("Seleccione una vista o filtro temporal:"),
        dcc.Dropdown(
            id='dropdown-filtro',
            options=[{'label': 'Nacional', 'value': 'NACIONAL'}],
            value='NACIONAL',
            style={'width': '50%'}
        )
    ], style={'padding': '20px'}),
    
    html.Div([
        dcc.Graph(id='grafico-principal')
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)