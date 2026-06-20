// Управляет приветственной модалкой дашборда: автооткрытием, ручным запуском, шагами новичка и отключением автопоказа.
$(function () {
  const modalElement = document.getElementById("dashboardStartModal");

  // Если на странице нет приветствия или Bootstrap не загружен, тихо выходим и не мешаем остальному интерфейсу.
  if (!modalElement || typeof bootstrap === "undefined") {
    return;
  }

  const modal = new bootstrap.Modal(modalElement);
  // Ключ нужен, чтобы показывать автоприветствие не чаще одного раза за сессию конкретного пользователя.
  const sessionKey = [
    "acestaDashboardStartShown",
    modalElement.dataset.userId || "user",
    modalElement.dataset.sessionKey || "browser",
  ].join(":");
  const $modal = $(modalElement);
  let openMode = "manual";
  let beginnerStep = parseInt(modalElement.dataset.step || "1", 10);

  // sessionStorage обернут в try/catch, чтобы ограничения браузера не ломали страницу.
  function getSessionItem(key) {
    try {
      return window.sessionStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function setSessionItem(key, value) {
    try {
      window.sessionStorage.setItem(key, value);
    } catch (e) {
      return false;
    }

    return true;
  }

  // Чекбокс "Больше не показывать" виден только при автопоказе и скрывается при ручном открытии.
  function setCheckVisibility(isVisible) {
    $modal.find(".dashboard-start-check").each(function () {
      const $check = $(this);
      const shouldStayHidden = $check.attr("data-hide-after-close") === "true";

      $check.toggleClass("d-none", !isVisible || shouldStayHidden);
    });
  }

  // Переключает шаги приветствия новичка, точки-индикаторы и состояние кнопок назад/вперед.
  function setBeginnerStep(step) {
    const maxStep = 3;

    beginnerStep = Math.min(Math.max(step, 1), maxStep);
    modalElement.dataset.step = beginnerStep;
    $modal.find(".dashboard-start-beginner-dots").each(function () {
      $(this)
        .find("span")
        .removeClass("is-active")
        .eq(beginnerStep - 1)
        .addClass("is-active");
    });
    $modal.find(".dashboard-start-beginner-back").prop("disabled", beginnerStep === 1);
    $modal.find(".dashboard-start-beginner-next").toggleClass("d-none", beginnerStep === maxStep);
  }

  // При автопоказе запоминаем факт показа в сессии, а новичка всегда возвращаем на первый шаг.
  modalElement.addEventListener("shown.bs.modal", function () {
    if (openMode === "auto") {
      setSessionItem(sessionKey, "true");
    }
    if ($modal.hasClass("dashboard-start-beginner")) {
      setBeginnerStep(1);
    }
  });

  // При закрытии сбрасываем состояние новичка и прячем чекбокс до следующего автопоказа.
  modalElement.addEventListener("hidden.bs.modal", function () {
    if ($modal.hasClass("dashboard-start-beginner")) {
      setBeginnerStep(1);
    }
    setCheckVisibility(false);
  });

  if ($modal.hasClass("dashboard-start-beginner")) {
    setBeginnerStep(beginnerStep);
  }

  // Автопоказ срабатывает только если его разрешил шаблон и модалку еще не показывали в этой сессии.
  if (
    modalElement.dataset.autoShow === "true" &&
    getSessionItem(sessionKey) !== "true"
  ) {
    openMode = "auto";
    setCheckVisibility(true);
    modal.show();
  }

  // "Быстрый старт" открывает приветствие вручную, поэтому чекбокс отключения автопоказа не показываем.
  $(".dashboard-start-link").on("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    openMode = "manual";
    setCheckVisibility(false);
    modal.show();
  });

  $(".dashboard-start-beginner-next").on("click", function () {
    setBeginnerStep(beginnerStep + 1);
  });

  $(".dashboard-start-beginner-back").on("click", function () {
    setBeginnerStep(beginnerStep - 1);
  });

  // Чекбокс отправляет AJAX-запрос и отключает будущий автопоказ приветствия для пользователя.
  $("#dashboardStartDontShow").on("change", function () {
    if (!this.checked || !modalElement.dataset.hideUrl) {
      return;
    }

    const $check = $(this).closest(".dashboard-start-check");

    $.ajax({
      url: modalElement.dataset.hideUrl,
      method: "POST",
      data: {
        csrfmiddlewaretoken: csrfToken,
      },
      success: function () {
        $check.attr("data-hide-after-close", "true");
        $check.find(".form-check-input").prop("disabled", true);
        modalElement.dataset.autoShow = "";
        modal.hide();
      },
      error: function () {
        $check.find(".form-check-input").prop("checked", false);
      },
    });
  });
});
