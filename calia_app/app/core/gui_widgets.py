# -*- coding: utf-8 -*-
# // -- Peter Luebke Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.

import random
import math
import numpy as np
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import (
    Color, Ellipse, Line, Rectangle, PushMatrix, PopMatrix, Rotate,
    RenderContext
)
# Korrekter Import, wie von dir schon umgesetzt
from kivy.graphics.shader import Shader

from kivy.clock import Clock
from kivy.properties import ListProperty, NumericProperty, StringProperty

# ==============================================================================
# 1. DER SHADER-HINTERGRUND (Mit Tippfehler-Korrektur)
# ==============================================================================

FUTURISTIC_GRID_SHADER = """
#ifdef GL_ES
precision highp float;
#endif
uniform vec2 u_resolution;
uniform float u_time;
uniform vec4 u_color;
float grid(vec2 pos, float size, float pulse) {
    float line = pow(1.0 - abs(fract(pos.x * size) * 2.0 - 1.0), 20.0);
    line += pow(1.0 - abs(fract(pos.y * size) * 2.0 - 1.0), 20.0);
    line = clamp(line * (0.5 + pulse * 0.5), 0.0, 1.0);
    return line;
}
void main(void) {
    vec2 pos = gl_FragCoord.xy / u_resolution.xy;
    pos.x *= u_resolution.x / u_resolution.y; 
    float t = u_time * 0.05; 
    vec2 grid_pos_1 = vec2(pos.x + t, pos.y - t);
    vec2 grid_pos_2 = vec2(pos.x - t * 0.7, pos.y + t * 0.7);
    float pulse = (sin(u_time) * 0.5 + 0.5);
    float grid_1 = grid(grid_pos_1, 10.0, pulse);
    float grid_2 = grid(grid_pos_2, 5.0, pulse * 0.5);
    float final_grid = grid_1 * 0.5 + grid_2 * 0.3;
    vec3 color = mix(vec3(0.01, 0.02, 0.05), u_color.rgb, final_grid);
    float vignette = 1.0 - smoothstep(0.8, 1.2, length(pos - vec2(pos.x, 0.5)));
    color *= vignette * 1.5;
    gl_FragColor = vec4(color, 1.0);
}
"""

class ShaderBackground(Widget):
    """
    Korrigierte ShaderBackground-Klasse.
    """
    nexus_color = ListProperty([0.1, 0.7, 1, 1])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas = RenderContext()
        s = self.canvas.shader
        s.fs = FUTURISTIC_GRID_SHADER
        with self.canvas:
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_shader, nexus_color=self._update_shader)
        Clock.schedule_interval(self._update_time, 1/60.)

    def _update_shader(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos
        self.canvas['u_resolution'] = list(self.size)
        self.canvas['u_color'] = list(self.nexus_color)

    def _update_time(self, dt):
        # --- KORREKTUR HIER ---
        # von 'get_boattime' zu 'get_boottime'
        self.canvas['u_time'] = Clock.get_boottime()
        # --- ENDE KORREKTUR ---


# ==============================================================================
# 2. DIE NEUE "EQUALIZER"-WELLE (Unverändert)
# ==============================================================================

class EqualizerWaveform(Widget):
    """
    Eine professionelle 'Equalizer-Säulen'-Wellenform.
    Sie hat 4 Modi: idle, speaking, thinking, listening.
    """
    mode = StringProperty('idle')
    amplitude = NumericProperty(0) 
    nexus_color = ListProperty([0.1, 0.7, 1, 1]) 

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.num_bars = 25 
        self.bar_elements = [] 
        self.time = 0.0
        self.target_heights = np.zeros(self.num_bars)
        self.current_heights = np.zeros(self.num_bars)
        self.color_cyan = np.array((0.2, 0.8, 1.0, 0.9))
        self.color_magenta = np.array((0.8, 0.2, 1.0, 0.9))
        self.bind(size=self._init_bars)
        Clock.schedule_interval(self._update_wave, 1/60.)

    def _init_bars(self, *args):
        """Erstellt die Grafik-Instruktionen für die Säulen."""
        self.canvas.clear()
        self.bar_elements = [] 
        with self.canvas:
            for i in range(self.num_bars):
                color_instr = Color(1,1,1,1) 
                rect_instr = Rectangle(pos=(0, 0), size=(1, 1))
                self.bar_elements.append((color_instr, rect_instr))

    def _update_wave(self, dt):
        self.time += dt
        
        # 1. Ziel-Höhen berechnen (je nach Modus)
        if self.mode == 'listening':
            for i in range(self.num_bars):
                x_norm = i / self.num_bars
                wave = (math.sin(x_norm * 8.0 - self.time * 10.0) * 0.5 + 0.5)
                self.target_heights[i] = self.amplitude * wave * 1.5 + 0.02
        
        elif self.mode == 'speaking':
            for i in range(self.num_bars):
                x_norm = i / self.num_bars
                wave = (math.sin(x_norm * 5.0 - self.time * 5.0) * 0.5 + 0.5)
                wave_2 = (math.sin(x_norm * 2.0 + self.time * 3.0) * 0.5 + 0.5)
                self.target_heights[i] = (wave * 0.6 + wave_2 * 0.4) * 0.7 + 0.02

        elif self.mode == 'thinking':
            for i in range(self.num_bars):
                self.target_heights[i] = random.uniform(0.02, 0.4)
        
        else: # 'idle'
            for i in range(self.num_bars):
                x_norm = i / self.num_bars
                wave = (math.sin(x_norm * 3.0 + self.time * 1.0) * 0.5 + 0.5)
                self.target_heights[i] = wave * 0.15 + 0.02

        # 2. Aktuelle Höhen sanft an Ziel-Höhen angleichen (Lerp)
        self.current_heights += (self.target_heights - self.current_heights) * (dt * 15.0)

        # 3. Grafik-Instruktionen aktualisieren
        bar_width = (self.width / self.num_bars) * 0.8 

        for i, (color_instr, rect_instr) in enumerate(self.bar_elements):
            x_norm = i / self.num_bars
            bar_height = self.current_heights[i] * self.height
            bar_height = max(2.0, bar_height)
            bar_x = self.x + (x_norm * self.width) + (bar_width * 0.1)
            
            rect_instr.pos = (bar_x, self.center_y - bar_height / 2) # Zentriert Y
            rect_instr.size = (bar_width, bar_height)
            
            color = self.color_cyan * (1.0 - x_norm) + self.color_magenta * x_norm
            final_color = color * np.array(self.nexus_color)
            final_color[3] = 0.9 
            
            color_instr.rgba = final_color.tolist()

# ==============================================================================
# 3. NEXUS, PANEL, LABEL (Unverändert)
# ==============================================================================

class NexusCore(Widget):
    """
    ANGEPASSTE NexusCore-Klasse.
    Das "C.A.L.I.A."-Logo wurde aus dieser Klasse ENTFERNT.
    """
    nexus_color = ListProperty([0.1, 0.7, 1, 1])
    nexus_rotation_angle = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw)
        Clock.schedule_interval(self._update_rotation, 1/60.)

    def _update_rotation(self, dt):
        if self.nexus_color == [0.7, 0, 1, 1]: 
            self.nexus_rotation_angle += 120 * dt 
        else:
            self.nexus_rotation_angle += 30 * dt 

    def on_nexus_color(self, *args):
        self._redraw()

    def _redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(*self.nexus_color[:3], 0.4) 
            Rectangle(source='assets/images/glow.png', pos=(self.center_x - self.width * 0.45, self.center_y - self.height * 0.45), size=(self.width * 0.9, self.height * 0.9))
            PushMatrix()
            Rotate(angle=self.nexus_rotation_angle, origin=self.center)
            Color(*self.nexus_color[:3], 0.3)
            Line(circle=(self.center_x, self.center_y, self.width * 0.48), width=1.5)
            Color(*self.nexus_color[:3], 0.2)
            Line(circle=(self.center_x, self.center_y, self.width * 0.38, 0, 180), width=1.2)
            PopMatrix()
            PushMatrix()
            Rotate(angle=-self.nexus_rotation_angle * 0.8, origin=self.center)
            Color(*self.nexus_color[:3], 0.4)
            Line(circle=(self.center_x, self.center_y, self.width * 0.45), width=1)
            PopMatrix()

class SciFiPanel(BoxLayout):
    nexus_color = ListProperty([0.1, 0.7, 1, 1])
    background_opacity = NumericProperty(0.1)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw_background,
                  size=self._draw_background,
                  nexus_color=self._draw_background)
    def _draw_background(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.nexus_color[:3], self.background_opacity)
            Rectangle(pos=self.pos, size=self.size)
            Color(*self.nexus_color[:3], 0.5)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=1.2)

class SciFiLabel(Label):
    nexus_color = ListProperty([0.1, 0.7, 1, 1])
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw_background,
                  size=self._draw_background,
                  nexus_color=self._draw_background)
    def _draw_background(self, *args):
        self.canvas.before.clear()
        corner_cut = self.height * 0.3
        with self.canvas.before:
            Color(*self.nexus_color[:3], 0.15)
            points = [
                self.x + corner_cut, self.y,
                self.x + self.width - corner_cut, self.y,
                self.x + self.width, self.y + corner_cut,
                self.x + self.width, self.y + self.height,
                self.x, self.y + self.height,
                self.x, self.y + corner_cut
            ]
            Line(points=points, width=1.5, close=True)