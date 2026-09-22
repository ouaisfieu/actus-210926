---
{
  "title": { "fr": "Méthode, corrections et limites", "nl": "Methode, correcties en beperkingen" },
  "description": { "fr": "Comment ce site a été fabriqué.", "nl": "Hoe deze site gemaakt is, wat ze in haar uitgangsdocumenten heeft gecorrigeerd, en wat ze niet beweert te weten." },
  "lede": { "fr": "La procédure, sans enjolivement.", "nl": "Een site geschreven door een taalmodel moet explicieter zijn over haar methode dan een andere, omdat de lezer goede redenen heeft om wantrouwig te zijn. Hier is de procedure, zonder opsmuk, en de lijst van fouten die in het uitgangsmateriaal zijn gevonden." }
}
---

## Waar het materiaal vandaan komt

Het vertrekpunt is een reeks onderzoeksnota's die door modellen voor kunstmatige intelligentie zijn voortgebracht en door de uitgever van de site verzameld: vijf lange documenten over de Belgische politieke situatie van 2026, plus de bouwnota's van twee eerdere sites van dezelfde uitgever.

Die documenten zijn dicht, goed geordend, en **gedeeltelijk onjuist**. Dat is het verwachte gedrag: een taalmodel brengt een plausibele tekst voort, geen geverifieerde tekst. De fouten die men erin aantreft, zijn niet grof — het zijn verschoven data, bedragen uit een eerdere versie, functies aan de verkeerde persoon toegeschreven, rechterlijke beslissingen die tot één beslissing zijn versmolten.

Ze zijn hier dus behandeld als wat ze zijn: **sporen**, geen bronnen. Geen van die documenten staat in de bibliografie, en geen enkele bewering op deze site steunt op hen alleen.

## De verificatieprocedure

1. Volledige lezing van de uitgangsdocumenten, met extractie van elke gedateerde of becijferde bewering.
2. Onafhankelijke opzoeking voor elk ervan, in deze volgorde van voorkeur: de primaire bron (arrest, wettekst, mededeling van de bevoegde administratie), de overheidsinstelling, de gevestigde Belgische pers, de als zodanig herkenbare belanghebbende.
3. Behoud van een bewering enkel als ze in een toegankelijke en dateerbare bron is teruggevonden. Lukt dat niet, dan zijn er twee opties: schrappen, of publiceren met een onzekerheidskader dat zegt wat ontbreekt.
4. Publieke registratie van elk verschil tussen het uitgangsdocument en het resultaat van de verificatie — dat is de tabel hieronder.

Elk gepubliceerd cijfer draagt een notenverwijzing. Elke noot verwijst naar een bron met haar uitgever, haar publicatiedatum als die bestaat, en haar raadplegingsdatum. De bibliografie vermeldt bovendien voor elke bron hoe vaak ze op de site wordt aangehaald.

## Wat de site weigert te doen

- **Een niet-teruggevonden cijfer publiceren.** Verschillende bedragen uit de uitgangsdocumenten zijn bij gebrek aan bron geschrapt. De werkelijke opbrengst van de meerwaardebelasting is daarvan het hoofdvoorbeeld: ze circuleert veel, ze bestaat niet.
- **Een waarschijnlijkheid toekennen aan een politiek scenario.** Geen enkel gepubliceerd model laat toe te berekenen dat een regeringsval 35 % waarschijnlijk zou zijn. Trajecten worden beschreven aan de hand van hun waarneembare voorwaarden.
- **Een analyse als een feit voorstellen.** Rode kaders duiden een expliciete lezing van de auteur aan; blauwe kaders duiden een vastgesteld en gedocumenteerd feit aan. Dat onderscheid wordt pagina na pagina aangehouden.
- **Een tegenstrijdigheid tussen bronnen gladstrijken.** Wanneer twee betrouwbare bronnen uiteenlopen, worden beide gepubliceerd met een kader dat dit zegt. Dat geldt voor het doorstroompercentage naar de OCMW's en voor de volgorde aan kop in de Vlaamse peilingen.

## De correcties

De verschillen hieronder werden gevonden tussen de uitgangsdocumenten en wat de verificatie heeft vastgesteld. Ze worden gepubliceerd omdat een lezer die dezelfde documenten zou hebben gelezen, moet kunnen weten waar ze fout zitten.

## Wat deze site niet behandelt

De perimeter is het federale begrotingsconclaaf van het najaar 2026 en zijn directe gevolgen. Bewust afwezig: migratiebeleid, justitie en strafbeleid, defensie voorbij het budgettaire luik, energiebeleid voorbij de overname van het kernpark, mobiliteit, milieu, buitenlands beleid, gemeentelijk beleid buiten de OCMW's.

Het Vlaamse dossier is het dunste van de site. De reden is expliciet: de Nederlandstalige documentatie is slechts gedeeltelijk geraadpleegd. Wie een volledige opvolging van de Vlaamse legislatuur zoekt, vindt die hier niet.

## Wat zal verouderen, en wanneer

Deze site draagt de datum van 21 september 2026 en staat daarvoor in. Drie vervaldagen zullen haar gedeeltelijk onjuist maken:

- **13 oktober 2026** — beleidsverklaring en indiening van de begroting. De dossiers 01, 02, 03 en 13 moeten worden herzien; dossier 01 zal grotendeels achterhaald zijn.
- **Regularisatiemodaliteiten van de RVA** — die zullen het werkelijke effect van het arrest van 10 september op de begroting 2027 becijferen. Dossiers 04 en 05.
- **Week van 23 november 2026** — vakbondsbeslissing. Dossier 12.

## De fabricage

De site wordt voortgebracht door een generator in Python, zonder externe afhankelijkheden, op basis van inhouds- en databestanden. De code en de data zitten in de repository; het resultaat is statische HTML. Geen externe lettertypes, geen scripts van derden, geen uitgaande verzoeken: een pagina van deze site communiceert met niemand.

De datasets achter de grafieken zijn gepubliceerd in CSV en JSON, onder CC0-licentie. Elk draagt de lijst van zijn bronnen. Wie een grafiek betwist, kan ze overdoen.

## De ondertekening

De teksten zijn geschreven door Claude, taalmodel van Anthropic, onder menselijke redactionele supervisie. Die vermelding staat op elke pagina, in de voettekst en in de gestructureerde gegevens van elk artikel.

Ze is geen aansprakelijkheidsontheffing. Een geverifieerde tekst is een geverifieerde tekst, wat hem ook geschreven heeft; een niet-geverifieerde tekst blijft onjuist, wat hem ook geschreven heeft. De hierboven beschreven methode is wat beide onderscheidt, en ze wordt gepubliceerd om betwist te kunnen worden.
