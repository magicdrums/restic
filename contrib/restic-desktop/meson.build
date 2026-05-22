project('restic-desktop', 'python',
  version: '1.0.0',
  meson_version: '>= 0.59.0',
)

install_subdir(
  'restic_desktop',
  install_dir: get_option('prefix') / 'lib' / 'restic-desktop',
  exclude_files: ['__pycache__'],
)

install_data(
  'data/org.restic.ResticDesktop.desktop',
  install_dir: get_option('prefix') / 'share/applications',
)

install_data(
  'data/org.restic.ResticDesktop.metainfo.xml',
  install_dir: get_option('prefix') / 'share/metainfo',
)

install_data(
  'data/org.restic.ResticDesktop.svg',
  install_dir: get_option('prefix') / 'share/icons/hicolor/scalable/apps',
)

install_data(
  'restic-desktop',
  install_dir: get_option('prefix') / 'bin',
  install_mode: 'rwxr-xr-x',
)
