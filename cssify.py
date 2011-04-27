#!/usr/bin/python

import re
import sys
from optparse import OptionParser

validation_re = (
                 "(?P<node>"
                   "(?P<position>//?)(?P<tag>[a-zA-Z\*]{1,6})" # //div
                   "(\[("
                     "(?P<matched>(?P<mattr>@?[a-zA-Z]{1,5}(\(\))?)=\"(?P<mvalue>[\w\s]*))\"" # [@id="bleh"] and [text()="meh"]
                   "|"
                     "(?P<contained>contains\((?P<cattr>text\(\)|@[a-zA-Z]{1,5}),\s*\"(?P<cvalue>[\w\s]*)\"\))" # [contains(text(), "bleh")] and [contains(@id, "bleh")]
                   ")\])?"
                   "(\[(?P<nth>\d)\])?"
                 ")"
                 )

prog = re.compile(validation_re)

class XpathException(Exception):
    pass

def cssify(xpath):
    """
    >>> cssify("fail")
    Traceback (most recent call last):
        ...
    XpathException: Invalid or unsupported Xpath: fail
    >>> cssify('//a')
    'a'
    >>> cssify('//a[2]')
    'a:nth(2)'
    >>> cssify('//a//a')
    'a a'
    >>> cssify('//a[@id="myId"]')
    'a#myId'
    >>> cssify('//a[@id="myId"][4]')
    'a#myId:nth(4)'
    >>> cssify('//*[@id="myId"]')
    '#myId'
    >>> cssify('id("myId")')
    '#myId'
    >>> cssify('//a[@class="myClass"]')
    'a.myClass'
    >>> cssify('//*[@class="myClass"]')
    '.myClass'
    >>> cssify('//a[@class="multiple classes"]')
    'a.multiple.classes'
    >>> cssify('//a[text()="my text"]')
    'a:contains(my text)'
    >>> cssify('//a[contains(@id, "bleh")]')
    'a[id*=bleh]'
    >>> cssify('//a[contains(text(), "bleh")]')
    'a:contains(bleh)'
    """

    result = prog.match(xpath)
    if not result:
        raise XpathException("Invalid or unsupported Xpath: %s" % xpath)
    else:
        css = ""
        for node in [n[0] for n in prog.findall(xpath)]:
            log("node found: %s" % node)
            node_match = prog.match(node).groupdict()
            log("broke node down to: %s" % node_match)

            position = " " if node_match['position'] == "//" else " > "
            tag = "" if node_match['tag'] == "*" else node_match['tag']

            if node_match['matched']:
                if node_match['mattr'] == "@id":
                    attr = "#%s" % node_match['mvalue'].replace(" ", "#")
                elif node_match['mattr'] == "@class":
                    attr = ".%s" % node_match['mvalue'].replace(" ", ".")
                elif node_match['mattr'] == "text()":
                    attr = ":contains(%s)" % node_match['mvalue']
                elif node_match['mattr']:
                    attr = "[%s=%s]" % (node_match['mattr'].replace("@", ""),
                                        node_match['mvalue'])
            elif node_match['contained']:
                if node_match['cattr'].startswith("@"):
                    attr = "[%s*=%s]" % (node_match['cattr'].replace("@", ""),
                                         node_match['cvalue'])
                elif node_match['cattr'] == "text()":
                    attr = ":contains(%s)" % node_match['cvalue']
            else:
                attr = ""

            if node_match['nth']:
                nth = ":nth(%s)" % node_match['nth']
            else:
                nth = ""

            node_css = position + tag + attr + nth

            log("final node css: %s" % node_css)

            css += node_css
        css = css.strip()
        return css

if __name__ == "__main__":
    usage = "usage: %prog [options] XPATH"
    parser = OptionParser(usage)
    parser.add_option("-t", "--test",
                      action="store_true", dest="test", default=False,
                      help="run tests")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="print status messages to stdout")

    (options, args) = parser.parse_args()

    if options.verbose:
        def log(msg):
            print "> %s" % msg
    else:
        def log(msg):
            pass

    if options.test:
        import doctest
        doctest.testmod()
    else:
        if len(args) != 1:
            parser.error("incorrect number of arguments")
        try:
            print cssify(args[0])
        except XpathException, e:
            print e
            sys.exit(1)
else:
    def log(msg):
        pass
