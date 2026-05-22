# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, GLib, Gtk

from restic_desktop.restic import ResticError, check_repo, list_snapshots


class SnapshotsPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._win = window

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        refresh_btn = Gtk.Button(label="Actualizar")
        refresh_btn.connect("clicked", lambda *_: self.refresh())
        check_btn = Gtk.Button(label="Verificar repositorio")
        check_btn.connect("clicked", self._on_check)
        toolbar.append(refresh_btn)
        toolbar.append(check_btn)
        self.append(toolbar)

        scrolled = Gtk.ScrolledWindow(vexpand=True)
        self._list = Gtk.ListBox()
        self._list.add_css_class("boxed-list")
        self._list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        scrolled.set_child(self._list)
        self.append(scrolled)

        self._status = Gtk.Label(label="")
        self._status.add_css_class("dim-label")
        self.append(self._status)

        self._spinner = Gtk.Spinner()
        toolbar.append(self._spinner)

    def refresh(self):
        if not self._win.require_repo():
            return
        self._spinner.start()
        self._status.set_label("Cargando instantáneas…")

        def work():
            try:
                snaps = list_snapshots(self._win.repository, self._win.password)
                GLib.idle_add(self._show_snapshots, snaps)
            except ResticError as e:
                GLib.idle_add(self._show_error, str(e))

        GLib.Thread.new("snapshots", work)

    def _show_error(self, msg: str):
        self._spinner.stop()
        self._status.set_label(msg)
        self._win.toast(msg)

    def _show_snapshots(self, snaps: list):
        self._spinner.stop()
        while child := self._list.get_first_child():
            self._list.remove(child)

        if not snaps:
            self._status.set_label("No hay instantáneas en este repositorio")
            return

        self._status.set_label(f"{len(snaps)} instantánea(s)")
        for snap in snaps:
            sid = snap.get("short_id") or snap.get("id", "")[:8]
            time_str = snap.get("time", "")
            hostname = snap.get("hostname", "")
            paths = ", ".join(snap.get("paths", []))
            tags = ", ".join(snap.get("tags", []))

            row = Adw.ActionRow(title=f"{sid} — {time_str}")
            row.set_subtitle(f"{hostname} | {paths}" + (f" | [{tags}]" if tags else ""))
            self._list.append(row)

    def _on_check(self, *_):
        if not self._win.require_repo():
            return
        self._spinner.start()
        self._status.set_label("Verificando repositorio…")

        def work():
            try:
                summary = check_repo(self._win.repository, self._win.password)
                errors = summary.get("num_errors", 0)
                if errors:
                    msg = f"Verificación completada con {errors} error(es)"
                else:
                    msg = "Repositorio verificado sin errores"
                GLib.idle_add(self._check_done, msg)
            except ResticError as e:
                GLib.idle_add(self._check_done, str(e), True)

        GLib.Thread.new("check", work)

    def _check_done(self, msg: str, is_error: bool = False):
        self._spinner.stop()
        self._status.set_label(msg)
        self._win.toast(msg)
