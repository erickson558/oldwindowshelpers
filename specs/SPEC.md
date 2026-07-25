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

### 2.1 Personajes (v0.1.0)

Incluidos, obtenidos ya extraídos del proyecto open-source `clippy.js`
(ver [`NOTICE`](../NOTICE)):

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

Agregar más personajes en el futuro (ej. Dot, Hoverbot, Mother Nature,
Office Logo, Scribble) es cuestión de conseguir su sprite sheet en el mismo
esquema (ver 2.3) — no requiere cambios de arquitectura.

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

### 2.4 Menú de clic derecho (ventana y bandeja)

Cambiar personaje ▸ · Decime un consejo · Ayuda de Windows · Siempre visible
(toggle) · Ocultar/Mostrar · Idioma ▸ (es/en) · Iniciar con Windows (toggle) ·
Acerca de · ☕ Cómprame una cerveza · Salir.

"Ayuda de Windows" simula la tecla F1 (`app/windows_help.py`) — el atajo de
ayuda contextual universal de Windows desde la versión 95 hasta hoy — en vez
de intentar abrir un ejecutable de ayuda específico por versión de Windows
(decisión tomada porque no existe un único "centro de ayuda" válido para
Win95 a Win11 por igual).

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

- `tools/fetch_assets.py`: descarga y convierte los 6 personajes de v0.1.0
  desde `clippyjs/clippy.js`.
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

## 5. Criterios de aceptación (v0.1.0)

- [ ] `python main.py` muestra el personaje flotando y responde al clic
      derecho con el menú completo.
- [ ] Cambiar de personaje desde el menú (ventana o bandeja) actualiza la
      animación sin reiniciar la app.
- [ ] "Decime un consejo" muestra un globo de texto y una animación one-shot.
- [ ] El estado (personaje, idioma, posición, siempre-visible, autoarranque)
      persiste entre reinicios de la app.
- [ ] `python tools/build_exe.py` genera `OldWindowsHelpers.exe` junto a
      `main.py`, sin consola, con el ícono correcto.
- [ ] `python -m pytest tests/` pasa en verde.
- [ ] Push de un tag `vX.Y.Z` dispara un GitHub Release con el `.exe` adjunto.
