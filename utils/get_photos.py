from typing import Dict, List, Union
from config_data.config import RAPID_API_HEADERS, RAPID_API_ENDPOINTS
from loguru import logger
import json
import requests


@logger.catch
def parse_photos(hotel_id: int) -> Union[List[Dict], None]:
    """
    Функция делает запрос в request_to_api и десериализирует результат. Если запрос получен и десериализация прошла -
    возвращает обработанный результат в виде списка словарей, иначе None.

    :param hotel_id: id отеля для запроса по api.
    :return: None или список словарей с полной информацией по фоткам отеля.
    """

    querystring = {
        "currency": "USD",
        "eapid": 1,
        "locale": "ru_RU",
        "siteId": 300000001,
        "propertyId": hotel_id
    }

    responce = requests.request(
        "POST",
        url=RAPID_API_ENDPOINTS['hotel-photos'],
        json=querystring,
        headers=RAPID_API_HEADERS
    )

    if responce and responce.text != '':
        result = json.loads(responce.text)['data']['propertyInfo']['propertyGallery']['images']
        return result
    return None


@logger.catch
def process_photos(all_photos: List[Dict], amount_photos: int) -> Union[List[str], None]:
    """
    Функция получает список словарей - результат парсинга фоток, выбирает нужную информацию, обрабатывает и складывает
    в список result.

    :param all_photos: список словарей с полной информацией по фоткам отеля.
    :param amount_photos: количество фотографий.
    :return: result - список заданной в amount_photos длины с url фоток.
    """

    photos = all_photos[:amount_photos]
    result = list()
    for photo in photos:
        try:
            url = photo.get('image').get('url')
            result.append(url)
        except Exception:
            result = None

    return result
