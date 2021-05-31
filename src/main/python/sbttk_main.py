import sys

from fbs_runtime.application_context.PySide2 import ApplicationContext

from database import engine, Base, Session, Settings
from main_ui import MainWindow


def initialize_database():
    """Initializes database"""
    Base.metadata.create_all(engine)
    with Session.begin() as session:
        settings = session.query(Settings).first()
        if settings is None:
            settings = Settings(
                total_kista_months=40,
                account_no='00201300028079000001 (Nabjeeban Dhangadhi)'
            )
            session.add(settings)


if __name__ == '__main__':
    app_ctxt = ApplicationContext()  # 1. Instantiate ApplicationContext

    initialize_database()  # init database

    window = MainWindow(app_ctxt)
    window.showMaximized()

    exit_code = app_ctxt.app.exec_()  # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)
