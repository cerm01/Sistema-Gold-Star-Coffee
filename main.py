"""
main.py
Punto de entrada de GoldStar Coffee – Client Management.

Arquitectura:
  main.py              → ventana principal + navegación lateral
  odoo_service.py      → capa de acceso a datos (XML-RPC)
  workers.py           → QThread workers (operaciones asíncronas)
  styles.py            → constantes de estilos
  tab_busqueda.py      → vista Búsqueda y Listado
  tab_formulario.py    → vista Crear / Editar contacto
  tab_dashboard.py     → vista Dashboard con estadísticas
  .env                 → credenciales (NO se sube al repositorio)
"""
import sys
import os

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStackedWidget, QMessageBox, QFrame, QPushButton,
    QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import styles
from odoo_service import OdooService, OdooConfig
from workers import ConnectWorker
from tab_busqueda import TabBusqueda
from tab_formulario import TabFormulario
from tab_dashboard import TabDashboard


def _load_config() -> OdooConfig:
    url      = os.getenv("ODOO_URL",      "")
    db       = os.getenv("ODOO_DB",       "")
    username = os.getenv("ODOO_USERNAME", "")
    api_key  = os.getenv("ODOO_API_KEY",  "")

    missing = [k for k, v in {
        "ODOO_URL": url, "ODOO_DB": db,
        "ODOO_USERNAME": username, "ODOO_API_KEY": api_key,
    }.items() if not v]

    if missing:
        raise EnvironmentError(
            f"Faltan variables de entorno: {', '.join(missing)}\n"
            "Crea un archivo .env con las claves necesarias."
        )
    return OdooConfig(url=url, db=db, username=username, api_key=api_key)


# ──────────────────────────────────────────────────────────────────────────── #

class _NavButton(QPushButton):
    """Botón de navegación lateral."""
    def __init__(self, icon: str, label: str):
        super().__init__(f"  {icon}    {label}")
        self.setCheckable(True)
        self.setMinimumHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(styles.NAV_BTN_STYLE)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class GoldStarApp(QWidget):
    PAGE_SEARCH = 0
    PAGE_DASH   = 1
    PAGE_CREATE = 2
    PAGE_EDIT   = 3   # dinámico

    def __init__(self):
        super().__init__()
        try:
            config = _load_config()
        except EnvironmentError as exc:
            QMessageBox.critical(None, "Configuración faltante", str(exc))
            sys.exit(1)

        self._service        = OdooService(config)
        self._companies      = []
        self._connect_worker = None

        self._build_ui()
        self._connect_odoo()

    # ------------------------------------------------------------------ #
    #  UI principal                                                        #
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        self.setWindowTitle("GoldStar Coffee – Gestión de Clientes")
        self.showMaximized()
        self.setStyleSheet(styles.APP_STYLE)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(styles.SIDEBAR_WIDTH)
        sidebar.setStyleSheet(f"background: {styles.SIDEBAR_BG};")
        sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        s_lay = QVBoxLayout(sidebar)
        s_lay.setContentsMargins(0, 0, 0, 0)
        s_lay.setSpacing(0)

        # Logo + nombre
        hdr = QWidget()
        hdr.setStyleSheet(f"background: {styles.SIDEBAR_BG};")
        hdr_lay = QVBoxLayout(hdr)
        hdr_lay.setContentsMargins(22, 28, 22, 22)
        hdr_lay.setSpacing(4)

        logo_row = QHBoxLayout()
        logo_row.setSpacing(10)
        logo_lbl = QLabel("☕")
        logo_lbl.setStyleSheet("font-size: 28px;")
        logo_lbl.setFixedWidth(36)
        app_name = QLabel("GoldStar Coffee")
        app_name.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        logo_row.addWidget(logo_lbl)
        logo_row.addWidget(app_name)
        logo_row.addStretch()

        sub_lbl = QLabel("Gestión de Clientes")
        sub_lbl.setStyleSheet(f"color: {styles.SIDEBAR_TEXT}; font-size: 11px; margin-left: 46px;")

        hdr_lay.addLayout(logo_row)
        hdr_lay.addWidget(sub_lbl)
        s_lay.addWidget(hdr)

        # Separador
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {styles.SIDEBAR_HOVER};")
        s_lay.addWidget(div)
        s_lay.addSpacing(10)

        # Sección "Menú"
        menu_lbl = QLabel("  MENÚ")
        menu_lbl.setStyleSheet(
            f"color: {styles.SIDEBAR_TEXT}; font-size: 10px; font-weight: bold;"
            "letter-spacing: 1px; padding: 4px 22px;"
        )
        s_lay.addWidget(menu_lbl)

        # Botones de navegación
        self._nav_search = _NavButton("🔍", "Búsqueda")
        self._nav_dash   = _NavButton("📊", "Dashboard")
        self._nav_create = _NavButton("➕", "Nuevo Contacto")
        self._nav_edit   = _NavButton("✏", "Editando…")
        self._nav_edit.setVisible(False)

        for btn in [self._nav_search, self._nav_dash, self._nav_create, self._nav_edit]:
            s_lay.addWidget(btn)

        self._nav_search.clicked.connect(lambda: self._goto(self.PAGE_SEARCH))
        self._nav_dash.clicked.connect(lambda: self._goto(self.PAGE_DASH))
        self._nav_create.clicked.connect(lambda: self._goto(self.PAGE_CREATE))
        self._nav_edit.clicked.connect(lambda: self._goto(self.PAGE_EDIT))

        s_lay.addStretch()

        # Separador inferior
        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet(f"background: {styles.SIDEBAR_HOVER};")
        s_lay.addWidget(div2)

        # Estado de conexión
        self.lbl_status = QLabel("⏳ Conectando…")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet(
            f"color: {styles.SIDEBAR_TEXT}; font-size: 11px; padding: 14px 22px;"
        )
        s_lay.addWidget(self.lbl_status)

        root.addWidget(sidebar)

        # ── Contenido (QStackedWidget) ───────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {styles.BG};")

        self._tab_search = TabBusqueda(self._service, self._open_edit_page)
        self._tab_dash   = TabDashboard(self._service)
        self._tab_create = TabFormulario(self._service, self._companies)
        self._tab_create.saved.connect(self._on_create_saved)

        self._stack.addWidget(self._tab_search)   # 0
        self._stack.addWidget(self._tab_dash)     # 1
        self._stack.addWidget(self._tab_create)   # 2
        # PAGE_EDIT (3) se agrega dinámicamente

        root.addWidget(self._stack, stretch=1)

        self._goto(self.PAGE_SEARCH)

    # ------------------------------------------------------------------ #
    #  Navegación                                                          #
    # ------------------------------------------------------------------ #
    def _goto(self, page: int):
        if page == self.PAGE_EDIT and self._stack.count() <= self.PAGE_EDIT:
            return
        self._stack.setCurrentIndex(page)

        self._nav_search.setChecked(page == self.PAGE_SEARCH)
        self._nav_dash.setChecked(page == self.PAGE_DASH)
        self._nav_create.setChecked(page == self.PAGE_CREATE)
        self._nav_edit.setChecked(page == self.PAGE_EDIT)

        if page == self.PAGE_DASH:
            self._tab_dash.load_stats()

    def _open_edit_page(self, partner_id: int):
        # Remueve página de edición previa si existe
        if self._stack.count() > self.PAGE_EDIT:
            old = self._stack.widget(self.PAGE_EDIT)
            self._stack.removeWidget(old)
            old.deleteLater()

        edit_form = TabFormulario(
            self._service, self._companies, partner_id=partner_id
        )
        edit_form.saved.connect(self._on_edit_saved)
        self._stack.insertWidget(self.PAGE_EDIT, edit_form)

        self._nav_edit.setText(f"  ✏    Editar #{partner_id}")
        self._nav_edit.setVisible(True)
        self._goto(self.PAGE_EDIT)

    # ------------------------------------------------------------------ #
    #  Conexión a Odoo                                                     #
    # ------------------------------------------------------------------ #
    def _connect_odoo(self):
        self._connect_worker = ConnectWorker(self._service)
        self._connect_worker.success.connect(self._on_connected)
        self._connect_worker.error.connect(self._on_connect_error)
        self._connect_worker.start()

    def _on_connected(self, uid: int, companies: list[dict]):
        self._companies = companies
        self._tab_search.set_companies(companies)

        # Reconstruir la página de creación con compañías cargadas
        self._stack.removeWidget(self._tab_create)
        self._tab_create.deleteLater()
        self._tab_create = TabFormulario(self._service, self._companies)
        self._tab_create.saved.connect(self._on_create_saved)
        self._stack.insertWidget(self.PAGE_CREATE, self._tab_create)

        self.lbl_status.setText(f"✅ Conectado\nUID {uid}")
        self.lbl_status.setStyleSheet(
            "color: #4caf50; font-size: 11px; padding: 14px 22px;"
        )

    def _on_connect_error(self, msg: str):
        self.lbl_status.setText("❌ Sin conexión")
        self.lbl_status.setStyleSheet(
            "color: #ef5350; font-size: 11px; padding: 14px 22px;"
        )
        QMessageBox.critical(self, "Error de Conexión", msg)

    # ------------------------------------------------------------------ #
    #  Callbacks de formulario                                             #
    # ------------------------------------------------------------------ #
    def _on_create_saved(self, partner_id: int):
        if partner_id > 0:
            self._tab_search.refresh()
        self._goto(self.PAGE_SEARCH)

    def _on_edit_saved(self, partner_id: int):
        if self._stack.count() > self.PAGE_EDIT:
            old = self._stack.widget(self.PAGE_EDIT)
            self._stack.removeWidget(old)
            old.deleteLater()
        self._nav_edit.setVisible(False)
        if partner_id > 0:
            self._tab_search.refresh()
        self._goto(self.PAGE_SEARCH)


# ──────────────────────────────────────────────────────────────────────────── #

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GoldStarApp()
    window.show()
    sys.exit(app.exec())
