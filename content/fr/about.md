---
{
  "title": { "fr": "À propos", "nl": "Over deze site" },
  "description": { "fr": "Ce que ce site est, qui l'écrit, sous quelle licence, et ce qu'il fait de vos données — rien.", "nl": "Wat deze site is, wie ze schrijft, onder welke licentie, en wat ze met uw gegevens doet — niets." },
  "lede": { "fr": "Un site sans rédaction, sans publicité, sans traceur et sans modèle économique. Ce qui suit dit à quoi il sert, comment le réutiliser, et à qui adresser un reproche.", "nl": "Een site zonder redactie, zonder reclame, zonder trackers en zonder verdienmodel. Wat volgt zegt waar ze voor dient, hoe ze te hergebruiken, en bij wie een verwijt thuishoort." }
}
---

## Ce que c'est

Un instantané daté. Le site décrit la Belgique politique telle qu'elle est le **21 septembre 2026**, jour d'ouverture du conclave budgétaire fédéral, et il est construit pour que cette date reste visible partout : dans son nom, dans son en-tête, dans la date de chaque source, dans la page [[p:method|Méthode]] qui annonce à l'avance ce qui périmera.

Ce parti pris a un coût — plusieurs pages seront obsolètes le 13 octobre — et un bénéfice : il permet d'être précis. Un site qui prétend rester valable six mois doit écrire au conditionnel. Un site qui assume une date peut écrire au présent, citer des montants exacts, et dire quand il se trompera.

## Ce que ce n'est pas

Ce n'est pas un média : il n'y a ni rédaction, ni enquête de terrain, ni entretien. Tout ce qui est publié ici a d'abord été publié ailleurs, par des journalistes, des juridictions ou des administrations. La valeur ajoutée est le rassemblement, la vérification croisée, la datation et la mise en relation — pas l'information de première main.

Ce n'est pas non plus un site neutre. Les dossiers contiennent des lectures assumées, signalées par des encadrés rouges. Elles sont séparées des faits, qui sont dans les encadrés bleus, et des incertitudes, qui sont dans les encadrés jaunes. Le lecteur qui ne veut que les faits peut ignorer le rouge.

## Qui écrit

Les textes, les vérifications, les graphiques et le code sont produits par **Claude**, modèle de langage développé par Anthropic, sous supervision éditoriale humaine. L'éditeur reste anonyme ; il choisit le périmètre, tranche les arbitrages éditoriaux et publie.

La mention d'auteur figure sur chaque page et dans les données structurées `schema.org` de chaque article, sous la forme d'un nœud `Person` explicitement rattaché à Anthropic. Un lecteur, un moteur de recherche ou un autre système automatique peuvent donc savoir sans ambiguïté ce qui a produit ce texte.

## Licences

- **Textes** — Creative Commons Attribution 4.0 International (CC BY 4.0). Réutilisation libre, y compris commerciale, à condition de citer la source.
- **Code, feuille de style, script, jeux de données** — CC0 1.0, domaine public. Aucune condition.

Les jeux de données des graphiques sont téléchargeables en CSV et en JSON depuis la page [[p:data|Données ouvertes]], chacun accompagné de ses sources.

Les contenus cités ou liés restent la propriété de leurs auteurs. Les liens externes portent l'attribut `rel="nofollow"` : ce site ne transmet aucun signal de référencement aux sites qu'il cite, dans un sens ni dans l'autre.

## Vie privée

Ce site ne collecte rien. Pas de cookie, pas de traceur, pas d'analytique, pas de police distante, pas de script tiers, pas de formulaire. La recherche plein texte s'exécute entièrement dans le navigateur, sur un fichier d'index statique ; aucune requête n'est envoyée nulle part.

Le seul élément stocké localement est votre préférence de thème clair ou sombre, dans le stockage local de votre navigateur. Elle ne quitte pas votre machine et peut être effacée en vidant les données du site.

L'hébergement est assuré par GitHub Pages, dont les journaux de serveur échappent au contrôle de ce site.

## Accessibilité

Le site vise le niveau AA des règles WCAG 2.1. Concrètement :

- un seul `h1` par page, hiérarchie de titres continue, lien d'évitement en tête de document ;
- chaque graphique est un SVG portant `role="img"`, un titre et une description longue, et il est doublé d'un tableau de données dépliable — aucune information n'est portée par la seule couleur ;
- les couleurs de séries suivent la palette d'Okabe et Ito, conçue pour rester distinguable en vision deutéranope, protanope et tritanope ; les couleurs des partis politiques ne sont **pas** utilisées, parce qu'elles ne se distinguent pas ;
- contrastes vérifiés en thème clair et en thème sombre, indicateur de focus visible, `prefers-reduced-motion` respecté ;
- le site reste entièrement lisible sans JavaScript : seules la recherche, les filtres de chronologie et la bascule de thème en dépendent ;
- feuille d'impression dédiée, qui affiche les URL des liens et conserve les tableaux de données.

## Signaler une erreur

Une erreur factuelle sur ce site est un défaut, pas une opinion divergente. Le dépôt du code est public et accepte les signalements. Les corrections apportées après publication seront ajoutées au tableau de la page [[p:method|Méthode]], avec leur date — au même titre que celles apportées aux documents de départ.

## Les sites voisins

Deux sites antérieurs du même éditeur traitent du même pays sous un autre angle : une veille chronologique et une analyse par mécanismes. Celui-ci en diffère par trois choix : l'ancrage sur une date unique, l'index d'acteurs relié aux dossiers et à la chronologie, et la publication des données en format ouvert.
