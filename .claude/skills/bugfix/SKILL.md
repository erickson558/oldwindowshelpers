---
name: bugfix
description: Corrige errores reales de OldWindowsHelpers sin romper funcionalidad existente, siguiendo un proceso estricto de analisis -> correccion -> validacion -> versionado -> commit -> push. Usar cuando el usuario reporte un bug, algo "roto", o pida explicitamente corregir errores manteniendo el resto de la app intacta.
---

# bugfix

Proceso de 6 fases para corregir errores en un proyecto ya funcional, sin
romper nada. No te saltees fases ni "arregles a ciegas" — primero entender la
causa raíz, después tocar código.

## Reglas críticas

- **No romper funcionalidades existentes**. El sistema ya funciona: no se
  elimina ninguna feature, el comportamiento actual se mantiene intacto
  salvo el bug puntual que se corrige.
- **No arreglar a ciegas**: primero analizar y reproducir el problema,
  identificar la causa raíz, recién después corregir. Si algo se "arregla"
  sin entender por qué pasaba, es sospechoso de tapar el síntoma en vez de
  la causa.
- **Versión consistente**: `Vx.x.x`, sincronizada en `version.py`, el badge
  de `README.md`, el tag de git y el GitHub Release (ver `tools/bump_version.py`).
  Normalmente un bugfix sube el **patch**; si además agrega capacidad nueva
  (ej. una animación que antes no existía), es **minor**.

## Fase 1 — Análisis (obligatoria antes de tocar código)

1. Reproducí el problema si es posible (correr la app, un test, revisar
   logs/config). Para bugs visuales de la ventana flotante, no alcanza con
   mirar los sprites offline con PIL — hay que probar en vivo (Tkinter +
   Windows tienen su propia forma de componer transparencia que un render
   offline no replica). Si necesitás capturar pantalla para verificar un fix
   visual, armá tu propio fondo de control (una ventana sólida propia) en vez
   de capturar el escritorio real del usuario — puede tener contenido
   personal.
2. Identificá: causa raíz, impacto, riesgo de la corrección.
3. Recién ahí pasá a la Fase 2.

## Fase 2 — Corrección

- Corregí la causa raíz, no el síntoma.
- Mejorá manejo de errores/validaciones si el bug lo amerita (ej. una
  excepción no capturada que puede crashear la UI).
- Código limpio y comentado (ver la convención de este repo en `CLAUDE.md`).

## Fase 3 — Validación

```powershell
python -m pytest tests/ -v
```

Si el bug era visual o de comportamiento en vivo, volvé a probarlo en vivo
(no alcanza con que pasen los tests unitarios) antes de dar por corregido.

## Fase 4 — Versionado

```powershell
python tools/bump_version.py patch   # o minor, si agregaste capacidad nueva
```

Completá el detalle en `CHANGELOG.md` bajo la versión nueva.

## Fase 5 — Commit

Mensaje tipo Conventional Commits, con la versión entre paréntesis, ej.:

```
fix: remove magenta fringe and normalize character size (v0.3.0)
```

## Fase 6 — Push

```powershell
git add -A
git commit -m "..."
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin main
git push origin vX.Y.Z
```

El push del tag dispara `.github/workflows/release.yml` (recompila y publica
el Release con el `.exe` adjunto).

## Entregable al usuario

Respondé en este orden: (1) análisis de errores encontrados — causa raíz e
impacto, (2) qué se corrigió y cómo, (3) versión nueva y por qué ese tipo de
bump, (4) comandos corridos, (5) confirmación de que el release quedó
publicado.
