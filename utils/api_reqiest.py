import requests
from requests.models import Response
from typing import Dict, Union
from loguru import logger


@logger.catch
def request_to_api(url: str, querystring: Dict, headers: Dict) -> Union[Response, None]:
    """
    Функция осуществляет get-запрос к api. Если ответ == 200: возвращает результат, иначе None.

    :param url: строка с энд-пойнтом для запроса.
    :param querystring: словарь с параметрами для запроса.
    :param headers: словарь с "X-RapidAPI-Key" и "X-RapidAPI-Host"
    :return: ответ от api или None
    """
    try:
        request = requests.get(url=url, params=querystring, headers=headers, timeout=10)
        if request.status_code == requests.codes.ok:
            return request
    except Exception:
        return None
