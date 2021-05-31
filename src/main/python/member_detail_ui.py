from pathlib import Path

from PySide2.QtCore import QAbstractTableModel, Qt, Signal, Slot
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (QVBoxLayout, QLabel, QWidget, QTableView,
                               QSpinBox, QLineEdit, QPushButton, QHBoxLayout,
                               QFormLayout, QMessageBox, QFileDialog)
from openpyxl import Workbook

from database import Session, RinLagani, SawaAsuli
from database_access import (MemberDto, to_member, to_member_dto,
                             get_member_by_id, save_or_update_member,
                             delete_member_by_id, get_transactions_by_member_id,
                             delete_rin_lagani_by_id, delete_sawa_asuli_by_id)
from rin_lagani_ui import RinLaganiWindow
from sawa_asuli_ui import SawaAsuliWindow
from util import table_models_to_excel_sheet
from view_transaction_ui import ViewTransactionWindow


class TransactionsTableModel(QAbstractTableModel):
    def __init__(self, member_id, *args, **kwargs):
        super(TransactionsTableModel, self).__init__(*args, **kwargs)
        self.member_id = member_id
        self.transactions = []
        self.totals = {}
        self.load_data()

    def load_data(self):
        with Session.begin() as session:
            self.transactions, self.totals = get_transactions_by_member_id(
                session, self.member_id)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            # if it is last row show totals
            if row == len(self.transactions):
                if col == 0: return 'Total'
                if col == 1: return str(self.totals['lagani_total'])
                if col == 2: return str(self.totals['asuli_total'])
                if col == 3: return str(self.totals['byaj_total'])
                if col == 4: return str(self.totals['harjana_total'])
                if col == 5: return str(self.totals['bachat_total'])
                if col == 6: return str(self.totals['banki_sawa'])
                if col == 7: return str(self.totals['grand_total'])
            else:
                # else show normal transactions
                tx = self.transactions[row]
                if col == 0: return tx.date
                if col == 1:
                    if tx.is_alya_rin:
                        return str(tx.rin_lagani) + ' (Alya rin)'
                    else:
                        return str(tx.rin_lagani)
                if col == 2: return str(tx.sawa_asuli)
                if col == 3: return str(tx.byaj)
                if col == 4: return str(tx.harjana)
                if col == 5: return str(tx.bachat)
                if col == 6: return str(tx.banki_sawa)
                if col == 7:
                    if tx.is_rin_lagani:
                        return '0'
                    else:
                        return str(tx.total)
                if col == 8: return str(tx.remarks)

    def rowCount(self, parent):
        return len(self.transactions) + 1

    def columnCount(self, parent):
        return 9

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0: return 'Date'
            if section == 1: return 'Lagani'
            if section == 2: return 'Asuli'
            if section == 3: return 'Byaj'
            if section == 4: return 'Harjana'
            if section == 5: return 'Bachat'
            if section == 6: return 'Banki Sawa'
            if section == 7: return 'Grand total'
            if section == 8: return 'Remarks'

        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return section + 1


class MemberDetailView(QWidget):
    """Member detail view."""

    member_data_changed = Signal()
    status_bar_updated = Signal(str, int)
    STATUS_BAR_MSG_TIME = 5000

    def __init__(self, app_ctxt, *args, **kwargs):
        super(MemberDetailView, self).__init__(*args, **kwargs)
        self.app_ctxt = app_ctxt
        self.member_dto = MemberDto.default()
        self.rin_lagani_window = None
        self.sawa_asuli_window = None
        self.view_transaction_window = None
        self.__setup_ui()

    def __setup_ui(self):
        self.setContentsMargins(0, 0, 0, 0)
        # create icons
        save_icon = QIcon(self.app_ctxt.get_resource('save-32.png'))
        delete_icon = QIcon(self.app_ctxt.get_resource('trash-32.png'))
        edit_icon = QIcon(self.app_ctxt.get_resource('edit-32.png'))
        export_icon = QIcon(self.app_ctxt.get_resource('xls-export-32.png'))
        print_icon = QIcon(self.app_ctxt.get_resource('print-32.png'))
        # member form
        account_no_label = QLabel('Account number:')
        self.account_no_input = QSpinBox()
        self.account_no_input.setMaximumWidth(300)
        name_label = QLabel('Name:')
        self.name_input = QLineEdit()
        self.name_input.setMaximumWidth(300)
        # create save button
        save_member_button = QPushButton(save_icon, 'Save user')
        save_member_button.setFixedWidth(180)
        save_member_button.clicked.connect(self.save_member)
        # delete member button
        self.delete_member_button = QPushButton(delete_icon, 'Delete user')
        self.delete_member_button.setFixedWidth(180)
        self.delete_member_button.clicked.connect(self.delete_member)
        # create member form layout
        form_layout = QFormLayout()
        form_layout.addRow(account_no_label, self.account_no_input)
        form_layout.addRow(name_label, self.name_input)
        form_layout.addWidget(save_member_button)
        form_layout.addWidget(self.delete_member_button)
        # rin lagani button
        self.rin_lagani_button = QPushButton('Rin lagani')
        self.rin_lagani_button.setFixedWidth(180)
        self.rin_lagani_button.clicked.connect(
            lambda: self.handle_rin_lagani(None))
        # sawa asuli button
        self.sawa_asuli_button = QPushButton('Sawa Asuli')
        self.sawa_asuli_button.setFixedWidth(180)
        self.sawa_asuli_button.clicked.connect(
            lambda: self.handle_sawa_asuli(None))
        # edit latest transaction button
        self.edit_button = QPushButton(edit_icon, 'Edit transaction')
        self.edit_button.setFixedWidth(180)
        self.edit_button.clicked.connect(self.handle_transaction_edit)
        # delete latest transaction
        self.delete_button = QPushButton(delete_icon, 'Delete transaction')
        self.delete_button.setFixedWidth(180)
        self.delete_button.clicked.connect(self.handle_transaction_delete)
        # export transactions button
        self.export_button = QPushButton(export_icon, 'Export')
        self.export_button.setFixedWidth(180)
        self.export_button.pressed.connect(self.export_transactions)
        # view transaction button
        self.view_button = QPushButton('View transaction')
        self.view_button.setFixedWidth(180)
        self.view_button.pressed.connect(self.handle_transaction_view)
        # create layout for buttons
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.export_button)
        vbox_layout.addWidget(self.rin_lagani_button)
        vbox_layout.addWidget(self.sawa_asuli_button)
        vbox_layout.addWidget(self.view_button)
        vbox_layout.addWidget(self.edit_button)
        vbox_layout.addWidget(self.delete_button)
        vbox_layout.addWidget(self.delete_member_button)
        # create layout for member for and actions container
        hbox_layout = QHBoxLayout()
        hbox_layout.setContentsMargins(0, 0, 0, 0)
        hbox_layout.setSpacing(5)
        # hbox_layout.addLayout(vbox_layout)
        hbox_layout.addLayout(vbox_layout)
        hbox_layout.addLayout(form_layout)
        # wrap member form and actions in a widget
        search_form_container = QWidget()
        search_form_container.setLayout(hbox_layout)
        # create transactions table
        self.transactions_table = QTableView()
        self.model = TransactionsTableModel(self.member_dto.id)
        self.transactions_table.setModel(self.model)
        self.transactions_table.selectionModel().selectionChanged.connect(
            self.enable_disable_member_actions)
        # create layout
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(search_form_container)
        vbox_layout.addWidget(self.transactions_table)
        # set the layout to vbox_layout
        self.setLayout(vbox_layout)
        # connect to member data changed to enable/disable member actions
        self.enable_disable_member_actions()

    def enable_disable_member_actions(self):
        if self.member_dto.id is None:
            self.delete_member_button.setEnabled(False)
            self.rin_lagani_button.setEnabled(False)
            self.sawa_asuli_button.setEnabled(False)
            self.export_button.setEnabled(False)
        else:
            self.delete_member_button.setEnabled(True)
            self.sawa_asuli_button.setEnabled(True)
            self.rin_lagani_button.setEnabled(True)
            self.export_button.setEnabled(True)
        # only allow edit delete button when there are transactions
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.view_button.setEnabled(False)
        # get selected indexes
        indexes = self.transactions_table.selectedIndexes()
        if not indexes is None and len(indexes) > 0:
            row = indexes[0].row()
            # can view any transaction
            if row < len(self.model.transactions):
                self.view_button.setEnabled(True)
            # only allow edit and delete to last transactions
            if row == len(self.model.transactions) - 1:
                self.edit_button.setEnabled(True)
                self.delete_button.setEnabled(True)

    def clear_inputs(self):
        self.account_no_input.clear()
        self.name_input.clear()

    @Slot()
    def update_model(self):
        self.model.member_id = self.member_dto.id
        self.model.load_data()
        self.model.load_data()
        self.model.layoutChanged.emit()

    @Slot()
    def set_member(self, id):
        """Set member to show detailed view."""
        if id is None:
            self.member_dto = MemberDto.default()
            self.account_no_input.clear()
            self.name_input.clear()
            self.member_data_changed.emit()
        else:
            with Session.begin() as session:
                self.member_dto = to_member_dto(get_member_by_id(session, id))
            self.account_no_input.setValue(self.member_dto.account_no)
            self.name_input.setText(self.member_dto.name)
        self.update_model()
        self.enable_disable_member_actions()

    @Slot()
    def save_member(self):
        self.status_bar_updated.emit('Saving member', self.STATUS_BAR_MSG_TIME)
        self.member_dto.account_no = self.account_no_input.value()
        self.member_dto.name = self.name_input.text()
        with Session.begin() as session:
            errors = save_or_update_member(session, to_member(self.member_dto))
        if errors:
            error_text = ''.join(errors.values())
            self.status_bar_updated.emit(error_text, 0)
        else:
            self.member_dto = MemberDto.default()
            self.clear_inputs()
            self.update_model()
            self.enable_disable_member_actions()
            self.member_data_changed.emit()
            self.status_bar_updated.emit('Member saved successfully',
                                         self.STATUS_BAR_MSG_TIME)

    @Slot()
    def delete_member(self):
        # show confirm delete dialog
        delete_dialog = QMessageBox(self)
        delete_dialog.setText(
            f'Are you sure you want to delete {self.member_dto.name}?')
        delete_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        delete_dialog.setIcon(QMessageBox.Icon.Question)
        button = delete_dialog.exec_()
        # if delete is confirmed delete the user
        if button == QMessageBox.Yes:
            with Session.begin() as session:
                delete_member_by_id(session, self.member_dto.id)
            self.member_dto = MemberDto.default()
            self.clear_inputs()
            self.update_model()
            self.enable_disable_member_actions()
            self.member_data_changed.emit()
            self.status_bar_updated.emit('Member deleted.',
                                         self.STATUS_BAR_MSG_TIME)

    @Slot()
    def handle_rin_lagani(self, id=None):
        # remove previous window and its connection
        # This is done so that a new window is created for different id arguments.
        if not self.rin_lagani_window is None:
            self.rin_lagani_window.rin_lagani_changed.disconnect(
                self.handle_rin_lagani_or_sawa_asuli_changed)
            self.rin_lagani_window = None
        # create new window and connection
        self.rin_lagani_window = RinLaganiWindow(self.member_dto.id, id,
                                                 self.app_ctxt, parent=self)
        self.rin_lagani_window.rin_lagani_changed.connect(
            self.handle_rin_lagani_or_sawa_asuli_changed)
        self.rin_lagani_window.show()

    @Slot()
    def handle_sawa_asuli(self, id=None):
        # remove previous window and its connection
        # This is done so that a new window is created for different id arguments.
        if not self.sawa_asuli_window is None:
            self.sawa_asuli_window.sawa_asuli_changed.disconnect(
                self.handle_rin_lagani_or_sawa_asuli_changed)
            self.sawa_asuli_window = None
        # create new window and connection
        self.sawa_asuli_window = SawaAsuliWindow(self.member_dto.id,
                                                 self.app_ctxt, id,
                                                 parent=self)
        self.sawa_asuli_window.sawa_asuli_changed.connect(
            self.handle_rin_lagani_or_sawa_asuli_changed)
        # show new window
        self.sawa_asuli_window.show()

    @Slot()
    def handle_rin_lagani_or_sawa_asuli_changed(self):
        self.update_model()
        self.enable_disable_member_actions()

    @Slot()
    def handle_transaction_edit(self):
        transaction = self.model.transactions[-1]
        # print('transaction id--->', transaction.id)
        if transaction.is_rin_lagani:
            self.handle_rin_lagani(transaction.id)
        else:
            self.handle_sawa_asuli(transaction.id)

    @Slot()
    def handle_transaction_delete(self):
        transaction = self.model.transactions[-1]
        # show confirm delete dialog
        delete_dialog = QMessageBox(self)
        delete_dialog.setText('Are you sure you want to delete transaction?')
        delete_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        delete_dialog.setIcon(QMessageBox.Icon.Question)
        button = delete_dialog.exec_()
        # if delete is confirmed delete the user
        if button == QMessageBox.Yes:
            with Session.begin() as session:
                if transaction.is_rin_lagani:
                    errors = delete_rin_lagani_by_id(session, transaction.id)
                else:
                    errors = delete_sawa_asuli_by_id(session, transaction.id)
            if errors is None:
                self.update_model()
                self.enable_disable_member_actions()
                self.status_bar_updated.emit('Transaction deleted.',
                                             self.STATUS_BAR_MSG_TIME)
            else:
                self.status_bar_updated.emit(
                    'Transaction could not be deleted.',
                    self.STATUS_BAR_MSG_TIME)

    @Slot()
    def export_transactions(self):
        name = self.name_input.text()
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
        table_models_to_excel_sheet([self.model], ws)
        try:
            wb.save(file_name)
        except IOError as ex:
            self.status_bar_updated.emit('Could not save file',
                                         self.STATUS_BAR_MSG_TIME)

    @Slot()
    def handle_transaction_view(self):
        self.view_transaction_window = None
        # get selected indexes
        indexes = self.transactions_table.selectedIndexes()
        if not indexes is None and len(indexes) > 0:
            row = indexes[0].row()
            tx = self.model.transactions[row]
            if tx.is_rin_lagani:
                tx_type = RinLagani
            else:
                tx_type = SawaAsuli
            self.view_transaction_window = ViewTransactionWindow(tx.id, tx_type,
                                                                 parent=self)
            self.view_transaction_window.show()
