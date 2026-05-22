# Restic Desktop

Interfaz gráfica de escritorio para [restic](https://restic.net) en Fedora y entornos GNOME. Envuelve el binario `restic` (no lo reemplaza) y usa salida `--json` para las operaciones.

## Funciones

- Configurar repositorio (local, SFTP, S3, etc.)
- Guardar contraseña en el llavero GNOME (libsecret)
- Inicializar repositorio nuevo
- Copia de seguridad de carpetas seleccionadas con barra de progreso
- Listar y verificar instantáneas
- Restaurar una instantánea a una carpeta de destino

## Requisitos (Fedora)

```bash
sudo dnf install restic python3-gobject python3-gobject-devel \
  libadwaita libadwaita-devel python3-pip
pip install --user secretstorage
```

En Fedora 41+ suele bastar:

```bash
sudo dnf install restic python3-gobject libadwaita python3-secretstorage
```

## Ejecución sin instalar

Desde este directorio:

```bash
chmod +x restic-desktop
./restic-desktop
```

## Instalación

```bash
meson setup build
meson compile -C build
sudo meson install -C build
```

Luego inicia la aplicación desde el menú de actividades (**Restic Desktop**) o con:

```bash
restic-desktop
```

## Uso rápido

1. Abre **Restic Desktop** y pulsa el icono de configuración.
2. Indica la ruta del repositorio (por ejemplo `/home/TU_USUARIO/backups/restic`) y una contraseña segura.
3. Si el repositorio no existe, usa **Inicializar repositorio nuevo**.
4. En **Copia de seguridad**, añade carpetas y pulsa **Iniciar copia de seguridad**.
5. En **Instantáneas** revisa las copias creadas.
6. En **Restaurar**, elige una instantánea y la carpeta de destino.

## Arquitectura

```
┌─────────────────────┐
│  GTK4 / libadwaita  │  ← interfaz (Python + PyGObject)
└──────────┬──────────┘
           │ subprocess + RESTIC_* env
┌──────────▼──────────┐
│   restic (binario)  │  ← cifrado, deduplicación, backends
└─────────────────────┘
```

Restic no expone una API de biblioteca Go; la integración oficial para scripts y GUIs es ejecutar el CLI con `--json`.

## Licencia

BSD 2-Clause (igual que restic).
