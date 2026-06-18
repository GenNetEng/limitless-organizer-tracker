"""CSS selectors for scraping play.limitlesstcg.com.

The application page (FR2) has been verified against a live, authenticated
session: it lives at `/user/application/<application_id>` and the status
text is rendered in `.organizer-application .status .code` as
"Status: <span class='bold'>{word}</span>". Only the "pending" wording has
been observed live; "approved"/"rejected"/"expired" are best-guess based on
the same structure (see fixtures in tests/fixtures/html). If a real status
doesn't match one of the known keywords, `parse_status_html` falls back to
UNKNOWN and preserves the raw text for manual reading.

The resubmit flow (FR3) has also been verified against the live page: the
application page renders all three "steps" of the resubmit wizard in a
single DOM (`.page1` form, `.page2` confirmation questions, `.page3` success
message), with `.page2`/`.page3` hidden via inline `display: none` until
revealed. Clicking `.page1 button.continue` is a pure client-side reveal of
`.page2` (the data is already present, no network request); clicking
`.page2 button.submit` is the actual resubmit action and the only step with
a real server-side side effect, so it was NOT exercised live. The
success-path result (`.page3` becoming visible with class `success`) is
verified structurally; the failure-path structure (an error rendered in
`.response`) is best-guess, following the same UNKNOWN-fallback pattern as
FR2's unverified non-pending statuses.
"""

# Path template for an organizer's application page; format with
# `application_id=settings.limitless_application_id`.
APPLICATION_PATH_TEMPLATE = "/user/application/{application_id}"

APPLY_PATH = "/user/apply"
LOGIN_PATH = "/login"

# Element containing the current organization application status text.
APPLICATION_STATUS_SELECTOR = ".organizer-application .status .code"

# Login form (password-based, as opposed to the Discord OAuth button).
LOGIN_USERNAME_SELECTOR = ".login-form input[name='username']"
LOGIN_PASSWORD_SELECTOR = ".login-form input[name='password']"
LOGIN_SUBMIT_SELECTOR = ".login-form button[type='submit']"

# Button that reveals the resubmit confirmation step (.page2); pure
# client-side toggle, no server-side effect.
RESUBMIT_CONTINUE_BUTTON_SELECTOR = ".page1 button.continue"

# Container revealed by Continue; waited on to confirm the JS transition
# completed before clicking the actual resubmit button.
RESUBMIT_PAGE2_SELECTOR = ".page2"

# Button that actually resubmits the organization application.
RESUBMIT_BUTTON_SELECTOR = ".page2 button.submit"

# Element shown on a successful resubmit (class "success" once visible).
RESUBMIT_RESULT_SELECTOR = ".page3"
