# Zabbix template creation

DESCRIPTION:

Create Zabbix template based on template definition file.


LIMITATION:

1.Only create one template one run.

2.Only support creating items when 'type of information' is 'log'.

3.Only support creating triggers when 'funtion' is 'iregexp' in expressions.


PROCEDURE:

1.Uncompress this package in work directory on HWM node.

2.Fill template and regular expression definition in excel file such as 'Template definition example.xlsx'.
(In the example excel, contents in sheet 'template definition' will be converted into ZBX format in sheet 'zbxformat')

3.Copy contents without title in 'zbxformat' sheet to file such as 'item_example.csv', 
which will be the input file of 'zbx_template_create.py'.

4.Copy contents without title in 'regular expression' sheet to file such as 'regexp_example.csv',
which will be another input file of 'zbx_template_create.py'.

5.Run command such as below to create template, and regular expressions if necessary.

  python zbx_template_create.py item_example.csv -r regexp_example.csv


COMMAND HELP:

usage: zbx_template_create.py [-h] [-v] [-r REG_FILE] [-y] [-m] file

Add items for Zabbix template.

positional arguments:
  file                  Zabbix item definition file

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -r REG_FILE, --regexp REG_FILE
                        Zabbix regular expressions definition file
  -y, --yes             send YES in interactive mode
  -m, --multi_condition
                        set multi conditions in trigger expression
