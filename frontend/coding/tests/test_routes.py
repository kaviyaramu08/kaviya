import unittest

from fastapi.testclient import TestClient

from main import app


class RoutesExportTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_docx_export_returns_document_bytes(self):
        response = self.client.post(
            "/export/docx",
            json={
                "document_type": "Service Agreement",
                "text": "This is a draft agreement.",
                "terms": "Confidentiality obligations apply.",
                "logo_base64": None,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("application/vnd.openxmlformats-officedocument.wordprocessingml.document", response.headers["content-type"])
        self.assertTrue(response.content.startswith(b"PK"))

    def test_pdf_export_returns_pdf_bytes(self):
        response = self.client.post(
            "/export/pdf",
            json={
                "document_type": "Service Agreement",
                "text": "This is a draft agreement.",
                "terms": "Confidentiality obligations apply.",
                "logo_base64": None,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("application/pdf", response.headers["content-type"])
        self.assertTrue(response.content.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
