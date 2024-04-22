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
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )


# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

class GI_SceneProperties(PropertyGroup):

    up: BoolProperty(
        name="Up",
        description="Up button on gamepad",
        default = False
        )
    down: BoolProperty(
        name="Down",
        description="Down button on gamepad",
        default = False
        )
    left: BoolProperty(
        name="Left",
        description="Left button on gamepad",
        default = False
        )
    right: BoolProperty(
        name="Right",
        description="Right button on gamepad",
        default = False
        )

    # my_float: FloatProperty(
    #     name = "Float",
    #     description = "Float Property",
    #     default = 23.7,
    #     min = 0.01,
    #     max = 30.0
    #     )

    # my_float_vector: FloatVectorProperty(
    #     name = "Float Vector",
    #     description="Float Vector Property",
    #     default=(0.0, 0.0, 0.0),
    #     #subtype='COLOR',
    #     min= 0.0, # float
    #     max = 0.1
    # ) 
        
    # my_enum: EnumProperty(
    #     name="Enum",
    #     description="Enum Property",
    #     items=[ ('OP1', "Option 1", ""),
    #             ('OP2', "Option 2", ""),
    #           ]
    #     )

        
class GI_GamepadInputPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Gamepad Input Example"
    bl_idname = "SCENE_PT_gamepad"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    
    def draw(self, context):
        layout = self.layout

        scene = context.scene
        gamepad = scene.addon_gamepad

        layout.label(text="Gamepad")
        row = layout.row()
        row.operator("wm.test_gamepad")

        row = layout.row()
        row.prop(gamepad, "up")
        row.prop(gamepad, "down")
        row.prop(gamepad, "left")
        row.prop(gamepad, "right")


class GI_gamepad(bpy.types.Operator):
    bl_idname = "wm.test_gamepad"
    bl_label = "Test Gamepad"
    bl_description = "Vibrates active gamepad and shows data in console"

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
    
classes = (
    GI_SceneProperties,
    GI_GamepadInputPanel,
    GI_gamepad,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.addon_gamepad = PointerProperty(type=GI_SceneProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.addon_gamepad


if __name__ == "__main__":
    register()
