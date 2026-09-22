---
{
  "title": { "fr": "Données ouvertes", "nl": "Open data" },
  "description": { "fr": "Tous les jeux de données du site.", "nl": "Alle datasets achter de grafieken van de site, in CSV en JSON, onder CC0-licentie, met hun bronnen." },
  "lede": { "fr": "Un graphique qu'on ne peut pas refaire est une affirmation.", "nl": "Een grafiek die je niet kunt reproduceren is een bewering, geen bewijs. Alle cijferreeksen van deze site zijn downloadbaar, in twee formaten, met de lijst van hun bronnen." }
}
---

## Wat gepubliceerd wordt

Elke grafiek op de site steunt op een gegevensreeks die los van de tekst wordt bewaard. Die reeksen worden ongewijzigd gepubliceerd, zonder aggregatie of herbewerking: het zijn exact de getallen die de staven voortbrengen.

Voor elk zijn twee formaten beschikbaar:

- **CSV** — één rij per categorie, de labels in het Frans en het Nederlands in de eerste twee kolommen, daarna één kolom per reeks. Ontbrekende waarden zijn lege cellen, nooit nullen.
- **JSON** — hetzelfde, plus de tweetalige titel, de eenheid, en de lijst van de bronnen met hun titel en URL.

Een bestand `donnees/index.json` somt alle beschikbare datasets op.

## Licentie en voorwaarden

De data worden gepubliceerd onder **CC0 1.0**, dus in het publieke domein. U mag ze overnemen, wijzigen, publiceren en verkopen, zonder voorwaarde of naamsvermelding.

Dat is niet genereus: deze cijfers zijn niet van ons. Ze komen uit publicaties van de Nationale Bank, het Federaal Agentschap van de Schuld, het Grondwettelijk Hof, universiteiten en redacties. Wat hier origineel is, is het in reeks brengen en het verifiëren — niet de getallen.

Gebruikt u deze data, dan is het enige nuttige wat u kunt doen: teruggaan naar de bronnen die in het JSON-bestand staan, en nagaan of ze wel degelijk zeggen wat wij hen laten zeggen.

## Wat de data niet bevatten

::: incertitude
Drie voorzorgen gelden voor alle reeksen.

**De horizonten zijn niet vergelijkbaar.** Een inspanning van tien miljard tegen 2029 en een inspanning van 900 miljoen voor het boekjaar 2027 laten zich niet zonder voorzorg op dezelfde schaal zetten. De noten onder elke grafiek signaleren dat geval per geval.

**Lege waarden zijn geen nullen.** Een lege cel betekent dat de bron dat cijfer niet publiceert. Dat komt vaak voor in peilingreeksen, waar instituten niet alle partijen voor alle jaren uitsplitsen.

**Ramingen zijn geen voorspellingen.** De schuld- en tekorttrajecten 2026-2029 zijn opgesteld bij ongewijzigd beleid. Ze bevatten noch de beslissingen van het lopende conclaaf, noch het effect van het arrest van 10 september over de werkloosheid, noch de kost van een eventuele overname van het kernpark.
:::
