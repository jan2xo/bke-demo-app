# BKE Demo App

Permanent GUI certification application for the BKE product-facing Licensing Agent boundary.

## Purpose

This repository exists to prove that a BKE desktop product can remain deliberately thin: the product describes itself with `bke.manifest.json`, asks the local BKE Licensing Agent for authorization, and never duplicates licensing or updater verification logic.

Canonical integration references used for this implementation:

- `jan2xo/bke-licensing-agent` main: `d1e2307e6329977f2c3c171fd92e333d6973328d`
- `jan2xo/bke-updater-core` main: `c78f89244073721c928626ac33da34a4258f5a12`

The Demo App has no direct updater-core dependency.

## Canonical product manifest

`bke.manifest.json` identifies the product as `bke-demo-app`. Application version is owned by `src/bke_demo_app/version.py`; packaging reads that value dynamically and startup manifest validation rejects any manifest version mismatch.

## Licensing Agent boundary

Authorization is requested only from:

`POST http://127.0.0.1:8765/v1/authorize`

Request shape:

```json
{
  "product_id": "bke-demo-app",
  "version": "1.0.0",
  "installation_id": "..."
}
```

Minimum response shape:

```json
{
  "authorized": true,
  "reason": "ok"
}
```

The Agent may additionally return `update_state` and an Agent-owned loopback `license_center_url`. Unknown update state is treated as unverifiable. A non-loopback License Center URL is rejected.

The Demo App never accepts a license key, verifies a lease, verifies signatures, resolves updater trust, or imports updater-core. Activation is routed to the Licensing Agent-owned License Center at `http://127.0.0.1:8765/license-center` when the Agent reports `activation_required`.

## GUI states

The GUI exposes authorization refresh, Agent-owned activation routing, update state, and a protected demo action. Protected functionality is enabled only in the `AUTHORIZED` state. Missing/invalid manifest, unavailable Agent, deny, activation required, unsupported, and unverifiable states all fail closed.

## Verification

The repository CI runs without third-party runtime or test dependencies:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
```

Coverage includes valid/invalid/missing manifest, version mismatch, Agent ALLOW/DENY, activation required, Agent unavailable, malformed response, unsupported/unverifiable update states, protected functionality never running after DENY, no direct updater-core dependency/import, and no duplicated lease/signature verification logic.

Native macOS and Windows GUI/E2E certification is intentionally not claimed by this repository CI and remains a separate certification step.

## Run

With a compatible local Licensing Agent listening on the loopback endpoint:

```bash
PYTHONPATH=src python -m bke_demo_app
```
