import os
from werkzeug.utils import secure_filename

ON_SERVER = bool(os.environ.get("ON_SERVER", None))
ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
IMAGES_DIR = os.path.join(ROOT_DIR, "static", "images")
LOGO_DIR = os.path.join(ROOT_DIR, "static", "assets")


os.makedirs(IMAGES_DIR, exist_ok=True)


class ImageHandlerError(Exception):
    pass


def upload_image(file):
    if file.filename == "":
        raise ImageHandlerError("Filename is empty.")

    if not file:
        raise ImageHandlerError("No file.")

    filename = secure_filename(file.filename)
    path = os.path.join(IMAGES_DIR, filename)
    file.save(path)

    return filename


def remove_image(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        raise ImageHandlerError(f"An error occurred while removing the file: {e}")


def upload_logo(file):
    if file.filename == "":
        raise ImageHandlerError("Filename is empty.")

    if not file:
        raise ImageHandlerError("No file.")

    filename = "logo.png"
    path = os.path.join(LOGO_DIR, filename)
    file.save(path)

    return filename
