---
name: comment-code
description: Agrega comentarios explicativos al codigo de OldWindowsHelpers para dejar claro que hace cada parte. Usar cuando el usuario pida "comenta este archivo", "explicame el codigo con comentarios", "no entiendo que hace esta funcion, agregale comentarios", sobre uno o varios archivos del repo.
---

# comment-code

Este proyecto pidió explícitamente un nivel de comentarios más generoso que
el estilo minimalista por defecto: el usuario quiere poder leer el código y
entender qué hace cada parte sin tener que preguntar.

## Alcance

- Si el usuario nombra archivos específicos, trabajar solo sobre esos.
- Si no especifica, preguntar (o inferir del contexto reciente: el último
  archivo tocado, el diff sin commitear, etc.) — no comentar todo el repo de
  una sola pasada sin que lo pidan.

## Qué agregar

1. **Docstring de módulo** (si falta): 1-3 líneas explicando el rol del
   archivo dentro de la app (¿es la ventana flotante? ¿el motor de
   animación? ¿la persistencia de config?).
2. **Por función/método no trivial**: qué hace, qué recibe, qué devuelve.
   Las funciones de una línea y obvias (getters simples, wrappers directos)
   no necesitan comentario aparte del docstring del módulo.
3. **Trucos específicos de la plataforma**: transparencia de ventana por
   color clave (`-transparentcolor`), resolución de rutas con
   `sys._MEIPASS` bajo PyInstaller, autoarranque vía `winreg`, simulación de
   F1 con `keybd_event`, hilo aparte de `pystray` y por qué hace falta
   `root.after(0, ...)` para volver al hilo de Tkinter. Estos son los puntos
   donde un lector nuevo se pierde si no se explican.
4. **Decisiones de diseño no obvias** ya documentadas en `specs/SPEC.md`
   (ej. por qué se ignoran `sounds`/`exitBranch` del formato original) — un
   comentario corto en el lugar del código donde aplica, con referencia a la
   spec si hace falta más detalle.

## Qué NO hacer

- No reescribir ni "mejorar" la lógica — solo agregar comentarios. Si
  encontrás un bug al leer, avisalo aparte, no lo arregles en silencio dentro
  de este pase.
- No comentar lo obvio línea por línea (ruido que dificulta la lectura).
- No dejar comentarios en inglés si el resto del archivo está en español (o
  viceversa) — mantené el idioma consistente dentro de cada archivo.

## Al terminar

Resumir qué archivos se comentaron y qué partes quedaron documentadas, para
que el usuario pueda revisar el diff rápido.
