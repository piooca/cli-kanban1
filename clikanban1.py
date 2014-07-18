#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
from os import popen
from os.path import exists, expanduser
import argparse
from random import randint
import time

__author__ = 'pioo'
__version__ = '0.2a'

# terminal width
_board_width = int(popen('stty size', 'r').read().split()[1]) - 1

# TODO find dbfile's place
# is the DB initialized?
_dbfile = expanduser("~") + "/.cli-kanban1.db"
if not exists(_dbfile):
    _needs_init = True
else:
    _needs_init = False
_conn = sqlite3.connect(_dbfile)
_cur = _conn.cursor()


def create_db():
    """
    Initializes an empty database
    """
    #TODO error handling of DB initalization
    _cur.execute("CREATE TABLE tasks ("
                 "id TEXT(2) PRIMARY KEY, "
                 "data TEXT, "
                 "tableid NUMBER)")
    _cur.execute("CREATE TABLE tables ("
                 "tableid NUMBER PRIMARY KEY, "
                 "tablename TEXT)")
    _cur.execute("CREATE TABLE log ("
                 "date NUMBER, "
                 "taskid TEXT(2), "
                 "event TEXT, "
                 "tableid NUMBER)")
    tables = (
        (0, 'todo'),
        (1, 'now'),
        (2, 'done')
    )
    _cur.executemany("INSERT INTO tables VALUES(?, ?)", tables)
    _conn.commit()


def print_line(nr_tables):
    """
    Prints a lame decoration line on the screen.
    Needs the number of tables to place the + sign to the
    right place.
    """
    table_width = _board_width / nr_tables
    for i in range(nr_tables):
        print "+" + "-" * (table_width - 2),
    print "+"


def num_of_tables():
    """
    Remove this funcion?
    """
    #TODO remove this function
    _cur.execute("SELECT COUNT(tableid) FROM tables")
    row = _cur.fetchone()
    return row[0]


def list_tables():
    """
    Lists all the available kanban tables
    :return: array
    """
    #TODO error handling of table listing from DB
    _cur.execute("SELECT tablename FROM tables ORDER BY tableid")
    tables = []
    while True:
        row = _cur.fetchone()
        if row is None:
            break
        tables.append(row[0])
    return tables


def log_events(taskid, event, tableid):
    """
    A primitive event logging funcion
    """
    #TODO error handling of log_events
    date = int(time.time())
    query = "INSERT INTO log VALUES(:date, :taskid, :event, :tableid)"
    _cur.execute(query,
                 {'date': date, 'taskid': taskid, 'event': event, 'tableid': tableid})
    _conn.commit()


def print_log(taskid):
    """
    Shows event log of one or all tasks.
    """
    #TODO error handling of event log printing
    if taskid == 'dump':
        query = 'SELECT * FROM log ORDER BY date'
        _cur.execute(query)
    elif taskid == 'all':
        query = 'SELECT date,data,event,tablename ' \
                'FROM log AS L ' \
                'JOIN tasks AS T1 on L.taskid=T1.id ' \
                'JOIN tables AS T2 on L.tableid=T2.tableid ' \
                'ORDER BY date'
        _cur.execute(query)
    else:
        query = 'SELECT date,data,event,tablename ' \
                'FROM log AS L ' \
                'JOIN tasks AS T1 on L.taskid=T1.id ' \
                'JOIN tables AS T2 on L.tableid=T2.tableid ' \
                'WHERE L.taskid=?' \
                'ORDER BY date'
        _cur.execute(query, (taskid,))
    while True:
        row = _cur.fetchone()
        if not row:
            break
        print time.strftime("%Y/%m/%d %H:%M", time.localtime(int(row[0]))),
        print "{2:<8}[{3:^8}] {1:{width}}".format(*row, width=_board_width/3)


def get_table(table):
    """
    Returns the list of tasks in a table
    :param table: string, name of the table
    :rtype : tuple of tuples
    """
    _cur.execute(
        "SELECT id,data "
        "FROM tasks AS T "
        "JOIN tables AS B ON T.tableid=B.tableid "
        "WHERE B.tablename=?",
        (table,))
    return _cur.fetchall()


def print_table(table=None):
    """
    Print all the tasks or tasks from one kanban table
    to the output with lame formatting.
    """
    #TODO implement some "pretty print" thing
    #TODO use some table printing library
    tasklists = {}
    if table is None:
        # print all tables
        tables = list_tables()
        table_number = len(tables)
        table_width = _board_width / len(tables)

        #printing header
        decor = "+" + "-" * (table_width - 1)
        print decor * table_number + "+"

        for table in tables:
            print "|" + table.center(table_width - 2),
            tasklists[table] = get_table(table)
        print "|"
        print decor * table_number + "+"

        #printing the data
        have_data = True
        while have_data:
            row = []
            have_data = False
            for table in tables:
                try:
                    row.append(tasklists[table].pop(0))
                    have_data = True
                except IndexError:
                    row.append('')
            if not have_data:
                break
            for element in row:
                if element:
                    print "|" + element[0].ljust(3) + element[1][:table_width-5].ljust(table_width - 5),
                else:
                    print "|" + ' '.ljust(table_width - 2),
            print "|"
        print decor * table_number  + "+"
    else:
        # print just the specified table
        tasklists[table] = get_table(table)
        print table.upper()
        for taskid, taskname in tasklists[table]:
            print "%s\t%s" % (taskid, taskname)


def new_id():
    """
    Generates a new, unused id for a task
    A taskid is a HEX number from 0 to FF. Therefore only 256 tasks
    can live in a kanban database.
    """
    #TODO decide: is redesigning taskID handling required?
    newid = str(hex(randint(0, 255))).replace('0x', '')
    _cur.execute("SELECT COUNT(id) FROM tasks WHERE id = ?", (newid,))
    while _cur.fetchone()[0]:
        newid = str(hex(randint(0, 255))).replace('0x', '')
        _cur.execute("SELECT COUNT(id) FROM tasks WHERE id = ?", (newid,))
    return newid


def new_task(s, table='todo'):
    """
    Creates a new task in the specified table. Default is todo table.
    :param s: string, task definition
    """
    #TODO error handling of creating a new task
    table_id = get_table_id(table)
    newid = new_id()
    query = 'INSERT INTO tasks VALUES(:id, :todo, :tableid)'
    _cur.execute(query, {"id": newid, "todo": s, "tableid": table_id})
    _conn.commit()
    log_events(newid, 'created', 0)
    return newid


def get_table_id(table):
    """
    Converts table name to table id
    :param table: string
    :rtype : str
    """
    #TODO error handling in get_table_id
    sqlstatement = 'SELECT tableid FROM tables WHERE tablename=?'
    _cur.execute(sqlstatement, (table,))
    return _cur.fetchone()[0]


def get_task_location(taskid):
    """
    Returns the table's id where a specified task is located
    """
    #TODO error handling in get_task_location
    sqlstatement = 'SELECT tableid FROM tasks WHERE id=?'
    _cur.execute(sqlstatement, (taskid,))
    return _cur.fetchone()[0]


def move_task(task_id, to_table):
    """
    Moves a task into a specified table
    :param task_id: string, task's id to move
    :param to_table: string, a table's name to move the task into
    """
    #TODO error handling of moving a task
    to_table_id = get_table_id(to_table)
    sqlstatement = 'UPDATE tasks SET tableid=:to_table WHERE id=:task_id'
    _cur.execute(sqlstatement,
                 {"task_id": task_id, "to_table": to_table_id})
    _conn.commit()
    log_events(task_id, 'moved', to_table_id)


def delete_task(task_id):
    """
    Deletes a task
    :param task_id: task's id to delete
    """
    #TODO error handling of deleting a task
    table_id = get_task_location(task_id)
    sqlstatement = 'DELETE FROM tasks WHERE id=?'
    _cur.execute(sqlstatement, (task_id,))
    _conn.commit()
    log_events(task_id, 'deleted', table_id)


def empty_table(table):
    """
    Deletes all the tasks of the specified table
    :param table: string, table name to empty
    """
    #TODO error handling of table clearing
    for task, table in get_table(table):
        delete_task(task)


def parse_args():
    """
    Argument parsing as usual.
    Hence this is a command line application this def is the
    interface.
    """
    description = "A CLI Kanban dashboard"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--version', action="version", version=__version__)

    task_group = parser.add_argument_group('task manipulation options')
    task_group.add_argument('-n', '--new',
                            dest="task_desc",
                            metavar="DESC",
                            nargs="*",
                            help="add new task to the board")
    task_group.add_argument('-p', '--pick',
                            dest="pick_id",
                            metavar="ID",
                            help="pick a task from TODO and move it to NOW")
    task_group.add_argument('-f', '--finish',
                            dest="finish_id",
                            metavar="ID",
                            help="moves a task from NOW to DONE")
    task_group.add_argument('-m', '--move',
                            dest='move',
                            metavar='movestring',
                            help="moves a specified task from one table to "
                                 "another, format: id,tablename")
    task_group.add_argument('-d', '--delete',
                            dest="delete_id",
                            metavar="ID",
                            help="deletes a task from the board")
    task_group.add_argument('-s', '--showlog',
                            dest='log',
                            nargs='?',
                            metavar='taskid',
                            const='all',
                            help='Show task log')

    table_group = parser.add_argument_group('table manipulation options')
    table_group.add_argument('-l', '--list',
                             dest="table",
                             const="all",
                             choices=['todo', 'now', 'done', 'all'],
                             nargs='?',
                             metavar='table',
                             help="lists the dashboard or a table")
    table_group.add_argument('-c', '--clear',
                             dest='clear',
                             choices=['todo', 'now', 'done', 'all'],
                             const='done',
                             nargs='?',
                             metavar='table',
                             help="clear one or all table, default: done, "
                                  "available options: todo, now, done, all")

    main_group = parser.add_argument_group('main argument')
    main_group.add_argument('task',
                            nargs="*",
                            help="short task description, same as -n/--new")
    return parser, parser.parse_args()


def main():
    """
    Main program.
    """
    parser, args = parse_args()

    # non-existent database file
    if _needs_init:
        create_db()
    if args.table:
        if args.table == "all":
            print_table()
        else:
            print_table(args.table)
    # pick a task
    elif args.pick_id:
        move_task(args.pick_id, 'now')
        print_table()
    # finish a task
    elif args.finish_id:
        move_task(args.finish_id, 'done')
        print_table()
    # delete a task
    elif args.delete_id:
        delete_task(args.delete_id)
        print_table()
    # move a task
    elif args.move:
        task_id, table = args.move.split(',')
        move_task(task_id, table)
        print_table()
    # clear one or all tables
    elif args.clear:
        if args.clear != 'all':
            empty_table(args.clear)
        else:
            for table in list_tables():
                empty_table(table)
        print_table()
    # create new task
    elif args.task_desc:
        new_task(' '.join(args.task_desc).strip().decode('utf-8'))
        print_table()
    elif args.task:
        new_task(' '.join(args.task).strip().decode('utf-8'))
        print_table()
    # show log
    elif args.log:
        print_log(args.log)
    # default action is to show the dashboard (all tables)
    else:
        print_table()

    _conn.close()


if __name__ == "__main__":
    main()
