import datetime
import json
import vk_api
from vk_api.exceptions import ApiError
from Db_create import engine,Session
from setting import group_token, user_token, v
from vk_api.longpoll import VkLongPoll
from random import randrange


vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)

session = Session()
connection = engine.connect()

def write_msg(user_id, message, attachment=None):
  vk.method(
      'messages.send', {
      'user_id': user_id,
      'message': message,
      'random_id': randrange(10**7),
      'attachment': attachment
    })

def find_user(sex, age_at, age_to, city):
  all_persons = []
  link_profile = 'https://vk.com/id'
  vk_ = vk_api.VkApi(token=user_token)
  res = vk_.method(
      'users.search', {
      'sort': 1,
      'sex': sex,
      'status': 6,
      'age_from': age_at,
      'age_to': age_to,
      'has_photo': 1,
      'count': 200,
      'online': 0,
      'hometown': city
     })
  try:
    for element in res['items']:
      person = [
        element['first_name'], element['last_name'],
        link_profile + str(element['id']), element['id'],
      ]
      all_persons.append(person)
    return all_persons
  except Exception:
      write_msg(user_id, 'Что-то пошло не так.'
                         '\nVkinder - для активации бота.')


def get_photo(user_owner_id):
  vk_ = vk_api.VkApi(token=user_token)
  try:
    response = vk_.method(
      'photos.get', {
      'access_token': user_token,
      'v': v,
      'owner_id': user_owner_id,
      'album_id': 'profile',
      'extended': 1,
      'photo_sizes': 1,
      })
  except ApiError:
    return 'нет доступа к фото'
  users_photos = []
  for i in range(10):
    try:
      users_photos.append([
        response['items'][i]['likes']['count'],
        'photo' + str(response['items'][i]['owner_id']) + '_' +
        str(response['items'][i]['id'])
      ])
    except IndexError:
      users_photos.append(['нет фото.'])
  return users_photos


def sort_likes(photos):
  result = []
  for element in photos:
    if element != ['нет фото.'] and photos != 'нет доступа к фото':
            result.append(element)
  return sorted(result)


def json_create(lst):
  today = datetime.date.today()
  today_str = f'{today.day}.{today.month}.{today.year}'
  res = {}
  res_list = []
  for num, info in enumerate(lst):
    res['data'] = today_str
    res['first_name'] = info[0]
    res['second_name'] = info[1]
    res['link'] = info[2]
    res['id'] = info[3]
    res_list.append(res.copy())

  with open("result.json", "a", encoding='UTF-8') as write_file:
    json.dump(res_list, write_file, ensure_ascii=False)

  print(f'Информация о загруженных файлах успешно записана в json файл.')

