(function () {
  var list = document.querySelector("[data-sight-list]");

  if (!list) {
    return;
  }

  var search = list.querySelector("[data-sight-search]");
  var input = list.querySelector("[data-sight-search-input]");
  var toggle = list.querySelector("[data-sight-search-toggle]");
  var clear = list.querySelector("[data-sight-search-clear]");
  var empty = list.querySelector("[data-sight-search-empty]");
  var rowsContainer = list.querySelector("[data-sight-rows]");
  var loadError = list.querySelector("[data-sight-load-error]");
  var loadRetry = list.querySelector("[data-sight-load-retry]");
  var loader = document.querySelector("#loader");
  var loadUrl = list.dataset.sightLoadUrl;
  var rows = Array.prototype.slice.call(
    list.querySelectorAll("[data-sight-row]")
  );
  var isControlActivation = false;

  function normalize(value) {
    return value.toLocaleLowerCase("ru-RU").replace(/ё/g, "е");
  }

  function setSightLabel(row, query) {
    var label = row.querySelector("[data-sight-label]");
    var sightName = row.dataset.sightName;
    var normalizedName = normalize(sightName);
    var position = 0;
    var matchPosition = normalizedName.indexOf(query, position);

    while (label.firstChild) {
      label.removeChild(label.firstChild);
    }

    if (!query || matchPosition === -1) {
      label.appendChild(document.createTextNode(sightName));
      return;
    }

    while (matchPosition !== -1) {
      if (matchPosition > position) {
        label.appendChild(
          document.createTextNode(sightName.slice(position, matchPosition))
        );
      }

      var mark = document.createElement("mark");

      mark.className = "sight-search-match";
      mark.textContent = sightName.slice(
        matchPosition,
        matchPosition + query.length
      );
      label.appendChild(mark);

      position = matchPosition + query.length;
      matchPosition = normalizedName.indexOf(query, position);
    }

    if (position < sightName.length) {
      label.appendChild(document.createTextNode(sightName.slice(position)));
    }
  }

  function filterSights() {
    var query = normalize(input.value.trim());
    var isActive = query.length > 0;
    var hasMatches = false;

    rows.forEach(function (row) {
      var isMatch =
        !isActive || normalize(row.dataset.sightName).includes(query);

      setSightLabel(row, isMatch ? query : "");
      row.hidden = !isMatch;
      hasMatches = hasMatches || isMatch;
    });

    empty.hidden = !isActive || hasMatches;
    clear.hidden = !isActive;
  }

  function enterSearchMode() {
    list.classList.add("sight-search-mode");
    search.classList.add("sight-search-open");
    toggle.setAttribute("aria-expanded", "true");
    toggle.setAttribute("aria-label", "Поиск точек притяжения открыт");
    input.removeAttribute("tabindex");
    clear.removeAttribute("tabindex");
  }

  function openSearch() {
    enterSearchMode();
    input.focus();
  }

  function setSearchEnabled(isEnabled) {
    toggle.disabled = !isEnabled;

    if (isEnabled) {
      toggle.removeAttribute("aria-disabled");
      toggle.setAttribute("aria-label", "Открыть поиск точек притяжения");
      toggle.setAttribute("title", "Найти точку притяжения");
      return;
    }

    toggle.setAttribute("aria-disabled", "true");
    toggle.setAttribute("aria-label", "Список точек загружается");
    toggle.setAttribute("title", "Список точек загружается");
  }

  function setLoaderVisible(isVisible) {
    if (!loader) {
      return;
    }

    loader.style.display = isVisible ? "block" : "none";
  }

  function initializeTooltips(root) {
    if (!window.bootstrap || !bootstrap.Tooltip) {
      return;
    }

    Array.prototype.forEach.call(
      root.querySelectorAll('[data-bs-toggle="tooltip"]'),
      function (tooltipTrigger) {
        bootstrap.Tooltip.getOrCreateInstance(tooltipTrigger);
      }
    );
  }

  function loadRemainingSights() {
    if (!loadUrl) {
      setSearchEnabled(true);
      return;
    }

    loadError.hidden = true;
    list.setAttribute("aria-busy", "true");
    setLoaderVisible(true);

    fetch(loadUrl, {
      credentials: "same-origin",
      headers: {"X-Requested-With": "XMLHttpRequest"},
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Sight list loading failed");
        }

        return response.text();
      })
      .then(function (html) {
        var template = document.createElement("template");

        template.innerHTML = html;
        rowsContainer.appendChild(template.content);
        initializeTooltips(rowsContainer);
        rows = Array.prototype.slice.call(
          list.querySelectorAll("[data-sight-row]")
        );
        filterSights();
        loadUrl = "";
        list.removeAttribute("data-sight-load-url");
        setSearchEnabled(true);
      })
      .catch(function () {
        loadError.hidden = false;
      })
      .then(function () {
        list.removeAttribute("aria-busy");
        setLoaderVisible(false);
      });
  }

  function scheduleRemainingSightsLoad() {
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(loadRemainingSights);
    });
  }

  function resetSearch() {
    input.value = "";
    filterSights();
    list.classList.remove("sight-search-mode");
    search.classList.remove("sight-search-open");
    toggle.setAttribute("aria-expanded", "false");
    setSearchEnabled(!toggle.disabled);
    input.setAttribute("tabindex", "-1");
    clear.setAttribute("tabindex", "-1");
  }

  toggle.addEventListener("click", function () {
    if (!search.classList.contains("sight-search-open")) {
      openSearch();
      return;
    }

    input.focus();
  });

  loadRetry.addEventListener("click", loadRemainingSights);

  clear.addEventListener("click", function () {
    input.value = "";
    filterSights();
    input.focus();
  });

  input.addEventListener("focus", enterSearchMode);
  input.addEventListener("input", filterSights);
  input.addEventListener("blur", function () {
    window.requestAnimationFrame(function () {
      if (
        isControlActivation ||
        document.activeElement === input ||
        normalize(input.value.trim())
      ) {
        return;
      }

      resetSearch();
    });
  });
  input.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation();
      resetSearch();
      toggle.focus();
    }
  });
  list.addEventListener("pointerdown", function (event) {
    if (event.target.closest("a, button, input, select, .select2-container")) {
      isControlActivation = true;
    }
  });
  window.addEventListener("pointerup", function () {
    if (!isControlActivation) {
      return;
    }

    window.setTimeout(function () {
      isControlActivation = false;
      if (
        document.activeElement !== input &&
        !normalize(input.value.trim())
      ) {
        resetSearch();
      }
    }, 0);
  });
  window.addEventListener("pointercancel", function () {
    isControlActivation = false;
  });

  if (loadUrl) {
    setSearchEnabled(false);
    scheduleRemainingSightsLoad();
  } else {
    setSearchEnabled(true);
  }
})();
