Web Scraping New York Times Articles 
------------------------

## Scraper 
Scraper is a class for collecting article data from New York Times based on query keyword. First, this will fetch article meta data such as "page url", "keywords" and "type of material" through NYT [article search API](https://developer.nytimes.com/article_search_v2.json#/README). Next, starts scraping article contents by given page url. 

For analytical use, collected dataset will be stored in local mongoDB. It is true that this is not the best way to save long text in a single field, but one, body contents are not that large and two, it is implemented as personal academic use. So, you can modify the later part of this code to whatever storage that suits you.  

## Install 
#### Authentification 
Get your NYT API key from [here]() and set an environment variable as below.
```bash
# bash_profile or other profile script based on whatever shell you use   
vim ~/.bash_profile 
export NYT_API_TOKEN=your-api-key-here
source ~/.bash_profile 
```

#### Set up local mongo DB
You need to set up a mongoDB(community edition) in your local environment. If you're on mac, you can easily install with homebrew. 
```bash
brew update  
brew install mongodb
```
Now you can run mongoDB 
```bash
# start mongoDB  
mongod

# try this on another terminal to check if it listens  
mongo --host 127.0.0.1:27017 
```

Just press Ctrl+C in the terminal if you want to shut it down.


If you are not on mac, visit [here](https://docs.mongodb.com/manual/administration/install-community/)  


#### Install requirements 
```bash
pipenv install
```

## Usage 

#### For Scraping 
```bash
pipenv run python3 scraper.py --from_date='2017-01-02' --to_date='2017-04-01' --keyword='gun'
```

#### Getting data from mongoDB as a dataframe object 
```python
# get db client 
import pymongo 
from pymo
ngo import MongoClient
client = MongoClient()
db = client.nytimes
collection = db.articles

# make dataframe out of mongoDB
columns = []
df = pd.DataFrame(list(db.articles.find()), columns=columns)
``` 


