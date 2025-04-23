import functools
import typing

from helpers.audio import Audio

T = typing.TypeVar("T")


def with_api_key(
    api_key_func: typing.Callable[[], str],
) -> typing.Callable[[typing.Callable[..., T]], typing.Callable[..., T]]:
    """
    Decorator for static class methods that handles API key authentication.
    If the wrapped function raises an exception with a 401 status code,
    it will get a new API key from the provided function and retry the call.

    Args:
        api_key_func: Function that returns an API key

    Returns:
        The decorated function that handles API key authentication
    """

    def decorator(func: typing.Callable[..., T]) -> typing.Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: typing.Any, **kwargs: typing.Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if hasattr(e, "status_code") and getattr(e, "status_code", None) == 401:
                    new_api_key = api_key_func()
                    kwargs["api_key"] = new_api_key
                    return func(*args, **kwargs)
                else:
                    raise

        return wrapper

    return decorator


def capture_response(
    func: typing.Callable[..., typing.Any],
) -> typing.Callable[..., typing.Optional[str]]:
    """
    Decorator for static class methods that captures the response, prints it to console,
    and always returns a string.
    If 'audio' parameter exists in the function signature, it will be used; otherwise, it defaults to False.

    Args:
        func: The static method to be decorated

    Returns:
        The wrapped function that captures, prints the response, and returns it as a string
    """

    @functools.wraps(func)
    def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Optional[str]:
        if "audio" not in kwargs:
            kwargs["audio"] = False

        is_audio = kwargs["audio"]

        try:
            response = func(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e}")

            return None

        str_response = str(response) if response is not None else ""

        if is_audio:
            Audio.text_to_speech(str_response)
        else:
            print(str_response)

        return str_response

    return wrapper
