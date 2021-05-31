from pathlib import Path

from PySide2.QtCore import Qt, Slot, QAbstractTableModel
from PySide2.QtWidgets import (QMainWindow, QVBoxLayout, QTableView,
                               QPushButton, QStatusBar, QWidget, QFileDialog)
from openpyxl import Workbook

from database import Session
from database_access import get_member_wise_summary
from util import table_models_to_excel_sheet


class MemberWiseSummaryModel(QAbstractTableModel):
    def __init__(self, *args, **kwargs):
        super(MemberWiseSummaryModel, self).__init__(*args, **kwargs)
        self.summaries = []
        self.totals = {}
        self.__load_data()

    def __load_data(self):
        with Session.begin() as session:
            self.summaries, self.totals = get_member_wise_summary(session)
        self.layoutChanged.emit()

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            if row == len(self.summaries):
                if col == 0: return 'Total'
                if col == 1: return str(self.totals['alya_rin'])
                if col == 2: return str(self.totals['total_rin_lagani'])
                if col == 3: return str(self.totals['total_sawa_asuli'])
                if col == 4: return str(self.totals['total_byaj'])
                if col == 5: return str(self.totals['total_harjana'])
                if col == 6: return str(self.totals['total_bachat'])
                if col == 7: return str(self.totals['banki_sawa'])
            else:
                summary = self.summaries[row]
                if col == 0: return summary.name
                if col == 1: return str(summary.alya_rin)
                if col == 2: return str(summary.total_rin_lagani)
                if col == 3: return str(summary.total_sawa_asuli)
                if col == 4: return str(summary.total_byaj)
                if col == 5: return str(summary.total_harjana)
                if col == 6: return str(summary.total_bachat)
                if col == 7: return str(summary.banki_sawa)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0: return 'Member name'
            if section == 1: return 'Alya rin'
            if section == 2: return 'Total rin lagani'
            if section == 3: return 'Total sawa asuli'
            if section == 4: return 'Total byaj'
            if section == 5: return 'Total harjana'
            if section == 6: return 'Total bachat'
            if section == 7: return 'Banki sawa'

    def columnCount(self, parent):
        return 8

    def rowCount(self, parent):
        return len(self.summaries) + 1


class MemberWiseSummaryWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MemberWiseSummaryWindow, self).__init__(*args, **kwargs)
        self.__setup_ui()

    def __setup_ui(self):
        # export transactions button
        export_button = QPushButton('Export summary')
        export_button.setMaximumWidth(200)
        export_button.clicked.connect(self.handle_export)
        # create table
        self.summary_model = MemberWiseSummaryModel()
        self.summary_table = QTableView()
        self.summary_table.setModel(self.summary_model)
        # create layout
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(export_button)
        vbox_layout.addWidget(self.summary_table)
        # create wrapper widget
        widget = QWidget()
        widget.setLayout(vbox_layout)
        # set central widget
        self.setCentralWidget(widget)
        self.setStatusBar(QStatusBar())

    @Slot()
    def handle_export(self):
        name = 'member-wise-summary'
        default_path = str(Path.home().joinpath(name + '.xlsx'))
        file_name, _ = QFileDialog.getSaveFileName(self, "Save", default_path,
                                                   "Excel (*.xlsx )")
        # if no file selected return
        if file_name == '':
            return
        # save model to workbook
        wb = Workbook()
        ws = wb.active
        ws.title = name
        table_models_to_excel_sheet([self.summary_model], ws)
        try:
            wb.save(file_name)
        except IOError as ex:
            self.statusBar().clearMessage()
            self.statusBar().showMessage('Could not save file', 5000)
