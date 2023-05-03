from typing import Dict, Union
from utils.api_reqiest import request_to_api
from config_data.config import RAPID_API_HEADERS, RAPID_API_ENDPOINTS
import re
import json
from loguru import logger


@logger.catch
def parse_cities_group(city: str) -> Union[Dict[str, str], None]:
    """
    Функция делает запрос в request_to_api и десериализирует результат. Если запрос получен и десериализация прошла -
    возвращает обработанный результат в виде словаря - подходящие города и их id, иначе None.

    :param city: город для поиска.
    :return: None или словарь с результатом: {'city_name': 'city_id'}
    """
    querystring = {"query": city, "locale": "ru_RU", "currency": "USD"}
    responce = request_to_api(
        url=RAPID_API_ENDPOINTS['cities-groups'],
        querystring=querystring,
        headers=RAPID_API_HEADERS)

    if responce:
        pattern = r'(?<="CITY_GROUP",).+?[\]]'
        find = re.search(pattern, responce.text)
        if find:
            cities = dict()
            try:
                result = json.loads(f"{{{find[0]}}}")
                for entity in result.get('entities'):
                    if entity.get('type') == 'CITY':
                        pattern = r'\<(/?[^>]+)>'
                        city_clear_name = re.sub(pattern, '', entity.get('caption', {}))
                        cities[city_clear_name] = entity.get('geoId')
            except Exception:
                cities = None

            return cities
    return None
