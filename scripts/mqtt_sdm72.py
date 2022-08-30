import json
import logging
import struct
import time

import paho.mqtt.publish as publish
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

PRIVATE_CONFIG = {}


def mqtt_publish(topic, payload, retain):
    publish.single(hostname=PRIVATE_CONFIG['MQTT']['HOSTNAME'], port=1883, client_id='sdm72',
                   auth={'username': PRIVATE_CONFIG['MQTT']['USERNAME'],
                         'password': PRIVATE_CONFIG['MQTT']['PASSWORD']},
                   topic=topic, payload=json.dumps(payload), retain=retain)


def mqtt_discovery(sn):
    dev_cfg = {"name": '',
               "state_topic": 'homeassistant/sensor/SDM72/state',
               "value_template": '',
               "device_class": '',
               "state_class": '',
               "unit_of_measurement": '',
               "expire_after": sample_interval * 2}
    for param in PRIVATE_CONFIG['SDM72']['SENSORS'].keys():
        dev_cfg['state_class'] = 'measurement'
        param_type = param.split('_')
        value_template = ' )'
        if 'VOLTAGE' == param_type[0]:
            dev_cfg['device_class'] = 'voltage'
            dev_cfg['unit_of_measurement'] = 'V'
        elif 'CURRENT' == param_type[0]:
            dev_cfg['device_class'] = 'current'
            dev_cfg['unit_of_measurement'] = 'A'
        elif 'FREQUENCY' == param_type[0]:
            dev_cfg['device_class'] = 'frequency'
            dev_cfg['unit_of_measurement'] = 'Hz'
        elif 'POWER' == param_type[0]:
            if 'ACTIVE' == param_type[1]:
                param_class = 'power'
                param_unit = 'W'
            elif 'APPARENT' == param_type[1]:
                param_class = 'apparent_power'
                param_unit = 'VA'
            elif 'REACTIVE' == param_type[1]:
                param_class = 'reactive_power'
                param_unit = 'VAr'
            elif 'FACTOR' == param_type[1]:
                param_class = 'power_factor'
                param_unit = '%'
                value_template = ' | float * 100.0 ) | round(3)'
            else:
                continue
            dev_cfg['device_class'] = param_class
            dev_cfg['unit_of_measurement'] = param_unit
        elif 'ENERGY' == param_type[0]:
            if 'ACTIVE' == param_type[1]:
                param_unit = 'kWh'
            elif 'REACTIVE' == param_type[1]:
                param_unit = 'kVArh'
            else:
                continue
            dev_cfg['state_class'] = 'total_increasing'
            dev_cfg['device_class'] = 'energy'
            dev_cfg['unit_of_measurement'] = param_unit
        else:
            continue
        phase_count = PRIVATE_CONFIG['SDM72']['SENSORS'][param][1]
        for count in range(phase_count):
            reg_addr = PRIVATE_CONFIG['SDM72']['SENSORS'][param][0] + count * 2
            if 1 != phase_count:
                param_name = param + '_L' + str(count + 1)
            else:
                param_name = param
            dev_cfg['name'] = 'SDM72_' + param_name
            dev_cfg['value_template'] = '{{ ( value_json.' + param_name + value_template + ' }}'
            dev_cfg['unique_id'] = sn + str(reg_addr)
            meter_param_addr[reg_addr] = param_name
            meter_params_value[param_name] = 0
            mqtt_publish('homeassistant/sensor/SDM72_' + param_name + '/config', dev_cfg, True)


if __name__ == '__main__':
    modbus = ModbusClient()
    try:
        logging.info('INIT')
        meter_param_addr = {}
        meter_params_value = {}
        f = open('private_config.json')
        PRIVATE_CONFIG = json.load(f)
        sensor_values = {}
        f.close()
        if bool(PRIVATE_CONFIG['MQTT']):
            pass
        sample_interval = PRIVATE_CONFIG['SDM72']['SAMPLE_INTERVAL']
        unit_addr = PRIVATE_CONFIG['SDM72']['SLAVE_ADDRESS']
        modbus = ModbusClient(method='rtu', port=PRIVATE_CONFIG['SDM72']['SERIAL_PORT'], baudrate=19200, parity='E')
        modbus.connect()
        result = modbus.read_holding_registers(address=0xFC00, count=2, unit=unit_addr).registers
        print(result)
        serial_num = str((result[0] << 16) + result[1])
        mqtt_discovery(sn=serial_num)

        reg_list = list(meter_param_addr.keys())
        reg_gaps = [[s, e] for s, e in zip(reg_list, reg_list[1:]) if s + 2 < e]
        reg_edges = iter(reg_list[:1] + sum(reg_gaps, []) + reg_list[-1:])
        reg_ranges = list(zip(reg_edges, reg_edges))
        logging.info('LOOP')
        while True:
            start_time = time.time()
            for reg_range in reg_ranges:
                param_count = (reg_range[1] - reg_range[0]) // 2 + 1
                param_values = modbus.read_input_registers(address=reg_range[0], count=param_count * 2,
                                                           unit=unit_addr).registers
                for i in range(0, param_count * 2, 2):
                    meter_params_value[meter_param_addr[reg_range[0] + i]] = round(
                        struct.unpack('>f',
                                      struct.pack('>HH',
                                                  param_values[i],
                                                  param_values[i + 1]))[0], 3)
            try:
                mqtt_publish('homeassistant/sensor/SDM72/state', meter_params_value, False)
            except Exception:
                logging.exception('MQTT_PUBLISH')
            time.sleep(sample_interval - (time.time() - start_time))
    except Exception:
        logging.exception('MAIN')
    try:
        modbus.close()
    except Exception:
        pass
