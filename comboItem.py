from enum import StrEnum

class ImageColormode(StrEnum):
    COLOR = "Color"
    GRAYSCALE = "Grayscale"

class ColorFormat(StrEnum):
    HSV_255     = "HSV(255)"
    HSV_360_255 = "HSV(360,255)"
    HSV_100     = "HSV(%)"
    HSV_360_100 = "HSV(360,%)"

    HLS_255     = "HLS(255)"
    HLS_360_255 = "HLS(360,255)"
    HLS_100     = "HLS(%)"
    HLS_360_100 = "HLS(360,%)"
    
    RGB_255     = "RGB(255)"
    RGB_100     = "RGB(%)"

def isFormatHSV(format):
    return format == ColorFormat.HSV_255 \
            or format == ColorFormat.HSV_360_255 \
            or format == ColorFormat.HSV_100 \
            or format == ColorFormat.HSV_360_100

def isFormatHLS(format):
    return format == ColorFormat.HLS_255 \
            or format == ColorFormat.HLS_360_255 \
            or format == ColorFormat.HLS_100 \
            or format == ColorFormat.HLS_360_100

def isFormatRGB(format):
    return format == ColorFormat.RGB_255 \
            or format == ColorFormat.RGB_100

class ColorListSize(StrEnum): # 右パネルは自動サイズ調整するので、全アイテム同じ幅が望ましい
    XS = " XS"
    S = "  S"
    M = "  M"
    L = "  L"
    XL = " XL"
    XXL = "XXL"