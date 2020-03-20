# Joy

Joy is a simple tool to control your DJI Tello drone using your Joystick and PC.

Simplicity is the key of this tool: it does not offer telemetry and/or video feedback.

## Requirements
* Python 3.6+ due to [PEP498 Usage](https://docs.python.org/3.6/whatsnew/3.6.html#whatsnew36-pep498)
* SDL Library - Windows shared library is already included, for Linux and macOS please check your package manager of reference.
* Python modules listed in [requirements.txt](requirements.txt)

## Setup
```
pip install -r requirements.txt
python joy.py
```
In case you run Windows, please execute `run.ps1` using PowerShell after python module installation.

This setup has been tested successfully on Windows 10 version 1909 and an Xbox One Controller.

## Caveats
### My CPU is burning like hell!
Please calibrate `AXIS_DEAD` according to your Joystick of reference. High CPU usage means that a high volume of analog stick events are triggered by the Joystick. Each event corresponds to a new command to be scheduled and sent to the drone. `AXIS_DEAD` permit to filter out small and involountary movements of the sticks.
