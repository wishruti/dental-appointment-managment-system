from baseObject import baseObject

class dashboard(baseObject):
    def __init__(self):
        self.setup()

    def get_stats(self):
        cur = self.cur

        cur.execute("SELECT COUNT(*) AS count FROM Users WHERE UserRole = 'Doctor'")
        total_doctors = cur.fetchone()['count']

        cur.execute("SELECT COUNT(*) AS count FROM Users WHERE UserRole = 'Patient'")
        total_patients = cur.fetchone()['count']

        cur.execute("SELECT COUNT(*) AS count FROM Schedules WHERE YEARWEEK(Start) = YEARWEEK(CURDATE())")
        appointments_this_week = cur.fetchone()['count']

        cur.execute("""
            SELECT P.PName, P.PCode, COUNT(PS.P_id) AS TimesUsed
            FROM Procedure_Status PS
            JOIN Procedures P ON PS.P_id = P.P_id
            GROUP BY PS.P_ID
            HAVING TimesUsed > 5
            ORDER BY TimesUsed DESC
            LIMIT 5
        """)
        top_procedures = cur.fetchall()

        return total_doctors, total_patients, appointments_this_week, top_procedures
