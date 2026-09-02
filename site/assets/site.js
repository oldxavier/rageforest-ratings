const state = {
  players: [],
  visible: 100,
  query: "",
  sortKey: null,
  sortType: null,
  sortDirection: "ascending",
};

const body = document.querySelector("#ratings-body");
const search = document.querySelector("#player-search");
const showAll = document.querySelector("#show-all");
const count = document.querySelector("#result-count");
const sortButtons = [...document.querySelectorAll("[data-sort]")];

const escapeHtml = (value) =>
  String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  })[character]);

function sortableValue(player, key, type) {
  const value = player[key];
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
  sortButtons.forEach((button) => {
    const active = button.dataset.sort === state.sortKey;
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
    ? ` Sorted by ${sortButtons.find((button) => button.dataset.sort === state.sortKey).textContent.trim().toLocaleLowerCase()} (${state.sortDirection}).`
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

sortButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const sameColumn = state.sortKey === button.dataset.sort;
    state.sortDirection = sameColumn && state.sortDirection === "ascending"
      ? "descending"
      : "ascending";
    state.sortKey = button.dataset.sort;
    state.sortType = button.dataset.type;
    renderPlayers();
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
