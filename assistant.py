import typing

import dotenv

import servers.button as button_server
from helpers.cache import Cache
from helpers.logger import logger
from modules.employer import Employer

dotenv.load_dotenv()


def load_config() -> typing.Dict[str, typing.Any]:
    """
    Loads the configuration for the AI assistant.
    """
    config = {
        "audio": True,
        "local": False,
        "run_server": False,
        "run_button_server": True,
    }

    logger.log_system_event("configuration_loaded", f"Config: {config}")

    return config


def set_config(config: typing.Dict[str, typing.Any]) -> None:
    """
    Sets the configuration values in the cache.
    """
    Cache.load_values()
    Cache.set_audio(config["audio"])
    Cache.set_local(config["local"])
    Cache.set_server(config["run_server"])
    Cache.set_button_server(config["run_button_server"])

    logger.log_system_event("cache_updated", "Cache values updated based on new config")


def start_server(employer: Employer) -> None:
    """
    Starts the API and button servers based on the provided configuration.
    """
    print("Starting button server...")
    button_server.start_app(employer_instance=employer)


def main() -> None:
    """
    Main function to run the AI assistant.
    """
    print("\nStarting program...")

    logger.log_system_event("application_startup", "AI Assistant starting up")

    config = load_config()
    set_config(config)

    employer = Employer()
    logger.log_system_event("employer_initialized", "Employer instance created")

    start_server(employer)


if __name__ == "__main__":
    main()
