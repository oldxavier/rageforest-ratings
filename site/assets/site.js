const state = {
  players: [],
  visible: 100,
  query: "",
  sortKey: null,
  sortType: null,
  sortDirection: "ascending",
};

const civState = {
  civilizations: [],
  scope: "all",
  sortKey: "rank",
  sortType: "number",
  sortDirection: "ascending",
};

const body = document.querySelector("#ratings-body");
const search = document.querySelector("#player-search");
const showAll = document.querySelector("#show-all");
const count = document.querySelector("#result-count");
const playerSortButtons = [...document.querySelectorAll("[data-player-sort]")];
const civBody = document.querySelector("#civ-ratings-body");
const civCount = document.querySelector("#civ-result-count");
const civRankHeading = document.querySelector("#civ-rank-heading");
const civSortButtons = [...document.querySelectorAll("[data-civ-sort]")];
const civScopeButtons = [...document.querySelectorAll("[data-civ-scope]")];

const escapeHtml = (value) =>
  String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  })[character]);

function sortableValue(row, key, type) {
  const value = row[key];
  if (type === "text") return String(value).toLocaleLowerCase();
  if (type === "rank" || type === "rating") return typeof value === "number" ? value : null;
  return Number(value);
}

function comparePlayers(left, right) {
  const a = sortableValue(left, state.sortKey, state.sortType);
  const b = sortableValue(right, state.sortKey, state.sortType);

  // Exact ranks and ratings are deliberately absent below rank 500. Keep those rows after the
  // sortable exact values rather than inventing a hidden order for them.
  if (a === null && b === null) return left.handle.localeCompare(right.handle);
  if (a === null) return 1;
  if (b === null) return -1;

  const comparison = typeof a === "string"
    ? a.localeCompare(b)
    : a - b;
  if (comparison === 0) return left.handle.localeCompare(right.handle);
  return state.sortDirection === "ascending" ? comparison : -comparison;
}

function selectedPlayers() {
  const query = state.query.trim().toLocaleLowerCase();
  let players = query
    ? state.players.filter((player) => player.handle.toLocaleLowerCase().includes(query))
    : [...state.players];
  if (state.sortKey) players.sort(comparePlayers);
  return query ? players : players.slice(0, state.visible);
}

function updateSortHeaders() {
  playerSortButtons.forEach((button) => {
    const active = button.dataset.playerSort === state.sortKey;
    button.closest("th").setAttribute(
      "aria-sort",
      active ? state.sortDirection : "none",
    );
    button.classList.toggle("active-sort", active);
  });
}

function renderPlayers() {
  const players = selectedPlayers();
  const query = state.query.trim();

  body.innerHTML = players.length
    ? players.map((player) => `
      <tr>
        <td>${player.rank}</td>
        <td>${escapeHtml(player.handle)}</td>
        <td>${player.rating}</td>
        <td>±${player.uncertainty}</td>
        <td>${player.games.toLocaleString()}</td>
        <td>${player.win_rate.toFixed(1)}%</td>
        <td>${player.team_average_rating}</td>
        <td>${player.opponent_team_average_rating}</td>
        <td>${player.average_lobby_rating}</td>
      </tr>`).join("")
    : '<tr><td colspan="9" class="loading">No matching player.</td></tr>';

  const sorted = state.sortKey
    ? ` Sorted by ${playerSortButtons.find((button) => button.dataset.playerSort === state.sortKey).textContent.trim().toLocaleLowerCase()} (${state.sortDirection}).`
    : "";
  count.textContent = query
    ? `${players.length} matching player${players.length === 1 ? "" : "s"}.${sorted}`
    : `Showing ${Math.min(state.visible, state.players.length)} of ${state.players.length} players.${sorted}`;
  showAll.textContent = state.visible === 765 ? "Show first 100" : "Show all 765";
  updateSortHeaders();
}

search.addEventListener("input", (event) => {
  state.query = event.target.value;
  renderPlayers();
});

showAll.addEventListener("click", () => {
  state.visible = state.visible === 765 ? 100 : 765;
  state.query = "";
  search.value = "";
  renderPlayers();
});

playerSortButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const sameColumn = state.sortKey === button.dataset.playerSort;
    state.sortDirection = sameColumn && state.sortDirection === "ascending"
      ? "descending"
      : "ascending";
    state.sortKey = button.dataset.playerSort;
    state.sortType = button.dataset.type;
    renderPlayers();
  });
});

function selectedCivilizations() {
  const top100Order = [...civState.civilizations].sort((left, right) =>
    right.top100_win_rate - left.top100_win_rate
    || right.top100_games - left.top100_games
    || left.civilization.localeCompare(right.civilization));
  const top100Ranks = new Map(
    top100Order.map((civilization, index) => [civilization.civilization, index + 1]),
  );
  const rows = civState.civilizations.map((civilization) => ({
    ...civilization,
    model_rank: civilization.rank,
    rank: civState.scope === "all"
      ? civilization.rank
      : top100Ranks.get(civilization.civilization),
    games: civilization[`${civState.scope}_games`],
    win_rate: civilization[`${civState.scope}_win_rate`],
  }));

  rows.sort((left, right) => {
    const a = sortableValue(left, civState.sortKey, civState.sortType);
    const b = sortableValue(right, civState.sortKey, civState.sortType);
    const comparison = typeof a === "string" ? a.localeCompare(b) : a - b;
    if (comparison === 0) return left.civilization.localeCompare(right.civilization);
    return civState.sortDirection === "ascending" ? comparison : -comparison;
  });
  return rows;
}

function updateCivSortHeaders() {
  civSortButtons.forEach((button) => {
    const active = button.dataset.civSort === civState.sortKey;
    button.closest("th").setAttribute(
      "aria-sort",
      active ? civState.sortDirection : "none",
    );
    button.classList.toggle("active-sort", active);
  });
}

function renderCivilizations() {
  const rows = selectedCivilizations();
  civBody.innerHTML = rows.length
    ? rows.map((civilization) => {
      const effect = civilization.rating_effect > 0
        ? `+${civilization.rating_effect}`
        : civilization.rating_effect;
      return `
        <tr>
          <td>${civilization.rank}</td>
          <td>${escapeHtml(civilization.civilization)}</td>
          <td>${effect}</td>
          <td>${civilization.games.toLocaleString()}</td>
          <td>${civilization.win_rate.toFixed(1)}%</td>
        </tr>`;
    }).join("")
    : '<tr><td colspan="5" class="loading">Civilization ratings could not be loaded.</td></tr>';

  const scope = civState.scope === "all"
    ? "all eligible games"
    : "games with at least two final top-100 players on each team";
  civRankHeading.textContent = civState.scope === "all"
    ? "Model rank"
    : "Top-100 win-rate rank";
  civCount.textContent = `${rows.length} civilizations · ${scope}.`;
  updateCivSortHeaders();
}

civScopeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    civState.scope = button.dataset.civScope;
    civState.sortKey = "rank";
    civState.sortType = "number";
    civState.sortDirection = "ascending";
    civScopeButtons.forEach((candidate) => {
      const active = candidate === button;
      candidate.classList.toggle("active", active);
      candidate.setAttribute("aria-pressed", active);
    });
    renderCivilizations();
  });
});

civSortButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const sameColumn = civState.sortKey === button.dataset.civSort;
    civState.sortDirection = sameColumn && civState.sortDirection === "ascending"
      ? "descending"
      : "ascending";
    civState.sortKey = button.dataset.civSort;
    civState.sortType = button.dataset.type;
    renderCivilizations();
  });
});

fetch("data/ratings.json")
  .then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then((payload) => {
    state.players = payload.players;
    renderPlayers();
  })
  .catch(() => {
    body.innerHTML = '<tr><td colspan="9" class="loading">Ratings could not be loaded.</td></tr>';
    count.textContent = "The downloadable CSV remains available above.";
  });

fetch("data/civilizations.json")
  .then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then((payload) => {
    civState.civilizations = payload.civilizations;
    renderCivilizations();
  })
  .catch(() => {
    civBody.innerHTML = '<tr><td colspan="5" class="loading">Civilization ratings could not be loaded.</td></tr>';
    civCount.textContent = "The downloadable CSV remains available above.";
  });
