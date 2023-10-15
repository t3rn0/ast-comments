# ast-comments

An extension to the built-in `ast` module. 
Finds comments in source code and adds them to the parsed tree.

## Installation
```
pip install ast-comments
```

## Usage

There is no difference in usage between `ast` and `ast-comments`
```
>>> from ast_comments import *
>>> tree = parse("hello = 'hello' # comment to hello")
```
Parsed tree is an instance of the original `ast.Module` object.
The only difference is that there is a new type of tree node: `Comment`
```
>>> tree
<_ast.Module object at 0x7ffba52322e0>
>>> tree.body
[<ast.Assign object at 0x10a01d5b0>, <ast_comments.Comment object at 0x10a09e0a0>]
>>> tree.body[1].value
'# comment to hello'
>>> dump(tree)
"Module(body=[Assign(targets=[Name(id='hello', ctx=Store())], value=Constant(value='hello')), Comment(value='# comment to hello', inline=True)], type_ignores=[])"
```
If you have python3.9 or above it's also possible to unparse the tree object with its comments preserved.
```
>>> print(unparse(tree))
hello = 'hello'  # comment to hello
```
More examples can be found in test_parse.py and test_unparse.py.

## Contributing
You are welcome to open an issue or create a pull request
