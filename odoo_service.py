"""
odoo_service.py
Capa de acceso a datos para Odoo vía XML-RPC.
Toda la lógica de red está centralizada aquí; la UI no toca xmlrpc directamente.
"""
import xmlrpc.client
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OdooConfig:
    url: str
    db: str
    username: str
    api_key: str


@dataclass
class ContactResult:
    id: int
    name: str
    email: str
    phone: str
    city: str
    street: str
    company_id: Any       # [id, name] o False
    is_company: bool
    active: bool


class OdooServiceError(Exception):
    pass


class OdooService:
    """Encapsula todas las llamadas XML-RPC a Odoo."""

    def __init__(self, config: OdooConfig):
        self._config = config
        self._uid: int | None = None
        self._models = None

    # ------------------------------------------------------------------ #
    #  Autenticación                                                       #
    # ------------------------------------------------------------------ #
    def connect(self) -> int:
        """Autentica y devuelve el UID. Lanza OdooServiceError si falla."""
        try:
            common = xmlrpc.client.ServerProxy(
                f"{self._config.url}/xmlrpc/2/common", allow_none=True
            )
            uid = common.authenticate(
                self._config.db, self._config.username, self._config.api_key, {}
            )
            if not uid:
                raise OdooServiceError("Credenciales inválidas — autenticación fallida.")
            self._uid = uid
            self._models = xmlrpc.client.ServerProxy(
                f"{self._config.url}/xmlrpc/2/object", allow_none=True
            )
            return uid
        except OdooServiceError:
            raise
        except Exception as exc:
            raise OdooServiceError(f"Error de red al conectar: {exc}") from exc

    @property
    def is_connected(self) -> bool:
        return self._uid is not None

    def _require_connection(self):
        if not self.is_connected:
            raise OdooServiceError("No hay conexión activa con Odoo.")

    # ------------------------------------------------------------------ #
    #  Helpers internos                                                    #
    # ------------------------------------------------------------------ #
    def _execute(self, model: str, method: str, args: list, kwargs: dict) -> Any:
        self._require_connection()
        try:
            return self._models.execute_kw(
                self._config.db, self._uid, self._config.api_key,
                model, method, args, kwargs,
            )
        except Exception as exc:
            raise OdooServiceError(f"Error ejecutando {model}.{method}: {exc}") from exc

    # ------------------------------------------------------------------ #
    #  Compañías                                                           #
    # ------------------------------------------------------------------ #
    def get_companies(self) -> list[dict]:
        """Devuelve lista de {id, name} de todas las compañías."""
        return self._execute(
            "res.company", "search_read", [[]], {"fields": ["id", "name"]}
        )

    # ------------------------------------------------------------------ #
    #  Contactos / Partners                                                #
    # ------------------------------------------------------------------ #
    _PARTNER_FIELDS = [
        "id", "name", "email", "phone",
        "city", "street", "company_id", "is_company", "active",
    ]

    def search_partners(
        self,
        company_ids: list[int] | None = None,
        search_text: str = "",
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[ContactResult], int]:
        """
        Busca partners y devuelve (lista_de_resultados, total_count).
        """
        domain: list = []

        if company_ids:
            domain.append(("company_id", "in", company_ids))

        if search_text:
            domain += [
                "|", "|",
                ("name",  "ilike", search_text),
                ("email", "ilike", search_text),
                ("phone", "ilike", search_text),
            ]

        total = self._execute(
            "res.partner", "search_count", [domain], {}
        )
        raw = self._execute(
            "res.partner", "search_read", [domain],
            {"fields": self._PARTNER_FIELDS, "offset": offset, "limit": limit},
        )
        results = [self._map_partner(r) for r in raw]
        return results, total

    def get_partner(self, partner_id: int) -> ContactResult:
        raw = self._execute(
            "res.partner", "read", [[partner_id]], {"fields": self._PARTNER_FIELDS}
        )
        if not raw:
            raise OdooServiceError(f"Contacto {partner_id} no encontrado.")
        return self._map_partner(raw[0])

    def create_partner(self, data: dict) -> int:
        """Crea un partner y devuelve su nuevo ID."""
        return self._execute("res.partner", "create", [data], {})

    def update_partner(self, partner_id: int, data: dict) -> bool:
        return self._execute("res.partner", "write", [[partner_id], data], {})

    def delete_partner(self, partner_id: int) -> bool:
        return self._execute("res.partner", "unlink", [[partner_id]], {})

    # ------------------------------------------------------------------ #
    #  Estadísticas para Dashboard                                         #
    # ------------------------------------------------------------------ #
    def get_stats(self) -> dict:
        """Devuelve métricas básicas para el dashboard."""
        total_partners = self._execute("res.partner", "search_count", [[]], {})
        total_companies_partners = self._execute(
            "res.partner", "search_count", [[("is_company", "=", True)]], {}
        )
        total_individuals = self._execute(
            "res.partner", "search_count", [[("is_company", "=", False)]], {}
        )
        with_email = self._execute(
            "res.partner", "search_count",
            [[("email", "!=", False), ("email", "!=", "")]],
            {},
        )
        with_phone = self._execute(
            "res.partner", "search_count",
            [[("phone", "!=", False), ("phone", "!=", "")]],
            {},
        )
        companies = self.get_companies()

        return {
            "total_partners":           total_partners,
            "total_companies_partners": total_companies_partners,
            "total_individuals":        total_individuals,
            "with_email":               with_email,
            "with_phone":               with_phone,
            "num_companies":            len(companies),
            "companies":                companies,
        }

    # ------------------------------------------------------------------ #
    #  Mapper                                                              #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _map_partner(raw: dict) -> ContactResult:
        return ContactResult(
            id=raw["id"],
            name=raw.get("name") or "",
            email=raw.get("email") or "",
            phone=raw.get("phone") or "",
            city=raw.get("city") or "",
            street=raw.get("street") or "",
            company_id=raw.get("company_id"),
            is_company=raw.get("is_company", False),
            active=raw.get("active", True),
        )
