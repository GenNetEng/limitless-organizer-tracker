"""CSS selectors for scraping play.limitlesstcg.com.

The application page (FR2) has been verified against a live, authenticated
session: it lives at `/user/application/<application_id>` and the status
text is rendered in `.organizer-application .status .code` as
"Status: <span class='bold'>{word}</span>". Only the "pending" wording has
been observed live; "approved"/"rejected"/"expired" are best-guess based on
the same structure (see fixtures in tests/fixtures/html). If a real status
doesn't match one of the known keywords, `parse_status_html` falls back to
UNKNOWN and preserves the raw text for manual reading.

The org settings / resubmit selectors below (FR3) are still best-guess
placeholders pending a live-credential verification pass.
"""

# Path template for an organizer's application page; format with
# `application_id=settings.limitless_application_id`.
APPLICATION_PATH_TEMPLATE = "/user/application/{application_id}"

ORG_SETTINGS_PATH = "/account/settings/orgs"
APPLY_PATH = "/user/apply"
LOGIN_PATH = "/login"

# Element containing the current organization application status text.
APPLICATION_STATUS_SELECTOR = ".organizer-application .status .code"

# Login form (password-based, as opposed to the Discord OAuth button).
LOGIN_USERNAME_SELECTOR = ".login-form input[name='username']"
LOGIN_PASSWORD_SELECTOR = ".login-form input[name='password']"
LOGIN_SUBMIT_SELECTOR = ".login-form button[type='submit']"

# Button/link that resubmits the organization application.
RESUBMIT_BUTTON_SELECTOR = "button.resubmit, a.resubmit"

# Element containing the outcome message after a resubmit action.
RESUBMIT_RESULT_SELECTOR = ".resubmit-result"
