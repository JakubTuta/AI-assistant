import functools
import os
import typing

import requests

from helpers.audio import Audio

T = typing.TypeVar("T")


def exit_on_exception(func: typing.Callable[..., T]) -> typing.Callable[..., T]:
    """
    Decorator that captures all exceptions, prints them with class name and exits the program.
    Works for both static and instance methods of classes.

    Args:
        func: The method to be decorated

    Returns:
        The wrapped function that handles exceptions and exits on error
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            class_name = args[0].__class__.__name__ if args else "Unknown"
            print(f"\n[{class_name}]: {e}")

            os._exit(1)

    return wrapper


def retry_on_unauthorized(refresh_token_method_name: str):
    """
    Decorator that retries the function if a 401 or 403 error occurs.
    It will call the refresh token method before retrying the function.

    Args:
        refresh_token_method_name: The name of the method to call for refreshing the token

    Returns:
        A decorator that wraps the function and handles the retry logic
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)

            except requests.exceptions.RequestException as e:
                if hasattr(e, "response") and (
                    getattr(e.response, "status_code", None) == 401
                    or getattr(e.response, "status_code", None) == 403
                ):
                    refresh_method = getattr(self, refresh_token_method_name)
                    refresh_method(self.refresh_token)

                    return func(self, *args, **kwargs)

                elif hasattr(e, "response") and getattr(
                    e.response, "status_code", None
                ) not in range(200, 300):
                    print(f"\nError in {func.__name__}: {e}")

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
            class_name = args[0].__class__.__name__ if args else "Unknown"
            print(f"\n[{class_name}]: {e}")

            return None

        str_response = str(response) if response is not None else ""

        if is_audio:
            Audio.text_to_speech(str_response)
        else:
            print(str_response)

        return str_response

    return wrapper


def capture_exception(
    func: typing.Callable[..., T],
) -> typing.Callable[..., typing.Optional[T]]:
    """
    Decorator that captures all exceptions and prints them as "[class name]: exception".
    Works for both static and instance methods of classes.

    Args:
        func: The method to be decorated

    Returns:
        The wrapped function that handles exceptions and returns None on error
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> typing.Optional[T]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            class_name = args[0].__class__.__name__ if args else "Unknown"
            print(f"\n[{class_name}]: {e}")
            return None

    return wrapper
