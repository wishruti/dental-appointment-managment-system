from baseObject import baseObject
import pymysql

class schedule(baseObject):
    def __init__(self):
        self.setup()
        self.table = 'Schedules'
        self.pk = 'SID'
        self.fields = ['DoctorID', 'PatientID', 'Start', 'End','HourBlocks', 'Status', 'Notes']

    def verify_new(self, n=0):
        self.errors = []
        s = schedule()
        s.getAll()

        for row in s.data:
            if (
                row['DoctorID'] == self.data[n]['DoctorID'] and
                row['Start'] == self.data[n]['Start']
            ):
                self.errors.append("This time slot is already booked for the doctor.")
                break

        if not self.data[n].get('Status'):
            self.data[n]['Status'] = 'Open'

        return len(self.errors) == 0

    def get(self, pkval):
        sql = f"SELECT * FROM {self.table} WHERE {self.pk} = %s"
        self.cur.execute(sql, (pkval,))
        row = self.cur.fetchone()
        if row:
            self.data = [row]
        else:
            self.data = []

    def delete(self, pkval):
    # First delete from Procedure_Status table
        sql1 = "DELETE FROM Procedure_Status WHERE SID = %s"
        self.cur.execute(sql1, (pkval,))

    # Then delete from Schedules table
        sql2 = f"DELETE FROM {self.table} WHERE {self.pk} = %s"
        self.cur.execute(sql2, (pkval,))

        self.conn.commit()

