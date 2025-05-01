from baseObject import baseObject
import pymysql
import hashlib

class user(baseObject):
    def __init__(self):
        self.setup()
        self.roles = [{'value':'admin','text':'admin'},{'value':'patient','text':'patient'}, {'value':'doctor','text':'doctor'}]
    def hashPassword(self,pw):
        pw = pw+'xyz'
        return hashlib.md5(pw.encode('utf-8')).hexdigest()
    def role_list(self):
        rl = []
        for item in self.roles:
            rl.append(item['value'])
        return rl
    def verify_new(self,n=0):
        self.errors = []
        if '@' not in self.data[n]['Email']:
            self.errors.append('Email must contain @')
        if self.data[n]['UserRole'] not in self.role_list():
            self.errors.append(f'role must be one of {self.role_list()}')
        u = user()
        u.getByField('Email',self.data[0]['Email'])
        if len(u.data) > 0:
            self.errors.append(f"Email address is already in use. ({self.data[0]['Email']})")
        if len(self.data[n]['Password']) < 3:
            self.errors.append('Password should be greater than 3 chars.')
        if self.data[n]['Password'] != self.data[n]['password2']:
            self.errors.append('Retyped password must match.')
        self.data[n]['Password'] = self.hashPassword(self.data[n]['Password'])
        
        if len(self.errors) == 0:
            return True
        else:
            return False
    def verify_update(self,n=0):
        self.errors = []
        if '@' not in self.data[n]['Email']:
            self.errors.append('Email must contain @')
        if self.data[n]['UserRole'] not in self.role_list():
            self.errors.append(f'role must be one of {self.role_list()}')
        u = user()
        u.getByField('Email',self.data[0]['Email'])
        if len(u.data) > 0 and u.data[0][u.pk] != self.data[n][self.pk]:
            self.errors.append(f"Email address is already in use. ({self.data[0]['Email']})")
        
        if len(self.data[n]['Password']) == 0:
            del self.data[n]['Password']
        else:
            if len(self.data[n]['Password']) < 3:
                self.errors.append('Password needs to be more than 3 chars.')
            else:
                self.data[n]['Password'] = self.hashPassword(self.data[n]['Password'])
     
        if len(self.errors) == 0:
            return True
        else:
            return False
    def tryLogin(self,Email,pw):
        pw = self.hashPassword(pw)
        sql = f'SELECT * FROM `{self.tn}` WHERE `Email` = %s AND `Password` = %s;'
        tokens = [Email,pw]
        print(sql,tokens)
        self.cur.execute(sql,tokens)
        self.data = []
        for row in self.cur:
            self.data.append(row)
        if len(self.data) == 1: 
            return True
        else:
            return False
    # new addition  for schdeule 
    def getByFieldLike(self, field, value):
        self.sql = f"SELECT * FROM {self.tn} WHERE {field} = %s"
        self.cur.execute(self.sql, (value,))
        self.data = self.cur.fetchall()
        return self
