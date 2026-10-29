import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  ShieldCheck,
  Search,
  Wallet,
  Package,
  Radar,
  GitCompare,
  ClipboardCheck,
  ScanEye,
  MessageCircle,
  FileText,
  Settings,
  LayoutDashboard,
  ChevronRight,
  AlertTriangle,
  Menu,
  ExternalLink,
  Moon,
  Sun,
} from "lucide-react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import "./style.css";
import { Lang, t, Key, D, statusKey, trustKey, LOGO_SRC, fmtMoney, fmtNumber, fmtDate } from "./i18n";
import { tx, txl, unitLabel } from "./backendText";
import { Pill, Num, Amount, Empty, LangSwitch, Skeleton } from "./components/ui";
import { Login } from "./components/Login";
import { Overview } from "./components/Overview";
import { Copilot } from "./components/Copilot";
import { normalizeApiPath } from "./apiPath";
import { authFetch, setCsrf } from "./authSession";
import { DecisionAI } from "./components/DecisionAI";
import { ExecutiveStory } from "./components/ExecutiveStory";
import { SalesVisuals } from "./components/SalesVisuals";
type RecordAny = Record<string, any>;

const nav = [
  {
    title: "g_overview" as Key,
    items: [
      { id: "overview", key: "n_overview" as Key, Icon: LayoutDashboard },
      { id: "sales", key: "n_sales" as Key, Icon: Activity },
      { id: "briefing", key: "n_briefing" as Key, Icon: FileText },
    ],
  },
  {
    title: "g_analytics" as Key,
    items: [
      { id: "change", key: "n_change" as Key, Icon: GitCompare },
      { id: "money", key: "n_money" as Key, Icon: Wallet },
      { id: "sku", key: "n_sku" as Key, Icon: Package },
    ],
  },
  {
    title: "g_smart" as Key,
    items: [
      { id: "anomaly", key: "n_anomaly" as Key, Icon: Radar },
      { id: "risk", key: "n_risk" as Key, Icon: AlertTriangle },
      { id: "ai", key: "n_ai" as Key, Icon: MessageCircle },
      { id: "ml-workspace", key: "n_ai" as Key, Icon: Radar },
    ],
  },
  {
    title: "g_decisions" as Key,
    items: [
      { id: "cases", key: "n_cases" as Key, Icon: Search },
      { id: "recommend", key: "n_recommend" as Key, Icon: ClipboardCheck },
      { id: "decision", key: "n_decision" as Key, Icon: ClipboardCheck },
    ],
  },
  {
    title: "g_reports" as Key,
    items: [
      { id: "reports", key: "n_reports" as Key, Icon: FileText },
      { id: "passport", key: "n_passport" as Key, Icon: ShieldCheck },
      { id: "trust", key: "n_trust" as Key, Icon: ShieldCheck },
    ],
  },
  {
    title: "g_system" as Key,
    items: [
      { id: "graph", key: "n_graph" as Key, Icon: Package },
      { id: "health", key: "n_health" as Key, Icon: ShieldCheck },
      { id: "settings", key: "n_settings" as Key, Icon: Settings },
    ],
  },
];
async function api(path: string, init?: RequestInit) {
  const headers = new Headers(init?.headers);
  const r = await authFetch(normalizeApiPath(path), { ...init, headers });
  if (r.status === 401) {
    window.dispatchEvent(new Event("nexus-unauth"));
    throw Error("unauthorized");
  }
  if (!r.ok) throw Error((await r.text()).slice(0, 200));
  return r.json();
}
async function downloadFile(path: string, filename: string) {
  // Authenticated download: token goes in the Authorization header, never in the URL
  // (production mode rejects query tokens; URLs leak into history and proxy logs).
  const headers = new Headers();
  const r = await authFetch(normalizeApiPath(path), { headers });
  if (r.status === 401) {
    window.dispatchEvent(new Event("nexus-unauth"));
    throw Error("unauthorized");
  }
  if (!r.ok) throw Error("download failed (" + r.status + ")");
  const url = URL.createObjectURL(await r.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}
function App({
  lang,
  setLang,
  theme,
  setTheme,
  authOn,
  isAdmin,
  onSignOut,
}: {
  lang: Lang;
  setLang: (l: Lang) => void;
  theme: "dark" | "light";
  setTheme: (theme: "dark" | "light") => void;
  authOn: boolean;
  isAdmin: boolean;
  onSignOut: () => void;
}) {
  // Truthful data indicator: driven by /api/health (open endpoint), never hardcoded.
  const [dataConnected, setDataConnected] = useState<boolean | null>(null);
  useEffect(() => {
    let alive = true;
    fetch(normalizeApiPath("/api/health"))
      .then((r) => (r.ok ? r.json() : null))
      .then((h) => { if (alive) setDataConnected(h ? Boolean(h.ingested) : null); })
      .catch(() => { if (alive) setDataConnected(null); });
    return () => { alive = false; };
  }, []);
  const [sales, setSales] = useState<RecordAny | null>(null),
    [salesFilters, setSalesFilters] = useState<RecordAny | null>(null),
    [monthStart, setMonthStart] = useState(""),
    [monthEnd, setMonthEnd] = useState(""),
    [salesBranch, setSalesBranch] = useState(""),
    [salesChannel, setSalesChannel] = useState(""),
    [salesError, setSalesError] = useState(""),
    [page, setPage] = useState("overview"),
    [overview, setOverview] = useState<RecordAny | null>(null),
    [datasets, setDatasets] = useState<RecordAny[]>([]),
    [cases, setCases] = useState<RecordAny[]>([]),
    [selected, setSelected] = useState<string | null>(null),
    [detail, setDetail] = useState<RecordAny | null>(null),
    [skus, setSkus] = useState<RecordAny[]>([]),
    [branches, setBranches] = useState<RecordAny[]>([]),
    [query, setQuery] = useState(""),
    [searchText, setSearchText] = useState(""),
    [status, setStatus] = useState("investigating"),
    [reason, setReason] = useState(""),
    [decision, setDecision] = useState(""),
    [owner, setOwner] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [menu, setMenu] = useState(false),
    [analystQuestion, setAnalystQuestion] = useState(""),
    [analystAnswer, setAnalystAnswer] = useState<RecordAny | null>(null),
    [analystBusy, setAnalystBusy] = useState(false),
    [imageFile, setImageFile] = useState<File | null>(null),
    [imageResult, setImageResult] = useState<RecordAny | null>(null);
  const [recommendations, setRecommendations] = useState<RecordAny | null>(null),
    [contextAnswer, setContextAnswer] = useState<RecordAny | null>(null),
    [contextBusy, setContextBusy] = useState(false),
    [contextOrigin, setContextOrigin] = useState("overview"),
    [contextCase, setContextCase] = useState<string | null>(null);
  const [readiness, setReadiness] = useState<RecordAny | null>(null),
    [storyStep, setStoryStep] = useState(0);
  const [story, setStory] = useState<RecordAny | null>(null),
    [storyLoading, setStoryLoading] = useState(false),
    [briefing, setBriefing] = useState<RecordAny | null>(null),
    [chartStory, setChartStory] = useState<RecordAny | null>(null),
    [storyMode, setStoryMode] = useState(false);
  const [anomalyData, setAnomalyData] = useState<RecordAny | null>(null),
    [passData, setPassData] = useState<RecordAny | null>(null),
    [graphSku, setGraphSku] = useState(""),
    [graphData, setGraphData] = useState<RecordAny | null>(null),
    [xray, setXray] = useState<RecordAny | null>(null);
  const [riskIntelligence, setRiskIntelligence] = useState<RecordAny | null>(null),
    [comparison, setComparison] = useState<RecordAny | null>(null),
    [availableMonths, setAvailableMonths] = useState<string[]>([]),
    [currentMonth, setCurrentMonth] = useState(""),
    [previousMonth, setPreviousMonth] = useState(""),
    [skuDetail, setSkuDetail] = useState<RecordAny | null>(null);
  useEffect(() => {
    if (page === "recommend" || page === "overview")
      api("/client/recommendations?lang=" + lang)
        .then(setRecommendations)
        .catch(() => setRecommendations(null));
  }, [page, lang]);
  useEffect(() => {
    if (page === "health")
      api("/product/readiness")
        .then(setReadiness)
        .catch(() => setReadiness(null));
  }, [page]);
  useEffect(() => {
    if (page === "briefing" || page === "overview")
      api("/story/briefing?lang=" + lang)
        .then(setBriefing)
        .catch(() => setBriefing(null));
  }, [page, lang]);
  const askContext = async () => {
    setContextBusy(true);
    try {
      setContextAnswer(
        await api("/client/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question: analystQuestion || "Explain the current business context",
            page: contextOrigin,
            case_id: contextCase || undefined,
            lang,
          }),
        }),
      );
      setPage("ai");
    } catch (e) {
      setError(String(e));
    } finally {
      setContextBusy(false);
    }
  };
  const openMetric = async (id: string) => {
    setStoryLoading(true);
    setStory(null);
    try {
      setStory(await api("/story/metrics/" + encodeURIComponent(id) + "?lang=" + lang));
    } catch (e) {
      setError(String(e));
    } finally {
      setStoryLoading(false);
    }
  };
  const explainChart = async () => {
    try {
      setChartStory(await api("/story/chart/daily-sales?lang=" + lang));
    } catch (e) {
      setError(String(e));
    }
  };
  const refresh = async () => {
    try {
      const [o, d, c, s, b] = await Promise.all([
        api("/overview"),
        api("/datasets"),
        api("/cases"),
        api("/skus?limit=40"),
        api("/branches"),
      ]);
      setOverview(o);
      setDatasets(d);
      setCases(c);
      setSkus(s);
      setBranches(b);
      setError("");
    } catch (e) {
      setError(String(e));
    }
  };
  useEffect(() => {
    refresh();
  }, []);
  useEffect(() => {
    if (selected)
      api("/cases/" + selected)
        .then(setDetail)
        .catch((e) => setError(String(e)));
  }, [selected]);
  useEffect(() => {
    api("/skus?limit=40&q=" + encodeURIComponent(query))
      .then(setSkus)
      .catch(() => {});
  }, [query]);
  useEffect(() => {
    if (page !== "sales") return;
    api("/sales/filters")
      .then(setSalesFilters)
      .catch((e) => setSalesError(String(e)));
  }, [page]);
  useEffect(() => {
    if (page !== "sales") return;
    setSalesError("");
    let query = new URLSearchParams();
    if (monthStart) query.set("start", monthStart);
    if (monthEnd) query.set("end", monthEnd);
    if (salesBranch) query.set("branch", salesBranch);
    if (salesChannel) query.set("channel", salesChannel);
    api("/sales/intelligence?" + query)
      .then(setSales)
      .catch((e) => setSalesError(String(e)));
  }, [page, monthStart, monthEnd, salesBranch, salesChannel]);
  useEffect(() => {
    if (page === "risk")
      api("/intelligence/risk")
        .then(setRiskIntelligence)
        .catch((e) => setError(String(e)));
  }, [page]);
  useEffect(() => {
    if (page === "change")
      api("/intelligence/periods")
        .then((x) => {
          setAvailableMonths(x.months);
          setCurrentMonth((v: string) => v || x.months[x.months.length - 1] || "");
          setPreviousMonth((v: string) => v || x.months[x.months.length - 2] || "");
        })
        .catch((e) => setError(String(e)));
  }, [page]);
  useEffect(() => {
    if (page === "change" && currentMonth && previousMonth)
      api("/intelligence/compare?current=" + currentMonth + "&previous=" + previousMonth)
        .then(setComparison)
        .catch((e) => setError(String(e)));
  }, [page, currentMonth, previousMonth]);
  useEffect(() => {
    if (page === "anomaly")
      api("/transform/anomalies")
        .then(setAnomalyData)
        .catch((e) => setError(String(e)));
  }, [page]);
  useEffect(() => {
    if (page === "passport")
      api("/transform/passports")
        .then(setPassData)
        .catch((e) => setError(String(e)));
  }, [page]);
  useEffect(() => {
    if (page === "change" && currentMonth && previousMonth)
      api("/transform/revenue-xray?current=" + currentMonth + "&previous=" + previousMonth)
        .then(setXray)
        .catch((e) => setError(String(e)));
  }, [page, currentMonth, previousMonth]);
  const openSku = (id: string) => {
    api("/intelligence/sku/" + encodeURIComponent(id))
      .then(setSkuDetail)
      .catch((e) => setError(String(e)));
  };
  const metric = (key: string) => overview?.metrics?.find((x: RecordAny) => x.key === key),
    fmt = (n: number, unit = "") =>
      n == null ? t(lang, "na") : unit === "EGP" ? fmtMoney(lang, n, "EGP", false) : fmtNumber(lang, n) + (unitLabel(lang, unit) ? " " + unitLabel(lang, unit) : "");
  const save = async (kind: "status" | "decision") => {
    if (!selected) return;
    setBusy(true);
    setError("");
    try {
      const payload =
        kind === "status" ? { status, reason, actor: "local-analyst" } : { action: decision, owner, reason, status: "proposed" };
      setDetail(
        await api("/cases/" + selected + (kind === "status" ? "" : "/decisions"), {
          method: kind === "status" ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }),
      );
      setReason("");
      setDecision("");
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };
  const unsupported = (heading: string) => (
    <section className="card empty">
      <h2>{heading}</h2>
      <p>
        Not configured or validated. No generated predictions or placeholder answers are presented. This feature requires externally
        acquired datasets, trained and evaluated models, or grounded LLM integration.
      </p>
      <a href="/api/cv/status" target="_blank">
        Inspect availability
      </a>
    </section>
  );
  const mlabel = (k: string) =>
    ("trust_" + k) in D ? t(lang, ("trust_" + k) as Key) : ("m_" + k) in D ? t(lang, ("m_" + k) as Key) : k.replace(/_/g, " ");
  const CH: Record<string, Key> = { "E-commerce": "ch_ecommerce", "Retail POS": "ch_retail_pos", "Wholesale / reseller": "ch_wholesale" };
  const chan = (c: string) => (CH[c] ? t(lang, CH[c]) : c);
  const dirLabel = (d: string) => ("dir_" + d in D ? t(lang, ("dir_" + d) as Key) : d);
  const recTitle = (ti: string) => {
    const m = String(ti).match(/^(?:Verify metric: |راجع تعريف المؤشر: )(.+)$/);
    return m ? t(lang, "ac_verify") + ": " + mlabel(m[1]) : tx(lang, String(ti).replace(/^(Review: |مراجعة: )/, ""));
  };
  const title =
    page === "ml-workspace"
      ? lang === "ar" ? "مركز ML والقرارات" : "ML & Decision Center"
      : t(lang, ("n_" + page) as Key);
  const D2: Record<string, Key> = Object.fromEntries(nav.flatMap((g) => g.items.map((i) => [i.id, i.key])));
  return (
    <div className="app">
      <a href="#content" className="skip" style={{ position: "absolute", insetInlineStart: -9999 }}>
        {t(lang, "skip")}
      </a>
      <aside className={"sidebar " + (menu ? "expanded" : "")} aria-label={t(lang, "app_name")}>
        <div className="brand">
          <img src={LOGO_SRC} alt="Cottonil" width={345} height={50} />
          <small>{t(lang, "app_tag")}</small>
        </div>
        <nav>
          {nav
            .map((g) => ({ ...g, items: g.items.filter((i) => i.id !== "health" || isAdmin) }))
            .map((g) => (
              <div className="navgroup" key={g.title}>
                <div className="navhint">{t(lang, g.title)}</div>
                {g.items.map(({ id, key, Icon }) => (
                  <button
                    key={id}
                    aria-current={page === id ? "page" : undefined}
                    className={page === id ? "active" : ""}
                    onClick={() => {
                      setPage(id);
                      if (id !== "ai") {
                        setContextOrigin(id);
                        setContextCase(null);
                      }
                      setMenu(false);
                      setSelected(null);
                    }}
                  >
                    <Icon size={18} />
                    <span>{id === "ml-workspace" ? (lang === "ar" ? "مركز ML والقرارات" : "ML & Decision Center") : t(lang, key)}</span>
                    {page === id && <ChevronRight size={14} className="chev" />}
                  </button>
                ))}
              </div>
            ))}
        </nav>
        <div className="sidebottom">
          <span className={"pulse" + (dataConnected ? "" : " off")} aria-hidden="true" />
          <span role="status">
            {dataConnected === null ? t(lang, "data_status_unknown") : dataConnected ? t(lang, "data_source_local") : t(lang, "data_not_connected")}
          </span>
        </div>
      </aside>
      <main id="content">
        <header className="top">
          <button className="mobileMenu" onClick={() => setMenu(!menu)} aria-label={t(lang, "open_menu")}>
            <Menu size={20} />
          </button>
          <div className="titles">
            <h1>{title}</h1>
          </div>
          <div className="headright">
            <LangSwitch lang={lang} setLang={setLang} />
            <button className="ghost themeToggle" aria-label={lang === "ar" ? (theme === "dark" ? "تفعيل الوضع الفاتح" : "تفعيل الوضع الداكن") : (theme === "dark" ? "Switch to light mode" : "Switch to dark mode")} title={theme === "dark" ? "Light mode" : "Dark mode"} aria-pressed={theme === "dark"} onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>{theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}</button>
            {authOn && (
              <button className="ghost" onClick={onSignOut}>
                {t(lang, "lg_signout")}
              </button>
            )}
          </div>
        </header>
        {error && (
          <div role="alert" className="error">
            {t(lang, "err_generic")}
          </div>
        )}
        {storyLoading && (
          <div className="notice" role="status">
            {t(lang, "loading")}
          </div>
        )}
        {story && (
          <div className="storyBackdrop" onClick={() => setStory(null)}>
            <section className="storyDrawer" role="dialog" aria-modal="true" aria-label={story.title} onClick={(e) => e.stopPropagation()}>
              <button className="link drawerClose" onClick={() => setStory(null)}>
                {t(lang, "close")}
              </button>
              <span className="eyebrow">{t(lang, "explain_number")}</span>
              <h2>{story.title}</h2>
              <strong className="storyValue">
                <Amount lang={lang} value={story.value} unit={story.unit} />
              </strong>
              <Pill lang={lang} kind="trust" value={story.trust} />
              {(["what", "meaning", "assessment", "change", "next_action", "reliability"] as const).map((k) => (
                <div className="storySection" key={k}>
                  <h4>{t(lang, ("sd_" + k) as Key)}</h4>
                  <p>{story[k]}</p>
                </div>
              ))}
              <p className="muted">
                {t(lang, "sources")}: {story.sources?.join(", ")}
              </p>
              <button
                className="action"
                onClick={() => {
                  setStory(null);
                  setPage("passport");
                }}
              >
                {t(lang, "n_passport")}
              </button>
            </section>
          </div>
        )}
        {page === "overview" && (
          <Overview
            lang={lang}
            overview={overview}
            recs={recommendations}
            chartStory={chartStory}
            openCases={cases.filter((c) => c.status !== "resolved" && c.status !== "dismissed").length}
            onExplain={openMetric}
            onExplainChart={explainChart}
            onCloseChart={() => setChartStory(null)}
            go={(p, id) => {
              setPage(p);
              if (id) setSelected(id);
            }}
          />
        )}
        {page === "recommend" && (
          <section className="card">
            <h2>{t(lang, "ac_title")}</h2>
            <p className="muted">{t(lang, "ac_note")}</p>
            {recommendations?.recommendations?.length ? (
              recommendations.recommendations.map((r: RecordAny) => (
                <article className="recommendCard" key={r.id}>
                  <div className="sectionhead">
                    <h3>{recTitle(r.title)}</h3>
                    <Pill lang={lang} kind="sev" value={r.priority} />
                  </div>
                  <p>{tx(lang, r.context)}</p>
                  <p>
                    <strong>{t(lang, "ac_action")}: </strong>
                    {r.action}
                  </p>
                  <p className="muted">
                    {t(lang, "evidence")}: {r.evidence?.map((k: string) => mlabel(k)).join(" · ") || "—"}
                  </p>
                  {r.case_id ? (
                    <button
                      className="action"
                      onClick={() => {
                        setSelected(r.case_id);
                        setPage("cases");
                      }}
                    >
                      {t(lang, "open_investigation")}
                    </button>
                  ) : (
                    <button className="action" onClick={() => setPage("passport")}>
                      {t(lang, "review_reliability")}
                    </button>
                  )}
                </article>
              ))
            ) : (
              <Empty title={t(lang, "ac_none")} />
            )}
          </section>
        )}
        {page === "health" && (
          <section className="card healthPanel">
            <h2>{t(lang, "hl_title")}</h2>
            <p className="muted">{t(lang, "hl_note")}</p>
            {!readiness ? (
              <p role="status">{t(lang, "hl_unavail")}</p>
            ) : (
              <>
                <div className="kpis">
                  <div className="kpi">
                    <small>{t(lang, "hl_datasets")}</small>
                    <strong>
                      <Num>{fmtNumber(lang, readiness.data.datasets)}</Num>
                    </strong>
                  </div>
                  <div className="kpi">
                    <small>{t(lang, "hl_metrics")}</small>
                    <strong>
                      <Num>{fmtNumber(lang, readiness.data.metrics)}</Num>
                    </strong>
                  </div>
                  <div className="kpi">
                    <small>{t(lang, "ov_open_cases")}</small>
                    <strong>
                      <Num>{fmtNumber(lang, readiness.investigations_pending)}</Num>
                    </strong>
                  </div>
                </div>
                <div className="healthRows">
                  {(
                    [
                      ["hl_csv", readiness.data.source_files_present],
                      ["hl_mart", readiness.capabilities.sales_mart],
                      ["hl_write", readiness.capabilities.write_access_configured],
                      ["hl_llm", readiness.capabilities.llm_provider_configured],
                    ] as [Key, boolean][]
                  ).map(([k, ok]) => (
                    <div className="healthRow" key={k}>
                      <span>{t(lang, k)}</span>
                      <span className={"pill " + (ok ? "verified" : "warning")}>{t(lang, ok ? "hl_ok" : "hl_no")}</span>
                    </div>
                  ))}
                </div>
                <p className="muted">
                  {t(lang, "hl_last")}: <Num>{readiness.data.last_ingested_at ? fmtDate(lang, readiness.data.last_ingested_at) : "—"}</Num>
                </p>
              </>
            )}
          </section>
        )}
        {page === "briefing" && (
          <section className="card executiveBrief">
            <h2>{briefing?.headline || t(lang, "br_empty")}</h2>
            <p>{briefing?.key_takeaway}</p>
            <div className="kpis">
              {briefing?.metrics?.map((m: RecordAny) => (
                <div className="kpi" key={m.id}>
                  <small>{m.title}</small>
                  <strong>
                    <Amount lang={lang} value={m.value} unit={m.unit} />
                  </strong>
                  <div className="kpifoot">
                    <Pill lang={lang} kind="trust" value={m.trust} />
                    <button className="explainBtn" onClick={() => openMetric(m.id)}>
                      {t(lang, "explain_number")}
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <h3>{t(lang, "br_attention")}</h3>
            {briefing?.open_investigations?.map((c: RecordAny) => (
              <button
                key={c.id}
                className="caseRow"
                onClick={() => {
                  setSelected(c.id);
                  setPage("cases");
                }}
              >
                <div>
                  <b>{tx(lang, c.title)}</b>
                  <small>
                    <Num code>{c.id}</Num>
                  </small>
                </div>
                <Pill lang={lang} kind="status" value={c.status} />
              </button>
            ))}
            <h3>{t(lang, "br_next")}</h3>
            {briefing?.next_actions?.map((a: string) => (
              <p key={a}>{a}</p>
            ))}
            <p className="muted">{txl(lang, briefing?.limitations, " · ")}</p>
            <button className="primary" onClick={() => setStoryMode(true)}>
              {t(lang, "story_start")}
            </button>
            {storyMode && (
              <ExecutiveStory lang={lang} briefing={briefing} daily={overview?.daily || []} onClose={() => setStoryMode(false)} />
            )}
          </section>
        )}
        {page === "ml-workspace" && <DecisionAI lang={lang} />}
        {page === "sales" && (
          <div className="salesDashboard">
            <div className="card">
              <div className="sectionhead">
                <h3>{t(lang, "p_sales_title")}</h3>
                <button
                  onClick={() => {
                    setMonthStart("");
                    setMonthEnd("");
                    setSalesBranch("");
                    setSalesChannel("");
                  }}
                >
                  {t(lang, "p_clear")}
                </button>
              </div>
              <div className="filters">
                <label>
                  {t(lang, "p_from_month")}
                  <select value={monthStart} onChange={(e) => setMonthStart(e.target.value)}>
                    <option value="">{t(lang, "all")}</option>
                    {salesFilters?.months?.map((m: string) => (
                      <option key={m}>{m}</option>
                    ))}
                  </select>
                </label>
                <label>
                  {t(lang, "p_to_month")}
                  <select value={monthEnd} onChange={(e) => setMonthEnd(e.target.value)}>
                    <option value="">{t(lang, "all")}</option>
                    {salesFilters?.months?.map((m: string) => (
                      <option key={m}>{m}</option>
                    ))}
                  </select>
                </label>
                <label>
                  {t(lang, "p_branch")}
                  <select value={salesBranch} onChange={(e) => setSalesBranch(e.target.value)}>
                    <option value="">{t(lang, "p_all_branches")}</option>
                    {salesFilters?.branches?.map((b: string) => (
                      <option key={b}>{b}</option>
                    ))}
                  </select>
                </label>
                <label>
                  {t(lang, "p_channel")}
                  <select value={salesChannel} onChange={(e) => setSalesChannel(e.target.value)}>
                    <option value="">{t(lang, "p_all_channels")}</option>
                    {salesFilters?.channels?.map((c: string) => (
                      <option key={c} value={c}>
                        {chan(c)}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              {salesError && <p role="alert">{salesError}</p>}
              <p className="muted">{tx(lang, sales?.caveat)}</p>
            </div>
            <div className="kpis">
              {[
                ["net", t(lang, "m_net_sales")],
                ["gross", t(lang, "p_gross")],
                ["discount", t(lang, "p_discounts")],
                ["units", t(lang, "m_sold_units")],
              ].map(([k, lbl]) => (
                <div className="kpi" key={k}>
                  <small>{lbl}</small>
                  <strong>{!sales ? <Skeleton h={30} w="70%" /> : sales.totals?.[k] == null ? "—" : fmt(sales.totals[k], k === "units" ? "" : "EGP")}</strong>
                  <span className="pill warning">{t(lang, "trust_source_derived")}</span>
                </div>
              ))}
            </div>
            <div className="twocol">
              <section className="card">
                <h3>{t(lang, "p_by_channel")}</h3>
                {sales?.channels?.map((c: RecordAny) => (
                  <div className="barrow" key={c.label}>
                    <span>{chan(c.label)}</span>
                    <div>
                      <i
                        style={{
                          width: ((c.revenue || 0) / Math.max(1, ...(sales?.channels || []).map((x: RecordAny) => x.revenue))) * 100 + "%",
                        }}
                      />
                    </div>
                    <b>{fmt(c.revenue, "EGP")}</b>
                  </div>
                ))}
              </section>
            </div>
            <SalesVisuals lang={lang} monthly={sales?.monthly} branches={sales?.branches} products={sales?.products} />
            <div className="twocol">
              <section className="card">
                <h3>{t(lang, "p_top_branches")}</h3>
                <div className="tablewrap">
                  <table>
                    <thead>
                      <tr>
                        <th>{t(lang, "p_branch")}</th>
                        <th>{t(lang, "revenue")}</th>
                        <th>{t(lang, "p_units")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sales?.branches?.map((b: RecordAny) => (
                        <tr key={b.label} onClick={() => setSalesBranch(b.label)} style={{ cursor: "pointer" }}>
                          <td>
                            <b>{b.label}</b>
                          </td>
                          <td>{fmt(b.revenue, "EGP")}</td>
                          <td>{fmt(b.units)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
              <section className="card">
                <h3>{t(lang, "p_top_products")}</h3>
                <div className="tablewrap">
                  <table>
                    <thead>
                      <tr>
                        <th>{t(lang, "p_product")}</th>
                        <th>{t(lang, "m_net_sales")}</th>
                        <th>{t(lang, "p_units")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sales?.products?.map((p: RecordAny) => (
                        <tr key={p.label}>
                          <td>{p.label}</td>
                          <td>{fmt(p.revenue, "EGP")}</td>
                          <td>{fmt(p.units)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          </div>
        )}
        {page === "trust" && (
          <>
            <div className="notice">
              <ShieldCheck size={20} />
              {t(lang, "p_trust_note")}
            </div>
            <div className="card">
              <div className="sectionhead">
                <h3>{t(lang, "p_ledger")}</h3>
                <span>
                  {overview?.metrics?.length || 0} {t(lang, "p_defined_metrics")}
                </span>
              </div>
              <div className="tablewrap">
                <table>
                  <thead>
                    <tr>
                      <th>{t(lang, "p_metric")}</th>
                      <th>{t(lang, "p_calc_value")}</th>
                      <th>{t(lang, "p_trust")}</th>
                      <th>{t(lang, "p_def_source")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overview?.metrics?.map((m: RecordAny) => (
                      <tr key={m.key}>
                        <td>
                          <b>{mlabel(m.key)}</b>
                        </td>
                        <td>{fmt(m.value, m.unit)}</td>
                        <td>
                          <Pill lang={lang} kind="trust" value={m.trust} />
                        </td>
                        <td>
                          {tx(lang, m.definition)}
                          <small>{m.source}</small>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="card">
              <div className="sectionhead">
                <h3>{t(lang, "p_datasets")}</h3>
                <span>
                  {datasets.length} {t(lang, "p_source_tables")}
                </span>
              </div>
              <div className="tablewrap">
                <table>
                  <thead>
                    <tr>
                      <th>{t(lang, "p_table")}</th>
                      <th>{t(lang, "p_records")}</th>
                      <th>{t(lang, "p_missing")}</th>
                      <th>{t(lang, "evidence")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {datasets.map((d) => (
                      <tr key={d.name}>
                        <td>{d.name}</td>
                        <td>{fmt(d.rows)}</td>
                        <td>{Object.values(d.nulls as Record<string, number>).reduce((a, b) => a + b, 0)}</td>
                        <td>
                          <a href={"/api/evidence/" + d.name} target="_blank">
                            {t(lang, "p_source_sample")}
                            <ExternalLink size={12} />
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
        {page === "cases" && (
          <div className="twocol casegrid">
            <section className="card">
              <h3>{t(lang, "p_queue")}</h3>
              {cases.map((c) => (
                <button
                  key={c.id}
                  className={"caseRow " + (selected === c.id ? "chosen" : "")}
                  onClick={() => {
                    setSelected(c.id);
                    setContextOrigin("cases");
                    setContextCase(c.id);
                  }}
                >
                  <AlertTriangle size={19} />
                  <div>
                    <b>{tx(lang, c.title)}</b>
                    <small>
                      <Num code>{c.id}</Num> · <Pill lang={lang} kind="status" value={c.status} />
                    </small>
                  </div>
                  <ChevronRight size={16} />
                </button>
              ))}
            </section>
            <section className="card">
              <h3>{t(lang, "p_dossier")}</h3>
              {detail ? (
                <>
                  <div className="eyebrow">
                    <Num code>{detail.case.id}</Num> · <Pill lang={lang} kind="sev" value={detail.case.severity} />
                  </div>
                  <h2>{tx(lang, detail.case.title)}</h2>
                  <Pill lang={lang} kind="status" value={detail.case.status} />
                  <h4>{t(lang, "p_observations")}</h4>
                  {detail.case.observations.map((s0: string) => (
                    <p key={s0}>{tx(lang, s0)}</p>
                  ))}
                  <h4>{t(lang, "p_hypotheses")}</h4>
                  <ul>
                    {detail.case.hypotheses.map((s0: string) => (
                      <li key={s0}>{tx(lang, s0)}</li>
                    ))}
                  </ul>
                  <h4>{t(lang, "p_evidence_metrics")}</h4>
                  {detail.case.evidence.map((key: string) => (
                    <div key={key} className="evidence">
                      <span>{mlabel(key)}</span>
                      <b>{fmt(metric(key)?.value, metric(key)?.unit)}</b>
                    </div>
                  ))}
                  <h4>{t(lang, "p_record_status")}</h4>
                  <div className="form">
                    <select value={status} onChange={(e) => setStatus(e.target.value)}>
                      {["open", "investigating", "action_required", "resolved", "dismissed"].map((s) => (
                        <option key={s} value={s}>
                          {statusKey(s) ? t(lang, statusKey(s) as Key) : s}
                        </option>
                      ))}
                    </select>
                    <textarea placeholder={t(lang, "reason")} value={reason} onChange={(e) => setReason(e.target.value)} />
                    <button disabled={busy || reason.length < 4} onClick={() => save("status")}>
                      {t(lang, "p_save_status")}
                    </button>
                    <input placeholder={t(lang, "p_proposed_action")} value={decision} onChange={(e) => setDecision(e.target.value)} />
                    <input placeholder={t(lang, "p_owner")} value={owner} onChange={(e) => setOwner(e.target.value)} />
                    <button disabled={busy || !decision || !owner || reason.length < 4} onClick={() => save("decision")}>
                      {t(lang, "p_record_decision")}
                    </button>
                  </div>
                  <h4>{t(lang, "p_audit")}</h4>
                  {detail.events.length ? (
                    detail.events.map((e: RecordAny) => (
                      <p key={e.id} className="timeline">
                        <b>{e.kind}</b> {e.detail}
                        <small>{e.created_at}</small>
                      </p>
                    ))
                  ) : (
                    <p>{t(lang, "p_no_edits")}</p>
                  )}
                </>
              ) : (
                <div className="empty">{t(lang, "p_select_case")}</div>
              )}
            </section>
          </div>
        )}
        {page === "money" && (
          <>
            <div className="kpis">
              {["net_sales", "margin", "purchase_line_cost", "refunds"].map((key) => (
                <div className="kpi" key={key}>
                  <small>{mlabel(key)}</small>
                  <strong>{fmt(metric(key)?.value, "EGP")}</strong>
                  <Pill lang={lang} kind="trust" value={metric(key)?.trust || "unavailable"} />
                </div>
              ))}
            </div>
            <div className="notice">
              <AlertTriangle size={18} />
              {t(lang, "p_cost_note")}
            </div>
            <div className="card">
              <h3>{t(lang, "p_branch_rev")}</h3>
              {branches.slice(0, 12).map((b) => (
                <div className="barrow" key={b.branch_id}>
                  <span>{b.branch_id}</span>
                  <div>
                    <i style={{ width: (b.revenue / (branches[0]?.revenue || 1)) * 100 + "%" }} />
                  </div>
                  <b>{fmt(b.revenue, "EGP")}</b>
                </div>
              ))}
            </div>
          </>
        )}
        {page === "sku" && (
          <>
            <div className="card">
              <div className="sectionhead">
                <h3>{t(lang, "p_sku_explorer")}</h3>
                <input
                  aria-label={t(lang, "p_search_aria")}
                  placeholder={t(lang, "p_search_sku")}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>
              <div className="tablewrap">
                <table>
                  <thead>
                    <tr>
                      <th>{t(lang, "p_sku")}</th>
                      <th>{t(lang, "p_sold_units")}</th>
                      <th>{t(lang, "m_net_sales")}</th>
                      <th>{t(lang, "p_margin")}</th>
                      <th>{t(lang, "p_purchase_units")}</th>
                      <th>{t(lang, "p_profile")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {skus.map((x) => (
                      <tr key={x.sku_id}>
                        <td>
                          <b>{x.sku_id}</b>
                        </td>
                        <td>{fmt(x.units)}</td>
                        <td>{fmt(x.revenue, "EGP")}</td>
                        <td>{fmt(x.margin, "EGP")}</td>
                        <td>{fmt(x.purchased_units)}</td>
                        <td>
                          <button className="link" onClick={() => openSku(x.sku_id)}>
                            {t(lang, "p_inspect")}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="muted">{t(lang, "p_sku_note")}</p>
            </div>
            {skuDetail && (
              <section className="card">
                <div className="sectionhead">
                  <h3>
                    {t(lang, "p_sku_dossier")} · <Num code>{skuDetail.sku.sku_id}</Num>
                  </h3>
                  <button onClick={() => setSkuDetail(null)} className="ghost">
                    {t(lang, "close")}
                  </button>
                </div>
                <div className="kpis">
                  {[
                    [t(lang, "revenue"), skuDetail.sku.revenue],
                    [t(lang, "m_sold_units"), skuDetail.sku.units],
                    [t(lang, "p_margin"), skuDetail.sku.margin],
                    [t(lang, "p_purchase_activity"), skuDetail.sku.purchased_units],
                  ].map(([label, val]) => (
                    <div className="kpi" key={String(label)}>
                      <small>{label}</small>
                      <strong>{fmt(val as number)}</strong>
                    </div>
                  ))}
                </div>
                <h4>{t(lang, "p_coverage")}</h4>
                {skuDetail.limitations.map((x: string) => (
                  <p className="muted" key={x}>
                    {tx(lang, x)}
                  </p>
                ))}
                <p className="muted">
                  {t(lang, "sources")}: {skuDetail.sources.join(" · ")}
                </p>
              </section>
            )}
          </>
        )}
        {page === "risk" && (
          <>
            <div className="kpis">
              {[
                [t(lang, "p_active_signals"), riskIntelligence?.summary?.total],
                [t(lang, "sev_critical"), riskIntelligence?.summary?.critical],
                [t(lang, "sev_high"), riskIntelligence?.summary?.high],
                [t(lang, "p_unresolved"), riskIntelligence?.summary?.unresolved],
              ].map(([label, n]) => (
                <div className="kpi" key={String(label)}>
                  <small>{label}</small>
                  <strong>{n ?? "—"}</strong>
                </div>
              ))}
            </div>
            <section className="card">
              <h3>{t(lang, "p_risk_title")}</h3>
              <p className="muted">{t(lang, "p_risk_note")}</p>
              {riskIntelligence?.signals?.map((c: RecordAny) => (
                <button
                  key={c.id}
                  className="caseRow"
                  onClick={() => {
                    setPage("cases");
                    setSelected(c.id);
                  }}
                >
                  <AlertTriangle size={18} />
                  <div>
                    <b>{tx(lang, c.title)}</b>
                    <small>
                      <Pill lang={lang} kind="status" value={c.status} /> · {c.metrics.map((m: RecordAny) => mlabel(m.key)).join("، ")}
                    </small>
                  </div>
                  <Pill lang={lang} kind="sev" value={c.severity} />
                </button>
              ))}
              <p className="muted">{txl(lang, riskIntelligence?.limitations, " ")}</p>
            </section>
          </>
        )}
        {page === "change" && (
          <>
            <section className="card">
              <div className="sectionhead">
                <h3>{t(lang, "p_compare_title")}</h3>
                <span>{t(lang, "p_monthly_mart")}</span>
              </div>
              <div className="compareFilters">
                <label>
                  {t(lang, "p_cur_month")}{" "}
                  <select value={currentMonth} onChange={(e) => setCurrentMonth(e.target.value)}>
                    {availableMonths.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  {t(lang, "p_cmp_month")}{" "}
                  <select value={previousMonth} onChange={(e) => setPreviousMonth(e.target.value)}>
                    {availableMonths.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              {comparison && (
                <>
                  <div className="kpis">
                    <div className="kpi">
                      <small>{t(lang, "p_cur_rev")}</small>
                      <strong>{fmt(comparison.current.revenue, "EGP")}</strong>
                    </div>
                    <div className="kpi">
                      <small>{t(lang, "p_prev_rev")}</small>
                      <strong>{fmt(comparison.previous.revenue, "EGP")}</strong>
                    </div>
                    <div className="kpi">
                      <small>{t(lang, "p_rev_change")}</small>
                      <strong>{fmt(comparison.delta, "EGP")}</strong>
                    </div>
                    <div className="kpi">
                      <small>{t(lang, "p_change_pct")}</small>
                      <strong>{comparison.change_pct === null ? t(lang, "na") : comparison.change_pct + "%"}</strong>
                    </div>
                  </div>
                  <p className="muted">{txl(lang, comparison.limitations, " ")}</p>
                </>
              )}
            </section>
            {comparison && (
              <div className="twocol">
                {[
                  [t(lang, "p_branches"), comparison.branches],
                  [t(lang, "p_products"), comparison.products],
                  [t(lang, "p_channels"), comparison.channels],
                ].map(([title, data]) => (
                  <section className="card" key={title as string}>
                    <h3>
                      {title as string} · {t(lang, "p_largest")}
                    </h3>
                    <div className="tablewrap">
                      <table>
                        <thead>
                          <tr>
                            <th>{t(lang, "p_id")}</th>
                            <th>{t(lang, "p_current")}</th>
                            <th>{t(lang, "p_previous")}</th>
                            <th>{t(lang, "p_delta")}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(data as RecordAny[]).map((x) => (
                            <tr key={x.label}>
                              <td>{chan(x.label)}</td>
                              <td>{fmt(x.current_revenue)}</td>
                              <td>{fmt(x.previous_revenue)}</td>
                              <td className={x.delta < 0 ? "negative" : "positive"}>{fmt(x.delta)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </section>
                ))}
              </div>
            )}
          </>
        )}
        {page === "anomaly" && (
          <>
            <div className="kpis">
              <div className="kpi">
                <small>{t(lang, "p_outliers")}</small>
                <strong>{anomalyData?.total_detected ?? "—"}</strong>
              </div>
              <div className="kpi">
                <small>{t(lang, "p_scanned")}</small>
                <strong>{anomalyData?.scanned_branch_months ?? "—"}</strong>
              </div>
              <div className="kpi">
                <small>{t(lang, "p_threshold")}</small>
                <strong>|Z| ≥ 3.5</strong>
              </div>
            </div>
            <section className="card">
              <h3>{t(lang, "p_anom_title")}</h3>
              <p className="muted">{t(lang, "p_anom_note")}</p>
              <div className="tablewrap">
                <table>
                  <thead>
                    <tr>
                      <th>{t(lang, "p_signal")}</th>
                      <th>{t(lang, "p_branch")}</th>
                      <th>{t(lang, "p_month")}</th>
                      <th>{t(lang, "p_observed")}</th>
                      <th>{t(lang, "p_reference")}</th>
                      <th>{t(lang, "p_robust_z")}</th>
                      <th>{t(lang, "p_investigation")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {anomalyData?.signals?.map((a: RecordAny) => (
                      <tr key={a.id}>
                        <td>
                          {dirLabel(a.direction)} <Pill lang={lang} kind="sev" value={a.severity} />
                        </td>
                        <td>{a.entity_id}</td>
                        <td>{a.period}</td>
                        <td>{fmt(a.actual, "EGP")}</td>
                        <td>{fmt(a.expected, "EGP")}</td>
                        <td>{a.deviation_score}</td>
                        <td>
                          {a.has_case ? (
                            <button
                              onClick={() => {
                                setSelected(a.case_id);
                                setPage("cases");
                              }}
                            >
                              {t(lang, "p_open_case")}
                            </button>
                          ) : (
                            <span className="muted">{t(lang, "p_review_req")}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="muted">{txl(lang, anomalyData?.limitations, " · ")}</p>
            </section>
          </>
        )}
        {page === "passport" && (
          <section className="card">
            <h3>{t(lang, "p_pass_title")}</h3>
            <p>{t(lang, "p_pass_desc")}</p>
            <div className="tablewrap">
              <table>
                <thead>
                  <tr>
                    <th>{t(lang, "p_metric")}</th>
                    <th>{t(lang, "p_value")}</th>
                    <th>{t(lang, "p_trust")}</th>
                    <th>{t(lang, "p_formula")}</th>
                    <th>{t(lang, "p_source")}</th>
                    <th>{t(lang, "p_investigations")}</th>
                  </tr>
                </thead>
                <tbody>
                  {passData?.passports?.map((p: RecordAny) => (
                    <tr key={p.id}>
                      <td>
                        <b>{mlabel(p.id)}</b>
                      </td>
                      <td>{fmt(p.value, p.unit)}</td>
                      <td>
                        <Pill lang={lang} kind="trust" value={p.trust} />
                      </td>
                      <td>{tx(lang, p.formula)}</td>
                      <td>{p.sources.join(" / ")}</td>
                      <td>
                        {p.related_cases.map((id: string) => (
                          <button
                            key={id}
                            className="link"
                            onClick={() => {
                              setPage("cases");
                              setSelected(id);
                            }}
                          >
                            {id}
                          </button>
                        ))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <h4>{t(lang, "p_trust_defs")}</h4>
            {Object.entries(passData?.trust_definitions || {}).map(([k, v]) => (
              <p key={k}>
                <Pill lang={lang} kind="trust" value={k} /> {tx(lang, String(v))}
              </p>
            ))}
          </section>
        )}
        {page === "graph" && (
          <section className="card">
            <h3>{t(lang, "p_graph_title")}</h3>
            <p className="muted">{t(lang, "p_graph_note")}</p>
            <div className="form">
              <input placeholder={t(lang, "p_enter_sku")} value={graphSku} onChange={(e) => setGraphSku(e.target.value)} />
              <button
                disabled={!graphSku}
                onClick={() =>
                  api("/transform/graph/sku/" + encodeURIComponent(graphSku))
                    .then(setGraphData)
                    .catch((e) => setError(String(e)))
                }
              >
                {t(lang, "p_explore")}
              </button>
            </div>
            {graphData && (
              <>
                <div className="twocol">
                  {graphData.nodes.map((n: RecordAny) => (
                    <div key={n.id} className="kpi">
                      <small>{n.type}</small>
                      <strong>{n.label}</strong>
                      {n.amount !== undefined && <p>{fmt(n.amount, "EGP")}</p>}
                    </div>
                  ))}
                </div>
                <p>{graphData.edges.map((e: RecordAny) => e.relation + " · " + t(lang, trustKey(e.trust))).join(" | ")}</p>
                <p className="muted">{txl(lang, graphData.limitations, " · ")}</p>
              </>
            )}
          </section>
        )}
        {page === "change" && xray && (
          <section className="card">
            <h3>{t(lang, "p_xray_title")}</h3>
            <div className="kpis">
              {Object.entries(xray.metrics).map(([key, m]: [string, any]) => (
                <div className="kpi" key={key}>
                  <small>
                    {mlabel(key)} {t(lang, "p_change_word")}
                  </small>
                  <strong>{fmt(m.delta)}</strong>
                  <span>{m.change_pct == null ? t(lang, "na") : m.change_pct + "%"}</span>
                </div>
              ))}
            </div>
            <p className="muted">
              {t(lang, "p_reconcile")}: {xray.branch_reconciles ? t(lang, "yes") : t(lang, "p_check_failed")} ·{" "}
              {txl(lang, xray.limitations, " · ")}
            </p>
          </section>
        )}
        {page === "decision" && (
          <div className="card">
            <h3>{t(lang, "p_decision_title")}</h3>
            <p>{t(lang, "p_decision_desc")}</p>
            {cases.map((c) => (
              <button
                className="caseRow"
                key={c.id}
                onClick={() => {
                  setPage("cases");
                  setSelected(c.id);
                }}
              >
                <ClipboardCheck size={18} />
                <div>
                  <b>{tx(lang, c.title)}</b>
                  <small>
                    <Num code>{c.id}</Num> · <Pill lang={lang} kind="status" value={c.status} />
                  </small>
                </div>
                <ChevronRight size={16} />
              </button>
            ))}
          </div>
        )}
        {page === "ai" && (
          <Copilot
            lang={lang}
            api={api}
            contextLabel={contextOrigin in D2 ? t(lang, D2[contextOrigin]) : contextOrigin}
            contextPage={contextOrigin}
            contextCase={contextCase}
            go={(p, id) => {
              setPage(p);
              if (id) setSelected(id);
            }}
          />
        )}
        {(page === "catalog" || page === "textile") && (
          <section className="card">
            <h3>{page === "catalog" ? "Catalog Detective: image color explorer" : "Textile Quality: image inspection"}</h3>
            <p className="muted">
              Real local image color analysis is available. Fabric defect classification and product recognition require trained/evaluated
              weights and remain unavailable; no invented predictions.
            </p>
            <div className="form">
              <input
                aria-label="Select image"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={(e) => {
                  setImageFile(e.target.files?.[0] || null);
                  setImageResult(null);
                }}
              />
              {imageFile && (
                <img
                  alt="Selected image preview"
                  src={URL.createObjectURL(imageFile)}
                  style={{ maxWidth: 300, maxHeight: 260, objectFit: "contain" }}
                />
              )}
              <button
                disabled={!imageFile}
                onClick={async () => {
                  if (!imageFile) return;
                  const body = new FormData();
                  body.append("file", imageFile);
                  try {
                    setImageResult(await api("/cv/color-analysis", { method: "POST", body }));
                  } catch (e) {
                    setError(String(e));
                  }
                }}
              >
                Analyze image colors
              </button>
            </div>
            {imageResult && (
              <div className="answer">
                <h3>{imageResult.dominant_color}</h3>
                <p>RGB: {imageResult.rgb?.join(", ")}</p>
                <p>{imageResult.method}</p>
                <p className="muted">{imageResult.limitation}</p>
              </div>
            )}
          </section>
        )}
        {page === "reports" && (
          <div className="card">
            <img src={LOGO_SRC} alt="Cottonil" width={172} height={25} style={{ marginBlockEnd: 16 }} />
            <h3>{t(lang, "rp_title")}</h3>
            <p>{t(lang, "rp_desc")}</p>
            <div className="reportActions">
              <button
                type="button"
                className="action"
                onClick={() => downloadFile("/api/reports/executive.pdf?lang=" + lang, "cottonil-executive.pdf").catch(() => window.alert("Download failed"))}
              >
                {t(lang, "rp_pdf")}
              </button>
              <button
                type="button"
                className="action"
                onClick={() => downloadFile("/api/reports/executive.xlsx", "cottonil-executive.xlsx").catch(() => window.alert("Download failed"))}
              >
                {t(lang, "rp_xlsx")}
              </button>
              <button
                type="button"
                className="ghost"
                style={{ padding: "9px 18px", borderRadius: 10, border: "1px solid var(--c-border-strong)" }}
                onClick={() => downloadFile("/api/reports/summary", "cottonil-summary.json").catch(() => window.alert("Download failed"))}
              >
                {t(lang, "rp_json")}
              </button>
            </div>
            <p className="muted">{t(lang, "rp_note")}</p>
          </div>
        )}
        {page === "settings" && (
          <div className="card">
            <h3>{t(lang, "n_settings")}</h3>
            <p>{t(lang, "st_note")}</p>
            <button className="primary" onClick={refresh}>
              {t(lang, "st_reload")}
            </button>
          </div>
        )}
        <footer>
          <span>{t(lang, "footer_flow")}</span>
          <span>{t(lang, "footer_note")}</span>
        </footer>
      </main>
    </div>
  );
}
/** UI hint only (hides admin-only menu items). The server enforces the role on every request. */
function roleOf(tok: string | null): string {
  if (tok?.startsWith("session:")) return tok.slice(8);
  try {
    return JSON.parse(atob((tok || "").split(".")[0].replace(/-/g, "+").replace(/_/g, "/"))).r || "viewer";
  } catch {
    return "viewer";
  }
}
function Root() {
  const [theme, setTheme] = useState<"light" | "dark">(() => document.documentElement.dataset.theme === "dark" ? "dark" : "light");
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("cottonil-theme", theme); } catch {}
  }, [theme]);
  const [lang, setLang] = useState<Lang>(() => {
    try {
      const s = localStorage.getItem("cottonil-language");
      if (s === "ar" || s === "en") return s;
    } catch {}
    return "ar";
  });
  const [authReq, setAuthReq] = useState<boolean | "error" | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
    document.title = t(lang, "app_name");
    try {
      localStorage.setItem("cottonil-language", lang);
    } catch {}
  }, [lang]);
  const setToken = (v: string | null) => {
    if (!v) setCsrf("");
    setTokenState(v);
  };
  useEffect(() => {
    fetch("/api/auth/status")
      .then((r) => { if (!r.ok) throw new Error("Authentication status unavailable"); return r.json(); })
      .then(async (j) => {
        setAuthReq(!!j.required);
        if (j.required) {
          const me = await authFetch('/api/auth/me');
          if (me.ok) {
            const identity = await me.json();
            setCsrf(identity.csrf || '');
            setTokenState('session:' + identity.role);
          }
        }
      })
      .catch(() => setAuthReq("error"));
    const h = () => { setToken(null); };
    window.addEventListener("nexus-unauth", h);
    return () => window.removeEventListener("nexus-unauth", h);
  }, []);
  if (authReq === "error") return <div className="emptystate" role="alert">{lang === "ar" ? "تعذر التحقق من حالة تسجيل الدخول. تأكدي من اتصال الخادم ثم أعيدي تحميل الصفحة." : "Unable to verify authentication status. Check the backend connection and reload."}</div>;
  if (authReq === null)
    return (
      <div className="emptystate" role="status">
        {t(lang, "loading")}
      </div>
    );
  if (authReq === true && !token) return <Login lang={lang} setLang={setLang} onSignedIn={setToken} />;
  return (
    <App lang={lang} setLang={setLang} theme={theme} setTheme={setTheme} authOn={authReq === true} isAdmin={authReq === false || roleOf(token) === "admin"} onSignOut={() => { authFetch('/api/auth/logout', {method: 'POST'}).then((r) => { if (!r.ok) throw new Error('Logout failed'); setToken(null); }).catch(() => window.alert(lang === 'ar' ? 'تعذر تسجيل الخروج من الخادم، برجاء المحاولة مرة أخرى' : 'Server logout failed. Please try again.')); }} />
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>,
);
