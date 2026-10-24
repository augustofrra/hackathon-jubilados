from pathlib import Path
import tempfile,zipfile,sys,time,json,collections
sys.path.insert(0,str(Path(__file__).parent))
import servidor,motor_validacao
base=Path(__file__).parent
source=Path('/mnt/data')
with tempfile.TemporaryDirectory() as tmp:
 servidor.DB=Path(tmp)/'teste.db'
 db=servidor.connect()
 try:
  z=zipfile.ZipFile(source/'estoque_antecipe_100k (1).zip'); name=next(n for n in z.namelist() if n.lower().endswith('.csv'))
  t=time.monotonic();print('IMPORT_ESTOQUE',servidor.import_one(db,name,z.read(name)),flush=True)
  print('IMPORT_CNPJ',servidor.import_one(db,'cnpj_situacao_mock.csv',(source/'cnpj_situacao_mock.csv').read_bytes()),flush=True)
  print('REGRA',servidor.import_one(db,'validadores_antecipe.json',(base/'validadores_antecipe.json').read_bytes()),flush=True)
  rid=db.execute('SELECT id FROM regras').fetchone()[0]
  print('IMPORT_SECONDS',round(time.monotonic()-t,2),flush=True)
  t=time.monotonic();print('VALIDACAO',motor_validacao.run(db,rid),flush=True)
  print('VALIDACAO_SECONDS',round(time.monotonic()-t,2),flush=True)
  print('STATUSES',[(x[0],x[1]) for x in db.execute('SELECT status,COUNT(*) FROM avaliacoes GROUP BY status')],flush=True)
  print('STATS',servidor.stats(db,{})['indicadores'],flush=True)
  t=time.monotonic();print('COMPARACAO', {k:v for k,v in motor_validacao.compare_gabarito(db,base/'resultado_esperado_100k.json').items() if k!='amostras_divergencias'},flush=True)
  print('COMPARACAO_SECONDS',round(time.monotonic()-t,2),flush=True)
 finally:db.close()
