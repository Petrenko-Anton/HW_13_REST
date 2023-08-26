from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User
from src.schemas import ContactModel, ContactResponse, ContactUpdate
from src.repository import contacts as repo_contacts
from src.services.auth import auth_service

router = APIRouter(prefix='/contacts', tags=["contacts"])


@router.get("/", response_model=List[ContactResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_contacts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieve a list of contacts for a specific user with specified pagination parameters.

    :param skip: Number of contacts to skip.
    :type skip: int
    :param limit: Maximum number of contacts to retrieve.
    :type limit: int
    :param db: SQLAlchemy database session obtained from the `get_db` dependency.
    :type db: Session
    :param current_user: User instance representing the authenticated user.
    :type current_user: User
    :return: List of contacts.
    :rtype: List[ContactResponse]
    """
    contacts = await repo_contacts.get_contacts(skip, limit, current_user, db)
    return contacts


@router.get("/birthdays", response_model=List[ContactResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def congrat_contacts(current_user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):
    """
    Retrieve a list of contacts of current user with upcoming birthdays.

    :param current_user: User instance representing the authenticated user.
    :type current_user: User
    :param db: SQLAlchemy database session obtained from the `get_db` dependency.
    :type db: Session
    :return: List of contacts with upcoming birthdays.
    :rtype: List[ContactResponse]
    """
    contacts = await repo_contacts.seven_days(current_user, db)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_contact(contact_id: int,
                       current_user: User = Depends(auth_service.get_current_user),
                       db: Session = Depends(get_db)):
    """
    Retrieve a single contact of current user by its ID.

    :param contact_id: ID of the contact to retrieve.
    :type contact_id: int
    :param current_user: User instance representing the authenticated user.
    :type current_user: User
    :param db: SQLAlchemy database session obtained from the `get_db` dependency.
    :type db: Session
    :return: Contact information.
    :rtype: ContactResponse
    """
    contact = await repo_contacts.get_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.get("/find/{search_string}", response_model=ContactResponse, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def find_contact_by_name_last_name_or_email(search_string: str,
                                                  current_user: User = Depends(auth_service.get_current_user),
                                                  db: Session = Depends(get_db)):
    """
    Find a contact (from current user contact list) by name, last name, or email.

    :param search_string: String to search for in the contact's name, last name, or email.
    :type search_string: str
    :param current_user: User instance representing the authenticated user.
    :type current_user: User
    :param db: SQLAlchemy database session obtained from the `get_db` dependency.
    :type db: Session
    :return: Contact information matching the search string.
    :rtype: ContactResponse
    """
    contact = await repo_contacts.find_contact(search_string, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post("/", response_model=ContactResponse, description='No more than 10 requests per minute',
             dependencies=[Depends(RateLimiter(times=10, seconds=60))], status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactModel,
                         current_user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    """
    Create a new contact in current user's contact list.

    :param body: Contact information to be created.
    :type body: ContactModel
    :param current_user: User instance representing the authenticated user.
    :type current_user: User
    :param db: SQLAlchemy database session obtained from the `get_db` dependency.
    :type db: Session
    :return: Created contact information.
    :rtype: ContactResponse
    """
    return await repo_contacts.create_contact(body, current_user, db)


@router.put("/{contact_id}", response_model=ContactResponse, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def update_contact(body: ContactUpdate, contact_id: int,
                         current_user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    """
      Update an existing contact in current user's contact list..

      :param body: Contact information to be updated.
      :type body: ContactUpdate
      :param contact_id: ID of the contact to be updated.
      :type contact_id: int
      :param current_user: User instance representing the authenticated user.
      :type current_user: User
      :param db: SQLAlchemy database session obtained from the `get_db` dependency.
      :type db: Session
      :return: Updated contact information.
      :rtype: ContactResponse
      """
    contact = await repo_contacts.update_contact(contact_id, body, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", response_model=ContactResponse, description='No more than 10 requests per minute',
               dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def remove_contact(contact_id: int,
                         current_user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    """
    Remove a contact from current user's contact list.

    :param contact_id: ID of the contact to be removed.
    :type contact_id: int
    :param current_user: User instance representing the authenticated user.
    :type current_user: User
    :param db: SQLAlchemy database session obtained from the `get_db` dependency.
    :type db: Session
    :return: Removed contact information.
    :rtype: ContactResponse
    """
    contact = await repo_contacts.remove_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact
