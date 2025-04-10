import functools
import typing

from helpers.audio import Audio

T = typing.TypeVar("T")


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
