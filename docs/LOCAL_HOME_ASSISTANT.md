# Keep School Day Grid running locally with Home Assistant

This guide keeps School Day Grid on your own network and makes its current
school-day information reliably available in Home Assistant. School Day Grid
remains the source of truth; Home Assistant reads it over the local network.

## What "constant connection" means here

Home Assistant polls the School Day Grid REST API every five minutes and again
just after midnight. This is intentional: either service can restart, lose its
network briefly, or be updated without permanently breaking the other. Home
Assistant automatically resumes reading the data when the app becomes available.

The direct Home Assistant adapter in School Day Grid is for optional calendar
publishing and legacy migration. It is not needed for this local REST setup.

## 1. Run School Day Grid with Docker

Install Docker Desktop, then open PowerShell in the School Day Grid folder:

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

Docker Compose is configured with `restart: unless-stopped`, so the app comes
back after a container or Docker restart. The calendar database is stored in
the `data` folder beside the compose file, so rebuilding the container does not
erase the calendar.

Check that it is healthy:

```powershell
docker compose ps
docker compose logs -f
```

Open `http://localhost:8088` to finish the calendar setup. Then, from another
device on the same network, open:

```text
http://YOUR-SCHOOL-DAY-GRID-IP:8088/api/v1/health
```

It should return JSON with `"status": "ok"`.

### Make the host dependable

- Reserve a fixed LAN IP address for the host computer in the router, or give
  it a local DNS name. Do not point Home Assistant at an address that changes.
- Configure Docker Desktop to start when you sign in, and prevent the host from
  sleeping. A desktop that is shut down or asleep cannot serve Home Assistant.
- For an always-on household installation, run the same Compose project on a
  NAS, mini PC, server, or other always-on device instead of a daily-use laptop.
- Back up the `data` folder or use School Day Grid's backup feature before
  changing computers.

## 2. Add the Home Assistant helper package

This repository includes a ready-to-use helper package:

```text
home-assistant/school_day_grid.yaml
```

1. Copy that file to `/config/packages/school_day_grid.yaml` in Home Assistant.
2. Replace all three instances of `192.168.1.42` with the fixed IP address or
   local DNS name of the School Day Grid host.
3. If packages are not already enabled, add this to Home Assistant's
   `configuration.yaml`:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

4. Check the Home Assistant configuration, then restart Home Assistant.

The package creates these entities:

- `sensor.school_day_grid_today`
- `sensor.school_day_grid_tomorrow`
- `sensor.school_day_grid_next_school_day`

Their state is a readable label such as `Day 3` or `No School`. Their attributes
include the date, cycle-day number, type, detail, and source. The included
midnight automation asks Home Assistant to refresh all three immediately after
the day changes; normal polling is every five minutes.

This is the Home Assistant equivalent of a helper for this integration. A native
Home Assistant Helper (such as an input boolean or number) cannot itself make
HTTP requests, so REST sensors are the appropriate durable building block.

## 3. Network and security

For this LAN-only option, keep `SDG_REQUIRE_LOGIN=false`: the REST sensors do
not use the app's browser session login. Do not publish port 8088 to the public
internet. If practical, limit the host firewall rule for port 8088 to the Home
Assistant server's LAN address.

If you need access outside your home, place the app behind an authenticated
HTTPS reverse proxy and review its access controls rather than exposing port
8088 directly.

## MQTT option

School Day Grid can also publish Home Assistant MQTT Discovery messages. MQTT
is useful if you already run a broker, but the current app publishes its MQTT
state after schedule changes or when you manually publish it. It does not yet
republish automatically at midnight, so REST is the recommended option for a
continuously current daily value.

## Sharing this setup

Other households follow the same recipe: run the Compose project on an
always-on device, complete their own calendar setup, reserve that device's LAN
address, and copy the included helper package into their Home Assistant
configuration. Their data remains local in their own `data` folder.

Home Assistant documents both [REST sensors](https://www.home-assistant.io/integrations/sensor.rest/)
and [configuration packages](https://www.home-assistant.io/docs/configuration/packages/).
