"""
Script para criar o banco de dados e o usuário administrador inicial.
Execute: python seed.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.db.session import Base
from app.models.models import Usuario, PerfilUsuario
from app.core.security import get_password_hash


async def criar_banco():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        print("Criando tabelas...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tabelas criadas com sucesso!")

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Verificar se já existe admin
        from sqlalchemy import select
        result = await session.execute(
            select(Usuario).where(Usuario.email == "admin@bioacervo.org")
        )
        admin = result.scalar_one_or_none()

        if not admin:
            admin = Usuario(
                nome="Administrador",
                email="admin@bioacervo.org",
                senha_hash=get_password_hash("Admin@1234"),
                perfil=PerfilUsuario.administrador,
                ativo=True,
            )
            session.add(admin)
            await session.commit()
            print("✅ Usuário admin criado: admin@bioacervo.org / Admin@1234")
        else:
            print("ℹ️  Usuário admin já existe")

    await engine.dispose()
    print("\n🚀 Banco de dados pronto! Execute: uvicorn app.main:app --reload")


if __name__ == "__main__":
    asyncio.run(criar_banco())
