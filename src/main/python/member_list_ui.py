from PySide2.QtCore import (Qt, QAbstractListModel, Signal, Slot, QRegExp,
                            QSortFilterProxyModel)
from PySide2.QtWidgets import (QListView, QWidget, QVBoxLayout, QLineEdit,
                               QScrollBar)

from database import Session
from database_access import get_member_list, to_member_dto


class MemberListModel(QAbstractListModel):
    def __init__(self, *args, **kwargs):
        super(MemberListModel, self).__init__(*args, **kwargs)
        self.member_list = []
        self.load_data()

    def load_data(self):
        with Session.begin() as session:
            self.member_list = list(
                map(to_member_dto, get_member_list(session)))

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.member_list[index.row()].name

    def rowCount(self, parent):
        return len(self.member_list)


class MemberListView(QWidget):
    """Creates list view of members"""

    member_selection_changed = Signal(int)

    def __init__(self, *args, **kwargs):
        super(MemberListView, self).__init__(*args, **kwargs)
        self.__setup_ui()

    def __setup_ui(self):
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(150)
        self.setMaximumWidth(300)
        # create search bar
        self.search_box = QLineEdit()
        self.search_box.textChanged.connect(self.search_text_changed)
        self.search_box.setPlaceholderText('Member name...')
        # create list view
        self.list_view = QListView()
        self.model = MemberListModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)  # proxy to filter names
        self.list_view.setModel(self.proxy_model)
        self.list_view.selectionModel().selectionChanged.connect(
            self.list_view_selection_changed)
        scrollbar = QScrollBar()
        self.list_view.addScrollBarWidget(scrollbar, Qt.AlignRight)
        # create layout
        vbox_layout = QVBoxLayout()
        vbox_layout.setContentsMargins(10, 10, 0, 0)
        vbox_layout.setSpacing(10)
        vbox_layout.addWidget(self.search_box)
        vbox_layout.addWidget(self.list_view)
        # set layout to vbox_layout
        self.setLayout(vbox_layout)

    @Slot()
    def search_text_changed(self):
        search_text = self.search_box.text().strip()
        if search_text != '':
            self.proxy_model.setFilterRegExp(
                QRegExp(search_text, Qt.CaseInsensitive, QRegExp.FixedString))
        else:
            self.proxy_model.setFilterRegExp('.*')
        self.model.layoutChanged.emit()

    @Slot()
    def list_view_selection_changed(self):
        """When member selection is changed emit member_selection_changed"""
        indexes = self.list_view.selectedIndexes()
        if not indexes is None:
            selected_member_id = self.model.member_list[indexes[0].row()].id
            self.member_selection_changed.emit(selected_member_id)

    @Slot()
    def update_member_list(self):
        """Handle member information changed for member in list view."""
        self.model.load_data()
        self.model.layoutChanged.emit()
        self.list_view.selectionModel().clearSelection()
