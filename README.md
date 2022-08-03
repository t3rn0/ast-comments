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
>>> import ast_comments as astcom
>>> tree = astcom.parse("hello = 'hello' # comment to hello")
```
Parsed tree is instance of the original ast.Module object
```
>>> tree
<_ast.Module object at 0x7ffba52322e0>
```
Any "statement" node of the tree has `comments` field
```
>>> tree.body[0].comments
('comment to hello',)
>>> astcom.dump(tree)
"Module(body=[Assign(targets=[Name(id='hello', ctx=Store())], value=Constant(value='hello', kind=None), type_comment=None, comments=('comment to hello',))], type_ignores=[])"
```

## Contributing
You are welcome to open an issue or create a pull request