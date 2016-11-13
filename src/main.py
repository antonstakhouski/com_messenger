# !/usr/bin/env python

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    from ComPortMessenger import ComPortMessenger

    app = QApplication(sys.argv)

    messenger = ComPortMessenger()
    messenger.show()

    sys.exit(app.exec_())
