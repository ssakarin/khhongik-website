const lookup = document.querySelector(".fee-lookup");
const query = document.querySelector("#fee-query");
const status = document.querySelector("#fee-search-status");
const groups = [...document.querySelectorAll(".fee-group")].map((section) => ({
  section,
  name: section.querySelector("h2").textContent,
  rows: [...section.querySelectorAll("tbody tr")],
}));

function normalize(text) {
  return text.toLowerCase().replace(/[\s·(),]+/g, "");
}

function filterFees() {
  const term = normalize(query.value);
  let matches = 0;

  for (const { section, name, rows } of groups) {
    let groupMatches = 0;
    for (const row of rows) {
      const item = row.querySelector('th[scope="row"]').textContent;
      row.hidden = !normalize(name + item).includes(term);
      if (!row.hidden) groupMatches += 1;
    }
    section.hidden = groupMatches === 0;
    matches += groupMatches;
  }

  status.textContent = term ? (matches ? `검색 결과 ${matches}개` : "일치하는 항목이 없습니다.") : "";
}

lookup.hidden = false;
query.addEventListener("input", filterFees);
