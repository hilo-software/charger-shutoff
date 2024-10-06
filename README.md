# Charger Shutoff
## Summary
- Python script which works with a TP-Link Smart Plug to detect when charging a device is complete and shutdown the plug.
## Purpose
- Shutting down the power output of a Smart Plug effectively unplugs the charger.
- Save wear and tear on the charger.
- Save potential leakage on the charged device after full charge is attained.
- Reduce likelihood of fire.
## Prerequisites
- TP-Link Smart Plug with Emeter (Energy meter) capability
  - The KP115 Smart Plug and the HS300 Smart Strip models are compatible
- The target plug must have an alias name assigned to it.
- Kasa python library to access TP-Link Smart Plug features from python
## How it works
The script looks at the power draw of the TP-Link plug and based on the measured power draw, shuts off the plug once the chargers power draw drops below the CUTOFF_POWER limit.
## Usage
- Plug charger into device
- Turn on smart plug and verify charging is occurring
- On any PC that supports command line Python 3.6.1 or above, run the shutoff_plug.py script with the name of the smart plug.
- For example with a plug named test01:
```
$ ./scripts/shutoff_plug.py test01
```
## Sample Run
```
$ ./scripts/shutoff_plug.py test01
2024-10-05 15:21:53 - __main__ - INFO - >>>>> START plug: test01 <<<<<
2024-10-05 15:21:58 - __main__ - INFO - plug: test01, power: 15.398
2024-10-05 15:21:58 - __main__ - INFO - is_charging: power: 15.398
2024-10-05 15:26:58 - __main__ - INFO - is_charging: power: 15.522
2024-10-05 15:31:58 - __main__ - INFO - is_charging: power: 15.563
2024-10-05 15:36:58 - __main__ - INFO - is_charging: power: 15.744
2024-10-05 15:41:59 - __main__ - INFO - is_charging: power: 15.769
2024-10-05 15:46:59 - __main__ - INFO - is_charging: power: 15.853
2024-10-05 15:51:59 - __main__ - INFO - is_charging: power: 15.973
2024-10-05 15:56:59 - __main__ - INFO - is_charging: power: 16.126
2024-10-05 16:01:59 - __main__ - INFO - is_charging: power: 16.127
2024-10-05 16:06:59 - __main__ - INFO - is_charging: power: 16.878
2024-10-05 16:11:59 - __main__ - INFO - is_charging: power: 16.805
2024-10-05 16:17:00 - __main__ - INFO - is_charging: power: 14.444
2024-10-05 16:22:00 - __main__ - INFO - is_charging: power: 9.518
2024-10-05 16:27:00 - __main__ - INFO - is_charging: power: 5.871
2024-10-05 16:32:00 - __main__ - INFO - is_charging: power: 3.235
2024-10-05 16:37:00 - __main__ - INFO - is_charging: power: 2.009
2024-10-05 16:37:00 - __main__ - INFO - plug is off: True
2024-10-05 16:37:00 - __main__ - INFO - >>>>> FINI plug: test01, status: True <<<<<
```
