from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    sqlalchemy_database_url: str = "postgresql://postgres:111111@localhost:5432/postgress"
    secret_key: str = "some_secret_key"
    algorithm: str = "algo1"
    mail_username: str = "sponge"
    mail_password: str = "bob"
    mail_from: str = "example@example.com"
    mail_from_name: str = "sender"
    mail_port: int = 456
    mail_server: str = "smtp.gmail.com"
    redis_host: str = "localhost"
    redis_port: int = 6379
    cloudinary_name: str = "super"
    cloudinary_api_key: str = "mega"
    cloudinary_api_secret: str = "lol"

    class Config:
        env_file = "./.env"
        env_file_encoding = "utf-8"
        extra = 'ignore'

settings = Settings()

