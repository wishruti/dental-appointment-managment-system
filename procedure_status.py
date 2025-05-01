from baseObject import baseObject
from flask import request

class procedure_status(baseObject):
    def __init__(self):
        super().setup()
        self.table = "Procedure_Status"
        self.PK = "SID"

    def getFullInfo(self, sid):
        sql = """
        SELECT 
            s.SID,
            s.Start AS ScheduleDate,
            s.HourBlocks AS ScheduleTime,
            s.Status,
            s.Notes,
            p.UserID AS PatientID,
            p.Full_Name AS PatientName,
            d.UserID AS DoctorID,
            d.Full_Name AS DoctorName
        FROM Schedules s
        LEFT JOIN Users p ON s.PatientID = p.UserID
        LEFT JOIN Users d ON s.DoctorID = d.UserID
        WHERE s.SID = %s
        """
        self.cur.execute(sql, (sid,))
        self.data = self.cur.fetchall()

    def getAllProcedures(self):
        sql = "SELECT P_id, PName FROM Procedures WHERE Status = 'Active'"
        self.cur.execute(sql)
        return self.cur.fetchall()

    def getSelectedProcedureIDs(self, sid):
        sql = "SELECT P_id FROM Procedure_Status WHERE SID = %s"
        self.cur.execute(sql, (sid,))
        rows = self.cur.fetchall()
        return [row['P_id'] for row in rows]

    def saveStatusUpdate(self, sid, status, notes, procedure_ids):
        # Update schedule Status and Notes
        sql = "UPDATE Schedules SET Status = %s, Notes = %s WHERE SID = %s"
        self.cur.execute(sql, (status, notes, sid))

        # Clear previous records
        self.cur.execute("DELETE FROM Procedure_Status WHERE SID = %s", (sid,))

        # Insert new records for each procedure
        for pid in procedure_ids:
            proc_note_key = f'ProcedureNote_{pid}'
            proc_note = request.form.get(proc_note_key)

            if proc_note is not None and proc_note.strip() == '':
                proc_note = None  # store NULL if empty

            self.cur.execute(
                "INSERT INTO Procedure_Status (SID, P_id, Completed, Notes) VALUES (%s, %s, %s, %s)",
                (sid, pid, status, proc_note)
            )

        self.conn.commit()

    def getScheduleList(self, hide_completed_for_doctors=False, doctor_id=None):
        sql = """
        SELECT 
            s.SID, s.Start AS ScheduleDate, s.HourBlocks AS ScheduleTime, s.Notes, s.Status,
            p.Full_Name AS PatientName
        FROM Schedules s
        LEFT JOIN Users p ON s.PatientID = p.UserID
        """
        conditions = []

        if hide_completed_for_doctors:
            conditions.append("s.Status != 'Completed'")
        if doctor_id:
            conditions.append("s.DoctorID = %s")

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY s.Start ASC"

        if doctor_id:
            self.cur.execute(sql, (doctor_id,))
        else:
            self.cur.execute(sql)

        return self.cur.fetchall()


