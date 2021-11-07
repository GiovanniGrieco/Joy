"""
Copyright 2020  Aircomm
SPDX-License-Identifier: MIT

Author: Giovanni Grieco <giovanni@grieco.dev>
"""
import collections
import time
import os
from threading import Thread

from scapy import sendrecv
from scapy.layers.inet import IP, UDP
from scapy.packet import Raw

"""
Importing SDL2 in Windows could lead to an ImportError if DLL is not found.
Let's force it to search in the current directory.
"""
if os.name == 'nt':
    os.environ['PYSDL2_DLL_PATH'] = os.curdir

import sdl2
import sdl2.ext


class JoystickController:
    """
    Control your DJI Tello drone using your Joystick, directly from your PC.
    Be sure that networking is already setup and the drone is reachable.
    """

    def __init__(self):
        """
        Initialize useful constants and routing mapping to setup controller actions.
        """
        self._running = True
        self._command_queue = collections.deque()

        ###
        # You may want to customize the constants and button mapping below
        # to suit your specific needs and Joystick characteristics.
        ###
        self._joystick = self._init_joystick()
        self._AXIS_DEAD = 2500
        self._AXIS_MAX_VAL = 32767
        self._axis_state = {
            'roll':  0,
            'quota': 0,
            'yaw':   0,
            'pitch': 0
        }
        self._event_map = {
            'SELECT':  self._land,
            'START':   self._takeoff,
            'A':       self._emergency_land,
            'Y':       self._command,
            'LEFT_X':  self._set_roll,
            'LEFT_Y':  self._set_pitch,
            'RIGHT_X': self._set_yaw,
            'RIGHT_Y': self._set_quota
        }
        self._button_map = ('A', 'B', 'X', 'Y', 'LB', 'RB', 'SELECT', 'START', 'JL', 'JR')
        self._axis_map = ('LEFT_X', 'LEFT_Y', 'LT', 'RIGHT_X', 'RIGHT_Y', 'RT')

        print(f'Connected to {sdl2.SDL_JoystickName(self._joystick).decode()}')

    def run(self):
        """
        Main runtime procedure.
        Manage threads, an empty loop and shutdown procedure in case of program termination.
        """
        threads = (
            Thread(target=self._receive_command_loop, daemon=True),
            Thread(target=self._send_command_loop, daemon=False),
        )

        for t in threads:
            t.start()

        self._run_loop()

        # if we exit from the run loop for some reason, shutdown
        self._command_queue.clear()
        self._land()

        for t in threads:
            t.join()

    @staticmethod
    def _init_joystick():
        """
        Initialize joystick using SDL library. Note that it is automatically
        chosen the first enumerated joystick.

        Returns
        -------
        The SDL Joystick object.
        """
        sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK)

        njoysticks = sdl2.SDL_NumJoysticks()
        if njoysticks < 1:
            raise RuntimeError(f'No joysticks connected!')

        print('Joysticks available:')
        for i in range(njoysticks):
            joy = sdl2.SDL_JoystickOpen(i)
            print(f'  - {sdl2.SDL_JoystickName(joy).decode()}')

        return sdl2.SDL_JoystickOpen(0)

    def _run_loop(self):
        """
        Main running loop, just to check and handle interrupt signal.
        """
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self._running = False

    def _receive_command_loop(self):
        """
        Manage Joystick events and call their mapped function.
        """
        while self._running:
            for event in sdl2.ext.get_events():
                try:
                    if event.type == sdl2.SDL_JOYBUTTONDOWN:
                        self._event_map[self._button_map[event.jbutton.button]]()
                    elif event.type == sdl2.SDL_JOYAXISMOTION:
                        if abs(event.jaxis.value) > self._AXIS_DEAD:
                            self._event_map[self._axis_map[event.jaxis.axis]](event.jaxis.value)
                except KeyError:
                    pass

    def _send_command_loop(self):
        """
        Handle command execution using hard real-time, FCFS-based scheduling policy.
        """
        while self._running:
            try:
                cmd = self._command_queue.pop()

                answer = sendrecv.sr1(IP(dst='192.168.10.1') / UDP(dport=8889) / cmd,
                                      verbose=1,
                                      timeout=0.2)
                try:
                    response = answer[Raw].load.decode()
                    print(f'EXE {cmd}: {response}')
                except TypeError:
                    print(f'EXE {cmd}: unknown')
                    continue

            except IndexError:  # nothing to schedule, retry another time
                time.sleep(0.5)
                continue

    def _command(self):
        """
        Take control of the DJI Tello.
        """
        print('Pressed Command button')
        self._command_queue.append('command')

    def _land(self, force=False):
        """
        Schedule drone landing.

        Parameters
        ----------
        force: clear out FCFS queue, in case of absolute necessity.
        """
        print('Pressed Land button')
        if force:
            self._command_queue.clear()

        self._command_queue.append('land')

    def _emergency_land(self):
        """
        Schedule drone emergency landing.
        Caution: don't harm the drone!
        """
        self._command_queue.clear()
        self._command_queue.append('emergency')

    def _takeoff(self):
        """
        Schedule drone takeoff.
        Note: if drone is not taking off, check your battery charge level!
        """
        print('Pressed Takeoff button')
        self._command_queue.append('takeoff')

    def _set_roll(self, raw_val):
        """
        Set roll axis value.
        """
        val = int(raw_val * 100 / self._AXIS_MAX_VAL)

        if self._axis_state['roll'] != val:
            self._axis_state['roll'] = val
            self._dispatch_axis_update()

    def _set_quota(self, raw_val):
        """
        Set quota axis value.
        """
        val = -int(raw_val * 100 / self._AXIS_MAX_VAL)

        if self._axis_state['quota'] != val:
            self._axis_state['quota'] = val
            self._dispatch_axis_update()

    def _set_yaw(self, raw_val):
        """
        Set yaw axis value.
        """
        val = int(raw_val * 100 / self._AXIS_MAX_VAL)

        if self._axis_state['yaw'] != val:
            self._axis_state['yaw'] = val
            self._dispatch_axis_update()

    def _set_pitch(self, raw_val):
        """
        Set pitch axis value.
        """
        val = -int(raw_val * 100 / self._AXIS_MAX_VAL)

        if self._axis_state['pitch'] != val:
            self._axis_state['pitch'] = val
            self._dispatch_axis_update()

    def _dispatch_axis_update(self):
        """
        Schedule an update of the pitch-roll-quota-yaw of the drone, tipically
        managed using Joystick analog sticks.
        """
        # print(f'RC: {self._axis_state}')  # Caution: this message is highly frequent
        self._command_queue.append(f'rc {self._axis_state["roll"]} '
                                   f'{self._axis_state["pitch"]} '
                                   f'{self._axis_state["quota"]} '
                                   f'{self._axis_state["yaw"]}')


if __name__ == '__main__':
    print(f'This is Joy - Copyright 2020  Aircomm')
    ctrl = JoystickController()
    ctrl.run()
