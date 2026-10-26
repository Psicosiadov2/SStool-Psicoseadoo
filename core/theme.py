"""Tema glassmorphism azul oscuro de PsicoseadoSSTool."""

import tkinter.font as tkfont

# ---- Superficies ----
BG_APP = "#020814"
BG_TITLEBAR = "#071528"
BG_TOPNAV = "#08182c"
BG_CONTENT = "#061222"
BG_ELEVATED = "#0d2139"
BG_GLASS = "#091a2e"
BG_GLASS_HOVER = "#102d49"
BG_GLASS_LIGHT = "#143653"
BG_GLASS_DEEP = "#07111f"

# ---- Tarjetas ----
CARD_BG = "#0e233a"
CARD_BG_HOVER = "#153754"
CARD_BORDER = "#23496b"
CARD_BORDER_HOVER = "#65baff"

# ---- Acentos (se mantienen los nombres por compatibilidad interna) ----
RED_PRIMARY = "#319cff"
RED_BRIGHT = "#69c2ff"
RED_HOVER = "#2288df"
RED_DARK = "#123a60"
RED_MUTED = "#5996c2"
RED_DIM = "#28587c"
RED_GHOST = "#102a44"

# ---- Texto ----
TEXT_HEADING = "#f2f8ff"
TEXT_PRIMARY = "#d9ebfa"
TEXT_SECONDARY = "#aec9df"
TEXT_MUTED = "#7fa0bc"
TEXT_FAINT = "#5f809b"
TEXT_ON_ACCENT = "#ffffff"

# ---- Bordes / separadores ----
BORDER_SUBTLE = "#183650"
BORDER_STRONG = "#35678d"
BORDER_GLOW = "#3d9ee8"
GLASS_HIGHLIGHT = "#76caff"
GLASS_REFLECTION = "#2b6085"
AMBIENT_BLUE = "#0d3c68"

# ---- Scrollbar ----
SCROLLBAR_TRACK = "#071426"
SCROLLBAR = "#245478"
SCROLLBAR_HOVER = "#3c8ac0"

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

    FONT_BRAND = (FONT_DISPLAY, 14, "bold")
    FONT_TITLE = (FONT_DISPLAY, 17, "bold")
    FONT_EYEBROW = (FONT_FAMILY, 10, "bold")
    FONT_SECTION_TITLE = (FONT_DISPLAY, 13, "bold")
    FONT_TAB = (FONT_FAMILY, 11)
    FONT_TAB_ACTIVE = (FONT_FAMILY, 11, "bold")
    FONT_CARD_TITLE = (FONT_DISPLAY, 11, "bold")
    FONT_CARD_DESC = (FONT_FAMILY, 9)
    FONT_SMALL = (FONT_FAMILY, 9)
    FONT_BUTTON = (FONT_FAMILY, 10, "bold")
    FONT_WINDOW_CONTROL = (FONT_FAMILY, 12)


# Valores iniciales; App los recalcula contra las fuentes instaladas.
FONT_BRAND = (FONT_DISPLAY, 14, "bold")
FONT_TITLE = (FONT_DISPLAY, 17, "bold")
FONT_EYEBROW = (FONT_FAMILY, 10, "bold")
FONT_SECTION_TITLE = (FONT_DISPLAY, 13, "bold")
FONT_TAB = (FONT_FAMILY, 11)
FONT_TAB_ACTIVE = (FONT_FAMILY, 11, "bold")
FONT_CARD_TITLE = (FONT_DISPLAY, 11, "bold")
FONT_CARD_DESC = (FONT_FAMILY, 9)
FONT_SMALL = (FONT_FAMILY, 9)
FONT_BUTTON = (FONT_FAMILY, 10, "bold")
FONT_WINDOW_CONTROL = (FONT_FAMILY, 12)

# ---- Layout ----
TITLEBAR_HEIGHT = 46
TOPNAV_HEIGHT = 46
CONTENT_HEADER_HEIGHT = 50
CARD_HEIGHT = 112
CARD_PAD_X = 6
CARD_PAD_Y = 6
CORNER_RADIUS = 9
SHELL_RADIUS = 16
