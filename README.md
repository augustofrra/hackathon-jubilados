## ANTECIPE V6 — Regras e Filtros

## Manual de instalação, execução e utilização

O **Antecipe V6** é um protótipo de plataforma web local, desenvolvido para o desafio Hackathon Antecipe da Kanastra.

O objetivo é permitir a importação de recebíveis, o armazenamento em SQLite, a execução de regras de elegibilidade configuráveis e a consulta de resultados financeiros.

O projeto utiliza Python no servidor e HTML, CSS e JavaScript na interface.

**Estado do projeto:** protótipo funcional com limitações conhecidas. A validação financeira ainda apresenta divergências em relação ao gabarito fornecido pelo desafio.

---

# 1. Requisitos de instalação

Para executar o projeto em um computador Windows, são necessários:

| Recurso | Necessário? | Observação |
|---|---|---|
| Python 3 | Sim | Executa o servidor |
| Navegador web | Sim | Exibe a interface |
| Visual Studio Code | Não | Opcional |
| Git | Não | Opcional para obter o código |
| SQLite separado | Não | Módulo `sqlite3` incluído na distribuição padrão do Python |
| Node.js | Não | O projeto não utiliza Node.js |
| Streamlit | Não | O projeto não utiliza Streamlit |
| pandas e Plotly | Não | Não são dependências do projeto |
| Compilador C/C++ | Não | Não é necessário para executar o código fornecido |

### Versão do Python

Recomenda-se utilizar **Python 3.13**.

O código utiliza recursos da biblioteca padrão do Python 3. Entretanto, a compatibilidade com todas as versões do Python e do Windows não foi testada sistematicamente.

### Recursos do computador

A aplicação precisa de espaço livre para armazenar o banco de dados e processar os arquivos recebidos.

Não há requisitos mínimos de RAM, processador ou armazenamento comprovados por testes em diferentes computadores.

Para carteiras grandes, recomenda-se acompanhar o consumo de memória e o tamanho do banco SQLite.

---

# 2. Instalação do Python no Windows

Acesse:

https://www.python.org/downloads/windows/

Instale o Python 3.13.

Caso o instalador apresente a opção **Add Python to PATH**, habilite-a.

Se utilizar o Python Install Manager, poderá instalar a versão pelo PowerShell:

```powershell
py install 3.13
```

Depois de instalar, feche e abra novamente o terminal.

Execute:

```powershell
python --version
```

Ou:

```powershell
py --version
```

O terminal deverá apresentar uma versão do Python.

Se nenhum dos comandos funcionar, verifique a instalação e a configuração do PATH.

### Dependências adicionais

O projeto utiliza módulos da biblioteca padrão, incluindo:

- `sqlite3`
- `csv`
- `json`
- `zipfile`
- `http.server`
- `hashlib`
- `datetime`
- `threading`

**Não há necessidade de executar `pip install` para as dependências identificadas no código da V6.**

Também não é necessário compilar manualmente arquivos Python, HTML ou JavaScript.

---

# 3. Como baixar o projeto

No GitHub:

1. Abra o repositório.
2. Clique em **Code**.
3. Escolha **Download ZIP**.
4. Aguarde o download.
5. Abra a pasta Downloads.
6. Clique com o botão direito no ZIP.
7. Escolha **Extrair tudo**.
8. Abra a pasta extraída.

A estrutura do ZIP fornecido contém uma pasta chamada:

`Antecipe_V6_Regras_Filtros`

Dentro dela estão os arquivos do programa.

Em alguns casos, a extração cria duas pastas com o mesmo nome.

Exemplo:

```text
Downloads/
└── Antecipe_V6_Regras_Filtros/
    └── Antecipe_V6_Regras_Filtros/
        ├── servidor.py
        ├── motor_validacao.py
        ├── index.html
        ├── INICIAR_ANTECIPE.bat
        └── ...
```

O programa deve ser iniciado na pasta que contém `servidor.py`.

---

# 4. Estrutura do projeto

```text
Antecipe_V6_Regras_Filtros/
│
├── .gitignore
├── index.html
├── INICIAR_ANTECIPE.bat
├── LEIA-ME.txt
├── motor_validacao.py
├── patch_v5.py
├── PROMPTS.md
├── README.md
├── resultado_esperado_100k.json
├── servidor.py
├── teste_auditoria_v6.py
├── teste_integracao.py
├── testes_rapidos.py
└── validadores_antecipe.json
```

### Arquivos principais

**servidor.py**

Contém o servidor HTTP, a API local, as operações de importação, autenticação e consultas ao SQLite.

**motor_validacao.py**

Contém a implementação das regras de elegibilidade, dos cálculos de precificação e das funções de comparação com o gabarito.

**index.html**

Contém a interface web, incluindo HTML, CSS e JavaScript.

**INICIAR_ANTECIPE.bat**

Executa o servidor no Windows utilizando o Python disponível.

**validadores_antecipe.json**

Contém as regras financeiras e seus parâmetros.

**resultado_esperado_100k.json**

Contém os resultados de referência para comparação.

**testes_rapidos.py**

Contém verificações básicas do código.

**teste_integracao.py e teste_auditoria_v6.py**

Contêm testes mais amplos. A execução depende das condições e dos arquivos utilizados pelos scripts.

**patch_v5.py**

Arquivo auxiliar incluído no projeto. Não é necessário executá-lo para iniciar normalmente o servidor V6.

---

# 5. Como executar — Método recomendado

## Executar pelo arquivo BAT

Este é o método mais simples no Windows.

1. Abra a pasta que contém `servidor.py`.
2. Localize `INICIAR_ANTECIPE.bat`.
3. Dê dois cliques no arquivo.
4. Uma janela de terminal será aberta.
5. O programa tentará iniciar o servidor.

O arquivo BAT utiliza inicialmente:

```powershell
py -3 servidor.py
```

Se o comando `py` não estiver disponível, tenta:

```powershell
python servidor.py
```

Quando a inicialização funcionar, aparecerá uma mensagem semelhante a:

```text
Antecipe V6 pronto em http://127.0.0.1:8501
```

O código também tenta abrir o navegador automaticamente.

Caso isso não aconteça, acesse manualmente:

http://127.0.0.1:8501

**Mantenha o terminal aberto durante a utilização.**

---

# 6. Como executar pelo PowerShell

Abra o PowerShell do Windows.

Entre na pasta do projeto.

Exemplo para uma extração com duas pastas:

```powershell
cd "$HOME\Downloads\Antecipe_V6_Regras_Filtros\Antecipe_V6_Regras_Filtros"
```

O caminho poderá ser diferente conforme o local onde você salvou o projeto.

Para verificar onde está:

```powershell
pwd
```

Para listar os arquivos:

```powershell
dir
```

Confirme que `INICIAR_ANTECIPE.bat` e `servidor.py` aparecem na lista.

Execute:

```powershell
.\INICIAR_ANTECIPE.bat
```

Se preferir iniciar diretamente pelo Python:

```powershell
python servidor.py
```

Outra possibilidade:

```powershell
py -3 servidor.py
```

Depois acesse:

http://127.0.0.1:8501

---

# 7. Como executar pelo Visual Studio Code

O VS Code é opcional.

Caso deseje utilizá-lo, baixe em:

https://code.visualstudio.com/

Após instalar:

1. Abra o VS Code.
2. Selecione **File → Open Folder**.
3. Escolha a pasta do Antecipe.
4. Clique em **Terminal → New Terminal**.
5. Confirme o diretório atual.

Execute:

```powershell
dir
```

Se aparecer uma subpasta chamada `Antecipe_V6_Regras_Filtros`, mas não aparecer `servidor.py`, entre na subpasta:

```powershell
cd .\Antecipe_V6_Regras_Filtros
```

Confira novamente:

```powershell
dir
```

Quando o arquivo `servidor.py` aparecer, execute:

```powershell
.\INICIAR_ANTECIPE.bat
```

Ou:

```powershell
python servidor.py
```

Abra o endereço local apresentado pelo servidor.

---

# 8. Primeiro acesso

O servidor possui rotas para cadastrar o primeiro administrador e autenticar usuários.

No primeiro acesso, siga as instruções da interface para criar o administrador.

O código exige:

- Nome de usuário com pelo menos 3 caracteres.
- Senha com pelo menos 10 caracteres.

A senha é processada com PBKDF2-HMAC-SHA256 e salt aleatório antes do armazenamento.

Esse mecanismo evita guardar a senha original diretamente no banco, mas não significa que toda a implementação de segurança tenha sido auditada.

As sessões são mantidas em memória no processo do servidor. Isso significa que reiniciar o servidor encerra as sessões existentes.

A aplicação deve ser utilizada localmente e não deve ser exposta diretamente à internet sem revisão de segurança.

---

# 9. Importação de arquivos

A interface permite enviar:

- Arquivos CSV.
- Arquivos JSON.
- Arquivos ZIP contendo CSV ou JSON.

A classificação é feita pelo servidor a partir do conteúdo e da estrutura reconhecida.

### Formato CSV do desafio

O formato fornecido pela Kanastra utiliza:

```text
Separador: ;
Decimal: vírgula
Datas: dd/mm/aaaa
Cabeçalho: primeira linha
Codificação: UTF-8
```

### Importar recebíveis

1. Abra a área de importação.
2. Selecione o CSV ou ZIP contendo os recebíveis.
3. Envie o arquivo.
4. Confira a mensagem de processamento.

### Importar a situação cadastral

Envie também:

`cnpj_situacao_mock.csv`

Essa base é utilizada para consultar a situação cadastral dos sacados durante a validação.

### Limites implementados

O código estabelece:

- Limite de 120 MB por arquivo enviado.
- Até 100 arquivos CSV/JSON dentro de um ZIP.
- Limite agregado de 300 MB de conteúdo descompactado aceito na verificação do ZIP.

Esses limites pertencem à implementação atual e não são garantias de desempenho ou proteção completa contra todos os arquivos maliciosos.

### Arquivos duplicados

O servidor calcula um hash SHA-256 para identificar reimportações do mesmo conteúdo.

Isso reduz a repetição de arquivos idênticos, mas **não garante a detecção de um mesmo título incluído em planilhas diferentes**.

A prevenção completa de dupla cessão de recebíveis ainda necessita de mecanismos adicionais.

---

# 10. Gestão das regras financeiras

O sistema utiliza o JSON:

`validadores_antecipe.json`

Ele contém validadores identificados por código, com campos `ativo` e `parametros`.

O servidor oferece uma API para salvar novas configurações e o painel apresenta opções de edição dos validadores reconhecidos.

### Regras disponíveis na configuração fornecida

| Regra | Configuração inicial |
|---|---|
| CNPJ_SACADO_VALIDO | Ativa |
| SITUACAO_CADASTRAL_SACADO | Ativa; aceita ATIVA |
| TIPO_RECEBIVEL | Ativa; aceita Duplicata e Duplicata de Serviço |
| VALOR_MINIMO | Ativa; mínimo de R$ 100 |
| NAO_VENCIDA | Ativa |
| PRAZO_MAXIMO | Ativa; máximo de 180 dias |
| CONCENTRACAO_MAXIMA_SACADO | Ativa; 10% por raiz de CNPJ |
| PRAZO_MINIMO | Inativa; parâmetro de 30 dias |
| CONCENTRACAO_MAXIMA_CEDENTE | Inativa; parâmetro de 8% |

### Como modificar

1. Abra a área de regras.
2. Selecione um conjunto compatível.
3. Clique na opção de edição.
4. Altere os validadores e seus parâmetros.
5. Salve a configuração.
6. Execute novamente a validação dos recebíveis.

O código cria uma nova versão da configuração no SQLite e registra informações sobre a alteração.

**Atenção:** salvar uma nova configuração não recalcula automaticamente todas as decisões. A revalidação deve ser executada depois.

### Limitação importante

Embora o sistema implemente os validadores conhecidos, ainda existem divergências em relação ao gabarito do desafio.

A implementação atual da concentração utiliza totais de valor nominal agrupados por fundo e pela raiz do CNPJ.

Essa interpretação ainda não foi comprovada como integralmente equivalente à utilizada no resultado esperado.

---

# 11. Como interpretar os resultados

O motor oficial implementado em `motor_validacao.py` pode produzir três situações:

**APROVADO**

O recebível passou pelos validadores ativos, sem impedimentos ou dados faltantes identificados pelo motor.

**BARRADO**

O recebível violou uma ou mais regras ativas.

**PENDENTE**

Não foram identificadas violações conclusivas, mas existem dados insuficientes para completar a análise.

A classificação `PENDENTE` é uma decisão adicional da implementação, utilizada para não tratar ausência de informações como aprovação.

O gabarito do desafio utiliza principalmente `APROVADO` e `BARRADO`.

Assim, a existência de pendências é uma das diferenças que precisam ser consideradas na comparação.

### Motivos de recusa

O sistema registra os códigos das regras violadas.

A interface apresenta esses motivos para consulta.

A qualidade e a clareza das explicações devem ser verificadas na demonstração com os arquivos reais.

---

# 12. Cálculo da antecipação

A configuração oficial fornecida utiliza:

```text
Método: DESCONTO_SIMPLES
Taxa mensal: 2%
Base de dias: 30
```

O motor calcula:

```text
Valor estimado =
Valor nominal × (1 - taxa mensal × prazo / base_dias)
```

A taxa é convertida de percentual para decimal.

O prazo utilizado pelo motor é a diferença entre a data de aquisição e a data de vencimento.

### Exemplo

```text
Valor nominal: R$ 1.000,00
Taxa mensal: 2%
Prazo: 30 dias
Base: 30 dias

Desconto: R$ 20,00
Valor estimado: R$ 980,00
```

O código utiliza `Decimal` para o cálculo e arredondamento monetário, mas a origem dos valores importados e a equivalência financeira completa ainda exigem verificação.

Para títulos não aprovados, o valor antecipável é definido como zero.

O valor calculado é uma estimativa com base nas regras configuradas, não uma proposta financeira contratual.

---

# 13. Dashboard, consultas e filtros

A interface possui consultas por API e exibe os dados em tabelas e indicadores.

Os filtros implementados incluem critérios como:

- Fundo.
- Tipo de recebível.
- Situação cadastral.
- Status da validação.
- Motivo de recusa.
- Valor mínimo e máximo.
- Período de aquisição.
- Dados de identificação do cedente.

O código também disponibiliza pesquisa e paginação.

A consulta de recebíveis é realizada pelo SQLite, sem transferir necessariamente todo o conteúdo da carteira para uma única tabela do navegador.

Isso melhora a organização das consultas, mas o desempenho com milhões de registros depende dos filtros, índices, armazenamento e capacidade do computador.

---

# 14. API local

O servidor implementa rotas HTTP para comunicação com o frontend.

Algumas rotas disponíveis são:

| Método | Rota | Finalidade |
|---|---|---|
| GET | `/api/config` | Consultar configuração inicial e sessão |
| POST | `/api/setup` | Criar administrador |
| POST | `/api/login` | Autenticar |
| POST | `/api/logout` | Encerrar sessão |
| POST | `/api/upload` | Importar arquivos |
| GET | `/api/records` | Consultar recebíveis |
| GET | `/api/stats` | Consultar indicadores |
| GET | `/api/regras` | Consultar regras |
| GET | `/api/regras/detalhes` | Consultar um conjunto específico |
| POST | `/api/regras/salvar` | Salvar nova configuração |
| POST | `/api/avaliar` | Executar validação |
| GET | `/api/conferencia` | Comparar com o gabarito |
| GET | `/api/auditoria` | Obter informações de auditoria |
| GET | `/api/divergencias.csv` | Exportar divergências |

As rotas operacionais exigem sessão autenticada.

O upload recebe bytes do arquivo e utiliza o nome informado na URL.

A existência dessas rotas foi confirmada no código. Isso não equivale a uma auditoria completa de segurança ou a um teste de integração externo de todas elas.

---

# 15. Banco de dados

O servidor utiliza SQLite.

O código cria tabelas para:

- Arquivos importados.
- Recebíveis.
- Situação cadastral.
- Conjuntos de regras.
- Pagamentos.
- Arquivos de referência.
- Usuários.
- Avaliações.
- Conteúdo original de arquivos.
- Histórico de alterações nas regras.

O banco é persistente em arquivo local.

O servidor utiliza o modo WAL do SQLite.

### Como fazer backup

1. Encerre o Antecipe.
2. Confirme que o processo do servidor foi finalizado.
3. Copie o banco de dados para uma pasta segura.
4. Preserve a cópia antes de atualizar o sistema.

Não publique bancos de dados reais em repositórios públicos.

Não exclua arquivos auxiliares do SQLite enquanto o banco estiver sendo utilizado.

---

# 16. Como executar os testes

O projeto contém três arquivos relacionados a testes:

```text
testes_rapidos.py
teste_integracao.py
teste_auditoria_v6.py
```

Para executar os testes rápidos:

```powershell
python testes_rapidos.py
```

Para os outros scripts:

```powershell
python teste_integracao.py
```

```powershell
python teste_auditoria_v6.py
```

### Atenção às dependências de dados

O script `teste_integracao.py` faz referência a arquivos de teste localizados em `/mnt/data`, um caminho utilizado no ambiente de desenvolvimento.

Esse caminho não existe normalmente em computadores Windows.

Portanto, **o teste de integração poderá falhar em outro computador até que seus caminhos sejam adaptados para a localização real dos arquivos**.

Antes de usar o resultado como evidência de qualidade, confira:

- Se os arquivos de entrada foram encontrados.
- Se o banco temporário foi criado.
- Se todas as validações foram executadas.
- Se o programa terminou sem exceções.
- Se o resultado foi realmente comparado com o gabarito.

A execução de um script sem erro não garante, por si só, precisão financeira.

---

# 17. Resultados do desafio e limitações

O material fornecido para o hackathon contém aproximadamente 100 mil recebíveis.

O gabarito compartilhado apresenta:

| Situação esperada | Quantidade |
|---|---:|
| Aprovados | 85.215 |
| Barrados | 15.339 |
| Total | 100.554 |

Em testes anteriores da V6, foram relatadas divergências entre o motor e o gabarito.

A atualização de regras e filtros não foi acompanhada de uma nova comprovação de concordância integral.

Portanto:

**Não é correto afirmar que a versão atual reproduz todas as 85.215 aprovações.**

A interpretação de concentração, situação cadastral e critérios temporais ainda deve ser investigada.

O sistema também não possui comprovação de desempenho completo para 10 milhões de recebíveis financeiros com todas as regras e campos.

---

# 18. Como encerrar

No terminal em que o servidor está executando, pressione:

`Ctrl + C`

Aguarde o encerramento.

Fechar apenas a aba do navegador não encerra necessariamente o processo Python.

---

# 19. Como executar novamente

Depois da instalação inicial, normalmente basta:

1. Abrir a pasta do projeto.
2. Executar `INICIAR_ANTECIPE.bat`.
3. Acessar `http://127.0.0.1:8501`.
4. Fazer login.

Os dados persistem se o arquivo SQLite utilizado anteriormente for preservado.

Se você executar outra cópia do projeto em uma pasta diferente, ela poderá utilizar um banco de dados diferente.

---

# 20. Solução de problemas

## Python não reconhecido

Execute:

```powershell
python --version
```

Ou:

```powershell
py --version
```

Se nenhum funcionar, verifique a instalação e o PATH.

## Pasta não encontrada

Execute:

```powershell
pwd
```

Depois:

```powershell
dir
```

Localize a pasta correta antes de tentar iniciar o servidor.

## Arquivo BAT não encontrado

Se o PowerShell apresentar erro ao executar:

```powershell
.\INICIAR_ANTECIPE.bat
```

Verifique se está na pasta que contém esse arquivo.

Se houver outra subpasta com o mesmo nome, entre nela com `cd`.

## Arquivo servidor.py não encontrado

Execute:

```powershell
Get-ChildItem -Recurse -Filter servidor.py
```

Use o resultado para localizar a pasta principal.

## Porta 8501 ocupada

O servidor utiliza a porta fixa 8501.

Se outra aplicação estiver utilizando essa porta, a V6 informa que ela está ocupada e não inicia uma nova instância nessa mesma porta.

Para verificar o uso da porta:

```powershell
netstat -ano | findstr :8501
```

Não encerre processos desconhecidos sem confirmar sua finalidade.

## A página não abre

Confirme que o servidor iniciou.

Acesse:

http://127.0.0.1:8501

Se o terminal apresentar erros, resolva-os antes de tentar acessar novamente.

## Os recebíveis não aparecem

Verifique:

1. Se o upload foi concluído.
2. Se o arquivo foi reconhecido.
3. Se os dados foram inseridos.
4. Se existem filtros ativos.
5. Se a validação foi executada.
6. Se o servidor está utilizando o banco correto.

Se necessário, consulte o terminal para identificar erros.

---

# 21. Segurança e utilização responsável

O Antecipe V6 é um protótipo local.

Existem medidas implementadas, como hash de senha, autenticação por sessão e consultas SQL parametrizadas em partes relevantes do sistema.

Entretanto, essas medidas não comprovam segurança completa.

Não foram demonstrados testes abrangentes de:

- Resistência a ataques de autenticação.
- Segurança de todos os endpoints.
- Controle de acesso corporativo.
- Exposição pública do servidor.
- Recuperação de desastres.
- Concorrência sob grande volume de usuários.
- Conformidade com exigências regulatórias financeiras.

Não utilize o sistema para autorizar operações reais sem auditoria adicional.

---

# 22. Resumo rápido

### Instalação inicial

Instale o Python 3 e extraia o projeto.

### Abrir a pasta

No PowerShell:

```powershell
cd "CAMINHO_REAL_DA_PASTA_DO_PROJETO"
```

### Iniciar

```powershell
.\INICIAR_ANTECIPE.bat
```

Ou:

```powershell
python servidor.py
```

### Abrir a plataforma

http://127.0.0.1:8501

### Encerrar

`Ctrl + C`

### Executar testes rápidos

```powershell
python testes_rapidos.py
```

---

# 23. Checklist de instalação

- [ ] Python 3 instalado.
- [ ] Comando `python` ou `py` funcionando.
- [ ] Projeto extraído do ZIP.
- [ ] Pasta correta identificada.
- [ ] `servidor.py` presente.
- [ ] `motor_validacao.py` presente.
- [ ] `index.html` presente.
- [ ] `INICIAR_ANTECIPE.bat` presente.
- [ ] `validadores_antecipe.json` presente.
- [ ] Servidor iniciado sem erro.
- [ ] Navegador acessando `127.0.0.1:8501`.
- [ ] Administrador configurado.
- [ ] Arquivos de recebíveis importados.
- [ ] Cadastro de CNPJs importado.
- [ ] Regras verificadas.
- [ ] Validação executada.
- [ ] Resultados consultados.
- [ ] Divergências financeiras consideradas.
- [ ] Banco de dados preservado.
- [ ] Testes executados e seus resultados conferidos.

---

# 24. Relatório técnico resumido

**Projeto:** Antecipe V6 — Regras e Filtros

**Objetivo:** centralizar a importação, análise e simulação de antecipação de recebíveis.

**Tecnologias:** Python, HTML, CSS, JavaScript, JSON e SQLite.

**Arquitetura:** aplicação web local com servidor Python e banco de dados embarcado.

**Decisões principais:** utilização da biblioteca padrão do Python, persistência SQLite, regras configuráveis, registro de histórico e paginação de consultas.

**Funcionalidades implementadas:** importação, autenticação, consulta, validação, precificação, edição de regras, auditoria e exportação de divergências.

**Limitações principais:** divergência com o gabarito financeiro, prevenção incompleta de duplicidade de títulos entre arquivos e ausência de testes completos de segurança e escala.

**Histórico de utilização de IA:** disponível em `PROMPTS.md`.

---

## Aviso final

O Antecipe V6 foi desenvolvido como demonstração técnica para o Hackathon Antecipe.

O código implementa os principais componentes solicitados pelo desafio, mas **não há comprovação de que todos os requisitos estejam atendidos sem falhas**.

As funcionalidades financeiras, de segurança e de prevenção de duplicidade exigem testes e revisões adicionais antes da utilização em ambiente de produção.
