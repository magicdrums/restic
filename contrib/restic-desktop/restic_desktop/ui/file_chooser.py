# SPDX-License-Identifier: BSD-2-Clause
"""Selector de carpetas compatible con Fedora / portales GTK."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")

from gi.repository import GLib, Gio, Gtk


def gfile_to_path(gfile: Gio.File | None) -> str | None:
    if gfile is None:
        return None
    path = gfile.get_path()
    if path:
        return path
    uri = gfile.get_uri()
    if uri and uri.startswith("file://"):
        return GLib.filename_from_uri(uri)[0]
    return None


def pick_folder(window: Gtk.Window, on_selected) -> None:
    """Abre un diálogo para elegir carpeta. on_selected(path|None)."""

    def done_native(chooser: Gtk.FileChooserNative, response: Gtk.ResponseType) -> None:
        path = None
        if response == Gtk.ResponseType.ACCEPT:
            path = gfile_to_path(chooser.get_file())
        chooser.destroy()
        on_selected(path)

    try:
        chooser = Gtk.FileChooserNative.new(
            "Seleccionar carpeta",
            window,
            Gtk.FileChooserAction.SELECT_FOLDER,
            "Añadir",
            "Cancelar",
        )
        chooser.connect("response", done_native)
        chooser.show()
        return
    except Exception:
        pass

    dialog = Gtk.FileDialog(title="Seleccionar carpeta")

    def done_dialog(source: Gtk.FileDialog, result) -> None:
        path = None
        try:
            folder = source.select_folder_finish(result)
            path = gfile_to_path(folder)
        except GLib.Error:
            path = None
        on_selected(path)

    dialog.select_folder(window, None, done_dialog)
