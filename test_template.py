from base_test import BaseTest
from template import Template, TemplateVariable, ConvoTemplate
from unittest.mock import Mock


class TemplateTest(BaseTest):
    def check_variables(self, a,b,outcome):
        self.assertEqual([TemplateVariable(*outcome)], Template(a).find_variables(b))

    def test_variables(self):
        self.check_variables('abcd', 'axcd', (1,1,1,1))
        self.check_variables('abcd', 'axycd', (1,1,1,2))
        self.check_variables('abcd', 'ad', (1,2,0,2))
        self.assertEqual([], Template('abcd').find_variables('abcd'))

    def test_similarity(self):
        # without variables
        # replace
        self.assertBetween(0.5, 0.9, Template('abcd',[]).similarity('axcd'))
        # insert
        self.assertBetween(0.5, 0.9, Template('abcd',[]).similarity('abxcd'))
        # delete
        self.assertBetween(0.5, 0.9, Template('abcd',[]).similarity('acd'))
        # no change
        self.assertEqual(1, Template('abcd',[]).similarity('abcd'))

        # with 1 variable
        # replace
        self.assertEqual(1, Template('abcd',[TemplateVariable(1,1,1,1)]).similarity('axcd'))
        # insert
        self.assertBetween(0.5, 0.9, Template('abcd',[TemplateVariable(1,1,1,1)]).similarity('axycd'))
        self.assertEqual(1, Template('abcd',[TemplateVariable(1,1,1,2)]).similarity('axycd'))
        # delete
        self.assertEqual(1, Template('abcd',[TemplateVariable(1,1,0,1)]).similarity('acd'))
        self.assertBetween(0.5, 0.9, Template('abcd',[TemplateVariable(1,1,1,1)]).similarity('acd'))
        # insert
        self.assertEqual(1, Template('abcd',[TemplateVariable(1,1,0,5)]).similarity('awxyzcd'))
        self.assertBetween(0.5, 0.9, Template('abcd',[TemplateVariable(1,1,0,3)]).similarity('awxyzcd'))
        # no change
        self.assertEqual(1, Template('abcd',[TemplateVariable(1,1,1,1)]).similarity('abcd'))

    def test_show_template(self):
        t = Template(b'abcdefghijklmnopqrstuvwxyz',[TemplateVariable(1,4,1,4), TemplateVariable(9,1,1,4) ])
        self.assertEqual('a\x1b[32mbcde\x1b[0mfghi\x1b[32mj\x1b[0mklmnopqrstuvwxyz', t.show())
        t = Template(b'abcdefghijklmnopqrstuvwxyz',[TemplateVariable(1,4,1,4), TemplateVariable(9,0,1,4) ])
        self.assertEqual('a\x1b[32mbcde\x1b[0mfghi\x1b[31m*\x1b[0mjklmnopqrstuvwxyz', t.show())

    def check_update(self, a):
        t = Template('abcdefghijklmnopqrstuvwxyz',[TemplateVariable(1,4,1,4), TemplateVariable(9,1,1,4) ])
        self.assertLess(t.similarity(a), 1)
        t.update(a)
        self.assertEqual(1, t.similarity(a))

    def test_update(self):
        self.check_update('')
        self.check_update('xyzabcdefghijklmnopqrstuvwxyz')
        self.check_update('xyzabcdefghijklmnopqrstuvwxyzxyz')
        self.check_update('defghijklmnopqrstuvw')
        self.check_update('abcdefghixyzxyklmnopqrstuvwxyz')

    def mock_var(self, pos=0, len=0, fits=True):
        mock_var = Mock()
        mock_var.fits.return_value = fits
        mock_var.pos= pos
        mock_var.len = len
        mock_var.__lt__ = lambda x,y: True
        return mock_var

    def test_var_fit(self):
        self.assertTrue(Template("abc", [self.mock_var(fits=True)]).fit_variable('good'))
        self.assertTrue(Template("abc", [self.mock_var(fits=False), self.mock_var(fits=True)]).fit_variable('good'))
        self.assertFalse(Template("abc", [self.mock_var(fits=False)]).fit_variable('bad'))

    def check_consolidate(self, invars, checkvars):
        invars = [TemplateVariable(*v) for v in invars]
        checkvars = [TemplateVariable(*v) for v in checkvars]
        t = Template("abcdefghijklmnopqrstuvwxyz", invars)
        self.assertEqual(checkvars, t.variables)

    def test_consolidate(self):
        # variable inclusion
        self.check_consolidate([(1, 5, 5, 5), (2, 4, 4, 4)], [(1, 5, 5, 5)])
        # variable with shorter min_len
        self.check_consolidate([(1, 5, 5, 5), (2, 4, 1, 4)], [(1, 5, 2, 5)])
        # variable with longer max_len
        self.check_consolidate([(1, 5, 5, 5), (2, 4, 4, 5)], [(1, 5, 5, 6)])
        # non contiguous variable
        self.check_consolidate([(1, 5, 5, 5), (7, 1, 1, 1)], [(1, 5, 5, 5), (7, 1, 1, 1)])


class ConvoTemplateTest(BaseTest):
    def check_similarity(self, sent, recv, result):
        sent_mock = Mock()
        sent_mock.similarity.return_value = sent
        recv_mock = Mock()
        recv_mock.similarity.return_value = recv
        c = ConvoTemplate("","")
        c.recv = recv_mock
        c.sent = sent_mock
        self.assertEqual(result, c.similarity('a', 'b'))
        sent_mock.similarity.assert_called_once_with('a')
        recv_mock.similarity.assert_called_once_with('b')

    def test_similarity(self):
        self.check_similarity(2, 0.5, 1.25)
        self.check_similarity(2, 0, 1)
        self.check_similarity(0, 2, 1)
        self.check_similarity(0, 0, 0)

    def test_update(self):
        sent_mock = Mock()
        recv_mock = Mock()
        c = ConvoTemplate("", "")
        c.recv = recv_mock
        c.sent = sent_mock
        c.update('a', 'b')
        sent_mock.update.assert_called_once_with('a')
        recv_mock.update.assert_called_once_with('b')