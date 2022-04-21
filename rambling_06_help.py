# -*- coding: utf-8 -*-
"""
Created on Fri Mar 18 16:37:04 2022
Created on Mon Mar 14 00:00:33 2022
Created on Fri Mar  4 13:37:57 2022

@author: TARDIInsanity

the program will simply crash on type errors.
you will be informed of the type of type error.

FORMAL STYLE GUILDELINES:
    choose ONE name to reserve for function arguments and return values

there are 2.4 types of phrases:
    __statement__ # may only occur in a __routine__
        __routine__ # a list of __statement__s separated by any whitespace
            __program__ # the whole file which is uniquely allowed to stand alone
    __expr__ # returns a value
        if an expression occurs in the context of a statement,
        it will be optimized for ignoring its return value.
        this means all constants at the routine level are ignored by the parser
        and therefore comments can simply be strings that appear in the code
        __nullary__ # an expression that takes zero arguments
            __const__ # a constant value from the source code

there are 3.1 types of data objects:
    int # an integer. simple.
    str # a string. simple.
        chr # a string of length 1.
    macro # a macro object, basically a function

GUIDE:
    the entire file being executed is considered a "macro".
    * refers to a valid pythonic identifier
    an __expr__ (expression) will pause outside computation, evaluate its contents,
        and then the result is used in place of wherever __expr__ appeared.
    a __routine__ is a whitespace-separated list of statements
    when indices are accessed, unless otherwise specified, negative values result in an index error.
    lines beginning with ~~~ represent deliberately unimplemented features
    stack names can be any integer or string
    stacks are created and removed automatically

meta __expr__ templates:
    *
        traditionally known as a 'local variable'.
        refers to the last locally defined value for that identifier

function __expr__ templates:
    macro (__routine__)
        returns a function that simply performs that routine
    current
        returns a reference to the macro in which it was called.
        i expect the most common idiom with this to be "if ... current" (recursion)
    break
        returns a function which, when called, will exit the function in which it was named
        (execution is moved to the end of the __routine__ in which the 'break' keyword was evaluated)
        when a function exits, the associated <break> function deactivates, and does nothing when called
        one function's break CAN be called from a nested function if its reference is passed along.
        
        don't get too optimistic though - all variables are active stacks.
        all variables can be overwritten in a new context, and functions use the updated values.
        whenever a __routine__ ends, all variables it overwrote are reverted.
    repeat
        returns a function which, when called, will return evaluation to the beginning of its routine
        this is essential for performing for & while loops without using recursion

contextual __statement__ templates:
    popping __name__ (*0 *1 *2...) __macro__
        for n-many identifiers in (*0 *1 *2...)
        pops the first n elements from __name__
        defines them respectively (index 0 <-> *0)
        calls the __macro__
        undefines them
    getting __name__ (*0 *1 *2...) __macro__
        simply gets the first n elements instead of popping them

function __statement__ templates:
    call __function__
        trivially equivalent to "if 1 __function__"
    if __value__ __function__
        calls __function__ if and only if bool(__value__).
        pythonic bool() conversion.
        this is technically unnecessary:
            push buffer macro ()
            push buffer __function__
            # CONVERT __value__ TO EITHER 0 OR 1; for integers: perform 0**x
            del buffer __value__ # deletes <pass> if 1, deletes <function> if 0.
            call pop buffer 0
        however, needing 1 preparatory command and 4 standard commands for every <if> is excessive
        even though this method DOES allow you to perform arbitrary integer branching

stack __expr__ templates:
    pop __name__ __i__ # get & del at the same time
        pop __name__ 0 -> pops the first element
        pop __name__ 1 -> pops the second element
        ...
        as a statement: 'pop' is replaced with 'del'
    get __name__ __i__ # returns an element from __name__
        as a statement: 'get' does nothing
    size __name__
        returns, as a nonnegative integer, the length of the current stack.
        this is MUCH more optimized than any alternative.

stack __statement__ templates:
    clone __source__ __destination__ __n__
        copies the first __n__ elements from __source__ to __destination__
        in the same order (index 0 in source -> index 0 in dest)
        the destination can be the same as the source.
    dup __name__ __i__ __j__
        reusing the value for __name__,
        push __name__ __j__ get __name__ __i__
    del __name__ __i__
        discards the element at index __i__
    push __name__ __i__ __value__
        will insert __value__ onto the stack before element __i__
        such that "get __name__ __i__" returns __value__
    flip __name__ __start__ __end__
        flips a segment of a stack.
        min = min(__start__, __end__)
        max = max(__start__, __end__)
        the flipped segment includes <min> and excludes <max>
        formally: index <min + i> moves to <max + ~i>
    swap __alpha__ __i__ __beta__ __j__
        swaps the values of <get __alpha__ __i__> and <get __beta__ __j__>
    rot __name__ __start__ __end__ __n__
        rotates a segment of a stack.
        pulls the last (=greatest index) __n__ values to the front (=least index) of the range
        negative __n__ reverses this effect (NOT flip)
        __start__ > __end__ reverses this effect (NOT flip)
        ... both at the same time cancel out.
        length = abs(__start__ - __end__)
        if length is zero, nothing happens.
        n = __n__ % length
        if n is zero, nothing happens.

string __expr__ templates:
    read
        returns an input string in its entirety
    len __target__
        if __target__ is a string:
            returns, as a nonnegative integer, the length of a given string.
        if __target__ is a function:
            returns the number of lines in the function
            redundant constants DO count towards this number
    slice __value__ __start__ __end__
        if __start__ is an integer:
            uses __start__%len(__value__) for __start__
        if __start__ is a string:
            if __start__ is not in __value__:
                uses 0 for __start__
            uses __value__.index(__start__)+len(__start__) for __start__
        if __end__ is an integer:
            uses __end__%len(__value__) for __end__
        if __end__ is a string:
            if __end__ is not in __value__:
                uses len(__value__) for __end__
            uses __value__.index(__end__) for __end__
        
        if __start__ >= __end__: returns ""
        otherwise: returns __value__[__start__:__end__]
    cat __name__ __n__ __joiner__
        converts the first __n__ values on __name__ to strings.
        concatenates them, inserting __joiner__ (as a string) between them,
        so the result will start with input[0].
        if __n__ <= 0: returns ""

string __statement__ templates:
    print __name__ __n__
        appends the first __n__ items to the end of the print buffer.
        input[0] is pushed first, etc.
    flush
        prints the print buffer in the order items were pushed and then prints a newline.
        integers are printed as their string representations.
    split __name__ __string__ __value__
        onto stack __name__...
        if __value__ is a string:
            if value is "": pushes list(__string__)
            pushes __string__.split(__value__)
        if __value__ is an int:
            splits __string__ into __value__-length segments
            the remainder is then pushed to the end, even if it is the empty string.
            if __value__ is 0:
                just as with "div", the remainder is the entire string, and there is no quotient.
            if __value__ < 0:
                divides the string into segments starting from the end, instead of the beginning.

integer __expr__ templates:
    shift __target__ __n__
        "left shift"
        if __target__ is 0 or __n__ is 0: returns __target__
        if __n__ < 0: returns __target__ >> -__n__
        otherwise: returns __target__ << __n__
    pow __base__ __n__
        if __n__ == 0 or __base__ == 1: returns 1
        if __n__ < 0 or __base__ == 0: returns 0
        if __base__ == -1: returns __base__ ** (__n__ % 2)
        otherwise: returns __base__ ** __n__
        notice: "-(__n__ == 0)" <-> "0 ** __n__"
    log __target__ __base__
        using the absolute value of both values...
        if __target__ == 0: returns -1
        if __base__ == 0: returns 0
        if __base__ == 1: returns __target__ (works as the absolute value function)
        otherwise: returns floor(log(__target__, base=__base__))
    sign __target__
        returns -1 if __target__ < 0
        returns 1 if __target__ > 0
        returns 0 if __target__ == 0
    neg __value__
        numerically negates an int
    not __value__
        bitwise negates an int; or takes boolean not of a string.
        empty strings become -1, other strings become 0

nary integer __expr__ templates:
    these pop & combine the first __n__ elements from __name__
    non-integers result in TypeErrors
    OP : the operaiton
    ZID : the identity element returned when __n__ <= 0
    sum __name__ __n__ # OP: +; ZID: 0
    prod __name__ __n__ # OP: *; ZID: 1
    and __name__ __n__ # OP: &; ZID: -1
    nand __name__ __n__
        negates the result of "and"
    or __name__ __n__ # OP: |; ZID: 0
    nor __name__ __n__
        negates the result of "or"
    xor __name__ __n__ # OP: ^; ZID: 0
        for each bit returns 1 if an odd number of them are set
        notice: ~xor(a0, a1, a2...) = xor(~a0, a1, a2...) = xor(a0, ~a1, a2...) = ...
    nxor __name__ __n__
        negates the result of "xor"

integer __statement__ templates:
    div __name__
        pops the first two elements
        (index 0 is the dividend, index 1 is the divisor)
        if divisor == 0: <mod> = dividend, <div> = 0
        if divisor < 0: <mod> <= 0
        always: divisor = <div>*dividend + <mod>
        pushes <mod> and then <div>, so that
        index 0 is the quotient, and
        index 1 is the remainder.

stack-len preserving integer __statement__ templates:
    sort __name__ __n__
        pops the first __n__ elements, sorts them, and pushes them back onto __name__
        all functions will appear first
        followed by all strings
            strings are sorted alphabetically (python sort)
        followed by all ints
            ints are sorted in ascending order (end of list == most positive integer)
    ineg __name__ __n__ # algebraic NEG
        in-place negates the first __n__ elements.
        some properties:
            x & -x = smallest binary bit of x
            x + -x = 0 = ; x | -x = -(x & -x); x ^ -x = -2*(x & -x)
            neg is self-reversing
    inot __name__ __n__ # bitwise NOT
        in-place inverts the first __n__ elements
        some properties:
            x + ~x = x | ~x = x ^ ~x = -1; x & ~x = 0
            empty strings become -1, other strings become 0
            not is self-reversing for integers
    bitsort __name__ __n__ # sorts the bits in the first __n__ values so that the last value has the fewest
        this is implemented via a boolean bubble sort method, repeating about __n__ times:
            ant, sub = (ant|sub, ant&sub)
        [O(n^2) each: read, calc, set]
        the first value is the OR reduction
        the second value is the traditional XOR reduction (exactly 1: xor(1,1,1) = 0)
        the last value is the AND reduction
        
        note: bitsort S N will return a list of integers with special properties
            outlined in the bitsort package included with this file.
    bitgrad __name__ __n__
        leading = <values>[1:]
        following = <values>[:-1]
        result = [i & ~j for i, j in zip(leading, following)]
        it finds all *descending* bits in the sequence, all the bits where they transition from 1 to 0.
        to find the ascending bits, reverse the sequence, perform this, and reverse it again.
        
        note: bitsort S N bitgrad S N will return a list of integers with a special property
            result[i] has bits set wherever EXACTLY i+1 bits were set in the input
            result[0] is always the MONO-XOR (the XOR which is 1 only if exactly 1 bit was set in ALL inputs)
            result[n-1] is always the AND reduction
~~~ nxact __name__ __n__ __k__ # "not xact __name__ __n__ __k__"
~~~ xact __name__ __n__ __k__ # bitwise COUNT
~~~     bits are set in the output when EXACTLY __k__ many bits were set in the input
~~~     for negative values of __k__, set bits when EXACTLY ~__k__ many bits were not set

general __expr__ templates:
    bool __value__
        converts 0 and "" into 0, all else into -1
    eq __a__ __b__
        returns -1 if __a__ and __b__ are the same, else 0
        for ints and strings: __a__ == __b__ is the same as in python
        for functions: __a__ == __b__ exactly when __a__ and __b__ refer to the same internal object
    chr __value__
        converts an integer to a character
    str __value__
        converts to a string representation
    ord __value__
        reverses the <chr> expression
    int __value__
        converts from a string to an integer, if possible

general __statement__ templates:
    IPC: in-place converts the first __n__ values on __name__
    ibool __name__ __n__
        IPC to booleans (each value becomes 0 or -1)
    ieq __name__ __n__
        performs a cyclic equality check
        stack[i] == stack[i+1] -> result[i] for i in range(n-1)
        stack[n-1] == stack[0] -> result[n-1]
        -1 is "True", and 0 is "False".
    ichr __name__ __n__
        IPC from integers to characters
    istr __name__ __n__
        IPC to strings
    iord __name__ __n__
        IPC from characters to integers
    iint __name__ __n__
        IPC from strings to integers, if possible

CHALLENGES
    IF without if
        push 0 0 macro ()
        push 0 0 __function__
        del 0 neg bool __condition__
        # deletes __function__ if FALSE, else deletes macro ()
        call pop 0 0
    IF-ELSE without two ifs
        push 0 0 __false__
        push 0 0 __true__
        call __condition__ # places anything on stack 0
        del 0 neg bool pop 0 0
        call pop 0 0
    
    ... assuming __condition__ pushes its result onto stack 0
    DO-WHILE loops
        call macro (... call __condition__ if pop 0 0 current)
    WHILE-DO loops
        call __condition__
        if pop 0 0 macro (... call __condition__ if pop 0 0 current)
    an ELSE (after WHILE) clause:
        # the do-while version is easiest
        call macro (
            call __body__
            call __condition__
            push 0 0 __else__
            push 0 0 current
            rot 0 3 1
            del 0 pop 0 0
            call pop 0 0
            )
        # while-do, however...
        call macro (
            "any reference to <break> in the loop will NOT trigger the else"
            push 0 0 macro ()
            push 0 0 __else__
            push 0 0 current
            push 0 0 __body__
            call __condition__
            push 0 0 2
            prod 0 2
            push 0 0 1
            sum 0 2
            del 0 get 0 0
            del 0 pop 0 0
            call pop 0 0
            call pop 0 0
            )
        # i guess therefore it is easier to just do a do-while with a forecheck...
        call __condition__
        if pop 0 0 __do_while__
    RANGE using len:
        perform "push i 0 len i" n times. stack i will get range(a, a+n), where <a> is the initial length
    WIPE a stack: "del i len i"
    TRANSFER a stack: "clone a b len a del a len a"

!!! FUTURE FEATURE IMPLEMENTATION IDEAS
    features that i MUST add, but don't know what the best way would be
    EXPR import __filename__
        returns the text contents of a file
    STMT export __filename__ __i__
        inserts the contents of the print buffer at line __i__ in the file
        items are separated by newlines
    EXPR compile __string__
        interprets a string as code; returns a function that would execute that code

!!! HYPOTHETICAL FEATURES
    dictionary object
    EXPR map
        returns a new map object
    maps would allow the same kinds of keys as stacks
    get, pop, del: work in obvious ways where the map is used as the "stack name",
        where stacks will not be allowed to have maps for names.
    push: also obvious, but worth being explicit. it sets a value at a key (map[key] = val)
    ibool, ieq, ichar, iint, iord, istr, sort, ineg, inot, bitsort, bitgrad,
        sum, prod, and, or, xor, nand, nor, nxor: NOT allowed for maps
    print, split, cat, rot, flip: NOT allowed for maps
    getting, popping: these also DON'T work
    both "size" and "len" work on maps.
    SUBHYPOTHETICAL:
        have maps' values be stacks as well; making maps indistinguishable from the global stack container object
        then allow...
        EXPR global
            returns the map that stores all the stacks
        and then have popping & getting take an additional <map> parameter
        and maybe also have a <map> parameter be mandatory for all function calls
        thus allowing for extremely powerful and safe context containment

    # when sensical: gets __name__ and __function__ once, reusing them
    STMT for * __name__ __function__
        # could also be called 'each'
        while len __name__ > 0:
            popping __name__ (*) (call __function__)
        # which is to say: it will assign * to the first value in __name__, popping it.
        # and perform __function; repeating this process until __name__ is empty.
    STMT while __name__ __function__
        # could also be called 'each'
        V1) while len __name__ > 0:
            #optional: del __name__ 0
            calls __function__
        V2) while bool(pop __name__ 0): # may or may not error for empty
            calls __function__
        V3) while bool(get __name__ 0): # may or may not error for empty
            calls __function__
    package:
        EXPR getter (* * *...) __macro__ # returns a reference to the function
        EXPR popper (* * *...) __macro__ # returns a reference to the function
        STMT fcall __name__ __function__ # calls the function on that stack
    package:
        STMT return __value__
        EXPR call __function__ -> __value__
"""

def make_hypothetical(Macro, deep_copy, safe_get_stack, lexit):
    class Fors:
        @staticmethod
        def v1(arguments, context) -> object:
            identifier, stack_name, macr = arguments
            if not isinstance(macr, Macro):
                raise TypeError("attempted to call a non-macro of type"
                                f" ({type(macr)}): {repr(macr)}")
            stack = safe_get_stack("for", stack_name, context)
            if len(stack):
                value = stack.pop(-1)
                macr(context)
                parent = context.chain[-1]
                parent.sub.define(identifier, value)
                parent.inject_after_here(arguments)
                return parent.here[1] # self
            return None # stopiteration
        v1_args = (str, None, None)
    class Whiles:
        @classmethod
        def v1(cls, do_del:bool=False):
            def wrapped(arguments, context) -> object:
                stack_name, macr = arguments
                if not isinstance(macr, Macro):
                    raise TypeError("attempted to call a non-macro of type"
                                    f" ({type(macr)}): {repr(macr)}")
                stack = safe_get_stack("while", stack_name, context)
                if len(stack):
                    if do_del:
                        stack.pop(-1)
                    macr(context)
                    parent = context.chain[-1]
                    parent.inject_after_here(arguments)
                    return parent.here[1] # self
                return None # stopiteration
            return wrapped
        v1_args = (None, None)
        v2_3_funcs = [[(lambda stack: stack and stack.pop(-1)), (lambda stack: stack.pop(-1))],
                      [(lambda stack: stack and stack[-1]), (lambda stack: stack[-1])]]
        @classmethod
        def v2_3(cls, v3:bool=False, error:bool=False) -> callable:
            function = cls.v2_3_funcs[v3][error]
            def wrapped(arguments, context) -> object:
                stack_name, macr = arguments
                if not isinstance(macr, Macro):
                    raise TypeError("attempted to call a non-macro of type"
                                    f" ({type(macr)}): {repr(macr)}")
                if function(safe_get_stack("while", stack_name, context)):
                    macr(context)
                    parent = context.chain[-1]
                    parent.inject_after_here(arguments)
                    return parent.here[1] # self
                return None # stopiteration
            return wrapped
        v2_3_args = (None, None)
    class Manipulators:
        @staticmethod # expr
        def compile(arguments, context) -> object:
            stack_name, = arguments
            stack = safe_get_stack("compile", stack_name, context)
            code = "\n".join(str(i) for i in stack)
            stack = []
            return Macro("__compiled__", lexit(code))
        compile_args = (None,)
        @staticmethod # stmt
        def include(arguments, context) -> object:
            filename, = arguments
            with open(filename, "r") as file:
                text = file.read()
            macro = Macro(filename, lexit("\n".join(text)))
            macro(context)
            return None
        include_args = (str,)
    return {"for":Fors, "while":Whiles, "manipulators":Manipulators}
