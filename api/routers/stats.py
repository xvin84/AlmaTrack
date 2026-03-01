from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.base import get_session
from db.models import User, Employment

router = APIRouter()

async def get_db_session():
    async with get_session() as session:
        yield session

@router.get("/summary")
async def get_stats_summary(session: AsyncSession = Depends(get_db_session)):
    users_count = await session.scalar(select(func.count()).select_from(User).where(User.privacy_level < 2, User.status == "approved"))
    companies_count = await session.scalar(
        select(func.count(Employment.company_name.distinct()))
        .join(User, User.telegram_id == Employment.user_id)
        .where(User.privacy_level < 2, User.status == "approved")
    )
    cities_count = await session.scalar(
        select(func.count(Employment.city.distinct()))
        .join(User, User.telegram_id == Employment.user_id)
        .where(User.privacy_level < 2, User.status == "approved")
    )
    
    employers_result = await session.execute(
        select(Employment.company_name, func.count())
        .join(User, User.telegram_id == Employment.user_id)
        .where((User.privacy_level < 2) & (Employment.company_name != None) & (User.status == "approved"))
        .group_by(Employment.company_name)
        .order_by(func.count().desc()).limit(10)
    )
    employers = []
    employers_count = []
    for row in employers_result:
        employers.append(row[0])
        employers_count.append(row[1])

    levels_result = await session.execute(
        select(Employment.position_level, func.count())
        .join(User, User.telegram_id == Employment.user_id)
        .where((User.privacy_level < 2) & (Employment.position_level != None) & (User.status == "approved"))
        .group_by(Employment.position_level)
    )
    levels = []
    levels_count = []
    for row in levels_result:
        levels.append(row[0])
        levels_count.append(row[1])

    cities_result = await session.execute(
        select(Employment.city, func.count())
        .join(User, User.telegram_id == Employment.user_id)
        .where((User.privacy_level < 2) & (Employment.city != None) & (User.status == "approved"))
        .group_by(Employment.city)
        .order_by(func.count().desc()).limit(7)
    )
    cities = []
    city_counts = []
    for row in cities_result:
        cities.append(row[0])
        city_counts.append(row[1])

    faculties_result = await session.execute(
        select(User.faculty, func.count())
        .where((User.privacy_level < 2) & (User.faculty != None) & (User.status == "approved"))
        .group_by(User.faculty)
        .order_by(func.count().desc()).limit(10)
    )
    faculties = []
    faculty_counts = []
    for row in faculties_result:
        faculties.append(row[0])
        faculty_counts.append(row[1])
        
    years_result = await session.execute(
        select(User.graduation_year, func.count())
        .where((User.privacy_level < 2) & (User.graduation_year != None) & (User.status == "approved"))
        .group_by(User.graduation_year)
        .order_by(User.graduation_year.asc())
    )
    years = []
    year_counts = []
    for row in years_result:
        years.append(str(row[0]))
        year_counts.append(row[1])

    return {
        "summary": {
            "total_users": users_count or 0,
            "total_companies": companies_count or 0,
            "total_cities": cities_count or 0,
        },
        "charts": {
            "employers": {"labels": employers, "data": employers_count},
            "levels": {"labels": levels, "data": levels_count},
            "cities": {"labels": cities, "data": city_counts},
            "faculties": {"labels": faculties, "data": faculty_counts},
            "years": {"labels": years, "data": year_counts}
        }
    }
