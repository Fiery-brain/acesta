document.addEventListener("DOMContentLoaded", function () {
  function updateCompactLink(block) {
    var compactLink = block ? block.querySelector("[data-rating-compact]") : null;

    if (!compactLink) {
      return;
    }

    if (
      block.querySelector(".rating-region-extra-opened") ||
      block.querySelector(".rating-region-gap.d-none")
    ) {
      compactLink.classList.add("rating-region-compact-visible");
    } else {
      compactLink.classList.remove("rating-region-compact-visible");
    }
  }

  document.querySelectorAll(".rating-region-gap").forEach(function (gapRow) {
    gapRow.addEventListener("click", function () {
      var block = gapRow.closest(".rating-region-block");
      var currentRow = gapRow.previousElementSibling;

      while (currentRow && currentRow.classList.contains("rating-region-extra")) {
        currentRow.classList.add("rating-region-extra-opened");
        currentRow = currentRow.previousElementSibling;
      }

      gapRow.classList.add("d-none");
      updateCompactLink(block);
    });
  });

  document.querySelectorAll("[data-rating-compact]").forEach(function (button) {
    button.addEventListener("click", function () {
      var block = button.closest(".rating-region-block");

      if (!block) {
        return;
      }

      block.querySelectorAll(".rating-region-extra-opened").forEach(function (row) {
        row.classList.remove("rating-region-extra-opened");
      });
      block.querySelectorAll(".rating-region-gap").forEach(function (gapRow) {
        gapRow.classList.remove("d-none");
      });
      updateCompactLink(block);
    });
  });
});
