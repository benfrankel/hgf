###############################################################################
#                                                                             #
#   Copyright 2017 - Ben Frankel                                              #
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

from .visual import Visual, visualattr

from ..component import Component
from ..util import Rect, keyboard

import pygame


class GraphicalComponent(Rect, Component, metaclass=Visual):
    def __init__(self, x=0, y=0, w=0, h=0, visible=True, hover=True, click=True, focus=False, opacity=1):
        super().__init__(x, y, w, h, pause=False)

        # User interaction flags
        self.can_hover = hover
        self.can_click = click
        self.can_focus = focus

        # Visual attributes
        self.is_visible = visible
        self.size = w, h

        # State flags
        self.is_hovered = False
        self.is_focused = False
        self.is_stale = False  # Stale components will be refreshed

        # Graphical hierarchy
        self._graphical_children = []
        self._z = 0

        # Surfaces
        self._opacity = opacity
        if self.is_transparent:
            self._colorkey = None
            self._background = None
            self._display = None
        elif self.is_translucent:
            self._colorkey = (0, 0, 0, 0)
            self._background = pygame.Surface(self.size, pygame.SRCALPHA)
            self._display = pygame.Surface(self.size, pygame.SRCALPHA)
        else:  # self.is_opaque
            self._colorkey = (0, 0, 0)
            self._background = pygame.Surface(self.size)
            self._display = pygame.Surface(self.size)
        if self._colorkey is not None:
            self._background.set_colorkey(self.colorkey)
            self._display.set_colorkey(self.colorkey)

        # Dirty rectangle status
        self._is_dirty = False
        self._dirty_rects = []
        self._dirty_area = 0

        self._old_rect = None
        self._old_visible = None

    def prepare_hook(self):
        self.resize_hook_send()

    # Note!
    # Refresh should never modify size or position
    # It is expected to draw on top of the existing rect
    def refresh(self): pass

    def show_hook(self): pass

    def hide_hook(self): pass

    def activate_hook(self): pass

    def deactivate_hook(self): pass

    def take_focus_hook(self): pass

    def lose_focus_hook(self): pass

    def key_down_hook(self, unicode, key, mods): pass

    def key_up_hook(self, key, mods): pass

    def mouse_enter_hook(self, start, end, buttons): pass

    def mouse_exit_hook(self, start, end, buttons): pass

    def mouse_motion_hook(self, start, end, buttons): pass

    def mouse_down_hook(self, pos, button): pass

    def mouse_up_hook(self, pos, button): pass

    def track_hook(self): pass

    def _visibility_change(self, before, after):
        if after:
            self.show_hook()
        else:
            self.hide_hook()

    @visualattr
    def is_visible(self, _visibility_change): pass

    @visualattr
    def w(self, resize_hook): pass

    @visualattr
    def h(self, resize_hook): pass

    @property
    def is_transparent(self):
        return self._opacity == 0

    @property
    def is_translucent(self):
        return self._opacity == 1

    @property
    def is_opaque(self):
        return self._opacity == 2

    @property
    def is_dirty(self):
        if self._old_visible is None:
            return self.is_visible
        return self._is_dirty or self._old_visible != self.is_visible

    @is_dirty.setter
    def is_dirty(self, other):
        if other and not self.is_root:
            for rect in self._dirty_rects:
                self._clean_dirty_rects(rect)
        self._is_dirty = other

    @property
    def z(self):
        return self._z

    @z.setter
    def z(self, other):
        self._z = other
        if not self.is_root:
            self.parent._child_changed_z(self)

    @property
    def colorkey(self):
        return self._colorkey

    @colorkey.setter
    def colorkey(self, other):
        if self._colorkey != other:
            self._colorkey = other
            self._background.set_colorkey(other)
            self._display.set_colorkey(other)

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, other):
        if self._background.get_size() != other.get_size():
            self.size = other.get_size()
            if self.is_translucent:
                self._display = pygame.Surface(other.get_size(), pygame.SRCALPHA)
            elif self.is_opaque:
                self._display = pygame.Surface(other.get_size())
        if self._colorkey is not None:
            self._background.set_colorkey(self.colorkey)
            self._display.set_colorkey(self.colorkey)
        self._background = other
        self.is_dirty = True

    def abs_pos(self):
        if self.is_root:
            return self.pos
        px, py = self.parent.abs_pos()
        return px + self.x, py + self.y

    def abs_rect(self):
        return Rect(*self.abs_pos(), self.w, self.h)

    # Should only be called once, at setup
    def _recursive_refresh(self):
        for child in self._graphical_children:
            if child.is_loaded:
                child._recursive_refresh()
        self.refresh()

    def prepare(self):
        super().prepare()
        self._recursive_refresh()

    # Should only be called when style / options are reloaded
    def _recursive_stale(self):
        for child in self._graphical_children:
            if child.is_loaded:
                child._recursive_stale()
        self.is_stale = True

    def reload_style(self):
        super().reload_style()
        self._recursive_stale()

    def reload_options(self):
        super().reload_options()
        self._recursive_stale()

    def _child_changed_z(self, child):
        self._graphical_children.remove(child)
        for i, other in enumerate(self._graphical_children):
            if other.z > child.z:
                self._graphical_children.insert(i, child)
        self._graphical_children.append(child)

    def register(self, *children):
        super().register(*children)
        for child in children:
            if isinstance(child, GraphicalComponent):
                for i, other in enumerate(self._graphical_children):
                    if other.z > child.z:
                        self._graphical_children.insert(i, child)
                        break
                self._graphical_children.append(child)

    def unregister(self, *children):
        super().unregister(*children)
        for child in children:
            try:
                self._graphical_children.remove(child)
            except ValueError:
                pass

    def show(self):
        self.is_visible = True
        self.show_hook()

    def _recursive_lose_focus(self):
        if self.is_focused:
            self.lose_focus()
        for child in self._graphical_children:
            child._recursive_lose_focus()

    def hide(self):
        self.is_visible = False
        self._recursive_lose_focus()
        self.hide_hook()

    def toggle_show(self):
        if self.is_visible:
            self.hide()
        else:
            self.show()

    def activate(self):
        self.show()
        self.unpause()
        self.activate_hook()

    def deactivate(self):
        self.hide()
        self.pause()
        self.deactivate_hook()

    def take_focus(self):
        self._app.give_focus(self)
        self.take_focus_hook()

    def lose_focus(self):
        self._app.remove_focus(self)
        self.lose_focus_hook()

    def disowned_hook(self):
        if self._old_visible and self._old_rect is not None:
            try:
                self.parent._add_dirty_rect(self._old_rect)
            except AttributeError:
                pass
        for rect in self._dirty_rects:
            self._clean_dirty_rects(rect)
        self.is_dirty = self.is_visible

    def _key_down(self, unicode, key, mod):
        try:
            self.handle_message(self, self.controls_get(keyboard.name_from_pygame(key, mod)))
        except KeyError:
            pass
        self.key_down_hook(unicode, key, mod)

    def _key_up(self, key, mod):
        self.key_up_hook(key, mod)

    def _mouse_enter(self, start, end, buttons):
        self.mouse_enter_hook(start, end, buttons)
        for child in self._graphical_children:
            if child.can_hover and not child.is_paused and child.collide_point(end):
                rel_start = (start[0] - child.x, start[1] - child.y)
                rel_end = (end[0] - child.x, end[1] - child.y)
                child._mouse_enter(rel_start, rel_end, buttons)

    def _mouse_exit(self, start, end, buttons):
        self.mouse_exit_hook(start, end, buttons)
        for child in self._graphical_children:
            if child.can_hover and not child.is_paused and child.collide_point(start):
                rel_start = (start[0] - child.x, start[1] - child.y)
                rel_end = (end[0] - child.x, end[1] - child.y)
                child._mouse_exit(rel_start, rel_end, buttons)

    def _mouse_motion(self, start, end, buttons):
        self.mouse_motion_hook(start, end, buttons)
        for child in self._graphical_children:
            if child.can_hover and not child.is_paused and child.collide_point(start) and child.collide_point(end):
                rel_start = (start[0] - child.x, start[1] - child.y)
                rel_end = (end[0] - child.x, end[1] - child.y)
                child._mouse_motion(rel_start, rel_end, buttons)

    def _mouse_down(self, pos, button):
        self.mouse_down_hook(pos, button)
        if self.can_focus and not self.is_focused:
            self.take_focus()
        for child in self._graphical_children[::-1]:
            if child.can_click and not child.is_paused and child.collide_point(pos):
                rel_pos = (pos[0] - child.x, pos[1] - child.y)
                child._mouse_down(rel_pos, button)

    def _mouse_up(self, pos, button):
        self.mouse_up_hook(pos, button)
        for child in self._graphical_children:
            if child.can_click and not child.is_paused and child.collide_point(pos):
                rel_pos = (pos[0] - child.x, pos[1] - child.y)
                child._mouse_up(rel_pos, button)

    def _add_dirty_rect(self, rect):
        if not self.is_dirty and rect not in self._dirty_rects:
            area = rect.area
            if area + self._dirty_area > self.area:
                self.is_dirty = True
                self._dirty_area += area
            else:
                self._dirty_rects.append(rect)
                if not self.is_root:
                    self.parent._add_dirty_rect(Rect(self.x + rect.x, self.y + rect.y, rect.w, rect.h))

    def _clean_dirty_rects(self, rect):
        self._dirty_rects.remove(rect)
        self._dirty_area -= rect.area
        if not self.is_root:
            self.parent._clean_dirty_rects(Rect(self.x + rect.x, self.y + rect.y, rect.w, rect.h))

    def _transition_rects(self):
        if self._old_visible and self.is_visible:
            old = self._old_rect
            comb = Rect(min(self.x, old.x), min(self.y, old.y))
            comb.w = max(self.right, old.right) - comb.x
            comb.h = max(self.bottom, old.bottom) - comb.y
            if self.area + old.area > comb.area:
                return [comb]
            else:
                return [self._old_rect, Rect.copy(self)]
        elif self._old_visible:
            return [self._old_rect]
        elif self.is_visible:
            return [Rect.copy(self)]
        return []

    def _redraw_area(self, rect):
        children = self._graphical_children[:]
        self._display.fill(self.colorkey, rect.as_pygame_rect())
        self._display.blit(self._background, rect.pos, rect.as_pygame_rect())
        for child in children:
            if child.is_visible:
                if child.is_transparent:
                    children.extend(child._graphical_children)
                else:
                    area = rect.intersect(child)
                    if area is not None:
                        area.x -= child.x
                        area.y -= child.y
                        self._display.blit(child._display, (child.x + area.x, child.y + area.y), area.as_pygame_rect())

    def _clean_display(self):
        self.is_dirty = False
        self._dirty_rects = []
        self._old_rect = Rect.copy(self)
        self._old_visible = self.is_visible

    def _prepare_display(self):
        for child in self._graphical_children:
            if not child.is_transparent and child.is_dirty and not self.is_dirty:
                for rect in child._transition_rects():
                    self._add_dirty_rect(rect)
            if child.is_visible:
                child._prepare_display()
            elif child._old_visible:
                child._clean_display()
        if not self.is_transparent:
            if self.is_stale:
                self.refresh()
                self.is_stale = False
                self.is_dirty = True
            if self.is_dirty:
                self._redraw_area(self.rel_rect())
            else:
                for rect in self._dirty_rects:
                    self._redraw_area(rect)
        changed = self.is_dirty or self._dirty_rects
        self._clean_display()
        return changed

    def _recursive_track(self):
        self._track()
        for child in self._graphical_children:
            if not child.is_paused:
                child._recursive_track()

    # Catch mouse events not caught by Pygame
    def _track(self):
        self.track_hook()
        pos = pygame.mouse.get_pos()
        if not self.is_root:
            pos = tuple(x1 - x2 for x1, x2 in zip(pos, self.parent.abs_pos()))
        if self.is_hovered != self.collide_point(pos):
            rel = pygame.mouse.get_rel()
            self.is_hovered = not self.is_hovered
            if self.is_hovered:
                self._mouse_enter((pos[0] - rel[0], pos[1] - rel[1]), pos, pygame.mouse.get_pressed())
            else:
                self._mouse_exit((pos[0] - rel[0], pos[1] - rel[1]), pos, pygame.mouse.get_pressed())
        if self.is_hovered and not pygame.mouse.get_focused():
            self.is_hovered = False
            self._mouse_exit(pos, pos, pygame.mouse.get_pressed())

    def step(self):
        self._recursive_tick_hook()
        self._recursive_track()
        self._prepare_display()
