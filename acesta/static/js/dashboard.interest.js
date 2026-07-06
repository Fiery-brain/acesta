let splitter;
let splitterRatio;
let interestLayoutFrame;
let interestLayoutUpdatesPanels = false;
const interestDesktopWidth = 992;
const interestPageOffset = 140;
const interestAudienceHeight = 164;
const interestSplitterHintCookie = "acesta_interest_splitter_hint_hidden";
const interestSplitterHintCookieDays = 90;
// Splitter positions sit at their center, so 163 keeps the visible panel >= 160px.
const interestMinimumPanelHeight = 163;

function getInterestContainerHeight() {
  return Math.max(
    interestMinimumPanelHeight * 2 + 5,
    window.innerHeight - interestPageOffset
  );
}

function getSplitterPosition() {
  if (typeof splitter === "undefined") {
    return null;
  }
  var position = splitter.position();
  if (Array.isArray(position)) {
    position = position[0];
  }
  position = Number(position);
  return Number.isFinite(position) ? position : null;
}

function clampInterestPosition(position, height) {
  return Math.min(
    Math.max(position, interestMinimumPanelHeight),
    height - interestMinimumPanelHeight
  );
}

function rememberSplitterRatio() {
  var position = getSplitterPosition();
  var height = $("#content").height();
  if (position !== null && height > 0) {
    splitterRatio = position / height;
  }
}

function hasInterestCookie(name) {
  return document.cookie.split(";").some(function (cookie) {
    return cookie.trim().indexOf(encodeURIComponent(name) + "=") === 0;
  });
}

function hideInterestSplitterHint() {
  var hint = document.querySelector("#interest-splitter-hint");
  if (hint) {
    hint.classList.remove("is-visible");
  }
}

function dismissInterestSplitterHint() {
  hideInterestSplitterHint();
  var expires = new Date();
  expires.setDate(expires.getDate() + interestSplitterHintCookieDays);
  document.cookie =
    encodeURIComponent(interestSplitterHintCookie) +
    "=1; expires=" +
    expires.toUTCString() +
    "; path=/; SameSite=Lax";
}

function defineSplitter() {
  var containerHeight = getInterestContainerHeight();
  var position = clampInterestPosition(
    Number.isFinite(splitterRatio)
      ? splitterRatio * containerHeight
      : containerHeight - interestAudienceHeight,
    containerHeight
  );

  $("#content").height(containerHeight);
  splitter = $("#content").split({
    orientation: "horizontal",
    limit: {
      leftUpper: interestMinimumPanelHeight,
      rightBottom: interestMinimumPanelHeight,
    },
    position: position,
    onDrag: function () {
      dismissInterestSplitterHint();
      rememberSplitterRatio();
      scheduleInterestLayout(false);
    },
  });
  splitterRatio = position / containerHeight;
}

function updateSplitter() {
  var isDesktop = window.innerWidth >= interestDesktopWidth;
  if (typeof splitter !== "undefined") {
    if (isDesktop) {
      var containerHeight = getInterestContainerHeight();
      $("#content").height(containerHeight);
      splitter.refresh();
      splitter.position(
        clampInterestPosition(splitterRatio * containerHeight, containerHeight)
      );
    } else {
      splitter.destroy();
      splitter = undefined;
      $("#content").css("height", "");
    }
  } else if (isDesktop) {
    defineSplitter();
  }
}

function applyInterestPanelHeights() {
  var interest = document.querySelector("#interest-container");
  if (!interest) {
    return;
  }

  var table = interest.querySelector("#interest-table-container");
  var stage = interest.querySelector(".interest-map-stage");
  var map = interest.querySelector("#map");
  var mapContainer = interest.querySelector("#map-container");

  if (window.innerWidth < interestDesktopWidth) {
    [table, stage, map, mapContainer].forEach(function (element) {
      if (element) {
        element.style.removeProperty("height");
        element.style.removeProperty("max-height");
        element.style.removeProperty("min-height");
      }
    });
    return;
  }

  var topPanel = document.querySelector("#content > .top_panel");
  var topHeight = topPanel ? topPanel.clientHeight : interest.clientHeight;
  if (!topHeight) {
    return;
  }

  var tableHeight = Math.max(80, topHeight - 128);
  var mapHeight = Math.max(120, topHeight - 99);
  if (table) {
    table.style.maxHeight = Math.round(tableHeight) + "px";
  }
  if (stage) {
    stage.style.height = Math.round(mapHeight) + "px";
  }
  if (map) {
    map.style.height = Math.round(mapHeight) + "px";
  }
  if (mapContainer) {
    mapContainer.style.removeProperty("min-height");
  }

  var graph = map && map.querySelector(".js-plotly-plot");
  if (
    graph &&
    window.Plotly &&
    (!graph.layout || Math.round(Number(graph.layout.height)) !== mapHeight)
  ) {
    window.Plotly.relayout(graph, {height: mapHeight});
  }
}

function performInterestLayout() {
  interestLayoutFrame = undefined;
  if (interestLayoutUpdatesPanels) {
    updateSplitter();
  }
  interestLayoutUpdatesPanels = false;
  applyInterestPanelHeights();
  window.dispatchEvent(new CustomEvent("interest:layout"));
}

function scheduleInterestLayout(updatePanels) {
  if (updatePanels !== false) {
    interestLayoutUpdatesPanels = true;
  }
  if (typeof interestLayoutFrame !== "undefined") {
    return;
  }
  interestLayoutFrame = window.requestAnimationFrame(performInterestLayout);
}

function getInterestMapBalloonPlacementOrder(directionX, directionY) {
  if (!Number.isFinite(directionX) || !Number.isFinite(directionY)) {
    return [];
  }
  if (Math.abs(directionX) > Math.abs(directionY)) {
    return directionX < 0
      ? ["right", "top", "bottom"]
      : ["left", "top", "bottom"];
  }
  if (directionY < 0) {
    return ["bottom", "left", "right"];
  }
  if (directionY > 0) {
    return ["top", "left", "right"];
  }
  return [];
}

function normalizeInterestMapLongitude(longitude, referenceLongitude) {
  if (!Number.isFinite(longitude) || !Number.isFinite(referenceLongitude)) {
    return longitude;
  }
  var offset =
    ((((longitude - referenceLongitude + 180) % 360) + 360) % 360) - 180;
  return referenceLongitude + offset;
}

function projectInterestMapPoint(map, longitude, latitude, preferredX) {
  var center = map.getCenter();
  var centerLongitude = Number(center && center.lng);
  var normalizedLongitude = normalizeInterestMapLongitude(
    longitude,
    centerLongitude
  );
  var container =
    typeof map.getContainer === "function" ? map.getContainer() : null;
  var width = container ? container.clientWidth : 0;
  if (!width) {
    return null;
  }
  var referenceX = Number.isFinite(preferredX) ? preferredX : width / 2;
  var best = null;

  [
    normalizedLongitude - 360,
    normalizedLongitude,
    normalizedLongitude + 360,
  ].forEach(function (candidateLongitude) {
    var point = map.project([candidateLongitude, latitude]);
    if (!point || !Number.isFinite(point.x) || !Number.isFinite(point.y)) {
      return;
    }
    var overflow =
      point.x < 0 ? -point.x : point.x > width ? point.x - width : 0;
    var score = overflow * Math.max(width, 1) * 10 + Math.abs(point.x - referenceX);
    if (!best || score < best.score) {
      best = {x: point.x, y: point.y, score: score};
    }
  });

  return best;
}

function getInterestMapArrowWidths(referenceZoom, currentZoom) {
  var zoomOutProgress = Math.min(
    1,
    Math.max(0, (referenceZoom - currentZoom) / 3)
  );
  return {
    shaft: 4 + zoomOutProgress * 4,
    headLength: 18 + zoomOutProgress * 6,
    headWidth: 12 + zoomOutProgress * 6,
  };
}

function buildInterestMapArrowGeometry(map, coordinates, dimensions) {
  if (
    !Array.isArray(coordinates) ||
    coordinates.length < 2 ||
    typeof map.unproject !== "function"
  ) {
    return null;
  }

  var projected = new Array(coordinates.length);
  var endCoordinates = coordinates[coordinates.length - 1];
  var end = projectInterestMapPoint(
    map,
    Number(endCoordinates[0]),
    Number(endCoordinates[1]),
    null
  );
  if (!end) {
    return null;
  }
  projected[projected.length - 1] = end;

  for (var index = coordinates.length - 2; index >= 0; index -= 1) {
    var coordinate = coordinates[index];
    var nextPoint = projected[index + 1];
    projected[index] = projectInterestMapPoint(
      map,
      Number(coordinate[0]),
      Number(coordinate[1]),
      nextPoint.x
    );
    if (!projected[index]) {
      return null;
    }
  }

  var previous = projected[projected.length - 2];
  var directionX = end.x - previous.x;
  var directionY = end.y - previous.y;
  var directionLength = Math.hypot(directionX, directionY);
  if (!Number.isFinite(directionLength) || directionLength <= 0.01) {
    return null;
  }

  directionX /= directionLength;
  directionY /= directionLength;
  var baseX = end.x - directionX * dimensions.headLength;
  var baseY = end.y - directionY * dimensions.headLength;
  var halfWidth = dimensions.headWidth / 2;
  var normalX = -directionY;
  var normalY = directionX;

  // Finish the shaft just inside the wide end of the head. If it reaches the
  // tip, the square line end remains visible on both sides of the sharp point.
  var overlap = Math.max(2, dimensions.shaft / 2);
  var trimDistance = Math.max(0, dimensions.headLength - overlap);
  var shaftPoints = null;
  var remaining = trimDistance;

  for (var pointIndex = projected.length - 1; pointIndex > 0; pointIndex -= 1) {
    var segmentEnd = projected[pointIndex];
    var segmentStart = projected[pointIndex - 1];
    var segmentLength = Math.hypot(
      segmentEnd.x - segmentStart.x,
      segmentEnd.y - segmentStart.y
    );
    if (!Number.isFinite(segmentLength) || segmentLength <= 0.01) {
      continue;
    }
    if (segmentLength >= remaining) {
      var ratio = remaining / segmentLength;
      var cutPoint = {
        x: segmentEnd.x + (segmentStart.x - segmentEnd.x) * ratio,
        y: segmentEnd.y + (segmentStart.y - segmentEnd.y) * ratio,
      };
      shaftPoints = projected.slice(0, pointIndex).concat([cutPoint]);
      break;
    }
    remaining -= segmentLength;
  }

  if (!shaftPoints || shaftPoints.length < 2) {
    return null;
  }

  function unproject(pointX, pointY) {
    var coordinate = map.unproject([pointX, pointY]);
    if (
      !coordinate ||
      !Number.isFinite(coordinate.lng) ||
      !Number.isFinite(coordinate.lat)
    ) {
      return null;
    }
    return [coordinate.lng, coordinate.lat];
  }

  var tip = unproject(end.x, end.y);
  var left = unproject(
    baseX + normalX * halfWidth,
    baseY + normalY * halfWidth
  );
  var right = unproject(
    baseX - normalX * halfWidth,
    baseY - normalY * halfWidth
  );
  if (!tip || !left || !right) {
    return null;
  }

  var shaftCoordinates = [];
  for (var shaftIndex = 0; shaftIndex < shaftPoints.length; shaftIndex += 1) {
    var shaftCoordinate = unproject(
      shaftPoints[shaftIndex].x,
      shaftPoints[shaftIndex].y
    );
    if (!shaftCoordinate) {
      return null;
    }
    shaftCoordinates.push(shaftCoordinate);
  }

  return {
    shaft: {
      type: "LineString",
      coordinates: shaftCoordinates,
    },
    head: {
      type: "Polygon",
      coordinates: [[tip, left, right, tip]],
    },
  };
}

$(function () {
  scheduleInterestLayout();
  $(window).on("resize", function () {
    scheduleInterestLayout();
    scheduleInterestSplitterHintUpdate();
  });

  var interest = document.querySelector("#interest-container");
  var regionCardStorageKey = "acestaInterestRegionCardCompact";
  var lastScrolledInterestRow = null;
  var audienceHintObserver = null;
  var audienceHintFrame = null;

  function updateInterestSplitterHint() {
    audienceHintFrame = null;
    var hint = document.querySelector("#interest-splitter-hint");
    var frame = document.querySelector("#audience-container iframe");
    var hasGroups = false;

    if (frame) {
      try {
        hasGroups = Boolean(
          frame.contentDocument &&
            frame.contentDocument.querySelector(".audience-group")
        );
      } catch (error) {
        hasGroups = false;
      }
    }

    if (
      hint &&
      hasGroups &&
      window.innerWidth >= interestDesktopWidth &&
      !hasInterestCookie(interestSplitterHintCookie)
    ) {
      hint.classList.add("is-visible");
    } else {
      hideInterestSplitterHint();
    }
  }

  function scheduleInterestSplitterHintUpdate() {
    if (audienceHintFrame !== null) {
      return;
    }
    audienceHintFrame = window.requestAnimationFrame(
      updateInterestSplitterHint
    );
  }

  function observeAudienceForSplitterHint() {
    var frame = document.querySelector("#audience-container iframe");
    if (!frame) {
      scheduleInterestSplitterHintUpdate();
      return;
    }

    if (audienceHintObserver) {
      audienceHintObserver.disconnect();
    }

    try {
      var frameDocument = frame.contentDocument;
      if (frameDocument && frameDocument.documentElement) {
        audienceHintObserver = new MutationObserver(
          scheduleInterestSplitterHintUpdate
        );
        audienceHintObserver.observe(frameDocument.documentElement, {
          childList: true,
          subtree: true,
        });
      }
    } catch (error) {
      audienceHintObserver = null;
    }
    scheduleInterestSplitterHintUpdate();
  }

  var audienceFrame = document.querySelector("#audience-container iframe");
  if (audienceFrame) {
    audienceFrame.addEventListener("load", observeAudienceForSplitterHint);
  }
  observeAudienceForSplitterHint();
  var interestMapResizeObserver = null;
  var observedInterestMap = null;
  var observedRegionCard = null;
  var lastInterestMapViewport = "";
  var lastInterestMapCamera = "";
  var lastInterestMapState = "";
  var interestMapViewportTimer = null;
  var interestMapLibre = null;
  var interestMapGraph = null;
  var interestMapAfterplotHandler = null;
  var lastAppliedInterestMapCameraIntent = "";
  var interestMapCameraFrame = null;
  var interestMapCameraTimer = null;
  var interestMapCameraGeneration = 0;
  var interestMapBalloonFrame = null;
  var interestMapBalloonSettleTimer = null;
  var regionCardState = {
    initialized: false,
    isRegions: null,
    sessionCompact: false,
    closed: false,
  };

  function getStoredRegionCardCompact() {
    try {
      return window.sessionStorage.getItem(regionCardStorageKey) === "true";
    } catch (error) {
      return false;
    }
  }

  function storeRegionCardCompact() {
    try {
      window.sessionStorage.setItem(regionCardStorageKey, "true");
    } catch (error) {
      // Current-page behavior still works when storage is unavailable.
    }
  }

  regionCardState.sessionCompact = getStoredRegionCardCompact();

  function getRegionCard() {
    return interest.querySelector("#region-current-card");
  }

  function getRegionCardContent() {
    return interest.querySelector("#region-current-card-content");
  }

  function updateInterestMapViewport() {
    interestMapViewportTimer = null;
    var map = interest.querySelector("#map");
    if (
      !map ||
      !window.dash_clientside ||
      typeof window.dash_clientside.set_props !== "function"
    ) {
      return;
    }

    var mapRect = map.getBoundingClientRect();
    if (!mapRect.width || !mapRect.height) {
      return;
    }

    var card = getRegionCard();
    var rightInset = 0;
    var topInset = 0;
    if (card && !card.classList.contains("d-none")) {
      var cardRect = card.getBoundingClientRect();
      var overlapsMap =
        cardRect.right > mapRect.left &&
        cardRect.left < mapRect.right &&
        cardRect.bottom > mapRect.top &&
        cardRect.top < mapRect.bottom;
      if (overlapsMap) {
        rightInset = Math.max(0, mapRect.right - cardRect.left + 16);
        topInset = Math.max(0, cardRect.bottom - mapRect.top + 16);
      }
    }

    var viewport = {
      width: Math.round(mapRect.width),
      height: Math.round(mapRect.height),
      rightInset: Math.round(rightInset),
      topInset: Math.round(topInset),
    };
    var viewportKey = JSON.stringify(viewport);
    if (viewportKey === lastInterestMapViewport) {
      return;
    }

    lastInterestMapViewport = viewportKey;
    window.dash_clientside.set_props("interest-map-viewport", {
      data: viewport,
    });
  }

  function scheduleInterestMapViewport() {
    if (interestMapViewportTimer !== null) {
      window.clearTimeout(interestMapViewportTimer);
    }
    interestMapViewportTimer = window.setTimeout(updateInterestMapViewport, 180);
  }

  function initializeInterestMapViewport() {
    var map = interest.querySelector("#map");
    var card = getRegionCard();
    if (!map || typeof window.ResizeObserver === "undefined") {
      scheduleInterestMapViewport();
      return;
    }

    if (!interestMapResizeObserver) {
      interestMapResizeObserver = new ResizeObserver(function () {
        scheduleInterestMapViewport();
      });
    }
    if (map !== observedInterestMap) {
      if (observedInterestMap) {
        interestMapResizeObserver.unobserve(observedInterestMap);
      }
      observedInterestMap = map;
      interestMapResizeObserver.observe(map);
    }
    if (card && card !== observedRegionCard) {
      if (observedRegionCard) {
        interestMapResizeObserver.unobserve(observedRegionCard);
      }
      observedRegionCard = card;
      interestMapResizeObserver.observe(card);
    }

    scheduleInterestMapViewport();
  }

  window.addEventListener("interest:layout", function () {
    scheduleInterestMapViewport();
    settleInterestMapBalloons();
  });

  function getInterestMapLibre() {
    var graph = interest.querySelector("#map .js-plotly-plot");
    if (!graph || !graph._fullLayout) {
      return null;
    }

    var subplot = null;
    if (graph._fullLayout.map && graph._fullLayout.map._subplot) {
      subplot = graph._fullLayout.map._subplot;
    } else if (
      graph._fullLayout.mapbox &&
      graph._fullLayout.mapbox._subplot
    ) {
      subplot = graph._fullLayout.mapbox._subplot;
    }

    return subplot && subplot.map ? subplot.map : null;
  }

  function updateInterestMapCameraState() {
    var map = getInterestMapLibre();
    if (
      !map ||
      !window.dash_clientside ||
      typeof window.dash_clientside.set_props !== "function"
    ) {
      return;
    }

    var center = map.getCenter();
    var camera = {
      center: {
        lon: Number(center && center.lng),
        lat: Number(center && center.lat),
      },
      zoom: Number(map.getZoom()),
    };
    if (
      !Number.isFinite(camera.center.lon) ||
      !Number.isFinite(camera.center.lat) ||
      !Number.isFinite(camera.zoom)
    ) {
      return;
    }

    var cameraKey = JSON.stringify(camera);
    if (cameraKey === lastInterestMapCamera) {
      return;
    }
    lastInterestMapCamera = cameraKey;
    window.dash_clientside.set_props("interest-map-camera", {data: camera});
  }

  function getInterestMapCameraIntent(graph) {
    var meta =
      (graph.layout && graph.layout.meta) ||
      (graph._fullLayout && graph._fullLayout.meta);
    var intent = meta && meta.acestaInterestCamera;
    var center = intent && intent.center;
    var longitude = Number(center && center.lon);
    var latitude = Number(center && center.lat);
    var zoom = Number(intent && intent.zoom);

    if (
      !intent ||
      typeof intent.key !== "string" ||
      !Number.isFinite(longitude) ||
      !Number.isFinite(latitude) ||
      !Number.isFinite(zoom)
    ) {
      return null;
    }

    return {
      key: intent.key,
      longitude: longitude,
      latitude: latitude,
      zoom: zoom,
    };
  }

  function updateInterestMapState(graph) {
    if (
      !graph ||
      !window.dash_clientside ||
      typeof window.dash_clientside.set_props !== "function"
    ) {
      return;
    }
    var meta =
      (graph.layout && graph.layout.meta) ||
      (graph._fullLayout && graph._fullLayout.meta);
    var state = meta && meta.acestaInterestState;
    if (!state || state.ready !== true) {
      return;
    }
    var stateKey = JSON.stringify(state);
    if (stateKey === lastInterestMapState) {
      return;
    }
    lastInterestMapState = stateKey;
    window.dash_clientside.set_props("interest-map-state", {data: state});
  }

  function getInterestMapCameraIntentSignature(intent) {
    if (!intent) {
      return "";
    }
    return JSON.stringify({
      key: intent.key,
      longitude: intent.longitude,
      latitude: intent.latitude,
      zoom: intent.zoom,
    });
  }

  function cancelInterestMapCameraSync() {
    interestMapCameraGeneration += 1;
    if (interestMapCameraFrame !== null) {
      window.cancelAnimationFrame(interestMapCameraFrame);
      interestMapCameraFrame = null;
    }
    if (interestMapCameraTimer !== null) {
      window.clearTimeout(interestMapCameraTimer);
      interestMapCameraTimer = null;
    }
  }

  function applyInterestMapCamera(graph, generation, attempt) {
    interestMapCameraFrame = null;
    interestMapCameraTimer = null;
    if (
      generation !== interestMapCameraGeneration ||
      !graph.isConnected ||
      graph !== interest.querySelector("#map .js-plotly-plot")
    ) {
      return;
    }

    var intent = getInterestMapCameraIntent(graph);
    var map = getInterestMapLibre();
    if (!intent || !map) {
      if (attempt < 8) {
        interestMapCameraTimer = window.setTimeout(function () {
          applyInterestMapCamera(graph, generation, attempt + 1);
        }, 25 * (attempt + 1));
      }
      return;
    }

    var intentSignature = getInterestMapCameraIntentSignature(intent);
    if (intentSignature === lastAppliedInterestMapCameraIntent) {
      return;
    }
    lastAppliedInterestMapCameraIntent = intentSignature;

    var currentCenter = map.getCenter();
    var currentLongitude = Number(currentCenter && currentCenter.lng);
    var currentLatitude = Number(currentCenter && currentCenter.lat);
    var currentZoom = Number(map.getZoom());
    var longitudeDifference = Math.abs(
      ((((currentLongitude - intent.longitude + 180) % 360) + 360) % 360) -
        180
    );
    var cameraDiffers =
      !Number.isFinite(currentLongitude) ||
      !Number.isFinite(currentLatitude) ||
      !Number.isFinite(currentZoom) ||
      longitudeDifference > 1e-8 ||
      Math.abs(currentLatitude - intent.latitude) > 1e-8 ||
      Math.abs(currentZoom - intent.zoom) > 1e-8;

    if (cameraDiffers) {
      map.jumpTo({
        center: [intent.longitude, intent.latitude],
        zoom: intent.zoom,
      });
    }

    updateInterestMapArrows();
    settleInterestMapBalloons();
  }

  function scheduleInterestMapCamera(graph) {
    if (!graph) {
      return;
    }
    var intent = getInterestMapCameraIntent(graph);
    if (
      intent &&
      getInterestMapCameraIntentSignature(intent) ===
      lastAppliedInterestMapCameraIntent
    ) {
      return;
    }
    cancelInterestMapCameraSync();
    var generation = interestMapCameraGeneration;
    interestMapCameraFrame = window.requestAnimationFrame(function () {
      interestMapCameraFrame = window.requestAnimationFrame(function () {
        applyInterestMapCamera(graph, generation, 0);
      });
    });
  }

  function initializeInterestMapCamera() {
    var graph = interest.querySelector("#map .js-plotly-plot");
    if (!graph) {
      return;
    }

    if (interestMapGraph !== graph) {
      cancelInterestMapCameraSync();
      lastAppliedInterestMapCameraIntent = "";
      if (
        interestMapGraph &&
        interestMapAfterplotHandler &&
        typeof interestMapGraph.removeListener === "function"
      ) {
        interestMapGraph.removeListener(
          "plotly_afterplot",
          interestMapAfterplotHandler
        );
      }
      interestMapGraph = graph;
      interestMapAfterplotHandler = function () {
        updateInterestMapState(graph);
        scheduleInterestMapCamera(graph);
      };
      graph.on("plotly_afterplot", interestMapAfterplotHandler);
      updateInterestMapState(graph);
      scheduleInterestMapCamera(graph);
    }
  }

  function updateInterestMapArrows() {
    var graph = interest.querySelector("#map .js-plotly-plot");
    if (!graph || !graph._fullLayout) {
      return;
    }

    var fullMap =
      graph._fullLayout.map && graph._fullLayout.map._subplot
        ? graph._fullLayout.map
        : graph._fullLayout.mapbox;
    var subplot = fullMap && fullMap._subplot;
    var map = subplot && subplot.map;
    var layoutLayers = (fullMap && fullMap.layers) || [];
    if (!map || !Number.isFinite(map.getZoom())) {
      return;
    }

    if (!Array.isArray(layoutLayers)) {
      return;
    }

    var pendingShaft = null;
    layoutLayers.forEach(function (layer, index) {
      var properties = layer.source && layer.source.properties;
      var arrowPart = properties && properties.acestaArrowPart;
      var referenceZoom = Number(properties && properties.acestaArrowZoom);
      if (
        (arrowPart !== "shaft" && arrowPart !== "head") ||
        !Number.isFinite(referenceZoom)
      ) {
        return;
      }

      var layerId = "plotly-layout-layer-" + subplot.uid + "-" + index;
      if (!map.getLayer(layerId)) {
        return;
      }

      var widths = getInterestMapArrowWidths(referenceZoom, map.getZoom());
      if (arrowPart === "shaft") {
        try {
          var currentWidth = map.getPaintProperty(layerId, "line-width");
        } catch (e) {
          return;
        }
        if (
          !Number.isFinite(currentWidth) ||
          Math.abs(currentWidth - widths.shaft) > 0.01
        ) {
          map.setPaintProperty(layerId, "line-width", widths.shaft);
        }
        var shaftSourceId = "source-" + subplot.uid + "-" + index;
        var shaftSource = map.getSource(shaftSourceId);
        pendingShaft = {
          coordinates: layer.source.geometry.coordinates,
          properties: properties,
          source: shaftSource,
          widths: widths,
        };
        return;
      }

      if (
        !pendingShaft ||
        !pendingShaft.source ||
        typeof pendingShaft.source.setData !== "function"
      ) {
        return;
      }

      var geometry = buildInterestMapArrowGeometry(
        map,
        pendingShaft.coordinates,
        pendingShaft.widths
      );
      var sourceId = "source-" + subplot.uid + "-" + index;
      var source = map.getSource(sourceId);
      if (!geometry || !source || typeof source.setData !== "function") {
        return;
      }

      var shaftGeometryKey = JSON.stringify(geometry.shaft.coordinates);
      if (pendingShaft.source.acestaArrowGeometryKey !== shaftGeometryKey) {
        pendingShaft.source.acestaArrowGeometryKey = shaftGeometryKey;
        pendingShaft.source.setData({
          type: "Feature",
          properties: pendingShaft.properties,
          geometry: geometry.shaft,
        });
      }

      var headGeometryKey = JSON.stringify(geometry.head.coordinates);
      if (source.acestaArrowGeometryKey !== headGeometryKey) {
        source.acestaArrowGeometryKey = headGeometryKey;
        source.setData({
          type: "Feature",
          properties: properties,
          geometry: geometry.head,
        });
      }
      pendingShaft = null;
    });
  }

  function getIntersectionArea(first, second) {
    var width = Math.max(
      0,
      Math.min(first.right, second.right) - Math.max(first.left, second.left)
    );
    var height = Math.max(
      0,
      Math.min(first.bottom, second.bottom) - Math.max(first.top, second.top)
    );
    return width * height;
  }

  function positionInterestMapBalloons() {
    interestMapBalloonFrame = null;

    var map = getInterestMapLibre();
    var stage = interest.querySelector(".interest-map-stage");
    var mapElement = interest.querySelector("#map");
    var container = interest.querySelector("#interest-map-balloons");
    if (!map || !stage || !mapElement || !container) {
      return;
    }

    var stageRect = stage.getBoundingClientRect();
    var mapRect = mapElement.getBoundingClientRect();
    var safeRect = {
      left: mapRect.left - stageRect.left + 10,
      top: mapRect.top - stageRect.top + 10,
      right: mapRect.right - stageRect.left - 10,
      bottom: mapRect.bottom - stageRect.top - 10,
    };
    var obstacles = [];
    var card = getRegionCard();
    if (card && !card.classList.contains("d-none")) {
      var cardRect = card.getBoundingClientRect();
      obstacles.push({
        left: cardRect.left - stageRect.left - 8,
        top: cardRect.top - stageRect.top - 8,
        right: cardRect.right - stageRect.left + 8,
        bottom: cardRect.bottom - stageRect.top + 8,
      });
    }

    var occupied = [];
    var balloons = Array.prototype.slice.call(
      container.querySelectorAll(".interest-map-balloon")
    );
    balloons.forEach(function (balloon) {
      var longitude = Number(balloon.dataset.lon);
      var latitude = Number(balloon.dataset.lat);
      if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) {
        return;
      }

      var point = null;
      try {
        point = projectInterestMapPoint(map, longitude, latitude, null);
      } catch (error) {
        return;
      }
      if (!point) {
        return;
      }
      var anchorX = mapRect.left - stageRect.left + point.x;
      var anchorY = mapRect.top - stageRect.top + point.y;
      if (!Number.isFinite(anchorX) || !Number.isFinite(anchorY)) {
        return;
      }

      var balloonWidth = balloon.offsetWidth;
      var balloonHeight = balloon.offsetHeight;
      var gap = 18;
      var candidates = [
        {
          placement: "top",
          left: anchorX - balloonWidth / 2,
          top: anchorY - balloonHeight - gap,
        },
        {
          placement: "bottom",
          left: anchorX - balloonWidth / 2,
          top: anchorY + gap,
        },
        {
          placement: "left",
          left: anchorX - balloonWidth - gap,
          top: anchorY - balloonHeight / 2,
        },
        {
          placement: "right",
          left: anchorX + gap,
          top: anchorY - balloonHeight / 2,
        },
      ];

      var targetLongitude = Number(balloon.dataset.targetLon);
      var targetLatitude = Number(balloon.dataset.targetLat);
      var placementOrder = [];
      if (
        Number.isFinite(targetLongitude) &&
        Number.isFinite(targetLatitude)
      ) {
        try {
          var targetPoint = projectInterestMapPoint(
            map,
            targetLongitude,
            targetLatitude,
            point.x
          );
          var directionX = targetPoint.x - point.x;
          var directionY = targetPoint.y - point.y;
          placementOrder = getInterestMapBalloonPlacementOrder(
            directionX,
            directionY
          );
        } catch (error) {
          placementOrder = [];
        }
      }

      candidates.forEach(function (candidate, index) {
        candidate.right = candidate.left + balloonWidth;
        candidate.bottom = candidate.top + balloonHeight;
        var overflow =
          Math.max(0, safeRect.left - candidate.left) +
          Math.max(0, candidate.right - safeRect.right) +
          Math.max(0, safeRect.top - candidate.top) +
          Math.max(0, candidate.bottom - safeRect.bottom);
        var overlap = obstacles.concat(occupied).reduce(function (total, item) {
          return total + getIntersectionArea(candidate, item);
        }, 0);
        candidate.score = overflow * 1000 + overlap * 10 + index;
        candidate.fits = overflow === 0 && overlap === 0;
      });

      var allowedCandidates = placementOrder.length
        ? placementOrder.map(function (placement) {
            return candidates.find(function (candidate) {
              return candidate.placement === placement;
            });
          })
        : candidates.slice();
      var preferredCandidate = allowedCandidates.find(function (candidate) {
        return candidate.placement === placementOrder[0] && candidate.fits;
      });
      allowedCandidates.sort(function (first, second) {
        return first.score - second.score;
      });
      var best = preferredCandidate || allowedCandidates[0];
      best.left = Math.min(
        Math.max(best.left, safeRect.left),
        safeRect.right - balloonWidth
      );
      best.top = Math.min(
        Math.max(best.top, safeRect.top),
        safeRect.bottom - balloonHeight
      );
      best.right = best.left + balloonWidth;
      best.bottom = best.top + balloonHeight;

      var tailPadding = 12;
      var tailX = Math.min(
        Math.max(anchorX - best.left, tailPadding),
        balloonWidth - tailPadding
      );
      var tailY = Math.min(
        Math.max(anchorY - best.top, tailPadding),
        balloonHeight - tailPadding
      );
      var tailXValue = Math.round(tailX) + "px";
      var tailYValue = Math.round(tailY) + "px";
      if (balloon.style.getPropertyValue("--balloon-tail-x") !== tailXValue) {
        balloon.style.setProperty("--balloon-tail-x", tailXValue);
      }
      if (balloon.style.getPropertyValue("--balloon-tail-y") !== tailYValue) {
        balloon.style.setProperty("--balloon-tail-y", tailYValue);
      }

      var left = Math.round(best.left) + "px";
      var top = Math.round(best.top) + "px";
      if (balloon.style.left !== left) {
        balloon.style.left = left;
      }
      if (balloon.style.top !== top) {
        balloon.style.top = top;
      }
      if (balloon.dataset.placement !== best.placement) {
        balloon.dataset.placement = best.placement;
      }
      if (balloon.dataset.positioned !== "true") {
        balloon.dataset.positioned = "true";
      }
      occupied.push(best);
    });
  }

  function scheduleInterestMapBalloons() {
    if (interestMapBalloonFrame !== null) {
      return;
    }
    interestMapBalloonFrame = window.requestAnimationFrame(
      positionInterestMapBalloons
    );
  }

  function settleInterestMapBalloons() {
    scheduleInterestMapBalloons();
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(scheduleInterestMapBalloons);
    });
    if (interestMapBalloonSettleTimer !== null) {
      window.clearTimeout(interestMapBalloonSettleTimer);
    }
    interestMapBalloonSettleTimer = window.setTimeout(function () {
      interestMapBalloonSettleTimer = null;
      scheduleInterestMapBalloons();
    }, 120);
  }

  function initializeInterestMapBalloons() {
    var map = getInterestMapLibre();
    if (!map) {
      return;
    }

    if (interestMapLibre !== map) {
      if (interestMapLibre) {
        interestMapLibre.off("move", scheduleInterestMapBalloons);
        interestMapLibre.off("moveend", scheduleInterestMapBalloons);
        interestMapLibre.off("resize", scheduleInterestMapBalloons);
        interestMapLibre.off("render", scheduleInterestMapBalloons);
        interestMapLibre.off("idle", scheduleInterestMapBalloons);
        interestMapLibre.off("move", updateInterestMapArrows);
        interestMapLibre.off("moveend", updateInterestMapCameraState);
        interestMapLibre.off("render", updateInterestMapArrows);
        interestMapLibre.off("idle", updateInterestMapArrows);
      }
      interestMapLibre = map;
      interestMapLibre.on("move", scheduleInterestMapBalloons);
      interestMapLibre.on("moveend", scheduleInterestMapBalloons);
      interestMapLibre.on("resize", scheduleInterestMapBalloons);
      interestMapLibre.on("render", scheduleInterestMapBalloons);
      interestMapLibre.on("idle", scheduleInterestMapBalloons);
      interestMapLibre.on("move", updateInterestMapArrows);
      interestMapLibre.on("moveend", updateInterestMapCameraState);
      interestMapLibre.on("render", updateInterestMapArrows);
      interestMapLibre.on("idle", updateInterestMapArrows);
      updateInterestMapArrows();
      updateInterestMapCameraState();
      settleInterestMapBalloons();
      return;
    }

    updateInterestMapArrows();
    scheduleInterestMapBalloons();
  }

  function getIsRegionsSelected() {
    var homeAreaInputs = interest.querySelectorAll("#home-area input");
    var selectedHomeArea = interest.querySelector("#home-area input:checked");

    if (!homeAreaInputs.length) {
      return interest.querySelector("#home-area-dummy img") ? true : null;
    }

    if (!selectedHomeArea) {
      return null;
    }

    return selectedHomeArea === homeAreaInputs[0];
  }

  function updateRegionCardToggle() {
    var card = getRegionCard();
    if (!card) {
      return;
    }

    var toggle = card.querySelector("#region-current-card-toggle");

    if (!toggle) {
      return;
    }

    var isExpanded = !card.classList.contains(
      "region-current-card--collapsed"
    );
    var label = isExpanded
      ? "Свернуть карточку региона"
      : "Развернуть карточку региона";

    var expandedValue = isExpanded ? "true" : "false";

    if (toggle.getAttribute("aria-expanded") !== expandedValue) {
      toggle.setAttribute("aria-expanded", expandedValue);
    }
    if (toggle.getAttribute("aria-label") !== label) {
      toggle.setAttribute("aria-label", label);
    }
    if (toggle.getAttribute("title") !== label) {
      toggle.setAttribute("title", label);
    }
  }

  function setRegionCardCompact(isCompact) {
    var card = getRegionCard();
    if (!regionCardState.initialized || regionCardState.closed || !card) {
      return;
    }

    card.classList.toggle("region-current-card--collapsed", isCompact);
    updateRegionCardToggle();
  }

  function rememberCompactRegionCard() {
    if (!regionCardState.sessionCompact) {
      regionCardState.sessionCompact = true;
      storeRegionCardCompact();
    }

    setRegionCardCompact(true);
  }

  function initializeRegionCard() {
    if (regionCardState.initialized) {
      return;
    }

    var card = getRegionCard();
    var content = getRegionCardContent();
    var isRegions = getIsRegionsSelected();

    if (!card || !content || !content.children.length || isRegions === null) {
      return;
    }

    regionCardState.isRegions = isRegions;

    card.classList.toggle(
      "region-current-card--collapsed",
      !isRegions || regionCardState.sessionCompact
    );
    regionCardState.initialized = true;
    updateRegionCardToggle();
  }

  function syncRegionCardArea() {
    if (!regionCardState.initialized) {
      return;
    }

    var isRegions = getIsRegionsSelected();
    if (isRegions === null || isRegions === regionCardState.isRegions) {
      return;
    }

    regionCardState.isRegions = isRegions;
    if (isRegions) {
      setRegionCardCompact(regionCardState.sessionCompact);
    } else {
      rememberCompactRegionCard();
    }
  }

  function scheduleRegionCardAreaSync() {
    window.setTimeout(syncRegionCardArea, 0);
  }

  interest.addEventListener("click", function (event) {
    if (event.target.closest("#home-area label, #home-area input")) {
      scheduleRegionCardAreaSync();
      return;
    }

    if (event.target.closest("#map")) {
      lastScrolledInterestRow = null;
      window.setTimeout(scrollInterestTableToSelectedRow, 150);
    }

    var card = event.target.closest("#region-current-card");
    var toggle = event.target.closest("#region-current-card-toggle");
    var close = event.target.closest("#region-current-card-close");
    if (!card || (!toggle && !close)) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();

    if (close) {
      regionCardState.closed = true;
      card.classList.add("d-none");
      scheduleInterestMapViewport();
      scheduleInterestMapBalloons();
      return;
    }

    setRegionCardCompact(
      !card.classList.contains("region-current-card--collapsed")
    );
    scheduleInterestMapViewport();
    scheduleInterestMapBalloons();
  });

  interest.addEventListener("change", function (event) {
    if (event.target.closest("#home-area input")) {
      scheduleRegionCardAreaSync();
    }
  });

  interest.addEventListener("mousemove", function (event) {
    if (
      !regionCardState.initialized ||
      regionCardState.closed ||
      !regionCardState.isRegions ||
      !event.isTrusted ||
      (event.sourceCapabilities && event.sourceCapabilities.firesTouchEvents) ||
      !event.target.closest("#map")
    ) {
      return;
    }

    rememberCompactRegionCard();
  });

  function initializeInterestTooltips(root) {
    if (!root) {
      return;
    }

    var tooltipTriggerList = [].slice.call(
      root.querySelectorAll('[data-bs-toggle="tooltip"]')
    );

    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
      bootstrap.Tooltip.getOrCreateInstance(tooltipTriggerEl);
    });
  }

  function initializeInterestSortTooltips() {
    var tooltipText =
      "Сортировка переключается по кругу: по возрастанию → по убыванию → без сортировки.";
    var sortButtons = interest.querySelectorAll(
      '#table-interesants th:not([data-dash-column="history_action"]) .column-header--sort'
    );

    sortButtons.forEach(function (sortButton) {
      if (sortButton.dataset.interestSortTooltip === "true") {
        return;
      }

      sortButton.setAttribute("data-bs-toggle", "tooltip");
      sortButton.setAttribute("title", tooltipText);
      sortButton.dataset.interestSortTooltip = "true";
    });
  }

  function initializeUpdatedLink() {
    var updatedLink = interest.querySelector("#updated-link");

    if (
      !updatedLink ||
      updatedLink.dataset.updatedLinkInitialized === "true"
    ) {
      return;
    }

    if (!updatedLink.querySelector("svg")) {
      updatedLink.innerHTML =
        '<svg width="22" height="22"><use href="/static/img/sprite.svg#updated"></use></svg>';
    }

    var tooltipTitle = updatedLink.getAttribute("data-title");

    if (!tooltipTitle) {
      return;
    }

    var tooltip = bootstrap.Tooltip.getInstance(updatedLink);

    if (tooltip) {
      tooltip.dispose();
    }

    updatedLink.setAttribute("title", tooltipTitle);
    bootstrap.Tooltip.getOrCreateInstance(updatedLink);
    updatedLink.dataset.updatedLinkInitialized = "true";
  }

  function initializeRegionPotentialIcons() {
    var icons = interest.querySelectorAll(
      ".region-current-card__potential-icon[data-rank]"
    );

    icons.forEach(function (icon) {
      if (icon.querySelector("svg")) {
        return;
      }

      var rank = icon.dataset.rank;
      icon.innerHTML =
        '<svg width="16" height="16" aria-hidden="true">' +
        '<use href="/static/img/sprite.svg#rank-' +
        rank +
        '"></use></svg>';
    });
  }

  function scrollInterestTableToSelectedRow() {
    var selectedCell = interest.querySelector(
      "#table-interesants td.cell--selected"
    );

    if (!selectedCell) {
      lastScrolledInterestRow = null;
      return;
    }

    var rowKey =
      selectedCell.getAttribute("data-dash-row") ||
      selectedCell.parentElement.rowIndex.toString();
    if (rowKey === lastScrolledInterestRow) {
      return;
    }

    var row = selectedCell.closest("tr");
    var container = interest.querySelector("#interest-table-container");
    if (!row || !container) {
      return;
    }

    lastScrolledInterestRow = rowKey;
    window.requestAnimationFrame(function () {
      if (!row.isConnected) {
        return;
      }

      var containerRect = container.getBoundingClientRect();
      var rowRect = row.getBoundingClientRect();
      var centeredTop =
        container.scrollTop +
        rowRect.top -
        containerRect.top -
        (container.clientHeight - rowRect.height) / 2;

      container.scrollTo({top: Math.max(0, centeredTop), behavior: "smooth"});
    });
  }

  var interestObserver = new MutationObserver(function (mutations) {

    mutations.forEach(function(e) {
      if (e.target.id == "react-select-2--list") {
        $(".Select-noresults").text("Вид не найден");
      }
      if (typeof e.target.tagName !== "undefined") {
        if (e.target.tagName.toLowerCase() == "h3") {
          $("#title-container").attr("type", "button");
          $("#title-container").attr("title", $("#title").text());
        }
        if (
          e.target.tagName.toLowerCase() == "div" &&
          e.target.className == "dt-table-container__row dt-table-container__row-1"
        ) {
          $(".column-header-name").each(function () {
            var columnId = $(this).closest("th").attr("data-dash-column");
            if ($(this).find("[data-interest-header-help]").length) {
              return;
            }
            if (columnId == "qty_display") {
              $(this).html(
                $(this).text() +
                  '<a href="#" class="ms-1" data-interest-header-help data-bs-toggle="tooltip" title="Количество запросов туристических объектов за&nbsp;месяц"><svg fill="#939699" width="22" height="22"><use href="/static/img/sprite.svg#help"></use></svg></a>'
              );
            } else if (columnId == "ppt_display") {
              $(this).html(
                $(this).text() +
                  '<a href="#" class="ms-1" data-interest-header-help data-bs-toggle="tooltip" title="Региональная популярность или&nbsp;доля, которую занимает регион в&nbsp;показах запросу туристических объектов, деленная на&nbsp;долю всех показов результатов в&nbsp;регионе. Если популярность более 100%, это означает, что в&nbsp;данном регионе существует повышенный интерес к&nbsp;этому запросу, если меньше 100% - пониженный."><svg fill="#939699" width="22" height="22"><use href="/static/img/sprite.svg#help"></use></svg></a>'
              );
            }
          });
        }
      }
    });

    initializeInterestSortTooltips();
    initializeInterestTooltips(interest);
    initializeUpdatedLink();
    initializeRegionPotentialIcons();
    scrollInterestTableToSelectedRow();
    initializeRegionCard();
    initializeInterestMapViewport();
    initializeInterestMapCamera();
    initializeInterestMapBalloons();
    scheduleInterestLayout(false);
  });

  interestObserver.observe(interest, {
    subtree: true,
    attributes: true,
    childList: true,
    characterData: true,
  });

  initializeUpdatedLink();
  initializeRegionPotentialIcons();
  initializeInterestSortTooltips();
  initializeInterestTooltips(interest);
  scrollInterestTableToSelectedRow();
  initializeRegionCard();
  initializeInterestMapViewport();
  initializeInterestMapCamera();
  initializeInterestMapBalloons();
  scheduleInterestLayout(false);

  $(window).on("load", function() {
    initializeUpdatedLink();
    initializeRegionPotentialIcons();
    initializeInterestSortTooltips();
    initializeInterestTooltips(interest);
    scrollInterestTableToSelectedRow();
    initializeRegionCard();
    initializeInterestMapViewport();
    initializeInterestMapCamera();
    initializeInterestMapBalloons();
    scheduleInterestLayout();
  });
});
