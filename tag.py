# Python 3.11 or later
from enum import auto, StrEnum 

class TagItem(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, last, count):
        return f"ITEM_{name.lower()}"
    
    TEXT_LOAD_STAT = auto()
    TEXT_LOADED_IMAGE_DETAIL = auto()
    IMAGE_IMAGE = auto()
    IMAGE_DRAWLIST = auto()
    TABLE_WINDOWPANE = auto()
    COMBO_IMAGE_COLORMODE = auto()
    COMBO_COLORFORMAT = auto()
    COMBO_COLORLIST_SIZE = auto()
    CHKBOX_COLORLIST_SELECT_ = auto() # 末尾にindexを付加すること
    INPUT_MANUAL_X = auto()
    INPUT_MANUAL_Y = auto()
    TABLE_LIST_COLUMN = auto()

class TagTexture(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, last, count):
        return f"TEXTURE_{name.lower()}"
    
    IMAGE = auto()
    GRAYSCALE = auto()
    COLORCIRCLE_CIRCLE = auto()
    COLORCIRCLE_SQUARE_ = auto() # 末尾にindexを付加すること

class TagDrawLayer(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, last, count):
        return f"DLAYER_{name.lower()}"
    
    POINT_INDICATOR = auto()

class TagWindow(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, last, count):
        return f"WINDOW_{name.lower()}"
    
    IMAGE = auto()
    PRIMARY = auto()

class TagGroup(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, last, count):
        return f"Group_{name.lower()}"
    
    LOADING_INFO = auto()
    COLOR_LIST = auto()
    COLOR_LIST_INVIS = auto()

class TagHandler(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, last, count):
        return f"HANDLER_{name.lower()}"
    
    WIDGET = auto()