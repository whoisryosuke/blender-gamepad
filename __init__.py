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
        self.left_analog = 0.0
        self.right_analog = 0.0
        self.l1 = False
        self.l2 = 0.0
        self.r1 = False
        self.r2 = 0.0
        self.cross = False #south
        self.square = False #west
        self.triangle = False #north
        self.circle = False #east
        self.start = False
        self.select = False
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
                    self.left_analog = self._normalize_btn_analog(event.state)
                case "ABS_X":
                    self.right_analog = self._normalize_btn_analog(event.state)
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
    
    # Objects to control
    obj_player: PointerProperty(
        name="Player Rig",
        description="The rig that animation actions will be assigned to",
        type=bpy.types.Object,
        )
    
    # Actions for objects
    action_movement: PointerProperty(
        name="Movement",
        description="Action for Left Analog or Movement Buttons",
        type=bpy.types.Action,
        )
    action_btn_cross: PointerProperty(
        name="Cross",
        description="Action for Cross (PS) / B (Nin) / A (Xbox)",
        type=bpy.types.Action,
        )
    action_btn_circle: PointerProperty(
        name="Circle",
        description="Action for Circle (PS) / A (Nin) / B (Xbox)",
        type=bpy.types.Action,
        )
    action_btn_triangle: PointerProperty(
        name="Triangle",
        description="Action for Triangle (PS) / X (Nin) / Y (Xbox)",
        type=bpy.types.Action,
        )
    action_btn_square: PointerProperty(
        name="Square",
        description="Action for Square (PS) / Y (Nin) / X (Xbox)",
        type=bpy.types.Action,
        )
    action_btn_start: PointerProperty(
        name="Start",
        description="Action for Options (PS) / Start (Nin) / Start (Xbox)",
        type=bpy.types.Action,
        )

# UI Panel
class GI_GamepadInputPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_category = "Gamepad"
    bl_label = "Gamepad Settings"
    bl_idname = "SCENE_PT_gamepad_panel"
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
        row = layout.row()
        row.operator("object.start_gamepad_sync")

        # Objects
        row = layout.row()
        row.prop(gamepad_props, "obj_player")

        # Actions
        row = layout.row()
        row.prop(gamepad_props, "action_movement")
        row = layout.row()
        row.prop(gamepad_props, "action_btn_cross")
        row = layout.row()
        row.prop(gamepad_props, "action_btn_circle")
        row = layout.row()
        row.prop(gamepad_props, "action_btn_triangle")
        row = layout.row()
        row.prop(gamepad_props, "action_btn_square")
        row = layout.row()
        row.prop(gamepad_props, "action_btn_start")


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


def create_animation_strip(player, current_frame, action):
    # Make sure we create a "slot" for animation data - if it doesn't exist we get errors
    if player.animation_data is None:
        player.animation_data_create()

    # Create new animation track ("NLA Track")
    new_track = player.animation_data.nla_tracks.new()
    strip_name = "cross.001"

    # Create new strip on that track and add action to it
    new_strip = new_track.strips.new(strip_name, current_frame, action)
    # We set extrapolation mode to NOTHING so it keeps playing (default is "HOLD" - freezing anim)
    new_strip.extrapolation = 'NOTHING'
    new_strip.blend_in = 1.2
    new_strip.blend_out = 1.2

    return new_strip

class GI_ModalOperator(bpy.types.Operator):
    """Gamepad syncing and camera movement"""
    bl_idname = "object.start_gamepad_sync"
    bl_label = "Gamepad Navigation"
    theta = 0
    analogMovementRate = 0.1
    jump_rate = 0.5

    _timer = None

    is_moving = False
    movement_strip = None
    btn_cross = False
    btn_cross_strip = None
    btn_circle = False
    btn_circle_strip = None


    def get_num_repeat(self, strip, current_frame):
        action_frame_count = strip.frame_end - strip.frame_start
        strip_frame_start = strip.frame_start
        check_frame_start = strip_frame_start + action_frame_count
        total_repeat_frames = current_frame - check_frame_start
        num_repeats = total_repeat_frames / action_frame_count
        
        return num_repeats

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            return self.cancel(context)
        if event.type == 'TIMER':

            camera = context.scene.camera
            current_frame = context.scene.frame_current
            last_frame = context.scene.frame_end
            fps = context.scene.render.fps
            # gamepad_input = context.scene.gamepad_input
            gamepad_input = self.gamepad

            # Props
            gamepad_props = context.scene.gamepad_props
            player = gamepad_props.obj_player
            action_btn_cross = gamepad_props.action_btn_cross
            action_btn_circle = gamepad_props.action_btn_circle
            action_movement = gamepad_props.action_movement

            # Local state
            rotationX = 0.0
            rotationY = 0.0
            rotationZ = 0.0
            navHorizontal = 0.0
            navVertical = 0.0
            is_jumping = gamepad_input.cross and not self.btn_cross
            is_landing = not gamepad_input.cross and self.btn_cross

            if gamepad_input.up:
                navVertical = -self.analogMovementRate
            if gamepad_input.down:
                navVertical = self.analogMovementRate
            if gamepad_input.left:
                navHorizontal = self.analogMovementRate
            if gamepad_input.right:
                navHorizontal = -self.analogMovementRate
            if is_jumping:
                print("Jumping!")
                player.keyframe_insert(data_path="location", frame=current_frame - fps/10)
                player.location.z += self.jump_rate
            if is_landing:
                player.keyframe_insert(data_path="location", frame=current_frame - fps/10)
                player.location.z -= self.jump_rate
            
            # Set camera rotation in euler angles
            # camera.rotation_mode = 'XYZ'
            # camera.rotation_euler[0] += rotationX
            # camera.rotation_euler[1] += rotationY
            # camera.rotation_euler[2] += rotationZ

            # Set camera translation
            player.location.x += navHorizontal
            player.location.y += navVertical

            # Not moving? Reset flag.
            if navHorizontal is 0.0 and navVertical is 0.0 and self.is_moving:
                self.is_moving = False

                # Update the last movement to repeat until this moment
                num_repeats = self.get_num_repeat(self.movement_strip, current_frame)
                self.movement_strip.repeat += num_repeats

            # Moving? 
            if navHorizontal != 0.0 or navVertical != 0.0 and not self.is_moving:
                self.is_moving = True

                # Create new strip on that track and add action to it
                self.movement_strip = create_animation_strip(player, current_frame, action_movement)
                

            # Save keyframes for movement
            if self.is_moving or is_jumping or is_landing:
                player.keyframe_insert(data_path="location", frame=current_frame)

            # Handle key presses
            # Cross
            if gamepad_input.cross and not self.btn_cross:
                # Update local state so we only assign action once per press (unless you want hold...)
                self.btn_cross = True

                self.btn_cross_strip = create_animation_strip(player, current_frame, action_btn_cross)

            if not gamepad_input.cross and self.btn_cross:
                # Update local state so we only assign action once per press (unless you want hold...)
                self.btn_cross = False
                num_repeats = self.get_num_repeat(self.btn_cross_strip, current_frame)
                self.btn_cross_strip.repeat += num_repeats

            # Circle
            if gamepad_input.circle and not self.btn_circle:
                # Update local state so we only assign action once per press (unless you want hold...)
                self.btn_circle = True

                self.btn_circle_strip = create_animation_strip(player, current_frame, action_btn_circle)

            if not gamepad_input.circle and self.btn_circle:
                # Update local state so we only assign action once per press (unless you want hold...)
                self.btn_circle = False
                num_repeats = self.get_num_repeat(self.btn_circle_strip, current_frame)
                self.btn_circle_strip.repeat += num_repeats




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
        player = context.scene.gamepad_props.obj_player

        # Save initial keyframes (needed or else it starts as moved)
        current_frame = context.scene.frame_current
        player.keyframe_insert(data_path="location", frame=current_frame)

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
