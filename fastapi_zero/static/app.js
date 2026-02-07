const form = document.getElementById("scrape-form");
const searchForm = document.getElementById("search-form");
const statusEl = document.getElementById("status");
const searchStatusEl = document.getElementById("search-status");
const resultsEl = document.getElementById("results");
const rawEl = document.getElementById("raw");
const sortEl = document.getElementById("result-sort");
const rawSortEl = document.getElementById("raw-sort");
const priceMinEl = document.getElementById("price-min");
const priceMaxEl = document.getElementById("price-max");
const loadingOverlay = document.getElementById("loading-overlay");
const loadingText = document.getElementById("loading-text");

let lastResults = [];
let lastRawItems = [];

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

const discoverFromBaseUrls = async (baseUrls, config) => {
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
          max_urls: config?.maxUrls ?? 500,
          max_concurrency: config?.maxConcurrency ?? 10,
          include_patterns: includePatterns,
          use_sitemap: true,
          follow_links: true,
          max_depth: config?.maxDepth ?? 1,
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
  const actions = document.createElement('div');
  actions.style.display = 'flex';
  actions.style.gap = '8px';
  const addBtn = document.createElement('button');
  addBtn.className = 'btn small';
  addBtn.textContent = 'Adicionar';
  addBtn.addEventListener('click', () => {
    addToCart(item.product_id, 1);
  });
  actions.append(link, addBtn);

  row.append(name, category, price, actions);
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

const findProductForRaw = (item) => {
  if (!lastResults.length) return null;
  const byUrl = lastResults.find((p) => p.source_url === item.url);
  if (byUrl?.product_id) return byUrl;

  const rawTitle = normalizeText(item.title || "");
  if (!rawTitle) return null;

  const candidates = lastResults.filter((p) => {
    const name = normalizeText(p.name || "");
    return name && (name.includes(rawTitle) || rawTitle.includes(name));
  });

  if (!candidates.length) return null;
  if (item.price == null) return candidates[0];

  const price = Number(item.price);
  const withPrice = candidates.find((p) =>
    Math.abs(Number(p.lowest_price || 0) - price) <= Math.max(1, price * 0.05)
  );

  return withPrice || candidates[0];
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

  const actions = document.createElement("div");
  actions.style.display = "flex";
  actions.style.gap = "8px";

  const addBtn = document.createElement("button");
  addBtn.className = "btn small";
  addBtn.textContent = "Adicionar";

  const match = findProductForRaw(item);
  if (match?.product_id) {
    addBtn.addEventListener("click", () => {
      addToCart(match.product_id, 1);
    });
  } else {
    addBtn.disabled = true;
    addBtn.title = "Produto não salvo";
  }

  actions.append(link, addBtn);

  row.append(title, currency, price, actions);
  return row;
};

const applyRawSort = () => {
  if (!lastRawItems.length) {
    renderTable(rawEl, ["Título", "Moeda", "Preço", "Ações"], []);
    return;
  }

  const sortValue = rawSortEl?.value || "price-asc";
  const sorted = lastRawItems.slice().sort((a, b) => {
    if (sortValue === "price-desc") {
      if (a.price == null && b.price == null) return 0;
      if (a.price == null) return 1;
      if (b.price == null) return -1;
      return b.price - a.price;
    }
    if (sortValue === "name-asc") {
      return (a.title || "").localeCompare(b.title || "");
    }
    if (sortValue === "name-desc") {
      return (b.title || "").localeCompare(a.title || "");
    }
    if (a.price == null && b.price == null) return 0;
    if (a.price == null) return 1;
    if (b.price == null) return -1;
    return a.price - b.price;
  });

  renderTable(
    rawEl,
    ["Título", "Moeda", "Preço", "Ações"],
    sorted.map(buildRawRow)
  );
};

/* --- Cart client (optimistic, minimal DOM updates) --- */
const cartToggle = document.getElementById('cart-toggle');
const cartPanel = document.getElementById('cart-panel');
const cartBadge = document.getElementById('cart-badge');
const cartItemsEl = document.getElementById('cart-items');

let cartState = { id: 0, items: [] };

const formatCurrency = (v) => `R$ ${Number(v || 0).toFixed(2)}`;

const updateCartBadge = () => {
  const totalQty = cartState.items.reduce((s, it) => s + (it.quantity || 0), 0);
  cartBadge.textContent = String(totalQty);
};

const renderCart = () => {
  cartItemsEl.innerHTML = '';
  if (!cartState.items.length) {
    cartItemsEl.innerHTML = '<div class="row"><span>Sem itens</span></div>';
    updateCartBadge();
    return;
  }

  for (const it of cartState.items) {
    const node = document.createElement('div');
    node.className = 'cart-item';

    const name = document.createElement('div');
    name.className = 'name';
    name.textContent = it.name || 'Produto';

    const qty = document.createElement('div');
    qty.className = 'qty';
    qty.textContent = String(it.quantity || 0);

    const price = document.createElement('div');
    price.className = 'price';
    price.textContent = it.price ? formatCurrency(it.price) : '-';

    const link = document.createElement('a');
    link.className = 'cart-link';
    link.textContent = 'Abrir';
    if (it.source_url) {
      link.href = it.source_url;
      link.target = '_blank';
      link.rel = 'noreferrer';
    } else {
      link.href = '#';
      link.addEventListener('click', (e) => e.preventDefault());
      link.style.opacity = '0.5';
    }

    const remove = document.createElement('button');
    remove.className = 'remove';
    remove.textContent = '×';
    remove.title = 'Remover';
    remove.addEventListener('click', () => {
      // optimistic remove
      const prev = cartState.items.slice();
      cartState.items = cartState.items.filter((x) => x.id !== it.id);
      renderCart();
      if (String(it.id).startsWith('temp-')) return; // no server id
      fetch(`/cart/items/${it.id}`, { method: 'DELETE' }).then((res) => {
        if (!res.ok) {
          cartState.items = prev;
          renderCart();
        }
      }).catch(() => {
        cartState.items = prev;
        renderCart();
      });
    });

    node.append(name, qty, price, link, remove);
    cartItemsEl.appendChild(node);
  }

  updateCartBadge();
};

const fetchCart = async () => {
  try {
    const res = await fetch('/cart');
    if (!res.ok) return;
    const data = await res.json();
    cartState.id = data.id || 0;
    cartState.items = (data.items || []).map((it) => ({
      id: it.id,
      product_id: it.product_id,
      name: it.name,
      quantity: it.quantity,
      price: it.lowest_price || 0,
      source_url: it.source_url || null,
    }));
    renderCart();
  } catch (e) {
    // ignore
  }
};

const addToCart = async (productId, quantity = 1) => {
  // optimistic local update: add temp item
  const tempId = `temp-${Date.now()}`;
  // try find product in lastResults to get name/price
  const prod = lastResults.find((p) => p.product_id === productId) || {};
  const existing = cartState.items.find((i) => i.product_id === productId);
  if (existing) {
    existing.quantity = existing.quantity + quantity;
  } else {
    cartState.items.push({
      id: tempId,
      product_id: productId,
      name: prod.name,
      quantity,
      price: prod.lowest_price,
      source_url: prod.source_url,
    });
  }
  renderCart();

  try {
    const res = await fetch('/cart/items', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId, quantity }),
    });
    if (!res.ok) throw new Error('failed');
    const saved = await res.json();
    // replace temp id with server id
    cartState.items = cartState.items.map((it) => (it.id === tempId ? { ...it, id: saved.id } : it));
    renderCart();
  } catch (e) {
    // revert optimistic change
    const prev = cartState.items.filter((i) => !(i.id === tempId));
    cartState.items = prev;
    renderCart();
    alert('Não foi possível adicionar ao carrinho');
  }
};

// wire toggles
if (cartToggle) {
  cartToggle.addEventListener('click', async () => {
    cartPanel.classList.toggle('hidden');
    await fetchCart();
  });
}
// panel remains open; no close button

// fetch cart once on load (non-blocking)
fetchCart();

const runScrape = async (urls, searchQuery = null, options = {}) => {
  statusEl.textContent = "";
  resultsEl.innerHTML = "";
  rawEl.innerHTML = "";
  lastRawItems = [];

  if (!urls.length) {
    statusEl.textContent = "Informe pelo menos uma URL.";
    return;
  }

  const productUrls = urls.filter(looksLikeProductUrl);
  const baseUrls = urls.filter((url) => !looksLikeProductUrl(url));

  let finalUrls = productUrls;

  if (!finalUrls.length && baseUrls.length) {
    showLoading("Descobrindo produtos nas lojas...");
    finalUrls = await discoverFromBaseUrls(baseUrls, {
      maxUrls: options.maxUrls,
      maxDepth: options.maxPages,
      maxConcurrency: options.maxConcurrency,
    });
  }

  if (!finalUrls.length) {
    hideLoading();
    statusEl.textContent = "Não encontrei URLs de produtos. Tente links diretos de produtos.";
    return;
  }

  // Filter URLs by query if provided
  if (searchQuery) {
    const temperature = Number(options.temperature ?? 0.3);
    const threshold = 0.2 + temperature * 0.6;
    const needle = normalizeText(searchQuery);

    const filtered = finalUrls.filter((url) => {
      const slug = normalizeText(url);
      const hit = slug.includes(needle);
      if (temperature < 0.4) {
        return hit;
      }
      if (temperature < 0.7) {
        return hit || Math.random() < threshold * 0.2;
      }
      return true;
    });

    if (filtered.length > 0) {
      finalUrls = filtered;
      statusEl.textContent = `Filtrados ${finalUrls.length} URLs relevantes para "${searchQuery}"`;
    }
  }

  const payload = {
    urls: finalUrls,
    category: document.getElementById("category").value || null,
    max_concurrency: Number(options.maxConcurrency ?? document.getElementById("concurrency").value),
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
      const temperature = Number(options.temperature ?? 0.3);
      const threshold = 0.2 + temperature * 0.6;
      const relevantProducts = products
        .map((p) => ({
          product: p,
          relevance: calculateRelevance(p.name, searchQuery),
        }))
        .filter((item) => (temperature < 0.4 ? item.relevance > 0 : true))
        .sort((a, b) => b.relevance - a.relevance)
        .map((item) => item.product);

      const sliced =
        temperature < 0.7
          ? relevantProducts.filter(() => Math.random() < threshold || temperature < 0.4)
          : relevantProducts;

      statusEl.textContent = `Capturados ${data.total_scraped} URLs. Salvos ${data.total_saved} preços. ${sliced.length} relevantes para "${searchQuery}".`;
      products = sliced;
    } else {
      statusEl.textContent = `Capturados ${data.total_scraped} URLs. Salvos ${data.total_saved} preços.`;
    }

    lastResults = products;
    applyResultFilters();

    lastRawItems = data.raw_items || [];
    applyRawSort();
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
if (rawSortEl) {
  rawSortEl.addEventListener("change", applyRawSort);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const urls = document
    .getElementById("urls")
    .value.split("\n")
    .map((url) => url.trim())
    .filter(Boolean);
  
  const searchQuery = document.getElementById("search-query")?.value.trim() || null;

  const maxPages = Number(document.getElementById("multi-pages").value);
  const maxUrls = Number(document.getElementById("multi-limit").value);
  const temperature = Number(document.getElementById("multi-temperature").value);
  const maxConcurrency = Number(document.getElementById("concurrency").value);

  await runScrape(urls.length ? urls : defaultStoreUrls, searchQuery, {
    maxPages,
    maxUrls,
    temperature,
    maxConcurrency,
  });
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
      await runScrape(urls, searchTerm || null, {
        maxPages,
        maxUrls,
        temperature,
        maxConcurrency: Number(document.getElementById("concurrency").value),
      });
    } catch (error) {
      hideLoading();
      searchStatusEl.textContent = error.message;
    } finally {
      searchForm.querySelector("button").disabled = false;
    }
  });
}
