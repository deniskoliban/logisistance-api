# Project specification — European Freight & Logistics Assistant

This document is the working source of truth for scope. It is a direct record of the product
brief, lightly structured. Anything marked **TBD** is open and not yet decided.

## 1. Project mission

Build a smart logistics management platform designed specifically for independent road freight
carriers, self-employed transport entrepreneurs and small transport businesses operating within
the European Union.

The platform should help independent carriers discover profitable transportation opportunities,
manage their vehicles, find compatible cargo, optimise routes and make better operational
decisions.

The core idea is a centralised logistics assistant that integrates multiple European freight
exchanges and transportation marketplaces into a single, intelligent interface.

Instead of manually searching through multiple freight platforms, comparing transportation
offers, calculating routes and looking for return loads, carriers should be able to manage these
activities from one place.

The product prioritises simplicity, efficiency, automation and practical value for small
independent transport operators.

## 2. Target audience

- Self-employed truck and van drivers.
- Independent owner-operators.
- Small transportation and logistics companies.
- Entrepreneurs operating commercial vehicles across the European Union.
- Carriers specialising in international and domestic road transportation.

The platform should be particularly useful for small operators who do not have access to
enterprise-level fleet management or logistics optimisation software.

## 3. Core product features

### 3.1 Vehicle registration and management

Users register and manage one or multiple commercial vehicles. Each vehicle profile contains the
transportation parameters that matter:

- Vehicle type and category.
- Vehicle registration information.
- Maximum payload capacity (kg).
- Cargo compartment length, width and height.
- Cargo volume capacity (m³).
- Vehicle dimensions.
- Body type (van, box truck, curtain-sided truck, refrigerated vehicle, etc.).
- Loading capabilities and equipment.
- Additional transportation restrictions and capabilities.

The system uses these parameters when searching for and evaluating freight opportunities.

### 3.2 Freight exchange integrations

The platform integrates with popular European freight exchanges and transportation marketplaces
so that offers from multiple external platforms appear in one unified interface.

Potential integrations:

- TIMOCOM.
- Trans.eu.
- Teleroute.
- Wtransnet.
- Other relevant European freight marketplaces.

Integration methods prioritise official APIs and authorised integration mechanisms.

The architecture must support adding new freight exchange providers without significant changes
to the core application. Each integration is implemented through an independent provider adapter.

### 3.3 Intelligent freight search and filtering

Users search for available transportation orders across integrated freight exchanges. Results are
filtered and ranked by:

- Current vehicle location.
- Vehicle type and configuration.
- Maximum payload capacity.
- Cargo dimensions and volume.
- Pickup location.
- Delivery destination.
- Pickup and delivery dates.
- Available driving range.
- Preferred countries and regions.
- Transportation requirements.

Only orders compatible with the selected vehicle and the user's operational preferences are
identified. Users can also search for freight by a specific location, destination or preferred
route.

### 3.4 Route planning and delivery time estimation

Users select a freight order and calculate a route between pickup and delivery locations. The
system provides:

- Recommended transportation route.
- Total distance.
- Estimated driving time.
- Estimated arrival time.
- Estimated delivery duration.
- Route visualisation on an interactive map.

Route calculations account for relevant commercial vehicle restrictions whenever supported by the
routing provider, and consider applicable European driving and rest-time regulations (EU
Regulation 561/2006) when calculating realistic delivery estimates.

### 3.5 Return cargo and backhaul search

A flagship feature. The platform helps carriers find additional transportation orders along their
existing route or near their delivery destination.

Example: a carrier has an order from Poland to Germany. Instead of driving back empty, the system
searches the integrated freight exchanges for orders that could be transported:

- From the delivery destination.
- Along the return route.
- Near the planned route.
- Within a reasonable distance of the vehicle's current location.

The system identifies potentially profitable return loads and presents them to the user.

### 3.6+ Remaining sections — TBD

The brief was cut off after section 3.5. Remaining features, non-functional requirements,
monetisation and delivery plan are open items to be defined next.

## 4. Decisions

| Topic | Status | Notes |
| --- | --- | --- |
| Tech stack | **decided** | Angular 22 frontend ([logisistance-web](https://github.com/deniskoliban/logisistance-web)) + Python 3.12 / FastAPI backend (this repository) |
| Source layout | **decided** | Two repositories, split from the initial v0.1 monorepo: independent deploy lifecycles, API contract exchanged through `/openapi.json` |
| UI framework | **decided** | Angular Material 3 with light and dark themes driven by `mat.theme()` and CSS `color-scheme` |
| Localisation | **decided** | Transloco 9 (`@jsverse/transloco`), English + Russian, switchable at runtime without reload. UI strings and validation messages live in the frontend dictionaries; API `detail` messages stay English for now — translating them needs stable error codes |
| Forms | **decided** | Angular Signal Forms (`@angular/forms/signals`): model in a `signal`, validation in the schema, `[formRoot]`/`[formField]` bindings |
| Responsiveness | **required** | Every screen must be usable at 360 px (phone), 768 px (tablet) and 1440 px (desktop) with no horizontal scrolling |
| Database | **decided for v0.1** | SQLite via SQLAlchemy 2; `DATABASE_URL` swaps to PostgreSQL without code changes. Add Alembic before the first deploy |
| Auth | **decided for v0.1** | Email + password, Argon2 hashing, JWT bearer token (12 h) stored in `localStorage` |
| Driver age | **decided** | Stored as `date_of_birth` (ISO date); `age` is derived on every response, so it cannot go stale. Rules 18–100 and no future dates live in `app/core/dates.py` |
| First slice (v0.1) | **shipped** | Registration + driver profile (name, age, country, city) + basic vehicle profiles |
| Freight exchange access (API keys, partner agreements) | TBD | TIMOCOM / Trans.eu / Teleroute / Wtransnet each need authorised access, so v0.2 starts with a mock provider adapter |
| Routing provider | TBD | Needs commercial-vehicle restrictions (e.g. HERE, TomTom, PTV, GraphHopper) |
| Geocoding provider | TBD | |
| Profitability model for ranking backhauls | TBD | Needs rate per km, empty-run cost, fuel, tolls |

## 5. Deliberate scope cuts in v0.1

- No freight data, routing or map yet — those need partner credentials / API keys that do not
  exist for this project. Fake data was avoided on purpose.
- No refresh tokens, password reset, email verification or roles.
- No migrations: tables are created from the SQLAlchemy models at startup.
- Vehicle documents (insurance, MOT, ADR certificates) and trailer pairing are not modelled yet.

