import scrapy
import csv
import time
from filmsscrapy.items import FilmsscrapyItem

def get_table(table):
    span = table.css('span')
    a_tags = span.css('a')
    if a_tags:
        text_list = a_tags.css('::text').getall()
        all_text = ', '.join(set(text_list))
    else:
        all_text = span.css('::text').get()
    return all_text

class MoviesSpider(scrapy.Spider):
    name = "movies"
    start_urls = ["https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту"]

    def parse(self, response):
        for selector in response.css('div#mw-pages li'):
            film_url = "https://ru.wikipedia.org/" + selector.css('a::attr(href)').get()
            yield response.follow(film_url, callback=self.parse_movie)
        
        next_page = response.xpath('//a[text()="Следующая страница"]/@href').get()
        if next_page:
            next_url = "https://ru.wikipedia.org/" + next_page
            yield response.follow(next_url, callback=self.parse)

    def parse_movie(self, response):
        item = FilmsscrapyItem()
        item['title'] = response.css('th::text').get()
        item['genre'] = get_table(response.css('tr:contains("Жанры"), tr:contains("Жанр")'))
        item['director'] = get_table(response.css('tr:contains("Режиссёры"), tr:contains("Режиссёр")'))
        item['country'] = get_table(response.css('tr:contains("Страна"), tr:contains("Страны")'))
        item['year'] = get_table(response.css('tr:contains("Год")'))
        item['rating'] = None
        
        imdb_link = response.css('tr:contains("IMDb") span a::attr(href)').get()
        time.sleep(1.5)
        
        if imdb_link:
            yield scrapy.Request(imdb_link, callback=self.parse_imdb_rating, meta={'item': item})
        else:
            yield item
    
    def parse_imdb_rating(self, response):
        item = response.meta['item']
        item['rating'] = response.css('div.sc-acdbf0f3-0 span.sc-bde20123-1::text').get()
        yield item

    def close(self, reason):
        with open('movies.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Title', 'Genre', 'Director', 'Country', 'Year', 'IMDB Rating']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in self.crawled_items:
                writer.writerow({
                    'Title': item['title'],
                    'Genre': item['genre'],
                    'Director': item['director'],
                    'Country': item['country'],
                    'Year': item['year'],
                    'IMDB Rating': item['rating']
                })