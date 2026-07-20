%% Solar wind driving of geomagnetic activity schematic
clc; clear; close all;

% matlab -batch "addpath('src/lorenzsw'); figure1_schematic"

out_dir = fullfile('docs', 'assets', 'figures');
if ~exist(out_dir, 'dir')
    mkdir(out_dir);
end

% Select one: "publication", "space-weather", "high-contrast", "reference-gray"
color_scheme = "space-weather";
colors = get_color_scheme(color_scheme);

fig = figure('Color', 'w', 'Units', 'inches', 'Position', [1 1 7.2 5.2]);
ax = axes(fig);
hold(ax, 'on');
axis(ax, 'equal');
axis(ax, [0 10 0 7]);
axis(ax, 'off');
set(ax, 'Position', [0.04 0.06 0.92 0.86]);

text(ax, 5.1, 6.82, 'Chaotic Interaction of SW-M-I System', ...
    'FontSize', 12, 'FontWeight', 'bold', 'Color', colors.text, ...
    'HorizontalAlignment', 'center');

%% Boundaries
y = linspace(0.45, 6.45, 260);
x_bow = 3.55 + 0.12 * (y - 3.5).^2 - 0.04 * (y - 3.5);
x_mp = 5.05 + 0.35 * (y - 3.5).^2;

fill(ax, [x_bow, fliplr(x_mp)], ...
    [y, fliplr(y)], colors.sheath, ...
    'EdgeColor', 'none', 'FaceAlpha', 0.88);
plot(ax, x_bow, y, '--', 'Color', colors.bowShock, 'LineWidth', 1.0);
plot(ax, x_mp, y, '-', 'Color', colors.magnetopause, 'LineWidth', 1.25);

text(ax, 2.35, 5.95, 'Bow Shock', 'FontSize', 9.5, 'Color', colors.text);
text(ax, 7.45, 6.15, 'Magnetopause', 'FontSize', 9.5, 'Color', colors.text);
text(ax, 4.75, 5.45, 'Magnetosheath', 'FontSize', 9.5, 'Color', colors.text);

%% Solar wind flow and upstream field lines
x_starts = [-0.1, 0.8, 1.7, 2.6, 3.5, 4.4];
for x0 = x_starts(1:3)
    plot(ax, [x0 x0 + 2.2], [6.35 0.45], '-', 'Color', colors.upstreamField, 'LineWidth', 1.3);
    draw_arrow(ax, [x0 + 1.95, 1.10], [x0 + 2.08, 0.78], colors.upstreamField, 0.8, 0.09);
end
u = linspace(0, 1, 180);
bend = max((u - 0.42) / 0.72, 0);
bend = bend.^2 .* (3 - 1 * bend);
curve_reaches = [2.10, 1.70, 1.2];
for i = 1:3
    x0 = x_starts(i + 3);
    x_imf = x0 + curve_reaches(i) * u + 0.18 * u.^2;
    y_imf = 6.35 - 5.90 * u - 0.46 * sin(pi * u) .* bend;
    plot(ax, x_imf, y_imf, '-', 'Color', colors.upstreamField, 'LineWidth', 1.3);
    draw_arrow(ax, [x_imf(145) y_imf(145)], [x_imf(154) y_imf(154)], colors.upstreamField, 0.8, 0.09);
end
text(ax, 0.95, 3.88, 'Solar wind', 'FontSize', 9.5, 'Color', colors.text);
draw_arrow(ax, [2.0 3.85], [3.0 3.85], colors.solarWind, 0.9, 0.10);
text(ax, 1.10, 0.48, 'Magnetic field lines', 'FontSize', 9.5, ...
    'Color', colors.mutedText);

%% Earth
earth_center = [7.20, 3.45];
earth_r = 0.58;
ang = linspace(0, 2*pi, 240);

%% Earth
fill(ax, earth_center(1) + earth_r * cos(ang), earth_center(2) + earth_r * sin(ang), ...
    colors.earth, 'EdgeColor', colors.earthEdge, 'LineWidth', 1.2);
plot(ax, earth_center(1) + earth_r * cos(ang), earth_center(2) + earth_r * sin(ang), ...
    '-', 'Color', colors.earthEdge, 'LineWidth', 1.2);

text(ax, 1.25, 2.00, 'Merging', 'FontSize', 9.5, 'Color', colors.text);
text(ax, 1.25, 1.75, 'IMF and Geomagnetic', 'FontSize', 9.5, 'Color', colors.text);
text(ax, 1.25, 1.5, 'Field Lines', 'FontSize', 9.5, 'Color', colors.text);
draw_arrow(ax, [3.28 2.05], [3.58 2.45], colors.merging, 0.9, 0.10);
draw_arrow(ax, [3.46 1.93], [3.18 1.55], colors.merging, 0.9, 0.10);

%% Coordinate triad
origin = [8.95 0.90];
draw_arrow(ax, origin, origin + [0.00 0.62], colors.axis, 0.9, 0.09);
draw_arrow(ax, origin, origin + [-0.45 -0.32], colors.axis, 0.9, 0.09);
draw_arrow(ax, origin, origin + [0.55 0.00], colors.axis, 0.9, 0.09);
text(ax, origin(1) - 0.06, origin(2) + 0.74, 'z', 'FontSize', 8.5, 'Color', colors.axis);
text(ax, origin(1) - 0.64, origin(2) - 0.42, 'y', 'FontSize', 8.5, 'Color', colors.axis);
text(ax, origin(1) + 0.65, origin(2) - 0.02, 'x', 'FontSize', 8.5, 'Color', colors.axis);

set(fig, 'InvertHardcopy', 'off');
exportgraphics(fig, fullfile(out_dir, 'figure1_solar_wind_schematic.png'), 'Resolution', 600);
exportgraphics(fig, fullfile(out_dir, 'figure1_solar_wind_schematic.tif'), 'Resolution', 600);
exportgraphics(fig, fullfile(out_dir, 'figure1_solar_wind_schematic.pdf'), 'ContentType', 'vector');

function draw_arrow(ax, p0, p1, color, line_width, head_size)
    if nargin < 5
        head_size = 0.16;
    end
    plot(ax, [p0(1), p1(1)], [p0(2), p1(2)], '-', 'Color', color, 'LineWidth', line_width);
    v = p1 - p0;
    v = v / max(norm(v), eps);
    n = [-v(2), v(1)];
    base = p1 - head_size * 1.55 * v;
    tip = [p1; base + head_size * n; base - head_size * n];
    patch(ax, tip(:, 1), tip(:, 2), color, 'EdgeColor', 'none');
end

function colors = get_color_scheme(name)
    switch lower(string(name))
        case "publication"
            colors.text = [0.10 0.13 0.16];
            colors.mutedText = [0.42 0.47 0.51];
            colors.sheath = [0.86 0.90 0.93];
            colors.bowShock = [0.32 0.38 0.43];
            colors.magnetopause = [0.08 0.16 0.24];
            colors.upstreamField = [0.78 0.83 0.87];
            colors.solarWind = [0.09 0.33 0.52];
            colors.merging = [0.84 0.36 0.14];
            colors.earth = [0.97 0.98 0.96];
            colors.earthEdge = [0.10 0.13 0.16];
            colors.axis = [0.12 0.14 0.16];

        case "space-weather"
            colors.text = [0.08 0.12 0.16];
            colors.mutedText = [0.38 0.48 0.55];
            colors.sheath = [0.80 0.90 0.96];
            colors.bowShock = [0.12 0.38 0.56];
            colors.magnetopause = [0.03 0.21 0.35];
            colors.upstreamField = [0.72 0.83 0.90];
            colors.solarWind = [0.00 0.47 0.66];
            colors.merging = [0.91 0.43 0.10];
            colors.earth = [0.97 0.98 0.95];
            colors.earthEdge = [0.06 0.16 0.22];
            colors.axis = [0.08 0.12 0.16];

        case "high-contrast"
            colors.text = [0.00 0.00 0.00];
            colors.mutedText = [0.28 0.28 0.28];
            colors.sheath = [0.90 0.90 0.90];
            colors.bowShock = [0.00 0.00 0.00];
            colors.magnetopause = [0.00 0.00 0.00];
            colors.upstreamField = [0.72 0.72 0.72];
            colors.solarWind = [0.00 0.00 0.00];
            colors.merging = [0.00 0.00 0.00];
            colors.earth = [1.00 1.00 1.00];
            colors.earthEdge = [0.00 0.00 0.00];
            colors.axis = [0.00 0.00 0.00];

        case "reference-gray"
            colors.text = [0.14 0.14 0.14];
            colors.mutedText = [0.50 0.50 0.50];
            colors.sheath = [0.86 0.87 0.88];
            colors.bowShock = [0.25 0.25 0.25];
            colors.magnetopause = [0.12 0.12 0.12];
            colors.upstreamField = [0.88 0.89 0.90];
            colors.solarWind = [0.12 0.12 0.12];
            colors.merging = [0.12 0.12 0.12];
            colors.earth = [0.98 0.98 0.97];
            colors.earthEdge = [0.12 0.12 0.12];
            colors.axis = [0.12 0.12 0.12];

        otherwise
            error('Unknown color_scheme: %s', name);
    end
end
