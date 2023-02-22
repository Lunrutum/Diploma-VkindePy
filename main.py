import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from Db_create import engine, Base, Session, write_msg, add_user_fav, add_user_photos, add_to_bl, \
    check_db_user, check_register, check_bl,delete_db_photo, delete_db_blacklist, check_db_favorites, delete_db_favorites, register_user
from setting import group_token, user_token, v
from function_Vkinder import find_user, get_photo, sort_likes, json_create
import requests
from datetime import datetime

vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)

session = Session()
connection = engine.connect()


def loop_bot():
    for this_event in longpoll.listen():
        if this_event.type == VkEventType.MESSAGE_NEW:
            if this_event.to_me:
                message_text = this_event.text
                return message_text, this_event.user_id


def bot_menu(id_num):
    write_msg(
        id_num, f"Привет я бот Vkinder!\n"
                f"\nПервый раз? Пройди регистрацию.\n"
                f"Для регистрации напиши - Да.\n"
                f"Зарегистрирован? Напиши - Поиск.\n"
                f"Избранное - 2\n"
                f"Черный список - b\n")


def info():
    write_msg(
        user_id, f'Последняя анкета.'
                 f'Избранное - 2'
                 f'Черный список - b'
                 f'Поиск? Пиши - Поиск'
                 f'Меню или перезапуск - Начать')


def reg_new_user(id_num):
    write_msg(id_num, 'Регистрация пройдена!')
    write_msg(id_num, 'Начать - для активации\n')
    register_user(id_num)


def to_favorites(ids):
    all_fav_user = check_db_favorites(ids)
    write_msg(ids, f'Те кого вы добавили в избранное:')
    for nums, users in enumerate(all_fav_user):
        write_msg(ids, f'{users.first_name}, {users.second_name}, {users.link}')
        write_msg(ids, '1 - Удалить, 2 - Далее \n4 - Выйти')
        msg_texts, user_ids = loop_bot()
        if msg_texts == '2':
            if nums >= len(all_fav_user) - 1:
                write_msg(
                    user_ids, f'Последняя анкета.\n'
                              f'Начать - для перезапуска\n')
        elif msg_texts == '1':
            delete_db_favorites(users.vk_id)
            delete_db_photo(users.vk_id)
            write_msg(user_ids, f'Анкета удалена.')
            if nums >= len(all_fav_user) - 1:
                write_msg(
                    user_ids, f'Последняя анкета.\n'
                              f'Начать - для перезапуска\n')
        elif msg_texts.lower() == '4':
            write_msg(ids, 'Начать - для старта')
            break
        else:
            input_error()
            break


def to_blacklist(ids):
    all_bl_user = check_bl(ids)
    write_msg(ids, f'Те кого вы добавили в черный список:')
    for num, user in enumerate(all_bl_user):
        write_msg(ids, f'{user.first_name}, {user.second_name}, {user.link}')
        write_msg(ids, '1 - Удалить, 2 - Далее \n4 - Выход')
        msg_texts, user_ids = loop_bot()
        if msg_texts == '2':
            if num >= len(all_bl_user) - 1:
                write_msg(
                    user_ids, f'Последняя анкета.\n'
                              f'Начать - для перезапуска\n')
        elif msg_texts == '1':
            print(user.id)
            delete_db_blacklist(user.vk_id)
            write_msg(user_ids, f'Анкета удалена.')
            if num >= len(all_bl_user) - 1:
                write_msg(
                    user_ids, f'Последняя анкета.\n'
                              f'Начать - для перезапуска\n')
        elif msg_texts.lower() == '4':
            write_msg(ids, 'Начать - для перезапуска')
            break
        else:
            input_error()
            break


def get_info(user_id):
    url = 'https://api.vk.com/method/users.get'
    params = {'user_ids': user_id, 'fields': 'bdate,sex,city',
              'access_token': user_token,
              'v': v}
    res = requests.get(url, params=params)
    json_res_search = res.json()
    try:
        if 'bdate' in json_res_search['response'][0].keys() and \
                len(json_res_search['response'][0]['bdate']) > 7:
            age_use = int(json_res_search['response'][0]['bdate'][-4:])
            age_to = (int(datetime.now().year) - age_use) + 3
            age_at = (int(datetime.now().year) - age_use) - 3

        else:
            write_msg(user_id, 'Возраст от:')
            msg_text, user_id = loop_bot()
            age_to = msg_text[0:1]
            write_msg(user_id, 'Возраст до:')
            msg_text, user_id = loop_bot()
            age_at = msg_text[0:1]

        sex_user = json_res_search['response'][0]['sex']
        if sex_user == 1:
            sex = 2
        elif sex_user == 2:
            sex = 1

        else:
            write_msg(user_id, 'Пол? \n1 - Женский\n2 - Мужской')
            msg_text, user_id = loop_bot()
            sex = msg_text[0:1]

        if 'city' in json_res_search['response'][0]:
            city = json_res_search['response'][0]['city']['title']

        else:
            write_msg(user_id, 'Введите город')
            msg_text, user_id = loop_bot()
            city = msg_text[0:len(msg_text)].lower()

        return sex, age_to, age_at, city
    except KeyError:
        write_msg(user_id, 'Ошибка получения токена.')


def input_error():
    write_msg(user_id, 'Я Вас не понимаю.'
                       '\nНачать - для активации или перезапуска.')
    

if __name__ == '__main__':
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    while True:
        msg_text, user_id = loop_bot()

        if msg_text[0:6].lower() == 'начать':
            bot_menu(user_id)
            msg_text, user_id = loop_bot()

            if msg_text.lower() == 'да':
                cur_user_id = check_register(user_id)
                if cur_user_id:
                    write_msg(user_id, 'Вы уже зарегистрированы.'
                                       '\nНачать - для активации или перезапуска.')
                else:
                    reg_new_user(user_id)

            elif msg_text[0:5].lower() == 'поиск':
                try:
                    sex, age_to, age_at, city = get_info(user_id)
                    res_search = find_user(sex, int(age_at), int(age_to), city)
                    json_create(res_search)
                    cur_user_id = check_register(user_id)
                    for i in range(len(res_search)):
                        favorites, black_list_user = check_db_user(res_search[i][3])
                        user_photo = get_photo(res_search[i][3])
                        if user_photo == 'нет доступа' or favorites is not None or black_list_user is not None:
                            continue
                        sor_user_photo = sort_likes(user_photo)
                        write_msg(
                            user_id,
                            f'\n{res_search[i][0]}  {res_search[i][1]}  {res_search[i][2]}',
                        )
                        try:
                            write_msg(user_id,
                                      f'фото:',
                                      attachment=','.join([
                                          sor_user_photo[-1][1], sor_user_photo[-2][1],
                                          sor_user_photo[-3][1]
                                      ]))
                        except IndexError:
                            for photo in range(len(sor_user_photo)):
                                write_msg(user_id,
                                          f'фото:',
                                          attachment=sor_user_photo[photo][1])
                        write_msg(
                            user_id,
                            '1 - В избранное, 2 - В черный список, 3 - Далее, \n4 - выход'
                        )
                        msg_text, user_id = loop_bot()
                        if msg_text == '3':
                            if i >= len(res_search) - 1:
                                info()
                        elif msg_text == '1':
                            if i >= len(res_search) - 1:
                                info()
                                break
                            try:
                                add_user_fav(user_id, res_search[i][3], res_search[i][1], res_search[i][0], city,
                                             res_search[i][2], cur_user_id.id)
                                add_user_photos(user_id, sor_user_photo[0][1], res_search[i][3],
                                                sor_user_photo[0][0], cur_user_id.id)
                            except AttributeError:
                                write_msg(
                                    user_id,
                                    'Для начала Зарегистрируйтесь!\n Введите - Начать для перезагрузки'
                                )
                                break
                        elif msg_text == '2':
                            if i >= len(res_search) - 1:
                                info()
                            add_to_bl(user_id, res_search[i][3], res_search[i][1],
                                      res_search[i][0], city, res_search[i][2],
                                      sor_user_photo[0][1], sor_user_photo[0][0],
                                      cur_user_id.id)
                        elif msg_text.lower() == '4':
                            write_msg(user_id, 'Пока.')
                            break
                        else:
                            input_error()
                            break
                except Exception:
                    write_msg(user_id, 'Что-то не так.'
                                       '\nНачать - для перезагрузки.')

            elif msg_text == '2':
                to_favorites(user_id)

            elif msg_text == 'b':
                to_blacklist(user_id)

            else:
                input_error()

        elif len(msg_text) > 0:
            write_msg(user_id, f'Привет! '
                               f'\nНачать - для активации.')
