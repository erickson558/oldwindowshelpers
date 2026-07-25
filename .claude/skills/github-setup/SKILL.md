---
name: github-setup
description: Publica por primera vez el repositorio OldWindowsHelpers en GitHub (repo público, primer commit, push a main) usando la cuenta erickson558 ya autenticada en gh CLI. Usar cuando el usuario pida "subir el proyecto a GitHub", "crear el repo", o "hacer el primer commit" y todavía no exista el repositorio remoto.
---

# github-setup

Publica este proyecto en GitHub por primera vez, de punta a punta, explicando
cada comando (el usuario quiere aprender el proceso, no solo que se ejecute).

## Antes de correr nada

1. `git status` (si ya existe `.git/`) — si hay cambios sin revisar que no
   parecen míos de esta sesión, mostralos y preguntar antes de seguir.
2. `gh auth status` — debe mostrar la cuenta `erickson558` activa con scopes
   `repo` y `workflow`. Si no está autenticada o es otra cuenta activa, avisar
   y detenerse (no cambiar la cuenta activa sin confirmación explícita).

## Pasos (explicar brevemente qué hace cada uno al ejecutarlo)

1. **Inicializar git** (si `.git/` no existe todavía):
   ```powershell
   git init
   git branch -M main
   ```
2. **Revisar qué se va a subir** antes de un `git add` amplio:
   ```powershell
   git status
   ```
   Prestar atención a archivos que no deberían subirse (credenciales, `.env`,
   builds) — deben estar en `.gitignore` (ya incluye `build/`, `dist/`,
   `*.exe`, `__pycache__/`, etc.).
3. **Agregar y commitear** con un mensaje profesional basado en lo
   efectivamente implementado (no genérico tipo "first commit"):
   ```powershell
   git add -A
   git commit -m "feat: initial release of OldWindowsHelpers v0.1.0

   Floating desktop Office Assistant revival (Clippy, F1, Genius, Links,
   Merlin, Rocky) for Windows, with right-click character switching,
   system tray, multi-language support, PyInstaller packaging and
   automated GitHub release workflow."
   ```
4. **Crear el repositorio público en GitHub** con la cuenta ya autenticada:
   ```powershell
   gh repo create oldwindowshelpers --public --source=. --remote=origin --description "Ayudantes de Office clasicos (Clippy y compania) como personajes flotantes en el escritorio de Windows"
   ```
5. **Subir a main**:
   ```powershell
   git push -u origin main
   ```
6. **Primer tag/release** (opcional acá; normalmente lo hace el skill
   `/release`):
   ```powershell
   git tag -a v0.1.0 -m "v0.1.0"
   git push origin --tags
   ```
7. Verificar que quedó todo publicado:
   ```powershell
   gh repo view erickson558/oldwindowshelpers --web=false
   ```

## Convención de commits sugerida para el futuro

`feat:` (funcionalidad nueva → bump minor), `fix:` (arreglo → bump patch),
`docs:`, `chore:`, `refactor:`, `test:` — ver
[Conventional Commits](https://www.conventionalcommits.org/es/). El tipo del
commit más significativo desde el último tag determina qué bump de versión
corresponde (ver skill `/release`).

## Al terminar

Resumir para el usuario: URL del repo creado, rama por defecto (`main`), y
recordar que los próximos cambios se publican con el skill `/release` (no
repitiendo este flujo de "primera vez").
