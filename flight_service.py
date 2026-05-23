import requests
import os
from datetime import datetime

RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '')
SKYSCANNER_HOST = 'sky-scrapper.p.rapidapi.com'

HEADERS = {
    'x-rapidapi-key': RAPIDAPI_KEY,
    'x-rapidapi-host': SKYSCANNER_HOST
}


def buscar_aeroporto(codigo_iata):
    """Busca entityId e skyId pelo código IATA ou nome da cidade."""
    print(f'[API] Buscando aeroporto: {codigo_iata}')
    url = 'https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchAirport'
    try:
        resp = requests.get(
            url,
            headers={
                'x-rapidapi-key': os.getenv('RAPIDAPI_KEY', ''),
                'x-rapidapi-host': SKYSCANNER_HOST
            },
            params={'query': codigo_iata, 'locale': 'pt-BR'},
            timeout=15
        )
        print(f'[API] Status searchAirport: {resp.status_code}')
        data = resp.json()
        print(f'[API] Resposta searchAirport: {str(data)[:300]}')

        if not data.get('status') or not data.get('data'):
            print(f'[API] Aeroporto não encontrado para: {codigo_iata}')
            return None

        items = data['data']
        # Prioriza resultado do tipo AIRPORT, evita CITY
        item = None
        for i in items:
            if i.get('navigation', {}).get('entityType') == 'AIRPORT':
                item = i
                break
        if not item:
            item = items[0]

        nav = item.get('navigation', {})
        flight_params = nav.get('relevantFlightParams', {})
        resultado = {
            'skyId': flight_params.get('skyId', '') or nav.get('entityId', ''),
            'entityId': nav.get('entityId', ''),
            'nome': item.get('presentation', {}).get('title', '')
        }
        print(f'[API] Aeroporto encontrado: {resultado}')
        return resultado

    except Exception as e:
        print(f'[API] Erro ao buscar aeroporto {codigo_iata}: {e}')
        return None


def buscar_voos_skyscanner(demanda):
    """Busca voos no Skyscanner e retorna lista de ofertas."""
    print(f'[Skyscanner] Buscando voos: {demanda.origem} -> {demanda.destino} em {demanda.data_ida}')

    origem = buscar_aeroporto(demanda.origem)
    destino = buscar_aeroporto(demanda.destino)

    if not origem or not destino:
        print(f'[Skyscanner] Não foi possível encontrar um dos aeroportos.')
        return []

    if not origem.get('skyId') or not origem.get('entityId'):
        print(f'[Skyscanner] skyId ou entityId inválido para origem: {origem}')
        return []

    if not destino.get('skyId') or not destino.get('entityId'):
        print(f'[Skyscanner] skyId ou entityId inválido para destino: {destino}')
        return []

    url = 'https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchFlights'
    params = {
        'originSkyId': origem['skyId'],
        'destinationSkyId': destino['skyId'],
        'originEntityId': origem['entityId'],
        'destinationEntityId': destino['entityId'],
        'date': demanda.data_ida,
        'cabinClass': 'economy',
        'adults': str(demanda.adultos),
        'sortBy': 'price_low',
        'currency': demanda.moeda,
        'market': 'BR',
        'countryCode': 'BR',
        'locale': 'pt-BR'
    }

    if demanda.data_volta:
        params['returnDate'] = demanda.data_volta

    try:
        print(f'[Skyscanner] Chamando searchFlightsComplete com params: {params}')
        resp = requests.get(
            url,
            headers={
                'x-rapidapi-key': os.getenv('RAPIDAPI_KEY', ''),
                'x-rapidapi-host': SKYSCANNER_HOST
            },
            params=params,
            timeout=30
        )
        print(f'[Skyscanner] Status: {resp.status_code}')

        data = resp.json()
        print(f'[Skyscanner] Resposta (primeiros 500 chars): {str(data)[:500]}')

        itineraries = data.get('data', {}).get('itineraries', [])
        print(f'[Skyscanner] Itinerários encontrados: {len(itineraries)}')

        resultados = []
        for item in itineraries[:5]:
            preco_raw = item.get('price', {}).get('raw', None)
            if preco_raw is None:
                continue

            legs = item.get('legs', [])
            cias = []
            for leg in legs:
                for carrier in leg.get('carriers', {}).get('marketing', []):
                    nome = carrier.get('name', '')
                    if nome and nome not in cias:
                        cias.append(nome)

            resultados.append({
                'preco': float(preco_raw),
                'companhia': ', '.join(cias) if cias else 'N/D',
                'link': f'https://www.skyscanner.com.br/transporte/passagens-aereas/{demanda.origem.lower()}/{demanda.destino.lower()}/{demanda.data_ida.replace("-", "")}/',
                'fonte': 'skyscanner'
            })

        print(f'[Skyscanner] Ofertas processadas: {len(resultados)}')
        return resultados

    except Exception as e:
        print(f'[Skyscanner] Erro na busca de voos: {e}')
        return []


def verificar_preco_demanda(demanda):
    """Verifica preços e retorna a melhor oferta ou None."""
    print(f'[Verificar] Iniciando verificação para demanda {demanda.id}: {demanda.origem}->{demanda.destino}')

    ofertas = buscar_voos_skyscanner(demanda)

    if not ofertas:
        print(f'[Verificar] Nenhuma oferta encontrada.')
        return None

    ofertas.sort(key=lambda x: x['preco'])
    melhor = ofertas[0]
    print(f'[Verificar] Melhor oferta: R${melhor["preco"]} via {melhor["companhia"]}')
    return melhor
