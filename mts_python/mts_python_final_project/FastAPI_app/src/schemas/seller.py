from pydantic import BaseModel, EmailStr
from typing import List, Optional
from .books import ReturnedBook 

# Схема для входящих данных при регистрации продавца
class IncomingSeller(BaseModel):
    first_name: str
    last_name: str
    e_mail: EmailStr
    password: str

# Схема для возврата данных о продавце без пароля
class ReturnedSeller(BaseModel):
    id: int
    first_name: str
    last_name: str
    e_mail: EmailStr

    class Config:
        orm_mode = True

# Схема для детального отображения продавца с его книгами
class DetailedSeller(ReturnedSeller):
    books: List[ReturnedBook] = []

class SellerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    e_mail: Optional[EmailStr] = None
