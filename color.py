import colorsys

class Color:

    def __init__(self):
        self.rgb = (0.0, 0.0, 0.0)
        self.rgba = (0.0, 0.0, 0.0, 1.0)
        self.hsv = (0.0, 0.0, 0.0)
        self.hls = (0.0, 0.0, 0.0)
        self.hex = "000000"
        self.luma = 0.0

    def set_rgb(self, rgb):
        """色をRGB形式でセットする

        Args:
            rgb(tuple(float)): RGB値、0~1の範囲
        """
        self.rgb = rgb
        self.rgba = (*rgb, 1.0)
        self.hsv = colorsys.rgb_to_hsv(*rgb)
        self.hls = colorsys.rgb_to_hls(*rgb)
        self.hex = "{:02x}{:02x}{:02x}".format(*map(lambda v: round(v*255), rgb)).upper()
        # ITU-R 601-2 luma
        self.luma = rgb[0] * 255 * 299/1000 + rgb[1] * 255 * 587/1000 + rgb[2] * 255 * 114/1000

    def get_value(self, target, max):
        """最大値を指定して各値を取得する
        
        単純に各値をround(value * max)するだけ。HSV(360, 100, 100)のような特殊ケースにはget_value_h_others()を使用せよ

        Args:
            target(str): 対象。rgb, rgba, hsv, hls。
            max(int): 最大値。255なり100なり

        Returns:
            tuple[int, int, int]: 結果。

        Raises:
            ValueError: target値が想定外の場合
        """

        match target:
            case "rgb":
                return tuple(map(lambda v: round(v * max), self.rgb))
            case "rgba":
                return tuple(map(lambda v: round(v * max), self.rgba))
            case "hsv":
                return tuple(map(lambda v: round(v * max), self.hsv))
            case "hls":
                return tuple(map(lambda v: round(v * max), self.hls))
            case _:
                raise ValueError(f"\"target\" must be one of rgb, rgba, or hsv: {target}")


    def get_value_h_others(self, target, h_max, others_max):
        """最大値を指定して各値を取得する
                
        HSV(360, 100, 100)のような特殊ケース用

        Args:
            target(str): 対象。hsv, hls。
            h_max(int): 最大値。360なり100なり。色相にのみ適用
            others_max(int): 色相以外の最大値。255なり100なり

        Returns:
            tuple[int, int, int]: 結果。

        Raises:
            ValueError: target値が想定外の場合
        """

        match target:
            case "hsv":
                return (round(self.hsv[0] * h_max), *map(lambda v: round(v * others_max), self.hsv[1:]))
            case "hls":
                return (round(self.hls[0] * h_max), *map(lambda v: round(v * others_max), self.hls[1:]))
            case _:
                raise ValueError(f"\"target\" must be hsv or hls: {target}")
