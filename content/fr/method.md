---
{
  "title": { "fr": "Méthode, corrections et limites", "nl": "Methode, correcties en beperkingen" },
  "description": { "fr": "Comment ce site a été fabriqué, ce qu'il a corrigé dans ses documents de départ, et ce qu'il ne prétend pas savoir.", "nl": "Hoe deze site gemaakt is, wat ze in haar uitgangsdocumenten heeft gecorrigeerd, en wat ze niet beweert te weten." },
  "lede": { "fr": "Un site écrit par un modèle de langage doit être plus explicite qu'un autre sur sa méthode, parce que le lecteur a de bonnes raisons de s'en méfier. Voici la procédure, sans enjolivement, et la liste des erreurs trouvées dans le matériau de départ.", "nl": "Een site geschreven door een taalmodel moet explicieter zijn over haar methode dan een andere, omdat de lezer goede redenen heeft om wantrouwig te zijn. Hier is de procedure, zonder opsmuk, en de lijst van fouten die in het uitgangsmateriaal zijn gevonden." }
}
---

## D'où vient le matériau

Le point de départ est un ensemble de notes de recherche produites par des modèles d'intelligence artificielle et rassemblées par l'éditeur du site : cinq documents longs sur la situation politique belge de 2026, plus les notes de fabrication de deux sites antérieurs du même éditeur.

Ces documents sont denses, bien organisés, et **partiellement faux**. C'est le comportement attendu : un modèle de langage produit un texte plausible, pas un texte vérifié. Les erreurs qu'on y trouve ne sont pas grossières — ce sont des dates décalées, des montants d'une version antérieure, des fonctions attribuées à la mauvaise personne, des décisions de justice fusionnées en une seule.

Ils ont donc été traités ici comme ce qu'ils sont : des **pistes**, pas des sources. Aucun de ces documents n'est cité dans la bibliographie, et aucune affirmation du site ne repose sur eux seuls.

## La procédure de vérification

1. Lecture intégrale des documents de départ, extraction de chaque affirmation datée ou chiffrée.
2. Recherche indépendante pour chacune, en privilégiant dans cet ordre : la source primaire (arrêt, texte légal, communication de l'administration compétente), l'institution publique, la presse belge établie, la partie prenante identifiée comme telle.
3. Conservation d'une affirmation uniquement si elle a été retrouvée dans une source accessible et datable. En cas d'échec, deux options : abandon, ou publication accompagnée d'un encadré d'incertitude qui dit ce qui manque.
4. Consignation publique de chaque écart entre le document de départ et le résultat de la vérification — c'est le tableau ci-dessous.

Chaque chiffre publié porte un appel de note. Chaque note renvoie à une source avec son éditeur, sa date de publication quand elle existe, et sa date de consultation. La bibliographie indique en outre, pour chaque source, combien de fois elle est citée dans le site.

## Ce que le site refuse de faire

- **Publier un chiffre non retrouvé.** Plusieurs montants présents dans les documents de départ ont été écartés faute de source. Le rendement réel de la taxe sur les plus-values en est l'exemple principal : il circule beaucoup, il n'existe pas.
- **Attribuer une probabilité à un scénario politique.** Aucun modèle publié ne permet de calculer qu'une chute de gouvernement serait probable à 35 %. Les trajectoires sont décrites par leurs conditions observables.
- **Présenter une analyse comme un fait.** Les encadrés rouges signalent une lecture assumée de l'auteur ; les encadrés bleus signalent un fait établi et sourcé. La distinction est maintenue page par page.
- **Lisser une contradiction entre sources.** Quand deux sources fiables divergent, les deux sont publiées avec un encadré qui le dit. C'est le cas du taux de report vers les CPAS et de l'ordre de tête des sondages flamands.

## Les corrections

Les écarts ci-dessous ont été trouvés entre les documents de départ et ce que la vérification a établi. Ils sont publiés parce qu'un lecteur qui aurait lu les mêmes documents doit pouvoir savoir où ils se trompent.

## Ce que ce site ne traite pas

Le périmètre est le conclave budgétaire fédéral de l'automne 2026 et ses effets directs. Sont volontairement absents : la politique migratoire, la justice et la politique pénale, la défense au-delà de son volet budgétaire, la politique énergétique au-delà du rachat du parc nucléaire, la mobilité, l'environnement, la politique étrangère, la politique communale hors CPAS.

Le dossier flamand est le plus mince du site. La raison est explicite : la documentation néerlandophone n'a été consultée que partiellement. Un lecteur qui cherche un suivi complet de la législature flamande ne le trouvera pas ici.

## Ce qui périmera, et quand

Ce site est daté du 21 septembre 2026 et il le revendique. Trois échéances le rendront partiellement faux :

- **13 octobre 2026** — déclaration de politique générale et dépôt du budget. Les dossiers 01, 02, 03 et 13 devront être révisés ; le dossier 01 sera largement obsolète.
- **Modalités de régularisation de l'ONEM** — elles chiffreront l'effet réel de l'arrêt du 10 septembre sur le budget 2027. Dossiers 04 et 05.
- **Semaine du 23 novembre 2026** — décision syndicale. Dossier 12.

## La fabrication

Le site est produit par un générateur écrit en Python, sans dépendance extérieure, à partir de fichiers de contenu et de données. Le code et les données sont dans le dépôt ; le résultat est du HTML statique. Aucune police distante, aucun script tiers, aucune requête sortante : une page de ce site ne communique avec personne.

Les jeux de données des graphiques sont publiés en CSV et en JSON, sous licence CC0. Chacun porte la liste de ses sources. Un lecteur qui conteste un graphique peut le refaire.

## La signature

Les textes sont écrits par Claude, modèle de langage d'Anthropic, sous supervision éditoriale humaine. Cette mention figure sur chaque page, dans le pied de page et dans les données structurées de chaque article.

Elle n'est pas une décharge de responsabilité. Un texte vérifié est un texte vérifié, quel que soit ce qui l'a écrit ; un texte non vérifié reste faux, quel que soit ce qui l'a écrit. La méthode décrite ci-dessus est ce qui distingue les deux, et elle est publiée pour pouvoir être contestée.
