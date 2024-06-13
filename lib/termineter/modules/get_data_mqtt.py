from __future__ import unicode_literals
import binascii
import struct
import paho.mqtt.client as paho
import json
import logging
from c1218.errors import C1218ReadTableError
from termineter.module import TermineterModuleOptical
from mqtt_config import (
    mqtt_user,
    mqtt_password,
    mqtt_host,
    mqtt_port,
    meter_name,
    mqtt_topic_prefix,
    meter_id,
)

class Module(TermineterModuleOptical):
    def __init__(self, *args, **kwargs):
        super(Module, self).__init__(*args, **kwargs)
        self.author = ['David Nagy']
        self.description = 'Read Data part From A C12.19 Table'
        self.detailed_description = 'This module retrieves and processes data from the smart meter.'
        self.setup_mqtt()

        self.sensor_types = [
            "Fwd_kWh",
            "Rev_kWh",
            "fwd_Now",
            "rev_Now",
            "L1_A",
            "L1_V",
            "L2_A",
            "L2_V",
            "L3_A",
            "L3_V",
        ]

        self.publish_initial_configurations(self.sensor_types)

    def setup_mqtt(self):
        self.client = paho.Client()
        self.client.username_pw_set(mqtt_user, mqtt_password)
        try:
            self.client.connect(mqtt_host, int(mqtt_port))
            self.client.loop_start()
            self.frmwk.print_status("MQTT client connected.")
        except Exception as e:
            self.frmwk.print_error(f"Failed to connect to MQTT: {str(e)}")

    def disconnect(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.frmwk.print_status("MQTT client disconnected.")
        except Exception as e:
            self.frmwk.print_error(f"Failed to disconnect MQTT: {str(e)}")

    def __del__(self):
        self.disconnect()

    def publish(self, topic, payload, qos=0, retain=False):
        self.client.publish(topic, payload, qos, retain)

    def get_or_create_config(self, key):
        """Generates or retrieves MQTT Home Assistant discovery configuration."""
        config_details = {
            "Fwd_kWh": (
                "mdi:transmission-tower-import",
                "Energy Import",
                "kWh",
                "total_increasing",
                "energy",
            ),
            "Rev_kWh": (
                "mdi:transmission-tower-export",
                "Energy Export",
                "kWh",
                "total_increasing",
                "energy",
            ),
            "fwd_Now": (
                "mdi:meter-electric-outline",
                "Power Import",
                "W",
                "measurement",
                "power",
            ),
            "rev_Now": ("mdi:meter-electric", "Power Export", "W", "measurement", "power"),
            "L1_A": ("mdi:alpha-a-circle", "Phase 1 Amperage", "A", "measurement", None),
            "L1_V": (
                "mdi:alpha-v-circle",
                "Phase 1 Voltage",
                "V",
                "measurement",
                "voltage",
            ),
            "L2_A": ("mdi:alpha-a-circle", "Phase 2 Amperage", "A", "measurement", None),
            "L2_V": (
                "mdi:alpha-v-circle",
                "Phase 2 Voltage",
                "V",
                "measurement",
                "voltage",
            ),
            "L3_A": ("mdi:alpha-a-circle", "Phase 3 Amperage", "A", "measurement", None),
            "L3_V": (
                "mdi:alpha-v-circle",
                "Phase 3 Voltage",
                "V",
                "measurement",
                "voltage",
            ),
        }
        if key in config_details:
            icon, name, unit, state_class, device_class = config_details[key]
            data = {
                "device": {
                    "identifiers": [meter_id],
                    "manufacturer": "Networked Electricity Services",
                    "model": "NES-Meter",
                    "name": "Electricity Meter"
                },
                "name": name,
                "unit_of_measurement": unit,
                "state_topic": f"{mqtt_topic_prefix}/{meter_name}/{key}",
                "unique_id": f"{meter_id}_{key}",
                "state_class": state_class,
                "icon": icon,
                "platform": "mqtt",
            }
            if device_class:
                data["device_class"] = device_class
            self.frmwk.print_status(f"Config for {key} created/updated. {data}")
            return json.dumps(data)
        logging.warning(f"No config found for {key}")
        return None

    def publish_initial_configurations(self, sensor_types):
        """Publishes initial configurations for all sensors."""
        for sensor_type in sensor_types:
            config_payload = self.get_or_create_config(sensor_type)
            if config_payload:
                config_topic = f"homeassistant/sensor/{meter_name}_{sensor_type}/config"
                self.publish(config_topic, config_payload, retain=True)
                self.frmwk.print_status(f"Initial configuration published for {config_topic}")

    def publish_data(self, buffer_dict):
        """Publishes sensor data to MQTT."""
        for key, value in buffer_dict.items():
            data_topic = f"{mqtt_topic_prefix}/{meter_name}/{key}"
            self.publish(data_topic, value, qos=0, retain=False)
            self.frmwk.print_status(f"Data published to {data_topic}: {value}")

    def parse_input_buffer(self, byte, table_id):
        """Parses the input buffer and returns a dictionary of values based on table_id."""
        try:
            if len(byte) < 36:
                byte += b"\x00" * (36 - len(byte))
            int32_values = struct.unpack("<" + "i" * (len(byte) // 4), byte)

            if table_id == 23:
                data = {
                    "Fwd_kWh": int32_values[0] / 1000,
                    "Rev_kWh": int32_values[1] / 1000,
                }
            elif table_id == 28:
                data = {
                    "fwd_Now": int32_values[0],
                    "rev_Now": int32_values[1],
                    "L1_A": int32_values[4] / 1000,
                    "L2_A": int32_values[5] / 1000,
                    "L3_A": int32_values[6] / 1000,
                    "L1_V": int32_values[7] / 1000,
                    "L2_V": int32_values[8] / 1000,
                    "L3_V": int32_values[9] / 1000,
                }

            self.frmwk.print_status(f"Parsed data for table_id {table_id}: {data}")
            return data
        except ValueError as e:
            self.frmwk.print_error(f"Error converting data to bytes for table_id {table_id}: {e}")
            return {}

    def read_and_process_data(self, conn, table_id, octet):
        """Utility method to read table data, log, parse, and process."""
        try:
            data = conn.get_table_part(table_id, octet, 0)
            self.frmwk.print_hexdump(data)
            self.frmwk.print_status('Read ' + str(len(data)) + ' bytes')
            parsed_data = self.parse_input_buffer(data, table_id)
            if parsed_data:
                self.publish_data(parsed_data)

        except C1218ReadTableError as error:
            self.frmwk.print_error('Caught C1218ReadTableError: ' + str(error))

    def run(self):
        conn = self.frmwk.serial_connection
        self.read_and_process_data(conn, 23, 8)
        self.read_and_process_data(conn, 28, 40)
