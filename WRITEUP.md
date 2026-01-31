# architecture write-up

see [README.md](README.md) for instructions.

when i first received this takehome, i took a look at the codebase structure and read through the README to understand what i was building. the requirements were clear: build a backend for a smart home energy management system with django and graphql, supporting different device types (solar panels, batteries, evs, appliances) with telemetry simulation.

## architecture decisions

the first thing i tackled was the data model design. i went with a single table inheritance (sti) pattern - one `Device` model with a `device_type` field and jsonfield for type-specific properties. this felt like the right tradeoff because:
- it's simpler than having four separate tables
- easy to query all devices together (which the energy summary needs)
- flexible if we need to add new device types later
- postgresql's jsonfield handles the type-specific data well

the downside is no database-level constraints on properties, but i handle validation in `DeviceService.validate_properties()` which works fine. the requirements said to focus on clean code and design thinking rather than perfect schema enforcement, so i went with flexibility.

i separated the business logic into service classes (`DeviceService`, `EnergyService`, `TelemetryService`) instead of putting everything in the models. this keeps the models thin and makes the logic reusable across graphql, admin panel, and celery tasks. it also made testing way easier - i could test the services in isolation without hitting the database.

one interesting decision was storing both `current_state` (as a jsonfield on device) and historical `TelemetryReading` records. there's some duplication here, but it enables fast real-time queries for the energy summary without having to query time-series data. the `current_state` gives instant access to the latest values, while `TelemetryReading` is there for historical analytics.

for the telemetry simulation, i used celery beat to run it every 60 seconds. this keeps it non-blocking and makes it easy to scale workers horizontally if needed. the simulation logic itself was fun to work on - i used a gaussian curve for solar output centered at noon, with peak production during 10am-2pm as specified. for appliances, i went with probabilistic on/off patterns which feels realistic.

## implementation

i completed all three main objectives:

**data models** - the device model handles all four device types using the sti pattern. each device type has its required properties validated, and i added computed properties like `current_power_watts` and `charge_percentage` that make the graphql queries clean.

**graphql api** - i implemented the register device mutation, list devices query (with filtering), get single device, and the energy summary query. the energy summary was interesting because it needs to aggregate across all devices - i iterate through active devices, categorize power as production (positive) or consumption (negative), and extract storage states for batteries/evs.

**telemetry simulation** - the celery task runs every minute and simulates each device type appropriately. solar panels use time-based calculations, appliances have realistic on/off patterns, and storage devices update charge levels based on their mode. the auto-idle logic was a nice touch - batteries/evs automatically switch to idle when they hit capacity limits.

one thing i partially implemented is the time-range telemetry queries. the backend method `TelemetryService.get_telemetry_aggregated()` exists and supports hour/day/week/month intervals using django's truncation functions, but i didn't expose it via graphql yet. it's ready to go though - just needs a query field added to the schema.

## approach to the requirements

### a. energy summary across all connected devices

the current implementation queries all active devices in one go and calculates totals. it uses the `current_state` jsonfield so there's no time-series query needed - just a simple iteration. for the current scale this works fine, but for 2m+ devices i'd need to add pagination or device grouping, maybe cache the summary for 30-60 seconds, and use database aggregation functions instead of python loops.

for the solar calculations, i used a gaussian curve centered at noon with the formula `output = rated_capacity * exp(-((hour - 12)² / (2 * 4²)))` which gives peak production during 10am-2pm as required. i added ±15% random variation for weather simulation and set output to zero before 6am and after 8pm.


### b. query energy data over time range

i built `get_telemetry_aggregated()` which uses django's `TruncHour`, `TruncDay`, `TruncWeek`, `TruncMonth` functions to group readings by interval, then aggregates avg/max/min power and avg charge. the query structure is clean:

```python
TelemetryReading.objects.filter(
    device=device, timestamp__gte=start, timestamp__lte=end
).annotate(period=TruncHour('timestamp')).values('period').annotate(
    avg_power=Avg('power_watts'), max_power=Max('power_watts')
).order_by('period')
```

for 2m+ devices, i'd partition the TelemetryReading table by device_id or timestamp, maybe use timescaledb for time-series optimization, and set up read replicas for analytics queries.

### c. scaling to 2m+ devices

when scaling, the main challenges are:

**database** - i'd use postgresql hash partitioning on `device_id` (4-16 partitions) with composite `(device_id, timestamp)` indexes and brin indexes on timestamp. timescaledb would handle automatic time-based partitioning, compression (80-90% reduction), and continuous aggregates, with 2-3 read replicas for analytics queries.

**application** - redis caching for device states (60s ttl) and energy summaries (30s ttl), with kafka message queue where celery publishes telemetry events and workers consume in batches of 1000 for bulk inserts. horizontal scaling with 10-20 django servers behind a load balancer and 50-100 celery workers in separate pools.

**data retention** - tiered storage: hot data (0-30 days) in postgresql, warm (30-365 days) compressed in timescaledb, cold (1+ years) in s3. downsampling: keep raw data 7 days, aggregate to hourly for 90 days, daily for 2 years, monthly forever, reducing storage from terabytes to gigabytes.

## tools & process

the django orm made the queries clean, and postgresql's jsonfield handled the flexible device properties nicely. celery was straightforward to set up - just configure the beat schedule and the tasks run automatically.

## tradeoffs & future work

the main tradeoff i made was using the sti pattern instead of separate tables. it's less type-safe but more flexible, and the validation layer handles the constraints. for a production system, i might add database-level checks or use a hybrid approach.

if i had more time, i'd:
- expose the time-range telemetry queries via graphql
- add device grouping/aggregation for the energy summary
- implement the caching layer
- add more sophisticated telemetry simulation (weather patterns, seasonal variations)
- build out the admin interface more
- add device management mutations (update, deactivate)

overall i think the design is clean and handles the requirements well. the service layer makes it easy to optimize later without changing the api contract, and the graphql schema is flexible enough for frontend needs. the code feels maintainable and the tests cover the main scenarios.
