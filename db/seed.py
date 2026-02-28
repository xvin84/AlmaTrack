import asyncio
import random
from datetime import datetime

from db.base import engine, get_session
from db.models import Base, User, Employment, UserProgress

# Predefined data for standard pseudo-randomization
FIRST_NAMES = ["Иван", "Алексей", "Дмитрий", "Екатерина", "Анна", "Мария", "Михаил", "Николай", "Ольга", "София"]
LAST_NAMES = ["Иванов", "Петров", "Смирнов", "Соколов", "Кузнецов", "Попов", "Лебедева", "Новикова", "Козлова", "Морозова"]
FACULTIES = ["Информационные технологии", "Экономика и бизнес", "Дизайн и медиа", "Проектный менеджмент"]
CITIES = ["Москва", "Санкт-Петербург", "Казань", "Новосибирск", "Екатеринбург", "Иннополис"]
COMPANIES = ["Яндекс", "VK", "Тинькофф", "Сбер", "Ozon", "Авито", "Mail.ru", "MTS", "Alfa-Bank", "Kaspersky"]
LEVELS = ["intern", "junior", "middle", "senior", "lead", "cto"]
FORMATS = ["office", "remote", "hybrid"]
TITLES = ["Python Developer", "Frontend Engineer", "Data Scientist", "Product Manager", "UX/UI Designer", "QA Engineer", "DevOps Engineer"]

async def seed_db(num_users=30):
    async with get_session() as session:
        for i in range(1, num_users + 1):
            telegram_id = 9000000 + i
            full_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            faculty = random.choice(FACULTIES)
            enrollment_year = random.randint(2018, 2024)
            is_alumni = enrollment_year <= 2020
            
            user = User(
                telegram_id=telegram_id,
                username=f"seed_user_{i}",
                full_name=full_name,
                faculty=faculty,
                enrollment_year=enrollment_year,
                graduation_year=enrollment_year + 4 if is_alumni else None,
                is_alumni=is_alumni,
                privacy_level=random.choice([1, 2])
            )
            session.add(user)
            await session.flush()
            
            # Create user progress
            progress = UserProgress(
                user_id=telegram_id,
                xp_points=random.randint(0, 1600),
                current_level=random.randint(1, 5),
                streak_days=random.randint(0, 30),
                total_updates=random.randint(0, 5),
            )
            session.add(progress)
            
            # Create employment data (80% chance for alumni, 40% for active students)
            chance = 0.8 if is_alumni else 0.4
            if random.random() < chance:
                emp = Employment(
                    user_id=telegram_id,
                    company_name=random.choice(COMPANIES),
                    city=random.choice(CITIES),
                    work_format=random.choice(FORMATS),
                    position_title=random.choice(TITLES),
                    position_level=random.choice(LEVELS),
                    started_at="2023-01-01",
                    is_current=True
                )
                session.add(emp)
                
        await session.commit()
    print(f"✅ Успешно сгенерировано {num_users} профилей для дашборда.")

async def main():
    # Make sure all tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    await seed_db(50)

if __name__ == "__main__":
    asyncio.run(main())
