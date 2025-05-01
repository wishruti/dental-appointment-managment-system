from baseObject import baseObject
import pymysql
import hashlib

class procedures(baseObject):
    def __init__(self):
        self.setup()
        
  
    def role_list(self):
        rl = []
        for item in self.roles:
            rl.append(item['value'])
        return rl
    def verify_new(self,n=0):
        self.errors = []
       
        
        if len(self.errors) == 0:
            return True
        else:
            return False
    def verify_update(self,n=0):
        self.errors = []
        
        if len(self.errors) == 0:
            return True
        else:
            return False
    # def getWithOwner(self):
    #     sql = f'SELECT * FROM `` LEFT JOIN `users` ON `procedures`.`owner_uid` = `users`.`uid`;'
    #     print(sql)
    #     self.cur.execute(sql)
    #     self.data = []
    #     for row in self.cur:
    #         self.data.append(row)
    