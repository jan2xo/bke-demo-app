from __future__ import annotations

import uuid
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from .agent import UpdateState
from .controller import AppState, DemoController


def default_manifest_path() -> Path:
    return Path(__file__).resolve().parents[2] / "bke.manifest.json"


class DemoAppWindow:
    def __init__(self, root: tk.Tk, controller: DemoController) -> None:
        self.root = root
        self.controller = controller
        root.title("BKE Demo App")
        root.minsize(560, 360)

        container = ttk.Frame(root, padding=20)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="BKE Demo App", font=("TkDefaultFont", 18, "bold")).pack(anchor="w")
        ttk.Label(
            container,
            text="Permanent Licensing Agent boundary certification application",
        ).pack(anchor="w", pady=(2, 18))

        self.state_var = tk.StringVar(value="Starting")
        self.detail_var = tk.StringVar(value="")
        self.update_var = tk.StringVar(value="Update: unknown")
        self.output_var = tk.StringVar(value="Protected functionality has not run.")

        ttk.Label(container, textvariable=self.state_var, font=("TkDefaultFont", 12, "bold")).pack(anchor="w")
        ttk.Label(container, textvariable=self.detail_var, wraplength=510).pack(anchor="w", pady=(4, 4))
        ttk.Label(container, textvariable=self.update_var).pack(anchor="w", pady=(0, 16))

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(0, 18))
        ttk.Button(actions, text="Refresh Authorization", command=self.refresh).pack(side="left")
        self.activate_button = ttk.Button(actions, text="Open License Center", command=self.open_license_center)
        self.activate_button.pack(side="left", padx=(8, 0))
        self.protected_button = ttk.Button(actions, text="Run Protected Demo", command=self.run_protected)
        self.protected_button.pack(side="left", padx=(8, 0))

        ttk.Separator(container).pack(fill="x", pady=(0, 14))
        ttk.Label(container, textvariable=self.output_var, wraplength=510).pack(anchor="w")

        self.refresh()

    def refresh(self) -> None:
        status = self.controller.refresh()
        labels = {
            AppState.AUTHORIZED: "AUTHORIZED",
            AppState.ACTIVATION_REQUIRED: "ACTIVATION REQUIRED",
            AppState.DENIED: "DENIED",
            AppState.AGENT_UNAVAILABLE: "LICENSING AGENT UNAVAILABLE",
            AppState.UNSUPPORTED: "UNSUPPORTED",
            AppState.UNVERIFIABLE: "UNVERIFIABLE",
            AppState.MANIFEST_ERROR: "MANIFEST ERROR",
            AppState.STARTING: "STARTING",
        }
        self.state_var.set(labels[status.state])
        self.detail_var.set(status.message)

        update = status.decision.update_state if status.decision else UpdateState.UNKNOWN
        self.update_var.set(f"Update: {update.value}")

        self.protected_button.configure(state="normal" if status.protected_enabled else "disabled")
        activation_available = (
            status.state == AppState.ACTIVATION_REQUIRED
            and status.decision is not None
            and status.decision.license_center_url is not None
        )
        self.activate_button.configure(state="normal" if activation_available else "disabled")

    def open_license_center(self) -> None:
        decision = self.controller.status.decision
        if decision is None or not decision.activation_required or decision.license_center_url is None:
            return
        webbrowser.open(decision.license_center_url)

    def run_protected(self) -> None:
        def protected_action() -> None:
            self.output_var.set("Protected functionality executed after ALLOW.")

        if not self.controller.run_protected(protected_action):
            self.output_var.set("Protected functionality blocked: authorization is not ALLOW.")


def run_gui(manifest_path: str | None = None, installation_id: str | None = None) -> None:
    root = tk.Tk()
    controller = DemoController(
        manifest_path=manifest_path or str(default_manifest_path()),
        installation_id=installation_id or str(uuid.uuid4()),
    )
    DemoAppWindow(root, controller)
    root.mainloop()
