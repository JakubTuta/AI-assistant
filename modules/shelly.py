import requests

from helpers import decorators
from helpers.audio import Audio
from helpers.cache import Cache


class Shelly:
    _base_url = "http://192.168.18.53"

    @decorators.capture_response
    @decorators.JobRegistry.register_job
    @staticmethod
    def turn_light_on() -> str:
        """
        Controls a physical Shelly smart switch/relay device to turn ON a connected light fixture.
        This function sends a HTTP GET request to a specific Shelly device on the local network
        to activate relay 0, which controls the connected lighting circuit.

        Use this function when the user wants to:
        - Turn on lights in a room
        - Activate lighting via smart home control
        - Switch on electrical devices connected to the Shelly relay
        - Enable illumination through voice commands or automation

        Keywords: turn on light, light on, shelly on, turn light on, switch on light, enable light,
                 activate light, start light, power on light, illuminate, lighting on

        Returns:
            str: Success confirmation message or detailed error information about the light operation.
        """

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech("Turning light on...")
        print("Turning light on...")

        try:
            response = requests.get(f"{Shelly._base_url}/light/0/?turn=on")

            if response.status_code == 200:
                return "Light turned on successfully."
            else:
                return f"Error: Failed to turn on light. Status code: {response.status_code}"

        except requests.exceptions.RequestException as e:
            print(f"Error turning on light: {e}")
            return "Error: Could not connect to Shelly device to turn on the light."

    @decorators.capture_response
    @decorators.JobRegistry.register_job
    @staticmethod
    def turn_light_off() -> str:
        """
        Controls a physical Shelly smart switch/relay device to turn OFF a connected light fixture.
        This function sends a HTTP GET request to a specific Shelly device on the local network
        to deactivate relay 0, which controls the connected lighting circuit.

        Use this function when the user wants to:
        - Turn off lights in a room
        - Deactivate lighting via smart home control
        - Switch off electrical devices connected to the Shelly relay
        - Disable illumination through voice commands or automation
        - Save energy by turning off unnecessary lighting

        Keywords: turn off light, light off, shelly off, turn light off, switch off light, disable light,
                 deactivate light, stop light, power off light, darken, lighting off, extinguish

        Returns:
            str: Success confirmation message or detailed error information about the light operation.
        """

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech("Turning light off...")
        print("Turning light off...")

        try:
            response = requests.get(f"{Shelly._base_url}/light/0/?turn=off")

            if response.status_code == 200:
                return "Light turned off successfully."
            else:
                return f"Error: Failed to turn off light. Status code: {response.status_code}"

        except requests.exceptions.RequestException as e:
            print(f"Error turning off light: {e}")
            return "Error: Could not connect to Shelly device to turn off the light."
