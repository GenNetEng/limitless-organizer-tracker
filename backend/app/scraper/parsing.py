from dataclasses import dataclass

from bs4 import BeautifulSoup

from app.db.models import ApplicationStatus
from app.scraper.selectors import APPLICATION_STATUS_SELECTOR, REVIEW_NOTE_SELECTOR, RESUBMIT_RESULT_SELECTOR

# Order matters: more specific terms are checked before "pending", which can
# appear as a substring of surrounding copy regardless of the actual status.
_STATUS_KEYWORDS: tuple[tuple[str, ApplicationStatus], ...] = (
    ("approved", ApplicationStatus.APPROVED),
    ("rejected", ApplicationStatus.REJECTED),
    ("expired", ApplicationStatus.EXPIRED),
    ("pending", ApplicationStatus.PENDING),
)

@dataclass(frozen=True)
class ApplicationStatusResult:
    status: ApplicationStatus
    raw_text: str
    review_note: str | None = None


def parse_status_html(html: str) -> ApplicationStatusResult:
    """Parse the organization application status from the settings page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    element = soup.select_one(APPLICATION_STATUS_SELECTOR)
    raw_text = element.get_text(strip=True) if element else ""

    note_element = soup.select_one(REVIEW_NOTE_SELECTOR)
    note_text = note_element.get_text(strip=True) if note_element else ""
    review_note = note_text if note_text else None

    lowered = raw_text.lower()
    for keyword, status in _STATUS_KEYWORDS:
        if keyword in lowered:
            return ApplicationStatusResult(status=status, raw_text=raw_text, review_note=review_note)

    return ApplicationStatusResult(status=ApplicationStatus.UNKNOWN, raw_text=raw_text, review_note=review_note)


def parse_resubmit_result(html: str) -> bool:
    """Parse whether a resubmit action succeeded from the resulting page HTML.

    A resubmit succeeds when `.page3` (hidden by default via inline
    `display: none`) has been revealed with its "success" class intact.
    Any other state (no `.page3`, or `.page3` still hidden) is a failure.
    """
    soup = BeautifulSoup(html, "html.parser")
    element = soup.select_one(RESUBMIT_RESULT_SELECTOR)
    if element is None:
        return False

    classes = element.get("class") or []
    style = element.get("style") or ""
    return "success" in classes and "display: none" not in style
