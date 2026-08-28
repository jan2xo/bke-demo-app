using System.Text.Json;
using System.Text.Json.Serialization;
using BKE.Desktop.Client;

const string SdkVersion = "1.0.0";

if (args.Any(arg => arg is "-h" or "--help" or "help"))
{
    PrintHelp();
    return 0;
}

var command = args.FirstOrDefault()?.ToLowerInvariant() ?? "authorize";
if (command is not ("authorize" or "license-center" or "full"))
{
    Console.Error.WriteLine($"Unknown command: {command}");
    PrintHelp();
    return 64;
}

ProductManifest manifest;
try
{
    manifest = await LoadManifestAsync(ResolveManifestPath());
}
catch (Exception ex) when (ex is IOException or JsonException or InvalidDataException)
{
    Console.Error.WriteLine($"manifest_error={ex.Message}");
    return 65;
}

var installationId = InstallationIdStore.GetOrCreate();
Console.WriteLine($"sdk=BKE.Desktop.Client/{SdkVersion}");
Console.WriteLine($"product_id={manifest.ProductId}");
Console.WriteLine($"version={manifest.Version}");
Console.WriteLine($"installation_id={installationId}");

using var cancellation = new CancellationTokenSource();
Console.CancelKeyPress += (_, eventArgs) =>
{
    eventArgs.Cancel = true;
    cancellation.Cancel();
};

using var client = BkeDesktopClient.Create();

if (command == "license-center")
{
    var licenseCenter = await client.OpenLicenseCenterAsync(
        manifest.ProductId,
        manifest.Version,
        installationId,
        cancellation.Token);

    PrintLicenseCenter(licenseCenter);
    var refreshed = await client.AuthorizeAsync(
        manifest.ProductId,
        manifest.Version,
        installationId,
        cancellation.Token);
    PrintAuthorization(refreshed);
    return ExitCode(refreshed.Status);
}

var authorization = await client.AuthorizeAsync(
    manifest.ProductId,
    manifest.Version,
    installationId,
    cancellation.Token);
PrintAuthorization(authorization);

if (command == "authorize" || authorization.Status != AuthorizationStatus.ActivationRequired)
    return ExitCode(authorization.Status);

Console.WriteLine("activation_flow=opening_license_center");
var activation = await client.OpenLicenseCenterAsync(
    manifest.ProductId,
    manifest.Version,
    installationId,
    cancellation.Token);
PrintLicenseCenter(activation);

var finalAuthorization = await client.AuthorizeAsync(
    manifest.ProductId,
    manifest.Version,
    installationId,
    cancellation.Token);
PrintAuthorization(finalAuthorization);
return ExitCode(finalAuthorization.Status);

static void PrintHelp()
{
    Console.WriteLine("BKE Demo SDK Client");
    Console.WriteLine();
    Console.WriteLine("Commands:");
    Console.WriteLine("  authorize       Ask the local Licensing Agent for authorization.");
    Console.WriteLine("  license-center  Open the Agent-owned License Center, then authorize again.");
    Console.WriteLine("  full            Authorize; if activation is required, open License Center and re-authorize.");
    Console.WriteLine();
    Console.WriteLine("Environment overrides:");
    Console.WriteLine("  BKE_DEMO_MANIFEST         Path to bke.manifest.json.");
    Console.WriteLine("  BKE_DEMO_INSTALLATION_ID  Stable installation ID to use instead of the local persisted ID.");
}

static string ResolveManifestPath()
{
    var overridePath = Environment.GetEnvironmentVariable("BKE_DEMO_MANIFEST");
    if (!string.IsNullOrWhiteSpace(overridePath))
        return Path.GetFullPath(overridePath);

    var besideExecutable = Path.Combine(AppContext.BaseDirectory, "bke.manifest.json");
    if (File.Exists(besideExecutable))
        return besideExecutable;

    return Path.GetFullPath("bke.manifest.json");
}

static async Task<ProductManifest> LoadManifestAsync(string path)
{
    await using var stream = File.OpenRead(path);
    var manifest = await JsonSerializer.DeserializeAsync<ProductManifest>(stream)
        ?? throw new InvalidDataException("manifest root is empty");

    if (manifest.SchemaVersion != 1)
        throw new InvalidDataException("unsupported manifest schemaVersion");
    if (string.IsNullOrWhiteSpace(manifest.ProductId))
        throw new InvalidDataException("manifest productId is missing");
    if (string.IsNullOrWhiteSpace(manifest.Version))
        throw new InvalidDataException("manifest version is missing");

    return manifest;
}

static void PrintAuthorization(AuthorizationResult result)
{
    Console.WriteLine($"authorization_status={result.Status}");
    Console.WriteLine($"authorization_reason={result.Reason}");
}

static void PrintLicenseCenter(LicenseCenterResult result)
{
    Console.WriteLine($"license_center_status={result.Status}");
    Console.WriteLine($"license_center_reason={result.Reason}");
}

static int ExitCode(AuthorizationStatus status) => status switch
{
    AuthorizationStatus.Authorized => 0,
    AuthorizationStatus.ActivationRequired => 10,
    AuthorizationStatus.Denied => 11,
    AuthorizationStatus.Unsupported => 12,
    AuthorizationStatus.AgentUnavailable => 20,
    AuthorizationStatus.Timeout => 21,
    AuthorizationStatus.ProtocolRejected => 22,
    AuthorizationStatus.InvalidRequest => 23,
    AuthorizationStatus.InvalidResponse => 24,
    _ => 25
};

internal sealed record ProductManifest(
    [property: JsonPropertyName("schemaVersion")] int SchemaVersion,
    [property: JsonPropertyName("productId")] string ProductId,
    [property: JsonPropertyName("version")] string Version);

internal static class InstallationIdStore
{
    public static string GetOrCreate()
    {
        var overrideId = Environment.GetEnvironmentVariable("BKE_DEMO_INSTALLATION_ID");
        if (!string.IsNullOrWhiteSpace(overrideId))
            return overrideId.Trim();

        var local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        if (string.IsNullOrWhiteSpace(local))
            local = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);

        var directory = Path.Combine(local, "BKE Digital Solutions", "BKE Demo App");
        var path = Path.Combine(directory, "installation-id.txt");

        try
        {
            if (File.Exists(path))
            {
                var existing = File.ReadAllText(path).Trim();
                if (Guid.TryParse(existing, out _))
                    return existing;
            }

            Directory.CreateDirectory(directory);
            var created = Guid.NewGuid().ToString("D");
            File.WriteAllText(path, created);
            return created;
        }
        catch (IOException)
        {
            return Guid.NewGuid().ToString("D");
        }
        catch (UnauthorizedAccessException)
        {
            return Guid.NewGuid().ToString("D");
        }
    }
}
