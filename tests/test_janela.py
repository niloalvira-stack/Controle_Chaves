from PyQt5.QtWidgets import QApplication
from autenticacao.login_window import LoginWindow
import sys

def dummy_success(user):
    print("LOGIN OK!", user)

app = QApplication(sys.argv)
win = LoginWindow(dummy_success)
win.show()
sys.exit(app.exec_())
