import csv
import uuid
import zipfile
from io import BytesIO
from typing import List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.models import Especime
from app.config.config import settings


class ExportService:
    """Exportação no formato Darwin Core Archive (DwC-A)."""

    DWC_FIELDS = [
        "id", "basisOfRecord", "occurrenceID", "catalogNumber", "recordedBy",
        "eventDate", "country", "stateProvince", "county", "locality",
        "decimalLatitude", "decimalLongitude", "geodeticDatum", "coordinateUncertaintyInMeters",
        "kingdom", "phylum", "class", "order", "family", "genus",
        "specificEpithet", "scientificName", "scientificNameAuthorship",
        "identifiedBy", "dateIdentified", "sex", "lifeStage",
        "individualCount", "occurrenceStatus", "preparations",
        "fieldNumber", "associatedMedia", "license", "rightsHolder",
        "modified",
    ]

    @staticmethod
    def _especime_to_dwc(e: Especime) -> dict:
        """Converte um espécime para o mapeamento Darwin Core."""
        t = e.taxonomia
        l = e.localidade

        # Montar URL de mídia
        imagens_url = "|".join(
            [img.url_relativa for img in e.imagens if img.url_relativa]
        ) if e.imagens else ""

        return {
            "id": e.dwc_record_id or f"urn:catalog:{e.codigo_catalogo}",
            "basisOfRecord": "PreservedSpecimen",
            "occurrenceID": e.dwc_record_id or "",
            "catalogNumber": e.codigo_catalogo,
            "recordedBy": e.coletor_principal or "",
            "eventDate": e.data_coleta.strftime("%Y-%m-%d") if e.data_coleta else "",
            "country": l.pais if l else "Brasil",
            "stateProvince": l.estado if l else "",
            "county": l.municipio if l else "",
            "locality": l.localidade if l else "",
            "decimalLatitude": l.latitude if l else "",
            "decimalLongitude": l.longitude if l else "",
            "geodeticDatum": l.datum_geodesico if l else "WGS84",
            "coordinateUncertaintyInMeters": l.precisao_coordenadas_m if l else "",
            "kingdom": t.reino if t else "",
            "phylum": t.filo if t else "",
            "class": t.classe if t else "",
            "order": t.ordem if t else "",
            "family": t.familia if t else "",
            "genus": t.genero if t else "",
            "specificEpithet": t.epiteto_especifico if t else "",
            "scientificName": t.nome_cientifico if t else "",
            "scientificNameAuthorship": t.autor_descricao if t else "",
            "identifiedBy": e.identificado_por or "",
            "dateIdentified": e.data_identificacao.strftime("%Y-%m-%d") if e.data_identificacao else "",
            "sex": e.sexo or "",
            "lifeStage": e.estagio_vida or "",
            "individualCount": e.numero_individuos,
            "occurrenceStatus": "present",
            "preparations": e.meio_preservacao or "",
            "fieldNumber": e.numero_campo or "",
            "associatedMedia": imagens_url,
            "license": e.licenca or e.direitos,
            "rightsHolder": "",
            "modified": e.atualizado_em.strftime("%Y-%m-%dT%H:%M:%S") if e.atualizado_em else "",
        }

    @staticmethod
    def _gerar_meta_xml(nome_csv: str, fields: List[str]) -> str:
        field_tags = "\n".join(
            [f'    <field index="{i}" term="http://rs.tdwg.org/dwc/terms/{f}"/>'
             for i, f in enumerate(fields) if f != "id"]
        )
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<archive xmlns="http://rs.tdwg.org/dwc/text/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://rs.tdwg.org/dwc/text/ http://rs.tdwg.org/dwc/text/tdwg_dwc_text.xsd">
  <core encoding="UTF-8" fieldsTerminatedBy="," linesTerminatedBy="\\n"
        fieldsEnclosedBy="&quot;" ignoreHeaderLines="1"
        rowType="http://rs.tdwg.org/dwc/terms/Occurrence">
    <files><location>{nome_csv}</location></files>
    <id index="0"/>
{field_tags}
  </core>
</archive>"""

    @staticmethod
    def _gerar_eml_xml(total: int) -> str:
        now = datetime.utcnow().strftime("%Y-%m-%d")
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<eml:eml xmlns:eml="eml://ecoinformatics.org/eml-2.1.1"
         packageId="urn:uuid:{uuid.uuid4()}" system="BioAcervo">
  <dataset>
    <title>Exportação BioAcervo - Darwin Core Archive</title>
    <pubDate>{now}</pubDate>
    <abstract><para>Exportação de {total} espécimes do acervo biológico.</para></abstract>
    <intellectualRights><para>Conforme licença de cada registro.</para></intellectualRights>
  </dataset>
</eml:eml>"""

    @staticmethod
    async def exportar_dwca(db: AsyncSession, ids: List[int] = None) -> bytes:
        """Gera um arquivo ZIP Darwin Core Archive em memória."""
        query = (
            select(Especime)
            .options(
                selectinload(Especime.taxonomia),
                selectinload(Especime.localidade),
                selectinload(Especime.imagens),
            )
        )
        if ids:
            query = query.where(Especime.id.in_(ids))

        result = await db.execute(query)
        especimes = result.scalars().all()

        # Montar CSV em memória
        rows = [ExportService._especime_to_dwc(e) for e in especimes]

        # Escrever via StringIO
        import io
        sio = io.StringIO()
        writer = csv.DictWriter(sio, fieldnames=ExportService.DWC_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
        csv_bytes = sio.getvalue().encode("utf-8")

        # Montar ZIP
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("occurrence.csv", csv_bytes)
            zf.writestr(
                "meta.xml",
                ExportService._gerar_meta_xml("occurrence.csv", ExportService.DWC_FIELDS).encode("utf-8"),
            )
            zf.writestr(
                "eml.xml",
                ExportService._gerar_eml_xml(len(rows)).encode("utf-8"),
            )

        return zip_buffer.getvalue()


class EtiquetaService:
    """Geração de etiquetas com código de barras em PDF."""

    @staticmethod
    def gerar_etiqueta_pdf(especime: Especime) -> bytes:
        from reportlab.lib.pagesizes import A6, landscape
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib import colors
        import barcode
        from barcode.writer import ImageWriter
        from io import BytesIO

        buffer = BytesIO()
        largura, altura = landscape(A6)
        c = rl_canvas.Canvas(buffer, pagesize=(largura, altura))

        # Fundo branco
        c.setFillColor(colors.white)
        c.rect(0, 0, largura, altura, fill=1)

        # Cabeçalho
        c.setFillColor(colors.HexColor("#1a472a"))
        c.rect(0, altura - 20 * mm, largura, 20 * mm, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(largura / 2, altura - 13 * mm, "COLEÇÃO BIOLÓGICA")

        # Nome científico
        c.setFillColor(colors.black)
        c.setFont("Helvetica-BoldOblique", 12)
        nome_cient = especime.taxonomia.nome_cientifico if especime.taxonomia else "N/D"
        c.drawCentredString(largura / 2, altura - 28 * mm, nome_cient)

        # Família
        if especime.taxonomia and especime.taxonomia.familia:
            c.setFont("Helvetica", 9)
            c.drawCentredString(largura / 2, altura - 34 * mm, f"Família: {especime.taxonomia.familia}")

        # Dados de coleta
        c.setFont("Helvetica", 8)
        y = altura - 42 * mm
        linha = 5 * mm
        dados = [
            ("Código:", especime.codigo_catalogo),
            ("Coletor:", especime.coletor_principal or "N/D"),
            ("Data coleta:", especime.data_coleta.strftime("%d/%m/%Y") if especime.data_coleta else "N/D"),
        ]
        if especime.localidade:
            loc = especime.localidade
            loc_str = ", ".join(filter(None, [loc.municipio, loc.estado, loc.pais]))
            dados.append(("Local:", loc_str))
            if loc.latitude is not None and loc.longitude is not None:
                dados.append(("Coordenadas:", f"{loc.latitude:.4f}, {loc.longitude:.4f}"))

        for label, valor in dados:
            c.setFont("Helvetica-Bold", 8)
            c.drawString(8 * mm, y, label)
            c.setFont("Helvetica", 8)
            c.drawString(35 * mm, y, str(valor)[:55])
            y -= linha

        # Código de barras
        try:
            barcode_io = BytesIO()
            codigo = especime.codigo_barras or especime.codigo_catalogo
            # Usar Code128
            CODE128 = barcode.get_barcode_class("code128")
            bc = CODE128(codigo, writer=ImageWriter())
            bc.write(barcode_io, options={
                "module_width": 0.4, "module_height": 8, "font_size": 6,
                "text_distance": 2, "quiet_zone": 2,
            })
            barcode_io.seek(0)
            from reportlab.lib.utils import ImageReader
            img_reader = ImageReader(barcode_io)
            c.drawImage(img_reader, largura - 65 * mm, 5 * mm, width=60 * mm, height=22 * mm)
        except Exception:
            c.setFont("Helvetica", 7)
            c.drawString(largura - 65 * mm, 10 * mm, f"CÓD: {especime.codigo_barras or especime.codigo_catalogo}")

        c.save()
        return buffer.getvalue()
