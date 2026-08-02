import math
import random
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectButton, DirectLabel, DirectSlider
from panda3d.core import (
    WindowProperties,
    AmbientLight,
    DirectionalLight,
    Vec4,
    TextNode,
    TransparencyAttrib,
    LineSegs,
    CardMaker,
)

class Simulador(ShowBase):
    def __init__(self):
        super().__init__()

        # ==========================
        # CONFIGURACIÓN DE LA VENTANA
        # ==========================
        props = WindowProperties()
        props.setTitle("Simulador 3D - Flujo de Agua")
        props.setSize(1400, 800)
        self.win.requestProperties(props)

        self.disableMouse()

        # ==========================
        # CÁMARA
        # ==========================
        self.camera.setPos(0, -22, 0)
        self.camera.lookAt(0, 0, 0)

        # ==========================
        # FONDO
        # ==========================
        self.setBackgroundColor(0.88, 0.91, 0.95, 1)

        # ==========================
        # ILUMINACIÓN
        # ==========================
        ambient = AmbientLight("ambient")
        ambient.setColor(Vec4(0.7, 0.7, 0.7, 1))
        ambient_np = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_np)

        directional = DirectionalLight("directional")
        directional.setColor(Vec4(1, 1, 1, 1))
        directional_np = self.render.attachNewNode(directional)
        directional_np.setHpr(-45, -45, 0)
        self.render.setLight(directional_np)

        # ==========================
        # ESTADO Y VARIABLES (Cálculo Vectorial / Parámetros)
        # ==========================
        self.simulando = True
        self.estado = "Ejecutando"
        self.radio_tuberia = 0.45  # Ancho de la tubería modificable
        self.presion = 1.0         # Presión del agua modificable
        self.velocidad_agua = 3.0

        # ==========================
        # INTERFAZ (UI)
        # ==========================
        self.titulo = DirectLabel(
            text="SIMULADOR 3D DE FLUJO DE AGUA",
            scale=0.07,
            pos=(0, 0, 0.90),
            frameColor=(0, 0, 0, 0),
            text_fg=(0, 0, 0, 1),
            text_align=TextNode.ACenter,
        )

        self.panel = DirectLabel(
            frameColor=(0.18, 0.20, 0.25, 0.95),
            frameSize=(-0.35, 0.35, -0.88, 0.88),
            pos=(-1.30, 0, 0),
            text=""
        )

        self.panelTitulo = DirectLabel(
            parent=self.panel,
            text="PANEL DE CONTROL",
            scale=0.055,
            pos=(0, 0, 0.75),
            frameColor=(0, 0, 0, 0),
            text_fg=(1, 1, 1, 1),
            text_align=TextNode.ACenter,
        )

        self.botonInicio = DirectButton(
            parent=self.panel,
            text="INICIAR",
            scale=0.05,
            frameSize=(-2.2, 2.2, -0.6, 0.6),
            pos=(0, 0, 0.55),
            command=self.iniciar,
        )

        self.botonPausa = DirectButton(
            parent=self.panel,
            text="PAUSAR",
            scale=0.05,
            frameSize=(-2.2, 2.2, -0.6, 0.6),
            pos=(0, 0, 0.38),
            command=self.pausar,
        )

        self.botonReiniciar = DirectButton(
            parent=self.panel,
            text="REINICIAR",
            scale=0.05,
            frameSize=(-2.2, 2.2, -0.6, 0.6),
            pos=(0, 0, 0.21),
            command=self.reiniciar,
        )

        # --- CONTROLES DESLIZANTES (SLIDERS) ---
        # 1. Ancho de Tubería
        self.labelAncho = DirectLabel(
            parent=self.panel,
            text="Ancho Tubería:",
            scale=0.04,
            pos=(0, 0, 0.02),
            frameColor=(0, 0, 0, 0),
            text_fg=(1, 1, 1, 1),
        )
        self.sliderAncho = DirectSlider(
            parent=self.panel,
            range=(0.25, 0.75),
            value=self.radio_tuberia,
            pageSize=0.05,
            scale=0.25,
            pos=(0, 0, -0.08),
            command=self.actualizarAnchoTubería,
        )

        # 2. Presión del Agua
        self.labelPresion = DirectLabel(
            parent=self.panel,
            text="Presión de Agua:",
            scale=0.04,
            pos=(0, 0, -0.22),
            frameColor=(0, 0, 0, 0),
            text_fg=(1, 1, 1, 1),
        )
        self.sliderPresion = DirectSlider(
            parent=self.panel,
            range=(0.2, 3.0),
            value=self.presion,
            pageSize=0.2,
            scale=0.25,
            pos=(0, 0, -0.32),
            command=self.actualizarPresionAgua,
        )

        # Estado visual
        self.estadoTexto = DirectLabel(
            parent=self.panel,
            text="Estado:",
            scale=0.045,
            pos=(0, 0, -0.52),
            frameColor=(0, 0, 0, 0),
            text_fg=(1, 1, 1, 1),
        )

        self.estadoValor = DirectLabel(
            parent=self.panel,
            text=self.estado,
            scale=0.045,
            pos=(0, 0, -0.63),
            frameColor=(0, 0, 0, 0),
            text_fg=(0.2, 1, 0.2, 1),
        )

        # ==========================
        # NODO CONTENEDOR DE TUBERÍAS
        # ==========================
        self.nodo_tuberia = self.render.attachNewNode("NodoTuberias")
        self.dibujar_estructura()

        # ==========================
        # SISTEMA DE PARTÍCULAS (AGUA ABUNDANTE)
        # ==========================
        self.particulas = []
        self.numero_particulas = 1000

        for i in range(self.numero_particulas):
            cm_particula = CardMaker(f"part_{i}")
            cm_particula.setFrame(-0.07, 0.07, -0.07, 0.07)
            esfera = self.render.attachNewNode(cm_particula.generate())
            esfera.setBillboardPointEye()
            esfera.setColor(0.05, 0.50, 1.00, 0.85)

            self.particulas.append({
                "modelo": esfera,
                "progreso": random.uniform(0.0, 17.57),
                "desp_y": random.uniform(-0.35, 0.35),
                "desp_z": random.uniform(-0.35, 0.35)
            })

        # ==========================
        # TAREAS
        # ==========================
        self.taskMgr.add(self.actualizarAgua, "ActualizarAgua")
        self.taskMgr.add(self.buclePrincipal, "BuclePrincipal")

    def actualizarEstado(self):
        self.estadoValor["text"] = self.estado
        if self.simulando:
            self.estadoValor["text_fg"] = (0.2, 1, 0.2, 1)
        else:
            self.estadoValor["text_fg"] = (1, 0.5, 0.2, 1)

    def iniciar(self):
        self.simulando = True
        self.estado = "Ejecutando"
        self.actualizarEstado()

    def pausar(self):
        self.simulando = False
        self.estado = "Pausado"
        self.actualizarEstado()

    def reiniciar(self):
        self.simulando = False
        self.estado = "Reiniciado"
        self.actualizarEstado()

        for p in self.particulas:
            p["progreso"] = random.uniform(0.0, 17.57)

    def actualizarAnchoTubería(self):
        self.radio_tuberia = self.sliderAncho.getValue()
        self.nodo_tuberia.removeNode()
        self.nodo_tuberia = self.render.attachNewNode("NodoTuberias")
        self.dibujar_estructura()

    def actualizarPresionAgua(self):
        self.presion = self.sliderPresion.getValue()

    def dibujar_estructura(self):
        lineas = LineSegs()
        lineas.setThickness(3)
        lineas.setColor(Vec4(0.05, 0.05, 0.08, 1))  # Tubería color negro sólido

        radio = self.radio_tuberia
        pasos = 24

        # 1. Tubería horizontal
        for i in range(pasos):
            a1 = math.radians(i * 360 / pasos)
            a2 = math.radians((i + 1) * 360 / pasos)
            y1 = radio * math.cos(a1)
            z1 = radio * math.sin(a1)
            y2 = radio * math.cos(a2)
            z2 = radio * math.sin(a2)

            lineas.moveTo(-9.0, y1, z1)
            lineas.drawTo(-1.0, y1, z1)

        # 2. Codo Curvo
        for i in range(pasos):
            a1 = math.radians(i * 360 / pasos)
            segmentos_codo = 16
            for j in range(segmentos_codo):
                ang1 = math.radians(j * 90 / segmentos_codo)
                ang2 = math.radians((j + 1) * 90 / segmentos_codo)
                
                oz1 = radio * math.cos(a1)
                ox1 = radio * math.sin(a1)
                
                x1 = -1.0 + (1.0 + oz1) * math.sin(ang1)
                z1 = -1.0 + (1.0 + oz1) * math.cos(ang1)
                x2 = -1.0 + (1.0 + oz1) * math.sin(ang2)
                z2 = -1.0 + (1.0 + oz1) * math.cos(ang2)
                
                lineas.moveTo(x1, ox1, z1)
                lineas.drawTo(x2, ox1, z2)

        # 3. Tubería vertical
        for i in range(pasos):
            a1 = math.radians(i * 360 / pasos)
            y1 = radio * math.cos(a1)
            x1 = radio * math.sin(a1)

            lineas.moveTo(x1, y1, -1.0)
            lineas.drawTo(x1, y1, -9.0)

        node = lineas.create()
        self.nodo_tuberia.attachNewNode(node)

    def actualizarAgua(self, task):
        if not self.simulando:
            return task.cont

        dt = globalClock.getDt()
        velocidad = self.velocidad_agua
        longitud_total = 17.57

        limite_desp = self.radio_tuberia * 0.85

        for p in self.particulas:
            p["progreso"] += velocidad * dt
            if p["progreso"] > longitud_total:
                p["progreso"] = 0.0

            prog = p["progreso"]
            
            # Mantener dispersión acotada al ancho actual de la tubería
            dy = max(-limite_desp, min(limite_desp, p["desp_y"]))
            dz = max(-limite_desp, min(limite_desp, p["desp_z"]))

            if prog <= 8.0:
                # Tramo Horizontal
                x = -9.0 + prog
                y = dy
                z = dz
            elif prog <= 9.57:
                # Tramo Codo Curvo
                arc_prog = prog - 8.0
                angulo = (arc_prog / 1.5708) * (math.pi / 2.0)
                x = -1.0 + (1.0 + dz) * math.sin(angulo)
                z = -1.0 + (1.0 + dz) * math.cos(angulo)
                y = dy
            else:
                # Tramo Vertical
                vert_prog = prog - 9.57
                x = 0.0 + dz
                y = dy
                z = -1.0 - vert_prog

            p["modelo"].setPos(x, y, z)

        return task.cont

    def buclePrincipal(self, task):
        if not self.simulando:
            return task.cont
        # Ecuación de velocidad proporcional a la presión del fluido
        self.velocidad_agua = 3.0 * self.presion
        return task.cont

app = Simulador()
app.run()