from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Security,  BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import UserModel, UserResponse, TokenModel, RequestEmail
from src.repository import users as repo_users
from src.services.auth import auth_service
from src.services.email import send_email


router = APIRouter(prefix='/auth', tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    Router to signup a new user and create him in database, sending him confirmation email in the background.

    :param body: pydantic schema validating username, email and password.
    :type body: UserModel
    :param background_tasks: the instance of of fastapi class 'BackgroundTasks' which is used to start confirmation
    email sending in the background
    :type background_tasks: BackgroundTasks
    :param request: An instance of the fastapi class `Request`, representing the incoming HTTP request. It contains
    information about the current request, including the URL
    :type request: Request
    :param db: SQLAlchemy database session obtained from the `get_db` dependency.
    :type db: Session
    :return: Returns a dictionary (JSON object) containing information about the new user and a success message.
    :rtype: dict
    """
    exist_user = await repo_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repo_users.create_user(body, db)
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    return {"user": new_user, "detail": "User successfully created"}


@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Log in a user and generate access and refresh tokens.

    :param body: OAuth2 password request form containing the username (email) and password.
    :type body: OAuth2PasswordRequestForm
    :param db: SQLAlchemy database session obtained from the `get_db` dependency.
    :type db: Session
    :return: Returns a dictionary (JSON object) containing the access token, refresh token, and token type.
    :rtype: dict
    """
    user = await repo_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repo_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """
    Refresh the access token using the provided refresh token.

    :param credentials: HTTP Authorization credentials containing the refresh token.
    :type credentials: HTTPAuthorizationCredentials
    :param db: SQLAlchemy database session obtained from the `get_db` dependency.
    :type db: Session
    :return: Returns a dictionary (JSON object) containing the new access token, refresh token, and token type.
    :rtype: dict
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repo_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repo_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repo_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Confirm a user's email using the provided token.

    :param token: Token sent to the user's email for confirmation.
    :type token: str
    :param db: SQLAlchemy database session obtained from the `get_db` dependency.
    :type db: Session
    :return: Returns a message (JSON object) indicating the result of email confirmation.
    :rtype: dict
    """
    email = await auth_service.get_email_from_token(token)
    user = await repo_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repo_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """
    Send a confirmation email to the user.

    :param body: Request body containing the user's email.
    :type body: RequestEmail
    :param background_tasks: Object of the fastapi class BackgroundTasks used to start email sending in the background.
    :type background_tasks: BackgroundTasks
    :param request: An instance of the fastapi class `Request` representing the incoming HTTP request.
    :type request: Request
    :param db: SQLAlchemy database session obtained from the `get_db` dependency.
    :type db: Session
    :return: Returns a message (JSON object) indicating the result of email sending.
    :rtype: dict
    """
    user = await repo_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": "Check your email for confirmation."}
