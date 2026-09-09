from pydantic import BaseModel


class ExchangeCodeRequest(BaseModel):
    code: str
    waba_id: str
    phone_number_id: str


class RegisterPhoneRequest(BaseModel):
    phone_number_id: str
    access_token: str
    pin: str = "000000"  # TODO: generate/collect per customer in production


class SubscribeWabaRequest(BaseModel):
    waba_id: str
    access_token: str

class SendMessageRequest(BaseModel):
    to: str
    message: str
