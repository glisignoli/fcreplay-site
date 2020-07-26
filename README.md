# fcreplay-site

## Installation
You need to have pg_config available in your path:
 * Linux: Install postgres client
 * macOS: Install https://postgresapp.com/ or `brew install postgresql`
   * See: https://stackoverflow.com/questions/20170895/mac-virtualenv-pip-postgresql-error-pg-config-executable-not-found 
 * Google Cloud: No additial requirements

```console
python3 -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
```

## Running

```console
source ./venv/bin/activate
FLASK_APP=main.py flask run --host=127.0.0.1 --port=5000
```