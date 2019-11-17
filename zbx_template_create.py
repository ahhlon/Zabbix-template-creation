#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Create one Zabbix template and related regular expression based on csv files
"""

import sys
sys.path.append('./lib')
from pyzabbix import ZabbixAPI, ZabbixAPIException
import argparse
import re
import os
import mysql.connector
import yaml

# Function {
def get_shell_command_result(cmd):
    cmd_result = os.popen(cmd).read()
    return cmd_result
def get_command_line_args():
    parser = argparse.ArgumentParser(description='Add items for Zabbix template.')
    parser.add_argument('-v', '--version', action='version', version=TL_VERSION)
    parser.add_argument(
        'file',
        type = str,
        help='Zabbix item definition file'
    )
    parser.add_argument(
        '-r', '--regexp',
        dest = 'reg_file',
        default = None,
        type = str,
        help='Zabbix regular expressions definition file'
    )
    parser.add_argument(
        '-y', '--yes',
        default=False,
        action='store_true',
        help='send YES in interactive mode'
    )
    parser.add_argument(
        '-m', '--multi_condition',
        dest = 'm',
        default=False,
        action='store_true',
        help='set multi conditions in trigger expression'
    )
    args = parser.parse_args()
    return args

# Insert regexps to Zabbixdb
def add_regular_expressions(regexp, reglist, args_y):
    regexp = "'" + regexp + "'"
    db = mysql.connector.connect(user=zbx_db_usr,passwd=zbx_db_pw,database=zbx_db_name)

    cursor = db.cursor()

    sql_exi_reg = "select regexpid from regexps where name=%s;" % \
                (regexp)
    exi_regid = 0
    try:
        cursor.execute(sql_exi_reg)
        exi_regid = cursor.fetchone()[0]
    except:
        pass
    if exi_regid != 0 and not args_y:
        Ans_reg = raw_input("{0} already exists, do you want to recreate it?[Y/N]".format(regexp)).lower()
        if Ans_reg == 'yes' or Ans_reg == 'y':
            sql_delete_exi_reg = "delete from regexps where name=%s;" % \
                                    (regexp)
            try:
                cursor.execute(sql_delete_exi_reg)
                db.commit()
            except:
                print("Failed to delete {0}".format(regexp))
                db.rollback()
        else:
            return
    elif exi_regid != 0 and args_y:
        sql_delete_exi_reg = "delete from regexps where name=%s;" % \
                                (regexp)
        try:
            cursor.execute(sql_delete_exi_reg)
            db.commit()
        except:
            print("Failed to delete {0}".format(regexp))
            db.rollback()

    #sql_ireg = "select @max_regexpid:=max(regexpid) from regexps;"
    sql_ireg = "select nextid from ids where field_name='regexpid';"
    cursor.execute(sql_ireg)
    iregid = cursor.fetchone()[0] + 1

    sql_insreg = "insert into `regexps` VALUES (%s, %s, %s)" % \
                (iregid, regexp, '\'\'')
    sql_updregid = "update ids set nextid='%s' where field_name='regexpid';" % \
                (iregid)
    try:
        cursor.execute(sql_insreg)
        db.commit()
        print ("Success {0}".format(sql_insreg))
        try:
            cursor.execute(sql_updregid)
            db.commit()
            print ("Success {0}".format(sql_updregid))
        except:
            db.rollback()
            print ("Fail {0}".format(sql_updregid))
    except:
        db.rollback()
        print ("Fail {0}".format(sql_insreg))

    for exp in reglist:
        #sql_iexp = "select @max_expressionid:=max(expressionid) from expressions;"
        sql_iexp = "select nextid from ids where field_name='expressionid';"
        cursor.execute(sql_iexp)
        iexpid = cursor.fetchone()[0] + 1
        for i in range(0, len(exp),1):
            exp[i]="'" + exp[i] + "'"
        sql_insexp = "insert into `expressions` VALUES (%s, %s, %s, %s, %s, %s)" % \
                    (iexpid, iregid, exp[0], exp[1], '\',\'', exp[2])
        sql_updexpid = "update ids set nextid='%s' where field_name='expressionid';" % \
                    (iexpid)
        
        try:
            cursor.execute(sql_insexp)
            db.commit()
            print ("Success {0}".format(sql_insexp))
            try:
                cursor.execute(sql_updexpid)
                db.commit()
                print ("Success {0}".format(sql_updexpid))
            except:
                db.rollback()
                print ("Fail {0}".format(sql_updexpid))
        except:
            db.rollback()
            print ("Fail {0}".format(sql_insexp))
        cursor.close
        db.close

def create_zbx_template(template_name, args_y):
    template = zapi.template.get(filter={"host": template_name})
    if template and not args_y:
        Ans_tpl = raw_input("{0} already exists, do you want to recreate it?[Y/N]".format(template_name)).lower()
        if Ans_tpl == 'y' or Ans_tpl == 'yes':
            template_id = template[0]["templateid"]
            zapi.template.delete(template_id)
        else:
            return
    elif template and args_y:
        template_id = template[0]["templateid"]
        zapi.template.delete(template_id)

    template = zapi.template.create(
        host=template_name,
        groups={"groupid":"1"}
    )
    template_id = template["templateids"][0]
    print("Recreate template with templateid {0}".format(template_id))
    return template_id

def create_zbx_app(template_id, para):
    application_name = para[6]
    application = zapi.application.get(
        filter = {
            "name" : application_name,
            "hostid" : template_id
        }
    )
    if application:
        application_id = application[0]["applicationid"]
        return application_id
    else:
        try: 
            application = zapi.application.create(
                name = application_name,
                hostid = template_id
            )
            application_id = application["applicationids"][0]
            print("Create application with applicationid {0}".format(application_id))
            return application_id

        except ZabbixAPIException as e:
            print(e)
            sys.exit()

def create_zbx_item(template_name, template_id, application_id, para):
    item_name = para[0]
    keys = para[1]
    mon_type = para[5]
    interval = para[2]
    item_trends = para[4]
    global ZBX_VERSION
    if ZBX_VERSION < '3.0.0':
        item_histories = para[3]
    elif ZBX_VERSION > '3.0.0':
        item_histories = para[3] + 'd'

    try:
        item = zapi.item.create(
            hostid=template_id,
            name=item_name,
            key_=keys,
            type=mon_type,
            value_type=2, ### log type
            applications=[application_id],
            delay=interval,
            history=item_histories,
            trends=item_trends,
            status='0'
        )
        item_id = item["itemids"][0]
        print("Added item with itemid {0} to template: {1}".format(item_id, template_name))
        return item_id

    except ZabbixAPIException as e:
        print(e)
        sys.exit()

def create_zbx_trigger_condition(template_name, para):
    keys = para[1]
    regexp = re.compile(r'\[(.*)\]').search(keys).group(1)
    function = 'iregexp'
    global ZBX_VERSION
    if ZBX_VERSION < '3.0.0':
        expressions = '({' + template_name + ':' + keys + '.' + function + '(' + regexp + ')}#0)'
    elif ZBX_VERSION > '3.0.0':
        expressions = '({' + template_name + ':' + keys + '.' + function + '(' + regexp + ')}<>0)'
    return expressions

def create_zbx_trigger_multi_condition(template_name, para):
    keys = para[1]
    function = 'iregexp'
    global ZBX_VERSION
    conditions = []
    for i in range(10, len(para)):
        if ZBX_VERSION < '3.0.0':
            condition = '{' + template_name + ':' + keys + '.' + function + '(' + para[i] + ')}#0'
        elif ZBX_VERSION > '3.0.0':
            condition = '{' + template_name + ':' + keys + '.' + function + '(' + para[i] + ')}<>0'
        conditions.append(condition)
    if ZBX_VERSION < '3.0.0':
        relation = ' & '
    elif ZBX_VERSION > '3.0.0':
        relation = ' and '
    multi_condition = relation.join(conditions)
    expressions = '(' + multi_condition + ')'
    return expressions

def create_zbx_trigger(template_name, para, args_m):
    if args_m:
        expressions = create_zbx_trigger_multi_condition(template_name, para)
    else:
        expressions = create_zbx_trigger_condition(template_name, para)
    trigger_name = para[8]
    priorities = para[7]
    event_gen_mode = para[9]
    try:
        trigger = zapi.trigger.create(
            description = trigger_name,
            expression = expressions,
            priority = priorities,
            status = '0',
            type = event_gen_mode
        )
    except ZabbixAPIException as e:
        print(e)
        sys.exit()
    print("Added trigger with triggerid {0} to template: {1}".format(trigger["triggerids"][0], template_name))
# }

# shell command {
cmd_vip = "cat /etc/hosts | grep -i vip | head -1 | awk '{print $1}'"
cmd_ver = "zabbix_server --version | head -1 | egrep -o '[0-9]+\\.[0-9]+\\.[0-9]+'"
# }

# Variables {
TL_VERSION = '1.0.2'
ZBX_VERSION = get_shell_command_result(cmd_ver).strip()
IFCFG_FILE_NAME = '/etc/sysconfig/network-scripts/ifcfg-bond1.372'
HOSTS_FILE_NAME = '/etc/hosts'
# }

# Constants {
# }

# Zabbixapi

if __name__ == '__main__':
    AGRS = get_command_line_args()
    with open("./zbx_env.yaml", 'r') as zbx_env_file:
        zbx_env = yaml.load(zbx_env_file, Loader=yaml.SafeLoader)
    if zbx_env['zbx_ip']:
        zbx_vip = zbx_env['zbx_ip']
    else:
        zbx_vip = get_shell_command_result(cmd_vip).strip()
    zbx_url = 'https://' + zbx_vip + '/zabbix'
    zapi = ZabbixAPI(zbx_url)
    # Disable SSL certificate verification
    zapi.session.verify = False
    # Login to the Zabbix API
    zapi.login(zbx_env['zbx_GUI_usr'], zbx_env['zbx_GUI_pw'])
    with open(AGRS.file, 'r') as alarm_f:
        alarm_para = alarm_f.readlines()
        paras = []
        for line in alarm_para:
            para = line.strip().split('\t')
            paras.append(para)
    
    if zbx_env['TEMPLATE_NAME']:
        TEMPLATE_NAME = zbx_env['TEMPLATE_NAME']
    else:
        TEMPLATE_NAME = raw_input("Input template name you want to create:")
    TEMPLATE_ID = create_zbx_template(TEMPLATE_NAME, AGRS.yes)

    if TEMPLATE_ID:
        for para in paras:
        #for i in range(1,2,1):
            APPLICATION_ID = create_zbx_app(TEMPLATE_ID, para)
            ITEM_ID = create_zbx_item(TEMPLATE_NAME, TEMPLATE_ID, APPLICATION_ID, para)
            create_zbx_trigger(TEMPLATE_NAME, para, AGRS.m)

    if AGRS.reg_file:
        with open(AGRS.reg_file, 'r') as regexp_f:
            extra_para = regexp_f.readlines()
            regexp_paras = []
            for line in extra_para:
                regexp_org = line.strip().split('\t')
                regexp_para = [regexp_org[0]]
                i = 1
                for j in range(0,len(regexp_org)/3,1):
                    tmp_list = [regexp_org[i],regexp_org[i+1],regexp_org[i+2]]
                    regexp_para.append(tmp_list)
                    i = i + 3
                regexp_paras.append(regexp_para)

        for regexp_para in regexp_paras:
            REGEXP = regexp_para[0]
            REGLIST = regexp_para[1:]
            add_regular_expressions(REGEXP, REGLIST, AGRS.yes)
