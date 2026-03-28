# GaN Device Characterization Platform

A modern Windows 11 Fluent Design desktop application for **GaN HEMT device characterization**, built with **PySide6 + QFluentWidgets + PyQtGraph**.

> **UI Skeleton / Demo** — all measurements use simulated (Mock) data so the interface can be explored without real instruments.

---

## Screenshots

*(Screenshots will be added after first run)*

---

## Features

| Test Mode | Description |
|-----------|-------------|
| 🏠 Home | Instrument connection management (Keithley 2636B + 2657A) |
| ⚡ Gate Transfer | Id-Vgs sweep with log, gm, Ig views |
| 📊 Output Characteristics | Id-Vds family of curves |
| 💥 Breakdown Test | High-voltage breakdown sweep with safety warning |
| 🔌 Diode IV | Gate-Source / Gate-Drain / Drain-Source diode IV |
| ⚙️ Settings | Theme, data path, default NPLC |

---

## Tech Stack

| Component | Package | Version |
|-----------|---------|---------|
| GUI Framework | `PySide6` | ≥ 6.5 |
| UI Component Library | `PySide6-Fluent-Widgets` | ≥ 1.5 |
| Real-time Plotting | `pyqtgraph` | ≥ 0.13 |
| Data / Simulation | `numpy` | ≥ 1.24 |

---

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

---

## Project Structure

```
gan-char-gui/
├── main.py                          # Application entry point
├── requirements.txt
├── README.md
└── gui/
    ├── main_window.py               # FluentWindow with sidebar navigation
    ├── home_interface.py            # Instrument connection & channel mapping
    ├── settings_interface.py        # Theme, data path, NPLC settings
    ├── components/
    │   ├── plot_card.py             # Reusable PyQtGraph chart (Fluent styled)
    │   └── control_bar.py          # Start/Stop/Emergency Stop + progress
    └── test_interfaces/
        ├── base_test_interface.py   # Shared splitter layout (params + chart)
        ├── gate_transfer_interface.py
        ├── output_interface.py
        ├── breakdown_interface.py
        └── diode_iv_interface.py
```
