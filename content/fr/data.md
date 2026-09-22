---
{
  "title": { "fr": "Données ouvertes", "nl": "Open data" },
  "description": { "fr": "Tous les jeux de données des graphiques du site, en CSV et en JSON, sous licence CC0, avec leurs sources.", "nl": "Alle datasets achter de grafieken van de site, in CSV en JSON, onder CC0-licentie, met hun bronnen." },
  "lede": { "fr": "Un graphique qu'on ne peut pas refaire est une affirmation, pas une preuve. Toutes les séries chiffrées de ce site sont téléchargeables, dans deux formats, avec la liste de leurs sources.", "nl": "Een grafiek die je niet kunt reproduceren is een bewering, geen bewijs. Alle cijferreeksen van deze site zijn downloadbaar, in twee formaten, met de lijst van hun bronnen." }
}
---

## Ce qui est publié

Chaque graphique du site repose sur une série de données stockée séparément du texte. Ces séries sont publiées telles quelles, sans agrégation ni retraitement : ce sont exactement les nombres qui produisent les barres.

Deux formats sont disponibles pour chacune :

- **CSV** — une ligne par catégorie, les libellés en français et en néerlandais dans les deux premières colonnes, puis une colonne par série. Les valeurs absentes sont des cellules vides, jamais des zéros.
- **JSON** — la même chose, plus le titre bilingue, l'unité, et la liste des sources avec leur titre et leur URL.

Un fichier `donnees/index.json` liste l'ensemble des jeux de données disponibles.

## Licence et conditions

Les données sont publiées sous **CC0 1.0**, c'est-à-dire versées au domaine public. Vous pouvez les reprendre, les modifier, les publier, les vendre, sans condition ni attribution.

Cela n'a rien de généreux : ces chiffres ne nous appartiennent pas. Ils proviennent de publications de la Banque nationale, de l'Agence fédérale de la Dette, de la Cour constitutionnelle, d'universités et de rédactions. Ce qui est original ici, c'est la mise en série et la vérification — pas les nombres.

Si vous réutilisez ces données, la seule chose utile à faire est de remonter aux sources indiquées dans le fichier JSON, et de vérifier qu'elles disent bien ce que nous leur faisons dire.

## Ce que les données ne contiennent pas

::: incertitude
Trois précautions valent pour l'ensemble des séries.

**Les horizons ne sont pas comparables.** Un effort de dix milliards d'ici 2029 et un effort de 900 millions pour l'exercice 2027 ne se mettent pas sur la même échelle sans précaution. Les notes sous chaque graphique le signalent au cas par cas.

**Les valeurs absentes ne valent pas zéro.** Une cellule vide signifie que la source ne publie pas ce chiffre. C'est fréquent dans les séries de sondages, où les instituts ne détaillent pas tous les partis pour toutes les années.

**Les projections ne sont pas des prévisions.** Les trajectoires de dette et de déficit 2026-2029 sont établies à politique inchangée. Elles n'intègrent ni les décisions du conclave en cours, ni l'effet de l'arrêt du 10 septembre sur le chômage, ni le coût du rachat éventuel du parc nucléaire.
:::
