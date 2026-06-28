(function () {
  var modal = document.getElementById("selectRegion");

  if (!modal) {
    return;
  }

  var search = modal.querySelector("[data-region-search]");
  var input = modal.querySelector("[data-region-search-input]");
  var toggle = modal.querySelector("[data-region-search-toggle]");
  var clear = modal.querySelector("[data-region-search-clear]");
  var explanation = modal.querySelector("#regionSelectionExplanation");
  var explanationToggle = modal.querySelector(
    '[href="#regionSelectionExplanation"]'
  );
  var districts = Array.prototype.slice.call(
    modal.querySelectorAll("[data-region-district]")
  );
  var empty = modal.querySelector("[data-region-search-empty]");
  var isModalClosing = false;
  var isRegionLinkActivation = false;

  function getRegionLink(target) {
    if (!target || !target.closest) {
      return null;
    }

    return target.closest("[data-region-link]");
  }

  function normalize(value) {
    return value.toLocaleLowerCase("ru-RU").replace(/ё/g, "е");
  }

  function setRegionLabel(region, query) {
    var label = region.querySelector("[data-region-label]");
    var regionName = region.dataset.regionName;
    var normalizedName = normalize(regionName);
    var position = 0;
    var matchPosition = normalizedName.indexOf(query, position);

    while (label.firstChild) {
      label.removeChild(label.firstChild);
    }

    if (!query || matchPosition === -1) {
      label.appendChild(document.createTextNode(regionName));
      return;
    }

    while (matchPosition !== -1) {
      if (matchPosition > position) {
        label.appendChild(
          document.createTextNode(regionName.slice(position, matchPosition))
        );
      }

      var mark = document.createElement("mark");

      mark.className = "region-search-match";
      mark.textContent = regionName.slice(
        matchPosition,
        matchPosition + query.length
      );
      label.appendChild(mark);

      position = matchPosition + query.length;
      matchPosition = normalizedName.indexOf(query, position);
    }

    if (position < regionName.length) {
      label.appendChild(document.createTextNode(regionName.slice(position)));
    }
  }

  function filterRegions() {
    var query = normalize(input.value.trim());
    var isActive = query.length > 0;
    var hasMatches = false;

    districts.forEach(function (district) {
      var districtHasMatches = false;
      var regions = district.querySelectorAll("[data-region-name]");

      regions.forEach(function (region) {
        var isMatch =
          !isActive || normalize(region.dataset.regionName).includes(query);

        setRegionLabel(region, isMatch ? query : "");
        region.hidden = !isMatch;
        districtHasMatches = districtHasMatches || isMatch;
      });

      district.hidden = isActive && !districtHasMatches;
      hasMatches = hasMatches || (isActive && districtHasMatches);
    });

    empty.hidden = !isActive || hasMatches;
    clear.hidden = !isActive;
  }

  function handleInput() {
    input.value = input.value.replace(/[0-9]/g, "");
    filterRegions();
  }

  function closeExplanation() {
    if (
      !explanation ||
      typeof bootstrap === "undefined" ||
      !bootstrap.Collapse
    ) {
      return;
    }

    bootstrap.Collapse.getOrCreateInstance(explanation, {
      toggle: false
    }).hide();
  }

  function resetExplanation() {
    if (!explanation) {
      return;
    }

    explanation.classList.remove("show", "collapsing");
    explanation.classList.add("collapse");
    explanation.style.removeProperty("height");

    if (explanationToggle) {
      explanationToggle.classList.add("collapsed");
      explanationToggle.setAttribute("aria-expanded", "false");
    }
  }

  function enterSearchMode() {
    closeExplanation();
    modal.classList.add("region-search-mode");
    search.classList.add("region-search-open");
    toggle.setAttribute("aria-expanded", "true");
    toggle.setAttribute("aria-label", "Поиск по регионам открыт");
    input.removeAttribute("tabindex");
    clear.removeAttribute("tabindex");
  }

  function openSearch() {
    enterSearchMode();
    input.focus();
  }

  function resetSearch() {
    input.value = "";
    filterRegions();
    modal.classList.remove("region-search-mode");
    search.classList.remove("region-search-open");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Открыть поиск по регионам");
    input.setAttribute("tabindex", "-1");
    clear.setAttribute("tabindex", "-1");
  }

  toggle.addEventListener("click", function () {
    if (!search.classList.contains("region-search-open")) {
      openSearch();
      return;
    }

    input.focus();
  });

  clear.addEventListener("click", function () {
    input.value = "";
    filterRegions();
    input.focus();
  });

  input.addEventListener("focus", enterSearchMode);
  input.addEventListener("input", handleInput);
  input.addEventListener("blur", function (event) {
    var nextFocus = event.relatedTarget;

    window.requestAnimationFrame(function () {
      if (
        isModalClosing ||
        isRegionLinkActivation ||
        getRegionLink(nextFocus) ||
        document.activeElement === input
      ) {
        return;
      }

      if (!normalize(input.value.trim())) {
        resetSearch();
      }
    });
  });
  modal.addEventListener("pointerdown", function (event) {
    if (getRegionLink(event.target)) {
      isRegionLinkActivation = true;
    }
  });
  window.addEventListener("pointerup", function () {
    isRegionLinkActivation = false;
  });
  window.addEventListener("pointercancel", function () {
    isRegionLinkActivation = false;
  });
  input.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation();
      resetSearch();
      toggle.focus();
    }
  });
  modal.addEventListener("show.bs.modal", function () {
    resetExplanation();
    isModalClosing = false;
  });
  modal.addEventListener("hide.bs.modal", function () {
    closeExplanation();
    isModalClosing = true;
  });
  modal.addEventListener("hidden.bs.modal", function () {
    resetSearch();
    resetExplanation();
    isModalClosing = false;
  });
})();
