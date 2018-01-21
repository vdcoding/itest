#coding:utf-8
import os


#--------------------------文件资源配置信息------------------------------
#测试报告模板路径
TEMPALTE_PATH = os.path.join(os.path.dirname(__file__), 'template/')
#测试报告模板名称
TEMPLATE_NAME = 'index.html.template'
#渲染报告所需静态资源路径
STATIC = os.path.join(os.path.dirname(__file__), 'static')
#测试报告路径
REPORT_PATH = os.path.join(os.path.dirname(__file__), 'testreport')
os.makedirs(REPORT_PATH, exist_ok=True)
#默认测试报告名称
DEFAULT_REPORT_NAME = os.path.join(REPORT_PATH, 'index.html')
#支持的case文件格式
SUFFIX = ('xlsx', 'xls')
#支持的接口协议类型
SCHEMA = ('http', 'https')
METHOD = ('GET', 'POST')
#case的三种状态
SUCCESS = "Success"
FAIL = "Fail"
ERROR = "Error"
#用例中各字段的列索引
INAME_IDX = 0
URL_IDX = 1
METHOD_IDX = 2
DATA_IDX = 3
ASSERT_IDX = 4
#headers
HEADER = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"}


