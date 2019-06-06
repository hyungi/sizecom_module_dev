import requests, urllib.request, os
from crawler.crawler_interface import PlatformCrawler
from restapp.models import *
import logging


class MusinsaCrawler(PlatformCrawler):
    logger = logging.getLogger('Musinsa')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    def get_product_html(self, product_url):
        pass

    def get_review_html(self, product_url):
        pass

    def __init__(self, name='Musinsa', url='https://store.musinsa.com'):
        super().__init__(name, url)
        self.category = ""
        self.sub_category = ""
        self.product_name = ""
        self.size_info = {}
        self.product_url = ""
        self.product_description = ""
        self.img_url_list = []
        self.brand_name = ""
        self.product_no = ""
        self.brand_list = []
        self.size_standard = ""
        self.debug_mode = True

    def show_dev_info(self, date="2019.04.02"):
        return "category: " + self.category + ", sub_category: " + self.sub_category + \
               ", product_name: " + self.product_name + ", product_url: " + self.product_url + \
               ", size_info: " + str(self.size_info) + ", brand_name: " + self.brand_name + \
               ", product_no: " + self.product_no

    def update_brand_list(self):
        # 1. 브랜드 list 를 먼저 긁어온다
        # 브랜드 list 를 긁어온뒤, db 에서 브랜드 list 를 또한 가져와서 비교 한다음 없는 친구만 update 하기
        # 2. 완성한 브랜드 리스트를 바탕으로 해당 브랜드별 상세  페이지를 얻어낸다. 품절 옵션 추가.
        # https://store.musinsa.com/app/brand/goods_list/{brandname}?brand_code={brandname}&page=1&ex_soldout=Y
        _brand_list_url = self.url + '/app/contents/brandshop'

        _crawled_brand_dict = {}
        try:
            _brand_detail_url_list = self.get_page_html(_brand_list_url).find_all('li', attrs={'class': 'brand_li'})

            for brand_detail in _brand_detail_url_list:
                _crawled_brand_dict.update(
                    {brand_detail.find('a').get_text(strip=True): self.url + brand_detail.find('a', href=True)['href']}
                )

            _crawled_brand_set = set([brand_detail.find('a').get_text(strip=True) for brand_detail in _brand_detail_url_list])
            _current_brand_set = set(BrandInfo.objects.values_list('brand_name', flat=True))
            _new_brand_list = list(_crawled_brand_set.difference(_current_brand_set))
            self.logger.info('number of new_brand_list: ' + str(len(_new_brand_list)))
        except Exception as e:
            self.logger.debug('in update_brand_list - make _new_brand_list')
            self.logger.debug(e.args)
        try:
            for brand_name in _new_brand_list:
                _brand_name = brand_name
                _brand_url = _crawled_brand_dict.get(brand_name)
                self.logger.info('new_brand_info: ' + _brand_name + ', ' + _brand_url)
                # 바로 생성하는 케이스 > 인스턴스 만들고 save하는 것으로 변경
                BrandInfo.objects.create(brand_name=_brand_name, brand_url=_brand_url)
        except Exception as e:
            self.logger.debug('in update_brand_list - update BrandInfo')
            self.logger.debug(e.args)

    def get_brand_list(self):
        if self.debug_mode is True:
            self.update_brand_list()
        # 위 코드는 디버깅 할때 flow를 간단히 하기 위해 삽입한 코드 임
        # 2. update 된 brand_info 정보를 바탕으로 크롤링할 brand_list 를 작성함
        return BrandInfo.objects.values_list('brand_name', 'brand_url')

    def get_product_url_list(self, length):
        # 3. 업데이트 된 self.brand_list를 바탕으로 해당 브랜드별 상세 페이지를 얻어낸다. 품절 옵션 추가.
        # https://store.musinsa.com/app/brand/goods_list/{brand_name}?brand_code={brand_name}&page=1&ex_soldout=Y
        self.brand_list = self.get_brand_list()
        if self.debug_mode is True and length != 0:
            # 디버깅을 위해서 0 이외의 수가 들어올 경우 brand_list 의 길이를 줄여준다
            self.brand_list = dict(self.brand_list[:length])
        else:
            self.brand_list = dict(self.brand_list)
        ret_list = []
        for brand_detail_dict in self.brand_list:
            brand_name = brand_detail_dict
            brand_url = self.brand_list.get(brand_name)
            try:
                page_list = self.get_page_html(brand_url).find('div', attrs={'class': 'pagination'}).find_all('a', attrs={'class': 'paging-btn'})
                self.logger.info('number of page list: ' + len(page_list))
            except Exception as e:
                self.logger.debug('in_get_product_url_list')
                self.logger.debug(brand_name)
                self.logger.debug(brand_url)

            total_list = [page.get_text(strip=True) for page in page_list][2:-2]
            if len(total_list) < 1:
                self.logger.info('brand has no products ' + brand_url)
            else:
                if self.debug_mode is True:
                    total_list = ['1']

                for list_num in total_list:
                    ret_list.append(brand_url + '?page=' + list_num + '&ex_soldout=Y')
        return ret_list
        # 브랜드 별로 1~end 페이지 까지 url 을 긁어옴

    def get_product_detail(self):
        if self.debug_mode is True:
            brand_main_url_list = self.get_product_url_list(30)
        self.logger.info('in_get_product_detail - number of url list ' + str(len(brand_main_url_list)))
        brand_info = None
        for brand_main_url in brand_main_url_list:
            link_bs = self.get_page_html(brand_main_url).select('#searchList > li > div.li_inner > div.list_img > a')
            self.logger.info('number of product pages: ' + str(len(link_bs)))
            for link in link_bs:
                self.product_url = self.url + link.get("href")
                self.size_info = self.get_size_table(self.product_url)
                self.product_name = self.get_page_html(self.product_url).find('span', class_="product_title").get_text(strip=True)
                try:
                    self.brand_name, self.category, self.sub_category = self.get_page_html(self.product_url).select(
                        "#page_product_detail > div.right_area.page_detail_product > "
                        "div.right_contents.section_product_summary > div.product_info > p > a"
                    )
                    self.brand_name = self.get_page_html(self.product_url).select_one(
                        '#product_order_info > div.explan_product.product_info_section > ul > li:nth-child(1) > p.product_article_contents > strong > a'
                    ).get_text(strip=True)
                    self.category = self.category.get_text(strip=True)
                    self.sub_category = self.sub_category.get_text(strip=True)
                    self.logger.info('in_get_product_detail - get category, sub_category success: ' + self.category + ', ' + self.sub_category)
                except Exception as e:
                    self.logger.info('in_get_product_detail - get category, sub_category fail')

                self.product_description = self.get_product_description()
                self.update_image(self.product_name)

                # DB접근 Product
                if brand_info is None:
                    brand_info = BrandInfo.objects.get(brand_name=self.brand_name)
                    self.logger.info('in_get_product_detail - get brand_info: ' + brand_info.brand_url)

                CategoryInfo.objects.get_or_create(category_name=self.category)

                try:
                    product_info = ProductInfo.objects.get(product_url=self.product_url)
                    self.logger.info('product_info already exist: ' + str(product_info.product_url))
                except ProductInfo.DoesNotExist as e:
                    self.logger.info('create new product info tuple' + self.product_url)
                    ProductInfo.objects.create(
                        product_name=self.product_name,
                        product_url=self.product_url,
                        product_description=self.product_description,
                        brand_info=brand_info
                    )

                if self.size_info is None:
                    self.logger.info('no size data')
                else:
                    self.save_size_table()
                self.product_url = self.product_url[self.product_url.find('//') + 2:]

    def get_product_description(self):
        ret_desc = self.get_page_html(self.product_url).select_one('#detail_view')
        if ret_desc is None:
            ret_desc = "There is no description"
        else:
            ret_desc = ret_desc.get_text(strip=True)
        return ret_desc
    '''
    def get_brand_name(self):
        ret_lis = self.get_page_html(self.product_url).select_one(
            '#product_order_info > div.explan_product.product_info_section > ul > '
            'li:nth-child(1) > p.product_article_contents > strong'
        ).get_text().split('/')
        for idx, lis in enumerate(ret_lis):
            ret_lis[idx] = lis.strip()
        return ret_lis
    '''
    def update_image(self, file_name):
        # db로 바로 업데이트 하자
        ret_list = []
        img_bs_list = self.get_page_html(self.product_url).select_one('#detail_view')
        if img_bs_list is None:
            self.img_url_list = ['no_img']
            return
        else:
            img_bs_list = img_bs_list.find_all('img')
        file_name = os.getcwd() + file_name
        for idx, img_bs in enumerate(img_bs_list):
            img_url = img_bs['src'][2:]
            ret_list.append(img_url[img_url.find('//') + 2:])
            # urllib.request.urlretrieve(img_url, file_name + '_' + str(idx) + '.jpg')
        self.img_url_list = ret_list

    def get_size_table(self, url):
        product_bs = self.get_page_html(url)
        size_table = product_bs.find('table', attrs={'class': 'table_th_grey'})
        if size_table is None:
            return size_table
        try:
            self.size_standard = size_table.select_one(
                'table.table_th_grey:nth-child(3) > thead:nth-child(1) > tr:nth-child(1) > th:nth-child(1)'
            ).get_text(strip=True)
        except AttributeError as e:
            # 사이즈 조견표가 아닌 정보가 들어있는 경우임
            self.logger.info('in_get_size_standard - get size standard fail')
            return None
        thead = size_table.find_all('th', attrs={'class': 'item_val'})
        try:
            headings = [th.get_text(strip=True) for th in thead]
            headings.insert(0, '사이즈')
            self.logger.info('get headings: ' + str(headings))
            # headings
            tbody = size_table.find('tbody').find_all('tr')[2:]
        except Exception as e:
            self.logger.info('get headings fail: ' + e.args)
        _list = []
        for tb in tbody:
            tb_list = tb.find_all()
            _list.append([tl.get_text() for tl in tb_list])
        ret_data = {}
        for idx, heading in enumerate(headings):
            data_list = [info[idx] for info in _list]
            ret_data[heading] = data_list
        return ret_data

    def save_size_table(self):
        """
        class 에 저장된 정보를 db 로 옮기는 작업
        """
        self.logger.info(str(self.size_info))
        product_info = ProductInfo.objects.get(product_url=self.product_url)
        _size_info = self.size_info
        size_unit_list = _size_info.pop('사이즈')
        size_part_list = list(_size_info.keys())
        _category_info_id = CategoryInfo.objects.get(category_name=self.category).category_info_id

        for size_part in size_part_list:
            size_part_info = SizePartInfo.objects.get_or_create(size_part_name=size_part, category_info_id=_category_info_id)
            print(size_part_info)
            size_value_partial_list = list(_size_info.get(size_part))
            for idx, size_value in enumerate(size_value_partial_list):
                self.logger.info(
                    'size_unit: ' + size_unit_list[idx] +
                    ', size_value: ' + size_value +
                    ', product_info: ' + str(product_info.product_name) +
                    ', size_part_info: ' + str(size_part_info)
                )
                try:
                    SizeInfo.objects.create(
                        size_unit=size_unit_list[idx], size_value=size_value,
                        product_info=product_info, size_part_info=size_part_info
                    )
                    self.logger.info('size_info create success')
                except Exception as e:
                    self.logger.info(str(e.args) + 'size_info create fail ' + self.product_url)

        '''
        if self.category == '상의' or self.category == '아우터':
            size_unit_list = self.size_info.get('사이즈')
            length_size_list = self.size_info.get('총장')
            chest_size_list = self.size_info.get('가슴단면')
            shoulder_size_list = self.size_info.get('어깨너비')
            sleeve_size_list = self.size_info.get('소매길이')

            if length_size_list is not None:
                for index, size_unit in enumerate(size_unit_list):
                    # _size_standard_id = SizeStandard.objects.get(size_standard_name=self.size_standard).id
                    # _size_part_info_id = SizePartInfo.objects.get(size_part_name="총장").id
                    # '총장' 이라고 직접 넣는 것이 아니라 총장에 해당하는 단어를 위에서 찾을 것
                    SizeInfo.objects.create(
                        size_unit=size_unit, size_value=length_size_list[index], product_info=product_info
                        # size_standard_id=_size_standard_id,
                        # size_part_info_id=_size_part_info_id
                    )
                    # Post > save 하는 방식으로
                    print(size_unit, '총장', length_size_list[index])
            if chest_size_list is not None:
                for index, size_unit in enumerate(size_unit_list):
                    # _size_standard_id = SizeStandard.objects.get(size_standard_name=self.size_standard).id
                    # _size_part_info_id = SizePartInfo.objects.get(size_part_name="가슴단면").id
                    # '총장' 이라고 직접 넣는 것이 아니라 총장에 해당하는 단어를 위에서 찾을 것
                    SizeInfo.objects.create(
                        size_unit=size_unit, size_value=chest_size_list[index], product_info=product_info
                        # size_standard_id=_size_standard_id,
                        # size_part_info_id=_size_part_info_id
                    )
                    # Post > save 하는 방식으로
                    print(size_unit, '가슴단면', chest_size_list[index])
            if shoulder_size_list is not None:
                for index, size_unit in enumerate(size_unit_list):
                    # _size_standard_id = SizeStandard.objects.get(size_standard_name=self.size_standard).id
                    # _size_part_info_id = SizePartInfo.objects.get(size_part_name="어깨너비").id
                    # '총장' 이라고 직접 넣는 것이 아니라 총장에 해당하는 단어를 위에서 찾을 것
                    SizeInfo.objects.create(
                        size_unit=size_unit, size_value=shoulder_size_list[index], product_info=product_info
                        # size_standard_id=_size_standard_id,
                        # size_part_info_id=_size_part_info_id
                    )
                    print(size_unit, '어깨너비', shoulder_size_list[index])
            if sleeve_size_list is not None:
                for index, size_unit in enumerate(size_unit_list):
                    # _size_standard_id = SizeStandard.objects.get(size_standard_name=self.size_standard).id
                    # _size_part_info_id = SizePartInfo.objects.get(size_part_name="소매길이").id
                    # '총장' 이라고 직접 넣는 것이 아니라 총장에 해당하는 단어를 위에서 찾을 것
                    SizeInfo.objects.create(
                        size_unit=size_unit, size_value=sleeve_size_list[index], product_info=product_info
                        # size_standard_id=_size_standard_id,
                        # size_part_info_id=_size_part_info_id
                    )
                    print(size_unit, '소매길이', sleeve_size_list[index])

        else:
            size_unit_list = self.size_info.get('사이즈')
            length_size_list = self.size_info.get('총장')
            waist_size_list = self.size_info.get('허리단면')
            thigh_size_list = self.size_info.get('허벅지단면')
            bottom_size_list = self.size_info.get('밑단단면')
            crotch_size_list = self.size_info.get('밑위')
            if length_size_list is not None:
                for index, size_unit in enumerate(size_unit_list):
                    print(size_unit, '총장 ', length_size_list[index])
            if waist_size_list is not None:
                for index, size_unit in enumerate(size_unit_list):
                    print(size_unit, '허리단면 ', waist_size_list[index])
            if thigh_size_list is not None:
                for index, size_unit in enumerate(size_unit_list):
                    print(size_unit, '허벅지단면 ', thigh_size_list[index])
            if bottom_size_list is not None:
                for index, size_unit in enumerate(size_unit_list):
                    print(size_unit, '밑단단면 ', bottom_size_list[index])
            if crotch_size_list is not None:
                for index, size_unit in enumerate(size_unit_list):
                    print(size_unit, '밑위 ', crotch_size_list[index])
        '''
'''
dict_sample = {
    'Top':
        {
            product_name:
                {
                    '사이즈': ['XS', 'S', 'M', 'L', 'XL']
                    ...
                }
        }

}
'''
