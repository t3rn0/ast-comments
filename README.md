# ast-comments

A Python extension to the built-in `ast` module that preserves comments in the Abstract Syntax Tree.
This library finds comments in source code and includes them as nodes in the parsed AST.

## Installation
```
pip install ast-comments
```

## Usage

Usage is identical to the standard `ast` module:
```
>>> from ast_comments import *
>>> tree = parse("hello = 'hello' # comment to hello")
```
The parsed tree is an instance of the original `ast.Module` object.
The only difference is that there is a new type of tree node: `Comment`.
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
If you have Python 3.9 or above, you can also unparse the tree object with its comments preserved:
```
>>> print(unparse(tree))
hello = 'hello'  # comment to hello
```
**Note**: Python's `compile()` function cannot be used directly on the parsed tree output. The included `pre_compile_fixer()` function can be used to prepare the tree for compilation by stripping comment nodes when needed.

Additional examples can be found in the test files: `test_parse.py` and `test_unparse.py`.

## Contributing
Contributions are welcome! Please feel free to open an issue or create a pull request.
