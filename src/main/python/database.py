import enum
from decimal import Decimal

from sqlalchemy import (
    create_engine, Column, Integer, String, Numeric, Boolean,
    Enum, CheckConstraint, ForeignKey
)
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

db_path = 'sqlite:///data.db'
# db_path = 'sqlite://'
engine = create_engine(db_path)  # create engine
Base = declarative_base()  # create declarative base class
Session = sessionmaker(bind=engine)  # create session maker


class Member(Base):
    __tablename__ = 'members'

    id = Column(Integer, primary_key=True)
    account_no = Column(Integer, CheckConstraint('account_no > 0'),
                        nullable=False, unique=True)
    name = Column(String, CheckConstraint('name!=""'), nullable=False)

    rin_laganis = relationship('RinLagani', cascade='all, delete-orphan',
                               back_populates='member')

    sawa_asulis = relationship('SawaAsuli', cascade='all, delete-orphan',
                               back_populates='member')

    def __repr__(self):
        if self.id is None or self.account_no is None or self.name is None:
            return 'Member<>'
        return '<Member(id=%d, account_no=%d, name=%s)>' % (
            self.id, self.account_no, self.name)


class RinLagani(Base):
    __tablename__ = 'rinlaganis'

    id = Column(Integer, primary_key=True)
    date = Column(String(10), nullable=False)
    amount = Column(Numeric(13, 2), nullable=False, default=Decimal(0))
    is_alya_rin = Column(Boolean, default=False)
    kista_per_month = Column(Numeric(13, 2), nullable=False)
    remarks = Column(String)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=False)

    member = relationship('Member', back_populates='rin_laganis')
    sawa_asulis = relationship('SawaAsuli', back_populates='rin_lagani')

    def __repr__(self):
        if self.id is None or self.date is None or self.amount is None:
            return 'RinLagani<>'
        return 'RinLagani<(id=%s date=%s amount=%f)>' % (
            self.id, self.date, self.amount)


class SawaAsuli(Base):
    __tablename__ = 'sawaasulis'

    id = Column(Integer, primary_key=True)
    date = Column(String(10), nullable=False)
    amount = Column(Numeric(13, 2), nullable=False, default=Decimal(0))
    byaj = Column(Numeric(13, 2), nullable=False, default=Decimal(0))
    harjana = Column(Numeric(13, 2), nullable=False, default=Decimal(0))
    bachat = Column(Numeric(13, 2), nullable=False, default=Decimal(0))
    remarks = Column(String())
    rin_lagani_id = Column(Integer, ForeignKey('rinlaganis.id'))
    member_id = Column(Integer, ForeignKey('members.id'))

    member = relationship('Member', back_populates='sawa_asulis')
    rin_lagani = relationship('RinLagani', back_populates='sawa_asulis')

    def __repr__(self):
        if not (self.id is None or self.date is None or self.amount is None
                or self.harjana is None or self.bachat is None):
            return 'SawaAsuli<()>'
        return ('SawaAsuli<(id=%d date=%s amount=%f harjana=%f bachat=%f'
                'kista=%f)>') % (self.id, self.date, self.amount, self.amount,
                                 self.harjana, self.bachat)


class BankTransactionTypes(enum.Enum):
    """Enum representing bank transaction types(DEBIT, CREDIT, DEPOSIT)"""
    DEBIT = 0
    CREDIT = 1
    DEPOSIT = 2


class BankTransaction(Base):
    __tablename__ = 'banktransactions'

    id = Column(Integer, primary_key=True)
    date = Column(String(10), nullable=False)
    amount = Column(Numeric(13, 2), nullable=False, default=Decimal(0))
    type = Column(Enum(BankTransactionTypes), nullable=False)
    remarks = Column(String())

    def __repr__(self):
        if self.date is None or self.amount is None or self.type is None:
            return 'BankTransaction<()>'
        return ('BankTransaction<(date=%s, amount=%f, type=%s)>') % (
        self.date, self.amount, self.type)


class Settings(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    total_kista_months = Column(Integer, nullable=False)
    account_no = Column(String, nullable=False)
