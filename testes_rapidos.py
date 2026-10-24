"""Testes isolados: python testes_rapidos.py"""
import unittest,sqlite3,tempfile,json
from decimal import Decimal
import motor_validacao as m
class Testes(unittest.TestCase):
 def test_cnpj(self):
  self.assertTrue(m.valid_cnpj('11.222.333/0001-81'))
  self.assertFalse(m.valid_cnpj('11.222.333/0001-82'))
 def test_config(self):
  from pathlib import Path
  c=json.loads((Path(__file__).parent/'validadores_antecipe.json').read_text())
  self.assertEqual(len([x for x in m.validate_config(c)['validadores'] if x['ativo']]),7)
 def test_datas(self):
  self.assertEqual(str(m.parse_date('24/10/2026')),'2026-10-24')
  self.assertEqual(str(m.parse_date('2026-10-24')),'2026-10-24')
 def test_preco_exemplo(self):
  nominal=Decimal('1000.00');taxa=Decimal('0.02');dias=Decimal('30')
  self.assertEqual(nominal*(1-taxa*dias/30),Decimal('980.0000'))
if __name__=='__main__': unittest.main()
