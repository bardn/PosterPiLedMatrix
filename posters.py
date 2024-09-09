import requests
import json
from PIL import Image
from io import BytesIO
import time
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from threading import Lock

# Load configuration from file
config_file_path = 'config.json'

with open(config_file_path) as config_file:
    config = json.load(config_file)

client_id = config['client_id']
tmdb_api_key = config['tmdb_api_key']
trakt_username = config['trakt_username']

headers = {
    'Content-Type': 'application/json',
    'trakt-api-key': client_id,
    'trakt-api-version': '2',
}

previous_poster_url = None
matrix = None
fill_image = True  # Toggle to allow image to fill matrix
zoom_percentage = 8  # Zoom level as a percentage (e.g., 10 means zoom in by 10%)
offset_pixels = -10  # Offset in pixels (e.g., 10 means offset by 10 pixels)

# Create a lock for the matrix
matrix_lock = Lock()

def setup_matrix():
    global matrix
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'adafruit-hat'
    options.brightness = 80
    options.gpio_slowdown = 4
    matrix = RGBMatrix(options=options)

def fetch_currently_watching():
    watching_url = f'https://api.trakt.tv/users/{trakt_username}/watching'
    try:
        response = requests.get(watching_url, headers=headers)
        response.raise_for_status()
        return response.json() if response.status_code == 200 else None
    except requests.RequestException as e:
        print(f"Request Exception: {e}")
        return None

def fetch_poster_from_tmdb(tmdb_id, is_movie=True, season_number=None):
    base_url = 'https://api.themoviedb.org/3'
    endpoint = f"/{'movie' if is_movie else 'tv'}/{tmdb_id}"
    if not is_movie and season_number:
        endpoint += f"/season/{season_number}"
    tmdb_url = f"{base_url}{endpoint}?api_key={tmdb_api_key}"
    try:
        response = requests.get(tmdb_url)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return f'https://image.tmdb.org/t/p/original{poster_path}'
    except requests.RequestException as e:
        print(f"Request Exception: {e}")
        return None

def resize_image(image, target_size, fill_matrix=True, zoom_percentage=0, offset_pixels=0):
    img_width, img_height = image.size
    target_width, target_height = target_size

    # Calculate aspect ratios
    img_aspect = img_width / img_height
    target_aspect = target_width / target_height

    if fill_matrix:
        # Resize to fill width and crop height with optional zoom
        if img_aspect < target_aspect:
            new_width = target_width
            new_height = int(new_width / img_aspect)
        else:
            new_height = target_height
            new_width = int(new_height * img_aspect)

        if zoom_percentage > 0:
            new_width = int(new_width * (1 + zoom_percentage / 100))
            new_height = int(new_height * (1 + zoom_percentage / 100))

        img = image.resize((new_width, new_height), Image.LANCZOS)

        # Calculate offset
        top = (new_height - target_height) // 2 + offset_pixels
        top = max(top, 0)  # Ensure top is not negative
        img = img.crop((0, top, target_width, top + target_height))
    else:
        # Resize to fit within target dimensions
        if img_aspect > target_aspect:
            new_width = target_width
            new_height = int(new_width / img_aspect)
        else:
            new_height = target_height
            new_width = int(new_height * img_aspect)

        img = image.resize((new_width, new_height), Image.LANCZOS)

        # Center the image on a blank background
        background = Image.new('RGB', target_size, (0, 0, 0))
        paste_x = (target_width - new_width) // 2
        paste_y = (target_height - new_height) // 2
        background.paste(img, (paste_x, paste_y))
        img = background

    return img

def display_poster(poster_url):
    global previous_poster_url, matrix, fill_image, zoom_percentage, offset_pixels

    if poster_url and poster_url != previous_poster_url:
        try:
            image_response = requests.get(poster_url)
            image_response.raise_for_status()
            img = Image.open(BytesIO(image_response.content))

            # Resize image based on the toggle
            img = resize_image(img, (matrix.width, matrix.height), fill_image, zoom_percentage, offset_pixels)
            img = img.convert('RGB')

            # Lock the matrix for display
            with matrix_lock:
                # Clear the canvas before updating
                matrix.Clear()
                print("Canvas cleared")

                # Update display with image
                matrix.SetImage(img)
                print("Image displayed")

            previous_poster_url = poster_url
        except requests.RequestException as e:
            print(f"Request Exception: {e}")
        except Exception as e:
            print(f"Exception: {e}")

def display_watching_info(watching_data):
    if isinstance(watching_data, dict):
        media_type = watching_data.get('type')
        if media_type == 'movie':
            movie_id = watching_data.get('movie', {}).get('ids', {}).get('tmdb')
            if movie_id:
                poster_url = fetch_poster_from_tmdb(movie_id, is_movie=True)
                if poster_url:
                    display_poster(poster_url)
        elif media_type == 'episode':
            episode = watching_data.get('episode')
            show_id = watching_data.get('show', {}).get('ids', {}).get('tmdb')
            if episode and show_id:
                season_number = episode.get('season')
                if season_number:
                    poster_url = fetch_poster_from_tmdb(show_id, is_movie=False, season_number=season_number)
                    if poster_url:
                        display_poster(poster_url)

def main():
    global previous_poster_url
    setup_matrix()
    while True:
        watching_data = fetch_currently_watching()
        if watching_data:
            display_watching_info(watching_data)
        time.sleep(5)  # Check every 5 seconds

if __name__ == '__main__':
    main()
