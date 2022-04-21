# -*- coding: utf-8 -*-
"""
Created on Sun Mar 20 15:42:15 2022
Created on Sat Mar 19 18:28:20 2022
Created on Tue Mar 15 15:10:57 2022

@author: TARDIInsanity
"""

#from dataclasses import dataclass

#@dataclass
class Constant:
    def __init__(self, value:object):
        self.value = value
    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.value)})"

call = lambda self: self()

def get_by_function(code:str, function:callable) -> (str, str):
    clen = len(code)
    i = 0
    while i < clen and function(code[i]):
        i += 1
    return (code[:i], code[i:])
def strip_whitespace(code:str) -> str:
    clen = len(code)
    i = 0
    while i < clen and code[i] in " ,\n\t;":
        i += 1
    return code[i:]

@call
class GetNumber:
    @staticmethod
    def get_sign_ops(code:str) -> (list, str):
        '''retrieve the condensed operation code for a series of unary operands'''
        operations = []
        clen = len(code)
        i = 0
        while i < clen and code[i] in "+-~":
            sign = 1
            while i < clen and code[i] in "+-":
                if code[i] == "-":
                    sign *= -1
                i += 1
            if sign == -1:
                operations.append(-1)
            sign = 1
            while i < clen and code[i] == "~":
                sign ^= 1
                i += 1
            if sign == 0:
                operations.append(0)
        return (operations, code[i:])
    @staticmethod
    def get_digital(code:str, clen:int, digits:iter) -> (str, str):
        '''retrieve the longest sequence of the given digits'''
        i = 0
        while i < clen and code[i] in digits:
            i += 1
        return (code[:i], code[i:])
    CODEPAIRS = {
        None:("0123456789", 10),
        #"0u" UNARY : just takes the length of ones following it
        "0b":("01", 2),
        "0B":("01", 2),
        "0q":("0123", 4),
        "0Q":("0123", 4),
        "0o":("01234567", 8),
        "0O":("01234567", 8),
        "0x":("0123456789abcdefABCDEF", 16),
        "0X":("0123456789abcdefABCDEF", 16),
        "0v":("0123456789abcdefghijABCDEFGHIJ", 20),
        "0V":("0123456789abcdefghijABCDEFGHIJ", 20),
        #"0a" ALPHANUMERIC (36)
        }
    @classmethod
    def get_natural(cls, code:str, clen:int) -> (int, str):
        if not code:
            raise SyntaxError("unexpected lack of digits")
        pair = code[:2]
        if pair in ("0u", "0U"):
            result, remainder = get_by_function(code[2:], "1".__eq__)
            result = len(result) # unary zero is just "0u"
        elif pair in ("0a", "0A"):
            result, remainder = get_by_function(code[2:], str.isalnum)
            result = int(result, 36)
        else:
            if pair in cls.CODEPAIRS:
                digits, base = cls.CODEPAIRS[pair]
                o = 2
            else:
                digits, base = cls.CODEPAIRS[None]
                o = 0
            result, remainder = cls.get_digital(code[o:], clen-o, digits)
            if not result:
                raise SyntaxError(f"integer representation {code[:20]} must contain at least one digit from '{digits}'")
            #print(f"Converting ({result}) to base ({base}) from ({code=}); ({clen=}); ({o=}); ({digits}), with remainder ({remainder})")
            result = int(result, base=base)
        if remainder[:1] == "y":
            temp, remainder = cls.get_natural(remainder[1:], len(remainder)-1)
            result **= temp
        return (result, remainder)
    def __call__(self, code:str, allow_mul:bool=True) -> (int, str):
        code = strip_whitespace(code)
        if not code:
            return (0, code)
        operations, code = self.get_sign_ops(code)
        value, code = self.get_natural(code, len(code))
        for op in reversed(operations):
            # easier AND more maintainable than trying to work out the mathematical solution
            # is to just perform the operations (almost) verbatim
            if op: # -1 means negate
                value *= -1
            else: # 0 means bitwise not
                value ^= -1
        while code and code[0] == "*":
            temp, code = self(code[1:], False)
            value *= temp
        return (value, code)

@call
class GetIdentifier:
    @staticmethod
    def __call__(code:str) -> (str, str):
        return get_by_function(code, lambda i: ("_"+i).isidentifier())

@call
class GetQuote:
    @staticmethod
    def __call__(code:str):
        closer = code[0]
        clen = len(code)
        i = 1
        lastescape = -1
        while i < clen:
            if code[i] == closer:
                return (code[1:i], code[i+1:])
            if code[i] == "\\":
                lastescape = i
                i += 1
            i += 1
        if i > clen:
            raise SyntaxError(f"unexpected escape char ({code[-1]}) ending code")
        noclose = lambda *vals: SyntaxError(f"quotation ({closer}) was never closed, beginning with: {code[:20]}", *vals)
        if lastescape == clen-2 and code[-1] == closer:
            raise noclose(f"likely escaped closer: {code[-5:]}")
        raise noclose()

class Lex:
    def __init__(self, code:str, closer:str=None):
        self.code = code
        self.closer = closer
        self.sub = None
        self.temp = []
    def __iter__(self):
        return self
    def substep(self):
        try:
            keep, result = next(self.sub)
            if keep:
                self.temp.append(result)
            return (False, result)
        except StopIteration:
            self.code = self.sub.code
            self.sub = None
            result = self.temp
            self.temp = []
            return (True, result)
    def popnum(self):
        number, self.code = GetNumber(self.code)
        return number
    def popide(self):
        identifier, self.code = GetIdentifier(self.code)
        return identifier
    QUOTE = "'" + '"'
    def quote(self):
        quote, self.code = GetQuote(self.code)
        return quote
    BRACE = {"(":")", "<":">",
             "[":"]", "{":"}"}
    def substart(self):
        self.sub = self.__class__(self.code[1:], self.BRACE[self.code[0]])
        return f"entering brace: {self.code[0]}"
    def __next__(self):
        self.code = strip_whitespace(self.code)
        if self.sub is not None:
            return self.substep()
        if not self.code:
            raise StopIteration
        if (first := self.code[0]) == self.closer:
            self.code = self.code[1:]
            raise StopIteration
        if first.isnumeric() or first in "+-~":
            return (True, Constant(self.popnum()))
        if first.isalpha() or first == "_":
            return (True, self.popide())
        if first in self.QUOTE:
            return (True, Constant(self.quote()))
        if first in self.BRACE:
            return (False, self.substart())
        if first in self.BRACE.values():
            # why do i always throw the next 20 or so characters with it?
            # because it's almost trivial to find where the error occurred that way
            # and way easier to implement than position tracking.
            raise SyntaxError(f"mismatched closing brace spotted: {first} followed by {self.code[1:20]}")
        raise SyntaxError(f"unexpected token '{first}' beginning segment {self.code[:20]}")

class Lexer:
    def __init__(self, code):
        self.lexer = Lex(code)
        self.result = []
    def __iter__(self):
        return self
    def __next__(self):
        result = next(self.lexer)
        if result[0]:
            self.result.append(result[1])
        return result

def bitsort(values:list, vlen:int=None):
    '''from bitsort import bitsort'''
    values = list(values)
    if vlen is None:
        vlen = len(values)
    odds = values[1::2]+[0]
    evens = values[::2]
    for _ in range(vlen+1):
        evens, odds = zip(*((i|j, i&j) for i, j in zip(evens, odds)))
        evens = list(evens)
        odds = list(odds)
        odds[:-1], evens[1:] = zip(*((i|j, i&j) for i, j in zip(odds[:-1], evens[1:])))
    return [i for j in zip(evens, odds) for i in j][:vlen]

def bitgrad_new(values:list):
    '''from bitsort import bitgrad_new'''
    return [i&~j for i, j in zip(values, values[1:]+[values[0]])]

def log(value, base):
    '''from math import log;
    only the integer part is used and the args are positive ints'''
    if base < 2 or value < 1:
        return -1
    buffer = {1:base}
    result = 0
    while value >= base:
        present = 1
        while value >= buffer[present]:
            present <<= 1
            if present not in buffer:
                buffer[present] = buffer[present>>1]**2
        present >>= 1
        value = value // buffer[present]
        result += present
    return result

def floor(value):
    '''from math import floor'''
    return int(value//1)

#from functools import wraps

def reduce(function, sequence, initial):
    '''from functools import reduce'''
    value = initial
    for element in iter(sequence):
        value = function(value, element)
    return value

# !!!
# !!! PRIMARY BODY
# !!!

nbool = lambda i: -bool(i)
ident = lambda i: i
nones = lambda i, d: d if i is None else i
call = lambda self: self()

class liststr:
    '''from typing import List
    liststr = List[str]'''
    def __repr__(self):
        return "List[str]"

class Typedict(dict):
    def __getitem__(self, key):
        if super().__contains__(key):
            return super().__getitem__(key)
        for i in self:
            if issubclass(key, i):
                return super().__getitem__(key)

# !!! UPDATE TO INCLUDE ALL ATTAINABLE TYPE OBJECTS IN THIS LANGUAGE
typemap = Typedict({
    int:0,
    str:1,
    })

def deep_copy(array):
    if isinstance(array, (int, str, Constant)):
        return array
    if isinstance(array, list):
        return [deep_copy(i) for i in array]
    raise ValueError(f"Unexpected array type: {type(array)}; {array}")

def take_last(stack, n:int):
    result = []
    if isinstance(n, slice):
        result, stack[n] = stack[n], []
    elif n > 0:
        slic = slice(-n, None, 1)
        result, stack[slic] = stack[slic], []
    return result

#@dataclass
class D_Buffer:
    def __init__(self, buffer:str=""):
        self.buffer = buffer
    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.buffer)})"
    def s_print(self, source:list, n):
        if n > 0: # FIXED: ~ was supposed to be -
            self.buffer += "".join(str(i) for i in take_last(source, n)[::-1])
    def s_flush(self):
        print(self.buffer)
        self.buffer = ""
    def e_read(self, destination:list):
        '''unused'''
        i = input()
        destination.extend(i)
        return len(i)

class D_Dapper(dict):
    def __getitem__(self, key):
        if key not in self:
            self[key] = []
        return super().__getitem__(key)
    def append(self, key, value):
        if key not in self:
            self[key] = []
        self[key].append(value)
    def appends(self, keys, vals):
        for key, val in zip(keys, vals):
            self.append(key, val)
    def shear(self, key):
        self[key].pop(-1)
        if not super().__getitem__(key):
            super().__delitem__(key)
    def last(self, key):
        return self[key][-1]
    def get_ref(self, key):
        return Variable(key, self)

class D_Coatrack(D_Dapper):
    def __init__(self):
        super().__init__()
        self[vars] = D_Dapper()
        self[print] = D_Buffer()
        self[dir] = {}
        self.chain = []

#@dataclass
class Variable:
    def __init__(self, key:object, parent:D_Dapper):
        self.key = key
        self.parent = parent
    def __repr__(self):
        return f"{self.__class__.__name__}{repr((self.key, self.parent))}"
    @property
    def value(self):
        return self.parent.last(self.key)

@call # the only way to properly override __init__
class Samey(tuple):
    def __len__(self):
        return self.length
    def __getitem__(self, index):
        if isinstance(index, int) and max(index, ~index) < self.length:
            return tuple.__getitem__(self, 0)
        raise IndexError("invalid index for Samey-tuple: "+repr(index))
    def __call__(self, value, length:int):
        result = self.__class__([value])
        result.length = length
        return result
    def __iter__(self):
        if not self.length:
            return (i for i in range(0))
        value = self[0]
        return (value for _ in range(self.length))

class Statement:
    def __init__(self, function:callable, slots:list):
        '''function: the main function which expects <len(slots)-many arguments
        in a list> & <the context>. Functions must perform their own type-checking.
        slots: a list of functions. Each function takes a list of elements
        and the context and must return one element for use in the main function.
        The main function must return a (bool, object) pair, where the <bool>
        decides whether to print the object.'''
        self.function = function
        self.arity = tuple(slots)
        assert callable(function)

class Expression(Statement):
    def __init__(self, function:callable, slots:list, statement_version:Statement=None):
        '''See <Statement.__init__.__doc__> for more details.
        statement_version: an object with identical side-effects but which computes
        more efficiently because it does not need to return a meaningful object.
        Expressions, when used as expressions, should return a (bool, object) pair,
        where the <object> will be used in an evaluation regardless of the <bool>.'''
        super().__init__(function, slots)
        self.statement_version = nones(statement_version, self)

class Macro:
    def __init__(self, name, routine:list):
        '''CALL behavior is implemented in the special CALL statement'''
        self.name = name
        self.routine = routine
    def __hash__(self):
        return hash(self.name)
    def __str__(self):
        return f"macro {self.name}"
    def __call__(self, context):
        parent = context.chain[-1]
        parent.sub = parent.__class__(deep_copy(self.routine), context)
    def __eq__(self, value):
        return isinstance(value, self.__class__) and value.name == self.name
    def __lt__(self, value):
        return isinstance(value, self.__class__) and value.name < self.name
typemap[Macro] = 2
class MethodWrapper(Macro):
    def __init__(self, name, method:callable):
        self.method = [method]
    def __call__(self, context):
        self.method[0]()

PASS = lambda arguments, context: None
STATEMENTS = {}
STMT_FUNC = {}
def statement(key:str, *argtypes):
    if isinstance(key, int):
        if key not in STATEMENTS:
            STMT_FUNC[key] = PASS
            STATEMENTS[key] = Statement(PASS, (None,)*key)
        return STATEMENTS[key]
    def wrapper(function):
        STMT_FUNC[key] = function
        STATEMENTS[key] = Statement(function, argtypes)
        return None
    return wrapper
EXPRESSIONS = {}
EXPR_FUNC = {}
def expression(key:str, *argtypes, statement_version=None):
    if statement_version == "pass":
        statement_version = statement(len(argtypes))
    def wrapper(function):
        EXPR_FUNC[key] = function
        EXPRESSIONS[key] = Expression(function, argtypes, statement_version)
    return wrapper

Needful = (Statement, Expression)

# !!! STRINGERS

plural = lambda n, txt: str(n) + " " + txt + "s"*(n != 1)
got_invalid = lambda op_name, b: f"<{op_name}> operation received an invalid {b} "
get_type = lambda i: f"type: {type(i)}"
index_range = lambda op_name, stack_name, i: f"<{op_name}> operation tried to access {plural(i, 'space')} past the end of the {stack_name} stack."
index_negative = lambda op_name, stack_name, i: f"<{op_name}> operation tried to access negative index '{i}' of the {stack_name} stack"
index_type = lambda op_name, stack_name: f"<{op_name}> operation tried to access the {stack_name} stack at a non-integer index"

# !!! UTILITIES

def get_stack(op_name, stack_name, context, len_requirement:int=None, suppress_neg_error:bool=False):
    try:
        if isinstance(stack_name, Macro):
            raise TypeError
        result = context[stack_name]
    except TypeError:
        raise TypeError(got_invalid(op_name, "STACK_NAME of")+get_type(stack_name))
    if isinstance(len_requirement, int):
        if len_requirement < 0 and not suppress_neg_error:
            raise IndexError(index_negative(op_name, stack_name, len_requirement))
        difference = len_requirement-len(result)
        if difference > 0:
            raise IndexError(index_range(op_name, stack_name, difference))
    elif len_requirement is not None:
        raise TypeError(index_type(op_name, stack_name))
    return result

def require_index(op_name, stack_name, index, index_name="index"):
    if not isinstance(index, int):
        raise TypeError(got_invalid(op_name, index_name))
    if index < 0:
        raise IndexError(index_negative(op_name, stack_name, index))

def wrapper_mapfunc(name:str):
    def wrapper(function):
        def wrapped(arguments, context) -> None:
            stack_name, number = arguments
            stack = get_stack(name, stack_name, context, number)
            stack[-number:] = [function(i) for i in stack[-number:]]
        return statement(name, None, None)(wrapped)
    return wrapper

def wrapper_listfunc(name:str):
    def wrapper(function):
        def wrapped(arguments, context) -> None:
            stack_name, number = arguments
            stack = get_stack(name, stack_name, context, number)
            stack[-number:] = function(stack[-number:])
        return statement(name, None, None)(wrapped)
    return wrapper

@statement("discard", None, None)
def _(arguments, context):
    stack_name, number = arguments
    take_last(get_stack("discard", stack_name, context, number, True), number)
def expr_reduce(name:str, zid):
    def wrapper(function):
        def wrapped(arguments, context) -> None:
            stack_name, number = arguments
            stack = get_stack(name, stack_name, context, number, True)
            if number <= 0:
                return zid
            return reduce(function, take_last(stack, number), zid)
        return expression(name, None, None, statement_version=STATEMENTS["discard"])(wrapped)
    return wrapper
def expr_reducep(name:str, zid, post:callable):
    def wrapper(function):
        def wrapped(arguments, context) -> None:
            stack_name, number = arguments
            stack = get_stack(name, stack_name, context, number, True)
            if number <= 0:
                return zid
            return post(reduce(function, take_last(stack, number), zid))
        return expression(name, None, None, statement_version=STATEMENTS["discard"])(wrapped)
    return wrapper
def expr_sum(name:str, zid):
    def wrapped(arguments, context) -> None:
        stack_name, number = arguments
        stack = get_stack(name, stack_name, context, number, True)
        if number <= 0:
            return zid
        return sum(take_last(stack, number), start=zid)
    return expression(name, None, None, statement_version=STATEMENTS["discard"])(wrapped)

# !!! BEHAVIOR FUNCTIONS

def sort_key(value):
    return (typemap[type(value)], hash(value))
def div_func(divisor, dividend):
    '''(denominator, numerator) -> (remainder, quotient)
    obeying the rule: denominator*quotient + remainder == numerator'''
    if divisor == 0:
        return (dividend, 0)
    return divmod(dividend, divisor)[::-1]
def string_div(seglen:int, string):
    if seglen == 0:
        return (string, [])
    if seglen == 1:
        return ("", list(string))
    if seglen == -1:
        return ("", list(string[::-1]))
    step = 1
    adjunct = 0
    if seglen < 0:
        string = string[::-1]
        step = -1
        adjunct = -1
    number = len(string)//abs(seglen)
    quotient = [string[i*seglen+adjunct or None:(i+1)*seglen+adjunct or None:step] for i in range(0, number)][::step]
    remainder = string[number*seglen:] if step == 1 else string[:number*seglen]
    return (remainder, quotient)
def stack_rotate(segment, n:int):
    return segment[n:] + segment[:n]
def not_behavior(value) -> int:
    if hasattr(value, "__invert__"):
        return ~value
    return ~nbool(value)

# !!! STATEMENT DEFINITIONS
# the return value of a statement is ignored

wrapper_mapfunc("ibool")(nbool)
wrapper_mapfunc("ichr")(chr)
wrapper_mapfunc("istr")(str)
wrapper_mapfunc("iord")(ord)
wrapper_mapfunc("iint")(int)
wrapper_mapfunc("ineg")(int.__neg__)
wrapper_mapfunc("inot")(not_behavior)
wrapper_listfunc("bitsort")(bitsort)
wrapper_listfunc("bitgrad")(bitgrad_new)
@wrapper_listfunc("ieq")
def _(values:list) -> list:
    return [nbool(i==j) for i,j in zip(values, values[1:]+[values[0]])]
@wrapper_listfunc("sort")
def _(values:list) -> list:
    return sorted(values, key=sort_key)
@statement("div", None)
def _(arguments, context) -> None:
    stack_name, = arguments
    stack = get_stack("div", stack_name, context, 2)
    stack[-2:] = list(div_func(*stack[-2:]))
@statement("split", None, None, None)
def _(arguments, context):
    stack_name, string, separator = arguments
    stack = get_stack("split", stack_name, context)
    if not isinstance(string, str):
        raise TypeError(got_invalid("split", "string parameter"))
    if isinstance(separator, int):
        remainder, quotient = string_div(separator, string)
        stack.extend(quotient)
        stack.append(remainder)
    elif isinstance(separator, str):
        if separator == "":
            stack.extend(string)
        else:
            stack.extend(string.split(separator))
    else:
        raise TypeError(got_invalid("split", "separator parameter"))

@statement("clone", None, None, None)
def _(arguments, context) -> None:
    source_name, dest_name, number = arguments
    source = get_stack("clone", source_name, context, number)
    dest = get_stack("clone", dest_name, context)
    dest.extend(source[-number:])
@statement("dup", None, None, None)
def _(arguments, context) -> None:
    stack_name, source, dest = arguments
    require_index("dup", stack_name, source, "source index")
    require_index("dup", stack_name, dest, "destination index")
    stack = get_stack("dup", stack_name, context, max(source, (dest or 1)-1))
    stack.insert(-dest, stack[~source])
@statement("del", None, None)
def _(arguments, context) -> None:
    stack_name, index = arguments
    require_index("del", stack_name, index)
    stack = get_stack("del", stack_name, context, index)
    stack.pop(~index)
@statement("push", None, None, None)
def _(arguments, context) -> None:
    stack_name, index, value = arguments
    require_index("push", stack_name, index)
    stack = get_stack("push", stack_name, context, (index or 1)-1)
    if index:
        stack.insert(-index, value)
    else:
        stack.append(value)
@statement("flip", None, None, None)
def _(arguments, context) -> None:
    stack_name, start, end = arguments
    require_index("flip", stack_name, start, "start index")
    require_index("flip", stack_name, end, "end index")
    start, end = min(start, end), max(start, end)
    stack = get_stack("flip", stack_name, context, end)
    stack[-end:-start] = stack[-end:-start][::-1]
@statement("rot", None, None, None, None)
def _(arguments, context) -> None:
    stack_name, start, end, number = arguments
    require_index("rot", stack_name, start, "start index")
    require_index("rot", stack_name, end, "end index")
    if start == end:
        return None
    flipped = number < 0
    if start > end:
        start, end = end, start
        flipped ^= True
    stack = get_stack("rot", stack_name, context, end)
    number %= end-start
    if start == 0:
        start = None
    else:
        start *= -1
    stack[-end:start] = stack_rotate(stack[-end:start], -number if flipped else number)

@statement("print", None, None)
def _(arguments, context) -> None:
    stack_name, number = arguments
    stack = get_stack("print", stack_name, context, number)
    context[print].s_print(stack, number)
@statement("flush")
def _(arguments, context) -> None:
    assert not arguments
    context[print].s_flush()

# !!! SPECIAL STATEMENT DEFINITIONS

@statement("call", None)
def _(arguments, context) -> None:
    macr, = arguments
    if not isinstance(macr, Macro):
        raise TypeError("attempted to call a non-macro of type"
                        f" ({type(macr)}): {repr(macr)}")
    return macr(context)
@statement("if", None, None)
def _(arguments, context) -> None:
    value, macr = arguments
    if value:
        return STMT_FUNC["call"]((macr,), context)
@statement("popping", None, liststr, None)
def _(arguments, context, actually_getting:bool=False) -> None:
    op_name = "getting" if actually_getting else "popping"
    stack_name, names, macro = arguments
    if not isinstance(macro, Macro):
        raise TypeError(f"<{op_name}> statement attempted to call a non-function")
    number = len(names)
    stack = get_stack(op_name, stack_name, context, number)
    macro(context)
    # <macro> sets context.chain[-1].sub to be a new engine
    # engines, on init, append themselves to chain.
    # therefore, chain[-1] NOW refers to this subcontext.
    if not number:
        return None
    values = stack[-number:][::-1]
    if not actually_getting:
        stack[-number:] = []
    context.chain[-1].defines(names, values)
@statement("getting", None, liststr, None)
def _(arguments, context) -> None:
    return STMT_FUNC["popping"](arguments, context, True)

# !!! EXPRESSION DEFINITIONS
# the return value of an expression is vital to its nature

@expression("pop", None, None, statement_version=STATEMENTS["del"])
def _(arguments, context) -> object:
    stack_name, index = arguments
    require_index("pop", stack_name, index)
    stack = get_stack("pop", stack_name, context, index)
    return stack.pop(~index)
@expression("get", None, None, statement_version="pass")
def _(arguments, context) -> object:
    stack_name, index = arguments
    require_index("get", stack_name, index)
    stack = get_stack("get", stack_name, context, index)
    return stack[~index]
@expression("size", None, statement_version="pass")
def _(arguments, context) -> object:
    stack_name, = arguments
    stack = get_stack("get", stack_name, context)
    return len(stack)
@expression("read")
def _(arguments, context) -> object:
    assert not arguments
    return input()
@expression("len", None, statement_version="pass")
def _(arguments, context) -> object:
    value, = arguments
    return len(value)
@expression("shift", None, None, statement_version="pass")
def _(arguments, context) -> object:
    target, number = arguments
    if not target or not number:
        return target
    if number < 0:
        return target >> -number
    return target << number
@expression("pow", None, None, statement_version="pass")
def _(arguments, context) -> object:
    base, number = arguments
    if number == 0 or base == 1:
        return 1
    if number < 0 or base == 0:
        return 0
    if base == -1:
        return base**(number%2)
    if base == 2:
        return 1<<number
    return base**number
@expression("log", None, None, statement_version="pass")
def _(arguments, context) -> object:
    target, base = arguments
    target = abs(target)
    base = abs(base)
    if target == 0:
        return -1
    if base == 0:
        return 0
    if base == 1:
        return target
    return int(floor(log(target, base)))
@expression("sign", None, statement_version="pass")
def _(arguments, context) -> object:
    target, = arguments
    if not target:
        return 0
    if target < 0:
        return -1
    return 1

expression("bool", None, statement_version="pass")(nbool)
expression("chr", None, statement_version="pass")(chr)
expression("str", None, statement_version="pass")(str)
expression("ord", None, statement_version="pass")(ord)
expression("int", None, statement_version="pass")(int)
expression("neg", None, statement_version="pass")(int.__neg__)
expression("not", None, statement_version="pass")(not_behavior)
@expression("eq", None, None, statement_version="pass")
def _(arguments, context) -> object:
    left, right = arguments
    return -nbool(left==right)
expr_sum("sum", 0)
expr_reduce("prod", 1)(int.__mul__)
expr_reduce("and", -1)(int.__and__)
expr_reduce("or", 0)(int.__or__)
expr_reduce("xor", 0)(int.__xor__)
expr_reducep("nand", -1, int.__invert__)(int.__and__)
expr_reducep("nor", 0, int.__invert__)(int.__or__)
expr_reducep("nxor", 0, int.__invert__)(int.__xor__)
@expression("slice", None, None, None, statement_version="pass")
def _(arguments, context) -> object:
    value, start, end = arguments
    if not isinstance(value, str):
        raise TypeError("<slice> operation attempted to slice a non-string")
    if not isinstance(start, (int, str)):
        raise TypeError("<slice> start parameter must be an integer or string")
    if not isinstance(end, (int, str)):
        raise TypeError("<slice> end parameter must be an integer or string")
    if not value:
        return ""
    if isinstance(start, int):
        start %= len(value)
    elif isinstance(start, str):
        if start in value:
            start = value.index(start)+len(start)
        else:
            start = 0
    if isinstance(end, int):
        end %= len(value)
    elif isinstance(end, str):
        if end in value:
            end = value.index(end)
        else:
            end = len(value)
    return value[start:end]
@expression("cat", None, None, None, statement_version="pass")
def _(arguments, context) -> object:
    stack_name, number, joiner = arguments
    stack = get_stack("cat", stack_name, context, number, True)
    if number <= 0:
        return ""
    return str(joiner).join(str(i) for i in take_last(stack, number))

# !!! SPECIAL EXPRESSION DEFINITIONS

@expression("macro", list)
def _(arguments, context) -> None:
    routine, = arguments
    return Macro("macro", deep_copy(routine))
@expression("current", statement_version="pass")
def _(arguments, context) -> object:
    assert not arguments
    return context.chain[-1].macro
@expression("break", statement_version="pass")
def _(arguments, context) -> object:
    assert not arguments
    return MethodWrapper("break", context.chain[-1].break_me)
@expression("repeat", statement_version="pass")
def _(arguments, context) -> object:
    assert not arguments
    return MethodWrapper("repeat", context.chain[-1].repeat_me)

# !!! END DEFINITION SERIES

def type_check(requirement, value):
    '''only used for SPECIAL statements and expressions.
    If a requirement other than <None> is satisfied, the item is NOT evaluated'''
    if requirement is None:
        return True
    if requirement is liststr:
        return isinstance(value, list) and all(isinstance(i, str) for i in value)
    if requirement is list:
        return isinstance(value, list)
    if requirement is str:
        return isinstance(value, str)
    raise NotImplementedError(f"type requirement {requirement} was never implemented."
                              "How did it show up?")

def evaluation_prune(val):
    if isinstance(val, (Constant, Variable)):
        return val.value
    return val

class Engine:
    def __init__(self, tree:(list, (str, Constant, list)), context:D_Coatrack=None, macro:Macro=None):
        self.macro = nones(macro, Macro("__main__", deep_copy(tree)))
        self.sub = None
        #self.tree = [[0, i] for i in tree]
        #self.index = 0
        #self.stack = []
        self.context = nones(context, D_Coatrack())
        self.context.chain.append(self)
        self.locals = []
        self.repeat_me()
    def repeat_me(self):
        self.desub() # disassemble all subcontexts
        self.tree = [[0, i] for i in deep_copy(self.macro.routine)]
        self.treel = len(self.tree)
        self.index = 0
        self.stack = []
    def break_me(self):
        #self.desub() triggers on the inevitable IndexError that follows
        self.tree = []
    def define(self, identifier, value):
        self.locals.append(identifier)
        self.context[vars].append(identifier, value)
    def defines(self, identifiers:list, values:list):
        self.locals.extend(identifiers)
        self.context[vars].appends(identifiers, values)
    def dereference(self):
        for name in self.locals:
            self.context[vars].shear(name)
        self.locals = []
    def deinitialize(self):
        self.desub()
        self.dereference()
        self.context.chain.pop(-1)
    def desub(self):
        if self.sub is not None:
            self.sub.deinitialize()
            self.sub = None
    @property
    def here(self):
        return self.tree[self.index]
    @here.setter
    def here(self, value):
        self.tree[self.index] = value
    @here.deleter
    def here(self):
        del self.tree[self.index]
    def inject_after_here(self, values:list):
        self.tree[self.index+1:self.index+1] = values
    def __iter__(self):
        return self
    def __next__(self) -> str:
        DEBUG and print("working at index "+str(self.index))
        if self.sub is None:
            stop = None
            try:
                stage, head = self.here
                DEBUG and print("retrieved stage & head")
            except IndexError as e:
                stop = StopIteration(e)
            if stop is not None:
                raise stop
            return self.STAGES[stage](self, head)
        try:
            return next(self.sub)
        except StopIteration:
            self.desub()
            return next(self)
    def stage_0(self, head) -> str:
        DEBUG and print("stage 0")
        if self.stack:
            index, conds = self.stack[-1]
            requirement = conds[self.index-index-1]
            if requirement is not None:
                correct = type_check(requirement, head)
                if correct:
                    self.here = [2, head]
                    return f"passing value verbatim of type {requirement}"
        if isinstance(head, str):
            # NAME (variables or keywords)
            return self.stage_0_name(head)
        elif isinstance(head, Constant):
            return self.stage_0_const(head)
        elif isinstance(head, list):
            self.here = [2, head]
            return "passing list"
        else:
            raise RuntimeError(f"Unexpected token of type {type(head)} in syntax tree: "+str(head))
    def stage_0_name(self, head) -> str:
        DEBUG and print("stage 0 name: "+head)
        if self.index == 0:
            return self.stage_0_name_0(head)
        else:
            return self.stage_0_name_else(head)
    def stage_0_name_0(self, head) -> str:
        DEBUG and print("at index 0")
        if head in STATEMENTS:
            self.here = [1, STATEMENTS[head]]
            return "preparing statement"
        elif head in EXPRESSIONS:
            self.here = [1, EXPRESSIONS[head].statement_version]
            return "preparing expression as statement"
        else:
            del self.here
            return "ignoring effectless variable reference: "+head
    def stage_0_name_else(self, head) -> str:
        DEBUG and print("at index "+str(self.index))
        if head in EXPRESSIONS:
            self.here = [1, EXPRESSIONS[head]]
            return "preparing expression"
        elif head in self.context[vars]:
            self.here = [2, self.context[vars].get_ref(head)]
            return "passing variable"
        else:
            raise NameError("Undefined variable: "+head)
    def stage_0_const(self, head) -> str:
        DEBUG and print("stage 0 constant: "+repr(head))
        if self.index == 0:
            del self.here
            return "ignoring effectless constant"
        else:
            self.here = [2, head.value]
            return "passing constant: "+str(head)
    def stage_1(self, head) -> str:
        DEBUG and print("stage 1")
        if isinstance(head, (str, Constant, list)):
            raise RuntimeError(f"Current tree paths would never allow <[1, {type(head)}]>")
        elif not head.arity:
            self.evaluate()
            return "evaluating 0-arg function"
        else:
            self.stack.append([self.index, head.arity])
            self.index += 1
            return "advancing one level deeper"
    def stage_2(self, head) -> str:
        DEBUG and print("stage 2")
        if not self.stack:
            if self.index > 0:
                raise RuntimeError("Unexpected index greater than zero while index stack is empty")
            del self.here
            return "removing completed statement"
        final, sigs = self.stack[-1]
        arity = len(sigs)
        completed = self.index - final
        requirement = sigs[completed-1]
        assert type_check(requirement, head)
        if completed == arity:
            self.index = final
            self.stack.pop(-1)
            self.evaluate(arity)
            return f"evaluating {arity}-arg function"
        else:
            self.index += 1
            return "advancing to next arg"
    STAGES = [stage_0, stage_1, stage_2]
    def evaluate(self, arity_hint:int=None):
        DEBUG and print("evaluating a statement with arity "+str(arity_hint))
        stage, head = self.here
        if stage != 1:
            raise RuntimeError("Internal data failure (after preparing N arguments "+
                "for something, upon looking back, it was no longer waiting at stage 1)")
        if arity_hint is None:
            arity_hint = len(head.arity)
        arguments = [evaluation_prune(i[1]) for i in self.popn(arity_hint)]
        result = head.function(arguments, self.context)
        self.here = [2*(not isinstance(result, Needful)), result]
    def popn(self, n:int) -> list:
        if not n:
            return list()
        i = self.index+1
        return take_last(self.tree, slice(i, i+n, 1))

DEBUG = False
test = {
    0: "push 1 0 1 push 2 0 2 push 3 0 3", # correctly sets stack: 1 = [1], 2 = [2], 3 = [3].
    1: "push 1 0 1 push 1 0 2 push 1 0 3", # correctly sets stack: 1 = [1,2,3].
    2: "push 1 0 1 push 1 0 2 push 1 0 3 print 1 3 flush", # correctly prints 321
    (2,1): "push 1 0 1 push 1 0 2 push 1 0 3 sum 1 3 print 1 1 flush", # correctly prints 6 = 1+2+3
    (2,2): "push 1 0 1 push 1 0 2 push 1 0 3 prod 1 3 print 1 1 flush", # correctly prints 6 = 1*2*3
    3: "push 1 0 1 push 2 0 pop 1 0", # correctly transfers value across
    (4,0): "push 1 0 1 push 1 0 10 push 2 0 pop 1 0", # correctly transfers integer 10
    (4,1): "push 1 0 1 push 1 0 10 push 2 0 pop 1 1", # correctly transfers integer 1
    (4,2): "push 1 0 1 push 1 0 10 push 2 0 pop 1 2", # correctly erroes index OOB
    (4,3): "push 1 0 1 push 1 0 10 push 2 0 pop 1 -1", # correctly errors -1 index
    5: "push 'mmm' 0 macro (push 1 0 1 push 1 0 2)", # correctly defines mmm to be this macro
    (5, 1): "push 'mmm' 0 macro (push 1 0 1 push 1 0 2) call get  'mmm' 0", # correctly performs the action defined by the macro
    (5, 2): "push 'mmm' 0 macro (push 1 0 1 push 1 0 2) call get 'mmm' 0 call get 'mmm' 0", # correctly performs the action defined by the macro twice
    6: "push 1 0 1 push 1 0 5 getting 1 (a b) macro (push 2 0 a push 2 0 a push 2 0 b print 2 3 flush) push 1 0 0 print 1 1 flush",
    # 6: correctly sets a = [5] and b = [1], but INCORRECTLY fails to deallocate them
    # FIXED: inserted .sub so that the subordinate is in charge of the variables
    # .BUG: print attempts to print n+1 items instead of n
    # FIXED: misimplementation in D_Buffer
    (6, 1):"push 1 0 1 push 1 0 5 getting 1 (a b c) macro (flush)",
    # incorrectly hits index error: only erroring at dereference step.
    # FIXED: throws index error at allocation step
    (6, 2):"push 1 0 1 push 1 0 5 getting 1 (a a) macro (push 1 0 a print 1 1 flush)",
    # correctly sets a = [5, 1] and consequently only allows the value '1' to be accessed
    (6, 3):"push 1 0 1 push 1 0 5 popping 1 (a b) macro (push 1 0 a push 1 0 b print 1 2 flush)",
    # correctly prints '15' and the values are gone from the stacks
    7:"push 1 0 1 push 1 0 5 pop 1 0 print 1 1 flush", # correctly pops <5>
    (7, 1): "push 1 0 1 push 1 0 5 push 1 0 7 pop 1 1 print 1 2 flush", # correctly prints 71
    (7, 2): "push 1 0 1 push 1 0 get 1 0 pring 1 2 flush",
    # NOTE: it interprets 'pring' as a redundant variable mention
    # it then ignores the redundant instances of 1 and 2
    # and ends up printing nothing
    (7, 2, 1): "push 1 0 1 push 1 0 get 1 0 print 1 2 flush", # correctly prints 11
    (7, 3): "push 1 0 1 push 1 0 5 push 1 0 7 del 1 1 print 1 2 flush", # correctly prints 71
    (7, 4): "push 1 0 1 push 1 0 5 dup 1 0 1", # correctly has 1,5,1
    (7, 5): "push 1 0 1 push 1 0 5 dup 1 1 1", # correctly has 1,1,5
    (7, 6): "push 1 0 1 push 1 0 5 dup 1 2 1", # correctly has 1,1,5
    (7, 7): "push 1 0 1 push 1 0 5 dup 1 3 1", # incorrectly has 1,1,5
    # FIXED: implementation of 'push' falsely assumed that python list.insert would error for unreasonable indices
    (8, 0): "push 1 0 4 push 1 0 3 push 1 0 2 push 1 0 1 flip 1 0 3 print 1 4 flush", # 3214
    (8, 1): "push 1 0 4 push 1 0 3 push 1 0 2 push 1 0 1 flip 1 0 2 print 1 4 flush", # 2134
    (8, 2): "push 1 0 4 push 1 0 3 push 1 0 2 push 1 0 1 flip 1 1 3 print 1 4 flush", # 1324
    (8, 3): "push 1 0 4 push 1 0 3 push 1 0 2 push 1 0 1 flip 1 3 0 print 1 4 flush", # 3214
    # all four CORRECT; notice (8,3) == (8,0)
    (8, 4): "push 1 0 4 push 1 0 3 push 1 0 2 push 1 0 1 rot 1 0 3 1 print 1 4 flush", # 3124
    (8, 5): "push 1 0 4 push 1 0 3 push 1 0 2 push 1 0 1 rot 1 3 0 1 print 1 4 flush", # 2314
    (8, 6): "push 1 0 4 push 1 0 3 push 1 0 2 push 1 0 1 rot 1 3 0 -1 print 1 4 flush", # 3124
    (8, 7): "push 1 0 4 push 1 0 3 push 1 0 2 push 1 0 1 rot 1 0 3 -1 print 1 4 flush", # 2314
    (8, 8): "push 1 0 4 push 1 0 3 push 1 0 2 push 1 0 1 rot 1 0 3 -3 print 1 4 flush", # 1234
    # all five CORRECT
    9: "push 1 0 read print 1 1 flush",
    # correctly passes an input string
    (10, 1): "push 1 0 1 "*1 + "push 2 0 size 1 print 2 1 flush print 1 size 1 flush",
    (10, 4): "push 1 0 1 "*4 + "push 2 0 size 1 print 2 1 flush print 1 size 1 flush",
    (10, 15): "push 1 0 1 "*15 + "push 2 0 size 1 print 2 1 flush print 1 size 1 flush",
    # correctly reads inputs without destroying them
    11: "push 1 0 1 push 1 0 5 push 1 0 7 clone 1 2 3", # correctly clones 3 values from 1 to 2
    (11, 1): "push 1 0 1 push 1 0 5 push 1 0 7 clone 1 2 4", # correctly errors
    12: "push 1 0 1 push 1 0 1 push 1 0 5 push 1 0 5 push 1 0 7 ieq 1 4 print 1 4 flush",
    13: "if eq 'yes' read macro (push 1 0 'correct' print 1 1 flush)",
    # correctly performs this action only when the correct password is entered
    14: "push 0 0 3 push 0 0 5"
        "push 'prin' 0 macro (print 0 2 flush clone 0 0 2)"
        "popping 'prin' (prin) macro (clone 0 0 2"
        " push 0 0 or 0 2 push 0 0 'or ' call prin" # 7
        " push 0 0 nor 0 2 push 0 0 'nor ' call prin" # -8 == ~7
        " push 0 0 xor 0 2 push 0 0 'xor ' call prin" # 6
        " push 0 0 nxor 0 2 push 0 0 'nxor ' call prin"
        " push 0 0 and 0 2 push 0 0 'and ' call prin" # 1
        " push 0 0 nand 0 2 push 0 0 'nand ' call prin"
        " push 0 0 shift pop 0 0 pop 0 0 push 0 0 'shift ' call prin" # 5<<3 == 40
        " push 0 0 pow pop 0 0 pop 0 0 push 0 0 'pow ' call prin" # 5**3 == 125
        " div 0 push 0 1 ' div ' print 0 3 flush clone 0 0 2" # divmod(5,3) == (1,2)
        ")",
    # correctly prints the expected results
    15: "call macro ("
        " push 0 0 read"
        " push 0 0 ~5" # ~5 = -5-1; the -1 offsets the 'size 0' entry
        " push 0 0 size 0"
        " push 0 0 sum 0 2"
        " clone 0 2 size 0"
        " print 2 size 2 flush"
        " if pop 0 0 current" # RECURSION method
        ") push 0 0 size 0 push 0 0 'DONE: ' print 0 size 0 flush",
    (15, 1): "call macro ("
        " push 0 0 read"
        " push 0 0 ~5"
        " push 0 0 size 0"
        " push 0 0 sum 0 2"
        " clone 0 2 size 0"
        " print 2 size 2"" flush"
        " if pop 0 0 repeat" # WHILE/GOTO/LOOP method
    # correctly loops, collecting 5 strings, and printing them in reverse order of appearance
    # !!! NEED TO TEST:
    # string operations
    # misc. operations
    # 'slice'
    }

def lexit(code):
    buffer = Lexer(code)
    list(buffer)
    return buffer.result

tests = dict((i, lexit(j)) for i, j in test.items())
engines = dict((i, Engine(j)) for i, j in tests.items())

def mex(*keys):
    #return Engine(lexit(eval("test"+str(list(keys)))))
    return Engine(eval("engines"+str(list(keys))).macro.routine)

QUITS = {
    "quit",
    "exit"
    }
HELPS = {"?", "help"}
def interpret_line(user_in, line):
    if user_in in {"quit", "exit"}:
        return ("exiting console...", False)
    if user_in in {"?", "help"}:
        return ("\n".join((
            "QUITS lists all valid quit commands",
            "HELPS lists all valid commands to print this statement",
            "INPUTS lists your input history for this session",
            "OUTPUTS lists the console's print history",
            "all other actions and behaviors simply use python's <eval> statement",
            "the 'mex' function will return an <Engine> object using test code corresponding"
            " to the input keys: mex(2,1) uses test[2,1] for example. <Engine> objects can be"
            " iterated over, showing the various steps of computation. To ignore those steps,"
            " perform '_ = list(<Engine>)', which will evaluate the entire program to completion"
            " before finally setting '_' equal to the output history.",
            "Note that this language's interpreter is very inefficient on the interpretation level."
            )), True)
    try:
        return (eval(user_in, globals(), globals()), True)
    except SyntaxError:
        try:
            exec(user_in, globals(), globals())
            return ("executed line", True)
        except Exception as e:
            return (e, True)
    except Exception as e:
        return (e, True)

INPUTS = []
OUTPUTS = []
def console_loop():
    line = 0
    loop = True
    while loop:
        user_in = input(f"Rambling [{line}]:")
        INPUTS.append(user_in)
        line += 1
        line_out, loop = interpret_line(user_in, line)
        OUTPUTS.append(line_out)
        print(line_out)

def main():
    console_loop()
