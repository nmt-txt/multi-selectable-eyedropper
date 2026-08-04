from color import Color

class Picked:
    pos : tuple
    color : Color

    def __init__(self, pos, rgba):
        self.pos = pos
        self.color = Color()
        self.color.set_rgb(rgba[:3])

items = list()
selected = list() # 選択状態をTrue/Falseでアイテム分保持

# 2つのlistを同時に扱うというクセのある構成なので、書き込みはなるべくメソッドを用いること

def append(item, selected_state):
    items.append(item)
    selected.append(selected_state)
    return len(items)-1

def insert(at, item, selected_state):
    items.insert(at, item)
    selected.insert(at, selected_state)
    return

def pop_at(index):
    return (items.pop(index), selected.pop(index))

def delete_at(index):
    return pop_at(index)

def swap(src_index, target_index):
    items[target_index], items[src_index] = items[src_index], items[target_index]
    selected[target_index], selected[src_index] = selected[src_index], selected[target_index]
    return

def clear():
    l = len(items)
    items.clear()
    selected.clear()
    return l