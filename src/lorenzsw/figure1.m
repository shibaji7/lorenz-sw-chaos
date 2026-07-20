%% Solar wind driving of geomagnetic activity schematic
clc; clear; close all;

% matlab -batch "addpath('src/lorenzsw'); figure1_schematic"

out_dir = fullfile('docs', 'assets', 'figures');
if ~exist(out_dir, 'dir')
    mkdir(out_dir);
end

fig = figure('Color', 'w', 'Units', 'inches', 'Position', [1 1 7.2 5.2]);
ax = axes(fig);
hold(ax, 'on');
axis(ax, 'equal');
axis(ax, [0 10 0 7]);
axis(ax, 'off');
set(ax, 'Position', [0.04 0.06 0.92 0.86]);

gray_line = [0.78 0.80 0.81];
dark_line = [0.12 0.12 0.12];
sheath = [0.86 0.87 0.88];
aurora_violet = [0.72 0.48 0.86];

text(ax, 5.1, 6.82, 'Solar wind driving of geomagnetic activity', ...
    'FontSize', 12, 'FontWeight', 'bold', 'Color', [0.15 0.15 0.15], ...
    'HorizontalAlignment', 'center');
text(ax, 0.35, 6.55, 'a', 'FontSize', 12, 'FontWeight', 'bold');

%% Boundaries
y = linspace(0.45, 6.45, 260);
x_bow = 3.55 + 0.12 * (y - 3.5).^2 - 0.04 * (y - 3.5);
x_mp = 5.05 + 0.35 * (y - 3.5).^2;

fill(ax, [x_bow, fliplr(x_mp)], ...
    [y, fliplr(y)], sheath, ...
    'EdgeColor', 'none', 'FaceAlpha', 0.88);
plot(ax, x_bow, y, '--', 'Color', [0.25 0.25 0.25], 'LineWidth', 1.0);
plot(ax, x_mp, y, '-', 'Color', dark_line, 'LineWidth', 1.25);

text(ax, 2.35, 5.95, 'Bow Shock', 'FontSize', 9.5);
text(ax, 7.45, 6.15, 'Magnetopause', 'FontSize', 9.5);
text(ax, 4.75, 5.45, 'Magnetosheath', 'FontSize', 9.5);
% draw_arrow(ax, [5.0 5.18], [6.0 5.42], dark_line, 0.9, 0.10);

%% Solar wind flow and upstream field lines
for x0 = [-0.1, 0.8, 1.7, 2.6]
    plot(ax, [x0 x0 + 2.2], [6.35 0.45], '-', 'Color', [0.88 0.89 0.90], 'LineWidth', 1.3);
    draw_arrow(ax, [x0 + 1.95, 1.10], [x0 + 2.08, 0.78], [0.88 0.89 0.90], 0.8, 0.09);
end
text(ax, 0.95, 3.88, 'Solar wind', 'FontSize', 9.5);
draw_arrow(ax, [2.0 3.85], [3.0 3.85], dark_line, 0.9, 0.10);
text(ax, 1.10, 0.48, 'Magnetic field lines', 'FontSize', 9.5, 'Color', [0.50 0.50 0.50]);

%% Magnetospheric field lines
theta = linspace(-1.16, 1.16, 260);
for L = [1.55, 2.0, 2.55, 3.20]
    x_north = 7.35 + 0.56 * L * sin(theta) + 0.10 * L * sin(theta).^3;
    y_north = 3.45 + 0.48 * L * cos(theta).^2 + 0.19;
    x_south = x_north;
    y_south = 3.45 - 0.39 * L * cos(theta).^2 - 0.31;

    plot(ax, x_north, y_north, '-', 'Color', gray_line, 'LineWidth', 1.05);
    plot(ax, x_south, y_south, '-', 'Color', gray_line, 'LineWidth', 1.05);

    idx = 100;
    draw_arrow(ax, [x_north(idx) y_north(idx)], [x_north(idx + 6) y_north(idx + 6)], gray_line, 0.75, 0.075);
    draw_arrow(ax, [x_south(idx + 55) y_south(idx + 55)], [x_south(idx + 49) y_south(idx + 49)], gray_line, 0.75, 0.075);
end

for r = [0.82, 1.08, 1.34]
    phi = linspace(-0.86*pi, 0.86*pi, 260);
    x_line = 7.35 + 1.12 * r * cos(phi);
    y_line = 3.45 + 0.72 * r * sin(phi);
    keep = abs(y_line - 3.45) > 0.52 | x_line > 7.75;
    plot(ax, x_line(keep), y_line(keep), '-', 'Color', gray_line, 'LineWidth', 1.0);
end

for sgn = [-1, 1]
    for offset = [0.10, 0.32, 0.54]
        u = linspace(0, 1, 190);
        x_line = 7.10 - 1.25 * u - 1.15 * u.^2;
        y_line = 3.45 + sgn * (0.56 + offset + 0.32 * u + 0.18 * u.^2);
        plot(ax, x_line, y_line, '-', 'Color', gray_line, 'LineWidth', 1.0);
        draw_arrow(ax, [x_line(90) y_line(90)], [x_line(97) y_line(97)], gray_line, 0.75, 0.075);
    end
end

%% Earth and auroral oval
earth_center = [7.35, 3.45];
earth_r = 0.58;
ang = linspace(0, 2*pi, 240);
fill(ax, earth_center(1) + earth_r * cos(ang), earth_center(2) + earth_r * sin(ang), ...
    [0.98 0.98 0.97], 'EdgeColor', dark_line, 'LineWidth', 1.2);

cap_ang = linspace(28, 152, 90) * pi / 180;
cap_outer_x = earth_center(1) + 0.48 * cos(cap_ang);
cap_outer_y = earth_center(2) + 0.43 * sin(cap_ang);
cap_inner_x = earth_center(1) + 0.30 * cos(fliplr(cap_ang));
cap_inner_y = earth_center(2) + 0.26 * sin(fliplr(cap_ang));
fill(ax, [cap_outer_x, cap_inner_x], [cap_outer_y, cap_inner_y], ...
    aurora_violet, 'EdgeColor', 'none', 'FaceAlpha', 0.95);

cap_ang2 = linspace(208, 332, 90) * pi / 180;
cap_outer_x = earth_center(1) + 0.48 * cos(cap_ang2);
cap_outer_y = earth_center(2) + 0.43 * sin(cap_ang2);
cap_inner_x = earth_center(1) + 0.30 * cos(fliplr(cap_ang2));
cap_inner_y = earth_center(2) + 0.26 * sin(fliplr(cap_ang2));
fill(ax, [cap_outer_x, cap_inner_x], [cap_outer_y, cap_inner_y], ...
    aurora_violet, 'EdgeColor', 'none', 'FaceAlpha', 0.95);
plot(ax, earth_center(1) + earth_r * cos(ang), earth_center(2) + earth_r * sin(ang), ...
    '-', 'Color', dark_line, 'LineWidth', 1.2);

text(ax, 6.45, 3.83, 'Aurora', 'FontSize', 9.5, 'HorizontalAlignment', 'center', ...
    'BackgroundColor', aurora_violet, 'Margin', 4);
text(ax, 1.55, 2.00, 'Merging', 'FontSize', 9.5);
text(ax, 1.55, 1.75, 'electric field', 'FontSize', 9.5);
draw_arrow(ax, [3.28 2.05], [3.58 2.45], dark_line, 0.9, 0.10);
draw_arrow(ax, [3.46 1.93], [3.18 1.55], dark_line, 0.9, 0.10);

%% Coordinate triad
origin = [8.95 0.90];
draw_arrow(ax, origin, origin + [0.00 0.62], dark_line, 0.9, 0.09);
draw_arrow(ax, origin, origin + [-0.45 -0.32], dark_line, 0.9, 0.09);
draw_arrow(ax, origin, origin + [0.55 0.00], dark_line, 0.9, 0.09);
text(ax, origin(1) - 0.06, origin(2) + 0.74, 'z', 'FontSize', 8.5);
text(ax, origin(1) - 0.64, origin(2) - 0.42, 'y', 'FontSize', 8.5);
text(ax, origin(1) + 0.65, origin(2) - 0.02, 'x', 'FontSize', 8.5);

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
