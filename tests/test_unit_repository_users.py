import unittest
import datetime
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.database.models import User, Base
from src.schemas import UserModel, UserDb
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_avatar,
)


class TestUsers(unittest.IsolatedAsyncioTestCase):

    def compare_user_attrs(self,user1, user2):
        self.assertEqual(user1.username, user2.username)
        self.assertEqual(user1.email, user2.email)
        self.assertEqual(user1.password, user2.password)


    test_user = User(username="Andriy", email="andriy@gmail.com", password="test r 1")

    def setUp(self):
        engine = create_engine('sqlite:///./test.db')
        DBSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = DBSession()
        Base.metadata.create_all(bind=engine)
        self.session = session
        self.token = "test token"


    async def test_01_create_user(self):
        body = UserModel(username="Andriy", email="andriy@gmail.com", password="test r 1")
        result = await create_user(body=body, db=self.session)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.password, body.password)
        self.assertTrue(hasattr(result, "id"))

    async def test_02_update_token(self):
        sq = select(User).filter_by(email=self.test_user.email)
        result = self.session.execute(sq)
        user = result.scalar_one_or_none()
        await update_token(user=user, token=self.token, db=self.session)
        self.assertEqual(user.refresh_token, self.token)

    async def test_03_get_user_by_email_found(self):
        result = await get_user_by_email(email=self.test_user.email, db=self.session)
        self.compare_user_attrs(result, self.test_user)

    async def test_04_get_user_by_email_not_found(self):
        result = await get_user_by_email(email="example@example.com", db=self.session)
        self.assertIsNone(result)

    async def test_05_confirmed_email(self):
        await confirmed_email(email=self.test_user.email, db=self.session)
        sq = select(User).filter_by(email=self.test_user.email)
        result = self.session.execute(sq)
        user = result.scalar_one_or_none()
        self.assertEqual(user.confirmed, True)

    async def test_06_update_avatar(self):
        result = await update_avatar(email=self.test_user.email, url="http:/test.com/avatar", db=self.session)
        self.assertEqual(result.avatar, "http:/test.com/avatar")


    def tearDown(self):
        self.session.close()

    @classmethod
    def tearDownClass(cls):
        engine = create_engine('sqlite:///./test.db')
        DBSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = DBSession()
        Base.metadata.drop_all(bind=session.bind)
        # тут закоментовано щоб можна було перевірити роботу тестів в базі SQLite, але для повторного запуску тестів
        # треба буде чистити таблицю в базі вручну

if __name__ == '__main__':
    unittest.main()
