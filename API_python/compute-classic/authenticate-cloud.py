import pycurl
import cStringIO
import json
import os

response = cStringIO.StringIO()

# Mudar dados ou atribuir arquivo json
data = json.dumps({"password" : "Abacaxi!1@2#3","user" : "/Compute-611977642/vitor.pinto"})

# Mudar url:
url = 'https://compute.uscom-central-1.oraclecloud.com/authenticate/'
cookie = 'string'

c = pycurl.Curl()
c.setopt(pycurl.SSL_VERIFYPEER, 0)
c.setopt(pycurl.TIMEOUT, 10)
c.setopt(pycurl.SSL_VERIFYHOST, 0)
c.setopt(c.URL, url)
c.setopt(c.HTTPHEADER, ['Content-Type:application/oracle-compute-v3+json'])
c.setopt(pycurl.POST, 1)
c.setopt(pycurl.POSTFIELDS,data)
c.setopt(c.HEADERFUNCTION, response.write)
#c.setopt(c.WRITEFUNCTION, response.write)

 
c.perform()
c.close()

answer = response.getvalue()
print answer
response.close()



