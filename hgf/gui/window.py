#!/usr/bin/env python

###############################################################################
#                                                                             #
#   Copyright 2017 Ben Frankel                                                #
#                                                                             #
#   Licensed under the Apache License, Version 2.0 (the "License");           #
#   you may not use this file except in compliance with the License.          #
#   You may obtain a copy of the License at                                   #
#                                                                             #
#       http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                             #
#   Unless required by applicable law or agreed to in writing, software       #
#   distributed under the License is distributed on an "AS IS" BASIS,         #
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#   See the License for the specific language governing permissions and       #
#   limitations under the License.                                            #
#                                                                             #
###############################################################################


import pygame

from . import base


class Window(base.StructuralComponent):
    def __init__(self, w, h, *args, **kwargs):
        super().__init__(w, h, **kwargs)
        self.name = 'window'

        self.args = args
        self.surf = None

        self.bg_color = None

    def load_hook(self):
        self.bg_color = self.style_get('bg-color')
        pygame.display.set_caption(self.options_get('title'))

    def open(self):
        self.surf = pygame.display.set_mode(self.size, *self.args)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.key_down(event.unicode, event.key, event.mod)
        elif event.type == pygame.KEYUP:
            self.key_up(event.key, event.mod)
        elif event.type == pygame.MOUSEMOTION:
            start = (event.pos[0] - event.rel[0], event.pos[1] - event.rel[1])
            self._mouse_motion(start, event.pos, event.buttons)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._mouse_down(event.pos, event.button)
        elif event.type == pygame.MOUSEBUTTONUP:
            self._mouse_up(event.pos, event.button)

    def handle_message(self, sender, message):
        if message == 'exit':
            exit()
        # TODO: Warn about unhandled message?

    def refresh(self):
        self.bg_color = self.style_get('bg-color')
        pygame.display.set_caption(self.options_get('title'))

    def _draw(self):
        if super()._draw():
            self.surf.fill(self.bg_color)
            self.surf.blit(self._display, (0, 0))
            pygame.display.update()
