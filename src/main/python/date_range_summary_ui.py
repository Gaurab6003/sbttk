from decimal import Decimal
from pathlib import Path

from PySide2.QtCore import QAbstractTableModel, Qt, Slot, Signal
from PySide2.QtWidgets import (QMainWindow, QWidget, QTableView, QVBoxLayout,
                               QFormLayout, QStatusBar, QLabel, QComboBox,
                               QLineEdit, QPushButton, QHBoxLayout, QCheckBox,
                               QFileDialog)
from nepali_datetime import date
from openpyxl import Workbook

from database import Session
from database_access import get_monthly_transactions, get_date_range_summary
from util import str_to_date, table_models_to_excel_sheet


class SawaAsuliModel(QAbstractTableModel):
    def __init__(self, *args, **kwargs):
        super(SawaAsuliModel, self).__init__(*args, **kwargs)
        self.transactions = []
        zero = Decimal(0)
        self.totals = {
            'sawa_asuli': zero,
            'byaj': zero,
            'harjana': zero,
            'bachat': zero,
            'grand_total': zero,
        }

    def set_data(self, transactions, totals):
        self.transactions = transactions
        self.totals = totals

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            if row == len(self.transactions):
                if col == 1: return 'Total'
                if col == 2: return str(self.totals['sawa_asuli'])
                if col == 3: return str(self.totals['byaj'])
                if col == 4: return str(self.totals['harjana'])
                if col == 5: return str(self.totals['bachat'])
                if col == 6: return str(self.totals['grand_total'])
            else:
                asuli = self.transactions[row].transaction_dto
                member_name = self.transactions[row].member_name
                if col == 0: return asuli.date
                if col == 1: return member_name
                if col == 2: return str(asuli.sawa_asuli)
                if col == 3: return str(asuli.byaj)
                if col == 4: return str(asuli.harjana)
                if col == 5: return str(asuli.bachat)
                if col == 6: return str(asuli.total)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0: return 'Date'
            if section == 1: return 'Member name'
            if section == 2: return 'Sawa asuli'
            if section == 3: return 'Byaj'
            if section == 4: return 'Harjana'
            if section == 5: return 'Bachat'
            if section == 6: return 'Total'

    def columnCount(self, parent):
        return 7

    def rowCount(self, parent):
        return len(self.transactions) + 1


class RinLaganiModel(QAbstractTableModel):
    def __init__(self, *args, **kwargs):
        super(RinLaganiModel, self).__init__(*args, **kwargs)
        self.transactions = []
        zero = Decimal(0)
        self.totals = {'rin_lagani': zero}

    def set_data(self, transactions, totals):
        self.transactions = transactions
        self.totals = totals

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            if row == len(self.transactions):
                if col == 1: return 'Total'
                if col == 2: return str(self.totals['rin_lagani'])
            else:
                tx = self.transactions[row].transaction_dto
                member_name = self.transactions[row].member_name
                if col == 0: return tx.date
                if col == 1: return member_name
                if col == 2:
                    if tx.is_alya_rin:
                        return str(tx.rin_lagani) + ' (Alya rin)'
                    else:
                        return str(tx.rin_lagani)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0: return 'Date'
            if section == 1: return 'Member name'
            if section == 2: return 'Rin Lagani'

    def columnCount(self, parent):
        return 3

    def rowCount(self, parent):
        return len(self.transactions) + 1


class BankTransactionModel(QAbstractTableModel):
    def __init__(self, *args, **kwargs):
        super(BankTransactionModel, self).__init__(*args, **kwargs)
        self.transactions = []
        zero = Decimal(0)
        self.totals = {'deposit': zero}

    def set_data(self, transactions, totals):
        self.transactions = transactions
        self.totals = totals

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            if row == len(self.transactions):
                if col == 0: return 'Total'
                if col == 1: return str(self.totals['deposit'])
            else:
                tx = self.transactions[row]
                if col == 0: return tx.date
                if col == 1: return str(tx.amount)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0: return 'Date'
            if section == 1: return 'Deposit'

    def columnCount(self, parent):
        return 2

    def rowCount(self, parent):
        return len(self.transactions) + 1


class DateRangeSummaryWindow(QMainWindow):
    transaction_saved = Signal()

    def __init__(self, *args, **kwargs):
        super(DateRangeSummaryWindow, self).__init__(*args, **kwargs)
        self.year = date.today().year
        self.dates = [date(self.year, month, 1) for month in range(1, 13)]
        self.__setup_ui()
        self.load_monthly_data(0)

    def __setup_ui(self):
        self.setWindowTitle('Bank Transaction')
        # year label
        year_header_label = QLabel('Year:')
        year_label = QLabel(str(self.year))
        # month label
        month_label = QLabel('Month:')
        self.month_combo_box = QComboBox()
        months = map(lambda dt: dt.strftime('%B'), self.dates)
        self.month_combo_box.addItems(months)
        self.month_combo_box.currentIndexChanged.connect(self.load_monthly_data)
        # export transactions button
        export_button = QPushButton('Export transactions')
        export_button.clicked.connect(self.handle_export)
        # deposit deficit
        deposit_deficit_header_label = QLabel('Deposit deficit:')
        self.deposit_deficit_label = QLabel('')
        self.deposit_deficit_label.setStyleSheet('font-weight: bold;')
        # create layout for form
        form_layout = QFormLayout()
        form_layout.addRow(year_header_label, year_label)
        form_layout.addRow(month_label, self.month_combo_box)
        form_layout.addWidget(export_button)
        form_layout.addRow(deposit_deficit_header_label,
                           self.deposit_deficit_label)
        # create form for date range summary
        # date range summary toggle checkbox
        enable_date_range_summary_label = QLabel('Enable date range summary')
        self.date_range_summary_check_box = QCheckBox()
        self.date_range_summary_check_box.setChecked(False)
        self.date_range_summary_check_box.toggled.connect(
            self.handle_toggle_date_range_summary)
        # start date
        start_date_label = QLabel('Sart date:')
        self.start_date_input = QLineEdit()
        self.start_date_input.setMaximumWidth(150)
        self.start_date_input.setInputMask('9999-00-00')
        self.start_date_input.setEnabled(False)
        # end date
        end_date_label = QLabel('End date:')
        self.end_date_input = QLineEdit()
        self.end_date_input.setMaximumWidth(150)
        self.end_date_input.setInputMask('9999-00-00')
        self.end_date_input.setEnabled(False)
        # view date range summary button
        self.view_summary_button = QPushButton(
            'View summary')
        self.view_summary_button.setMaximumWidth(150)
        self.view_summary_button.clicked.connect(
            self.load_date_range_data)
        # create date range summary form layout
        date_range_layout = QFormLayout()
        date_range_layout.addRow(enable_date_range_summary_label,
                                 self.date_range_summary_check_box)
        date_range_layout.addRow(start_date_label, self.start_date_input)
        date_range_layout.addRow(end_date_label, self.end_date_input)
        date_range_layout.addWidget(self.view_summary_button)
        # main input form layut
        main_input_layout = QHBoxLayout()
        main_input_layout.setSpacing(10)
        main_input_layout.addLayout(form_layout)
        main_input_layout.addLayout(date_range_layout)
        # create main_input_layout wrapper widget to restrict width
        input_widget = QWidget()
        input_widget.setMaximumWidth(800)
        input_widget.setLayout(main_input_layout)
        # sawa asuli table
        self.sawa_asuli_model = SawaAsuliModel()
        self.sawa_asuli_table = QTableView()
        self.sawa_asuli_table.setModel(self.sawa_asuli_model)
        # bank transactions table
        self.bank_txns_model = BankTransactionModel()
        self.bank_txns_table = QTableView()
        self.bank_txns_table.setModel(self.bank_txns_model)
        # rin lagani table
        self.rin_lagani_model = RinLaganiModel()
        self.rin_lagani_table = QTableView()
        self.rin_lagani_table.setModel(self.rin_lagani_model)
        # create main layout
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(input_widget)
        vbox_layout.addWidget(self.sawa_asuli_table)
        vbox_layout.addWidget(self.bank_txns_table)
        vbox_layout.addWidget(self.rin_lagani_table)
        # create wrapper widget
        widget = QWidget()
        widget.setLayout(vbox_layout)
        # set central widget
        self.setCentralWidget(widget)
        # create status bar
        self.setStatusBar(QStatusBar())

    def status_bar_message(self, msg):
        self.statusBar().clearMessage()
        self.statusBar().showMessage(msg, 5000)

    def update_data(self, rin_laganis, sawa_asulis, bank_transactions, totals):
        # update table data
        self.sawa_asuli_model.set_data(sawa_asulis, totals)
        self.bank_txns_model.set_data(bank_transactions, totals)
        self.rin_lagani_model.set_data(rin_laganis, totals)
        # notify changes
        self.sawa_asuli_model.layoutChanged.emit()
        self.bank_txns_model.layoutChanged.emit()
        self.rin_lagani_model.layoutChanged.emit()
        # change deposit deficit
        self.deposit_deficit_label.setText(
            str(totals['sawa_asuli'] - totals['deposit']))

    @Slot()
    def handle_toggle_date_range_summary(self, checked):
        if checked:
            self.start_date_input.setEnabled(True)
            self.end_date_input.setEnabled(True)
            self.view_summary_button.setEnabled(True)
            self.month_combo_box.setEnabled(False)
        else:
            self.start_date_input.setEnabled(False)
            self.end_date_input.setEnabled(False)
            self.view_summary_button.setEnabled(False)
            self.month_combo_box.setEnabled(True)

    @Slot()
    def load_monthly_data(self, index):
        # if nothing is selected and index is out of range ignore
        if index is None or index >= len(self.dates):
            return
        # load data
        dt = self.dates[index]
        with Session.begin() as session:
            transactions = get_monthly_transactions(session, dt)
            rin_laganis, sawa_asulis, bank_transactions, totals = transactions
        # update data
        self.update_data(rin_laganis, sawa_asulis, bank_transactions, totals)

    @Slot()
    def load_date_range_data(self):
        start_date = str_to_date(self.start_date_input.text())
        end_date = str_to_date(self.end_date_input.text())
        # if start date or end date is invalid ignore
        if start_date is None or end_date is None:
            return
        # load date
        with Session.begin() as session:
            transactions = get_date_range_summary(session, start_date, end_date)
            rin_laganis, sawa_asulis, bank_transactions, totals = transactions
        # update data
        self.update_data(rin_laganis, sawa_asulis, bank_transactions,
                         totals)

    @Slot()
    def handle_export(self):
        if self.date_range_summary_check_box.isChecked():
            name = (self.start_date_input.text() + ' to '
                    + self.end_date_input.text())
        else:
            name = self.month_combo_box.currentText()
        default_path = str(Path.home().joinpath(name + '-transactions.xlsx'))
        file_name, _ = QFileDialog.getSaveFileName(self, "Save", default_path,
                                                   "Excel (*.xlsx )")
        # if no file selected return
        if file_name == '':
            return
        # save model to workbook
        wb = Workbook()
        ws = wb.active
        ws.title = name + '_transactions'
        table_models_to_excel_sheet(
            [self.sawa_asuli_model, self.bank_txns_model,
             self.rin_lagani_model], ws)
        try:
            wb.save(file_name)
        except IOError as ex:
            self.statusBar().clearMessage()
            self.statusBar().showMessage('Could not save file', 5000)
