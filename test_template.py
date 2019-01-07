from base_test import BaseTest
from template import Template, TemplateVariable
from util import dbg


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
