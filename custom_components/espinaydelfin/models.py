from datetime import date
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class SubscriberInfo(BaseModel):
    subscriber_code: str
    address: str

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

class Invoice(BaseModel):
    doc_number: str = Field(..., alias="N. DOC")
    period: str = Field(..., alias="Periodo")
    consumption_m3: float = Field(..., alias="Consumo m3")
    amount_euro: float = Field(..., alias="Importe €")
    reference: str = Field(..., alias="Referencia")
    status: str = Field(..., alias="Estado")
    pay_url: Optional[str] = Field(None, alias="Pagar")
    invoice_url: Optional[str] = Field(None, alias="Factura")

    class Config:
        populate_by_name = True

    def to_ha_dict(self) -> Dict[str, Any]:
        """Returns a dictionary with clean keys for Home Assistant attributes."""
        return {
            "doc_number": self.doc_number,
            "period": self.period,
            "consumption_m3": self.consumption_m3,
            "amount_euro": self.amount_euro,
            "reference": self.reference,
            "status": self.status,
            "pay_url": self.pay_url,
            "invoice_url": self.invoice_url,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dictionary using aliases, suitable for storage."""
        return self.model_dump(by_alias=True)
