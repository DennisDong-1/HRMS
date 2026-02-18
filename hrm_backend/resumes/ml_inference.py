"""
ml_inference.py
---------------
Thin wrapper around the sibling `resume-screener` ML pipeline.

Provides two public functions:
  - parse_resume_file(path)          -> str   (raw resume text)
  - run_ml_screening(path, job_desc) -> dict  (score, skills, decision)
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make the sibling `resume-screener` package importable.
# Project layout:
#   HRM_With_AI/
#     HRMS/hrm_backend/          <- Django project root
#     resume-screener/           <- ML pipeline
# ---------------------------------------------------------------------------
_SCREENER_DIR = Path(__file__).resolve().parents[3] / "resume-screener"
if str(_SCREENER_DIR) not in sys.path:
    sys.path.insert(0, str(_SCREENER_DIR))

# ---------------------------------------------------------------------------
# Lazy imports from the ML pipeline (imported here so errors surface early).
# ---------------------------------------------------------------------------
try:
    from matcher.embedding_scorer import EmbeddingScorer          # noqa: E402
    from matcher.text_cleaner import clean_text                   # noqa: E402
    from matcher.phrase_skill_matcher import PhraseSkillMatcher   # noqa: E402
    _ML_AVAILABLE = True
except ImportError as _e:
    _ML_AVAILABLE = False
    _ML_IMPORT_ERROR = str(_e)


# ---------------------------------------------------------------------------
# Resume text extraction helpers
# ---------------------------------------------------------------------------

def _extract_text_pdf(path: str) -> str:
    """Extract text from a PDF file using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError(
            "PyMuPDF is required for PDF parsing. Install it with: pip install pymupdf"
        )
    text_parts = []
    with fitz.open(path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def _extract_text_docx(path: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    try:
        import docx
    except ImportError:
        raise ImportError(
            "python-docx is required for DOCX parsing. Install it with: pip install python-docx"
        )
    doc = docx.Document(path)
    return "\n".join(para.text for para in doc.paragraphs)


def parse_resume_file(path: str) -> str:
    """
    Extract raw text from a resume file.

    Supports .pdf and .docx extensions.
    Raises ValueError for unsupported formats.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return _extract_text_pdf(path)
    elif ext == ".docx":
        return _extract_text_docx(path)
    else:
        raise ValueError(f"Unsupported resume format: '{ext}'. Only PDF and DOCX are supported.")


# ---------------------------------------------------------------------------
# Main screening function
# ---------------------------------------------------------------------------

def run_ml_screening(resume_file_path: str, job_description: str) -> dict:
    """
    Run the ML screening pipeline for a single resume.

    Args:
        resume_file_path: Absolute filesystem path to the uploaded resume file.
        job_description:  The job's description text (used as the query).

    Returns:
        {
            "score":            float,   # 0–100 cosine similarity score
            "extracted_skills": list,    # all skills found in resume
            "matched_skills":   list,    # skills that also appear in job description
            "decision":         str,     # "SHORTLISTED" or "REJECTED"
        }

    Raises:
        RuntimeError: if the ML pipeline could not be imported.
    """
    if not _ML_AVAILABLE:
        raise RuntimeError(
            f"ML pipeline is not available. Import error: {_ML_IMPORT_ERROR}"
        )

    # 1. Parse resume text
    resume_text = parse_resume_file(resume_file_path)

    # 2. Clean both texts
    clean_resume = clean_text(resume_text)
    clean_job = clean_text(job_description)

    # 3. Compute cosine similarity via EmbeddingScorer
    scorer = EmbeddingScorer()
    similarity = scorer.score(clean_job, clean_resume)  # returns 0.0–1.0
    score = round(float(similarity) * 100, 2)           # convert to 0–100

    # 4. Extract skills from resume text using PhraseSkillMatcher
    skill_matcher = PhraseSkillMatcher()
    extracted_skills: list[str] = skill_matcher.extract(resume_text)

    # 5. Find which extracted skills appear in the job description (case-insensitive)
    job_desc_lower = job_description.lower()
    matched_skills: list[str] = [
        skill for skill in extracted_skills
        if skill.lower() in job_desc_lower
    ]

    # 6. Determine decision
    decision = "SHORTLISTED" if score >= 60 else "REJECTED"

    return {
        "score": score,
        "extracted_skills": extracted_skills,
        "matched_skills": matched_skills,
        "decision": decision,
    }
