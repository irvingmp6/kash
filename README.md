# Kash
A command line utility to allow you to import your bank activity into a local database.

Kash first checks if the path provided is an existing database with the required table. 

If the path provided is not an existing database, Kash will create a new database using the path provided and create a table inside that new db.

Kash updates the table with csv's transactions. It does this by converting the CSV files into a dataframe. 

Kash will never insert duplicate transactions nor will it insert pending transactions. 

Kash only updates the table with "settled" transactions to keep the table nice and clean. This is done for two resons. One, because "pending" transactions look different from the "settled" ones, there is no programatic way to tell when a "pending" transaction has settled unless we used a complex algorithm. Even then, the pay off isn't worth it if we're already going to insert the transaction once it settles in a few days. Two, "pending" transactions are at risk of being reversed and ultimately disappear from the bank statement. Again, I can develop the algorithm to check if it disappeared but the pay off isn't worth it in this case either.

# Usage
## Installation
```
$ git clone https://github.com/irvingmp6/kash.git
$ pip install -e ./kash
```
## Test using sample data (Chase)
### kash import
Let's `import` transactions into the database using a sample chase CSV file. The following command will initialize the database and will show you the records that are ready to be imported.
```
$ kash import test.db kash/test_files/sample_chase_bank_activity.csv --account-alias "Chase" 
```
The following command actually imports the records. Notice the `--commit` at the end.
```
$ kash import test.db kash/test_files/sample_chase_bank_activity.csv --account-alias "Chase" --commit
```
The following command shows you that there is nothing new to import (because we already imported the data in the last command using `--commit`).
```
$ kash import test.db kash/test_files/sample_chase_bank_activity.csv --account-alias "Chase" 
```

## Test using sample data other than Chase
### kash import-raw
Let's use sample files that are different from Chase. The following commands make use of `import-raw` which requires the path to a config file as another parameter.
```
$ kash import-raw test.db kash/test_files/wells_fargo_config.ini kash/test_files/sample_wf_bank_activity.csv --account-alias "WF"
$ kash import-raw test.db kash/test_files/wells_fargo_config.ini kash/test_files/sample_wf_bank_activity.csv --account-alias "WF" --commit
$ kash import-raw test.db kash/test_files/wells_fargo_config.ini kash/test_files/sample_wf_bank_activity.csv --account-alias "WF"

```
## Some more test files
I included more test files using a different bank to show you how the configurations are different.
```
$ kash import-raw test.db kash/test_files/truist_config.ini kash/test_files/sample_truist_bank_activity.csv --account-alias "Truist"
$ kash import-raw test.db kash/test_files/truist_config.ini kash/test_files/sample_truist_bank_activity.csv --account-alias "Truist" --commit
$ kash import-raw test.db kash/test_files/truist_config.ini kash/test_files/sample_truist_bank_activity.csv --account-alias "Truist"
```

# How I use it
I created this app for myself as a way to query the transactions from a bank account that I strictly dedicate to paying bills. All of my payments are made through auto-pay, so I use this app/db to check if payments were in fact made instead of manually looking them up in a csv file.

I augment this with a separate system where I calculate a financial forecast that tells me how much money I will every day for the next few months to allow me to budget throughout the year and better plan for bigger expenses.
## Future plans
I have future plans to add this kind of functionality into the app. (Side note, I did have something like this built in but it required more dev work to get it to crunch the numbers and match my separate system. Because of that I ended up scrapping the idea unplugging all of the extra functionality from it.)
## Automation
I also have a wrapper python app that automatically (and securely) downloads the bank files which then calls Kash to make the inserts. That kind of automation is outside the scope of what Kash does, which is why I did not include that in Kash. I might create a separate repo to house that project. But for now, it's just sitting in my local machine.
## SQL
For now, I'm using SQLLiteStudio to query my transactions. 
Documentation: https://sqlitestudio.pl/
When I get more time, I'll add functionality to return records based through the terminal instead of using a different app.
