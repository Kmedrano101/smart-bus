# Support for smart-BUS G4 Devices

This project aims to provide support for smart-BUS G4 devices to work on Home Assistant by Google. It allows for communication and control of these devices, enabling integration with other systems or applications. The project focuses on implementing operations for relays and sensors commonly used in smart-BUS G4 systems.

## List of Operations Codes

### Relays

- Single Channel Control:
  - Operation Code: 0x0031
  - Response Code: 0x0032 (add 0FEEEEEEEE at the beginning)

- Read Status of Channels:
  - Operation Code: 0x0033
  - Response Code: 0x0034 (add 0BEEEEEEEE at the beginning)

## Protocol Information

For detailed protocol information and specifications, please refer to the official smart-BUS G4 protocols documentation available at [www.smarthomebus.com/downloads-7-protocols.html](www.smarthomebus.com/downloads-7-protocols.html).

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


## Contributing

Contributions are welcome! If you would like to contribute to this project, please follow the guidelines for contributions. You can open an issue to report bugs or suggest enhancements, or submit a pull request with your proposed changes.

## License

This project is licensed under the [MIT License](LICENSE). Please see the LICENSE file for more details.

## Contact

If you have any questions or need further assistance regarding this project, please feel free to contact the author, Kmedrano101, at [kevin.ejem18@gmail.com](mailto:kevin.ejem18@gmail.com).


