#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
from os import popen
from os.path import exists
import argparse
from random import randint
from time import time

__author__ = 'pioo'
__version__ = '0.2a'

#terminal width
__board_width__ = int(popen('stty size', 'r').read().split()[1]) - 1

#TODO find dbfile's place
# is the DB initialized?
__dbfile__ = "/home/pioo/.cli-kanban1.db"
if not exists(__dbfile__):
    __needs_init__ = True
else:
    __needs_init__ = False
__conn__ = sqlite3.connect(__dbfile__)
__cur__ = __conn__.cursor()


def create_db():
    """
    Initializes an empty database
    """
    #TODO error handling of DB initalization
    __cur__.execute("CREATE TABLE tasks ("
        "id TEXT(2) PRIMARY KEY, "
        "data TEXT, "
        "tableid NUMBER)")
    __cur__.execute("CREATE TABLE tables ("
        "tableid NUMBER PRIMARY KEY, "
        "tablename TEXT)")
    __cur__.execute("CREATE TABLE log ("
        "date NUMBER, "
        "taskid TEXT(2), "
        "event TEXT, "
        "tableid NUMBER)")
    tables = (
        (0, 'todo'),
        (1, 'now'),
        (2, 'done')
    )
    __cur__.executemany("INSERT INTO tables VALUES(?, ?)", tables)
    __conn__.commit()


def print_line(nr_tables):
    """
    Prints a lame decoration line on the screen.
    Needs the number of tables to place the + sign to the
    right place.
    """
    table_width = __board_width__ / nr_tables
    for i in range(nr_tables):
        print "+" + "-" * (table_width - 2),
    print "+"


def num_of_tables():
    """
    Remove this funcion?
    """
    #TODO remove this function
    __cur__.execute("SELECT COUNT(tableid) FROM tables")
    row = __cur__.fetchone()
    return row[0]


def list_tables():
    """
    Lists all the available kanban tables
    :return: array
    """
    #TODO error handling of table listing from DB
    __cur__.execute("SELECT tablename FROM tables ORDER BY tableid")
    tables = []
    while True:
        row = __cur__.fetchone()
        if row is None:
            break
        tables.append(row[0])
    return tables


def log_events(taskid, event, tableid):
    """
    A primitive event logging funcion
    """
    #TODO error handling of log_events
    date = int(time())
    query = "INSERT INTO log VALUES(:date, :taskid, :event, :tableid)"
    __cur__.execute(query,
        {'date': date, 'taskid': taskid, 'event': event, 'tableid': tableid})
    __conn__.commit()


def print_log(taskid):
    """
    Shows event log of one or all tasks.
    """
    #TODO error handling of event log printing
    if taskid == 'all':
        sqlstatement = 'SELECT * FROM log ORDER BY date'
        __cur__.execute(sqlstatement)
    else:
        sqlstatement = 'SELECT * FROM log WHERE taskid=? ORDER BY date'
        __cur__.execute(sqlstatement, (taskid,))
    while True:
        row = __cur__.fetchone()
        if not row:
            break
        print "{0} {1}\t'{2:^10}'\t{3}".format(*row)


def get_table(table):
    """
    Returns the list of tasks in a table
    :param table: string, name of the table
    :rtype : tuple of tuples
    """
    __cur__.execute(
        "SELECT id,data "
        "FROM tasks AS T "
        "JOIN tables AS B ON T.tableid=B.tableid "
        "WHERE B.tablename=?",
                    (table,))
    return __cur__.fetchall()


def print_table(table=None):
    """
    Print all the tasks or tasks from one kanban table
    to the output with lame formatting.
    """
    #TODO implement some "pretty print" thing
    tasklist = {}
    if table is None:
        # all tables
        tables = list_tables()
        foo = []
        bar = []
        i = 0
        for table in tables:
            bar.append(table.upper())
            tasklist[table] = get_table(table)
            for taskid, taskname in tasklist[table]:
                bar.append((taskid, taskname))
            foo.append(bar)
            bar = []
            i += 1

        nr_records = 0
        nr_tables = len(foo)
        table_width = __board_width__ / nr_tables
        for i in range(nr_tables):
            if len(foo[i]) > nr_records:
                nr_records = len(foo[i])

        #header
        print_line(nr_tables)
        for i in range(nr_tables):
            print "|" + foo[i][0].center(table_width - 2),
        print "|"
        print_line(nr_tables)

        #rows
        for j in range(1, nr_records):
            for i in range(nr_tables):
                if len(foo[i]) > j:
                    print "|" + foo[i][j][0].ljust(2) + " " +\
                    foo[i][j][1][:table_width - 5].ljust(table_width - 5),
                else:
                    print "|" + ''.ljust(table_width - 2),
            print "|"
        print_line(nr_tables)
    else:
        tasklist[table] = get_table(table)
        print table.upper()
        for taskid, taskname in tasklist[table]:
            print "%s\t%s" % (taskid, taskname)


def new_id():
    """
    Generates a new, unused id for a task
    A taskid is a HEX number from 0 to FF. Therefore only 256 tasks
    can live in a kanban database.
    """
    #TODO decide: is redesigning taskID handling required?
    newid = str(hex(randint(0, 255))).replace('0x', '')
    __cur__.execute("SELECT COUNT(id) FROM tasks WHERE id = ?", (newid,))
    while __cur__.fetchone()[0]:
        newid = str(hex(randint(0, 255))).replace('0x', '')
        __cur__.execute("SELECT COUNT(id) FROM tasks WHERE id = ?", (newid,))
    return newid


def new_task(s, table='todo'):
    """
    Creates a new task in the specified table. Default is todo table.
    :param s: string, task definition
    """
    #TODO error handling of creating a new task
    #tableID 0 is the todo table
    table_id = get_table_id('todo')
    newid = new_id()
    query = 'INSERT INTO tasks VALUES(:id, :todo, :tableid)'
    __cur__.execute(query, {"id": newid, "todo": s, "tableid": table_id})
    __conn__.commit()
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
    __cur__.execute(sqlstatement, (table,))
    return __cur__.fetchone()[0]


def get_task_location(taskid):
    """
    Returns the table's id where a specified task is located
    """
    #TODO error handling in get_task_location
    sqlstatement = 'SELECT tableid FROM tasks WHERE id=?'
    __cur__.execute(sqlstatement, (taskid,))
    return __cur__.fetchone()[0]


def move_task(task_id, to_table):
    """
    Moves a task into a specified table
    :param task_id: string, task's id to move
    :param to_table: string, a table's name to move the task into
    """
    #TODO error handling of moving a task
    to_table_id = get_table_id(to_table)
    sqlstatement = 'UPDATE tasks SET tableid=:to_table WHERE id=:task_id'
    __cur__.execute(sqlstatement,
        {"task_id": task_id, "to_table": to_table_id})
    __conn__.commit()
    log_events(task_id, 'moved', to_table_id)


def delete_task(task_id):
    """
    Deletes a task
    :param task_id: task's id to delete
    """
    #TODO error handling of deleting a task
    table_id = get_task_location(task_id)
    sqlstatement = 'DELETE FROM tasks WHERE id=?'
    __cur__.execute(sqlstatement, (task_id,))
    __conn__.commit()
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

    task_group = parser.add_argument_group('task view/manipulation options')
    task_group.add_argument('-l', '--list',
                            dest="table",
                            const="all",
                            choices=['todo', 'now', 'done', 'all'],
                            nargs='?',
                            metavar='table',
                            help="lists the dashboard or a table")
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
    task_group.add_argument('-c', '--clear',
                            dest='clear',
                            choices=['todo', 'now', 'done', 'all'],
                            const='done',
                            nargs='?',
                            metavar='table',
                            help="clear one or all table, default: done, "
                                "available options: todo, now, done, all")
    task_group.add_argument('-s', '--showlog',
                            dest='log',
                            nargs='?',
                            metavar='taskid',
                            const='all',
                            help='Show task log')

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

    if __needs_init__:
        create_db()
    if args.table:
        if args.table == "all":
            print_table()
        else:
            print_table(args.table)
    elif args.pick_id:
        move_task(args.pick_id, 'now')
    elif args.finish_id:
        move_task(args.finish_id, 'done')
    elif args.clear:
        if args.clear != 'all':
            empty_table(args.clear)
        else:
            for table in ['todo', 'now', 'done']:
                empty_table(table)
    elif args.move:
        task_id, table = args.move.split(',')
        move_task(task_id, table)
    elif args.task_desc:
        new_task(' '.join(args.task_desc).strip().decode('utf-8'))
    elif args.task:
        new_task(' '.join(args.task).strip().decode('utf-8'))
    elif args.log:
        print_log(args.log)
    else:
        print_table()

    __conn__.close()


if __name__ == "__main__":
    main()
