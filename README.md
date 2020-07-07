# Django Magic Link

Opinionated Django app for managing "magic link" logins.

**WARNING**

If you send a login link to the wrong person, they will gain full access to the user's account. Use
with extreme caution, and do not use this package without reading the source code and ensuring that
you are comfortable with it. If you have an internal security team, ask them to look at it before
using it. If your clients have security sign-off on your application, ask them to look at it before
using it.

**/WARNING**

This app is not intended for general purpose URL tokenisation; it is designed to support a single
use case - so-called "magic link" logins.

There are lots of alternative apps that can support this use case, including the project from which
this has been extracted -
[`django-request-token`](https://github.com/yunojuno/django-request-token). The reason for yet
another one is to handle the real-world challenge of URL caching / pre-fetch, where intermediaries
use URLs with unintended consequences.

This packages supports a very specific model:

1. User is sent a link to log them in automatically.
2. User clicks on the link, and which does a GET request to the URL.
3. User is presented with a confirmation page, but is _not_ logged in.
4. User clicks on a button and performs a POST to the same page.
5. The POST request authenticates the user, and deactivates the token.

The advantage of this is the email clients do not support POST links, and any prefetch that attempts
a POST will fail the CSRF checks.

The purpose is to ensure that someone actively, purposefully, clicked on a link to authenticate
themselves. This enables instant deactivation of the token, so that it can no longer be used.

In practice, without this check, valid magic links may be requested a number of times via GET
request before the intended recipient even sees the link. If you use a "max uses" restriction to
lock down the link you may find this limit is hit, and the end user then finds that the link is
inactive. The alternative to this is to remove the use limit and rely instead on an expiry window.
This risks leaving the token active even after the user has logged in. This package is targeted at
this situation.

## Use

### Prerequisite: Override the default templates.

This package has two HTML templates that must be overridden in your local application.

**logmein.html**

This is the landing page that a user sees when they click on the magic link. You can add any content
you like to this page - the only requirement is that must contains a simple form with a csrf token
and a submit button. This form must POST back to the link URL. The template render context includes
the `link` which has a `get_absolute_url` method to simplify this:

```html
<form method="POST" action="{{ link.get_absolute_url }}>
    {% csrf_token %}
    <button type="submit">Log me in</button>
</form>
```

**error.html**

If the link has expired, been used, or is being accessed by someone who is already logged in, then
the `error.html` template will be rendered. The template context includes `link` and `error`.

```html
<p>Error handling magic link {{ link }}: {{ error }}.</p>
```

### 1. Create a new login link

The first step in managing magic links is to create one. Links are bound to a user, and can have a
custom expiry and post-login redirect URL.

```python
# create a link with the default expiry and redirect
link = MagicLink.objects.create(user=user)

# create a link with a specific redirect
link = MagicLink.objects.create(user=user, redirect_to="/foo")

# create a link with a specific expiry (in seconds)
link = MagicLink.objects.create(user=user, expiry=60)
```

### 3. Send the link to the user

This package does not handle the sending on your behalf - it is your responsibility to ensure that
you send the link to the correct user. If you send the link to the wrong user, they will have full
access to the link user's account. **YOU HAVE BEEN WARNED**.

## Auditing

A core requirement of this package is to be able to audit the use of links - for monitoring and
analysis. To enable this we have a second model, `MagicLinkUse`, and we create a new object for
every request to a link URL, _regardless of outcome_. Questions that we want to have answers for
include:

-   How long does it take for users to click on a link?
-   How many times is a link used before the POST login?
-   How often is a link used _after_ a successful login?
-   How often does a link expire before a successful login?
-   Can we identify common non-user client requests (email caches, bots, etc)?
-   Should we disable links after X non-POST requests?

In order to facilitate this analysis we denormalise a number of timestamps from the `MagicLinkUse`
object back onto the `MagicLink` itself:

-   `created_at` - when the record was created in the database
-   `accessed_at` - the first GET request to the link URL
-   `logged_in_at` - the successful POST
-   `expires_at` - the link expiry, set when the link is created.

Note that the expiry timestamp is **not** updated when the link is used. This is by design, to
retain the original expiry timestamp.

### Link validation

In addition to the timestamp fields, there is a separate boolean flag, `is_active`. This acts as a
"kill switch" that overrides any other attribute, and it allows a link to be disabled without having
to edit (or destroy) existing timestamp values. You can deactivate all links in one hit by calling
`MagicLink.objects.deactivate()`.

A link's `is_valid` property combines both `is_active` and timestamp data to return a bool value
that defines whether a link can used, based on the following criteria:

1. The link is active (`is_active`)
2. The link has not expired (`expires_at`)
3. The link has not already been used (`logged_in_at`)

In addition to checking the property `is_valid`, the `validate()` method will raise an exception
based on the specific condition that failed. This is used by the link view to give feedback to the
user on the nature of the failure.

### Request authorization

If the link's `is_valid` property returns `True`, then the link _can_ be used. However, this does
not mean that the link can be used by anyone. We do not allow authenticated users to login using
someone else's magic link. The `authorize()` method takes a `User` argument and determines whether
they are authorized to use the link. If the user is authenticated, and does not match the
`link.user`, then a `PermissionDenied` exception is raised.

### Putting it together

Combining the validation, authorization and auditing, we get a simplified flow that looks something
like this:

```python
def get(request, token):
    """Render login page."""
    link = get_object_or_404(MagicLink, token=token)
    link.validate()
    link.authorize(request.user)
    link.audit()
    return render("logmein.html")

def post(request, token):
    """Handle the login POST."""
    link = get_object_or_404(MagicLink, token=token)
    link.validate()
    link.authorize(request.user)
    link.login(request)
    link.disable()
    return redirect(link.redirect_to)
```

## Settings

Settings are read from the environment first, then Django settings.

-   `MAGIC_LINK_DEFAULT_EXPIRY`: the default link expiry, in seconds (defaults to 60 - 1 minute).

-   `MAGIC_LINK_DEFAULT_REDIRECT`: the default redirect URL (defaults to "/").

-   `MAGIC_LINK_AUTHORIZATION_BACKEND`: the preferred authorization backend to use, in the case
    where you have more than one specified in the `settings.AUTHORIZATION_BACKENDS` setting.
    Defaults to `django.contrib.auth.backends.ModelBackend`.

## Screenshots

**Default landing page (`logmein.html`)**

<img src="https://raw.githubusercontent.com/yunojuno/django-magic-link/master/screenshots/landing-page.png" width=600 alt="Screenshot of default landing page" />

**Default error page (`error.html`)**

<img src="https://raw.githubusercontent.com/yunojuno/django-magic-link/master/screenshots/error-page.png" width=600 alt="Screenshot of default error page" />

**Admin view of magic link uses**

<img src="https://raw.githubusercontent.com/yunojuno/django-magic-link/master/screenshots/admin-inline.png" width=600 alt="Screenshot of MagicLinkUseInline" />
