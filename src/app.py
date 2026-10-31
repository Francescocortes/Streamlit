from pathlib import Path
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, callback, dcc, html

# Rutas y aplicación
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
app = Dash(
    __name__,
    title='Observatorio de Mortalidad | Colombia 2019',
    assets_folder=str(BASE_DIR / 'assets'),
)
app.index_string = app.index_string.replace(
    '{%favicon%}',
    '<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">',
)
server = app.server

# Datos de defunciones y catálogos DANE
df_mortalidad = pd.read_excel(
    DATA_DIR / 'Anexo1.NoFetal2019_CE_15-03-23.xlsx',
    sheet_name='No_Fetales_2019',
    usecols=['COD_DANE', 'MES', 'SEXO', 'GRUPO_EDAD1', 'MANERA_MUERTE', 'COD_MUERTE'],
)
df_municipios = pd.read_excel(
    DATA_DIR / 'Divipola_CE_.xlsx',
    sheet_name='Hoja1',
    usecols=['COD_DANE', 'DEPARTAMENTO', 'MUNICIPIO'],
    dtype={'COD_DANE': str},
)

def normalizar_codigo(valor):
    if pd.isna(valor):
        return None
    return str(valor).strip().removesuffix('.0').zfill(5)


def normalizar_texto(serie):
    return serie.astype('string').str.strip().str.upper()


df_mortalidad['COD_DANE'] = df_mortalidad['COD_DANE'].map(normalizar_codigo)
df_municipios['COD_DANE'] = df_municipios['COD_DANE'].map(normalizar_codigo)
df_municipios['DEPARTAMENTO'] = normalizar_texto(df_municipios['DEPARTAMENTO'])
df_municipios['MUNICIPIO'] = normalizar_texto(df_municipios['MUNICIPIO'])
df_municipios = df_municipios.drop_duplicates('COD_DANE')
df_mortalidad = df_mortalidad.merge(
    df_municipios[['COD_DANE', 'DEPARTAMENTO', 'MUNICIPIO']],
    on='COD_DANE', how='left',
)
df_mortalidad['DEPARTAMENTO'] = df_mortalidad['DEPARTAMENTO'].fillna('SIN DEPARTAMENTO')
df_mortalidad['MUNICIPIO'] = df_mortalidad['MUNICIPIO'].fillna('SIN MUNICIPIO')
df_mortalidad['MES'] = pd.to_numeric(df_mortalidad['MES'], errors='coerce').astype('Int64')
df_mortalidad['COD_MUERTE'] = df_mortalidad['COD_MUERTE'].astype('string').str.strip().str.upper()

# Códigos DANE para sexo y ciclo de vida
sexo_labels = {1: 'Masculino', 2: 'Femenino', 3: 'Sin especificar'}
df_mortalidad['SEXO_LABEL'] = pd.to_numeric(df_mortalidad['SEXO'], errors='coerce').map(sexo_labels).fillna('Sin especificar')

rangos_edad = [
    ('Mortalidad neonatal', range(0, 5), 'Menor de 1 mes'),
    ('Mortalidad infantil', range(5, 7), '1 a 11 meses'),
    ('Primera infancia', range(7, 9), '1 a 4 años'),
    ('Niñez', range(9, 11), '5 a 14 años'),
    ('Adolescencia', range(11, 12), '15 a 19 años'),
    ('Juventud', range(12, 14), '20 a 29 años'),
    ('Adultez temprana', range(14, 17), '30 a 44 años'),
    ('Adultez intermedia', range(17, 20), '45 a 59 años'),
    ('Vejez', range(20, 25), '60 a 84 años'),
    ('Longevidad / centenarios', range(25, 29), '85 a 100+ años'),
    ('Edad desconocida', range(29, 30), 'Sin información'),
]
edad_codigo_a_categoria = {
    codigo: (categoria, rango)
    for categoria, codigos, rango in rangos_edad
    for codigo in codigos
}
def categoria_edad(codigo):
    try:
        return edad_codigo_a_categoria.get(int(codigo), ('Edad sin clasificar', 'Sin clasificación'))[0]
    except (TypeError, ValueError):
        return 'Edad sin clasificar'

df_mortalidad['CICLO_VIDA'] = df_mortalidad['GRUPO_EDAD1'].map(categoria_edad)
orden_edades = [categoria for categoria, _, _ in rangos_edad] + ['Edad sin clasificar']

# Catálogo CIE-10: conserva las descripciones de 3 y 4 caracteres.
df_causas = pd.read_excel(
    DATA_DIR / 'Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx',
    sheet_name='Final', skiprows=9, header=None, usecols='C:F',
)
causa_por_codigo = {}
for fila in df_causas.itertuples(index=False, name=None):
    codigo_3, descripcion_3, codigo_4, descripcion_4 = fila
    if pd.notna(codigo_3) and pd.notna(descripcion_3):
        causa_por_codigo[str(codigo_3).strip().upper()] = str(descripcion_3).strip()
    if pd.notna(codigo_4) and pd.notna(descripcion_4):
        causa_por_codigo[str(codigo_4).strip().upper()] = str(descripcion_4).strip()

# Coordenadas municipales de DIVIPOLA para representar cada departamento en el mapa.
df_coordenadas = pd.read_excel(
    DATA_DIR / 'Divipola_CE_.xlsx',
    sheet_name='Hoja3', skiprows=2, header=None, usecols='A:G',
)
df_coordenadas = df_coordenadas.iloc[:, [1, 4, 5, 6]].copy()
df_coordenadas.columns = ['DEPARTAMENTO', 'TIPO', 'LONGITUD', 'LATITUD']
df_coordenadas['DEPARTAMENTO'] = normalizar_texto(df_coordenadas['DEPARTAMENTO'])
for columna in ['LONGITUD', 'LATITUD']:
    df_coordenadas[columna] = pd.to_numeric(
        df_coordenadas[columna].astype('string').str.replace(',', '.', regex=False),
        errors='coerce',
    )
centroides_departamento = (
    df_coordenadas.dropna(subset=['LONGITUD', 'LATITUD'])
    .groupby('DEPARTAMENTO', as_index=False)
    .agg(LONGITUD=('LONGITUD', 'mean'), LATITUD=('LATITUD', 'mean'))
)

# Denominadores municipales: proyecciones oficiales DANE para calcular tasas comparables.
archivo_poblacion = DATA_DIR / 'Poblacion_Municipal_DANE_2018_2042.xlsx'
df_poblacion = pd.read_excel(
    archivo_poblacion,
    sheet_name='PobMunicipalxÁrea',
    header=7,
    usecols='A:G',
)
df_poblacion = df_poblacion.iloc[:, [0, 2, 4, 5, 6]].copy()
df_poblacion.columns = ['COD_DEPARTAMENTO', 'COD_MUNICIPIO', 'ANIO', 'AREA', 'POBLACION']
df_poblacion = df_poblacion[
    pd.to_numeric(df_poblacion['ANIO'], errors='coerce').eq(2019)
    & df_poblacion['AREA'].astype('string').str.strip().str.casefold().eq('total')
].copy()
df_poblacion['COD_DANE'] = df_poblacion['COD_MUNICIPIO'].map(normalizar_codigo)
df_poblacion['POBLACION'] = pd.to_numeric(df_poblacion['POBLACION'], errors='coerce')
df_poblacion = df_poblacion.dropna(subset=['COD_DANE', 'POBLACION']).drop_duplicates('COD_DANE')
df_poblacion = df_poblacion.merge(
    df_municipios[['COD_DANE', 'DEPARTAMENTO', 'MUNICIPIO']],
    on='COD_DANE', how='left',
)

meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]
colores = ['#167d8d', '#22a699', '#78c7b5', '#f1b96a', '#ee8f72', '#8c79b8']
TODOS = 'COLOMBIA COMPLETA'
DEPARTAMENTOS = sorted(df_mortalidad.loc[df_mortalidad['DEPARTAMENTO'] != 'SIN DEPARTAMENTO', 'DEPARTAMENTO'].dropna().unique())


def estilo_figura(figura, alto=360, leyenda=False):
    figura.update_layout(
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=alto,
        margin=dict(l=16, r=24, t=35, b=24),
        font=dict(family='Arial', color='#587078', size=11),
        showlegend=leyenda,
        hoverlabel=dict(bgcolor='#18343d', font_color='white'),
        xaxis=dict(showgrid=True, gridcolor='#e8efed', zeroline=False, title=None),
        yaxis=dict(showgrid=False, title=None),
    )
    return figura


app.layout = html.Div([
    html.Header([
        html.Div([
            html.Div('OM', className='brand-mark'),
            html.Div([
                html.Div('DATOS ABIERTOS · COLOMBIA', className='eyebrow'),
                html.Div('Observatorio de Mortalidad', className='brand-title'),
            ]),
        ], className='brand'),
        html.Div('ESTADÍSTICAS VITALES · 2019', className='header-note'),
    ], className='topbar'),
    html.Main([
        html.Section([
            html.Div([
                html.Div('COLOMBIA · DEFUNCIONES NO FETALES', className='eyebrow hero-eyebrow'),
                html.H1('Una mirada territorial\na la mortalidad.', className='hero-title'),
                html.P('Explora los patrones de mortalidad por territorio, tiempo, sexo y ciclo de vida.', className='hero-copy'),
                html.Div([html.Span('●', className='status-dot'), ' Fuentes: DANE · Estadísticas vitales y proyecciones de población'], className='source-note'),
            ], className='hero-text'),
            html.Img(src='/assets/observatorio.svg', className='hero-image', alt='Gráfico de datos y lupa'),
        ], className='hero'),
        html.Section([
            html.Div([
                html.Div([
                    html.Div('01', className='section-index'),
                    html.Div([html.H2('Panel de exploración'), html.P('Usa el filtro para comparar Colombia con un departamento.')]),
                ], className='section-heading'),
                html.Div([
                    html.Label('TERRITORIO DE ANÁLISIS', htmlFor='dropdown-departamento'),
                    dcc.Dropdown(
                        id='dropdown-departamento',
                        options=[{'label': 'Colombia completa', 'value': TODOS}] + [
                            {'label': nombre.title(), 'value': nombre} for nombre in DEPARTAMENTOS
                        ],
                        value=TODOS, clearable=False, searchable=True,
                        className='dashboard-dropdown',
                    ),
                ], className='control territory-control'),
            ], className='explorer-head'),
            html.Div([
                html.Div([
                    html.Div([html.Div('01 · TERRITORIO', className='chart-kicker'), html.Div('Defunciones por departamento · círculos por centroide departamental', className='chart-subtitle')], className='chart-meta'),
                    dcc.Graph(id='mapa-departamentos', config={'displayModeBar': False, 'responsive': True}, style={'height': 'clamp(380px, 52vh, 500px)', 'width': '100%'}),
                ], className='chart-card grid-wide'),
                html.Div([
                    html.Div([html.Div('02 · TIEMPO', className='chart-kicker'), html.Div('Total de defunciones por mes', className='chart-subtitle')], className='chart-meta'),
                    dcc.Graph(id='grafico-mensual', config={'displayModeBar': False, 'responsive': True}, style={'height': 'clamp(320px, 42vh, 390px)', 'width': '100%'}),
                ], className='chart-card grid-wide'),
                html.Div([
                    html.Div([html.Div('03 · VIOLENCIA', className='chart-kicker'), html.Div('Municipios con más homicidios por arma de fuego · CIE-10 X95*', className='chart-subtitle')], className='chart-meta'),
                    dcc.Graph(id='grafico-homicidios', config={'displayModeBar': False, 'responsive': True}, style={'height': 'clamp(320px, 42vh, 390px)', 'width': '100%'}),
                ], className='chart-card'),
                html.Div([
                    html.Div([html.Div('04 · TASA MUNICIPAL', className='chart-kicker'), html.Div('10 municipios con menor tasa por 100.000 habitantes', className='chart-subtitle')], className='chart-meta'),
                    dcc.Graph(id='grafico-tasa-baja', config={'displayModeBar': False, 'responsive': True}, style={'height': 'clamp(340px, 44vh, 410px)', 'width': '100%'}),
                    html.P('Tasa calculada con defunciones registradas / población total proyectada por DANE para 2019.', className='chart-note'),
                ], className='chart-card'),
                html.Div([
                    html.Div([html.Div('05 · CAUSAS', className='chart-kicker'), html.Div('10 principales causas de muerte · ordenadas de mayor a menor', className='chart-subtitle')], className='chart-meta'),
                    html.Div(id='tabla-causas', className='table-wrap'),
                ], className='chart-card'),
                html.Div([
                    html.Div([html.Div('06 · SEXO Y TERRITORIO', className='chart-kicker'), html.Div('Comparación de defunciones por sexo en cada departamento', className='chart-subtitle')], className='chart-meta'),
                    dcc.Graph(id='grafico-sexo-departamento', config={'displayModeBar': False, 'responsive': True}, style={'height': 'clamp(420px, 54vh, 520px)', 'width': '100%'}),
                ], className='chart-card'),
                html.Div([
                    html.Div([html.Div('07 · CICLO DE VIDA', className='chart-kicker'), html.Div('Defunciones por rangos de edad agrupados según GRUPO_EDAD1', className='chart-subtitle')], className='chart-meta'),
                    dcc.Graph(id='histograma-edades', config={'displayModeBar': False, 'responsive': True}, style={'height': 'clamp(360px, 46vh, 440px)', 'width': '100%'}),
                    html.Details([
                        html.Summary('Ver rangos de edad usados'),
                        html.Ul([html.Li(f'{nombre}: códigos {min(codigos)}–{max(codigos)} · {rango}') for nombre, codigos, rango in rangos_edad]),
                    ], className='age-reference'),
                ], className='chart-card grid-wide'),
            ], className='dashboard-grid'),
        ], className='explorer'),
        html.Footer([
            html.Span('OBSERVATORIO DE MORTALIDAD · PROYECTO ACADÉMICO'),
            html.A('Población municipal 2019: DANE', href='https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion', target='_blank'),
        ], className='footer'),
    ], className='page-content'),
], className='app-shell')


@callback(
    Output('mapa-departamentos', 'figure'),
    Output('grafico-mensual', 'figure'),
    Output('grafico-homicidios', 'figure'),
    Output('grafico-tasa-baja', 'figure'),
    Output('tabla-causas', 'children'),
    Output('grafico-sexo-departamento', 'figure'),
    Output('histograma-edades', 'figure'),
    Input('dropdown-departamento', 'value'),
)
def actualizar_panel(territorio):
    df = df_mortalidad if territorio == TODOS else df_mortalidad[df_mortalidad['DEPARTAMENTO'] == territorio]
    etiqueta_territorio = 'Colombia' if territorio == TODOS else territorio.title()

    # Mapa nacional de burbujas: ubicación departamental aproximada, tamaño y color por total.
    defunciones_departamento = df_mortalidad.groupby('DEPARTAMENTO').size().rename('DEFUNCIONES').reset_index()
    mapa = defunciones_departamento.merge(centroides_departamento, on='DEPARTAMENTO', how='inner')
    figura_mapa = px.scatter_geo(
        mapa, lat='LATITUD', lon='LONGITUD', size='DEFUNCIONES', color='DEFUNCIONES',
        hover_name='DEPARTAMENTO', hover_data={'LATITUD': False, 'LONGITUD': False, 'DEFUNCIONES': ':,.0f'},
        color_continuous_scale=['#dcefe9', '#22a699', '#126978'], size_max=38,
        labels={'DEFUNCIONES': 'Defunciones'},
    )
    figura_mapa.update_geos(
        scope='south america', center={'lat': 4.5, 'lon': -73.5}, projection_scale=4.3,
        showcountries=True, countrycolor='#b9cbc7', showland=True, landcolor='#f3f7f5',
        showocean=True, oceancolor='#eaf3f4', coastlinecolor='#d7e2df',
    )
    figura_mapa.update_layout(coloraxis_colorbar={'title': 'Defunciones', 'thickness': 12}, margin=dict(l=8, r=34, t=8, b=8), height=480)
    estilo_figura(figura_mapa, alto=480)

    # Evolución mensual de defunciones.
    serie_mensual = df.groupby('MES').size().reindex(range(1, 13), fill_value=0).rename('DEFUNCIONES').reset_index()
    serie_mensual['MES'] = serie_mensual['MES'].map(lambda numero: meses[int(numero) - 1])
    figura_mensual = px.line(
        serie_mensual, x='MES', y='DEFUNCIONES', markers=True,
        labels={'MES': 'Mes', 'DEFUNCIONES': 'Defunciones'},
        color_discrete_sequence=[colores[0]],
    )
    figura_mensual.update_traces(line={'width': 3}, marker={'size': 8}, hovertemplate='%{x}<br><b>%{y:,.0f}</b> defunciones<extra></extra>')
    estilo_figura(figura_mensual, alto=340)

    # Homicidios por arma de fuego codificados X95 en CIE-10.
    homicidios = df[
        df['MANERA_MUERTE'].astype('string').str.casefold().eq('homicidio')
        & df['COD_MUERTE'].astype('string').str.startswith('X95', na=False)
    ]
    ciudades_violentas = homicidios.groupby(['MUNICIPIO', 'DEPARTAMENTO']).size().rename('DEFUNCIONES').reset_index()
    ciudades_violentas = ciudades_violentas.nlargest(5, 'DEFUNCIONES').sort_values('DEFUNCIONES')
    figura_homicidios = px.bar(
        ciudades_violentas, x='DEFUNCIONES', y='MUNICIPIO', orientation='h',
        color_discrete_sequence=[colores[4]], custom_data=['DEPARTAMENTO'],
        labels={'MUNICIPIO': 'Municipio', 'DEFUNCIONES': 'Casos'},
    )
    figura_homicidios.update_traces(hovertemplate='%{y} · %{customdata[0]}<br><b>%{x:,.0f}</b> homicidios X95<extra></extra>')
    estilo_figura(figura_homicidios, alto=350)

    # Tasa municipal por 100.000 habitantes usando población DANE de 2019.
    defunciones_municipio = df.groupby('COD_DANE').size().rename('DEFUNCIONES').reset_index()
    universo_tasas = df_poblacion if territorio == TODOS else df_poblacion[df_poblacion['DEPARTAMENTO'] == territorio]
    tasas = universo_tasas.merge(defunciones_municipio, on='COD_DANE', how='left')
    tasas['DEFUNCIONES'] = tasas['DEFUNCIONES'].fillna(0)
    tasas['TASA_100K'] = tasas['DEFUNCIONES'] / tasas['POBLACION'] * 100000
    municipios_menor_tasa = tasas[ tasas['POBLACION'] > 0 ].nsmallest(10, 'TASA_100K').sort_values('TASA_100K', ascending=False)
    figura_tasa = px.pie(
        municipios_menor_tasa, names='MUNICIPIO', values='TASA_100K', hole=0.42,
        custom_data=['DEPARTAMENTO', 'DEFUNCIONES'], color_discrete_sequence=colores,
    )
    figura_tasa.update_traces(
        textposition='inside', textinfo='label+percent',
        hovertemplate='%{label} · %{customdata[0]}<br>Tasa: %{value:.1f} por 100.000<br>Defunciones: %{customdata[1]:,.0f}<extra></extra>',
    )
    estilo_figura(figura_tasa, alto=370, leyenda=False)

    # Tabla con las 10 causas más frecuentes y su descripción oficial.
    principales = df.groupby('COD_MUERTE').size().rename('TOTAL_CASOS').nlargest(10).reset_index()
    principales['CAUSA'] = principales['COD_MUERTE'].map(causa_por_codigo).fillna('Descripción no disponible en el catálogo')
    filas_tabla = [
        html.Tr([html.Th('Código CIE-10'), html.Th('Nombre de la causa'), html.Th('Casos')]),
        *[
            html.Tr([
                html.Td(fila.COD_MUERTE), html.Td(fila.CAUSA), html.Td(f'{int(fila.TOTAL_CASOS):,}'.replace(',', '.')),
            ])
            for fila in principales.itertuples(index=False)
        ],
    ]
    tabla = html.Table(filas_tabla, className='causes-table')

    # Defunciones por sexo y departamento (o el territorio seleccionado).
    resumen_sexo = df.groupby(['DEPARTAMENTO', 'SEXO_LABEL']).size().rename('DEFUNCIONES').reset_index()
    figura_sexo = px.bar(
        resumen_sexo, x='DEPARTAMENTO', y='DEFUNCIONES', color='SEXO_LABEL', barmode='stack',
        color_discrete_map={'Masculino': colores[0], 'Femenino': colores[2], 'Sin especificar': colores[3]},
        labels={'DEPARTAMENTO': 'Departamento', 'DEFUNCIONES': 'Defunciones', 'SEXO_LABEL': 'Sexo'},
    )
    figura_sexo.update_layout(xaxis_tickangle=-55, legend_title_text='Sexo')
    estilo_figura(figura_sexo, alto=500, leyenda=True)

    # Distribución por ciclo de vida según los rangos de GRUPO_EDAD1 de la referencia.
    edades = df.groupby('CICLO_VIDA').size().reindex(orden_edades, fill_value=0).rename('DEFUNCIONES').reset_index()
    edades['CICLO_VIDA'] = pd.Categorical(edades['CICLO_VIDA'], categories=orden_edades, ordered=True)
    figura_edades = px.bar(
        edades, x='CICLO_VIDA', y='DEFUNCIONES', color_discrete_sequence=[colores[1]],
        labels={'CICLO_VIDA': 'Etapa / rango de edad', 'DEFUNCIONES': 'Defunciones'},
    )
    figura_edades.update_traces(hovertemplate='%{x}<br><b>%{y:,.0f}</b> defunciones<extra></extra>')
    figura_edades.update_layout(xaxis_tickangle=-25)
    estilo_figura(figura_edades, alto=400)

    return figura_mapa, figura_mensual, figura_homicidios, figura_tasa, tabla, figura_sexo, figura_edades


if __name__ == '__main__':
    app.run(debug=True)
