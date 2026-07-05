(function () {
  "use strict";

  var observer;
  var initializationFrame = null;

  function disposeTooltips(root) {
    if (!window.bootstrap || !bootstrap.Tooltip || !root) {
      return;
    }

    var triggers = [];
    if (root.nodeType === Node.ELEMENT_NODE && root.matches("[data-bs-toggle='tooltip']")) {
      triggers.push(root);
    }
    if (root.querySelectorAll) {
      triggers = triggers.concat(
        Array.prototype.slice.call(
          root.querySelectorAll("[data-bs-toggle='tooltip']")
        )
      );
    }
    triggers.forEach(function (trigger) {
      var tooltip = bootstrap.Tooltip.getInstance(trigger);
      if (tooltip) {
        tooltip.dispose();
      }
    });
  }

  function initializeTooltips() {
    initializationFrame = null;
    if (!window.bootstrap || !bootstrap.Tooltip) {
      window.setTimeout(scheduleInitialization, 50);
      return;
    }

    document
      .querySelectorAll("#audience [data-bs-toggle='tooltip']")
      .forEach(function (trigger) {
        bootstrap.Tooltip.getOrCreateInstance(trigger);
      });
  }

  function scheduleInitialization() {
    if (initializationFrame !== null) {
      return;
    }
    initializationFrame = window.requestAnimationFrame(initializeTooltips);
  }

  function startObserver() {
    var audience = document.querySelector("#audience");
    if (!audience) {
      window.setTimeout(startObserver, 50);
      return;
    }

    observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        mutation.removedNodes.forEach(disposeTooltips);
      });
      scheduleInitialization();
    });
    observer.observe(audience, {childList: true, subtree: true});
    scheduleInitialization();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startObserver);
  } else {
    startObserver();
  }
})();
