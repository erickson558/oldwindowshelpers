# Changelog

Todos los cambios notables de este proyecto se documentan acá.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto sigue [SemVer](https://semver.org/lang/es/).

## [0.3.0] - 2026-07-25

### Corregido

- **Fleco/halo mágenta visible alrededor de todos los personajes**: la
  transparencia por color-key de Tkinter no hacía blending real, y los
  bordes antialiased del arte original quedaban con un halo rosado —
  confirmado en vivo con capturas de pantalla (no era detectable renderizando
  offline con PIL). Se soluciona endureciendo el canal alfa después de
  escalar cada frame (`app/animation.py`).
- **Tamaño inconsistente entre personajes**: los 6 originales medían
  93-128px de alto y los 5 nuevos hasta 285px — al cambiar de personaje el
  tamaño pegaba un salto incómodo. Ahora todos se escalan a una altura
  fija (`DISPLAY_HEIGHT`), preservando su aspect ratio.
- Sin DPI awareness, en pantallas con escalado de Windows (125%/150%/200%,
  común en laptops modernas) el sistema estiraba la ventana él mismo y se
  veía borrosa — otra causa del reclamo de "tamaño incómodo". Se agrega
  `app/dpi.py`.
- **Falso positivo de Kaspersky** al activar "Iniciar con Windows": se
  compila con `--noupx` y un recurso de versión real (`tools/build_exe.py`),
  y si el antivirus bloquea la escritura al registro la app avisa con un
  mensaje claro y reintenta la próxima vez, en vez de crashear o fallar en
  silencio (`app/settings.py`, `main.py`).

### Agregado

- **Animaciones completas para Mother Nature, Office Logo y The Dot**: se
  investigó y escribió un decodificador propio del formato binario `.acs`
  de Microsoft Agent (`tools/acs_decoder.py`, verificado al 100% contra 3
  archivos reales — ver specs/SPEC.md 2.3c) y se re-generaron estos 3
  personajes con el mismo nivel de detalle que los 6 originales (36-38
  animaciones nombradas cada uno, en vez de una sola "Idle"). Ahora tienen
  entrada propia en `app/signature_actions.py` para "Animar".
  `tools/acs_importer.py` dejó de ser experimental: ahora puede convertir un
  `.acs` propio de verdad.
- Skill `/bugfix` (`.claude/skills/bugfix/`): proceso de análisis →
  corrección → validación → versionado → commit → push para futuros bugs.

## [0.2.0] - 2026-07-25

### Agregado

- Acción **"Animar"** en el menú de clic derecho (ventana y bandeja): a
  diferencia de "Decime un consejo" (animación al azar), reproduce el gesto
  de firma de cada personaje (`app/signature_actions.py`) junto con una
  frase única suya, en es/en.
- 5 personajes nuevos: **Mother Nature, Office Logo, The Dot, Scribble y
  Power Pup** (`tools/fetch_extra_assets.py`), investigados y verificados
  visualmente a partir de The Spriters Resource — ver specs/SPEC.md 2.1/2.3b
  para el detalle de cómo se reconstruyeron (fidelidad reducida: una sola
  animación "Idle" por personaje, en vez del set completo con nombre que
  traen los 6 originales).
- Investigación documentada de personajes reales identificados pero no
  incorporados todavía (Hoverbot, Bosgrove, Max, Earl, Kairu, Will, Saeko
  Sensei, Mono Rey, Manma-chan) y confirmación de que **"Da Vinci" no es un
  Office Assistant real** (ver specs/SPEC.md 2.1).

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
