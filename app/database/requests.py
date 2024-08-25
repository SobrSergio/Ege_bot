from app.database.models import async_session
from app.database.models import User
from sqlalchemy import select, func


async def set_user(tg_id: int, username: str) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id, username=username))
            await session.commit()
            return 1
        return 0

async def is_admin(tg_id: int) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user.is_admin if user else False
    

async def get_all_users() -> list:
    async with async_session() as session:
        result = await session.scalars(select(User.tg_id))
        return result.all()

async def get_user_count() -> int:
    async with async_session() as session:
        count = await session.scalar(select(func.count(User.id)))
        return count
    
async def save_user_mistake(tg_id: int, category: str, word_wrong: str, word_right: str) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user:
            if category == 'accents':
                mistakes = user.accents_repet
            elif category == 'dictionary':
                mistakes = user.dictionary_repet
            elif category == 'norms':
                mistakes = user.norms_repet
            else:
                return 

            new_mistake = f'{word_wrong}_{word_right}'
            if new_mistake not in mistakes.split('\n'):
                if category == 'accents':
                    user.accents_repet += (f'{new_mistake}\n')
                elif category == 'dictionary':
                    user.dictionary_repet += (f'{new_mistake}\n')
                elif category == 'norms':
                    user.norms_repet += (f'{new_mistake}\n')

                await session.commit()
                
async def get_user_mistakes(tg_id: int, category: str) -> list:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            return []

        mistakes = []
        if category == 'accents':
            mistakes = user.accents_repet.strip().split('\n')
        elif category == 'dictionary':
            mistakes = user.dictionary_repet.strip().split('\n')
        elif category == 'norms':
            mistakes = user.norms_repet.strip().split('\n')

        return [{'correct_word': item.split('_')[0], 'wrong_word': item.split('_')[1]} for item in mistakes if '_' in item]
    
async def get_user_mistake_count(tg_id: int, category: str) -> int:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            return 0

        mistakes = []
        if category == 'accents':
            mistakes = user.accents_repet.strip().split('\n')
        elif category == 'dictionary':
            mistakes = user.dictionary_repet.strip().split('\n')
        elif category == 'norms':
            mistakes = user.norms_repet.strip().split('\n')

        # Возвращаем количество ошибок (фильтруем пустые строки)
        return len([item for item in mistakes if item])

async def remove_user_mistake(tg_id: int, category: str, word_right: str) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user:
            if category == 'accents':
                mistakes = user.accents_repet.split('\n')
            elif category == 'dictionary':
                mistakes = user.dictionary_repet.split('\n')
            elif category == 'norms':
                mistakes = user.norms_repet.split('\n')
            else:
                return

            # Удаляем ошибку из списка
            mistakes = [mistake for mistake in mistakes if mistake and mistake.split('_')[0] != word_right]

            # Обновляем поле с ошибками
            if category == 'accents':
                user.accents_repet = '\n'.join(mistakes) + '\n'
            elif category == 'dictionary':
                user.dictionary_repet = '\n'.join(mistakes) + '\n'
            elif category == 'norms':
                user.norms_repet = '\n'.join(mistakes) + '\n'

            await session.commit()

