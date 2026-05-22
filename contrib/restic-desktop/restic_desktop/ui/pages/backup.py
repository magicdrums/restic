# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

import os

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, GLib, Gtk

from restic_desktop import config
from restic_desktop.restic import BackupProgress, ResticError, backup
from restic_desktop.ui.file_chooser import pick_folder


class BackupPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._win = window

        label = Gtk.Label(label="Carpetas a respaldar", xalign=0)
        label.add_css_class("title-4")
        self.append(label)

        self._paths_box = Gtk.ListBox()
        self._paths_box.add_css_class("boxed-list")
        self._paths_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.append(self._paths_box)

        manual_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._manual_path = Gtk.Entry()
        self._manual_path.set_placeholder_text("O escribe la ruta: /home/usuario/Documents")
        self._manual_path.set_hexpand(True)
        manual_add_btn = Gtk.Button(label="Añadir ruta")
        manual_add_btn.connect("clicked", self._on_add_manual_path)
        manual_box.append(self._manual_path)
        manual_box.append(manual_add_btn)
        self.append(manual_box)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        add_btn = Gtk.Button(label="Añadir carpeta…")
        add_btn.connect("clicked", self._on_add_folder)
        remove_btn = Gtk.Button(label="Quitar selección")
        remove_btn.connect("clicked", self._on_remove_folder)
        btn_row.append(add_btn)
        btn_row.append(remove_btn)
        self.append(btn_row)

        self._progress = Gtk.ProgressBar(show_text=True)
        self.append(self._progress)

        self._status = Gtk.Label(label="")
        self._status.set_wrap(True)
        self._status.add_css_class("dim-label")
        self.append(self._status)

        self._backup_btn = Gtk.Button(label="Iniciar copia de seguridad")
        self._backup_btn.add_css_class("suggested-action")
        self._backup_btn.connect("clicked", self._on_backup)
        self.append(self._backup_btn)

        self._spinner = Gtk.Spinner()
        btn_row.append(self._spinner)

        self._load_paths()

    def _append_path_row(self, path: str) -> None:
        action_row = Adw.ActionRow(title=path)
        list_row = Gtk.ListBoxRow()
        list_row.set_child(action_row)
        self._paths_box.append(list_row)

    def _path_from_list_row(self, row: Gtk.Widget) -> str | None:
        if isinstance(row, Gtk.ListBoxRow):
            child = row.get_child()
            if isinstance(child, Adw.ActionRow):
                return child.get_title()
        if isinstance(row, Adw.ActionRow):
            return row.get_title()
        return None

    def _load_paths(self):
        while child := self._paths_box.get_first_child():
            self._paths_box.remove(child)
        for path in config.get_backup_paths():
            self._append_path_row(path)

    def _paths(self) -> list[str]:
        paths = []
        row = self._paths_box.get_first_child()
        while row:
            path = self._path_from_list_row(row)
            if path:
                paths.append(path)
            row = row.get_next_sibling()
        return paths

    def _save_paths(self, paths: list[str]) -> None:
        config.set_backup_paths(paths)

    def _add_path(self, path: str) -> bool:
        path = os.path.expanduser(path.strip())
        if not path:
            self._win.toast("Indica una ruta válida")
            return False
        if not os.path.isdir(path):
            self._win.toast(f"No existe o no es una carpeta: {path}")
            return False
        paths = self._paths()
        if path in paths:
            self._win.toast("Esa carpeta ya está en la lista")
            return False
        paths.append(path)
        self._save_paths(paths)
        self._append_path_row(path)
        self._win.toast(f"Carpeta añadida: {path}")
        return True

    def _on_add_manual_path(self, *_):
        path = self._manual_path.get_text()
        if self._add_path(path):
            self._manual_path.set_text("")

    def _on_add_folder(self, *_):
        pick_folder(self._win, self._folder_picked)

    def _folder_picked(self, path: str | None) -> None:
        if path is None:
            return
        self._add_path(path)

    def _on_remove_folder(self, *_):
        row = self._paths_box.get_selected_row()
        if not row:
            self._win.toast("Selecciona una carpeta de la lista")
            return
        self._paths_box.remove(row)
        self._save_paths(self._paths())
        self._win.toast("Carpeta quitada")

    def _on_backup(self, *_):
        if not self._win.require_repo():
            return
        paths = self._paths()
        if not paths:
            self._win.toast("Añade al menos una carpeta")
            return

        self._backup_btn.set_sensitive(False)
        self._spinner.start()
        self._progress.set_fraction(0)
        self._status.set_label("Preparando copia de seguridad…")

        def on_progress(p: BackupProgress):
            GLib.idle_add(self._update_progress, p)

        def work():
            try:
                summary = backup(
                    self._win.repository,
                    self._win.password,
                    paths,
                    on_progress=on_progress,
                )
                GLib.idle_add(self._backup_done, summary.snapshot_id, None)
            except ResticError as e:
                GLib.idle_add(self._backup_done, None, str(e))

        GLib.Thread.new("backup", work)

    def _update_progress(self, p: BackupProgress):
        self._progress.set_fraction(min(p.percent_done / 100.0, 1.0))
        self._progress.set_text(f"{p.percent_done:.1f}%")
        files = f"{p.files_done}/{p.total_files} archivos"
        self._status.set_label(files)

    def _backup_done(self, snapshot_id: str | None, error: str | None):
        self._spinner.stop()
        self._backup_btn.set_sensitive(True)
        if error:
            self._status.set_label(error)
            self._win.toast(error)
            return
        self._progress.set_fraction(1.0)
        msg = f"Copia completada. Snapshot: {snapshot_id}"
        self._status.set_label(msg)
        self._win.toast(msg)
        self._win._snapshots_page.refresh()
