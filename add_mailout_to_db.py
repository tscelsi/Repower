#! /usr/bin/env python3

import sqlite3
import sys
import argparse
import csv
import subprocess as sp
import datetime


class Error(Exception):
    pass


def get_args(params=None):
    parser = argparse.ArgumentParser(
        description='''Select email addresses and save to database as 
                    new mailout.''')
    parser.add_argument('sqlite_database_file')
    parser.add_argument('msg_subject')
    parser.add_argument('-n', '--dry-run', action='store_true')
    parser.add_argument('--select-expr')
    parser.add_argument('-c', '--check-all', action='store_true',
                        help='initially check all checkboxes')
    args = parser.parse_args(params)
    return args


def main():
    args = get_args()

    sent_date = datetime.date.today().isoformat()

    conn = sqlite3.connect(args.sqlite_database_file)

    query_string = "INSERT INTO messages (description) VALUES (?);"
    cursor = conn.execute(query_string, [args.msg_subject])
    # Get 'rowid' of last row inserted:
    message_id = cursor.lastrowid
    if not message_id:
        raise Error("Could not add message to database.") 
    
    query_string = "SELECT description from messages WHERE id == ?;"
    cursor = conn.execute(query_string, [message_id])
    assert(cursor.fetchone()[0] == args.msg_subject)

    cmd = ['zenity', '--list', '--checklist',
           '--width=600', '--height=600',
           '--text=Mailout: "{}"'.format(args.msg_subject),
           '--column=Send', '--column=Name', '--column=Email',
           '--column=ID', '--print-column', '4']
    
    query_string = (
        '''SELECT members.id, firstname, lastname, email
        FROM members WHERE email NOTNULL''' 
    )
    if args.select_expr:
        query_string += (' AND ' + args.select_expr)
        
    cursor = conn.execute(query_string)

    row_list = []
    checked = 'TRUE' if args.check_all else 'FALSE'
    for id, fn, ln, em in cursor:
        row_list.extend([checked, '{} {}'.format(fn, ln), em, str(id)])

    subproc = sp.run(cmd + row_list, stdout=sp.PIPE)
    if subproc.returncode != 0:
        print("Cancelled")
        return

    output = subproc.stdout.decode().rstrip()
    selected_ids = output.split('|') if output else []
    new_items = [(message_id, int(id), sent_date) for id in selected_ids]

    query_string = (
        '''INSERT INTO mailouts (message_id, member_id, sent_date)
        VALUES (?, ?, ?)''')

    cursor = conn.executemany(query_string, new_items)

    query_string = (
        '''SELECT firstname, lastname, email
        FROM mailouts JOIN members ON members.id == member_id
        WHERE message_id == ?''')

    cursor = conn.execute(query_string, [message_id])
    print("Address list:\n")
    for fn, ln, em in cursor.fetchall():
        print('"{} {}" <{}>'.format(fn, ln, em))
    print()
    
    if args.dry_run:
        conn.rollback()
        print('Database not modified.  New message id will be: {}'.format(message_id))
    else:
        conn.commit()
        print('Changes committed!  New message id: {}'.format(message_id))
        
    conn.close()


#-----------------------------------------------------------------------------


if __name__ == '__main__':
    main()
