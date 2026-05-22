# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, Gtk

from restic_desktop import config, credentials
from restic_desktop.restic import ResticError, find_restic, init_repo


class SettingsPage(Adw.PreferencesWindow):
    def __init__(self, parent_window):
        super().__init__(transient_for=parent_window, modal=True)
        self._win = parent_window
        self.set_title("Configuración")

        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Repositorio")

        self._repo_row = Adw.EntryRow(title="Ubicación del repositorio")
        self._repo_row.set_text(config.get_repository() or "")
        self._repo_row.set_show_apply_button(True)
        group.add(self._repo_row)

        self._password_row = Adw.PasswordEntryRow(title="Contraseña del repositorio")
        repo = config.get_repository()
        if repo:
            pwd = credentials.get_password(repo)
            if pwd:
                self._password_row.set_text(pwd)
        group.add(self._password_row)

        page.add(group)

        actions_group = Adw.PreferencesGroup(title="Acciones")

        init_row = Adw.ActionRow(
            title="Inicializar repositorio",
            subtitle="Crea un repositorio vacío en la ubicación indicada",
        )
        init_btn = Gtk.Button(label="Inicializar")
        init_btn.add_css_class("suggested-action")
        init_btn.connect("clicked", self._on_init)
        init_row.add_suffix(init_btn)
        actions_group.add(init_row)

        save_row = Adw.ActionRow(
            title="Guardar configuración",
            subtitle="Guarda repositorio y contraseña en el llavero",
        )
        save_btn = Gtk.Button(label="Guardar")
        save_btn.connect("clicked", self._on_save)
        save_row.add_suffix(save_btn)
        actions_group.add(save_row)

        page.add(actions_group)
        self.add(page)

    @classmethod
    def as_dialog(cls, parent_window):
        return cls(parent_window)

    def _on_save(self, *_):
        repo = self._repo_row.get_text().strip()
        password = self._password_row.get_text()
        if not repo or not password:
            self._win.toast("Indica repositorio y contraseña")
            return
        self._win.set_repository(repo, password)
        self._win.toast("Configuración guardada")
        self.close()

    def _on_init(self, *_):
        repo = self._repo_row.get_text().strip()
        password = self._password_row.get_text()
        if not repo or not password:
            self._win.toast("Indica repositorio y contraseña para inicializar")
            return
        try:
            find_restic()
            init_repo(repo, password)
            self._win.set_repository(repo, password)
            self._win.toast("Repositorio inicializado correctamente")
            self.close()
        except ResticError as e:
            self._win.toast(str(e))
