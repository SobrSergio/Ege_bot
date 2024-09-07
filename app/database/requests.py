from sqlalchemy import delete, select, func
from app.database.models import async_session, User, Mistake, ParonymsMistake
import ast


async def get_user_by_tg_id(tg_id: int):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))


async def set_user(tg_id: int, username: str) -> None:
    user = await get_user_by_tg_id(tg_id)
    if not user:
        async with async_session() as session:
            session.add(User(tg_id=tg_id, username=username))
            await session.commit()


async def is_admin(tg_id: int) -> bool:
    user = await get_user_by_tg_id(tg_id)
    return user.is_admin if user else False


async def get_all_users() -> list:
    async with async_session() as session:
        return (await session.scalars(select(User.tg_id))).all()


async def get_user_count() -> int:
    async with async_session() as session:
        return await session.scalar(select(func.count(User.id)))


async def get_user_mistake_count(tg_id: int, category: str) -> int:
    user = await get_user_by_tg_id(tg_id)
    if not user:
        return 0

    model = ParonymsMistake if category == "paronyms" else Mistake
    filters = [model.user_id == user.id]
    if category != "paronyms":
        filters.append(model.category == category)

    async with async_session() as session:
        return await session.scalar(select(func.count(model.id)).where(*filters))


async def get_user_mistakes(tg_id: int, category: str) -> list:
    user = await get_user_by_tg_id(tg_id)
    if not user:
        return []

    async with async_session() as session:
        model = ParonymsMistake if category == "paronyms" else Mistake
        mistakes = await session.scalars(
            select(model).where(model.user_id == user.id)
        )
        if category == "paronyms":
            return [
                {
                    'words': m.paronym_wrong,
                    'all_paronyms': ast.literal_eval(m.all_paronyms),
                    'words_dop': m.explanation
                } 
                for m in mistakes
            ]
        else:
            return [
                {
                    'words': m.correct_word,
                    'words_dop': m.wrong_word
                } 
                for m in mistakes
            ]


async def save_user_mistake(tg_id: int, category: str, wrong_word: str = None, correct_word: str = None, all_paronyms: list = None, explanation: str = None) -> None:
    user = await get_user_by_tg_id(tg_id)
    if not user:
        return

    async with async_session() as session:
        model = ParonymsMistake if category == "paronyms" else Mistake
        filter_conditions = (
            (model.user_id == user.id) &
            (model.paronym_wrong == wrong_word) &
            (model.all_paronyms == str(all_paronyms)) &
            (model.explanation == explanation)
        ) if category == "paronyms" else (
            (model.user_id == user.id) &
            (model.category == category) &
            (model.wrong_word == wrong_word) &
            (model.correct_word == correct_word)
        )
        
        existing_mistake = await session.scalar(select(model).where(filter_conditions))
        if not existing_mistake:
            new_mistake = model(
                user_id=user.id,
                paronym_wrong=wrong_word,
                all_paronyms=str(all_paronyms),
                explanation=explanation
            ) if category == "paronyms" else model(
                user_id=user.id,
                category=category,
                wrong_word=wrong_word,
                correct_word=correct_word
            )
            session.add(new_mistake)
            await session.commit()


async def remove_user_mistake(tg_id: int, category: str, word_right: str = None, paronym_wrong: str = None) -> None:
    user = await get_user_by_tg_id(tg_id)
    if not user:
        return

    async with async_session() as session:
        model = ParonymsMistake if category == "paronyms" else Mistake
        conditions = (
            (model.user_id == user.id) &
            (model.paronym_wrong == paronym_wrong)
        ) if category == "paronyms" else (
            (model.user_id == user.id) &
            (model.category == category) &
            (model.correct_word == word_right)
        )
        
        await session.execute(delete(model).where(conditions))
        await session.commit()
