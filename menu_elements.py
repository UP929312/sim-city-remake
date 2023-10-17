import math
from typing import Any, Callable, Literal, NoReturn

import pygame

from utils import IMAGES, centered_text, outline


class GoBack(Exception):
    pass


def go_back() -> NoReturn:
    raise GoBack


# ================================================================================================================================
def font_size_controller(text: str | int, x1: int, x2: int, y1: int, y2: int) -> int:
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

    def intersected(self, x: int, y: int):  #  -> "Element" | None    # type: ignore[no-untyped-def]
        return self if self.x1 <= x <= self.x1 + self.width and self.y1 <= y <= self.y1 + self.height else None


class Label(Element):
    def __init__(self, text: str | int, x1: int, y1: int, width: int | float, height: int | float, text_colour: tuple[int, int, int] = (255, 255, 255)) -> None:
        super().__init__(x1, y1, width, height, text)
        self.text_colour = text_colour
        self.text_size = font_size_controller(self.text, self.x1, self.x1 + int(width), self.y1, self.y1 + int(height))
        self.center_x = int(x1 + width // 2)
        self.center_y = int(y1 + height // 2)

    def draw(self, window: pygame.surface.Surface) -> None:
        centered_text(window, self.text_size, self.text, self.text_colour, self.center_x, self.center_y)

    def __str__(self) -> str:
        return super().__str__() + f" and text_colour: `{self.text_colour}`"


class Button(Element):
    def __init__(self, x1: int, y1: int, width: int | float, height: int | float, text: str | None, on_click: Callable) -> None:
        super().__init__(x1, y1, width, height, str(text))
        if text is not None:
            self.label = Label(text, x1, y1, int(width), int(height))
        self.on_click = on_click

    def draw(self, window: pygame.surface.Surface) -> None:
        pygame.draw.rect(window, (50, 50, 50), (self.x1, self.y1, self.width, self.height))
        if hasattr(self, "label"):
            self.label.draw(window)


class IconButton(Element):
    """
    Used in the actual game to select different buildings and such
    on_click returns window, clicked_element, mouse_x, mouse_y
    """

    def __init__(
        self, x1: int, y1: int, width: int, height: int, text: str, icon_image: str, is_selected: bool, on_click: Callable[[pygame.surface.Surface, Button, int, int], None]
    ) -> None:
        super().__init__(x1, y1, width, height, text)
        self.icon_image = icon_image
        self.on_click = on_click
        self.text = text  # This is used to detect which button was pressed.
        self.is_selected = is_selected

    def draw(self, window: pygame.surface.Surface) -> None:
        window.blit(IMAGES[self.icon_image], (self.x1, self.y1))
        if self.is_selected:
            outline(window, self.x1, self.y1)


class RowButton(Element):
    """
    Used in the actual game to represent the bottom row
    on_click returns window, clicked_element, mouse_x, mouse_y
    """

    def __init__(self, x1: int, y1: int, width: int, height: int, text: str) -> None:
        super().__init__(x1, y1, width, height, text)
        self.text = text  # This is used to detect which button was pressed.
        self.label = Label(self.text, self.x1, self.y1-2, self.width, self.height, text_colour=(255, 255, 0))

    def draw(self, window: pygame.surface.Surface) -> None:
        pygame.draw.rect(window, (0, 0, 0), (self.x1, self.y1, self.width, self.height))
        self.label.draw(window)

    def __str__(self) -> str:
        return f"{self.__class__.__name__} object: ({self.x1}, {self.y1}) width & height: {self.width}, {self.height}, with text `{self.text}`"


class RowOfButtons(Element):
    """
    Used in the actual game to represent the bottom row
    """
    def __init__(self, x1: int, y1: int, width: int, height: int, text_items: list[str]) -> None:  #, on_click: Callable[[pygame.surface.Surface, RowButton, int, int], None]) -> None:
        super().__init__(x1, y1, width, height, text="")
        #self.on_click = on_click
        self.children = [
            RowButton((x1+(width//len(text_items))*i), y1, width//len(text_items), height, text)
            for i, text in enumerate(text_items)
        ]

    def draw(self, window: pygame.surface.Surface) -> None:
        for child in self.children:
            child.draw(window)

    def __str__(self) -> str:
        return super().__str__() + "\n" + "\n".join([f"    With child buttons: {self.children}"])


class ToggleRow(Element):
    def __init__(self, x1: int, y1: int, width: int, height: int, text: str, key: str, starting_value: int) -> None:
        super().__init__(x1, y1, width, height, text)
        self.key = key
        self.value = starting_value

        # 40 : gap-10 : 10: gap-20 : 20 - Generate biomes : (Yes) Toggle
        section1, section2 = int(x1 + ((width) // 10) * 4), int(x1 + ((width) // 10) * 5)
        self.name_label = Label(text, x1, y1, section1 - x1, height)
        self.toggled_label = Label("(Yes)" if self.value else "(No)", int(section1 + (0.1 * width)), y1, section2 - section1, height)
        self.toggle_button = Button(int(section2 + (0.2 * width)), y1, width - section2, height * 0.75, "Toggle", self.on_click)

        self.children: tuple[Label, Label, Button] = (self.name_label, self.toggled_label, self.toggle_button)

    def draw(self, window: pygame.surface.Surface) -> None:
        for child in (self.name_label, self.toggled_label, self.toggle_button):
            child.draw(window)  # type: ignore[attr-defined]

    def on_click(self, *_) -> Literal["Not None"]:  # type: ignore[no-untyped-def]
        self.value = not self.value
        self.toggled_label.text = "(Yes)" if self.value else "(No)"
        return "Not None"

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
        self.value = starting_value or (minimum + maximum) // 2
        self.minimum = minimum
        self.maximum = maximum
        self.big_step = big_step
        self.small_step = small_step
        self.middle = middle or (minimum + maximum) // 2

        middle_height = height // 2

        self.name_label = Label(text, x1, y1, width * 0.25, middle_height)
        self.value_label = Label(self.value, int(x1 + (width * 0.75)), y1, width * 0.25, middle_height)
        self.children: list[Label | Button] = [self.name_label, self.value_label]
        slot_size = width // 9
        for i, icon in enumerate(["<<", "<", "0", ">", ">>"]):
            button = Button(x1 + (slot_size * i * 2), y1 + middle_height, slot_size, middle_height, icon, self.on_click)
            self.children.append(button)

    def draw(self, window: pygame.surface.Surface) -> None:
        for child in self.children:
            child.draw(window)

    def on_click(self, window: pygame.surface.Surface, button: Button, *_: Any) -> Literal["Not None"]:
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
            print(f"Uh oh, IntegerSelector recieved something outside of it's normal, it recieved: {button.text}")
        self.value_label.text = str(self.value)
        return "Not None"

    def intersected(self, x: int, y: int) -> Label | Button | None:  # type: ignore[return]
        if super().intersected(x, y):
            for button in self.children[2:]:
                if button.intersected(x, y):
                    return button

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

    def draw(self, window: pygame.surface.Surface) -> None:
        percent_in = self.value / (self.maximum + self.minimum)
        width_in = percent_in * self.width
        self.slider_button.draw(window)
        pygame.draw.rect(window, (80, 80, 80), rect=(self.x1 + width_in, self.y1 - (int(self.height / 1.3)), self.width // 20, self.height * 2))

    def intersected(self, x, y) -> Button | None:  # type: ignore[no-untyped-def, return]
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

    def draw(self, window: pygame.surface.Surface) -> None:
        self.value_label.text = str(self.slider_element.value)

        self.name_label.draw(window)
        self.value_label.draw(window)
        self.slider_element.draw(window)


pygame.font.init()
BACK_BUTTON = Button(0, 0, 64, 64, "<", lambda *_: go_back())

# ================================================================================================================================


def handle_collisions(window: pygame.surface.Surface, mouse_x: int, mouse_y: int, elements: list[Button | IconButton]) -> None | Any:  # type: ignore[return]
    for element in [x for x in elements if hasattr(x, "on_click")]:
        clicked_button = element.intersected(mouse_x, mouse_y)
        if clicked_button:
            result = clicked_button.on_click(window, clicked_button, mouse_x, mouse_y)  # type: ignore[attr-defined]
            return result


def handle_menu(window: pygame.surface.Surface, title: str, elements: list[Button | IconButton | SliderRow]) -> Element:

    title_font_size = font_size_controller(title, 0, window.get_width(), 0, window.get_height() // 5)

    while True:
        window.fill((0, 0, 0))
        centered_text(window, title_font_size, title, (255, 255, 255), window.get_width() // 2, 80)

        for element in elements:
            element.draw(window)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                go_back()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
                x, y = pygame.mouse.get_pos()
                result = handle_collisions(window, x, y, elements)  # type: ignore[arg-type]
                if result is not None:
                    return result    # type: ignore[no-any-return]
