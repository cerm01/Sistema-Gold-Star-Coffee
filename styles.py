"""
styles.py
Estilos centralizados para toda la aplicación GoldStar.
"""

# Paleta de colores principal
PRIMARY       = "#0078d4"
PRIMARY_DARK  = "#005a9e"
PRIMARY_LIGHT = "#e7f3ff"
SUCCESS       = "#107c10"
SUCCESS_DARK  = "#0b5c0b"
DANGER        = "#d13438"
DANGER_DARK   = "#a4262c"
WARNING       = "#ca5010"
GRAY          = "#6c757d"
GRAY_DARK     = "#495057"
BG            = "#f0f2f5"
CARD_BG       = "#ffffff"
BORDER        = "#e0e0e0"
TEXT_MAIN     = "#1a1a2e"
TEXT_SUB      = "#555"

# Paleta sidebar
SIDEBAR_BG     = "#1e2a3b"
SIDEBAR_HOVER  = "#2d3f56"
SIDEBAR_ACTIVE = "#0d1f30"
SIDEBAR_TEXT   = "#8fa8c4"
SIDEBAR_WIDTH  = 230

APP_STYLE = f"""
    QWidget {{
        background-color: {BG};
        font-family: 'Segoe UI', 'SF Pro Display', Arial;
        color: {TEXT_MAIN};
    }}
    QGroupBox {{
        border: 1px solid {BORDER};
        border-radius: 12px;
        margin-top: 20px;
        background-color: {CARD_BG};
        font-weight: bold;
        font-size: 14px;
        color: #444;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 5px;
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        border: none;
        background: #e8eaed;
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: #c0c4cc;
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #9aa0ac;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
"""

NAV_BTN_STYLE = f"""
    QPushButton {{
        background: transparent;
        color: {SIDEBAR_TEXT};
        text-align: left;
        padding: 13px 22px;
        border: none;
        font-size: 13px;
        border-radius: 0;
        border-left: 3px solid transparent;
    }}
    QPushButton:hover {{
        background: {SIDEBAR_HOVER};
        color: #d0dce8;
    }}
    QPushButton:checked {{
        background: {SIDEBAR_ACTIVE};
        color: white;
        border-left: 3px solid {PRIMARY};
        font-weight: bold;
    }}
"""

TABLE_STYLE = f"""
    QTableWidget {{
        background-color: white;
        border: 1px solid {BORDER};
        border-radius: 12px;
        gridline-color: #f0f0f0;
        alternate-background-color: #fafafa;
        outline: none;
    }}
    QHeaderView::section {{
        background-color: #f8f9fa;
        padding: 12px;
        border: none;
        border-bottom: 2px solid #eee;
        font-weight: bold;
        color: #444;
        font-size: 12px;
    }}
    QTableWidget::item {{
        padding: 10px;
        border-bottom: 1px solid #f5f5f5;
        color: #333;
    }}
    QTableWidget::item:selected {{
        background-color: {PRIMARY_LIGHT};
        color: #000;
    }}
"""

INPUT_STYLE = f"""
    QLineEdit, QComboBox, QTextEdit {{
        padding: 8px 14px;
        border: 2px solid #eee;
        border-radius: 8px;
        background: #fdfdfd;
        font-size: 13px;
        color: {TEXT_MAIN};
    }}
    QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
        border: 2px solid {PRIMARY};
        background: white;
    }}
    QLineEdit:disabled, QComboBox:disabled, QTextEdit:disabled {{
        background: #f5f5f5;
        color: #999;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    QComboBox::down-arrow {{
        width: 12px;
        height: 12px;
    }}
    QComboBox QAbstractItemView {{
        border: 1px solid {BORDER};
        border-radius: 8px;
        background: white;
        selection-background-color: {PRIMARY_LIGHT};
        selection-color: {PRIMARY};
    }}
"""

LIST_STYLE = f"""
    QListWidget {{
        border: 1px solid #ddd;
        border-radius: 8px;
        background: #fff;
        padding: 5px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 8px;
        border-radius: 4px;
        font-size: 13px;
    }}
    QListWidget::item:selected {{
        background-color: {PRIMARY_LIGHT};
        color: {PRIMARY};
    }}
"""

LABEL_TITLE_STYLE   = f"font-size: 24px; font-weight: bold; color: {TEXT_MAIN};"
LABEL_SECTION_STYLE = f"font-weight: bold; color: {TEXT_SUB}; font-size: 12px;"


def btn_style(color: str, hover: str, text_color: str = "white") -> str:
    return f"""
        QPushButton {{
            background-color: {color};
            color: {text_color};
            border-radius: 8px;
            font-weight: bold;
            font-size: 12px;
            border: none;
            padding: 0 16px;
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {color}; margin-top: 1px; }}
        QPushButton:disabled {{ background-color: #ccc; color: #999; }}
    """


def stat_card_style(accent: str) -> str:
    return f"""
        QFrame {{
            background: white;
            border-radius: 14px;
            border-left: 5px solid {accent};
        }}
    """
