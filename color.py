import colorsys

class Color:

    def __init__(self):
        self.rgb = (0,0,0)
        self.rgba = (0,0,0,255)
        self.hsv = (0,0,0)
        self.hls = (0,0,0)
        self.hex = "000000"
        self.luma = 0

    def set_rgb(self, rgb):
        self.rgb = rgb
        self.rgba = (*rgb, 255)
        self.hsv = tuple(
            map(lambda v: round(255*v), colorsys.rgb_to_hsv(*list(map(lambda v: v/255, rgb))))
        )
        self.hls = tuple(
            map(lambda v: round(255*v), colorsys.rgb_to_hls(*list(map(lambda v: v/255, rgb))))
        )
        self.hex = "{:02x}{:02x}{:02x}".format(*rgb).upper()
        self.luma = rgb[0] * 299/1000 + rgb[1] * 587/1000 + rgb[2] * 114/1000
