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
import subprocess
import sys
import os

def lerp( a, b, alpha ):
    return a + alpha * ( b - a )


# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

sync_enabled = False


def defaultInput():
    return {
        "pressed": False,
        "velocity": 0,
    }

class MIDIInput():
    def __init__(self) -> None:

        # Initialize props to track gamepad input
        self.pressed = {
            "C": False,
            "C#": False,
            "D": False,
            "D#": False,
            "E": False,
            "F": False,
            "F#": False,
            "G": False,
            "G#": False,
            "A": False,
            "A#": False,
            "B": False,
        }
        self.velocity = {
            "C": 0,
            "C#": 0,
            "D": 0,
            "D#": 0,
            "E": 0,
            "F": 0,
            "F#": 0,
            "G": 0,
            "G#": 0,
            "A": 0,
            "A#": 0,
            "B": 0,
        }

        # Setup threads
        self._thread_flag= threading.Event() # used to pause thread
        self._thread= threading.Thread(target=self._sync_midi, args=(self._thread_flag,))
        self._thread.daemon = True # used to kill thread if Blender closes
        self._thread.start()

    def stop(self):
        self._thread_flag.set()

    def _sync_midi(self, thread_flag):
        # Create "infinite loop" while thread is flagged to run
        while not thread_flag.is_set():
            self._sync_midi_data()
    
    def _sync_midi_data(self):
        import rtmidi

        midiin = rtmidi.RtMidiIn()

        def print_message(midi):
            if midi.isNoteOn():
                print('ON: ', midi.getMidiNoteName(midi.getNoteNumber()), midi.getVelocity())
                fullNote = midi.getMidiNoteName(midi.getNoteNumber())
                velocity = midi.getVelocity()
                noteLetter = fullNote[:-1]
                print("Note saving: ", noteLetter)
                self.pressed[noteLetter] = True
                self.velocity[noteLetter] = velocity
                print("Note saved: ", self.pressed[noteLetter])

            elif midi.isNoteOff():
                print('OFF:', midi.getMidiNoteName(midi.getNoteNumber()))
            elif midi.isController():
                print('CONTROLLER', midi.getControllerNumber(), midi.getControllerValue())

        ports = range(midiin.getPortCount())
        if ports:
            for i in ports:
                print(midiin.getPortName(i))
            print("Opening port 0!") 
            midiin.openPort(0)
            while True:
                m = midiin.getMessage(250) # some timeout in ms
                if m:
                    print_message(m)
        else:
            print('NO MIDI INPUT PORTS!')

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

        row = layout.row()
        row.operator("wm.install_midi")
        
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

class GI_install_midi(bpy.types.Operator):
    """Test function for gamepads"""
    bl_idname = "wm.install_midi"
    bl_label = "Install dependencies"
    bl_description = "Installs necessary Python modules for MIDI input"

    def execute(self, context: bpy.types.Context):

        print("Installing MIDI library...") 
        python_exe = os.path.join(sys.prefix, 'bin', 'python.exe')
        target = os.path.join(sys.prefix, 'lib', 'site-packages')

        subprocess.call([python_exe, '-m', 'ensurepip'])
        subprocess.call([python_exe, '-m', 'pip', 'install', '--upgrade', 'pip'])

        subprocess.call([python_exe, '-m', 'pip', 'install', '--upgrade', 'rtmidi', '-t', target])

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

            midi_input = self.midi_input
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
            # if gamepad_input.up:
            #     navVertical = self.analogMovementRate

            ## Buttons
            # btn_cross_depth = 1 if gamepad_input.cross else 0
            
            # Save initial position as previous frame
            # if gamepad_input.left_analog_y > 0 and not self.btn_analog_left:
            #     self.btn_analog_left = True
            #     move_obj.keyframe_insert(data_path="rotation_euler", frame=current_frame - 1)
            # if gamepad_input.cross and not self.btn_cross_state:
            #     self.btn_cross_state = True
            #     gamepad_props.btn_cross.keyframe_insert(data_path="location", frame=current_frame - 1)

            # Rotate object
            ## Set object rotation in euler angles
            # move_obj.rotation_mode = 'XYZ'
            # move_obj.rotation_euler[0] = rotationX
            # move_obj.rotation_euler[1] = rotationY
            # move_obj.rotation_euler[2] = rotationZ

            # Move objects
            ## Face buttons
            # gamepad_props.btn_cross.location.z = btn_cross_depth


            # Make keyframes
            # We do this last after all the transformations to they can be stored

            # Analog left
            # if gamepad_input.left_analog_y > 0:
            #     move_obj.keyframe_insert(data_path="rotation_euler", frame=current_frame)
            # elif gamepad_input.left_analog_y == 0 and self.btn_analog_left:
            #     self.btn_analog_left = False
            #     move_obj.keyframe_insert(data_path="rotation_euler", frame=current_frame)

            # We compare the gamepad state to the internal state (so we can apply keyframes on press _and_ release)
            # Pressed
            # if gamepad_input.cross:
            #     gamepad_props.btn_cross.keyframe_insert(data_path="location", frame=current_frame)
            # # Released
            # if not gamepad_input.cross and self.btn_cross_state:
            #     self.btn_cross_state = False
            #     gamepad_props.btn_cross.keyframe_insert(data_path="location", frame=current_frame)



        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        # Create the timer
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        # Create the gamepad only when running modal
        # (only do this if you disable the global one below)
        self.midi_input = MIDIInput()

        # Save original position of objects
        # print("Saving position")
        # gamepad_props = context.scene.gamepad_props

        # Save initial keyframes (needed or else it starts as moved)
        # current_frame = context.scene.frame_current
        # gamepad_props.analog_left.keyframe_insert(data_path="rotation_euler", frame=current_frame)
        # gamepad_props.btn_cross.keyframe_insert(data_path="location", frame=current_frame)

        # Start animation
        bpy.ops.screen.animation_play()

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        # Remove timer
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

        # Release gamepad class and threads
        self.midi_input.stop()
        del self.midi_input

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
    GI_install_midi,
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
