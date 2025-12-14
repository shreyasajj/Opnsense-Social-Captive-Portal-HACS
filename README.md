# Captive Portal (Custom Integration for Home Assistant)

A **Home Assistant custom integration** that connects to your **Captive Portal server** and exposes real-time visibility into guest access, approvals, and tracked devices.

Designed for **local polling**, simple setup, and automation-friendly sensors.

---

## ✨ Features

- 📡 Connects to a self-hosted Captive Portal server
- 📊 Exposes guest access state as Home Assistant sensors
- 🧑‍💻 Tracks approved, denied, and pending users
- 📱 Tracks connected devices via `device_tracker`
- 🧩 Configurable via Home Assistant UI (Config Flow)
- 🚀 Fully compatible with **HACS**

---

## 📦 Entities Created

### Sensors

| Sensor | Description |
|------|------------|
| `sensor.captive_portal_pending_requests` | Number of users awaiting approval |
| `sensor.captive_portal_approved_users` | Number of approved users |
| `sensor.captive_portal_denied_users` | Number of denied users |
| `sensor.captive_portal_tracked_devices` | Number of tracked devices |

### Device Trackers

- Creates `device_tracker` entities for devices reported by the Captive Portal
- Useful for presence detection, automations, and dashboards

---

## 🛠 Installation (HACS)

### Option 1: Install via HACS (Recommended)

1. Open **HACS**
2. Go to **Integrations**
3. Click **⋮ → Custom repositories**
4. Add this repository:
   ```
   https://github.com/your-repo/captive-portal
   ```
5. Category: **Integration**
6. Search for **Captive Portal**
7. Install
8. Restart Home Assistant

---

### Option 2: Manual Installation

1. Copy the `captive_portal` folder into:
   ```
   custom_components/captive_portal/
   ```
2. Restart Home Assistant

---

## ⚙️ Configuration

This integration is **configured entirely through the UI**.

### Steps

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **Captive Portal**
4. Enter:
   - **Host**: IP address or hostname of your Captive Portal server
   - **Port**: Server port (default shown in UI)
5. Submit

If the connection is successful, entities will be created automatically.

---

## 🚨 Error Handling

- **Cannot connect**  
  Verify host, port, and that the Captive Portal server is reachable.

- **Already configured**  
  Only one instance per Captive Portal server is allowed.

---

## 🧠 Automation Example

```yaml
alias: Captive Portal - Pending Guest
trigger:
  - platform: numeric_state
    entity_id: sensor.captive_portal_pending_requests
    above: 0
action:
  - service: notify.mobile_app_phone
    data:
      message: "A guest is waiting for WiFi approval."
```

---

## 📡 Architecture

- **I/O Class:** Local polling
- **Transport:** HTTP (aiohttp)
- **No cloud dependency**

---

## 🐞 Issues & Support

https://github.com/your-repo/captive-portal/issues

---

## 📄 License

MIT License
