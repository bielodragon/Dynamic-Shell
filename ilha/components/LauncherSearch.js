.pragma library

function normalized(value) {
    return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}
function score(title, extra, query) {
    const name = normalized(title), other = normalized(extra), text = normalized(query).trim();
    if (!text) return 1;
    if (name === text) return 1000;
    if (name.startsWith(text)) return 800 - Math.min(100, name.length);
    if (name.includes(text)) return 600 - name.indexOf(text);
    if (other.includes(text)) return 300;
    let index = 0, gap = 0;
    for (const letter of text) {
        const found = name.indexOf(letter, index);
        if (found < 0) return 0;
        gap += found - index; index = found + 1;
    }
    return Math.max(1, 100 - gap);
}
function apps(entries, query) {
    return Array.from(entries).map(entry => ({kind:"app", id:entry.id, title:entry.name,
        detail:entry.genericName || entry.comment || "Aplicativo", icon:entry.icon,
        rank:score(entry.name, (entry.comment || "") + " " + Array.from(entry.keywords || []).join(" "), query)}))
        .filter(row => row.rank > 0).sort((a,b) => b.rank - a.rank || a.title.localeCompare(b.title)).slice(0, 40);
}
function clipboard(entries, query) {
    return entries.filter(row => normalized(row.title).includes(normalized(query).trim()));
}

// O catálogo é nosso; os nomes em inglês também permitem os atalhos conhecidos.
function actions(query) {
    const rows = [
        {id:"wallpapers", title:"Mudar wallpaper", detail:"Escolher em ~/Pictures/Wallpapers", icon:"preferences-desktop-wallpaper", keywords:"wallpaper fundo papel de parede"},
        {id:"light", title:"Modo claro", detail:"Aplicar o tema Claro da Ilha", icon:"weather-clear", keywords:"light claro"},
        {id:"dark", title:"Modo escuro", detail:"Aplicar o tema Escuro da Ilha", icon:"weather-clear-night", keywords:"dark escuro"},
        {id:"random-wallpaper", title:"Wallpaper aleatório", detail:"Sortear uma imagem de ~/Pictures/Wallpapers", icon:"media-playlist-shuffle", keywords:"random randomizar wallpaper aleatorio"},
        {id:"themes", title:"Mudar esquema de cores", detail:"Escolher entre os temas prontos e personalizados", icon:"preferences-desktop-theme", keywords:"scheme schema esquema cores tema theme"},
        {id:"lock", title:"Bloquear tela", detail:"Bloquear a sessão atual", icon:"system-lock-screen", keywords:"lock bloquear"}
    ];
    return rows.map((row, order) => Object.assign({kind:"action",order:order}, row, {rank:score(row.title,row.keywords,query)}))
        .filter(row => row.rank > 0).sort((a,b) => b.rank - a.rank || a.order - b.order);
}
function filterRows(rows, query) {
    return rows.map(row => Object.assign({},row,{rank:score(row.title,row.detail,query)}))
        .filter(row => row.rank > 0).sort((a,b) => b.rank - a.rank || a.title.localeCompare(b.title)).slice(0,60);
}
