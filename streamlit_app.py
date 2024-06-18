#!/usr/bin/env python
# coding: utf-8

# In[4]:

import streamlit as st
import pandas as pd
import altair as alt
import statsmodels.formula.api as sm


# In[5]:


def unico(df):
    i = 0
    for col in df.columns:
        if df[col].nunique() == 1:
            print(col)
            i +=1
    if i == 0:
        print('No hay columnas con un unico valor')
def elimina_col_unicas(df):
    '''
    Elimina de un dataframe dado aquellas columnas con un unico valor
    INPUT:
    df: El dataframe a limpiar
    OUTPUT:
    El dataframe procesado
    '''
    col_to_drop = []
    for col in df.columns:
        if df[col].nunique() == 1:
            col_to_drop.append(col)
    return df.drop(columns = col_to_drop)
def turquia(df):
    '''
    Unifica el nombre registrado para Turquía
    '''
    df.Country = df.Country.replace({'Türkiye':'Turkey'})
    return df


# # Preprocesado y Carga de datos

# ## recursos: EAG_FIN_SOURCE
# Describe los recursos destinados por cada pais a la educación

# In[6]:


recursos = pd.read_csv('datos/EAG_FIN_SOURCE.csv')
columns_to_drop = ['Flag Codes', 'Flags','YEAR']
for col in recursos.columns:
    if len(recursos[col].unique()) == 1:
        columns_to_drop.append(col)
recursos = (recursos
 .drop(columns = columns_to_drop)
 .dropna()
)


# Vamos a definir una función para preprocesar los  archivos con información sobre el empleo y el nivel de estudios:
# - EAG_NEAC
# - EAG_NEAC_unemploy
# - EAG_NEAC_employment
# 
# Esta función elimina las columanas que solo tienen un valor (provienen de haber filtrado la información de la base de datos al descargar el archivo, y debido a ello ahora no aportan información)
# 
# También eliminaremos algunas columnas innecesarias para nuestro análisis. Columnas que vamos a eliminar:  
# COUNTRY: Es el código del país, nos podemos quedar con el nombre del país.  
# Unit Code: Tiene solo un valor: PC (porcentaje), salvo los valores nulos.  
# Unit: Igual que la columna Unit Code  
# Flag Codes: Informan de metadatos de algunos registros    
# Flags: Informan de metadatos de algunos registros  
# Reference Period Code: Es el año, y esa información la tenemos en la columna reference Period 
# 
# También eliminamos las filas con datos faltantes.

# In[7]:


def preprocesado_1(df):
    '''
    Esta función elimina las columnas con un solo valor.
    Elimina una selección de columnas
    Elimina los valores faltantes
    Devuelve el dataframe preprocesado, con el índice reseteado.
    Convierte la columna con fechas en entero, y renombra la columna a Year
    '''
    columns_to_drop = []
    for col in df.columns:
        if df[col].nunique() == 1:
            columns_to_drop.append(col)
    df = df.drop(columns = columns_to_drop)
    columns_to_drop2 = ['COUNTRY','Flag Codes','Flags','Reference Period Code']
    df = df.drop(columns = columns_to_drop2)
    df = df.dropna()
    df['Reference Period'] = df['Reference Period'].astype('int32')
    df = df.rename(columns={'Reference Period':'Year'})
    df = turquia(df)
    return df.reset_index(drop=True)
    


# ## estudios: EAG_NEAC
# Porcentaje de población por nivel estudios
# 
# Tenemos muy pocos registros anteriores al 2022, asi que nos centraremos en hacer el estudio en ese año

# In[8]:


estudios = preprocesado_1(pd.read_csv('datos/EAG_NEAC.csv'))
estudios = estudios[estudios.Year == 2022].drop(columns='Year')


# ## desempleo: EAG_NEAC_unemploy
# Porcentaje de desempleo por nivel estudios
# 
# Utilizamos la función definida anteriormente para preprocesar los datos con información académica, ya que tienen columnas similares

# In[9]:


desempleo = preprocesado_1(pd.read_csv('datos/EAG_NEAC_unenploy.csv'))


# ## empleo: EAG_NEAC_employment
# Porcentaje de empleados por nivel estudios
# 
# Utilizamos la función definida anteriormente para preprocesar los datos con información académica, ya que tienen columnas similares

# In[10]:


empleo = preprocesado_1(pd.read_csv('datos/EAG_NEAC_employment.csv'))


# ## ratio: EAG_PERS_RATIO
# This dataset shows the ratio of full-time students to full-time teaching staff, as well as the average class size at a given level of education and type of institution.
# 
# Vamos a quedarnos con las instituciones públicas y con la ratio en los niveles de educación secundaria obligatoria.
# 
# Eliminamos las columnas Flag Codes, Flags y YEAR (duplicada en Year), COUNTRY (Código del país, presente en la columna Country) REF_SECTOR y Reference sector (ya que nos vamos a quedar con el sector público), INDICATOR' e Indicator, ya que solo nos quedaremos con la ratio alumno/profesor, y Education level, ya que indica el nivel educativo, y está ya codificado en la columna EDUCATION_LEV

# In[11]:


ratio = pd.read_csv('datos/EAG_PERS_RATIO.csv')
ratio = ratio[ratio['Education level'].isin(['Primary education','Lower secondary education'])]
ratio = ratio.query('INDICATOR == "PERS_AVG_CLASS" & REF_SECTOR == "INST_PUB"')
ratio = ratio.drop(columns=[
    'Flag Codes','Flags', 'YEAR','REF_SECTOR','Reference sector','INDICATOR','Indicator',
    'Education level','COUNTRY'])
ratio = ratio.dropna()
ratio = ratio.groupby(['Country','Year']).Value.mean().reset_index()
ratio = turquia(ratio)


# ## sueldo: EAG_TS_STA
# Teachers' statutory salaries: 
# This dataset presents internationally comparable data on (full-time) salaries of teachers in public institutions at pre-primary, primary and general (lower and upper) secondary education. Statutory salaries are displayed by level of education.
# 
# Eliminamos las columnas Flag Codes, Flags, Year y YEAR (Se ha descargado la información más reciente disponible, así que el año se ha codificado como 9999), COUNTRY (códigos de países), Level of education y Experience level están disponibles en otras columnas

# In[12]:


sueldo = pd.read_csv('datos/EAG_TS_STA.csv')
sueldo = sueldo.drop(columns = ['COUNTRY','Flag Codes','Flags','YEAR', 'Year','Level of education','Experience level'])
sueldo = sueldo.dropna().reset_index(drop=True)
sueldo = elimina_col_unicas(sueldo)
sueldo = turquia(sueldo)
sueldo = sueldo.groupby(['Country']).Value.mean().reset_index()
sueldo.Country = sueldo.Country.replace({'England (UK)':'United Kingdom'})


# ## economia: EAG_FIN_ANNEX_2  (SIN USO)
# Finance indicators - reference statistics  This dataset presents reference statistics (GDP, Total Government Expenditure, deflators, etc.) that are used to calculate some of the indicators on educational expenditure included in the indicators dataset.

# In[13]:


economia = pd.read_csv('datos/EAG_FIN_ANNEX_2.csv')
economia = economia.drop(columns = ['LOCATION','Flag Codes', 'Flags', 'TIME'])
economia = elimina_col_unicas(economia)
economia = turquia(economia)


# ## media_matematicas: Puntuación media de matemáticas en PISA

# Vamos a definir una función para preprocesar los datos provenientes de los archivos PDF que almacenan las medias en ciencias, lectura y matemátias

# In[14]:


def preproceso_medias(ruta):
    df = pd.read_excel(ruta)
    df = (df
          .rename(columns={'Column1':'Country', 'Column2':'score','Column4':'standard_deviation'})
         )
    df =df[['Country', 'score', 'standard_deviation']]
    df = df.iloc[3:]
    df = df.reset_index(drop=True)
    df =(df
         .assign(score = df.score.astype('int16'),
                 standard_deviation = df.standard_deviation.astype('int16'),
                 Country = df.Country.apply(lambda x: x.replace('*','')),
                 OECD = 1
                )
        )
    df.loc[38:, 'OECD'] = 0
    df = turquia(df)
    return df


# In[15]:


media_matematicas = preproceso_medias('datos/mean_score_mathematics.xlsx')
media_matematicas.Country = media_matematicas.Country.replace('Ukrainian regions (18 of 27)', 'Ukraine')


# ## media_lectura: Puntuación media en lectura en PISA

# In[16]:


media_lectura = preproceso_medias('datos/mean_score_reading.xlsx')
media_lectura.Country = media_lectura.Country.replace('Ukrainian regions (18 of 27)', 'Ukraine')


# ## media_ciencias: Puntuación media en ciencias en PISA

# In[17]:


media_ciencias = preproceso_medias('datos/mean_score_science.xlsx')
media_ciencias.Country = media_ciencias.Country.replace('Ukrainian regions (18 of 27)', 'Ukraine')


# Vamos a definir una función para los PDF que contienen información sobre los niveles de los estudiantes en ciencias, lectura y matemáticas. Necesitamos una pequeña variación en la función que preprocesa el archivo PDF de los niveles de ciencias

# In[18]:


def preproceso_niveles(ruta):
    df = pd.read_excel(ruta)
    df = (df
     .iloc[7:,[0,1,3,5,7,9,11,13,15,17]]
     .rename(columns={'Column1':'Country', 'Column2':'Below','Column4':'Level1c',
                     'Column6':'Level1b','Column8':'Level1a','Column10':'Level2',
                     'Column12':'Level3','Column14':'Level4','Column16':'Level5', 'Column18':'Level6'})
     .reset_index(drop=True)
    )
    df = (df
     .assign(
         Country = df.Country.apply(lambda x: x.replace('*','')),
         OECD = 1
         )
    )
    df.loc[38:, 'OECD'] = 0
    df.drop(columns = 'OECD', inplace=True)
    for col in df.columns:
        try:
            df[col] = df[col].astype('float')
        except:
            pass
    df = turquia(df)
    return df
def preproceso_niveles_ciencias(ruta):
    df = pd.read_excel(ruta)
    df = (df
     .iloc[7:,[0,1,3,5,7,9,11,13,15]]
     .rename(columns={'Column1':'Country', 'Column2':'Below','Column4':'Level1b',
                     'Column6':'Levela','Column8':'Level2','Column10':'Level3',
                     'Column12':'Level4','Column14':'Level5','Column16':'Level6'})
     .reset_index(drop=True)
    )
    df = (df
     .assign(
         Country = df.Country.apply(lambda x: x.replace('*','')),
         OECD = 1
         )
    )
    df.loc[38:, 'OECD'] = 0
    df.drop(columns = 'OECD', inplace=True)
    for col in df.columns:
        try:
            df[col] = df[col].astype('float')
        except:
            pass
    df = turquia(df)
    return df   


# ## niveles_matematicas: Porcentaje de estudiantes en cada nivel de matematicas

# In[19]:


niveles_matematicas = preproceso_niveles('datos/percentage_levels_mathematics.xlsx')
niveles_matematicas.Country = niveles_matematicas.Country.replace('Ukrainian regions (18 of 27)', 'Ukraine')


# ## niveles_lectura: Porcentaje de estudiantes en cada nivel de matematicas

# In[20]:


niveles_lectura = preproceso_niveles('datos/percentage_levels_reading.xlsx')
niveles_lectura.Country = niveles_lectura.Country.replace('Ukrainian regions (18 of 27)', 'Ukraine')


# ## niveles_ciencias: Porcentaje de estudiantes en cada nivel de matematicas

# In[21]:


niveles_ciencias = preproceso_niveles_ciencias('datos/percentage_levels_science.xlsx')
niveles_ciencias.Country = niveles_ciencias.Country.replace('Ukrainian regions (18 of 27)', 'Ukraine')


# ## media_matematicas_genero: Puntuación media de matemáticas diferenciadas por género
# 
# Vamos a definir una función para eliminar la columna OECD y convertir en decimales las puntuaciones

# In[22]:


def numerico_OECD(df, tipo_numero = 'int32', OECD=False):
    '''
    Convierte las columnas numéricas almacenadas como objeto en números (enteros)
    OECD indica si queremos conservar la columna OECD
    tipo_numero indica el tipo al que convertir las columnas numéricas
    '''
    for col in df.columns:
        if col in ['Country', 'OECD']:
            continue
        try:
            df[col] = df[col].astype(tipo_numero)
        except:
            pass
    if not OECD:
        df.drop(columns = 'OECD', inplace=True)
    df = turquia(df)
    return df


# In[23]:


media_matematicas_genero = pd.read_excel('datos/performance_by_gender_mathematics.xlsx')
media_matematicas_genero = (media_matematicas_genero
 .iloc[2:,[0,1,5,7,9,11,12]]
 .rename(columns={'Column1':'Country', 'Column2':'Media','Column6':'P10',
                     'Column8':'Mediana','Column10':'P90'})
 .reset_index(drop=True)
)

media_matematicas_genero = (media_matematicas_genero
.assign(
    OECD = media_matematicas_genero.OECD.astype('int16'),
    Country = media_matematicas_genero.Country.apply(lambda x: x.replace('*','')),
    )
)
media_matematicas_genero = numerico_OECD(media_matematicas_genero)
media_matematicas_genero.Country = media_matematicas_genero.Country.replace('Ukrainian regions (18 of 27)', 'Ukraine')


# ## diferencias_matematicas_genero: Diferencias entre las puntuaciones medias en matemáticas por género

# In[24]:


diferencias_matematicas_genero = pd.read_excel('datos/performance_diff_by_gender_mathematics.xlsx')
diferencias_matematicas_genero = (diferencias_matematicas_genero
 .iloc[2:,[0,1,5,7,9,11]]
 .rename(columns={'Column1':'Country', 'Column2':'Diff','Column6':'P10',
                     'Column8':'Mediana','Column10':'P90'})
 .reset_index(drop=True)
)
diferencias_matematicas_genero = (diferencias_matematicas_genero
 .assign(
     OECD = diferencias_matematicas_genero.OECD.astype('int16'),
     Country = diferencias_matematicas_genero.Country.apply(lambda x: x.replace('*','')),
 )
)
diferencias_matematicas_genero = numerico_OECD(diferencias_matematicas_genero)
diferencias_matematicas_genero.Country = diferencias_matematicas_genero.Country.replace(
    'Ukrainian regions (18 of 27)', 'Ukraine')


# ## rendimiento_matematicas_2003_2022: Puntuaciones en las pruebas de matemáticas del 2003 al 2022

# In[25]:


rendimiento_matematicas_2003_2022 = pd.read_excel('datos/performance_from_2003_to_2022_mathematics.xlsx', na_values='m')
rendimiento_matematicas_2003_2022=(
    rendimiento_matematicas_2003_2022
     .iloc[2:,[0]+list(range(1,16,2))]
     .reset_index(drop=True)
    .rename(columns={'Column1':'Country', 'Column2':'PISA2003','Column4':'PISA2006',
                     'Column6':'PISA2009','Column8':'PISA2012','Column10':'PISA2015',
                     'Column12':'PISA2018','Column14':'PISA2022'})
)
rendimiento_matematicas_2003_2022 = (
    rendimiento_matematicas_2003_2022
    .assign(
        OECD = rendimiento_matematicas_2003_2022.OECD.astype('int16'),
        Country = rendimiento_matematicas_2003_2022.Country.map(lambda x: x.replace('*', ''))
    )
)
rendimiento_matematicas_2003_2022 = numerico_OECD(rendimiento_matematicas_2003_2022, tipo_numero='float32')
rendimiento_matematicas_2003_2022.Country = rendimiento_matematicas_2003_2022.Country.replace(
    'Ukrainian regions (18 of 27)', 'Ukraine')


# ## rendimiento_lectura_2003_2022: Puntuaciones en las pruebas de lectura del 2003 al 2022

# In[26]:


rendimiento_lectura_2003_2022 = pd.read_excel('datos/performance_from_2003_to_2022_reading.xlsx', na_values='m')
rendimiento_lectura_2003_2022 = (
    rendimiento_lectura_2003_2022
     .iloc[2:,[0]+list(range(1,18,2))]
     .reset_index(drop=True)
    .rename(columns={'Column1':'Country', 'Column2':'PISA2000','Column4':'PISA2003',
                     'Column6':'PISA2006','Column8':'PISA2009','Column10':'PISA2012',
                     'Column12':'PISA2015','Column14':'PISA2018','Column16':'PISA2022'})
)
rendimiento_lectura_2003_2022 = (
    rendimiento_lectura_2003_2022
    .assign(
        OECD = rendimiento_lectura_2003_2022.OECD.astype('int16'),
        Country = rendimiento_lectura_2003_2022.Country.map(lambda x: x.replace('*', ''))
    )
)
rendimiento_lectura_2003_2022 = numerico_OECD(rendimiento_lectura_2003_2022, tipo_numero='float32')
rendimiento_lectura_2003_2022.Country = rendimiento_lectura_2003_2022.Country.replace(
    'Ukrainian regions (18 of 27)', 'Ukraine')


# ## rendimiento_ciencias_2003_2022: Puntuaciones en las pruebas de ciencias del 2003 al 2022

# In[27]:


rendimiento_ciencias_2003_2022 = pd.read_excel('datos/performance_from_2003_to_2022_science.xlsx', na_values='m')
rendimiento_ciencias_2003_2022 = (
    rendimiento_ciencias_2003_2022
     .iloc[2:,[0]+list(range(1,14,2))]
     .reset_index(drop=True)
    .rename(columns={'Column1':'Country','Column2':'PISA2006','Column4':'PISA2009','Column6':'PISA2012',
                     'Column8':'PISA2015','Column10':'PISA2018','Column12':'PISA2022'})
)
rendimiento_ciencias_2003_2022 = (
    rendimiento_ciencias_2003_2022
    .assign(
        OECD = rendimiento_ciencias_2003_2022.OECD.astype('int16'),
        Country = rendimiento_ciencias_2003_2022.Country.map(lambda x: x.replace('*', ''))
    )
)
rendimiento_ciencias_2003_2022 = numerico_OECD(rendimiento_ciencias_2003_2022, tipo_numero='float32')
rendimiento_ciencias_2003_2022.Country = rendimiento_ciencias_2003_2022.Country.replace(
    'Ukrainian regions (18 of 27)', 'Ukraine')


# ## estatus_socioeconomico: Estatus socioeconómico de los estudiantes por países

# In[28]:


estatus_socioeconomico = pd.read_excel('datos/socio_economic_status.xlsx', na_values='m') 
estatus_socioeconomico = (estatus_socioeconomico
 .iloc[2:,[0,1,21]]
 .reset_index(drop=True)
 .rename(columns = {'Column1':'Country','Column2':'Estatus'})
)
estatus_socioeconomico = (
    estatus_socioeconomico
    .assign(
        OECD = estatus_socioeconomico.OECD.astype('int16'),
        Country = estatus_socioeconomico.Country.map(lambda x: x.replace('*',''))
    )
)
estatus_socioeconomico = numerico_OECD(estatus_socioeconomico, tipo_numero='float32')
estatus_socioeconomico.Country = estatus_socioeconomico.Country.replace('Ukrainian regions (18 of 27)', 'Ukraine')


# ## estatus_socioeconomico_mates: Estatus socioeconómico de los estudiantes por países en matemáticas

# In[29]:


estatus_socioeconomico_mates = pd.read_excel('datos/socio_economic_status_mathematics.xlsx', na_values='m') 
estatus_socioeconomico_mates = (estatus_socioeconomico_mates
 .iloc[9:,[0,5,7,9,11,17]]
 .reset_index(drop=True)
 .rename(columns = {'Column1':'Country','Column6':'Q1','Column8':'Q2','Column10':'Q3','Column12':'Q4' })
)
estatus_socioeconomico_mates = (
    estatus_socioeconomico_mates
    .assign(
        Country = estatus_socioeconomico_mates.Country.map(lambda x: x.replace('*','')),
        OECD = estatus_socioeconomico_mates.OECD.astype('int16')
    )
)
estatus_socioeconomico_mates= numerico_OECD(estatus_socioeconomico_mates, tipo_numero='float32')
estatus_socioeconomico_mates.Country = estatus_socioeconomico_mates.Country.replace('Ukrainian regions (18 of 27)', 'Ukraine')


# # Representaciones

# In[30]:


europa = ['Albania', 'Armenia', 'Austria', 'Azerbaijan', 'Belarus', 'Belgium', 'Bosnia', 'Bulgaria',
          'Croatia', 'Cyprus', 'Czech Republic', 'Denmark', 'Estonia', 'Finland', 'France', 'Georgia', 
          'Germany','Greece', 'Hungary', 'Ireland', 'Italy', 'Kosovo', 'Latvia', 'Liechtenstein','Lithuania', 
          'Luxembourg', 'Macedonia', 'Malta', 'Moldova', 'Monaco', 'Montenegro', 'Netherlands',
          'Norway', 'Poland', 'Portugal', 'Romania', 'Russia', 'San Marino', 'Serbia', 'Slovak Republic',
          'Slovenia', 'Spain', 'Sweden', 'Switzerland', 'Turkey', 'Ukraine', 'United Kingdom']


# ## fig1

# In[31]:


# Grafica comparativa de las puntuaciones en las tres materias de PISA en los países europeos

a = media_matematicas.drop(columns = ['standard_deviation'])
a['materia'] = 'matemáticas'
b = media_ciencias.drop(columns = ['standard_deviation'])
b['materia'] = 'ciencias'
c = media_lectura.drop(columns = ['standard_deviation'])
c['materia'] = 'lectura'
todas_materias = pd.concat([a,b,c]).drop(columns=['OECD'])

paises = set.intersection(set(europa), set(todas_materias.Country.unique()))
paises = list(paises)
nearest = alt.selection_point(nearest=True, on="pointerover",
                              fields=["Country"], empty=False)
fig1 = alt.Chart(
    todas_materias.query("Country in @paises")
).mark_line().encode(
    alt.X('Country', axis = alt.Axis(title = 'País', labelFontSize=12, titleFontSize=14)),
    alt.Y('score', scale = alt.Scale(domain =[000, 580]), 
          axis=alt.Axis(title = 'Puntuación', labelFontSize=12, titleFontSize=14)),
    color = alt.Color('materia', legend= alt.Legend(titleFontSize=12, labelFontSize=11))
).properties(title='Puntuación en PISA 2022 (Europa)')

points = fig1.mark_point().encode(
    opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
    color = alt.Color('materia', legend=None)
)
columns = ['matemáticas', 'ciencias', 'lectura']
rules = alt.Chart(todas_materias.query("Country in @paises")).transform_pivot(
    "materia",
    value="score",
    groupby=["Country"]
).mark_rule(color="gray").encode(
    x="Country:N",
    opacity=alt.condition(nearest, alt.value(0.3), alt.value(0)),
    tooltip=['Country'] + [alt.Tooltip(c, type="nominal") for c in columns],
).add_params(nearest)

fig1 = alt.layer(fig1, points, rules).configure_title(
    fontSize=20
)
# fig1.display()
# fig1.save('images/fig1.png', ppi=300)


# In[32]:


# Grafica comparativa de las puntuaciones en las tres materias de PISA

nearest = alt.selection_point(nearest=True, on="pointerover",
                              fields=["Country"], empty=False)
fig1a = alt.Chart(
    media_matematicas
).mark_line().encode(
    alt.X('Country', axis = alt.Axis(title = 'País', labelFontSize=12, titleFontSize=14)),
    alt.Y('score', scale = alt.Scale(domain =[000, 600]), 
          axis=alt.Axis(title = 'Puntuación', labelFontSize=12, titleFontSize=14)),
    # color = alt.Color('materia', legend= alt.Legend(titleFontSize=12, labelFontSize=11))
).properties(title='Puntuación en PISA 2022 (Europa)')

points = fig1a.mark_point().encode(
    opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
    # color = alt.Color('materia', legend=None)
)
columns = ['matemáticas', 'ciencias', 'lectura']
rules = alt.Chart(media_matematicas).mark_rule(color="gray").encode(
    x="Country:N",
    opacity=alt.condition(nearest, alt.value(0.3), alt.value(0)),
    tooltip=['Country', alt.Tooltip('score', title='Puntuación')]
).add_params(nearest)

fig1a = alt.layer(fig1a, points, rules).properties(width=900).configure_title(
    fontSize=20
)
# fig1a.display()
# fig1a.save('images/fig1a.png', ppi=300)



# ## fig2

# In[33]:


# Comparativa de las puntuaciones en PISA / Países europeos

fig2 = alt.Chart(todas_materias.query("Country in @europa & materia =='matemáticas'")).mark_bar().encode(
    alt.X('Country', axis = alt.Axis(title = 'País', labelFontSize=12, titleFontSize=14)),
    alt.Y('score', scale = alt.Scale(domain =[0, 600]), 
          axis = alt.Axis(title = 'Puntuación', labelFontSize=12, titleFontSize=14)),
    color = alt.condition(
        alt.datum.Country == 'Spain',
        alt.value('orange'),
        alt.value('steelblue')
    ),
    tooltip=['Country','score']
).properties(width=700, height=270, title='Puntuación en Matemáticas PISA 2022 (Europa)').configure_title(
    fontSize=20
)

# fig2.display()
# fig2.save('images/fig2.png', ppi=300)


# ## fig3

# In[34]:


# Diferencias por género en Pisa en Europa
fig3 = alt.Chart(diferencias_matematicas_genero[['Country','Diff']].query("Country in @europa")).mark_bar().encode(
    alt.X('Country:N', axis = alt.Axis(title = 'Países', labelFontSize=12, titleFontSize=14)),
    alt.Y('Diff:Q',scale = alt.Scale(domain=[-24,24]), 
          axis = alt.Axis(title = 'Diferencia', labelFontSize=12, titleFontSize=14)),
    color = alt.condition(
        alt.datum.Diff>0,
        alt.value('steelblue'),
        alt.value('orange')
    ),
    tooltip=[alt.Tooltip('Country', title='País'),alt.Tooltip('Diff',title='Diferencia')]
).properties(title='Diferencias Niños - Niñas en Matemáticas (Europa)').configure_title(
    fontSize=20
)

# fig3.display()
#fig3.save('images/fig3.png', ppi=300)


# ## fig4

# In[35]:


# Diferencias por género en Pisa 
fig4a = alt.Chart(
    diferencias_matematicas_genero[['Country','Diff']].query('Diff>0')
                 ).mark_bar().encode(
    alt.Y('Country:N', axis = alt.Axis(title = 'Países', labelFontSize=11, titleFontSize=14), sort='-x'),
    alt.X('Diff:Q',scale = alt.Scale(domain=[0,24]), title='Diferencia de Puntos' ),
    color = alt.condition(
        alt.datum.Diff>0,
        alt.value('steelblue'),
        alt.value('orange')
    )
).properties(title=alt.TitleParams('Niños vs Niñas', fontSize=12),width=100)
fig4b = alt.Chart(
    diferencias_matematicas_genero[['Country','Diff']].query('Diff<0')
                 ).mark_bar().encode(
    alt.Y('Country:N', axis = alt.Axis(title = None, labelFontSize=11, titleFontSize=14), sort='-x'),
    alt.X('Diff:Q',scale = alt.Scale(domain=[-23,0]), title='Diferencia de Puntos' ),
    color = alt.condition(
        alt.datum.Diff>0,
        alt.value('steelblue'),
        alt.value('orange')
    )
).properties(title=alt.TitleParams('Niñas vs Niños', fontSize=12),width=100)

fig4 = fig4a | fig4b
fig4.properties(title='Diferencias en matemáticas por Género').configure_title(
    anchor='middle', fontSize=20, offset=10
)
# fig4.display()
# fig4.save('images/fig4.png', ppi=300)


# ## fig5

# In[36]:


# Nivel educativo por países

lista_estudios = ['L0T2','L3T4','L5T8']
#'L0T2': 'Below upper secondary education',
#'L3T4': 'Upper secondary or post-secondary non-tertiary education',
#'L5T8': 'Tertiary education',

paises = estudios.Country.sort_values().unique()

paises_aa = paises[:14]
paises_bb = paises[14:28]
paises_cc = paises[28:]

estudios_H_M = estudios.query('ISC11A in @lista_estudios')[[
    'Country', 'ISC11A', 'Gender','Value']].groupby(['Country', 'ISC11A']).Value.mean().reset_index()
# Japón solo tiene información de la educaión terciaria, así que lo eliminamos
estudios_H_M = estudios_H_M.query('Country not in ["Japan"]')
WIDTH = 160
HEIGHT = 600
G1 = alt.Chart(estudios_H_M.query("Country in @paises_aa")).mark_bar().encode(
    alt.X('Value', axis = alt.Axis(title= None,labelFontSize=12, titleFontSize=14)),
    alt.Y('Country', axis = alt.Axis(title= "País",labelFontSize=12, titleFontSize=14)),
    yOffset = ('ISC11A'),
    # color= alt.Color('ISC11A:O', title='Nivel Educativo')
    color= alt.Color(
        'ISC11A:O', title='Nivel Educativo', 
        legend= alt.Legend(titleFontSize=12, labelFontSize=11, orient='bottom',
        labelExpr="datum.label === 'L0T2' ? 'Inferior a Ed. Secund.': datum.label === 'L3T4' ? 'Ed. Secund.' : 'Ed. Terciaria'"
                    )
    ),
    
).properties(height=HEIGHT, width=WIDTH)

G2 = alt.Chart(estudios_H_M.query("Country in @paises_bb")).mark_bar().encode(
    alt.X('Value', axis = alt.Axis(title= 'Porcentaje',labelFontSize=12, titleFontSize=14)),
    alt.Y('Country', axis = alt.Axis(title= None,labelFontSize=12, titleFontSize=14)),
    yOffset = ('ISC11A'),
    color= 'ISC11A:O'
).properties(height=HEIGHT, width=WIDTH)

G3 = alt.Chart(estudios_H_M.query("Country in @paises_cc")).mark_bar().encode(
    alt.X('Value', axis = alt.Axis(title= None,labelFontSize=12, titleFontSize=14)),
    alt.Y('Country', axis = alt.Axis(title= None,labelFontSize=12, titleFontSize=14)),
    yOffset = ('ISC11A'),
    color= 'ISC11A:O'
).properties(height=HEIGHT, width=WIDTH)
fig5 = G1|G2|G3
fig5 = fig5.properties(title='Porcentaje de nivel educativo por paises').configure_title(
    fontSize=20,
    anchor='middle',
    color='black',
    offset=20
)


# fig5.properties(title='Porcentaje de nivel educativo por paises').configure_title(
#     fontSize=20,
#     anchor='middle',
#     color='black',
#     offset=20
# ).save('images/fig5.png', ppi=300)


# ## fig5a

# In[37]:


# Desempleo por nivel de estudios y género

#'L0T2': 'Below upper secondary education',
#'L3T4': 'Upper secondary or post-secondary non-tertiary education',
#'L5T8': 'Tertiary education',
color_scale = alt.Scale(domain=['Men', 'Women'],
                        range=['#2c7fb8','orange'])
paises_a = desempleo.Country.sort_values().unique()[:25]
paises_b = desempleo.Country.sort_values().unique()[25:]

df = desempleo.copy()
df.ISC11A = df.ISC11A.replace({'L0T2':'Sin Ed.secund.', 'L3T4':'Ed.secund' , 'L5T8':'Ed.terciaria'})
df.ISC11A.unique()

paises_a = df.Country.sort_values().unique()[:25]
paises_b = df.Country.sort_values().unique()[25:]

niveles =['Sin Ed.secund.','Ed.secund' ,'Ed.terciaria']
niveles_dropdown = alt.binding_select(options=niveles, name='Nivel de estudios: ')
niveles_select = alt.selection_point(fields=['ISC11A'], bind=niveles_dropdown, value = 'Sin Ed.secund.')
grafica_izq =(alt
 .Chart(df.query('Country in @paises_a'))
 .mark_bar()
 .encode(
     y = alt.Y('Country',axis = alt.Axis(title= 'País',labelFontSize=12, titleFontSize=14)),
     x = alt.X('Value', 
               axis = alt.Axis(title= 'Porcentaje',labelFontSize=12, titleFontSize=14),
               # title = 'Porcentaje',
               scale=alt.Scale(domain = [0,45])),
     yOffset='Gender',
     color = alt.Color('Gender', title = 'Género', scale = color_scale,
                       legend= alt.Legend(titleFontSize=12, labelFontSize=11,
                                          labelExpr="datum.label === 'Men' ? 'Hombre': 'Mujer'")
                      )                
 )
 .properties(
     height=500,
     width=200
 )
).add_params(niveles_select).transform_filter(niveles_select)

grafica_der =(alt
 .Chart(df.query('Country in @paises_b'))
 .mark_bar()
 .encode(
     y = alt.Y('Country',axis = alt.Axis(title= None,labelFontSize=12, titleFontSize=14)),
     x = alt.X('Value', axis = alt.Axis(title= 'Porcentaje',labelFontSize=12, titleFontSize=14),
               scale=alt.Scale(domain = [0,45])),
     yOffset='Gender',
     color = alt.Color('Gender:N')
 )
 .properties(
     height=500,
     width=200
 )
).add_params(niveles_select).transform_filter(niveles_select)

fig5a = (grafica_izq | grafica_der).properties(
    title='Desempleo por nivel de estudios y género').configure_title(
    anchor='middle', fontSize=20, offset=10
)

# fig5a.display()


# fig5a.save('images/fig5c.png', ppi=300)


# ## fig6

# Vamos a comparar la ratio con los resultados en matemáticas. Los resultados que tenemos son del 2022, así que filtramos la ratio para el último año que tenemos disponible (2021) y mezclamos con el dataset de las puntuaciones de matematicas.

# In[38]:


paises = set.intersection(set(ratio.Country), set(todas_materias.Country))
df = pd.merge(
    media_matematicas[['Country', 'score']].query('Country in @paises'),
    ratio[ratio.Year == 2021].query('Country in @paises'),
    on = 'Country').rename(
            columns = {'score': 'Puntuacion', 'Value':'Ratio'}
    ).drop(columns = 'Year')


america = ['United States', 'Mexico', 'Brazil', 'Colombia', 'Chile', 'Costa Rica']
asia = ['Japan','Korea' ]
otros = ['Iceland', 'Israel', 'Australia']

df['zona'] = 'otros'
for i, row in df.iterrows():
    if row.Country in europa:
        df.iat[i,3] = 'Europa'
    elif row.Country in america:
        df.iat[i,3] = 'América'

reg = sm.ols(formula="Puntuacion ~ Ratio", data=df).fit()
df['pred'] = reg.predict(df.Ratio)

chart1 = (alt
 .Chart(df)
 .mark_circle(size=60, opacity = 1)
 .encode(
     x = alt.X('Ratio', scale = alt.Scale(domain =[16, 30]),
              axis = alt.Axis(title='Ratio', labelFontSize=12, titleFontSize=14 )),
     y = alt.Y('Puntuacion', scale = alt.Scale(domain =[330, 580]),
              axis = alt.Axis(title='Puntuación', labelFontSize=12, titleFontSize=14 )),
     color = alt.Color('zona', title = 'Zona', legend= alt.Legend(titleFontSize=12, labelFontSize=11)),
     tooltip = [alt.Tooltip('Country', title='País'), alt.Tooltip('Ratio', format='.1f'), alt.Tooltip('Puntuacion', title='Puntuación')]
 )
)
chart2 = (alt
 .Chart(df)
 .mark_line(color='black',strokeDash=[6,3], opacity = 0.7)
 .encode(
     x = alt.X('Ratio', scale = alt.Scale(domain =[16, 30])),
     y = alt.Y('pred', scale = alt.Scale(domain =[330, 580])),
 )
)

fig6 = (chart2 + chart1).properties(
    height=450,
    width = 500,
    title=alt.TitleParams('Ratio vs puntuación en matemáticas', fontSize=20)
    # title='Ratio vs puntuación en matemáticas'
)
# fig6.display()
# fig6.save('images/fig6.png', ppi=300)


# ## fig7

# In[39]:


df = pd.merge(
    media_matematicas[['Country', 'score']],
    estatus_socioeconomico_mates,
    on = 'Country').rename(
            columns = {'score': 'Puntuacion'}
    )
idx = df.query('Country == "OECD average"').index[0]
df = df.drop(index = idx).dropna().reset_index(drop=True)


# In[40]:


europa = ['Albania', 'Armenia', 'Austria', 'Azerbaijan', 'Belarus', 'Belgium', 'Bosnia', 'Bulgaria', 'Croatia', 
          'Cyprus', 'Czech Republic', 'Denmark', 'Estonia', 'Finland', 'France', 'Georgia', 'Germany', 'Greece', 
          'Hungary', 'Ireland', 'Italy', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Macedonia', 
          'Malta', 'Moldova', 'Monaco', 'Montenegro', 'Netherlands', 'Norway', 'Poland', 'Portugal', 'Romania', 
          'Russia', 'San Marino', 'Serbia', 'Slovak Republic', 'Slovenia', 'Spain', 'Sweden', 'Switzerland', 
          'Turkey', 'Ukraine', 'United Kingdom', 'Kosovo']
asia = ['Thailand', 'North Macedonia', 'Mongolia','Singapore', 'Viet Nam', 'Cambodia', 'Malaysia',  'Philippines', 
        'Kazakhstan',  'Indonesia', 'Brunei Darussalam', 'Hong Kong (China)', 'Macao (China)', 'Korea',  
        'Japan', 'Uzbekistan', 'ChineseTaipei']
medio_este =['Israel', 'Jordan','Baku (Azerbaijan)', 'SaudiArabia','UnitedArab Emirates','PalestinianAuthority','Qatar']
america = ['Dominican Republic','Jamaica', 'El Salvador','Chile', 'Brazil', 'Canada', 'Panama', 'Peru',
           'Paraguay', 'Colombia', 'Argentina', 'Uruguay', 'United States', 'Guatemala', 'Mexico']
otros =['Morocco','Iceland','Australia','New Zealand']


# In[41]:


df['zona'] = 'otros'
for i, row in df.iterrows():
    if row.Country in europa:
        df.iat[i,6] = 'Europa'
    elif row.Country in america:
        df.iat[i,6] = 'América'
    elif row.Country in asia:
        df.iat[i,6] = 'Asia'
    elif row.Country in medio_este:
        df.iat[i,6] = 'Medio Este'


# In[42]:


WIDTH =900
HEIGHT = 300
zonas_dropdown = alt.binding_select(options=[None,'Europa', 'América','Asia','Medio Este'], 
                                    labels=['Todas','Europa', 'América','Asia','Medio Este'],
                                    name="Zona")
zonas_select = alt.selection_point(fields = ['zona'], bind = zonas_dropdown, value='Europa')

G1 = alt.Chart(df).mark_area().encode(
    alt.X('Country'),
    alt.Y('Q1:Q', scale = alt.Scale(domain =[0, 650])),
    alt.Y2('Q4:Q')
)
G2 = alt.Chart(df).mark_line(color='orange').encode(
    alt.X('Country', axis = alt.Axis(title = 'País', labelFontSize=12, titleFontSize=14)),
    alt.Y('Puntuacion', axis = alt.Axis(title = 'Puntuación', labelFontSize=12, titleFontSize=14), 
          scale = alt.Scale(domain =[0, 650])
         ),
)



fig7 = G1 + G2

fig7 = fig7.add_params(
    zonas_select
).transform_filter(zonas_select)
# fig7
fig7 = fig7.properties(
    # title='Puntuación matemáticas (rango socioeconómico)', 
    title=alt.TitleParams('Puntuación matemáticas (rango socioeconómico)', fontSize=20),
    height= HEIGHT, width = WIDTH,
               )#.display()
# fig7.properties(title='Puntuación matemáticas (rango socioeconómico)', height= HEIGHT, width = WIDTH
#                ).save('images/fig7a.png', ppi=300)


# ## fig8

# In[43]:


df = pd.merge(
    media_matematicas[['Country', 'score']],
    estatus_socioeconomico,
    on = 'Country').rename(
            columns = {'score': 'Puntuacion'}
    )
OECD_media = df.query('Country == "OECD average"').Puntuacion.values[0]
idx = df.query('Country == "OECD average"').index[0]
df = df.drop(index = idx).dropna().reset_index(drop=True)


# In[44]:


df['zona'] = 'otros'
for i, row in df.iterrows():
    if row.Country in europa:
        df.iat[i,3] = 'Europa'
    elif row.Country in america:
        df.iat[i,3] = 'América'
    elif row.Country in asia:
        df.iat[i,3] = 'Asia'
    elif row.Country in medio_este:
        df.iat[i,3] = 'Medio Este'


# In[45]:


HEIGHT = 300
WIDTH = 600

zonas_dropdown = alt.binding_select(options=[None,'Europa', 'América','Asia','Medio Este'], 
                                    labels=['Todas','Europa', 'América','Asia','Medio Este'],
                                    name="Zona")
zonas_select = alt.selection_point(fields = ['zona'], bind = zonas_dropdown, value='Europa')

G1 = alt.Chart(df).mark_bar().encode(
    alt.X('Country:N', axis = alt.Axis(title = 'País', labelFontSize=12, titleFontSize=14)),
    alt.Y('Estatus:Q',scale = alt.Scale(domain=[-2.4,4]),
          axis = alt.Axis(title = 'Estatus Socioeconómico', labelFontSize=12, titleFontSize=14)
          ),
    color = alt.condition(
        alt.datum.Estatus>0,
        alt.value('steelblue'),
        alt.value('orange')
    ),
    tooltip = [alt.Tooltip('Country', title='País'),alt.Tooltip('Estatus', title='Estatus', format='.2f'),
              alt.Tooltip('Puntuacion', title='Puntuación')]
).properties(title='Puntuación en matemáticas vs nivel socioeconómico')

G2 = alt.Chart(df).mark_line(color='red', point=False).encode(
    alt.X('Country', axis = alt.Axis(title = 'País', labelFontSize=12, titleFontSize=14)),
    alt.Y('Puntuacion',
          axis = alt.Axis(title = 'Puntuación', labelFontSize=12, titleFontSize=14),
          scale = alt.Scale(domain =[0, 660])
         )
)
# rule = alt.Chart(df).mark_rule(strokeDash=[6,3], color = 'lightred').encode(
#     y = alt.Y('mean(Puntuacion)', scale = alt.Scale(domain =[0, 700])))

rule = alt.Chart(df).mark_rule(strokeDash=[6,3], color = 'gray', opacity=0.1).encode(
    y = alt.Y(datum = OECD_media, scale = alt.Scale(domain =[0, 700]), axis=None))

fig8 = alt.layer(G1, G2, rule).resolve_scale(y='independent').properties(
    title=alt.TitleParams('Puntuación matemáticas (rango socioeconómico)', fontSize=20),
    height=HEIGHT, 
    width=WIDTH
)
fig8 = fig8.add_params(zonas_select).transform_filter(zonas_select)

# fig8.display()
# fig8.save('images/fig8a_europa.png', ppi=300)


# In[46]:


HEIGHT = 500
WIDTH = 500

selector = alt.selection_point(fields=['zona'])
condition = alt.condition(
    selector,
    'zona:N',
    alt.value('lightgray')
)

fig8c = (alt
 .Chart(df)
 .mark_circle(size=60, opacity=0.8)
 .encode(
     alt.X('Estatus:Q', scale = alt.Scale(domain =[-2.5, 1]),
          axis = alt.Axis(title = 'Estatus', labelFontSize=12, titleFontSize=14)),
     alt.Y('Puntuacion:Q',scale = alt.Scale(domain =[200, 640]),
          axis = alt.Axis(title = 'Puntuación', labelFontSize=12, titleFontSize=14)),
     color = condition,
     tooltip=[alt.Tooltip('Country', title='País'),
              alt.Tooltip('Estatus', title='Estatus', format='.2f'),
              alt.Tooltip('Puntuacion', title='Puntuación')]
 )
 .add_params(selector)
 .properties(title='Puntuación en matemáticas vs nivel socioeconómico')
 .configure_legend(
     titleFontSize=13,
     labelFontSize=12
 )
        )

fig8c = fig8c.properties(
    title=alt.TitleParams('Puntuación en matemáticas vs nivel socioeconómico', fontSize=20),
    height=HEIGHT, width=WIDTH
)
# fig8c.add_params(zonas_select).transform_filter(zonas_select)
# fig8c.display()
# fig8c.save('images/fig8c.png', ppi=300)


# ## fig9

# In[47]:


orden = pd.merge(
    sueldo, media_matematicas, on = 'Country', how='inner'
    ).sort_values(by='Value', ascending=False).Country.to_list()
df = pd.merge(sueldo, media_matematicas, on = 'Country', how='inner')
df = df.sort_values(by = 'Value', ascending=False).reset_index(drop=True)
df['numerac'] = list(range(len(df)))

reg = sm.ols(formula="score ~ numerac", data=df).fit()
df['pred'] = reg.predict(df.numerac)
df['puntuaciones'] = 'Puntuación Matemáticas'
df['tendencia'] = 'Tendencia puntuaciones'


base = alt.Chart(
    # pd.merge(sueldo, media_matematicas, on = 'Country', how='inner')
    df
).encode(
    x =alt.X('Country:N', sort=orden, axis=alt.Axis(title='Países', titleFontSize=14, labelFontSize=12)), 
)
bar = base.mark_bar().encode(
    # y = alt.Y('Value', title='Sueldo medio'),
    y = alt.Y('Value', axis= alt.Axis(title='Sueldo medio', labelFontSize=12, titleFontSize=14)),
    tooltip = [alt.Tooltip('Country', title='País'), alt.Tooltip('mean(Value)', format='.2f', title='Sueldo')]
)
line = base.mark_line(color = 'red').encode(
    y = alt.Y('score:Q', scale=alt.Scale(domain = [0,550]), title='Puntuacion en matemáticas', axis=None),
)
line_cir = base.mark_circle(color = 'red').encode(
    y = alt.Y('score:Q', scale=alt.Scale(domain = [0,550]), title='Puntuacion en matemáticas', axis=None),
    tooltip= [alt.Tooltip('Country', title='País'), alt.Tooltip('score', title='Puntuación')]
)


line2 = base.mark_line(color = 'orange', strokeDash=[6,3]).encode(
    y = alt.Y('pred:Q', scale=alt.Scale(domain = [0,550]), title=None, axis=None),
    tooltip=[alt.Tooltip('pred', format='.1f', title='Tendencia')]
)

puntuacion = (alt
 .Chart(df.sort_values(by='numerac', ascending=False).head(1))
 .mark_circle()
 .encode(
     x = alt.X('Country', sort=orden),
     y = alt.Y('score:Q',scale=alt.Scale(domain = [0,550]), title=None, axis=None)
 )
)
texto_punt = (puntuacion
 .mark_text(
     align='left',
     dx=12,
     fontSize =12,
     color='red'
 )
 .encode(text='puntuaciones')
)

tendencia = (alt
 .Chart(df.sort_values(by='numerac', ascending=False).head(1))
 .mark_circle()
 .encode(
     x = alt.X('Country', sort=orden),
     y = alt.Y('pred:Q',scale=alt.Scale(domain = [0,550]), title=None, axis=None)
 )
)
texto_tend = (tendencia
 .mark_text(
     align='left',
     dx=12,
     fontSize =12,
     color='orange'
 )
 .encode(text='tendencia')
)


fig9 = (bar + line2 + line + line_cir + texto_punt + texto_tend).resolve_scale(y='independent').properties(
    title='Sueldo vs puntuación en matemáticas').configure_title( 
    fontSize=20,
)
# fig9.display()
# fig9.save('images/fig9.png', ppi=300)


# In[ ]:

st.set_page_config(layout="wide")
st.markdown("<div style = 'background:#cccccc; padding-left: 20px;'><h3>Educación y factores socioeconómicos </h3></div>", unsafe_allow_html=True)

st.write("")
panel1 = st.container()
with panel1:
    columns = st.columns([2,0.1, 2,0.5])
    with columns[0]:
        st.altair_chart(fig1, use_container_width=True)
        st.altair_chart(fig3, use_container_width=True)
    with columns[2]:
        st.altair_chart(fig5, use_container_width=True)

panel2 = st.container()
with panel2:
    columns = st.columns([2,0.3, 2,0.3])
    with columns[0]:
        st.altair_chart(fig9, use_container_width=True)
        st.altair_chart(fig8c, use_container_width=False)
    
    with columns[2]:
        st.altair_chart(fig5a, use_container_width=False)
panel3 = st.container()
with panel3:
    columns = st.columns([2,0.3, 2,0.3])
    with columns[0]:
        st.altair_chart(fig6, use_container_width=False)
 