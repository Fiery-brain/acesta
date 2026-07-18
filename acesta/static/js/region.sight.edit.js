(function () {
  "use strict";

  function bindSubmitState(inputs, submit) {
    function update() {
      submit.disabled = inputs.some(function (input) {
        return !input.value.trim();
      });
    }

    inputs.forEach(function (input) {
      input.addEventListener("input", update);
    });
    update();
    return update;
  }

  const addModalElement = document.querySelector("#addSight");
  if (addModalElement) {
    bindSubmitState(
      [addModalElement.querySelector("[data-sight-add-message-input]")],
      addModalElement.querySelector("[data-sight-add-submit]")
    );
  }

  const modalElement = document.querySelector("#editSight");
  if (!modalElement) return;

  const loading = modalElement.querySelector("[data-sight-edit-loading]");
  const message = modalElement.querySelector("[data-sight-edit-message]");
  const messageText = modalElement.querySelector("[data-sight-edit-message-text]");
  const details = modalElement.querySelector("[data-sight-edit-details]");
  const sightInput = modalElement.querySelector("[data-sight-edit-input]");
  const messageInput = modalElement.querySelector("[data-sight-edit-message-input]");
  const submit = modalElement.querySelector("[data-sight-edit-submit]");
  const retry = modalElement.querySelector("[data-sight-edit-retry]");
  const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
  const urlTemplate = modalElement.dataset.sightEditUrl;
  let requestController = null;
  let activeSightId = null;

  function setState(state, text) {
    loading.hidden = state !== "loading";
    message.hidden = state !== "message";
    details.hidden = state !== "content";
    messageText.textContent = text || "";
  }

  const updateSubmitState = bindSubmitState(
    [sightInput, messageInput],
    submit
  );

  function getTooltipTriggers(root) {
    return root.querySelectorAll('[data-bs-toggle="tooltip"]');
  }

  function disposeTooltips(root) {
    if (!window.bootstrap || !bootstrap.Tooltip) return;

    getTooltipTriggers(root).forEach(function (tooltipTrigger) {
      const tooltip = bootstrap.Tooltip.getInstance(tooltipTrigger);
      if (tooltip) tooltip.dispose();
    });
  }

  function initializeTooltips(root) {
    if (!window.bootstrap || !bootstrap.Tooltip) return;

    getTooltipTriggers(root).forEach(function (tooltipTrigger) {
      bootstrap.Tooltip.getOrCreateInstance(tooltipTrigger);
    });
  }

  function clearDetails() {
    disposeTooltips(details);
    details.replaceChildren();
  }

  function reset() {
    if (requestController) requestController.abort();
    requestController = null;
    sightInput.value = "";
    messageInput.value = "";
    clearDetails();
    setState("loading");
    updateSubmitState();
  }

  async function load() {
    if (!activeSightId) return;
    if (requestController) requestController.abort();
    requestController = new AbortController();
    sightInput.value = "";
    clearDetails();
    setState("loading");
    updateSubmitState();
    const url = urlTemplate.replace("/0/change/", `/${activeSightId}/change/`);

    try {
      const response = await fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        signal: requestController.signal,
      });
      if (!response.ok) throw new Error("request_failed");
      const data = await response.json();
      disposeTooltips(details);
      details.innerHTML = data.details_html || "";
      sightInput.value = data.sight_id || "";
      setState("content");
      requestAnimationFrame(function () {
        initializeTooltips(details);
      });
      updateSubmitState();
    } catch (error) {
      if (error.name !== "AbortError") {
        console.error("Sight edit error", error);
        setState(
          "message",
          "Не удалось загрузить информацию о точке. Попробуйте ещё раз."
        );
      }
    }
  }

  function open(sightId) {
    reset();
    activeSightId = sightId;
    modal.show();
    load();
  }

  document.addEventListener(
    "click",
    function (event) {
      const trigger = event.target.closest("[data-sight-edit-id]");
      if (!trigger) return;
      event.preventDefault();
      event.stopPropagation();
      open(trigger.dataset.sightEditId);
    },
    true
  );

  retry.addEventListener("click", load);
  modalElement.addEventListener("hidden.bs.modal", function () {
    activeSightId = null;
    reset();
  });
})();
