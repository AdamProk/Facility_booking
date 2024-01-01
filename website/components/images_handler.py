import os

ON_SERVER = bool(os.environ.get("ON_SERVER", None))
ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
IMAGES_DIR = os.path.join(ROOT_DIR, "static", "images")

