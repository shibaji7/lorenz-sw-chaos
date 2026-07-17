%% Magnetotail reference-style schematic
clc; clear; close all;

% matlab -batch "addpath('src/lorenzsw'); figure1_magnetotail_reference"

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
set(ax, 'Position', [0.04 0.06 0.92 0.88]);

dark = [0.18 0.18 0.18];
field = [0.56 0.58 0.58];
field_light = [0.72 0.74 0.74];
sheet = [0.66 0.67 0.68];
aurora = [0.10 0.58 0.20];
earth_blue = [0.62 0.78 0.83];
land = [0.06 0.18 0.18];

earth_center = [3.25, 3.55];
earth_r = 0.43;
ang = linspace(0, 2*pi, 260);

%% Magnetopause and lobes
t = linspace(-1.18, 1.18, 260);
x_mp = earth_center(1) - 0.25 - 1.45 * cos(t) - 0.52 * cos(t).^2;
y_mp = earth_center(2) + 2.55 * sin(t);
plot(ax, x_mp, y_mp, '--', 'Color', [0.48 0.48 0.48], 'LineWidth', 1.1);

x_upper = linspace(earth_center(1) + 0.25, 8.00, 260);
y_upper = earth_center(2) + 0.90 + 1.05 * (1 - exp(-(x_upper - earth_center(1)) / 1.25));
x_lower = x_upper;
y_lower = earth_center(2) - 0.90 - 1.05 * (1 - exp(-(x_lower - earth_center(1)) / 1.25));
plot(ax, x_upper, y_upper, '-', 'Color', field_light, 'LineWidth', 1.1);
plot(ax, x_lower, y_lower, '-', 'Color', field_light, 'LineWidth', 1.1);
text(ax, 6.55, 5.95, 'MAGNETOTAIL LOBE', 'FontSize', 8.5, ...
    'FontWeight', 'bold', 'HorizontalAlignment', 'center');

%% Plasma sheet
x_ps = linspace(earth_center(1) + 0.38, 9.55, 280);
top_ps = earth_center(2) + 0.42 * exp(-(x_ps - earth_center(1)) / 4.7) + 0.10;
bot_ps = earth_center(2) - 0.42 * exp(-(x_ps - earth_center(1)) / 4.7) - 0.10;
top_ps = top_ps - 0.08 * (x_ps - x_ps(1)) / (x_ps(end) - x_ps(1));
bot_ps = bot_ps + 0.08 * (x_ps - x_ps(1)) / (x_ps(end) - x_ps(1));
fill(ax, [x_ps, fliplr(x_ps)], [top_ps, fliplr(bot_ps)], sheet, ...
    'EdgeColor', [0.38 0.38 0.38], 'LineWidth', 0.8, 'FaceAlpha', 0.82);
text(ax, 5.25, earth_center(2) + 0.02, 'PLASMA SHEET', 'FontSize', 9.0, ...
    'FontWeight', 'bold', 'Color', 'w', 'HorizontalAlignment', 'center');

% Nightside reconnection tail crossing.
plot(ax, [8.55 9.85], [earth_center(2) + 0.12, earth_center(2) + 0.30], ...
    '-', 'Color', [0.40 0.40 0.40], 'LineWidth', 1.0);
plot(ax, [8.55 9.85], [earth_center(2) - 0.12, earth_center(2) - 0.30], ...
    '-', 'Color', [0.40 0.40 0.40], 'LineWidth', 1.0);
text(ax, 8.45, 2.72, 'NIGHTSIDE', 'FontSize', 8.6, 'FontWeight', 'bold');
text(ax, 8.45, 2.48, 'RECONNECTION', 'FontSize', 8.6, 'FontWeight', 'bold');

%% Magnetic field lines
for scale = [0.78, 1.04, 1.32]
    theta = linspace(-1.18, 1.18, 240);
    x_line = earth_center(1) - 0.10 - scale * (0.72 * cos(theta) + 0.46 * cos(theta).^2);
    y_line = earth_center(2) + scale * 1.05 * sin(theta);
    plot(ax, x_line, y_line, '-', 'Color', field, 'LineWidth', 1.1);
    arrow_on_curve(ax, x_line, y_line, 75, 84, field, 0.11);
end

for scale = [1.15, 1.55, 1.95]
    theta = linspace(-1.30, 1.30, 260);
    x_line = earth_center(1) - 0.05 - scale * (0.92 * cos(theta) + 0.28 * cos(theta).^2);
    y_line = earth_center(2) + scale * 1.20 * sin(theta);
    keep = x_line > 0.40 & y_line > 0.20 & y_line < 6.80;
    plot(ax, x_line(keep), y_line(keep), '-', 'Color', field, 'LineWidth', 1.0);
    idx = find(keep, 1, 'first') + 55;
    if idx < numel(x_line) - 8
        arrow_on_curve(ax, x_line, y_line, idx, idx + 8, field, 0.10);
    end
end

for sgn = [-1, 1]
    for offset = [0.05, 0.34]
        u = linspace(0, 1, 230);
        x0 = earth_center(1) + 0.20;
        y0 = earth_center(2) + sgn * (0.48 + 0.12 * offset);
        x1 = 7.75;
        y1 = earth_center(2) + sgn * (1.45 + offset);
        x_line = x0 + (x1 - x0) * u;
        y_line = y0 + (y1 - y0) * (1 - exp(-3.2*u)) / (1 - exp(-3.2));
        y_line = y_line + sgn * 0.10 * sin(pi*u) .* (1 - u);
        plot(ax, x_line, y_line, '-', 'Color', field_light, 'LineWidth', 1.0);
        arrow_on_curve(ax, x_line, y_line, 72, 63, field_light, 0.095);
    end
end

text(ax, 1.30, 3.35, 'MAGNETIC FIELD LINE', 'FontSize', 8.2, ...
    'FontWeight', 'bold', 'Rotation', 62);

%% Earth, polar cap, and auroral oval
fill(ax, earth_center(1) + earth_r*cos(ang), earth_center(2) + earth_r*sin(ang), ...
    earth_blue, 'EdgeColor', 'none');

land1 = earth_center + earth_r * [0.30*cos(linspace(0,2*pi,50)) - 0.18; ...
    0.90*sin(linspace(0,2*pi,50)) + 0.02]';
land2 = earth_center + earth_r * [0.22*cos(linspace(0,2*pi,45)) + 0.10; ...
    0.65*sin(linspace(0,2*pi,45)) - 0.04]';
fill(ax, land1(:,1), land1(:,2), land, 'EdgeColor', 'none');
fill(ax, land2(:,1), land2(:,2), land, 'EdgeColor', 'none');

plot(ax, earth_center(1) + earth_r*cos(ang), earth_center(2) + earth_r*sin(ang), ...
    '-', 'Color', dark, 'LineWidth', 0.8);

draw_oval_band(ax, earth_center + [0.00, 0.36], 0.50, 0.16, 0.33, 0.075, ...
    200, 340, aurora);
draw_oval_band(ax, earth_center + [0.00, -0.36], 0.47, 0.14, 0.31, 0.065, ...
    20, 160, aurora);
text(ax, earth_center(1) + 0.08, earth_center(2) + 0.62, 'POLAR', ...
    'FontSize', 6.2, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
text(ax, earth_center(1) + 0.08, earth_center(2) + 0.48, 'CAP', ...
    'FontSize', 6.2, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
text(ax, earth_center(1) + 0.18, earth_center(2) - 0.72, 'AURORAL', ...
    'FontSize', 6.8, 'FontWeight', 'bold', 'Color', aurora, ...
    'HorizontalAlignment', 'center');
text(ax, earth_center(1) + 0.18, earth_center(2) - 0.90, 'OVAL', ...
    'FontSize', 6.8, 'FontWeight', 'bold', 'Color', aurora, ...
    'HorizontalAlignment', 'center');

% Small inner plasma-sphere indication, kept visually secondary.
ps_ctr = earth_center + [0.50, 0.00];
fill(ax, ps_ctr(1) + 0.28*cos(ang), ps_ctr(2) + 0.34*sin(ang), ...
    [0.94 0.94 0.92], 'EdgeColor', [0.50 0.50 0.50], 'LineWidth', 0.7);
text(ax, ps_ctr(1), ps_ctr(2), 'PLASMA', 'FontSize', 5.8, ...
    'Rotation', 90, 'HorizontalAlignment', 'center');
text(ax, ps_ctr(1) + 0.16, ps_ctr(2), 'SPHERE', 'FontSize', 5.8, ...
    'Rotation', 90, 'HorizontalAlignment', 'center');

set(fig, 'InvertHardcopy', 'off');
ref_png = fullfile(out_dir, 'figure1_magnetotail_reference.png');
target_png = fullfile(out_dir, 'figure1_solar_wind_schematic.png');
exportgraphics(fig, ref_png, 'Resolution', 600);
if isfile(target_png)
    ref_img = imread(ref_png);
    target_img = imread(target_png);
    [target_h, target_w, ~] = size(target_img);
    [ref_h, ref_w, ref_c] = size(ref_img);
    canvas = uint8(255 * ones(target_h, target_w, ref_c));
    paste_h = min(ref_h, target_h);
    paste_w = min(ref_w, target_w);
    y0 = floor((target_h - paste_h) / 2) + 1;
    x0 = floor((target_w - paste_w) / 2) + 1;
    src_y0 = floor((ref_h - paste_h) / 2) + 1;
    src_x0 = floor((ref_w - paste_w) / 2) + 1;
    canvas(y0:y0+paste_h-1, x0:x0+paste_w-1, :) = ...
        ref_img(src_y0:src_y0+paste_h-1, src_x0:src_x0+paste_w-1, :);
    imwrite(canvas, ref_png);
end
exportgraphics(fig, fullfile(out_dir, 'figure1_magnetotail_reference.pdf'), 'ContentType', 'vector');

function draw_oval_band(ax, center, outer_rx, outer_ry, inner_rx, inner_ry, a1, a2, color)
    th = linspace(a1, a2, 100) * pi / 180;
    xo = center(1) + outer_rx * cos(th);
    yo = center(2) + outer_ry * sin(th);
    xi = center(1) + inner_rx * cos(fliplr(th));
    yi = center(2) + inner_ry * sin(fliplr(th));
    fill(ax, [xo, xi], [yo, yi], color, 'EdgeColor', 'none', 'FaceAlpha', 0.95);
end

function arrow_on_curve(ax, x, y, i0, i1, color, head_size)
    i0 = max(1, min(numel(x), i0));
    i1 = max(1, min(numel(x), i1));
    p0 = [x(i0), y(i0)];
    p1 = [x(i1), y(i1)];
    plot(ax, [p0(1), p1(1)], [p0(2), p1(2)], '-', 'Color', color, 'LineWidth', 0.8);
    v = p1 - p0;
    v = v / max(norm(v), eps);
    n = [-v(2), v(1)];
    base = p1 - 1.45 * head_size * v;
    tip = [p1; base + head_size*n; base - head_size*n];
    patch(ax, tip(:,1), tip(:,2), color, 'EdgeColor', 'none');
end
