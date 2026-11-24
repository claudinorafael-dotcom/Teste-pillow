# Teste da Apify como fonte de notas e preço (plano para 25/11/2026)

Decisão de 24/11: APIs oficiais não servem (Global Wine Score encerrou; Wine-Searcher API custa US$ 335/mês e
só dá score agregado; Vivino não tem API). Testar um raspador hospedado na Apify, com a busca atual como reserva.

## Raspador escolhido

`abotapi/wine-searcher-scraper` (Wine-Searcher Scraper - Wine Prices, Scores, Offers & LWIN)
- Pay per event, cerca de US$ 1,70 por 1.000 vinhos; crédito gratuito da Apify (US$ 5/mês) cobre milhares.
- Entrada: `inputType:"auto"`, `wineNames:[...]` (aceita nome + safra), `targetCurrency:"BRL"` (testar; senão USD),
  `fetchOffers:false`, `fetchReviews:false`, `maxItems`.
- Saída por vinho: `wineName, vintage, producer, appellation, region, grapeVariety, score, criticScores {crítico: nota},
  criticReviewsCount, avgPrice, cheapestPriceAmount, cheapestPriceMerchant, labelImageUrl, wineSearcherUrl`.
- Ressalva: 69% de execuções bem-sucedidas na página do actor; tratar resultado vazio como "não encontrado".

Descartados: `mrbridge/vivino-wine-data-scraper` (só média Vivino, que já pegamos de graça),
`mrbridge/millesima-wine-scraper` e `growth-installations/jamessuckling-scraper` (não aceitam nome de vinho).

## Como rodar (API da Apify)

Token: pedir pelo formulário seguro (`request_credential`, host `api.apify.com`, header `Authorization: Bearer`).
```
POST https://api.apify.com/v2/acts/abotapi~wine-searcher-scraper/run-sync-get-dataset-items?timeout=120
Content-Type: application/json
{"inputType":"auto","wineNames":["Travaglini Gattinara 2021", "..."],"targetCurrency":"BRL","fetchOffers":false,"fetchReviews":false,"maxItems":20}
```

## Plano de teste

1. Rodar os 16 rótulos da adega numa execução.
2. Comparar com `ficha.notas` atual: quantos vinhos voltaram, quais críticos apareceram, preço em R$ ou USD.
3. Se cobrir bem (≥ 10 de 16 com notas por crítico): incluir no protocolo e no prompt da tarefa como passo 1 da
   pesquisa de críticos; busca na web vira complemento. Mapear `criticScores` para as chaves do app:
   James Suckling→suckling, Robert Parker/Wine Advocate→parker, Wine Spectator→spectator, Decanter→decanter,
   Vinous→vinous, Tim Atkin→atkin, Descorchados→descorchados.
4. Se cobrir mal: manter como está e registrar aqui o resultado.
