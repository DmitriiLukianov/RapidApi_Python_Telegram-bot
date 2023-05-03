from loader import bot
from telebot.types import Message, CallbackQuery
from keyboards.inline.yes_no_reply import get_yes_no
from keyboards.inline.cities_for_choice import print_cities
from utils.factories import for_city
from states.search_info import UsersStates
from telegram_bot_calendar import DetailedTelegramCalendar
from datetime import date, timedelta
from utils.get_cities import parse_cities_group
from utils.ready_for_answer import low_high_price_answer, best_deal_answer
from loguru import logger
import re


@bot.message_handler(state=UsersStates.cities, is_digit=True)  # Если название города - цифры
@logger.catch
def get_city_incorrect(message: Message) -> None:
    """
    Функция, ожидающая некорректный ввод города. Если название города - цифры - выводит сообщение об ошибке.

    :param message: сообщение Telegram
    """

    bot.send_message(message.from_user.id, '⚠️ Название города должно состоять из букв')


@bot.message_handler(state=UsersStates.cities, is_digit=False)  # Если название города - не цифры
@logger.catch
def get_city(message: Message) -> None:
    """
    Функция, ожидающая корректный ввод города.
    Записывает состояние пользователя 'cities' и показывает клавиатуру с выбором конкретного города для уточнения.

    :param message: сообщение Telegram
    """

    cities_dict = parse_cities_group(message.text)
    if cities_dict:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['cities'] = cities_dict
        bot.send_message(message.from_user.id, 'Пожалуйста, уточните:', reply_markup=print_cities(cities_dict))
    else:
        bot.send_message(message.from_user.id, '⚠️ Не нахожу такой город. Введите ещё раз.')


@bot.callback_query_handler(func=None, city_config=for_city.filter())
@logger.catch
def clarify_city(call: CallbackQuery) -> None:
    """
    Функция, реагирующая на нажатие кнопки с выбором конкретного города.
    Записывает состояния пользователя 'city_id' и 'city' выбранного города.
    Предлагает ввести количество отелей.

    :param call: отклик клавиатуры.
    """
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.delete_message(call.message.chat.id, call.message.message_id)

    with bot.retrieve_data(call.message.chat.id, call.message.chat.id) as data:
        data['city_id'] = re.search(r'\d+', call.data).group()
        data['city'] = [city for city, city_id in data['cities'].items() if city_id == data['city_id']][0]
    bot.set_state(call.from_user.id, UsersStates.amount_hotels, call.message.chat.id)
    bot.send_message(call.message.chat.id, 'Сколько отелей найти?')


@bot.message_handler(state=UsersStates.amount_hotels, is_digit=True)  # Если количество отелей - число
@logger.catch
def get_amount_hotels(message: Message) -> None:
    """
    Функция, ожидающая корректный ввод количества отелей.
    Записывает состояние пользователя 'amount_hotels' и показывает клавиатуру с вопросом о необходимости
    загрузить фото отелей. Варианты ответа: 'да' и 'нет'.

    :param message: сообщение Telegram
    """

    if 1 <= int(message.text) <= 10:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['amount_hotels'] = int(message.text)
        bot.send_message(message.from_user.id, 'Желаете загрузить фото отелей?', reply_markup=get_yes_no())
    else:
        bot.send_message(message.from_user.id, '⚠️ Количество отелей в топе должно быть от 1 до 10')


@bot.message_handler(state=UsersStates.amount_hotels, is_digit=False)  # Если количество отелей - не число
@logger.catch
def amount_hotels_incorrect(message: Message) -> None:
    """
    Функция, ожидающая некорректный ввод количества отелей.
    Если количество отелей - не число - выводит сообщение об ошибке.

    :param message: сообщение Telegram
    """

    bot.send_message(message.from_user.id, '⚠️ Количество отелей должно быть от 1 до 10')


@bot.callback_query_handler(func=lambda call: call.data == 'yes' or call.data == 'no')
@logger.catch
def need_photo_reply(call: CallbackQuery) -> None:
    """
    Функция, реагирующая на нажатие кнопки 'да' и 'нет' на вопрос о необходимости загрузить фото отелей.
    Если ответ 'да': записывает состояния пользователя 'need_photo' = True и предлагает ввести количество фото.
    Если ответ 'нет': записывает состояния пользователя 'need_photo' = False и 'amount_photo' = 0 и
    показывает клавиатуру-календарь с выбором даты заезда.

    :param call: отклик клавиатуры.
    """

    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    with bot.retrieve_data(call.message.chat.id, call.message.chat.id) as data:
        if call.data == "yes":
            bot.send_message(call.message.chat.id, text='Введите количество фото')
            data['need_photo'] = True
            bot.set_state(call.from_user.id, UsersStates.amount_photo, call.message.chat.id)
        elif call.data == "no":
            data['need_photo'] = False
            data['amount_photo'] = 0
            calendar, step = DetailedTelegramCalendar(min_date=date.today()).build()
            bot.send_message(call.message.chat.id, f"Введите дату заезда", reply_markup=calendar)
        else:
            bot.send_message(call.message.chat.id, text='⚠️ Нажмите кнопку "Да" или "Нет"')


@bot.message_handler(state=UsersStates.amount_photo, is_digit=True)  # Если количество фото - число
@logger.catch
def get_amount_photo(message: Message) -> None:
    """
    Функция, ожидающая корректный ввод количества фото.
    Записывает состояние пользователя 'amount_photo' и показывает клавиатуру-календарь с выбором даты заезда.

    :param message: сообщение Telegram
    """

    if 1 <= int(message.text) <= 10:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['amount_photo'] = int(message.text)
        calendar, step = DetailedTelegramCalendar(min_date=date.today()).build()
        bot.send_message(message.chat.id, f"Введите дату заезда", reply_markup=calendar)
    else:
        bot.send_message(message.from_user.id, '⚠️ Количество фото должно быть от 1 до 10')


@bot.message_handler(state=UsersStates.amount_photo, is_digit=False)  # Если количество фото - не число
@logger.catch
def amount_photo_incorrect(message: Message) -> None:
    """
    Функция, ожидающая некорректный ввод количества фото.
    Если количество фото - не число - выводит сообщение об ошибке.

    :param message: сообщение Telegram
    """

    bot.send_message(message.from_user.id, '⚠️ Количество фото от 1 до 10')


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
@logger.catch
def date_reply(call: CallbackQuery) -> None:
    """
    Функция, реагирующая на нажатие кнопки на клавиатуре-календаре.
    Проверяет, записаны ли состояния 'start_date' и 'end_date'.
    Если нет - снова предлагает выбрать дату и записывает эти состояния.
    Если да, то проверяет состояние пользователя 'last_command'.
    Если 'last_command' == 'lowprice' или 'highprice' - завершает опрос и
    вызывает функцию для подготовки ответа на запрос пользователя. Затем ожидает ввода следующей команды.
    Иначе продолжает опрос и предлагает ввести минимальную цену за ночь.

    :param call: отклик клавиатуры.
    """

    with bot.retrieve_data(call.message.chat.id, call.message.chat.id) as data:
        if not data.get('start_date'):
            result, key, step = DetailedTelegramCalendar(min_date=date.today()).process(call.data)
        elif not data.get('end_date'):
            new_start_date = data.get('start_date') + timedelta(1)
            result, key, step = DetailedTelegramCalendar(min_date=new_start_date).process(call.data)

    if not result and key:
        bot.edit_message_text("Введите дату", call.message.chat.id, call.message.message_id, reply_markup=key)
    elif result:
        with bot.retrieve_data(call.message.chat.id, call.message.chat.id) as data:
            if not data.get('start_date'):
                data['start_date'] = result
                calendar, step = DetailedTelegramCalendar(min_date=result + timedelta(1)).build()
                bot.edit_message_text("Введите дату выезда",
                                      call.message.chat.id, call.message.message_id, reply_markup=calendar)
            elif not data.get('end_date'):
                data['end_date'] = result

                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

                if data.get('last_command') in ('lowprice', 'highprice'):
                    data_dict = data
                    low_high_price_answer(call.message, data_dict, call.from_user.username)
                    bot.set_state(call.from_user.id, UsersStates.last_command, call.message.chat.id)
                    bot.send_message(call.message.chat.id,
                                     f"Введите следующую команду команду!\n"
                                     f"Например: <b>/help</b>", parse_mode="html")
                else:
                    bot.set_state(call.from_user.id, UsersStates.start_price, call.message.chat.id)
                    bot.send_message(call.message.chat.id, "Введите минимальную цену за ночь $:")


@bot.message_handler(state=UsersStates.start_price, is_digit=True)  # Если количество $ - число
@logger.catch
def get_start_price(message: Message) -> None:
    """
    Функция, ожидающая корректный ввод количества $.
    Записывает состояние пользователя 'start_price' и предлагает ввести максимальную цену за ночь.

    :param message: сообщение Telegram
    """

    if int(message.text) > 0:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['start_price'] = int(message.text)
        bot.set_state(message.from_user.id, UsersStates.end_price, message.chat.id)
        bot.send_message(message.chat.id, "Введите максимальную цену за ночь $:")
    else:
        bot.send_message(message.from_user.id, '⚠️ Введите число больше нуля')


@bot.message_handler(state=UsersStates.start_price, is_digit=False)  # Если количество $ - не число
@logger.catch
def start_price_incorrect(message: Message) -> None:
    """
    Функция, ожидающая некорректный ввод количества $.
    Если количество $ - не число - выводит сообщение об ошибке.

    :param message: сообщение Telegram
    """

    bot.send_message(message.from_user.id, '⚠️ Введите число больше нуля')


@bot.message_handler(state=UsersStates.end_price, is_digit=True)  # Если количество $ - число
@logger.catch
def get_end_price(message: Message) -> None:
    """
    Функция, ожидающая корректный ввод количества $.
    Записывает состояние пользователя 'end_price' и предлагает ввести максимальное расстояние до центра в км.

    :param message: сообщение Telegram
    """

    if int(message.text) > 0:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if int(message.text) > data['start_price']:
                data['end_price'] = int(message.text)
                bot.set_state(message.from_user.id, UsersStates.end_distance, message.chat.id)
                bot.send_message(message.chat.id, "Введите максимальное расстояние до центра в км\n"
                                                  "(например 13.5):")
            else:
                bot.send_message(message.chat.id,
                                 f"⚠️ Максимальная цена должна быть больше {data['start_price']}$")
    else:
        bot.send_message(message.from_user.id, '⚠️ Введите число больше нуля')


@bot.message_handler(state=UsersStates.end_price, is_digit=False)  # Если количество $ - не число
@logger.catch
def end_price_incorrect(message: Message) -> None:
    """
    Функция, ожидающая некорректный ввод количества $.
    Если количество $ - не число - выводит сообщение об ошибке.

    :param message: сообщение Telegram
    """

    bot.send_message(message.from_user.id, '⚠️ Введите число больше нуля')


@bot.message_handler(state=UsersStates.end_distance)
@logger.catch
def get_end_distance(message: Message) -> None:
    """
    Функция, ожидающая ввод максимального расстояния до центра.
    Записывает состояние пользователя 'end_distance', завершает опрос и
    вызывает функцию для подготовки ответа на запрос пользователя.
    Затем ожидает ввода следующей команды.

    :param message: сообщение Telegram
    """

    if ',' in message.text:
        message.text = message.text.replace(',', '.')

    try:
        message.text = float(message.text)
        if message.text > 0:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['end_distance'] = message.text
                data_dict = data
                best_deal_answer(message, data_dict, message.from_user.username)
                bot.set_state(message.from_user.id, UsersStates.last_command, message.chat.id)
                bot.send_message(message.chat.id, f"Введите следующую команду!\n"
                                                  f"Например: <b>/help</b>", parse_mode="html")
        else:
            bot.send_message(message.from_user.id, '⚠️ Введите число больше нуля')
    except Exception:
        bot.set_state(message.from_user.id, UsersStates.last_command, message.chat.id)
        bot.send_message(message.chat.id, "⚠️⚠️⚠️Ошибка. Попробуйте еще раз.\n"
                                          "Введите команду! Например: <b>/help</b>", parse_mode="html")
