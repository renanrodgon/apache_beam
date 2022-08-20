from unittest import skip
import re
import apache_beam as beam
from apache_beam.io import ReadFromText
from apache_beam.options.pipeline_options import PipelineOptions

pipeline_options =PipelineOptions(argv=None)
pipeline = beam.Pipeline(options=pipeline_options)

colunas_dengue = [
                'id',
                'data_iniSE',
                'casos',
                'ibge_code',
                'cidade',
                'uf',
                'cep',
                'latitude',
                'longitude']

def lista_para_dicionario(elemento, colunas):
    """
    Recebe 2 listas
    Retorna 1 dicionário
    """

    return dict(zip(colunas, elemento))

def texto_para_lista(elemento, delimitador='|'):
    """
    Recebe um texto e um delimitador
    Retorna uma lista de elementos pelo delimitador
    """

    return elemento.split(delimitador)

def trata_datas(elemento):
    """
    Recebe um dicionário e cria um novo campo com ANO-MES
    Retorna o mesmo dicionário com o novo campo
    """
    elemento['ano_mes'] = '-'.join(elemento['data_iniSE'].split('-')[:2])
    return elemento

def chave_uf(elemento):
    """
    Receber um dicionário
    Retornar uma tupla com o estado(UF) e o elemento (UF, dicionário)
    """
    chave = elemento['uf']
    return (chave, elemento)

def casos_dengue(elemento):
    """
    Recebe uma tupla ('RS', [{},{}])
    Retornar uma tupla (RS-2014-12, 8.0)
    """
    uf, registros = elemento
    for registro in registros:
        if bool(re.search(r'\d', registro['casos'])):
            yield (f"{uf}-{registro['ano_mes']}", float(registro['casos']))
        else:
            yield (f"{uf}-{registro['ano_mes']}", 0.0)

def chave_uf_ano_mes_de_lista(elemento):
    """
    Receber uma lista de elementos
    Retornar uma tupla contendo uma chave e o valor de chuva em mm
    ('UF-ANO-MES', 1.3)
    ['2016-01-24', '4.2', 'TO']
    """
    data, mm, uf = elemento
    ano_mes = '-'.join(data.split('-')[:2])
    chave = f'{uf}-{ano_mes}'
    if float(mm) < 0:
        mm = 0.0
    else:
        mm = float(mm)
    return chave, mm

def arrendonda(elemento):
    """
    Recebe uma tupla ('SE-2019-06', 1410.8000000000084)
    Retorna uma tupla com o valor arrendodado ('SE-2019-06', 1410.8)
    """
    chave, mm = elemento
    return (chave, round(mm, 1))

# dengue = (
#     pipeline
#     | "Leitura do dataset de dengue" >> 
#         ReadFromText('casos_dengue.txt', skip_header_lines=1)
#     | "De texto para lista" >> beam.Map(texto_para_lista)
#     | "De lista para dicionário" >> beam.Map(lista_para_dicionario, colunas_dengue)
#     | "Criar campo ano_mes" >> beam.Map(trata_datas)
#     | "Criar chave pelo estado" >> beam.Map(chave_uf)
#     | "Agrupar pelo estado" >> beam.GroupByKey()
#     | "Descompactar casos de dengue" >> beam.FlatMap(casos_dengue)
#     | "Soma dos casos pela chave" >> beam.CombinePerKey(sum)
#     #| "Mostrar resultados" >> beam.Map(print)

# )

chuvas= (
    pipeline
    | "Leitura do dataset de chuvas" >> 
        ReadFromText('chuvas.csv', skip_header_lines=1)
    | "De texto para lista (chuvas)" >> beam.Map(texto_para_lista, delimitador=',')
    | "Criando a chave UF-ANO-MES" >> beam.Map(chave_uf_ano_mes_de_lista)
    | "Soma do total de chuvas pela chave" >> beam.CombinePerKey(sum)
    | "Arrendodar resuldados de chuvas" >> beam.Map(arrendonda)
    | "Mostrar resultados de chuvas" >> beam.Map(print)
)

pipeline.run()