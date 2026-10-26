import unittest
import json
import datetime
from app import app
from database import init_db
from seed import seed_data

class SpendWiseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-key-spendwise'
        self.client = app.test_client()
        init_db()
        seed_data()

    def test_01_login_logout(self):
        """Test login with seeded credentials and logout"""
        # Bad login
        res = self.client.post('/login', data={'email': 'test@spendwise.com', 'password': 'wrongpassword'}, follow_redirects=True)
        self.assertIn(b'Invalid email or password', res.data)

        # Good login
        res = self.client.post('/login', data={'email': 'test@spendwise.com', 'password': 'test123'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Financial Dashboard', res.data)
        self.assertIn(b'Alex Morgan', res.data)

        # Logout
        res = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'You have been logged out', res.data)

    def test_02_dashboard_and_apis(self):
        """Test dashboard page and JSON API routes"""
        # Log in
        self.client.post('/login', data={'email': 'test@spendwise.com', 'password': 'test123'}, follow_redirects=True)

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

    def test_03_transactions_page_and_filtering(self):
        """Test transaction listing and filter parameters"""
        self.client.post('/login', data={'email': 'test@spendwise.com', 'password': 'test123'}, follow_redirects=True)

        res = self.client.get('/transactions')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Transactions', res.data)

        # Filter by type Expense
        res = self.client.get('/transactions?type=Expense')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'amount-expense', res.data)

        # Filter by category Food
        res = self.client.get('/transactions?category=Food')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Food', res.data)

    def test_04_add_edit_delete_transaction(self):
        """Test full CRUD lifecycle for transaction"""
        self.client.post('/login', data={'email': 'test@spendwise.com', 'password': 'test123'}, follow_redirects=True)

        today_str = datetime.date.today().strftime('%Y-%m-%d')

        # 1. Add valid transaction
        post_data = {
            'type': 'Expense',
            'amount': 2499.50,
            'category': 'Entertainment',
            'date': today_str,
            'note': 'IMAX Movie & Popcorn'
        }
        res = self.client.post('/api/transactions', json=post_data)
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.data)
        self.assertTrue(res_json['success'])
        tx_id = res_json['transaction']['id']

        # 2. Get transaction
        get_res = self.client.get(f'/api/transactions/{tx_id}')
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(json.loads(get_res.data)['transaction']['note'], 'IMAX Movie & Popcorn')

        # 3. Update transaction
        update_data = {
            'type': 'Expense',
            'amount': 2999.00,
            'category': 'Entertainment',
            'date': today_str,
            'note': 'IMAX Movie with snacks and merchandise'
        }
        update_res = self.client.post(f'/api/transactions/{tx_id}', json=update_data)
        self.assertEqual(update_res.status_code, 200)
        self.assertTrue(json.loads(update_res.data)['success'])

        # Verify update
        get_res2 = self.client.get(f'/api/transactions/{tx_id}')
        self.assertEqual(json.loads(get_res2.data)['transaction']['amount'], 2999.00)

        # 4. Delete transaction
        del_res = self.client.post(f'/api/transactions/{tx_id}/delete')
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(json.loads(del_res.data)['success'])

        # Verify deleted
        get_res3 = self.client.get(f'/api/transactions/{tx_id}')
        self.assertEqual(get_res3.status_code, 404)

    def test_05_validation_errors(self):
        """Test backend validation checks"""
        self.client.post('/login', data={'email': 'test@spendwise.com', 'password': 'test123'}, follow_redirects=True)

        # Negative amount
        res = self.client.post('/api/transactions', json={
            'type': 'Expense',
            'amount': -100,
            'category': 'Food',
            'date': '2026-10-26'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('positive number', json.loads(res.data)['error'])

        # Invalid category for Income
        res2 = self.client.post('/api/transactions', json={
            'type': 'Income',
            'amount': 5000,
            'category': 'Rent', # Rent is not an income category
            'date': '2026-10-26'
        })
        self.assertEqual(res2.status_code, 400)

    def test_06_budgets_and_history(self):
        """Test budgets and history pages"""
        self.client.post('/login', data={'email': 'test@spendwise.com', 'password': 'test123'}, follow_redirects=True)

        # Budgets page
        res = self.client.get('/budgets')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Monthly Budgets', res.data)
        self.assertIn(b'Food', res.data)
        self.assertIn(b'progress-orange', res.data) # Below 85%
        self.assertIn(b'progress-red', res.data)    # Above 85%

        # Update budget
        b_res = self.client.post('/api/budgets', json={
            'category': 'Food',
            'limit': 15000.0,
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
