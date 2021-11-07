import os

"""
Importing SDL2 in Windows could lead to an ImportError if DLL is not found.
Let's force it to search in the current directory.
"""
if os.name == 'nt':
    os.environ['PYSDL2_DLL_PATH'] = os.curdir

import sdl2
import events

def onJoystickMotion(event, world):
    print('axis motion')

sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK)

njoysticks = sdl2.SDL_NumJoysticks()
if njoysticks < 1:
    raise RuntimeError(f'No joysticks connected!')

print('Joysticks available:')
for i in range(njoysticks):
    joy = sdl2.SDL_JoystickOpen(i)
    print(f'  - {sdl2.SDL_JoystickName(joy).decode()}')

joy = sdl2.SDL_JoystickOpen(0)


