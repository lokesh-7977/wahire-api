from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_uri: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_whatsapp_number: str
    gemini_api_key: str
    mail_host: str
    mail_port: int
    mail_user: str
    mail_username: str
    mail_password: str
    mail_from_email: str
    mail_from_username: str

    class Config:
        env_file = ".env"
