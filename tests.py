#!/usr/bin/env python
# -*- coding: utf-8 -*-
from clikanban1 import *


def create_data():
    """
    if this gonna turn into a project, then we will do testings
    """
    new_task('task1')
    new_task('task2')
    new_task('task3')
    new_task('task4')
    new_task('task5')
    move_task(new_task('task6'), 'now')
    new_task('task7')
    move_task(new_task('task8'), 'now')
    new_task('task9')
    move_task(new_task('task10'), 'done')
    new_task('task11')
