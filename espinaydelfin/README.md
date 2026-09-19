# Espina & Delfín Integration for Home Assistant

This integration allows you to automatically retrieve your invoices from the Espina & Delfín customer portal.

## Features

- **Automatic Scraping**: Retrieves invoice data (period, consumption, amount, status, etc.) from the provider's website.
- **Incremental Updates**: Only adds new invoices to your local storage, preventing duplicates.
- **Subscriber Info**: Captures your subscriber code and address.
- **Manual Trigger**: A service to run the extraction whenever you want.
- **Automatic Sync**: Scheduled to run automatically on the last day of every month.

## Configuration

The integration requires:
- **Username**
- **Password**
- **Base URL** (Optional, defaults to `https://clientes.espinaydelfin.com`)

## Services

- `espinaydelfin.sync_invoices`: Manually triggers the extraction process.
  - `overwrite`: If set to `true`, it will replace all existing stored data with the new data from the web.

## Requirements

- Internet access to reach the provider's portal.
- Home Assistant with Playwright capabilities (or handled by the integration's environment).
