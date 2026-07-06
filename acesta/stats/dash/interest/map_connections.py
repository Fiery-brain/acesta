import math
from dataclasses import dataclass
from dataclasses import replace
from typing import Iterable
from typing import Optional
from typing import Tuple

from dash import html

Coordinate = Tuple[float, float]

MAP_TILE_SIZE = 512
MAX_MERCATOR_LATITUDE = 85.05112878
MAX_REGION_ZOOM = 6.25
MAX_MIXED_ZOOM = 8.5
MAX_POINT_ZOOM = 12

ARROW_COLOR = "#FFA5A6"  # "  # F06A74"
ARROW_SHADOW_COLOR = "#C46C6D"  # C44D63
SOURCE_REGION_COLOR = "#FFA5A6"  # "#4F9286"63A89B
SOURCE_CLICK_PREFIX = "source-"


@dataclass(frozen=True)
class BalloonContent:
    title: str
    eyebrow: str = ""
    details: Tuple[object, ...] = ()
    tone: str = "medium"


@dataclass(frozen=True)
class MapEntity:
    kind: str
    identifier: str
    title: str
    anchor: Coordinate
    extent: Tuple[Coordinate, ...] = ()
    geometry: object = None
    balloon: Optional[BalloonContent] = None

    @property
    def key(self) -> str:
        return f"{self.kind}_{self.identifier}"

    @property
    def fit_coordinates(self) -> Tuple[Coordinate, ...]:
        return self.extent or (self.anchor,)

    def with_balloon(self, balloon: Optional[BalloonContent]):
        return replace(self, balloon=balloon)


@dataclass(frozen=True)
class MapConnection:
    source: MapEntity
    target: MapEntity

    @property
    def key(self) -> str:
        return f"{self.source.key}--{self.target.key}"


@dataclass(frozen=True)
class ArrowGeometry:
    zoom: float
    curve: Tuple[Coordinate, ...]
    dashes: Tuple[Tuple[Coordinate, ...], ...]
    dash_endpoints: Tuple[Coordinate, ...]
    lead_in: Tuple[Coordinate, ...]
    arrowhead: Tuple[Tuple[Coordinate, ...], ...]


@dataclass(frozen=True)
class ConnectionOverlay:
    center: dict
    zoom: float
    layers: Tuple[dict, ...]
    balloons: Tuple[object, ...]


def parse_entity_key(value: str) -> Tuple[Optional[str], Optional[str]]:
    """Return a safe kind/id pair from Plotly and Dash entity identifiers."""
    if not isinstance(value, str):
        return None, None

    kind, separator, identifier = value.partition("_")
    if not separator or kind not in {"regions", "cities", "sights"}:
        return None, None
    if not identifier:
        return None, None
    return kind, identifier


def get_click_entity_key(map_data: dict) -> Optional[str]:
    """Extract one entity key from point or region Plotly clickData."""
    try:
        point = map_data["points"][0]
    except (IndexError, KeyError, TypeError):
        return None

    kind, identifier = parse_entity_key(point.get("id"))
    if kind is not None:
        return f"{kind}_{identifier}"

    location = point.get("location")
    if location in (None, ""):
        return None
    return f"regions_{location}"


def get_source_click_entity_key(map_data: dict) -> Optional[str]:
    """Extract a source key without confusing it with a point target."""
    try:
        value = map_data["points"][0]["id"]
    except (IndexError, KeyError, TypeError):
        return None

    if not isinstance(value, str) or not value.startswith(SOURCE_CLICK_PREFIX):
        return None
    source_value = value.removeprefix(SOURCE_CLICK_PREFIX)
    kind, identifier = parse_entity_key(source_value)
    if kind is None:
        return None
    return f"{kind}_{identifier}"


def _normalize_longitude(longitude: float, reference: float) -> float:
    return reference + ((longitude - reference + 180) % 360) - 180


def _project_point(longitude: float, latitude: float) -> Coordinate:
    latitude = max(-MAX_MERCATOR_LATITUDE, min(MAX_MERCATOR_LATITUDE, latitude))
    latitude_radians = math.radians(latitude)
    return (
        (longitude + 180) / 360,
        (1 - math.asinh(math.tan(latitude_radians)) / math.pi) / 2,
    )


def _unproject_point(x: float, y: float) -> Coordinate:
    longitude = x * 360 - 180
    latitude = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y))))
    return longitude, latitude


def create_region_entity(
    identifier,
    title: str,
    geometry,
    balloon: Optional[BalloonContent] = None,
) -> MapEntity:
    """Create an entity whose anchor is guaranteed to lie inside its polygon."""
    anchor = geometry.representative_point()
    min_x, min_y, max_x, max_y = geometry.bounds
    bounds = (
        (float(min_x), float(min_y)),
        (float(min_x), float(max_y)),
        (float(max_x), float(max_y)),
        (float(max_x), float(min_y)),
    )
    return MapEntity(
        kind="regions",
        identifier=str(identifier),
        title=title,
        anchor=(float(anchor.x), float(anchor.y)),
        extent=bounds,
        geometry=geometry,
        balloon=balloon,
    )


def create_point_entity(
    kind: str,
    identifier,
    title: str,
    longitude: float,
    latitude: float,
    balloon: Optional[BalloonContent] = None,
) -> MapEntity:
    if kind not in {"cities", "sights"}:
        raise ValueError(f"Unsupported point entity kind: {kind}")
    return MapEntity(
        kind=kind,
        identifier=str(identifier),
        title=title,
        anchor=(float(longitude), float(latitude)),
        balloon=balloon,
    )


def build_arrow_curve(start: Coordinate, end: Coordinate) -> Tuple[Coordinate, ...]:
    """Build a north-bending source-to-target curve in Mercator space."""
    start = (_normalize_longitude(start[0], end[0]), start[1])
    start_x, start_y = _project_point(*start)
    end_x, end_y = _project_point(*end)
    delta_x = end_x - start_x
    delta_y = end_y - start_y
    distance = math.hypot(delta_x, delta_y)
    if distance <= 1e-12:
        return ()

    perpendicular_x = -delta_y / distance
    perpendicular_y = delta_x / distance
    if perpendicular_y > 0:
        perpendicular_x *= -1
        perpendicular_y *= -1

    bend = min(0.045, distance * 0.12)
    control_x = (start_x + end_x) / 2 + perpendicular_x * bend
    control_y = (start_y + end_y) / 2 + perpendicular_y * bend

    projected_curve = []
    for step in range(49):
        position = step / 48
        inverse = 1 - position
        projected_curve.append(
            (
                inverse * inverse * start_x
                + 2 * inverse * position * control_x
                + position * position * end_x,
                inverse * inverse * start_y
                + 2 * inverse * position * control_y
                + position * position * end_y,
            )
        )

    return tuple(_unproject_point(x, y) for x, y in projected_curve)


def _build_arrowhead(
    curve: Tuple[Coordinate, ...], zoom: float
) -> Tuple[Tuple[Tuple[Coordinate, ...], ...], Tuple[Coordinate, ...]]:
    if len(curve) < 2:
        return (), ()

    projected_curve = tuple(_project_point(*point) for point in curve)
    previous_x, previous_y = projected_curve[-2]
    end_x, end_y = projected_curve[-1]
    tangent_x = end_x - previous_x
    tangent_y = end_y - previous_y
    tangent_length = math.hypot(tangent_x, tangent_y)
    if tangent_length == 0:
        return (), ()

    tangent_x /= tangent_length
    tangent_y /= tangent_length
    world_size = MAP_TILE_SIZE * (2**zoom)
    head_length = 18 / world_size
    head_width = 6 / world_size
    base_x = end_x - tangent_x * head_length
    base_y = end_y - tangent_y * head_length
    normal_x = -tangent_y
    normal_y = tangent_x
    left = (base_x + normal_x * head_width, base_y + normal_y * head_width)
    right = (base_x - normal_x * head_width, base_y - normal_y * head_width)

    tip = _unproject_point(end_x, end_y)
    arrowhead = ((tip, _unproject_point(*left), _unproject_point(*right), tip),)

    remaining = 18 / world_size
    lead_in_start = projected_curve[0]
    for index in range(len(projected_curve) - 1, 0, -1):
        segment_end = projected_curve[index]
        segment_start = projected_curve[index - 1]
        segment_length = math.dist(segment_start, segment_end)
        if segment_length >= remaining:
            ratio = remaining / segment_length
            lead_in_start = (
                segment_end[0] + (segment_start[0] - segment_end[0]) * ratio,
                segment_end[1] + (segment_start[1] - segment_end[1]) * ratio,
            )
            break
        remaining -= segment_length

    lead_in = (
        _unproject_point(*lead_in_start),
        _unproject_point(end_x, end_y),
    )
    return arrowhead, lead_in


def _build_arrow_dashes(
    curve: Tuple[Coordinate, ...],
    zoom: float,
    dash_length: float = 18,
    gap_length: float = 12,
    lead_in_length: float = 16,
) -> Tuple[Tuple[Tuple[Coordinate, ...], ...], Tuple[Coordinate, ...]]:
    if len(curve) < 2:
        return (), ()

    world_size = MAP_TILE_SIZE * (2**zoom)
    projected_curve = tuple(
        (x * world_size, y * world_size)
        for x, y in (_project_point(*point) for point in curve)
    )
    total_length = sum(
        math.dist(projected_curve[index - 1], projected_curve[index])
        for index in range(1, len(projected_curve))
    )
    drawable_length = max(0, total_length - lead_in_length)
    if drawable_length == 0:
        return (), ()

    dashes = []
    endpoints = []
    current_dash = [projected_curve[0]]
    drawing = True
    pattern_remaining = dash_length
    traversed = 0.0

    for index in range(1, len(projected_curve)):
        current = projected_curve[index - 1]
        target = projected_curve[index]
        segment_length = math.dist(current, target)
        if segment_length == 0:
            continue

        direction_x = (target[0] - current[0]) / segment_length
        direction_y = (target[1] - current[1]) / segment_length
        segment_remaining = min(segment_length, drawable_length - traversed)

        while segment_remaining > 1e-9:
            step = min(segment_remaining, pattern_remaining)
            next_point = (
                current[0] + direction_x * step,
                current[1] + direction_y * step,
            )
            if drawing:
                current_dash.append(next_point)
            current = next_point
            segment_remaining -= step
            traversed += step
            pattern_remaining -= step

            if pattern_remaining <= 1e-9:
                if drawing and len(current_dash) > 1:
                    dashes.append(tuple(current_dash))
                    endpoints.extend((current_dash[0], current_dash[-1]))
                drawing = not drawing
                pattern_remaining = dash_length if drawing else gap_length
                current_dash = [current] if drawing else []

        if traversed >= drawable_length - 1e-9:
            break
        if drawing and current_dash:
            current_dash[-1] = target

    if drawing and len(current_dash) > 1:
        dashes.append(tuple(current_dash))
        endpoints.extend((current_dash[0], current_dash[-1]))

    def unproject_pixel_point(point):
        return _unproject_point(point[0] / world_size, point[1] / world_size)

    return (
        tuple(tuple(unproject_pixel_point(point) for point in dash) for dash in dashes),
        tuple(unproject_pixel_point(point) for point in endpoints),
    )


def build_arrow_geometry(curve: Tuple[Coordinate, ...], zoom: float) -> ArrowGeometry:
    arrowhead, lead_in = _build_arrowhead(curve, zoom)
    dashes, endpoints = _build_arrow_dashes(curve, zoom)
    return ArrowGeometry(
        zoom=zoom,
        curve=curve,
        dashes=dashes,
        dash_endpoints=endpoints,
        lead_in=lead_in,
        arrowhead=arrowhead,
    )


def _get_bounds(points: Iterable[Coordinate]) -> Tuple[float, float, float, float]:
    points = tuple(points)
    return (
        min(point[0] for point in points),
        max(point[0] for point in points),
        min(point[1] for point in points),
        max(point[1] for point in points),
    )


def _get_connection_max_zoom(connections: Tuple[MapConnection, ...]) -> float:
    kinds = {
        entity.kind
        for connection in connections
        for entity in (connection.source, connection.target)
    }
    if kinds == {"regions"}:
        return MAX_REGION_ZOOM
    if "regions" in kinds:
        return MAX_MIXED_ZOOM
    return MAX_POINT_ZOOM


def _get_connection_camera(
    connections: Tuple[MapConnection, ...],
    curves: Tuple[Tuple[Coordinate, ...], ...],
    viewport: dict,
    fallback_height: int,
) -> Tuple[dict, float]:
    reference_longitude = connections[0].target.anchor[0]
    width = max(320, int((viewport or {}).get("width") or 700))
    height = max(280, int((viewport or {}).get("height") or fallback_height))
    horizontal_padding = 76
    vertical_padding = 64
    max_top_inset = max(0, height - vertical_padding * 2 - 160)
    top_inset = max(
        0,
        min(max_top_inset, int((viewport or {}).get("topInset") or 0)),
    )
    max_zoom = _get_connection_max_zoom(connections)

    entity_points = []
    for connection in connections:
        for entity in (connection.source, connection.target):
            for longitude, latitude in entity.fit_coordinates:
                entity_points.append(
                    _project_point(
                        _normalize_longitude(longitude, reference_longitude),
                        latitude,
                    )
                )

    arrow_points = tuple(
        tuple(
            _project_point(
                _normalize_longitude(longitude, reference_longitude), latitude
            )
            for longitude, latitude in curve
        )
        for curve in curves
        if curve
    )
    full_points = entity_points + [point for curve in arrow_points for point in curve]

    arrow_bounds = _get_bounds(point for points in arrow_points for point in points)
    min_x, max_x, min_y, max_y = arrow_bounds
    arrow_center_x = (min_x + max_x) / 2
    arrow_center_y = (min_y + max_y) / 2

    safe_left = horizontal_padding
    safe_right = width - horizontal_padding
    safe_top = top_inset + vertical_padding
    safe_bottom = height - vertical_padding
    arrow_screen_x = (safe_left + safe_right) / 2
    arrow_screen_y = (safe_top + safe_bottom) / 2

    zoom_limits = [max_zoom]
    for point_x, point_y in full_points:
        delta_x = point_x - arrow_center_x
        delta_y = point_y - arrow_center_y
        if delta_x < 0:
            zoom_limits.append(
                math.log2((arrow_screen_x - safe_left) / (MAP_TILE_SIZE * abs(delta_x)))
            )
        elif delta_x > 0:
            zoom_limits.append(
                math.log2((safe_right - arrow_screen_x) / (MAP_TILE_SIZE * delta_x))
            )
        if delta_y < 0:
            zoom_limits.append(
                math.log2((arrow_screen_y - safe_top) / (MAP_TILE_SIZE * abs(delta_y)))
            )
        elif delta_y > 0:
            zoom_limits.append(
                math.log2((safe_bottom - arrow_screen_y) / (MAP_TILE_SIZE * delta_y))
            )

    zoom = max(0, min(zoom_limits) - 0.12)
    world_size = MAP_TILE_SIZE * (2**zoom)
    center_x = arrow_center_x - (arrow_screen_x - width / 2) / world_size
    center_y = arrow_center_y - (arrow_screen_y - height / 2) / world_size

    longitude, latitude = _unproject_point(center_x, center_y)
    return {"lon": longitude, "lat": latitude}, zoom


def _geojson_feature(geometry_type: str, coordinates, properties=None) -> dict:
    return {
        "type": "Feature",
        "properties": properties or {},
        "geometry": {"type": geometry_type, "coordinates": coordinates},
    }


def _build_arrow_layers(arrow: ArrowGeometry) -> Tuple[dict, ...]:
    if not (arrow.curve and arrow.arrowhead):
        return ()

    return (
        {
            "source": _geojson_feature(
                "LineString",
                arrow.curve,
                {
                    "acestaArrowPart": "shaft",
                    "acestaArrowZoom": arrow.zoom,
                },
            ),
            "sourcetype": "geojson",
            "type": "line",
            "color": ARROW_COLOR,
            "line": {"width": 4},
        },
        {
            "source": _geojson_feature(
                "Polygon",
                arrow.arrowhead,
                {
                    "acestaArrowPart": "head",
                    "acestaArrowZoom": arrow.zoom,
                    "acestaArrowPrevious": arrow.curve[-2],
                    "acestaArrowEnd": arrow.curve[-1],
                },
            ),
            "sourcetype": "geojson",
            "type": "fill",
            "color": ARROW_COLOR,
        },
    )


def _build_endpoint_layers(connection: MapConnection) -> Tuple[dict, ...]:
    same_entity = connection.source.key == connection.target.key
    if connection.source.kind == "regions" and not same_entity:
        return (
            {
                "source": connection.source.geometry.__geo_interface__,
                "sourcetype": "geojson",
                "type": "line",
                "color": SOURCE_REGION_COLOR,
                "opacity": 0.7,
                "line": {"width": 2},
            },
        )

    point = connection.target.anchor if same_entity else connection.source.anchor
    source = _geojson_feature("Point", point)
    return (
        {
            "source": source,
            "sourcetype": "geojson",
            "type": "circle",
            "color": ARROW_SHADOW_COLOR,
            "opacity": 0.24,
            "circle": {"radius": 9 if not same_entity else 13},
        },
        {
            "source": source,
            "sourcetype": "geojson",
            "type": "circle",
            "color": ARROW_COLOR,
            "circle": {"radius": 7 if not same_entity else 11},
        },
    )


def render_map_balloon(
    entity: MapEntity,
    role: str,
    related_anchor: Optional[Coordinate] = None,
):
    if entity.balloon is None:
        return None

    content = entity.balloon
    children = []
    if content.eyebrow:
        children.append(
            html.Div(content.eyebrow, className="interest-map-balloon__eyebrow")
        )
    children.append(html.H4(content.title, className="interest-map-balloon__title"))
    children.extend(
        html.Div(detail, className="interest-map-balloon__metric")
        for detail in content.details
        if detail
    )

    attributes = {
        "data-role": role,
        "data-entity-key": entity.key,
        "data-lat": entity.anchor[1],
        "data-lon": entity.anchor[0],
    }
    if related_anchor is not None:
        attributes.update(
            {
                "data-target-lat": related_anchor[1],
                "data-target-lon": related_anchor[0],
            }
        )
    return html.Div(
        children,
        className=(
            "interest-map-balloon " f"interest-map-balloon--popularity-{content.tone}"
        ),
        **attributes,
    )


def _build_balloons(
    connections: Tuple[MapConnection, ...],
    persistent_entities: Tuple[MapEntity, ...],
) -> Tuple[object, ...]:
    balloons = []
    rendered = set()
    self_target_keys = {
        connection.target.key
        for connection in connections
        if connection.source.key == connection.target.key
    }

    for entity in persistent_entities:
        if entity.key in self_target_keys:
            continue
        related_anchor = next(
            (
                connection.source.anchor
                for connection in connections
                if connection.target.key == entity.key
            ),
            None,
        )
        balloon = render_map_balloon(entity, "target", related_anchor)
        if balloon is not None:
            balloons.append(balloon)
            rendered.add((entity.key, "target"))

    for connection in connections:
        if connection.source.key == connection.target.key:
            balloon = render_map_balloon(connection.source, "self")
            render_key = (connection.source.key, "self")
        else:
            balloon = render_map_balloon(
                connection.source,
                "source",
                connection.target.anchor,
            )
            render_key = (connection.source.key, "source")
        if balloon is not None and render_key not in rendered:
            balloons.append(balloon)
            rendered.add(render_key)

        if connection.source.key == connection.target.key:
            continue

        target_key = (connection.target.key, "target")
        if target_key not in rendered:
            balloon = render_map_balloon(
                connection.target,
                "target",
                connection.source.anchor,
            )
            if balloon is not None:
                balloons.append(balloon)
                rendered.add(target_key)

    return tuple(balloons)


def build_connection_overlay(
    connections: Iterable[MapConnection],
    viewport: dict,
    fallback_height: int,
    default_center: dict,
    default_zoom: float,
    persistent_entities: Iterable[MapEntity] = (),
) -> ConnectionOverlay:
    """Build camera, layers, and balloons for zero, one, or many connections."""
    connections = tuple(connections)
    persistent_entities = tuple(persistent_entities)
    curves = tuple(
        build_arrow_curve(connection.source.anchor, connection.target.anchor)
        for connection in connections
    )

    center = default_center
    zoom = default_zoom
    nonempty_connections = tuple(
        connection for connection, curve in zip(connections, curves) if curve
    )
    nonempty_curves = tuple(curve for curve in curves if curve)
    if nonempty_connections:
        center, zoom = _get_connection_camera(
            nonempty_connections,
            nonempty_curves,
            viewport,
            fallback_height,
        )

    layers = []
    for connection, curve in zip(connections, curves):
        layers.extend(_build_endpoint_layers(connection))
        if curve:
            layers.extend(_build_arrow_layers(build_arrow_geometry(curve, zoom)))

    return ConnectionOverlay(
        center=center,
        zoom=zoom,
        layers=tuple(layers),
        balloons=_build_balloons(connections, persistent_entities),
    )
