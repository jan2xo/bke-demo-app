using BKE.Demo.LauncherPlugin;
using BKE.Launcher.PluginHost;

IBkeLauncherPlugin plugin = new BkeDemoLauncherPlugin();

Require(
    plugin.Identity.ProductId == BkeDemoLauncherPlugin.ProductId &&
    plugin.Identity.ProductId == "bke-trial-product",
    "BKE Demo Launcher plugin product identity drifted.");
Require(
    plugin.Identity.PluginVersion == BkeDemoLauncherPlugin.Version &&
    plugin.Identity.PluginVersion == "2.0.0",
    "BKE Demo Launcher plugin version drifted.");
Require(
    plugin.Identity.MinimumHostContractVersion ==
        LauncherPluginContract.Version,
    "BKE Demo Launcher plugin host-contract floor drifted.");

var pluginApi = typeof(IBkeLauncherPlugin)
    .GetMethods()
    .Select(method => method.Name)
    .ToHashSet(StringComparer.Ordinal);
Require(
    pluginApi.SetEquals([
        "get_Identity",
        "InitializeAsync",
        "OpenAsync",
        "ShutdownAsync",
    ]),
    "BKE Launcher plugin API surface drifted.");

var contextProperties = typeof(ILauncherContext)
    .GetProperties()
    .Select(property => property.Name)
    .ToArray();
Require(
    contextProperties.SequenceEqual(["Authorization"]),
    "BKE Demo plugin host context widened unexpectedly.");

Console.WriteLine("BKE Demo Launcher plugin certification: PASS");
Console.WriteLine($"product_id={plugin.Identity.ProductId}");
Console.WriteLine($"version={plugin.Identity.PluginVersion}");
Console.WriteLine($"host_contract={plugin.Identity.MinimumHostContractVersion}");
return;

static void Require(bool condition, string message)
{
    if (!condition)
    {
        throw new InvalidOperationException(message);
    }
}
