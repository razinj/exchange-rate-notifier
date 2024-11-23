# Exchange Rate Notifier

A script that fetches the exchange rates (USD base) from [OpenExchangeRate](https://openexchangerates.org) and sends an email notification if the rate is above the defined threshold for the given currencies.

The script runs on a defined scheduled GitHub Actions workflow (in theory, but it will never be on the exact defined timing, see [here](https://upptime.js.org/blog/2021/01/22/github-actions-schedule-not-working/) for more information).

> **Note:** This script was tested and used with Python 3.12

## Setup

### For local usage

1. Sign up at OpenExchangeRate to get an APP ID (free plan is enough).
2. Create a `.env` file based on the sample.
3. Run the script as specified below in `Run` step.

### For GitHub Actions

1. Sign up at OpenExchangeRate to get an APP ID (free plan is enough).
2. Create a GitHub Actions repository secret named `ENV_FILE_CONTENT` and populate it with the same content as in the sample file (`.env.sample`).
3. Create a GitHub Actions repository secret named `THRESHOLD_RATE` and populate it (only reason why this is separate from the above secret is because it changes quite frequently, you don't have to grab all the other values to adjust the threshold).
4. Either run manually or wait until scheduled time.

## Run

Setup and install dependencies:

```shell
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the script:

```shell
python src/script.py
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
