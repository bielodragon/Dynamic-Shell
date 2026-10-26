function hexToRgb(hex) {
    const value = hex.replace("#", "");
    return [parseInt(value.slice(0, 2), 16), parseInt(value.slice(2, 4), 16), parseInt(value.slice(4, 6), 16)];
}

function rgbToHsv(hex) {
    const rgb = hexToRgb(hex).map(value => value / 255);
    const max = Math.max(...rgb), min = Math.min(...rgb), delta = max - min;
    let hue = 0;
    if (delta > 0) {
        if (max === rgb[0]) hue = ((rgb[1] - rgb[2]) / delta) % 6;
        else if (max === rgb[1]) hue = (rgb[2] - rgb[0]) / delta + 2;
        else hue = (rgb[0] - rgb[1]) / delta + 4;
        hue = (hue * 60 + 360) % 360;
    }
    return [hue, max === 0 ? 0 : delta / max, max];
}

function hsvToHex(hue, saturation, value) {
    const chroma = value * saturation;
    const segment = hue / 60;
    const middle = chroma * (1 - Math.abs(segment % 2 - 1));
    const offset = value - chroma;
    let rgb;
    if (segment < 1) rgb = [chroma, middle, 0];
    else if (segment < 2) rgb = [middle, chroma, 0];
    else if (segment < 3) rgb = [0, chroma, middle];
    else if (segment < 4) rgb = [0, middle, chroma];
    else if (segment < 5) rgb = [middle, 0, chroma];
    else rgb = [chroma, 0, middle];
    return "#" + rgb.map(part => Math.round((part + offset) * 255).toString(16).padStart(2, "0")).join("");
}

function qcolorToHex(color) {
    return "#" + [color.r, color.g, color.b].map(part => Math.round(part * 255).toString(16).padStart(2, "0")).join("");
}

function luminance(hex) {
    const rgb = hexToRgb(hex).map(channel => {
        const value = channel / 255;
        return value <= 0.04045 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
}

function contrast(first, second) {
    const a = luminance(first), b = luminance(second);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}
