(function () {
  "use strict";

  var root = document.getElementById("practiceApp");
  if (!root) return;

  var apiBase = (root.getAttribute("data-api-base") || "").replace(/\/$/, "");
  var subjectSelect = document.getElementById("practiceSubject");
  var difficultySelect = document.getElementById("practiceDifficulty");
  var nextButton = document.getElementById("practiceNext");
  var solutionButton = document.getElementById("practiceSolution");
  var statusEl = document.getElementById("practiceStatus");
  var metaEl = document.getElementById("practiceMeta");
  var questionEl = document.getElementById("practiceQuestion");
  var solutionPanel = document.getElementById("practiceSolutionPanel");
  var solutionEl = document.getElementById("practiceSolutionBody");
  var currentQuestion = null;
  var metaLoaded = false;

  function setStatus(message, isError) {
    if (!statusEl) return;
    statusEl.textContent = message || "";
    statusEl.classList.toggle("is-error", Boolean(isError));
    statusEl.hidden = !message;
  }

  function setLoading(isLoading) {
    root.classList.toggle("is-loading", isLoading);
    if (nextButton) nextButton.disabled = isLoading || !metaLoaded || !apiBase;
    if (solutionButton) {
      solutionButton.disabled = isLoading || !currentQuestion;
    }
  }

  function typeset(nodes) {
    if (!window.MathJax || !window.MathJax.typesetPromise) return Promise.resolve();
    var targets = nodes ? (Array.isArray(nodes) ? nodes : [nodes]) : undefined;
    return window.MathJax.typesetPromise(targets).catch(function () {});
  }

  function clearSolution() {
    if (solutionPanel) solutionPanel.hidden = true;
    if (solutionEl) solutionEl.innerHTML = "";
  }

  function renderQuestion(question) {
    currentQuestion = question;
    clearSolution();

    if (!questionEl) return;

    var parts = [];
    if (question.title) {
      parts.push("<h2 class=\"practice-question__title\">" + escapeHtml(question.title) + "</h2>");
    }
    if (question.content) {
      parts.push("<div class=\"practice-question__content\">" + question.content + "</div>");
    }

    questionEl.innerHTML = parts.join("");
    questionEl.hidden = false;

    if (metaEl) {
      var metaParts = [];
      if (question.subject) metaParts.push(question.subject);
      if (question.difficulty) metaParts.push("难度 " + question.difficulty);
      if (question.chapter) metaParts.push(question.chapter);
      metaEl.textContent = metaParts.join(" · ");
      metaEl.hidden = metaParts.length === 0;
    }

    if (solutionButton) {
      solutionButton.disabled = false;
      solutionButton.hidden = false;
    }

    return typeset([questionEl]);
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function apiUrl(path) {
    return apiBase + path;
  }

  function fetchJson(path) {
    return fetch(apiUrl(path), {
      method: "GET",
      headers: { accept: "application/json" },
    }).then(function (response) {
      return response.json().catch(function () {
        return { error: "接口返回了无效数据。" };
      }).then(function (payload) {
        if (!response.ok) {
          throw new Error(payload.error || "请求失败（" + response.status + "）");
        }
        return payload;
      });
    });
  }

  function populateFilters(meta) {
    if (!subjectSelect) return;

    subjectSelect.innerHTML = "";
    (meta.subjects || []).forEach(function (subject) {
      var option = document.createElement("option");
      option.value = subject;
      option.textContent = subject;
      subjectSelect.appendChild(option);
    });

    if (difficultySelect) {
      var current = difficultySelect.value || "all";
      difficultySelect.innerHTML = "";
      var allOption = document.createElement("option");
      allOption.value = "all";
      allOption.textContent = "全部难度";
      difficultySelect.appendChild(allOption);

      (meta.difficulties || []).forEach(function (level) {
        var levelOption = document.createElement("option");
        levelOption.value = String(level);
        levelOption.textContent = "难度 " + level;
        difficultySelect.appendChild(levelOption);
      });

      difficultySelect.value = current;
    }
  }

  function loadMeta() {
    if (!apiBase) {
      setStatus("练习 API 尚未配置。请在仓库 _data/practice.yml 中填写 api_base，并完成 Cloudflare 部署。", true);
      setLoading(false);
      return Promise.resolve();
    }

    setLoading(true);
    setStatus("正在加载题库信息…");

    return fetchJson("/api/meta")
      .then(function (meta) {
        metaLoaded = true;
        populateFilters(meta);
        if (subjectSelect) subjectSelect.disabled = false;
        if (difficultySelect) difficultySelect.disabled = false;
        var total = meta.total || 0;
        setStatus(total ? "题库已就绪，共 " + total + " 题。" : "题库为空。");
      })
      .catch(function (error) {
        metaLoaded = false;
        setStatus(error.message || "无法连接练习 API。", true);
      })
      .finally(function () {
        setLoading(false);
      });
  }

  function loadQuestion() {
    if (!apiBase || !subjectSelect) return;

    var subject = subjectSelect.value;
    var difficulty = difficultySelect ? difficultySelect.value : "all";
    if (!subject) {
      setStatus("请先选择科目。", true);
      return;
    }

    setLoading(true);
    setStatus("正在抽题…");
    clearSolution();
    if (questionEl) questionEl.hidden = true;
    if (metaEl) metaEl.hidden = true;

    var query = "/api/random?subject=" + encodeURIComponent(subject) + "&difficulty=" + encodeURIComponent(difficulty);

    fetchJson(query)
      .then(function (question) {
        setStatus("");
        return renderQuestion(question);
      })
      .catch(function (error) {
        currentQuestion = null;
        if (solutionButton) solutionButton.disabled = true;
        setStatus(error.message || "抽题失败。", true);
      })
      .finally(function () {
        setLoading(false);
      });
  }

  function loadSolution() {
    if (!currentQuestion || !currentQuestion.id) return;

    setLoading(true);
    setStatus("正在加载解析…");

    fetchJson("/api/solution?id=" + encodeURIComponent(currentQuestion.id))
      .then(function (payload) {
        setStatus("");
        if (!solutionPanel || !solutionEl) return;
        solutionEl.innerHTML = payload.solution || "<p>暂无解析。</p>";
        solutionPanel.hidden = false;
        return typeset([solutionEl]);
      })
      .catch(function (error) {
        setStatus(error.message || "解析加载失败。", true);
      })
      .finally(function () {
        setLoading(false);
      });
  }

  if (nextButton) {
    nextButton.addEventListener("click", loadQuestion);
  }

  if (solutionButton) {
    solutionButton.addEventListener("click", loadSolution);
  }

  loadMeta();
})();
