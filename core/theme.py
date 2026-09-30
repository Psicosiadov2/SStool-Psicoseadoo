"""Tema minimalista negro y gris de PsicoseadoSSTool."""

import tkinter.font as tkfont

# ---- Superficies ----
BG_APP = "#000000"
BG_TITLEBAR = "#030303"
BG_TOPNAV = "#050505"
BG_CONTENT = "#080808"
BG_ELEVATED = "#0a0a0a"

# ---- Tarjetas ----
CARD_BG = "#0d0d0d"
CARD_BG_HOVER = "#161616"
CARD_BORDER = "#212121"
CARD_BORDER_HOVER = "#747474"

# ---- Gris ----
RED_PRIMARY = "#8e8e8e"
RED_BRIGHT = "#aaaaaa"
RED_HOVER = "#717171"
RED_DARK = "#353535"
RED_MUTED = "#848484"
RED_DIM = "#535353"
RED_GHOST = "#111111"

# ---- Texto (tonos grises) ----
TEXT_HEADING = "#aaaaaa"
TEXT_PRIMARY = "#aaaaaa"
TEXT_SECONDARY = "#aaaaaa"
TEXT_MUTED = "#aaaaaa"
TEXT_FAINT = "#aaaaaa"
TEXT_ON_ACCENT = "#aaaaaa"

# ---- Bordes / separadores ----
BORDER_SUBTLE = "#212121"
BORDER_STRONG = "#3d3d3d"

# ---- Scrollbar ----
SCROLLBAR_TRACK = "#050505"
SCROLLBAR = "#353535"
SCROLLBAR_HOVER = "#717171"

# ---- Fuentes ----
FONT_FAMILY = "Segoe UI"
FONT_DISPLAY = "Segoe UI"
FONT_MONO = "Consolas"


def configure_fonts(root):
    """Usa la tipografia nativa de Windows 11 con fallbacks seguros."""
    global FONT_FAMILY, FONT_DISPLAY, FONT_MONO
    global FONT_BRAND, FONT_TITLE, FONT_EYEBROW, FONT_SECTION_TITLE
    global FONT_TAB, FONT_TAB_ACTIVE, FONT_CARD_TITLE, FONT_CARD_DESC
    global FONT_SMALL, FONT_BUTTON, FONT_WINDOW_CONTROL

    available = {family.casefold(): family for family in tkfont.families(root)}

    def choose(*families):
        for family in families:
            if family.casefold() in available:
                return available[family.casefold()]
        return families[-1]

    FONT_FAMILY = choose("Segoe UI", "DejaVu Sans", "Arial")
    FONT_DISPLAY = FONT_FAMILY
    FONT_MONO = choose("Cascadia Mono", "Consolas")

    FONT_BRAND = (FONT_DISPLAY, 15, "bold")
    FONT_TITLE = (FONT_DISPLAY, 18, "bold")
    FONT_EYEBROW = (FONT_FAMILY, 11, "bold")
    FONT_SECTION_TITLE = (FONT_DISPLAY, 14, "bold")
    FONT_TAB = (FONT_FAMILY, 12)
    FONT_TAB_ACTIVE = (FONT_FAMILY, 12, "bold")
    FONT_CARD_TITLE = (FONT_DISPLAY, 14, "bold")
    FONT_CARD_DESC = (FONT_FAMILY, 12)
    FONT_SMALL = (FONT_FAMILY, 11)
    FONT_BUTTON = (FONT_FAMILY, 11, "bold")
    FONT_WINDOW_CONTROL = (FONT_FAMILY, 12)


# Valores iniciales; App los recalcula contra las fuentes instaladas.
FONT_BRAND = (FONT_DISPLAY, 15, "bold")
FONT_TITLE = (FONT_DISPLAY, 18, "bold")
FONT_EYEBROW = (FONT_FAMILY, 11, "bold")
FONT_SECTION_TITLE = (FONT_DISPLAY, 14, "bold")
FONT_TAB = (FONT_FAMILY, 12)
FONT_TAB_ACTIVE = (FONT_FAMILY, 12, "bold")
FONT_CARD_TITLE = (FONT_DISPLAY, 14, "bold")
FONT_CARD_DESC = (FONT_FAMILY, 12)
FONT_SMALL = (FONT_FAMILY, 11)
FONT_BUTTON = (FONT_FAMILY, 11, "bold")
FONT_WINDOW_CONTROL = (FONT_FAMILY, 12)

# ---- Layout ----
TITLEBAR_HEIGHT = 54
TOPNAV_HEIGHT = 48
CONTENT_HEADER_HEIGHT = 58
CARD_HEIGHT = 182
CARD_PAD_X = 5
CARD_PAD_Y = 5
CORNER_RADIUS = 2
