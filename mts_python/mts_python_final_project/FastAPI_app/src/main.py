from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from src.configurations.database import create_db_and_tables, global_init
from src.routers import v1_router
from src.routers.v1 import books, seller
from icecream import ic

@asynccontextmanager
async def lifespan(app: FastAPI):
    ic("I am here!")
    global_init()
    await create_db_and_tables()
    yield

app = FastAPI(
    title="Book Library App",
    description="Учебное приложение для MTS Shad",
    version="0.0.1",
    default_response_class=ORJSONResponse,
    responses={404: {"description": "Not found!"}},
    lifespan=lifespan,
)

app.include_router(books.books_router)
app.include_router(seller.seller_router)
app.include_router(v1_router)

