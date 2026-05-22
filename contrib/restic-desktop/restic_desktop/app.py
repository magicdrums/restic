# SPDX-License-Identifier: BSD-2-Clause
"""Aplicación GTK4 / libadwaita."""

from __future__ import annotations

import sys

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw  # noqa: E402

from restic_desktop.ui.main_window import MainWindow  # noqa: E402


class ResticDesktopApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.restic.ResticDesktop")

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = MainWindow(application=self)
        win.present()


def main() -> int:
    Adw.init()
    app = ResticDesktopApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
