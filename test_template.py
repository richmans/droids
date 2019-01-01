from base_test import BaseTest
from template import Template, TemplateVariable

class TemplateTest(BaseTest):
    def checkVariables(self, a,b,outcome):
        self.assertEqual([TemplateVariable(*outcome, "")], Template(a).find_variables(b))

    def test_variables(self):
        self.checkVariables('abcd', 'axcd', (1,1,1))
        self.checkVariables('abcd', 'axycd', (1,1,2))
