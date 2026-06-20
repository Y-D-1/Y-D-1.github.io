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
  var numberEl = document.getElementById("practiceNumber");
  var solutionPanel = document.getElementById("practiceSolutionPanel");
  var dividerEl = document.getElementById("practiceDivider");
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

  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function findLatexDelimiterEnd(text, start, openToken, closeToken) {
    var pos = start + openToken.length;
    var depth = 1;
    while (pos < text.length && depth > 0) {
      if (text.startsWith(openToken, pos)) {
        depth += 1;
        pos += openToken.length;
        continue;
      }
      if (text.startsWith(closeToken, pos)) {
        depth -= 1;
        if (depth === 0) {
          return pos + closeToken.length;
        }
        pos += closeToken.length;
        continue;
      }
      pos += 1;
    }
    return -1;
  }

  function splitMathSegments(text) {
    var segments = [];
    var cursor = 0;

    while (cursor < text.length) {
      var next = -1;
      var token = null;

      if (text.startsWith("\\(", cursor)) {
        next = cursor;
        token = ["\\(", "\\)"];
      } else if (text.startsWith("\\[", cursor)) {
        next = cursor;
        token = ["\\[", "\\]"];
      } else if (text[cursor] === "$") {
        if (text[cursor + 1] === "$") {
          next = cursor;
          token = ["$$", "$$"];
        } else {
          next = cursor;
          token = ["$", "$"];
        }
      }

      if (next < 0) {
        segments.push({ type: "text", value: text.slice(cursor) });
        break;
      }

      if (next > cursor) {
        segments.push({ type: "text", value: text.slice(cursor, next) });
      }

      var end = findLatexDelimiterEnd(text, next, token[0], token[1]);
      if (end < 0) {
        segments.push({ type: "text", value: text.slice(next) });
        break;
      }

      segments.push({ type: "math", value: text.slice(next, end) });
      cursor = end;
    }

    return segments;
  }

  function formatTextSegment(text) {
    return splitMathSegments(text)
      .map(function (segment) {
        if (segment.type === "math") {
          return segment.value;
        }
        return escapeHtml(segment.value)
          .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
          .replace(/\*([^*]+)\*/g, "<em>$1</em>");
      })
      .join("");
  }

  function renderTextMarkdown(text) {
    if (!text) return "";

    var paragraphs = text.replace(/\r\n/g, "\n").split(/\n{2,}/);
    var html = [];

    paragraphs.forEach(function (paragraph) {
      var lines = paragraph.split("\n");
      var listType = null;
      var listItems = [];

      function flushList() {
        if (!listType) return;
        html.push("<" + listType + ">");
        listItems.forEach(function (item) {
          html.push("<li>" + formatTextSegment(item) + "</li>");
        });
        html.push("</" + listType + ">");
        listType = null;
        listItems = [];
      }

      lines.forEach(function (line) {
        var ordered = line.match(/^\s*(\d+)\.\s+(.*)$/);
        var bullet = line.match(/^\s*-\s+(.*)$/);
        var numbered = line.match(/^\s*\((\d+)\)\s+(.*)$/);

        if (ordered) {
          if (listType !== "ol") {
            flushList();
            listType = "ol";
          }
          listItems.push(ordered[2]);
          return;
        }

        if (bullet) {
          if (listType !== "ul") {
            flushList();
            listType = "ul";
          }
          listItems.push(bullet[1]);
          return;
        }

        if (numbered) {
          flushList();
          html.push(
            '<p class="practice-subpart"><span class="practice-subpart__label">(' +
              numbered[1] +
              ")</span> " +
              formatTextSegment(numbered[2]) +
              "</p>"
          );
          return;
        }

        flushList();
        if (line.trim()) {
          html.push("<p>" + formatTextSegment(line) + "</p>");
        }
      });

      flushList();
    });

    return html.join("");
  }

  function renderMarkdown(text) {
    if (!text) return "";

    var html = [];
    var cursor = 0;

    while (cursor < text.length) {
      var displayStart = text.indexOf("\\[", cursor);
      if (displayStart < 0) {
        html.push(renderTextMarkdown(text.slice(cursor)));
        break;
      }

      if (displayStart > cursor) {
        html.push(renderTextMarkdown(text.slice(cursor, displayStart)));
      }

      var displayEnd = findLatexDelimiterEnd(text, displayStart, "\\[", "\\]");
      if (displayEnd < 0) {
        html.push(renderTextMarkdown(text.slice(displayStart)));
        break;
      }

      html.push('<div class="practice-display-math">' + text.slice(displayStart, displayEnd) + "</div>");
      cursor = displayEnd;
    }

    return html.join("");
  }

  function clearSolution() {
    if (solutionPanel) solutionPanel.hidden = true;
    if (dividerEl) dividerEl.hidden = true;
    if (solutionEl) solutionEl.innerHTML = "";
  }

  function renderQuestion(question) {
    currentQuestion = question;
    clearSolution();

    if (!questionEl || !questionSection) return;

    if (numberEl) {
      numberEl.textContent = question.number ? "（" + question.number + "）" : "";
    }

    questionEl.innerHTML = renderMarkdown(question.content || "") || "<p>暂无题目内容。</p>";
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
    if (numberEl) numberEl.textContent = "";

    var query = "/api/random?subject=" + encodeURIComponent(subject);

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
        solutionEl.innerHTML = renderMarkdown(payload.solution || "") || "<p>暂无解析。</p>";
        if (dividerEl) dividerEl.hidden = false;
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
