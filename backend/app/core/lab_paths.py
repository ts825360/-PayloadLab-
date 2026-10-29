"""Resolve protected routes relative to the mounted ASGI application's root."""
import re


def relative_path(scope):
    path = scope.get('path', '')
    root = scope.get('root_path', '').rstrip('/')
    # Some ASGI servers include root_path in path; others already strip it.
    # Only remove an exact path-segment prefix, never /api from /api2.
    if root and path.startswith(root + '/'):
        path = path[len(root):]
    elif root and path == root:
        path = '/'
    return path


def lab_route(scope):
    return re.fullmatch(r'/labs/([^/]+)/(analyze|attempt|render)/?', relative_path(scope))
