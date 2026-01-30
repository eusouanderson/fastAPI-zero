const form = document.getElementById("scrape-form");
const searchForm = document.getElementById("search-form");
const statusEl = document.getElementById("status");
const searchStatusEl = document.getElementById("search-status");
const resultsEl = document.getElementById("results");
const rawEl = document.getElementById("raw");
const sortEl = document.getElementById("result-sort");
const priceMinEl = document.getElementById("price-min");
const priceMaxEl = document.getElementById("price-max");
const loadingOverlay = document.getElementById("loading-overlay");
const loadingText = document.getElementById("loading-text");

let lastResults = [];

const showLoading = (message = "Buscando produtos...") => {
  loadingText.textContent = message;
  loadingOverlay.classList.remove("hidden");
};

const hideLoading = () => {
  loadingOverlay.classList.add("hidden");
};

const normalizeText = (value) =>
  value
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

const calculateRelevance = (text, query) => {
  if (!query || !text) return 0;
  const normalizedText = text.toLowerCase();
  const normalizedQuery = query.toLowerCase();
  const words = normalizedQuery.split(/\s+/);
  
  let score = 0;
  for (const word of words) {
    if (normalizedText.includes(word)) {
      score += 1;
    }
  }
  
  // Exact match bonus
  if (normalizedText.includes(normalizedQuery)) {
    score += words.length;
  }
  
  return score;
};

const looksLikeProductUrl = (url) =>
  /\/produto\//i.test(url) ||
  /\/product\//i.test(url) ||
  /\/item\//i.test(url) ||
  /\/p\/[\w-]*\d/i.test(url) ||
  /\/MLB-\d+/i.test(url);

const discoverFromBaseUrls = async (baseUrls) => {
  const includePatterns = [
    "/produto/",
    "/product/",
    "/item/",
    "/p/[\\w-]*\\d",
    "/MLB-\\d+",
  ];

  const discovered = new Set();

  for (const baseUrl of baseUrls) {
    try {
      const response = await fetch("/crawl/urls", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          base_url: baseUrl,
          max_urls: 500,
          max_concurrency: 10,
          include_patterns: includePatterns,
          use_sitemap: true,
          follow_links: false,
          max_depth: 1,
        }),
      });

      if (!response.ok) {
        continue;
      }

      const data = await response.json();
      (data.urls || []).forEach((url) => discovered.add(url));
    } catch (error) {
      // Ignore discovery errors per base URL
    }
  }

  return Array.from(discovered);
};

const renderTable = (container, headers, rows) => {
  container.innerHTML = "";
  const headerRow = document.createElement("div");
  headerRow.className = "row header";
  headers.forEach((h) => {
    const span = document.createElement("span");
    span.textContent = h;
    headerRow.appendChild(span);
  });
  container.appendChild(headerRow);

  if (!rows.length) {
    const empty = document.createElement("div");
    empty.className = "row";
    empty.innerHTML = `<span>Sem dados</span>`;
    container.appendChild(empty);
    return;
  }

  rows.forEach((row) => {
    container.appendChild(row);
  });
};

const defaultStoreUrls = [
  "https://www.kabum.com.br/",
  "https://www.pichau.com.br/",
  "https://www.terabyteshop.com.br/",
  "https://lista.mercadolivre.com.br/pecas-de-computadores",
  "https://www.popshopinformatica.com.br/pecas-para-computador",
  "https://www.netalfa.com.br/hardware",
  "https://www.brazilpc.com.br/",
  "https://www.loja.gsiinformatica.com.br/pecas",
];

const buildResultRow = (item) => {
  const row = document.createElement("div");
  row.className = "row";

  const name = document.createElement("span");
  name.textContent = item.name;

  const category = document.createElement("span");
  category.textContent = item.category ?? "-";

  const price = document.createElement("span");
  price.textContent = `${item.currency ?? ""} ${item.lowest_price.toFixed(2)}`;

  const link = document.createElement("a");
  link.href = item.source_url;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.textContent = "Abrir";

  row.append(name, category, price, link);
  return row;
};

const applyResultFilters = () => {
  if (!lastResults.length) {
    renderTable(resultsEl, ["Produto", "Categoria", "Menor preço", "Link"], []);
    return;
  }

  const minValue = Number(priceMinEl?.value || "0");
  const maxRaw = priceMaxEl?.value;
  const maxValue = maxRaw ? Number(maxRaw) : Number.POSITIVE_INFINITY;
  const sortValue = sortEl?.value || "price-asc";

  let filtered = lastResults.filter((item) => {
    const price = Number(item.lowest_price || 0);
    return price >= minValue && price <= maxValue;
  });

  filtered = filtered.sort((a, b) => {
    if (sortValue === "price-desc") {
      return b.lowest_price - a.lowest_price;
    }
    if (sortValue === "name-asc") {
      return (a.name || "").localeCompare(b.name || "");
    }
    if (sortValue === "name-desc") {
      return (b.name || "").localeCompare(a.name || "");
    }
    return a.lowest_price - b.lowest_price;
  });

  renderTable(
    resultsEl,
    ["Produto", "Categoria", "Menor preço", "Link"],
    filtered.map(buildResultRow)
  );
};

const buildRawRow = (item) => {
  const row = document.createElement("div");
  row.className = "row";

  const title = document.createElement("span");
  title.textContent = item.title ?? "Sem título";

  const price = document.createElement("span");
  price.textContent = item.price ? item.price.toFixed(2) : "-";

  const currency = document.createElement("span");
  currency.textContent = item.currency ?? "-";

  const link = document.createElement("a");
  link.href = item.url;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.textContent = "Abrir";

  row.append(title, currency, price, link);
  return row;
};

const runScrape = async (urls, searchQuery = null) => {
  statusEl.textContent = "";
  resultsEl.innerHTML = "";
  rawEl.innerHTML = "";

  if (!urls.length) {
    statusEl.textContent = "Informe pelo menos uma URL.";
    return;
  }

  const productUrls = urls.filter(looksLikeProductUrl);
  const baseUrls = urls.filter((url) => !looksLikeProductUrl(url));

  let finalUrls = productUrls;

  if (!finalUrls.length && baseUrls.length) {
    showLoading("Descobrindo produtos nas lojas...");
    finalUrls = await discoverFromBaseUrls(baseUrls);
  }

  if (!finalUrls.length) {
    hideLoading();
    statusEl.textContent = "Não encontrei URLs de produtos. Tente links diretos de produtos.";
    return;
  }

  // Filter URLs by query if provided
  if (searchQuery) {
    const filtered = finalUrls.filter((url) => {
      const relevance = calculateRelevance(url, searchQuery);
      return relevance > 0;
    });
    
    if (filtered.length > 0) {
      finalUrls = filtered;
      statusEl.textContent = `Filtrados ${finalUrls.length} URLs relevantes para "${searchQuery}"`;
    }
  }

  const payload = {
    urls: finalUrls,
    category: document.getElementById("category").value || null,
    max_concurrency: Number(document.getElementById("concurrency").value),
  };

  form.querySelector("button").disabled = true;
  if (searchForm) {
    searchForm.querySelector("button").disabled = true;
  }
  
  showLoading("Processando... Extraindo preços...");

  try {
    const response = await fetch("/scrape/urls", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail ?? "Erro ao rodar scraping");
    }

    const data = await response.json();
    
    let products = data.products || [];
    
    // Filter products by search query if provided
    if (searchQuery) {
      products = products
        .map(p => ({
          ...p,
          _relevance: calculateRelevance(p.name, searchQuery)
        }))
        .filter(p => p._relevance > 0)
        .sort((a, b) => b._relevance - a._relevance);
      
      statusEl.textContent = `Capturados ${data.total_scraped} URLs. Salvos ${data.total_saved} preços. ${products.length} relevantes para "${searchQuery}".`;
    } else {
      statusEl.textContent = `Capturados ${data.total_scraped} URLs. Salvos ${data.total_saved} preços.`;
    }

    lastResults = products;
    applyResultFilters();

    renderTable(
      rawEl,
      ["Título", "Moeda", "Preço", "Link"],
      data.raw_items.map(buildRawRow)
    );
  } catch (error) {
    statusEl.textContent = error.message;
  } finally {
    hideLoading();
    form.querySelector("button").disabled = false;
    if (searchForm) {
      searchForm.querySelector("button").disabled = false;
    }
  }
};

if (sortEl) {
  sortEl.addEventListener("change", applyResultFilters);
}
if (priceMinEl) {
  priceMinEl.addEventListener("input", applyResultFilters);
}
if (priceMaxEl) {
  priceMaxEl.addEventListener("input", applyResultFilters);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const urls = document
    .getElementById("urls")
    .value.split("\n")
    .map((url) => url.trim())
    .filter(Boolean);
  
  const searchQuery = document.getElementById("search-query")?.value.trim() || null;

  await runScrape(urls.length ? urls : defaultStoreUrls, searchQuery);
});

if (searchForm) {
  searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    searchStatusEl.textContent = "";

    const searchTerm = document.getElementById("search-term").value.trim();
    const searchUrlInput = document.getElementById("search-url").value.trim();
    const maxPages = Number(document.getElementById("search-pages").value);
    const maxUrls = Number(document.getElementById("search-limit").value);
    const temperature = Number(
      document.getElementById("search-temperature").value
    );

    const finalSearchUrl = searchTerm
      ? `https://www.kabum.com.br/busca/${normalizeText(searchTerm)}`
      : searchUrlInput;

    if (!finalSearchUrl) {
      searchStatusEl.textContent = "Informe o nome da pesquisa ou a URL de busca.";
      return;
    }

    searchForm.querySelector("button").disabled = true;
    showLoading(`Buscando por "${searchTerm || "produtos"}"`);

    try {
      const response = await fetch("/crawl/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          search_url: finalSearchUrl,
          query: searchTerm || null,
          max_pages: maxPages,
          max_urls: maxUrls,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail ?? "Erro ao buscar produtos");
      }

      const data = await response.json();
      let urls = data.urls;

      if (searchTerm) {
        const needle = normalizeText(searchTerm);
        const threshold = 0.2 + temperature * 0.6;
        urls = urls.filter((url) => {
          const slug = normalizeText(url.split("/produto/")[1] ?? "");
          const hit = slug.includes(needle);
          if (temperature < 0.4) {
            return hit;
          }
          if (temperature < 0.7) {
            return hit || Math.random() < threshold * 0.2;
          }
          return true;
        });
      }

      searchStatusEl.textContent = `Encontrados ${data.total_urls} produtos. Rodando scraping...`;
      showLoading("Coletando dados dos produtos...");
      await runScrape(urls);
    } catch (error) {
      hideLoading();
      searchStatusEl.textContent = error.message;
    } finally {
      searchForm.querySelector("button").disabled = false;
    }
  });
}
