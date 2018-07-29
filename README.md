# SQLite-View
A web interface to manage multiple SQLite databases.

# Installation
To install SQLite-View first clone this repository and move to that directory.

`$ git clone https://github.com/Jason2605/SQLite-View.git`

`$ cd SQLite-View`

Then in your favourite python virtual environment, install the requirements with pip.

`$ pip install -r requirements.txt`

# Running
To run SQLite-View.

`$ python3 runserver.py`

This will bind to 0.0.0.0:5000 by default, you can change this in runserver.py

**Note:** If you are running this for the first time, you will be prompted to enter a username and password on the command line, this is the account you log in with on the website.

# Features

- Manage multiple sqlite databases
- Export databases to an SQL file
- Delete tables within databases
- Add table indexes
- Add/rename/delete columns
- View table schema
- View table indexes
- View data
  * View it in tabular format
  * View it in JSON format
- Manipulate the data
  * Delete rows
  * Edit rows
  * Run user defined queries
- Users
  * Separate user accounts
  
# Screenshots

![](https://pyfilter.co.uk/static/images/sqlite-view/home.png)
![](https://pyfilter.co.uk/static/images/sqlite-view/tables.png)
![](https://pyfilter.co.uk/static/images/sqlite-view/schema.png)
![](https://pyfilter.co.uk/static/images/sqlite-view/data.png)
![](https://pyfilter.co.uk/static/images/sqlite-view/search.png)
![](https://pyfilter.co.uk/static/images/sqlite-view/json.png)
