# WiFi Human Detection

ESP32 + Wi-Fi router CSI human-presence detection. C++ runs on ESP32; Python handles collection, preprocessing, ML/DL, and inference.

## Software flow
Router -> ESP32 CSI -> USB Serial -> Python -> preprocessing -> ML/DL -> HUMAN / NO HUMAN

## Current status
The Python pipeline is ready to test without hardware using the CSI simulator. The ESP32 CSI callback is a hardware-specific placeholder until the exact ESP32 model is known.

## Quick start
```powershell
cd wifi-human-detection-project
py -m pip install -r python/requirements.txt
py python/collector/simulator.py
py python/dataset/create_dataset.py
py python/training/train.py
py python/evaluation/evaluate.py
```

Use `py python/visualize.py` to view simulated CSI. Later, replace simulated CSV files with real ESP32 CSI recordings.
