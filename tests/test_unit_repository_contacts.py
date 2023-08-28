import unittest
import phonenumbers
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic_extra_types.phone_numbers import PhoneNumber

from src.database.models import Contact, User, Base
from src.schemas import ContactModel, ContactUpdate
from src.repository.contacts import (
    get_contacts,
    get_contact,
    create_contact,
    find_contact,
    seven_days,
    remove_contact,
    update_contact
)


class TestContacts(unittest.IsolatedAsyncioTestCase):

    def compare_contact_attrs(self,contact1, contact2):
        self.assertEqual(contact1.name, contact2.name)
        self.assertEqual(contact1.last_name, contact2.last_name)
        self.assertEqual(contact1.email, contact2.email)
        self.assertEqual(contact1.birthday, contact2.birthday)
        self.assertEqual(contact1.description, contact2.description)

        phone_number_1 = phonenumbers.parse(contact1.phone, None)
        phone_number_2 = phonenumbers.parse(contact2.phone, None)
        formatted_phone_1 = phonenumbers.format_number(phone_number_1, phonenumbers.PhoneNumberFormat.E164)
        formatted_phone_2 = phonenumbers.format_number(phone_number_2, phonenumbers.PhoneNumberFormat.E164)
        self.assertEqual(formatted_phone_1, formatted_phone_2)


    test_contact = Contact(name="John", last_name="Doe", phone=PhoneNumber("+380963835247"), email="john@gmail.com",
                           birthday=datetime.date(year=1981, month=7, day=20), description="test contact")
    test_contact_1 = Contact(name="Papa", last_name="Het", phone=PhoneNumber("+380671112233"), email="hetfield@gmail.com",
                           birthday=datetime.date(year=1962, month=5, day=12), description="test contact 1")

    def setUp(self):
        engine = create_engine('sqlite:///../test.db')
        DBSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = DBSession()
        Base.metadata.create_all(bind=engine)
        self.session = session
        self.user = User(id=1)

    async def test_create_contact(self):
        body = ContactModel(name="John", last_name="Doe", phone=PhoneNumber("+380963835247"), email="john@gmail.com",
                            birthday=datetime.date(year=1981, month=7, day=20), description="test contact")
        result = await create_contact(body=body, user=self.user, db=self.session)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.birthday, body.birthday)
        self.assertEqual(result.description, body.description)
        self.assertTrue(hasattr(result, "id"))

    async def test_create_contact_1(self):
        body = ContactModel(name="Papa", last_name="Het", phone=PhoneNumber("+380671112233"), email="hetfield@gmail.com",
                           birthday=datetime.date(year=1962, month=5, day=12), description="test contact 1")
        result = await create_contact(body=body, user=self.user, db=self.session)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.birthday, body.birthday)
        self.assertEqual(result.description, body.description)
        self.assertTrue(hasattr(result, "id"))

    async def test_get_contacts(self):
        contacts = [self.test_contact, self.test_contact_1]
        result = await get_contacts(skip=0, limit=10, user=self.user, db=self.session)
        for res, con in zip(result, contacts):
            self.compare_contact_attrs(res, con)

    async def test_birthdays_week(self):
        today = datetime.date.today()
        cur_year = today.year
        week_after = today + datetime.timedelta(days=7)
        contacts = [self.test_contact, self.test_contact_1]
        bday_boys = []
        for contact in contacts:
            if today < contact.birthday.replace(year=cur_year) <= week_after:
                bday_boys.append(contact)
        result = await seven_days(user=self.user, db=self.session)
        for res, con in zip(result, bday_boys):
            self.compare_contact_attrs(res, con)

    async def test_get_contact_found(self):
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.compare_contact_attrs(result, self.test_contact)

    async def test_get_contact_not_found(self):
        result = await get_contact(contact_id=10, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_find_contact_found(self):
        search_string_1 = "John"
        search_string_2 = "Doe"
        search_string_3 = "john@gmail.com"
        result = await find_contact(search_string=search_string_1, user=self.user, db=self.session)
        self.compare_contact_attrs(result, self.test_contact)
        result = await find_contact(search_string=search_string_2, user=self.user, db=self.session)
        self.compare_contact_attrs(result, self.test_contact)
        result = await find_contact(search_string=search_string_3, user=self.user, db=self.session)
        self.compare_contact_attrs(result, self.test_contact)

    async def test_find_contact_not_found(self):
        search_string_1 = "Anton"
        search_string_2 = "Petrenko"
        search_string_3 = "test115@mail.ua"
        result = await find_contact(search_string=search_string_1,user=self.user, db=self.session)
        self.assertIsNone(result)
        result = await find_contact(search_string=search_string_2,user=self.user, db=self.session)
        self.assertIsNone(result)
        result = await find_contact(search_string=search_string_3,user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_update_contact_found(self):
        body = ContactUpdate(name="Igor", description="test update contact")
        contact = Contact(name="Igor", description="test update contact")
        result = await update_contact(contact_id=1, body=body, user=self.user, db=self.session)
        self.assertEqual(result.name, contact.name)
        self.assertEqual(result.description, contact.description)

    async def test_update_contact_not_found(self):
        body = ContactUpdate(name="Igor", description="test no contact to update")
        result = await update_contact(contact_id=10, body=body, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_remove_contact_found(self):
        result = await remove_contact(contact_id=2, user=self.user, db=self.session)
        self.compare_contact_attrs(result, self.test_contact_1)

    async def test_remove_contact_not_found(self):
        result = await remove_contact(contact_id=10, user=self.user, db=self.session)
        self.assertIsNone(result)

    def tearDown(self):
        self.session.close()

    @classmethod
    def tearDownClass(cls):
        engine = create_engine('sqlite:///../test.db')
        DBSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = DBSession()
        Base.metadata.drop_all(bind=session.bind)
        # тут закоментовано щоб можна було перевірити роботу тестів в базі SQLite, але для повторного запуску тестів
        # треба буде чистити таблицю в базі вручну

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(TestContacts('test_create_contact'))
    suite.addTest(TestContacts('test_create_contact_1'))
    suite.addTest(TestContacts('test_get_contacts'))
    suite.addTest(TestContacts('test_birthdays_week'))
    suite.addTest(TestContacts('test_get_contact_found'))
    suite.addTest(TestContacts('test_get_contact_not_found'))
    suite.addTest(TestContacts('test_find_contact_found'))
    suite.addTest(TestContacts('test_find_contact_not_found'))
    suite.addTest(TestContacts('test_update_contact_found'))
    suite.addTest(TestContacts('test_update_contact_not_found'))
    suite.addTest(TestContacts('test_remove_contact_found'))
    suite.addTest(TestContacts('test_remove_contact_not_found'))
    unittest.TextTestRunner().run(suite)
