import os
import asyncio
import re
import aiohttp
from html import unescape
from urllib.parse import urljoin
from typing import List, Optional, Tuple
from .models import Invoice, SubscriberInfo

class EspinayDelfinScraper:
    def __init__(self, base_url: str, username: str, password: str, browser_ws_url: Optional[str] = None):
        """
        :param base_url: The base URL of the service.
        :param username: User's login name.
        :param password: User's password.
        :param browser_ws_url: Optional URL for Browserless (e.g., http://homeassistant.local:3000).
        """
        self.base_url = base_url
        self.username = username
        self.password = password
        self.browser_ws_url = browser_ws_url

    async def scrape_all(self) -> Tuple[SubscriberInfo, List[Invoice]]:
        """Performs the full scraping process."""
        if self.browser_ws_url:
            return await self._scrape_via_browserless()
        else:
            raise RuntimeError("Local Playwright is not supported in this version. Please provide a Browserless URL.")

    async def _scrape_via_browserless(
        self,
    ) -> Tuple[SubscriberInfo, List[Invoice]]:
        """
        Scrapes using the Browserless /function endpoint.
        """

        script = """
        export default async ({ page, context }) => {
            await page.goto(context.base_url, {
                waitUntil: "networkidle2"
            });

            await page.type(
                'input[name="uname"]',
                context.username
            );

            await page.type(
                'input[name="pass"]',
                context.password
            );

            await Promise.all([
                page.waitForNavigation({
                    waitUntil: "networkidle2"
                }),
                page.click('button[type="submit"]')
            ]);

            return await page.content();
        };
        """

        endpoint = self.browser_ws_url.rstrip("/") + "/function"

        async with aiohttp.ClientSession() as session:
            payload = {
                "code": script,
                "context": {
                    "username": self.username,
                    "password": self.password,
                    "base_url": self.base_url,
                },
            }

            async with session.post(endpoint, json=payload) as response:
                content = await response.text()

                if response.status != 200:
                    raise RuntimeError(
                        f"Browserless /function error "
                        f"(status {response.status}): {content}"
                    )

                return await self._parse_html_content(content)

    async def _parse_html_content(self, content: str) -> Tuple[SubscriberInfo, List[Invoice]]:
        """Parses the rendered HTML content."""
        subscriber_info = await self._extract_subscriber_info_from_html(content)
        invoices = await self._extract_invoices_from_html(content)
        return subscriber_info, invoices

    async def _extract_subscriber_info_from_html(self, content: str) -> SubscriberInfo:
        """Extracts subscriber details using regex on HTML content."""
        code_match = re.search(r"Código de Abonado:\s*(\d+)", content, re.IGNORECASE)
        addr_match = re.search(r"(?:Enderezo|Dirección|Address):\s*(.*?)<", content, re.IGNORECASE)
        
        subscriber_code = code_match.group(1) if code_match else "Unknown"
        address = addr_match.group(1).strip() if addr_match else "Unknown"
        
        return SubscriberInfo(subscriber_code=subscriber_code, address=address)

    async def _extract_invoices_from_html(
        self, content: str
    ) -> List[Invoice]:
        """Parses the invoice table from HTML content."""
        invoices = []

        # base_url = "https://clientes.espinaydelfin.com/index.php"

        row_pattern = re.compile(
            r"<tr[^>]*>(.*?)</tr>",
            re.DOTALL | re.IGNORECASE
        )
        cell_pattern = re.compile(
            r"<td[^>]*>(.*?)</td>",
            re.DOTALL | re.IGNORECASE
        )

        rows = row_pattern.findall(content)

        def clean_cell(cell: str) -> str:
            """Remove HTML tags and decode HTML entities."""
            return unescape(
                re.sub(r"<[^>]+>", "", cell)
            ).strip()

        def extract_href(cell: str) -> str | None:
            """Extract and normalize the first href from a cell."""
            match = re.search(
                r'href\s*=\s*["\']([^"\']+)["\']',
                cell,
                re.IGNORECASE,
            )

            if not match:
                return None

            href = unescape(match.group(1)).strip()

            return href

            # return urljoin(base_url, href) if href else None

        def parse_float(val: str) -> float:
            if not val:
                return 0.0

            cleaned = re.sub(r"[^\d,.]", "", val)

            # Formato español: 1.234,56 -> 1234.56
            cleaned = cleaned.replace(".", "").replace(",", ".")

            return float(cleaned)

        for row in rows:
            cells = cell_pattern.findall(row)

            if not cells:
                continue

            # Texto limpio SOLO para las columnas que son datos
            row_texts = [clean_cell(c) for c in cells]

            # Skip header rows
            if not row_texts or "N. DOC" in row_texts[0]:
                continue

            try:
                if len(cells) >= 8:
                    pay_url = extract_href(cells[6])
                    invoice_url = extract_href(cells[7])

                    invoice_data = {
                        "N. DOC": row_texts[0],
                        "Periodo": row_texts[1],
                        "Consumo m3": parse_float(row_texts[2]),
                        "Importe €": parse_float(row_texts[3]),
                        "Referencia": row_texts[4],
                        "Estado": row_texts[5],
                        "pay_url": pay_url,
                        "invoice_url": invoice_url,
                    }

                    invoices.append(Invoice(**invoice_data))

            except (IndexError, ValueError):
                continue

        return invoices
