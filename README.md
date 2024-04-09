# Kash
This utility imports Chase account activity (CSV files) into a local database.

Kash first checks if the path provided is an existing database with the required table. 

If the path provided is not an existing database, Kash will create a new database using the path provided and create a table inside that new db.

Kash updates the table with csv's transactions. It does this by converting the CSV files into a dataframe. 

Kash will never insert duplicate transactions nor will it insert pending transactions. 

Kash only updates the table with "settled" or "purchased" transactions to prevent to keep the table nice and clean. This is because pending transactions look different from settled ones.  

# How I use it
I created this app for myself as a way to query the transactions from a bank account that I strictly dedicate to paying bills. All of my payments are made through auto-pay, so I use this app/db to check if payments were in fact made instead of manually looking them up in a csv file.

I augment this with a separate system where I calculate a financial forecast that tells me how much money I will every day for the next few months to allow me to budget throughout the year and better plan for bigger expenses.
## Future plans
I have future plans to add this kind of functionality into the app. (Side note, I did have something like this built in but it required more dev work to get it to crunch the numbers and match my separate system. Because of that I ended up scrapping the idea unplugging all of the extra functionality from it.)
## Automation
I also have a wrapper python app that automatically (and securely) downloads the bank files which then calls Kash to make the inserts. That kind of automation is outside the scope of what Kash does, which is why I did not include that in Kash. I might create a separate repo to house that project. But for now, it's just sitting in my local machine.
## SQL
For now, I'm using SQLLiteStudio to query my transactions. When I get more time, I'll add functionality to return records based through the terminal instead of using a different app.