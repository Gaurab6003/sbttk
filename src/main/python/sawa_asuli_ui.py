from datetime import timedelta
from decimal import Decimal
from sys import float_info

from PySide2.QtCore import Qt, Slot, Signal
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (QMainWindow, QWidget, QLabel, QLineEdit,
                               QDoubleSpinBox, QFormLayout, QStatusBar,
                               QPushButton, QVBoxLayout)

from database import Session, SawaAsuli
from database_access import (get_member_by_id, get_sawa_asuli_by_id,
                             get_latest_rin_lagani, calculate_banki_sawa,
                             get_latest_transaction,
                             get_second_last_transaction,
                             save_or_update_sawa_asuli)
from util import str_to_date


class SawaAsuliWindow(QMainWindow):
    sawa_asuli_changed = Signal()

    def __init__(self, member_id, app_ctxt, asuli_id, *args, **kwargs):
        super(SawaAsuliWindow, self).__init__(*args, **kwargs)
        # check if member exists
        with Session.begin() as session:
            member = get_member_by_id(session, member_id)
            if member is None:
                self.close()
            else:
                self.member_name = member.name
        self.asuli_id = asuli_id
        self.member_id = member_id
        self.rin_lagani_id = None
        self.kista_per_month = Decimal(0)
        self.lagani_rin = Decimal(0)
        self.is_bachat_only = False
        self.is_first_transaction = False
        # initialize app context
        self.app_ctxt = app_ctxt
        # setup UI
        self.__setup_ui()
        # initialize values
        self.init_values()

    def __setup_ui(self):
        self.setWindowTitle('Sawa Asuli')
        self.setWindowModality(Qt.ApplicationModal)
        # name
        name_label = QLabel('Member name:')
        name = QLabel(self.member_name)
        # start date
        start_date_label = QLabel('Start date:')
        self.start_date_input = QLineEdit()
        self.start_date_input.setInputMask('9999-00-00')
        self.start_date_input.setEnabled(False)
        # end date
        end_date_label = QLabel('End date:')
        self.end_date_input = QLineEdit()
        self.end_date_input.setInputMask('9999-00-00')
        self.end_date_input.textChanged.connect(self.calculate_values)
        # days
        days_label = QLabel('Days')
        self.days_input = QLineEdit()
        self.days_input.setEnabled(False)
        # Lagani rin
        lagani_rin_label = QLabel('Lagani rin:')
        self.lagani_rin_input = QDoubleSpinBox()
        self.lagani_rin_input.setMaximum(float_info.max)
        self.lagani_rin_input.setEnabled(False)
        # kista per month
        kista_per_month_label = QLabel('Kista per month:')
        self.kista_per_month_input = QDoubleSpinBox()
        self.kista_per_month_input.setMaximum(float_info.max)
        self.kista_per_month_input.setEnabled(False)
        # amount
        amount_label = QLabel('Amount:')
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(float_info.max)
        self.amount_input.valueChanged.connect(self.calculate_values)
        # byaj per day
        byaj_per_day_label = QLabel('Byaj per day:')
        self.byaj_per_day_input = QDoubleSpinBox()
        self.byaj_per_day_input.setMaximum(float_info.max)
        self.byaj_per_day_input.setEnabled(False)
        # byaj
        byaj_label = QLabel('Byaj:')
        self.byaj_input = QDoubleSpinBox()
        self.byaj_input.setMaximum(float_info.max)
        self.byaj_input.setEnabled(False)
        # harjana
        harjana_label = QLabel('Harjana:')
        self.harjana_input = QDoubleSpinBox()
        self.harjana_input.setMaximum(float_info.max)
        # bachat
        bachat_label = QLabel('Bachat:')
        self.bachat_input = QDoubleSpinBox()
        self.bachat_input.setMaximum(float_info.max)
        self.bachat_input.setEnabled(True)
        # grand total
        grand_total_label = QLabel('Grand total:')
        self.grand_total_input = QDoubleSpinBox()
        self.grand_total_input.setMaximum(float_info.max)
        self.grand_total_input.setEnabled(False)
        # banki sawa
        banki_sawa_label = QLabel('Banki sawa:')
        self.banki_sawa_input = QDoubleSpinBox()
        self.banki_sawa_input.setMaximum(float_info.max)
        self.banki_sawa_input.setEnabled(False)
        # remarks
        remarks_label = QLabel('Remarks:')
        self.remarks_input = QLineEdit()
        # save button
        save_icon = QIcon(self.app_ctxt.get_resource('save-32.png'))
        self.save_button = QPushButton(save_icon, 'Save')
        self.save_button.pressed.connect(self.save_sawa_asuli)
        # create form layout
        form_layout = QFormLayout()
        form_layout.addRow(name_label, name)
        form_layout.addRow(lagani_rin_label, self.lagani_rin_input)
        form_layout.addRow(start_date_label, self.start_date_input)
        form_layout.addRow(end_date_label, self.end_date_input)
        form_layout.addRow(kista_per_month_label, self.kista_per_month_input)
        form_layout.addRow(amount_label, self.amount_input)
        form_layout.addRow(days_label, self.days_input)
        form_layout.addRow(byaj_per_day_label, self.byaj_per_day_input)
        form_layout.addRow(byaj_label, self.byaj_input)
        form_layout.addRow(harjana_label, self.harjana_input)
        form_layout.addRow(bachat_label, self.bachat_input)
        form_layout.addRow(grand_total_label, self.grand_total_input)
        form_layout.addRow(banki_sawa_label, self.banki_sawa_input)
        form_layout.addRow(remarks_label, self.remarks_input)
        form_layout.addWidget(self.save_button)
        # create error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet('color: red')
        # create main layouts
        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(form_layout)
        vbox_layout.addWidget(self.error_label)
        # create wrapper widget
        widget = QWidget()
        widget.setLayout(vbox_layout)
        # create status bar
        self.setStatusBar(QStatusBar())
        # set the central widget and fix the size
        self.setCentralWidget(widget)
        self.setMaximumSize(self.sizeHint().width() + 100,
                            self.sizeHint().height() + 100)

    def init_values(self):
        with Session.begin() as session:
            # set latest transaction based on if the sawa asuli is new or being updated.
            if self.asuli_id is None:
                latest_tx = get_latest_transaction(session, self.member_id)
            else:
                latest_tx = get_second_last_transaction(session,
                                                        self.member_id)
            # load latest rin lagani calculate banki sawa
            rin_lagani = get_latest_rin_lagani(session, self.member_id)
            self.lagani_rin = calculate_banki_sawa(rin_lagani)
            # if sawa asuli already exists load its values
            if not self.asuli_id is None:
                sawa_asuli = get_sawa_asuli_by_id(session, self.asuli_id)
                self.amount_input.setValue(sawa_asuli.amount)
                self.byaj_input.setValue(sawa_asuli.byaj)
                self.harjana_input.setValue(sawa_asuli.harjana)
                self.bachat_input.setValue(sawa_asuli.bachat)
                self.remarks_input.setText(sawa_asuli.remarks)
                # while editing latest sawa asuli do not count its sawa asuli when calulating banki sawa
                self.lagani_rin += sawa_asuli.amount
            # check if the sawa asuli should be bachat only
            if rin_lagani is None or self.lagani_rin == Decimal(0):
                self.start_date_input.setText('')
                self.is_bachat_only = True
                self.rin_lagani_id = None
                self.kista_per_month = Decimal(0)
                self.amount_input.setEnabled(False)
            else:
                if type(latest_tx) == SawaAsuli:
                    start_date = str(
                        str_to_date(latest_tx.date) + timedelta(days=1))
                else:
                    start_date = latest_tx.date
                self.start_date_input.setText(start_date)
                self.rin_lagani_id = rin_lagani.id
                self.kista_per_month = rin_lagani.kista_per_month
            # set initial values to input fields
            self.lagani_rin_input.setValue(self.lagani_rin)
            self.kista_per_month_input.setValue(self.kista_per_month)
            self.calculate_values()

    @Slot()
    def calculate_values(self):
        # if it is first transaction don't do anything
        if self.is_first_transaction:
            return
        if self.is_bachat_only:
            self.grand_total_input.setValue(self.bachat_input.value())
            return
        # calculate start and end dates
        start_date = str_to_date(self.start_date_input.text())
        end_date = str_to_date(self.end_date_input.text())
        if start_date is None or end_date is None:
            self.status_bar_message('Invalid dates.')
            return
        if end_date < start_date:
            self.status_bar_message('End date is less than start date.')
            return
        time_delta = end_date - start_date
        days = time_delta.days + 1
        # update days_input value
        self.days_input.setText(str(days))
        # byaj per day = (previous banki sawa(lagani rin) / 0.12) / 365
        byaj_per_day = (self.lagani_rin * Decimal('0.12')) / Decimal('365')
        self.byaj_per_day_input.setValue(byaj_per_day)
        # calculate byaj = byaj per day * days
        self.byaj_input.setValue(byaj_per_day * days)
        # calculate grand total
        self.grand_total_input.setValue(
            Decimal(str(self.amount_input.value()))
            + Decimal(str(self.byaj_input.value()))
            + Decimal(str(self.harjana_input.value()))
            + Decimal(str(self.bachat_input.value())))
        # calculate banki sawa
        self.banki_sawa_input.setValue(
            self.lagani_rin - Decimal(str(self.amount_input.value())))

    def status_bar_message(self, msg):
        self.statusBar().clearMessage()
        self.statusBar().showMessage(msg, 5000)

    @Slot()
    def save_sawa_asuli(self):
        sawa_asuli = SawaAsuli(id=self.asuli_id,
                               date=self.end_date_input.text(),
                               member_id=self.member_id,
                               rin_lagani_id=self.rin_lagani_id,
                               amount=Decimal(str(self.amount_input.value())),
                               byaj=Decimal(str(self.byaj_input.value())),
                               harjana=Decimal(str(self.harjana_input.value())),
                               bachat=Decimal(str(self.bachat_input.value())),
                               remarks=self.remarks_input.text())
        with Session.begin() as session:
            errors = save_or_update_sawa_asuli(session, sawa_asuli)
        if errors:
            self.status_bar_message('Error while saving sawa asuli.')
            # print(errors)
            errors_text = '\n'.join(errors.values())
            self.error_label.setText(errors_text)
        else:
            self.status_bar_message('Successfully saved sawa asuli.')
            self.sawa_asuli_changed.emit()
            self.close()
