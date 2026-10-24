"""Validação do JSON oficial. Sem dependências externas."""
import json,re,datetime,sqlite3,collections
from decimal import Decimal, ROUND_HALF_UP

SUPPORTED={'CNPJ_SACADO_VALIDO','SITUACAO_CADASTRAL_SACADO','TIPO_RECEBIVEL','VALOR_MINIMO','NAO_VENCIDA','PRAZO_MAXIMO','CONCENTRACAO_MAXIMA_SACADO','PRAZO_MINIMO','CONCENTRACAO_MAXIMA_CEDENTE'}

def numbers(v):return re.sub(r'\D','',str(v or ''))
def parse_date(s):
    try:return datetime.date.fromisoformat(s[:10]) if re.match(r'^\d{4}-\d\d-\d\d',str(s)) else datetime.datetime.strptime(s,'%d/%m/%Y').date()
    except (TypeError, ValueError):return None

def valid_cnpj(value):
    n=numbers(value)
    if len(n)!=14 or n==n[0]*14:return False
    for length in (12,13):
        weights=[5,4,3,2,9,8,7,6,5,4,3,2] if length==12 else [6,5,4,3,2,9,8,7,6,5,4,3,2]
        d=(sum(int(n[i])*weights[i] for i in range(length))*10)%11
        if (d if d<10 else 0)!=int(n[length]):return False
    return True

def validate_config(cfg):
    if not isinstance(cfg,dict) or not isinstance(cfg.get('validadores'),list) or not cfg['validadores']:
        raise ValueError('JSON precisa conter validadores[].')
    codes=[r.get('codigo') for r in cfg['validadores']]
    if len(codes)!=len(set(codes)):raise ValueError('Há códigos de validação repetidos.')
    unknown=[r.get('codigo') for r in cfg['validadores'] if r.get('ativo') and r.get('codigo') not in SUPPORTED]
    if unknown:raise ValueError('Validadores ativos desconhecidos: '+', '.join(map(str,unknown)))
    p=cfg.get('precificacao',{})
    if p.get('metodo')!='DESCONTO_SIMPLES' or float(p.get('base_dias',0))<=0:raise ValueError('Precificação não suportada.')
    return cfg

def run(db,rule_id):
    rec=db.execute('SELECT conteudo FROM regras WHERE id=?',(rule_id,)).fetchone()
    if not rec:raise ValueError('Conjunto não encontrado')
    cfg=validate_config(json.loads(rec['conteudo']))
    active={r['codigo']:r.get('parametros',{}) for r in cfg['validadores'] if r.get('ativo')}
    # A concentração considera valor nominal total por fundo e raiz de CNPJ,
    # usando todos os títulos na carteira, independentemente das demais regras.
    totals=collections.defaultdict(int);by_sacado=collections.defaultdict(int);by_cedente=collections.defaultdict(int)
    cursor=db.execute('SELECT id,fundo,doc_sacado,doc_cedente,valor FROM registros')
    while True:
        batch=cursor.fetchmany(4000)
        if not batch:break
        for r in batch:
            fund=r['fundo'] or ''; cents=round((r['valor'] or 0)*100)
            totals[fund]+=cents;by_sacado[fund,numbers(r['doc_sacado'])[:8]]+=cents
            by_cedente[fund,numbers(r['doc_cedente'])[:8]]+=cents
    cadastral={r['doc']:r['situacao'] for r in db.execute('SELECT doc,situacao FROM situacoes')}
    now=datetime.datetime.now().isoformat(timespec='seconds')
    count=0;unavailable=0
    with db:
        db.execute('DELETE FROM avaliacoes WHERE regra_id=?',(rule_id,))
        # O cursor usa a mesma conexão, mas somente outras tabelas são alteradas.
        cur=db.execute('SELECT id,dados,fundo,doc_sacado,doc_cedente,valor,vencimento_iso,aquisicao_iso FROM registros ORDER BY id')
        while True:
            rows=cur.fetchmany(1500)
            if not rows:break
            batch=[]
            for r in rows:
                raw=json.loads(r['dados']);fund=r['fundo'] or '';sacado=numbers(r['doc_sacado']);cedente=numbers(r['doc_cedente'])
                venc=parse_date(r['vencimento_iso'] or raw.get('DATA_VENCIMENTO_ORIGINAL',''))
                acquisition=parse_date(r['aquisicao_iso'] or raw.get('DATA_AQUISICAO',''))
                days=(venc-acquisition).days if venc and acquisition else None
                reasons=[];warnings=[]
                for code,p in active.items():
                    failed=False
                    if code=='CNPJ_SACADO_VALIDO':failed=not valid_cnpj(sacado)
                    elif code=='SITUACAO_CADASTRAL_SACADO':
                        status=cadastral.get(sacado)
                        if status is None:warnings.append('Situação cadastral não localizada para '+sacado)
                        else:failed=status.upper() not in [str(x).upper() for x in p['situacoes_aceitas']]
                    elif code=='TIPO_RECEBIVEL':failed=raw.get('TIPO_RECEBIVEL','') not in p['tipos_aceitos']
                    elif code=='VALOR_MINIMO':failed=(r['valor'] or 0)<float(p['valor_minimo'])
                    elif code=='NAO_VENCIDA':
                        if days is None:warnings.append('Data de vencimento ou aquisição não disponível')
                        else:failed=days<0
                    elif code=='PRAZO_MAXIMO':
                        if days is None:warnings.append('Prazo não disponível')
                        else:failed=days>int(p['prazo_maximo_dias'])
                    elif code=='PRAZO_MINIMO':
                        if days is None:warnings.append('Prazo mínimo não calculável')
                        else:failed=days<int(p['prazo_minimo_dias'])
                    elif code in ('CONCENTRACAO_MAXIMA_SACADO','CONCENTRACAO_MAXIMA_CEDENTE'):
                        if code=='CONCENTRACAO_MAXIMA_SACADO':
                            if p.get('agrupamento')!='RAIZ_CNPJ':raise ValueError('Agrupamento de concentração não suportado')
                            exposure=by_sacado[fund,sacado[:8]]
                        else:exposure=by_cedente[fund,cedente[:8]]
                        if totals[fund]:failed=exposure*100>totals[fund]*float(p['percentual_maximo'])
                    if failed:reasons.append(code)
                status='BARRADO' if reasons else ('PENDENTE' if warnings else 'APROVADO')
                if status=='PENDENTE':unavailable+=1
                # Desconto simples comercial: VP = VN * (1 - taxa_mensal * prazo/base)
                rate=Decimal(str(cfg['precificacao']['taxa_mensal_percentual']))/100
                nominal=Decimal(str(r['valor'] or 0)); term=Decimal(days or 0)/Decimal(str(cfg['precificacao']['base_dias']))
                quoted=(nominal*(1-rate*term)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)
                price=max(Decimal(0),quoted) if status=='APROVADO' else Decimal(0)
                reasons_json=json.dumps({'motivos':reasons,'avisos':warnings,'valor_antecipavel':float(price),'prazo_dias':days,'valor_nominal':float(nominal),'desconto':float(max(Decimal(0),nominal-price)) if status=='APROVADO' else 0},ensure_ascii=False)
                batch.append((r['id'],rule_id,status,reasons_json,now))
            db.executemany('INSERT INTO avaliacoes(registro_id,regra_id,status,motivos,avaliado_em) VALUES(?,?,?,?,?)',batch)
            count+=len(rows)
        db.execute('UPDATE regras SET ativo=0')
        db.execute('UPDATE regras SET ativo=1 WHERE id=?',(rule_id,))
    return {'avaliados':count,'pendentes':unavailable,'aviso':'PENDENTE significa que não há informações suficientes para decidir; não é aprovação.'}

def compare_gabarito(db,path):
    data=json.load(open(path,encoding='utf-8'))
    active=db.execute('SELECT id FROM regras WHERE ativo=1 LIMIT 1').fetchone()
    if not active:raise ValueError('Execute primeiro o conjunto de regras.')
    cursor=db.execute('SELECT r.linha,r.documento,a.status,a.motivos FROM registros r JOIN avaliacoes a ON a.registro_id=r.id WHERE a.regra_id=? ORDER BY r.linha,r.id',(active['id'],))
    by_line={r['linha']:(r['documento'],r['status'],json.loads(r['motivos']).get('motivos',[])) for r in cursor}
    divergencias=[];matched=0
    for row in data:
        entry=by_line.get(row['linha']);wanted=sorted(row.get('barrado_por',[]))
        if entry and entry[0]==row['id'] and entry[1]==row['status'] and sorted(entry[2])==wanted:matched+=1
        else:
            if len(divergencias)<100:divergencias.append({'linha':row['linha'],'id':row['id'],'esperado':row['status'],'motivos_esperados':wanted,'calculado':entry})
    return {'esperados':len(data),'coincidentes':matched,'divergentes':len(data)-matched,'amostras_divergencias':divergencias}


def audit_summary(db, reference_path):
    """Auditoria descritiva; o gabarito nunca altera decisões de validação."""
    expected=json.load(open(reference_path,encoding='utf-8'))
    ref_counts=collections.Counter(r['status'] for r in expected)
    active=db.execute('SELECT id FROM regras WHERE ativo=1 ORDER BY id DESC LIMIT 1').fetchone()
    if not active:raise ValueError('Primeiro execute a validação em Regras e histórico.')
    calculated=collections.Counter({r['status']:r['n'] for r in db.execute('SELECT status,COUNT(*) n FROM avaliacoes WHERE regra_id=? GROUP BY status',(active['id'],))})
    total=db.execute('SELECT COUNT(*) FROM registros').fetchone()[0]
    no_registration=db.execute('SELECT COUNT(*) FROM registros r LEFT JOIN situacoes s ON r.doc_sacado=s.doc WHERE s.doc IS NULL').fetchone()[0]
    bad_registration=db.execute("SELECT COUNT(*) FROM registros r JOIN situacoes s ON r.doc_sacado=s.doc WHERE UPPER(s.situacao)<>'ATIVA'").fetchone()[0]
    cmp=compare_gabarito(db,reference_path)
    return {'total_recebiveis':total,'com_cadastro':total-no_registration,'sem_cadastro':no_registration,
      'cadastros_nao_ativos':bad_registration,'esperado':dict(ref_counts),'calculado':dict(calculated),
      'coincidentes':cmp['coincidentes'],'divergentes':cmp['divergentes'],
      'taxa_concordancia':round(100*cmp['coincidentes']/len(expected),4) if expected else None,
      'explicacao':'Cadastro ausente produz pendência, não aprovação. O gabarito é usado somente para confronto e nunca alimenta o motor.'}


def audit_csv(db,reference_path):
    """Gera CSV em memória das divergências para análise sem modificar nada."""
    import csv,io
    expected=json.load(open(reference_path,encoding='utf-8'))
    rule=db.execute('SELECT id FROM regras WHERE ativo=1 ORDER BY id DESC LIMIT 1').fetchone()
    if not rule:raise ValueError('Primeiro execute uma validação.')
    records={r['linha']:r for r in db.execute("""SELECT r.linha,r.documento,r.doc_sacado,r.doc_cedente,r.valor,a.status,a.motivos,
           COALESCE(s.situacao,'SEM CADASTRO') cadastro
           FROM registros r LEFT JOIN avaliacoes a ON a.registro_id=r.id AND a.regra_id=?
           LEFT JOIN situacoes s ON s.doc=r.doc_sacado ORDER BY r.id""",(rule['id'],))}
    out=io.StringIO();writer=csv.writer(out,delimiter=';');writer.writerow(['linha','documento','status_esperado','status_calculado','motivos_esperados','motivos_calculados','situacao_cadastral','doc_sacado','valor_nominal'])
    for e in expected:
        actual=records.get(e['linha']); reasons=json.loads(actual['motivos']).get('motivos',[]) if actual and actual['motivos'] else []
        if actual and actual['documento']==e['id'] and actual['status']==e['status'] and sorted(reasons)==sorted(e.get('barrado_por',[])):continue
        writer.writerow([e['linha'],e['id'],e['status'],actual['status'] if actual else 'AUSENTE',','.join(e.get('barrado_por',[])),','.join(reasons),actual['cadastro'] if actual else '',actual['doc_sacado'] if actual else '',actual['valor'] if actual else ''])
    return '\ufeff'+out.getvalue()
