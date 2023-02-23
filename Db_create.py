from random import randrange
from sqlalchemy.exc import IntegrityError, InvalidRequestError
import sqlalchemy as sq
import vk_api
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from vk_api.longpoll import VkLongPoll

from setting import group_token

vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)

Base = declarative_base()
engine = sq.create_engine('postgresql://postgres:***@localhost:5432/name',
                          client_encoding='utf8')

if not database_exists(engine.url):
    create_database(engine.url)
    print('Создана база данных')

Session = sessionmaker(bind=engine)
session = Session()
engine.connect()
connection = engine.connect()


class VKUser(Base):
    __tablename__ = 'vk_users'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    vk_id = sq.Column(sq.Integer, unique=True)


class Favorites(Base):
    __tablename__ = 'favorites'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    first_name = sq.Column(sq.String)
    second_name = sq.Column(sq.String)
    city = sq.Column(sq.String)
    link = sq.Column(sq.String)
    id_user = sq.Column(sq.Integer, sq.ForeignKey('vk_users.id', ondelete='CASCADE'))


class Watched(Base):
    __tablename__ = 'watched'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    id_watch_users = sq.Column(sq.Integer, sq.ForeignKey('vk_users.id', ondelete='CASCADE'))


class BlackList(Base):
    __tablename__ = 'black_list'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    first_name = sq.Column(sq.String)
    second_name = sq.Column(sq.String)
    city = sq.Column(sq.String)
    link = sq.Column(sq.String)
    link_photo = sq.Column(sq.String)
    likes = sq.Column(sq.Integer)
    vk_users = sq.Column(sq.Integer, sq.ForeignKey('vk_users.id', ondelete='CASCADE'))


def add_user_fav(event_id, vk_id, first_name, second_name, city, link, id_user):
    try:
        new_user = Favorites(vk_id=vk_id, first_name=first_name, second_name=second_name, city=city, link=link,
                             id_user=id_user)
        session.add(new_user)
        session.commit()
        write_msg(event_id, 'Добавлен в избранное.')
        return True
    except (IntegrityError, InvalidRequestError):
        write_msg(event_id, 'Уже в избранном.')
        return False


def add_user_watched(event_id, vk_id, id_watch_users):
    try:
        new_user = Watched(vk_id=vk_id, id_watch_users = id_watch_users )
        session.add(new_user)
        session.commit()
        return True
    except (IntegrityError, InvalidRequestError):
        write_msg(event_id,
                  'Не удалось сохранить в базу данных просмотренную анкету')
        return False


def add_to_bl(event_id, vk_id, first_name, second_name, city, link, link_photo, likes, vk_users):
    try:
        new_user = BlackList(vk_id=vk_id, first_name=first_name, second_name=second_name, city=city, link=link,
                             link_photo=link_photo, likes=likes, vk_users=vk_users)
        session.add(new_user)
        session.commit()
        write_msg(event_id, 'Заблокирован.')
        return True
    except (IntegrityError, InvalidRequestError):
        write_msg(event_id, 'Был заблокирован ранее.')
        return False


def delete_db_blacklist(ids):
    user_for_bd = session.query(BlackList).filter_by(vk_id=ids).first()
    session.delete(user_for_bd)
    session.commit()


def delete_db_favorites(ids):
    user_for_fav = session.query(Favorites).filter_by(vk_id=ids).first()
    session.delete(user_for_fav)
    session.commit()


# def delete_db_photo(ids):
#     user_find_photos = session.query(Photos).filter_by(vk_id=ids).first()
#     session.delete(user_find_photos)
#     session.commit()


def register_user(vk_id):
    new_user = VKUser(vk_id=vk_id)
    session.add(new_user)
    session.commit()
    return True


def check_register(ids):
    check_user_id = session.query(VKUser).filter_by(vk_id=ids).first()
    return check_user_id


def check_db_user(ids):
    fav_user = session.query(Favorites).filter_by(vk_id=ids).first()
    bl_user = session.query(BlackList).filter_by(vk_id=ids).first()
    watch_user = session.query(Watched).filter_by(vk_id=ids).first()
    return fav_user, bl_user, watch_user


def check_bl(ids):
    check_bl_user = session.query(VKUser).filter_by(vk_id=ids).first()
    bl_all_users = session.query(BlackList).filter_by(vk_users=check_bl_user.id).all()
    return bl_all_users


def check_db_favorites(ids):
    check_fav_user = session.query(VKUser).filter_by(vk_id=ids).first()
    fav_all_users = session.query(Favorites).filter_by(id_user=check_fav_user.id).all()
    return fav_all_users


def write_msg(user_id, message, attachment=None):
    vk.method(
        'messages.send', {
            'user_id': user_id,
            'message': message,
            'random_id': randrange(10 ** 7),
            'attachment': attachment
        })



if __name__ == '__main__':
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
