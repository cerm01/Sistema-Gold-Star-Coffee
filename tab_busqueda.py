"""
tab_busqueda.py
Pestaña de Búsqueda y Listado de Contactos con paginación.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QAbstractItemView, QFrame,
    QGraphicsDropShadowEffect, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

import styles
from workers import SearchWorker, DeletePartnerWorker


PAGE_SIZE = 50


class TabBusqueda(QWidget):

    def __init__(self, service, on_edit_requested):
        """
        service            : OdooService
        on_edit_requested  : callable(partner_id) — abre la pestaña de edición
        """
        super().__init__()
        self._service           = service
        self._on_edit_requested = on_edit_requested
        self._current_page      = 0
        self._total             = 0
        self._worker            = None
        self._companies_dict    = {}   # name -> id
        self._build_ui()

    # ------------------------------------------------------------------ #
    #  UI                                                                  #
    # ------------------------------------------------------------------ #
    def _apply_shadow(self, w):
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(18)
        sh.setXOffset(0)
        sh.setYOffset(4)
        sh.setColor(QColor(0, 0, 0, 25))
        w.setGraphicsEffect(sh)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(16)

        # ── Panel de filtros ────────────────────────────────────────────
        filter_card = QGroupBox("Panel de Control")
        self._apply_shadow(filter_card)
        fl = QHBoxLayout()
        fl.setContentsMargins(20, 25, 20, 25)
        fl.setSpacing(24)

        # Compañías
        ec = QVBoxLayout()
        lbl_e = QLabel("🏢  Compañías")
        lbl_e.setStyleSheet(styles.LABEL_SECTION_STYLE)
        self.list_companies = QListWidget()
        self.list_companies.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection
        )
        self.list_companies.setMinimumHeight(80)
        self.list_companies.setStyleSheet(styles.LIST_STYLE)
        ec.addWidget(lbl_e)
        ec.addWidget(self.list_companies)

        # Búsqueda
        sc = QVBoxLayout()
        lbl_s = QLabel("🔎  Búsqueda Rápida")
        lbl_s.setStyleSheet(styles.LABEL_SECTION_STYLE)
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Nombre, Email o Teléfono…")
        self.input_search.setMinimumHeight(40)
        self.input_search.setStyleSheet(styles.INPUT_STYLE)
        self.input_search.returnPressed.connect(self._search)
        sc.addWidget(lbl_s)
        sc.addWidget(self.input_search)
        sc.addStretch()

        # Botones
        bc = QVBoxLayout()
        bc.addSpacing(22)
        self.btn_search = QPushButton("🔍  BUSCAR")
        self.btn_search.setMinimumHeight(40)
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search.setStyleSheet(
            styles.btn_style(styles.PRIMARY, styles.PRIMARY_DARK)
        )
        self.btn_search.clicked.connect(self._search)

        self.btn_clear = QPushButton("✖  LIMPIAR")
        self.btn_clear.setMinimumHeight(40)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet(
            styles.btn_style(styles.GRAY, styles.GRAY_DARK)
        )
        self.btn_clear.clicked.connect(self._clear)

        bc.addWidget(self.btn_search)
        bc.addSpacing(8)
        bc.addWidget(self.btn_clear)

        fl.addLayout(ec, stretch=3)
        fl.addLayout(sc, stretch=4)
        fl.addLayout(bc, stretch=2)
        filter_card.setLayout(fl)
        layout.addWidget(filter_card)

        # ── Barra de estado + acciones de fila ─────────────────────────
        action_bar = QHBoxLayout()
        self.lbl_status = QLabel("Sin resultados")
        self.lbl_status.setStyleSheet("color: #777; font-size: 12px;")

        self.btn_edit = QPushButton("✏  EDITAR")
        self.btn_edit.setMinimumHeight(34)
        self.btn_edit.setEnabled(False)
        self.btn_edit.setStyleSheet(
            styles.btn_style(styles.WARNING, "#a0400d")
        )
        self.btn_edit.clicked.connect(self._edit_selected)

        self.btn_delete = QPushButton("🗑  ELIMINAR")
        self.btn_delete.setMinimumHeight(34)
        self.btn_delete.setEnabled(False)
        self.btn_delete.setStyleSheet(
            styles.btn_style(styles.DANGER, styles.DANGER_DARK)
        )
        self.btn_delete.clicked.connect(self._delete_selected)

        action_bar.addWidget(self.lbl_status)
        action_bar.addStretch()
        action_bar.addWidget(self.btn_edit)
        action_bar.addSpacing(8)
        action_bar.addWidget(self.btn_delete)
        layout.addLayout(action_bar)

        # ── Tabla ───────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Email", "Teléfono", "Ciudad", "Empresa"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.setStyleSheet(styles.TABLE_STYLE)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.doubleClicked.connect(self._edit_selected)
        layout.addWidget(self.table)

        # ── Paginación ──────────────────────────────────────────────────
        pag = QHBoxLayout()
        self.btn_prev = QPushButton("◀  Anterior")
        self.btn_prev.setMinimumHeight(32)
        self.btn_prev.setEnabled(False)
        self.btn_prev.setStyleSheet(
            styles.btn_style("#e9ecef", "#dee2e6", "#333")
        )
        self.btn_prev.clicked.connect(self._prev_page)

        self.lbl_page = QLabel("—")
        self.lbl_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_page.setStyleSheet("color: #555; font-size: 12px; min-width: 160px;")

        self.btn_next = QPushButton("Siguiente  ▶")
        self.btn_next.setMinimumHeight(32)
        self.btn_next.setEnabled(False)
        self.btn_next.setStyleSheet(
            styles.btn_style("#e9ecef", "#dee2e6", "#333")
        )
        self.btn_next.clicked.connect(self._next_page)

        pag.addStretch()
        pag.addWidget(self.btn_prev)
        pag.addWidget(self.lbl_page)
        pag.addWidget(self.btn_next)
        pag.addStretch()
        layout.addLayout(pag)

    # ------------------------------------------------------------------ #
    #  API pública                                                         #
    # ------------------------------------------------------------------ #
    def set_companies(self, companies: list[dict]):
        """Llamado desde la ventana principal tras conectar."""
        self._companies_dict = {c["name"]: c["id"] for c in companies}
        self.list_companies.clear()
        for name in self._companies_dict:
            self.list_companies.addItem(name)

    def refresh(self):
        """Re-ejecuta la búsqueda actual (útil tras crear/editar)."""
        self._run_search(self._current_page)

    # ------------------------------------------------------------------ #
    #  Slots privados                                                      #
    # ------------------------------------------------------------------ #
    def _search(self):
        self._current_page = 0
        self._run_search(0)

    def _clear(self):
        self.input_search.clear()
        self.list_companies.clearSelection()
        self.table.setRowCount(0)
        self._current_page = 0
        self._total = 0
        self._update_pagination()
        self.lbl_status.setText("Sin resultados")

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._run_search(self._current_page)

    def _next_page(self):
        max_page = max(0, (self._total - 1) // PAGE_SIZE)
        if self._current_page < max_page:
            self._current_page += 1
            self._run_search(self._current_page)

    def _run_search(self, page: int):
        if not self._service.is_connected:
            return
        ids = [
            self._companies_dict[i.text()]
            for i in self.list_companies.selectedItems()
        ]
        text = self.input_search.text().strip()
        offset = page * PAGE_SIZE

        self.btn_search.setEnabled(False)
        self.lbl_status.setText("Buscando…")

        self._worker = SearchWorker(
            self._service, ids if ids else None, text, offset, PAGE_SIZE
        )
        self._worker.success.connect(self._on_search_success)
        self._worker.error.connect(self._on_search_error)
        self._worker.start()

    def _on_search_success(self, results, total):
        self._total = total
        self.btn_search.setEnabled(True)
        self.table.setRowCount(0)

        for i, c in enumerate(results):
            self.table.insertRow(i)
            comp_name = c.company_id[1] if isinstance(c.company_id, list) else "—"
            for col, val in enumerate(
                [str(c.id), c.name, c.email, c.phone, c.city, comp_name]
            ):
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, c.id)
                self.table.setItem(i, col, item)

        self.lbl_status.setText(
            f"{total} resultado{'s' if total != 1 else ''} encontrado{'s' if total != 1 else ''} "
            f"— mostrando {len(results)} en esta página"
        )
        self._update_pagination()

    def _on_search_error(self, msg):
        self.btn_search.setEnabled(True)
        self.lbl_status.setText("Error en la búsqueda")
        QMessageBox.critical(self, "Error de búsqueda", msg)

    def _on_selection_changed(self):
        has = bool(self.table.selectedItems())
        self.btn_edit.setEnabled(has)
        self.btn_delete.setEnabled(has)

    def _edit_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        partner_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self._on_edit_requested(partner_id)

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        name = self.table.item(row, 1).text()
        partner_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        confirm = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Estás seguro de eliminar a <b>{name}</b>?<br>"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self._del_worker = DeletePartnerWorker(self._service, partner_id)
        self._del_worker.success.connect(self._on_delete_success)
        self._del_worker.error.connect(lambda e: QMessageBox.critical(self, "Error", e))
        self._del_worker.start()

    def _on_delete_success(self):
        QMessageBox.information(self, "Eliminado", "Contacto eliminado correctamente.")
        self.refresh()

    def _update_pagination(self):
        total_pages = max(1, -(-self._total // PAGE_SIZE))   # ceil division
        cur = self._current_page + 1
        self.lbl_page.setText(f"Página {cur} de {total_pages}")
        self.btn_prev.setEnabled(self._current_page > 0)
        self.btn_next.setEnabled(self._current_page < total_pages - 1)
