"""
Stage 4 — LLM Resume Structuring (LLM #1)

Takes RAW resume text (plain text extracted from PDF/DOCX, before any
regex section-splitting) and asks Gemini to extract structured sections
directly: skills, education, experience, and projects (if present).

No scoring here — structuring only.
"""

from __future__ import annotations
from typing import Dict, List

from src.analysis.llm_client import generate_structured_json

RESUME_STRUCTURE_SCHEMA = {
    "type": "object",
    "properties": {
        "skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Standardized skill names extracted from the resume.",
        },
        "education": {
            "type": "array",
            "items": {"type": "string"},
            "description": "One entry per degree/qualification.",
        },
        "experience": {
            "type": "array",
            "items": {"type": "string"},
            "description": "One entry per role/position held.",
        },
        "projects": {
            "type": "array",
            "items": {"type": "string"},
            "description": "One entry per project. MUST be empty list if resume has no projects.",
        },
    },
    "required": ["skills", "education", "experience", "projects"],
}

_PROMPT_TEMPLATE = """You are extracting structured information from a resume's raw text.

Your job: read the resume text below and extract FOUR sections:
1. skills - individual skill/technology names (standardize casing and common \
abbreviations, e.g. "reactjs" -> "React", "js" -> "JavaScript")
2. education - one entry per degree/qualification (institution, degree, year if present)
3. experience - one entry per job/role held (title, company, duration, brief summary)
4. projects - one entry per project (name and brief description)

"- Each skill must be a SINGLE atomic concept, not a bundled phrase. "
"Split compound skills into separate entries (e.g. 'GDPR', 'HIPAA', 'PCI-DSS' "
"as three separate skills, not one combined string). Avoid parenthetical "
"expansions - use the common short form only (e.g. 'SIEM', not "
"'Security Information and Event Management (SIEM)')."

IMPORTANT - IDENTIFY BY MEANING, NOT BY HEADER WORDING:
Resumes use inconsistent section headers ("Academic Background" vs "Education" vs \
"Qualifications" vs no header at all). Do NOT rely on exact header text matching. \
Instead, read and understand the content itself. If a paragraph mentions a degree, \
university, or graduation year - even with no "Education" header, or under an \
unfamiliar header like "Academic Credentials" - treat it as an education entry. \
Apply the same contextual reasoning to skills, experience, and projects: identify \
them by what the content actually describes, not by what word introduces it.

CRITICAL RULES:
- Extract ONLY what is actually present or clearly implied in the text. Do NOT \
invent, assume, or fabricate information that isn't there in some form.
- If the resume has NO project section and NO project-like content anywhere, \
return an empty list for "projects". Do not force a project into existence.
- Do not score, rank, rate, or evaluate anything. Extraction only.
- Do not include duplicate entries.

Return JSON only, matching the schema exactly.

Resume text:
---
{raw_text}
---
"""


def structure_resume(raw_text: str) -> Dict[str, List[str]]:
    """
    Extracts structured sections from raw resume text via Gemini.
    Falls back to an all-empty structure if the LLM call fails
    (e.g. free-tier rate limit hit), so the pipeline never crashes —
    downstream stages should handle empty sections gracefully.
    """
    empty_result = {"skills": [], "education": [], "experience": [], "projects": []}

    if not raw_text or not raw_text.strip():
        return empty_result

    prompt = _PROMPT_TEMPLATE.format(raw_text=raw_text.strip())

    try:
        result = generate_structured_json(prompt, RESUME_STRUCTURE_SCHEMA)
        return {
            "skills": result.get("skills", []),
            "education": result.get("education", []),
            "experience": result.get("experience", []),
            "projects": result.get("projects", []),
        }
    except RuntimeError as e:
        print(f"[resume_structurer] LLM extraction failed: {e}")
        return empty_result


if __name__ == "__main__":
    sample_raw_text = """
    John Doe
    Email: john@example.com

    Academic Credentials
    B.Sc Computer Science, XYZ University, 2022

    Career History
    Software Engineer at ABC Corp (2022-2024)
    Built REST APIs using Python and Flask, worked with MySQL databases.

    Technical Toolkit
    Python, ReactJS, MySQL, Docker
    """
    import json
    result = structure_resume(sample_raw_text)
    print(json.dumps(result, indent=2))
