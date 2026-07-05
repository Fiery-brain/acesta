(function () {
  "use strict";

  const modalElement = document.querySelector("#historyModal");
  if (!modalElement) return;

  const loading = modalElement.querySelector("[data-history-loading]");
  const content = modalElement.querySelector("[data-history-content]");
  const message = modalElement.querySelector("[data-history-message]");
  const header = modalElement.querySelector("[data-history-header]");
  const chart = modalElement.querySelector("[data-history-chart]");
  const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
  let requestController = null;
  let hoverObserver = null;

  const colors = {
    qty: "#a3a6aa",
    mean: "#429388",
    place: "#429388",
  };

  function setState(state, text) {
    loading.hidden = state !== "loading";
    content.hidden = state !== "content";
    message.hidden = state !== "message";
    message.textContent = text || "";
  }

  function addMonths(date, count) {
    const result = new Date(date.getTime());
    result.setUTCMonth(result.getUTCMonth() + count);
    return result;
  }

  function addDays(date, count) {
    const result = new Date(date.getTime());
    result.setUTCDate(result.getUTCDate() + count);
    return result;
  }

  function tooltipTemplate(series, forecast) {
    const value = series.unit === "%" ? "%{y:,.0f}%" : "%{y:,.0f}";
    const type = forecast ? "Прогноз" : "%{customdata[0]}";
    return `<b>%{x|%B %Y}</b><br>${series.name}: ${value}<br>${type}<extra></extra>`;
  }

  function lineStyle(series, color, dash) {
    const line = { color: color, width: 3, shape: "linear" };
    if (series.id !== "place") {
      line.shape = "spline";
      line.smoothing = 0.45;
    }
    if (dash) line.dash = dash;
    return line;
  }

  function placeTickStep(payload) {
    const placeSeries = payload.series.find((series) => series.id === "place");
    if (!placeSeries) return 1;
    const values = (placeSeries.points || [])
      .concat(placeSeries.forecast || [])
      .map((point) => point.value)
      .filter((value) => Number.isFinite(value));
    if (!values.length) return 1;

    const span = Math.max(...values) - Math.min(...values);
    const rawStep = Math.max(1, Math.ceil(span / 10));
    const magnitude = 10 ** Math.floor(Math.log10(rawStep));
    const normalized = rawStep / magnitude;
    const multiplier =
      normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 3 ? 3 : normalized <= 5 ? 5 : 10;
    return multiplier * magnitude;
  }

  function compactUnifiedHover() {
    const legend = chart.querySelector(".hoverlayer .legend");
    const title = legend && legend.querySelector(".legendtitletext");
    const groups = legend && legend.querySelector(".groups");
    const firstTrace = groups && groups.querySelector(".traces");
    const background = legend && legend.querySelector(".bg");
    if (!title || !groups || !firstTrace || !background) {
      return;
    }

    const offset = Math.max(
      0,
      firstTrace.getBoundingClientRect().top -
        background.getBoundingClientRect().top -
        2
    );
    const height = Number.parseFloat(background.getAttribute("height"));
    title.remove();
    groups.setAttribute("transform", `translate(0, -${offset})`);
    if (Number.isFinite(height)) {
      background.setAttribute("height", Math.max(0, height - offset));
    }
  }

  function observeUnifiedHover() {
    if (hoverObserver) hoverObserver.disconnect();
    const hoverLayer = chart.querySelector(".hoverlayer");
    if (!hoverLayer) return;
    hoverObserver = new MutationObserver(compactUnifiedHover);
    hoverObserver.observe(hoverLayer, { childList: true, subtree: true });
  }

  function buildTraces(payload) {
    const traces = [];
    payload.series.forEach(function (series) {
      const color = colors[series.id] || "#429388";
      const actual = series.points || [];
      const forecast = series.forecast || [];
      traces.push({
        type: "scatter",
        mode: "lines+markers",
        name: series.name,
        legendgroup: series.id,
        x: actual.map((point) => point.date),
        y: actual.map((point) => point.value),
        customdata: actual.map((point) => [point.is_imputed ? "Расчётное значение" : "Фактические данные", point.is_imputed]),
        meta: { pointClass: actual.map((point) => point.is_imputed ? "is-imputed" : "is-actual") },
        yaxis: series.axis,
        line: lineStyle(series, color),
        marker: { color: color, size: 8 },
        hovertemplate: tooltipTemplate(series, false),
      });
      if (forecast.length) {
        const bridge = actual.length ? [actual[actual.length - 1]] : [];
        const forecastPoints = bridge.concat(forecast);
        traces.push({
          type: "scatter",
          mode: "lines",
          name: `${series.name} — прогноз`,
          legendgroup: series.id,
          showlegend: false,
          x: forecastPoints.map((point) => point.date),
          y: forecastPoints.map((point) => point.value),
          yaxis: series.axis,
          line: lineStyle(series, color, "dot"),
          hoverinfo: "skip",
        });
        traces.push({
          type: "scatter",
          mode: "markers",
          name: `${series.name} — прогноз`,
          legendgroup: series.id,
          showlegend: false,
          x: forecast.map((point) => point.date),
          y: forecast.map((point) => point.value),
          customdata: forecast.map(() => ["Прогноз"]),
          yaxis: series.axis,
          marker: { color: "#ffffff", size: 8, line: { color: color, width: 2 } },
          hovertemplate: tooltipTemplate(series, true),
        });
      }
    });
    return traces;
  }

  function renderChart(payload) {
    const dates = payload.series.flatMap((series) =>
      (series.points || []).concat(series.forecast || []).map((point) => point.date)
    );
    if (!dates.length) {
      setState("message", "История пока отсутствует.");
      return;
    }
    dates.sort();
    const rangeEnd = addDays(
      new Date(`${dates[dates.length - 1]}T00:00:00Z`),
      15
    );
    const historyEndDates = payload.series.flatMap((series) => (series.points || []).map((point) => point.date)).sort();
    const historyEnd = new Date(`${historyEndDates[historyEndDates.length - 1]}T00:00:00Z`);
    const rangeStart = addDays(addMonths(historyEnd, -11), -15);
    const hasSecondAxis = payload.series.some((series) => series.axis === "y2");
    const layout = {
      autosize: true,
      margin: { l: 62, r: hasSecondAxis ? 68 : 28, t: 18, b: 30 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      font: { family: "Golos, sans-serif", color: "#343434", size: 13 },
      hovermode: "x unified",
      hoverdistance: 10,
      hoverlabel: {
        bgcolor: "#ffffff",
        bordercolor: "#d8d8d8",
        font: { color: "#343434" },
      },
      legend: { orientation: "h", x: 0, y: 1.08, groupclick: "togglegroup" },
      xaxis: {
        type: "date",
        range: [rangeStart.toISOString(), rangeEnd.toISOString()],
        dtick: "M3",
        nticks: 10,
        ticklabelstandoff: 8,
        showgrid: true,
        gridcolor: "#eeeeee",
        showspikes: true,
        spikemode: "across",
        spikesnap: "cursor",
        spikedash: "dot",
        spikecolor: "#939699",
        // rangeselector: {
        //   x: 0,
        //   y: 1.18,
        //   buttons: [
        //     { count: 6, label: "6 месяцев", step: "month", stepmode: "backward" },
        //     { count: 12, label: "1 год", step: "month", stepmode: "backward" },
        //     { count: 24, label: "2 года", step: "month", stepmode: "backward" },
        //     { step: "all", label: "Весь период" },
        //   ],
        // },
        rangeslider: {
          visible: true,
          thickness: 0.08,
          bgcolor: "#f4f4f4",
          bordercolor: "#dedede",
          borderwidth: 1,
        },
        color: "#a3a6aa",
      },
      yaxis: {
        title: payload.reverse_axis ? "Место" : "Запросы",
        autorange: payload.reverse_axis ? "reversed" : true,
        dtick: payload.reverse_axis ? placeTickStep(payload) : null,
        // tickmode: "auto",
        // nticks: 10,
        showgrid: true,
        gridcolor: "#eeeeee",
        zeroline: false,
        color: "#a3a6aa", //colors[series.id], // ||
      },
    };
    if (payload.reverse_axis) {
      layout.yaxis.tickmode = "linear";
      layout.yaxis.tick0 = 0;
      layout.yaxis.tickformat = ",.0f";
    }
    if (!payload.reverse_axis) layout.yaxis.rangemode = "tozero";
    if (hasSecondAxis) {
      layout.yaxis2 = {
        title: "Популярность, %",
        overlaying: "y",
        side: "right",
        rangemode: "tozero",
        showgrid: false,
        zeroline: false,
        color: "#3F958C", //colors[series.id]// ||
      };
    }
    const config = {
      responsive: true,
      locale: "ru",
      displaylogo: false,
      scrollZoom: true,
      displayModeBar: false,
      doubleClick: "reset",
    };
    Plotly.react(chart, buildTraces(payload), layout, config).then(function () {
      observeUnifiedHover();
      setState("content");
      Plotly.Plots.resize(chart);
    });
  }

  async function open(payload) {
    if (!payload || !payload.domain || !payload.entity_type || !payload.entity_id) return;
    if (requestController) requestController.abort();
    requestController = new AbortController();
    header.replaceChildren();
    setState("loading");
    modal.show();
    const params = new URLSearchParams(payload);
    try {
      const response = await fetch(`${window.acestaHistoryUrl}?${params}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        signal: requestController.signal,
      });
      if (!response.ok) throw new Error("request_failed");
      const data = await response.json();
      header.innerHTML = data.header_html || "";
      renderChart(data);
    } catch (error) {
      if (error.name !== "AbortError") {
        console.error("History chart error", error);
        setState("message", "Не удалось загрузить историю. Попробуйте ещё раз.");
      }
    }
  }

  window.AcestaHistory = { open: open };

  document.addEventListener("click", function (event) {
    const trigger = event.target.closest("[data-history-domain]");
    if (!trigger) return;
    event.preventDefault();
    event.stopPropagation();
    open({
      domain: trigger.dataset.historyDomain,
      entity_type: trigger.dataset.historyEntityType,
      entity_id: trigger.dataset.historyEntityId,
    });
  }, true);

  modalElement.addEventListener("hidden.bs.modal", function () {
    if (requestController) requestController.abort();
    if (hoverObserver) hoverObserver.disconnect();
    if (window.Plotly && chart.data) Plotly.purge(chart);
  });
})();
