from datetime import date
from pydantic import BaseModel, Field
from typing import Optional

class SubscriberInfo(BaseModel):
    subscriber_code: str
    address: str

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
