(function () {
  "use strict";

  window.dash_clientside = window.dash_clientside || {};
  window.dash_clientside.clientside = Object.assign(
    {},
    window.dash_clientside.clientside,
    {
      renderAudience: function (data) {
        function h(type, props, children) {
          var componentProps = Object.assign({}, props || {});
          if (typeof children !== "undefined") {
            componentProps.children = children;
          }
          return {
            namespace: "dash_html_components",
            type: type,
            props: componentProps,
          };
        }

        function metric(label, value, className) {
          return h("P", {className: className || "text-end"}, [
            label,
            h("B", {}, value),
          ]);
        }

        data = data || {};
        if (data.empty) {
          return h(
            "P",
            {className: "text-muted pt-2 ps-1"},
            h("Small", {}, data.empty)
          );
        }

        var indicators = data.indicators || {};
        return (data.groups || []).map(function (group) {
          var details = [
            metric("есть пара ", group.p),
            metric("дети до 6 лет ", group.c6),
            metric("дети от 7 до 12 лет ", group.c12),
            h("P", {className: "mb-0 text-end"}, [
              "отношения ",
              h("Span", {className: "d-none d-lg-inline"}, "с родителями "),
              h("Span", {className: "d-inline d-lg-none"}, "с род. "),
              h("B", {}, group.pr),
            ]),
          ];

          if (indicators.salary || indicators.bill) {
            details.push(h("Hr", {}));
          }
          if (indicators.salary) {
            details.push(
              h("P", {className: "mb-0 text-end"}, [
                h("Span", {className: "d-none d-lg-inline"}, "средняя зарплата "),
                h("Span", {className: "d-inline d-lg-none"}, "ср. зарплата "),
                h("Strong", {}, indicators.salary),
              ])
            );
          }
          if (indicators.bill) {
            details.push(
              h("P", {className: "mb-0 text-end"}, [
                h("Span", {className: "d-none d-lg-inline"}, "средний чек "),
                h("Span", {className: "d-inline d-lg-none"}, "ср. чек "),
                h("Strong", {}, indicators.bill),
              ])
            );
          }
          if (indicators.change) {
            details.push(
              h("P", {className: "mb-0 text-end"}, [
                h("Span", {className: "d-none d-xl-inline"}, "изменение среднего чека "),
                h("Span", {className: "d-none d-lg-inline d-xl-none"}, "изменение ср. чека "),
                h("Span", {className: "d-inline d-lg-none"}, "изм. ср. чека "),
                h(
                  "Strong",
                  {
                    className: "colored-percentage",
                    "data-value": indicators.changeSign,
                  },
                  indicators.change
                ),
              ])
            );
          }

          var children = [
            h(
              "Div",
              {className: "d-flex justify-content-between px-3 audience-main-container"},
              [
                h("Div", {}, [
                  h("Div", {className: "audience-qty"}, group.q),
                  h("P", {className: "audience-sex mb-0 " + group.sc}, group.s),
                  h("P", {className: "audience-age mb-0"}, group.a),
                ]),
                h("Div", {
                  className: "audience-tourism-type bg-" + group.t,
                  "data-bs-toggle": "tooltip",
                  "data-bs-title": group.tt,
                  "data-bs-placement": "bottom",
                }),
              ]
            ),
            h(
              "Div",
              {className: "my-2 audience-more px-3", style: {fontSize: "13px"}},
              details
            ),
          ];
          if (group.priority) {
            children.push(
              h(
                "Div",
                {className: "px-3 metric metric-interest rank-4 audience-priority-group"},
                "☆ Приоритетная группа"
              )
            );
          }
          return h(
            "Div",
            {className: "audience-group me-3 border rounded-2 p-0 border-" + group.t},
            children
          );
        });
      },
    }
  );

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
