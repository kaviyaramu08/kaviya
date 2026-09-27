from datetime import date
from io import BytesIO

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


router = APIRouter()


class GenerateRequest(BaseModel):
	document_type: str
	parties: str
	terms: str
	effective_date: date


class ExportRequest(BaseModel):
	document_type: str
	text: str
	terms: str = ""
	logo_base64: str | None = None


@router.get("/health")
def health():
	return {"status": "ok"}


@router.post("/generate")
def generate_document(payload: GenerateRequest):
	if not payload.parties.strip() or not payload.terms.strip():
		raise HTTPException(status_code=400, detail="Parties and terms are required.")

	generated_text = (
		f"{payload.document_type}\n\n"
		f"Effective date: {payload.effective_date.isoformat()}\n\n"
		f"Parties\n{payload.parties.strip()}\n\n"
		f"Terms and Conditions\n{payload.terms.strip()}"
	)
	return {"generated_text": generated_text}


def _build_export_sections(payload: ExportRequest):
	sections = []

	if payload.document_type.strip():
		sections.append(payload.document_type.strip())

	if payload.text.strip():
		sections.append(payload.text.strip())

	if payload.terms.strip():
		sections.append("Terms and Conditions")
		sections.append(payload.terms.strip())

	return sections


@router.post("/export/{file_format}")
def export_document(file_format: str, payload: ExportRequest):
	if file_format == "txt":
		return Response(payload.text, media_type="text/plain")

	if file_format == "docx":
		doc = Document()
		for index, section in enumerate(_build_export_sections(payload)):
			if index == 0:
				doc.add_heading(section, level=1)
			elif section == "Terms and Conditions":
				doc.add_heading(section, level=2)
			else:
				doc.add_paragraph(section)

		buffer = BytesIO()
		doc.save(buffer)
		buffer.seek(0)
		return Response(buffer.getvalue(), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

	if file_format == "pdf":
		buffer = BytesIO()
		styles = getSampleStyleSheet()
		doc = SimpleDocTemplate(buffer, pagesize=letter)
		story = []
		story.append(Paragraph(payload.document_type.strip() or "Legal Document", styles["Title"]))
		story.append(Spacer(1, 12))
		if payload.text.strip():
			story.append(Paragraph(payload.text.strip(), styles["BodyText"]))
			story.append(Spacer(1, 12))
		if payload.terms.strip():
			story.append(Paragraph("Terms and Conditions", styles["Heading2"]))
			story.append(Paragraph(payload.terms.strip(), styles["BodyText"]))
		doc.build(story)
		buffer.seek(0)
		return Response(buffer.getvalue(), media_type="application/pdf")

	raise HTTPException(status_code=400, detail="Unsupported export format.")
