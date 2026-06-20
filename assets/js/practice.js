(function () {
  "use strict";

  var root = document.getElementById("practiceApp");
  if (!root) return;

  var apiBase = (root.getAttribute("data-api-base") || "").replace(/\/$/, "");
  var subjectSelect = document.getElementById("practiceSubject");
  var nextButton = document.getElementById("practiceNext");
  var solutionButton = document.getElementById("practiceSolution");
  var statusEl = document.getElementById("practiceStatus");
  var questionSection = document.getElementById("practiceQuestionSection");
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

    if (!questionEl || !questionSection) return;

    questionEl.innerHTML = question.content || "<p>暂无题目内容。</p>";
    questionSection.hidden = false;

    if (solutionButton) {
      solutionButton.disabled = false;
      solutionButton.hidden = false;
    }

    return typeset([questionEl]);
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

  function populateSubjects(meta) {
    if (!subjectSelect) return;

    subjectSelect.innerHTML = "";
    (meta.subjects || []).forEach(function (subject) {
      var option = document.createElement("option");
      option.value = subject;
      option.textContent = subject;
      subjectSelect.appendChild(option);
    });
  }

  function loadMeta() {
    if (!apiBase) {
      setStatus("练习 API 尚未配置。", true);
      setLoading(false);
      return Promise.resolve();
    }

    setLoading(true);
    setStatus("");

    return fetchJson("/api/meta")
      .then(function (meta) {
        metaLoaded = true;
        populateSubjects(meta);
        if (subjectSelect) subjectSelect.disabled = false;
        setStatus("");
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
    if (!subject) {
      setStatus("请先选择科目。", true);
      return;
    }

    setLoading(true);
    setStatus("");
    clearSolution();
    if (questionSection) questionSection.hidden = true;

    var query = "/api/random?subject=" + encodeURIComponent(subject) + "&difficulty=all";

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
    setStatus("");

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
