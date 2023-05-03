# ofxstatement-mbankcz
This is a parser for CSV transaction history exported from mBank a.s. (Czech Republic) from within the report in Account History (CSV).

The expected field separator is semicolon (";") and character encoding Win-1250.

It is a plugin for [ofxstatement](https://github.com/SinyaWeo/ofxstatement-mbankcz).
I've based this on  the [ofxstatement-airbankcz](https://github.com/milankni/ofxstatement-airbankcz) plugin.

## Usage
```shell
$ ofxstatement convert -t mbankcz movements.csv mbank.ofx
```
## Configuration
```shell
$ ofxstatement edit-config
```
And enter e.g. this:
```
[mbankcz]
plugin = mbankcz
currency = CZK
account = mBank CZK
```

## Issues
I've created this to conform mainly to my needs, so it is possible that I haven't
covered all possible transaction types, etc. If you have an improvement, feel free
to open an issue or a pull request.
