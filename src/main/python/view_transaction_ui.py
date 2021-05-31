import datetime
from decimal import Decimal

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMainWindow, QLabel, QFormLayout, QWidget

from database import Session, RinLagani
from database_access import get_rin_lagani_by_id, get_sawa_asuli_by_id
from util import str_to_date, date_to_str


class ViewTransactionWindow(QMainWindow):
    def __init__(self, id, tx_type, *args, **kwargs):
        super(ViewTransactionWindow, self).__init__(*args, **kwargs)
        self.id = id
        self.tx_type = tx_type
        self.__setup_ui()
        self.__load_data()

    def __setup_ui(self):
        self.setWindowTitle('View Transaction')
        self.setWindowModality(Qt.ApplicationModal)

        member_name_header_label = QLabel('Member name:')
        self.member_name_label = QLabel()

        form_layout = QFormLayout()
        form_layout.addRow(member_name_header_label, self.member_name_label)

        if self.tx_type == RinLagani:
            date_header_label = QLabel('Date:')
            self.date_label = QLabel()
            amount_header_label = QLabel('Amount:')
            self.amount_label = QLabel()
            remarks_header_label = QLabel('Remarks:')
            self.remarks_label = QLabel()
            form_layout.addRow(date_header_label, self.date_label)
            form_layout.addRow(amount_header_label, self.amount_label)
            form_layout.addRow(remarks_header_label, self.remarks_label)
        else:
            start_date_header_label = QLabel('Start date:')
            self.start_date_label = QLabel()
            end_date_header_label = QLabel('End date:')
            self.end_date_label = QLabel()
            days_header_label = QLabel('Days:')
            self.days_label = QLabel()
            lagani_rin_header_label = QLabel('Lagani rin:')
            self.lagani_rin_label = QLabel()
            kista_per_month_header_label = QLabel('Kista per month:')
            self.kista_per_month_label = QLabel()
            amount_header_label = QLabel('Amount')
            self.amount_label = QLabel()
            byaj_per_day_header_label = QLabel('Byaj per day:')
            self.byaj_per_day_label = QLabel()
            byaj_header_label = QLabel('Byaj:')
            self.byaj_label = QLabel()
            harjana_header_label = QLabel('Harjana:')
            self.harjana_label = QLabel()
            bachat_header_label = QLabel('Bachat:')
            self.bachat_label = QLabel()
            grand_total_header_label = QLabel('Grand total:')
            self.grand_total_label = QLabel()
            banki_sawa_header_label = QLabel('Banki sawa:')
            self.bank_sawa_label = QLabel()
            remarks_header_label = QLabel('Remarks')
            self.remarks_label = QLabel()
            form_layout.addRow(start_date_header_label, self.start_date_label)
            form_layout.addRow(end_date_header_label, self.end_date_label)
            form_layout.addRow(lagani_rin_header_label, self.lagani_rin_label)
            form_layout.addRow(kista_per_month_header_label,
                               self.kista_per_month_label)
            form_layout.addRow(amount_header_label, self.amount_label)
            form_layout.addRow(days_header_label, self.days_label)
            form_layout.addRow(byaj_per_day_header_label,
                               self.byaj_per_day_label)
            form_layout.addRow(byaj_header_label, self.byaj_label)
            form_layout.addRow(harjana_header_label, self.harjana_label)
            form_layout.addRow(bachat_header_label, self.bachat_label)
            form_layout.addRow(grand_total_header_label, self.grand_total_label)
            form_layout.addRow(banki_sawa_header_label, self.bank_sawa_label)
            form_layout.addRow(remarks_header_label, self.remarks_label)
        # create wrapper widget
        widget = QWidget()
        widget.setLayout(form_layout)
        # set central widget
        self.setCentralWidget(widget)
        # self.setFixedSize(self.sizeHint())

    def __load_data(self):
        if self.tx_type == RinLagani:
            with Session.begin() as session:
                rin_lagani = get_rin_lagani_by_id(session, self.id)
                self.member_name_label.setText(rin_lagani.member.name)
                self.date_label.setText(rin_lagani.date)
                self.amount_label.setText(str(rin_lagani.amount))
                self.remarks_label.setText(rin_lagani.remarks)
        else:
            with Session.begin() as session:
                sawa_asuli = get_sawa_asuli_by_id(session, self.id)
                if sawa_asuli.rin_lagani is None:
                    # bachat only
                    self.start_date_label.setText('')
                    self.lagani_rin_label.setText('0')
                    self.kista_per_month_label.setText('0')
                    self.days_label.setText('0')
                    self.byaj_per_day_label.setText('0')
                    self.bank_sawa_label.setText('0')
                else:
                    start_date, banki_sawa = self.get_start_date_and_banki_sawa(
                        sawa_asuli)
                    self.start_date_label.setText(start_date)
                    self.lagani_rin_label.setText(str(banki_sawa))
                    self.kista_per_month_label.setText(
                        str(sawa_asuli.rin_lagani.kista_per_month))
                    time_delta = str_to_date(sawa_asuli.date) - str_to_date(
                        start_date)
                    days = time_delta.days
                    self.days_label.setText(str(days))
                    byaj_per_day = ((banki_sawa * Decimal('0.12'))
                                    / Decimal('365'))
                    self.byaj_per_day_label.setText(
                        '{:.2f}'.format(byaj_per_day))
                    banki_sawa = banki_sawa - sawa_asuli.amount
                    self.bank_sawa_label.setText(str(banki_sawa))

                self.member_name_label.setText(sawa_asuli.member.name)
                self.end_date_label.setText(sawa_asuli.date)
                self.amount_label.setText(str(sawa_asuli.amount))
                self.byaj_label.setText(str(sawa_asuli.byaj))
                self.harjana_label.setText(str(sawa_asuli.harjana))
                self.bachat_label.setText(str(sawa_asuli.bachat))
                self.remarks_label.setText(str(sawa_asuli.remarks))
                grand_total = (sawa_asuli.amount + sawa_asuli.byaj
                               + sawa_asuli.harjana + sawa_asuli.bachat)
                self.grand_total_label.setText(str(grand_total))

    def get_start_date_and_banki_sawa(self, sawa_asuli):
        # get date of transaction just before this transaction
        transactions = sawa_asuli.rin_lagani.sawa_asulis
        transactions.sort(key=lambda tx: str_to_date(tx.date))

        dt = str_to_date(sawa_asuli.date)
        before_date = sawa_asuli.rin_lagani.date
        banki_sawa = sawa_asuli.rin_lagani.amount
        # ignore rin lagani in calculations
        for asuli in transactions[1:]:
            if str_to_date(asuli.date) >= dt:
                break
            banki_sawa -= asuli.amount
            before_date = asuli.date
        # if before transaction is sawa asuli then banki sawa is mot equal to the rin lagani amount
        if banki_sawa != sawa_asuli.rin_lagani.amount:
            before_date = date_to_str(
                str_to_date(before_date) + datetime.timedelta(days=1))

        return before_date, banki_sawa
