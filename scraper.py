import os
import argparse
import logging
from datetime import datetime, timedelta
from requests import get
import json
import concurrent.futures 

import pandas as pd 
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bs4 import BeautifulSoup


API_KEY = os.environ['NYT_API_TOKEN']
DBNAME = 'nytimes'
COLL_NAME = 'articles'
ENDPOINT = 'http://api.nytimes.com/svc/search/v2/articlesearch.json'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Scraper(object):

	def __init__(self, dbname, collection_name, endpoint):
		self.dbname = dbname
		self.columns = ['_id', 'web_url', 'pub_date', 'document_type', 
		'type_of_material', 'word_count', 'keywords', 'query', 'text']
		self.collection_name = collection_name
		self.endpoint = endpoint
			
	def scrape_and_save(self, params):
		'''
		extract data into pandas dataframe 
		@param params: parameters for API
		@return: None 
		'''
		response = get(self.endpoint, params=params)
		response_json = response.json()

		# page units are bucketed in 10
		# hits shows the total number of matched articles
		max_pages = int(response_json['response']['meta']['hits']/10) + 1

		# get metadata
		metadata = self.query_metadata(response_json['response'])
		df = pd.DataFrame(metadata, columns=self.columns[:-2])

		# get text data 
		web_urls = df['web_url'].values.tolist()
		page_contents_data = self.scrap_pages(web_urls)
		df[self.columns[-2]] = params['q']
		df[self.columns[-1]] = page_contents_data

		logger.debug('Extracted records example..')

		# write records into mongodb
		client = MongoClient()
		db = client[self.dbname]
		coll = db[self.collection_name]
		records = json.loads(df.T.to_json()).values()

		try:
			logger.info('Start writing records to DB ...')
			result = coll.insert_many(records)
			logger.info('Successfully done inserting records !')
			return result.acknowledged

		except PyMongoError as e:
			logger.error('Failed to insert records: ')
			logger.error(e)
			return False
	
	def query_metadata(self, response_json):
		'''
		query metadata
		@param response_json: api response in json format 
		@return: a list of metadata row 
		'''
		
		# columns to extract from the response 
		selected_column = self.columns[:-2]
		
		# extract the data
		metadata = []
		logger.info('Extract metadata using API')
		for row in response_json['docs']:
			selected_row = []
			for item in selected_column:
				selected_row.append(row[item])
			metadata.append(selected_row)
		logger.info('Finish extracting metadata')
		return metadata

	def scrap_pages(self, web_urls):
		'''
		:loop over response in order to get web_url of each object.
		@param web_urls: web url list to scrap article
		@return: a list of page contents string 
		'''
		n_contents = len(web_urls)
		page_contents = []

		logger.info('Scraping pages ... ')
		pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
		page_contents = pool.map(self.scrap_page, web_urls)
		page_contents = list(page_contents)
		# for i in range(n_contents):
		# 	body_text_str = self.scrap_page(web_urls[i])
		# 	page_contents.append(body_text_str)
		logger.info('Finish scraping pages')
		return page_contents 

	def scrap_page(self, web_url):
		'''
		: parse only body text from response json and return a list of body texts 
		@param web_url: web_url for parsing html 
		@return: a page contents text, string
		'''
		page = get(web_url)
		soup = BeautifulSoup(page.content, 'html.parser')

		# find body text contents 
		body_text = soup.find_all(class_='story-body-text')
		body_text_str = ' '.join([bd.get_text() for bd in body_text])

		return body_text_str



if __name__ == '__main__':
	# set cli argument interface 
	arg_parser = argparse.ArgumentParser(prog='', description='cli argument for scarping articles')
	arg_parser.add_argument('--from_date', dest='from_date', help='date query articles from', required=True)
	arg_parser.add_argument('--to_date', dest='to_date', help='date query articles to', required=True)
	arg_parser.add_argument('--keyword', dest='keyword', help='keyword to query articles', required=True)

	args = arg_parser.parse_args()
	params = {'begin_date':args.from_date, 'end_date':args.to_date, 'q':args.keyword}
	params['api-key'] = API_KEY

	# initialize a Scrpaer instance 
	scraper = Scraper(DBNAME, COLL_NAME, ENDPOINT)
	
	# write to mongo db
	scraper.scrape_and_save(params)




