using Avalonia;
using Avalonia.Controls;
using Avalonia.Layout;

namespace BKE.Demo.LauncherPlugin;

internal sealed class DemoWindow : Window
{
    private int _runCount;

    public DemoWindow()
    {
        Title = "BKE Demo App";
        Width = 520;
        Height = 320;
        MinWidth = 420;
        MinHeight = 260;

        var status = new TextBlock
        {
            Text = "Protected demo is ready.",
            TextWrapping = Avalonia.Media.TextWrapping.Wrap,
        };

        var runButton = new Button
        {
            Content = "Run protected demo",
            HorizontalAlignment = HorizontalAlignment.Left,
        };
        runButton.Click += (_, _) =>
        {
            _runCount++;
            status.Text =
                $"Protected plugin functionality executed {_runCount} time{(_runCount == 1 ? string.Empty : "s")}.";
        };

        Content = new StackPanel
        {
            Margin = new Thickness(24),
            Spacing = 14,
            Children =
            {
                new TextBlock
                {
                    Text = "BKE Demo App",
                    FontSize = 24,
                    FontWeight = Avalonia.Media.FontWeight.SemiBold,
                },
                new TextBlock
                {
                    Text =
                        "This lightweight app is compiled into BKE Launcher and opens only after Licensing Agent authorization.",
                    TextWrapping = Avalonia.Media.TextWrapping.Wrap,
                },
                new TextBlock
                {
                    Text =
                        "Product: bke-trial-product · Version: 2.0.0 · Execution: LAUNCHER_PLUGIN",
                    TextWrapping = Avalonia.Media.TextWrapping.Wrap,
                },
                runButton,
                status,
            },
        };
    }
}
