import requests
import os
import re
import time
from datetime import datetime, timedelta

RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '')
SKYSCANNER_HOST = 'sky-scrapper.p.rapidapi.com'


def buscar_aeroporto(codigo_iata, tentativas=3):
    """Busca entityId e skyId pelo código IATA ou nome da cidade."""
    print(f'[API] Buscando aeroporto: {codigo_iata}')
    url = 'https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchAirport'

    for tentativa in range(tentativas):
        try:
            resp = requests.get(
                url,
                headers={
                    'x-rapidapi-key': os.getenv('RAPIDAPI_KEY', ''),
                    'x-rapidapi-host': SKYSCANNER_HOST
                },
                params={'query': codigo_iata, 'locale': 'pt-BR'},
                timeout=30
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
            print(f'[API] Tentativa {tentativa+1}/{tentativas} falhou para {codigo_iata}: {e}')
            if tentativa < tentativas - 1:
                time.sleep(3)

    print(f'[API] Todas as tentativas falharam para: {codigo_iata}')
    return None


def _extrair_dias_flexibilidade(texto):
    """
    Extrai número de dias de flexibilidade do texto.
    Exemplos: '±3 dias' → 3, '+/-2 dias' → 2, '3 dias' → 3, '±1' → 1
    Retorna 0 se não encontrar número.
    """
    if not texto:
        return 0
    match = re.search(r'(\d+)', texto)
    if match:
        return int(match.group(1))
    return 0


def _buscar_voos_data(origem, destino, data_str, demanda, tentativas=3):
    """
    Busca voos para uma data específica usando aeroportos já resolvidos.
    Retorna lista de ofertas.
    """
    print(f'[Skyscanner] Buscando voos em {data_str}: {demanda.origem} -> {demanda.destino}')

    url = 'https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchFlights'
    params = {
        'originSkyId': origem['skyId'],
        'destinationSkyId': destino['skyId'],
        'originEntityId': origem['entityId'],
        'destinationEntityId': destino['entityId'],
        'date': data_str,
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

    headers = {
        'x-rapidapi-key': os.getenv('RAPIDAPI_KEY', ''),
        'x-rapidapi-host': SKYSCANNER_HOST
    }

    for tentativa in range(tentativas):
        try:
            print(f'[Skyscanner] Tentativa {tentativa+1}/{tentativas} - data {data_str}')
            resp = requests.get(url, headers=headers, params=params, timeout=45)
            print(f'[Skyscanner] Status: {resp.status_code}')

            data = resp.json()
            print(f'[Skyscanner] Resposta (primeiros 500 chars): {str(data)[:500]}')

            if not data.get('status'):
                print(f'[Skyscanner] API retornou status False para {data_str}')
                if tentativa < tentativas - 1:
                    time.sleep(5)
                continue

            # Se resultado incompleto, faz segunda chamada com sessionId
            context_status = data.get('data', {}).get('context', {}).get('status', '')
            session_id = data.get('data', {}).get('context', {}).get('sessionId', '')
            if context_status == 'incomplete' and session_id:
                print(f'[Skyscanner] Resultado incompleto, buscando mais com sessionId...')
                time.sleep(3)
                params2 = dict(params)
                params2['sessionId'] = session_id
                resp2 = requests.get(url, headers=headers, params=params2, timeout=45)
                if resp2.status_code == 200:
                    data2 = resp2.json()
                    if data2.get('status'):
                        itins2 = data2.get('data', {}).get('itineraries', [])
                        if len(itins2) > len(data.get('data', {}).get('itineraries', [])):
                            print(f'[Skyscanner] Segunda chamada retornou {len(itins2)} itinerários')
                            data = data2

            itineraries = data.get('data', {}).get('itineraries', [])
            print(f'[Skyscanner] Itinerários encontrados para {data_str}: {len(itineraries)}')

            resultados = []
            for item in itineraries[:25]:
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
                    'link': f'https://www.skyscanner.com.br/transporte/passagens-aereas/{demanda.origem.lower()}/{demanda.destino.lower()}/{data_str.replace("-", "")}/',
                    'fonte': 'skyscanner',
                    'data_voo': data_str
                })

            if resultados:
                return resultados

            if tentativa < tentativas - 1:
                time.sleep(5)

        except Exception as e:
            print(f'[Skyscanner] Erro na tentativa {tentativa+1} para {data_str}: {e}')
            if tentativa < tentativas - 1:
                time.sleep(3)

    return []


def buscar_voos_skyscanner(demanda, tentativas=3):
    """Busca voos no Skyscanner e retorna lista de ofertas."""
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

    # Determina datas a buscar com base na flexibilidade
    dias_flex = _extrair_dias_flexibilidade(demanda.flexibilidade)
    data_base = datetime.strptime(demanda.data_ida, '%Y-%m-%d')

    if dias_flex > 0:
        print(f'[Skyscanner] Flexibilidade de ±{dias_flex} dias detectada!')
        datas = []
        for delta in range(-dias_flex, dias_flex + 1):
            data_candidata = data_base + timedelta(days=delta)
            # Não busca datas passadas
            if data_candidata >= datetime.today():
                datas.append(data_candidata.strftime('%Y-%m-%d'))
        print(f'[Skyscanner] Buscando em {len(datas)} datas: {datas}')
    else:
        datas = [demanda.data_ida]

    todas_ofertas = []
    for data_str in datas:
        ofertas_data = _buscar_voos_data(origem, destino, data_str, demanda, tentativas)
        todas_ofertas.extend(ofertas_data)
        if len(datas) > 1:
            time.sleep(2)  # Pausa entre buscas para não sobrecarregar a API

    print(f'[Skyscanner] Total de ofertas encontradas em todas as datas: {len(todas_ofertas)}')
    return todas_ofertas


def verificar_preco_demanda(demanda):
    """Verifica preços e retorna a melhor oferta ou None."""
    print(f'[Verificar] Iniciando verificação para demanda {demanda.id}: {demanda.origem}->{demanda.destino}')

    ofertas = buscar_voos_skyscanner(demanda)

    if not ofertas:
        print(f'[Verificar] Nenhuma oferta encontrada.')
        return None

    ofertas.sort(key=lambda x: x['preco'])
    melhor = ofertas[0]

    data_info = f' (data: {melhor["data_voo"]})' if melhor.get('data_voo') != demanda.data_ida else ''
    print(f'[Verificar] Melhor oferta: R${melhor["preco"]} via {melhor["companhia"]}{data_info}')
    return melhor
