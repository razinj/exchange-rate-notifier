# Exchange Rate Notifier

A script that fetches the exchange rates (USD base) from [OpenExchangeRate](https://openexchangerates.org) and sends an email notification if the rate is above the defined threshold for the given currencies.

The script runs on a defined scheduled GitHub Actions workflow (in theory, but it will never be on the exact defined timing, see [here](https://upptime.js.org/blog/2021/01/22/github-actions-schedule-not-working/) for more information).

> **Note:** This script was tested and used with Python 3.12

## Run

Install dependencies:

```shell
pip install -r requirements.txt
```

Run the script:

```shell
python script.py
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
