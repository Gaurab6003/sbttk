from decimal import Decimal
from sys import float_info

from PySide2.QtCore import QAbstractTableModel, Qt, Slot, Signal
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (QMainWindow, QWidget, QTableView, QVBoxLayout,
                               QHBoxLayout, QPushButton, QMessageBox,
                               QStatusBar, QLabel, QDoubleSpinBox, QLineEdit,
                               QFormLayout, QRadioButton, QGroupBox)

from database import Session, BankTransactionTypes, BankTransaction
from database_access import (get_bank_transactions_and_rin_laganis,
                             delete_bank_transaction_by_id,
                             get_bank_transaction_by_id,
                             save_or_update_bank_transaction)


class BankTransactionModel(QAbstractTableModel):
    def __init__(self, *args, **kwargs):
        super(BankTransactionModel, self).__init__(*args, **kwargs)
        self.transactions = []
        self.totals = {}
        self.load_data()

    def load_data(self):
        with Session.begin() as session:
            value = get_bank_transactions_and_rin_laganis(session)
            self.transactions, self.totals = value

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            # if it is the last row show total
            if row == len(self.transactions):
                if col == 0:
                    return 'Total'
                if col == 1:
                    return str(self.totals['debit_total'])
                if col == 2:
                    return str(self.totals['credit_total'])
            else:
                # else show normal transaction
                tx = self.transactions[row]
                if col == 0:
                    return tx.date
                if col == 1:
                    if tx.type == 'DEBIT' or tx.type == 'RIN_LAGANI':
                        return str(tx.amount)
                    return '0'
                if col == 2:
                    if tx.type == 'CREDIT' or tx.type == 'DEPOSIT':
                        return str(tx.amount)
                    return '0'
                if col == 3:
                    return tx.type
                if col == 4:
                    return tx.remarks

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0: return 'Date'
            if section == 1: return 'Debit'
            if section == 2: return 'Credit'
            if section == 3: return 'Type'
            if section == 4: return 'Remarks'

    def columnCount(self, parent):
        return 5

    def rowCount(self, parent):
        return len(self.transactions) + 1


class BankTransactionsWindow(QMainWindow):
    def __init__(self, app_ctxt, *args, **kwargs):
        super(BankTransactionsWindow, self).__init__(*args, **kwargs)
        self.app_ctxt = app_ctxt
        self.bank_transaction_window = None
        self.__setup_ui()

    def __setup_ui(self):
        self.setWindowTitle('Bank Transactions')
        # create icons
        add_icon = QIcon(self.app_ctxt.get_resource('plus-32.png'))
        edit_icon = QIcon(self.app_ctxt.get_resource('edit-32.png'))
        delete_icon = QIcon(self.app_ctxt.get_resource('trash-32.png'))
        # create buttons
        add_button = QPushButton(add_icon, 'Add transaction')
        add_button.setFixedWidth(180)
        add_button.pressed.connect(self.add_bank_transaction)
        self.edit_button = QPushButton(edit_icon, 'Edit transaction')
        self.edit_button.setFixedWidth(180)
        self.edit_button.clicked.connect(self.edit_bank_transaction)
        self.delete_button = QPushButton(delete_icon, 'Delete transaction')
        self.delete_button.setFixedWidth(180)
        self.delete_button.clicked.connect(self.delete_bank_transaction)
        # create layout for buttons
        hbox_layout = QHBoxLayout()
        self.setContentsMargins(0, 0, 0, 0)
        hbox_layout.setSpacing(10)
        hbox_layout.addWidget(add_button)
        hbox_layout.addWidget(self.edit_button)
        hbox_layout.addWidget(self.delete_button)
        # create wrapper widget for button
        button_container = QWidget()
        button_container.setContentsMargins(0, 0, 0, 0)
        button_container.setLayout(hbox_layout)
        button_container.setFixedWidth(560)
        # create table view
        self.model = BankTransactionModel()
        self.bank_transactions_table = QTableView()
        self.bank_transactions_table.setModel(self.model)
        self.bank_transactions_table.selectionModel().selectionChanged.connect(
            self.enable_disable_controls)
        # create layout
        vbox_layout = QVBoxLayout()
        vbox_layout.setSpacing(10)
        vbox_layout.addWidget(button_container)
        vbox_layout.addWidget(self.bank_transactions_table)
        # create status bar
        self.setStatusBar(QStatusBar())
        # enable disable controls
        self.enable_disable_controls()
        # create wrapper widget
        widget = QWidget()
        widget.setLayout(vbox_layout)
        # set central widget
        self.setCentralWidget(widget)

    def status_bar_message(self, msg):
        self.statusBar().clearMessage()
        self.statusBar().showMessage(msg, 5000)

    def get_selected_index_row(self):
        indexes = self.bank_transactions_table.selectedIndexes()
        if not indexes is None and len(indexes) > 0:
            row = indexes[0].row()
            return row

    @Slot()
    def enable_disable_controls(self):
        enabled = True
        row = self.get_selected_index_row()
        # if there are no transactions disable edit and delete
        if len(self.model.transactions) == 0:
            enabled = False
        elif row is None or row == len(self.model.transactions):
            # if no row is selected disable
            # if selected row is the last row then disable it
            enabled = False
        elif self.model.transactions[row].type == 'RIN_LAGANI':
            # if selected transaction is rin lagani disable edit and delete
            enabled = False

        # enable or disable button
        if enabled:
            self.edit_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        else:
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)

    @Slot()
    def update_model(self):
        self.model.load_data()
        self.model.layoutChanged.emit()
        self.bank_transactions_table.clearSelection()

    def disconnect_signal_and_remove_window(self):
        """Utility function to remove bank transaction window and its connections"""
        if self.bank_transaction_window:
            self.bank_transaction_window.transaction_saved.disconnect(
                self.update_model)
            self.bank_transaction_window = None

    @Slot()
    def add_bank_transaction(self):
        self.disconnect_signal_and_remove_window()
        self.bank_transaction_window = BankTransactionWindow(None,
                                                             self.app_ctxt,
                                                             parent=self)
        self.bank_transaction_window.transaction_saved.connect(
            self.update_model)
        self.bank_transaction_window.show()

    def edit_bank_transaction(self):
        row = self.get_selected_index_row()
        if not row is None:
            id = self.model.transactions[row].id
            # open bank transaction window
            self.disconnect_signal_and_remove_window()
            self.bank_transaction_window = BankTransactionWindow(id,
                                                                 self.app_ctxt,
                                                                 parent=self)
            self.bank_transaction_window.transaction_saved.connect(
                self.update_model)
            self.bank_transaction_window.show()

    def delete_bank_transaction(self):
        row = self.get_selected_index_row()
        if not row is None:
            id = self.model.transactions[row].id
            # show confirm delete dialog
            delete_dialog = QMessageBox(self)
            delete_dialog.setText(
                f'Are you sure you want to delete transaction?')
            delete_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            delete_dialog.setIcon(QMessageBox.Icon.Question)
            button = delete_dialog.exec_()
            # if delete is confirmed by the user
            if button == QMessageBox.Yes:
                with Session.begin() as session:
                    delete_bank_transaction_by_id(session, id)
                self.update_model()
                self.enable_disable_controls()
                self.status_bar_message('Transaction deleted successfully.')


class BankTransactionWindow(QMainWindow):
    transaction_saved = Signal()

    def __init__(self, transaction_id, app_ctxt, *args, **kwargs):
        super(BankTransactionWindow, self).__init__(*args, **kwargs)
        self.transaction_id = transaction_id
        self.app_ctxt = app_ctxt
        self.__setup_ui()
        if not self.transaction_id is None:
            self.__load_data()

    def __setup_ui(self):
        self.setWindowTitle('Bank Transaction')
        self.setWindowModality(Qt.ApplicationModal)
        # create icon
        save_icon = QIcon(self.app_ctxt.get_resource('save-32.png'))
        # date
        date_label = QLabel('Date:')
        self.date_input = QLineEdit()
        self.date_input.setInputMask('9999-00-00')
        # transaction type radio button
        self.debit_radio_button = QRadioButton('Debit')
        self.debit_radio_button.setCheckable(True)
        self.credit_radio_button = QRadioButton('Credit')
        self.credit_radio_button.setCheckable(True)
        self.deposit_radio_button = QRadioButton('Deposit')
        self.deposit_radio_button.setCheckable(True)
        # create layout for radio button
        transaction_type_label = QLabel('Transaction type:')
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.debit_radio_button)
        vbox_layout.addWidget(self.credit_radio_button)
        vbox_layout.addWidget(self.deposit_radio_button)
        # create groupbox
        self.type_group_box = QGroupBox()
        self.type_group_box.setLayout(vbox_layout)
        # amount
        amount_label = QLabel('Amount:')
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(float_info.max)
        # remarks
        remarks_label = QLabel('Remarks:')
        self.remarks_input = QLineEdit()
        # save button
        save_button = QPushButton(save_icon, 'Save transaction')
        save_button.pressed.connect(self.save_transaction)
        # form layout
        form_layout = QFormLayout()
        form_layout.addRow(date_label, self.date_input)
        form_layout.addRow(transaction_type_label, self.type_group_box)
        form_layout.addRow(amount_label, self.amount_input)
        form_layout.addRow(remarks_label, self.remarks_input)
        form_layout.addWidget(save_button)
        # create wrapper widget
        widget = QWidget()
        widget.setLayout(form_layout)
        # set central widget
        self.setCentralWidget(widget)
        # create status bar
        self.setStatusBar(QStatusBar())
        # set size to fixed
        self.setFixedSize(self.sizeHint())

    def status_bar_message(self, msg):
        self.statusBar().clearMessage()
        self.statusBar().showMessage(msg, 5000)

    def __load_data(self):
        with Session.begin() as session:
            transaction = get_bank_transaction_by_id(session,
                                                     self.transaction_id)
            if not transaction is None:
                self.date_input.setText(transaction.date)
                self.amount_input.setValue(transaction.amount)
                self.remarks_input.setText(transaction.remarks)
                if transaction.type == BankTransactionTypes.DEBIT:
                    self.debit_radio_button.setChecked(True)
                elif transaction.type == BankTransactionTypes.CREDIT:
                    self.credit_radio_button.setChecked(True)
                else:
                    self.debit_radio_button.setChecked(True)

    @Slot()
    def save_transaction(self):
        # get type of transaction
        tx_type = None
        if self.debit_radio_button.isChecked():
            tx_type = BankTransactionTypes.DEBIT
        elif self.credit_radio_button.isChecked():
            tx_type = BankTransactionTypes.CREDIT
        elif self.deposit_radio_button.isChecked():
            tx_type = BankTransactionTypes.DEPOSIT
        amount = Decimal(str(self.amount_input.value()))
        # create transaction
        transaction = BankTransaction(id=self.transaction_id, type=tx_type,
                                      amount=amount,
                                      date=self.date_input.text(),
                                      remarks=self.remarks_input.text())
        # save transaction
        with Session.begin() as session:
            errors = save_or_update_bank_transaction(session, transaction)
        # check if any error occured
        print(errors)
        if errors is None:
            self.status_bar_message('Saved transaction successfully.')
            self.transaction_saved.emit()
            self.close()
        else:
            self.status_bar_message('Transaction could not be saved.')
