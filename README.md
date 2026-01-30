# Smart Home Energy Management System - Technical Interview

Build the backend for a smart home energy management system using Django and GraphQL.

**Time Limit: 4 hours**

**Please set aside 30 minutes for the write up.** Don't fret if you don't finish all the objectives within the 4 hour window
We are more interested in your approach, clean code, clear domain modeling, design thinking, rather than your code fully working end to end

---

## Product Requirements

### Devices

The system must support these device types:

| Device Type          | Capabilities                                             | Example Properties                                             |
| -------------------- | -------------------------------------------------------- | -------------------------------------------------------------- |
| **Solar Panel**      | Produces energy                                          | Rated capacity (e.g., 5000W max output)                        |
| **Battery**          | Stores energy, can charge or discharge                   | Capacity (e.g., 13500 Wh), max charge rate, max discharge rate |
| **Electric Vehicle** | Can charge (consume) OR discharge back to home (produce) | Battery capacity, current charge level, charge/discharge rates |
| **Appliance**        | Consumes energy                                          | Average power draw (e.g., AC unit: 3000W, dishwasher: 1800W)   |

**Key behaviors:**

- EVs can operate in three modes: charging, discharging (vehicle-to-home), or idle
- Batteries have separate charge and discharge rate limits (they're not always symmetric)
- Solar output varies by time of day (assume peak production 10am-2pm)

---

## Tasks

### Objectives

**1. Data Models**

Design and implement Django models for devices and telemetry data.

**2. GraphQL API**

- **Register a device** - Add a new device to the system with its properties
- **List devices** - Return all registered devices with their current state
- **Energy summary** - Return a snapshot showing:
  - Total power being produced (watts)
  - Total power being consumed (watts)
  - Net power flow (positive = exporting to grid, negative = importing)
  - Battery/EV storage state (capacity and current charge %)

**3. Telemetry Simulation**

Implement a Celery task that generates plausible energy values for each device type.

- Solar output should vary by time of day
- Appliances should have realistic on/off patterns
- Storage devices should update charge levels based on their mode

---

## Deliverables

1. **BRIEF write-up** (in a separate file):
   - Architecture decisions or tradeoffs that you made if any
   - If you did not finish all of the objectives, clearly explain with pseudo code or comments how you'd finish it
   - How you would approach the following.
     a. Energy summary across all connected devices
     b. Query energy data over a time range and various intervals such as 1 hour, 1 day, 1 week, 1 month
     c. How would you scale all of the above to 2M+ devices?
2. Reply to the same email thread with your zipped up repo

---

## Setup

```bash
make build     # Build containers (first time)
make up        # Start containers
make migrate   # Run database migrations
```

## Quick Reference

```bash
make up              # Start containers
make down            # Stop containers
make logs            # View logs
make shell           # Bash into Django container
make django-shell    # Django Python shell
make migrate         # Run migrations
make makemigrations  # Create new migrations
make seed            # Seed sample devices
make reset           # Wipe database and restart
```

## GraphQL Playground

http://localhost:8000/graphql
