# schemas.py
from pydantic import BaseModel

class CreateCheckoutSessionRequest(BaseModel):
    user_id: int
    credits: int
    amount: int