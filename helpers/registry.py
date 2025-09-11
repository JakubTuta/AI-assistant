import os
import typing
from abc import ABC, abstractmethod

T = typing.TypeVar("T")


class ServiceRegistry:
    """Simplified registry for managing jobs and services."""

    _jobs: typing.Dict[str, typing.Callable] = {}
    _services: typing.Dict[str, typing.Any] = {}
    _service_instances: typing.Dict[str, typing.Any] = {}

    @classmethod
    def get_all_jobs(cls) -> typing.Dict[str, typing.Callable]:
        """Get all registered jobs."""
        return cls._jobs.copy()

    @classmethod
    def get_service_instance(cls, service_name: str) -> typing.Any:
        """Get instance of a registered service."""
        return cls._service_instances.get(service_name)

    @classmethod
    def register_job(
        cls, name_or_func: typing.Union[str, typing.Callable, None] = None
    ):
        """
        Decorator to register a standalone job function.

        Usage:
            @ServiceRegistry.register_job()
            def my_job():
                '''Job description here'''
                pass

            or

            @ServiceRegistry.register_job
            def my_job():
                '''Job description here'''
                pass
        """

        def decorator(func):
            job_name = name_or_func if isinstance(name_or_func, str) else func.__name__

            if not func.__doc__:
                raise ValueError(f"Job '{job_name}' must have documentation")

            cls._jobs[job_name] = func
            return func

        if callable(name_or_func):
            # Used as @register_job without parentheses
            return decorator(name_or_func)

        return decorator

    @classmethod
    def register_service(
        cls, service_class: type, env_vars: typing.Optional[typing.List[str]] = None
    ):
        """
        Register a service class with optional environment variable checks.

        Args:
            service_class: The service class to register
            env_vars: List of required environment variables
        """
        service_name = service_class.__name__.lower()

        # Check environment variables if specified
        if env_vars:
            missing_vars = [var for var in env_vars if not os.getenv(var)]
            if missing_vars:
                print(f"\n{'='*60}")
                print(f"{service_class.__name__.upper()} CREDENTIALS NOT SET UP")
                print("=" * 60)
                print(f"Missing environment variables: {', '.join(missing_vars)}")
                print(f"{service_class.__name__} services will not be available.")
                print("=" * 60 + "\n")
                return service_class

        # Store service class
        cls._services[service_name] = service_class

        # Create instance and register methods
        try:
            instance = service_class()
            cls._service_instances[service_name] = instance

            # Register all methods marked with @method_job
            for attr_name in dir(instance):
                attr = getattr(instance, attr_name)
                if hasattr(attr, "_is_job_method"):
                    job_name = getattr(attr, "_job_name", attr_name)
                    cls._jobs[job_name] = attr

        except Exception as e:
            print(f"Failed to initialize {service_class.__name__}: {e}")
            # Clean up partial registration
            cls._services.pop(service_name, None)
            cls._service_instances.pop(service_name, None)

        return service_class

    @classmethod
    def method_job(
        cls, name_or_method: typing.Union[str, typing.Callable, None] = None
    ):
        """
        Decorator to mark service methods as jobs.

        Usage:
            class MyService:
                @ServiceRegistry.method_job()
                def my_method(self):
                    '''Method description here'''
                    pass

                or

                @ServiceRegistry.method_job
                def my_method(self):
                    '''Method description here'''
                    pass
        """

        def decorator(method):
            method_name = (
                name_or_method if isinstance(name_or_method, str) else method.__name__
            )

            if not method.__doc__:
                raise ValueError(f"Method '{method_name}' must have documentation")

            method._is_job_method = True
            method._job_name = method_name
            return method

        if callable(name_or_method):
            # Used as @method_job without parentheses
            return decorator(name_or_method)

        return decorator


def service_with_env_check(*env_vars: str):
    """
    Decorator to register a service class with environment variable checks.

    Usage:
        @service_with_env_check('API_KEY', 'SECRET_KEY')
        class MyService:
            pass
    """

    def decorator(service_class):
        return ServiceRegistry.register_service(service_class, list(env_vars))

    return decorator


def simple_service(service_class):
    """
    Decorator to register a service class without environment checks.

    Usage:
        @simple_service
        class MyService:
            pass
    """
    return ServiceRegistry.register_service(service_class)


register_job = ServiceRegistry.register_job
method_job = ServiceRegistry.method_job
