import logging
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQuick import QQuickView
from PyQt5.QtCore import QUrl

logging.basicConfig(filename='MLpedia.log', level=logging.INFO)


class Dummy(object):
    pass


myscope = Dummy()


def _create():
    global myscope

    app = QApplication(sys.argv)
    main_url = os.path.join('qml', 'main.qml')

    view = QQuickView()
    view.setSource(QUrl(main_url))
    view.show()
    myscope.component = view
    return app


def create_app():
    global myscope
    logging.info('Booting up the app')

    try:
        logging.info('App started')
        return _create()
    except Exception as e:
        logging.exception('Failed to start the app')
        raise e


if __name__ == '__main__':
    app = create_app()
    sys.exit(app.exec_())
