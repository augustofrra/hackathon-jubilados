from pathlib import Path
import tempfile,zipfile,sys,csv,io
sys.path.insert(0,str(Path(__file__).parent))
import servidor,motor_validacao
source=Path('/mnt/data');project=Path(__file__).parent
if not (source/'estoque_antecipe_100k (1).zip').exists():
 print('Dados reais não disponíveis. Teste de auditoria requer base do desafio.');sys.exit(0)
with tempfile.TemporaryDirectory() as tmp:
 servidor.DB=Path(tmp)/'test.db';db=servidor.connect()
 try:
  with zipfile.ZipFile(source/'estoque_antecipe_100k (1).zip') as z:
   name=next(x for x in z.namelist() if x.endswith('.csv'))
   servidor.import_one(db,name,z.read(name))
  servidor.import_one(db,'cnpj_situacao_mock.csv',(source/'cnpj_situacao_mock.csv').read_bytes())
  servidor.import_one(db,'validadores_antecipe.json',(project/'validadores_antecipe.json').read_bytes())
  rule=db.execute('SELECT id FROM regras').fetchone()[0]
  result=motor_validacao.run(db,rule)
  assert result['avaliados']==100554
  summary=motor_validacao.audit_summary(db,project/'resultado_esperado_100k.json')
  csvreport=motor_validacao.audit_csv(db,project/'resultado_esperado_100k.json')
  lines=list(csv.reader(io.StringIO(csvreport.lstrip('\ufeff')),delimiter=';'))
  assert summary['divergentes']==len(lines)-1,(summary['divergentes'],len(lines))
  assert summary['total_recebiveis']==100554
  print('AUDITORIA_OK',summary,'csv_divergencias',len(lines)-1)
 finally:db.close()
