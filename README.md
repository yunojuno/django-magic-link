# Django Magic Link

Opinionated Django app for managing "magic link" logins.

This app is not intended for general purpose URL tokenisation; rather it is designed to support a
single use case - so-called "magic link" logins.

There are lots of alternative apps that can support this use case, including the project from which
this has been extracted - `django-request-tokens`. The reason for yet another one is to handle the
real-world challenge of URL caching / pre-fetch, where intermediaries use URLs with unintended
consequences.

This packages supports a very specific model:

1. User is sent a URL to log them in.
2. User clicks on the link, and which does a GET request to the URL.
3. User is presented with a confirmation page, but is _not_ logged in.
4. User clicks on a button and performs a POST to the same page.
5. The POST request authenticates the user, and deactivates the token.

The advantage of this is the email clients do not support POST links, and any prefetch that attempts
a POST will fail the CSRF checks.

The purpose is to ensure that someone actively, purposefully, clicked on a link to authenticate
themselves. This enables instant deactivation of the token, so that it can no longer be used.

In practice, without this check, many tokenised authentication links are "used up" before the
intended recipient has clicked on the link.
