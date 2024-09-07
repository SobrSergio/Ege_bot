from sqlalchemy import BigInteger, String, ForeignKey, Boolean, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
import os
from dotenv import load_dotenv


load_dotenv(override=True)
engine = create_async_engine(url=os.getenv('SQLALCHEMY_URL'))
async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    
    mistakes = relationship('Mistake', back_populates='user', cascade='all, delete-orphan')
    paronym_mistakes = relationship('ParonymsMistake', back_populates='user', cascade='all, delete-orphan') 

class Mistake(Base):
    __tablename__ = 'mistakes'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    category: Mapped[str] = mapped_column(String(50))
    wrong_word: Mapped[str] = mapped_column(String(255))
    correct_word: Mapped[str] = mapped_column(String(255))
    
    user = relationship('User', back_populates='mistakes')
    
class ParonymsMistake(Base):
    __tablename__ = 'paronyms_mistakes'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    paronym_wrong: Mapped[str] = mapped_column(String(255)) 
    all_paronyms: Mapped[str] = mapped_column(String(255))
    explanation: Mapped[str] = mapped_column(Text) 

    user = relationship('User', back_populates='paronym_mistakes') 

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
