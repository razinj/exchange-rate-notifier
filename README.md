# Exchange Rate Notifier

A script that fetches the exchange rates (USD base) from [OpenExchangeRate](https://openexchangerates.org) and sends an email notification if the rate is above the defined threshold for the given currencies.

The script runs on a scheduled GitHub Actions workflow every 1h between 8-22 (in theory, but it will never be exactly one hour, see [here](https://upptime.js.org/blog/2021/01/22/github-actions-schedule-not-working/) for more information).

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
