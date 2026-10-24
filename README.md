# ANTECIPE V6 — Portal local de antecipação de recebíveis

Protótipo para o desafio *Hackathon Antecipe*. Preserva login, importações CSV/ZIP/JSON, banco SQLite, filtros, gráficos e regras da V5 e acrescenta **auditoria cadastral** e **exportação CSV de divergências**.

## Executar do zero no Windows

1. Instale **Python 3.13** em <https://www.python.org/downloads/windows/>. Depois abra um novo PowerShell e verifique: `python --version` (ou `py --version`).
2. Baixe este repositório como ZIP, extraia **todos** os arquivos e abra a pasta `Antecipe_V6` (onde estão `servidor.py` e `INICIAR_ANTECIPE.bat`).
3. Dê dois cliques em **`INICIAR_ANTECIPE.bat`**. Alternativamente, abra o PowerShell nessa pasta e execute `python servidor.py` ou `py -3 servidor.py`.
4. Acesse <http://127.0.0.1:8501>, crie seu usuário administrador no primeiro acesso e faça login. **Mantenha o terminal aberto.** Para encerrar, pressione `Ctrl+C` no terminal.

Não é necessário `pip install`, Node.js, Streamlit, pandas, Plotly nem instalar SQLite separadamente. Não há variáveis de ambiente obrigatórias. O servidor escuta em `127.0.0.1:8501`. Se a porta estiver ocupada, feche outras versões do Antecipe antes de iniciar.

## Como demonstrar aos jurados

1. Na página **Importação**, envie o ZIP contendo `estoque_antecipe.csv` (CSV com cabeçalho, separador `;`, decimal com vírgula, data `dd/mm/aaaa`, UTF-8) e `cnpj_situacao_mock.csv`. Envie separadamente se preferir.
2. O aplicativo identifica o tipo de arquivo pelas colunas, armazena os títulos no SQLite e identifica reimportação do **mesmo arquivo** pelo SHA-256. Uma nova versão do conteúdo pode exigir auditoria adicional de duplicidade por título.
3. O arquivo `validadores_antecipe.json` está incluído; no menu **Regras e histórico**, selecione **Validar recebíveis** para aplicar as regras ativas. Parâmetros e ativação são lidos do arquivo, sem editar o código.
4. Abra **Consulta** para filtrar títulos e consultar `APROVADO`, `BARRADO` ou `PENDENTE`, motivos e valor líquido estimado. Abra o **Dashboard** para indicadores e gráficos.
5. Em **Regras e histórico**, clique em **Analisar cobertura cadastral e divergências** e em **Exportar divergências CSV**. A comparação com o gabarito é apenas auditoria, **não** determina os resultados do motor.

## API local

Os endpoints usam JSON e requerem sessão autenticada no navegador (exceto configuração/login):

| Método | Rota | Função |
|---|---|---|
| GET | `/api/config` | Estado de configuração e sessão |
| POST | `/api/setup` | Criar administrador no primeiro acesso |
| POST | `/api/login` | Autenticar |
| POST | `/api/logout` | Encerrar sessão |
| POST | `/api/upload?nome=arquivo.csv` | Enviar os bytes do CSV, ZIP ou JSON (`application/octet-stream`) |
| GET | `/api/records` | Consultar títulos com filtros e paginação |
| GET | `/api/stats` | Indicadores e gráficos |
| GET | `/api/regras` | Ver conjuntos de regras |
| POST | `/api/avaliar` | Executar validação (`{"regra_id":1}`) |
| GET | `/api/auditoria` | Cobertura cadastral e divergências |
| GET | `/api/divergencias.csv` | Baixar CSV das divergências |
| GET | `/api/conferencia` | Comparar resultados ao gabarito |

A interface utiliza **a mesma API** de importação e validação disponível via HTTP. Para uso por scripts, autentique-se primeiro e encaminhe o cookie da sessão. A API é local e não deve ser exposta na rede pública.

## Regras e preço

O arquivo `validadores_antecipe.json` define os validadores ativos e seus parâmetros. As regras fornecidas incluem CNPJ do sacado, situação cadastral, tipo, valor mínimo, vencimento, prazo e concentração por raiz de CNPJ do sacado. Regras marcadas com `ativo: false` são ignoradas. O preço estimado usa **desconto simples comercial**: `líquido = nominal × (1 − taxa_mensal × dias/base_dias)`, com os números retirados do JSON (originalmente 2% ao mês e base de 30 dias). Essa estimativa não equivale a uma oferta financeira.

A data-base indicada no desafio é **22/10/2026**; as verificações de prazo neste protótipo usam os campos `DATA_AQUISICAO` e `DATA_VENCIMENTO_ORIGINAL` de cada título. Essa interpretação deve ser confirmada com a regra oficial do desafio.

## Testes e limites conhecidos

No teste com o estoque e cadastro fornecidos: **100.554 títulos**, **3.041 cadastros**, valor nominal total de aproximadamente **R$ 604,93 milhões**. Resultado computado: **69.203 aprovados, 13.841 barrados e 17.510 pendentes**. O gabarito registra **85.215 aprovados, 15.339 barrados**; a comparação exata de status **e motivos** encontrou **80.867 concordâncias** e **19.687 divergências**. Existem **22.222 títulos sem correspondência cadastral** no CSV fornecido. A V6 não reproduz integralmente o gabarito e **não deve tomar decisões financeiras reais**.

Para reproduzir testes básicos:

```powershell
python testes_rapidos.py
python teste_integracao.py
python teste_auditoria_v6.py
```

Os testes de integração podem levar vários segundos ou minutos e utilizam os arquivos do desafio quando disponíveis. Uma simulação prévia de 10 milhões de registros reduzidos não é comprovação de processamento completo de 10 milhões de notas.

## Arquitetura e decisões

- **Servidor**: Python (`servidor.py`), API HTTP local.
- **Motor de regras e conciliação**: `motor_validacao.py`.
- **Interface**: `index.html` com HTML, CSS e JavaScript sem frameworks externos.
- **Banco**: SQLite (`antecipe.db`), criado automaticamente e preservado entre execuções.
- **Importação**: CSV/ZIP/JSON com identificação por colunas, registro da origem e hash de arquivo.
- **Auditoria**: confronto linha a linha com `resultado_esperado_100k.json` e exportação de divergências.

### O que ficou de fora

Garantia de unicidade de um mesmo título em **arquivos diferentes** (deduplicação de arquivo não é deduplicação de recebível), segurança para implantação pública, operação multiusuário corporativa, processamento completo de 10 milhões de títulos e reprodução integral das decisões oficiais. A regra de concentração deve ser auditada quanto ao universo considerado antes de uso real.

## Proteção de dados e versionamento

O banco `antecipe.db` guarda dados importados e credenciais locais. **Não publique o banco nem dados reais de clientes no GitHub.** Faça backup com o servidor encerrado antes de substituir os arquivos de uma versão anterior. O histórico dos prompts de IA está em [`PROMPTS.md`](PROMPTS.md).


## V6 — Gestão de regras e filtros adicionais

Em **Regras e histórico**, clique em **Editar regras**, altere os interruptores e parâmetros e selecione **Salvar nova versão das regras**. O sistema cria um registro auditável, preservando as versões anteriores. Para aplicar as alterações, selecione **Validar recebíveis** no novo conjunto. Os parâmetros permanecem armazenados no SQLite; o arquivo JSON original não é sobrescrito.

Em **Consultar recebíveis**, também é possível filtrar por tipo, motivo específico de recusa, valor mínimo/máximo e período de aquisição, além dos filtros existentes. Filtros são combinados no banco SQLite; as consultas são paginadas.

**Atenção:** alterar regras pode modificar a contagem de aprovações. Isso não corrige por si só divergências com o gabarito oficial.
