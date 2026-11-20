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

## Orçamento de tokens (decisão de 20/11/2026)

A primeira versão usava três subagentes em paralelo por vinho (cerca de 350 mil tokens por garrafa). Agora:

- **Um único subagente por vinho**, modelo Sonnet (`model: "sonnet"`), no máximo 12 buscas e 4 aberturas de página.
  A sessão principal só consolida e grava.
- **Sites que bloqueiam** (nunca abrir; usar o trecho da busca e marcar "via busca, não conferido"): Wine Enthusiast,
  James Suckling, Wine Advocate, Decanter (nota em paywall), Wine Spectator, CellarTracker, Wine-Searcher, Wine.com,
  Mercado Livre, Mistral, Grand Cru, World Wine. Descorchados, Pão de Açúcar, Evino: abrir.
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
  "Já dá, ápice a partir de X" (janela de 6+ anos, mais de 1 ano antes da faixa), "No ápice" (dentro da faixa),
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
- `status` (pesquisas): `pendente` → `solicitada` → `verificada`.
- Fotos tiradas no app já chegam reduzidas (≤1600 px); as que eu subo, ≤1200 px.
