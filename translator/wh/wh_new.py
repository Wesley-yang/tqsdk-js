#!/usr/bin/env python
#coding=utf-8

import logging

import ply.lex as lex
import ply.yacc as yacc

import wh.whlex
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class TranslateException(Exception):
    def __init__(self, err_line, err_col, err_msg):
        self.err_line = err_line
        self.err_col = err_col
        self.err_msg = err_msg
    def __str__(self):
        return "line:%d, col:%d, msg:%s" % (self.err_line, self.err_col, self.err_msg)


#转换支持环境
def reset():
    global input_serials, input_params, serials, output_serials, body_lines, function_serials, scount, current_line, temp_serials, line_start_map, current_output_serial, output_axis_list, next_color
    input_serials = []  # 所有输入序列
    output_serials = []
    output_axis_list = []
    temp_serials = []
    function_serials = []
    serials = []
    input_params = [] # 所有参数
    body_lines = [] # 输出行
    scount = 0
    next_color = 0
    current_line = []
    line_start_map = {} #行号->行第一个字符pos的映射表
    current_output_serial = {
        "color": get_auto_color(),
        "type": "LINE"
    }

def get_auto_color():
    global next_color
    colors = ["RED", "GREEN", "BLUE", "CYAN", "GRAY", "MAGENTA", "YELLOW", "LIGHTGRAY", "LIGHTRED", "LIGHTGREEN", "LIGHTBLUE"]
    c = colors[next_color]
    next_color = (next_color + 1) % len(colors)
    return c

def auto_serial_name():
    global scount
    scount += 1
    return "S_%d" % scount

def is_param(n):
    return n in input_params

def is_serial(n):
    return n in serials

def define_serial(serial_name, is_temp):
    if serial_name not in serials:
        serials.append(serial_name)
    if is_temp and serial_name not in temp_serials:
        temp_serials.append(serial_name)

def define_param(param_name):
    if param_name not in input_params:
        input_params.append(param_name)

def define_input_serial(serial_name):
    define_serial(serial_name, False)
    if serial_name not in input_serials:
        input_serials.append(serial_name)

def define_output(serial_name):
    global current_output_serial
    define_serial(serial_name, False)
    current_output_serial["name"] = serial_name
    output_serials.append(current_output_serial)
    current_output_serial = {
        "name": "",
        "color": get_auto_color(),
        "type": "LINE"
    }



def set_output_color(color):
    global current_output_serial
    c = color_map.get(color, color)
    current_output_serial["color"] = c


def set_output_type(t):
    global current_output_serial
    if t == "COLORSTICK":
        current_output_serial["type"] = "RGBAR"
    elif t == "VOLUMESTICK" or t == "OPISTICK":
        current_output_serial["type"] = "PCBAR"
    else:
        current_output_serial["type"] = t


def define_function_serial(fname, fparam):
    nname = function_map.get(fname, fname)
    for i in range(0, len(function_serials)):
        if function_serials[i]["name"] == nname and function_serials[i]["param"] == fparam:
            return function_serials[i]["id"]
    id = auto_serial_name()
    s = {
        "id": id,
        "name": nname,
        "param": fparam,
    }
    function_serials.append(s)
    current_line.append("{id}[i]={name}(i, {param}, {id});".format(**s))
    define_serial(id, True)
    return s["id"]

def as_value(s):
    return s+"[i]";

def finish_line(last):
    global body_lines, current_line
    body_lines += current_line
    body_lines.append(last)
    current_line = []


#lex+yacc语法规范
tokens = [
    "ID", 'NUMBER', "COMMENT",
    "VVALUE", "VSERIAL",
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'LPAREN', 'RPAREN',
    'COMMA', "SEMICOLON", "COLON", "COLON_EQUALS",
    "LT", "LTE", "GT", "GTE", 'EQUALS', 'NOT_EQUALS',
    "AND", "OR",
    "SERIAL",
    "FUNCS", #函数，1个序列参数
    "FUNCSS", #函数，2个序列参数
    "FUNCSV", #函数，1个序列参数,一个数值参数
    "FUNCSVV",
    "FUNCVV",
    "FUNCV",
    "COLOR",
    "OFUNC",
    "IFELSE",
    "BACKGROUNDSTYLE",
    # 0 是保持本身坐标不变。
    # 1 是将坐标固定在0到100之间。
    # 2 是将坐标以0为中轴的坐标系。
    "ORDER",
    "NEWLINE",
]


reserved = {
    # 输入序列
    "OPEN": "SERIAL",
    "HIGH": "SERIAL",
    "LOW": "SERIAL",
    "CLOSE": "SERIAL",
    "VOL": "SERIAL",
    "OPI": "SERIAL",
    "O": "SERIAL",
    "H": "SERIAL",
    "L": "SERIAL",
    "C": "SERIAL",
    # 序列函数
    "ABS": "FUNCV",
    "REF": "FUNCSV",
    "MA": "FUNCSV",
    "STD": "FUNCSV",
    "EMA": "FUNCSV",
    "DMA": "FUNCSV",
    "HHV": "FUNCSV",
    "LLV": "FUNCSV",
    "SUM": "FUNCSV",
    "COUNT": "FUNCSV",
    "SMA": "FUNCSVV",
    "MAX": "FUNCVV",
    "MIN": "FUNCVV",
    "BARSLAST": "FUNCS",
    # 颜色
    "COLORRED": "COLOR",
    "COLORGREEN": "COLOR",
    "COLORBLUE": "COLOR",
    "COLORCYAN": "COLOR",
    "COLORBLACK": "COLOR",
    "COLORWHITE": "COLOR",
    "COLORGRAY": "COLOR",
    "COLORMAGENTA": "COLOR",
    "COLORYELLOW": "COLOR",
    "COLORLIGHTGRAY": "COLOR",
    "COLORLIGHTRED": "COLOR",
    "COLORLIGHTGREEN": "COLOR",
    "COLORLIGHTBLUE": "COLOR",
    # 输出函数
    "COLORSTICK": "OFUNC",
    "VOLUMESTICK": "OFUNC",
    "OPISTICK": "OFUNC",
    # 特殊函数
    "IFELSE": "IFELSE",
    "BACKGROUNDSTYLE": "BACKGROUNDSTYLE",
    # 交易函数
    "BK": "ORDER",
    "SK": "ORDER",
    "BP": "ORDER",
    "SP": "ORDER",
    "BPK": "ORDER",
    "SPK": "ORDER",
}

function_map = {
    #WH函数到本地函数名映射表
    "HHV": "HIGHEST",
    "LLV": "LOWEST",
    "STD": "STDEV",
}

inserial_selector_map = {
    "O": "OPEN",
    "H": "HIGH",
    "L": "LOW",
    "C": "CLOSE",
    "VOL": "VOLUME",
    "OPI": "CLOSE_OI",
}

order_map = {
    # WH交易指令到本地指令映射表
    "BP": 'C.ORDER("BUY", "CLOSE", {volume})',
    "BK": 'C.ORDER("BUY", "OPEN", {volume})',
    "BPK": 'C.ORDER("BUY", "CLOSEOPEN", {volume})',
    "SP": 'C.ORDER("SELL", "CLOSE", {volume})',
    "SK": 'C.ORDER("SELL", "OPEN", {volume})',
    "SPK": 'C.ORDER("SELL", "CLOSEOPEN", {volume})',
}

color_map = {
    #WH名到本地名映射表
    "COLORRED": "RED",
    "COLORGREEN": "GREEN",
    "COLORBLUE": "BLUE",
    "COLORCYAN": "CYAN",
    "COLORBLACK": "BLACK",
    "COLORWHITE": "WHITE",
    "COLORGRAY": "GRAY",
    "COLORMAGENTA": "MAGENTA",
    "COLORYELLOW": "YELLOW",
    "COLORLIGHTGRAY": "LIGHTGRAY",
    "COLORLIGHTRED": "LIGHTRED",
    "COLORLIGHTGREEN": "LIGHTGREEN",
    "COLORLIGHTBLUE": "LIGHTBLUE",
}

precedence = (
    ('left', 'SEMICOLON'),
    ('left', 'COLON'),
    ('left', "EQUALS", "NOT_EQUALS"),
    ('left', 'COMMA'),
    ('left', "AND", "OR"),
    ('left', "LT", "LTE", "GT", "GTE"),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    # ('left', "LPAREN", "RPAREN"),
    )




def p_program(p):
    """
    program : program line
            | line
    """
    if len(p) == 2:
        p[0] = []
        p[0] += p[1]
    elif len(p) == 3:
        p[0] = p[1]
        p[0] +=p[2]


def p_program_error(p):
    '''lines : error'''
    p[0] = None
    p.parser.error = 1


def p_line_output_serial_define(p):
    """
    line : ID COLON expression SEMICOLON
    """
    logger.debug("p_line_output_serial_define: %s, %s", p[1], p[3])
    p[0] = [
        {"aid": "DEFINE_OUTPUT", "name": p[1]},
        {"aid": "BODY_LINE", "content": '%s[i] = %s;' % (p[1], p[3])},
    ]

#
# def p_line_temp_serial_define(p):
#     """
#     line : ID COLON_EQUALS expression SEMICOLON
#     """
#     logger.debug("p_line_temp_serial_define: %s, %s", p[1], p[3])
#     p[0] = WhLine()
#     p[0].expression = p[3]
#     p[0].temp_id = p[1]
#
#
# def p_line_anoymouse_output(p):
#     """
#     line : expression SEMICOLON
#     """
#     logger.debug("p_line_anoymouse_output: %s", p[1])
#     p[0] = WhLine()
#     p[0].expression = p[3]
#     p[0].output_id = auto_serial_name()
#
#
# def p_line_background_style(p):
#     """
#     line : BACKGROUNDSTYLE LPAREN NUMBER RPAREN SEMICOLON
#     """
#     logger.debug("p_line_background_style: %s", p[3])
#     if p[3] == "1":
#         p[0] = [{"aid": "SET_AXIS_OPTION", "min":0, "max": 100}]
#     elif p[3] == "2":
#         p[0] = [{"aid": "SET_AXIS_OPTION", "min":0}]
#
#
# def p_line_order(p):
#     """
#     line : order_statement SEMICOLON
#     """
#     logger.debug("p_line_order: %s", p[1])
#     p[0] = "%s;" % (p[1])
#     finish_line(p[0])
#
#
# def p_statement_with_ofunc(p):
#     """
#     statement : statement COMMA OFUNC
#     """
#     logger.debug("p_statement_with_ofunc: %s, %s", p[1], p[3])
#     set_output_type(p[3])
#     p[0] = p[1]
#
#
# def p_statement_with_color(p):
#     """
#     statement : statement COMMA COLOR
#     """
#     logger.debug("p_statement_with_color: %s, %s", p[1], p[3])
#     set_output_color(p[3])
#     p[0] = p[1]
#
#
# def p_statement_with_order(p):
#     """
#     order_statement : statement COMMA ORDER
#     """
#     logger.debug("p_line_with_order: %s, %s", p[1], p[3])
#     order_template = order_map.get(p[3])
#     order = order_template.format(volume=1)
#     p[0] = "if({cond}) {order}".format(cond=p[1], order=order)
#
#
# def p_statement_with_order_volume(p):
#     """
#     order_statement : statement COMMA ORDER LPAREN NUMBER RPAREN
#     """
#     logger.debug("p_line_with_order_volume: %s, %s", p[1], p[3])
#     order_template = order_map.get(p[3])
#     order = order_template.format(volume=p[5])
#     p[0] = "if({cond}[i]) {order}".format(cond=p[1], order=order)
#

def p_expression_paren(t):
    '''expression : LPAREN expression RPAREN'''
    t[0] = t[2]


def p_expressionv_binop(p):
    """
    expression : expression PLUS expression
              | expression MINUS expression
              | expression TIMES expression
              | expression DIVIDE expression
              | expression LT expression
              | expression LTE expression
              | expression GT expression
              | expression GTE expression
              | expression AND expression
              | expression OR expression
              | expression EQUALS expression
              | expression NOT_EQUALS expression
    """
    logger.debug("p_expressionv_binop: %s", p[1], p[2], p[3])
    id = auto_serial_name()
    p[0] = (id, [
        {"aid": "DEFINE_SERIAL", "serial_name": id},
        {"aid": "BODY_LINE", "content": "{id}[i]=({p1} {p2} {p3});".format(id=id, p1=p[1], p2=p[2], p3=p[3])},
    ])


def p_expression_number(p):
    """
    expression : NUMBER
    """
    logger.debug("p_expressionv_number: %s", p[1])
    p[0] = (p[1], [])


def p_expressions_serial(p):
    """
    expression : ID
    """
    logger.debug("p_expressions_serial: %s", p[1])
    s = inserial_selector_map.get(p[1], p[1])
    define_input_serial(s)
    p[0] = s


def p_expressions_function(p):
    """
    expression : ID LPAREN RPAREN
               | ID LPAREN expression COMMA expression RPAREN
               | ID LPAREN expression COMMA expression COMMA expression RPAREN
    """
    logger.debug("p_expressions_function: %s", p[1])
    p[0] = p[1]



##########################################################################################
def p_expressionv_vvalue(p):
    """expression : VVALUE
    """
    logger.debug("p_expressionv_id: %s", p[1])
    if is_param(p[1]):
        p[0] = p[1]
    elif is_serial(p[1]):
        p[0] = as_value(p[1])
    else:
        global line_start_map
        raise TranslateException(err_line=p.slice[1].lineno,
                                 err_col=p.slice[1].lexpos - line_start_map.get(p.slice[1].lineno, 0) + 1,
                                 err_msg="无法识别的标识符: %s. 如果这是一个指标参数,请将它加入参数表中" % p[1])

def p_expressions_vserial(p):
    """expression : VSERIAL
    """
    logger.debug("p_expressions_id: %s", p[1])
    if is_serial(p[1]):
        p[0] = p[1]
    else:
        global line_start_map
        raise TranslateException(err_line=p.slice[1].lineno,
                                 err_col=p.slice[1].lexpos - line_start_map.get(p.slice[1].lineno, 0) + 1,
                                 err_msg="无法识别的标识符: %s. 请检查拼写是否有误" % p[1])


def p_function_ifelse(p):
    """ function : IFELSE LPAREN expression COMMA expression COMMA expression RPAREN"""
    logger.debug("p_function_ifelse: %s, %s, %s", p[3], p[5], p[7])
    id = auto_serial_name()
    define_serial(id, True)
    current_line.append("{id}[i]=IFELSE({cond}, {vtrue}, {vfalse});".format(id=id, cond=p[3], vtrue=p[5], vfalse=p[7]))
    p[0] = id

def p_function_s(p):
    """ function : FUNCS LPAREN expression RPAREN"""
    logger.debug("p_function_s: %s, %s", p[1], p[3])
    fname = function_map.get(p[1], p[1])
    s_name = define_function_serial(fname, "%s" % (p[3]))
    p[0] = "%s" % s_name

def p_function_sv(p):
    """ function : FUNCSV LPAREN expression COMMA expression RPAREN"""
    logger.debug("p_function_sv: %s, %s, %s", p[1], p[3], p[5])
    fname = function_map.get(p[1], p[1])
    s_name = define_function_serial(fname, "%s,%s" % (p[3], p[5]))
    p[0] = "%s" % s_name

def p_function_ss(p):
    """ function : FUNCSS LPAREN expression COMMA expression RPAREN"""
    logger.debug("p_function_ss: %s, %s, %s", p[1], p[3], p[5])
    fname = function_map.get(p[1], p[1])
    s_name = define_function_serial(fname, "%s,%s" % (p[3], p[5]))
    p[0] = "%s" % s_name

def p_function_vv(p):
    """ function : FUNCVV LPAREN expression COMMA expression RPAREN"""
    logger.debug("p_function_vv: %s, %s, %s", p[1], p[3], p[5])
    fname = function_map.get(p[1], p[1])
    id = auto_serial_name()
    define_serial(id, True)
    current_line.append("{id}[i]={name}({param});".format(id=id, name=fname, param="%s,%s" % (p[3], p[5])))
    p[0] = id

def p_function_v(p):
    """ function : FUNCV LPAREN expression RPAREN"""
    logger.debug("p_function_vv: %s, %s, %s", p[1], p[3])
    fname = function_map.get(p[1], p[1])
    id = auto_serial_name()
    define_serial(id, True)
    current_line.append("{id}[i]={name}({param});".format(id=id, name=fname, param=p[3]))
    p[0] = id

def p_function_svv(p):
    """ function : FUNCSVV LPAREN expression COMMA expression COMMA expression RPAREN"""
    logger.debug("p_function_svv: %s, %s, %s", p[1], p[3], p[5], p[7])
    fname = function_map.get(p[1], p[1])
    s_name = define_function_serial(fname, "%s,%s,%s" % (p[3], p[5], p[7]))
    p[0] = "%s" % s_name

def p_function_unknown_0(p):
    """ function : ID LPAREN RPAREN"""
    raise TranslateException(err_line=p.slice[1].lineno,
                             err_col=p.slice[1].lexpos - line_start_map.get(p.slice[1].lineno, 0) + 1,
                             err_msg="尚未支持此函数: %s." % p[1])

def p_function_unknown_1(p):
    """ function : ID LPAREN expression RPAREN"""
    raise TranslateException(err_line=p.slice[1].lineno,
                             err_col=p.slice[1].lexpos - line_start_map.get(p.slice[1].lineno, 0) + 1,
                             err_msg="尚未支持此函数: %s." % p[1])

def p_function_unknown_2(p):
    raise TranslateException(err_line=p.slice[1].lineno,
                             err_col=p.slice[1].lexpos - line_start_map.get(p.slice[1].lineno, 0) + 1,
                             err_msg="尚未支持此函数: %s." % p[1])

def p_function_unknown_3(p):
    raise TranslateException(err_line=p.slice[1].lineno,
                             err_col=p.slice[1].lexpos - line_start_map.get(p.slice[1].lineno, 0) + 1,
                             err_msg="尚未支持此函数: %s." % p[1])

def p_error(p):
    if p:
        raise TranslateException(err_line=p.lineno,
                                 err_col=p.lexpos - line_start_map.get(p.lineno, 0) + 1,
                                 err_msg="不应该出现在这里的字符 %s" % p.value)
    else:
        raise TranslateException(err_line=-1,
                                 err_col=-1,
                                 err_msg="代码未正确结束,请检查括号匹配和行末分号等")

def wenhua_translate(req):
    """
    req:{
        id: "macd', //指标函数名
        cname: "macd中文名", //指标中文名称
        type: "MAIN", //指标类型, MAIN=主图指标, SUB=副图指标
        params: [
            ("SHORT", 3, 1, 100), //参数表，参数名/默认值/最小值/最大值
            ("LONG", 5, 2, 200),
        ],
        src: "...", //文华原代码
    }
    ret: {
        errline: 10,   //当转换过程出错时，标记出错行号，无错时为0, 在文件尾部出错为-1
        errcol: 3, //当转换过程出错时，标记出错列号，无错时为0, 在文件尾部出错为-1
        errvalue: "sum", //当转换过程出错时，标记出错字符，无错时为""
        target: "...", //转换好的目标代码
    }
    """
    #检查请求信息
    indicator_id = req["id"]
    wenhua_src = req["src"]
    input_params = [p[0] for p in req["params"]]
    #解析并拼装
    parser = yacc.yacc(debug=True)
    x = parser.parse(wenhua_src)
    print(x)



#---------------------------------------------------------------------------------

if __name__ == "__main__":
    def tryconvert(f):
        ret = wenhua_translate(f)
        print("""
        -INPUT--------------------------------
        %s
        -OUTPUT--------------------------------
        %s
        -EXPECTED--------------------------------
        """ % (f["src"], ret))

    from cases.userfail.not_supported.trade import case
    tryconvert(case)

"""
AVEDEV(X,N)：返回X在N周期内的平均绝对偏差。
注：
1、N包含当前k线。
2、N为有效值，但当前的k线数不足N根，该函数返回空值；
3、N为0时，该函数返回空值；
4、N为空值，该函数返回空值；
5、N不能为变量

算法举例：计算AVEDEV(C,3);在最近一根K线上的值。

用麦语言函数可以表示如下：
(ABS(C-(C+REF(C,1)+REF(C,2))/3)+ABS(REF(C,1)-(C+REF(C,1)+REF(C,2))/3)+ABS(REF(C,2)-(C+REF(C,1)+REF(C,2))/3))/3;

例：
AVEDEV(C,5);//返回收盘价在5周期内的平均绝对偏差。
//表示5个周期内每个周期的收盘价与5周期收盘价的平均值的差的绝对值的平均值，判断收盘价与其均值的偏离程度
"""

