from django.contrib.auth.backends import ModelBackend


class TestAuthBackend(ModelBackend):
    """
    Authentication backend used for testing.

    This backend does nothing different from the standard model
    backend, but it exists so that we can have multiple backends
    in the test config. An early bug was caused by having only a
    single backend in testing, but multiple backends in a client
    app, which caused the call to login to fail.

    See https://github.com/django/django/blob/3.0.8/django/contrib/auth/__init__.py#L112-L120

    """
