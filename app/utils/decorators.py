"""
Role-based access control (SDS Section 7 - Security Design, FR-1.4, NFR-2.2).

Every Flask route that requires a specific role is wrapped in this decorator,
which inspects the logged-in user's `role` attribute before executing the view.
"""
from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def roles_required(*roles):
    """Restrict a view to users whose `role` is in `roles`. Combine with @login_required."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator
