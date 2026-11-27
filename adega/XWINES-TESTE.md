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

## Integração (27/11/2026, app v5.23)

- `adega/xwines/build_index.py <pasta com os dois CSV> <pasta de saída>` gera o índice: `wineries.json` (30.510 vinícolas,
  745 KB) e `w/000.json` a `w/127.json` (vinhos por `WineryID % 128`, com média geral e médias por safra com 5+ avaliações;
  cerca de 176 KB cada, 22 MB no total). Leva 1 minuto. O índice não está no repositório: é reconstruído a partir do dataset.
- O índice é publicado junto com a página como arquivos de apoio em `xw/` (130 arquivos). Em qualquer republicação da página
  sem `files`, os arquivos existentes são mantidos.
- No app (`adega/xwines/xw_core.js` é a cópia do trecho embutido): ao cadastrar, depois da leitura do rótulo ou pelo botão
  "Catálogo", o app carrega a lista de vinícolas uma vez, casa por palavras do produtor e do vinho, busca só os pedaços das
  vinícolas candidatas e mostra até 3 opções ("É um destes?"). Ao confirmar, preenche uvas, região, país e tipo quando
  vazios e grava `xw` no documento: `{id, vinicola, nome, media, n, mediaSafra, nSafra, corpo, acidez, harm, uvas, fonte}`.
- Uso da nota: quando a ficha não tem Vivino, a nota de qualidade usa `xw.mediaSafra` (20+ avaliações) ou `xw.media`;
  o card mostra o chip "Com."; a ficha tem a seção "Catálogo".
- Pesquisa: com `xw` no documento, a tarefa não busca o Vivino (uma busca a menos por garrafa) e cita o catálogo nas fontes.
- Teste do casamento com os 65 rótulos: 57 corretos (um deles na 2ª opção antes do ajuste de parênteses), 4 corretamente
  sem sugestão, 1 perdido (Barbanera Governo), 3 sugestões para vinhos fora do catálogo, que o Rafael recusa na confirmação.
- Não feito: preencher `xw` nas 65 garrafas já cadastradas (elas já têm Vivino) e usar o catálogo na aba Pesquisa.
