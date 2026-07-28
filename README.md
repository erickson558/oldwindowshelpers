# OldWindowsHelpers 📎

[![Version](https://img.shields.io/badge/version-0.5.2-blue)](CHANGELOG.md)
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
- [Aviso de antivirus](#aviso-de-antivirus-falso-positivo-conocido)
- [Versionado](#versionado)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Desarrollo con Claude Code](#desarrollo-con-claude-code)
- [Aviso sobre los personajes](#aviso-sobre-los-personajes)
- [Changelog](#changelog)
- [Licencia](#licencia)

## Características

- **Ventana flotante transparente**: el personaje aparece sin bordes ni fondo
  sobre el escritorio, arrastrable con el mouse.
- **15 personajes clásicos** listos para usar — los verdaderos "Office
  Assistant" de Microsoft Office. 10 con animaciones completas y nombradas
  (Clippy, F1, Genius, Links, Merlín, Rocky, Mother Nature, Office Logo,
  The Dot y Kairu) y 5 con "Idle" + varias animaciones cortas `MotionNN`
  (~2s cada una, elegidas al azar) por no haber podido recuperar su archivo
  original (Power Pup, Scribble, Will, Saeko Sensei, Monkey King) — ver
  [`specs/SPEC.md`](specs/SPEC.md) 2.1.
- **Mismo tamaño y sin fleco de color** en todos los personajes, sin
  importar el tamaño real de su sprite original, y con soporte para
  pantallas de alto DPI (ver `app/animation.py` y `app/dpi.py`).
- **Menú de clic derecho con estilo Windows 98**: sobre la ventana flotante,
  un menú propio (no el nativo de Tkinter, que en Windows no se puede
  recolorear ni animar) con la estética clásica — gris, selección azul
  marino, animación de desenrollado — y **letras mnemónicas subrayadas
  siempre visibles** (Alt+letra, o directamente la letra, activa cada
  opción). También disponible (sin este estilo, con el menú nativo del
  sistema) desde la bandeja:
  - Cambiar personaje
  - Decime un consejo (con globo de diálogo estilo Windows XP)
  - **Animar**: el gesto de firma de cada personaje (Clippy se hace mago,
    Merlín tira un hechizo exclusivo suyo, Rocky escarba en la basura, etc.)
  - Ayuda de Windows (simula F1, el atajo universal de ayuda)
  - Siempre visible / Ocultar / Mostrar
  - Idioma (Español/English)
  - Iniciar con Windows
  - Acerca de
  - ☕ Cómprame una cerveza
  - Salir
- **Consejos automáticos** cada cierto tiempo, además de bajo demanda, en un
  globo de diálogo con la forma clásica de Windows XP (rounded rectangle,
  cola, sombra).
- **Multi-idioma** (es/en), detecta el idioma de Windows por defecto.
- **Sin consola**: corre como app de escritorio pura (`--windowed`).
- Herramientas para **agregar más personajes** propios, incluyendo un
  decodificador real del formato `.acs` de Microsoft Agent
  (`tools/acs_importer.py`, `tools/acs_decoder.py`).

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
python tools/fetch_assets.py         # 6 de alta fidelidad, via clippy.js
python tools/fetch_acs_assets.py     # 4 de alta fidelidad, via .acs real decodificado
python tools/fetch_extra_assets.py   # 5 de fidelidad reducida, via Spriters Resource
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

Esto corre PyInstaller con `--onefile --windowed --noupx` (más un recurso de
versión con metadata real, ver "Aviso de antivirus" abajo), usa
`clippy_icon_136771.ico` como ícono, empaqueta `assets/` y `locales/`, y deja
**`OldWindowsHelpers.exe` en la misma carpeta que `main.py`** (no abre
consola, al ser una app gráfica).

## Aviso de antivirus (falso positivo conocido)

Algunos antivirus (Kaspersky en particular) pueden marcar `OldWindowsHelpers.exe`
como sospechoso, sobre todo al activar **"Iniciar con Windows"** desde el
menú. Esto es un **falso positivo muy conocido y documentado** en la
comunidad de PyInstaller: cualquier `.exe` sin firma digital que se auto-
registra en el arranque de Windows dispara heurísticas antivirus, sin que
eso signifique que el código sea malicioso. Podés revisar el código fuente
completo de este repo — es 100% Python legible, sin ofuscar.

Qué hacemos para mitigarlo (sin poder eliminarlo del todo, porque requeriría
un certificado de firma de código pago):

- Compilamos con `--noupx` (UPX es una técnica de compresión que también usa
  mucho malware para evadir firmas).
- El `.exe` incluye metadata de versión real (nombre, descripción, versión) —
  la mayoría del malware no la tiene.
- Si igual se bloquea la escritura al registro, la app avisa con un mensaje
  claro en vez de fallar en silencio, y reintenta activarlo la próxima vez
  que abrís la app (por si el antivirus lo había borrado sin avisar).

Qué podés hacer vos si tu antivirus lo bloquea:

1. Agregar una excepción puntual para `OldWindowsHelpers.exe` en tu antivirus.
2. Reportarlo como falso positivo (Kaspersky: https://opentip.kaspersky.com/,
   subís el archivo y pedís que lo revisen).
3. Si preferís no arriesgar, no actives "Iniciar con Windows" — el resto de
   la app funciona igual sin esa opción.

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
│   ├── menu_actions.py         # arma el menú de clic derecho (Win98Menu)
│   ├── win98_menu.py            # widget de menú propio, estilo Windows 98
│   ├── balloon.py                # globo de diálogo estilo Windows XP
│   ├── signature_actions.py    # gesto de firma por personaje ("Animar")
│   ├── tray.py                 # ícono de bandeja del sistema
│   ├── settings.py             # config.json + autoarranque (registro de Windows)
│   ├── i18n.py                  # traducciones
│   ├── windows_help.py          # acción "Ayuda de Windows" (F1)
│   ├── dpi.py                    # DPI awareness (pantallas de escalado alto)
│   └── resources.py             # rutas de recursos (fuente vs. .exe empaquetado)
├── assets/agents/<Nombre>/     # sprite sheet + animaciones de cada personaje
├── locales/{es,en}.json          # textos traducidos
├── tools/
│   ├── fetch_assets.py          # descarga/convierte personajes desde clippy.js
│   ├── acs_decoder.py             # decodificador real del formato .acs de Microsoft Agent
│   ├── fetch_acs_assets.py        # descarga/convierte via .acs real (alta fidelidad)
│   ├── fetch_extra_assets.py       # descarga/convierte via Spriters Resource (fidelidad reducida)
│   ├── acs_importer.py             # importa un .acs propio (usa acs_decoder.py)
│   ├── bump_version.py              # sube la versión + CHANGELOG + badge de README
│   └── build_exe.py                  # compila el .exe con PyInstaller
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

Los 15 personajes (Clippy, Merlín, Links, Rocky, Genius, F1, Mother Nature,
Office Logo, The Dot, Kairu, Power Pup, Scribble, Will, Saeko Sensei y
Monkey King) son propiedad de Microsoft Corporation; se incluyen
únicamente con fines de preservación y nostalgia, no comerciales. El
código de este repositorio (todo lo que **no** esté en
`assets/agents/`) es de autoría propia y se licencia en Apache 2.0 —
incluyendo `tools/acs_decoder.py`, un decodificador propio del formato
binario `.acs`, escrito investigando el formato (no copiando código de
terceros). Ver [`NOTICE`](NOTICE) para el detalle completo y la atribución a
[clippy.js](https://github.com/clippyjs/clippy.js),
[The Spriters Resource](https://www.spriters-resource.com) y al archivo de
preservación de [archive.org](https://archive.org/details/binder-97-office972000assistants)
de donde salieron los `.acs` originales.

## Changelog

Ver [`CHANGELOG.md`](CHANGELOG.md).

## Licencia

Código bajo [Apache License 2.0](LICENSE). Los assets de personajes tienen un
régimen distinto — ver el aviso arriba y [`NOTICE`](NOTICE).
