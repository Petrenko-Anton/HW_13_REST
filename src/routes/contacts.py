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
    contacts = await repo_contacts.get_contacts(skip, limit, current_user, db)
    return contacts


@router.get("/birthdays", response_model=List[ContactResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def congrat_contacts(current_user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):
    contacts = await repo_contacts.seven_days(current_user, db)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_contact(contact_id: int,
                       current_user: User = Depends(auth_service.get_current_user),
                       db: Session = Depends(get_db)):
    contact = await repo_contacts.get_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.get("/find/{search_string}", response_model=ContactResponse, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def find_contact_by_name_last_name_or_email(search_string: str,
                                                  current_user: User = Depends(auth_service.get_current_user),
                                                  db: Session = Depends(get_db)):
    contact = await repo_contacts.find_contact(search_string, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post("/", response_model=ContactResponse, description='No more than 10 requests per minute',
             dependencies=[Depends(RateLimiter(times=10, seconds=60))], status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactModel,
                         current_user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    return await repo_contacts.create_contact(body, current_user, db)


@router.put("/{contact_id}", response_model=ContactResponse, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def update_contact(body: ContactUpdate, contact_id: int,
                         current_user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    contact = await repo_contacts.update_contact(contact_id, body, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", response_model=ContactResponse, description='No more than 10 requests per minute',
               dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def remove_contact(contact_id: int,
                         current_user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    contact = await repo_contacts.remove_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact
