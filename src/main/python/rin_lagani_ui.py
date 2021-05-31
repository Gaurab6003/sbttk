from decimal import Decimal
from sys import float_info

from PySide2.QtCore import Qt, Slot, Signal
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (QMainWindow, QLabel, QLineEdit, QDoubleSpinBox,
                               QFormLayout, QWidget, QStatusBar, QPushButton,
                               QVBoxLayout)

from database import Session
from database_access import (RinLaganiDto, to_rin_lagani, get_rin_lagani_by_id,
                             save_or_update_rin_lagani, get_member_by_id)


class RinLaganiWindow(QMainWindow):
    rin_lagani_changed = Signal()

    def __init__(self, member_id, rin_lagani_id, app_ctxt, *args, **kwargs):
        super(RinLaganiWindow, self).__init__(*args, **kwargs)
        # check if member exists
        with Session.begin() as session:
            member = get_member_by_id(session, member_id)
            if member is None:
                self.close()
            else:
                self.member_name = member.name
        # initialize app context
        self.app_ctxt = app_ctxt
        # intialize RinLaganiDto
        self.rin_lagani_dto = RinLaganiDto.default()
        self.rin_lagani_dto.id = rin_lagani_id
        self.rin_lagani_dto.member_id = member_id
        # setup UI
        self.__setup_ui()
        # load data in database
        if not rin_lagani_id is None:
            self.load_data()

    def __setup_ui(self):
        self.setWindowTitle('Rin Lagani')
        self.setWindowModality(Qt.ApplicationModal)
        self.setMaximumSize(500, 300)
        # create header for rin lagani form
        member_name_label = QLabel('Member name:')
        member_name = QLabel(self.member_name)
        # date
        date_label = QLabel('Date:')
        self.date_input = QLineEdit()
        self.date_input.setInputMask('9999-00-00')
        # amount
        amount_label = QLabel('Amount:')
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(float_info.max)
        # remarks
        remarks_label = QLabel('Remarks:')
        self.remarks_input = QLineEdit()
        # save button
        save_icon = QIcon(self.app_ctxt.get_resource('save-32.png'))
        save_button = QPushButton(save_icon, 'Save')
        save_button.pressed.connect(self.save_rin_lagani)
        # form layout
        form_layout = QFormLayout()
        form_layout.addRow(member_name_label, member_name)
        form_layout.addRow(date_label, self.date_input)
        form_layout.addRow(amount_label, self.amount_input)
        form_layout.addRow(remarks_label, self.remarks_input)
        form_layout.addWidget(save_button)
        # create error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet('color: red')
        # create main layouts
        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(form_layout)
        vbox_layout.addWidget(self.error_label)
        # wrapper widget
        widget = QWidget()
        widget.setLayout(vbox_layout)
        # create status
        self.setStatusBar(QStatusBar())
        # set the central widget and fix the size
        self.setCentralWidget(widget)

    def status_bar_message(self, msg):
        self.statusBar().clearMessage()
        self.statusBar().showMessage(msg, 5000)

    def load_data(self):
        with Session.begin() as session:
            rin_lagani = get_rin_lagani_by_id(session,
                                              self.rin_lagani_dto.member_id)
            if not rin_lagani is None:
                self.date_input.setText(rin_lagani.date)
                self.amount_input.setValue(rin_lagani.amount)
                self.remarks_input.setText(rin_lagani.remarks)

    @Slot()
    def save_rin_lagani(self):
        self.rin_lagani_dto.date = self.date_input.text()
        self.rin_lagani_dto.amount = Decimal(str(self.amount_input.value()))
        self.rin_lagani_dto.remarks = self.remarks_input.text()
        with Session.begin() as session:
            errors = save_or_update_rin_lagani(session, to_rin_lagani(
                self.rin_lagani_dto))
        if errors:
            self.status_bar_message('Error while saving rin lagani.')
            # print(errors)
            errors_text = '\n'.join(errors.values())
            self.error_label.setText(errors_text)
        else:
            self.rin_lagani_changed.emit()
            self.close()
