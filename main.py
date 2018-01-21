import sys
import pathlib
from optparse import OptionParser

import xlrd

import itest
from .log import setup_log
from .core import parse_file, render_report, CaseRunner
from .Config import SUFFIX, DEFAULT_REPORT_NAME


def parse_options():
    parser = OptionParser(usage="itest [options], only support http and https")

    parser.add_option(
        '-f', '--casefile',
        type='str',
        action='append',
        dest='case_files',
        default=[],
        help="The test case file with excel format, support multiple"
    )

    parser.add_option(
        '-s', '--sheet',
        type='str',
        action='append',
        dest='test_sheet',
        default=['all'],
        help="Set the test suite which to run, support multiple"
    )
    
    parser.add_option(
        '-t','--test-report',
        type='str',
        dest='report',
        default=DEFAULT_REPORT_NAME,
        help="Set html report name, default is index.html"
    )
    
    parser.add_option(
        '--async-mode',
        action='store_true',
        dest='async_mode',
        default=False,
        help="The program will run under async mode,default is sync mode"
    )

    parser.add_option(
        '--loglevel', '-l',
        action='store',
        type='str',
        dest='loglevel',
        default='DEBUG',
        help="Choose from DEBUG/INFO/WARNING/ERROR/CRITICAL. Default is INFO.",
    )
    
    opts, args = parser.parse_args()
    return opts, args

def check_case_file(casefiles):
    error_files = []
    for f in casefiles:
        nf = pathlib.Path(f)
        if not pathlib.Path.exists(nf) and nf.suffix not in SUFFIX:
            error_files.append(f)
    return error_files

def check_sheet(casefile, sheet_set):
    error_sheet = []
    source = xlrd.open_workbook(casefile)
    sheet_name_list = source.sheet_names()
    for sheet in sheet_set:
        if sheet not in sheet_name_list:
            error_sheet.append(sheet)
    return error_sheet

def distinct_file(files):
    case_set = set(files)
    return list(case_set)

def distinct_sheet(sheets):
    sheet_set = set(sheets)
    if len(sheet_set) > 1:
        sheet_set.discard('all')
    return sheet_set

def all_sheet(sheet_set):
    if 'all' in sheet_set:
        return True
    return False

def main():
    options, arguments = parse_options()
    logger = setup_log(options.loglevel)
    file_set = distinct_file(options.case_files)
    sheet_set = distinct_sheet(options.test_sheet)
    error_files = check_case_file(file_set)
    
    def shutdown(code=1):
        logger.info("Shutting down (exit code %s), bye." % code)
        sys.exit(code)

    if not options.case_files:
        logger.error("The case file is needed!")
        shutdown()
    if error_files:
        logger.error("Files do not exists or unsupport format: {}".format(error_files))
        shutdown()
    if not all_sheet(sheet_set):
        if len(file_set) > 1:
            logger.error("Specify suite is not avaliable with multiple case files")
            shutdown()
        else:
            error_sheet = check_sheet(file_set[0], sheet_set)
            if error_sheet:
                logger.error("The sheet do not exists in case file: {}".format(error_sheet))
                shutdown()
            else:
                itercase = itercase = parse_file(file_set, sheet_set)
    else:
        itercase = parse_file(file_set)
        
    try:
        logger.info("Starting itest {}".format(itest.__version__))
        case_file_str = ','.join([pathlib.Path(f).name for f in file_set])
        result_set = CaseRunner(itercase, case_file_str).start(options.async_mode) 
        render_report(result_set, options.report) 
        logger.info("Finish the test")
    except FileNotFoundError as e:
        logger.error("No such file or directory:'{}'".format(options.report))
        shutdown(2)
    except KeyboardInterrupt as e:
        shutdown(0)

if __name__ == '__main__':
    main()
