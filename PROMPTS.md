# Registro de prompts — Antecipe

Este documento reúne os pedidos e orientações utilizados no desenvolvimento iterativo do **Antecipe**, um protótipo local para importação, análise e validação de recebíveis. O objetivo é documentar o uso de IA no projeto, facilitar sua reprodução e deixar transparentes os limites das implementações.

> **Transparência:** as descrições abaixo são **resumos fiéis das solicitações da conversa**, não transcrições literais de todos os prompts. Os trechos indicados como *prompt para Codex* representam tarefas propostas ao Codex; isso não comprova que tenham sido executadas. Resultados citados são relatos de testes nas etapas de desenvolvimento e não garantem comportamento da versão atual.

## Ferramentas envolvidas

- **ChatGPT (OpenAI):** planejamento, propostas de implementação, documentação, orientação de execução e análise de resultados relatados.
- **Codex (OpenAI):** foram preparados prompts de auditoria e documentação para possível uso no editor; o registro não pressupõe sua execução.
- **VS Code / PowerShell / Python:** ambiente utilizado para abrir arquivos e executar localmente o programa.

## Histórico de solicitações

| Etapa | Prompt / solicitação (resumo) | Objetivo e entregável | Observações |
|---|---|---|---|
| 1 — Conceito | Receber vários CSVs de recebíveis, pagamentos e regras, armazenar tudo em banco de dados e mostrar dados, filtros, gráficos e motivos de negação. | Definir o escopo funcional do Antecipe. | Regras externas e rastreabilidade eram requisitos desde o início. |
| 2 — Protótipo | Criar interface e importar arquivos ZIP/CSV/JSON com dados centralizados no SQLite. | Protótipo Python com interface web. | Importação e classificação financeira são capacidades distintas. |
| 3 — Interface V2 | Reconhecer automaticamente o tipo de arquivo, melhorar filtros e gráficos e adotar aparência inspirada em plataforma financeira profissional. | Importação sem classificação manual, dashboard e filtros. | Inspiração visual não implica vínculo com marca de terceiros. |
| 4 — Autenticação V3 | Melhorar a navegação lateral, criar login e integrar o JSON de validadores. | Login e navegação, com suporte ao arquivo de regras. | Leitura/armazenamento do JSON não prova execução correta das regras. |
| 5 — Correção da importação V4 | Corrigir caso em que arquivos enviados não apareciam nos indicadores e na tabela; atualizar dados após upload. | Importação mais direta, persistência e atualização visual. | Verificar em cada entrega a gravação e a consulta do banco. |
| 6 — Execução independente | Reduzir dependências e executar por um arquivo BAT em Windows, sem Streamlit. | Servidor Python, frontend HTML/JS e SQLite. | Ainda requer Python instalado; não é um `.exe` autossuficiente. |
| 7 — Escala | Testar aproximadamente 10 milhões de registros e melhorar desempenho de filtros e consultas. | Avaliação de carga, paginação e índices. | Teste sintético de tabela reduzida não equivale a 10 milhões de títulos completos. |
| 8 — Regras financeiras | Implementar os validadores do JSON, executar regras por recebível, registrar todas as reprovações e precificar antecipação. | Motor de validação e cálculo de desconto simples. | Exige comparação com o gabarito e investigação das divergências. |
| 9 — V5 | Corrigir falhas apontadas: regras não executadas, divergência nas 85.215 aprovações, precificação e explicações das recusas. | Versão V5 para avaliação. | Resultado esperado não deve ser forçado; decisão pendente é diferente de aprovada. |
| 10 — Execução | Explicar como executar no PowerShell e no VS Code, inclusive erros de pasta e Python. | Comandos de inicialização e solução de problemas. | O comando BAT deve ser executado dentro da pasta correta. |
| 11 — Auditoria Codex | Preparar um prompt para revisar todos os arquivos, testar integração, segurança, importação, regras e desempenho. | Instrução para auditoria automatizada. | Não há comprovação neste registro de que o Codex executou a auditoria. |
| 12 — Documentação | Criar README detalhado para instalação em outro computador Windows, com dependências, comandos, operação e troubleshooting. | Manual de instalação e execução. | Documentação deve refletir o comportamento real do código. |
| 13 — Registro de prompts | Registrar os pedidos feitos à IA de modo que o histórico possa ser versionado no GitHub. | Este arquivo `PROMPTS.md`. | Atualizar a cada nova mudança relevante. |

## Configuração de referência recebida para as regras

O usuário forneceu uma configuração JSON destinada ao fundo **ANTECIPE FIDC**, com as seguintes regras:

| Regra | Configuração informada | Ativa? |
|---|---|---|
| `CNPJ_SACADO_VALIDO` | Verificar validade do CNPJ do sacado | Sim |
| `SITUACAO_CADASTRAL_SACADO` | Situações aceitas: `ATIVA` | Sim |
| `TIPO_RECEBIVEL` | `Duplicata` e `Duplicata de Serviço` | Sim |
| `VALOR_MINIMO` | R$ 100,00 | Sim |
| `NAO_VENCIDA` | Não vencida | Sim |
| `PRAZO_MAXIMO` | 180 dias | Sim |
| `CONCENTRACAO_MAXIMA_SACADO` | 10% por `RAIZ_CNPJ` | Sim |
| `PRAZO_MINIMO` | 30 dias | **Não** |
| `CONCENTRACAO_MAXIMA_CEDENTE` | 8% | **Não** |

**Precificação configurada:** método `DESCONTO_SIMPLES`, taxa mensal de **2,0%**, base de **30 dias**. Uma representação típica do cálculo é `valor_nominal × (1 - 0,02 × prazo_em_dias / 30)`, mas políticas de arredondamento, data de referência e limites precisam ser verificadas no código e nos requisitos do desafio.

As regras devem ser **carregadas de arquivo externo**, respeitando o campo `ativo`; não devem ser substituídas por valores fixos escondidos no código.

## Conjunto de teste e critérios de conferência

- Estoque de referência: **100.554 recebíveis**.
- Base cadastral fornecida: **3.041 registros de CNPJ**.
- Gabarito de referência informado: **85.215 aprovados** e **15.339 barrados**.
- A igualdade apenas das contagens globais não basta: é necessário comparar, **registro por registro**, ID, status e todos os motivos `barrado_por`.
- Falhas ou ausência de informação cadastral devem ser explicitadas; não se deve inventar dados nem alterar artificialmente o resultado para bater com o gabarito.
- A precificação só deve ser apresentada como decisão financeira confirmada quando seus parâmetros, entradas e critérios de arredondamento forem validados.

## Prompt de auditoria para reutilização (versão consolidada)

> Analise o projeto Antecipe da pasta aberta no VS Code, incluindo `servidor.py`, `motor_validacao.py`, `index.html`, `INICIAR_ANTECIPE.bat`, `validadores_antecipe.json`, `resultado_esperado_100k.json` e `testes_rapidos.py`. Verifique a inicialização em Windows, a detecção automática e a importação transacional de CSV/ZIP/JSON, a persistência no SQLite, o login, os filtros, a paginação e os gráficos. Implemente e teste somente as regras descritas no JSON externo, preservando as regras inativas; registre os motivos de cada recusa e o cálculo de desconto simples de 2% ao mês. Compare decisões e motivos por recebível com o gabarito, fornecendo contagens, divergências e exemplos reprodutíveis. Faça testes de desempenho com amostra real e carga sintética, identificando claramente cada cenário. Corrija falhas identificadas sem apagar dados existentes. Ao final, documente os comandos exatos para executar em Windows e relate os testes realmente executados e limitações pendentes. Não declare sucesso sem evidência.

## Como manter este registro

Ao usar IA para mudar o projeto, acrescente uma entrada com:

1. **Data e ferramenta utilizada**.
2. **Solicitação original** ou resumo marcado como tal.
3. **Arquivos alterados**.
4. **Testes executados** e respectivos resultados verificáveis.
5. **Limitações conhecidas e próximos passos**.

Exemplo:

```markdown
### AAAA-MM-DD — Ajuste de filtros
- Ferramenta: ChatGPT / Codex
- Prompt: "Adicionar filtro por situação e vencimento, preservando paginação."
- Arquivos alterados: `index.html`, `servidor.py`
- Testes realizados: [comandos e resultados]
- Limitações: [informar ou escrever "nenhuma identificada nos testes executados"]
```

## Uso responsável de IA

Código e sugestões gerados com ajuda de IA podem conter erros. Todas as decisões de aprovação de recebíveis, cálculos financeiros e rotinas de segurança devem ser revisados e testados por responsáveis humanos antes do uso em operações reais. Evite publicar dados pessoais, dados financeiros sensíveis, credenciais e bancos de produção neste repositório.
