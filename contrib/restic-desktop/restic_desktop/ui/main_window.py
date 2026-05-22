# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, GLib, Gtk

from restic_desktop import config, credentials
from restic_desktop.ui.pages.backup import BackupPage
from restic_desktop.ui.pages.restore import RestorePage
from restic_desktop.ui.pages.settings import SettingsPage
from restic_desktop.ui.pages.snapshots import SnapshotsPage


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Restic Desktop")
        self.set_default_size(900, 640)

        self._repo: str | None = config.get_repository()
        self._password: str | None = None
        if self._repo:
            self._password = credentials.get_password(self._repo)

        self._toast_overlay = Adw.ToastOverlay()
        self.set_content(self._toast_overlay)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(12)
        toolbar.set_margin_end(12)
        toolbar.set_margin_top(6)
        toolbar.set_margin_bottom(6)

        self._repo_label = Gtk.Label()
        self._repo_label.set_hexpand(True)
        self._repo_label.set_xalign(0)
        self._repo_label.add_css_class("dim-label")
        toolbar.append(self._repo_label)

        settings_btn = Gtk.Button(icon_name="emblem-system-symbolic")
        settings_btn.set_tooltip_text("Configuración del repositorio")
        settings_btn.connect("clicked", self._open_settings)
        toolbar.append(settings_btn)

        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Restic Desktop"))
        header.pack_start(toolbar)

        self._snapshots_page = SnapshotsPage(self)
        self._backup_page = BackupPage(self)
        self._restore_page = RestorePage(self)

        view_stack = Adw.ViewStack()
        view_stack.add_titled(self._snapshots_page, "snapshots", "Instantáneas")
        view_stack.add_titled(self._backup_page, "backup", "Copia de seguridad")
        view_stack.add_titled(self._restore_page, "restore", "Restaurar")
        view_stack.set_margin_top(6)
        view_stack.set_margin_bottom(12)
        view_stack.set_margin_start(12)
        view_stack.set_margin_end(12)

        switcher = Adw.ViewSwitcher()
        switcher.set_stack(view_stack)
        switcher.set_policy(Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(switcher)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.append(header)
        content.append(view_stack)
        self._toast_overlay.set_child(content)

        self._update_repo_label()
        if self._repo and self._password:
            GLib.idle_add(self._snapshots_page.refresh)

    def toast(self, message: str, *, timeout: int = 4) -> None:
        toast = Adw.Toast.new(message)
        toast.set_timeout(timeout)
        self._toast_overlay.add_toast(toast)

    def _open_settings(self, *_):
        dialog = SettingsPage.as_dialog(self)
        dialog.present()

    def _update_repo_label(self):
        if self._repo:
            self._repo_label.set_label(f"Repositorio: {self._repo}")
        else:
            self._repo_label.set_label("Sin repositorio configurado")

    def set_repository(self, repo: str, password: str) -> None:
        config.set_repository(repo)
        credentials.store_password(repo, password)
        self._repo = repo
        self._password = password
        self._update_repo_label()
        self._snapshots_page.refresh()

    @property
    def repository(self) -> str | None:
        return self._repo

    @property
    def password(self) -> str | None:
        return self._password

    def require_repo(self) -> bool:
        if self._repo and self._password:
            return True
        self.toast("Configura primero el repositorio y la contraseña")
        self._open_settings()
        return False
