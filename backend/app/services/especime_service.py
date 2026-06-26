import uuid
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.models import Especime, Taxonomia, LocalidadeGeografica
from app.schemas.schemas import EspecimeCreate, EspecimeUpdate, BuscaEspecime


class EspecimeService:

    @staticmethod
    async def get_by_id(db: AsyncSession, especime_id: int) -> Optional[Especime]:
        result = await db.execute(
            select(Especime)
            .options(
                selectinload(Especime.taxonomia),
                selectinload(Especime.localidade),
                selectinload(Especime.imagens),
            )
            .where(Especime.id == especime_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_codigo(db: AsyncSession, codigo: str) -> Optional[Especime]:
        result = await db.execute(
            select(Especime)
            .options(
                selectinload(Especime.taxonomia),
                selectinload(Especime.localidade),
                selectinload(Especime.imagens),
            )
            .where(Especime.codigo_catalogo == codigo)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        data: EspecimeCreate,
        usuario_id: int,
    ) -> Especime:
        # Gerar código de barras e DwC record ID únicos
        dwc_id = f"urn:uuid:{uuid.uuid4()}"
        codigo_barras = f"SPEC-{uuid.uuid4().hex[:12].upper()}"

        especime = Especime(
            **data.model_dump(),
            codigo_barras=codigo_barras,
            dwc_record_id=dwc_id,
            cadastrado_por_id=usuario_id,
            data_entrada_colecao=datetime.utcnow(),
        )
        db.add(especime)
        await db.flush()
        await db.refresh(especime)

        # Recarregar com relacionamentos
        return await EspecimeService.get_by_id(db, especime.id)

    @staticmethod
    async def update(
        db: AsyncSession,
        especime: Especime,
        data: EspecimeUpdate,
    ) -> Especime:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(especime, field, value)
        especime.atualizado_em = datetime.utcnow()
        await db.flush()
        return await EspecimeService.get_by_id(db, especime.id)

    @staticmethod
    async def delete(db: AsyncSession, especime: Especime) -> None:
        await db.delete(especime)
        await db.flush()

    @staticmethod
    async def buscar(
        db: AsyncSession,
        filtros: BuscaEspecime,
    ) -> Tuple[int, List[Especime]]:
        conditions = []

        # Joins necessários
        query = (
            select(Especime)
            .join(Especime.taxonomia)
            .outerjoin(Especime.localidade)
            .options(
                selectinload(Especime.taxonomia),
                selectinload(Especime.localidade),
                selectinload(Especime.imagens),
            )
        )

        # Filtros taxonômicos
        if filtros.nome_cientifico:
            conditions.append(
                Taxonomia.nome_cientifico.ilike(f"%{filtros.nome_cientifico}%")
            )
        if filtros.familia:
            conditions.append(Taxonomia.familia.ilike(f"%{filtros.familia}%"))
        if filtros.genero:
            conditions.append(Taxonomia.genero.ilike(f"%{filtros.genero}%"))

        # Filtros geográficos
        if filtros.estado:
            conditions.append(
                LocalidadeGeografica.estado.ilike(f"%{filtros.estado}%")
            )
        if filtros.municipio:
            conditions.append(
                LocalidadeGeografica.municipio.ilike(f"%{filtros.municipio}%")
            )
        if filtros.bioma:
            conditions.append(
                LocalidadeGeografica.bioma.ilike(f"%{filtros.bioma}%")
            )

        # Filtros de caixa geográfica (bounding box)
        if filtros.lat_min is not None:
            conditions.append(LocalidadeGeografica.latitude >= filtros.lat_min)
        if filtros.lat_max is not None:
            conditions.append(LocalidadeGeografica.latitude <= filtros.lat_max)
        if filtros.lon_min is not None:
            conditions.append(LocalidadeGeografica.longitude >= filtros.lon_min)
        if filtros.lon_max is not None:
            conditions.append(LocalidadeGeografica.longitude <= filtros.lon_max)

        # Filtro por coletor
        if filtros.coletor:
            conditions.append(
                Especime.coletor_principal.ilike(f"%{filtros.coletor}%")
            )

        # Filtro por status
        if filtros.status:
            conditions.append(Especime.status == filtros.status)

        # Filtro por data
        if filtros.data_coleta_inicio:
            conditions.append(Especime.data_coleta >= filtros.data_coleta_inicio)
        if filtros.data_coleta_fim:
            conditions.append(Especime.data_coleta <= filtros.data_coleta_fim)

        if conditions:
            query = query.where(and_(*conditions))

        # Contagem total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar()

        # Paginação
        offset = (filtros.page - 1) * filtros.per_page
        query = query.offset(offset).limit(filtros.per_page).order_by(Especime.id.desc())

        result = await db.execute(query)
        items = result.scalars().all()

        return total, list(items)

    @staticmethod
    async def listar_todos(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[int, List[Especime]]:
        count_q = select(func.count(Especime.id))
        total = (await db.execute(count_q)).scalar()

        result = await db.execute(
            select(Especime)
            .options(
                selectinload(Especime.taxonomia),
                selectinload(Especime.localidade),
                selectinload(Especime.imagens),
            )
            .offset(skip)
            .limit(limit)
            .order_by(Especime.id.desc())
        )
        return total, list(result.scalars().all())
