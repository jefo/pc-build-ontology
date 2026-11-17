(function () {
  "use strict";

  const DATA = (window.PCBO_DEMO && window.PCBO_DEMO.scenarios) || [];
  if (!DATA.length) {
    document.body.innerHTML = "<p style='padding:40px;font-family:monospace'>demo data not found</p>";
    return;
  }

  const STATUS = {
    pass: { label: "ПРОЙДЕНО", cls: "pass" },
    warn: { label: "ВНИМАНИЕ", cls: "warn" },
    fail: { label: "БЛОК", cls: "fail" },
    skip: { label: "НЕТ ДАННЫХ", cls: "skip" },
  };

  const VERDICT = {
    PASS: { text: "ПРОЙДЕНО", color: "var(--green)" },
    PASS_WITH_WARNINGS: { text: "ДОПУСТИМО С ОГОВОРКАМИ", color: "var(--amber)" },
    FAIL: { text: "ЗАБЛОКИРОВАНО", color: "var(--red)" },
  };

  const $ = (id) => document.getElementById(id);

  const num = (v) => new Intl.NumberFormat("ru-RU").format(Math.round(v));

  function plural(n, one, few, many) {
    const mod10 = n % 10;
    const mod100 = n % 100;
    if (mod10 === 1 && mod100 !== 11) return one;
    if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
    return many;
  }

  function temperatureState(state) {
    if (state === "T_Throttle" || state === "T_Critical") return "bad";
    if (state === "T_Hot") return "warn";
    return "good";
  }

  function checkRows(s) {
    const r = s.result;
    const thermal = r.thermal_profile || {};
    const power = r.power_state || {};
    const pcie = r.pcie_topology || {};
    const profile = r.profile_conflicts || {};
    const mvs = r.mvs_allocation || {};
    const vrm = r.cpu_vrm;
    const gpcie = r.gpu_pcie;
    const floor = r.component_floor || {};
    const l5 = r.l5_validation || {};

    const rows = [
      {
        name: "structural_clearance",
        ru: "Геометрия корпуса",
        status: r.structural_clearance && r.structural_clearance.is_compatible ? "pass" : "fail",
        detail: r.structural_clearance && r.structural_clearance.is_compatible
          ? `GPU ${r.structural_clearance.tolerances.gpu_clearance_mm} мм · кулер ${r.structural_clearance.tolerances.cooler_clearance_mm} мм`
          : (r.structural_clearance.failures || []).join(" · "),
      },
      {
        name: "envelope_collision_3d",
        ru: "3D-конфликты кулер / VRM / RAM",
        status: r.envelope_collision_3d && r.envelope_collision_3d.is_compatible ? "pass" : "fail",
        detail: r.envelope_collision_3d && r.envelope_collision_3d.is_compatible
          ? `зазор RAM ${r.envelope_collision_3d.tolerances.ram_collision_gap_mm} мм`
          : (r.envelope_collision_3d.conflicts || []).join(" · "),
      },
      {
        name: "pcie_topology",
        ru: "Линии PCIe и бифуркация",
        status: (pcie.warnings || []).length ? "warn" : "pass",
        detail: `Gen${pcie.gpu_pcie_gen_effective} ×${pcie.gpu_effective_pcie_lanes} · ${pcie.effective_bandwidth_gbs} GB/s`,
      },
      {
        name: "thermal_profile",
        ru: "Нагрев и thermal soak",
        status: temperatureState(thermal.cpu_thermal_state) === "bad" || thermal.thermal_soak_active
          ? "warn"
          : "pass",
        detail: `CPU ${thermal.predicted_cpu_temp_C} °C · GPU ${thermal.predicted_gpu_temp_C} °C` +
          (thermal.thermal_soak_active ? ` · soak +${thermal.thermal_soak_penalty_C} °C` : ""),
      },
      {
        name: "marginal_value",
        ru: "Переплата без прироста",
        status: r.marginal_value ? "pass" : "skip",
        detail: r.marginal_value ? "MV-кандидаты рассчитаны" : "mv_candidates не переданы",
      },
      {
        name: "power_state",
        ru: "Питание и transient spikes",
        status: power.status === "BLOCK" ? "fail" : power.status === "WARN" ? "warn" : "pass",
        detail: `${power.full_load_power_W} W полной нагрузки · запас ${power.psu_headroom_factor}×`,
      },
      {
        name: "acoustic_class",
        ru: "Акустический класс",
        status: r.acoustic_class && r.acoustic_class.is_compliant ? "pass" : "warn",
        detail: `${r.acoustic_class.predicted_acoustic_class_load} под нагрузкой`,
      },
      {
        name: "profile_conflicts",
        ru: "Профили компонентов",
        status: profile.profile_validation_status === "BLOCK"
          ? "fail"
          : profile.profile_validation_status === "WARN"
            ? "warn"
            : "pass",
        detail: `${profile.summary ? profile.summary.optimal_count : 0} optimal · ${profile.summary ? profile.summary.block_count : 0} block`,
      },
      {
        name: "physical_constraints",
        ru: "Физические предикаты",
        status: r.physical_constraints && r.physical_constraints.pass ? "pass" : "fail",
        detail: r.physical_constraints
          ? `${r.physical_constraints.checks.length - r.physical_constraints.blocking_failures}/${r.physical_constraints.checks.length} предикатов`
          : "не переданы",
      },
      {
        name: "mvs_allocation",
        ru: "Минимальная спецификация",
        status: mvs.mvs_status === "FAIL" ? "fail" : mvs.mvs_status === "WARN" ? "warn" : "pass",
        detail: `${(mvs.violations || []).length} ${plural((mvs.violations || []).length, "нарушение", "нарушения", "нарушений")} · ${mvs.tier_label || "—"}`,
      },
      {
        name: "cpu_vrm",
        ru: "TDP процессора → VRM платы",
        status: !vrm ? "skip" : vrm.cpu_vrm_status === "PASS" ? "pass" : "fail",
        detail: !vrm ? "блок не передан" : `${vrm.cpu_tdp_w} W → ${vrm.actual_vrm}`,
      },
      {
        name: "gpu_pcie",
        ru: "Класс GPU → слот платы",
        status: !gpcie ? "skip" : gpcie.gpu_pcie_status === "PASS" ? "pass" : "fail",
        detail: !gpcie ? "блок не передан" : `${gpcie.gpu_class} → Gen${gpcie.actual_mb_gen}`,
      },
      {
        name: "component_floor",
        ru: "Полы интента",
        status: floor.floor_status === "SKIP" ? "skip" : floor.floor_status === "PASS" ? "pass" : "warn",
        detail: floor.intent_id ? `${floor.intent_id} · ${(floor.violations || []).length} нарушений` : "интент не задан",
      },
      {
        name: "l5_validation",
        ru: "Итоговый gate",
        status: l5.validation_status === "FAIL" ? "fail" : l5.validation_status === "PASS_WITH_WARNINGS" ? "warn" : "pass",
        detail: l5.action_required || "—",
      },
    ];

    return rows;
  }

  function tile(label, value, sub, tone) {
    return `<div class="tile">
      <div class="tile-label">${label}</div>
      <div class="tile-value ${tone || ""}">${value}</div>
      <div class="tile-sub">${sub}</div>
    </div>`;
  }

  function toneForHeadroom(v) {
    if (v >= 1.5) return "good";
    if (v >= 1.1) return "warn";
    return "bad";
  }

  function render(slug) {
    const s = DATA.find((x) => x.slug === slug) || DATA[0];
    const r = s.result;
    const l5 = r.l5_validation;
    const thermal = r.thermal_profile || {};
    const power = r.power_state || {};
    const profile = r.profile_conflicts || {};
    const budget = s.build.budget;
    const verdict = VERDICT[l5.validation_status] || VERDICT.FAIL;

    document.title = `PCBO — ${s.label}`;
    $("case-id").textContent = `${s.caseId} / ${s.label.toUpperCase()}`;
    $("tagline").textContent = s.tagline;
    $("total").textContent = s.total;

    const verdictEl = $("verdict");
    verdictEl.style.setProperty("--status", verdict.color);
    $("verdict-status").textContent = verdict.text;
    $("verdict-summary").textContent = l5.summary || "";
    $("verdict-action").textContent = l5.action_required || "—";
    $("verdict-note").textContent = `validation_status = ${l5.validation_status}`;

    const optimal = profile.summary ? profile.summary.optimal_count : 0;
    const blockers = (l5.failed_check_ids || []).length;
    const warnings = (l5.warnings || []).length;

    $("tiles").innerHTML = [
      tile(
        "CPU temp",
        `${thermal.predicted_cpu_temp_C}<small> °C</small>`,
        thermal.cpu_thermal_state,
        temperatureState(thermal.cpu_thermal_state)
      ),
      tile(
        "GPU temp",
        `${thermal.predicted_gpu_temp_C}<small> °C</small>`,
        thermal.gpu_thermal_state,
        temperatureState(thermal.gpu_thermal_state)
      ),
      tile(
        "PSU headroom",
        `${power.psu_headroom_factor}<small>×</small>`,
        `${power.full_load_power_W} W full load`,
        toneForHeadroom(power.psu_headroom_factor)
      ),
      tile(
        "Бюджет",
        `${num(budget.actual_cost / 1000)}<small>K ₽</small>`,
        `потолок ${num(budget.ceiling / 1000)}K ₽`,
        budget.actual_cost <= budget.ceiling ? "good" : "bad"
      ),
      tile(
        "Optimal profiles",
        `${optimal}`,
        `${profile.summary ? profile.summary.block_count : 0} block`,
        optimal > 0 ? "good" : "warn"
      ),
      tile(
        "Блокеры",
        `${blockers}`,
        `${warnings} ${plural(warnings, "предупреждение", "предупреждения", "предупреждений")}`,
        blockers ? "bad" : "good"
      ),
    ].join("");

    $("checks").innerHTML = checkRows(s).map((row, i) => {
      const st = STATUS[row.status] || STATUS.skip;
      return `<div class="check">
        <div class="check-index">${String(i + 1).padStart(2, "0")}</div>
        <div class="check-name">${row.name}<span>${row.ru}</span><em>${row.detail}</em></div>
        <div class="pill ${st.cls}">${st.label}</div>
      </div>`;
    }).join("");

    $("components").innerHTML = s.components.map((c) => (
      `<tr><td>${c[0]}</td><td>${c[1]}</td><td>${c[3]}</td></tr>`
    )).join("");

    $("config-note").textContent = s.note;

    const blockerList = l5.failed_check_ids || [];
    const warningList = l5.warnings || [];
    $("blockers").innerHTML = blockerList.length
      ? blockerList.map((x) => `<li>${x}</li>`).join("")
      : `<li class="empty">Нет блокирующих проверок.</li>`;
    $("warnings").innerHTML = warningList.length
      ? warningList.map((x) => `<li>${x}</li>`).join("")
      : `<li class="empty">Предупреждений нет.</li>`;

    $("tabs").innerHTML = DATA.map((x) => (
      `<button class="tab" role="tab" aria-selected="${x.slug === s.slug}" data-slug="${x.slug}">${x.label}</button>`
    )).join("");

    $("tabs").querySelectorAll(".tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        const next = btn.dataset.slug;
        history.replaceState(null, "", `?scenario=${encodeURIComponent(next)}`);
        render(next);
      });
    });
  }

  const params = new URLSearchParams(location.search);
  render(params.get("scenario") || DATA[0].slug);
})();
