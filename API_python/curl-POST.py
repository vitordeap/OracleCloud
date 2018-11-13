import pycurl
import cStringIO
import json


response = cStringIO.StringIO()

#Mudar usuario:senha
USER_PASS = 'admin:Senha123'

# Mudar url: 
url = 'URL_para_comando_POST'

#Mudar Content Type: exemplo para Compute
Content_Type = 'Content-Type:application/oracle-compute-v3+json'

# Mudar dados ou atribuir arquivo json
data = json.dumps({"desired_state" : "shutdown"}


c = pycurl.Curl()

#para desabilitar https e habilitar http
c.setopt(pycurl.SSL_VERIFYPEER, 0)
c.setopt(pycurl.TIMEOUT, 10)
c.setopt(pycurl.SSL_VERIFYHOST, 0)

#funcoes do CURL
c.setopt(c.URL, url)
c.setopt(pycurl.USERPWD, USER_PASS)
c.setopt(c.HTTPHEADER, [Content_Type])
c.setopt(pycurl.POST, 1)
c.setopt(pycurl.POSTFIELDS,data)

#Para Imprimir resposta: Headers de Resposta ou Mensagem de Resposta
#c.setopt(c.HEADERFUNCTION, response.write)
c.setopt(c.WRITEFUNCTION, response.write)

 
c.perform()
c.close()

answer = response.getvalue()
print answer
response.close()

