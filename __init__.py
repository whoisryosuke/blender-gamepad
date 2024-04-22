bl_info = {
    "name": "Gamepad Input Example",
    "description": "",
    "author": "whoisryosuke",
    "version": (0, 0, 2),
    "blender": (2, 80, 0),
    "location": "Properties > Output",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}

# __is_first_load = "operators" not in locals()
# if __is_first_load:
#     from .inputs import devices
# else:
#     import importlib

#     inputs = importlib.reload(inputs)

# from . import inputs
from .inputs import devices

import bpy

class GamepadInputPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Gamepad Input Example"
    bl_idname = "SCENE_PT_gamepad"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        # Create a simple row.
        layout.label(text=" Simple Row:")

        row = layout.row()
        row.prop(scene, "frame_start")
        row.prop(scene, "frame_end")

        # Create an row where the buttons are aligned to each other.
        layout.label(text=" Aligned Row:")

        row = layout.row(align=True)
        row.prop(scene, "frame_start")
        row.prop(scene, "frame_end")

        # Create two columns, by using a split layout.
        split = layout.split()

        # First column
        col = split.column()
        col.label(text="Column One:")
        col.prop(scene, "frame_end")
        col.prop(scene, "frame_start")

        # Second column, aligned
        col = split.column(align=True)
        col.label(text="Column Two:")
        col.prop(scene, "frame_start")
        col.prop(scene, "frame_end")

        # Big render button
        layout.label(text="Big Button:")
        row = layout.row()
        row.scale_y = 3.0
        row.operator("render.render")

        # Different sizes in a row
        layout.label(text="Different button sizes:")
        row = layout.row(align=True)
        row.operator("wm.test_gamepad")

class WM_gamepad(bpy.types.Operator):
    bl_idname = "wm.test_gamepad"
    bl_label = "Test Gamepad"
    bl_description = "Test function click me"

    def execute(self, context: bpy.types.Context):

        print("Finding gamepads...")
        for gamepad in devices:
            print("Gamepads found", gamepad.get_char_name())
            try:
                gamepad.set_vibration(0.5, 0.5, 420)
            except: 
                print("Couldn't vibrate gamepad.")
            # print("Getting gamepad data...")
            # events = gamepad.read()
            # for event in events:
                # print(event.ev_type, event.code, event.state)

        return {"FINISHED"}

def register():
    bpy.utils.register_class(GamepadInputPanel)
    bpy.utils.register_class(WM_gamepad)


def unregister():
    bpy.utils.unregister_class(GamepadInputPanel)
    bpy.utils.unregister_class(WM_gamepad)


if __name__ == "__main__":
    register()
