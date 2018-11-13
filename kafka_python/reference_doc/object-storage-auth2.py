import pycurl
import cStringIO

response = cStringIO.StringIO()

c = pycurl.Curl()
c.setopt(c.URL, 'https://demotrial.us.storage.oraclecloud.com/auth/v1.0')
c.setopt(c.HTTPHEADER, ['X-Storage-User: Storage-demotrial:vitor.pinto', 'X-Storage-Pass: Abacaxi!1@2#3'])
c.setopt(c.HEADERFUNCTION, response.write)
c.perform()
c.close()


answer = response.getvalue()

print answer

response.close()


