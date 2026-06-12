from dataclasses import dataclass

from bs4 import BeautifulSoup

from app.db.models import ApplicationStatus
from app.scraper.selectors import APPLICATION_STATUS_SELECTOR

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


def parse_status_html(html: str) -> ApplicationStatusResult:
    """Parse the organization application status from the settings page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    element = soup.select_one(APPLICATION_STATUS_SELECTOR)
    raw_text = element.get_text(strip=True) if element else ""

    lowered = raw_text.lower()
    for keyword, status in _STATUS_KEYWORDS:
        if keyword in lowered:
            return ApplicationStatusResult(status=status, raw_text=raw_text)

    return ApplicationStatusResult(status=ApplicationStatus.UNKNOWN, raw_text=raw_text)
