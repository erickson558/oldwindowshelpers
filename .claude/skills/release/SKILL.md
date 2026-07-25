---
name: release
description: Sube de version OldWindowsHelpers, sincroniza specs/CHANGELOG, compila el .exe localmente para verificar, y publica un tag/release en GitHub que dispara el workflow de release automatico. Usar cuando el usuario pida "subi la version", "haz un release", "publica los cambios", o "recompila y sube" tras haber implementado algo nuevo.
---

# release

Ciclo completo de release de OldWindowsHelpers: versión, build, tag y
publicación — siempre en este orden, sin saltarse pasos.

## 0. Chequeos previos

```powershell
git status
gh auth status
```

Si hay cambios sin commitear que no sean del trabajo actual, preguntar antes
de seguir. Si el repo remoto no existe todavía, usar el skill `/github-setup`
en su lugar (este skill asume que ya existe `origin` en GitHub).

## 1. Sincronizar documentación viva

- Releer `specs/SPEC.md`: si el trabajo reciente cambió comportamiento
  (nuevo personaje, nueva acción de menú, cambio de esquema de assets,
  nuevo idioma, etc.), actualizarlo ahora, en este paso — no después.
- Completar la sección correspondiente en `CHANGELOG.md` con el detalle real
  de lo agregado/arreglado (no dejar la plantilla vacía que deja
  `bump_version.py`).

## 2. Elegir el tipo de bump (SemVer)

Mirar los commits desde el último tag (`git log $(git describe --tags
--abbrev=0)..HEAD --oneline`) y decidir según Conventional Commits:

- Solo `fix:` / `docs:` / `chore:` → **patch**
- Algún `feat:` → **minor**
- Cambio incompatible (rompe `assets/agents/*`, config, o la CLI de las
  tools) → **major**

```powershell
python tools/bump_version.py <patch|minor|major>
```

Esto actualiza `version.py` y agrega la sección nueva en `CHANGELOG.md`
(completar el detalle si `bump_version.py` dejó la lista vacía).

## 3. Verificar build local antes de publicar

```powershell
python -m pytest tests/ -v
pip install -r requirements-dev.txt
python tools/build_exe.py
```

Confirmar que `OldWindowsHelpers.exe` se generó junto a `main.py`, sin
errores, y que las pruebas pasan. Si algo falla, NO seguir a publicar —
arreglarlo primero.

## 4. Commit, tag y push

```powershell
git add -A
git commit -m "chore(release): vX.Y.Z"
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin main --tags
```

## 5. Verificar el release automático

El push del tag dispara `.github/workflows/release.yml` (compila el `.exe`
en CI y crea el GitHub Release con el ejecutable adjunto). Verificar:

```powershell
gh run watch
gh release view vX.Y.Z
```

## Notas

- La versión debe quedar igual en `version.py`, el tag de git, el título del
  GitHub Release, y el diálogo "Acerca de" de la app (que ya lee
  `version.py` en tiempo real — no hace falta tocarlo a mano).
- El `.exe` compilado localmente en el paso 3 es solo para verificar antes de
  publicar — no se commitea (está en `.gitignore`); el `.exe` "oficial" es el
  que adjunta el GitHub Release generado en CI.
