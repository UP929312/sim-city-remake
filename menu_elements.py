import math
import sys
from typing import Any, Callable, NoReturn, TypeVar

import pygame


class GoBack(Exception):
    pass


def go_back() -> NoReturn:
    raise GoBack


# ================================================================================================================================
def font_size_controller(text: str | int, x1: int, x2: int, y1: int, y2: int) -> int:
    if not text:
        return 1
    return int(min((x2 - x1) / math.pow(len(str(text)), 0.8), (y2 - y1) * 0.8))


class Element:
    def __init__(self, x1: int, y1: int, width: int | float, height: int | float, text: str | int) -> None:
        assert width >= 16 and height >= 16, f"Height or width are too small (possibly negative) at {width=}, {height=}"
        self.x1 = int(x1)
        self.y1 = int(y1)
        self.width = int(width)
        self.height = int(height)
        self.text = text

    def __str__(self) -> str:
        return f"{self.__class__.__name__} object: ({self.x1}, {self.y1}) width and height: {self.width}, {self.height}, with text `{self.text}`"

    def intersected(self, x: int, y: int):  # type: ignore[no-untyped-def]   # -> "Element" | None
        return (self if
                self.x1 <= x <= self.x1 + self.width and
                self.y1 <= y <= self.y1 + self.height  # Remove the offset from the y coord
                else None)

    def draw(self, window: pygame.surface.Surface, vertical_scroll_offset: int) -> None:
        raise NotImplementedError


ElementType = TypeVar('ElementType', bound=Element)


class Label(Element):
    def __init__(self, text: str | int, x1: int, y1: int, width: int | float, height: int | float, text_colour: tuple[int, int, int] = (255, 255, 255)) -> None:
        super().__init__(x1, y1, width, height, text)
        self.text_colour = text_colour
        self.font_size = font_size_controller(self.text, self.x1, self.x1 + int(width), self.y1, self.y1 + int(height))
        self.center_x = int(x1 + width // 2)
        self.center_y = int(y1 + height // 2)

    def draw(self, window: pygame.surface.Surface, vertical_scroll_offset: int) -> None:
        font = pygame.font.SysFont("Comic Sans MS", self.font_size)
        text_rendered = font.render(str(self.text), False, self.text_colour)
        text_rect = text_rendered.get_rect(center=(self.center_x, self.center_y+vertical_scroll_offset))
        window.blit(text_rendered, text_rect)

    def __str__(self) -> str:
        return super().__str__() + f" and text_colour: `{self.text_colour}`"


class Button(Element):
    def __init__(self, x1: int, y1: int, width: int | float, height: int | float, text: str | None, on_click: Callable) -> None:  # type: ignore[type-arg]
        super().__init__(x1, y1, width, height, str(text))
        if text is not None:
            self.label = Label(text, x1, y1, int(width), int(height))
        self.on_click = on_click

    def draw(self, window: pygame.surface.Surface, vertical_scroll_offset: int) -> None:
        pygame.draw.rect(window, (50, 50, 50), (self.x1, self.y1+vertical_scroll_offset, self.width, self.height))
        if hasattr(self, "label"):
            self.label.draw(window, vertical_scroll_offset)


class IconButton(Element):
    """
    Used in the actual game to select different buildings and such
    on_click returns window, clicked_element, mouse_x, mouse_y
    """

    def __init__(
        self, x1: int, y1: int, width: int, height: int, text: str, icon_image: pygame.surface.Surface,
        is_selected: bool, on_click: Callable[[pygame.surface.Surface, Button, int, int], None]
    ) -> None:
        super().__init__(x1, y1, width, height, text)
        self.icon_image = icon_image
        self.on_click = on_click
        self.text = text  # This is used to detect which button was pressed.
        self.is_selected = is_selected

        self.size = 32

    def draw(self, window: pygame.surface.Surface, vertical_scroll_offset: int) -> None:
        window.blit(self.icon_image, (self.x1, self.y1+vertical_scroll_offset))
        if self.is_selected:
            pygame.draw.rect(window, (255, 255, 255), (self.x1, self.y1, self.size, 1))  # Top
            pygame.draw.rect(window, (255, 255, 255), (self.x1, self.y1, 1, self.size))  # Left
            pygame.draw.rect(window, (255, 255, 255), (self.x1 + self.size, self.y1, 1, self.size))  # Right
            pygame.draw.rect(window, (255, 255, 255), (self.x1, self.y1 + self.size, self.size, 1))  # Bottom


class RowButton(Element):
    """
    Used in the actual game to represent the bottom row
    on_click returns window, clicked_element, mouse_x, mouse_y
    """

    def __init__(self, x1: int, y1: int, width: int, height: int, text: str) -> None:
        super().__init__(x1, y1, width, height, text)
        self.text = text  # This is used to detect which button was pressed.
        self.label = Label(self.text, self.x1, self.y1 - 2, self.width, self.height, text_colour=(255, 255, 0))

    def draw(self, window: pygame.surface.Surface, vertical_scroll_offset: int) -> None:
        pygame.draw.rect(window, (0, 0, 0), (self.x1+vertical_scroll_offset, self.y1, self.width, self.height))
        self.label.draw(window, vertical_scroll_offset)

    def __str__(self) -> str:
        return f"{self.__class__.__name__} object: ({self.x1}, {self.y1}) width & height: {self.width}, {self.height}, with text `{self.text}`"


class RowOfButtons(Element):
    """
    Used in the actual game to represent the bottom row
    """
    def __init__(self, x1: int, y1: int, width: int, height: int, text_items: list[str]) -> None:  # , on_click: Callable[[pygame.surface.Surface, RowButton, int, int], None]) -> None:
        super().__init__(x1, y1, width, height, text="")
        # self.on_click = on_click
        self.children = [
            RowButton((x1+(width//len(text_items))*i), y1, width // len(text_items), height, text)
            for i, text in enumerate(text_items)
        ]

    def draw(self, window: pygame.surface.Surface, vertical_scroll_offset: int) -> None:
        for child in self.children:
            child.draw(window, vertical_scroll_offset)

    def __str__(self) -> str:
        return super().__str__() + "\n" + "\n".join([f"    With child buttons: {self.children}"])


class ToggleRow(Element):
    def __init__(self, x1: int, y1: int, width: int, height: int, text: str, key: str, starting_value: bool | None) -> None:
        super().__init__(x1, y1, width, height, text)
        self.key = key
        self.value = starting_value or False

        # 40 : gap-10 : 10: gap-20 : 20 - Generate biomes : (Yes) Toggle
        section1, section2 = int(x1 + ((width) // 10) * 4), int(x1 + ((width) // 10) * 5)
        self.name_label = Label(text, x1, y1, section1 - x1, height)
        self.toggled_label = Label("(Yes)" if self.value else "(No)", int(section1 + (0.1 * width)), y1, section2 - section1, height)
        self.toggle_button = Button(int(section2 + (0.2 * width)), y1, width - section2, height * 0.75, "Toggle", self.on_click)

        self.children: tuple[Label, Label, Button] = (self.name_label, self.toggled_label, self.toggle_button)

    def draw(self, window: pygame.surface.Surface, vertical_scroll_offset: int) -> None:
        for child in (self.name_label, self.toggled_label, self.toggle_button):
            child.draw(window, vertical_scroll_offset)

    def on_click(self, *_: Any) -> None:
        self.value = not self.value
        self.toggled_label.text = "(Yes)" if self.value else "(No)"

    def __str__(self) -> str:
        return (
            super().__str__() + "\n"  # fmt: skip
            + "\n".join(
                [f"    With child name_label: {self.name_label}", f"    With child toggled_label: {self.toggled_label}", f"    With child other buttons: {self.children[2:]}"]
            )
        )


class IntegerSelector(Element):
    def __init__(
        self, x1: int, y1: int, width: int, height: int, text: str,  # fmt: skip
        key: str, starting_value: int | None = None,  # fmt: skip
        minimum: int = 0, maximum: int = 100, big_step: int = 100, small_step: int = 10, middle: int | None = None,  # fmt: skip
    ) -> None:
        super().__init__(x1, y1, width, height, text)
        self.key = key
        self.value = starting_value or middle or (minimum + maximum) // 2
        self.minimum = minimum
        self.maximum = maximum
        self.big_step = big_step
        self.small_step = small_step
        self.middle = middle or (minimum + maximum) // 2

        middle_height = height // 2

        self.name_label = Label(text, x1, y1-4, width * 0.25, middle_height)
        self.value_label = Label(self.value, int(x1 + (width * 0.75)), y1-4, width * 0.25, middle_height)
        self.children: list[Label | Button] = [self.name_label, self.value_label]
        slot_size = width // 9
        for i, icon in enumerate(["<<", "<", "0", ">", ">>"]):
            button = Button(x1 + (slot_size * i * 2), y1 + middle_height, slot_size, middle_height, icon, self.on_click)
            self.children.append(button)

    def draw(self, window: pygame.surface.Surface, vertical_scroll_offset: int) -> None:
        for child in self.children:
            child.draw(window, vertical_scroll_offset)

    def on_click(self, _: pygame.surface.Surface, button: Button, *_1: Any) -> None:
        if button.text == "<<":
            self.value = max(self.value - self.big_step, self.minimum)
        elif button.text == "<":
            self.value = max(self.value - self.small_step, self.minimum)
        elif button.text == "0":
            if self.middle:
                self.value = self.middle
            else:
                self.value = (self.minimum + self.maximum) // 2
        elif button.text == ">":
            self.value = min(self.maximum, self.value + self.small_step)
        elif button.text == ">>":
            self.value = min(self.maximum, self.value + self.big_step)
        else:
            raise IndexError(f"Uh oh, IntegerSelector recieved something outside of it's normal, it recieved: {button.text}")
        self.value_label.text = str(self.value)

    def intersected(self, x: int, y: int) -> Button | None:  # type: ignore[return]
        if super().intersected(x, y):
            for button in self.children[2:]:
                if button.intersected(x, y):
                    return button  # type: ignore[return-value]

    def __str__(self) -> str:
        return (
            super().__str__() + "\n"
            + "\n".join([f"    With child name_label: {self.name_label}", f"    With child value_label: {self.value_label}", f"    With child other buttons: {self.children[2:]}"])
        )


class SliderElement(Element):
    def __init__(self, x1: int, y1: int, width: int, height: int, starting_value: int | None = None, minimum: int = 0, maximum: int = 100) -> None:
        super().__init__(x1, y1, width, height, text="")
        self.value = starting_value or (minimum + maximum) // 2
        self.x1 = x1
        self.y1 = y1
        self.width = width
        self.height = height
        self.minimum = minimum
        self.maximum = maximum

        def on_slider_click(self: SliderElement, mouse_x: int) -> None:
            offset_from_x1 = mouse_x - self.x1
            percent_in = offset_from_x1 / self.width
            self.value = int(percent_in * (self.maximum - self.minimum))

        self.slider_button = Button(self.x1, self.y1, self.width, self.height // 2, None, lambda _, _1, x, _2: on_slider_click(self, x))

    def draw(self, window: pygame.surface.Surface, vertical_scroll_offset: int) -> None:
        percent_in = self.value / (self.maximum + self.minimum)
        width_in = percent_in * self.width
        self.slider_button.draw(window, vertical_scroll_offset)
        pygame.draw.rect(window, (80, 80, 80), rect=(self.x1 + width_in, vertical_scroll_offset+self.y1 - (int(self.height / 1.3)), self.width // 20, self.height * 2))

    def intersected(self, x: int, y: int) -> Button | None:  # type: ignore[return]
        if self.slider_button.intersected(x, y):
            return self.slider_button


class SliderRow(Element):
    def __init__(self, x1: int, y1: int, width: int, height: int, text: str, starting_value: int | None = None, minimum: int = 0, maximum: int = 100) -> None:
        super().__init__(x1, y1, width, height, text)

        self.name_label = Label(text, x1, y1, width * 0.3, height // 2)
        self.slider_element = SliderElement(x1 + width // 2, y1 + height // 4, width // 2, height // 4, starting_value, minimum, maximum)
        self.value_label = Label(self.slider_element.value, int(x1 + (width * 0.25)), y1, width * 0.25, height // 2)

    def on_click(self, *_) -> None:  # type: ignore[no-untyped-def]
        pass  # Sigh, I never thought I'd get to this, but without this function/pass, it doesn't work

    def intersected(self, x: int, y: int) -> Button | None:  # type: ignore[return]
        if self.slider_element.intersected(x, y):
            return self.slider_element.slider_button

    def draw(self, window: pygame.surface.Surface, vertical_scroll_offset: int) -> None:
        self.value_label.text = str(self.slider_element.value)

        self.name_label.draw(window, vertical_scroll_offset)
        self.value_label.draw(window, vertical_scroll_offset)
        self.slider_element.draw(window, vertical_scroll_offset)


class TextEntry(Element):
    def __init__(self, x1: int, y1: int, width: int, height: int) -> None:
        super().__init__(x1, y1, width, height, "")
        self.text = ""

    def draw(self, window: pygame.surface.Surface, vertical_scroll_offset: int) -> None:
        BORDER = int(self.height*0.1)
        pygame.draw.rect(window, (80, 80, 80), rect=(self.x1, vertical_scroll_offset+self.y1, self.width, self.height))
        pygame.draw.rect(window, (0, 0, 0), rect=(self.x1+BORDER, vertical_scroll_offset+self.y1+BORDER, self.width-BORDER*2, self.height-BORDER*2))
        Label(self.text, self.x1+BORDER, vertical_scroll_offset+self.y1-6+BORDER, self.width-BORDER, self.height-BORDER).draw(window, vertical_scroll_offset)


pygame.font.init()
BACK_BUTTON = Button(0, 0, 64, 64, "<", lambda *_: go_back())

# ================================================================================================================================


def handle_collisions(window: pygame.surface.Surface, mouse_x: int, mouse_y: int,
                      elements: list[ElementType], vertical_scroll_offset: int) -> None | Any:
    """
    Returns None if no collisions were detected, else returns the value of the `on_click` function of the butotn that was pressed.
    """
    for element in [x for x in elements if hasattr(x, "on_click")]:
        clicked_button = element.intersected(mouse_x, mouse_y-vertical_scroll_offset)
        if clicked_button:
            # rint("="*50, "\n", str(clicked_button), "\n")
            result = clicked_button.on_click(window, clicked_button, mouse_x, mouse_y)  # pyright: ignore
            return result
    return None


def handle_menu(window: pygame.surface.Surface, title: str, elements: list[ElementType]) -> Any:
    """
    A forever loop which will exit when a button press returns something that isn't None, or they press Escape
    """
    title_label = Label(title, 0, 0, window.get_width(), int(window.get_height() // 6))

    last_element = max(elements, key=lambda element: element.y1)
    max_scroll_amount = last_element.y1+last_element.height+64
    amount_vertically_scrolled = 0

    while True:
        window.fill((0, 0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                go_back()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
                x, y = pygame.mouse.get_pos()
                result = handle_collisions(window, x, y, elements, amount_vertically_scrolled)
                if result is not None:
                    return result
            if event.type == pygame.MOUSEWHEEL and max_scroll_amount > window.get_height():  # Only if we need to scroll
                scrolling_down = event.y > 0
                event.y *= 10
                # if the first element is on the screen, and they're not scrolling up, allow
                # if the last element's y (and height) is > window height, and they're scrolling up, allow
                if (
                    (title_label.y1+amount_vertically_scrolled <= 0 and scrolling_down) or
                    (max_scroll_amount+amount_vertically_scrolled > window.get_height() and not scrolling_down)  # Scrolling up
                ):
                    amount_vertically_scrolled += event.y

        for element in elements+[title_label]:
            element.draw(window, vertical_scroll_offset=0 if element is BACK_BUTTON else amount_vertically_scrolled)
        pygame.display.update()
