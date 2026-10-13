import io
import re
import csv
import datetime as dt
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import openpyxl

from app.schemas.import_schema import ImportedRowSchema, ImportPreviewResponse, ImportExecuteResponse
from app.models.models import Especime, Taxonomia, LocalidadeGeografica, StatusEspecime, TipoColeta


def _slug(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    return re.sub(r"\s+", " ", str(text)).strip() or None


def _clean_name(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    v = re.sub(r"\s+", " ", str(text)).strip()
    return v or None


def _parse_date(value: object) -> Optional[dt.date]:
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    s = str(value).strip()
    if not s or s.lower() in {"desconhecido", "desconhecida", "-", "n/d"}:
        return None
    for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y", "%Y-%m-%d", "%d\\%m\\%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _parse_geo_location(text: Optional[str]) -> Dict[str, Any]:
    if not text:
        return {}
    t = text.strip()
    lat, lon, alt = None, None, None
    muni, uf = None, None
    metodo = None

    # UF
    if re.search(r"\bMG\b|Minas", t, re.I):
        uf = "MG"
    elif re.search(r"\bBA\b|Bahia", t, re.I):
        uf = "BA"
    elif re.search(r"\bSP\b|São Paulo", t, re.I):
        uf = "SP"
    elif re.search(r"\bGO\b|Goiás", t, re.I):
        uf = "GO"
    elif re.search(r"\bDF\b|Brasília|Brasilia", t, re.I):
        uf = "DF"

    # Municípios conhecidos da região de coleta do Norte de Minas / Bacia do São Francisco
    municipios = [
        "Januária", "Januaria", "Bonito de Minas", "Cônego Marinho", "Conego Marinho",
        "Juvenília", "Juvenilha", "Itacarambi", "Pedras de Maria da Cruz", "São Francisco",
        "Lontra", "Patis", "Montes Claros", "Varzelândia", "Manga", "Matias Cardoso",
        "Miravânia", "Montalvânia", "Jaíba", "Jaiba", "Ubaí", "Ubai", "São João das Missões",
        "Brasília de Minas", "Pintópolis", "Chapada Gaúcha", "Belo Horizonte"
    ]
    for m in municipios:
        if re.search(r"\b" + re.escape(m) + r"\b", t, re.I):
            muni = (
                m.replace("Januaria", "Januária")
                .replace("Conego Marinho", "Cônego Marinho")
                .replace("Juvenilha", "Juvenília")
                .replace("Jaiba", "Jaíba")
                .replace("Ubai", "Ubaí")
            )
            if not uf:
                uf = "MG"
            break

    # Pontos notórios de Januária sem o nome explícito da cidade
    if not muni and re.search(r"IFNMG|Brejo do amparo|Vila Paula|Vila Jadete|Riacho da Cruz|Campus Januária|Tejuco|Vila do Brejo", t, re.I):
        muni = "Januária"
        uf = "MG"

    # Altitude: ex 535m
    m_alt = re.search(r"(\d{2,4})\s*m\b", t, re.I)
    if m_alt:
        try:
            alt = float(m_alt.group(1))
        except ValueError:
            pass

    # Coordenadas em Graus Decimais (ex: -15.48185, -44.35202 ou -15,48185 -44,35202)
    clean_t = t.replace(",", ".")
    m_dec = re.search(r"(-?1[4-6]\.\d+)[^\d\-]+(-?4[3-5]\.\d+)", clean_t)
    if m_dec:
        try:
            lat = float(m_dec.group(1))
            lon = float(m_dec.group(2))
            if lat > 0:
                lat = -lat
            if lon > 0:
                lon = -lon
            metodo = "GPS de Campo (Decimal)"
        except ValueError:
            pass

    # Coordenadas em Graus, Minutos e Segundos (DMS) (ex: -15º 28' 01.6" S -44º 22' 13.7" W)
    if not lat:
        m_dms = re.search(
            r"(\d{1,2})[º°\s]+(\d{1,2})['’`\s]+(\d{1,2}(?:\.\d+)?)['’`\"”\s]*[Ss]?[^\d\-]+(\d{1,2})[º°\s]+(\d{1,2})['’`\s]+(\d{1,2}(?:\.\d+)?)['’`\"”\s]*[WwOo]?",
            t
        )
        if m_dms:
            try:
                d1, m1, s1, d2, m2, s2 = [float(x) for x in m_dms.groups()]
                lat = -(d1 + m1 / 60.0 + s1 / 3600.0)
                lon = -(d2 + m2 / 60.0 + s2 / 3600.0)
                metodo = "GPS de Campo (DMS)"
            except ValueError:
                pass

    # Bioma regional predominante (Norte de Minas Gerais / Cerrado e Caatinga)
    bioma = "Cerrado" if uf == "MG" else None

    return {
        "latitude": lat,
        "longitude": lon,
        "altitude_m": alt,
        "municipio": muni,
        "estado": uf,
        "bioma": bioma,
        "metodo_geolocalizacao": metodo,
    }


def _detect_and_map_headers(header_tuple: tuple) -> Dict[int, str]:
    header = tuple((v or "").strip().lower() for v in header_tuple)
    alias_map = {
        "nome cientifico": "nome_cientifico",
        "nome científico": "nome_cientifico",
        "nome popular": "nome_popular",
        "familia": "familia",
        "família": "familia",
        "familía": "familia",
        "genero": "genero",
        "gênero": "genero",
        "género": "genero",
        "especie": "especie",
        "espécie": "especie",
        "localizacao": "localizacao",
        "localização": "localizacao",
        "data da coleta": "data_coleta",
        "data de coleta": "data_coleta",
        "data coleta": "data_coleta",
        "origem": "origem",
        "coletor": "coletor",
        "codigo": "codigo",
        "código": "codigo",
        "filo": "filo",
        "classe": "classe",
        "ordem": "ordem",
    }
    result = {}
    for idx, h in enumerate(header):
        mapped = alias_map.get(h, h)
        if mapped in alias_map.values():
            result[idx] = mapped
    return result


class ImportService:

    @staticmethod
    def parse_and_validate_file(file_bytes: bytes, filename: str) -> ImportPreviewResponse:
        raw_rows = []

        if filename.lower().endswith(".csv"):
            text = file_bytes.decode("utf-8-sig", errors="ignore")
            lines = text.splitlines()
            reader = csv.reader(lines)
            headers = None
            pending_rows = []
            for row_idx, row in enumerate(reader, start=1):
                if not row or not any(row):
                    continue
                if headers is None:
                    joined = " ".join(row).upper()
                    if any(token in joined for token in ["CÓDIGO", "CODIGO", "NOME CIENTIFICO", "FAMILIA", "FAMILÍA", "ESPÉCIE", "ESPECIE"]):
                        headers = _detect_and_map_headers(tuple(row))
                        continue
                    pending_rows.append((row_idx, row))
                    continue

                raw_rows.append((row_idx, "CSV", row, headers))

            if headers is None and pending_rows:
                first_idx, first_row = pending_rows[0]
                headers = _detect_and_map_headers(tuple(first_row))
                if not headers:
                    headers = {i: f"col_{i}" for i in range(len(first_row))}
                for row_idx, row in pending_rows[1:]:
                    raw_rows.append((row_idx, "CSV", row, headers))
        else:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                headers = None
                for row_idx, row_values in enumerate(ws.iter_rows(values_only=True), start=1):
                    if not row_values or not any(v is not None for v in row_values):
                        continue
                    str_row = tuple("" if v is None else str(v) for v in row_values)
                    joined = " ".join(str_row).upper()
                    if any(token in joined for token in ["CÓDIGO", "CODIGO", "NOME CIENTIFICO", "FAMILIA"]):
                        headers = _detect_and_map_headers(str_row)
                        continue
                    if "ORGANIZAÇÃO" in joined or "ORGANIZACAO" in joined:
                        continue
                    if headers is None:
                        continue
                    raw_rows.append((row_idx, sheet_name, row_values, headers))

        parsed_rows: List[ImportedRowSchema] = []
        seen_codes = set()
        seen_taxonomias = set()
        seen_localidades = set()

        valid_cnt = 0
        warn_cnt = 0
        err_cnt = 0

        for idx, (row_idx, sheet, row, headers) in enumerate(raw_rows, start=1):
            def get_val(field_name: str) -> Optional[str]:
                for h_idx, mapped in headers.items():
                    if mapped == field_name and h_idx < len(row):
                        val = row[h_idx]
                        if val is not None:
                            return _clean_name(str(val))
                return None

            codigo = get_val("codigo") or f"HERB-AUTO-{idx:04d}"
            if "ORGANIZAÇÃO" in codigo.upper() or "ORGANIZACAO" in codigo.upper():
                continue

            nome_cientifico = get_val("nome_cientifico") or get_val("especie") or get_val("genero") or "Escipie não identificada"
            nome_popular = get_val("nome_popular")
            filo = get_val("filo")
            classe = get_val("classe")
            ordem = get_val("ordem")
            familia = get_val("familia")
            genero = get_val("genero")
            especie = get_val("especie")
            localizacao = get_val("localizacao")
            raw_date = get_val("data_coleta")
            origem = get_val("origem")
            coletor = get_val("coletor")

            parsed_date = _parse_date(raw_date)
            data_coleta_str = parsed_date.isoformat() if parsed_date else None

            status_val = "valid"
            msg_val = None

            if codigo in seen_codes:
                status_val = "warning"
                msg_val = f"Código {codigo} duplicado na planilha. Será atualizado se existir no banco."
                warn_cnt += 1
            else:
                seen_codes.add(codigo)
                valid_cnt += 1

            if nome_cientifico:
                seen_taxonomias.add(nome_cientifico.lower())
            if localizacao:
                seen_localidades.add(localizacao.lower())

            parsed_rows.append(
                ImportedRowSchema(
                    sheet=sheet,
                    row_index=row_idx,
                    codigo=codigo,
                    nome_cientifico=nome_cientifico,
                    nome_popular=nome_popular,
                    filo=filo,
                    classe=classe,
                    ordem=ordem,
                    familia=familia,
                    genero=genero,
                    especie=especie,
                    localizacao=localizacao,
                    data_coleta=data_coleta_str,
                    origem=origem,
                    coletor=coletor,
                    status_validacao=status_val,
                    mensagem_validacao=msg_val,
                )
            )

        return ImportPreviewResponse(
            filename=filename,
            total_rows=len(parsed_rows),
            valid_rows=valid_cnt,
            warning_rows=warn_cnt,
            error_rows=err_cnt,
            new_taxonomias_est=len(seen_taxonomias),
            new_localidades_est=len(seen_localidades),
            rows=parsed_rows,
        )

    @staticmethod
    async def execute_import(db: AsyncSession, rows: List[ImportedRowSchema], user_id: int) -> ImportExecuteResponse:
        especimes_criados = 0
        especimes_atualizados = 0
        taxonomias_criadas = 0
        localidades_criadas = 0
        erros = 0
        detalhes_erros = []

        tax_res = await db.execute(select(Taxonomia))
        all_tax = tax_res.scalars().all()
        tax_cache: Dict[str, int] = {t.nome_cientifico.strip().lower(): t.id for t in all_tax if t.nome_cientifico}

        loc_res = await db.execute(select(LocalidadeGeografica))
        all_loc = loc_res.scalars().all()
        loc_cache: Dict[str, int] = {}
        for l in all_loc:
            key = (l.localidade or "").strip().lower()
            if key:
                loc_cache[key] = l.id

        esp_res = await db.execute(select(Especime))
        all_esp = esp_res.scalars().all()
        esp_cache: Dict[str, Especime] = {
            e.codigo_catalogo.strip(): e for e in all_esp if e.codigo_catalogo
        }

        for r in rows:
            code_key = (r.codigo or "").strip()
            if not code_key or "ORGANIZAÇÃO" in code_key.upper() or "ORGANIZACAO" in code_key.upper():
                continue

            try:
                async with db.begin_nested():
                    # 1. Process Taxonomia
                    tax_name = r.nome_cientifico.strip() if r.nome_cientifico else "Não identificada"
                    tax_key = tax_name.lower()

                    tax_id = tax_cache.get(tax_key)
                    new_tax_created = False
                    if not tax_id:
                        new_tax = Taxonomia(
                            nome_cientifico=tax_name,
                            familia=r.familia,
                            genero=r.genero or (tax_name.split()[0] if " " in tax_name else tax_name),
                            epiteto_especifico=r.especie,
                            nome_comum=r.nome_popular,
                            filo=r.filo,
                            classe=r.classe,
                            ordem=r.ordem,
                        )
                        db.add(new_tax)
                        await db.flush()
                        tax_id = new_tax.id
                        tax_cache[tax_key] = tax_id
                        new_tax_created = True

                    # 2. Process Localidade
                    loc_id = None
                    new_loc_created = False
                    if r.localizacao:
                        loc_key = r.localizacao.strip().lower()
                        loc_id = loc_cache.get(loc_key)
                        if not loc_id:
                            geo_info = _parse_geo_location(r.localizacao)
                            new_loc = LocalidadeGeografica(
                                pais="Brasil",
                                estado=geo_info.get("estado"),
                                municipio=geo_info.get("municipio"),
                                localidade=r.localizacao,
                                latitude=geo_info.get("latitude"),
                                longitude=geo_info.get("longitude"),
                                altitude_m=geo_info.get("altitude_m"),
                                bioma=geo_info.get("bioma"),
                                metodo_geolocalizacao=geo_info.get("metodo_geolocalizacao"),
                                datum_geodesico="WGS84",
                                criado_em=dt.datetime.utcnow(),
                            )
                            db.add(new_loc)
                            await db.flush()
                            loc_id = new_loc.id
                            loc_cache[loc_key] = loc_id
                            new_loc_created = True

                    # 3. Upsert Especime
                    esp = esp_cache.get(code_key)

                    parsed_dt = None
                    if r.data_coleta:
                        try:
                            parsed_dt = dt.datetime.fromisoformat(r.data_coleta)
                        except ValueError:
                            pass

                    obs_origem = f"Origem: {r.origem}" if r.origem else None

                    if esp:
                        esp.taxonomia_id = tax_id
                        if loc_id:
                            esp.localidade_id = loc_id
                        if r.coletor:
                            esp.coletor_principal = r.coletor
                        if parsed_dt:
                            esp.data_coleta = parsed_dt
                        if obs_origem and not esp.observacoes:
                            esp.observacoes = obs_origem
                        especimes_atualizados += 1
                    else:
                        esp = Especime(
                            codigo_catalogo=code_key,
                            taxonomia_id=tax_id,
                            localidade_id=loc_id,
                            coletor_principal=r.coletor,
                            data_coleta=parsed_dt,
                            observacoes=obs_origem,
                            status=StatusEspecime.ativo,
                            tipo_coleta=TipoColeta.campo,
                            numero_individuos=1,
                            direitos="CC BY 4.0",
                            cadastrado_por_id=user_id,
                            data_entrada_colecao=dt.datetime.utcnow(),
                        )
                        db.add(esp)
                        esp_cache[code_key] = esp
                        especimes_criados += 1

                    await db.flush()

                    if new_tax_created:
                        taxonomias_criadas += 1
                    if new_loc_created:
                        localidades_criadas += 1

            except Exception as exc:
                erros += 1
                detalhes_erros.append(f"Linha {r.row_index} ({r.codigo}): {str(exc)}")

        await db.commit()

        return ImportExecuteResponse(
            total_processed=len(rows),
            especimes_criados=especimes_criados,
            especimes_atualizados=especimes_atualizados,
            taxonomias_criadas=taxonomias_criadas,
            localidades_criadas=localidades_criadas,
            erros=erros,
            detalhes_erros=detalhes_erros,
        )
