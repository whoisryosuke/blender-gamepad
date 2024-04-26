![Example of Blender addon using DualSense gamepad](./screenshot.gif)

# Blender Gamepad Input Addon

An example of how to get gamepad and other device input (like MIDI maybe) and use it inside Blender.

> On some devices like Mac you may need to give elevated permissions to Blender to allow for plugin to work.

## Installation

1. Download as a zip
1. Open Blender
1. Go to Edit > Preferences and go to the Addons tab on left.
1. Click install button.
1. Select the zip you downloaded.
1. You can confirm it's installed by searching for "Gamepad" and seeing if it's checked off

## How to use

1. Turn on your controller before opening Blender.
1. You can test if the gamepad is working by going to the 3D Viewport and expanding the side menu, there's a panel for the gamepad with a "Test Gamepad button".
1. This button should vibrate the controller. If it's not vibrating it's not being detected.
1. You can also see a list of detected gamepads here

> If you're using a PlayStation controller on Windows, you'll need to use an app like DS4Windows to create an fake XInput profile. The `inputs` library uses XInput on Windows, which is the protocol for Xbox and other 3rd party controllers.

### Camera movement

1. Make sure your scene has a camera in it and set it as the active camera.
1. In a 3D Viewport, click the Object menu item and select "Enable Gamepad Navigation".

## How it works

Uses `inputs` Python library to get gamepad input data across all platforms (Windows, Linux, and Mac).

We get access to the gamepad anywhere anytime, you can see an example of this in the test vibration function.

The gamepad input is synced to Blender using a "modal operator" class with a built-in timer that runs every `0.1` seconds. This not only syncs, but handles any other input-based logic (like moving the camera).

## Credits

- [inputs](https://github.com/zeth/inputs) by @zeth
