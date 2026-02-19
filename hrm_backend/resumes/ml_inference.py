"""
ml_inference.py
---------------
Thin wrapper around the sibling `resume-screener` ML pipeline.

Provides two public functions:
  - parse_resume_file(path)          -> str   (raw resume text)
  - run_ml_screening(path, job_desc) -> dict  (score, skills, ner_bonus, decision)

Three-signal hybrid pipeline
-----------------------------
Signal 1 – Embedding similarity  : EmbeddingScorer (SentenceTransformer cosine)
Signal 2 – Skill phrase matching  : EntityExtractor.extract() → skills list
Signal 3 – NER entity bonus       : EntityExtractor.extract() → titles/orgs/locs/exp
Fusion    – HybridRanker.hybrid_score() (weights: 50% emb, 35% skill, 15% NER)
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
# Lazy imports from the ML pipeline.
# ---------------------------------------------------------------------------
try:
    from modules.scorer.embedding_scorer import EmbeddingScorer   # noqa: E402
    from modules.scorer.hybrid_ranker import HybridRanker         # noqa: E402
    from modules.ner.ner_entity_extractor import EntityExtractor  # noqa: E402
    from utils.text_cleaner import TextCleaner                    # noqa: E402
    _ML_AVAILABLE = True
    _ML_IMPORT_ERROR = ""
except ImportError as _e:
    _ML_AVAILABLE = False
    _ML_IMPORT_ERROR = str(_e)


# ---------------------------------------------------------------------------
# Module-level singletons (lazy-initialised on first call).
# Loading SentenceTransformer + spaCy is expensive; do it only once.
# ---------------------------------------------------------------------------
_embedding_scorer: "EmbeddingScorer | None" = None
_entity_extractor: "EntityExtractor | None" = None
_hybrid_ranker: "HybridRanker | None" = None


def _get_embedding_scorer() -> "EmbeddingScorer":
    global _embedding_scorer
    if _embedding_scorer is None:
        _embedding_scorer = EmbeddingScorer()
    return _embedding_scorer


def _get_entity_extractor() -> "EntityExtractor":
    global _entity_extractor
    if _entity_extractor is None:
        _skills_file = str(_SCREENER_DIR / "data" / "skills" / "skills_list.txt")
        _entity_extractor = EntityExtractor(
            spacy_model="en_core_web_sm",
            skills_list_file=_skills_file,
        )
    return _entity_extractor


def _get_hybrid_ranker() -> "HybridRanker":
    global _hybrid_ranker
    if _hybrid_ranker is None:
        # Default balanced weights from the ML paper:
        # 50% embedding · 35% skill overlap · 15% NER bonus
        _hybrid_ranker = HybridRanker(w_embedding=0.50, w_skill=0.35, w_ner_bonus=0.15)
    return _hybrid_ranker


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
    Run the three-signal ML screening pipeline for a single resume.

    Signals
    -------
    1. Embedding similarity  — SentenceTransformer cosine (EmbeddingScorer)
    2. Skill phrase matching — spaCy PhraseMatcher via EntityExtractor
    3. NER entity bonus      — titles / organizations / locations / experience years

    Args:
        resume_file_path: Absolute filesystem path to the uploaded resume file.
        job_description:  The job's description text (used as the query).

    Returns:
        {
            "score":            float,   # 0–100 fused hybrid score
            "ner_bonus":        float,   # 0.0–1.0 raw NER-bonus component
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

    # ------------------------------------------------------------------
    # 1. Parse resume → raw text
    # ------------------------------------------------------------------
    resume_text = parse_resume_file(resume_file_path)

    # ------------------------------------------------------------------
    # 2. Clean both texts for embedding
    # ------------------------------------------------------------------
    clean_resume = TextCleaner.clean_text(resume_text)
    clean_job = TextCleaner.clean_text(job_description)

    # ------------------------------------------------------------------
    # 3. Signal 1 – Embedding cosine similarity (0–1)
    # ------------------------------------------------------------------
    scorer = _get_embedding_scorer()
    job_embedding = scorer.encode(clean_job)
    resume_embedding = scorer.encode(clean_resume)
    embedding_score: float = scorer.compute_similarity(job_embedding, resume_embedding)
    # Clamp to [0, 1] in case of floating-point drift
    embedding_score = max(0.0, min(1.0, embedding_score))

    # ------------------------------------------------------------------
    # 4. Signal 2 + 3 – Entity / skill extraction via EntityExtractor
    #    (EntityExtractor internally owns PhraseSkillMatcher + spaCy NER)
    # ------------------------------------------------------------------
    extractor = _get_entity_extractor()

    # Extract from resume text (raw, not cleaned – preserves date ranges for exp)
    resume_entities: dict = extractor.extract(resume_text)
    # Extract from job description
    job_entities: dict = extractor.extract(job_description)

    extracted_skills: list[str] = resume_entities.get("skills", [])
    job_skills: list[str] = job_entities.get("skills", [])

    # Matched skills = resume skills that appear in job description (fallback approach)
    job_desc_lower = job_description.lower()
    matched_skills: list[str] = [
        skill for skill in extracted_skills if skill.lower() in job_desc_lower
    ]

    # ------------------------------------------------------------------
    # 5. Fuse all three signals via HybridRanker
    # ------------------------------------------------------------------
    ranker = _get_hybrid_ranker()
    hybrid_result: dict = ranker.hybrid_score(
        embedding_score=embedding_score,
        job_skills=job_skills,
        resume_skills=extracted_skills,
        job_entities=job_entities,
        resume_entities=resume_entities,
    )

    # hybrid_score returns final_score in [0, 1] — scale to 0–100
    final_score = round(float(hybrid_result["final_score"]) * 100, 2)
    ner_bonus = round(float(hybrid_result["ner_bonus"]), 6)

    # ------------------------------------------------------------------
    # 6. Decision threshold
    # ------------------------------------------------------------------
    decision = "SHORTLISTED" if final_score >= 60 else "REJECTED"

    return {
        "score":            final_score,
        # Component breakdown (0–100 scaled)
        "embedding_score":  round(float(hybrid_result["embedding"]) * 100, 2),
        "skill_score":      round(float(hybrid_result["skill_overlap"]) * 100, 2),
        "ner_bonus":        ner_bonus,          # kept as raw 0–1 (stored in DB)
        "extracted_skills": extracted_skills,
        "matched_skills":   matched_skills,
        "decision":         decision,
    }
