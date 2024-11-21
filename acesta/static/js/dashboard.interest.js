let splitter;
let containerHeight = window.innerHeight - 40 - 100;
let interestHeight = Math.round(
  ((containerHeight - 164) / containerHeight) * 100
);

function defineSplitter() {
  splitter = $("#content")
    .height(containerHeight)
    .split({
      orientation: "horizontal",
      limit: 2,
      position: interestHeight + "%",
      onDrag: function (event) {
        if ($("#audience-container").height() <= 160) {
          splitter.position(interestHeight + "%");
        }
      },
    });
}
function updateSplitter() {
  if (typeof splitter !== "undefined") {
    if (window.innerWidth >= 992) {
      splitter.refresh();
    } else {
      splitter.destroy();
      splitter = undefined;
    }
  } else {
    if (window.innerWidth >= 992) {
      defineSplitter();
    }
  }
}

$(function () {
  let rtime;
  let timeout = false;
  let delta = 200;
  $(window).resize(function () {
    rtime = new Date();
    if (timeout === false) {
      timeout = true;
      setTimeout(location.reload(), delta);
    }
  });

  updateSplitter();
  $(window).on("resize", function (e) {
    updateSplitter();
  });

  $("title").bind("DOMSubtreeModified", function (e) {
    if ($(this).text().includes("...")) {
      $("#loader").css("display", "block");
    } else {
      $("#loader").css("display", "none");
    }
  });
  $("#interest-container").bind("DOMSubtreeModified", function (e) {
    if (e.target.id == "react-select-2--list") {
      $(".Select-noresults").text("Вид не найден");
    }
    if (e.target.tagName.toLowerCase() == "h3") {
      $("#title-container").attr("type", "button");
      $("#title-container").attr("title", $("#title").text());
    }
    if (
      e.target.tagName.toLowerCase() == "div" &&
      e.target.className == "dt-table-container__row dt-table-container__row-1"
    ) {
      $(".column-header-name").each(function () {
        if ($(this).parent().parent().attr("class").includes("column-1")) {
          $(this).html(
            $(this).text() +
              '<a href="#" class="ms-1" data-bs-toggle="tooltip" title="Количество запросов туристических объектов за&nbsp;месяц"><svg fill="#939699" width="22" height="22"><use href="/static/img/sprite.svg#help"></use></svg></a>'
          );
        } else if (
          $(this).parent().parent().attr("class").includes("column-2")
        ) {
          $(this).html(
            $(this).text() +
              '<a href="#" class="ms-1" data-bs-toggle="tooltip" title="Региональная популярность или&nbsp;доля, которую занимает регион в&nbsp;показах запросу туристических объектов, деленная на&nbsp;долю всех показов результатов в&nbsp;регионе. Если популярность более 100%, это означает, что в&nbsp;данном регионе существует повышенный интерес к&nbsp;этому запросу, если меньше 100% - пониженный."><svg fill="#939699" width="22" height="22"><use href="/static/img/sprite.svg#help"></use></svg></a>'
          );
        }
      });
      $("#map-container").css("minHeight", containerHeight - 242 + "px");
    }
  });

  $(window).on("load", function() {

    $("#updated-link").attr("title", $("#updated-link").attr("data-title"))
    $("#updated-link").html(
      '<svg width="22" height="22"><use href="/static/img/sprite.svg#updated"></use></svg>'
    )

    var tooltipTriggerList = [].slice.call(
      document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  });
});
