const state = { players: [], visible: 100, query: "" };

const body = document.querySelector("#ratings-body");
const search = document.querySelector("#player-search");
const showAll = document.querySelector("#show-all");
const count = document.querySelector("#result-count");

const escapeHtml = (value) =>
  String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  })[character]);

function renderPlayers() {
  const query = state.query.trim().toLocaleLowerCase();
  const filtered = query
    ? state.players.filter((player) => player.handle.toLocaleLowerCase().includes(query))
    : state.players.slice(0, state.visible);

  body.innerHTML = filtered.length
    ? filtered.map((player) => `
      <tr>
        <td>${player.rank}</td>
        <td>${escapeHtml(player.handle)}</td>
        <td>${player.rating}</td>
        <td>±${player.uncertainty}</td>
        <td>${player.games.toLocaleString()}</td>
        <td>${player.win_rate.toFixed(1)}%</td>
        <td>${player.activity}</td>
      </tr>`).join("")
    : '<tr><td colspan="7" class="loading">No matching player.</td></tr>';

  count.textContent = query
    ? `${filtered.length} match${filtered.length === 1 ? "" : "es"} across all 765 players`
    : `Showing ${Math.min(state.visible, state.players.length)} of ${state.players.length} named players`;
  showAll.textContent = state.visible === 765 ? "Show top 100" : "Show all 765";
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
    body.innerHTML = '<tr><td colspan="7" class="loading">Ratings could not be loaded.</td></tr>';
    count.textContent = "The downloadable CSV remains available above.";
  });
