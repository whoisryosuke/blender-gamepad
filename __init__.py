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
import numpy
import math
import mathutils

def lerp( a, b, alpha ):
    return a + alpha * ( b - a )


# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

sync_enabled = False
gamepad_input = {
    "up": False,
    "down": False,
    "left": False,
    "right": False,
}

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
        up = gamepad_input["up"];
        up_text = "True" if up else "False"
        row.label(text=up_text)
        row.prop(gamepad, "up")
        row.prop(gamepad, "down")
        row.prop(gamepad, "left")
        row.prop(gamepad, "right")


class GI_gamepad(bpy.types.Operator):
    """Test function for gamepads"""
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


class GI_ModalOperator(bpy.types.Operator):
    """Gamepad syncing and camera movement"""
    bl_idname = "object.modal_operator"
    bl_label = "Gamepad Navigation"
    theta = 0
    analogMovementRate = 0.1

    _timer = None

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            return self.cancel(context)
        if event.type == 'TIMER':
            # Find a viewport
            # We check the context for screen areas, and specifically 3D viewports 
            # currentArea = [area for area in bpy.context.screen.areas if area.type == 'VIEW_3D']
            # if len(currentArea) == 0:
                    # return
            # Then we grab the Region3D view, which has camera-like data
            # viewport = currentArea[0].spaces.active.region_3d

            # Get the camera origin
            # cameraOrigin = numpy.array(camera.view_location)
            # inputForce = 0

            camera = context.scene.camera
            gamepad_data = context.scene.addon_gamepad
            rotationX = 0.0
            rotationY = 0.0
            rotationZ = 0.0
            navHorizontal = 0.0
            navVertical = 0.0
            navDepth = 0.0

            # Sync gamepad input
            for gamepad in devices.gamepads:
                events = gamepad.read()
                for event in events:
                    # print(gamepad.get_char_name(), event.ev_type, event.code, event.state)
                    match event.code:
                        case "ABS_HAT0Y":
                            if(event.state == -1):
                                navVertical = self.analogMovementRate
                                gamepad_data["up"] = True
                            elif(event.state == 1):
                                navVertical = -self.analogMovementRate
                                gamepad_data["down"] = True
                            elif(event.state == 0):
                                gamepad_data["up"] = False
                                gamepad_data["down"] = False
                        case "ABS_HAT0X":
                            if(event.state == -1):
                                navHorizontal = -self.analogMovementRate
                                gamepad_data["left"] = True
                            elif(event.state == 1):
                                navHorizontal = self.analogMovementRate
                                gamepad_data["right"] = True
                            elif(event.state == 0):
                                gamepad_data["left"] = False
                                gamepad_data["right"] = False
                        case "ABS_Y":
                            if(event.state != 0):
                                rotationY = math.radians(event.state / 30000)
                                # print("[GAMEPAD] Analog vertical Pressed", rotationY)
                        case "ABS_X":
                            if(event.state != 0):
                                rotationX = math.radians(event.state / 30000)
                                # print("[GAMEPAD] Analog horizontal Pressed", rotationX)
                        case "ABS_Z":
                            if(event.state != 0):
                                rotationZ = math.radians(event.state / 255)
                                # print("[GAMEPAD] Left Trigger Pressed", rotationZ)
                        case "ABS_RZ":
                            if(event.state != 0):
                                rotationZ = -math.radians(event.state / 255)
                                # print("[GAMEPAD] Left Trigger Pressed", rotationZ)
                        
            # newTheta = self.theta * inputForce
            # rotationMatrix = numpy.array(
            #     [
            #         [math.cos(newTheta), -math.sin(newTheta), 0],
            #         [math.sin(newTheta), math.cos(newTheta), 0],
            #         [0,0,1]
            #     ]
            # )
            # viewport.view_location = numpy.dot(cameraOrigin, rotationMatrix)
            # print("new location", numpy.dot(cameraOrigin, rotationMatrix))
            
            # Set camera rotation in euler angles
            camera.rotation_mode = 'XYZ'
            camera.rotation_euler[0] += rotationX
            camera.rotation_euler[1] += rotationY
            camera.rotation_euler[2] += rotationZ

            # Set camera translation
            camera.location.x += navHorizontal
            camera.location.y += navVertical
            camera.location.z += navDepth


        return {'PASS_THROUGH'}
    
    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        return {'FINISHED'}

# Menu item
def GI_gamepad_menu_item(self, context):
    self.layout.operator(GI_ModalOperator.bl_idname, text="Enable Gamepad Navigation")

# Register and add to the object menu (required to also use F3 search "Modal Operator" for quick access).
bpy.types.VIEW3D_MT_object.append(GI_gamepad_menu_item)

# Load/unload addon into Blender
classes = (
    GI_SceneProperties,
    GI_GamepadInputPanel,
    GI_gamepad,
    GI_ModalOperator,
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
    bpy.ops.object.modal_operator('EXEC_DEFAULT')
