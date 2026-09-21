import logging
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE

from compit_inext_api.consts import CompitParameter
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    data_manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CompitThermostat(data_manager)], update_before_add=True)


class CompitThermostat(ClimateEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "solarcomp_thermostat"

    def __init__(self, data_manager):
        self._data_manager = data_manager
        self._attr_unique_id = f"compit_climate_{data_manager.device_id}"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        
        self._attr_min_temp = 20.0
        self._attr_max_temp = 85.0
        self._attr_target_temperature_step = 1.0
        
        self._attr_hvac_modes = [
            HVACMode.HEAT,  
            HVACMode.COOL,  
            HVACMode.AUTO,  
            HVACMode.OFF    
        ]
        
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

        self._target_temp = None
        self._current_temp = None
        self._hvac_mode = None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, str(self._data_manager.device_id))},
            "name": "SolarComp 971SD B1",
            "manufacturer": "Compit",
            "model": "SolarComp 971SD B1"
        }

    @property
    def current_temperature(self):
        return self._current_temp

    @property
    def target_temperature(self):
        return self._target_temp

    @property
    def hvac_mode(self):
        return self._hvac_mode

    async def async_set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE in kwargs:
            val = kwargs[ATTR_TEMPERATURE]
            success = await self._data_manager.connector.set_device_parameter(
                self._data_manager.device_id, 
                CompitParameter.DHW_TARGET_TEMPERATURE, 
                val
            )
            if success:
                self._target_temp = val
                self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        mode_val = "auto"
        if hvac_mode == HVACMode.HEAT:
            mode_val = "auto"
        elif hvac_mode == HVACMode.COOL:
            mode_val = "de_icing"
        elif hvac_mode == HVACMode.AUTO:
            mode_val = "holiday"
        elif hvac_mode == HVACMode.OFF:
            mode_val = "disabled"
            
        success = await self._data_manager.connector.select_device_option(
            self._data_manager.device_id, 
            CompitParameter.SOLAR_COMP_OPERATING_MODE, 
            mode_val
        )
        if success:
            self._hvac_mode = hvac_mode
            self.async_write_ha_state()

    async def async_update(self):
        try:
            await self._data_manager.async_update()
            connector = self._data_manager.connector
            dev_id = self._data_manager.device_id
            
            t_target = connector.get_current_value(dev_id, CompitParameter.DHW_TARGET_TEMPERATURE)
            # Zmieniono źródło aktualnej temperatury na czujnik góry zasobnika (T3)
            t_current = connector.get_current_value(dev_id, CompitParameter.TANK_TOP_T3_TEMPERATURE)
            
            if t_target is not None:
                try: self._target_temp = float(t_target)
                except ValueError: pass
                
            if t_current is not None:
                try: self._current_temp = float(t_current)
                except ValueError: pass
                
            op_mode = connector.get_current_option(dev_id, CompitParameter.SOLAR_COMP_OPERATING_MODE)
            
            if op_mode == "auto":
                self._hvac_mode = HVACMode.HEAT
            elif op_mode == "de_icing":
                self._hvac_mode = HVACMode.COOL
            elif op_mode == "holiday":
                self._hvac_mode = HVACMode.AUTO
            elif op_mode == "disabled":
                self._hvac_mode = HVACMode.OFF
                
        except Exception as e:
            _LOGGER.error("Błąd aktualizacji termostatu Compit: %s", e)