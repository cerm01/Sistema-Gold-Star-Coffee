"""
tab_formulario.py
Pestaña reutilizable para Crear y Editar contactos.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QGroupBox,
    QComboBox, QCheckBox, QMessageBox, QFrame,
    QGraphicsDropShadowEffect, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

import styles
from workers import CreatePartnerWorker, UpdatePartnerWorker, LoadPartnerWorker


class TabFormulario(QWidget):
    """
    Funciona como "Crear contacto" (partner_id=None) o
    "Editar contacto" (partner_id= int).
    Emite saved(partner_id) cuando la operación tiene éxito.
    """
    saved = pyqtSignal(int)

    def __init__(self, service, companies: list[dict], partner_id: int | None = None):
        super().__init__()
        self._service    = service
        self._companies  = companies   # [{id, name}, ...]
        self._partner_id = partner_id
        self._worker     = None
        self._build_ui()
        if partner_id is not None:
            self._load_partner(partner_id)

    # ------------------------------------------------------------------ #
    #  UI                                                                  #
    # ------------------------------------------------------------------ #
    def _shadow(self, w):
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(18)
        sh.setXOffset(0)
        sh.setYOffset(4)
        sh.setColor(QColor(0, 0, 0, 20))
        w.setGraphicsEffect(sh)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 20, 10, 20)

        # Scroll para pantallas pequeñas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner_w = QWidget()
        layout = QVBoxLayout(inner_w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        scroll.setWidget(inner_w)
        outer.addWidget(scroll)

        mode = "Editar Contacto" if self._partner_id else "Nuevo Contacto"
        title = QLabel(f"{'✏' if self._partner_id else '➕'}  {mode}")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {styles.TEXT_MAIN}; margin-bottom: 4px;")
        layout.addWidget(title)

        # ── Card: Información básica ────────────────────────────────────
        card_basic = QGroupBox("Información Básica")
        self._shadow(card_basic)
        form_basic = QFormLayout()
        form_basic.setContentsMargins(20, 25, 20, 20)
        form_basic.setSpacing(14)
        form_basic.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.chk_is_company = QCheckBox("Es una empresa")
        self.chk_is_company.setStyleSheet("font-size: 13px;")

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Nombre completo o razón social")
        self.inp_name.setMinimumHeight(38)
        self.inp_name.setStyleSheet(styles.INPUT_STYLE)

        self.cmb_company = QComboBox()
        self.cmb_company.setMinimumHeight(38)
        self.cmb_company.setStyleSheet(styles.INPUT_STYLE)
        self.cmb_company.addItem("— Sin empresa —", None)
        for c in self._companies:
            self.cmb_company.addItem(c["name"], c["id"])

        form_basic.addRow("", self.chk_is_company)
        form_basic.addRow("Nombre *", self.inp_name)
        form_basic.addRow("Empresa",  self.cmb_company)
        card_basic.setLayout(form_basic)
        layout.addWidget(card_basic)

        # ── Card: Contacto ──────────────────────────────────────────────
        card_contact = QGroupBox("Datos de Contacto")
        self._shadow(card_contact)
        form_contact = QFormLayout()
        form_contact.setContentsMargins(20, 25, 20, 20)
        form_contact.setSpacing(14)
        form_contact.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.inp_email  = QLineEdit()
        self.inp_email.setPlaceholderText("correo@ejemplo.com")
        self.inp_email.setMinimumHeight(38)
        self.inp_email.setStyleSheet(styles.INPUT_STYLE)

        self.inp_phone  = QLineEdit()
        self.inp_phone.setPlaceholderText("+52 33 0000 0000")
        self.inp_phone.setMinimumHeight(38)
        self.inp_phone.setStyleSheet(styles.INPUT_STYLE)

        form_contact.addRow("Email",    self.inp_email)
        form_contact.addRow("Teléfono", self.inp_phone)
        card_contact.setLayout(form_contact)
        layout.addWidget(card_contact)

        # ── Card: Dirección ─────────────────────────────────────────────
        card_addr = QGroupBox("Dirección")
        self._shadow(card_addr)
        form_addr = QFormLayout()
        form_addr.setContentsMargins(20, 25, 20, 20)
        form_addr.setSpacing(14)
        form_addr.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.inp_street = QLineEdit()
        self.inp_street.setPlaceholderText("Calle y número")
        self.inp_street.setMinimumHeight(38)
        self.inp_street.setStyleSheet(styles.INPUT_STYLE)

        self.inp_city   = QLineEdit()
        self.inp_city.setPlaceholderText("Ciudad")
        self.inp_city.setMinimumHeight(38)
        self.inp_city.setStyleSheet(styles.INPUT_STYLE)

        form_addr.addRow("Calle",  self.inp_street)
        form_addr.addRow("Ciudad", self.inp_city)
        card_addr.setLayout(form_addr)
        layout.addWidget(card_addr)

        # ── Botones ─────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setMinimumHeight(40)
        self.btn_cancel.setMinimumWidth(120)
        self.btn_cancel.setStyleSheet(styles.btn_style(styles.GRAY, styles.GRAY_DARK))
        self.btn_cancel.clicked.connect(self._cancel)

        label = "💾  Actualizar" if self._partner_id else "✅  Crear Contacto"
        self.btn_save = QPushButton(label)
        self.btn_save.setMinimumHeight(40)
        self.btn_save.setMinimumWidth(160)
        self.btn_save.setStyleSheet(styles.btn_style(styles.SUCCESS, styles.SUCCESS_DARK))
        self.btn_save.clicked.connect(self._save)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addSpacing(10)
        btn_row.addWidget(self.btn_save)
        layout.addLayout(btn_row)
        layout.addStretch()

    # ------------------------------------------------------------------ #
    #  Lógica                                                              #
    # ------------------------------------------------------------------ #
    def _load_partner(self, partner_id: int):
        self.btn_save.setEnabled(False)
        self._load_worker = LoadPartnerWorker(self._service, partner_id)
        self._load_worker.success.connect(self._populate)
        self._load_worker.error.connect(
            lambda e: QMessageBox.critical(self, "Error", e)
        )
        self._load_worker.start()

    def _populate(self, partner):
        self.inp_name.setText(partner.name)
        self.inp_email.setText(partner.email)
        self.inp_phone.setText(partner.phone)
        self.inp_street.setText(partner.street)
        self.inp_city.setText(partner.city)
        self.chk_is_company.setChecked(partner.is_company)

        if isinstance(partner.company_id, list):
            cid = partner.company_id[0]
            idx = self.cmb_company.findData(cid)
            if idx >= 0:
                self.cmb_company.setCurrentIndex(idx)

        self.btn_save.setEnabled(True)

    def _build_data(self) -> dict | None:
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Campo requerido", "El nombre es obligatorio.")
            self.inp_name.setFocus()
            return None

        data: dict = {
            "name":       name,
            "email":      self.inp_email.text().strip()  or False,
            "phone":      self.inp_phone.text().strip()  or False,
            "street":     self.inp_street.text().strip() or False,
            "city":       self.inp_city.text().strip()   or False,
            "is_company": self.chk_is_company.isChecked(),
        }
        company_id = self.cmb_company.currentData()
        data["company_id"] = company_id if company_id else False
        return data

    def _save(self):
        data = self._build_data()
        if data is None:
            return
        self.btn_save.setEnabled(False)

        if self._partner_id:
            self._worker = UpdatePartnerWorker(
                self._service, self._partner_id, data
            )
            self._worker.success.connect(
                lambda: self._on_saved(self._partner_id)
            )
        else:
            self._worker = CreatePartnerWorker(self._service, data)
            self._worker.success.connect(self._on_saved)

        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_saved(self, partner_id: int):
        self.btn_save.setEnabled(True)
        verb = "actualizado" if self._partner_id else "creado"
        QMessageBox.information(
            self, "✅ Éxito", f"Contacto {verb} correctamente."
        )
        self.saved.emit(partner_id)

    def _on_error(self, msg: str):
        self.btn_save.setEnabled(True)
        QMessageBox.critical(self, "Error al guardar", msg)

    def _cancel(self):
        self.saved.emit(-1)   # -1 = cancelado
