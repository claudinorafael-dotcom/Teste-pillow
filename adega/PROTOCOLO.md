# Minha Adega — protocolo de pesquisa automática

Página: https://claude.ai/artifact/BMNmyWd7UrrTx3y9emFYwS (privada, só o dono abre).
Banco: coleções `vinhos` e `consumos` (ArtifactData). Fotos: assets do artifact (`fotoId` → `/_blob/<id>`).

## Quando a sessão do Claude é acordada

1. Por um comentário "Pesquisar avaliações…" vindo da página (`comments.sendToClaude`), ou
2. Por uma varredura periódica. Em qualquer caso, consultar **todos** os documentos de `vinhos`
   com `pesquisa.status` em `pendente` ou `solicitada`, não só o citado no comentário.

## Para cada vinho pendente

1. Pesquisar na web (WebSearch) notas de terceiros **da safra exata**; se não houver, safras vizinhas, dizendo isso:
   James Suckling (suckling), Wine Advocate/Parker (parker), Wine Spectator (spectator), Decanter (decanter), Vinous/Galloni (vinous), Tim Atkin (atkin), Descorchados (descorchados), Vivino (vivino, 1–5), CellarTracker (cellartracker); chaves entre parênteses são as de ficha.notas. Também Jancis Robinson, Falstaff,
   Guia Descorchados (chilenos), Tim Atkin (argentinos), Vivino (nota 1–5 e nº de avaliações), CellarTracker (média).
2. Janela de consumo: preferir a janela publicada por crítico; senão, derivar das notas da comunidade.
3. Preço de mercado no Brasil: Mistral, Grand Cru, World Wine, Evino, Wine.com.br, Vinhos do Mundo; registrar a faixa e a data.
4. Foto do rótulo, só se `fotoId` estiver vazio: procurar imagem do rótulo (site do produtor ou loja), baixar para o
   scratchpad em pasta própria, reduzir a ≤1200 px, subir com `Artifact publish asset:true` e gravar o `id` em `fotoId`.
5. Gravar com `ArtifactData update` (pinar `if_version`):
   - `ficha.notas` com os valores verificados (null onde não houver),
   - `ficha.fontes` (lista de strings "Fonte nota (safra)"),
   - `ficha.precoEstimado` ("R$ x a y" + loja/data),
   - `ficha.janelaInicio/janelaFim/apice` se a pesquisa mudar algo,
   - `ficha.verificadaEm` (ISO), `pesquisa: {status:"feita", feitaEm}`.
   Não sobrescrever `resumo`, `harmonizacao`, `decantar` a menos que estejam errados.
6. Se o pedido veio por comentário, responder no mesmo thread (ArtifactComments) com um resumo de 3 a 5 linhas:
   notas, janela, preço, e se a foto foi adicionada.

## Convenções

- `pesquisa.status`: `pendente` (ainda não enviado/recebido) → `solicitada` (comentário enviado) → `feita`.
- Notas: números; Vivino em escala 1–5; demais em 100 pontos. Nunca inventar; `null` quando não encontrado.
- Tudo em português.
