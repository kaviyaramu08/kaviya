from __future__ import annotations

import base64
import os
from datetime import date

import requests
import streamlit as st

from dotenv import load_dotenv

from utils.text_utils import (
    format_html_preview,
    sanitize_text,
)


load_dotenv()


st.set_page_config(
    page_title="LegalEase",
    page_icon="⚖️",
    layout="wide",
)


BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000"
).rstrip("/")


# -----------------------------
# CSS
# -----------------------------

st.markdown(
    """
    <style>

    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #777;
        margin-bottom: 30px;
        font-size: 17px;
    }

    .preview-card {
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #cccccc;
        background-color: rgba(128,128,128,0.05);
        max-height: 620px;
        overflow-y: auto;
        line-height: 1.7;
    }

    .notice {
        padding: 15px;
        border-left: 4px solid #777;
        background-color: rgba(128,128,128,0.08);
        border-radius: 6px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Session state
# -----------------------------

if "document_text" not in st.session_state:

    st.session_state.document_text = ""


if "generated" not in st.session_state:

    st.session_state.generated = False


# -----------------------------
# Header
# -----------------------------

st.markdown(
    '<div class="main-title">⚖️ LegalEase</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-assisted legal document drafting'
    '</div>',
    unsafe_allow_html=True
)


# -----------------------------
# Sidebar
# -----------------------------

with st.sidebar:

    st.header("Settings")

    st.caption(
        f"Backend: `{BACKEND_URL}`"
    )

    try:

        health_response = requests.get(
            f"{BACKEND_URL}/health",
            timeout=3
        )

        if health_response.ok:

            st.success(
                "Backend connected"
            )

        else:

            st.warning(
                "Backend returned an error"
            )

    except requests.RequestException:

        st.error(
            "Backend unavailable"
        )

    st.markdown("---")

    logo = st.file_uploader(
        "Upload optional logo",
        type=[
            "png",
            "jpg",
            "jpeg"
        ]
    )

    st.markdown("---")

    st.info(
        "LegalEase creates AI-assisted drafts. "
        "Important documents should be reviewed "
        "by a qualified legal professional."
    )


# -----------------------------
# Main columns
# -----------------------------

left, right = st.columns(
    [0.9, 1.1],
    gap="large"
)


# ==========================================================
# LEFT
# ==========================================================

with left:

    st.subheader(
        "Document Details"
    )

    document_type = st.selectbox(
        "Document Type",
        [
            "Employment Contract",
            "Non-Disclosure Agreement (NDA)",
            "Residential Lease Agreement",
            "Freelance Work Contract",
            "Employment Offer Letter",
            "General Agreement",
        ]
    )

    custom_type = st.text_input(
        "Custom Document Type",
        placeholder="Example: Consulting Agreement"
    )

    selected_type = (
        custom_type.strip()
        if custom_type.strip()
        else document_type
    )

    parties = st.text_area(
        "Parties Involved",
        height=120,
        placeholder=(
            "Example:\n"
            "Jane Doe (Service Provider)\n"
            "TechNova Inc. (Client)"
        )
    )

    terms = st.text_area(
        "Terms & Conditions",
        height=180,
        placeholder=(
            "Payment within 30 days; "
            "Confidentiality must be maintained; "
            "Either party may terminate with 15 days notice"
        ),
        help=(
            "Separate individual terms with semicolons."
        )
    )

    effective_date = st.date_input(
        "Effective Date",
        value=date.today()
    )

    generate_button = st.button(
        "✨ Generate Document",
        type="primary",
        use_container_width=True
    )


    # -----------------------------
    # Generate
    # -----------------------------

    if generate_button:

        if not parties.strip():

            st.error(
                "Please enter the parties involved."
            )

        elif not terms.strip():

            st.error(
                "Please enter the terms."
            )

        else:

            payload = {
                "document_type": selected_type,
                "parties": parties.strip(),
                "terms": terms.strip(),
                "effective_date":
                    effective_date.isoformat(),
            }

            try:

                with st.spinner(
                    "Generating document..."
                ):

                    response = requests.post(
                        f"{BACKEND_URL}/generate",
                        json=payload,
                        timeout=120
                    )

                if response.ok:

                    result = response.json()

                    st.session_state.document_text = (
                        sanitize_text(
                            result[
                                "generated_text"
                            ]
                        )
                    )

                    st.session_state.generated = True

                    st.success(
                        "Document generated successfully."
                    )

                else:

                    try:

                        detail = response.json().get(
                            "detail",
                            response.text
                        )

                    except ValueError:

                        detail = response.text

                    st.error(
                        f"Generation failed: {detail}"
                    )

            except requests.RequestException as exc:

                st.error(
                    f"Could not connect to backend: {exc}"
                )


# ==========================================================
# RIGHT
# ==========================================================

with right:

    st.subheader(
        "Preview & Edit"
    )

    if st.session_state.generated:

        edited_text = st.text_area(
            "Editable Document",
            value=st.session_state.document_text,
            height=560,
        )

        st.session_state.document_text = (
            sanitize_text(
                edited_text
            )
        )

        st.markdown(
            "### Preview"
        )

        preview = format_html_preview(
            st.session_state.document_text
        )

        st.markdown(
            f"""
            <div class="preview-card">
                {preview}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            "### Download"
        )

        # -----------------------------
        # Logo conversion
        # -----------------------------

        logo_base64 = None

        if logo is not None:

            logo_base64 = base64.b64encode(
                logo.getvalue()
            ).decode("ascii")


        export_payload = {
            "document_type": selected_type,
            "text": st.session_state.document_text,
            "terms": terms.strip(),
            "logo_base64": logo_base64,
        }


        # -----------------------------
        # Export function
        # -----------------------------

        def export_file(file_format):

            try:

                response = requests.post(
                    f"{BACKEND_URL}/export/{file_format}",
                    json=export_payload,
                    timeout=60
                )

                if response.ok:

                    return response.content

                try:

                    detail = response.json().get(
                        "detail",
                        response.text
                    )

                except ValueError:

                    detail = response.text

                st.error(
                    f"Export failed: {detail}"
                )

                return None

            except requests.RequestException as exc:

                st.error(
                    f"Export failed: {exc}"
                )

                return None


        col1, col2, col3 = st.columns(3)


        # TXT

        with col1:

            txt_data = export_file(
                "txt"
            )

            if txt_data:

                st.download_button(
                    "Download TXT",
                    data=txt_data,
                    file_name=(
                        "legalease_document.txt"
                    ),
                    mime="text/plain",
                    use_container_width=True,
                )


        # DOCX

        with col2:

            docx_data = export_file(
                "docx"
            )

            if docx_data:

                st.download_button(
                    "Download DOCX",
                    data=docx_data,
                    file_name=(
                        "legalease_document.docx"
                    ),
                    mime=(
                        "application/vnd.openxmlformats-"
                        "officedocument.wordprocessingml.document"
                    ),
                    use_container_width=True,
                )


        # PDF

        with col3:

            pdf_data = export_file(
                "pdf"
            )

            if pdf_data:

                st.download_button(
                    "Download PDF",
                    data=pdf_data,
                    file_name=(
                        "legalease_document.pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=True,
                )

    else:

        st.info(
            "Your generated document will appear here."
        )

        st.markdown(
            """
            <div class="notice">

            <b>Workflow</b>

            <br><br>

            1. Enter document details

            <br>

            2. Click Generate Document

            <br>

            3. Edit the generated document

            <br>

            4. Preview the document

            <br>

            5. Download TXT, DOCX or PDF

            </div>
            """,
            unsafe_allow_html=True
        )