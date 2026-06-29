"""Seed seguro para usuário administrador inicial."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config.config import settings
from app.db.session import Base
from app.models.models import Usuario, PerfilUsuario
from app.config.security import get_password_hash


async def criar_banco():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        print("Criando/verificando tabelas do banco...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tabelas prontas!")

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        admin_email = settings.ADMIN_EMAIL
        admin_password = settings.ADMIN_PASSWORD
        if not admin_email or not admin_password:
            if settings.is_production:
                print("⚠️  ADMIN_EMAIL/ADMIN_PASSWORD ausentes; admin inicial não será criado.")
                await engine.dispose()
                return
            admin_email = admin_email or "admin@example.com"
            admin_password = admin_password or "AdminDev123"
            print("⚠️  Usando admin apenas para desenvolvimento. Defina ADMIN_EMAIL e ADMIN_PASSWORD.")

        from sqlalchemy import select
        result = await session.execute(
            select(Usuario).where(Usuario.email == admin_email)
        )
        admin = result.scalar_one_or_none()

        if not admin:
            admin = Usuario(
                nome="Administrador",
                email=admin_email,
                senha_hash=get_password_hash(admin_password),
                perfil=PerfilUsuario.administrador,
                ativo=True,
            )
            session.add(admin)
            await session.commit()
            print(f"✅ Usuário admin criado: {admin_email}")
        else:
            print("ℹ️  Usuário admin já existe")

    await engine.dispose()
    print("\n🚀 Banco de dados pronto! Execute: uvicorn main:app --reload")


if __name__ == "__main__":
    asyncio.run(criar_banco())
