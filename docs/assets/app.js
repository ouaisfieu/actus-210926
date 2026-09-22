/* 21.09.26 — script unique, sans dépendance.
   Quatre comportements : bascule de thème, filtres de chronologie,
   filtre de glossaire, recherche plein texte.
   Tout fonctionne en local ; rien n'est envoyé nulle part.
   Sans JavaScript, chaque page reste lisible et complète. */

(function () {
  "use strict";

  var CLE = "actus210926-theme";

  /* ---------------------------------------------------------- thème */

  function litTheme() {
    try { return localStorage.getItem(CLE); } catch (e) { return null; }
  }
  function ecritTheme(v) {
    try { localStorage.setItem(CLE, v); } catch (e) { /* mode privé */ }
  }

  function initTheme() {
    var bouton = document.querySelector("[data-theme-toggle]");
    var etiquette = document.querySelector("[data-theme-label]");
    var racine = document.documentElement;
    var lang = racine.lang.slice(0, 2);
    var mots = lang === "nl"
      ? { sombre: "Donkere modus", clair: "Lichte modus" }
      : { sombre: "Mode sombre", clair: "Mode clair" };

    var stocke = litTheme();
    if (stocke === "dark" || stocke === "light") racine.setAttribute("data-theme", stocke);

    function sombreActif() {
      var attr = racine.getAttribute("data-theme");
      if (attr) return attr === "dark";
      return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    }

    function rafraichis() {
      if (!bouton) return;
      var sombre = sombreActif();
      bouton.setAttribute("aria-pressed", sombre ? "true" : "false");
      if (etiquette) etiquette.textContent = sombre ? mots.clair : mots.sombre;
    }

    if (bouton) {
      bouton.addEventListener("click", function () {
        var suivant = sombreActif() ? "light" : "dark";
        racine.setAttribute("data-theme", suivant);
        ecritTheme(suivant);
        rafraichis();
      });
    }
    rafraichis();
  }

  /* -------------------------------------------------- chronologie */

  function initChrono() {
    var liste = document.querySelector("[data-chrono]");
    var barre = document.querySelector("[data-filtres]");
    var compte = document.querySelector("[data-compte]");
    if (!liste || !barre) return;

    var items = Array.prototype.slice.call(liste.children);
    var boutons = Array.prototype.slice.call(barre.querySelectorAll("button"));

    function applique(filtre) {
      var visibles = 0;
      items.forEach(function (li) {
        var tags = (li.getAttribute("data-tags") || "").split(/\s+/);
        var ok = filtre === "*" || tags.indexOf(filtre) !== -1;
        li.hidden = !ok;
        if (ok) visibles++;
      });
      boutons.forEach(function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-filtre") === filtre ? "true" : "false");
      });
      if (compte) {
        compte.textContent = compte.textContent.replace(/^\d+/, String(visibles));
      }
    }

    boutons.forEach(function (b) {
      b.addEventListener("click", function () { applique(b.getAttribute("data-filtre")); });
    });
  }

  /* ---------------------------------------------------- glossaire */

  function normalise(s) {
    s = String(s).toLowerCase();
    if (String.prototype.normalize) {
      s = s.normalize("NFD").replace(/[̀-ͯ]/g, "");
    }
    return s;
  }

  function initGlossaire() {
    var champ = document.querySelector("[data-glossaire-rech]");
    var liste = document.querySelector("[data-glossaire]");
    var compte = document.querySelector("[data-compte-g]");
    if (!champ || !liste) return;

    var entrees = Array.prototype.slice.call(liste.querySelectorAll("[data-terme]"));

    champ.addEventListener("input", function () {
      var q = normalise(champ.value.trim());
      var visibles = 0;
      entrees.forEach(function (e) {
        var ok = !q || normalise(e.textContent).indexOf(q) !== -1;
        e.hidden = !ok;
        if (ok) visibles++;
      });
      if (compte) compte.textContent = compte.textContent.replace(/^\d+/, String(visibles));
    });
  }

  /* ---------------------------------------------------- recherche */

  function echappe(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function extrait(corps, motsNorm) {
    var norm = normalise(corps);
    var pos = -1;
    for (var i = 0; i < motsNorm.length && pos === -1; i++) {
      pos = norm.indexOf(motsNorm[i]);
    }
    if (pos === -1) pos = 0;
    var debut = Math.max(0, pos - 90);
    var bout = corps.slice(debut, debut + 240);
    if (debut > 0) bout = "… " + bout;
    if (debut + 240 < corps.length) bout += " …";
    var sortie = echappe(bout);
    motsNorm.forEach(function (m) {
      if (m.length < 3) return;
      var re = new RegExp("(" + m.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi");
      sortie = sortie.replace(re, "<mark>$1</mark>");
    });
    return sortie;
  }

  function initRecherche() {
    var form = document.querySelector("[data-recherche]");
    if (!form) return;
    var champ = form.querySelector('input[name="q"]');
    var cible = document.querySelector("[data-resultats]");
    var compte = document.querySelector("[data-rech-compte]");
    var lang = document.documentElement.lang.slice(0, 2);
    var mots = lang === "nl"
      ? { res: "resultaten", rien: "Geen resultaten.", charge: "Index laden…" }
      : { res: "résultats", rien: "Aucun résultat.", charge: "Chargement de l'index…" };

    var index = null;
    var enCours = false;

    function chargeIndex(ensuite) {
      if (index) { ensuite(); return; }
      if (enCours) return;
      enCours = true;
      if (compte) compte.textContent = mots.charge;
      var req = new XMLHttpRequest();
      req.open("GET", form.getAttribute("data-index"), true);
      req.onload = function () {
        enCours = false;
        if (req.status >= 200 && req.status < 300) {
          try {
            index = JSON.parse(req.responseText).docs;
            index.forEach(function (d) { d._n = normalise(d.t + " " + d.k + " " + d.b); });
            ensuite();
          } catch (e) { if (compte) compte.textContent = mots.rien; }
        } else if (compte) { compte.textContent = mots.rien; }
      };
      req.onerror = function () { enCours = false; if (compte) compte.textContent = mots.rien; };
      req.send();
    }

    function cherche() {
      var brut = champ.value.trim();
      if (!brut) { cible.innerHTML = ""; if (compte) compte.textContent = ""; return; }
      var motsNorm = normalise(brut).split(/\s+/).filter(Boolean);

      var trouves = index.map(function (d) {
        var score = 0;
        var titreN = normalise(d.t);
        motsNorm.forEach(function (m) {
          if (d._n.indexOf(m) === -1) { score = -999; return; }
          score += 1;
          if (titreN.indexOf(m) !== -1) score += 6;
          if (normalise(d.k).indexOf(m) !== -1) score += 2;
        });
        return { d: d, score: score };
      }).filter(function (r) { return r.score > 0; })
        .sort(function (a, b) { return b.score - a.score; })
        .slice(0, 30);

      if (compte) {
        compte.textContent = trouves.length
          ? trouves.length + " " + mots.res
          : mots.rien;
      }
      cible.innerHTML = trouves.map(function (r) {
        return '<li><p class="res-k">' + echappe(r.d.k) + "</p>"
          + '<h3><a href="' + echappe(r.d.u) + '">' + echappe(r.d.t) + "</a></h3>"
          + '<p class="res-b">' + extrait(r.d.b, motsNorm) + "</p></li>";
      }).join("");
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      chargeIndex(cherche);
    });
    champ.addEventListener("input", function () {
      if (index) cherche(); else chargeIndex(cherche);
    });

    var q = new RegExp("[?&]q=([^&]*)").exec(window.location.search);
    if (q) {
      champ.value = decodeURIComponent(q[1].replace(/\+/g, " "));
      chargeIndex(cherche);
    }
  }

  /* -------------------------------------------------------- init */

  function demarre() {
    initTheme();
    initChrono();
    initGlossaire();
    initRecherche();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", demarre);
  } else {
    demarre();
  }
})();
