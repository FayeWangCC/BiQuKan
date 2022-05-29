import os
import threading
import time
import requests
import multiprocessing
from lxml import etree
from retrying import retry
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor


class Book(object):
	# 发送请求获取响应数据
	@retry(stop_max_attempt_number=3)
	def get_data(self, url=None, url_list=None):
		if url != None:
			# 发送请求获取响应
			resp = requests.get(url, headers=headers)
			time.sleep(0.2)
			# 设置响应编码
			resp.encoding = 'gbk'
			text = resp.text
			# 返回数据
			return text
		elif url_list != None:
			text_list = []
			for url_ in url_list:
				# 发送请求获取响应
				resp = requests.get(url_, headers=headers)
				time.sleep(0.2)
				# 设置响应编码
				resp.encoding = 'gbk'
				text = resp.text
				# 将数据组成列表返回
				text_list.append(text)
			# 返回数据
			return text_list

	# 格式化内容, 去除无用符号
	def format_string(self, string):
		new_string = str(string).replace("['", "").replace("']", "").replace("', ' \\xa0\\xa0", "\n").replace(
			"', '", "").replace("\\xa0", "").replace(" ", "").replace("笔趣看www.biqukan.la，最快更新最新章节！", "").replace("r/>",
		                                                                                                         "")
		return new_string

	# 子进程：解析并保存数据
	def parse_book_data(self, book_text):
		# 解析为HTML
		dom = etree.HTML(book_text)
		# 获取书籍信息
		book_name = str(dom.xpath('//h1[@class="bookTitle"]/text()')[0]).strip()
		book_author = str(dom.xpath('//h1[@class="bookTitle"]/small/a/text()')[0])
		book_classify = str(dom.xpath('//ol[@class="breadcrumb"]/li[2]/a/text()')[0])
		# 调用格式化函数,将简介内容格式化
		book_describe = self.format_string(dom.xpath('//p[@id="bookIntro"]/text()'))
		# 设置保存路径
		save_path = f'./小说/{book_name}/'
		# 判断目录是否存在
		if os.path.exists(save_path):
			# 存在就直接保存
			with open(f'{save_path}简介.txt', 'w') as f:
				f.write(f'书名:{book_name}\n作者:{book_author}\n分类:{book_classify}\n简介:\n{book_describe}\n\n')
		else:
			# 不存在就创建目录并保存
			os.makedirs(save_path)
			with open(f'{save_path}简介.txt', 'w') as f:
				f.write(f'书名:{book_name}\n作者:{book_author}\n分类:{book_classify}\n简介:\n{book_describe}\n\n')
		print(f'下载完成\t\t{book_name} 简介')

	# 获取页面信息
	def get_page_data(self, book_text):
		# 解析为HTML
		dom = etree.HTML(book_text)
		# 获取章节目录页面列表对象
		el_page = dom.xpath('//select[@class="form-control"]/option')
		page_url_list = []
		# 如果没有页码数据说明该书籍的章数在60以内，那么就只需要拿到当前页面的链接进行解析
		if len(el_page):
			for page in el_page:
				page_value = page.xpath('./@value')[0]
				# 获取页面url
				page_url = 'https://www.biqukan.la/' + str(page_value)
				page_url_list.append(page_url)
		else:
			page_url = dom.xpath('/html/head/link[1]/@href')[0]
			page_url_list.append(page_url)
		return page_url_list

	# 向页面发送请求获取页面章节数据
	def parse_section_data(self, page_text):
		dom = etree.HTML(page_text)
		# 获取章节列表对象
		el_section = dom.xpath('//dl[@class="panel-body panel-chapterlist"]/dd/a')
		# 获取页面链接
		page_url = dom.xpath('/html/head/link[1]/@href')[0]
		for section in el_section:
			section_url = str(page_url) + str(section.xpath('./@href')[0])
			# 多进程方式：创建子进程
			# get_content_process = multiprocessing.Process(target=book.get_content,)
			# 进程池方式：创建进程池
			# pool = Pool(50)
			# pool.apply_async(book.get_content, args=(book, section_url))
			# pool.close()
			# pool.join()
			# 多线程方式:创建并开启子线程
			get_content_thread = threading.Thread(target=book.get_content, args=(book, section_url))
			get_content_thread.start()

	# 线程池方式:创建线程池
	# pool = ThreadPoolExecutor(max_workers=8)
	# pool.submit(book.get_content, book, section_url)
	# pool.shutdown()

	# 获取章节内容的子进程
	def get_content(self, book, section_url):
		content = ''
		while True:
			section_text = book.get_data(section_url)
			dom = etree.HTML(section_text)
			el_content = dom.xpath('//div[@id="htmlContent"]/text()')
			book_name = str(dom.xpath('/html/body/div[2]/ol/li[3]/a/text()')[0]).strip()
			section_title = str(dom.xpath('//h1[@class="readTitle"]/text()')[0]).strip().replace("*", "")
			content = content + str(book.format_string(el_content)) + '\n'
			next_url = str(dom.xpath('//a[@id="linkIndex"]/@href')[0]) + str(
				dom.xpath('//a[@id="linkNext"]/@href')[0])
			# 获取下一页位置的链接如果包含_就是同一章节的第二页否则就是下一章
			if '_' in next_url:
				section_url = next_url
			else:
				break
		# 设置保存路径
		save_path = f'./小说/{book_name}/'
		# 判断目录是否存在
		if os.path.exists(save_path):
			# 存在就直接保存
			with open(f'{save_path}{section_title}.txt', 'w') as f:
				f.write(f'{section_title}\n\n{content}\n')
		else:
			# 不存在就创建目录并保存
			os.makedirs(save_path)
			with open(f'{save_path}{section_title}.txt', 'w') as f:
				f.write(f'{section_title}\n{content}')
			print(f'下载完成\t\t{section_title}')

	def run(self):
		book_text = book.get_data(url=start_url)
		# 创建并启动子进程:解析书籍内容并保存
		book_data_process = multiprocessing.Process(target=book.parse_book_data, kwargs={'book_text': book_text})
		book_data_process.start()
		page_url_list = book.get_page_data(book_text=book_text)
		page_text_list = book.get_data(url_list=page_url_list)
		for page_text in page_text_list:
			book.parse_section_data(page_text=page_text)


headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.62 Safari/537.36'
}

if __name__ == '__main__':
	start_url = input('请输入书籍章节目录页面url:')
	book = Book()
	book.run()
