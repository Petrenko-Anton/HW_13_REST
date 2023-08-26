import logging

from libgravatar import Gravatar
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import User
from src.schemas import UserModel


async def get_user_by_email(email: str, db: Session) -> User:
    """
    Gets a user from the database using specified email. Emails have to be unique for each user.
    This function is used by other functions in this module and routes.auth module.

    :param email: the email of the user we want to get.
    :type email: str
    :param db: The database session.
    :type db: Session
    :return: user, or None if it does not exist.
    :rtype: User | None
    """
    sq = select(User).filter_by(email=email)
    result = db.execute(sq)
    user = result.scalar_one_or_none()
    logging.info(user)
    return user


async def create_user(body: UserModel, db: Session) -> User:
    """
    Crates a new user in the database using pydantic schema UserModel.

    :param body: pydantic schema validating username, email and password.
    :type body: UserModel
    :param db: The database session.
    :type db: Session
    :return: newly created user
    :rtype: User
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        logging.error(e)
    new_user = User(**body.model_dump(), avatar=avatar)  # User(username=username, email=email, password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: Session) -> None:
    """
    Updates a JWT token for specified user.

    :param user: User to update the token for.
    :type user: User
    :param token: JWT token to update.
    :type token: str | None
    :param db: the database session.
    :type db: Session
    """
    user.refresh_token = token
    db.commit()


async def confirmed_email(email: str, db: Session) -> None:
    """
    Mark a user's email as confirmed in the database.

    This function updates the confirmation status of a user's email in the database to indicate that the email has been
    successfully confirmed.

    :param email: email which is used to confirm a user and has to belong to him.
    :type email: str
    :param db: the database session.
    :type db: Session
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


async def update_avatar(email, url: str, db: Session) -> User:
    """
    Updates the avatar of a user using his email.

    :param email: email which is used to confirm a user and has to belong to him.
    :type email: str
    :param url: the url pointing to users avatar.
    :type url: str
    :param db: the database session.
    :type db: Session
    :rtype: User
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user


