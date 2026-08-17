"""
Invasión Espacial — versión para navegador.

Es el mismo juego que ../main.py, adaptado para correr con pygbag, que lo
compila a WebAssembly. Tres cambios respecto al original:

1. El bucle es asíncrono. El navegador necesita recuperar el control entre
   fotograma y fotograma; sin el `await` la pestaña se congela.

2. Fotogramas fijos a 60. El original corría sin límite, así que la
   velocidad dependía de lo rápida que fuera la máquina. Las velocidades
   están reescaladas para que a 60 fps se juegue como estaba pensado.

3. Los sonidos se cargan una vez al arrancar. El original volvía a leer el
   archivo del disco en cada disparo y en cada impacto.

Además se añadió pantalla de inicio y reinicio con R: en una demo web el
visitante llega sin saber qué teclas usar, y sin reinicio la partida
termina en un callejón.
"""

import asyncio
import math
import random

import pygame
from pygame import mixer

pygame.init()

ANCHO, ALTO = 800, 600
FPS = 60

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Invasión Espacial")
reloj = pygame.time.Clock()

icono = pygame.image.load("ovni_32px.png")
pygame.display.set_icon(icono)
fondo = pygame.image.load("Fondo.jpg")

# ── Sonido ────────────────────────────────────────────────────────────
# Los navegadores no dejan sonar nada hasta que la persona interactúa,
# así que la música arranca con la primera tecla, no al cargar.
mixer.music.load("MusicaFondo.ogg")
mixer.music.set_volume(0.3)
sonido_disparo = mixer.Sound("disparo.ogg")
sonido_golpe = mixer.Sound("Golpe.ogg")
musica_sonando = False

# ── Velocidades, ya escaladas a 60 fps ────────────────────────────────
VEL_JUGADOR = 6
VEL_BALA = 9
VEL_ENEMIGO_X = 2.0
BAJADA_ENEMIGO = 26
CANTIDAD_ENEMIGOS = 8
LIMITE_INFERIOR = 460          # si un enemigo pasa de aquí, se acabó

img_jugador = pygame.image.load("spaceship.png")
img_enemigo = pygame.image.load("enemigo.png")
img_bala = pygame.image.load("bala.png")

fuente = pygame.font.Font("freesansbold.ttf", 32)
fuente_grande = pygame.font.Font("freesansbold.ttf", 44)
fuente_chica = pygame.font.Font("freesansbold.ttf", 18)

BLANCO = (255, 255, 255)
CELESTE = (94, 234, 212)


def texto_centrado(texto, fuente_usada, y, color=BLANCO):
    render = fuente_usada.render(texto, True, color)
    pantalla.blit(render, (ANCHO // 2 - render.get_width() // 2, y))


class Partida:
    """Todo el estado de una partida, para poder reiniciar creando otra."""

    def __init__(self):
        self.jugador_x = ANCHO // 2 - 32
        self.jugador_y = 500
        self.jugador_dx = 0
        self.puntaje = 0
        self.terminada = False
        self.balas = []
        self.enemigos = [self._nuevo_enemigo() for _ in range(CANTIDAD_ENEMIGOS)]

    def _nuevo_enemigo(self):
        return {
            "x": random.randint(0, ANCHO - 64),
            "y": random.randint(20, 160),
            "dx": random.choice([-1, 1]) * VEL_ENEMIGO_X,
        }

    def disparar(self):
        if self.terminada:
            return
        sonido_disparo.play()
        self.balas.append({"x": self.jugador_x, "y": self.jugador_y})

    def actualizar(self):
        if self.terminada:
            return

        # Jugador, sin salirse de la pantalla
        self.jugador_x = max(0, min(ANCHO - 64, self.jugador_x + self.jugador_dx))

        # Balas
        for bala in self.balas[:]:
            bala["y"] -= VEL_BALA
            if bala["y"] < -32:
                self.balas.remove(bala)

        # Enemigos
        for enemigo in self.enemigos:
            enemigo["x"] += enemigo["dx"]
            if enemigo["x"] <= 0 or enemigo["x"] >= ANCHO - 64:
                enemigo["dx"] = -enemigo["dx"]
                enemigo["y"] += BAJADA_ENEMIGO

            if enemigo["y"] > LIMITE_INFERIOR:
                self.terminada = True
                return

            for bala in self.balas[:]:
                if self._impacto(enemigo, bala):
                    sonido_golpe.play()
                    self.balas.remove(bala)
                    self.puntaje += 1
                    nuevo = self._nuevo_enemigo()
                    enemigo.update(nuevo)
                    break

    @staticmethod
    def _impacto(enemigo, bala):
        # Distancia euclídea entre los centros, como en el original.
        dx = enemigo["x"] - bala["x"]
        dy = enemigo["y"] - bala["y"]
        return math.sqrt(dx * dx + dy * dy) < 32

    def dibujar(self):
        pantalla.blit(fondo, (0, 0))
        for bala in self.balas:
            pantalla.blit(img_bala, (bala["x"] + 16, bala["y"] + 10))
        for enemigo in self.enemigos:
            pantalla.blit(img_enemigo, (enemigo["x"], enemigo["y"]))
        pantalla.blit(img_jugador, (self.jugador_x, self.jugador_y))
        pantalla.blit(fuente.render(f"Puntaje: {self.puntaje}", True, BLANCO), (10, 10))

        if self.terminada:
            velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            velo.fill((0, 0, 0, 170))
            pantalla.blit(velo, (0, 0))
            texto_centrado("JUEGO TERMINADO", fuente_grande, 230)
            texto_centrado(f"Puntaje final: {self.puntaje}", fuente, 300)
            texto_centrado("Pulsá R para jugar otra vez", fuente_chica, 360, CELESTE)


def dibujar_inicio():
    pantalla.blit(fondo, (0, 0))
    velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    velo.fill((0, 0, 0, 150))
    pantalla.blit(velo, (0, 0))
    texto_centrado("INVASIÓN ESPACIAL", fuente_grande, 200)
    texto_centrado("← →  mover", fuente_chica, 290)
    texto_centrado("ESPACIO  disparar", fuente_chica, 320)
    texto_centrado("Pulsá cualquier tecla para empezar", fuente, 390, CELESTE)


async def main():
    global musica_sonando

    partida = Partida()
    empezado = False

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                return

            if evento.type == pygame.KEYDOWN:
                # La música solo puede arrancar tras una interacción.
                if not musica_sonando:
                    mixer.music.play(-1)
                    musica_sonando = True

                if not empezado:
                    empezado = True
                elif partida.terminada:
                    if evento.key == pygame.K_r:
                        partida = Partida()
                else:
                    if evento.key == pygame.K_LEFT:
                        partida.jugador_dx = -VEL_JUGADOR
                    elif evento.key == pygame.K_RIGHT:
                        partida.jugador_dx = VEL_JUGADOR
                    elif evento.key == pygame.K_SPACE:
                        partida.disparar()

            if evento.type == pygame.KEYUP and evento.key in (pygame.K_LEFT, pygame.K_RIGHT):
                partida.jugador_dx = 0

        if empezado:
            partida.actualizar()
            partida.dibujar()
        else:
            dibujar_inicio()

        pygame.display.update()
        reloj.tick(FPS)

        # Devolverle el control al navegador. Sin esto, la pestaña se cuelga.
        await asyncio.sleep(0)


asyncio.run(main())
