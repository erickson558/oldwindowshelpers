# Changelog

Todos los cambios notables de este proyecto se documentan acá.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto sigue [SemVer](https://semver.org/lang/es/).

## [0.5.2] - 2026-07-27

### Corregido

- **El menú se quedaba trabado en "Idioma" al moverse por él**: mismo límite
  de fondo que el bug de v0.5.1, pero para eventos `<Motion>` (pasar el
  mouse) en vez de clics. Con el grab global activo, Windows puede
  redirigir el `<Motion>` real hacia el `Toplevel` del submenú que lo
  sostiene, aunque el mouse ya esté sobre una fila del padre —
  `_on_motion` interpretaba ese evento con las coordenadas locales del
  canvas equivocado, y el hover quedaba pegado en "Idioma" para siempre,
  sin cerrar su submenú ni dejar seguir navegando. Se corrige calculando
  a qué nivel de la cadena corresponde de verdad la posición ABSOLUTA de
  pantalla del mouse (`_dispatch_motion_by_root`), en vez de confiar en
  las coordenadas locales del canvas que recibió el evento
  (`app/win98_menu.py`, detalle en specs/SPEC.md 2.4b).

## [0.5.1] - 2026-07-27

### Corregido

- **El menú de clic derecho no dejaba elegir otro personaje (ni otro
  idioma)**: `grab_set_global()` (agregado en v0.5.0 para que el menú se
  cerrara con un clic fuera de la app) no se extiende a otros `Toplevel` de
  la misma aplicación, solo al que pidió el grab — y un submenú
  ("Cambiar personaje", "Idioma") es un `Toplevel` separado del nivel
  superior. El nivel superior se quedaba con el grab para siempre, así que
  los clics dentro de un submenú abierto quedaban atrapados y no hacían
  nada. Confirmado en vivo con un clic real simulado (no un evento
  sintético de Tk, que no hubiera reproducido el problema). Se corrige
  transfiriendo el grab al nivel más profundo actualmente abierto en vez de
  dejarlo fijo en el nivel superior (`app/win98_menu.py`, detalle completo
  en specs/SPEC.md 2.4b).

## [0.5.0] - 2026-07-27

### Agregado

- **Menú de clic derecho con estilo Windows 98**: la ventana flotante ya no
  usa el menú nativo de Tkinter (en Windows no se puede recolorear ni
  animar) sino un widget propio (`app/win98_menu.py`) con la estética
  clásica — cara gris, selección azul marino, bordes/separadores hundidos —
  y una animación de "desenrollado" al abrirse, igual que el efecto real de
  menús de Windows 98. El menú de la bandeja del sistema sigue siendo el
  nativo del sistema operativo (no se puede reskinar, es un camino de
  render completamente distinto).
- **Letras mnemónicas subrayadas, siempre visibles**: cada opción del menú
  tiene una letra propia (sin colisiones dentro de un mismo nivel,
  verificado con tests) que se puede apretar directamente para activarla —
  a diferencia de Windows moderno, no quedan ocultas hasta apretar Alt.
  Navegación completa por teclado (flechas, Enter, Escape, apertura/cierre
  de submenús).
- **Globo de diálogo estilo Windows XP**: "Decime un consejo"/"Animar" ya no
  muestran un rectángulo plano — ahora es un globo con forma de tooltip/
  balloon clásico (rounded rectangle, cola apuntando al personaje, sombra),
  horneado como un único bitmap con Pillow (misma técnica de endurecido de
  alfa que ya usan los sprites, para no repetir el bug del halo mágenta).

### Corregido (encontrado en revisión adversarial antes de publicarse)

- El wrap de texto del globo nuevo no cortaba una palabra sin espacios más
  ancha que el área de wrap (una URL, un typo de traducción), generando un
  globo de miles de píxeles de ancho — se agregó corte carácter-por-carácter
  como resguardo, igual que hacía el `wraplength` de Tk que se reemplazó.
- El menú nuevo no se cerraba si el usuario hacía clic fuera de la app
  entera (el escritorio, la barra de tareas, otra ventana) — solo cubría
  clics dentro de la propia app. Se agrega `grab_set_global()` (la técnica
  que documenta Tcl/Tk para esto) — ver specs/SPEC.md 2.4b para el detalle
  de qué otras dos soluciones se probaron y no funcionaron de forma
  confiable, y la limitación conocida que queda documentada a propósito.

## [0.4.2] - 2026-07-27

### Corregido

- **Will, Saeko Sensei y Power Pup se veían "animados cuando cargan, no
  estables"**: el loop `Idle` de estos personajes elegía el bloque de
  frames de mayor área PROMEDIO nomás, sin mirar cuánto variaba el tamaño
  de un frame al siguiente dentro de ese mismo bloque (Power Pup llegaba a
  tener 37x de diferencia entre su frame más chico y más grande dentro del
  "Idle" elegido) — en loop continuo eso se ve como estar a mitad de una
  transformación. Además, cada frame se apoyaba abajo dentro de su celda
  de tamaño fijo, así que un frame chico y uno grande consecutivos también
  saltaban de posición vertical. Investigando el bug se encontró una
  tercera causa más sutil: Saeko Sensei y Monkey King vienen con TODOS sus
  frames en el mismo lienzo nominal sin recortar, así que medir "área"
  como ancho×alto del PNG no distinguía nada para estos dos — se cambió a
  medir el bounding box real del canal alfa. Con las tres causas
  corregidas (`tools/fetch_extra_assets.py`), Saeko Sensei y Monkey King
  quedaron con un `Idle` prácticamente perfecto (pose completa y estable);
  Will y Power Pup mejoraron la posición (ya no saltan verticalmente) pero
  conservan algo de variación de tamaño — verificado en vivo que es un
  límite real del material de origen de esos dos personajes en particular
  (documentado en specs/SPEC.md 2.3b), no del algoritmo.

## [0.4.1] - 2026-07-27

### Corregido

- **Power Pup, Will y los personajes de fidelidad reducida se veían "a
  media animación"**: el diseño de v0.4.0 reproducía TODOS los frames del
  personaje como un solo disparo — para Saeko Sensei/Monkey King eso eran
  **más de 2 minutos y medio** por click de "Animar". Si el usuario hacía
  cualquier otra cosa antes de que terminara, volvía a encontrar al
  personaje congelado en un frame cualquiera del medio. Se reemplaza por
  varias animaciones cortas (`MotionNN`, ~2s cada una), partiendo la
  secuencia en bloques consecutivos en vez de una sola animación gigante.
- De paso se recupera la variedad de "animaciones random" que tienen el
  resto de los personajes: antes "Decime un consejo"/"Animar" repetían
  siempre la misma secuencia completa; ahora eligen al azar entre 8-84
  gestos cortos distintos según el personaje.

## [0.4.0] - 2026-07-25

### Corregido

- **Power Pup se veía "roto"**: su animación única mezclaba poses completas
  del personaje con instantes de transición sin contexto (nubes, capas
  sueltas) — se veían como manchas al azar. Se separó en dos animaciones:
  `Idle` (solo poses grandes/reconocibles, en loop calmo) y `Transform` (la
  secuencia completa, como gesto de un solo disparo vía "Animar"). Mismo
  tratamiento para Scribble, y para los 3 personajes nuevos de fidelidad
  reducida agregados en esta versión.
- Se descartan del todo frames que no son animación real coladas en los
  ZIPs de origen (íconos/miniaturas de fondo sólido, ej. una miniatura de
  modelo 3D encontrada en Scribble).
- Saeko Sensei y Monkey King venían con fondo mágenta opaco en vez de
  transparencia real (formato de paleta sin canal alfa) — se hubieran visto
  como un rectángulo sólido en la ventana flotante; se convierte el mágenta
  a transparencia de verdad antes de armar su sprite sheet.

### Agregado

- **Kairu** (delfín, ediciones asiáticas): agregado directamente con
  animaciones completas, decodificando su `.acs` real (`DOLPHIN.ACS`,
  mismo archivo de preservación que ya usábamos para Mother Nature/Office
  Logo/The Dot).
- **Will, Saeko Sensei y Monkey King**: 3 personajes nuevos (fidelidad
  reducida, vía The Spriters Resource — no se encontró su `.acs` real pese
  a buscarlo en esta y la sesión anterior).
- Investigación documentada de por qué Hoverbot, Bosgrove, Max y Earl
  siguen sin poder incorporarse (ver specs/SPEC.md 2.1).
- Se detectó y descartó `OFFCAT.ACS` (del mismo archivo de preservación)
  como duplicado de Links, no un personaje nuevo.

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
