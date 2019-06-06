from abc import *


class Crawler(metaclass=ABCMeta):
    """
    extends by platform
    e.g. Musinsa_Crawler
    """
    platform_url = None
    platform_name = None

    @abstractmethod
    def __init__(self, name, url):
        self.name = name
        self.url = url

    @abstractmethod
    def show_dev_info(self, date="2019.04.02"):
        '''
        show platform basic info
        :param date: String; the last update date for maintenance, should update manually
        :return: None
        '''
        print("Name: {name}\n" \
              "Url: {url}\n" \
              "Last update : {date}".format(name=self.name, url=self.url, date=date))

    @staticmethod
    def get_page_html(page_url):
        '''
        get html string of the page with bs4
        :param page_url: String
        :return: String
        '''
        import requests
        from bs4 import BeautifulSoup
        _page_source = requests.get(page_url)
        page_source = _page_source.text
        return BeautifulSoup(page_source, 'html.parser')


class PlatformCrawler(Crawler):
    @abstractmethod
    def __init__(self, name, url):
        super().__init__(name, url)

    @abstractmethod
    def show_dev_info(self, date="2019.04.02"):
        super(date)

    @abstractmethod
    def get_brand_list(self):
        '''
        get all brand urls of the platform
        :return: Dictionary; key: brand_name, value: brand_url
        '''
        pass

    @abstractmethod
    def get_product_url_list(self, length):
        '''
        get all product urls of the platform
        :return: Dictionary; key: product_name, value: product_url
        '''
        pass

    @abstractmethod
    def get_product_html(self, product_url):
        '''
        get product Html of given product_url
        :param product_url: String
        :return: String
        '''
        return self.get_page_html(product_url)

    @abstractmethod
    def get_review_html(self, product_url):
        '''
        get review Html of given product_url
        :param product_url: String
        :return: String
        '''
        return self.get_page_html(product_url)


class CommunityCrawler(Crawler):
    @abstractmethod
    def __init__(self, name, url):
        super(name, url)

    @abstractmethod
    def showDevInfo(self, date="2019.04.02"):
        super(date)

    @abstractmethod
    def getPageHtml(self, page_url):
        super(page_url)

    pass
