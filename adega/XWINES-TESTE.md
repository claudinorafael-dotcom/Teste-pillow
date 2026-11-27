# Teste do dataset X-Wines (27/11/2026)

Fonte: github.com/rogerioxavier/X-Wines (licença CC0). Versão Full no Google Drive, pasta 1LqguJNV-aKh1PuWMVx5ELA61LPfGfuu_
(`XWines_Full_100K_wines.zip` 4,5 MB e `XWines_Full_21M_ratings.zip` 304 MB; baixados com `gdown`).

- Vinhos: `WineID, WineName, Type, Elaborate, Grapes, Harmonize, ABV, Body, Acidity, Code, Country, RegionID, RegionName,
  WineryID, WineryName, Website, Vintages` (100.646 linhas).
- Avaliações: `RatingID, UserID, WineID, Vintage, Rating, Date` (21 milhões, 2012 a 2021, escala 1 a 5 com meios pontos).

## Resultado com os 65 rótulos da adega

- Encontrados: 57 de 65 (88%). Não encontrados: Barbanera Legàmi, Bianchi IV Generación, Casas del Bosque Botanic (Riesling e
  Rosé), Castellani Guadalmare Chianti Riserva, Fanti Sassomagno, Freixenet Asti, Séptima Gran Malbec.
- Nota média do rótulo (todas as safras) x Vivino gravado nas fichas: diferença média +0,02, desvio 0,14, máxima 0,36 (54 rótulos).
- Nota da safra exata disponível para cerca de 30 rótulos (safras até 2021); nada para 2022 em diante.
- Casamento por nome exige cuidado: o primeiro algoritmo errou Angélica Zapata, Caballo Loco, Braccale, Taittinger, Montes
  e Borgogno, que existem no catálogo com a vinícola escrita de outra forma (ex.: vinícola "Caballo Loco", não "Valdivieso").
- Agregar as 21 milhões de avaliações para um conjunto de vinhos leva 6 segundos em Python.

## Leitura

Serve como catálogo (nome, vinícola, uvas, região, corpo, acidez, harmonização) e como nota de comunidade offline que
concorda com o Vivino. Não tem críticos, preço nem janela de consumo, e está congelado em 2021.
