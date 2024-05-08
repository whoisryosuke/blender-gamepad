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
                self.save_input(midi, True);

            elif midi.isNoteOff():
                print('OFF:', midi.getMidiNoteName(midi.getNoteNumber()))
                self.save_input(midi, False);
            
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

    def save_input(self, midi, pressed):
        # We grab the note data. This returns a note like C#2
        fullNote = midi.getMidiNoteName(midi.getNoteNumber())
        velocity = midi.getVelocity()

        # We shave off the octave to focus on the base note (aka the "letter" like "C")
        noteLetter = fullNote[:-1]
        print("Note saving: ", noteLetter)

        # Save internal input
        self.pressed[noteLetter] = pressed
        self.velocity[noteLetter] = velocity
        print("Note saved: ", self.pressed[noteLetter])

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
        
    active_midi: EnumProperty(
        name="Active MIDI",
        description="MIDI used for control",
        items=gamepad_items
        )
        
    obj_c: PointerProperty(
        name="C",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
        
    obj_d: PointerProperty(
        name="D",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
        
    obj_e: PointerProperty(
        name="E",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
        
    obj_f: PointerProperty(
        name="F",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
        
    obj_g: PointerProperty(
        name="G",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
        
    obj_a: PointerProperty(
        name="A",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
        
    obj_b: PointerProperty(
        name="B",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
        
    obj_csharp: PointerProperty(
        name="C#",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
        
    obj_dsharp: PointerProperty(
        name="D#",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
    
    obj_fsharp: PointerProperty(
        name="F#",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
    
    obj_gsharp: PointerProperty(
        name="G#",
        description="Object to be controlled",
        type=bpy.types.Object,
        )
    
    obj_asharp: PointerProperty(
        name="A#",
        description="Object to be controlled",
        type=bpy.types.Object,
        )

# UI Panel
class GI_GamepadInputPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_category = "MIDI"
    bl_label = "MIDI Settings"
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
        
        # TODO: Specify active MIDI from list
        # layout.label(text="Select MIDI")
        # row = layout.row()
        # row.operator("wm.refresh_gamepads")
        # row = layout.row()
        # row.prop(gamepad_props, "active_midi")

        layout.label(text="Controls")
        row = layout.row()
        row.prop(gamepad_props, "obj_c")
        row = layout.row()
        row.prop(gamepad_props, "obj_d")
        row = layout.row()
        row.prop(gamepad_props, "obj_e")
        row = layout.row()
        row.prop(gamepad_props, "obj_f")
        row = layout.row()
        row.prop(gamepad_props, "obj_g")
        row = layout.row()
        row.prop(gamepad_props, "obj_a")
        row = layout.row()
        row.prop(gamepad_props, "obj_csharp")
        row = layout.row()
        row.prop(gamepad_props, "obj_dsharp")
        row = layout.row()
        row.prop(gamepad_props, "obj_fsharp")
        row = layout.row()
        row.prop(gamepad_props, "obj_gsharp")
        row = layout.row()
        row.prop(gamepad_props, "obj_asharp")



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
    """Syncs MIDI input to object animation"""
    bl_idname = "object.modal_operator"
    bl_label = "MIDI Navigation"
    theta = 0
    analogMovementRate = 0.1
    analog_frame = 0
    btn_analog_left = False
    pressed = {
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
            gamepad_props = context.scene.gamepad_props
            
            midi_input = self.midi_input

            ## Buttons
            for noteLetter in self.pressed: 
                self.move_note(midi_input, gamepad_props, noteLetter, current_frame)

        return {'RUNNING_MODAL'}
    
    def move_note(self, midi_input, gamepad_props, noteLetter, current_frame):
        ## Buttons
        btn_c_depth = 1 if midi_input.pressed[noteLetter] else 0
        move_obj = self.get_note_obj(gamepad_props, noteLetter)

        if move_obj == None:
            return;
        
        # Save initial position as previous frame
        if midi_input.pressed[noteLetter] and not self.pressed[noteLetter]:
            self.pressed[noteLetter] = True
            move_obj.keyframe_insert(data_path="location", frame=current_frame - 1)

        # Move objects
        ## Face buttons
        move_obj.location.z = btn_c_depth

        # Make keyframes
        # We do this last after all the transformations to they can be stored

        # We compare the gamepad state to the internal state (so we can apply keyframes on press _and_ release)
        # Pressed
        if midi_input.pressed[noteLetter]:
            move_obj.keyframe_insert(data_path="location", frame=current_frame)
        # Released
        if not midi_input.pressed[noteLetter] and self.pressed[noteLetter]:
            self.pressed[noteLetter] = False
            move_obj.keyframe_insert(data_path="location", frame=current_frame)

    def get_note_obj(self, gamepad_props, noteLetter):
        if noteLetter == "C":
            return gamepad_props.obj_c
        if noteLetter == "D":
            return gamepad_props.obj_d
        if noteLetter == "E":
            return gamepad_props.obj_e
        if noteLetter == "F":
            return gamepad_props.obj_f
        if noteLetter == "G":
            return gamepad_props.obj_g
        if noteLetter == "A":
            return gamepad_props.obj_a
        if noteLetter == "B":
            return gamepad_props.obj_b
        if noteLetter == "C#":
            return gamepad_props.obj_csharp
        if noteLetter == "D#":
            return gamepad_props.obj_dsharp
        if noteLetter == "F#":
            return gamepad_props.obj_fsharp
        if noteLetter == "G#":
            return gamepad_props.obj_gsharp
        if noteLetter == "A#":
            return gamepad_props.obj_asharp

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
def GI_midi_menu_item(self, context):
    self.layout.operator(GI_ModalOperator.bl_idname, text="Enable MIDI Recording")

# Register and add to the object menu (required to also use F3 search "Modal Operator" for quick access).
bpy.types.VIEW3D_MT_object.append(GI_midi_menu_item)

# Load/unload addon into Blender
classes = (
    GI_SceneProperties,
    GI_GamepadInputPanel,
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
