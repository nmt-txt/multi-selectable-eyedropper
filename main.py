# 複数箇所選択できる画像カラースポイトGUIソフト

import dearpygui.dearpygui as dpg
import numpy as np
from PIL import ImageGrab, Image, UnidentifiedImageError
import time, pyperclip, pathlib, math

from tag import TagItem, TagTexture, TagWindow, TagHandler, TagGroup, TagDrawLayer
import pickedColorState, imageState, comboItem, colorCircleSquare

dpg.create_context()
# dpg.show_item_registry()
dpg.create_viewport(title="Multi-selectable image color eyedropper(MSICE) v0.3", width=800, height=680)

# Dear PyGuiのカラーサークルは三角かつ色相の角度が気に入らない
# このため自作する。サークルは色が変わらないので事前ロードできるが、
# 明度彩度については色が変わるので、彩度シフトできる状態で保持する必要がある
color_circle_square = colorCircleSquare.colorCircleSquare("assets/square2.png")
square_tex_disposables = [] # テクスチャ破棄候補タグリスト


# 画像側処理
# ├── reflesh_loaded_image() 画像再読み込み開始。Ctrl+V、Loadボタン時。
# ├── load_image() クリップボードから画像読み込み
# └── display_image() 画像描画。画面フィットなど読み込みしないならここから
#     ├── register_colorimage() / register_grayscale() 必要であればテクスチャを登録
#     └── display_point_indicator() 描画サイズが変わったかもしれないので、インジケータも再描画

# ピックした色処理
# └── reflesh_color_list() リスト子要素を削除し、リストをやり直す
#    └── display_color_list_item() 子要素1つを描画するやつ
# ─── update_color_list_checkbox() チェックボックスの状態を更新する。select all系ボタン操作時に呼ばれる。

# テクスチャ事前ロード
# └── [名無し] カラーサークルのサークル部分を登録

# UI要素コールバック
# - on_add_color_manual(): 座標入力によるカラーピックのとき。inputあるいはbuttonのコールバック
# - on_clear_color_list(): 色リストクリア。クリアボタンによる。
# - on_select_color_item_checkbox(): 色アイテムのチェックボックスクリック時。app_dataに操作対象のindexを渡すこと
# - on_color_select_all(): 色全選択。
# - on_color_deselect_all(): 色選択外す。
# - on_color_toggle(): 色選択切り替える。
# - on_color_item_del(): 色アイテムのXボタンを押したとき。app_dataに操作対象indexを渡すこと。
# - on_color_item_reorder(): 色アイテムの上下ボタンを押したとき。app_dataにボタンが押されたやつのindexと、上か下かを-1,1で表したやつをタプルで渡すこと

# ハンドラ
# - handle_resize(): TagWindow.IMAGE(左側画像の子ウィンドウ)リサイズ時
# - handle_move(): カーソル移動時
# - handle_mouse_wheel(): マウスホイール
# - handle_click(): クリック時
# - handle_paste_key(): Ctrl+V

# 画像側の処理 ##########################################

def get_image_fit_size(image_size, within):
    """指定枠内に画像をフィットさせる場合の最大サイズを計算する

    Args:
        image_size (tuple(int)): オリジナル画像のXYサイズ
        within (tuple(int)): フィットさせる枠のXYサイズ
    Returns:
        tuple(tuple(int), float): オリジナル画像を枠にフィットさせる場合のXYサイズと、倍率のtuple
    """
    scale_x = within[0] / image_size[0]
    scale_y = within[1] / image_size[1]

    scale = min (scale_x, scale_y)
    fit_size = (max(1, round(image_size[0] * scale)), max(1, round(image_size[1] * scale)))
    return (fit_size, scale)


# 画像読み込み
def load_image():
    """画像をクリップボードから読み込み、imageStateにセットする
    Returns:
        tuple(bool, str): OK, エラーstring。Go的。OK==Trueならば成功
    """
    print("load_image")
    img = ImageGrab.grabclipboard()
    origin="clipboard"

    if img is None:
        # パス文字列そのもののコピーの場合ImageGrabはgrabしない
        # 文字列でなかったら捨て、パスでも存在しなければ捨て、存在しても対応していなければ捨てる
        clipboard_str = pyperclip.paste()
        if type(clipboard_str) is not str:
            return (False, "No image in clipboard!")
        clipboard_path = pathlib.Path(clipboard_str.strip()) 
        if not clipboard_path.exists() or not clipboard_path.is_file():
            return (False, f"\"{clipboard_path}\" is not exist or not a file!")
        if clipboard_path.suffix not in Image.registered_extensions():
            return (False, f"{clipboard_path.suffix} file is not supported!")
        img = [clipboard_path]

    if type(img) is list:
        origin = img[0]
        try :
            img = Image.open(img[0])
        except (UnidentifiedImageError, FileNotFoundError) as e:
            return (False, f"exception: {e}")

    imageState.image_color = img.convert("RGBA")
    imageState.origin = origin
    imageState.res = (img.width, img.height)
    imageState.is_origin_clipboard = origin == "clipboard"
    imageState.loaded = True
    return (True, "")

# カラー画像をtextureに登録する
def register_colorimage():
    img_np = np.array(imageState.image_color, dtype=np.float32)
    img_np /= 255.0

    with dpg.texture_registry():
        dpg.add_static_texture(tag=TagTexture.IMAGE, default_value=img_np.ravel(), width=imageState.res[0], height=imageState.res[1])
    

# 既に読み込んだ画像を元にグレースケールを登録する。
def register_grayscale():
    img_gray = imageState.image_color.convert("L")
    gray_np = np.array(img_gray, dtype=np.float32)
    gray_np /= 255.0
    dpg_image_gray = np.empty((img_gray.height, img_gray.width, 4), dtype=np.float32)
    dpg_image_gray[:,:, 0] = gray_np
    dpg_image_gray[:,:, 1] = gray_np
    dpg_image_gray[:,:, 2] = gray_np
    dpg_image_gray[:,:, 3] = 1.0
    with dpg.texture_registry():
        dpg.add_static_texture(tag=TagTexture.GRAYSCALE, default_value=dpg_image_gray.ravel(), width=img_gray.width, height=img_gray.height)


# 画像の表示。テクスチャがなければregisterして表示。画面フィットもここ。
def display_image():
    if not imageState.loaded:
        return
    available_size = dpg.get_item_rect_size(window_image)
    dpg.set_value(TagItem.TEXT_LOAD_STAT, "")

    selected = dpg.get_value(TagItem.COMBO_IMAGE_COLORMODE)

    if selected == comboItem.ImageColormode.COLOR:
        if not dpg.does_item_exist(TagTexture.IMAGE):
            dpg.configure_item(TagGroup.LOADING_INFO, show=True)
            dpg.set_value(TagItem.TEXT_LOAD_STAT, dpg.get_value(TagItem.TEXT_LOAD_STAT) + f"Image: {imageState.origin}\nres: {imageState.res[0]}x{imageState.res[1]}\n")
            dpg.set_value(TagItem.TEXT_LOAD_STAT, dpg.get_value(TagItem.TEXT_LOAD_STAT) + f"Loading...\n")
            register_colorimage()
        should_display_tag = TagTexture.IMAGE
    if selected == comboItem.ImageColormode.GRAYSCALE:
        if not dpg.does_item_exist(TagTexture.GRAYSCALE):
            dpg.configure_item(TagGroup.LOADING_INFO, show=True)
            dpg.set_value(TagItem.TEXT_LOAD_STAT, dpg.get_value(TagItem.TEXT_LOAD_STAT) + f"Image: {imageState.origin}\nres: {imageState.res[0]}x{imageState.res[1]}\n")
            dpg.set_value(TagItem.TEXT_LOAD_STAT, dpg.get_value(TagItem.TEXT_LOAD_STAT) + f"Grayscale loading...\n")
            register_grayscale()
        should_display_tag = TagTexture.GRAYSCALE

    preferred_size = get_image_fit_size(imageState.res, (available_size[0], available_size[1]))[0]

    start = (max(available_size[0], preferred_size[0]) - preferred_size[0], 0)
    end = (start[0]+preferred_size[0], preferred_size[1])

    # print(f"available: {available_size}, preferred: {preferred_size} = {start} {end}")
    
    dpg.configure_item(TagGroup.LOADING_INFO, show=False)
    dpg.set_value(TagItem.TEXT_LOAD_STAT, "")
    if not dpg.does_item_exist(TagItem.IMAGE_DRAWLIST):
        with dpg.drawlist(width=available_size[0], height=available_size[1], tag=TagItem.IMAGE_DRAWLIST, parent=window_image):
            with dpg.draw_layer():
                dpg.draw_image(should_display_tag, start, end, uv_min=(0,0), uv_max=(1,1), tag=TagItem.IMAGE_IMAGE)
            with dpg.draw_layer(tag=TagDrawLayer.POINT_INDICATOR):
                pass
    else :
        dpg.configure_item(TagItem.IMAGE_DRAWLIST, width=available_size[0], height=available_size[1])
        dpg.configure_item(TagItem.IMAGE_IMAGE, texture_tag = should_display_tag, pmin=start ,pmax=end)

    display_point_indicator()


# 画像リロード操作
def reflesh_loaded_image():
    print("reload start.")
    start = time.perf_counter()
    pickedColorState.clear()
    list_width = reflesh_color_list()

    if dpg.does_item_exist(TagTexture.IMAGE):
        dpg.delete_item(TagTexture.IMAGE)
    if dpg.does_item_exist(TagTexture.GRAYSCALE):
        dpg.delete_item(TagTexture.GRAYSCALE)
    if dpg.does_item_exist(TagItem.IMAGE_DRAWLIST):
        dpg.delete_item(TagItem.IMAGE_DRAWLIST)

    available_size = dpg.get_item_rect_size(window_image)
    dpg.configure_item(TagItem.TEXT_LOAD_STAT, wrap=available_size[0])

    ok, errDetail = load_image()
    if not ok:
        dpg.configure_item(TagGroup.LOADING_INFO, show=True)
        dpg.set_value(TagItem.TEXT_LOAD_STAT, dpg.get_value(TagItem.TEXT_LOAD_STAT) +"[ERROR] "+ errDetail + "\n")
        return
    
    origin_text = "Clipboard" if imageState.is_origin_clipboard else pathlib.Path(imageState.origin).name
    dpg.set_value(TagItem.TEXT_LOADED_IMAGE_DETAIL, f"{origin_text} ({imageState.res[0]}x{imageState.res[1]})")

    display_image()
    end = time.perf_counter()
    print(f"complete. {end-start} sec.")


def display_point_indicator():
    if not dpg.does_item_exist(TagItem.IMAGE_DRAWLIST):
        return

    dpg.delete_item(TagDrawLayer.POINT_INDICATOR, children_only=True)

    #offset = dpg.get_item_rect_min(TagItem.IMAGE_DRAWLIST) # DrawListは若干ズレて配置されている? # なんかここでは関係ない??????
    available_size = dpg.get_item_rect_size(TagWindow.IMAGE)
    texture_size = imageState.res
    preferred_size, image_resized_scale = get_image_fit_size(texture_size, (available_size[0], available_size[1]))

    x_align_offset = max(available_size[0], preferred_size[0]) - preferred_size[0]
            
    for i, (item, selected) in enumerate(zip(pickedColorState.items, pickedColorState.selected)):
        if selected:
            pos_draw = (
                item.pos[0] * image_resized_scale + x_align_offset,
                item.pos[1] * image_resized_scale
            )
            # pos_draw = (pos_draw[0] - offset[0], pos_draw[1] - offset[1]) # あれ? いらない?
            dpg.draw_circle(pos_draw, 4, color=(85,85,85), parent=TagDrawLayer.POINT_INDICATOR)
            dpg.draw_circle(pos_draw, 3, color=(255,255,255), parent=TagDrawLayer.POINT_INDICATOR)
            pos_text = (pos_draw[0]+10, pos_draw[1]-8)

            color_f = 0 if item.color.luma > 127 else 255
            color_b = 255 - color_f
            text = f"#{i+1}"

            # dpg.draw_text((pos_text[0]+1, pos_text[1]+1), f"#{i+1}", size=17, color=([color_b]*3), parent=TagDrawLayer.POINT_INDICATOR)
            dpg.draw_rectangle((pos_text[0]-2, pos_text[1]), (pos_text[0]+10*len(text), pos_text[1]+16), color=([color_b]*3), fill=[color_b, color_b, color_b, 200], parent=TagDrawLayer.POINT_INDICATOR)
            dpg.draw_text(pos_text, text, size=16, color=([color_f]*3), parent=TagDrawLayer.POINT_INDICATOR)



# 選んだ色側の処理 ##########################################

def convert_color_list_height(selected_size):
    line_height = 50
    match selected_size:
        case comboItem.ColorListSize.XS:
            line_height = 20
        case comboItem.ColorListSize.S:
            line_height = 40
        case comboItem.ColorListSize.M:
            line_height = 60
        case comboItem.ColorListSize.L:
            line_height = 80
        case comboItem.ColorListSize.XL:
            line_height = 100
        case comboItem.ColorListSize.XXL:
            line_height = 130

    return line_height

def reflesh_color_list():
    """色リスト表示を初期化し、作り直す。リストを描画するのに十分な幅pxを返す。
    """
    dpg.delete_item(TagGroup.COLOR_LIST, children_only=True)
    for v in square_tex_disposables:
        dpg.delete_item(v)
    square_tex_disposables.clear()

    selected_size = dpg.get_value(TagItem.COMBO_COLORLIST_SIZE)
    
    selected_format = dpg.get_value(TagItem.COMBO_COLORFORMAT)
    
    for i, item in enumerate(pickedColorState.items):
        square_tex_tag = "" # HLS色空間の場合、使用しないので空文字で良い
        if selected_format != comboItem.ColorFormat.HLS:
            square_tex_tag = f"{TagTexture.COLORCIRCLE_SQUARE_}{i}"
            with dpg.texture_registry():
                img_np = color_circle_square.get_shifted_hue(item.color.hsv[0])
                dpg.add_static_texture(color_circle_square.width, color_circle_square.height, img_np, tag=square_tex_tag)
                square_tex_disposables.append(square_tex_tag)

        display_color_list_item(i, item, selected_size, selected_format, TagGroup.COLOR_LIST, square_tex_tag)

            
def display_color_list_item(item_index, item, size, format, parent, square_tex_tag):
    """ 色アイテムを1つ表示し、作成したgroupのタグを返す
    """
    height_px = convert_color_list_height(size)
    Formats = comboItem.ColorFormat
    Sizes = comboItem.ColorListSize

    match format:
        case Formats.RGB:
            color_str = "({:>3},{:>3},{:>3})".format(*item.color.rgb)
        case Formats.HSV:
            color_str = "({:>3},{:>3},{:>3})".format(*item.color.hsv)
        case Formats.HLS:
            color_str = "({:>3},{:>3},{:>3})".format(*item.color.hls)
    if size != Sizes.S and size != Sizes.XS:
        if format == Formats.RGB:
            color_str += "\n   hsv({:>3},{:>3},{:>3})".format(*item.color.hsv)
        else :
            color_str += "\n   rgb({:>3},{:>3},{:>3})".format(*item.color.rgb)

    match size:
        # size: [foreground, background]
        case Sizes.XL | Sizes.XXL:
            circle_thickness = [2, 4]
            circle_radius = [4, 5]
        case Sizes.L:
            circle_thickness = [2, 3]
            circle_radius = [3, 4]
        case _:
            circle_thickness = [1, 3]
            circle_radius = [3, 4]
 
    with dpg.group(height=height_px, parent=parent, horizontal=True) as created:
        with dpg.group(height=height_px):
            dpg.add_text("#{:>2}".format(item_index+1))
            if size != Sizes.XS:
                dpg.add_checkbox(callback=on_select_color_item_checkbox, user_data=item_index, default_value=pickedColorState.selected[item_index], tag=f"{TagItem.CHKBOX_COLORLIST_SELECT_}{item_index}")
        if format == Formats.HLS:
            dpg.add_color_picker(default_value=item.color.rgba, width=height_px*1.4, height=height_px*1.4, picker_mode=dpg.mvColorPicker_wheel, no_side_preview=True, no_alpha=True, no_inputs=True)
        else:
            with dpg.drawlist(width=height_px, height=height_px):
                # カラーサークル
                dpg.draw_image(TagTexture.COLORCIRCLE_CIRCLE, (0,0), (height_px, height_px))
                center = height_px / 2.0
                hue_degree_f = ((item.color.hsv[0] + 21.2499999999992) % 255) / 255.0 # ClipStudioのサークルは30度時計回りにシフトしてるっぽい...? ただしここでは一周360ではなく255なので30という数字をそのまま使うとズレる
                hue_x = center + center * -math.cos(hue_degree_f * 2 * math.pi)
                hue_y = center + center * -math.sin(hue_degree_f * 2 * math.pi)
                dpg.draw_line((center,center), (hue_x, hue_y), color=(85,85,85), thickness=circle_thickness[1])
                dpg.draw_line((center,center), (hue_x, hue_y), color=(255,255,255), thickness=circle_thickness[0])
                # print(f"#{i} {hue_degree_f} ({hue_x}, {hue_y})")

                square_min = height_px * 0.22432432432432 # サークルと四角分離・余白削除前に四角がどこにあったかというと、83,83 から 284,284の範囲内
                square_max = height_px * 0.76756756756757 # これらをサークルの大きさである370で割る...
                dpg.draw_image(square_tex_tag, (square_min,square_min), (square_max,square_max))
                line_x = square_min + ((square_max - square_min) * (item.color.hsv[1] / 255.0))
                line_y = square_min + ((square_max - square_min) * ((255 - item.color.hsv[2]) / 255.0))
                dpg.draw_circle((line_x, line_y), circle_radius[1], color=(85,85,85))
                dpg.draw_circle((line_x, line_y), circle_radius[0], color=(255,255,255))
        with dpg.drawlist(width=20, height=height_px):
            dpg.draw_rectangle((0,0), (10,height_px), color=[45]*3, fill=item.color.rgba)
            dpg.draw_rectangle((10,0), (20,height_px), color=[45]*3, fill=([item.color.luma]*3))
        with dpg.group():
            if size != Sizes.XS:
                with dpg.group(horizontal=True):
                    dpg.add_text("@({:>4},{:>4})".format(*item.pos))
                    dpg.add_input_text(default_value=item.color.hex, width=50, readonly=True, auto_select_all=True)
            dpg.add_text(f"{color_str}")
        with dpg.group():
            if size == Sizes.XS:
                dpg.add_button(label="X", small=True, height=height_px/3) # height /3 not working... why?
            else :
                dpg.add_button(label="^", small=True, height=height_px/3, callback=on_color_item_reorder, user_data=(item_index, (item_index -1) % len(pickedColorState.items)))
                dpg.add_button(label="X", small=True, height=height_px/3, callback=on_color_item_del, user_data=item_index)
                if size != Sizes.S:
                    dpg.add_button(label="v", small=True, height=(height_px/3), callback=on_color_item_reorder, user_data=(item_index, (item_index +1) % len(pickedColorState.items)))
    return created

def update_color_list_checkbox():
    for i, v in enumerate(pickedColorState.selected):
        dpg.set_value(f"{TagItem.CHKBOX_COLORLIST_SELECT_}{i}", v)


# Loading texture ##########################################

with dpg.texture_registry():
    img = Image.open("assets/circle.png")
    img_np = np.array(img, dtype=np.float32)
    img_np /= 255.0
    dpg.add_static_texture(tag=TagTexture.COLORCIRCLE_CIRCLE, default_value=img_np.ravel(), width=img.width, height=img.height)



# UI element callbacks ##########################################
## 必要なもののみここに配置。例えば1つの関数コールで済むような処理はここに集めずにそのままcallbackに書く。

### Right pane #######################
def on_add_color_manual():
    if not imageState.loaded:
        return
    x = dpg.get_value(TagItem.INPUT_MANUAL_X)
    y = dpg.get_value(TagItem.INPUT_MANUAL_Y)

    if x=="":
        x = dpg.get_item_configuration(TagItem.INPUT_MANUAL_X)["hint"]
    if y=="":
        y = dpg.get_item_configuration(TagItem.INPUT_MANUAL_Y)["hint"]

    x = min(int(x), imageState.res[0])
    y = min(int(y), imageState.res[1])

    picked = pickedColorState.Picked((x,y), imageState.image_color.getpixel((x, y)))
    pickedColorState.append(picked, True)
    reflesh_color_list()
    display_point_indicator()

    dpg.set_value(TagItem.INPUT_MANUAL_X, "")
    dpg.set_value(TagItem.INPUT_MANUAL_Y, "")

def on_clear_color_list():
    pickedColorState.clear()
    reflesh_color_list()
    display_point_indicator()

def on_select_color_item_checkbox(sender, app_data, user_data):
    pickedColorState.selected[user_data] = not pickedColorState.selected[user_data]
    display_point_indicator()

def on_color_select_all():
    pickedColorState.selected = list(map(lambda _: True, pickedColorState.selected))
    update_color_list_checkbox()
    display_point_indicator()

def on_color_deselect_all():
    pickedColorState.selected = list(map(lambda _: False, pickedColorState.selected))
    update_color_list_checkbox()
    display_point_indicator()

def on_color_toggle():
    pickedColorState.selected = list(map(lambda b: not b, pickedColorState.selected))
    update_color_list_checkbox()
    display_point_indicator()

def on_color_item_del(sender, app_data, user_data):
    pickedColorState.delete_at(user_data)
    reflesh_color_list()
    display_point_indicator()

def on_color_item_reorder(sender, app_data, user_data):
    # user_data = (index, target).
    index = user_data[0]
    target = user_data[1]
    pickedColorState.swap(index, target)
    reflesh_color_list()
    display_point_indicator()



# Window Layout ##########################################

with dpg.window(tag=TagWindow.PRIMARY):#描画スペースの中にwindowを作る。
    with dpg.table(resizable=True, header_row=False, policy=dpg.mvTable_SizingStretchProp, tag=TagItem.TABLE_WINDOWPANE):
        # dpg.add_table_column(init_width_or_weight=0.6)
        # dpg.add_table_column(tag=TagItem.TABLE_LIST_COLUMN, init_width_or_weight=0.4)
        dpg.add_table_column(width_stretch=True, init_width_or_weight=1.0)
        dpg.add_table_column(tag=TagItem.TABLE_LIST_COLUMN, width_fixed=True, no_resize=True, init_width_or_weight=0.0)

        with dpg.table_row():
            # 左パネル
            with dpg.child_window(border=False):
                with dpg.group(horizontal=True):
                        dpg.add_button(label="Load", callback=reflesh_loaded_image)
                        dpg.add_text("|") # spacing
                        dpg.add_combo([e.value for e in comboItem.ImageColormode], default_value=comboItem.ImageColormode.COLOR.value, callback=display_image, tag=TagItem.COMBO_IMAGE_COLORMODE, fit_width=True)
                        dpg.add_text("v0.3", color=[150,200,255], tag=TagItem.TEXT_LOADED_IMAGE_DETAIL)
                with dpg.child_window(tag=TagWindow.IMAGE, border=False) as window_image:
                    with dpg.group(tag=TagGroup.LOADING_INFO):
                        dpg.add_text("To display copied image:\n  - Click the \"Load\" button above\n  - Press Ctrl+V (tips: release V first)\n\n", tag=TagItem.TEXT_LOAD_STAT)

            # 右パネル
            with dpg.child_window(border=False, auto_resize_x=True):
                with dpg.group():
                    with dpg.group(horizontal=True):
                        dpg.add_input_text(width=40, tag=TagItem.INPUT_MANUAL_X, hint="0", on_enter=True, callback=on_add_color_manual)
                        dpg.add_text(",")
                        dpg.add_input_text(width=40, tag=TagItem.INPUT_MANUAL_Y, hint="0", on_enter=True, callback=on_add_color_manual)
                        dpg.add_button(label="Add", callback=on_add_color_manual)
                        dpg.add_text("|")
                        dpg.add_combo([e.value for e in comboItem.ColorFormat], default_value=comboItem.ColorFormat.HSV.value, tag=TagItem.COMBO_COLORFORMAT, fit_width=True, callback=reflesh_color_list)
                        dpg.add_combo([e.value for e in comboItem.ColorListSize], default_value=comboItem.ColorListSize.M.value, tag=TagItem.COMBO_COLORLIST_SIZE, fit_width=True, callback=reflesh_color_list)
                        
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Select all", callback=on_color_select_all)
                        dpg.add_button(label="Deselect all", callback=on_color_deselect_all)
                        dpg.add_button(label="Toggle", callback=on_color_toggle)
                        dpg.add_text("|")
                        dpg.add_button(label="Clear", callback=on_clear_color_list)
                        
                with dpg.child_window(tag=TagGroup.COLOR_LIST, border=False, auto_resize_x=True):
                    dpg.add_text("") # default: empty. just as a placeholder.
                with dpg.group(tag=TagGroup.COLOR_LIST_INVIS, show=False):
                    pass



# Handler ##########################################

def handle_resize(sender, app_data, user_data):
    #print(f"HANDLE: RESIZE (send:{sender}, app_data:{app_data}, user_data:{user_data})")
    if app_data == TagWindow.IMAGE and dpg.does_item_exist(TagItem.IMAGE_IMAGE):
        display_image()

def handle_move(sender, app_data, user_data):
    if dpg.does_item_exist(TagItem.IMAGE_DRAWLIST) and dpg.is_item_hovered(TagItem.IMAGE_DRAWLIST):
        offset = dpg.get_item_rect_min(TagItem.IMAGE_DRAWLIST) # DrawListは若干ズレて配置されている?

        available_size = dpg.get_item_rect_size(window_image)
        texture_size = imageState.res
        preferred_size, image_resized_scale = get_image_fit_size(texture_size, (available_size[0], available_size[1]))

        x_align_offset = max(available_size[0], preferred_size[0]) - preferred_size[0]

        mouse_pos = (app_data[0]-x_align_offset, app_data[1])

        restored_pos = (
            max(0, min(round((mouse_pos[0]-offset[0])/image_resized_scale), texture_size[0]-1)),
            max(0, min(round((mouse_pos[1]-offset[1])/image_resized_scale), texture_size[1]-1))
        )

        dpg.configure_item(TagItem.INPUT_MANUAL_X, hint=restored_pos[0])
        dpg.configure_item(TagItem.INPUT_MANUAL_Y, hint=restored_pos[1])
        

def handle_mouse_wheel(sender, app_data, user_data):
    # 画像カラー/グレースケール選択をスクロールでも切り替えさせる

    def iterate_item(selectable, selecting, direction):
        selecting_index = selectable.index(selecting)
        return selectable[(selecting_index + direction) % len(selectable)]

    if dpg.is_item_hovered(TagItem.COMBO_IMAGE_COLORMODE):
        next = iterate_item(
            [e.value for e in comboItem.ImageColormode], 
            dpg.get_value(TagItem.COMBO_IMAGE_COLORMODE), 
            math.ceil(-app_data)
        )
        dpg.set_value(TagItem.COMBO_IMAGE_COLORMODE, next)
        display_image() # callbackが発動しない。嘘...

    if dpg.is_item_hovered(TagItem.COMBO_COLORLIST_SIZE):
        next = iterate_item(
            [e.value for e in comboItem.ColorListSize],
            dpg.get_value(TagItem.COMBO_COLORLIST_SIZE),
            math.ceil(-app_data)
        )
        dpg.set_value(TagItem.COMBO_COLORLIST_SIZE, next)
        reflesh_color_list()
    if dpg.is_item_hovered(TagItem.COMBO_COLORFORMAT):
        next = iterate_item(
            [e.value for e in comboItem.ColorFormat],
            dpg.get_value(TagItem.COMBO_COLORFORMAT),
            math.ceil(-app_data)
        )
        dpg.set_value(TagItem.COMBO_COLORFORMAT, next)
        reflesh_color_list()

def handle_click(sender, app_data, user_data):
    if dpg.does_item_exist(TagItem.IMAGE_DRAWLIST) and dpg.is_item_hovered(TagItem.IMAGE_DRAWLIST):
        mouse_pos = dpg.get_mouse_pos()
        offset = dpg.get_item_pos(TagWindow.IMAGE) # DrawListは自身の位置を知らない(0,0)。そのため親から位置を取ってくる。WindowとDrawListの間に何か出てくるとListのPosとの合わせ技になるだろう...
        mouse_pos_corrected = (mouse_pos[0]-offset[0], mouse_pos[1]-offset[1])
        
        available_size = dpg.get_item_rect_size(window_image)
        preferred_size, _ = get_image_fit_size(imageState.res, (available_size[0], available_size[1]))

        x_align_offset = max(available_size[0], preferred_size[0]) - preferred_size[0]

        mouse_pos_corrected = (mouse_pos_corrected[0]-x_align_offset, mouse_pos_corrected[1])

        # print(f"original: {mouse_pos}, mouse: {mouse_pos_corrected}, drawsize:{available_size}, image:{preferred_size}, imageOffsetX:{x_align_offset}")
        if mouse_pos_corrected[0] > preferred_size[0] or mouse_pos_corrected[1] > preferred_size[1] or mouse_pos_corrected[0] < 0 or mouse_pos_corrected[1] < 0:
            return
        

        clicked_image_pos = (
            int(dpg.get_item_configuration(TagItem.INPUT_MANUAL_X)["hint"]),
            int(dpg.get_item_configuration(TagItem.INPUT_MANUAL_Y)["hint"])
        )
        picked = pickedColorState.Picked(clicked_image_pos, imageState.image_color.getpixel(clicked_image_pos))
        pickedColorState.append(picked, True)
        reflesh_color_list()
        display_point_indicator()


def handle_paste_key(sender, app_data, user_data):
    if dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl):
        reflesh_loaded_image()
        

with dpg.item_handler_registry(tag=TagHandler.WIDGET):
    dpg.add_item_resize_handler(callback=handle_resize)
with dpg.handler_registry():
    dpg.add_mouse_move_handler(callback=handle_move)
    dpg.add_mouse_wheel_handler(callback=handle_mouse_wheel)
    dpg.add_key_release_handler(dpg.mvKey_V, callback=handle_paste_key)
    dpg.add_mouse_click_handler(callback=handle_click)

dpg.bind_item_handler_registry(TagWindow.IMAGE, TagHandler.WIDGET)



dpg.setup_dearpygui() 
dpg.show_viewport()
dpg.set_primary_window(TagWindow.PRIMARY, True)
dpg.start_dearpygui()

dpg.destroy_context()