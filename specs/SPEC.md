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

**Alta fidelidad** (6 — obtenidos ya extraídos del proyecto open-source
`clippy.js`, con animaciones nombradas: Wave, Greeting, Congratulate, etc.
Ver [`NOTICE`](../NOTICE) y `tools/fetch_assets.py`):

| Personaje | Rol original en Office Assistant |
|---|---|
| Clippy (Clippit) | El clip, el más icónico |
| F1 | Robot |
| Genius | Einstein |
| Links | El gato |
| Merlin | El mago |
| Rocky | El perro |

Excluidos a propósito del set completo de `clippy.js`:

- **Bonzi**: personaje de BONZI Software (empresa distinta a Microsoft,
  además asociado a adware histórico) — no es un Office Assistant.
- **Rover**: era el asistente de Windows XP Search Companion, no de Office.
- **Genie, Peedy**: demos de Microsoft Agent (otra tecnología de Microsoft,
  separada de Office Assistant) — nunca aparecieron dentro de Word/Excel/etc.

**Fidelidad reducida** (5 — investigados e incorporados a partir de The
Spriters Resource y archive.org, que NO traen animaciones nombradas como
clippy.js. Ver `tools/fetch_extra_assets.py` y 2.3b más abajo):

| Personaje | Descripción | Origen |
|---|---|---|
| Mother Nature | El globo terráqueo que se transforma en imágenes de la naturaleza | Office 97 |
| Office Logo | El logo animado y giratorio de Office 9x | Office 97/XP |
| The Dot | Bolita roja que cambia de forma constantemente | Office 97 |
| Scribble | Gato de estilo origami | Office 97 |
| Power Pup | Perro con disfraz de superhéroe | Office 97 |

Estos 5 tienen una única animación `"Idle"` que reproduce todos sus frames
en secuencia (no hay forma de saber, a partir de la fuente, qué frames
formaban `Wave`, `Greeting`, etc. por separado — ver 2.3b). Por eso tampoco
tienen entrada en `app/signature_actions.py`: "Animar" cae al resguardo
automático (repite su única animación `Idle`), aunque sí tienen su propia
frase (`animate.<Nombre>` en `locales/*.json`).

**Investigados pero NO incorporados** (fuentes reales encontradas y
documentadas, para una futura versión):

- **Hoverbot**: personaje real (Office 97), pero no se encontró ninguna
  fuente con datos de animación multi-frame utilizables — el único candidato
  en The Spriters Resource resultó mal etiquetado (apuntaba en realidad a
  "The Dot" de Office XP) y el de archive.org es solo una captura estática
  de la ventana de selección, no un sprite sheet.
- **Bosgrove, Max** (exclusivos de Office para Mac): solo existen capturas
  estáticas de la ventana "Gallery" (una sola pose), no hay sprite sheet ni
  frames de animación reales disponibles en ningún lado encontrado.
- **Earl** (gato azul, exclusivo de Mac), **Kairu** (delfín, ediciones
  asiáticas de Windows), **Will** (caricatura de Shakespeare, Office 97),
  **Saeko Sensei**, **Mono Rey (Sun Wukong)**, **Manma-chan** (ediciones
  regionales japonesa/china): personajes reales con sprite sheet o zip de
  frames disponible en The Spriters Resource, pero no se incorporaron en
  esta vuelta por alcance — quedan para una futura versión siguiendo el
  mismo proceso de 2.3b.
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

### 2.3b Cómo se generaron los 5 personajes de fidelidad reducida

A diferencia de `clippy.js` (que trae `agent.js` con animaciones ya
nombradas), The Spriters Resource entrega el arte de dos formas distintas,
ninguna con metadata de animación — `tools/fetch_extra_assets.py` convierte
ambas al mismo esquema de 2.3:

- **Sprite sheet en grilla ya armado** (Mother Nature, Office Logo): se
  detectó el tamaño de celda (124×93, el mismo que usan Clippy/F1/Genius/
  Links/Rocky) analizando la imagen — autocorrelación de columnas para el
  ancho, división exacta del alto por la cantidad de filas visibles
  (930/93=10 y 1674/93=18, ambas exactas). Las celdas completamente vacías
  (solo el color de fondo) se descartan.
- **ZIP de frames individuales ya recortados** (The Dot, Scribble, Power
  Pup): cada PNG del zip es un frame ya extraído a su propio tamaño (no hay
  un sheet compartido). Se recomponen en un sprite sheet nuevo, centrando
  cada frame horizontalmente y apoyándolo abajo dentro de una celda de
  tamaño fijo (el máximo del personaje) — esto pierde la posición relativa
  exacta que tenían los frames en la animación original, pero es necesario
  para reusar un motor que asume `frame_width`/`frame_height` constantes.
  Se descartan frames cuya área supere 15x la mediana del personaje (algún
  ZIP trae, mezclado, algún archivo que no es un frame real — ej. Power Pup
  traía una captura de 791x857px, ~220x el resto, casi seguro un artefacto
  de la extracción original).

En ambos casos se generó una única animación `"Idle"` con todos los frames
en el orden en que vinieron (numérico para los ZIP, fila-por-fila para las
grillas) — no hay forma de recuperar, sin la metadata original, cuáles
frames formaban `Wave`/`Greeting`/etc. por separado. **Cada uno de los 5 se
verificó visualmente** (recortando frames de muestra y mirándolos) antes de
darlo por bueno; ver el historial de esta sesión si hace falta repetir el
proceso para un personaje nuevo.

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

### 2.7 Importación de personajes propios

- `tools/fetch_assets.py`: descarga y convierte los 6 personajes de alta
  fidelidad desde `clippyjs/clippy.js`.
- `tools/fetch_extra_assets.py`: descarga y convierte los 5 personajes de
  fidelidad reducida desde The Spriters Resource (ver 2.3b).
- `tools/acs_importer.py`: **experimental**. Detecta si un archivo `.acs`
  parece válido, pero no decodifica su sprite sheet/animaciones (formato
  binario propietario mal documentado). Ver docstring del archivo para el
  punto de extensión si en el futuro se implementa un parser real.

## 3. Fuera de alcance (a propósito)

- Integración real con Microsoft Office (no lee ni interactúa con Word/Excel).
- Audio/sonidos de los personajes.
- Réplica fiel de la máquina de estados/branching original de Microsoft Agent.
- Soporte para sistemas operativos que no sean Windows (usa APIs de Windows
  para transparencia de ventana, idioma y autoarranque).

## 4. Empaquetado y releases

- `tools/build_exe.py` compila con PyInstaller (`--onefile --windowed`),
  usando `clippy_icon_136771.ico`, y deja el `.exe` junto a `main.py`.
- Versionado SemVer en `version.py` (único origen de verdad).
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
