from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import requests, json

num = 0
counter = 0
test_num = 0
error = []
error_str = ''
all_test = 0
reply_keyboard = [['дальше', '/stop']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)

def geocode(address):
    geocoder_request = "http://geocode-maps.yandex.ru/1.x/?geocode={address}&format=json".format(**locals())

    response = requests.get(geocoder_request)

    if response:
        json_response = response.json()
    else:
        raise RuntimeError(
            """Ошибка выполнения запроса:
            {request}
            Http статус: {status} ({reason})""".format(
                request=geocoder_request, status=response.status_code, reason=response.reason))

    features = json_response["response"]["GeoObjectCollection"]["featureMember"]
    return features[0]["GeoObject"] if features else None


def get_coordinates(address):
    toponym = geocode(address)
    if not toponym:
        return (None, None)

    toponym_coodrinates = toponym["Point"]["pos"]
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
    return float(toponym_longitude), float(toponym_lattitude)


def show_map(ll_spn=None, coord=None, map_type="sat"):
    if ll_spn and coord:
        map_request = "http://static-maps.yandex.ru/1.x/?{ll_spn}&l={map_type}&pt={coord[0]},{coord[1]},pm2bll".format(**locals())
    else:
        map_request = "http://static-maps.yandex.ru/1.x/?l={map_type}".format(**locals())

    return map_request


def start(bot, update):
    update.message.reply_text(
        'Привет!\n'
        'Я очень люблю географию, а особенно люблю географические карты. Из-за этого меня прозвали "бот-географ."\n'
        'Уже очень давно я ищу себе соперника для географического батла. Интересно, можешь ты стать моим соперником или нет. Для этого тебе необходимо пройти тестирование. Ты согласен?')
    return 1


def test_answer(bot, update):
    if update.message.text.lower() == 'да' or update.message.text.lower() == 'новый тест':
        update.message.reply_text("Отлино! (если ты не знаком с правилами тестирования, начни с обучающего теста)\n"
                                  "Выбери тест:\n"
                                  "-Обучение\n"
                                  "-Моря\n"
                                  "-Острова\n"
                                  "-Озёра")
        return 2
    else:
        update.message.reply_text('Хм... Мои тесты не самые сложные, так что волноваться не надо. Если ты уверен в своих силах и хочешь проверить свои знания, напиши "да", а если нет, то воспользуйся командой /stop')
        return 1


def test_choice(bot, update):
    global test
    if update.message.text in data:
        test = data[update.message.text]

        if test == data['Обучение']:
            update.message.reply_text('Внизу (под полем ввода) появилась клавиатура с двумя клавишами.\n'
                                      'Клавишу "дальше" необходимо нажимать после того, как введёшь ответ на вопрос\n'
                                      'Клавишу "stop" - если захочешь выйти из теста (при этом результаты тестирования не сохраняются)')

        update.message.reply_text('Чтобы начать тест, напиши "старт"', reply_markup = markup)
        return 3
    else:
        update.message.reply_text("Такого теста нет. Введи название из предложенных вариантов.")
        return 2


def test_question(bot, update):
    if test == data['Обучение']:
        update.message.reply_text('Сейчас твой тест посвящён континентам. Это снимок объекта со спутника. Объект, название которого нужно написать, отмечен голубой меткой. В ответ пиши точное название объекта. После того, как введёшь ответ, нажми на клавиатуре кнопку "дальше".')

    if test == data['Озёра']:
        update.message.reply_text('В ответ пиши название объекта вместе со слвом озеро. Например: озеро Байкал, Ладожское озеро')

    toponym_to_find = test["question"][num]
    lat, lon = get_coordinates(toponym_to_find)
    coord = (lat, lon)
    spn = test["spn"]
    ll_spn = "ll={0},{1}&spn={2},{2}".format(lat, lon, spn)

    bot.sendPhoto(
        update.message.chat.id, show_map(ll_spn, coord))

    return 4


def test_check(bot, update):
    global counter, num, error

    if test == data['Обучение'] and update.message.text != test["question"][num]:
        update.message.reply_text('Это неправильный ответ. Вводи название объекта без ошибок. Подсказка: ' + test["question"][num])
        return 4
    else:

        if update.message.text == test["question"][num]:
            counter += 1
        else:
            error.append(num+1)
        num += 1

        if num != len(test["question"]):
            return 3
        else:
            return 5


def test_result(bot, update):
    global num, counter, test_num, error, error_str, all_test

    if counter == 8:
        test_num += 1
        all_test += 1

    for num in error:
        error_str += str(num)+" "

    if test != data['Обучение']:
        update.message.reply_text('Правильных ответов: ' + str(counter) + ' из ' + str(len(test["question"])))
        if len(error) != 0:
            update.message.reply_text('Ошибка допущена в вопросах № ' + error_str)
        if test_num == 1:
            update.message.reply_text('Вау! Да ты просто ас в географических картах! С тобой будет интересно посоревноваться.')
        elif all_test == 3 and test_num == 1:
            update.message.reply_text('Вот это да! Ты прошёл все тесты и получил максимальный балл! Теперь ты точно готов к географическому батлу!')
        else:
            update.message.reply_text('Тебе ёщё надо потренироваться, чтобы достичь моего уровня.')

        update.message.reply_text('Если хочешь пройти этот тест заново или начать другой, напиши "новый тест"\n'
                              'Иначе воспользуйся командой /stop')
    else:
        update.message.reply_text('Теперь ты готов к тестированию. Напиши "новый тест" и проверь свои знания :)')

    num = 0
    counter = 0
    error_str = ''
    error = []

    return 1


def stop(bot, update):
    update.message.reply_text(
        "Очень жаль) Надеюсь, ещё увидимся :)", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    global data

    with open('test.json', 'r', encoding='utf-8') as fh:
        data = json.load(fh)

    updater = Updater("550967687:AAExUqJGHHab89cQf8TlfVTsVqcS5XzSWWQ")

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            1: [MessageHandler(Filters.text, test_answer)],
            2: [MessageHandler(Filters.text, test_choice)],
            3: [MessageHandler(Filters.text, test_question)],
            4: [MessageHandler(Filters.text, test_check)],
            5: [MessageHandler(Filters.text, test_result)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()