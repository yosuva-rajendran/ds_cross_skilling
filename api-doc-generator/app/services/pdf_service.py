import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from sqlmodel import Session

from app.models.endpoint import Endpoint
from app.models.component_schema import ComponentSchema
from app.models.generated_doc import GeneratedDoc
from app.repositories.endpoint_repository import EndpointRepository
from app.repositories.component_repository import ComponentRepository
from app.repositories.generated_doc_repository import GeneratedDocRepository
from app.repositories.api_version_repository import APIVersionRepository

PAGE_WIDTH = A4[0] - 30 * mm  # total usable width (left + right margin = 30mm)


class PDFService:

    def __init__(self, session: Session):
        self.version_repo = APIVersionRepository(session)
        self.endpoint_repo = EndpointRepository(session)
        self.component_repo = ComponentRepository(session)
        self.doc_repo = GeneratedDocRepository(session)

    def generate_pdf(self, project_id: int, version_id: int) -> bytes:
        version = self.version_repo.get_by_id(version_id)
        if not version or version.project_id != project_id:
            raise ValueError(f"Version {version_id} not found for project {project_id}")

        endpoints = self.endpoint_repo.get_by_version(version_id)
        components = self.component_repo.get_by_version(version_id)
        generated_docs = {
            doc.endpoint_id: doc
            for doc in self.doc_repo.get_by_version(version_id)
        }

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
        )

        styles = _build_styles()
        elements = []

        # Title page
        elements.append(Spacer(1, 50 * mm))
        elements.append(Paragraph("API Documentation", styles["Title"]))
        elements.append(Spacer(1, 8 * mm))
        elements.append(HRFlowable(width="60%", color=colors.HexColor("#2e86c1"), thickness=2))
        elements.append(Spacer(1, 8 * mm))
        elements.append(Paragraph(f"Version {version.version}", styles["Heading2"]))
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph(
            f"{len(endpoints)} endpoints &bull; {len(components)} schemas",
            styles["Normal"],
        ))
        elements.append(PageBreak())

        # Endpoints
        elements.append(Paragraph("Endpoints", styles["Heading1"]))
        elements.append(Spacer(1, 4 * mm))

        for i, ep in enumerate(endpoints):
            gen_doc = generated_docs.get(ep.id)
            elements.extend(self._build_endpoint_section(ep, gen_doc, styles))
            if i < len(endpoints) - 1:
                elements.append(Spacer(1, 3 * mm))
                elements.append(HRFlowable(width="100%", color=colors.HexColor("#d5d8dc"), thickness=0.5))
                elements.append(Spacer(1, 3 * mm))

        # Components
        if components:
            elements.append(PageBreak())
            elements.append(Paragraph("Schemas", styles["Heading1"]))
            elements.append(Spacer(1, 4 * mm))

            for i, comp in enumerate(components):
                elements.extend(self._build_component_section(comp, styles))
                if i < len(components) - 1:
                    elements.append(Spacer(1, 3 * mm))
                    elements.append(HRFlowable(width="100%", color=colors.HexColor("#d5d8dc"), thickness=0.5))
                    elements.append(Spacer(1, 3 * mm))

        doc.build(elements)
        return buffer.getvalue()

    def _build_endpoint_section(self, endpoint: Endpoint, gen_doc: GeneratedDoc | None, styles: Any) -> list:
        elements = []

        method_color = {
            "GET": "#27ae60", "POST": "#2980b9",
            "PUT": "#f39c12", "PATCH": "#e67e22",
            "DELETE": "#e74c3c",
        }.get(endpoint.method.upper(), "#7f8c8d")

        elements.append(Paragraph(
            f'<font color="{method_color}" size="14"><b>{endpoint.method.upper()}</b></font>'
            f'&nbsp;&nbsp;<font size="11">{endpoint.path}</font>',
            styles["EndpointTitle"],
        ))

        if gen_doc and gen_doc.description:
            elements.append(Spacer(1, 2 * mm))
            elements.append(Paragraph(gen_doc.description, styles["Body"]))
        elif endpoint.summary:
            elements.append(Spacer(1, 2 * mm))
            elements.append(Paragraph(endpoint.summary, styles["Body"]))

        if endpoint.parameters:
            elements.append(Spacer(1, 3 * mm))
            elements.append(Paragraph("Parameters", styles["Label"]))

            col_widths = [PAGE_WIDTH * 0.25, PAGE_WIDTH * 0.15, PAGE_WIDTH * 0.20, PAGE_WIDTH * 0.15]
            remaining = PAGE_WIDTH - sum(col_widths)
            col_widths.append(remaining)

            table_data = [["Name", "In", "Type", "Required", "Description"]]
            for param in endpoint.parameters:
                schema = param.get("schema", {}) or {}
                table_data.append([
                    param.get("name", ""),
                    param.get("in", "query"),
                    schema.get("type", "string"),
                    "Yes" if param.get("required") else "No",
                    Paragraph(param.get("description", "-") or "-", styles["CellText"]),
                ])

            table = Table(table_data, colWidths=col_widths)
            table.setStyle(_table_style())
            elements.append(table)

        if gen_doc and gen_doc.usage_example:
            elements.append(Spacer(1, 3 * mm))
            elements.append(Paragraph("Example", styles["Label"]))

            example = gen_doc.usage_example
            for fence in ("```bash", "```json", "```shell", "```"):
                example = example.replace(fence, "")
            example = example.strip()
            example = example.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            example = example.replace("\n", "<br/>")
            elements.append(Paragraph(example, styles["CodeExample"]))

        if gen_doc and gen_doc.error_codes:
            elements.append(Spacer(1, 3 * mm))
            elements.append(Paragraph("Responses", styles["Label"]))

            col_widths = [PAGE_WIDTH * 0.12, PAGE_WIDTH * 0.88]
            table_data = [["Code", "Description"]]
            for code, desc in gen_doc.error_codes.items():
                table_data.append([code, Paragraph(desc, styles["CellText"])])

            table = Table(table_data, colWidths=col_widths)
            table.setStyle(_table_style())
            elements.append(table)

        return elements

    def _build_component_section(self, component: ComponentSchema, styles: Any) -> list:
        elements = []

        elements.append(Paragraph(component.name, styles["EndpointTitle"]))

        if component.description:
            elements.append(Paragraph(component.description, styles["Body"]))

        if component.properties:
            required_fields = set(component.required or [])
            col_widths = [PAGE_WIDTH * 0.30, PAGE_WIDTH * 0.30, PAGE_WIDTH * 0.15]

            table_data = [["Property", "Type", "Required"]]
            for prop_name, prop_info in component.properties.items():
                prop_type = prop_info.get("type", "unknown") if isinstance(prop_info, dict) else "unknown"
                table_data.append([prop_name, prop_type, "Yes" if prop_name in required_fields else "No"])

            table = Table(table_data, colWidths=col_widths)
            table.setStyle(_table_style(header_color="#1a5276"))
            elements.append(table)

        return elements


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "EndpointTitle",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1a5276"),
        spaceBefore=4,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#2e86c1"),
        fontName="Helvetica-Bold",
        spaceBefore=2,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "CodeExample",
        fontName="Courier",
        fontSize=7,
        leading=10,
        backColor=colors.HexColor("#f4f6f7"),
        borderPadding=(6, 6, 6, 6),
        spaceAfter=4,
        wordWrap="CJK",
    ))
    styles.add(ParagraphStyle(
        "CellText",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    ))

    return styles


def _table_style(header_color: str = "#2e86c1") -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_color)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d5d8dc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
    ])
