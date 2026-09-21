import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfEnergy,
    UnitOfPower,
)
from compit_inext_api.consts import CompitParameter
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    data_manager = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        # Przekazujemy klucz tłumaczenia (z pl.json) jako drugi argument
        CompitCloudSensor(data_manager, "collector_temperature", CompitParameter.COLLECTOR_TEMPERATURE, SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, SensorStateClass.MEASUREMENT),
        CompitCloudSensor(data_manager, "tank_bottom_t2", CompitParameter.TANK_BOTTOM_T2_TEMPERATURE, SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, SensorStateClass.MEASUREMENT),
        CompitCloudSensor(data_manager, "tank_top_t3", CompitParameter.TANK_TOP_T3_TEMPERATURE, SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, SensorStateClass.MEASUREMENT),
        CompitCloudSensor(data_manager, "tank_t4", CompitParameter.TANK_T4_TEMPERATURE, SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, SensorStateClass.MEASUREMENT),
        CompitCloudSensor(data_manager, "collector_power", CompitParameter.COLLECTOR_POWER, SensorDeviceClass.POWER, UnitOfPower.KILO_WATT, SensorStateClass.MEASUREMENT),
        CompitCloudSensor(data_manager, "energy_total", CompitParameter.ENERGY_TOTAL, SensorDeviceClass.ENERGY, UnitOfEnergy.KILO_WATT_HOUR, SensorStateClass.TOTAL_INCREASING),
        CompitCloudSensor(data_manager, "energy_today", CompitParameter.ENERGY_TODAY, SensorDeviceClass.ENERGY, UnitOfEnergy.KILO_WATT_HOUR, SensorStateClass.TOTAL_INCREASING),
        CompitCloudSensor(data_manager, "energy_consumption_mwh", CompitParameter.ENERGY_CONSUMPTION, SensorDeviceClass.ENERGY, UnitOfEnergy.MEGA_WATT_HOUR, SensorStateClass.TOTAL_INCREASING),
        CompitCloudSensor(data_manager, "energy_consumption_kwh", CompitParameter.ENERGY_YESTERDAY, SensorDeviceClass.ENERGY, UnitOfEnergy.KILO_WATT_HOUR, SensorStateClass.TOTAL_INCREASING),
    ]
    
    async_add_entities(sensors, update_before_add=True)


class CompitCloudSensor(SensorEntity):
    
    # Informuje HA, że encja bierze nazwę z tłumaczeń i urządzenia docelowego
    _attr_has_entity_name = True

    def __init__(self, data_manager, translation_key, parameter, device_class, unit, state_class):
        self._data_manager = data_manager
        self._parameter = parameter
        self._state = None
        
        self._attr_translation_key = translation_key
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, str(self._data_manager.device_id))},
            "name": "SolarComp 971SD B1",
            "manufacturer": "Compit",
            "model": "SolarComp 971SD B1"
        }

    @property
    def native_value(self):
        return self._state

    @property
    def unique_id(self):
        return f"compit_cloud_{self._data_manager.device_id}_{self._parameter.name}"

    async def async_update(self):
        try:
            await self._data_manager.async_update()
            val = self._data_manager.connector.get_current_value(self._data_manager.device_id, self._parameter)
            
            if val is not None:
                try:
                    self._state = float(val)
                except ValueError:
                    self._state = val
            else:
                self._state = None
                
        except Exception as e:
            _LOGGER.error("Błąd podczas odczytu danych sensora %s: %s", self._attr_translation_key, e)