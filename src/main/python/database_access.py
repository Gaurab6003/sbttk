from decimal import Decimal

from dataclasses import dataclass
from sqlalchemy import and_

from database import (Member, RinLagani, SawaAsuli, Settings,
                      BankTransactionTypes, BankTransaction)
from util import (str_to_date, get_month_start, get_month_end)


@dataclass
class MemberDto:
    """Member data transfer object"""
    id: int
    account_no: int
    name: str

    @classmethod
    def default(cls):
        """
        Creates MemberDto with default parameters
        :return: MemberDto with default parameter
        """
        return MemberDto(None, 0, '')


def to_member_dto(member):
    """
    Convert Member to MemberDto.
    :param member: Member to be converted
    :return: Converted MemberDto
    """
    return MemberDto(id=member.id, account_no=member.account_no,
                     name=member.name)


def to_member(dto):
    """
    Convert MemberDto to Member.
    :param dto: MemberDto to be converted
    :return: Converted MemberDto
    """
    return Member(id=dto.id, account_no=dto.account_no, name=dto.name)


def get_member_list(session):
    """
    Get the list of all the members in the database.
    :param session: current database session
    :return: list of members in the database
    """
    return session.query(Member).order_by(Member.account_no).all()


def save_or_update_member(session, member):
    """
    Updates the member if it has id or else persists the new member.
    :param session: current database session
    :param member: member to be saved
    :return: error if any
    """
    errors = {}
    if member.name == "":
        errors['name'] = 'Name cannot be blank.'

    count = session.query(Member).filter(
        and_(Member.account_no == member.account_no,
             Member.id != member.id)).count()
    if count > 0 or member.account_no <= 0:
        errors['account_no'] = (
            'Account number is negative or it has already been taken.')

    if len(errors.keys()) > 0:
        return None, errors

    session.merge(member)


def delete_member_by_id(session, id):
    """
    Delete a member from database.
    :param session: current database session
    :param member: member to be deleted
    """
    member = get_member_by_id(session, id)
    if member:
        session.delete(member)


def get_member_by_id(session, id):
    """
    Get a member with matching id in the database.
    :param session: current database session
    :param id: id of the member
    :return: member with matching id
    """
    return session.query(Member).filter(Member.id == id).first()


@dataclass
class RinLaganiDto:
    id: int
    date: str
    amount: Decimal
    is_alya_rin: bool
    kista_per_month: Decimal
    remarks: str
    member_id: int

    @classmethod
    def default(cls):
        """
        Creates MemberDto object with default values
        :return: MemberDto object with default parameters
        """
        return RinLaganiDto(None, '', Decimal(0), False, Decimal(0), '', None)


def to_rin_lagani_dto(rin_lagani):
    """
    Convert RinLagani to RinLaganiDto.
    :param rin_lagani: RinLagani to be converted
    :return: Converted RinLaganiDto
    """
    return RinLaganiDto(id=rin_lagani.id, date=rin_lagani.date,
                        amount=rin_lagani.amount,
                        is_alya_rin=rin_lagani.is_alya_rin,
                        kista_per_month=rin_lagani.kista_per_month,
                        remarks=rin_lagani.remarks,
                        member_id=rin_lagani.member_id)


def to_rin_lagani(rin_lagani_dto):
    """
    Convert RinLaganiDto to RinLagani.
    :param rin_lagani_dto: RinLaganiDto to be converted
    :return: Converted RinLagani
    """
    return RinLagani(id=rin_lagani_dto.id, date=rin_lagani_dto.date,
                     amount=rin_lagani_dto.amount,
                     is_alya_rin=rin_lagani_dto.is_alya_rin,
                     kista_per_month=rin_lagani_dto.kista_per_month,
                     remarks=rin_lagani_dto.remarks,
                     member_id=rin_lagani_dto.member_id)


def validate_rin_lagani(session, rin_lagani, latest_tx, latest_rin_lagani):
    errors = {}
    # rin lagani amount cannot be negetive or zero
    if rin_lagani.amount <= Decimal(0):
        errors['rin_lagani'] = 'Rin lagani amount not valid.'
    # check validity of date
    date = str_to_date(rin_lagani.date)
    if date is None:
        errors['date'] = 'Invalid date'
        return errors
    # check if member exists with given member_id
    if get_member_by_id(session, rin_lagani.member_id) is None:
        errors['member_id'] = 'Invalid member.'
        return errors
    # if there is no transaction yet then allow save
    if latest_tx is None:
        return errors
    # check if it is the latest transaction
    if str_to_date(rin_lagani.date) <= str_to_date(latest_tx.date):
        errors['date'] = 'Date cannot be in the past than latest transaction.'
        return errors
    # if there are no rin laganis allow save
    if latest_rin_lagani is None:
        return errors
    # calculate if previous banki sawa are cleared
    if calculate_banki_sawa(latest_rin_lagani) > Decimal(0):
        errors['rin_lagani'] = 'Previous rin lagani not cleared.'
    return errors


def save_or_update_rin_lagani(session, rin_lagani):
    """
    Updates the RinLagani if it has id or else persists new RinLagani
    :param session: current database session
    :param rin_lagani: RinLagani to be saved.
    :return: errors if any
    """
    if rin_lagani.id is None:
        # while persisting new rin lagani latest is the last transaction
        latest_tx = get_latest_transaction(session,
                                           rin_lagani.member_id)
        latest_rin_lagani = get_latest_rin_lagani(session, rin_lagani.member_id)
    else:
        # while updating existing rin lagani latest is the 2nd last transaction
        latest_tx = get_second_last_transaction(session,
                                                rin_lagani.member_id)
        latest_rin_lagani = get_second_last_rin_lagani(session,
                                                       rin_lagani.member_id)
    # validate rin lagani
    errors = validate_rin_lagani(session, rin_lagani, latest_tx,
                                 latest_rin_lagani)
    if len(errors) > 0:
        return errors

    # calculate kista per months
    settings = session.query(Settings).first()
    rin_lagani.kista_per_month = rin_lagani.amount / settings.total_kista_months
    # save or update rin lagani
    session.merge(rin_lagani)


def get_rin_lagani_by_id(session, id):
    """
    Get member with matching id from the database
    :param session: current database session
    :param id: RinLagani id
    :return: RinLagani with matching id
    """
    return session.query(RinLagani).filter(RinLagani.id == id).first()


def delete_rin_lagani_by_id(session, id):
    """
    Delete member with matching id from the database
    :param session: current database session
    :param id: id of the member to be deleted
    """
    rin_lagani = get_rin_lagani_by_id(session, id)
    if rin_lagani is None:
        return 'No RinLagani with given id found.'
    # can only delete latest transaction for given member
    latest_tx = get_latest_transaction(session, rin_lagani.member_id)
    if type(latest_tx) != type(rin_lagani) or latest_tx.id != rin_lagani.id:
        return 'Can only delete latest transaction'
    session.delete(rin_lagani)


def get_rin_laganis_by_member_id(session, member_id):
    """
    Get a list of rin lagani done by member
    :param session: current database session
    :param member_id: member id
    :return: list of rin laganis that match member id supplied
    """
    return session.query(RinLagani).filter(
        RinLagani.member_id == member_id).all()


@dataclass
class SawaAsuliDto:
    id: int
    date: str
    amount: Decimal
    byaj: Decimal
    harjana: Decimal
    bachat: Decimal
    remarks: str
    rin_lagani_id: int
    member_id: int

    @classmethod
    def default(cls):
        zero = Decimal(0)
        return SawaAsuliDto(None, '', zero, zero, zero, zero, '', None,
                            None)


def to_sawa_asuli_dto(sawa_asuli):
    """
    Convert SawaAsuli to SawaAsuliDto
    :param sawa_asuli: SawaAsuli to be converted
    :return: SawaAsuliDto converted from provided SawaAsuli
    """
    return SawaAsuliDto(id=sawa_asuli.id, date=sawa_asuli.date,
                        amount=sawa_asuli.amount, byaj=sawa_asuli.byaj,
                        harjana=sawa_asuli.harjana, bachat=sawa_asuli.bachat,
                        remarks=sawa_asuli.remarks,
                        rin_lagani_id=sawa_asuli.rin_lagani_id,
                        member_id=sawa_asuli.member_id)


def to_sawa_asuli(sawa_asuli_dto):
    """
    Convert SawaAsuliDto to SawaAsuli
    :param sawa_asuli_dto: SawaAsuliDto to be converted
    :return: SawaAsuli converted from SawaAsuliDto
    """
    return SawaAsuli(id=sawa_asuli_dto.id, date=sawa_asuli_dto.date,
                     amount=sawa_asuli_dto.amount, byaj=sawa_asuli_dto.byaj,
                     harjana=sawa_asuli_dto.harjana,
                     bachat=sawa_asuli_dto.bachat,
                     remarks=sawa_asuli_dto.remarks,
                     rin_lagani_id=sawa_asuli_dto.rin_lagani_id,
                     member_id=sawa_asuli_dto.member_id)


def validate_sawa_asuli(session, sawa_asuli, latest_tx):
    errors = {}
    zero = Decimal(0)
    # check if sawa asuli date is before than the latest transaction date
    latest_tx_date = str_to_date(latest_tx.date)
    sawa_asuli_date = str_to_date(sawa_asuli.date)
    if sawa_asuli_date <= latest_tx_date:
        errors['date'] = 'Date cannot be in the past than latest transaction.'
        return errors
    # check if latest rin lagani is cleared
    rin_lagani = get_latest_rin_lagani(session, sawa_asuli.member_id)
    banki_sawa = zero
    if not rin_lagani is None:
        banki_sawa = calculate_banki_sawa(rin_lagani)
        # while editing latest sawa asuli do not count its sawa asuli when calulating banki sawa
        if not sawa_asuli.id is None:
            # get the sawa asuli being edited from the database
            asuli = get_sawa_asuli_by_id(session, sawa_asuli.id)
            banki_sawa += sawa_asuli.amount
    # bachat only sawa asuli can only have rin bachat
    if rin_lagani is None or banki_sawa == zero:
        if (sawa_asuli.amount > zero or sawa_asuli.byaj > zero
                or sawa_asuli.harjana > zero):
            errors['amount'] = 'Invalid amounts for bachat only sawa asuli'
    return errors


def save_or_update_sawa_asuli(session, sawa_asuli):
    """
    Persists SawaAsuli
    :param session: current database session
    :param sawa_asuli: sawa asuli to be saved
    :return: err if any
    """
    if sawa_asuli.id is None:
        latest_tx = get_latest_transaction(session,
                                           sawa_asuli.member_id)
    else:
        latest_tx = get_second_last_transaction(session,
                                                sawa_asuli.member_id)
    # simple validations
    errors = {}
    # check validity of amounts
    zero = Decimal(0)
    if (sawa_asuli.amount < zero or sawa_asuli.byaj < zero
            or sawa_asuli.harjana < zero or sawa_asuli.bachat < zero):
        errors['amount'] = 'Invalid amount, byaj, harjana or bachat'
    # check validity of date
    if str_to_date(sawa_asuli.date) is None:
        errors['date'] = 'Invalid date.'
        return errors
    # check if member exists with given member_id
    if get_member_by_id(session, sawa_asuli.member_id) is None:
        errors['member_id'] = ['Invalid member.']
        return errors
    # if there are no latest transactions allow saving sawa asuli
    if latest_tx is None:
        return errors
    # further validate sawa asuli
    errors = validate_sawa_asuli(session, sawa_asuli, latest_tx)
    if len(errors) > 0:
        return errors

    # save or update sawa asuli
    session.merge(sawa_asuli)


def get_sawa_asuli_by_id(session, id):
    """
    Get SawaAsuli matching the given id from the database.
    :param session: current database session
    :param id: SawaAsuli id
    :return: SawaAsuli matching the id
    """
    return session.query(SawaAsuli).filter(SawaAsuli.id == id).first()


def delete_sawa_asuli_by_id(session, id):
    """
    Deletes SawaAsuli with matching id from the database.
    :param session: current database session
    :param id: SawaAsuli id
    """
    sawa_asuli = get_sawa_asuli_by_id(session, id)
    if sawa_asuli is None:
        return 'No SawaAsuli with given id found.'
    # can only delete latest transaction for given member
    latest_tx = get_latest_transaction(session, sawa_asuli.member_id)
    if type(latest_tx) != type(sawa_asuli) or latest_tx.id != sawa_asuli.id:
        return 'Can only delete latest transaction'
    session.delete(sawa_asuli)


def get_sawa_asulis_by_rin_lagani_id(session, id):
    """
    Get a list of SawaAsuli for given RinLagani id
    :param session: current database session
    :param id: RinLagani id
    :return: list of SawaAsuli
    """
    return session.query(SawaAsuli).filter(SawaAsuli.rin_lagani_id == id).all()


def get_sawa_asulis_by_member_id(session, id):
    """
    Get a list of RinLagani for given Member id
    :param session: current database session
    :param id: Member id
    :return: list of SawaAsuli
    """
    return session.query(SawaAsuli).filter(SawaAsuli.member_id == id).all()


def get_sawa_asulis_without_rin_lagani(session, id):
    """
    Get a list of SawaAsuli for given member id which does not have RinLagani
    :param session: current database session
    :param id: Member id
    :return: list of SawaAsuli
    """
    return session.query(SawaAsuli).filter(
        and_(SawaAsuli.member_id == id, SawaAsuli.rin_lagani_id == None))


def get_latest_transaction(session, member_id):
    """
    Find the latest RinLagani or SawaAsuli for given Member id
    :param session: Current database session
    :param member_id: Member id
    :return: latest RinLagani or SawaAsuli
    """
    rin_laganis = get_rin_laganis_by_member_id(session, member_id)
    sawa_asulis = get_sawa_asulis_by_member_id(session, member_id)
    rin_laganis.extend(sawa_asulis)
    if len(rin_laganis) == 0:
        return None
    return max(rin_laganis, key=lambda tx: str_to_date(tx.date))


def get_second_last_transaction(session, member_id):
    """
    Find second last RinLagani or SawaAsuli for given Member id
    :param session: current database session
    :param member_id: Member id
    :return: second last RinLagani or SawaAsuli
    """
    rin_laganis = get_rin_laganis_by_member_id(session, member_id)
    sawa_asulis = get_sawa_asulis_by_member_id(session, member_id)
    rin_laganis.extend(sawa_asulis)
    if len(rin_laganis) < 2:
        return None
    else:
        rin_laganis.sort(key=lambda tx: str_to_date(tx.date))
        return rin_laganis[-2]


def get_latest_rin_lagani(session, member_id):
    """
    Find the latest RinLagani for the given Member id
    :param session: current database session
    :param member_id: Member id
    :return: latest RinLagani
    """
    rin_laganis = get_rin_laganis_by_member_id(session, member_id)
    if len(rin_laganis) == 0:
        return None
    return max(rin_laganis, key=lambda lagani: str_to_date(lagani.date))


def get_second_last_rin_lagani(session, member_id):
    """
    Find the 2nd last RinLagani for given member
    :param session: current database session
    :param member_id: Member id
    :return: RinLagani previous to latest RinLagani
    """
    rin_laganis = get_rin_laganis_by_member_id(session, member_id)
    if len(rin_laganis) < 2:
        return None
    else:
        rin_laganis.sort(key=lambda r: str_to_date(r.date))
        return rin_laganis[-2]


def get_rin_laganis_in_month(session, member_id, date):
    """
    Find RinLaganis in month of given date for given member
    :param session: current database session
    :param member_id: Member id
    :param date: nepali_datetime.date object
    :return: RinLagani list
    """
    rin_laganis = get_rin_laganis_by_member_id(session, member_id)
    filtered_rin_laganis = []
    for rin_lagani in rin_laganis:
        date1 = str_to_date(rin_lagani.date)
        if date.year == date1.year and date.month == date1.month:
            filtered_rin_laganis.append(filtered_rin_laganis)
    return filtered_rin_laganis


def get_sawa_asulis_in_month(session, member_id, date):
    """
    Find SawaAsulis in month of given date for given member
    :param session: current database session
    :param member_id: Member id
    :param date: nepali_datetime.date object
    :return: SawaAsuli list
    """
    sawa_asulis = get_sawa_asulis_by_member_id(session, member_id)
    filtered_sawa_asulis = []
    for sawa_asuli in sawa_asulis:
        date1 = str_to_date(sawa_asuli.date)
        if date.year == date1.year and date.month == date1.month:
            filtered_sawa_asulis.append(sawa_asuli)
    return filtered_sawa_asulis


def calculate_banki_sawa(rin_lagani):
    """
    Calculate banki sawa for a RinLagani. If rin_lagani is None return zero.
    :param rin_lagani: RinLagani
    :return: banki sawa for the given RinLagani
    """
    if rin_lagani is None:
        return Decimal(0)
    banki_sawa = rin_lagani.amount
    for sawa_asuli in rin_lagani.sawa_asulis:
        banki_sawa -= sawa_asuli.amount
    return banki_sawa


@dataclass
class BankTransactionDto:
    id: int
    date: str
    amount: Decimal
    type: str  # 'rin_lagani' will be for RinLagani
    remarks: str

    def default(self):
        return BankTransactionDto(None, '', Decimal(0), 'DEPOSIT', '')


def rin_lagani_to_bank_transaction_dto(rin_lagani):
    """
    Converts a RinLagani to BankTransactionDto
    :param rin_lagani: RinLagani
    :return: BankTransactionDto
    """
    remarks = f'Rin lagani by {rin_lagani.member.name}'
    return BankTransactionDto(id=rin_lagani.id, date=rin_lagani.date,
                              amount=rin_lagani.amount, type='RIN_LAGANI',
                              remarks=remarks)


def to_bank_transaction_dto(tx):
    """
    Converts BankTransaction to BankTransactionDto
    :param tx: BankTransaction
    :return: BankTransactionDto
    """
    return BankTransactionDto(id=tx.id, date=tx.date, amount=tx.amount,
                              type=tx.type.name, remarks=tx.remarks)


def to_bank_transaction(tx_dto):
    """
    Convert BankTransactionDto to BankTransaction
    :param tx_dto: BankTransactionDto
    :return: BankTransaction
    """
    if tx_dto.type == BankTransactionTypes.DEBIT.name:
        tx_type = BankTransactionTypes.DEBIT
    elif tx_dto.type == BankTransactionTypes.CREDIT.name:
        tx_type = BankTransactionTypes.CREDIT
    else:
        tx_type = BankTransactionTypes.DEPOSIT

    return BankTransaction(id=tx_dto.id, date=tx_dto.date, amount=tx_dto.amount,
                           type=tx_type, remarks=tx_dto.remarks)


def save_or_update_bank_transaction(session, transaction):
    """
    Saves or updates the given bank transaction
    :param session:
    :param transaction:
    :return:
    """
    errors = {}
    if str_to_date(transaction.date) is None:
        errors['date'] = 'Invalid date'
    # check errors in amount
    if transaction.amount is None or transaction.amount <= Decimal(0):
        errors['amount'] = 'Amount cannot be zero or negetive.'
    # check if type is None
    if transaction.type is None:
        errors['type'] = 'Type cannot be None.'
    # if there are one or more errors return
    if len(errors) > 0:
        return errors
    # save or update transaction
    session.merge(transaction)


def get_bank_transaction_by_id(session, id):
    """
    Finds BankTransaction with given id
    :param session: current database session
    :param id: BankTransaction id
    :return: BankTransaction
    """
    return session.query(BankTransaction).filter(
        BankTransaction.id == id).first()


def delete_bank_transaction_by_id(session, id):
    """
    Deletes BankTransaction with given id
    :param session: current database session
    :param id: BankTransaction id
    :return: errors if any
    """
    transaction = get_bank_transaction_by_id(session, id)
    if transaction is None:
        return f'Could find bank transaction with id {id}'
    # delete transaction
    session.delete(transaction)


def get_all_bank_transactions(session):
    """
    Returns all BankTransactions
    :param session: current database session
    :return: list of BankTransaction
    """
    return session.query(BankTransaction).all()


def get_all_bank_transactions_in_month(session, date):
    """
    Find BankTransaction in month of given date
    :param session: current database session
    :param date: nepali_datetime.date object
    :return: BankTransactino list
    """
    bank_transactions = get_all_bank_transactions(session)
    filtered_transactions = []
    for bank_transaction in bank_transactions:
        date1 = str_to_date(bank_transaction.date)
        if date.year == date1.year and date.month == date1.month:
            filtered_transactions.append(filtered_transactions)
    return filtered_transactions


@dataclass
class TransactionDto:
    id: int
    date: str
    rin_lagani: Decimal
    sawa_asuli: Decimal
    byaj: Decimal
    harjana: Decimal
    bachat: Decimal
    banki_sawa: Decimal
    remarks: str
    is_rin_lagani: bool
    is_alya_rin: bool
    total: Decimal


def rin_lagani_to_transaction_dto(rin_lagani):
    """
    Convert RinLagani or RinLaganiDto to TransactionDto
    :param rin_lagani: RinLagani or RinLaganiDto
    :return: TransactionDto
    """
    zero = Decimal(0)
    return TransactionDto(id=rin_lagani.id, date=rin_lagani.date,
                          rin_lagani=rin_lagani.amount,
                          sawa_asuli=zero, byaj=zero, harjana=zero, bachat=zero,
                          banki_sawa=rin_lagani.amount,
                          remarks=rin_lagani.remarks,
                          is_rin_lagani=True,
                          is_alya_rin=rin_lagani.is_alya_rin,
                          total=rin_lagani.amount)


def sawa_asuli_to_transaction_dto(sawa_asuli):
    """
    Convert SawaAsuli or SawaAsuliDto to TransactionDto
    :param sawa_asuli: SawaAsuli or SawaAsuliDto
    :return: TransactionDto
    """
    zero = Decimal(0)
    total = (sawa_asuli.amount + sawa_asuli.byaj + sawa_asuli.harjana
             + sawa_asuli.bachat)
    return TransactionDto(id=sawa_asuli.id, date=sawa_asuli.date,
                          rin_lagani=zero,
                          sawa_asuli=sawa_asuli.amount, byaj=sawa_asuli.byaj,
                          harjana=sawa_asuli.harjana, bachat=sawa_asuli.bachat,
                          banki_sawa=zero, remarks=sawa_asuli.remarks,
                          is_rin_lagani=False, is_alya_rin=False, total=total)


def get_transactions_by_member_id(session, member_id):
    """
    Finds all the transactions for given member
    :param session: current database session
    :param member_id: Member id
    :return: list of TransactionDto for given member and total
    """
    zero = Decimal(0)
    totals = {
        'lagani_total': zero,
        'asuli_total': zero,
        'byaj_total': zero,
        'harjana_total': zero,
        'bachat_total': zero,
        'banki_sawa': zero
    }
    transactions = []
    rin_laganis = get_rin_laganis_by_member_id(session, member_id)
    for rin_lagani in rin_laganis:
        # convert to transaction dto
        transactions.append(rin_lagani_to_transaction_dto(rin_lagani))
        # get sawa asulis for this rin lagani
        sawa_asulis = get_sawa_asulis_by_rin_lagani_id(session, rin_lagani.id)
        # calculate rin lagani total
        totals['lagani_total'] += rin_lagani.amount
        # initialize banki sawa
        banki_sawa = rin_lagani.amount
        # set banki sawa to latest banki sawa
        totals['banki_sawa'] = banki_sawa
        for sawa_asuli in sawa_asulis:
            # convert to transaction dto
            sawa_asuli_dto = sawa_asuli_to_transaction_dto(sawa_asuli)
            banki_sawa -= sawa_asuli_dto.sawa_asuli
            sawa_asuli_dto.banki_sawa = banki_sawa
            transactions.append(sawa_asuli_dto)
            # calculate totals
            totals['asuli_total'] += sawa_asuli.amount
            totals['byaj_total'] += sawa_asuli.byaj
            totals['harjana_total'] += sawa_asuli.harjana
            totals['bachat_total'] += sawa_asuli.bachat
            # set banki sawa to latest banki sawa
            totals['banki_sawa'] = banki_sawa
    # remainining sawa asulis which only have bachat
    for sawa_asuli in get_sawa_asulis_without_rin_lagani(session, member_id):
        transactions.append(sawa_asuli_to_transaction_dto(sawa_asuli))
    # sort transactions according to date
    transactions.sort(key=lambda tx: str_to_date(tx.date))
    return transactions, totals


def get_bank_transactions_and_rin_laganis(session):
    """
    Gets a list of all BankTransactionDto including RinLagani
    :param session: current database session
    :return: list of BankTransactionDto sorted by date and total
    """
    totals = {
        'debit_total': Decimal(0),
        'credit_total': Decimal(0)
    }
    transactions = []
    # get all BankTransaction and map them to BankTransactionDto
    bank_txns = get_all_bank_transactions(session)
    for tx in bank_txns:
        transactions.append(to_bank_transaction_dto(tx))
        if tx.type == BankTransactionTypes.DEBIT:
            totals['debit_total'] += tx.amount
        else:
            totals['credit_total'] += tx.amount

    # get all RinLagni and map them to BankTransactionDto
    rin_laganis = session.query(RinLagani).all()
    for rin_lagani in rin_laganis:
        transactions.append(rin_lagani_to_bank_transaction_dto(rin_lagani))
        totals['debit_total'] += rin_lagani.amount
    # sort by date
    transactions.sort(key=lambda tx: str_to_date(tx.date))
    # return transactions
    return transactions, totals


@dataclass
class MemberTransactionDto:
    """TransactionDto with Member name"""
    member_name: str
    transaction_dto: TransactionDto


def get_date_range_summary(session, start_date, end_date):
    """
    Find all the transactions between given date.
    :param session: current database session
    :start_date: start date inclusive
    :end date: end date inclusive
    :return: MemberTransactionDtos for rin laganis, MemberTransactionDtos for sawa asulis,  BankTransactionDtos for deposits, totals
    """
    zero = Decimal(0)
    totals = {
        'rin_lagani': zero,
        'sawa_asuli': zero,
        'byaj': zero,
        'harjana': zero,
        'bachat': zero,
        'grand_total': zero,
        'deposit': zero
    }
    rin_laganis = []
    # get all rin laganis in given date range
    for rin_lagani in session.query(RinLagani).all():
        rin_lagani_date = str_to_date(rin_lagani.date)
        if rin_lagani_date >= start_date and rin_lagani_date <= end_date:
            dto = rin_lagani_to_transaction_dto(rin_lagani)
            # create MemberTransactionDto from TransactionDto
            rin_laganis.append(
                MemberTransactionDto(rin_lagani.member.name, dto))
            # update lagani total
            totals['rin_lagani'] += rin_lagani.amount
    # sort rin laganis
    rin_laganis.sort(key=lambda tx: str_to_date(tx.transaction_dto.date))
    # get all sawa sulis in given date range
    sawa_asulis = []
    for sawa_asuli in session.query(SawaAsuli).all():
        sawa_asuli_date = str_to_date(sawa_asuli.date)
        if sawa_asuli_date >= start_date and sawa_asuli_date <= end_date:
            dto = sawa_asuli_to_transaction_dto(sawa_asuli)
            # create MemberTransactionDto from TransactionDto
            sawa_asulis.append(
                MemberTransactionDto(sawa_asuli.member.name, dto))
            # update totals
            totals['sawa_asuli'] += sawa_asuli.amount
            totals['byaj'] += sawa_asuli.amount
            totals['harjana'] += sawa_asuli.amount
            totals['bachat'] += sawa_asuli.amount
            totals['grand_total'] += dto.total
    # sort sawa asuli
    sawa_asulis.sort(key=lambda tx: str_to_date(tx.transaction_dto.date))
    # get all bank transactions in given date range
    bank_transactions = []
    for bank_tx in session.query(BankTransaction).all():
        # ignore if not a deposit
        if bank_tx.type != BankTransactionTypes.DEPOSIT:
            continue
        bank_tx_date = str_to_date(bank_tx.date)
        if bank_tx_date >= start_date and bank_tx_date <= end_date:
            bank_transactions.append(to_bank_transaction_dto(bank_tx))
            totals['deposit'] += bank_tx.amount
    bank_transactions.sort(key=lambda tx: str_to_date(tx.date))

    return rin_laganis, sawa_asulis, bank_transactions, totals


def get_monthly_transactions(session, date):
    """
    Get date range summary for given date's month
    :param session: current database session
    :param date: nepali_datetime.date object
    :return: MemberTransactionDtos for rin laganis, MemberTransactionDtos for sawa asulis,  BankTransactionDtos for deposits, totals
    """
    start_date = get_month_start(date)
    end_date = get_month_end(date)
    return get_date_range_summary(session, start_date, end_date)


@dataclass
class MemberSummaryDto:
    name: str
    alya_rin: Decimal
    total_rin_lagani: Decimal
    total_sawa_asuli: Decimal
    total_byaj: Decimal
    total_harjana: Decimal
    total_bachat: Decimal
    banki_sawa: Decimal

    @classmethod
    def default(cls):
        zero = Decimal(0)
        return MemberSummaryDto('', zero, zero, zero, zero, zero, zero, zero)


def get_member_wise_summary(session):
    """
    Get MemberWiseSummaryDto for all members along with total
    :param session: current database session
    :return: MemberSummaryDto list and totals
    """
    zero = Decimal(0)
    totals = {
        'alya_rin': zero,
        'total_rin_lagani': zero,
        'total_sawa_asuli': zero,
        'total_byaj': zero,
        'total_harjana': zero,
        'total_bachat': zero,
        'banki_sawa': zero
    }
    member_summaries = []
    # for every member
    for member in session.query(Member).all():
        dto = MemberSummaryDto.default()
        dto.name = member.name
        # for every rin lagani for member
        for lagani in member.rin_laganis:
            if lagani.is_alya_rin:
                dto.alya_rin += lagani.amount
            else:
                dto.total_rin_lagani += lagani.amount
            dto.banki_sawa += lagani.amount
            # for every sawa asuli for the rin lagani
            for asuli in lagani.sawa_asulis:
                dto.total_sawa_asuli += asuli.amount
                dto.total_byaj += asuli.byaj
                dto.total_harjana += asuli.harjana
                dto.total_bachat += asuli.bachat
                dto.banki_sawa -= asuli.amount
        # for every sawa asuli not related to rin lagani
        for asuli in get_sawa_asulis_without_rin_lagani(session, member.id):
            # it will only contain bachat
            dto.total_bachat += asuli.bachat
        # add members total to overall total
        totals['alya_rin'] += dto.alya_rin
        totals['total_rin_lagani'] += dto.total_rin_lagani
        totals['total_sawa_asuli'] += dto.total_sawa_asuli
        totals['total_byaj'] += dto.total_byaj
        totals['total_harjana'] += dto.total_harjana
        totals['total_bachat'] += dto.total_bachat
        totals['banki_sawa'] += dto.banki_sawa
        # apeend dto to member_summaries
        member_summaries.append(dto)

    return member_summaries, totals
