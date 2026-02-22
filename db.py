import os

from datetime import datetime, timezone

from dotenv import load_dotenv

from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

load_dotenv()


DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{os.environ.get('POSTGRES_USER')}:"
    f"{os.environ.get('POSTGRES_PASSWORD')}@"
    f"{os.environ.get('POSTGRES_HOST')}:"
    f"{os.environ.get('POSTGRES_PORT', 5432)}/"
    f"{os.environ.get('POSTGRES_DB', 'autos')}"
)

# ---- ENGINE ----
engine = create_async_engine(
    DATABASE_URL,
    echo=False,          # Set True for SQL debug
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ---- CAR MODEL ----
class Car(Base):
    __tablename__ = "cars"

    url: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str | None] = mapped_column(String)
    price_usd: Mapped[int | None] = mapped_column(Integer)
    odometer: Mapped[int | None] = mapped_column(Integer)
    username: Mapped[str | None] = mapped_column(String)
    phone_number: Mapped[str | None] = mapped_column(String)
    image_url: Mapped[str | None] = mapped_column(String)
    images_count: Mapped[int | None] = mapped_column(Integer)
    car_number: Mapped[str | None] = mapped_column(String)
    car_vin: Mapped[str | None] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ---- INSERT WITH ON CONFLICT DO NOTHING ----
async def insert_car(car_data: dict):
    async with AsyncSessionLocal() as session:
        stmt = insert(Car).values(**car_data)
        stmt = stmt.on_conflict_do_nothing(index_elements=["url"])
        await session.execute(stmt)
        await session.commit()
