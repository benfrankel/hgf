#!/usr/bin/env python

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


import pygame

from hgf.util import keys


class Rect:
    def __init__(self, x=0, y=0, w=0, h=0):
        self._x = x
        self._y = y
        self._w = w
        self._h = h

    @property
    def size(self):
        return self._w, self._h

    @size.setter
    def size(self, other):
        self._w, self._h = other

    @property
    def w(self):
        return self.size[0]

    @w.setter
    def w(self, other):
        self.size = (other, self.size[1])

    @property
    def h(self):
        return self.size[1]

    @h.setter
    def h(self, other):
        self.size = (self.size[0], other)

    @property
    def width(self):
        return self.w

    @width.setter
    def width(self, other):
        self.w = other

    @property
    def height(self):
        return self.h

    @height.setter
    def height(self, other):
        self.h = other

    @property
    def pos(self):
        return self._x, self._y

    @pos.setter
    def pos(self, other):
        self._x, self._y = other

    topleft = pos

    @property
    def x(self):
        return self.pos[0]

    @x.setter
    def x(self, other):
        self.pos = (other, self.pos[1])

    left = x

    @property
    def y(self):
        return self.pos[1]

    @y.setter
    def y(self, other):
        self.pos = (self.pos[0], other)

    top = y

    @property
    def midx(self):
        return self.x + self.w // 2

    @midx.setter
    def midx(self, other):
        self.x = other - self.w // 2

    @property
    def right(self):
        return self.x + self.w

    @right.setter
    def right(self, other):
        self.x = other - self.w

    @property
    def midy(self):
        return self.y + self.h // 2

    @midy.setter
    def midy(self, other):
        self.y = other - self.h // 2

    @property
    def bottom(self):
        return self.y + self.h

    @bottom.setter
    def bottom(self, other):
        self.y = other - self.h

    @property
    def midtop(self):
        return self.midx, self.top

    @midtop.setter
    def midtop(self, other):
        self.midx, self.top = other

    @property
    def topright(self):
        return self.right, self.top

    @topright.setter
    def topright(self, other):
        self.right, self.top = other

    @property
    def midleft(self):
        return self.x, self.y + self.h // 2

    @midleft.setter
    def midleft(self, other):
        self.left, self.midy = other

    @property
    def center(self):
        return self.midx, self.midy

    @center.setter
    def center(self, other):
        self.midx, self.midy = other

    @property
    def midright(self):
        return self.right, self.midy

    @midright.setter
    def midright(self, other):
        self.right, self.midy = other

    @property
    def bottomleft(self):
        return self.left, self.bottom

    @bottomleft.setter
    def bottomleft(self, other):
        self.left, self.bottom = other

    @property
    def midbottom(self):
        return self.midx, self.bottom

    @midbottom.setter
    def midbottom(self, other):
        self.midx, self.bottom = other

    @property
    def bottomright(self):
        return self.right, self.bottom

    @bottomright.setter
    def bottomright(self, other):
        self.right, self.bottom = other

    def area(self):
        return self.w * self.h

    def collide_point(self, point):
        return self.left <= point[0] < self.right and self.top <= point[1] < self.bottom

    def collide_rect(self, rect):
        return self.left < rect.right and rect.left < self.right and self.top < rect.bottom and rect.top < self.bottom

    def intersect(self, rect):
        result = Rect(max(self.x, rect.x), max(self.y, rect.y))
        result.w = min(self.right, rect.right) - result.x
        result.h = min(self.bottom, rect.bottom) - result.y
        if result.w < 0 or result.h < 0:
            return None
        return result

    def as_pygame_rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.w == other.w and self.h == other.h

    def __str__(self):
        return '{}({}, {}, {}, {})'.format(self.__class__.__name__, self.x, self.y, self.w, self.h)

    __repr__ = __str__


class StructuralComponent(Rect):
    def __init__(self, w, h, x=0, y=0, visible=True, hover=True, click=True, focus=False, opacity=1):
        super().__init__(x, y, w, h)

        # Config identification
        self.name = None
        self._context = None

        # Hierarchical references
        self._app = None
        self.parent = None
        self._children = []

        # Depth
        self.z = 0

        # General flags
        self._is_visible = visible
        self._can_hover = hover
        self._can_click = click
        self.can_focus = focus
        self._opacity = opacity
        self._is_paused = False
        self._is_hovered = False
        self.is_focused = False

        # Surfaces
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

        # Dirty Rectangle memory
        self._is_dirty = False
        self._dirty_rects = []
        self._dirty_area = 0

        self._old_rect = None
        self._old_visible = None

        self.is_loaded = False

    @property
    def is_root(self):
        return self.parent is None

    @property
    def is_visible(self):
        return self._is_visible and (self.is_root or self.parent.is_visible)

    @property
    def can_hover(self):
        return self._can_hover and (self.is_root or self.parent.can_hover)

    @property
    def can_click(self):
        return self._can_click and (self.is_root or self.parent.can_click)

    @property
    def is_paused(self):
        return self._is_paused or not self.is_root and self.parent.is_paused

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
    def is_alive(self):
        return self._is_visible and not self._is_paused

    @property
    def app(self):
        return self._app

    @app.setter
    def app(self, other):
        self._app = other
        for child in self._children:
            child.app = other

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, other):
        self._context = other
        for child in self._children:
            child.context = other

    @property
    def is_dirty(self):
        if self._old_visible is None:
            return self._is_visible
        return self._is_dirty or self._old_rect != self or self._old_visible != self._is_visible

    @is_dirty.setter
    def is_dirty(self, other):
        if other and not self.is_root:
            for rect in self._dirty_rects:
                self._clean_dirty_rects(rect)
        self._is_dirty = other

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

    @background.setter  # Perhaps find a better solution than this to resizing?
    def background(self, other):
        if self.size != other.get_size():
            if self.is_translucent:
                self._display = pygame.Surface(other.get_size(), pygame.SRCALPHA)
            elif self.is_opaque:
                self._display = pygame.Surface(other.get_size())
        if self._colorkey is not None:
            self._background.set_colorkey(self.colorkey)
            self._display.set_colorkey(self.colorkey)
        self._background = other
        self.size = other.get_size()
        self.is_dirty = True

    def load_hook(self):
        pass

    def load(self):
        self.load_hook()
        self.is_loaded = True
        self.refresh()

    def refresh(self):
        pass

    def resize(self, size):
        if self.size != size:
            self.size = size
            self.refresh()

    def copy_rect(self):
        return Rect(self.x, self.y, self.w, self.h)

    def rel_rect(self):
        return Rect(0, 0, self.w, self.h)

    def abs_rect(self):
        if self.is_root:
            return self.copy_rect()
        abs_pos = self.parent.abs_rect().pos
        return Rect(abs_pos[0] - self.pos[0], abs_pos[1] - self.pos[1], self.w, self.h)

    def show_hook(self):
        pass

    def show(self):
        self._is_visible = True
        self.unpause()
        self.show_hook()

    def _parent_hiding(self):
        if self.is_focused:
            self.release_focus()
        for child in self._children:
            child._parent_hiding()

    def hide_hook(self):
        pass

    def hide(self):
        self._is_visible = False
        self._parent_hiding()
        self.pause()
        self.hide_hook()

    def take_focus_hook(self):
        pass

    def take_focus(self):
        self._app.give_focus(self)
        self.take_focus_hook()

    def release_focus_hook(self):
        pass

    def release_focus(self):
        self._app.remove_focus(self)
        self.release_focus_hook()

    def pause_hook(self):
        pass

    def pause(self):
        self._is_paused = True
        self.pause_hook()

    def unpause_hook(self):
        pass

    def unpause(self):
        self._is_paused = False
        self.unpause_hook()

    def style_get(self, query):
        return self._app.config.style_get(query, self.name, self.context)

    def options_get(self, query):
        return self._app.config.options_get(query, self.name, self.context)

    def controls_get(self, query):
        return self._app.config.controls_get(query, self.context)

    def register(self, child):
        if not child.is_root:
            child.parent.unregister(child)
        for rect in child._dirty_rects:
            child._clean_dirty_rects(rect)
        child.app = self._app
        child.parent = self
        if child.context is None and self.context is not None:
            child.context = self.context
        child.is_dirty = child._is_visible
        self._children.append(child)

    def register_all(self, children):
        for child in children:
            self.register(child)

    def unregister(self, child):
        self._children.remove(child)
        child.app = None
        child.parent = None
        child.context = None
        if child._old_visible and child._old_rect is not None:
            self._add_dirty_rect(child._old_rect)
        if child.is_focused:
            child.release_focus()

    def unregister_all(self, children):
        for child in children:
            self.unregister(child)

    def key_down(self, unicode, key, mod):
        try:
            self.handle_message(self, self.controls_get(keys.key_name(key, mod)))
        except KeyError:
            pass

    def key_up(self, key, mod):
        pass

    def mouse_enter_hook(self, start, end, buttons):
        pass

    def _mouse_enter(self, start, end, buttons):
        self.mouse_enter_hook(start, end, buttons)
        for child in self._children:
            if child._can_hover and child.is_alive and child.collide_point(end):
                rel_start = (start[0] - child.x, start[1] - child.y)
                rel_end = (end[0] - child.x, end[1] - child.y)
                child._mouse_enter(rel_start, rel_end, buttons)

    def mouse_exit_hook(self, start, end, buttons):
        pass

    def _mouse_exit(self, start, end, buttons):
        self.mouse_exit_hook(start, end, buttons)
        for child in self._children:
            if child._can_hover and child.is_alive and child.collide_point(start):
                rel_start = (start[0] - child.x, start[1] - child.y)
                rel_end = (end[0] - child.x, end[1] - child.y)
                child._mouse_exit(rel_start, rel_end, buttons)

    def mouse_motion_hook(self, start, end, buttons):
        pass

    def _mouse_motion(self, start, end, buttons):
        self.mouse_motion_hook(start, end, buttons)
        for child in self._children:
            if child._can_hover and child.is_alive and child.collide_point(start) and child.collide_point(end):
                rel_start = (start[0] - child.x, start[1] - child.y)
                rel_end = (end[0] - child.x, end[1] - child.y)
                child._mouse_motion(rel_start, rel_end, buttons)

    def mouse_down_hook(self, pos, button):
        pass

    def _mouse_down(self, pos, button):
        self.mouse_down_hook(pos, button)
        if self.can_focus and not self.is_focused:
            self.take_focus()
        for child in self._children[::-1]:
            if child._can_click and child.is_alive and child.collide_point(pos):
                rel_pos = (pos[0] - child.x, pos[1] - child.y)
                child._mouse_down(rel_pos, button)

    def mouse_up_hook(self, pos, button):
        pass

    def _mouse_up(self, pos, button):
        self.mouse_up_hook(pos, button)
        for child in self._children:
            if child._can_click and child.is_alive and child.collide_point(pos):
                rel_pos = (pos[0] - child.x, pos[1] - child.y)
                child._mouse_up(rel_pos, button)

    def handle_message(self, sender, message):
        self.send_message(message)

    def send_message(self, message):
        if not self.is_root:
            self.parent.handle_message(self, message)

    def _add_dirty_rect(self, rect):
        if not self.is_dirty and rect not in self._dirty_rects:
            area = rect.area()
            if area + self._dirty_area > self.area():
                self.is_dirty = True
                self._dirty_area += area
            else:
                self._dirty_rects.append(rect)
                if not self.is_root:
                    self.parent._add_dirty_rect(Rect(self.x + rect.x, self.y + rect.y, rect.w, rect.h))

    def _clean_dirty_rects(self, rect):
        self._dirty_rects.remove(rect)
        self._dirty_area -= rect.area()
        if not self.is_root:
            self.parent._clean_dirty_rects(Rect(self.x + rect.x, self.y + rect.y, rect.w, rect.h))

    def _transition_rects(self):
        if self._old_visible and self._is_visible:
            old = self._old_rect
            comb = Rect(min(self.x, old.x), min(self.y, old.y))
            comb.w = max(self.right, old.right) - comb.x
            comb.h = max(self.bottom, old.bottom) - comb.y
            if self.area() + old.area() > comb.area():
                return [comb]
            else:
                return [self._old_rect, self.copy_rect()]
        elif self._old_visible:
            return [self._old_rect]
        elif self._is_visible:
            return [self.copy_rect()]
        return []

    def _redraw_area(self, rect):
        children = self._children[:]
        self._display.fill(self.colorkey, rect.as_pygame_rect())
        self._display.blit(self._background, rect.pos, rect.as_pygame_rect())
        for child in children:
            if child._is_visible:
                if child.is_transparent:
                    children.extend(child._children)
                else:
                    area = rect.intersect(child)
                    if area is not None:
                        area.x -= child.x
                        area.y -= child.y
                        self._display.blit(child._display, (child.x + area.x, child.y + area.y), area.as_pygame_rect())

    def _draw(self):
        if self._is_visible:
            for child in self._children:
                if not child.is_transparent and child.is_dirty and not self.is_dirty:
                    for rect in child._transition_rects():
                        self._add_dirty_rect(rect)
                if child._is_visible or child._old_visible:
                    child._draw()
            if not self.is_transparent:
                if self.is_dirty:
                    self._redraw_area(self.rel_rect())
                else:
                    for rect in self._dirty_rects:
                        self._redraw_area(rect)
        changed = self.is_dirty or bool(self._dirty_rects)
        self.is_dirty = False
        self._dirty_rects = []
        self._old_rect = self.copy_rect()
        self._old_visible = self._is_visible
        return changed

    def track_hook(self):
        pass

    # Catch quick mouse events
    def _track(self):
        self.track_hook()
        pos = pygame.mouse.get_pos()
        if not self.is_root:
            pos = tuple(x1 - x2 for x1, x2 in zip(pos, self.parent.abs_rect().pos))
        if self._is_hovered != self.collide_point(pos):
            rel = pygame.mouse.get_rel()
            self._is_hovered = not self._is_hovered
            if self._is_hovered:
                self._mouse_enter((pos[0] - rel[0], pos[1] - rel[1]), pos, pygame.mouse.get_pressed())
            else:
                self._mouse_exit((pos[0] - rel[0], pos[1] - rel[1]), pos, pygame.mouse.get_pressed())
        if self._is_hovered and not pygame.mouse.get_focused():
            self._is_hovered = False
            self._mouse_exit(pos, pos, pygame.mouse.get_pressed())
        for child in self._children:
            if child.is_alive:
                child._track()

    def update_hook(self):
        pass

    def _update(self):
        if not all(self._children[i].z <= self._children[i+1].z for i in range(len(self._children) - 1)):
            self._children.sort(key=lambda x: x.z)
            self.is_dirty = True
        for child in self._children:
            if child.is_alive:
                child._update()
        self.update_hook()

    def tick(self):
        self._track()
        self._update()
        self._draw()
