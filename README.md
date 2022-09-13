# smart-bus
Smart-Bus home assistant integration for G4 devices

# Config Yaml

smartg4:

switch:
    - platform: smartg4
      reles:
       4:
        name: Rele1
        device_id: 27
           
light:
    - platform: smartg4
      dimmers:
       1:
        name: Dimmer1
        device_id: 27
