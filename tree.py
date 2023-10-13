#!/bin/env python3
import sys , typing , textwrap
import argparse
import tomli
#import tomllib
#XXX : `tomllib` is in python 3.11 stdlib
#But std `tomllib` don't support dump
#import tomli_w
#XXX : Array of Tables is preffered but tomli_w try inline table/list at first
import toml as tomli_w
class tomllib :
	def loads(s:str) : return tomli.loads(s)
	#def dump(obj,fp) : return tomli_w.dump(__obj=obj,__fp=fp)
	def dumps(obj)   : return tomli_w.dumps(obj)
import json as jsonlib
import yaml as yamllib
from functools import reduce

toml_limits = [
'null' ,
'single value or single list' ,
'YAML refrence' ,
]
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter , description=
f'''
`append, `set , `delete or `get a value in a tree structure and output the new structure.
Tree structure can be described by TOML, JSON or YAML from standard input.
	`=` for `set. Use `-a` option to append.
	`-` for `delete
	`?` for `get
if `delete or `get, `-` or `?` must be the first argument, and follow each level to access
if `set or `append, `=` must be the last but one argument.
	Put each level to access before it.
	Put the value to set or appended after it.
	The value to set should be JSON string format.
Use `-r` option to `append or `set a structure which the first node named "-" or "?",
otherwise it will be treated as `delete or `get.
`--` for treat all string after is not options. `--` twice to add "--" itself at first.
	Refers to python std `argparse`.
''' , epilog =
f'''
e.g. {sys.argv[0]} -- \? a b -c d <<< '{{"a":{{"b":{{"-c":{{"d":64}}}}}}}}'
e.g. {sys.argv[0]} -T - a b c d <<< '{{"a":{{"b":{{"c":{{"d":64}}}}}}}}'
e.g. {sys.argv[0]} -Y -a a another = value <<< '{{"a":{{"b":{{"-c":{{"d":64}}}}}}}}'
e.g. {sys.argv[0]} -P a b = '{{"$HOME":"JSON/YAML/TOML object is right"}}' <<< '{{"a":{{"b":{{"-c":{{"d":64}}}}}}}}'
e.g. {sys.argv[0]} -A m = new <<< '{{"a":{{"m":1}},"b":{{"m":1}}}}'
e.g. {sys.argv[0]} -A - m  <<< '{{"a":{{"m":1}},"b":{{"m":1}}}}'
e.g. {sys.argv[0]} -A 0 = new <<< '{{"a":[0,1,2,3],"b":["to","never mind"]}}'
e.g. {sys.argv[0]} -A - 1 <<< '{{"a":[0,1,2,3],"b":["to","never mind"]}}'
'''
)
parser.add_argument('-a' , action="store_true" , help=
'''
Append if given key not exists in tree.
'''
)
parser.add_argument('-r' , action="store_true" , help=
'''
For distingush conflict of tree that the last but one node is "="
or the first node is "-"/"?".
`append or `set when appears, otherwise `delete or `get.
'''
)
parser.add_argument('-y' , action="store_true" , help=
'''Input as YAML. Think about '[any]', it can be a TOML empyt table and a YAML list.'''
)
parser.add_argument('-J' , action="store_true" , help='Output as JSON(default)')
parser.add_argument('-Y' , action="store_true" , help=
'''
Output as YAML.
Note that YAML may output a document start/end line "---" or "..."
'''
)
parser.add_argument('-T' ,  action="store_true" , help=
f'''
Output as TOML.
Note that {toml_limits} is not supported in TOML.
'''
)
parser.add_argument('-P' , action="store_true" , help=
'''Output as pure output of py`print()` without newline end.'''
)
parser.add_argument('-A' , action="store_true" , help=
'''
Change all. Only valid in `set and `delete.
'''
)
args,todo = parser.parse_known_args()

#FIXME :
	#confilict between TOML and others : '[any]'
def loads(tree:str) :
	if args.y :
		tree = yamllib.safe_load(tree)
		return tree
	try :
		tree = jsonlib.loads(tree)
	except Exception as jsone :
		try :
			tree = tomllib.loads(tree)
		except Exception as tomle :
			try :
				tree = yamllib.safe_load(tree)
			except Exception as yamle :
				print(f'TOML : {tomle}' , file=sys.stderr)
				print(f'JSON : {jsone}' , file=sys.stderr)
				print(f'YAML : {yamle}' , file=sys.stderr)
				raise Exception('Format' , 'Details is on the top')
	return tree
def dump(todump) :
	if None : pass
	elif args.J : print(jsonlib.dumps(todump))
	elif args.Y : print(yamllib.dump(todump) , end='')
	elif args.T :
		try :
			print(tomllib.dumps(todump) , end='')
		except Exception :
			raise Exception("TOML" , textwrap.dedent(
				f'''
				Error when try to ouput TOML.
				If other formats is valid, maybe {toml_limits} in tree
				'''
			).replace('\n','').replace('\r',''))
	elif args.P : print(todump , end='')
	else : print(jsonlib.dumps(todump) , end='') #`-J` by default
def check(op:str , suppose:set) -> str :
	if not op in suppose :
		raise Exception('Usage', textwrap.dedent(
			f'''
			if you want to `delete or `get, the first argument should be one of {{"-","?"}} but now "{op}".
			if you want to `append or `set, the last but one argument should be one of {{"="}} but now "{op}".
			'''
		).replace('\n','').replace('\r',''))
	else : return op

tree = sys.stdin.read()
tree = loads(tree)

if not todo : pass
elif todo[0] == '--' : del todo[0]

if not todo : pass
elif args.r :
	if len(todo) < 2 : raise Exception('Usage' , 'At least 1 value for `append and `set')
	op = check(todo[-2] , {'='})
	todo = [todo[:-2] , todo[-1]]
elif todo[0] in {'-','?'} :
	op = check(todo[0] , {'-','?'})
	todo = [todo[1:] , 'null']
else :
	if len(todo) < 2 : raise Exception('Usage' , 'At least 1 value for `append and `set')
	op = check(todo[-2] , {'='})
	todo = [todo[:-2] , todo[-1]]

if not todo : pass
else :
	todo[0] = [loads(t) for t in todo[0]]
	todo[-1] = loads(todo[-1])

#FIXME when update to python 3.10+ : `match` - `case
if not todo : dump(tree)
elif op == '?' :
	if args.A : raise Exception('Usage' , 'Can not get all by `-A`')
	todo[0] = [tree] + todo[0]
	dump(reduce(lambda d,k : d[k] , todo[0]))
elif op == '=' :
	if args.a :
		if args.A : raise Exception('Usage' , 'Can not append all by `-A`')
		if todo[0] == [] : raise Exception('Usage' , 'Can not append out of itself')
		todo[0] = [tree] + todo[0]
		reduce(lambda d,k : d.setdefault(k,{}) , todo[0][:-1])[todo[0][-1]] = todo[1]
	else :
		if args.A :
			if not len(todo[0]) == 1 : raise Exception('Usage' , 'Can not set multi key or none key by `-A`')
			def lapply(tree) :
				def rapply(k) :
					#print(f'{dump(k)},{dump(todo[0][0])} : {k == todo[0][0]}')
					if k == todo[0][0] : tree[k] = todo[1]
					else : lapply(tree[k])
				if isinstance(tree,dict) : list(map(rapply,tree))
				elif isinstance(tree,list) : list(map(rapply,range(len(tree))))
			lapply(tree)
		else :
			if todo[0] == [] : tree = todo[1]
			else :
				todo[0] = [tree] + todo[0]
				toset = reduce(lambda d,k : d[k] , todo[0][:-1])
				toset[todo[0][-1]]
				toset[todo[0][-1]] = todo[1]
				#To prevent add key to root node, split `reduce` and assignment
	dump(tree)
elif op == '-' :
	if args.A :
		if not len(todo[0]) == 1 : raise Exception('Usage' , 'Can not set multi key or none key by `-A`')
		def lapply(tree) :
			def rapply(k) -> list :
				if k == todo[0][0] : return [k]
				else :
					lapply(tree[k])
					return []
			if isinstance(tree,dict) :
				todel = reduce(lambda l1,l2 : l1 + l2 , map(rapply,tree) , [])
			elif isinstance(tree,list) :
				todel = reduce(lambda l1,l2 : l1 + l2 , map(rapply,range(len(tree))) , [])
			else : todel = []
			for k in todel : del tree[k]
		lapply(tree)
	else :
		if todo[0] == [] : tree = None
		else :
			todo[0] = [tree] + todo[0]
			del reduce(lambda d,k : d[k] , todo[0][:-1])[todo[0][-1]]
	dump(tree)
else : raise Exception('Program Logic' , 'Please contact the author')
