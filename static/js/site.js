/* Motion design du site. Sans ce script, tout le contenu reste visible.
   Rien ne bouge si le visiteur a demandé moins d'animations (prefers-reduced-motion). */
(function () {
  var mouvement = window.matchMedia("(prefers-reduced-motion: no-preference)").matches;
  var souris = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  /* 1. Apparition des blocs au défilement */
  var blocs = document.querySelectorAll(".reveler");
  function montrer(bloc) {
    bloc.classList.add("vu");
    // Une fois l'apparition terminée, le bloc peut réagir à la souris sans délai.
    setTimeout(function () {
      bloc.classList.add("pret");
    }, 1100);
  }
  if ("IntersectionObserver" in window) {
    var observateur = new IntersectionObserver(
      function (entrees) {
        entrees.forEach(function (entree) {
          if (entree.isIntersecting) {
            montrer(entree.target);
            observateur.unobserve(entree.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px" }
    );
    blocs.forEach(function (bloc) {
      observateur.observe(bloc);
    });
  } else {
    blocs.forEach(montrer);
  }

  /* Visionneuse de la galerie : plein écran, flèches du clavier, balayage au doigt.
     Sans script, chaque vignette ouvre simplement l'image en grand. */
  document.querySelectorAll("[data-galerie]").forEach(function (galerie) {
    var liens = Array.prototype.slice.call(galerie.querySelectorAll(".galerie__cadre"));
    if (!liens.length || typeof HTMLDialogElement !== "function") return;
    var fleche = function (d) {
      return '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="' + d + '"/></svg>';
    };
    var boite = document.createElement("dialog");
    boite.className = "visionneuse";
    boite.setAttribute("aria-label", "Galerie d'images");
    boite.innerHTML =
      '<div class="visionneuse__scene">' +
      '<div class="visionneuse__haut"><span class="visionneuse__compte" aria-live="polite"></span>' +
      '<button type="button" data-fermer aria-label="Fermer">' + fleche("M18 6 6 18M6 6l12 12") + "</button></div>" +
      '<div class="visionneuse__image"><img alt=""></div>' +
      '<div class="visionneuse__bas">' +
      '<button type="button" data-pas="-1" aria-label="Image précédente">' + fleche("M15 18l-6-6 6-6") + "</button>" +
      '<p class="visionneuse__legende"></p>' +
      '<button type="button" data-pas="1" aria-label="Image suivante">' + fleche("M9 18l6-6-6-6") + "</button>" +
      "</div></div>";
    document.body.appendChild(boite);
    var image = boite.querySelector("img");
    var compte = boite.querySelector(".visionneuse__compte");
    var legende = boite.querySelector(".visionneuse__legende");
    var position = 0;

    function afficher(index) {
      position = (index + liens.length) % liens.length;
      var lien = liens[position];
      image.src = lien.href;
      image.alt = lien.querySelector("img").alt;
      legende.textContent = lien.dataset.legende || "";
      compte.textContent = position + 1 + " / " + liens.length;
      image.style.animation = "none";
      void image.offsetWidth;
      image.style.animation = "";
    }
    boite.querySelectorAll("[data-pas]").forEach(function (bouton) {
      bouton.hidden = liens.length < 2;
      bouton.addEventListener("click", function () {
        afficher(position + Number(bouton.dataset.pas));
      });
    });
    boite.querySelector("[data-fermer]").addEventListener("click", function () {
      boite.close();
    });
    boite.addEventListener("click", function (evenement) {
      var cible = evenement.target;
      if (cible.classList.contains("visionneuse__image") || cible.classList.contains("visionneuse__scene")) boite.close();
    });
    boite.addEventListener("keydown", function (evenement) {
      if (evenement.key === "ArrowRight") afficher(position + 1);
      if (evenement.key === "ArrowLeft") afficher(position - 1);
    });
    var departX = null;
    boite.addEventListener("touchstart", function (evenement) {
      departX = evenement.touches[0].clientX;
    }, { passive: true });
    boite.addEventListener("touchend", function (evenement) {
      if (departX === null) return;
      var ecart = evenement.changedTouches[0].clientX - departX;
      if (Math.abs(ecart) > 50 && liens.length > 1) afficher(position + (ecart < 0 ? 1 : -1));
      departX = null;
    });
    liens.forEach(function (lien, index) {
      lien.addEventListener("click", function (evenement) {
        if (evenement.metaKey || evenement.ctrlKey || evenement.shiftKey) return;
        evenement.preventDefault();
        afficher(index);
        boite.showModal();
      });
    });
  });

  if (!mouvement || !souris) return;

  /* 2. Inclinaison en 3D et halo qui suit la souris (cartes de projet, photo) */
  document.querySelectorAll("[data-incliner]").forEach(function (element) {
    var force = parseFloat(element.dataset.incliner) || 4;
    element.addEventListener("pointermove", function (evenement) {
      var cadre = element.getBoundingClientRect();
      var x = (evenement.clientX - cadre.left) / cadre.width;
      var y = (evenement.clientY - cadre.top) / cadre.height;
      element.style.setProperty("--ry", ((x - 0.5) * 2 * force).toFixed(2) + "deg");
      element.style.setProperty("--rx", ((0.5 - y) * 2 * force).toFixed(2) + "deg");
      element.style.setProperty("--mx", Math.round(evenement.clientX - cadre.left) + "px");
      element.style.setProperty("--my", Math.round(evenement.clientY - cadre.top) + "px");
    });
    element.addEventListener("pointerleave", function () {
      element.style.setProperty("--rx", "0deg");
      element.style.setProperty("--ry", "0deg");
    });
  });

  /* 3. Boutons « aimantés » : ils suivent légèrement la souris */
  document.querySelectorAll("[data-aimant]").forEach(function (bouton) {
    bouton.addEventListener("pointermove", function (evenement) {
      var cadre = bouton.getBoundingClientRect();
      var x = (evenement.clientX - cadre.left) / cadre.width - 0.5;
      var y = (evenement.clientY - cadre.top) / cadre.height - 0.5;
      bouton.style.setProperty("--ax", (x * 14).toFixed(1) + "px");
      bouton.style.setProperty("--ay", (y * 10).toFixed(1) + "px");
    });
    bouton.addEventListener("pointerleave", function () {
      bouton.style.setProperty("--ax", "0px");
      bouton.style.setProperty("--ay", "0px");
    });
  });
})();
