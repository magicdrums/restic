# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, GLib, Gtk

from restic_desktop.restic import ResticError, list_snapshots, restore
from restic_desktop.ui.file_chooser import pick_folder


class RestorePage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._win = window

        form = Adw.PreferencesGroup(title="Restaurar desde instantánea")

        self._snapshot_row = Adw.ComboRow(title="Instantánea")
        form.add(self._snapshot_row)

        self._target_row = Adw.EntryRow(title="Carpeta de destino")
        self._target_row.set_text(str(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)))
        form.add(self._target_row)

        pick_btn = Gtk.Button(label="Elegir carpeta de destino…")
        pick_btn.connect("clicked", self._on_pick_target)
        self.append(form)
        self.append(pick_btn)

        self._restore_btn = Gtk.Button(label="Restaurar")
        self._restore_btn.add_css_class("destructive-action")
        self._restore_btn.connect("clicked", self._on_restore)
        self.append(self._restore_btn)

        self._status = Gtk.Label(label="")
        self._status.set_wrap(True)
        self._status.add_css_class("dim-label")
        self.append(self._status)

        refresh_btn = Gtk.Button(label="Cargar instantáneas")
        refresh_btn.connect("clicked", lambda *_: self._load_snapshots())
        self.append(refresh_btn)

        self._snapshots: list[dict] = []

    def _load_snapshots(self):
        if not self._win.require_repo():
            return

        def work():
            try:
                snaps = list_snapshots(self._win.repository, self._win.password)
                GLib.idle_add(self._fill_snapshots, snaps)
            except ResticError as e:
                GLib.idle_add(self._win.toast, str(e))

        GLib.Thread.new("restore-snapshots", work)

    def _fill_snapshots(self, snaps: list):
        self._snapshots = snaps
        model = Gtk.StringList()
        for snap in snaps:
            sid = snap.get("short_id") or str(snap.get("id", ""))[:8]
            time_str = snap.get("time", "")
            model.append(f"{sid} — {time_str}")
        self._snapshot_row.set_model(model)
        if snaps:
            self._snapshot_row.set_selected(0)

    def _on_pick_target(self, *_):
        pick_folder(self._win, self._target_picked)

    def _target_picked(self, path: str | None) -> None:
        if path:
            self._target_row.set_text(path)

    def _on_restore(self, *_):
        if not self._win.require_repo():
            return
        if not self._snapshots:
            self._win.toast("Carga las instantáneas primero")
            return

        idx = self._snapshot_row.get_selected()
        if idx == Gtk.INVALID_LIST_POSITION:
            self._win.toast("Selecciona una instantánea")
            return

        snap = self._snapshots[idx]
        raw_id = snap.get("id") or snap.get("short_id")
        snapshot_id = str(raw_id) if raw_id else ""
        target = self._target_row.get_text().strip()
        if not target:
            self._win.toast("Indica carpeta de destino")
            return

        self._restore_btn.set_sensitive(False)
        self._status.set_label("Restaurando…")

        def work():
            try:
                restore(
                    self._win.repository,
                    self._win.password,
                    snapshot_id,
                    target,
                )
                GLib.idle_add(self._restore_done, target, None)
            except ResticError as e:
                GLib.idle_add(self._restore_done, None, str(e))

        GLib.Thread.new("restore", work)

    def _restore_done(self, target: str | None, error: str | None):
        self._restore_btn.set_sensitive(True)
        if error:
            self._status.set_label(error)
            self._win.toast(error)
            return
        msg = f"Restauración completada en {target}"
        self._status.set_label(msg)
        self._win.toast(msg)
