# Changelog

Todos los cambios notables de este proyecto se documentan acá.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto sigue [SemVer](https://semver.org/lang/es/).

## [0.1.0] - 2026-07-25

### Agregado

- Ventana flotante transparente con el personaje activo (Tkinter + Pillow),
  arrastrable y siempre-visible configurable.
- Motor de animación por sprite sheet compatible con los assets extraídos de
  Microsoft Agent / Office Assistant.
- 6 personajes clásicos incluidos: Clippy, F1, Genius, Links, Merlin, Rocky.
- Menú de clic derecho: cambiar de personaje, pedir un consejo, "Ayuda de
  Windows" (F1), ocultar/mostrar, siempre visible, idioma, iniciar con
  Windows, acerca de, comprame una cerveza, salir.
- Icono en la bandeja del sistema con el mismo menú.
- Soporte multi-idioma (español/inglés), detectando el idioma de Windows.
- Consejos automáticos periódicos ("tips") y al pedirlos manualmente.
- Botón "Cómprame una cerveza" (PayPal).
- Compilación a `.exe` sin consola con PyInstaller (`tools/build_exe.py`).
- Script de descarga/conversión de personajes (`tools/fetch_assets.py`) e
  importador experimental de archivos `.acs` propios (`tools/acs_importer.py`).
- Versionado semántico (`version.py` + `tools/bump_version.py`).
- Workflows de GitHub Actions para build continuo y release automático por tag.
- Specs, Agents y Skills de Claude Code para mantener el proyecto (ver
  `specs/SPEC.md`, `.claude/agents/`, `.claude/skills/`).
