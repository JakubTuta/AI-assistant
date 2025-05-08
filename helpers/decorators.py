import functools
import os
import typing

import requests

from helpers.audio import Audio
from helpers.cache import Cache

T = typing.TypeVar("T")


class JobRegistry:
    available_jobs = {}
    _services = {}
    _pending_registrations = []

    @classmethod
    def register_job(cls, name=None):
        """Decorator for static methods and functions."""
        # Check if we're being called with the function directly or with parameters
        if callable(name):
            # Used as @register_job without parentheses
            func = name
            job_name = func.__name__

            # Check if function has documentation
            if not func.__doc__:
                print(f"No documentation found for job '{job_name}'")
                os._exit(1)

            cls.available_jobs[job_name] = func
            return func

        # Otherwise, we're called with parameters as @register_job() or @register_job("name")
        def decorator(func):
            job_name = name or func.__name__

            # Check if function has documentation
            if not func.__doc__:
                print(f"No documentation found for job '{job_name}'")
                os._exit(1)

            # Wrap the function to ensure it handles arguments properly
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            cls.available_jobs[job_name] = wrapper
            return wrapper

        return decorator

    @classmethod
    def register_service(cls, service_name=None):
        """Decorator for service classes.
        If service_name is not provided, will use lowercase class name.
        """

        def decorator(service_class):
            # If service_name is not provided, use lowercase class name
            actual_service_name = service_name or service_class.__name__.lower()
            cls._services[actual_service_name] = service_class
            return service_class

        # Handle case when decorator is used without parentheses
        if callable(service_name):
            service_class = service_name
            service_name = None
            return decorator(service_class)

        return decorator

    @classmethod
    def register_method(cls, service_name=None, method_name=None, job_name=None):
        """Decorator for methods that should be registered as jobs.
        Required to use with classes that need instance methods.
        If service_name is not provided, will determine from class name.
        """

        def decorator(method):
            # Check if method has documentation
            if not method.__doc__:
                method_display_name = (
                    method.__qualname__
                    if hasattr(method, "__qualname__")
                    else method.__name__
                )
                print(f"No documentation found for method '{method_display_name}'")
                os._exit(1)

            # Get the class from the method using __qualname__
            # This works even if the decorator is applied before the class is fully defined
            if service_name is None:
                # Extract class name from method.__qualname__ which is typically 'ClassName.method_name'
                class_name = method.__qualname__.split(".")[0].lower()
                actual_service_name = class_name
            else:
                actual_service_name = service_name

            cls._pending_registrations.append(
                {
                    "service": actual_service_name,
                    "method": method_name or method.__name__,
                    "job": job_name or method.__name__,
                }
            )
            return method

        # Handle case when decorator is used without parentheses
        if callable(service_name):
            method = service_name
            service_name = None
            return decorator(method)

        return decorator


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
            function_name = func.__name__ if hasattr(func, "__name__") else "Unknown"
            print(f"\n[{class_name} - {function_name}]: {e}")

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
                    class_name = args[0].__class__.__name__ if args else "Unknown"
                    function_name = (
                        func.__name__ if hasattr(func, "__name__") else "Unknown"
                    )
                    print(f"\n[{class_name} - {function_name}]: {e}")

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
    def wrapper(*args, **kwargs) -> typing.Optional[str]:
        try:
            response = func(*args, **kwargs)

        except Exception as e:
            class_name = args[0].__class__.__name__ if args else "Unknown"
            function_name = func.__name__ if hasattr(func, "__name__") else "Unknown"
            print(f"\n[{class_name} - {function_name}]: {e}")

            return

        str_response = str(response) if response is not None else ""

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech(str_response)
        print(str_response)

        return str_response

    return wrapper


def capture_exception(
    func: typing.Callable[..., T],
) -> typing.Callable[..., typing.Union[T, str]]:
    """
    Decorator that captures all exceptions and returns them as "[class name]: exception".
    Works for both static and instance methods of classes.

    Args:
        func: The method to be decorated

    Returns:
        The wrapped function that handles exceptions and returns error message on exception
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> typing.Union[T, str]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            class_name = args[0].__class__.__name__ if args else "Unknown"
            function_name = func.__name__ if hasattr(func, "__name__") else "Unknown"

            error_message = f"\n[{class_name} - {function_name}]: {e}"
            print(error_message)

            return error_message

    return wrapper
