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
import threading
import numpy
import math
import mathutils

def lerp( a, b, alpha ):
    return a + alpha * ( b - a )


# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

sync_enabled = False

class GamepadInput():
    def __init__(self, index) -> None:
        # Initialize props to track gamepad input
        self.up = False
        self.down = False
        self.left = False
        self.right = False
        self.left_analog_x = 0.0
        self.left_analog_y = 0.0
        self.right_analog_x = 0.0
        self.right_analog_y = 0.0
        self.l1 = False
        self.l2 = 0.0
        self.r1 = False
        self.r2 = 0.0
        self.cross = False #south
        self.square = False #west
        self.triangle = False #north
        self.circle = False #east
        self.start = False # I refuse to acknowledge "option". start for life.
        self.select = False # aka share
        self.home = False
        self.touchpad = False

        self.gamepad_index = index
        
        # Setup threads
        self._thread_flag= threading.Event() # used to pause thread
        self._thread= threading.Thread(target=self._sync_gamepad, args=(self._thread_flag,))
        self._thread.daemon = True # used to kill thread if Blender closes
        self._thread.start()


    def stop(self):
        self._thread_flag.set()

    def _sync_gamepad(self, thread_flag):
        # Create "infinite loop" while thread is flagged to run
        while not thread_flag.is_set():
            self._sync_gamepad_data()
    
    def _sync_gamepad_data(self):
        # Sync gamepad input
        gamepad = devices.gamepads[self.gamepad_index]
        events = gamepad.read()
        for event in events:
            print(gamepad.get_char_name(), event.ev_type, event.code, event.state)
            match event.code:
                case "ABS_HAT0Y":
                    if(event.state == -1):
                        self.up = True
                    elif(event.state == 1):
                        self.down = True
                    elif(event.state == 0):
                        self.up = False
                        self.down = False
                case "ABS_HAT0X":
                    if(event.state == -1):
                        self.left = True
                    elif(event.state == 1):
                        self.right = True
                    elif(event.state == 0):
                        self.left = False
                        self.right = False
                case "ABS_Y":
                    self.left_analog_x = self._normalize_btn_analog(event.state)
                case "ABS_X":
                    self.left_analog_y = self._normalize_btn_analog(event.state)
                case "ABS_RY":
                    self.right_analog_x = self._normalize_btn_analog(event.state)
                case "ABS_RX":
                    self.right_analog_y = self._normalize_btn_analog(event.state)
                case "ABS_Z":
                    self.l2 = self._normalize_btn_trigger(event.state)
                case "ABS_RZ":
                    self.r2 = self._normalize_btn_trigger(event.state)
                case "BTN_SOUTH":
                    self.cross = self._normalize_btn_bool(event.state)
                case "BTN_NORTH":
                    self.triangle = self._normalize_btn_bool(event.state)
                case "BTN_WEST":
                    self.square = self._normalize_btn_bool(event.state)
                case "BTN_EAST":
                    self.circle = self._normalize_btn_bool(event.state)
                case "BTN_TL":
                    self.l1 = self._normalize_btn_bool(event.state)
                case "BTN_TR":
                    self.r1 = self._normalize_btn_bool(event.state)
                case "BTN_SELECT":
                    self.start = self._normalize_btn_bool(event.state)
                case "BTN_START":
                    self.select = self._normalize_btn_bool(event.state)

    def _normalize_btn_bool(self, state):
        return True if state == 1 else False
    
    def _normalize_btn_analog(self, state):
        """Takes analog stick input and normalizes it to 0 - 1"""
        return state / 30000
    
    def _normalize_btn_trigger(self, state):
        """Takes trigger input and normalizes it to 0 - 1"""
        return state / 255

# Creates dropdown items formatted as an array of tuples
def gamepad_items(self, context):
    items = [(str(index), gamepad.get_char_name(), "") for index, gamepad in enumerate(devices.gamepads)]
    return items

# UI properties
class GI_SceneProperties(PropertyGroup):
        
    active_gamepad: EnumProperty(
        name="Active Gamepad",
        description="Gamepad used for control",
        items=gamepad_items
        )
        
    analog_left: PointerProperty(
        name="Analog Left",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
        
    btn_cross: PointerProperty(
        name="Cross button",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
        
    btn_circle: PointerProperty(
        name="Circle button",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
        
    btn_triangle: PointerProperty(
        name="Triangle button",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
        
    btn_square: PointerProperty(
        name="Square button",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
        
    btn_l1: PointerProperty(
        name="L1 button",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
        
    btn_r1: PointerProperty(
        name="R1 button",
        description="Object to be controlled",
        type=bpy.types.Object,
        )

# UI Panel
class GI_GamepadInputPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_category = "Gamepad"
    bl_label = "Gamepad Settings"
    bl_idname = "SCENE_PT_gamepad"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    # bl_context = "output"
    
    def draw(self, context):
        layout = self.layout

        scene = context.scene
        gamepad_props = scene.gamepad_props
        
        # TODO: Specify active gamepad from list
        layout.label(text="Select gamepad")
        # row = layout.row()
        # row.operator("wm.refresh_gamepads")
        row = layout.row()
        row.prop(gamepad_props, "active_gamepad")

        layout.label(text="Debug")
        row = layout.row()
        row.operator("wm.test_gamepad")

        layout.label(text="Controls")
        row = layout.row()
        row.prop(gamepad_props, "analog_left")
        row = layout.row()
        row.prop(gamepad_props, "btn_cross")
        row = layout.row()
        row.prop(gamepad_props, "btn_circle")
        row = layout.row()
        row.prop(gamepad_props, "btn_triangle")
        row = layout.row()
        row.prop(gamepad_props, "btn_square")
        row = layout.row()
        row.prop(gamepad_props, "btn_l1")
        row = layout.row()
        row.prop(gamepad_props, "btn_r1")


class GI_gamepad(bpy.types.Operator):
    """Test function for gamepads"""
    bl_idname = "wm.test_gamepad"
    bl_label = "Test Gamepad"
    bl_description = "Vibrates active gamepad and shows data in console"

    def execute(self, context: bpy.types.Context):

        print("Finding gamepads...")
        current_gamepad = context.scene.gamepad_props.active_gamepad
        print("active gamepad", current_gamepad)
        try:
            devices.gamepads[int(current_gamepad)].set_vibration(0.5, 0.5, 420)
        except: 
            print("Couldn't vibrate gamepad.")

        return {"FINISHED"}


class GI_ModalOperator(bpy.types.Operator):
    """Gamepad syncing and camera movement"""
    bl_idname = "object.modal_operator"
    bl_label = "Gamepad Navigation"
    theta = 0
    analogMovementRate = 0.1
    analog_frame = 0
    btn_analog_left = False
    btn_cross_state = False

    # Timer used for modal
    _timer = None

    # Objects
    _obj_analog_left = None

    def modal(self, context, event):
        current_frame = context.scene.frame_current
        last_frame = context.scene.frame_end
        if event.type in {'RIGHTMOUSE', 'ESC'} or current_frame >= last_frame:
            return self.cancel(context)
        if event.type == 'TIMER':
            camera = context.scene.camera
            gamepad_props = context.scene.gamepad_props
            
            move_obj = gamepad_props.analog_left

            gamepad_input = self.gamepad
            rotationX = 0.0
            rotationY = 0.0
            rotationZ = 0.0
            navHorizontal = 0.0
            navVertical = 0.0
            navDepth = 0.0
            btn_cross_depth = 0.0
            btn_circle_depth = 0.0
            btn_triangle_depth = 0.0
            btn_square_depth = 0.0
            btn_l1_depth = 0.0
            btn_r1_depth = 0.0

            # Get input
            ## D-pad
            if gamepad_input.up:
                navVertical = self.analogMovementRate
            if gamepad_input.down:
                navVertical = -self.analogMovementRate
            if gamepad_input.left:
                navHorizontal = self.analogMovementRate
            if gamepad_input.right:
                navHorizontal = -self.analogMovementRate
            
            ## Left analog stick
            rotationY = math.radians(gamepad_input.left_analog_y * 30)
            rotationX = math.radians(gamepad_input.left_analog_x * 30)

            ## Buttons
            btn_cross_depth = 1 if gamepad_input.cross else 0
            btn_circle_depth = 1 if gamepad_input.circle else 0
            btn_triangle_depth = 1 if gamepad_input.triangle else 0
            btn_square_depth = 1 if gamepad_input.square else 0
            btn_l1_depth = 1 if gamepad_input.l1 else 0
            btn_r1_depth = 1 if gamepad_input.r1 else 0
            
            # Save initial position as previous frame
            if gamepad_input.left_analog_y > 0 and not self.btn_analog_left:
                self.btn_analog_left = True
                move_obj.keyframe_insert(data_path="rotation_euler", frame=current_frame - 1)
            if gamepad_input.cross and not self.btn_cross_state:
                self.btn_cross_state = True
                gamepad_props.btn_cross.keyframe_insert(data_path="location", frame=current_frame - 1)

            # Calculate camera
            ## Set camera rotation in euler angles
            move_obj.rotation_mode = 'XYZ'
            move_obj.rotation_euler[0] = rotationX
            move_obj.rotation_euler[1] = rotationY
            move_obj.rotation_euler[2] = rotationZ

            # Set camera translation
            # move_obj.location.x += navHorizontal
            # move_obj.location.y += navVertical
            # move_obj.location.z += navDepth

            # Move objects
            ## Face buttons
            gamepad_props.btn_cross.location.z = btn_cross_depth
            gamepad_props.btn_circle.location.z = btn_circle_depth
            gamepad_props.btn_triangle.location.z = btn_triangle_depth
            gamepad_props.btn_square.location.z = btn_square_depth
            ## Triggers
            gamepad_props.btn_l1.location.z = btn_l1_depth
            gamepad_props.btn_r1.location.z = btn_r1_depth


            # Make keyframes
            # We do this last after all the transformations to they can be stored

            # Analog left
            if gamepad_input.left_analog_y > 0:
                move_obj.keyframe_insert(data_path="rotation_euler", frame=current_frame)
            elif gamepad_input.left_analog_y == 0 and self.btn_analog_left:
                self.btn_analog_left = False
                move_obj.keyframe_insert(data_path="rotation_euler", frame=current_frame)

            # We compare the gamepad state to the internal state (so we can apply keyframes on press _and_ release)
            # Pressed
            if gamepad_input.cross:
                gamepad_props.btn_cross.keyframe_insert(data_path="location", frame=current_frame)
            # Released
            if not gamepad_input.cross and self.btn_cross_state:
                self.btn_cross_state = False
                gamepad_props.btn_cross.keyframe_insert(data_path="location", frame=current_frame)



        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        # Create the timer
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        # Create the gamepad only when running modal
        # (only do this if you disable the global one below)
        self.gamepad = GamepadInput(int(context.scene.gamepad_props.active_gamepad))

        # Save original position of objects
        print("Saving position")
        gamepad_props = context.scene.gamepad_props
        move_obj = gamepad_props.analog_left

        self._obj_analog_left = move_obj.location


        # Save initial keyframes (needed or else it starts as moved)
        current_frame = context.scene.frame_current
        gamepad_props.analog_left.keyframe_insert(data_path="rotation_euler", frame=current_frame)
        gamepad_props.btn_cross.keyframe_insert(data_path="location", frame=current_frame)

        # Start animation
        bpy.ops.screen.animation_play()

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        # Remove timer
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

        # Release gamepad class and threads
        self.gamepad.stop()
        del self.gamepad

        # Cancel animation
        bpy.ops.screen.animation_cancel()

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

    bpy.types.Scene.gamepad_props = PointerProperty(type=GI_SceneProperties)
    # If you wanted global gamepad input, you can enable it here
    # to be active all the time instead of only when modal is running
    # bpy.types.Scene.gamepad_input = GamepadInput()

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    # del bpy.types.Scene.gamepad_input


if __name__ == "__main__":
    register()
