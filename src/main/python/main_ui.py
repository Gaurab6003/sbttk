from PySide2.QtCore import QSize, Qt, Slot
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtWidgets import (
    QMainWindow, QHBoxLayout, QWidget, QScrollArea, QStatusBar, QAction, QMenu,
    QToolBar
)

from member_detail_ui import MemberDetailView
from member_list_ui import MemberListView
from settings_ui import SettingsWindow, AboutDialog
from bank_transaction_ui import BankTransactionsWindow
from date_range_summary_ui import DateRangeSummaryWindow
from member_wise_summary import MemberWiseSummaryWindow


class MainWindow(QMainWindow):
    """This is application's main window."""

    def __init__(self, app_ctxt, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.app_ctxt = app_ctxt
        self.settings_window = None
        self.about_window = None
        self.bank_transactions_window = None
        self.date_range_summary_window = None
        self.member_wise_summary_window = None
        self.__setup_ui()

    def __setup_ui(self):
        """Sets up main UI"""
        self.setWindowTitle('SBTTK')
        self.setMinimumSize(QSize(800, 600))
        stylesheet = open(self.app_ctxt.get_resource('style.qss'), 'r').read()
        self.setStyleSheet(stylesheet)
        # setup icons and actions
        self.__create_icons()
        self.__create_actions()
        # create menu, toolbar ans status bar
        self.__setup_menu_and_toolbar()
        self.setStatusBar(QStatusBar(self))
        # create main layout
        self.hbox_layout = QHBoxLayout()
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        self.hbox_layout.setSpacing(0)
        # create member list view
        self.member_list_view = MemberListView()
        self.hbox_layout.addWidget(self.member_list_view)
        # create member detail view
        self.member_details_view = MemberDetailView(self.app_ctxt)
        self.hbox_layout.addWidget(self.member_details_view)
        # create coordination between list view and detail view and main view
        self.member_list_view.member_selection_changed.connect(
            self.member_details_view.set_member
        )
        self.member_details_view.member_data_changed.connect(
            self.member_list_view.update_member_list
        )
        self.member_details_view.status_bar_updated.connect(
            self.update_status_bar
        )
        # wrap layout inside widget
        widget = QWidget()
        widget.setLayout(self.hbox_layout)
        # wrap widget inside scrollbar
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        # set widget wrapped inside scrollbar as central widget
        self.setCentralWidget(scroll)

    def __create_icons(self):
        """creates icons"""
        self.add_member_icon = QIcon(
            self.app_ctxt.get_resource('add-user-32.png'))
        self.summary_icon = QIcon(
            self.app_ctxt.get_resource('business-report-32.png'))
        self.bank_icon = QIcon(
            self.app_ctxt.get_resource('bank-building-32.png'))
        self.add_icon = QIcon(self.app_ctxt.get_resource('plus-32.png'))
        self.toolbar_icon = QIcon(self.app_ctxt.get_resource('toolbar-32.png'))
        self.about_icon = QIcon(self.app_ctxt.get_resource('about-32.png'))
        self.settings_icon = QIcon(
            self.app_ctxt.get_resource('settings-32.png'))
        self.exit_icon = QIcon(self.app_ctxt.get_resource('exit-32.png'))

    def __create_actions(self):
        """Creates actions and connects their signals to slots"""
        # member
        # member
        self.add_member = QAction(self.add_member_icon, '&Add member', self)
        self.add_member.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_A))
        self.add_member.triggered.connect(self.handle_add_member)
        # monthly summary
        self.date_range_summary = QAction(self.summary_icon,
                                          '&Date range summary', self)
        self.date_range_summary.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_D))
        self.date_range_summary.triggered.connect(
            self.handle_date_range_summary)
        # member wise summary
        self.member_wise_summary = QAction(self.summary_icon,
                                           '&Member wise summary', self)
        self.member_wise_summary.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_M))
        self.member_wise_summary.triggered.connect(
            self.handle_member_wise_summary)
        # view bank transactions
        self.view_bank_transactions = QAction(self.bank_icon,
                                              '&View bank transactions',
                                              self)
        self.view_bank_transactions.setShortcut(
            QKeySequence(Qt.CTRL + Qt.Key_B))
        self.view_bank_transactions.triggered.connect(
            self.handle_view_bank_transactions)
        # show/hide toolbar
        self.show_hide_toolbar = QAction(self.toolbar_icon,
                                         '&Show/hide toolbar', self)
        self.show_hide_toolbar.triggered.connect(self.handle_show_hide_toolbar)
        self.show_hide_toolbar.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_T))
        # show about
        self.show_about = QAction(self.about_icon, '&About', self)
        self.show_about.triggered.connect(self.handle_show_about)
        # show settings
        self.settings = QAction(self.settings_icon, '&Settings', self)
        self.settings.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_S))
        self.settings.triggered.connect(self.handle_settings)
        # exit app
        self.exit_app = QAction(self.exit_icon, '&Exit', self)
        self.exit_app.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Q))
        self.exit_app.triggered.connect(self.handle_exit_app)

    def __setup_menu_and_toolbar(self):
        """Creates menu and toolbar for the main UI."""
        # craete member menu
        member_menu = QMenu('Member')
        member_menu.addAction(self.add_member)
        # create summary menu
        summary_menu = QMenu('Summary')
        summary_menu.addActions(
            [self.date_range_summary, self.member_wise_summary])
        # create bank transaction menu
        bank_transaction_menu = QMenu('Bank transaction')
        bank_transaction_menu.addAction(self.view_bank_transactions)
        # create settings menu
        settings_menu = QMenu('Settings')
        settings_menu.addActions(
            [self.show_hide_toolbar, self.settings, self.show_about,
             self.exit_app])
        # create main menu
        menu = self.menuBar()
        menu.addMenu(member_menu)
        menu.addMenu(summary_menu)
        menu.addMenu(bank_transaction_menu)
        menu.addMenu(settings_menu)
        # create toolbar
        self.toolbar = QToolBar('Actions')
        self.toolbar.setIconSize(QSize(32, 32))
        self.toolbar.addActions(
            [self.add_member, self.date_range_summary, self.settings])
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        self.toolbar.setVisible(False)  # hide toolbar by default

    @Slot()
    def update_status_bar(self, message, time=0):
        """
        Update message and decoration of status bar.
        :param message: message to show in status bar
        :param type: message type('error', 'success', 'message')
        """
        self.statusBar().clearMessage()
        if time == 0:
            self.statusBar().showMessage(message)
        else:
            self.statusBar().showMessage(message, timeout=time)

    @Slot()
    def handle_add_member(self):
        self.member_details_view.set_member(None)

    @Slot()
    def handle_show_hide_toolbar(self):
        self.toolbar.setVisible(not self.toolbar.isVisible())

    @Slot()
    def handle_exit_app(self):
        self.app_ctxt.app.closeAllWindows()

    @Slot()
    def handle_settings(self):
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.app_ctxt, parent=self)
        self.settings_window.show()

    @Slot()
    def handle_show_about(self):
        if self.about_window is None:
            self.about_window = AboutDialog(parent=self)
        self.about_window.show()

    @Slot()
    def handle_view_bank_transactions(self):
        if self.bank_transactions_window is None:
            self.bank_transactions_window = BankTransactionsWindow(
                app_ctxt=self.app_ctxt, parent=self)
        self.bank_transactions_window.showMaximized()

    @Slot()
    def handle_date_range_summary(self):
        self.date_range_summary_window = None
        self.date_range_summary_window = DateRangeSummaryWindow(parent=self)
        self.date_range_summary_window.showMaximized()

    @Slot()
    def handle_member_wise_summary(self):
        self.member_wise_summary_window = None
        self.member_wise_summary_window = MemberWiseSummaryWindow(parent=self)
        self.member_wise_summary_window.showMaximized()