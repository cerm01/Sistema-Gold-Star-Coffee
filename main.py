import sys
import xmlrpc.client
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QLabel, QGroupBox, 
                             QTabWidget, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QListWidget, QAbstractItemView, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

class GoldStarApp(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- CONFIGURACIÓN DE ODOO ---
        self.url = "https://multiservicios-especializados.odoo.com"
        self.db = "multiservicios-especializados"
        self.username = "carlos.efrain.rosas.medina@gmail.com"
        self.api_key = "33924b5d46d4196877c5fcea4d0cb8a325491b7e"
        
        self.uid = None
        self.models = None
        self.diccionario_empresas = {}

        self.initUI()
        self.conectar_odoo_automatico()

    def apply_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        widget.setGraphicsEffect(shadow)

    def initUI(self):
        self.setWindowTitle('GoldStar Coffee - Client Management')
        self.showMaximized() 
        # Fondo general más suave
        self.setStyleSheet("""
            QWidget { background-color: #f8f9fa; font-family: 'Segoe UI', Arial; }
            QGroupBox { 
                border: 1px solid #e0e0e0; 
                border-radius: 12px; 
                margin-top: 20px; 
                background-color: white; 
                font-weight: bold; 
                font-size: 15px;
                color: #444;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; }
        """) 

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 30, 40, 40)

        # Header elegante
        header = QLabel("Sistema de Gestión de Clientes")
        header.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header.setStyleSheet("color: #1a1a1a; margin-bottom: 10px;")
        layout_principal.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: transparent; }
            QTabBar::tab { 
                background: #e9ecef; padding: 12px 40px; 
                font-weight: bold; font-size: 13px; border-top-left-radius: 8px; border-top-right-radius: 8px;
                color: #666; margin-right: 4px;
            }
            QTabBar::tab:selected { background: white; color: #0078d4; }
        """)

        self.tabs.addTab(self.create_tab_busqueda(), "🔍 BÚSQUEDA Y LISTADO")
        layout_principal.addWidget(self.tabs)

    def create_tab_busqueda(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 20, 10, 10)

        # --- PANEL DE CONTROL (FILTROS) ---
        filter_card = QGroupBox("Panel de Control")
        self.apply_shadow(filter_card)
        
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(20, 25, 20, 25)
        filter_layout.setSpacing(30)

        # Selector de Compañías
        empresa_container = QVBoxLayout()
        lbl_empresa = QLabel("🏢 Compañías")
        lbl_empresa.setStyleSheet("font-weight: bold; color: #555;")
        self.listado_empresas = QListWidget()
        self.listado_empresas.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.listado_empresas.setFixedHeight(120)
        self.listado_empresas.setStyleSheet("""
            QListWidget { 
                border: 1px solid #ddd; border-radius: 8px; background: #fff; padding: 5px; 
            }
            QListWidget::item { padding: 8px; border-radius: 4px; }
            QListWidget::item:selected { background-color: #e7f3ff; color: #0078d4; }
        """)
        empresa_container.addWidget(lbl_empresa)
        empresa_container.addWidget(self.listado_empresas)

        # Buscador Central
        busqueda_container = QVBoxLayout()
        lbl_search = QLabel("🔎 Búsqueda Rápida")
        lbl_search.setStyleSheet("font-weight: bold; color: #555;")
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Nombre, Email o Teléfono...")
        self.input_search.setFixedHeight(45)
        self.input_search.setStyleSheet("""
            QLineEdit { 
                padding: 0 15px; border: 2px solid #eee; border-radius: 10px; 
                background: #fdfdfd; font-size: 14px;
            }
            QLineEdit:focus { border: 2px solid #0078d4; background: white; }
        """)
        busqueda_container.addWidget(lbl_search)
        busqueda_container.addWidget(self.input_search)
        busqueda_container.addStretch()

        # Botones de Acción
        botones_container = QVBoxLayout()
        botones_container.addSpacing(25) # Alineación con los inputs
        
        self.btn_search = QPushButton("BUSCAR")
        self.btn_search.setFixedHeight(45)
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search.setStyleSheet(self.get_button_style("#0078d4", "#005a9e"))
        self.btn_search.clicked.connect(self.ejecutar_busqueda)

        self.btn_clear = QPushButton("LIMPIAR")
        self.btn_clear.setFixedHeight(45)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet(self.get_button_style("#6c757d", "#495057"))
        self.btn_clear.clicked.connect(self.limpiar_busqueda)
        
        botones_container.addWidget(self.btn_search)
        botones_container.addWidget(self.btn_clear)

        filter_layout.addLayout(empresa_container, stretch=3)
        filter_layout.addLayout(busqueda_container, stretch=4)
        filter_layout.addLayout(botones_container, stretch=2)
        filter_card.setLayout(filter_layout)
        
        layout.addWidget(filter_card)

        # --- TABLA DE RESULTADOS ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Email", "Teléfono", "Ciudad", "Empresa"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { 
                background-color: white; border: 1px solid #e0e0e0; border-radius: 12px; 
                gridline-color: #f0f0f0; alternate-background-color: #fafafa;
            }
            QHeaderView::section { 
                background-color: #f8f9fa; padding: 12px; border: none;
                border-bottom: 2px solid #eee; font-weight: bold; color: #444;
            }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f0f0f0; color: #333; }
            QTableWidget::item:selected { background-color: #e7f3ff; color: #000; }
        """)
        
        layout.addSpacing(20)
        layout.addWidget(self.table)
        return widget

    def get_button_style(self, color, hover_color):
        return f"""
            QPushButton {{
                background-color: {color}; color: white; border-radius: 10px;
                font-weight: bold; font-size: 13px; border: none;
            }}
            QPushButton:hover {{ background-color: {hover_color}; }}
            QPushButton:pressed {{ background-color: {color}; margin-top: 2px; }}
        """

    # --- LÓGICA DE ODOO ---
    def conectar_odoo_automatico(self):
        try:
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            uid = common.authenticate(self.db, self.username, self.api_key, {})
            if uid:
                self.uid = uid
                self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
                empresas = self.models.execute_kw(self.db, self.uid, self.api_key, 'res.company', 'search_read', [[]], {'fields': ['id', 'name']})
                self.listado_empresas.clear()
                self.diccionario_empresas = {e['name']: e['id'] for e in empresas}
                for nombre in self.diccionario_empresas.keys():
                    self.listado_empresas.addItem(nombre)
            else:
                QMessageBox.critical(self, "Error", "Fallo de autenticación automática.")
        except Exception as e:
            QMessageBox.critical(self, "Conexión", f"Error de red: {str(e)}")

    def ejecutar_busqueda(self):
        if not self.uid: return
        items = self.listado_empresas.selectedItems()
        ids = [self.diccionario_empresas[i.text()] for i in items]
        
        texto = self.input_search.text().strip()
        domain = [('company_id', 'in', ids)] if ids else [('company_id', '=', False)]

        if texto:
            domain += ['|', '|', ('name', 'ilike', texto), ('email', 'ilike', texto), ('phone', 'ilike', texto)]

        try:
            contactos = self.models.execute_kw(self.db, self.uid, self.api_key, 'res.partner', 'search_read', [domain], 
                                              {'fields': ['id', 'name', 'email', 'phone', 'city', 'company_id'], 'limit': 200})
            self.table.setRowCount(0)
            for i, c in enumerate(contactos):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(str(c.get('id'))))
                self.table.setItem(i, 1, QTableWidgetItem(str(c.get('name'))))
                self.table.setItem(i, 2, QTableWidgetItem(str(c.get('email') or "")))
                self.table.setItem(i, 3, QTableWidgetItem(str(c.get('phone') or "")))
                self.table.setItem(i, 4, QTableWidgetItem(str(c.get('city') or "")))
                comp = c.get('company_id')
                self.table.setItem(i, 5, QTableWidgetItem(comp[1] if isinstance(comp, list) else "Global"))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def limpiar_busqueda(self):
        self.input_search.clear()
        self.listado_empresas.clearSelection()
        self.table.setRowCount(0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GoldStarApp()
    window.show()
    sys.exit(app.exec())