import functools


def require_docstring(func):
    """
    Decorator that checks if a function or method has a docstring.
    Raises a ValueError if the docstring is missing or empty.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not func.getdoc() or func.getdoc().strip() == "":
            raise ValueError(f"Function {func.__name__} must have a docstring")
        return func(*args, **kwargs)

    return wrapper
