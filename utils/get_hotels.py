from typing import Dict, List, Union
from config_data.config import RAPID_API_HEADERS, RAPID_API_ENDPOINTS
from loguru import logger
import re
import requests
import json


@logger.catch
def parse_hotels(data_dict: Dict) -> Union[Dict[str, List[Dict]], None]:
    """
    Функция делает запрос и десериализирует результат. Если запрос получен и десериализация прошла -
    возвращает обработанный результат в виде словаря, иначе None.

    :param data_dict: словарь - данные для запроса по api.
    :return: None или словарь с ключом 'results' и значением - списком словарей полученных отелей.
    """

    if data_dict.get('last_command') == 'highprice':
        sort_order = 'PROPERTY_CLASS'
    else:
        sort_order = "PRICE_LOW_TO_HIGH"

    if data_dict.get('last_command') in ('highprice', 'lowprice'):
        querystring = {
            "currency": "USD",
            "eapid": 1,
            "locale": "ru_RU",
            "siteId": 300000001,
            "destination": {
                "regionId": data_dict['city_id'],
            },
            "checkInDate": {
                "day": data_dict['start_date'].day,
                "month": data_dict['start_date'].month,
                "year": data_dict['start_date'].year
            },
            "checkOutDate": {
                "day": data_dict['end_date'].day,
                "month": data_dict['end_date'].month,
                "year": data_dict['end_date'].year
            },
            "rooms": [
                {
                    "adults": 2,
                    "children": []
                }
            ],
            "resultsSize": data_dict['amount_hotels'],
            "sort": sort_order,
        }

    else:
        querystring = {
            "currency": "USD",
            "eapid": 1,
            "locale": "ru_RU",
            "siteId": 300000001,
            "destination": {
                "regionId": data_dict['city_id'],
            },
            "checkInDate": {
                "day": data_dict['start_date'].day,
                "month": data_dict['start_date'].month,
                "year": data_dict['start_date'].year
            },
            "checkOutDate": {
                "day": data_dict['end_date'].day,
                "month": data_dict['end_date'].month,
                "year": data_dict['end_date'].year
            },
            "rooms": [
                {
                    "adults": 2,
                    "children": []
                }
            ],
            "resultsSize": data_dict['amount_hotels'],
            "sort": sort_order,
            "filters": {
                "price": {
                    "max": data_dict['end_price'],
                    "min": data_dict['start_price']
                }
            }
        }

    responce = requests.request(
        "POST",
        url=RAPID_API_ENDPOINTS['hotel-list'],
        json=querystring,
        headers=RAPID_API_HEADERS
    )

    if responce:
        pattern = r'(?<=,)"properties":.+?(?=,"propertySearchListings)'
        find = re.search(pattern, responce.text)
        if find:
            result = json.loads(f"{{{find[0]}}}")
            return result
    return None


@logger.catch
def process_hotels_info(hotels_info_list: List[Dict], amount_nights: int) -> Dict[int, Dict]:
    """
    Функция получает список словарей - результат парсинга отелей, выбирает нужную информацию, обрабатывает и складывает
    в словарь hotels_info_dict

    :param hotels_info_list: список со словарями. Каждый словарь - полная информация по отелю (результат парсинга).
    :param amount_nights: количество ночей.
    :return: словарь с информацией по отелю: {hotel_id: {hotel_info}} (теоретически может быть пустым).
    """

    hotels_info_dict = dict()
    for hotel in hotels_info_list:
        hotel_id = hotel.get('id')
        if not hotel_id:
            continue
        hotel_url = f'https://www.hotels.com/h{str(hotel_id)}.Hotel-Information'
        hotel_name = hotel.get('name', 'No name')
        price_per_night = round(hotel['price']['lead']['amount'], 2)
        total_price = round(price_per_night * amount_nights, 2)

        distance_city_center = round(hotel['destinationInfo']['distanceFromDestination']['value'] * 1.609, 2)

        neighborhood = hotel.get('neighborhood', 'No data')
        if neighborhood is None:
            hotel_neighbourhood = 'No data'
        else:
            hotel_neighbourhood = hotel.get('neighborhood', 'No data').get('name', 'No data')

        hotels_info_dict[hotel_id] = {
            'name': hotel_name,
            'price_per_night': price_per_night,
            'total_price': total_price,
            'distance_city_center': distance_city_center,
            'hotel_url': hotel_url,
            'hotel_neighbourhood': hotel_neighbourhood
        }
    return hotels_info_dict


@logger.catch
def get_hotel_info_str(hotel_data: Dict, amount_nights: int) -> str:
    """
    Функция преобразует данные по отелю из словаря в строку с html.
    Используется для вывода информации через сообщение (bot.send_message).

    :param hotel_data: словарь с информацией по отелю.
    :param amount_nights: количество ночей.
    :return: строка с html с информацией по отелю
    """

    result = f"<b>🏩 Отель:</b> {hotel_data['name']}\n" \
             f"<b>📍 Район:</b> {hotel_data['hotel_neighbourhood']}\n" \
             f"<b>🚕 Расстояние до центра:</b> {hotel_data['distance_city_center']} Км\n" \
             f"<b>💰 Цена за 1 ночь: </b> от {hotel_data['price_per_night']}$\n" \
             f"<b>💰💰 Примерная стоимость за {amount_nights} ноч.:</b> {hotel_data['total_price']}$\n" \
             f"<b>⚓️ Подробнее об отеле <a href='{hotel_data['hotel_url']}'>на сайте >></a></b>"
    return result


@logger.catch
def get_hotel_info_str_nohtml(hotel_data: Dict, amount_nights: int) -> str:
    """
    Функция преобразует данные по отелю из словаря в строку без html.
    Используется для вывода информации через медиа группу (bot.send_media_group).

    :param hotel_data: словарь с информацией по отелю.
    :param amount_nights: количество ночей.
    :return: строка без html с информацией по отелю.
    """

    result = f"🏩 {hotel_data['name']}\n" \
             f"📍 Район: {hotel_data['hotel_neighbourhood']}\n" \
             f"🚕 Расстояние до центра: {hotel_data['distance_city_center']} Км\n" \
             f"💰 Цена за 1 ночь: от {hotel_data['price_per_night']}$\n" \
             f"💰💰 Примерная стоимость за {amount_nights} ноч.: {hotel_data['total_price']}$\n" \
             f"⚓️ Подробнее об отеле: {hotel_data['hotel_url']}"
    return result
