# Compit Solar - Home Assistant Custom Component

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A custom integration for Home Assistant to monitor and control Compit solar controllers via the iNext cloud API.

> **⚠️ Important Notice:**  
> Currently, this integration has been developed and tested **exclusively with the Compit SolarComp 971SD B1** model. While it utilizes the general `compit_inext_api` library, compatibility with other Compit devices (such as heat pumps or pellet boilers) is not guaranteed and may require further adjustments.

## Features
- **UI Configuration (Config Flow):** Easy setup directly from the Home Assistant integrations page (no YAML required).
- **Climate Entity:** An elegant thermostat interface to control the Domestic Hot Water (DHW) target temperature and switch operating modes (Auto, De-icing, Holiday, Off).
- **Energy Panel Ready:** Sensors use the `TOTAL_INCREASING` state class, making them fully compatible with the built-in Home Assistant Energy Dashboard.
- **Optimized Polling:** Implements a shared data coordinator to group requests and prevent API rate limits.
- **Live Sensors:** Real-time data extraction including collector temperature, tank temperatures (T2, T3, T4), collector power, and energy yields.

## Installation via HACS
1. Go to **HACS** -> **Integrations** -> Click the three dots in the top right corner -> **Custom repositories**.
2. Paste the URL of this repository and select **Integration** as the category.
3. Search for "Compit Solar" in HACS and click **Download**.
4. Restart Home Assistant.

## Configuration
Go to **Settings -> Devices & Services -> Add Integration -> Compit Solar**

You will be prompted to enter your iNext (Compit) cloud account email and password.
