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
