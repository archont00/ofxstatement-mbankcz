# ofxstatement-mbankcz
This is a parser for CSV transaction history exported from mBank S.A. (Czech Republic) from within the report in Account History (CSV).

The expected field separator is semicolon (";") and character encoding Win-1250.

It is a plugin for [ofxstatement](https://github.com/SinyaWeo/ofxstatement-mbankcz).

It is based on:
- [ofxstatement-equabankcz](https://github.com/kosciCZ/ofxstatement-equabankcz).
- [ofxstatement-mbankcz](https://github.com/SinyaWeo/ofxstatement-mbankcz) by SinyaWeo
- [ofxstatement-mbankcz](https://github.com/dvdkon/ofxstatement-mbankcz) by dvdkon, who modified the plugin so that extra head/tail lines of CSV file do not have to be deleted.

This version changes the behaviour when `"#Plátce/Příjemce"` is empty:
- The original plugin sets `"-"` to field OFX.NAME when there's no Payee in the CSV file. However, GnuCash then displays this useless character in the main `Description` field.
- This modified version of plugin keeps OFX.NAME empty and allows GnuCash to import OFX.MEMO to both `Description` and `Notes` fields.  

## Usage
:exclamation: This version accepts the CSV file as is - no need to manually delete redundant lines.
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
account = mKonto
```

## Issues
If you have an improvement, feel free to open an issue or a pull request.
