import pycurl
import cStringIO
import json

response = cStringIO.StringIO()

#------------------------------------------------------
#SUBSCRIBE TO TOPIC

#Mudar nome do topico
data = json.dumps({"topics": ["topicDEMO"]})

#Mudar base_uri
baseURI = 'https://129.150.115.252:1080/restproxy/consumers/idcs-ff049979217c422fb52a85216ec78831-oehcs-consumer-group/instances/rest-consumer-kakfadedicated-restprxy-1.compute-611977642.oraclecloud.internal-981e3e3b-b095-477f-b279-89ddfd84c748'




subscription_baseURI = baseURI + '/subscription'
records_baseURI = baseURI + '/records'



c = pycurl.Curl()
c.setopt(pycurl.SSL_VERIFYPEER, 0)
c.setopt(pycurl.TIMEOUT, 30)
c.setopt(pycurl.SSL_VERIFYHOST, 0)
c.setopt(c.URL, subscription_baseURI)
c.setopt(pycurl.USERPWD, 'admin:Teste123#')
c.setopt(c.HTTPHEADER, ['Content-Type:application/vnd.kafka.json.v2+json'])
c.setopt(pycurl.POST, 1)
c.setopt(pycurl.POSTFIELDS,data)
#c.setopt(c.HEADERFUNCTION, response.write)
c.setopt(c.WRITEFUNCTION, response.write)


c.perform()
c.close()


#---------------------------------------------------------------

#GET RECORDS

c = pycurl.Curl()
c.setopt(pycurl.SSL_VERIFYPEER, 0)
c.setopt(pycurl.TIMEOUT, 10)
c.setopt(pycurl.SSL_VERIFYHOST, 0)
c.setopt(c.URL, records_baseURI)
c.setopt(pycurl.USERPWD, 'admin:Teste123#')
c.setopt(c.HTTPHEADER, ['Accept:application/vnd.kafka.json.v2+json'])
#c.setopt(pycurl.POST, 1)
#c.setopt(c.HEADERFUNCTION, response.write)
c.setopt(c.WRITEFUNCTION, response.write)

 
c.perform()
c.close()

answer = response.getvalue()
print answer
response.close()

