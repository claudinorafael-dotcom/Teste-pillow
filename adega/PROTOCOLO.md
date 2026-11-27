# Minha Adega — protocolo de pesquisa automática

Página: https://claude.ai/artifact/BMNmyWd7UrrTx3y9emFYwS (privada, só o dono abre).
Banco: coleções `vinhos`, `consumos` e `pesquisas` (ArtifactData). Fotos: assets do artifact (`fotoId` → `/_blob/<id>`).

## Princípios de trabalho (pedido do Rafael)

- Sempre que houver uma forma melhor de fazer algo do que a que ele está usando, dizer isso de forma direta,
  com a recomendação e o porquê, antes de executar o que foi pedido.
- Nunca inventar notas ou preços: `null` quando não encontrado. Dizer de onde veio cada número.
- Tudo em português.

## Quando a sessão do Claude é acordada

1. Pela tarefa sob demanda "Adega: pesquisa sob demanda" (trig_01YRvMoRnB9F7ygo8BX57J46), disparada pelo próprio app
   via conector Claude Code Remote (`fire_trigger`) a cada garrafa ou pedido novo. É o caminho principal: cada disparo
   nasce numa sessão limpa que carrega só este protocolo (prompt autossuficiente na tarefa). Sem agendamento por relógio.
2. Como reserva, por um comentário "Pesquisar avaliações…" ou "Avaliar compra…" (`comments.sendToClaude`), que acorda
   a conversa que construiu a página.
Em qualquer caso, consultar **todos** os documentos pendentes de `vinhos` e `pesquisas`, não só o citado.

## Fonte primária: Wine-Searcher via Apify (decisão de 24/11/2026)

Testado com os 16 rótulos: 16 itens em 30 s, 14 com página, 10 com notas por crítico, custo US$ 0,045. Entra como
**primeiro passo** da pesquisa de notas e preço; a busca na web vira complemento.

- Chamada (o token da Apify está salvo no ambiente e o proxy o injeta; não enviar cabeçalho de autorização):
  ```
  POST https://api.apify.com/v2/acts/abotapi~wine-searcher-scraper/run-sync-get-dataset-items?timeout=120
  Content-Type: application/json
  {"inputType":"auto","wineNames":["<produtor> <vinho> <safra>"],"fetchOffers":false,"fetchReviews":false,"targetCurrency":"USD","maxItems":20,"proxy":{"useApifyProxy":true}}
  ```
  Usar o nome sem parênteses; para linhas, o nome da linha + uva (ex.: "San Pedro 1865 Selected Vineyards Carmenere 2021").
- Resposta por vinho: `wineName, vintage, criticScores {crítico: nota}, score (agregado), criticReviewsCount, avgPrice (USD),
  labelImageUrl, wineSearcherUrl`. Se `wineName` começar com "Best local price", não houve página: tratar como não encontrado.
- Mapa para `ficha.notas`: James Suckling→suckling; Robert Parker / Wine Advocate→parker; Wine Spectator→spectator;
  Decanter e Decanter World Wine Awards→decanter; Vinous→vinous; Tim Atkin→atkin; Patricio Tapia - Descorchados→descorchados;
  Wine Enthusiast→enthusiast; Revista Adega→adega; CellarTracker→cellartracker. Falstaff e outros só em `fontes`.
- Gravar `ficha.wineSearcherUrl` (o app mostra o botão "Ver na Wine-Searcher").
- Falha vista em 24/11 (12h05): o ator terminou com "Could not load any results page / time budget for opening a session
  exhausted", ou seja, a Wine-Searcher recusou os IPs de datacenter da Apify por alguns minutos. Regra: esperar 60 s e repetir
  uma vez com `"proxy":{"useApifyProxy":true,"apifyProxyGroups":["RESIDENTIAL"]}`; se falhar de novo, seguir sem a Apify e
  anotar em `fontes`. Enviar só os campos listados acima (a sessão daquele dia copiou "urls"/"lwins" de exemplo do ator).
  Para o Saint Felicien Rosé 2022 o resultado real era "sem página", então nada foi perdido.
- Limite do método: Suckling, Parker e Vinous ficam ocultos na Wine-Searcher (só assinantes), então o `criticReviewsCount`
  costuma ser maior que o nº de notas visíveis. Esses três continuam vindo da busca na web ou das capturas do Rafael.
- Fonte na ficha: "Wine-Searcher via Apify (safra X, data): crítico nota, …; agregado N de M críticos; preço médio US$ P".

## Catálogo X-Wines (27/11/2026)

Catálogo offline de 100 mil vinhos publicado com o app (detalhes em `adega/XWINES-TESTE.md`). Quando o documento tem o
campo `xw`, o Rafael confirmou o vinho no catálogo: a nota de comunidade vem dele e a pesquisa NÃO busca o Vivino
(`ficha.notas.vivino` fica null). Nunca alterar `xw`. Ao republicar a página, não remover os arquivos `xw/`.

## Custo por garrafa, versão 26/11/2026

Medição antes: 70 a 100 mil tokens por garrafa (sessão nova por garrafa, listagem do banco inteiro, subagente Sonnet com
8 buscas e aberturas de página). Mudanças aplicadas, mantendo o subagente de busca que o Rafael valoriza:

1. **Um lote por sessão**: o app dispara a tarefa no máximo uma vez a cada 10 min (`adega_fire_last` no aparelho); dentro
   da janela agenda um disparo adiado; ao abrir, se houver pendência com mais de 15 min, dispara uma vez. A sessão trata tudo.
2. **Marcador `pendente: true`** (campo de primeiro nível) em `vinhos` e `pesquisas` ao criar; a sessão consulta só
   `where pendente == true` e grava `pendente: false` ao terminar. Sem listar o banco inteiro.
3. **Ficha reaproveitada**: garrafa igual (produtor, vinho e safra normalizados) já pesquisada → o app copia a ficha e não
   pede pesquisa (`pesquisa.via: "copia"`).
4. **Subagente mais barato**: um agente por lote (até 8 vinhos), modelo Haiku, no máximo 4 buscas por vinho e nenhuma
   abertura de página, só para o que a Apify não traz (Suckling, Parker, Vinous, Vivino pelo trecho, preço no Brasil),
   resposta em JSON. Pula Suckling/Parker quando a Apify já trouxe.
5. **Vivino só pelo trecho da busca**: as páginas passaram a responder 403 depois do volume de 26/11.

Meta: 15 a 25 mil tokens por garrafa.

## Orçamento de tokens (decisão de 20/11/2026)

A primeira versão usava três subagentes em paralelo por vinho (cerca de 350 mil tokens por garrafa). Agora:

- **Um único subagente por vinho**, modelo Sonnet (`model: "sonnet"`), no máximo 8 buscas e 4 aberturas de página
  (reduzido de 12 em 24/11, porque a Apify já cobre a maior parte dos críticos e o preço de referência).
  A sessão principal só consolida e grava.
- **Sites que bloqueiam** (nunca abrir; usar o trecho da busca e marcar "via busca, não conferido"): Wine Enthusiast,
  James Suckling, Wine Advocate, Decanter (nota em paywall), Wine Spectator, CellarTracker, Wine-Searcher, Wine.com,
  Mercado Livre, Mistral, Grand Cru, World Wine. Descorchados, Pão de Açúcar, Evino: abrir.
- **Vivino, limites** (26/11): depois de muitas aberturas num dia, as páginas passam a responder 403 para todos. Nesse caso
  usar a média do rótulo que aparece no trecho da busca, marcada "média do rótulo, via busca, não conferido". O raspador de
  Vivino da Apify (mrbridge) foi bloqueado pelo classificador de segurança da sessão; não insistir nele.
- **Limite de uso da conta** (26/11): a tarefa sob demanda falhou com USAGE_LIMIT_REACHED e 8 garrafas ficaram sem ficha; a
  sessão principal fez a pesquisa em modo reduzido (Apify + busca, sem subagente). Quando o limite voltar, as próximas
  garrafas seguem o fluxo normal. Conferir `last_run` da tarefa quando houver pendências antigas.
- **Vivino, o que funciona** (aprendido em 20/11 com o Cecchi e o 1865): a busca de texto do site não carrega. Em vez disso,
  (1) WebSearch restrito a `vivino.com` com o nome do vinho para achar a URL `…/w/<número>`; (2) WebFetch dessa URL com
  `?year=<safra>`: a página abre e mostra nota média da safra e nº de avaliações. Nunca gravar "não encontrado no Vivino"
  sem ter feito os dois passos.
- **Críticos pagos**: uma busca por crítico (vinho + safra + nome do crítico); lojas e agregadores costumam expor a nota.
  O Rafael também pode mandar capturas do Wine-Searcher, que mostra Suckling/Atkin/Descorchados por safra; aceitar como fonte
  ("via Wine-Searcher, captura do Rafael").
- **O celular não gera mais ficha**: o app só lê o rótulo (modelo padrão) e pede a pesquisa. A ficha completa
  (resumo, estilo, uvas, vinificação, janela, harmonização, notas, preço) é escrita pela pesquisa. Há um botão
  "Ficha provisória (sem pesquisa)" na garrafa, modelo padrão, só para emergência.
- Sem atalho por perfil de vinho: todas as fontes são buscadas para toda garrafa (pedido do Rafael).

O que o subagente pede, numa única rodada: (a) notas da safra exata ou vizinhas em Suckling (`suckling`),
Wine Advocate (`parker`), Wine Spectator (`spectator`), Decanter (`decanter`), Vinous (`vinous`), Tim Atkin (`atkin`),
Descorchados (`descorchados`), Wine Enthusiast (só em `fontes`); (b) Vivino (`vivino`, 1–5, também produtor + uva) e
CellarTracker (`cellartracker`); (c) preço no Brasil (loja, R$, mês/ano) e no exterior; (d) produtor, uvas, vinificação,
janela publicada; (e) imagem do rótulo só se `fotoId` vazio.

## Para cada vinho pendente em `vinhos`

Gravar com `ArtifactData update` (pinar `if_version`) a ficha **completa** (o celular não a gera mais):
- `ficha.resumo`, `estilo`, `uvas`, `vinificacao`, `estadoHoje`, `safraComentario`, `decantar`, `temperatura`,
  `harmonizacao`, `confianca`, `observacoes`, `atualizadoEm`,
- `ficha.notas` (null onde não houver), `ficha.fontes` (lista "Fonte nota (safra)"),
- `ficha.precoEstimado` ("R$ x a y (loja, mês/ano)"),
- `ficha.janelaInicio/janelaFim/apice` (preferir janela de crítico) e `ficha.apiceInicio/apiceFim`: faixa de 3 anos em que
  o vinho deve estar no melhor (de um crítico quando houver; senão ápice ±1). O app mostra a faixa na barra e usa:
  "Já dá, ápice a partir de X" (janela de 6+ anos e ainda antes da faixa; desde 26/11 sem a folga de 1 ano, a pedido do
  Rafael: quem ainda vai melhorar conta como Guardar), "No ápice" (dentro da faixa; com 7+ anos de janela pela frente o
  card mostra "sem pressa, até X", porque o vinho se mantém mas não melhora),
  "Pronto, após o ápice" (depois da faixa). Uma faixa é mais honesta que um ano único, que seria precisão falsa.
- `ficha.verificadaEm` (ISO), `pesquisa: {status:"feita", feitaEm}`.
Se já houver ficha, não sobrescrever `resumo`, `harmonizacao`, `decantar` a menos que estejam errados.
Corrigir `produtor`/`uvas` do documento quando a leitura do rótulo tiver errado (ex.: Barbanera lido como Barbera).
Foto: baixar para o scratchpad em pasta própria, reduzir a ≤1200 px, subir com `Artifact publish asset:true`, gravar o `id` em `fotoId`.
Se houver `pesquisa.threadId`, responder no thread (ArtifactComments) em 3 a 5 linhas (notas, janela, preço) e resolver.

## Pedidos "Avaliar compra: … Documento pesquisas/<id>"

Vêm da aba Pesquisa. O documento tem `produtor, vinho, safra, precoPedido, loja, fotoId`. Pesquisar do mesmo modo e gravar:
- `verificada`: `{notas:{…}, precoMercado:"R$ x a y (loja, data)", precoJusto:"R$ x a y", veredito:"vale|ressalva|nao",
  titulo, justificativa (3 a 5 frases: preço pedido x mercado, safra, alternativas), alternativas, janela, fontes:[…], verificadaEm}`
- `status: "verificada"`.
Critério: "vale" se igual ou abaixo do mercado com boas notas; "ressalva" se até ~20% acima ou safra fraca;
"nao" acima disso ou com alternativa claramente melhor pelo mesmo preço.
Responder no thread com o veredito em 3 a 5 linhas e resolver.

## Convenções

- `pesquisa.status` (vinhos): `pendente` → `solicitada` (comentário enviado) → `feita`.
- `status` (pesquisas): `pendente` → `solicitada` → `verificada`. "Remover da lista" no app só marca `arquivada: true`
  (o documento continua no banco, para consulta futura); ao tratar pendências, ignorar documentos arquivados.
- `adega/dados/vinhos.json` e `adega/dados/pesquisas.json`: cópias do banco feitas pela sessão principal de tempos em tempos.
- Fotos tiradas no app já chegam reduzidas (≤1600 px); as que eu subo, ≤1200 px.

## Nota de qualidade (app, 24/11/2026)

Calculada na hora pelo app a partir de `ficha.notas`, não gravada no banco:
- média dos críticos em escala 100 (suckling, parker, spectator, decanter, vinous, atkin, descorchados, enthusiast, adega)
  puxada para 89 por uma nota fictícia: (soma + 89) / (n + 1), para uma nota isolada não valer como três;
- comunidade: só o Vivino, convertido (88 + (nota − 4) × 15; 4,0→88, 4,5→95). Decisão do Rafael em 26/11: o Vivino já é
  a grande comunidade; CellarTracker saiu da conta e dos chips do card (continua na ficha quando a Apify trouxer);
- qualidade = 70% críticos + 30% Vivino; só críticos quando não há Vivino; sem nenhum crítico, o Vivino convertido é
  puxado pela metade para 88, para que vinho só com nota de comunidade não passe na frente dos avaliados;
- faixas: ≥95 Excepcional, ≥92 Excelente, ≥89 Muito bom, ≥86 Bom, abaixo Simples;
- confiança: alta com 3+ críticos, média com 1 ou 2, baixa só com comunidade.
Aparece como chip "Q" no card, na seção Notas da ficha e na ordenação "qualidade (notas)".
