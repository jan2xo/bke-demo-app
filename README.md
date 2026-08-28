# BKE Demo App

Certification repository for the BKE product-facing Licensing Agent boundary.

## Current SDK certification path

The repository now includes a .NET 8 harness under `sdk/BKE.Demo.SdkClient` that consumes the released `BKE.Desktop.Client` v1.0.0 package.

Certified SDK source anchor:

`6fb8cb52c60d1e34414d2a4bc53fb7be52b1c294`

Vendored package:

`packages/BKE.Desktop.Client.1.0.0.nupkg`

Required SHA-256:

`9cd80194bc0ddb5f1f983143d37282f470cfb7772e41fa2d9df691f48425071e`

The SDK harness does not implement raw Agent HTTP transport. It calls `BkeDesktopClient.Create()`, `AuthorizeAsync(...)`, and `OpenLicenseCenterAsync(...)`; the SDK owns the fixed loopback Agent protocol, timeouts, parsing, and typed outcomes.

## Product identity

The current canonical test manifest is `bke.manifest.json`:

- product ID: `bke-trial-product`
- version: `2.0.0`
- display name: `BKE Digital Solutions`

The harness reads product ID/version from that manifest and uses one persisted local installation ID. Set `BKE_DEMO_INSTALLATION_ID` to override the ID for a controlled test.

## Run the SDK harness

Restore/build from the repository root:

```bash
dotnet restore sdk/BKE.Demo.SdkClient/BKE.Demo.SdkClient.csproj --configfile NuGet.Config
dotnet build sdk/BKE.Demo.SdkClient/BKE.Demo.SdkClient.csproj -c Release --no-restore
```

Authorization only:

```bash
dotnet run --project sdk/BKE.Demo.SdkClient -- authorize
```

Full activation test:

```bash
dotnet run --project sdk/BKE.Demo.SdkClient -- full
```

`full` performs authorization first. If the SDK reports `ActivationRequired`, it asks the Agent to open its License Center and, after that flow completes, authorizes again using the same product/version/installation identity.

Useful outcomes are printed directly:

```text
sdk=BKE.Desktop.Client/1.0.0
product_id=bke-trial-product
version=2.0.0
installation_id=...
authorization_status=Authorized
authorization_reason=...
```

The CI workflow also publishes self-contained `win-x64` and `osx-arm64` SDK demo artifacts so the harness can be exercised on a machine running the Licensing Agent without requiring a source checkout.

## Legacy Python GUI

The existing Tkinter certification implementation under `src/bke_demo_app` is retained for historical/behavioral coverage. It predates the reusable desktop SDK and still contains its own product-side transport. Do not use that legacy path as evidence that `BKE.Desktop.Client` works.

For SDK/Agent certification, use `sdk/BKE.Demo.SdkClient`.

## Trust boundary

The demo product is not a licensing authority. It does not receive or verify signed leases, signing keys, entitlement state, or updater trust. The Licensing Agent remains the local authority.

The SDK harness must not contain direct references to the Agent endpoint or raw `/v1/authorize` / `/v1/license-center/open` protocol paths; CI enforces that boundary.

## CI

CI verifies:

- existing Python compile/tests and manifest/version checks
- .NET 8 SDK selection
- exact vendored SDK package SHA-256
- restore resolves `BKE.Desktop.Client/1.0.0`
- Release build succeeds
- SDK harness contains SDK calls and no direct Agent HTTP transport
- self-contained Windows x64 and macOS arm64 demo artifacts publish successfully

Native end-to-end authorization still requires a real local Licensing Agent and is intentionally performed outside hosted CI.
