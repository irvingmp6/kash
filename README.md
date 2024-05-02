# Kash
A CLI app that allows you to interact with your bank activity.

Kash helps you consolidate all your transaction history from multiple banks into a single database table.

Kash also allows you to pull specific records through stored queries on demand.

## Prerequisites
* python 3.8 or higher
* Some basic SQL knowledge (to set up your custom queries)

## Set Up and Installation
**Download** the repository
```
$ git clone git@github.com:irvingmp6/kash.git
```
### (Optional) Installing in a Python Virtual Environment
To avoid updating current packages on your current python set up, it's always good practice to isolate any new package dependencies with a virtual environment.

**Create** a new Python virtual environment. I'm calling mine `kashEnv`.
```
$ python -v venv kashEnv
```
**Activate** the virtual environment (for Windows users)
```
$ source kashEnv/Scripts/activate 
```
**Activate** the virtual environment (for MacOS or Linux users)
```
$ source kashEnv/bin/activate
```
### Installing the package
Once you have the code downloaded (and you created a virtual enviornment), you're ready to **install** Kash.
```
$ python -m pip install -e ./kash
```
## Usage
Kash allows you to import your bank activity into a database through one of two ways:
* `kash import` - used for importing Chase CSV files*
* `kash import-raw`used for importing non-Chase CSV files*

* Banks allow you to download your own transaction history from their website when you log into your account.
#### How to download your Chase transactions:
1. Login to your [Chase](https://secure.chase.com/web/auth/dashboard#/dashboard/index/index) account.
2. Choose a bank account.
3. Click on the download icon under Transactions. This will take you to a "Download account activity" page.
4. Leave the default settings: 
* **Account**: The account you selected
* **File type**: Spreadsheet (Excel, CSV)
* **Activity**: Current display, including filters
5. Click "Download"
#### How to download your transactions from other non-Chase banks
1. Login to your bank's website.
2. Select an account.
3. Look for a download transactions button and click on it.
4. Definte a date range (if prompted).
5. Download the transactions as a CSV file.
### Importing your transactions into a database
Kash automatically sets up a new SQLite database when you run `kash import` or `kash import-raw` for the first time.
### The `kash import` subcommand
To import Chase CSV files into a database, use the `kash import` subcommand. It expects two positional arguments:
1. The path to a database (.db) file. Kash will verify if the patch exists. If it doesn't, it will create a new database in the path provided. If one does exist, it will attemt to connect to it and check to see if it contains a table named `bank_activity` with the proper columns. If the connectin or check fails, the program will error out. 
2. The path to the Chase CSV file.
```
$ kash import /path/to/database.db /path/to/chase_bank_activity.csv
```
Kash will compare the incoming transactions against the transactions that exists in the database and print out a summary of all the new transactions.

Kash will commit the inserts if the --commit flag is passed:
```
$ kash import /path/to/database.db /path/to/chase_bank_activity.csv --commit
```
Don't worry if you accidentally commit the same file twice. Kash's duplicate checking prevents the same transactions from entering the system.
### The `kash import-raw` subcommand
To import non-Chase CSV files into a database, use the `kash import-raw` subcommand. It expects three positional arguments:
1. The path to a database (.db) file. Kash will verify if the patch exists. If it doesn't, it will create a new database in the path provided. If one does exist, it will attemt to connect to it and check to see if it contains a table named `bank_activity` with the proper columns. If the connectin or check fails, the program will error out. 
2. The path to a config file that maps out the columns the CSv file*
3. The path to the non-Chase CSV file.
```
$ kash import /path/to/database.db /path/to/bank_config.ini /path/to/other_non-chase_bank_activity.csv
```
Just like with the `kash import-raw`, Kash will compare the incoming transactions against the transactions that exists in the database and print out a summary of all the new transactions.

Similarly, Kash will only commit the inserts if the --commit flag is passed:
```
$ kash import /path/to/database.db /path/to/bank_config.ini /path/to/other_non-chase_bank_activity.csv --commit
```
*To learn about how to set up a config files to import non-Chase csv files, visit the documnetation which explains this in further detail.
### The `kash get` subcommand
Kash allows you to fetch specific results from stored queries using the `kash get` subcommand. It expects two positionsl arguments:
1. The path to a configuration file that contains all the stored queries and their aliases.* 
2. A space-delimited list of pre-defined aliases that have been mapped to SQL querues in the configuration file*
```
$ kash get /path/to/stored_queries.ini query_alias_1 query_alias_2 query_alias_3
```
*To learn about how to set up a config files to store queries and their aliases, visit the documnetation which explains this in further detail.