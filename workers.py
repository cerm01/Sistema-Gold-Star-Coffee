"""
workers.py
QThread workers para ejecutar llamadas a Odoo sin bloquear la UI.
"""
from PyQt6.QtCore import QThread, pyqtSignal
from odoo_service import OdooService, OdooServiceError


class ConnectWorker(QThread):
    success = pyqtSignal(int, list)   # uid, companies
    error   = pyqtSignal(str)

    def __init__(self, service: OdooService):
        super().__init__()
        self._service = service

    def run(self):
        try:
            uid = self._service.connect()
            companies = self._service.get_companies()
            self.success.emit(uid, companies)
        except OdooServiceError as e:
            self.error.emit(str(e))


class SearchWorker(QThread):
    success = pyqtSignal(list, int)   # results, total
    error   = pyqtSignal(str)

    def __init__(self, service: OdooService, company_ids, text, offset, limit):
        super().__init__()
        self._service    = service
        self._company_ids = company_ids
        self._text       = text
        self._offset     = offset
        self._limit      = limit

    def run(self):
        try:
            results, total = self._service.search_partners(
                self._company_ids, self._text, self._offset, self._limit
            )
            self.success.emit(results, total)
        except OdooServiceError as e:
            self.error.emit(str(e))


class CreatePartnerWorker(QThread):
    success = pyqtSignal(int)   # new partner id
    error   = pyqtSignal(str)

    def __init__(self, service: OdooService, data: dict):
        super().__init__()
        self._service = service
        self._data    = data

    def run(self):
        try:
            new_id = self._service.create_partner(self._data)
            self.success.emit(new_id)
        except OdooServiceError as e:
            self.error.emit(str(e))


class UpdatePartnerWorker(QThread):
    success = pyqtSignal()
    error   = pyqtSignal(str)

    def __init__(self, service: OdooService, partner_id: int, data: dict):
        super().__init__()
        self._service    = service
        self._partner_id = partner_id
        self._data       = data

    def run(self):
        try:
            self._service.update_partner(self._partner_id, self._data)
            self.success.emit()
        except OdooServiceError as e:
            self.error.emit(str(e))


class DeletePartnerWorker(QThread):
    success = pyqtSignal()
    error   = pyqtSignal(str)

    def __init__(self, service: OdooService, partner_id: int):
        super().__init__()
        self._service    = service
        self._partner_id = partner_id

    def run(self):
        try:
            self._service.delete_partner(self._partner_id)
            self.success.emit()
        except OdooServiceError as e:
            self.error.emit(str(e))


class StatsWorker(QThread):
    success = pyqtSignal(dict)
    error   = pyqtSignal(str)

    def __init__(self, service: OdooService):
        super().__init__()
        self._service = service

    def run(self):
        try:
            stats = self._service.get_stats()
            self.success.emit(stats)
        except OdooServiceError as e:
            self.error.emit(str(e))


class LoadPartnerWorker(QThread):
    success = pyqtSignal(object)   # ContactResult
    error   = pyqtSignal(str)

    def __init__(self, service: OdooService, partner_id: int):
        super().__init__()
        self._service    = service
        self._partner_id = partner_id

    def run(self):
        try:
            partner = self._service.get_partner(self._partner_id)
            self.success.emit(partner)
        except OdooServiceError as e:
            self.error.emit(str(e))
