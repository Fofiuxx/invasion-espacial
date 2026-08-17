# Invasión Espacial

Arcade estilo Space Invaders hecho con Pygame, compilado a WebAssembly
para poder jugarlo en el navegador sin instalar nada.

**▶ Jugar: https://fofiuxx.github.io/invasion-espacial/**

`← →` mover · `ESPACIO` disparar · `R` reiniciar

---

## Qué hay dentro

```
index.html, web.apk        el juego compilado, listo para servir
browserfs.min.js           dependencia del runtime (ver abajo)
fuente/main.py             el juego original, de escritorio
fuente/web/main.py         la versión adaptada al navegador
```

## Correrlo en el escritorio

```bash
pip install pygame
```

```bash
cd fuente && python main.py
```

## Recompilar la versión web

```bash
pip install pygbag
```

```bash
python -m pygbag --build fuente/web
```

En Windows hay que anteponer `PYTHONUTF8=1`: pygbag lee el código con la
codificación del sistema y los acentos lo rompen.

---

## Qué cambió al pasarlo al navegador

El original y la versión web son el mismo juego, pero correr dentro de una
pestaña impone tres cosas:

**El bucle tiene que ser asíncrono.** El navegador necesita recuperar el
control entre fotograma y fotograma. Sin un `await asyncio.sleep(0)` al final
de cada vuelta, la pestaña se congela y hay que matarla.

**Los fotogramas tienen que ir fijos.** El original corría sin límite: en una
máquina rápida el bucle daba miles de vueltas por segundo y en una lenta
muchas menos, así que la velocidad del juego dependía del hardware. La
versión web fija 60 fps y reescala las velocidades para que se juegue igual
en cualquier equipo.

**El audio no puede sonar solo.** Los navegadores bloquean la reproducción
hasta que la persona interactúa con la página. La música arranca con la
primera tecla, no al cargar.

De paso: el original volvía a leer el archivo de sonido del disco en cada
disparo y en cada impacto. Ahora se cargan una sola vez al arrancar.

## Dos tropiezos que vale la pena documentar

**pygbag no acepta MP3.** Falla con un error poco claro sobre "formato no
soportado". Los tres audios están convertidos a OGG. La conversión además
bajó la música de 11,7 MB a 3,2 MB, que en una página web importa bastante.

**`browserfs.min.js` da 404 en el CDN de pygbag 0.9.3.** Sin ese archivo el
runtime arranca, descarga el intérprete de Python y luego se queda colgado
en "Loading, please wait" para siempre. La copia local en la raíz del
repositorio resuelve el problema — y de paso quita una dependencia externa.

---

## Créditos

Música: **It's Always Too Late to Start Over**, de Chris Zabriskie, tomada
de la biblioteca de audio de YouTube. Licencia Creative Commons Attribution.

El juego nació como proyecto de un curso de Python. El código de escritorio
es el del curso; la adaptación web, el reescalado de velocidades, la pantalla
de inicio y el reinicio son posteriores.
