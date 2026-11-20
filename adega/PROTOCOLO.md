# Minha Adega — protocolo de pesquisa automática

Página: https://claude.ai/artifact/BMNmyWd7UrrTx3y9emFYwS (privada, só o dono abre).
Banco: coleções `vinhos`, `consumos` e `pesquisas` (ArtifactData). Fotos: assets do artifact (`fotoId` → `/_blob/<id>`).

## Princípios de trabalho (pedido do Rafael)

- Sempre que houver uma forma melhor de fazer algo do que a que ele está usando, dizer isso de forma direta,
  com a recomendação e o porquê, antes de executar o que foi pedido.
- Nunca inventar notas ou preços: `null` quando não encontrado. Dizer de onde veio cada número.
- Tudo em português.

## Quando a sessão do Claude é acordada

1. Por um comentário "Pesquisar avaliações…" ou "Avaliar compra…" vindo da página (`comments.sendToClaude`), ou
2. Pela tarefa agendada "Adega: varredura de pesquisas pendentes" (a cada 4 h, sessão nova, prompt autossuficiente).
Em qualquer caso, consultar **todos** os documentos pendentes de `vinhos` e `pesquisas`, não só o citado no comentário.

## Pesquisa em paralelo (modo padrão)

Para cada vinho, disparar três subagentes ao mesmo tempo (Agent, `run_in_background: true`) e só depois consolidar:

| Agente | O que busca | Fontes |
|---|---|---|
| **críticos** | nota da safra exata; se só houver safras vizinhas, dizer isso; janela de consumo publicada | James Suckling (`suckling`), Wine Advocate/Parker (`parker`), Wine Spectator (`spectator`), Decanter (`decanter`), Vinous/Galloni/Neal Martin (`vinous`), Tim Atkin (`atkin`), Descorchados (`descorchados`); também Jancis Robinson, Falstaff, Jeb Dunnuck como apoio |
| **comunidade** | nota e nº de avaliações | Vivino (`vivino`, 1–5; buscar também por produtor + uva, o Vivino às vezes omite o nome da linha), CellarTracker (`cellartracker`, média) |
| **mercado** | preço no Brasil (faixa, loja, mês/ano) e, só se `fotoId` vazio, uma imagem do rótulo | Mistral, Grand Cru, World Wine, Evino, Wine.com.br, Magazine Luiza, Oba; preço no exterior como referência |

Chaves entre parênteses são as de `ficha.notas` / `verificada.notas`.
Sites que bloqueiam (Vivino direto, Wine-Searcher): usar o que a busca mostra e marcar "via agregador, não conferido".

## Para cada vinho pendente em `vinhos`

Gravar com `ArtifactData update` (pinar `if_version`):
- `ficha.notas` (null onde não houver), `ficha.fontes` (lista "Fonte nota (safra)"),
- `ficha.precoEstimado` ("R$ x a y (loja, mês/ano)"),
- `ficha.janelaInicio/janelaFim/apice` (preferir janela de crítico; o app usa o ápice para "Pronto para beber"),
- `ficha.verificadaEm` (ISO), `pesquisa: {status:"feita", feitaEm}`.
Não sobrescrever `resumo`, `harmonizacao`, `decantar` a menos que estejam errados.
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
