using Avalonia.Threading;
using BKE.Launcher.PluginHost;

namespace BKE.Demo.LauncherPlugin;

public sealed class BkeDemoLauncherPlugin : IBkeLauncherPlugin
{
    public const string ProductId = "bke-trial-product";
    public const string Version = "2.0.0";

    private ILauncherContext? _context;
    private DemoWindow? _window;

    public LauncherPluginIdentity Identity { get; } =
        new(
            ProductId,
            Version,
            LauncherPluginContract.Version);

    public Task InitializeAsync(
        ILauncherContext context,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        _context = context ?? throw new ArgumentNullException(nameof(context));
        return Task.CompletedTask;
    }

    public async Task OpenAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();

        if (_context is null)
        {
            throw new InvalidOperationException(
                "BKE Demo plugin was opened before Launcher initialization.");
        }

        await Dispatcher.UIThread.InvokeAsync(() =>
        {
            cancellationToken.ThrowIfCancellationRequested();

            if (_window is null)
            {
                _window = new DemoWindow();
                _window.Closed += (_, _) => _window = null;
                _window.Show();
                return;
            }

            if (!_window.IsVisible)
            {
                _window.Show();
            }

            _window.Activate();
        });
    }

    public async Task ShutdownAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();

        await Dispatcher.UIThread.InvokeAsync(() =>
        {
            _window?.Close();
            _window = null;
            _context = null;
        });
    }
}
