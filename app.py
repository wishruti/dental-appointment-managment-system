from flask import Flask
from flask import render_template
from flask import request,session, redirect, url_for, send_from_directory,make_response 
from flask_session import Session
from datetime import timedelta
from datetime import datetime, date
from user import user
from procedures import procedures
from schedules import schedule
from procedure_status import procedure_status
import time
import calendar
from dashboard_stats import dashboard
from baseObject import baseObject

class Reports(baseObject):
    pass


app = Flask(__name__,static_url_path='')

app.config['SECRET_KEY'] = '5sdghsgRTg'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)
sess = Session()
sess.init_app(app)

@app.route('/')
def home():
    return render_template('home.html', home=True)

# @app.route('/')
# def home():
#     return redirect('/login')

@app.context_processor
def inject_user():
    return dict(me=session.get('user'))

def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    if value is None:
        return ''
    try:
        return value.strftime(format)
    except AttributeError:
        return 'NA'

app.jinja_env.filters['format_datetime'] = format_datetime

@app.route('/login',methods = ['GET','POST'])
def login():
    if request.form.get('name') is not None and request.form.get('password') is not None:
        u = user()
        if u.tryLogin(request.form.get('name'),request.form.get('password')):
            print("Login ok")
            session['user'] = u.data[0]
            session['active'] = time.time()
            return redirect('main')
        else:
            print("Login Failed")
            return render_template('home.html', title='Home', msg='Incorrect username or password.', home =True) #made changes
    else:   
        if 'msg' not in session.keys() or session['msg'] is None:
            m = 'Type your email and password to continue.'
        else:
            m = session['msg']
            session['msg'] = None
        return render_template('home.html', title='Login', msg=m, home = True)    

@app.route('/logout',methods = ['GET','POST'])
def logout():
    if session.get('user') is not None:
        del session['user']
        del session['active']
    return render_template('home.html', title='Login', msg='You have logged out.', home = True)



@app.route('/main')
def main():
    if checkSession() == False:
        return redirect('/login')

    role = session['user'].get('UserRole', '').lower()

    # Role: Admin → Load dashboard stats
    if role == 'admin':
        dash = dashboard()
        total_doctors, total_patients, appointments_this_week, top_procedures = dash.get_stats()
        dash.cleanup()
        return render_template('main.html',
                               title='Main menu',
                               me=session['user'],
                               total_doctors=total_doctors,
                               total_patients=total_patients,
                               appointments_this_week=appointments_this_week,
                               top_procedures=top_procedures)

   
    elif role == 'doctor':
        dash = dashboard()
        total_doctors, total_patients, appointments_this_week, top_procedures = dash.get_stats()
        dash.cleanup()
        return render_template('doctor_main.html',
                                me=session['user'],
                                total_doctors=total_doctors,
                                total_patients=total_patients,
                                appointments_this_week=appointments_this_week,
                                top_procedures=top_procedures)

    # Role: Patient
    elif role == 'patient':
        return redirect('/patient_main')

    # Role: fallback (e.g., customer or unknown)
    else:
        return render_template('main.html', title='Main menu', me=session['user'])

    
@app.route('/users/manage',methods=['GET','POST'])
def manage_user():
    if checkSession() == False or session['user']['UserRole'] != 'admin': 
        return redirect('/login')
    o = user()
    action = request.args.get('action')
    pkval = request.args.get('pkval')
    if action is not None and action == 'delete': #action=delete&pkval=123
        o.deleteById(request.args.get('pkval'))
        return render_template('ok_dialog.html',msg= "Deleted.")
    if action is not None and action == 'insert':
        d = {}
        d['Full_name'] = request.form.get('Full_name')
        d['Phone_No'] = request.form.get('Phone_No')
        d['Email'] = request.form.get('Email')
        d['UserRole'] = request.form.get('UserRole')
        d['Password'] = request.form.get('Password')
        d['password2'] = request.form.get('password2')
        o.set(d)
        if o.verify_new():
            #print(o.data)
            o.insert()
            return render_template('ok_dialog.html',msg= "User added.")
        else:
            return render_template('users/add.html',obj = o)
    if action is not None and action == 'update':
        o.getById(pkval)
        o.data[0]['Full_name'] = request.form.get('Full_name')
        o.data[0]['Phone_No'] = request.form.get('Phone_No')
        o.data[0]['Email'] = request.form.get('Email')
        o.data[0]['UserRole'] = request.form.get('UserRole')
        o.data[0]['Password'] = request.form.get('Password')
        o.data[0]['password2'] = request.form.get('password2')
        if o.verify_update():
            o.update()
            return render_template('ok_dialog.html',msg= "User updated. ")
        else:
            return render_template('users/manage.html',obj = o)
    if pkval is None:
        o.getAll()
        return render_template('users/list.html',obj = o)
    if pkval == 'new':
        o.createBlank()
        return render_template('users/add.html',obj = o)
    else:
        print(pkval)
        o.getById(pkval)
        return render_template('users/manage.html',obj = o)
    
##############################################################################3
###################               Procedures:
############################################################################

@app.route('/procedures/manage', methods=['GET', 'POST'])
def manage_procedure():
    if checkSession() == False or session['user']['UserRole'] not in ['admin', 'doctor']:
        return redirect('/login')
    o = procedures()
    u = user()
    u.getAll()
    #o.owners = u.data
    action = request.args.get('action')
    pkval = request.args.get('pkval')

    if action == 'delete' and pkval:
        sql = "UPDATE Procedures SET Status = 'Inactive' WHERE P_id = %s"
        o.cur.execute(sql, [pkval])
        o.cur.connection.commit()
        return render_template('ok_dialog.html', msg="Procedure marked as inactive.")



    if action == 'insert':
        d = {}
        d['PName'] = request.form.get('PName')
        d['PCode'] = request.form.get('PCode')
        d['PList'] = request.form.get('PList')
        d['Pcost'] = request.form.get('Pcost')
        d['PNotes'] = request.form.get('PNotes')
        d['Status'] = 'Active'
        o.set(d)
        if o.verify_new():  # You'll need to implement this in your procedure class
            o.insert()
            return render_template('ok_dialog.html', msg="Procedures added.")
        else:
            return render_template('procedures/add.html', obj=o)

    if action == 'update' and pkval:
        o.getById(pkval)
        if o.data:
            o.data[0]['PName'] = request.form.get('PName')
            o.data[0]['PCode'] = request.form.get('PCode')
            o.data[0]['PList'] = request.form.get('PList')
            o.data[0]['Pcost'] = request.form.get('Pcost')
            o.data[0]['PNotes'] = request.form.get('PNotes')

            if o.verify_update():  # Implement this in your vehicle class
                o.update()
                return render_template('ok_dialog.html', msg="Procedure updated.")
            else:
                return render_template('procedures/manage.html', obj=o)
        else:
            return render_template('ok_dialog.html', msg=f"Procedure with ID {pkval} not found.")

    # if pkval is None:
    #     o.getAll()
    #     return render_template('procedures/list.html', obj=o)
    if pkval is None:
        o.cur.execute("SELECT * FROM Procedures WHERE Status = 'Active'")
        o.data = o.cur.fetchall()
        return render_template('procedures/list.html', obj=o)


    if pkval == 'new':
        o.createBlank()
        return render_template('procedures/add.html', obj=o)

    else:
        o.getById(pkval)
        if o.data:
            return render_template('procedures/manage.html', obj=o)
        else:
            return render_template('error_dialog.html', msg=f"Procedures with ID {pkval} not found.")

############################# Schedules ##################################

@app.route("/schedules/manage", methods=["GET", "POST"])
def schedules_manage():
    me = session['user']
    if me['UserRole'] != 'admin':
        return render_template("ok_dialog.html", msg="Access Denied: Admins only.")

    o = schedule()
    u1 = user()
    u2 = user()
    doctors = u1.getByFieldLike("UserRole", "doctor")
    patients = u2.getByFieldLike("UserRole", "patient")  # corrected lowercase for consistency

    pkval = request.args.get("pkval", "new")
    action = request.args.get("action", "").lower()

    if pkval != "new":
        o.get(pkval)

    if request.method == "POST":
        doctor_id = request.form.get("DoctorID")
        patient_id = request.form.get("PatientID")
        start_str = request.form.get("Start")
        duration_hours = int(request.form.get("HourBlocks"))

        start_dt = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
        end_dt = start_dt + timedelta(hours=duration_hours)

        d = {
            'DoctorID': doctor_id,
            'PatientID': patient_id,
            'Start': start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            'End': end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            'HourBlocks': duration_hours,
            'Status': request.form.get("Status") or 'Open',  # Set default Open
            'Notes': request.form.get("Notes") or ''
        }

        o.set(d)

        if action == "update":
            if o.verify_new():
                o.update()
                return render_template("ok_dialog.html", msg="Schedule Updated.")
        elif action == "insert":
            if o.verify_new():
                o.insert()
                return render_template("ok_dialog.html", msg="Schedule Created.")

    return render_template("schedules/manage.html", obj=o, me=me, doctors=doctors, patients=patients)

@app.route("/schedules/list")
def schedules_list():
    o = schedule()
    me = session['user']

    # Get requested month and year from query params
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)

    today = datetime.today()

    # If month/year not provided, use current
    if not month or not year:
        month = today.month
        year = today.year

    # First day of the month
    first_day = datetime(year, month, 1)

    # Days in month
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    days_in_month = (next_month - timedelta(days=1)).day

    # Adjust so Sunday = 0
    first_weekday = (first_day.weekday() + 1) % 7

    # Load schedules based on user role
    if me['UserRole'].lower() == 'admin':
        o.getAll()
    elif me['UserRole'].lower() == 'patient':
        sql = "SELECT * FROM Schedules WHERE PatientID = %s"
        o.cur.execute(sql, (me['UserID'],))
        o.data = o.cur.fetchall()
        print("👤 Patient sees #schedules:", len(o.data))
    elif me['UserRole'].lower() == 'doctor':
        sql = "SELECT * FROM Schedules WHERE DoctorID = %s"
        o.cur.execute(sql, (me['UserID'],))
        o.data = o.cur.fetchall()
        print(" Doctor sees #schedules:", len(o.data))

    # Map users for patient names
    u = user()
    u.getAll()
    users_by_id = {row['UserID']: row['Full_name'] for row in u.data}

    for row in o.data:
        # Convert Start field to datetime if needed
        if isinstance(row['Start'], str):
            try:
                row['Start'] = datetime.strptime(row['Start'], '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                print(f"Failed to convert Start for SID {row['SID']}: {row['Start']} — {e}")

        row['patient_name'] = users_by_id.get(row['PatientID'], 'Unknown')

        # Optional debug
        print("Row SID:", row['SID'], "Start =", row['Start'], "Type =", type(row['Start']))

    # Build calendar weeks
    weeks = []
    week = []

    # Fill empty cells before the first of month
    for _ in range(first_day.weekday()):
        week.append(None)

    for day in range(1, days_in_month + 1):
        current_date = date(year, month, day)
        week.append(current_date)
        if len(week) == 7:
            weeks.append(week)
            week = []

    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)

    return render_template(
        "schedules/list.html",
        objs=o,
        now=today,
        month=month,
        year=year,
        weeks=weeks,
        first_weekday=first_weekday,
        days_in_month=days_in_month,
        me=me
    )
@app.route("/schedules/delete")
def schedules_delete():
    me = session['user']
    if me['UserRole'] != 'admin':
        return render_template("ok_dialog.html", msg="Access Denied: Admins only.")

    pkval = request.args.get("pkval")
    if pkval:
        o = schedule()
        o.delete(pkval)
        return render_template("ok_dialog.html", msg="Schedule Deleted.")
    else:
        return render_template("ok_dialog.html", msg="No schedule ID provided.")

################################Procedure Status #######################################

@app.route('/procedure_status/manage', methods=['GET', 'POST'])
def manage_procedure_status():
    if 'user' not in session or session['user']['UserRole'] not in ['admin', 'doctor']:
        return redirect('/login')

    ps = procedure_status()
    user_role = session['user']['UserRole']
    hide_completed = user_role == 'doctor'

    # Load only open/booked schedules for doctors
    doctor_id = session['user']['UserID'] if user_role == 'doctor' else None
    schedule_list = ps.getScheduleList(hide_completed_for_doctors=hide_completed, doctor_id=doctor_id)

    # If no schedules available (all completed), show message
    if not schedule_list and user_role == 'doctor':
        return render_template("ok_dialog.html", msg="All your procedures are completed. Nothing to update.")

    # Determine SID to load
    sid = request.args.get('pkval')
    if not sid and schedule_list:
        sid = schedule_list[0]['SID']
    elif not sid:
        return render_template("ok_dialog.html", msg="No schedules available.")

    try:
        sid = int(sid)
    except ValueError:
        return render_template("ok_dialog.html", msg="Invalid schedule ID.")

    # Load data
    ps.getFullInfo(sid)
    all_procs = ps.getAllProcedures()
    selected_proc_ids = ps.getSelectedProcedureIDs(sid)

    # Lock editing if doctor and status is Completed
    current_status = ps.data[0]['Status']
    is_locked_for_doctor = user_role == 'doctor' and current_status == 'Completed'

    # Only allow POST if user is allowed to update
    if request.method == 'POST' and not is_locked_for_doctor:
        status = request.form.get('Status')
        notes = request.form.get('Notes')
        selected_procs = request.form.getlist('ProcedureList')
        ps.saveStatusUpdate(sid, status, notes, selected_procs)
        return render_template('ok_dialog.html', msg="Procedure status updated.")

    return render_template(
        'procedure_status/manage.html',
        obj=ps,
        procedures=all_procs,
        selected_procedures=selected_proc_ids,
        schedule_list=schedule_list,
        active_sid=sid,
        is_locked_for_doctor=is_locked_for_doctor
    )

##################### Report viewing by patient################

@app.route('/reports/view', methods=['GET', 'POST'])
def view_reports():
    if 'user' not in session:
        return redirect('/login')

    user = session['user']
    patient_id = user['UserID']

    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    db = Reports()
    db.setup()
    cursor = db.cur

    sql = """
        SELECT 
            u.Full_Name AS PatientName,
            d.Full_Name AS DoctorName,
            s.Start AS BookedDate,
            s.End AS CompletedDate,
            p.PName AS ProcedureName,
            COALESCE(ps.Notes, 'No notes') AS Notes,
            p.Pcost AS Cost
        FROM 
            Schedules s
            JOIN Users u ON s.PatientID = u.UserID
            JOIN Users d ON s.DoctorID = d.UserID
            JOIN Procedure_Status ps ON ps.SID = s.SID
            JOIN Procedures p ON ps.P_id = p.P_id
        WHERE 
            s.PatientID = %s
            AND ps.Completed = 'Completed'
        ORDER BY s.Start ASC
    """

    params = [patient_id]

    if start_date and end_date:
        sql += " AND DATE(s.Start) BETWEEN %s AND %s"
        params.append(start_date)
        params.append(end_date)

    cursor.execute(sql, tuple(params))
    raw_reports = cursor.fetchall()

    db.conn.close()

    grouped_reports = {}
    for r in raw_reports:
        key = r['BookedDate']
        if key not in grouped_reports:
            grouped_reports[key] = {
                'PatientName': r['PatientName'],
                'DoctorName': r['DoctorName'],
                'CompletedDate': r['CompletedDate'],
                'Procedures': [],
                'TotalCost': 0
            }
        grouped_reports[key]['Procedures'].append({
            'ProcedureName': r['ProcedureName'],
            'Cost': r['Cost'],
            'Notes': r['Notes']
        })
        grouped_reports[key]['TotalCost'] += r['Cost']  # Add cost for the visit

    return render_template('reports_view.html', grouped_reports=grouped_reports, me=user, start_date=start_date, end_date=end_date)



################################Patient Dashboard ######################################

@app.route('/patient_main')
def patient_main():
    if 'user' not in session:
        return redirect('/login')

    user = session['user']
    patient_id = user['UserID']

    db = Reports()
    db.setup()
    cursor = db.cur

    # 1. Upcoming Appointments
    cursor.execute("""
        SELECT COUNT(*) AS UpcomingCount
        FROM Schedules
        WHERE PatientID = %s
          AND Start > NOW()
          AND Status IN ('Booked', 'Open');
    """, (patient_id,))
    upcoming = cursor.fetchone()
    upcoming = upcoming['UpcomingCount'] if upcoming else 0

    # 2. Completed Visits
    cursor.execute("""
        SELECT COUNT(DISTINCT s.SID) AS CompletedVisits
        FROM Schedules s
        JOIN Procedure_Status ps ON s.SID = ps.SID
        WHERE s.PatientID = %s
          AND ps.Completed = 'Completed';
    """, (patient_id,))
    completed = cursor.fetchone()
    completed = completed['CompletedVisits'] if completed else 0

    # 3. Reports Available
    cursor.execute("""
        SELECT COUNT(DISTINCT s.SID) AS ReportsAvailable
        FROM Schedules s
        JOIN Procedure_Status ps ON s.SID = ps.SID
        WHERE s.PatientID = %s
          AND ps.Completed = 'Completed';
    """, (patient_id,))
    reports = cursor.fetchone()
    reports = reports['ReportsAvailable'] if reports else 0

    # 4. Last Procedures
    cursor.execute("""
        SELECT 
            p.PName AS PName,
            d.Full_name AS DoctorName,
            s.Start AS Date
        FROM 
            Schedules s
        JOIN Procedure_Status ps ON s.SID = ps.SID
        JOIN Procedures p ON ps.P_id = p.P_id
        JOIN Users d ON s.DoctorID = d.UserID
        WHERE 
            s.PatientID = %s
            AND ps.Completed = 'Completed'
        ORDER BY s.Start DESC
        LIMIT 5;
    """, (patient_id,))
    last_procedures = cursor.fetchall()

    db.conn.close()

    return render_template('patient_main.html', 
                           me=user,
                           upcoming_appointments=upcoming,
                           completed_visits=completed,
                           available_reports=reports,
                           last_procedures=last_procedures)

#########################################################################
# endpoint route for static files
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

#standalone function to be called when we need to check if a user is logged in.
def checkSession():
    if 'active' in session.keys():
        timeSinceAct = time.time() - session['active']
        #print(timeSinceAct)
        if timeSinceAct > 500:
            session['msg'] = 'Your session has timed out.'
            return False
        else:
            session['active'] = time.time()
            return True
    else:
        return False   


if __name__ == '__main__':
   app.run(host='127.0.0.1',debug=True)   