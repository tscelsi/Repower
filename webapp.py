from flask import Flask, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
import time
import sqlite3 as sql


# FLASK SIDE OF APP
app = Flask(__name__)
app.secret_key = 'some_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


def insert_event(date, _type, description):
    con = sql.connect("test.sqlite")
    cur = con.cursor()
    cur.execute("INSERT INTO events (date,type,description) VALUES (?,?,?)", (date, _type, description))
    con.commit()
    con.close()

def insert_member(firstname, lastname, email, mobile, landline, postcode, suburb, notes, added_on):
    con = sql.connect("test.sqlite")
    cur = con.cursor()
    cur.execute("INSERT INTO members (firstname, lastname, email, mobile, landline, postcode, notes, added_on) VALUES (?,?,?,?,?,?,?,?)",
        (firstname, lastname, email, mobile, landline, postcode, notes, added_on))
    print("postcode = " + str(postcode))
    result = cur.execute("SELECT code FROM postcodes WHERE code = " + postcode)
    print("result = " + str(result.fetchall()))
    if result.fetchall() == []:
        print('gets here')
        cur.execute("INSERT INTO postcodes (code, suburb) VALUES (?,?)",
            (postcode, suburb))
    con.commit()
    con.close()

def insert_mailouts(message_id, member_id, sent_date):
    con = sql.connect("test.sqlite")
    cur = con.cursor()
    cur.execute("INSERT INTO mailouts (message_id, member_id, sent_date) VALUES (?,?,?)", (message_id, member_id, sent_date))
    con.commit()
    con.close()


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/delete_member')
def delete_member():
    return render_template('delete_member.html')

@app.route('/delete_member_active', methods=['GET', 'POST'])
def delete_member_active():
    member_id = request.form['member_id']
    con = sql.connect("test.sqlite")
    cur = con.cursor()
    query = "DELETE FROM members WHERE id = " + str(member_id)
    print(query)
    cur.execute("DELETE FROM members WHERE id = " + str(member_id))
    con.commit()
    con.close()
    return render_template('delete_success.html')

@app.route('/delete_event')
def delete_event():
    return render_template('delete_event.html')

@app.route('/delete_event_active', methods=['GET', 'POST'])
def delete_event_active():
    event_id = request.form['event_id']
    con = sql.connect("test.sqlite")
    cur = con.cursor()
    query = "DELETE FROM events WHERE id = " + str(event_id)
    print(query)
    cur.execute("DELETE FROM events WHERE id = " + str(event_id))
    con.commit()
    con.close()
    return render_template('delete_success.html')


@app.route('/view_member')
def view_member():
    con = sql.connect("test.sqlite")
    cur = con.cursor()
    cur.execute("SELECT * FROM members")
    rows = cur.fetchall()
    con.commit()
    con.close()
    return render_template('view_member.html', rows=rows)

@app.route('/submit_new_member')
def submit_member():
    return render_template('submit_new_member.html')

@app.route('/submit_event')
def submit_event():
    return render_template('submit_event.html')

@app.route('/submit_events', methods=['GET', 'POST'])
def submit_events():
    if request.method == 'POST':

        date = request.form['date']
        _type = request.form['_type']
        description = request.form['description']

        print('-------')
        print(date)
        print(_type)
        print(description)
        print('-------')
        insert_event(date, _type, description)
        return render_template('home.html', date=date, _type=_type, description=description)
    return render_template('error.html')

@app.route('/submit_members', methods=['GET', 'POST'])
def submit_members():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        mobile = request.form['mobile']
        postcode = request.form['postcode']
        suburb = request.form['suburb']
        notes = request.form['notes']
        landline = request.form['landline']
        added_on = str(time.strftime("%Y-%m-%d"))
        insert_member(firstname, lastname, email, mobile, landline, postcode, suburb, notes, added_on)
        print(added_on)
        return render_template('submitted.html', landline=landline)


@app.route('/send_message')
def send_message():
    con = sql.connect("test.sqlite")
    cur = con.cursor()
    cur.execute("SELECT id, firstname, lastname FROM members")
    rows = cur.fetchall()
    con.commit()
    con.close()
    return render_template('send_message.html', rows=rows)

@app.route('/send_message_active', methods=['GET', 'POST'])
def send_message_active():
    if request.method == 'POST':
        message = request.form['message']
        member_list = request.form.getlist('include')
        if len(member_list) != 0:
            query = "SELECT email FROM members WHERE id = "
            query += member_list[0]
            for x in range(1,len(member_list)):
                query += " OR id = "
                query += member_list[x]
                print(query)
            con = sql.connect("test.sqlite")
            cur = con.cursor()
            cur.execute(query)
            member_emails = cur.fetchall()
            for member_email in member_emails:
                print(member_email)
            # send email to members
            # update messages table with new row
            query = "INSERT INTO messages (description) VALUES (" + message + ")"
            print(query)
            cur.execute(query)
            con.commit()
            con.close()
            # create new mailouts row with new id from messages table
            # update sent_invite column in event_mgmt
    return render_template('home.html')


if __name__ == '__main__':
    app.run(debug=True)
