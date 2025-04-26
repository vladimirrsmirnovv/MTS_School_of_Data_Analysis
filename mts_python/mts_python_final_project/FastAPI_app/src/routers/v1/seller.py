from fastapi import APIRouter, Depends, Response, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Annotated

from src.configurations import get_async_session
from src.models.seller import Seller
from src.schemas.seller import IncomingSeller, ReturnedSeller, DetailedSeller, SellerUpdate

seller_router = APIRouter(tags=["seller"], prefix="/api/v1/seller")
DBSession = Annotated[AsyncSession, Depends(get_async_session)]

# 1) регистрация продавца
@seller_router.post("/", response_model=ReturnedSeller, status_code=status.HTTP_201_CREATED)
async def create_seller(seller: IncomingSeller, session: DBSession):
    new_seller = Seller(**seller.model_dump())
    session.add(new_seller)
    await session.commit()
    await session.refresh(new_seller)
    return new_seller

# 2) получение списка всех продавцов (без password)
@seller_router.get("/", response_model=list[ReturnedSeller])
async def get_all_sellers(session: DBSession):
    query = select(Seller)
    result = await session.execute(query)
    return result.scalars().all()

# 3) данные о конкретном продавце с книгами
@seller_router.get("/{seller_id}", response_model=DetailedSeller)
async def get_seller(seller_id: int, session: DBSession):
    query = select(Seller).options(selectinload(Seller.books)).where(Seller.id == seller_id)
    result = await session.execute(query)
    seller = result.scalars().first()

    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    return seller

# 4) обновление данных о продавце (без пароля и книг)
@seller_router.put("/{seller_id}", response_model=ReturnedSeller)
async def update_seller(seller_id: int, new_data: SellerUpdate, session: DBSession):
    seller = await session.get(Seller, seller_id)
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    for key, value in new_data.model_dump(exclude_unset=True).items():
        setattr(seller, key, value)

    await session.commit()
    await session.refresh(seller)
    return seller

# 5) удаление продавца вместе с его книгами (cascade)
@seller_router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seller(seller_id: int, session: DBSession):
    seller = await session.get(Seller, seller_id)
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    await session.delete(seller)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
