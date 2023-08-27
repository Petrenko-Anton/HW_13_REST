from typing import List
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from src.database.models import Contact, User
from src.schemas import ContactModel, ContactUpdate


async def seven_days(user: User, db: Session) -> List[Contact]:
    """
    Retrieves all contacts who have birthday during next 7 days for  a specific user.

    :param user: The user to retrieve contacts for.
    :type user: User
    :type db: Session
    :return: A list of contacts.
    :rtype: List[contact]
    """
    today = date.today()
    cur_year = today.year
    week_after = today + timedelta(days=7)
    contacts = db.query(Contact).filter(Contact.user_id == user.id).all()
    result = []
    for contact in contacts:
        if today < contact.birthday.replace(year=cur_year) <= week_after:
            result.append(contact)
    return result


async def get_contacts(skip: int, limit: int, user: User, db: Session) -> List[Contact]:
    """
    Retrieves a list of contacts for a specific user with specified pagination parameters.

    :param skip: The number of contacts to skip.
    :type skip: int
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param user: The user to retrieve contacts for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: A list of contacts.
    :rtype: List[contact]
    """
    return db.query(Contact).filter(Contact.user_id == user.id).offset(skip).limit(limit).all()


async def get_contact(contact_id: int, user: User, db: Session) -> Contact:
    """
    Retrieves a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the note to retrieve.
    :type contact_id: int
    :param user: The user to retrieve the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The contact with the specified ID, or None if it does not exist.
    :rtype: Contact | None
    """
    return db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()


async def find_contact(search_string: str, user: User, db: Session) -> Contact:
    """
    Finds a contact by specified search string, searching in contacts name, last name or email.
    Search string can be in the beginning, inside, or end of the search fields, or can fully match.

    :param search_string: the string used to search in the contact fields.
    :type search_string: str
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The contact whose name, last name or email contains the search string, or None if it does not exist.
    :rtype: Contact | None
    """
    return db.query(Contact).filter(and_(Contact.user_id == user.id,
                                         or_(Contact.name.startswith(search_string),
                                             Contact.name.endswith(search_string),
                                             Contact.name == search_string,
                                             Contact.email.startswith(search_string),
                                             Contact.email.endswith(search_string),
                                             Contact.email == search_string,
                                             Contact.last_name.startswith(search_string),
                                             Contact.last_name.endswith(search_string),
                                             Contact.last_name == search_string))).one_or_none()


async def create_contact(body: ContactModel, user: User, db: Session) -> Contact:

    """
    The create_contact function creates a new contact in the database.

    :param body: Get the data from the request body
    :type body: ContactModel
    :param user: The user to create the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: A contact object
    :rtype: Contact
    """
    contact = Contact(name=body.name, last_name=body.last_name, phone=body.phone, email=body.email,
                      birthday=body.birthday, description=body.description, user_id=user.id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


async def remove_contact(contact_id: int, user: User, db: Session) -> Contact | None:
    """
    Removes a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to remove.
    :type contact_id: int
    :param user: The user to remove the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The removed contact, or None if it does not exist.
    :rtype: Contact | None
    """
    contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()
    if contact:
        db.delete(contact)
        db.commit()
    return contact


async def update_contact(contact_id: int, body: ContactUpdate, user: User, db: Session) -> Contact | None:
    """
    Updates a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param body: The updated data for the contact.
    :type body: contactUpdate
    :param user: The user to update the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The updated contact, or None if it does not exist.
    :rtype: Contact | None
    """
    contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()
    if contact:
        update_data = {k: v for k, v in body.model_dump().items() if v is not None}
        db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).update(update_data)
        db.commit()
        db.refresh(contact)
    return contact
