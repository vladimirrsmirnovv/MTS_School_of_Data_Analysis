from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Book(BaseModel):
    __tablename__ = "books_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int]
    pages: Mapped[int]

    seller_id: Mapped[int] = mapped_column(ForeignKey("sellers_table.id"), nullable=True)

    seller = relationship("Seller", back_populates="books", lazy="joined")