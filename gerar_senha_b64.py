import base64

senha = "#TI#srfi"
senha_b64 = base64.b64encode(senha.encode("utf-8")).decode("utf-8")
print(senha_b64)
