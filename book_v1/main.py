# 示例小说:夺舍之停不下来
# 笔趣看网址:https://www.biqukan.la/
# 示例小说网址:https://www.biqukan.la/book/74444/
# 创建Book类
import random
import time

import pymysql
import requests
from lxml import etree
from retrying import retry


class Book(object):
	def __init__(self, api, book_id):
		# Book类成员属性 name\author\describe\section\content
		self.api = api  # 书籍目录页API
		self.book_id = book_id  # 书籍ID
		self.name = None  # 书籍名称
		self.author = None  # 书籍作者
		self.describe = None  # 书籍简介
		self.classify = None  # 书籍归类
		self.book_url = None  # 书籍url
		self.section_id = None  # 章节ID
		self.title = None  # 章节标题
		self.content = ""  # 章节内容
		self.section_url = None  # 章节url
		self.book_list = []  # 存储书籍内容
		self.section_list = []  # 存储章节内容
		# 配置requests请求参数
		self.header_list = [
			'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
			'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
			'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
			'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11'
		]
		self.headers = {'User-Agent': ''}
		self.cookies = {}

	# 构建书籍来源url
	def create_satart_url(self):
		self.book_url = self.api + self.book_id + '/' + 'index_1.html'
		print(f'已初始化url\t\t{self.book_url}')

	# 随机User-Agent
	def random_user_agent(self):
		self.headers['User-Agent'] = self.header_list[random.randint(1, 4) - 1]
		print(f"已构建请求头\t\t{self.headers['User-Agent']}")

	# 获取章节目录页面响应数据
	@retry(stop_max_attempt_number=5)
	def book_data(self):
		# 跳出多层循环的布尔变量
		flag = False
		while True:
			time.sleep(random.randint(2, 5))
			# 发送请求,获取响应
			response = requests.get(self.book_url, headers=self.headers, timeout=10)
			print(f'已发送请求\t\t{self.book_url}')
			# 设置编码
			response.encoding = response.apparent_encoding
			# 解析响应
			dom = etree.HTML(response.text)
			# 循环进行是根据是否是章节目录的第一页来决定要不要获取书籍信息
			if 'index_1.html' in self.book_url:
				# 获取书籍信息
				self.name = dom.xpath('//h1[@class="bookTitle"]/text()')[0]
				# 获取书籍作者
				self.author = dom.xpath('//h1[@class="bookTitle"]/small/a/text()')[0]
				# 获取书籍简介
				desc = dom.xpath('//p[@class="text-muted"]/text()')[0]
				self.describe = str(desc).strip()
				# 获取书籍归类
				self.classify = dom.xpath('//ol[@class="breadcrumb"]/li[2]/a/text()')[0]
				# 将书籍信息组成字典添加到list中
				temp = {
					'book_id': self.book_id,
					'name': self.name,
					'author': self.author,
					'describe': self.describe,
					'classify': self.classify,
					'book_url': self.book_url
				}
				self.book_list.append(temp)
				print(f'已保存书籍信息\t\t{self.name}')
			# 获取所有章节对象
			dd_list = dom.xpath('//dl[@class="panel-body panel-chapterlist"]/dd')
			# 遍历获取各章节信息
			for section in dd_list:
				try:
					# 通过章节url获取章节id
					self.section_url = section.xpath('./a/@href')[0]
					self.section_id = str(self.section_url).split('/')[-1][:-5]
					# 获取章节标题
					self.title = section.xpath('./a/text()')[0]
					# 将章节信息构建成字典添加到章节列表中
					temp = {
						'section_id': self.section_id,
						'title': self.title,
						'content': self.content,
						'section_url': self.section_url,
						'book_id': self.book_id
					}
					self.section_list.append(temp)
					# 获取下一页链接
					book_next_page = dom.xpath('//a[contains(text(),"下一页")]/@href')[0]
					# 将下一页链接复制给book_url进行循环
					self.book_url = 'https://www.biqukan.la/' + str(book_next_page)
				except:
					flag = True
			if flag:
				print(f'已保存章节信息\t\t↓↓↓↓↓↓开始保存章节内容↓↓↓↓↓↓')
				break
			time.sleep(random.randint(0, 3))

	# 获取并解析响应数据获取章节内容
	@retry(stop_max_attempt_number=5)
	def section_data(self):
		# 跳出多层循环标记
		flag = True
		while flag:
			# 遍历获取章节url
			for section in self.section_list:
				if '_' in section['section_url']:
					print(f'已保存剩余内容\t\t{section["title"]}')
				else:
					print(f'已保存首页内容\t\t{section["title"]}')
				# 获取章节内容url
				section_url = self.api + self.book_id + '/' + str(section['section_url'])
				# 请求章节url获取章节内容并解析
				response = requests.get(section_url, headers=self.headers, timeout=10)
				# 设置响应内容编码
				response.encoding = response.apparent_encoding
				# 解析响应内容
				dom = etree.HTML(response.text)
				# 获取章节内容
				text = dom.xpath('//div[@id="htmlContent"]/text()')
				# 新的章节内容: 格式化内容,去除无用符号
				new_content = str(text).split("最新章节！")[-1]
				new_content = new_content.replace("', ' \\xa0\\xa0\\xa0\\xa0", "<br />")
				new_content = new_content.replace("', ' r />", "")
				new_content = new_content.replace("', '>']", "")
				new_content = new_content.replace(" ']", "")
				# 后续的内容需要拼接上原来的内容
				section['content'] = str(section['content']) + new_content
				# 根据按钮文字判断是否为下一页
				if '下一页' in dom.xpath('//a[@id="linkNext"]/text()')[0]:
					# 是:就获取下一页链接,并保存到section_list中
					next_page_url = dom.xpath('//a[@id="linkNext"]/@href')[0]
					section['section_url'] = next_page_url
					flag = True
				else:
					# 否:就设置退出标签为True
					flag = False
			time.sleep(random.randint(0, 2))

	def create_connection(self):
		# 创建数据库链接
		self.conn = pymysql.Connect(
			user='root',
			password='4012',
			host='localhost',
			database='biqukan',
			port=3306,
			charset="utf8"
		)
		# 创建游标对象
		self.curs = self.conn.cursor()
		print(f'已创建数据库链接\t\tMySQL:biqukan')

	def save_book_data(self):
		# 获取book_list中的数据
		book_id = self.book_list[0]['book_id']
		name = self.book_list[0]['name']
		author = self.book_list[0]['author']
		describe = self.book_list[0]['describe']
		classify = self.book_list[0]['classify']
		book_url = self.book_list[0]['book_url']
		# 定义SQL
		sql = "INSERT INTO book(`book_id`, `name`, `author`, `describe`, `classify`, `book_url`) VALUES ('%s','%s','%s','%s','%s','%s')" % (
			self.conn.escape_string(book_id), self.conn.escape_string(name), self.conn.escape_string(author),
			self.conn.escape_string(describe), self.conn.escape_string(classify), self.conn.escape_string(book_url))
		self.curs.execute(sql)
		self.conn.commit()
		print(f'完成保存数据\t\t{name}')

	def save_section_data(self):
		# 遍历获取section_list中的数据
		for section in self.section_list:
			section_id = section['section_id']
			title = section['title']
			content = section['content']
			section_url = section['section_url']
			book_id = section['book_id']
			# 构建SQL语句
			sql = "INSERT INTO section(`section_id`, `title`, `content`, `section_url`, `book_id`) VALUES ('%s','%s','%s','%s','%s')" % (
				self.conn.escape_string(section_id), self.conn.escape_string(title), self.conn.escape_string(content),
				self.conn.escape_string(section_url), self.conn.escape_string(book_id))
			self.curs.execute(sql)
		print(f'已保存所有章节')
		self.conn.commit()

	def close_all(self):
		print('数据已保存\t\t即将关闭链接')
		self.curs.close()
		self.conn.close()
		print('任务已完成\t\t数据库链接已关闭')

	def run(self):
		# 构建书籍来源url
		self.create_satart_url()
		# 随机User-Agent
		self.random_user_agent()
		# 获取并解析章节目录页面响应数据
		self.book_data()
		# 获取并解析响应数据获取章节内容
		self.section_data()
		# 创建数据库链接
		self.create_connection()
		# 存储book_list数据
		self.save_book_data()
		# 存储section_data信息
		self.save_section_data()
		# 提交保存数据并关闭链接
		self.close_all()


if __name__ == '__main__':
	api = 'https://www.biqukan.la/book/'
	book_id = input('请输入要抓取的书籍ID:')
	book = Book(api=api, book_id=book_id)
	book.run()
