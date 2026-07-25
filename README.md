# OldWindowsHelpers 📎

[![Version](https://img.shields.io/badge/version-0.2.0-blue)](CHANGELOG.md)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey)](#requisitos)

Trae de vuelta a los clásicos **Ayudantes de Office** (Clippy, Merlín, Links,
Rocky, Genius, F1) como personajes animados y flotantes sobre tu escritorio de
Windows, con menú de clic derecho para cambiar de personaje y pedirles ayuda —
como en Office 97/2000/XP/2003, pero para cualquier Windows moderno.

☕ Si te divierte, [comprame una cerveza](https://www.paypal.com/donate/?hosted_button_id=ZABFRXC2P3JQN).

## Índice

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Compilación a .exe](#compilación-a-exe)
- [Versionado](#versionado)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Desarrollo con Claude Code](#desarrollo-con-claude-code)
- [Aviso sobre los personajes](#aviso-sobre-los-personajes)
- [Changelog](#changelog)
- [Licencia](#licencia)

## Características

- **Ventana flotante transparente**: el personaje aparece sin bordes ni fondo
  sobre el escritorio, arrastrable con el mouse.
- **11 personajes clásicos** listos para usar — los verdaderos "Office
  Assistant" de Microsoft Office: Clippy, F1, Genius, Links, Merlín y Rocky
  (alta fidelidad, animaciones nombradas) más Mother Nature, Office Logo,
  The Dot, Scribble y Power Pup (fidelidad reducida — ver
  [`specs/SPEC.md`](specs/SPEC.md) 2.1).
- **Menú de clic derecho** (también disponible en la bandeja del sistema):
  - Cambiar personaje
  - Decime un consejo (con globo de diálogo)
  - **Animar**: el gesto de firma de cada personaje (Clippy se hace mago,
    Merlín tira un hechizo exclusivo suyo, Rocky escarba en la basura, etc.)
  - Ayuda de Windows (simula F1, el atajo universal de ayuda)
  - Siempre visible / Ocultar / Mostrar
  - Idioma (Español/English)
  - Iniciar con Windows
  - Acerca de
  - ☕ Cómprame una cerveza
  - Salir
- **Consejos automáticos** cada cierto tiempo, además de bajo demanda.
- **Multi-idioma** (es/en), detecta el idioma de Windows por defecto.
- **Sin consola**: corre como app de escritorio pura (`--windowed`).
- Herramientas para **agregar más personajes** propios (`tools/fetch_assets.py`,
  `tools/acs_importer.py`).

## Requisitos

- Windows 10/11 (usa APIs de Windows para el idioma y el autoarranque; en
  teoría corre sobre cualquier Windows con Python 3.11+, pero solo se probó
  en Windows moderno).
- Python 3.11 o superior (solo para correr desde código fuente o compilar;
  el `.exe` ya compilado no necesita Python instalado).

## Instalación

```powershell
git clone https://github.com/erickson558/oldwindowshelpers.git
cd oldwindowshelpers
pip install -r requirements.txt
```

Los personajes (sprites) ya vienen incluidos en `assets/agents/`. Si querés
volver a descargarlos o agregar los que falten:

```powershell
python tools/fetch_assets.py         # los 6 de alta fidelidad (clippy.js)
python tools/fetch_extra_assets.py   # los 5 de fidelidad reducida (Spriters Resource)
```

## Uso

```powershell
python main.py
```

El personaje aparece flotando cerca de la esquina inferior derecha del
escritorio. Hacé **clic derecho** sobre él (o sobre el ícono en la bandeja del
sistema) para abrir el menú de acciones.

## Compilación a .exe

```powershell
pip install -r requirements-dev.txt
python tools/build_exe.py
```

Esto corre PyInstaller con `--onefile --windowed`, usa
`clippy_icon_136771.ico` como ícono, empaqueta `assets/` y `locales/`, y deja
**`OldWindowsHelpers.exe` en la misma carpeta que `main.py`** (no abre
consola, al ser una app gráfica).

## Versionado

Este proyecto sigue [SemVer](https://semver.org/lang/es/) (`vMAJOR.MINOR.PATCH`):

- **MAJOR**: cambios incompatibles (ej. cambia el formato de `assets/agents/*`).
- **MINOR**: funcionalidad nueva compatible (ej. un personaje o acción de menú nueva).
- **PATCH**: arreglos y ajustes menores.

La versión vive en un único lugar, [`version.py`](version.py), y se refleja en
el diálogo "Acerca de", en el tag de git y en el Release de GitHub. Para subir
de versión:

```powershell
python tools/bump_version.py patch   # o minor / major
```

(el script deja impresos los comandos de `git commit`/`tag`/`push` a
continuación — ver también el skill `/release` en
[`.claude/skills/release/`](.claude/skills/release/SKILL.md)).

## Estructura del proyecto

```
oldwindowshelpers/
├── main.py                  # punto de entrada
├── version.py                # versión (fuente única de verdad)
├── app/                       # código de la aplicación
│   ├── character_window.py   # ventana flotante + animación + drag
│   ├── animation.py           # motor de sprite sheets
│   ├── menu_actions.py         # menú de clic derecho
│   ├── signature_actions.py    # gesto de firma por personaje ("Animar")
│   ├── tray.py                 # ícono de bandeja del sistema
│   ├── settings.py             # config.json + autoarranque (registro de Windows)
│   ├── i18n.py                  # traducciones
│   ├── windows_help.py          # acción "Ayuda de Windows" (F1)
│   └── resources.py             # rutas de recursos (fuente vs. .exe empaquetado)
├── assets/agents/<Nombre>/     # sprite sheet + animaciones de cada personaje
├── locales/{es,en}.json          # textos traducidos
├── tools/
│   ├── fetch_assets.py          # descarga/convierte personajes desde clippy.js
│   ├── fetch_extra_assets.py     # descarga/convierte personajes desde Spriters Resource
│   ├── acs_importer.py           # importador experimental de .acs propios
│   ├── bump_version.py            # sube la versión + CHANGELOG
│   └── build_exe.py                # compila el .exe con PyInstaller
├── tests/                          # pruebas (pytest)
├── specs/SPEC.md                    # especificación viva del proyecto (SDD)
├── .claude/{agents,skills}/           # agentes y skills de Claude Code
└── .github/workflows/                  # CI y release automático
```

## Desarrollo con Claude Code

Este repo aplica *Spec-Driven Development*: [`specs/SPEC.md`](specs/SPEC.md)
es la especificación viva del proyecto y se actualiza junto con cada cambio
de comportamiento relevante. Además trae, para quien use
[Claude Code](https://claude.com/claude-code) en este repo:

- **Agents** (`.claude/agents/`): `python-dev`, `release-manager`,
  `code-commenter`.
- **Skills** (`.claude/skills/`, invocables como `/github-setup`, `/release`,
  `/comment-code`): publicar en GitHub, subir de versión y generar el
  release, y comentar código explicando qué hace cada parte.

Ver [`CLAUDE.md`](CLAUDE.md) para las convenciones del proyecto.

## Aviso sobre los personajes

Los 11 personajes (Clippy, Merlín, Links, Rocky, Genius, F1, Mother Nature,
Office Logo, The Dot, Scribble y Power Pup) son propiedad de Microsoft
Corporation; se incluyen únicamente con fines de preservación y nostalgia,
no comerciales. El código de este repositorio (todo lo que **no** esté en
`assets/agents/`) es de autoría propia y se licencia en Apache 2.0. Ver
[`NOTICE`](NOTICE) para el detalle completo y la atribución a
[clippy.js](https://github.com/clippyjs/clippy.js) y
[The Spriters Resource](https://www.spriters-resource.com), de donde se
obtuvieron ya extraídos.

## Changelog

Ver [`CHANGELOG.md`](CHANGELOG.md).

## Licencia

Código bajo [Apache License 2.0](LICENSE). Los assets de personajes tienen un
régimen distinto — ver el aviso arriba y [`NOTICE`](NOTICE).
