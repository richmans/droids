from base_test import BaseTest
from template import Template, TemplateVariable, ConvoTemplate
from unittest.mock import Mock
from difflib import SequenceMatcher
from baseline import Baseline
from util import scrubbed_equals


class TemplateTest(BaseTest):
    def setUp(self):
        self.c = {
            'unrecognized_port': 0.5,
            'nonmatching_convo': 0,
            'max_text_len': 1024,
            'score_length_weight': 0.3,
            'score_vlen_weight': 0.3,
            'score_growth_weight': 0.2,
            'score_shrink_weight': 0.2,
            'score_ratio_weight': 0.3,
            'score_specials_weight': 1.0,
            'training_treshold': 0.4,
            'detection_treshold':  0.1,
            'special_strings': Baseline.SPECIAL_STRINGS
        }

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
        self.assertBetween(0.5, 0.9, Template('abcd',[], self.c).similarity('axcd'))
        # insert
        self.assertBetween(0.5, 0.9, Template('abcd',[], self.c).similarity('abxcd'))
        # delete
        self.assertBetween(0.5, 0.9, Template('abcd',[], self.c).similarity('acd'))
        # no change
        self.assertEqual(1, Template('abcd',[], self.c).similarity('abcd'))

        # with 1 variable
        # replace
        self.assertEqual(1, Template('abcd',[TemplateVariable(1,1,1,1)], self.c).similarity('axcd'))
        # insert
        self.assertBetween(0.5, 0.9, Template('abcd',[TemplateVariable(1,1,1,1)], self.c).similarity('axycd'))
        self.assertEqual(1, Template('abcd',[TemplateVariable(1,1,1,2)], self.c).similarity('axycd'))
        # delete
        self.assertEqual(1, Template('abcd',[TemplateVariable(1,1,0,1)], self.c).similarity('acd'))
        # This testcase does not seem relevant. Why should we care about deletion?
        #self.assertBetween(0.5, 0.9, Template('abcd',[TemplateVariable(1,1,1,1)], self.c).similarity('acd'))
        # insert
        self.assertEqual(1, Template('abcd',[TemplateVariable(1,1,0,5)], self.c).similarity('awxyzcd'))
        self.assertBetween(0.3, 0.9, Template('abcd',[TemplateVariable(1,1,0,3)], self.c).similarity('awxyzcd'))
        # no change
        self.assertEqual(1, Template('abcd',[TemplateVariable(1,1,1,1)], self.c).similarity('abcd'))

    def test_practical_similarity(self):
        a = (
        "set 093a802b6de10157270839be4e9257f5 53276566323039643166343731313839323666363139653438303333633061333035270a70300a2e\nget 093a802b6de10157270839be4e9257f5\nquit\n",
        "OK\n53276566323039643166343731313839323666363139653438303333633061333035270a70300a2e")
        b = (
        "set 34b4a59dbf92f6657fe944dc10db35d4 53276436613062323565386666613535386665336233303332303631356336383762270a70300a2e\nget 34b4a59dbf92f6657fe944dc10db35d4\nquit\n",
        "OK\n53276436613062323565386666613535386665336233303332303631356336383762270a70300a2e")
        self.assertBetween(0.4, 0.7, Template(a[0], [], self.c).similarity(b[0]))
        self.assertBetween(0.4, 0.7, Template(a[1], [], self.c).similarity(b[1]))

    def test_var_expansion(self):
        pass
        #self.assertEqual(1, Template('xabcdx', [TemplateVariable(1, 4, 4, 4)], self.c).similarity('xdyyyx'))
        #self.assertEqual(1, Template('xabcdyefghz', [TemplateVariable(1, 4, 4, 4)], self.c).similarity('xcayfgz'))


    def test_flag_similarity(self):
        a=b'FLAG{2CB2C3F4C4E07730DEDBBE5DF90F62D0}'
        b=b'FLAG{42DE58F5A636FF957623DB77DACFBBD4}'
        self.assertEqual(1, Template(a, [TemplateVariable(5, 32, 32, 32)], self.c).similarity(b))
        a=b'FLAG{2CB2C3F4C4E07730DEDBBE5DF90F62D0}'
        b=b'FLAG{352EE4908C1415B90D5971E91C2769A1}'
        self.assertEqual(1, Template(a, [TemplateVariable(5, 32, 32, 32)], self.c).similarity(b))

    def test_flag_detection(self):
        temp = Template('abcdefgh', [TemplateVariable(2,4,4,4)], self.c)
        self.assertEqual(0, temp.similarity("abFLAGgh"))

    def test_show_template(self):
        t = Template(b'abcdefghijklmnopqrstuvwxyz',[TemplateVariable(1,4,1,4), TemplateVariable(9,1,1,4) ], self.c)
        self.assertEqual('a\x1b[32mbcde\x1b[0mfghi\x1b[32mj\x1b[0mklmnopqrstuvwxyz', t.show())
        t = Template(b'abcdefghijklmnopqrstuvwxyz',[TemplateVariable(1,4,1,4), TemplateVariable(9,0,1,4) ], self.c)
        self.assertEqual('a\x1b[32mbcde\x1b[0mfghi\x1b[31m*\x1b[0mjklmnopqrstuvwxyz', t.show())

    def check_update(self, a):
        t = Template('abcdefghijklmnopqrstuvwxyz',[TemplateVariable(1,4,1,4), TemplateVariable(9,1,1,4) ], self.c)
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
        self.assertTrue(Template("abc", [self.mock_var(fits=True)], self.c).fit_variable('good'))
        self.assertTrue(Template("abc", [self.mock_var(fits=False), self.mock_var(fits=True)], self.c).fit_variable('good'))
        self.assertFalse(Template("abc", [self.mock_var(fits=False)], self.c).fit_variable('bad'))

    def check_consolidate(self, invars, checkvars):
        invars = [TemplateVariable(*v) for v in invars]
        checkvars = [TemplateVariable(*v) for v in checkvars]
        t = Template("abcdefghijklmnopqrstuvwxyz", invars, self.c)
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
    def setUp(self):
        self.c = {
            'unrecognized_port': 0.5,
            'nonmatching_convo': 0,
            'max_text_len': 1024,
            'score_length_weight': 0.3,
            'score_vlen_weight': 0.3,
            'score_growth_weight': 0.2,
            'score_shrink_weight': 0.2,
            'score_ratio_weight': 0.3,
            'score_specials_weight': 1.0,
            'training_treshold': 0.4,
            'detection_treshold':  0.1,
            'special_strings': Baseline.SPECIAL_STRINGS
        }

    def check_similarity(self, sent, recv, result):
        sent_mock = Mock()
        sent_mock.similarity.return_value = sent
        recv_mock = Mock()
        recv_mock.similarity.return_value = recv
        c = ConvoTemplate("","", self.c)
        c.recv = recv_mock
        c.sent = sent_mock
        self.assertEqual(result, c.similarity('a', 'b'))
        sent_mock.similarity.assert_called_once_with('a')
        recv_mock.similarity.assert_called_once_with('b')

    def test_similarity(self):
        self.check_similarity(2, 0.5, 0.5)
        self.check_similarity(2, 0, 0)
        self.check_similarity(0, 2, 0)
        self.check_similarity(0, 0, 0)

    def test_update(self):
        sent_mock = Mock()
        recv_mock = Mock()
        c = ConvoTemplate("", "", self.c)
        c.recv = recv_mock
        c.sent = sent_mock
        c.update('a', 'b')
        sent_mock.update.assert_called_once_with('a')
        recv_mock.update.assert_called_once_with('b')

class ScrubEqualsTest(BaseTest):
    def test_equals(self):
        self.assertTrue(scrubbed_equals(b"abc", b"abc"))
        self.assertFalse(scrubbed_equals(b"abc", b"abd"))
        self.assertTrue(scrubbed_equals(b"abcFLAG{0123AB}", b"abcFLAG{0123ABDAA}"))