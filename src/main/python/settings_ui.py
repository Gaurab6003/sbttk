from PySide2.QtCore import Slot, Signal
from PySide2.QtGui import QIcon, Qt
from PySide2.QtWidgets import (QDialog, QFormLayout, QLabel, QSpinBox,
                               QLineEdit, QPushButton,
                               QVBoxLayout, QMainWindow, QWidget, QStatusBar,
                               QMessageBox)

from database import Session, Settings
from database_access import complete_year


class SettingsWindow(QMainWindow):
    year_completed = Signal()

    def __init__(self, app_ctxt, *args, **kwargs):
        super(SettingsWindow, self).__init__(*args, **kwargs)
        self.app_ctxt = app_ctxt
        self.__settup_ui()
        self.load_data()

    def __settup_ui(self):
        self.setWindowTitle('SBTTK Settings')
        self.setWindowModality(Qt.ApplicationModal)
        # create icons
        save_icon = QIcon(self.app_ctxt.get_resource('save-32.png'))
        # create controls
        total_kista_months_label = QLabel('Total kista months:')
        self.total_kista_months_input = QSpinBox()
        account_no_label = QLabel('Account number:')
        self.account_no_input = QLineEdit()
        save_button = QPushButton(save_icon, 'Save')
        save_button.clicked.connect(self.handle_save_settings)
        # controls to migrate to next year
        year_start_date_label = QLabel('Year start date:')
        self.year_start_date_input = QLineEdit()
        self.year_start_date_input.setInputMask('9999-00-00')
        complete_year_button = QPushButton('Complete year')
        complete_year_button.clicked.connect(self.handle_complete_year)
        # create layout
        form_layout = QFormLayout()
        form_layout.addRow(total_kista_months_label,
                           self.total_kista_months_input)
        form_layout.addRow(account_no_label, self.account_no_input)
        form_layout.addWidget(save_button)
        form_layout.addRow(year_start_date_label, self.year_start_date_input)
        form_layout.addWidget(complete_year_button)
        # create wrapper widget and make it as central widget for the window
        widget = QWidget()
        widget.setLayout(form_layout)
        self.setCentralWidget(widget)
        # add status bar
        self.setStatusBar(QStatusBar())
        self.setFixedSize(self.sizeHint())

    def status_bar_message(self, msg):
        self.statusBar().clearMessage()
        self.statusBar().showMessage(msg, 5000)

    def load_data(self):
        with Session.begin() as session:
            settings = session.query(Settings).first()
            self.total_kista_months_input.setValue(settings.total_kista_months)
            self.account_no_input.setText(settings.account_no)

    @Slot()
    def handle_save_settings(self):
        with Session.begin() as session:
            settings = session.query(Settings).first()
            settings.total_kista_months = self.total_kista_months_input.value()
            settings.account_no = self.account_no_input.text()
        self.status_bar_message('Settings save successfully')

    @Slot()
    def handle_complete_year(self):
        # show confirm complete year dialog
        delete_dialog = QMessageBox(self)
        delete_dialog.setText('Are you sure you want to complete this year? '
                              'Please check start date carefully.')
        delete_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        delete_dialog.setIcon(QMessageBox.Icon.Question)
        button = delete_dialog.exec_()
        # if delete is confirmed delete the user
        if button == QMessageBox.Yes:
            date = self.year_start_date_input.text()
            with Session.begin() as session:
                error = complete_year(session, date)
            if not error is None:
                self.statusBar().showMessage(error)
            else:
                self.statusBar().showMessage('Successfully completed year.')
                self.year_completed.emit()


class AboutDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(AboutDialog, self).__init__(*args, **kwargs)
        self.__setup_ui()

    def __setup_ui(self):
        self.setWindowTitle('About')
        self.setModal(Qt.ApplicationModal)
        app_name_label = QLabel('Siddhababa Bachat Tatha Hitkosh Application.')
        copyright_label = QLabel('Copyright: Gaurab Dahit 2021')
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(app_name_label)
        vbox_layout.addWidget(copyright_label)
        self.setLayout(vbox_layout)
