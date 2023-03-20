# ekey home converter LAN rs485 HomeAssistant integration

This integration can only read the data from the so called home-protocol.
When using the home-protocol the ekey home rs485 sends packets as a underscore
delimited string.

## home-protocol packet details:

```
1       _ 0046    _ 4         _ 80156809150025 _ 1      _ 2
^         ^         ^           ^                ^        ^
PAKETTYP  USER ID   FINGER ID   SERIENNR FS      AKTION   RELAIS
``` 

For details see [ekey home rs 485 manual](https://www.ekey.net/wp-content/dokumente/Bedienungsanleitung_ekey_home_CV_LAN_RS-485_de_web_ID51_3009.pdf)

## Install

 * Download the [zip file](https://github.com/ochorocho/ekey_home_rs485/archive/refs/heads/main.zip) and extract it
 * Rename the folder to `ekey_home_rs485` 
 * Move the folder to HomeAssistant `config/custom_components/`

## Configuration

This custom integration will add the platform `ekey_home_rs485`.

```yaml
sensor:
  - platform: ekey_home_rs485
    ip_address: <ekey rs485 ip address>
    port: 56000 # Default port
    user_mapping:
      - ekey_user_id: 46 # The ekey user id without the leading zero(s)
        ha_username: david # HomeAssistant username/login for mapping
      - ekey_user_id: 47
        ha_username: maria
```

## Todo

 - [ ] Fire an event when data changes
 - [ ] Add config flow
 - [ ] Attach the sensor state to the user entity?!
 - [ ] Autodiscovery would be nice, swipe on device let HA know that there is some sort of fingerprint device available?!