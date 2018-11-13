import pycurl
import cStringIO
import json


response = cStringIO.StringIO()

#mudar nome do topico
data = json.dumps({"format": "json", "auto.offset.reset": "earliest"})

#mudar url >> <basePATH>/consumers/oehcs-consumer-group
url = 'https://129.150.115.252:1080/restproxy/consumers/oehcs-consumer-group'


c = pycurl.Curl()
c.setopt(pycurl.SSL_VERIFYPEER, 0)
c.setopt(pycurl.TIMEOUT, 10)
c.setopt(pycurl.SSL_VERIFYHOST, 0)
c.setopt(c.URL, url)

#mudar usuario:senha
c.setopt(pycurl.USERPWD, 'admin:Teste123#')

c.setopt(c.HTTPHEADER, ['Content-Type:application/vnd.kafka.json.v2+json'])
c.setopt(pycurl.POST, 1)
c.setopt(pycurl.POSTFIELDS,data)
#c.setopt(c.HEADERFUNCTION, response.write)
c.setopt(c.WRITEFUNCTION, response.write)

 
c.perform()
c.close()

answer = response.getvalue()
print answer
response.close()


