# 21.09.26

Site statique bilingue (français / néerlandais) consacré à la Belgique
politique **au 21 septembre 2026**, jour d'ouverture du conclave budgétaire
fédéral.

→ [ouaisfieu.github.io/actus-210926](https://ouaisfieu.github.io/actus-210926/)
· [Nederlandstalige versie](https://ouaisfieu.github.io/actus-210926/nl/)

## Le parti pris

Le site est un instantané daté, et il le dit partout : dans son nom, dans son
en-tête, dans la date de consultation de chaque source, et dans la page
[Méthode](https://ouaisfieu.github.io/actus-210926/methode.html) qui annonce à
l'avance quelles pages seront périmées le 13 octobre 2026.

Chaque chiffre publié porte un appel de note. Chaque note renvoie à une source
avec son éditeur, sa date de publication et sa date de consultation. Les faits
établis, les lectures assumées et les incertitudes déclarées sont dans des
encadrés de trois couleurs différentes, et ne sont jamais mélangés.

## Contenu

- **14 dossiers** — le conclave, les dix milliards, la fiscalité, le chômage,
  les CPAS, la dette, les pensions, la santé, la Wallonie, Bruxelles, la
  Flandre, le front social, les institutions, l'opinion.
- **38 fiches d'acteurs** — personnes, partis, institutions, syndicats, avec
  leurs positions datées, leurs citations sourcées et les dossiers où ils
  apparaissent, reliés dans les deux sens.
- **48 repères chronologiques** filtrables, de juin 2024 à novembre 2026.
- **12 jeux de données** publiés en CSV et en JSON sous licence CC0.
- **30 termes** de glossaire, **97 sources** classées par nature, une page de
  méthode avec le tableau public des corrections apportées aux documents de
  départ.

Le tout en deux langues, soit 124 pages.

## Stack

Un générateur maison en Python, **bibliothèque standard uniquement** : pas de
Node, pas de dépendance, pas d'installation. Le résultat est du HTML statique
sans aucune requête vers un tiers — ni police distante, ni script, ni traceur.

```
build.py              générateur (~1 900 lignes)
content/fr, content/nl  contenu éditorial, markdown maison + en-tête JSON
data/                 site, sources, acteurs, glossaire, chronologie,
                      figures, corrections — tout est bilingue
assets/               style.css, app.js, icon.svg, manifest
tools/check.py        contrôles de structure, liens, JSON-LD, données
tools/render.py       contrôles de rendu (Chromium, 2 configurations)
tools/og.py           cartes de partage Open Graph
docs/                 SORTIE — c'est ce dossier que GitHub Pages sert
.github/workflows/    vérifie que docs/ est à jour et lance check.py
```

### Syntaxe de contenu

Le markdown est volontairement minimal, augmenté de cinq directives :

| Directive | Effet |
| --- | --- |
| `[[s:identifiant]]` | appel de note vers une source de `data/sources.json` |
| `[[e:identifiant\|libellé]]` | lien vers une fiche d'acteur |
| `[[g:identifiant\|libellé]]` | lien vers une entrée de glossaire, avec infobulle |
| `[[d:identifiant\|libellé]]` · `[[p:clé\|libellé]]` | lien interne vers un dossier ou une page |
| `{{chart:identifiant}}` | graphique SVG + tableau de données + sources |
| `::: fait … :::` | encadré (`fait`, `chiffre`, `analyse`, `incertitude`, `contradiction`) |

## Construire

```sh
python3 build.py --clean     # produit docs/
python3 tools/check.py       # 8 familles de contrôles, sortie non nulle si échec
python3 tools/render.py      # rendu Chromium, 2 configurations, sans JS
python3 tools/og.py          # cartes de partage (demande Chromium)
```

Les contrôles vérifient : unicité du `h1`, longueur des titres et descriptions,
identifiants uniques, JSON-LD parsable, liens et ancres internes, réciprocité
des `hreflang`, couverture du sitemap, validité des flux Atom, cohérence de
l'index de recherche, longueur des séries de données, dates de consultation des
sources. Le rendu vérifie l'absence de débordement horizontal, d'erreur
JavaScript et de cible tactile inférieure à 24 pixels, et que la chronologie,
le glossaire et la recherche restent lisibles sans JavaScript.

## SEO et web sémantique

`lang` et `hreflang` sur chaque page avec `x-default`, canonical, Open Graph
avec carte d'image dédiée par dossier, Twitter Card, sitemap avec alternates,
flux Atom par langue, `manifest.webmanifest`.

Données structurées `schema.org` en `@graph` : `WebSite` (avec `SearchAction`),
`Person` pour l'auteur, `Organization` pour l'éditeur, puis selon la page
`Article`, `CollectionPage`, `ProfilePage`, `AboutPage`, `DataCatalog`,
`BreadcrumbList`, `ItemList` + `Event`, `DefinedTermSet` + `DefinedTerm`,
`Dataset` + `DataDownload`, `PoliticalParty`, `GovernmentOrganization`.

La particularité du site est l'ossature d'entités : chaque acteur possède un
`@id` stable, les dossiers le déclarent en `about` et `mentions`, les fiches
déclarent `sameAs` vers les références externes vérifiées, et les rétroliens
sont calculés au build. Le graphe est donc navigable dans les deux sens, par un
lecteur comme par une machine.

## Accessibilité

Niveau AA visé. Un seul `h1` par page, lien d'évitement, hiérarchie continue.
Chaque graphique est un SVG avec `role="img"`, un titre et une description
longue, doublé d'un tableau de données dépliable : aucune information n'est
portée par la seule couleur. Les séries utilisent la palette d'Okabe et Ito,
distinguable en vision deutéranope, protanope et tritanope — les couleurs des
partis politiques ne sont volontairement pas utilisées, parce qu'elles ne se
distinguent pas. Thème clair et sombre, `prefers-reduced-motion` respecté,
feuille d'impression dédiée.

## Déploiement

**Settings → Pages → Source : Deploy from a branch → Branch `main`, dossier
`/docs`.** Le fichier `docs/.nojekyll` désactive le traitement Jekyll.

Aucune action GitHub n'est nécessaire au déploiement : `docs/` est commité.
Le workflow fourni ne fait que vérifier que le dossier est bien à jour.

## Signature et licences

Textes, vérifications, graphiques et code produits par **Claude** (Anthropic),
sous supervision éditoriale humaine.

Textes CC BY 4.0, code et données CC0 — voir [`LICENSE`](LICENSE).

## À réviser

- après le **13 octobre 2026** (déclaration de politique générale) : dossiers
  01, 02, 03, 13 et la chronologie ;
- à la publication des **modalités de régularisation de l'ONEM** : dossiers 04
  et 05 ;
- après la **semaine du 23 novembre 2026** (décision syndicale) : dossier 12.
