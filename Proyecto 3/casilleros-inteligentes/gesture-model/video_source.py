"""Fuentes de video reutilizables: stream MJPEG de la ESP32-CAM o webcam local.

Compartido por recognize_stream.py y collect_keypoints.py.
"""
import time

import cv2
import numpy as np
import requests


class MJPEGStream:
    """Lector resiliente de un stream MJPEG (multipart/x-mixed-replace).

    El enlace WiFi de la ESP32-CAM puede ser inestable (cortes, timeouts). Si la
    conexion se cae, reconecta automaticamente en vez de morir.
    """
    def __init__(self, url):
        self.url = url
        self.buf = b""
        self._connect()

    def _connect(self):
        self.r = requests.get(self.url, stream=True, timeout=8)
        self.it = self.r.iter_content(chunk_size=4096)
        self.buf = b""

    def read(self):
        for _attempt in range(4):
            try:
                while True:
                    a = self.buf.find(b"\xff\xd8")
                    b = self.buf.find(b"\xff\xd9")
                    if a != -1 and b != -1 and b > a:
                        jpg = self.buf[a:b + 2]
                        self.buf = self.buf[b + 2:]
                        img = cv2.imdecode(np.frombuffer(jpg, np.uint8),
                                           cv2.IMREAD_COLOR)
                        if img is not None:
                            return True, img
                    self.buf += next(self.it)
            except (requests.exceptions.RequestException, StopIteration):
                print("[stream] corte, reconectando...")
                try:
                    self.r.close()
                except Exception:
                    pass
                try:
                    self._connect()
                except Exception:
                    time.sleep(1)
        return False, None

    def release(self):
        try:
            self.r.close()
        except Exception:
            pass


class Webcam:
    def __init__(self, index=0):
        self.cap = cv2.VideoCapture(index)

    def read(self):
        return self.cap.read()

    def release(self):
        self.cap.release()


def open_source(source, stream_url):
    """source: 'webcam' o 'mjpeg'. Devuelve (kind, objeto-con-.read()/.release())."""
    if source == "webcam":
        return "webcam", Webcam(0)
    return "mjpeg", MJPEGStream(stream_url)
