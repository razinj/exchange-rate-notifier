# Exchange Rate Notifier

A script that fetches exchange rates from one or more providers and sends a notification when the aggregated rate is above a defined threshold.

Currently supported providers:

- [OpenExchangeRates](https://openexchangerates.org)
- [ExchangeRate-API](https://www.exchangerate-api.com/docs/pair-conversion-requests)
- [currencyapi](https://currencyapi.com/docs/latest#latest-currency-exchange-data)
- [apilayer exchangeratesapi](https://docs.apilayer.com/exchangeratesapi/docs/exchange-rates-api-v-1-0-0#/default/getLatestRates)
- [fawazahmed0 exchange-api](https://github.com/fawazahmed0/exchange-api)
- Bank Al-Maghrib (`CoursBBE` and `CoursVirement` endpoints)

For multi-source mode, the script always collects per-source `details` and computes an aggregated rate using:

- `median` (recommended default)
- `mean`

The script runs on a defined scheduled GitHub Actions workflow (in theory, but it will never be on the exact defined timing, see [here](https://upptime.js.org/blog/2021/01/22/github-actions-schedule-not-working/) for more information).

> **Note:** This script was tested and used with Python 3.12

## Setup

### For local usage

1. Create a `.env` file based on `.env.sample`.
2. Configure at least one provider in `RATE_SOURCES`.
3. Add required credentials for each selected provider:
   - `openexchangerates` -> `OER_APP_ID`
   - `exchangerate_api` -> `EXCHANGERATE_API_KEY`
   - `currencyapi` -> `CURRENCYAPI_API_KEY`
   - `apilayer_exchangeratesapi` -> `APILAYER_EXCHANGERATESAPI_ACCESS_KEY`
   - `fawazahmed0_exchange_api` -> no API key required (optional `FAWAZAHMED0_CURRENCY_API_DATE`)
   - `bank_al_maghrib` -> `BAM_SUBSCRIPTION_KEY`
4. Run the script as specified below in `Run` step.

### For GitHub Actions

1. Create a GitHub Actions repository secret named `ENV_FILE_CONTENT` and populate it with the same content as your local `.env`.
2. Create a GitHub Actions repository variable named `THRESHOLD_RATE` (kept separate because it changes more frequently).
3. Either run manually or wait until scheduled time.

## Configuration

Core settings:

- `BASE_CURRENCY`
- `QUOTE_CURRENCY`
- `THRESHOLD_RATE`
- `RATE_SOURCES` (comma separated)
- `AGGREGATION_METHOD` (`median`, `mean`)
- `MIN_SUCCESSFUL_SOURCES` (default `1`)
- `HTTP_TIMEOUT_SECONDS`, `HTTP_MAX_RETRIES`, `HTTP_BACKOFF_BASE_SECONDS`, `HTTP_BACKOFF_MAX_SECONDS`
- `NOTIFY_ON_AGGREGATION_FAILURE` (`true` recommended)

Provider-specific settings:

- OpenExchangeRates: `OER_APP_ID`
- ExchangeRate-API: `EXCHANGERATE_API_KEY`
- currencyapi: `CURRENCYAPI_API_KEY`
- apilayer exchangeratesapi: `APILAYER_EXCHANGERATESAPI_ACCESS_KEY`
- fawazahmed0 exchange-api: optional `FAWAZAHMED0_CURRENCY_API_DATE` (`latest` by default)
- Bank Al-Maghrib: `BAM_SUBSCRIPTION_KEY`, optional `BAM_ENDPOINT` (`CoursBBE` by default)

Reliability recommendations:

- `HTTP_TIMEOUT_SECONDS=12`
- `HTTP_MAX_RETRIES=2`
- `HTTP_BACKOFF_BASE_SECONDS=0.5`
- `HTTP_BACKOFF_MAX_SECONDS=4`
- `NOTIFY_ON_AGGREGATION_FAILURE=true`

Example configuration:

```shell
BASE_CURRENCY=EUR
QUOTE_CURRENCY=MAD
THRESHOLD_RATE=10.30
RATE_SOURCES=openexchangerates,exchangerate_api,currencyapi,apilayer_exchangeratesapi,fawazahmed0_exchange_api,bank_al_maghrib
AGGREGATION_METHOD=median
MIN_SUCCESSFUL_SOURCES=1
HTTP_TIMEOUT_SECONDS=12
HTTP_MAX_RETRIES=2
HTTP_BACKOFF_BASE_SECONDS=0.5
HTTP_BACKOFF_MAX_SECONDS=4
NOTIFY_ON_AGGREGATION_FAILURE=true
OER_APP_ID=your_openexchangerates_app_id
EXCHANGERATE_API_KEY=your_exchangerate_api_key
CURRENCYAPI_API_KEY=your_currencyapi_key
APILAYER_EXCHANGERATESAPI_ACCESS_KEY=your_apilayer_exchangeratesapi_key
FAWAZAHMED0_CURRENCY_API_DATE=latest
BAM_SUBSCRIPTION_KEY=your_bank_al_maghrib_key
BAM_ENDPOINT=CoursBBE
```

## Add a New Provider

Use `src/rates/providers/template.py` as a starting point.

1. Copy it to `src/rates/providers/<provider_name>.py`.
2. Rename `TemplateProvider` and set `source_name`.
3. Implement request/auth and map response fields to `rate` and optional metadata.
4. Export it from `src/rates/providers/__init__.py`.
5. Register it in `AVAILABLE_PROVIDERS` inside `src/rates/service.py`.
6. Add any required env vars to `.env.sample` and tests under `tests/test_rates/providers/`.

## Run

Install dependencies:

```shell
poetry install
```

Run the script:

```shell
make run
```

## Development

Format:

```shell
make format
```

Lint:

```shell
make lint
```
