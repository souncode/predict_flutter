
from threading import Lock

cams = []
clients = set()
models = []
cams_lock = Lock()
camera_configs = []
issaveimage = False
save_path = "images"
