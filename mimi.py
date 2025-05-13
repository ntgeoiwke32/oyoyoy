from seleniumbase import SB
import time
import requests
import sys
import requests
import os
import random
import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Resolution:
    width: int
    height: int
    bits_per_pixel: Optional[int] = None

def get_random_resolution(bits_per_pixel_options: List[int] = [16, 24, 32]) -> Resolution:
    """
    Generate a random screen resolution with random variations.
    
    Args:
        bits_per_pixel_options (List[int]): List of possible color depths. Defaults to [16, 24, 32].
        
    Returns:
        Resolution: A Resolution object containing width, height, and bits per pixel.
    """
    # 1) Define base resolutions up to 4K
    base_resolutions = [
        Resolution(1280, 800),   # WXGA
        Resolution(1366, 768),   # HD+
    ]
    
    # 2) Choose a random base resolution
    base = random.choice(base_resolutions)
    
    # 3) Choose a random bits-per-pixel
    bpp = random.choice(bits_per_pixel_options)
    
    # 4) Compute random offsets between -10% and +10%
    w_offset = random.randint(-10, 10) / 100.0
    h_offset = random.randint(-10, 10) / 100.0
    
    # 5) Apply offsets and round
    new_width = round(base.width * (1 + w_offset))
    new_height = round(base.height * (1 + h_offset))
    
    # 6) Return a Resolution object
    return Resolution(new_width, new_height, bpp)


def stop_warp():
    try:
        # Check WARP status
        status_result = subprocess.run(["warp-cli", "status"], capture_output=True, text=True)
        print("WARP Status:")
        print(status_result.stdout)
        # If WARP is connected, disconnect it
        if "Connected" in status_result.stdout:
            print("Stopping WARP...")
            disconnect_result = subprocess.run(["sudo", "warp-cli", "disconnect"], check=True)
            print("WARP stopped successfully.")
        else:
            print("WARP is not currently connected.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while stopping WARP: {e}")


def start_warp():
    try:
        # Check WARP status
        status_result = subprocess.run(["warp-cli", "status"], capture_output=True, text=True)
        print("WARP Status:")
        print(status_result.stdout)
        # Start WARP if not already connected
        if "Connected" not in status_result.stdout:
            print("Starting WARP...")
            subprocess.run(["sudo", "warp-cli", "--accept-tos", "connect"], check=True)
            print("WARP started successfully.")
        else:
            print("WARP is already connected.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while managing WARP: {e}")


def testtw():
    # Retrieve environment variables
    channel = os.getenv("CHANNEL")
    authorization = os.getenv("AUTHORIZATION")
    client_id = os.getenv("TCLIENTID")

    if not channel or not authorization or not client_id:
        print("Missing required environment variables: CHANNEL, AUTHORIZATION, or TCLIENTID.")
        return False

    # Set up the API request
    url = f"https://api.twitch.tv/helix/streams?user_login={channel}"
    headers = {
        "Authorization": f"Bearer {authorization}",
        "Client-Id": client_id
    }

    try:
        # Send the GET request to the Twitch API
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Check if the response contains "live"
        if "live" in response.text:
            return True
        else:
            return False

    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return False


def testkick():
    token_url = "https://id.kick.com/oauth/token"
    client_id = os.getenv("CLIENTID")  # Replace with your client ID
    client_secret = os.getenv("CLIENTSECRET")  # Replace with your client secret
    body = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    try:
        token_response = requests.post(token_url, data=body)
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        # print(f"Access Token: {access_token}")
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving token: {client_id} {client_secret} {e}")
        return False

    channel_slug = os.getenv("CHANNEL")  # Replace this with the channel's slug
    url = f"https://api.kick.com/public/v1/channels?slug={channel_slug}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json().get("data", [])
        for channel in data:
            slug = channel.get("slug")
            is_live = channel.get("stream", {}).get("is_live")
            if is_live is True:
                return True
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving channel data: {e}")
        return False

    return False

resolution = get_random_resolution()
start_warp()
with SB(uc=True, test=True) as sb:
    sb.set_window_size(resolution.width, resolution.height)
    timp = random.randint(25,36)
    start_time = time.time()
    duration = timp * 60
    while time.time() - start_time < duration:
        if testkick():
            channel = os.getenv("CHANNEL")
            url = f'https://kick.com/{channel}'
            sb.uc_open_with_reconnect(url, 5)
            sb.uc_gui_click_captcha()
            sb.sleep(2)
            sb.uc_gui_handle_captcha()
            sb.sleep(5)
            if sb.is_element_present('button:contains("Accept")'):
                sb.uc_click('button:contains("Accept")', reconnect_time=4)
            if sb.is_element_present('button:contains("I am 18+")'):
                sb.uc_click('button:contains("I am 18+")', reconnect_time=4)
            driver2 = sb.get_new_driver(undetectable=True)
            driver2.uc_open_with_reconnect(url, 5)
            driver2.uc_gui_click_captcha()
            sb.sleep(2)
            driver2.uc_gui_handle_captcha()
            sb.sleep(15)
            if driver2.is_element_present('button:contains("Accept")'):
                driver2.uc_click('button:contains("Accept")', reconnect_time=4)
            if driver2.is_element_present('button:contains("I am 18+")'):
                driver2.uc_click('button:contains("I am 18+")', reconnect_time=4)
            while testkick() and time.time() - start_time < duration:
                if testkick():
                    sb.sleep(120)
                else:
                    break
            sb.quit_extra_driver()
        if testtw():
            channel = os.getenv("CHANNEL")
            url = f'https://www.twitch.tv/{channel}'
            sb.uc_open_with_reconnect(url, 5)
            sb.uc_gui_click_captcha()
            sb.sleep(2)
            sb.uc_gui_handle_captcha()
            if sb.is_element_present('button:contains("Start Watching")'):
                sb.uc_click('button:contains("Start Watching")', reconnect_time=4)
            if sb.is_element_present('button:contains("Accept")'):
                sb.uc_click('button:contains("Accept")', reconnect_time=4)
            driver2 = sb.get_new_driver(undetectable=True)
            driver2.uc_open_with_reconnect(url, 5)
            driver2.uc_gui_click_captcha()
            sb.sleep(2)
            driver2.uc_gui_handle_captcha()
            sb.sleep(15)
            if driver2.is_element_present('button:contains("Start Watching")'):
                driver2.uc_click('button:contains("Start Watching")', reconnect_time=4)
            if driver2.is_element_present('button:contains("Accept")'):
                driver2.uc_click('button:contains("Accept")', reconnect_time=4)
            sb.sleep(5)
            while testtw() and time.time() - start_time < duration:
                if testtw():
                    sb.sleep(120)
                else:
                    break
            sb.quit_extra_driver()
        if not testtw() and not testkick() and time.time() - start_time < duration:
            rnd = random.randint(1,600)
            sb.sleep(rnd)
            # driver2 = sb.get_new_driver(undetectable=True, proxy="socks5://127.0.0.1:1081")
            channel = os.getenv("CHANNEL")
            url = f'https://www.youtube.com/@{channel}/videos'
            sb.uc_open_with_reconnect(url, reconnect_time=4)
            rnd = random.randint(1,60)
            sb.sleep(rnd)
            if sb.is_element_present('button:contains("Accept")'):
                sb.uc_click('button:contains("Accept")', reconnect_time=4)
            screen_rect = sb.get_screen_rect()
            screen_width = screen_rect["width"]
            screen_height = screen_rect["height"]
            window_rect = sb.get_window_rect()
            window_width = window_rect["width"]
            window_height = window_rect["height"]
            x_start = int(window_width * 0.2)  # 75% of window width
            x_end = window_width - 1  # Maximum width inside the window
            y_start = int(window_height * 0.7)  # 75% of window height
            y_end = screen_height - 1  # Maximum height inside the window
            random_x = random.randint(x_start, x_end)
            random_y = random.randint(y_start, y_end)
            sb.uc_gui_click_x_y(random_x, random_y, timeframe=0.25)
            sb.sleep(2)
            urlnow = sb.get_current_url()
            kkk = 0
            while url == urlnow:
                window_rect = sb.get_window_rect()
                window_width = window_rect["width"]
                window_height = window_rect["height"]
                x_start = int(window_width * 0.15)  # 75% of window width
                x_end = window_width - 1  # Maximum width inside the window
                y_start = int(window_height * 0.7)  # 75% of window height
                y_end = screen_height - 1  # Maximum height inside the window
                random_x = random.randint(x_start, x_end)
                random_y = random.randint(y_start, y_end)
                sb.uc_gui_click_x_y(random_x, random_y, timeframe=0.25)
                sb.sleep(3)
                urlnow = sb.get_current_url()
                kkk += 1
                if kkk >= 10:
                    break
            while not testtw() and not testkick() and time.time() - start_time < duration:
                sb.sleep(120)
        sb.sleep(60)
