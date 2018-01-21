#coding:utf-8
import sys
import os
import re
import time
import datetime
import logging
import json
from pathlib import Path
from functools import wraps
from collections import namedtuple
from urllib.parse import urlparse

import requests
from jinja2 import FileSystemLoader, Template
from jinja2 import Environment
import xlrd
import gevent
from gevent.pool import Group
from tqdm import tqdm

from .Config import *
from .log import setup_log

logger = logging.getLogger('itest')

class CaseData(object):
    def __init__(self, nrow, case, bookname):
        self.interface_name = case.row_values(nrow)[INAME_IDX]
        self.url = case.row_values(nrow)[URL_IDX]
        self.method = case.row_values(nrow)[METHOD_IDX]
        self.data = case.row_values(nrow)[DATA_IDX]
        self.assertion = case.row_values(nrow)[ASSERT_IDX]
        self.identity = "{}-{}-{}".format(bookname, case.name, nrow)
        self.error_msg = ""

    def valid(self):
        return all([
            self.valid_schema(),
            self.valid_method(),
            self.valid_data()
        ])

    def valid_schema(self):
        o = urlparse(self.url)
        if o.scheme.lower() not in SCHEMA:
            self.error_msg = "Invalid schema,only support http/https"
            return False
        return True

    def valid_method(self):
        method = str(self.method).upper()
        if method not in METHOD:
            self.error_msg = "Invalid method,only support post/get"
            return False
        return True

    def valid_data(self):
        try:
            if self.data:
                data = json.loads(self.data)
                self.data = data
            else:
                if self.is_post():
                    self.error_msg = "post data is required!"
        except json.decoder.JSONDecodeError as e:
            #Expecting property name enclosed in double quotes
            self.error_msg = "Invalid json:{}".format(e.args)
            return False
        return True

    def is_post(self):
        return True if self.method.upper() == METHOD[1] else False

    def is_get(self):
        return False if self.method.upper() == METHOD[1] else True


class ResultData(object):
    def __init__(self, case):
        self.identity = case.identity
        self.interface_name = case.interface_name
        self.url = case.url
        self.method = case.method
        self.data = case.data
        self.assertion = case.assertion
        self.status = ERROR
        self.elapsed = 0
        self.response = ""


class Results(dict):
    def __init__(self):
        self.setdefault('success', 0)
        self.setdefault('fail', 0)
        self.setdefault('error', 0)
        self.setdefault('detail', [])
        self.static = STATIC
        self.casefile = ""

    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name)

    def add(self, result):
        if result.status == SUCCESS:
            self.success += 1
        elif result.status == FAIL:
            self.fail += 1
        elif result.status == ERROR:
            self.error += 1
        self.detail.append(result)


class CaseRunner(object):
    def __init__(self, itercase, casefile):
        self.itercase = itercase
        self.result_set = Results()
        self.result_set.casefile = casefile
        self.runner = Group()

    def start(self, async=False):
        self.pbar = tqdm(self.case_list, desc="StartRunning", unit="case", miniters=1, ascii=True)
        self.result_set.total = len(self.case_list)
        self.result_set.starttime = self.now_time
        if async:
            self._start_async()
        else:
            self._start_sync()
        self.result_set.endtime = self.now_time
        self.pbar.close()
        return self.result_set

    def _start_async(self):
        for case in self.case_list:
            self.runner.spawn(self.run_case, case).rawlink(self.async_result_handler)
        self.runner.join()
        
    def _start_sync(self):
        for case in self.pbar:
            result = self.run_case(case)
            self.result_set.add(result)
    
    @property
    def case_list(self, cases=[]):
        if not cases:
            for case in self.itercase:
                cases.append(case)
        return cases
    
    def async_result_handler(self, greenlet):
        self.pbar.update()
        # self.pbar.refresh()
        self.result_set.add(greenlet.value)

    def assert_ok(self, case, content):
        final_expect = self.clean_data(case.assertion)
        response = self.clean_data(content)
        expect = re.compile(r'{}'.format(final_expect))
        return expect.search(response)

    def run_case(self, case):
        result_data = ResultData(case)
        if not case.valid():
            result_data.response = case.error_msg
            return result_data
        try:
            start_time = time.time()
            params = case.data if case.method=='get' else {}
            data = case.data if case.method=='post' else {}
            response = requests.request(case.method, case.url, params=params, data=data, headers=HEADER)
            result_data.elapsed = int((time.time() - start_time)*1000)
        
            if response.status_code == requests.codes.ok:
                result_data.response = self.clean_data(response.content)
                if self.assert_ok(case, response.content):
                    result_data.status = SUCCESS
                else:
                    result_data.status = FAIL
            else:
                result_data.response = str(response.status_code)
        except Exception as e:
            result_data.response = self.clean_data(e.args)
        return result_data  

    def clean_data(self, data):
        if isinstance(data, bytes):
            str_data = data.decode()
        else:
            str_data = str(data)
        return str_data.replace(' ', '').replace('\"', '').replace("\'", '')
    
    @property
    def now_time(self):
        return str(datetime.datetime.now())[:19]

def parse_file(casefiles, sheet=None):
    for casefile in casefiles:
        filename = Path(casefile).name
        try:
            book = xlrd.open_workbook(casefile)
        except FileNotFoundError:
            logger.error("No such casefile:'{}',skipped".format(casefile))
            continue
        logger.info("Start to spawn cases in file {}".format(filename))
        if sheet is None:
            sheet_name_list = book.sheet_names()
        else:
            sheet_name_list = sheet
        for sheet_name in sheet_name_list:
            case = book.sheet_by_name(sheet_name)
            def cleaned_case(i, case):
                """verify whether the case format is correct"""
                try:
                    row = case.row_values(i)
                    try:
                        #4 field required at least
                        if len(row) < 4:
                            case._cell_values.remove(row)
                            logger.error("Wrong format data in sheet '{}-{}-{}',skipped!".format(sheet_name, i+1, row))
                            return False
                        #url,method are required
                        if not all([row[URL_IDX],row[METHOD_IDX]]):
                            case._cell_values.remove(row)
                            logger.error("Wrong format data in sheet '{}-{}-{}',skipped!".format(sheet_name, i+1, row))
                            return False
                    except IndexError:
                        #handle column index error
                        logger.error("Wrong format data in sheet '{}-{}-{}',skipped!".format(sheet_name, i+1, row))
                        return False
                except IndexError:
                    #handle row index error
                    return False
                return True
            valid_nrow = 0
            for i in range(1,case.nrows):
                if cleaned_case(i, case):
                    valid_nrow += 1
                    yield CaseData(i, case, filename)
            if case.nrows > 1:
                logger.info("Spawn {} valid cases in sheet '{}'".format(valid_nrow, sheet_name))

def render_report(result_set, report):
    env = Environment(loader=FileSystemLoader(TEMPALTE_PATH))
    template = env.get_template(TEMPLATE_NAME)
    content = template.render(result_set).encode('utf-8')
    with open(report, 'wb') as f:
        f.write(content)



