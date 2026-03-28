"""
tab_dashboard.py
Pestaña de Dashboard con estadísticas de la base de datos de Odoo.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGridLayout, QGraphicsDropShadowEffect,
    QScrollArea, QProgressBar,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor

import styles
from workers import StatsWorker


class StatCard(QFrame):
    def __init__(self, icon: str, label: str, value: str, accent: str):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-radius: 14px;
                border-left: 5px solid {accent};
            }}
        """)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(18)
        sh.setXOffset(0)
        sh.setYOffset(4)
        sh.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(sh)
        self.setMinimumHeight(110)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 36px;")
        icon_lbl.setFixedWidth(54)

        text_lay = QVBoxLayout()
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(
            f"font-size: 28px; font-weight: bold; color: {accent};"
        )
        label_lbl = QLabel(label)
        label_lbl.setStyleSheet("font-size: 12px; color: #777;")
        text_lay.addWidget(self.value_lbl)
        text_lay.addWidget(label_lbl)

        lay.addWidget(icon_lbl)
        lay.addLayout(text_lay)
        lay.addStretch()

    def update_value(self, v: str):
        self.value_lbl.setText(v)


class CoverageBar(QWidget):
    """Mini barra de progreso con etiqueta."""
    def __init__(self, label: str, accent: str):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        top = QHBoxLayout()
        self.lbl = QLabel(label)
        self.lbl.setStyleSheet("font-size: 12px; color: #555;")
        self.pct_lbl = QLabel("—")
        self.pct_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {accent};")
        top.addWidget(self.lbl)
        top.addStretch()
        top.addWidget(self.pct_lbl)
        self.bar = QProgressBar()
        self.bar.setFixedHeight(8)
        self.bar.setTextVisible(False)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                border: none; background: #f0f0f0; border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {accent}; border-radius: 4px;
            }}
        """)
        lay.addLayout(top)
        lay.addWidget(self.bar)

    def set_value(self, value: int, maximum: int):
        pct = round(value / maximum * 100) if maximum else 0
        self.bar.setMaximum(100)
        self.bar.setValue(pct)
        self.pct_lbl.setText(f"{pct}%  ({value:,})")


class TabDashboard(QWidget):

    def __init__(self, service):
        super().__init__()
        self._service = service
        self._worker  = None
        self._build_ui()

    # ------------------------------------------------------------------ #
    #  UI                                                                  #
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 20, 10, 20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("📊  Dashboard")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {styles.TEXT_MAIN};"
        )
        self.btn_refresh = QPushButton("🔄  Actualizar")
        self.btn_refresh.setFixedHeight(38)
        self.btn_refresh.setStyleSheet(
            styles.btn_style(styles.PRIMARY, styles.PRIMARY_DARK)
        )
        self.btn_refresh.clicked.connect(self.load_stats)
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(self.btn_refresh)
        layout.addLayout(hdr)

        # Stat cards (2×3 grid)
        grid = QGridLayout()
        grid.setSpacing(16)

        self.card_total    = StatCard("👥", "Total Contactos",    "—", styles.PRIMARY)
        self.card_empresas = StatCard("🏢", "Empresas",           "—", "#5c6bc0")
        self.card_personas = StatCard("🙋", "Personas",           "—", "#00897b")
        self.card_email    = StatCard("✉️",  "Con Email",          "—", styles.WARNING)
        self.card_phone    = StatCard("📞", "Con Teléfono",       "—", styles.SUCCESS)
        self.card_comp_num = StatCard("🏭", "Compañías Odoo",     "—", "#8e24aa")

        grid.addWidget(self.card_total,    0, 0)
        grid.addWidget(self.card_empresas, 0, 1)
        grid.addWidget(self.card_personas, 0, 2)
        grid.addWidget(self.card_email,    1, 0)
        grid.addWidget(self.card_phone,    1, 1)
        grid.addWidget(self.card_comp_num, 1, 2)
        layout.addLayout(grid)

        # Cobertura
        cov_box = QFrame()
        cov_box.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 14px;
                border: 1px solid #e0e0e0;
            }
        """)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(14)
        sh.setXOffset(0)
        sh.setYOffset(3)
        sh.setColor(QColor(0, 0, 0, 18))
        cov_box.setGraphicsEffect(sh)

        cov_lay = QVBoxLayout(cov_box)
        cov_lay.setContentsMargins(24, 20, 24, 20)
        cov_lay.setSpacing(14)

        cov_title = QLabel("📈  Cobertura de Datos")
        cov_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        cov_lay.addWidget(cov_title)

        self.bar_email  = CoverageBar("Contactos con Email",    styles.WARNING)
        self.bar_phone  = CoverageBar("Contactos con Teléfono", styles.SUCCESS)
        cov_lay.addWidget(self.bar_email)
        cov_lay.addWidget(self.bar_phone)
        layout.addWidget(cov_box)

        # Lista de compañías Odoo
        comp_box = QFrame()
        comp_box.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 14px;
                border: 1px solid #e0e0e0;
            }
        """)
        sh2 = QGraphicsDropShadowEffect()
        sh2.setBlurRadius(14)
        sh2.setXOffset(0)
        sh2.setYOffset(3)
        sh2.setColor(QColor(0, 0, 0, 18))
        comp_box.setGraphicsEffect(sh2)

        comp_lay = QVBoxLayout(comp_box)
        comp_lay.setContentsMargins(24, 20, 24, 20)
        comp_lay.setSpacing(10)
        comp_title = QLabel("🏭  Compañías Registradas en Odoo")
        comp_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        comp_lay.addWidget(comp_title)

        self.companies_container = QVBoxLayout()
        self.companies_container.setSpacing(6)
        comp_lay.addLayout(self.companies_container)
        layout.addWidget(comp_box)

        layout.addStretch()

    # ------------------------------------------------------------------ #
    #  Datos                                                               #
    # ------------------------------------------------------------------ #
    def load_stats(self):
        if not self._service.is_connected:
            return
        self.btn_refresh.setEnabled(False)
        self._worker = StatsWorker(self._service)
        self._worker.success.connect(self._on_stats)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_stats(self, stats: dict):
        self.btn_refresh.setEnabled(True)
        total = stats["total_partners"]

        self.card_total.update_value(f"{total:,}")
        self.card_empresas.update_value(f"{stats['total_companies_partners']:,}")
        self.card_personas.update_value(f"{stats['total_individuals']:,}")
        self.card_email.update_value(f"{stats['with_email']:,}")
        self.card_phone.update_value(f"{stats['with_phone']:,}")
        self.card_comp_num.update_value(str(stats["num_companies"]))

        self.bar_email.set_value(stats["with_email"], total)
        self.bar_phone.set_value(stats["with_phone"], total)

        # Lista de compañías
        while self.companies_container.count():
            item = self.companies_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for c in stats["companies"]:
            pill = QLabel(f"  🏭  {c['name']}  ")
            pill.setStyleSheet("""
                QLabel {
                    background: #f3f4f6;
                    border-radius: 8px;
                    padding: 6px 12px;
                    font-size: 12px;
                    color: #444;
                }
            """)
            self.companies_container.addWidget(pill)

    def _on_error(self, msg: str):
        self.btn_refresh.setEnabled(True)
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Error al cargar estadísticas", msg)
