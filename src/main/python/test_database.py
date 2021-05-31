import unittest
from decimal import Decimal

from sqlalchemy import exc

from database import engine, Base, Session, Member, RinLagani, SawaAsuli


class TestDatabase(unittest.TestCase):
    def setUp(self):
        # print('Running setup')
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        member1 = Member(account_no=1, name='Gaurab')
        member2 = Member(account_no=2, name='Sameer')

        rin_lagani1 = RinLagani(date='01/01/2077', amount=Decimal(1000))
        rin_lagani2 = RinLagani(date='01/02/2077', amount=Decimal(2000))

        sawa_asuli1 = SawaAsuli(date='02/01/2077', amount=Decimal(1000),
                                byaj=Decimal(100))
        sawa_asuli2 = SawaAsuli(date='05/02/2077', amount=Decimal(1000),
                                byaj=Decimal(100))
        sawa_asuli3 = SawaAsuli(date='10/02/2077', amount=Decimal(1000),
                                byaj=Decimal(100))

        rin_lagani1.sawa_asulis = [sawa_asuli1, sawa_asuli2]
        rin_lagani2.sawa_asulis = [sawa_asuli3]

        member1.rin_laganis = [rin_lagani1, rin_lagani2]

        with Session.begin() as session:
            session.add(member1)
            session.add(member2)

    def tearDown(self):
        # print('Running teardown')
        Base.metadata.drop_all(engine)

    def test_unique_account_no(self):
        with Session() as session:
            member2 = Member(account_no=2, name='Duplicate')
            session.add(member2)
            self.assertRaises(exc.IntegrityError, session.commit)

    def test_member_rin_lagani_relationship(self):
        with Session.begin() as session:
            member1 = session.query(Member).filter(Member.name == 'Gaurab') \
                .first()
            self.assertIsNotNone(member1)
            self.assertEqual(len(member1.transactions), 2)
            id = member1.id
            session.delete(member1)

        with Session.begin() as session:
            no_of_rin_laganis = session.query(RinLagani).filter(
                RinLagani.member_id == id).count()
            self.assertEqual(no_of_rin_laganis, 0)

    def test_member_sawa_asuli_relationship(self):
        with Session.begin() as session:
            member1 = session.query(Member).filter(Member.name == 'Gaurab') \
                .first()
            self.assertIsNotNone(member1)
            id = member1.id
            session.delete(member1)

        with Session.begin() as session:
            no_of_sawa_asulis = session.query(SawaAsuli).filter(
                SawaAsuli.member_id == id).count()
            self.assertEqual(no_of_sawa_asulis, 0)

    def test_rin_lagani_sawa_asuli_relationship(self):
        with Session.begin() as session:
            member1 = session.query(Member).filter(Member.name == 'Gaurab') \
                .first()
            id = member1.id
            rin_lagani = session.query(RinLagani).filter(
                RinLagani.member_id == member1.id).first()
            self.assertEqual(len(rin_lagani.transactions), 2)
            session.delete(rin_lagani)

        with Session.begin() as session:
            no_of_sawa_asulis = session.query(SawaAsuli).filter(
                SawaAsuli.member_id == id).count()
            self.assertEqual(no_of_sawa_asulis, 0)
