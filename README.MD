# Autobuy

This script buy crypto following a yaml list and save the order in a excel file.
Work with binance spot only.

## Installation
require [Python 3+](https://nodejs.org/).

1) Install packages

```sh
cd <folder>
pip install -r requirements.txt
```

Start script

2) Create a .env file with the following form:

```
KEY='YOUR_API_KEY'
SECRET='YOUR_SECRET_KEY'
```

3) Modify the yaml file with your preference, sum of percentage must be egual to 1

4) Start the script with the following command:
```
python autobuy.py -c <your_yaml_config_file> -p <primary_asset> -a <amount_of_primary_asset_to_spend>
```
Primary asset must be one of : USDT;USDC;BUSD;BTC....

5) Results are displayed in the command line and save in a csv file
