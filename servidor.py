"""Antecipe V6 local: HTTP + CSV + SQLite. Somente biblioteca padrão Python."""
import csv, io, json, sqlite3, zipfile, hashlib, re, os, secrets, threading, webbrowser, time
from pathlib import Path
from datetime import datetime
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from decimal import Decimal, InvalidOperation
from http.cookies import SimpleCookie
from hashlib import pbkdf2_hmac
import motor_validacao

ROOT=Path(__file__).resolve().parent
DB=ROOT/'antecipe.db'; HTML=(ROOT/'index.html').read_bytes() if (ROOT/'index.html').exists() else b''
MAX_FILE=120*1024*1024
SESSIONS={}; LOCK=threading.RLock()

def connect():
    db=sqlite3.connect(DB,timeout=45)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA busy_timeout=45000')
    db.executescript('''
CREATE TABLE IF NOT EXISTS arquivos(id INTEGER PRIMARY KEY,nome TEXT,sha256 TEXT UNIQUE,tipo TEXT,importado_em TEXT,linhas INTEGER);
CREATE TABLE IF NOT EXISTS registros(id INTEGER PRIMARY KEY,arquivo_id INTEGER,linha INTEGER,dados TEXT,doc_cedente TEXT,doc_sacado TEXT,valor REAL,vencimento TEXT,documento TEXT, UNIQUE(arquivo_id,linha));
CREATE TABLE IF NOT EXISTS situacoes(doc TEXT PRIMARY KEY,situacao TEXT,arquivo_id INTEGER);
CREATE TABLE IF NOT EXISTS regras(id INTEGER PRIMARY KEY,arquivo_id INTEGER,conteudo TEXT,ativo INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS pagamentos(id INTEGER PRIMARY KEY,arquivo_id INTEGER,linha INTEGER,documento TEXT,doc_sacado TEXT,valor REAL,data_pagamento TEXT,situacao TEXT,dados TEXT,UNIQUE(arquivo_id,linha));
CREATE TABLE IF NOT EXISTS referencias(id INTEGER PRIMARY KEY,arquivo_id INTEGER UNIQUE,conteudo TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS usuarios(id INTEGER PRIMARY KEY,nome TEXT UNIQUE,salt TEXT,senha_hash TEXT);
CREATE TABLE IF NOT EXISTS avaliacoes(id INTEGER PRIMARY KEY,registro_id INTEGER,regra_id INTEGER,status TEXT,motivos TEXT,avaliado_em TEXT,UNIQUE(registro_id,regra_id));
CREATE TABLE IF NOT EXISTS arquivos_conteudo(arquivo_id INTEGER PRIMARY KEY,conteudo BLOB NOT NULL);
''')
    cols={r['name'] for r in db.execute('PRAGMA table_info(registros)')}
    for col in ['fundo','cedente','sacado','tipo_recebivel','vencimento_iso','aquisicao_iso']:
        if col not in cols:db.execute('ALTER TABLE registros ADD COLUMN '+col+' TEXT')
    db.executescript('''CREATE TABLE IF NOT EXISTS historico_regras(id INTEGER PRIMARY KEY, regra_origem_id INTEGER, regra_nova_id INTEGER, usuario TEXT, alterado_em TEXT, conteudo TEXT); CREATE INDEX IF NOT EXISTS ix_documento ON registros(documento); CREATE INDEX IF NOT EXISTS ix_cedente ON registros(doc_cedente); CREATE INDEX IF NOT EXISTS ix_valor ON registros(valor); CREATE INDEX IF NOT EXISTS ix_tipo ON registros(tipo_recebivel); CREATE INDEX IF NOT EXISTS ix_aquisicao ON registros(aquisicao_iso); CREATE INDEX IF NOT EXISTS ix_fundo ON registros(fundo);CREATE INDEX IF NOT EXISTS ix_data ON registros(vencimento_iso);CREATE INDEX IF NOT EXISTS ix_sacado ON registros(doc_sacado);CREATE INDEX IF NOT EXISTS ix_avaliacoes ON avaliacoes(registro_id,regra_id);''')
    db.commit();return db

def norm(t):
    import unicodedata
    return re.sub(r'[^A-Z0-9]+','_',unicodedata.normalize('NFKD',str(t)).encode('ascii','ignore').decode().upper()).strip('_')
def doc(t):return ''.join(re.findall(r'\d+',str(t or '')))
def cash(t):
    s=str(t or '0').strip().replace('R$','').replace(' ','')
    if ',' in s:s=s.replace('.','').replace(',','.')
    try:return float(Decimal(s))
    except InvalidOperation:return 0

def date(t):
    s=str(t or '').strip()
    if re.fullmatch(r'\d{4}-\d\d-\d\d.*',s):return s[:10]
    if re.fullmatch(r'\d\d/\d\d/\d{4}',s):return s[6:]+'-'+s[3:5]+'-'+s[:2]
    return ''
def as_csv(blob):
    for enc in ('utf-8-sig','cp1252','latin1'):
        try:text=blob.decode(enc);break
        except UnicodeDecodeError:continue
    first=text[:8192]
    delimiter=';' if first.count(';')>first.count(',') else ','
    reader=csv.DictReader(io.StringIO(text),delimiter=delimiter)
    return [{norm(k):str(v or '').strip() for k,v in row.items() if k} for row in reader]

def type_of(cols):
    c=set(cols)
    if {'NU_DOCUMENTO','DOC_CEDENTE','DOC_SACADO','VALOR_NOMINAL'}<=c:return 'estoque'
    if ('DOC' in c or 'CNPJ' in c) and ('SITUACAO_CADASTRAL' in c or 'SITUACAO_CNPJ' in c):return 'cnpj'
    if ('VALOR_PAGO' in c or 'VALOR_PAGAMENTO' in c or 'VALOR_LIQUIDADO' in c) and ('NU_DOCUMENTO' in c or 'DOCUMENTO' in c or 'NUMERO_DOCUMENTO' in c):return 'pagamentos'
    return 'desconhecido'

def json_type(data,name):
    n=name.lower()
    if 'resultado_esperado' in n:return 'referencia'
    if 'validador' in n or 'regras' in n:return 'regras'
    if isinstance(data,dict) and ('rules' in data or 'validadores' in data):return 'regras'
    return 'referencia'

def import_one(db,name,blob):
    digest=hashlib.sha256(blob).hexdigest()
    old=db.execute('SELECT id FROM arquivos WHERE sha256=?',(digest,)).fetchone()
    if old:return {'arquivo':name,'situacao':'já importado','linhas':0}
    if name.lower().endswith('.csv'):
        rows=as_csv(blob)
        if not rows:raise ValueError('CSV vazio ou sem cabeçalho.')
        kind=type_of(rows[0])
        if kind=='desconhecido':raise ValueError('Colunas não reconhecidas: '+', '.join(list(rows[0])[:10]))
        payload=None
    elif name.lower().endswith('.json'):
        payload=json.loads(blob.decode('utf-8-sig'));kind=json_type(payload,name);rows=[]
    else:raise ValueError('Envie CSV, JSON ou ZIP.')
    with db:
        aid=db.execute('INSERT INTO arquivos(nome,sha256,tipo,importado_em,linhas) VALUES(?,?,?,?,?)',
            (name,digest,kind,datetime.now().isoformat(timespec='seconds'),len(rows) if kind not in ('regras','referencia') else 1)).lastrowid
        # Guarda arquivo original até 25 MB; arquivos maiores são identificados por hash e preservados no banco estruturado.
        if len(blob)<=25*1024*1024:db.execute('INSERT INTO arquivos_conteudo VALUES(?,?)',(aid,blob))
        if kind=='estoque':
            buffer=[]
            for i,r in enumerate(rows,2):
                buffer.append((aid,i,json.dumps(r,ensure_ascii=False),doc(r.get('DOC_CEDENTE')),doc(r.get('DOC_SACADO')),
                  cash(r.get('VALOR_NOMINAL')),r.get('DATA_VENCIMENTO_ORIGINAL',''),r.get('NU_DOCUMENTO',''),
                  r.get('NOME_FUNDO',''),r.get('NOME_CEDENTE',''),r.get('NOME_SACADO',''),r.get('TIPO_RECEBIVEL',''),
                  date(r.get('DATA_VENCIMENTO_ORIGINAL')),date(r.get('DATA_AQUISICAO'))))
                if len(buffer)>=2000:
                    db.executemany('INSERT INTO registros(arquivo_id,linha,dados,doc_cedente,doc_sacado,valor,vencimento,documento,fundo,cedente,sacado,tipo_recebivel,vencimento_iso,aquisicao_iso) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',buffer);buffer=[]
            if buffer:db.executemany('INSERT INTO registros(arquivo_id,linha,dados,doc_cedente,doc_sacado,valor,vencimento,documento,fundo,cedente,sacado,tipo_recebivel,vencimento_iso,aquisicao_iso) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',buffer)
        elif kind=='cnpj':
            db.executemany('INSERT INTO situacoes(doc,situacao,arquivo_id) VALUES(?,?,?) ON CONFLICT(doc) DO UPDATE SET situacao=excluded.situacao,arquivo_id=excluded.arquivo_id',
              [(doc(r.get('DOC') or r.get('CNPJ')),r.get('SITUACAO_CADASTRAL') or r.get('SITUACAO_CNPJ',''),aid) for r in rows])
        elif kind=='pagamentos':
            db.executemany('INSERT INTO pagamentos(arquivo_id,linha,documento,doc_sacado,valor,data_pagamento,situacao,dados) VALUES(?,?,?,?,?,?,?,?)',
                [(aid,i,r.get('NU_DOCUMENTO') or r.get('DOCUMENTO') or r.get('NUMERO_DOCUMENTO'),doc(r.get('DOC_SACADO') or r.get('CNPJ_SACADO')),
                   cash(r.get('VALOR_PAGO') or r.get('VALOR_PAGAMENTO') or r.get('VALOR_LIQUIDADO')),date(r.get('DATA_PAGAMENTO') or r.get('DATA_LIQUIDACAO')),
                   r.get('STATUS') or r.get('SITUACAO'),json.dumps(r,ensure_ascii=False)) for i,r in enumerate(rows,2)])
        elif kind=='regras':
            motor_validacao.validate_config(payload) if 'validadores' in payload else parse_rules(payload)
            db.execute('INSERT INTO regras(arquivo_id,conteudo,ativo) VALUES(?,?,0)',(aid,json.dumps(payload,ensure_ascii=False)))
        else:db.execute('INSERT INTO referencias(arquivo_id,conteudo) VALUES(?,?)',(aid,json.dumps(payload,ensure_ascii=False)))
    return {'arquivo':name,'tipo':kind,'situacao':'importado','linhas':len(rows)}

def import_file(db,name,blob):
    if len(blob)>MAX_FILE:raise ValueError('Arquivo excede 120 MB.')
    if not name.lower().endswith('.zip'):return [import_one(db,name,blob)]
    outcomes=[]
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        entries=[x for x in z.infolist() if not x.is_dir() and x.filename.lower().endswith(('.csv','.json'))]
        if len(entries)>100 or sum(x.file_size for x in entries)>300*1024*1024:raise ValueError('ZIP excede limites de segurança.')
        for e in entries:
            try:outcomes.append(import_one(db,e.filename,z.read(e)))
            except Exception as err:outcomes.append({'arquivo':e.filename,'situacao':'erro','mensagem':str(err)})
    return outcomes

OPS={'eq','ne','in','not_in','gt','gte','lt','lte','is_empty','not_empty','date_before','date_after'}
def parse_rules(payload):
    if not isinstance(payload,dict) or payload.get('schema')!='antecipe.rules.v1' or not isinstance(payload.get('rules'),list) or not payload['rules']:
        raise ValueError('JSON original armazenado, mas estrutura de regras ainda não traduzida. Esperado: schema antecipe.rules.v1 e rules[].')
    rules=payload['rules']
    for r in rules:
        if not isinstance(r,dict) or not r.get('id') or not re.fullmatch('[A-Z][A-Z0-9_]*',r.get('field','')) or r.get('operator') not in OPS or not r.get('reason'):
            raise ValueError('Uma regra está incompleta: precisa de id, field, operator e reason.')
        if r['operator'] not in {'is_empty','not_empty'} and 'value' not in r:raise ValueError('Falta value em '+r['id'])
    return rules

def match_rule(row,r):
    field=r['field'];op=r['operator'];expect=r.get('value')
    if field not in row:return None
    actual=str(row[field] or '').strip()
    if op=='is_empty':return actual==''
    if op=='not_empty':return actual!=''
    if op=='eq':return actual.casefold()==str(expect).casefold()
    if op=='ne':return actual.casefold()!=str(expect).casefold()
    if op=='in':return actual.casefold() in [str(x).casefold() for x in expect]
    if op=='not_in':return actual.casefold() not in [str(x).casefold() for x in expect]
    if op=='date_before':return bool(date(actual) and date(str(expect))) and date(actual)<date(str(expect))
    if op=='date_after':return bool(date(actual) and date(str(expect))) and date(actual)>date(str(expect))
    try:a=cash(actual);b=cash(expect)
    except Exception:return None
    return {'gt':a>b,'gte':a>=b,'lt':a<b,'lte':a<=b}[op]

def evaluate_batch(db,rule_id):
    record=db.execute('SELECT conteudo FROM regras WHERE id=?',(rule_id,)).fetchone()
    if not record:raise ValueError('Conjunto de regras não encontrado.')
    
    if 'validadores' in json.loads(record[0]):return motor_validacao.run(db,rule_id)
    rules=parse_rules(json.loads(record[0]));done=0
    with db:
        db.execute('DELETE FROM avaliacoes WHERE regra_id=?',(rule_id,))
        cur=db.execute('SELECT id,dados FROM registros')
        while True:
            batch=cur.fetchmany(1000)
            if not batch:break
            output=[]
            for r in batch:
                obj=json.loads(r['dados']);missing=[];reasons=[]
                for rule in rules:
                    result=match_rule(obj,rule)
                    if result is None:missing.append(rule['id'])
                    elif result:reasons.append(rule['reason'])
                status='NÃO AVALIADO' if missing else ('RECUSADO' if reasons else 'APROVADO')
                output.append((r['id'],rule_id,status,json.dumps({'motivos':reasons,'campos_ausentes':missing},ensure_ascii=False),datetime.now().isoformat(timespec='seconds')))
            db.executemany('INSERT INTO avaliacoes(registro_id,regra_id,status,motivos,avaliado_em) VALUES(?,?,?,?,?)',output);done+=len(output)
        db.execute('UPDATE regras SET ativo=0');db.execute('UPDATE regras SET ativo=1 WHERE id=?',(rule_id,))
    return done

def filters(q):
    where=[];args=[]
    fields={'fundo':'r.fundo','tipo':'r.tipo_recebivel','situacao':"COALESCE(s.situacao,'SEM CADASTRO')",'status':"COALESCE(av.status,'NÃO AVALIADO')"}
    for name,col in fields.items():
        if q.get(name):where.append(col+'=?');args.append(q[name][0])
    if q.get('motivo'):
        where.append("EXISTS (SELECT 1 FROM json_each(av.motivos,'$.motivos') je WHERE je.value=?)");args.append(q['motivo'][0])
    for key,col in [('valor_min','r.valor'),('valor_max','r.valor')]:
        if q.get(key):
            value=float(q[key][0].replace(',','.'))
            if value<0:raise ValueError('Valores de filtro não podem ser negativos.')
            where.append(col+('>=' if key=='valor_min' else '<=')+'?');args.append(value)
    for key,operator in [('aquisicao_inicio','>='),('aquisicao_fim','<=')]:
        if q.get(key):where.append('r.aquisicao_iso'+operator+'?');args.append(q[key][0])
    if q.get('busca'):
        s='%'+q['busca'][0]+'%';where.append('(r.documento LIKE ? OR r.cedente LIKE ? OR r.sacado LIKE ? OR r.doc_sacado LIKE ? OR r.doc_cedente LIKE ?)');args.extend([s]*5)
    for key,op,col in [('inicio','>=','r.vencimento_iso'),('fim','<=','r.vencimento_iso')]:
        if q.get(key):where.append(col+op+'?');args.append(q[key][0])
    return (' AND '.join(where) if where else '1=1'),args

def base():return ''' FROM registros r LEFT JOIN situacoes s ON s.doc=r.doc_sacado LEFT JOIN avaliacoes av ON av.registro_id=r.id AND av.regra_id=(SELECT id FROM regras WHERE ativo=1 ORDER BY id DESC LIMIT 1) '''

def stats(db,q):
    where,args=filters(q)
    res=db.execute('SELECT COUNT(*) n,COALESCE(SUM(r.valor),0) valor, COALESCE(SUM(CASE WHEN av.status="APROVADO" THEN r.valor ELSE 0 END),0) elegivel,COALESCE(SUM(CASE WHEN av.status="BARRADO" THEN r.valor ELSE 0 END),0) recusado, COALESCE(SUM(CASE WHEN av.status="APROVADO" THEN CAST(json_extract(av.motivos,"$.valor_antecipavel") AS REAL) ELSE 0 END),0) estimativa_liquida '+base()+' WHERE '+where,args).fetchone()
    group=[dict(x) for x in db.execute('SELECT COALESCE(NULLIF(r.fundo,""),"Não informado") nome,COUNT(*) quantidade,SUM(r.valor) valor '+base()+' WHERE '+where+' GROUP BY 1 ORDER BY valor DESC LIMIT 10',args)]
    situ=[dict(x) for x in db.execute('SELECT COALESCE(NULLIF(s.situacao,""),"SEM CADASTRO") nome,COUNT(*) quantidade '+base()+' WHERE '+where+' GROUP BY 1 ORDER BY quantidade DESC LIMIT 8',args)]
    status=[dict(x) for x in db.execute('SELECT COALESCE(av.status,"NÃO AVALIADO") nome,COUNT(*) quantidade '+base()+' WHERE '+where+' GROUP BY 1',args)]
    return {'indicadores':dict(res),'fundos':group,'situacoes':situ,'status':status,'total_arquivos':db.execute('SELECT COUNT(*) FROM arquivos').fetchone()[0]}

def records(db,q):
    where,args=filters(q);limit=min(200,max(1,int((q.get('limite') or ['50'])[0])));page=max(1,int((q.get('pagina') or ['1'])[0]))
    sql='''SELECT r.id,r.documento,r.fundo,r.cedente,r.sacado,r.valor,r.vencimento_iso vencimento,COALESCE(s.situacao,'SEM CADASTRO') situacao,COALESCE(av.status,'NÃO AVALIADO') status,COALESCE(av.motivos,'') motivos, CASE WHEN av.status='APROVADO' THEN json_extract(av.motivos,'$.valor_antecipavel') ELSE 0 END valor_antecipavel '''+base()+' WHERE '+where+' ORDER BY r.id DESC LIMIT ? OFFSET ?'
    return {'linhas':[dict(r) for r in db.execute(sql,args+[limit,(page-1)*limit])],'pagina':page}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def reply(self,status,data,typ='application/json; charset=utf-8',headers=None):
        if isinstance(data,(dict,list)):data=json.dumps(data,ensure_ascii=False).encode()
        elif isinstance(data,str):data=data.encode()
        self.send_response(status);self.send_header('Content-Type',typ);self.send_header('Content-Length',str(len(data)))
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store');self.send_header('X-Frame-Options','DENY');self.send_header('Content-Security-Policy',"default-src 'self' 'unsafe-inline'; connect-src 'self'")
        for k,v in (headers or {}).items():self.send_header(k,v)
        self.end_headers();self.wfile.write(data)
    def cookie_user(self):
        try:
            c=SimpleCookie();c.load(self.headers.get('Cookie',''));token=c['antecipe_sess'].value
            return SESSIONS.get(token)
        except Exception:return None
    def fail(self,status,msg):self.reply(status,{'erro':msg})
    def do_GET(self):
        url=urlparse(self.path);q=parse_qs(url.query)
        if url.path=='/':return self.reply(200,HTML,'text/html; charset=utf-8')
        with LOCK:
            db=connect()
            try:
                if url.path=='/api/config':return self.reply(200,{'setup':db.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0]==0,'login':bool(self.cookie_user())})
                if not self.cookie_user():return self.fail(401,'Faça login para acessar.')
                if url.path=='/api/stats':return self.reply(200,stats(db,q))
                if url.path=='/api/conferencia':return self.reply(200,motor_validacao.compare_gabarito(db,ROOT/'resultado_esperado_100k.json'))
                if url.path=='/api/auditoria':return self.reply(200,motor_validacao.audit_summary(db,ROOT/'resultado_esperado_100k.json'))
                if url.path=='/api/divergencias.csv':
                    report=motor_validacao.audit_csv(db,ROOT/'resultado_esperado_100k.json')
                    return self.reply(200,report,'text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="divergencias_antecipe_v6.csv"'})
                if url.path=='/api/records':return self.reply(200,records(db,q))
                if url.path=='/api/fundos':return self.reply(200,[r[0] for r in db.execute('SELECT DISTINCT fundo FROM registros WHERE fundo IS NOT NULL AND fundo<>"" ORDER BY fundo LIMIT 500')])
                if url.path=='/api/diagnostico':
                    counts=[dict(r) for r in db.execute("SELECT status, COUNT(*) quantidade FROM avaliacoes WHERE regra_id=(SELECT id FROM regras WHERE ativo=1 ORDER BY id DESC LIMIT 1) GROUP BY status")]
                    return self.reply(200,{'calculado':counts,'esperado':{'APROVADO':85215,'BARRADO':15339},'explicacao':'Os valores esperados são do gabarito. Divergências devem ser investigadas, não ajustadas artificialmente.'})
                if url.path=='/api/arquivos':return self.reply(200,[dict(r) for r in db.execute('SELECT id,nome,tipo,linhas,importado_em FROM arquivos ORDER BY id DESC LIMIT 150')])
                if url.path=='/api/regras/detalhes':
                    rid=int((q.get('id') or ['0'])[0]);rec=db.execute('SELECT id,conteudo,ativo FROM regras WHERE id=?',(rid,)).fetchone()
                    if not rec:return self.fail(404,'Conjunto de regras não encontrado.')
                    return self.reply(200,{'id':rec['id'],'ativo':bool(rec['ativo']),'config':json.loads(rec['conteudo'])})
                if url.path=='/api/historico_regras':return self.reply(200,[dict(x) for x in db.execute('SELECT id,regra_origem_id,regra_nova_id,usuario,alterado_em FROM historico_regras ORDER BY id DESC LIMIT 50')])
                if url.path=='/api/regras':
                    rows=[]
                    for r in db.execute('SELECT id,arquivo_id,ativo,conteudo FROM regras ORDER BY id DESC'):
                        try:
                            payload=json.loads(r['conteudo'])
                            (motor_validacao.validate_config(payload) if 'validadores' in payload else parse_rules(payload));compatible=True
                        except ValueError:compatible=False
                        rows.append({'id':r['id'],'arquivo_id':r['arquivo_id'],'ativo':bool(r['ativo']),'compativel':compatible})
                    return self.reply(200,rows)
                return self.fail(404,'Página não encontrada.')
            except Exception as e:return self.fail(400,str(e))
            finally:db.close()
    def do_POST(self):
        url=urlparse(self.path)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>MAX_FILE:return self.fail(413,'Arquivo maior que 120 MB.')
            if length<1:return self.fail(400,'Envie o conteúdo da solicitação.')
            body=self.rfile.read(length)
            with LOCK:
                db=connect()
                try:
                    if url.path in ('/api/setup','/api/login'):
                        data=json.loads(body);name=str(data.get('usuario','')).strip();password=str(data.get('senha',''))
                        if len(name)<3 or len(password)<10:return self.fail(400,'Informe usuário de 3 caracteres e senha de pelo menos 10 caracteres.')
                        exists=db.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0]
                        if url.path=='/api/setup':
                            if exists:return self.fail(403,'Administrador já cadastrado.')
                            salt=os.urandom(16);hashed=pbkdf2_hmac('sha256',password.encode(),salt,250000)
                            with db:db.execute('INSERT INTO usuarios(nome,salt,senha_hash) VALUES(?,?,?)',(name,salt.hex(),hashed.hex()))
                        else:
                            record=db.execute('SELECT salt,senha_hash FROM usuarios WHERE nome=?',(name,)).fetchone()
                            if not record:return self.fail(401,'Usuário ou senha incorretos.')
                            candidate=pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(record['salt']),250000)
                            if not secrets.compare_digest(candidate.hex(),record['senha_hash']):return self.fail(401,'Usuário ou senha incorretos.')
                        token=secrets.token_urlsafe(32);SESSIONS[token]=name
                        return self.reply(200,{'ok':True},headers={'Set-Cookie':f'antecipe_sess={token}; HttpOnly; SameSite=Strict; Path=/'})
                    if url.path=='/api/logout':
                        c=SimpleCookie();c.load(self.headers.get('Cookie',''))
                        if 'antecipe_sess' in c:SESSIONS.pop(c['antecipe_sess'].value,None)
                        return self.reply(200,{'ok':True},headers={'Set-Cookie':'antecipe_sess=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
                    if not self.cookie_user():return self.fail(401,'Sessão encerrada. Faça login.')
                    if url.path=='/api/upload':
                        name=unquote((parse_qs(url.query).get('nome') or ['arquivo.csv'])[0]);name=Path(name.replace('\\','/')).name
                        outcomes=import_file(db,name,body)
                        should_run=any(x.get('situacao')=='importado' and x.get('tipo') in ('estoque','cnpj','regras') for x in outcomes)
                        evaluation=None
                        if should_run and db.execute('SELECT COUNT(*) FROM registros').fetchone()[0]>0:
                            rule=db.execute('SELECT id FROM regras ORDER BY ativo DESC,id DESC LIMIT 1').fetchone()
                            if rule:
                                evaluation=evaluate_batch(db,rule['id'])
                        return self.reply(200,{'resultados':outcomes,'validacao':evaluation})
                    if url.path=='/api/regras/salvar':
                        data=json.loads(body);source_id=int(data.get('regra_id') or 0);cfg=data.get('config')
                        source=db.execute('SELECT id FROM regras WHERE id=?',(source_id,)).fetchone()
                        if not source:return self.fail(404,'Conjunto original não encontrado.')
                        motor_validacao.validate_config(cfg)
                        for item in cfg['validadores']:
                            if not isinstance(item.get('ativo'),bool):return self.fail(400,'Cada validador precisa definir ativo como verdadeiro ou falso.')
                            if item['codigo'] not in motor_validacao.SUPPORTED:return self.fail(400,'Validador desconhecido: '+str(item['codigo']))
                        for item in cfg['validadores']:
                            code=item['codigo'];par=item.get('parametros',{})
                            if not isinstance(par,dict):return self.fail(400,'Parâmetros inválidos: '+code)
                            for key in ['valor_minimo','prazo_maximo_dias','prazo_minimo_dias','percentual_maximo']:
                                if key in par and (not isinstance(par[key],(int,float)) or isinstance(par[key],bool) or par[key]<0):return self.fail(400,'Parâmetro inválido: '+key)
                            if code=='CONCENTRACAO_MAXIMA_SACADO' and par.get('agrupamento')!='RAIZ_CNPJ':return self.fail(400,'Agrupamento não suportado: utilize RAIZ_CNPJ.')
                        prec=cfg['precificacao']
                        for key in ['taxa_mensal_percentual','base_dias']:
                            if not isinstance(prec.get(key),(int,float)) or isinstance(prec[key],bool) or prec[key] <= (0 if key=='base_dias' else -1):return self.fail(400,'Precificação inválida: '+key)
                        with db:
                            db.execute('UPDATE regras SET ativo=0')
                            newid=db.execute('INSERT INTO regras(arquivo_id,conteudo,ativo) VALUES(NULL,?,1)',(json.dumps(cfg,ensure_ascii=False),)).lastrowid
                            db.execute('INSERT INTO historico_regras(regra_origem_id,regra_nova_id,usuario,alterado_em,conteudo) VALUES(?,?,?,?,?)',(source_id,newid,self.cookie_user(),datetime.now().isoformat(timespec='seconds'),json.dumps(cfg,ensure_ascii=False)))
                        # Não executa implicitamente para permitir revisão da configuração.
                        return self.reply(200,{'id':newid,'mensagem':'Nova versão das regras salva. Clique em Validar recebíveis para recalcular as decisões.'})
                    if url.path=='/api/avaliar':
                        rule_id=int(json.loads(body).get('regra_id',0))
                        
                        result=evaluate_batch(db,rule_id)
                        return self.reply(200,result if isinstance(result,dict) else {'avaliados':result})
                    return self.fail(404,'Operação desconhecida.')
                finally:db.close()
        except Exception as e:return self.fail(400,str(e))

def main():
    global HTML
    HTML=(ROOT/'index.html').read_bytes()
    db=connect()
    try:
        cfg=(ROOT/'validadores_antecipe.json').read_bytes()
        import_one(db,'validadores_antecipe.json',cfg)
    finally:db.close()
    host='127.0.0.1';port=8501
    try:server=ThreadingHTTPServer((host,port),Handler)
    except OSError:
        print('Porta 8501 ocupada. Encerre a versão anterior e tente novamente.');return
    print(f'Antecipe V6 pronto em http://{host}:{port}')
    threading.Timer(1,lambda:webbrowser.open(f'http://{host}:{port}')).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
