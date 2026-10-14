# falcosense

Async Python client for the [Tridonic FalcoSENSE](https://www.tridonic.com/de/int/product/32878)
people-counting / occupancy sensor.

It wraps the device's two local APIs:

- **REST (HTTPS, port 5000)** — static information and config validation.
- **MQTT (WebSocket over TLS, port 1883)** — live occupancy, line-counter,
  queue and alert metadata, pushed by the device's own broker.

No external MQTT broker is required; the client connects directly to the device.

This library is primarily developed to back the FalcoSENSE
[Home Assistant](https://www.home-assistant.io/) integration, but has no
Home Assistant dependency.

## Usage

```python
import aiohttp
from falcosense import FalcoSense

async def main() -> None:
    async with aiohttp.ClientSession() as session:
        client = FalcoSense("192.168.1.20", "<api-token>", session)
        device_name = await client.async_validate()
        client.add_listener(lambda: print(client.state))
        await client.async_connect()
        ...
        await client.async_disconnect()
```

## Authentication

The MQTT broker authenticates with the API **token as the username and no
password** (an empty-string password is rejected). The device serves a
self-signed certificate, so TLS verification is disabled by default.

## License

Apache-2.0
