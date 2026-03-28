"""
main.py
Punto de entrada de GoldStar Coffee – Client Management.

Arquitectura:
  main.py              → ventana principal + orquestación de pestañas
  odoo_service.py      → capa de acceso a datos (XML-RPC)
  workers.py           → QThread workers (operaciones asíncronas)
  styles.py            → constantes de estilos
  tab_busqueda.py      → pestaña Búsqueda y Listado
  tab_formulario.py    → pestaña Crear / Editar contacto
  tab_dashboard.py     → pestaña Dashboard con estadísticas
  .env                 → credenciales (NO se sube al repositorio)
"""
import sys
import os

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QMessageBox, QStatusBar,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

# Carga de variables de entorno desde .env (python-dotenv opcional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass   # Si no está instalado, usa variables de sistema directamente

import styles
from odoo_service import OdooService, OdooConfig
from workers import ConnectWorker
from tab_busqueda import TabBusqueda
from tab_formulario import TabFormulario
from tab_dashboard import TabDashboard


def _load_config() -> OdooConfig:
    """Lee las credenciales desde variables de entorno."""
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

class GoldStarApp(QWidget):
    # Índices de pestañas fijas
    TAB_SEARCH  = 0
    TAB_DASH    = 1
    TAB_CREATE  = 2
    TAB_EDIT    = 3   # dinámica (se crea al editar)

    def __init__(self):
        super().__init__()
        try:
            config = _load_config()
        except EnvironmentError as exc:
            QMessageBox.critical(None, "Configuración faltante", str(exc))
            sys.exit(1)

        self._service   = OdooService(config)
        self._companies = []
        self._connect_worker = None
        self._edit_tab_index = -1   # índice de pestaña de edición activa

        self._build_ui()
        self._connect_odoo()

    # ------------------------------------------------------------------ #
    #  UI principal                                                        #
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        self.setWindowTitle("GoldStar Coffee – Client Management")
        self.showMaximized()
        self.setStyleSheet(styles.APP_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(12)

        # ── Header ──────────────────────────────────────────────────────
        header_row = QHBoxLayout()

        logo_lbl = QLabel("☕")
        logo_lbl.setStyleSheet("font-size: 40px;")

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        app_title = QLabel("GoldStar Coffee")
        app_title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        app_title.setStyleSheet(f"color: {styles.TEXT_MAIN};")
        sub_title = QLabel("Sistema de Gestión de Clientes")
        sub_title.setStyleSheet("color: #777; font-size: 13px;")
        title_col.addWidget(app_title)
        title_col.addWidget(sub_title)

        self.lbl_status = QLabel("⏳ Conectando…")
        self.lbl_status.setStyleSheet(
            "color: #888; font-size: 12px; padding: 6px 14px;"
            "background: #f0f0f0; border-radius: 20px;"
        )

        header_row.addWidget(logo_lbl)
        header_row.addSpacing(10)
        header_row.addLayout(title_col)
        header_row.addStretch()
        header_row.addWidget(self.lbl_status)
        root.addLayout(header_row)

        # ── Tabs ────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(styles.TAB_STYLE)

        self._tab_search = TabBusqueda(self._service, self._open_edit_tab)
        self._tab_dash   = TabDashboard(self._service)

        self._tab_create = TabFormulario(self._service, self._companies)
        self._tab_create.saved.connect(self._on_create_saved)

        self.tabs.addTab(self._tab_search, "🔍  Búsqueda")
        self.tabs.addTab(self._tab_dash,   "📊  Dashboard")
        self.tabs.addTab(self._tab_create, "➕  Nuevo Contacto")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        root.addWidget(self.tabs)

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

        # Reconstruir la pestaña de creación con compañías cargadas
        self.tabs.removeTab(self.TAB_CREATE)
        self._tab_create = TabFormulario(self._service, self._companies)
        self._tab_create.saved.connect(self._on_create_saved)
        self.tabs.insertTab(self.TAB_CREATE, self._tab_create, "➕  Nuevo Contacto")

        self.lbl_status.setText(f"✅  Conectado  (UID {uid})")
        self.lbl_status.setStyleSheet(
            "color: #107c10; font-size: 12px; font-weight: bold;"
            "padding: 6px 14px; background: #e8f5e9; border-radius: 20px;"
        )

    def _on_connect_error(self, msg: str):
        self.lbl_status.setText("❌  Sin conexión")
        self.lbl_status.setStyleSheet(
            "color: #d13438; font-size: 12px; font-weight: bold;"
            "padding: 6px 14px; background: #fde8e8; border-radius: 20px;"
        )
        QMessageBox.critical(self, "Error de Conexión", msg)

    # ------------------------------------------------------------------ #
    #  Navegación entre pestañas                                           #
    # ------------------------------------------------------------------ #
    def _on_tab_changed(self, index: int):
        if index == self.TAB_DASH:
            self._tab_dash.load_stats()

    def _open_edit_tab(self, partner_id: int):
        """Abre (o reemplaza) la pestaña de edición con el partner dado."""
        # Cierra la pestaña de edición previa si existe
        if self._edit_tab_index >= 0:
            self.tabs.removeTab(self._edit_tab_index)
            self._edit_tab_index = -1

        edit_tab = TabFormulario(
            self._service, self._companies, partner_id=partner_id
        )
        edit_tab.saved.connect(self._on_edit_saved)

        idx = self.tabs.addTab(edit_tab, f"✏  Editar #{partner_id}")
        self._edit_tab_index = idx
        self.tabs.setCurrentIndex(idx)

    def _on_create_saved(self, partner_id: int):
        if partner_id > 0:
            self._tab_search.refresh()
            self.tabs.setCurrentIndex(self.TAB_SEARCH)
        # Si partner_id == -1 (cancelado) no hacemos nada

    def _on_edit_saved(self, partner_id: int):
        # Cierra la pestaña de edición y vuelve a búsqueda
        if self._edit_tab_index >= 0:
            self.tabs.removeTab(self._edit_tab_index)
            self._edit_tab_index = -1
        if partner_id > 0:
            self._tab_search.refresh()
        self.tabs.setCurrentIndex(self.TAB_SEARCH)


# ──────────────────────────────────────────────────────────────────────────── #

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GoldStarApp()
    window.show()
    sys.exit(app.exec())
