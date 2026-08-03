from enum import StrEnum

class ImageColormode(StrEnum):
    COLOR = "Color"
    GRAYSCALE = "Grayscale"

class ColorFormat(StrEnum):
    HSV = "HSV"
    HLS = "HLS"
    RGB = "RGB"

class ColorListSize(StrEnum): # 右パネルは自動サイズ調整するので、全アイテム同じ幅が望ましい
    XS = " XS"
    S = "  S"
    M = "  M"
    L = "  L"
    XL = " XL"
    XXL = "XXL"