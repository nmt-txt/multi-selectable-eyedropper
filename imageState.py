from PIL import Image

image_color: Image
origin: str
res: tuple
is_origin_clipboard: bool
loaded = False

class ImageState:
    _zoom = 0

    def zoom_in(self):
        self._zoom += 1
        if self._zoom > 10:
            self._zoom = 10
    def zoom_out(self):
        self._zoom -= 1
        if self._zoom < 0:
            self._zoom = 0
    def get_zoom(self):
        """0~1
        """
        return self._zoom / 10
        
