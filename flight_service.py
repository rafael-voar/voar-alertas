import requests
import os
from datetime import datetime

RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '')

SKYSCANNER_HOST = 'sky-scrapper.p.rapidapi.com'

HEADERS_SKYSCANNER = {
    'x-rapidapi-key': RAPIDAPI_KEY,
    'x-rapidapi-host': SKYSCANNER_HOST
}


def buscar_aeroporto(nome_cidade):
    """Busca o código IATA de um aeroporto pelo nome da cidade."""
    url = 'https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchAirport'
    params = {'query': nome_cidade, 'locale': 'pt-BR'}
    try:
        resp = requests.get(url, headers=HEADERS_SKYSCANNER, params=params, timeout=10)
        data = resp.json()
        resultados = []
        if data.get('status') and data.get('data'):
            for item in data['data'][:5]:
                resultados.append({
                    'skyId': item.get('skyId', ''),
                    'entityId': item.get('entityId', ''),
                    'nome': item.get('presentation', {}).get('title', ''),
                    'subtitulo': item.get('presentation', {}).get('subtitle', '')
                })
        return resultados
    except Exception as e:
        print(f'[buscar_aeroporto] Erro: {e}')
        return []


def buscar_voos_skyscanner(demanda):
    """
    Busca voos no Skyscanner via Air Scraper API.
    Retorna lista de ofertas com preço, cia aérea e link.
    """
    resultados = []

    try:
        # Passo 1: Buscar entidade de origem
        origem_data = buscar_aeroporto(demanda.origem)
        destino_data = buscar_aeroporto(demanda.destino)

        if not origem_data or not destino_data:
            print(f'[Skyscanner] Aeroporto não encontrado: {demanda.origem} -> {demanda.destino}')
            return []

        origem = origem_data[0]
        destino = destino_data[0]

        # Passo 2: Buscar voos
        url = 'https://sky-scrapper.p.rapidapi.com/api/v2/flights/searchFlightsComplete'
        params = {
            'originSkyId': origem['skyId'],
            'destinationSkyId': destino['skyId'],
            'originEntityId': origem['entityId'],
            'destinationEntityId': destino['entityId'],
            'date': demanda.data_ida,
            'returnDate': demanda.data_volta or '',
            'cabinClass': 'economy',
            'adults': str(demanda.adultos),
            'sortBy': 'best',
            'currency': demanda.moeda,
            'market': 'BR',
            'countryCode': 'BR',
            'locale': 'pt-BR'
        }

        resp = requests.get(
            url,
            headers=HEADERS_SKYSCANNER,
            params={k: v for k, v in params.items() if v},
            timeout=20
        )
        data = resp.json()

        itineraries = (
            data.get('data', {})
                .get('itineraries', [])
        )

        for item in itineraries[:10]:
            preco_raw = item.get('price', {}).get('raw', None)
            if preco_raw is None:
                continue

            legs = item.get('legs', [])
            cias = []
            for leg in legs:
                for carrier in leg.get('carriers', {}).get('marketing', []):
                    nome_cia = carrier.get('name', '')
                    if nome_cia and nome_cia not in cias:
                        cias.append(nome_cia)

            resultados.append({
                'preco': float(preco_raw),
                'companhia': ', '.join(cias) if cias else 'N/D',
                'link': f'https://www.skyscanner.com.br/transporte/passagens-aereas/{demanda.origem.lower()}/{demanda.destino.lower()}/{demanda.data_ida.replace("-", "")}/',
                'fonte': 'skyscanner'
            })

    except Exception as e:
        print(f'[Skyscanner] Erro na busca: {e}')

    return resultados


def verificar_preco_demanda(demanda):
    """
    Verifica os preços de uma demanda em todas as fontes.
    Retorna a melhor oferta encontrada ou None.
    """
    todas_ofertas = []

    # Busca no Skyscanner
    ofertas_sky = buscar_voos_skyscanner(demanda)
    todas_ofertas.extend(ofertas_sky)

    if not todas_ofertas:
        return None

    # Ordena pelo menor preço
    todas_ofertas.sort(key=lambda x: x['preco'])
    melhor = todas_ofertas[0]

    return melhor
