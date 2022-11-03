# What?
HomeAssistant integration of a Eastron SDM72D-M V2 energy meter.  
With a few modifications, may also work on similar devices from their [MBUS-enabled energy meter range](http://eastrongroup.com).  
 
# Why?
Due to the device's included M-BUS interface, all reported measurements can be easily integrated in a HomeAssistant setup.

# How?
The current implementation revolves around polling the device via a RS485 and reporting the values via MQTT.  
As such, the Python script can be run on any computer present on the same local network as the HomeAssistant/MQTT broker.  
Hardware-wise, a UART port connected to a RS485 adapter (with RTS signal used for direction control) is the only required link to the meter.  

Edit the [`private_config.json`](scripts/private_config.json) file by configuring the:  
	- used MQTT broker (`HOSTNAME`, `USERNAME`, `PASSWORD`),  
	- used serial port `SERIAL_PORT`, energy meter M-BUS address `SLAVE_ADDRESS`, and sampling interval `SAMPLE_INTERVAL`.  
	- polled measurement(s) `SENSORS`, using the following syntax: `Measurement_name`: [`Register_start_address`, `Number_of_phases`], where:  
		- `Measurement_name` is the name reported to the HomeAssistant instance,  
		- `Register_start_address` the value of the first register address where the measurement is located, noted in the [`user manual`](docs/SDM72DM-V2.pdf) as `Modbus Protocol Start Address Hex Lo Byte`,  
		- `Number_of_phases` is the number of successive values related to the same measurement but on a different phase:  
		- Set to `3` if requesting for eg. `Phase 1 current`, `Phase 2 current`, `Phase 3 current`.  
		- If only a single value is reported (for eg. `Sum of line currents`) set to `1`.  

# Who/where/when?
All the reverse-engineering, development, integration, and documentation efforts are based on the latest software and hardware versions available at the time of writing (November 2022), and licensed under the GNU General Public License v3.0.
