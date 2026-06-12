"""CSS selectors for scraping play.limitlesstcg.com.

These are best-guess placeholders based on common patterns and have not yet
been verified against a live, authenticated page. Once a real session is
available, capture the actual HTML for the org settings and resubmit pages
and update these selectors accordingly.
"""

ORG_SETTINGS_PATH = "/account/settings/orgs"
APPLY_PATH = "/user/apply"
LOGIN_PATH = "/login"

# Element containing the current organization application status text.
APPLICATION_STATUS_SELECTOR = ".application-status"

# Login form (password-based, as opposed to the Discord OAuth button).
LOGIN_USERNAME_SELECTOR = ".login-form input[name='username']"
LOGIN_PASSWORD_SELECTOR = ".login-form input[name='password']"
LOGIN_SUBMIT_SELECTOR = ".login-form button[type='submit']"

# Button/link that resubmits the organization application.
RESUBMIT_BUTTON_SELECTOR = "button.resubmit, a.resubmit"

# Element containing the outcome message after a resubmit action.
RESUBMIT_RESULT_SELECTOR = ".resubmit-result"
