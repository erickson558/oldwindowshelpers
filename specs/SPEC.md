# Especificación — OldWindowsHelpers

> Documento vivo. Se actualiza junto con cualquier cambio de comportamiento
> relevante (ver reglas de sincronización en [`CLAUDE.md`](../CLAUDE.md)).

## 1. Propósito

Revivir a los "Office Assistant" clásicos de Microsoft Office (Clippy,
Merlín, Links, Rocky, Genius, F1) como personajes animados flotando sobre el
escritorio de Windows, con acciones de clic derecho, para uso personal y
nostálgico — no busca replicar la integración real con Office ni con Windows,
sino su presencia visual y su espíritu de "ayudante".

## 2. Alcance funcional

### 2.1 Personajes

**Alta fidelidad** (10 — animaciones completas y nombradas: Wave, Greeting,
Congratulate, etc. Ver [`NOTICE`](../NOTICE)):

| Personaje | Rol original en Office Assistant | Fuente |
|---|---|---|
| Clippy (Clippit) | El clip, el más icónico | `clippy.js` (`tools/fetch_assets.py`) |
| F1 | Robot | `clippy.js` |
| Genius | Einstein | `clippy.js` |
| Links | El gato | `clippy.js` |
| Merlin | El mago | `clippy.js` |
| Rocky | El perro | `clippy.js` |
| Mother Nature | El globo terráqueo que se transforma en imágenes de la naturaleza | archivo `.acs` real (`tools/fetch_acs_assets.py`) |
| Office Logo | El logo animado y giratorio de Office 9x | archivo `.acs` real |
| The Dot | Bolita roja que cambia de forma constantemente | archivo `.acs` real |
| Kairu | Delfín azul (ediciones asiáticas de Office 97/2000/XP) | archivo `.acs` real |

Los primeros 6 se obtuvieron ya extraídos del proyecto open-source
`clippy.js`. Mother Nature, Office Logo y The Dot arrancaron en v0.2.0 como
"fidelidad reducida" (una sola animación `Idle`) y se re-generaron en v0.3.0
decodificando directamente sus archivos `.acs` originales con un
decodificador propio (`tools/acs_decoder.py`, ver 2.3c). Kairu se agregó
directamente por esta vía: el mismo archivo de preservación en archive.org
que ya usábamos (`binder-97-office972000assistants`) también trae
`DOLPHIN.ACS` (Kairu). Ese mismo archivo trae además `OFFCAT.ACS` — se
decodificó para revisar si era un personaje nuevo, y resultó ser el mismo
**Links** que ya teníamos vía clippy.js (mismo set de animaciones,
`IdleTailWagA-D`, etc.) — no se agrega de nuevo, sería un duplicado.

Todos comparten prácticamente el mismo catálogo de animaciones (Wave,
Greeting, Congratulate, GetTechy, GetWizardy, etc.) porque son la misma
familia de plantilla de Microsoft Agent.

Excluidos a propósito del set completo de `clippy.js`:

- **Bonzi**: personaje de BONZI Software (empresa distinta a Microsoft,
  además asociado a adware histórico) — no es un Office Assistant.
- **Rover**: era el asistente de Windows XP Search Companion, no de Office.
- **Genie, Peedy**: demos de Microsoft Agent (otra tecnología de Microsoft,
  separada de Office Assistant) — nunca aparecieron dentro de Word/Excel/etc.

**Fidelidad reducida** (5 — no se consiguió un archivo `.acs` real para
ninguno pese a buscarlo específicamente; solo un `.zip` de The Spriters
Resource con frames sueltos sin agrupar por animación. Ver
`tools/fetch_extra_assets.py` y 2.3b):

| Personaje | Descripción | Origen |
|---|---|---|
| Scribble | Gato de estilo origami | Office 97 |
| Power Pup | Perro con disfraz de superhéroe | Office 97 |
| Will | Caricatura de William Shakespeare | Office 97 |
| Saeko Sensei | Maestra de escuela | Ediciones japonesas |
| Monkey King (Mono Rey) | Sun Wukong, de "Viaje al Oeste" | Ediciones chinas |

Estos 5 tienen `Idle` (un loop calmo con el bloque de frames consecutivos
de mayor área promedio, para que el estado por defecto se vea razonablemente
reconocible) más varias animaciones cortas `Motion01`, `Motion02`, etc.
(~1.9s cada una, bloques consecutivos del resto de la secuencia original) en
vez de las decenas nombradas del resto del roster. NO tienen entrada en
`app/signature_actions.py` a propósito: "Decime un consejo"/"Animar" eligen
una `MotionNN` al azar (mismo resguardo que usa cualquier personaje sin
entrada explícita), lo que da variedad real entre gestos cortos en vez de
repetir siempre lo mismo. Ver 2.3b para el detalle completo de cómo se
segmentan y qué limitaciones tiene ese enfoque (no es perfecto: sin el
`.acs` original no hay forma de saber con certeza qué frames formaban qué
gesto real).

**Investigados pero NO incorporados** (fuentes reales encontradas y
documentadas, para una futura versión):

- **Hoverbot**: personaje real (Office 97). Se buscó en dos sesiones
  distintas sin encontrar ninguna fuente con datos de animación multi-frame
  utilizables — el único candidato en The Spriters Resource resultó mal
  etiquetado (apuntaba en realidad a "The Dot" de Office XP), el de
  archive.org (`MSOfficeMacAssistants.zip`) es solo una captura estática de
  la ventana de selección, y el archivo `binder-97-office972000assistants`
  (que sí trae `.acs` reales de Dot/Mother Nature/Office Logo/Kairu/Links)
  no incluye uno para Hoverbot.
- **Bosgrove, Max** (exclusivos de Office para Mac): solo existen capturas
  estáticas de la ventana "Gallery" (una sola pose); su formato nativo de
  Mac (resource fork clásico, distinto de `.acs`) tampoco está soportado por
  `tools/acs_decoder.py` — decodificarlo sería un proyecto aparte.
- **Earl** (gato azul, exclusivo de Mac), **Manma-chan** (promoción japonesa
  puntual, no un asistente estándar): personajes reales con sprite sheet o
  zip de frames disponible en The Spriters Resource, pero no se
  incorporaron por alcance — quedan para una futura versión siguiendo el
  mismo proceso de 2.3b si hace falta.
- **"Da Vinci"**: **no existe** ningún Office Assistant ni personaje de
  Microsoft Agent con ese nombre o parecido — se investigó a fondo
  (Wikipedia, wikis de Microsoft Agent, documentación de Encarta/Bookshelf/
  Creative Writer) sin encontrar rastro. Lo más probable es que la
  confusión sea con **Genius** (la caricatura de Einstein) o con **Will**
  (la caricatura de Shakespeare) — ambos son "genios históricos"
  caricaturizados, la misma idea que "Da Vinci".
- **"Natura"**: el usuario la pidió como "Natura"; el personaje real en
  inglés es **Mother Nature** (Office 97). No se pudo confirmar de forma
  independiente si la localización al español usó literalmente el nombre
  "Natura", pero el personaje en sí es 100% real y ya está incluido.

### 2.2 Ventana flotante

- Sin bordes, fondo transparente (color-key `#ff00ff`), siempre-encima
  configurable, arrastrable con el botón izquierdo del mouse.
- Posición y personaje activo persisten entre sesiones
  (`%APPDATA%/OldWindowsHelpers/config.json`).
- Animación: idle en loop (elige al azar entre las animaciones cuyo nombre
  contiene "Idle"), y animaciones "one-shot" (el resto) al pedir un consejo.
- **Tamaño consistente**: todo personaje se escala a `DISPLAY_HEIGHT = 160px`
  de alto (`app/animation.py`), preservando su aspect ratio original. Sin
  esto, cambiar de personaje entre uno de 93px de alto (Clippy) y uno de
  285px (Scribble, sin escalar) pegaba un salto de tamaño incómodo.
- **DPI aware** (`app/dpi.py`, se llama antes de crear cualquier ventana):
  sin esto, en pantallas con escalado de Windows (125%/150%/200%, común en
  laptops modernas) el sistema operativo escala la ventana él mismo
  estirando el bitmap final — se ve borroso y el tamaño real en pantalla ya
  no coincide con `DISPLAY_HEIGHT`. Otra causa del reclamo de "tamaño
  incómodo", además de la falta de normalización entre personajes.
- **Sin fleco/halo mágenta** (bug corregido en v0.3.0): la transparencia por
  color-key de Tkinter NO hace blending real — un píxel semitransparente del
  PNG original (cualquier borde antialiased) se mezcla con el fondo mágenta
  del widget ANTES de aplicarse el color-key, dejando un halo rosado visible
  alrededor del personaje. Se soluciona "endureciendo" el canal alfa
  (`_harden_alpha` en `app/animation.py`: por debajo de `ALPHA_HARDEN_THRESHOLD`
  el píxel pasa a 100% transparente, por encima a 100% opaco) — se aplica
  DESPUÉS de escalar el frame al tamaño de despliegue, porque el propio
  resize reintroduce semitransparencia en los bordes.

### 2.3 Formato de personaje (`assets/agents/<Nombre>/`)

```
agent.json:
{
  "name": "...",
  "sprite": "map.png",
  "frame_width": int,
  "frame_height": int,
  "animations": {
    "<NombreAnimacion>": [
      {"duration": <ms>, "images": [[x, y], ...]},
      ...
    ]
  }
}
map.png: sprite sheet con todas las poses, recortadas de a (frame_width, frame_height)
```

**Simplificación deliberada** respecto del formato original de Microsoft
Agent: se descartan `sounds` y `exitBranch`/`branching` (la máquina de
estados original). El reproductor (`app/animation.py`) toca cada animación en
secuencia lineal. Esto significa que no hay audio ni transiciones
"inteligentes" entre poses — se documenta como limitación conocida de v0.1.0,
no como omisión accidental.

### 2.3b Cómo se generaron los 5 de fidelidad reducida

Para estos 5 no se consiguió un archivo `.acs` real (ver 2.3c) pese a
buscarlo — solo un `.zip` de The Spriters Resource con un PNG individual ya
recortado por frame, sin agrupar por animación. `tools/fetch_extra_assets.py`
los convierte al esquema de 2.3: cada PNG del zip es un frame a su propio
tamaño (no hay un sheet compartido), así que se recomponen en un sprite
sheet nuevo, centrando cada frame horizontalmente y apoyándolo abajo dentro
de una celda de tamaño fijo (el máximo del personaje) — esto pierde la
posición relativa exacta que tenían los frames en la animación original,
pero es necesario para reusar un motor que asume `frame_width`/`frame_height`
constantes.

Antes de armar el sprite sheet se limpian tres tipos de frames que no son
una pose real del personaje (los tres, encontrados verificando visualmente
cada personaje frame por frame, no a ciegas):

- **Sin transparencia real** (`MAX_OPAQUE_FILL_RATIO`): algún ZIP trae
  colado un ícono o miniatura promocional de fondo sólido — en Scribble, un
  ícono de "cara de gato" y una miniatura de un modelo 3D en wireframe,
  ninguno de los dos un frame de animación real. Un frame de personaje
  genuino es una silueta recortada (tiene esquinas transparentes); una
  miniatura rectangular casi no tiene transparencia. Excepción: si el 100%
  de los frames de un personaje da "sin transparencia" (le pasó a Saeko
  Sensei y Monkey King, exportados en modo paleta con fondo mágenta opaco
  en vez de canal alfa), el filtro se omite — no es que todo el personaje
  sea basura, es que esa fuente en particular no usa transparencia real, y
  se convierte el mágenta a transparencia de verdad primero
  (`_magenta_to_real_alpha`, mismo color llave que usa
  `app/character_window.py`).
- **Área atípica** (`OUTLIER_AREA_RATIO`): algún frame mide muchísimo más
  que el resto (Power Pup traía uno de 791x857px, ~220x la mediana) — casi
  seguro un artefacto de la extracción original, no una pose.

**Cómo se arman las animaciones** (rediseñado en v0.5.0 — la primera versión,
en v0.4.0, tenía dos bugs reales reportados por el usuario y confirmados):

- v0.4.0 armaba dos animaciones: `Idle` con los frames de MAYOR área
  elegidos de cualquier punto de la secuencia (no consecutivos), y
  `Transform` con TODOS los frames restantes como un solo disparo gigante.
  Esto se veía "medio raro"/"a media animación" por dos razones reales: (1)
  `Idle` saltaba entre poses sin relación entre sí (elegidas por área, no
  por cercanía temporal), sin la fluidez de una animación real; (2)
  `Transform` reproducía CIENTOS o MILES de frames de una — para Saeko
  Sensei/Monkey King (~1300 frames a 120ms) eran **más de 2 minutos y
  medio** por click de "Animar". Si el usuario cambiaba de personaje o
  hacía cualquier otra cosa antes de que terminara, volvía a encontrar al
  personaje congelado en un frame cualquiera del medio de esa secuencia
  gigante — de ahí el "se ve a media animación".
- v0.5.0 en cambio parte la secuencia (ya filtrada de basura/atípicos, EN
  SU ORDEN ORIGINAL, sin reordenar por área) en bloques CONSECUTIVOS de
  `CHUNK_SIZE` frames (16 ⇒ ~1.9s cada uno a 120ms/frame). Frames vecinos en
  el material original tienen mucha más chance de pertenecer al mismo gesto
  real que frames sueltos elegidos por tamaño, así que cada bloque se ve
  como una animación corta con sentido en vez de un collage — aunque sigue
  siendo una aproximación (algunos bloques todavía mezclan un efecto con
  una pose, ver ejemplos verificados visualmente más abajo). El bloque con
  mayor área de contenido PROMEDIO se renombra `Idle` (el loop por
  defecto); el resto quedan como `Motion01`, `Motion02`, etc. — one-shots
  que "Decime un consejo"/"Animar" eligen al azar (no tienen entrada en
  `app/signature_actions.py` a propósito, así cae al resguardo aleatorio y
  se recupera la variedad de "animaciones random" que memoraba el usuario
  de los personajes de alta fidelidad). Cada personaje termina con entre 8
  (Scribble) y 84 (Monkey King) animaciones cortas, según su cantidad total
  de frames.

Cada personaje se verificó visualmente (recortando frames de muestra sobre
un fondo verde brillante, para detectar tanto problemas de transparencia
como de contenido, y revisando bloques `Motion` completos para confirmar
que ya no duran minutos) antes de darlo por bueno.

### 2.3c Cómo se recuperaron las animaciones completas de Mother Nature,
### Office Logo, The Dot y Kairu (`tools/acs_decoder.py`)

Mother Nature, Office Logo y The Dot arrancaron (v0.2.0) con el mismo
proceso de fidelidad reducida que 2.3b, pero se investigó si se podía hacer
algo mejor: encontrar y decodificar sus archivos `.acs` originales — el
mismo formato binario propietario que usaba Microsoft Agent, y que el
propio `clippy.js` NO sabe leer (sus assets ya vienen pre-extraídos por
otra herramienta, ver más abajo). Kairu se agregó directamente por esta vía
en v0.4.0, al notar que el mismo archivo de preservación en archive.org
(`binder-97-office972000assistants`) también trae su `.acs` (`DOLPHIN.ACS`)
— nunca tuvo una versión de fidelidad reducida. Ese mismo archivo trae
además `OFFCAT.ACS`, que se decodificó para revisar si era un personaje
nuevo: resultó ser **Links** (mismo set de animaciones exacto que el que ya
tenemos vía clippy.js) — se descartó por duplicado.

**Investigación**: no existe una especificación oficial de Microsoft en
circulación, pero sí:

- La "MSAgent Character Data Specification" (Lebeau Software, no oficial
  pero es la referencia de facto), con una sección de compresión que cita
  textualmente a ingenieros de Microsoft describiendo el algoritmo en
  mensajes de newsgroup de 1999-2002.
- El código fuente real de **Double Agent** (Cinnamon Software, GPLv3/LGPLv3
  — https://github.com/rschiang/cinsoft-double-agent), un reproductor de
  Microsoft Agent de código abierto con ~15 años de vida que sabe leer
  estos archivos de verdad. `clippy.js` en sí **no tiene ningún parser**:
  su propio README agradece a Cinnamon Software por Double Agent, "el
  programa que usamos para extraer a Clippy y sus amigos" — es decir,
  nuestros primeros 6 personajes están un nivel más abajo en la misma
  cadena de herramientas que ahora usamos directamente.
- **MSAgentUtils** (tkfoss, Swift, CC0), una reimplementación independiente
  desde cero que llega exactamente a las mismas constantes de bajo nivel
  que Double Agent.

Las tres fuentes coinciden byte a byte en el contenedor del archivo y en el
compresor LZ propietario que usa para los píxeles — esa coincidencia es la
base de la confianza en `tools/acs_decoder.py`.

**Resultado**: los 4 archivos `.acs` reales usados (`DOT.ACS`, `MNATURE.ACS`,
`LOGO.ACS`, `DOLPHIN.ACS`, de
https://archive.org/details/binder-97-office972000assistants, el mismo
archivo de preservación ya citado en `NOTICE`) decodifican al 100%: ~6235
frames en total, 0 corruptos o truncados, y resultaron tener el mismo
canvas (124×93) y prácticamente el mismo catálogo de animaciones (Wave,
Greeting, Congratulate, GetTechy, GetWizardy, GetArtsy, etc.) que Clippy/F1/
Genius/Links/Rocky — son la misma familia de plantilla de Microsoft Agent.
`tools/fetch_acs_assets.py` usa el decoder para generar el mismo esquema de
2.3 (agent.json + map.png) que el resto del roster, así que **no hizo falta
tocar el motor de animación** (`app/animation.py`) para nada.

Limitaciones honestas de `acs_decoder.py` (ninguna afecta a estos 3 archivos,
documentadas para quien lo use con un `.acs` distinto en el futuro):

- Un byte de flag por imagen cuyo significado no se determinó del todo (en
  los 3 archivos probados siempre vale 0, el camino "normal").
- El checksum por imagen/audio: el propio spec dice que su algoritmo nunca
  se determinó — no hace falta para decodificar píxeles.
- No se decodifica audio (siempre WAV sin comprimir) ni la máscara de
  "región" (hit-testing) de cada imagen — no los necesita esta app.
- Se verificó contra el spec v1.3; existe una v1.6 que solo se pudo leer
  resumida por IA, no textual — vale la pena diffear antes de confiar en el
  decoder para un `.acs` con características que v1.3 no cubra bien (ej. el
  bloque TTS, que ninguno de los 3 archivos probados usa).

### 2.4 Menú de clic derecho (ventana y bandeja)

Cambiar personaje ▸ · Decime un consejo · **Animar** · Ayuda de Windows ·
Siempre visible (toggle) · Ocultar/Mostrar · Idioma ▸ (es/en) · Iniciar con
Windows (toggle) · Acerca de · ☕ Cómprame una cerveza · Salir.

"Ayuda de Windows" simula la tecla F1 (`app/windows_help.py`) — el atajo de
ayuda contextual universal de Windows desde la versión 95 hasta hoy — en vez
de intentar abrir un ejecutable de ayuda específico por versión de Windows
(decisión tomada porque no existe un único "centro de ayuda" válido para
Win95 a Win11 por igual).

#### "Animar" vs. "Decime un consejo"

Ambas acciones reproducen una animación one-shot y muestran un globo de
texto, pero con una diferencia de intención:

- **Decime un consejo**: animación one-shot al azar + un tip genérico
  (`locales/<lang>.json` → `tips`), igual para cualquier personaje.
- **Animar**: reproduce el **gesto de firma** del personaje activo — una
  animación elegida a mano por lo característica que es de su personalidad
  (ver tabla abajo y `app/signature_actions.py`) — junto con una frase única
  de ese personaje (`locales/<lang>.json` → `animate.<Nombre>`).

| Personaje | Animación de firma | Por qué |
|---|---|---|
| Clippy | `GetWizardy` | Su transformación en mago es su gesto más icónico/memeable. |
| F1 | `GetTechy` | Encaja con su diseño de robot. |
| Genius | `Congratulate` | Un "¡Eureka!" celebratorio, a tono con el Einstein que representa. |
| Links | `GetArtsy` | El gato haciendo de artista. |
| Merlin | `DoMagic1` | Animación **exclusiva** de Merlin (no la tiene ningún otro personaje): un hechizo de mago de verdad. |
| Rocky | `EmptyTrash` | El perro escarbando en la basura — un chiste apropiado para un personaje canino. |
| Mother Nature | `Alert` | Un "aviso de la naturaleza", a tono con su mensaje ambiental. |
| Office Logo | `Show` | No tiene cara ni gestos propios; su animación de aparición es lo más "de su personalidad" que existe. |
| The Dot | `Explain` | Explica cambiando de forma, coherente con su frase característica. |
| Kairu | `Wave` | Un delfín + una ola, el chiste se arma solo. |

Power Pup, Scribble, Will, Saeko Sensei y Monkey King **no** están en esta
tabla a propósito (ver 2.1/2.3b): en vez de una animación de firma fija,
"Animar" les elige al azar una de sus `MotionNN` cortas — variedad real en
vez de siempre el mismo gesto.

Si se agrega un personaje nuevo sin entrada en `SIGNATURE_ANIMATIONS`, o sin
traducción `animate.<Nombre>`, "Animar" no rompe: cae a una animación
one-shot al azar y a un tip genérico respectivamente (mismo mecanismo de
respaldo que usa "Decime un consejo").

### 2.5 Multi-idioma

`es` (default) / `en`, detectado vía `GetUserDefaultUILanguage` de Windows si
el usuario no eligió uno manualmente. Extensible agregando
`locales/<código>.json` con las mismas claves que `locales/es.json` y
sumando el código a `SUPPORTED_LANGS` en `app/i18n.py`.

### 2.6 Autoarranque

Toggle en el menú que escribe/borra una entrada en
`HKCU\Software\Microsoft\Windows\CurrentVersion\Run` (no requiere permisos de
administrador; solo afecta al usuario actual).

**Falso positivo de antivirus (Kaspersky y similares)**: un `.exe` de
PyInstaller sin firma digital que se auto-registra en el arranque de Windows
dispara heurísticas antivirus con bastante frecuencia — no implica código
malicioso, es un patrón muy conocido en la comunidad de PyInstaller. Se
observó en la práctica: la app puede "creer" (según `config.json`) que el
autoarranque está activado mientras el antivirus ya borró la entrada real
del registro sin avisar. Mitigaciones aplicadas:

- Build: `--noupx` (UPX se usa mucho en malware para evadir firmas) +
  recurso de versión con metadata real (`tools/build_exe.py`).
- Runtime: si `set_start_with_windows()` falla (`OSError`/`PermissionError`),
  `main.py` revierte el checkbox y avisa con un mensaje claro
  (`warning.autostart_blocked_*` en `locales/*.json`) en vez de crashear o
  fallar en silencio.
- Auto-recuperación: al iniciar, si la config dice que el autoarranque debía
  estar activo pero la entrada del registro no está, se reintenta una vez
  (`_resolve_start_with_windows_state` en `main.py`) — por si el antivirus la
  había borrado por su cuenta entre una sesión y la siguiente.
- No hay forma de eliminar el falso positivo del todo sin firma de código
  (pagar un certificado Authenticode, fuera de alcance). Ver README.md
  "Aviso de antivirus" para las instrucciones que le quedan al usuario
  (excepción puntual, reporte de falso positivo, o simplemente no activar
  la opción).

### 2.7 Importación de personajes propios

- `tools/fetch_assets.py`: descarga y convierte los 6 personajes de alta
  fidelidad desde `clippyjs/clippy.js`.
- `tools/fetch_acs_assets.py`: descarga y convierte, con animaciones
  completas, Mother Nature/Office Logo/The Dot/Kairu desde sus `.acs`
  reales (ver 2.3c).
- `tools/fetch_extra_assets.py`: descarga y convierte Scribble/Power Pup/
  Will/Saeko Sensei/Monkey King (fidelidad reducida, no se consiguió su
  `.acs` para ninguno — ver 2.3b).
- `tools/acs_importer.py`: importa un archivo `.acs` **propio** (de tu
  propia instalación/medio de Office) y lo convierte con la misma
  fidelidad que `fetch_acs_assets.py`, usando `tools/acs_decoder.py`.
  Antes era experimental (solo detectaba si el archivo era válido); ya no.

## 3. Fuera de alcance (a propósito)

- Integración real con Microsoft Office (no lee ni interactúa con Word/Excel).
- Audio/sonidos de los personajes.
- Réplica fiel de la máquina de estados/branching original de Microsoft Agent.
- Soporte para sistemas operativos que no sean Windows (usa APIs de Windows
  para transparencia de ventana, idioma y autoarranque).

## 4. Empaquetado y releases

- `tools/build_exe.py` compila con PyInstaller (`--onefile --windowed
  --noupx`, más un recurso de versión con metadata real — ver 2.6 y
  README.md "Aviso de antivirus"), usando `clippy_icon_136771.ico`, y deja
  el `.exe` junto a `main.py`.
- Versionado SemVer en `version.py` (único origen de verdad; `tools/bump_version.py`
  también sincroniza el badge de `README.md`).
- `.github/workflows/build.yml`: build+tests en cada push a `main` (chequeo
  de humo, sin publicar release).
- `.github/workflows/release.yml`: en cada tag `v*.*.*`, compila el `.exe` y
  publica un GitHub Release adjuntándolo.

## 5. Criterios de aceptación

- [x] `python main.py` muestra el personaje flotando y responde al clic
      derecho con el menú completo.
- [x] Cambiar de personaje desde el menú (ventana o bandeja) actualiza la
      animación sin reiniciar la app.
- [x] "Decime un consejo" muestra un globo de texto y una animación one-shot.
- [x] "Animar" reproduce el gesto de firma del personaje activo (tabla en
      2.4) junto con su frase única, y no rompe para personajes sin entrada
      explícita (cae a un one-shot al azar + tip genérico).
- [x] El estado (personaje, idioma, posición, siempre-visible, autoarranque)
      persiste entre reinicios de la app.
- [x] `python tools/build_exe.py` genera `OldWindowsHelpers.exe` junto a
      `main.py`, sin consola, con el ícono correcto.
- [x] `python -m pytest tests/` pasa en verde.
- [x] Push de un tag `vX.Y.Z` dispara un GitHub Release con el `.exe` adjunto.
- [x] Todos los personajes se ven al mismo tamaño en pantalla (`DISPLAY_HEIGHT`)
      y sin fleco/halo mágenta en los bordes, verificado corriendo la app en
      vivo (no alcanza con renderizar offline, ver 2.2).
- [x] Mother Nature, Office Logo, The Dot y Kairu tienen animaciones
      completas y nombradas (no una sola "Idle"), decodificadas de su `.acs`
      real (2.3c).
- [x] Power Pup, Scribble, Will, Saeko Sensei y Monkey King tienen `Idle`
      (loop calmo) más varias `MotionNN` cortas (~2s cada una, no minutos)
      en vez de una única animación gigante — verificado que "Animar" ya no
      deja al personaje "pegado a media animación" y que hay variedad real
      entre distintos clics.
- [x] El roster completo (15 personajes) pasa `test_full_expected_roster_is_present`.
- [x] Si un antivirus bloquea "Iniciar con Windows", la app avisa con un
      mensaje claro en vez de crashear, y reintenta activarlo la próxima vez.
