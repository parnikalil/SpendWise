import unittest
import json
import datetime
from app import app
from database import init_db
from seed import seed_data

class SpendWiseStudentTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-key-spendwise-student'
        self.client = app.test_client()
        init_db()
        seed_data()

    def test_01_login_logout(self):
        """Test login with Parnika Lilani credentials and logout"""
        # Bad login
        res = self.client.post('/login', data={'email': 'parnika@spendwise.com', 'password': 'wrongpassword'}, follow_redirects=True)
        self.assertIn(b'Invalid email or password', res.data)

        # Good login with Parnika's account
        res = self.client.post('/login', data={'email': 'parnika@spendwise.com', 'password': 'test123'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Campus & Semester Dashboard', res.data)
        self.assertIn(b'Parnika Lilani', res.data)

        # Logout
        res = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'You have been logged out', res.data)

    def test_02_dashboard_and_apis(self):
        """Test dashboard page and student JSON API routes"""
        # Log in
        self.client.post('/login', data={'email': 'parnika@spendwise.com', 'password': 'test123'}, follow_redirects=True)

        # Dashboard page
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Total Income', res.data)
        self.assertIn(b'Total Expense', res.data)
        self.assertIn(b'Recent Transactions', res.data)

        # /api/dashboard
        api_res = self.client.get('/api/dashboard')
        self.assertEqual(api_res.status_code, 200)
        dash_data = json.loads(api_res.data)
        self.assertTrue(dash_data['success'])
        self.assertIn('summary', dash_data)
        self.assertGreater(dash_data['summary']['income'], 0)
        self.assertGreater(dash_data['summary']['expense'], 0)
        self.assertLessEqual(len(dash_data['recent_transactions']), 5)

        # /api/charts
        charts_res = self.client.get('/api/charts')
        self.assertEqual(charts_res.status_code, 200)
        charts_data = json.loads(charts_res.data)
        self.assertTrue(charts_data['success'])
        self.assertIn('expense_chart', charts_data)
        self.assertIn('history_chart', charts_data)
        self.assertGreater(len(charts_data['expense_chart']['labels']), 0)
        self.assertEqual(len(charts_data['history_chart']['labels']), 6)
        self.assertEqual(len(charts_data['history_chart']['income']), 6)
        self.assertEqual(len(charts_data['history_chart']['expense']), 6)

    def test_03_transactions_page_and_student_filters(self):
        """Test student transaction listing and filtering (Hostel, Fuel, Stationery, Recharge)"""
        self.client.post('/login', data={'email': 'parnika@spendwise.com', 'password': 'test123'}, follow_redirects=True)

        res = self.client.get('/transactions')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Transactions', res.data)

        # Filter by student expense category 'Stationery'
        res = self.client.get('/transactions?category=Stationery')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Stationery', res.data)

        # Filter by student expense category 'Fuel'
        res = self.client.get('/transactions?category=Fuel')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Fuel', res.data)

        # Filter by student expense category 'Hostel Fees'
        res = self.client.get('/transactions?category=Hostel Fees')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Hostel Fees', res.data)

    def test_04_add_edit_delete_student_transaction(self):
        """Test full CRUD lifecycle for student transaction"""
        self.client.post('/login', data={'email': 'parnika@spendwise.com', 'password': 'test123'}, follow_redirects=True)

        today_str = datetime.date.today().strftime('%Y-%m-%d')

        # 1. Add valid transaction for engineering graphics drawing kit
        post_data = {
            'type': 'Expense',
            'amount': 850.0,
            'category': 'Stationery',
            'date': today_str,
            'note': 'Engineering graphics sheet holder & drafting pens'
        }
        res = self.client.post('/api/transactions', json=post_data)
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.data)
        self.assertTrue(res_json['success'])
        tx_id = res_json['transaction']['id']

        # 2. Get transaction
        get_res = self.client.get(f'/api/transactions/{tx_id}')
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(json.loads(get_res.data)['transaction']['note'], 'Engineering graphics sheet holder & drafting pens')

        # 3. Update transaction
        update_data = {
            'type': 'Expense',
            'amount': 950.0,
            'category': 'Stationery',
            'date': today_str,
            'note': 'Engineering graphics sheets & mini drafter'
        }
        update_res = self.client.post(f'/api/transactions/{tx_id}', json=update_data)
        self.assertEqual(update_res.status_code, 200)
        self.assertTrue(json.loads(update_res.data)['success'])

        # Verify update
        get_res2 = self.client.get(f'/api/transactions/{tx_id}')
        self.assertEqual(json.loads(get_res2.data)['transaction']['amount'], 950.0)

        # 4. Delete transaction
        del_res = self.client.post(f'/api/transactions/{tx_id}/delete')
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(json.loads(del_res.data)['success'])

        # Verify deleted
        get_res3 = self.client.get(f'/api/transactions/{tx_id}')
        self.assertEqual(get_res3.status_code, 404)

    def test_05_validation_errors(self):
        """Test backend validation checks for student data"""
        self.client.post('/login', data={'email': 'parnika@spendwise.com', 'password': 'test123'}, follow_redirects=True)

        # Negative amount
        res = self.client.post('/api/transactions', json={
            'type': 'Expense',
            'amount': -50,
            'category': 'Food',
            'date': '2026-10-26'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('positive number', json.loads(res.data)['error'])

        # Invalid category for Income
        res2 = self.client.post('/api/transactions', json={
            'type': 'Income',
            'amount': 2000,
            'category': 'Hostel Fees', # Hostel Fees is an expense, not income
            'date': '2026-10-26'
        })
        self.assertEqual(res2.status_code, 400)

    def test_06_budgets_and_history(self):
        """Test student budgets and 6-month surplus/deficit history"""
        self.client.post('/login', data={'email': 'parnika@spendwise.com', 'password': 'test123'}, follow_redirects=True)

        # Budgets page
        res = self.client.get('/budgets')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Semester Category Budgets', res.data)
        self.assertIn(b'Stationery', res.data)
        self.assertIn(b'Hostel Fees', res.data)
        self.assertIn(b'progress-orange', res.data) # Below 85%
        self.assertIn(b'progress-red', res.data)    # Above 85% (Stationery 94.7%, Phone Recharge 89.9%)

        # Update budget
        b_res = self.client.post('/api/budgets', json={
            'category': 'Stationery',
            'limit': 2000.0,
            'month': datetime.date.today().month,
            'year': datetime.date.today().year
        })
        self.assertEqual(b_res.status_code, 200)
        self.assertTrue(json.loads(b_res.data)['success'])

        # History page
        h_res = self.client.get('/history')
        self.assertEqual(h_res.status_code, 200)
        self.assertIn(b'Financial History', h_res.data)
        self.assertIn(b'Surplus', h_res.data) # Positive savings (Green)
        self.assertIn(b'Deficit', h_res.data) # Negative savings (Red)

if __name__ == '__main__':
    unittest.main()
