from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
ASSETS_DIR = BASE_DIR / 'assets'

st.set_page_config(
    page_title='Observatorio de Mortalidad | Colombia 2019',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded',
)

st.markdown('''
<style>
:root{--ink:#17363d;--muted:#6b8184;--teal:#137b86;--mint:#eaf5f1;--line:#e5eeea;--paper:#fff;--bg:#f5f8f6}
[data-testid="stAppViewContainer"]{background:var(--bg);color:var(--ink)}
[data-testid="stHeader"]{background:rgba(245,248,246,.8)}
.block-container{max-width:1550px;padding:1.6rem clamp(1rem,4vw,3.5rem) 2rem}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line)}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:16px;padding:14px 18px}
[data-testid="stMetricLabel"]{color:#718987}
.hero-panel{background:linear-gradient(110deg,#edf7f3,#e6f1ee);border:1px solid #e0eee9;border-radius:24px;padding:30px 36px;margin:0 0 24px}
.hero-kicker,.chart-kicker{font-size:.68rem;letter-spacing:.14em;font-weight:700;color:var(--teal);text-transform:uppercase}
.hero-title{font-size:clamp(2rem,3.5vw,3.2rem);line-height:1.08;font-weight:800;letter-spacing:-.04em;color:var(--ink);margin:.55rem 0}
.hero-copy{font-size:1rem;color:#627c7e;max-width:680px}
div[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border:1px solid var(--line);border-radius:18px;padding:10px 14px;box-shadow:0 8px 28px rgba(29,72,68,.035)}
[data-testid="stPlotlyChart"]{width:100%}
.chart-subtitle{font-size:.85rem;color:var(--muted);margin:.2rem 0 .6rem}
.footer{color:#829796;font-size:.75rem;padding:1rem .2rem;border-top:1px solid var(--line);margin-top:1.5rem}
@media(max-width:700px){.hero-panel{padding:23px 20px}.block-container{padding-left:1rem;padding-right:1rem}}
</style>
''', unsafe_allow_html=True)

MESES = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]
COLORES = ['#167d8d', '#22a699', '#78c7b5', '#f1b96a', '#ee8f72', '#8c79b8']
TODOS = 'COLOMBIA COMPLETA'
RANGOS_EDAD = [
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
ORDEN_EDADES = [nombre for nombre, _, _ in RANGOS_EDAD] + ['Edad sin clasificar']
EDAD_A_CATEGORIA = {codigo: nombre for nombre, codigos, _ in RANGOS_EDAD for codigo in codigos}


def normalizar_codigo(valor):
    if pd.isna(valor):
        return None
    return str(valor).strip().removesuffix('.0').zfill(5)


def normalizar_texto(serie):
    return serie.astype('string').str.strip().str.upper()


def categoria_edad(valor):
    try:
        return EDAD_A_CATEGORIA.get(int(valor), 'Edad sin clasificar')
    except (TypeError, ValueError):
        return 'Edad sin clasificar'


@st.cache_data(show_spinner='Cargando y preparando las bases DANE…')
def cargar_datos():
    defunciones = pd.read_excel(
        DATA_DIR / 'Anexo1.NoFetal2019_CE_15-03-23.xlsx',
        sheet_name='No_Fetales_2019',
        usecols=['COD_DANE', 'MES', 'SEXO', 'GRUPO_EDAD1', 'MANERA_MUERTE', 'COD_MUERTE'],
    )
    municipios = pd.read_excel(
        DATA_DIR / 'Divipola_CE_.xlsx',
        sheet_name='Hoja1',
        usecols=['COD_DANE', 'DEPARTAMENTO', 'MUNICIPIO'],
        dtype={'COD_DANE': str},
    )
    defunciones['COD_DANE'] = defunciones['COD_DANE'].map(normalizar_codigo)
    municipios['COD_DANE'] = municipios['COD_DANE'].map(normalizar_codigo)
    municipios['DEPARTAMENTO'] = normalizar_texto(municipios['DEPARTAMENTO'])
    municipios['MUNICIPIO'] = normalizar_texto(municipios['MUNICIPIO'])
    municipios = municipios.drop_duplicates('COD_DANE')
    defunciones = defunciones.merge(municipios, on='COD_DANE', how='left')
    defunciones['DEPARTAMENTO'] = defunciones['DEPARTAMENTO'].fillna('SIN DEPARTAMENTO')
    defunciones['MUNICIPIO'] = defunciones['MUNICIPIO'].fillna('SIN MUNICIPIO')
    defunciones['MES'] = pd.to_numeric(defunciones['MES'], errors='coerce').astype('Int64')
    defunciones['COD_MUERTE'] = defunciones['COD_MUERTE'].astype('string').str.strip().str.upper()
    defunciones['SEXO_LABEL'] = pd.to_numeric(defunciones['SEXO'], errors='coerce').map(
        {1: 'Masculino', 2: 'Femenino', 3: 'Sin especificar'}
    ).fillna('Sin especificar')
    defunciones['CICLO_VIDA'] = defunciones['GRUPO_EDAD1'].map(categoria_edad)

    catalogo = pd.read_excel(
        DATA_DIR / 'Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx',
        sheet_name='Final', skiprows=9, header=None, usecols='C:F',
    )
    causa_por_codigo = {}
    for codigo_3, descripcion_3, codigo_4, descripcion_4 in catalogo.itertuples(index=False, name=None):
        if pd.notna(codigo_3) and pd.notna(descripcion_3):
            causa_por_codigo[str(codigo_3).strip().upper()] = str(descripcion_3).strip()
        if pd.notna(codigo_4) and pd.notna(descripcion_4):
            causa_por_codigo[str(codigo_4).strip().upper()] = str(descripcion_4).strip()

    coordenadas = pd.read_excel(
        DATA_DIR / 'Divipola_CE_.xlsx', sheet_name='Hoja3', skiprows=2,
        header=None, usecols='A:G',
    ).iloc[:, [1, 5, 6]].copy()
    coordenadas.columns = ['DEPARTAMENTO', 'LONGITUD', 'LATITUD']
    coordenadas['DEPARTAMENTO'] = normalizar_texto(coordenadas['DEPARTAMENTO'])
    for columna in ['LONGITUD', 'LATITUD']:
        coordenadas[columna] = pd.to_numeric(
            coordenadas[columna].astype('string').str.replace(',', '.', regex=False), errors='coerce'
        )
    centroides = (
        coordenadas.dropna(subset=['LONGITUD', 'LATITUD'])
        .groupby('DEPARTAMENTO', as_index=False)
        .agg(LONGITUD=('LONGITUD', 'mean'), LATITUD=('LATITUD', 'mean'))
    )

    poblacion = pd.read_excel(
        DATA_DIR / 'Poblacion_Municipal_DANE_2018_2042.xlsx',
        sheet_name='PobMunicipalxÁrea', header=7, usecols='A:G',
    ).iloc[:, [0, 2, 4, 5, 6]].copy()
    poblacion.columns = ['COD_DEPARTAMENTO', 'COD_MUNICIPIO', 'ANIO', 'AREA', 'POBLACION']
    poblacion = poblacion[
        pd.to_numeric(poblacion['ANIO'], errors='coerce').eq(2019)
        & poblacion['AREA'].astype('string').str.strip().str.casefold().eq('total')
    ].copy()
    poblacion['COD_DANE'] = poblacion['COD_MUNICIPIO'].map(normalizar_codigo)
    poblacion['POBLACION'] = pd.to_numeric(poblacion['POBLACION'], errors='coerce')
    poblacion = poblacion.dropna(subset=['COD_DANE', 'POBLACION']).drop_duplicates('COD_DANE')
    poblacion = poblacion.merge(municipios, on='COD_DANE', how='left')
    return defunciones, poblacion, causa_por_codigo, centroides


def estilo_figura(figura, alto=360, leyenda=False):
    figura.update_layout(
        template='plotly_white', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=alto, margin=dict(l=16, r=24, t=35, b=28),
        font=dict(family='Arial', color='#587078', size=11), showlegend=leyenda,
        hoverlabel=dict(bgcolor='#18343d', font_color='white'),
        xaxis=dict(showgrid=True, gridcolor='#e8efed', zeroline=False, title=None),
        yaxis=dict(showgrid=False, title=None),
    )
    return figura


def grafico_mapa(defunciones, centroides):
    por_departamento = defunciones.groupby('DEPARTAMENTO').size().rename('DEFUNCIONES').reset_index()
    mapa = por_departamento.merge(centroides, on='DEPARTAMENTO', how='inner')
    figura = px.scatter_geo(
        mapa, lat='LATITUD', lon='LONGITUD', size='DEFUNCIONES', color='DEFUNCIONES',
        hover_name='DEPARTAMENTO',
        hover_data={'LATITUD': False, 'LONGITUD': False, 'DEFUNCIONES': ':,.0f'},
        color_continuous_scale=['#dcefe9', '#22a699', '#126978'], size_max=38,
        labels={'DEFUNCIONES': 'Defunciones'},
    )
    figura.update_geos(
        scope='south america', center={'lat': 4.5, 'lon': -73.5}, projection_scale=4.3,
        showcountries=True, countrycolor='#b9cbc7', showland=True, landcolor='#f3f7f5',
        showocean=True, oceancolor='#eaf3f4', coastlinecolor='#d7e2df',
    )
    figura.update_layout(coloraxis_colorbar={'title': 'Defunciones', 'thickness': 12}, height=480)
    return estilo_figura(figura, alto=480)


def renderizar_panel(df, poblacion, causa_por_codigo, centroides, territorio):
    mapa, mensual = st.columns(2)
    with mapa:
        with st.container(border=True):
            st.markdown('<div class="chart-kicker">01 · TERRITORIO</div><div class="chart-subtitle">Defunciones por departamento · círculos por centroide departamental</div>', unsafe_allow_html=True)
            st.plotly_chart(grafico_mapa(df, centroides), use_container_width=True, config={'displayModeBar': False, 'responsive': True})
    with mensual:
        with st.container(border=True):
            st.markdown('<div class="chart-kicker">02 · TIEMPO</div><div class="chart-subtitle">Total de defunciones por mes</div>', unsafe_allow_html=True)
            serie = df.groupby('MES').size().reindex(range(1, 13), fill_value=0).rename('DEFUNCIONES').reset_index()
            serie['MES'] = serie['MES'].map(lambda numero: MESES[int(numero) - 1])
            figura = px.line(serie, x='MES', y='DEFUNCIONES', markers=True, color_discrete_sequence=[COLORES[0]], labels={'MES': 'Mes', 'DEFUNCIONES': 'Defunciones'})
            figura.update_traces(line={'width': 3}, marker={'size': 8}, hovertemplate='%{x}<br><b>%{y:,.0f}</b> defunciones<extra></extra>')
            st.plotly_chart(estilo_figura(figura, 350), use_container_width=True, config={'displayModeBar': False, 'responsive': True})

    homicidios, tasas_box = st.columns(2)
    with homicidios:
        with st.container(border=True):
            st.markdown('<div class="chart-kicker">03 · VIOLENCIA</div><div class="chart-subtitle">Municipios con más homicidios por arma de fuego · CIE-10 X95*</div>', unsafe_allow_html=True)
            seleccion_homicidios = df[
                df['MANERA_MUERTE'].astype('string').str.casefold().eq('homicidio')
                & df['COD_MUERTE'].astype('string').str.startswith('X95', na=False)
            ]
            top_ciudades = seleccion_homicidios.groupby(['MUNICIPIO', 'DEPARTAMENTO']).size().rename('DEFUNCIONES').reset_index()
            top_ciudades = top_ciudades.nlargest(5, 'DEFUNCIONES').sort_values('DEFUNCIONES')
            figura = px.bar(top_ciudades, x='DEFUNCIONES', y='MUNICIPIO', orientation='h', custom_data=['DEPARTAMENTO'], color_discrete_sequence=[COLORES[4]], labels={'MUNICIPIO': 'Municipio', 'DEFUNCIONES': 'Casos'})
            figura.update_traces(hovertemplate='%{y} · %{customdata[0]}<br><b>%{x:,.0f}</b> homicidios X95<extra></extra>')
            st.plotly_chart(estilo_figura(figura, 360), use_container_width=True, config={'displayModeBar': False, 'responsive': True})
    with tasas_box:
        with st.container(border=True):
            st.markdown('<div class="chart-kicker">04 · TASA MUNICIPAL</div><div class="chart-subtitle">10 municipios con menor tasa por 100.000 habitantes</div>', unsafe_allow_html=True)
            defunciones_municipio = df.groupby('COD_DANE').size().rename('DEFUNCIONES').reset_index()
            tasas = poblacion.merge(defunciones_municipio, on='COD_DANE', how='left')
            tasas['DEFUNCIONES'] = tasas['DEFUNCIONES'].fillna(0)
            tasas['TASA_100K'] = tasas['DEFUNCIONES'] / tasas['POBLACION'] * 100000
            menores = tasas[tasas['POBLACION'] > 0].nsmallest(10, 'TASA_100K').sort_values('TASA_100K', ascending=False)
            figura = px.pie(menores, names='MUNICIPIO', values='TASA_100K', hole=0.42, custom_data=['DEPARTAMENTO', 'DEFUNCIONES'], color_discrete_sequence=COLORES)
            figura.update_traces(textposition='inside', textinfo='label+percent', hovertemplate='%{label} · %{customdata[0]}<br>Tasa: %{value:.1f} por 100.000<br>Defunciones: %{customdata[1]:,.0f}<extra></extra>')
            st.plotly_chart(estilo_figura(figura, 360), use_container_width=True, config={'displayModeBar': False, 'responsive': True})
            st.caption('Tasa calculada con población total proyectada por DANE para 2019.')

    causas_col, sexo_col = st.columns(2)
    with causas_col:
        with st.container(border=True):
            st.markdown('<div class="chart-kicker">05 · CAUSAS</div><div class="chart-subtitle">10 principales causas de muerte · ordenadas de mayor a menor</div>', unsafe_allow_html=True)
            principales = df.groupby('COD_MUERTE').size().rename('TOTAL_CASOS').nlargest(10).reset_index()
            principales['NOMBRE_CAUSA'] = principales['COD_MUERTE'].map(causa_por_codigo).fillna('Descripción no disponible en el catálogo')
            principales = principales[['COD_MUERTE', 'NOMBRE_CAUSA', 'TOTAL_CASOS']].rename(columns={'COD_MUERTE': 'Código CIE-10', 'NOMBRE_CAUSA': 'Nombre de la causa', 'TOTAL_CASOS': 'Casos'})
            st.dataframe(principales, hide_index=True, use_container_width=True, height=410)
    with sexo_col:
        with st.container(border=True):
            st.markdown('<div class="chart-kicker">06 · SEXO Y TERRITORIO</div><div class="chart-subtitle">Defunciones por sexo en cada departamento</div>', unsafe_allow_html=True)
            resumen = df.groupby(['DEPARTAMENTO', 'SEXO_LABEL']).size().rename('DEFUNCIONES').reset_index()
            figura = px.bar(resumen, x='DEPARTAMENTO', y='DEFUNCIONES', color='SEXO_LABEL', barmode='stack', color_discrete_map={'Masculino': COLORES[0], 'Femenino': COLORES[2], 'Sin especificar': COLORES[3]}, labels={'DEPARTAMENTO': 'Departamento', 'DEFUNCIONES': 'Defunciones', 'SEXO_LABEL': 'Sexo'})
            figura.update_layout(xaxis_tickangle=-55, legend_title_text='Sexo')
            st.plotly_chart(estilo_figura(figura, 500, leyenda=True), use_container_width=True, config={'displayModeBar': False, 'responsive': True})

    with st.container(border=True):
        st.markdown('<div class="chart-kicker">07 · CICLO DE VIDA</div><div class="chart-subtitle">Defunciones agrupadas según los rangos de GRUPO_EDAD1</div>', unsafe_allow_html=True)
        edades = df.groupby('CICLO_VIDA').size().reindex(ORDEN_EDADES, fill_value=0).rename('DEFUNCIONES').reset_index()
        edades['CICLO_VIDA'] = pd.Categorical(edades['CICLO_VIDA'], categories=ORDEN_EDADES, ordered=True)
        figura = px.bar(edades, x='CICLO_VIDA', y='DEFUNCIONES', color_discrete_sequence=[COLORES[1]], labels={'CICLO_VIDA': 'Etapa / rango de edad', 'DEFUNCIONES': 'Defunciones'})
        figura.update_traces(hovertemplate='%{x}<br><b>%{y:,.0f}</b> defunciones<extra></extra>')
        figura.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(estilo_figura(figura, 410), use_container_width=True, config={'displayModeBar': False, 'responsive': True})
        with st.expander('Ver rangos de edad usados'):
            for nombre, codigos, rango in RANGOS_EDAD:
                st.write(f'• **{nombre}:** códigos {min(codigos)}–{max(codigos)} · {rango}')


def main():
    defunciones, poblacion, causas, centroides = cargar_datos()
    departamentos = sorted(defunciones.loc[defunciones['DEPARTAMENTO'] != 'SIN DEPARTAMENTO', 'DEPARTAMENTO'].dropna().unique())
    with st.sidebar:
        st.image(str(ASSETS_DIR / 'observatorio.svg'), width=150)
        st.markdown('## Observatorio de Mortalidad')
        st.caption('Estadísticas vitales de Colombia · 2019')
        st.divider()
        territorio = st.selectbox(
            'Territorio de análisis', [TODOS] + departamentos,
            format_func=lambda valor: 'Colombia completa' if valor == TODOS else valor.title(),
        )
        st.caption('El mapa conserva la vista nacional; el filtro aplica a los demás análisis.')
        st.divider()
        st.caption('Fuentes: DANE · Estadísticas vitales, DIVIPOLA y proyecciones de población.')

    filtradas = defunciones if territorio == TODOS else defunciones[defunciones['DEPARTAMENTO'] == territorio]
    nombre_territorio = 'Colombia' if territorio == TODOS else territorio.title()

    izquierda, derecha = st.columns([1.35, .65], vertical_alignment='center')
    with izquierda:
        st.markdown('<div class="hero-kicker">COLOMBIA · DEFUNCIONES NO FETALES</div><div class="hero-title">Una mirada territorial<br>a la mortalidad.</div><div class="hero-copy">Explora patrones por territorio, tiempo, sexo y ciclo de vida.</div>', unsafe_allow_html=True)
        st.caption('Fuente: estadísticas vitales · DANE')
    with derecha:
        st.image(str(ASSETS_DIR / 'observatorio.svg'), width=300)

    st.markdown('### Panel de exploración')
    st.caption(f'Vista actual: **{nombre_territorio} · 2019**')
    k1, k2, k3 = st.columns(3)
    k1.metric('Defunciones registradas', f'{len(filtradas):,}'.replace(',', '.'))
    k2.metric('Municipios con registros', f'{filtradas.loc[filtradas.MUNICIPIO != "SIN MUNICIPIO", "MUNICIPIO"].nunique():,}'.replace(',', '.'))
    k3.metric('Departamentos', f'{filtradas.loc[filtradas.DEPARTAMENTO != "SIN DEPARTAMENTO", "DEPARTAMENTO"].nunique():,}')

    renderizar_panel(filtradas, poblacion if territorio == TODOS else poblacion[poblacion['DEPARTAMENTO'] == territorio], causas, centroides, territorio)
    st.markdown('<div class="footer">OBSERVATORIO DE MORTALIDAD · PROYECTO ACADÉMICO · <a href="https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion" target="_blank">Proyecciones de población DANE</a></div>', unsafe_allow_html=True)


if __name__ == '__main__':
    main()
