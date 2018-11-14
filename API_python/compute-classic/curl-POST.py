import pycurl
import cStringIO
import json


#Mudar cookie
cookie = 'Cookie: ' + 'nimbula=eyJpZGVudGl0eSI6ICJ7XCJyZWFsbVwiOiBcInVzY29tLWNlbnRyYWwtMVwiLCBcInZhbHVlXCI6IFwie1xcXCJjdXN0b21lclxcXCI6IFxcXCJDb21wdXRlLTYxMTk3NzY0MlxcXCIsIFxcXCJyZWFsbVxcXCI6IFxcXCJ1c2NvbS1jZW50cmFsLTFcXFwiLCBcXFwiZW50aXR5X3R5cGVcXFwiOiBcXFwidXNlclxcXCIsIFxcXCJzZXNzaW9uX2V4cGlyZXNcXFwiOiAxNTQyMjE3MDU3Ljc0NTIxNTksIFxcXCJleHBpcmVzXFxcIjogMTU0MjIwODA1Ny43NDUyNDgxLCBcXFwidXNlclxcXCI6IFxcXCIvQ29tcHV0ZS02MTE5Nzc2NDIvdml0b3IucGludG9cXFwiLCBcXFwiZ3JvdXBzXFxcIjogW1xcXCIvQ29tcHV0ZS02MTE5Nzc2NDIvQ29tcHV0ZS5Db21wdXRlX09wZXJhdGlvbnNcXFwiXX1cIiwgXCJzaWduYXR1cmVcIjogXCJlbTd4UEczKy9yWlhia0tVTzVXaW02THR1S1VRWlZNMXVNQURLQ2RGMjZQRDF1QWZacGJ1eGhaaWNVbENvZzJ2Wld5NmI0MDd5cDgyOXRVcDRZeHVhQnFYRlMrQWsrUDZEZTlCbmJkc0EvMU5nY3ZlYTU2ZjgwMHRZVXFVcHRqbVdvZmZ4NVdiTDlKS0JKS09jY2g0WXJmbnJ6UnpFMWVmUENxcnQ4d2wxV0trYitNYnRVZjJIaHR5ZVk5bCtyOG5oZC90enByYWNUakZLY3pXemp3ZkZEcmUwZ3A5K1VEVHl1Nm1UQjNCSUtydXIxV1NJUURWSmtSRlpZYzVscXlnaElLeVFLZ2dwYjluNVdaanRUdkZDQlhtTHRJM0h4SUFoOFhwM05JZHM4NlhMYzZvVVIxMysreFFDTXU1anVJOW1aUXhHVk9IOXhPRWJTVjdhaFoyTXc9PVwifSJ9; Path=/; Max-Age=1800'

# Mudar url:
url = 'https://compute.uscom-central-1.oraclecloud.com/instance/'

#Mudar Content Type: exemplo para Compute
Content_Type = 'Content-Type:application/oracle-compute-v3+json'

# Mudar dados ou atribuir arquivo json
data = json.dumps({'desired_state' : 'shutdown'})


c = pycurl.Curl()


#para desabilitar https e habilitar http
c.setopt(pycurl.SSL_VERIFYPEER, 0)
c.setopt(pycurl.TIMEOUT, 10)
c.setopt(pycurl.SSL_VERIFYHOST, 0)

#funcoes do CURL
c.setopt(c.URL, url)
c.setopt(c.HTTPHEADER, [Content_Type, cookie])
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

