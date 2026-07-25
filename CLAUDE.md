# CLAUDE.md

Instrucciones de proyecto para Claude Code al trabajar en **OldWindowsHelpers**.

## Qué es este proyecto

App de escritorio para Windows (Python + Tkinter + Pillow + pystray) que
muestra a los Ayudantes de Office clásicos (Clippy, Merlín, Links, Rocky,
Genius, F1) como personajes flotantes animados, con menú de clic derecho y
compilación a `.exe` vía PyInstaller. Ver [`README.md`](README.md) para el
detalle funcional y [`specs/SPEC.md`](specs/SPEC.md) para la especificación
técnica completa.

## Spec-Driven Development (SDD)

Este repo mantiene una especificación viva en `specs/SPEC.md`. Regla dura:

- **Antes** de implementar una feature o cambio de comportamiento no trivial,
  leé `specs/SPEC.md` para entender el alcance y las decisiones ya tomadas
  (por qué se hicieron así, qué quedó fuera de alcance a propósito).
- **Después** de implementarlo, actualizá `specs/SPEC.md` (y `CHANGELOG.md`,
  y la versión con `tools/bump_version.py` si corresponde) en el mismo ciclo
  de trabajo — no lo dejes para después. La spec, el changelog y el código
  deben quedar sincronizados en cada commit relevante.
- Si agregás o cambiás un Agent o Skill de Claude Code (`.claude/agents/`,
  `.claude/skills/`), reflejalo también en `specs/SPEC.md` y en este archivo.

## Estilo de comentarios en el código (específico de este proyecto)

A diferencia de un estilo minimalista por defecto, en **este repo el usuario
pidió explícitamente comentarios que expliquen qué hace cada parte del
código** (funciones, bloques no triviales, decisiones de diseño). Al escribir
o tocar código acá:

- Agregá un docstring breve por módulo explicando su rol dentro de la app.
- Comentá bloques de lógica no obvia (por qué, no solo qué), especialmente
  donde haya trucos específicos de Windows/Tkinter (ej. transparencia por
  color clave, autoarranque por registro, simulación de F1).
- Para una pasada dedicada de comentarios sobre un archivo o diff, usá el
  skill `/comment-code` (ver `.claude/skills/comment-code/SKILL.md`) o el
  agent `code-commenter`.

## Agents y Skills disponibles

- **Agents** (`.claude/agents/`):
  - `python-dev`: implementa features siguiendo `specs/SPEC.md`, comenta el
    código según la convención de arriba, actualiza la spec si cambia el
    comportamiento.
  - `release-manager`: orquesta el ciclo de versión → build → tag → release
    (usa el skill `/release`).
  - `code-commenter`: agrega comentarios explicativos a archivos o diffs
    (usa el skill `/comment-code`).
- **Skills** (`.claude/skills/`):
  - `/github-setup`: primer commit + creación del repo público + push inicial.
  - `/release`: sync de specs/changelog, bump de versión, build del `.exe`,
    commit, tag y push (dispara el release automático de GitHub Actions).
  - `/comment-code`: pasa por un archivo/diff agregando comentarios claros.
  - `/bugfix`: análisis → corrección → validación → versionado → commit →
    push para corregir errores sin romper funcionalidad existente.

## Verificación visual en vivo (importante)

Bugs de renderizado de la ventana flotante (transparencia, tamaño, flecos de
color) **no se detectan renderizando offline con PIL** — Tkinter compone la
transparencia por color-key de forma distinta a un `alpha_composite` normal
(ver 2.2 en `specs/SPEC.md`, el bug del "fleco mágenta"). Para verificar un
fix visual hace falta correr la app de verdad y mirarla.

Si necesitás capturar pantalla para esa verificación: **armá tu propio fondo
de control** (una ventana Tkinter sólida, de un color que no se confunda con
ningún personaje) y capturá solo esa región — nunca captures el escritorio
real del usuario a ciegas, puede tener contenido personal (fotos, ventanas
abiertas) que no hace falta ver para verificar un sprite.

## Convenciones del código

- Python 3.11+, sin frameworks pesados: Tkinter + Pillow para la UI/animación,
  `pystray` para la bandeja, `winreg`/`ctypes` (stdlib) para autoarranque e
  idioma — evitar sumar dependencias nuevas sin necesidad real.
- Un solo punto de verdad para la versión: [`version.py`](version.py).
- Los personajes viven en `assets/agents/<Nombre>/{agent.json,map.png}` con el
  esquema descrito en [`app/animation.py`](app/animation.py) — cualquier
  importador nuevo debe producir ese mismo esquema para no tener que tocar
  el motor de animación. `tools/acs_decoder.py` (decodificador propio del
  formato `.acs` de Microsoft Agent) + `tools/acs_decoder.build_agent_assets()`
  ya hacen esa conversión — reusalo antes de escribir un converter nuevo
  desde cero (lo usan tanto `tools/fetch_acs_assets.py` como
  `tools/acs_importer.py`).
- Commits: [Conventional Commits](https://www.conventionalcommits.org/es/)
  (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`) — determinan si el próximo
  bump de versión es minor, patch o major.

## Comandos útiles

```powershell
pip install -r requirements-dev.txt   # deps + herramientas de build/test
python -m pytest tests/ -v            # pruebas
python main.py                        # correr la app desde código fuente
python tools/fetch_assets.py          # (re)descargar los personajes
python tools/build_exe.py             # compilar el .exe
python tools/bump_version.py patch    # subir de versión
```
