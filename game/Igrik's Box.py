from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import os

app = Ursina()

# --- Safe texture loader ---
def safe_load_texture(path, fallback='white_cube'):
    if path and os.path.exists(path):
        tex = load_texture(path)
        if tex:
            return tex
    return load_texture(fallback)

# Load textures safely
skybox_image = safe_load_texture("background.jpg")
grass_texture = safe_load_texture("grass_block.jpg")
stone_texture = safe_load_texture("stone_block.png")
brick_texture = safe_load_texture("brick_block.png")
dirt_texture = safe_load_texture("dirt_block.jpg")
wood_texture = safe_load_texture("wood_block.jpg")
bedrock_texture = safe_load_texture("bedrock_block.jpg")
leaves_texture = safe_load_texture("leaves_block.jpg")

textures = [grass_texture, stone_texture, brick_texture, dirt_texture, wood_texture, bedrock_texture, leaves_texture]
current_slot = 0

Sky(texture=skybox_image)

# --- Inventory setup ---
def make_slot():
    return {"id": None, "count": 0}

inventory = [make_slot() for _ in range(27)]  # 27 = 3 rows * 9 cols

# --- Hotbar UI ---
hotbar_slots = []
for i in range(9):
    # background slot (frame)
    slot = Entity(parent=camera.ui, model='quad', color=color.gray,
                  scale=(0.12,0.12), position=(-0.48 + i*0.12, -0.45))
    # icon fills slot
    icon = Entity(parent=slot, model='quad', texture=None,
                  scale=(0.504,0.504), position=(0,0,-0.01))
    # count text bottom-right
    label = Text(parent=slot, text="", origin=(.5,-.5), scale=2.5,
                 position=(0.05,-0.05), color=color.white)
    hotbar_slots.append({"bg": slot, "icon": icon, "label": label})

# selector highlight (behind icons)
selector = Entity(parent=camera.ui, model='quad', color=color.azure.tint(-.2),
                  scale=(0.13,0.13), position=hotbar_slots[current_slot]["bg"].position, z=0.1)

# --- Inventory UI (toggle with E) ---
inventory_ui = Entity(parent=camera.ui, enabled=False)
grid_slots = []
for row in range(3):
    for col in range(9):
        slot = Entity(parent=inventory_ui, model='quad', color=color.dark_gray,
                      scale=(0.12,0.12),
                      position=(-0.48 + col*0.12, 0.25 - row*0.12))
        icon = Entity(parent=slot, model='quad', texture=None,
                      scale=(0.115,0.115), position=(0,0,-0.01))
        label = Text(parent=slot, text="", origin=(.5,-.5), scale=2.5,
                     position=(0.05,-0.05), color=color.white)
        grid_slots.append({"bg": slot, "icon": icon, "label": label})

# --- Helpers ---
def update_ui():
    # hotbar
    for i in range(9):
        slot = inventory[i]
        hotbar_slots[i]["icon"].texture = textures[slot["id"]] if slot["id"] is not None else None
        hotbar_slots[i]["label"].text = str(slot["count"]) if slot["count"] > 0 else ""
    # inventory grid
    for i, slot in enumerate(inventory):
        grid_slots[i]["icon"].texture = textures[slot["id"]] if slot["id"] is not None else None
        grid_slots[i]["label"].text = str(slot["count"]) if slot["count"] > 0 else ""

def add_item(block_id, amount=1):
    # stack first
    for slot in inventory:
        if slot["id"] == block_id and slot["count"] < 32:
            addable = min(amount, 32 - slot["count"])
            slot["count"] += addable
            amount -= addable
            if amount <= 0:
                update_ui()
                return
    # new stack
    for slot in inventory:
        if slot["id"] is None:
            slot["id"] = block_id
            slot["count"] = min(32, amount)
            amount -= slot["count"]
            if amount <= 0:
                update_ui()
                return
    update_ui()

def remove_item(block_id, amount=1):
    for slot in inventory:
        if slot["id"] == block_id:
            slot["count"] -= amount
            if slot["count"] <= 0:
                slot["id"] = None
                slot["count"] = 0
            update_ui()
            return

# --- Voxel ---
class Voxel(Button):
    def __init__(self, position=(0,0,0), texture=grass_texture, block_id=0):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=.5,
            texture=texture,
            color=color.white,
            highlight_color=color.lime,
        )
        self.block_id = block_id

# --- Flat world ---
from random import randint  # make sure randint is imported at the top

for z in range(20):
    for x in range(20):
        if randint(1, 20) == 1:  # 1 in 20 chance for a tree
            # tree trunk
            Voxel(position=(x,1,z), texture=wood_texture, block_id=4)
            Voxel(position=(x,2,z), texture=wood_texture, block_id=4)

            # leaves around the top
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    Voxel(position=(x+dx, 3, z+dz), texture=leaves_texture, block_id=6)
            Voxel(position=(x,4,z), texture=leaves_texture, block_id=6)
            
for z in range(20):
    for x in range(20):
        Voxel(position=(x,0,z), texture=grass_texture, block_id=0)
for z in range(20):
    for x in range(20):
        Voxel(position=(x,-1,z), texture=dirt_texture, block_id=3)
for z in range(20):
    for x in range(20):
        Voxel(position=(x,-2,z), texture=dirt_texture, block_id=3)
for z in range(20):
    for x in range(20):
        Voxel(position=(x,-3,z), texture=dirt_texture, block_id=3)
for z in range(20):
    for x in range(20):
        Voxel(position=(x,-4,z), texture=stone_texture, block_id=1)
for z in range(20):
    for x in range(20):
        Voxel(position=(x,-5,z), texture=stone_texture, block_id=1)
for z in range(20):
    for x in range(20):
        Voxel(position=(x,-6,z), texture=stone_texture, block_id=1)
for z in range(20):
    for x in range(20):
        Voxel(position=(x,-7,z), texture=bedrock_texture, block_id=5)


# --- Input ---
def input(key):
    global current_slot
    if key == 'right mouse down' and not inventory_ui.enabled:
        hit_info = raycast(camera.world_position, camera.forward, distance=5)
        if hit_info.hit:
            slot = inventory[current_slot]
            if slot["id"] is not None and slot["count"] > 0:
                Voxel(position=hit_info.entity.position + hit_info.normal,
                      texture=textures[slot["id"]], block_id=slot["id"])
                remove_item(slot["id"], 1)

    if key == 'left mouse down' and not inventory_ui.enabled and mouse.hovered_entity:
        block_type = mouse.hovered_entity.block_id
        destroy(mouse.hovered_entity)
        add_item(block_type, 1)

    if key.isdigit() and not inventory_ui.enabled:
        num = int(key) - 1
        if 0 <= num < 9:
            current_slot = num
            selector.position = hotbar_slots[num]["bg"].position

    if key == 'e':
        inventory_ui.enabled = not inventory_ui.enabled
        mouse.locked = not inventory_ui.enabled
        player.enabled = not inventory_ui.enabled

# --- Player ---
player = FirstPersonController()


app.run()
