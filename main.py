import time

import machine
import network
import urequests

print("Starting...")


def connect_to_wifi(ssid, password):
    # Initialize the WiFi interface
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # Connect to the WiFi network
    print(f"Connecting to {ssid}...")
    wlan.connect(ssid, password)

    # Wait for connection with timeout
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print("Waiting for connection...")
        time.sleep(1)

    # Handle connection status
    if wlan.status() != 3:
        # 3 is success
        status = wlan.status()
        print(f"Connection failed with status {status}")
        # Common status codes:
        # 0: IDLE
        # 1: CONNECTING
        # -1: NO_AP_FOUND
        # -2: WRONG_PASSWORD
        # -3: CONNECTION_FAIL
        return False
    else:
        print("Connected!")
        ip = wlan.ifconfig()[0]
        print(f"IP address: {ip}")
        return True


ssid = "toya47689652"
password = "eb7sU36bMz"
connect_to_wifi(ssid, password)

INPUT_PINS = {
    "B": machine.Pin(9, machine.Pin.IN),
    "A": machine.Pin(10, machine.Pin.IN),
    "UP": machine.Pin(18, machine.Pin.IN),
    "LEFT": machine.Pin(19, machine.Pin.IN),
    "DOWN": machine.Pin(20, machine.Pin.IN),
    "RIGHT": machine.Pin(22, machine.Pin.IN),
}

prev_states = {key: 0 for key in INPUT_PINS}


# Track the last request time
last_request_time = 0
cooldown_period = 1  # 1 second cooldown


def scan_keypad():
    global prev_states, last_request_time

    current_time = time.time()

    # Check each pin
    for key, pin in INPUT_PINS.items():
        current_state = pin.value()
        # If button is pressed now (1) but wasn't before (0)
        if current_state == 1 and prev_states[key] == 0:
            print(f"Button {key} pressed")

            # Only send request if cooldown period has passed
            if current_time - last_request_time >= cooldown_period:
                try:
                    response = urequests.get(
                        f"http://192.168.18.51:5000/button-pressed/{key}/"
                    )
                    print(f"Response: {response.status_code}")
                    response.close()  # Important to free resources

                    # Update the last request time
                    last_request_time = current_time
                except Exception as e:
                    print(f"Request failed: {e}")
            else:
                print(f"Cooldown active, skipping request for {key}")

        # Update previous state
        prev_states[key] = current_state


while True:
    scan_keypad()
    time.sleep(0.25)
