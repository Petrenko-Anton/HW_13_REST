from datetime import datetime, timedelta
from typing import Optional

import pickle
import redis
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.conf.config import settings
from src.database.db import get_db
from src.repository import users as repo_users


class Auth:
    """
    Authentication service providing methods for password hashing, token creation, and user verification.

    Attributes:
    pwd_context (CryptContext): Password hashing context.
    SECRET_KEY (str): Secret key for token encoding.
    ALGORITHM (str): Token encoding algorithm.
    oauth2_scheme (OAuth2PasswordBearer): OAuth2 password bearer scheme.
    r (redis.Redis): Redis client for caching user data.
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    r = redis.Redis(host='localhost', port=6379, db=0)

    def verify_password(self, plain_password, hashed_password):
        """
        Verifies the provided plain password against a hashed password.

        :param plain_password: Plain password.
        :type plain_password: str
        :param hashed_password: Hashed password.
        :type hashed_password: str
        :return: True if the passwords match, False otherwise.
        :rtype: bool
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Generates a hash for the provided password.

        :param password: Password to hash.
        :type password: str
        :return: Hashed password.
        :rtype: str
        """
        return self.pwd_context.hash(password)

    def create_email_token(self, data: dict):
        """
        Creates an email confirmation token.

        :param data: Data to include in the token payload.
        :type data: dict
        :return: Email confirmation token.
        :rtype: str
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    # define a function to generate a new access token
    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Create an access token for the provided data.

        :param data: Data to include in the token payload.
        :type data: dict
        :param expires_delta: Optional expiration time for the token in seconds.
        :type expires_delta: float
        :return: Access token.
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    # define a function to generate a new refresh token
    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Create a refresh token for the provided data.

        :param data: Data to include in the token payload.
        :type data: dict
        :param expires_delta: Optional expiration time for the token in seconds.
        :type expires_delta: float
        :return: Refresh token.
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
        Decode a refresh token and extract the email from it.

        :param refresh_token: Refresh token.
        :type refresh_token: str
        :return: Extracted email.
        :rtype: str
        :raises HTTPException: If the token is invalid or has an invalid scope.
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """
        Get the current user based on the provided access token.

        :param token: Access token.
        :type token: str
        :param db: SQLAlchemy database session obtained from the `get_db` dependency.
        :type db: Session
        :return: Current user.
        :rtype: User
        :raises HTTPException: If the token is invalid, has an invalid scope, or the user cannot be retrieved.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user = await repo_users.get_user_by_email(email, db)
        if user is None:
            raise credentials_exception
        user = self.r.get(f"user:{email}")
        if user is None:
            user = await repo_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            self.r.set(f"user:{email}", pickle.dumps(user))
            self.r.expire(f"user:{email}", 900)
        else:
            user = pickle.loads(user)
        return user

    async def get_email_from_token(self, token: str):
        """
        Decode a token and extract the email from it.

        :param token: Token containing the email.
        :type token: str
        :return: Extracted email.
        :rtype: str
        :raises HTTPException: If the token is invalid or the email is not found.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")


auth_service = Auth()
