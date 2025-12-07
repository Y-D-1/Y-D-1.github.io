---
title: "泛函分析"
collection: exams
type: "专业限制性选修"
permalink: /exams/functional-analysis
venue: "ECNU"
date: 2024-11-05
location: "Shanghai, China"
grade: 3.0
a: 大三上
instructor: 何小清教授
---

<div class="exam-toc">
  <h2>试卷目录</h2>
  <ul>
    <li><a href="#2024-fall-test1">2024秋季学期第一次小测</a></li>
    <li><a href="#2024-fall-test2">2024秋季学期第二次小测</a></li>
  </ul>
</div>

<style>
.exam-toc {
  background: transparent;
  padding: 1.5rem;
  border-radius: 8px;
  margin: 2rem 0;
  border-left: 4px solid #4285f4;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.exam-toc h2 {
  margin-top: 0;
  color: inherit;
}

.exam-toc ul {
  list-style: none;
  padding-left: 0;
}

.exam-toc li {
  margin: 0.8rem 0;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background 0.3s;
}

.exam-toc li:hover {
  background: rgba(0, 0, 0, 0.05);
}

.exam-toc a {
  text-decoration: none;
  color: #4285f4;
  font-weight: 500;
  display: block;
}

.exam-header {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.9) 0%, rgba(118, 75, 162, 0.9) 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 8px;
  margin: 1.5rem 0;
}

.exam-header h3 {
  margin: 0;
  font-size: 1.4rem;
}

.exam-meta {
  opacity: 0.9;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

details {
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  margin: 1.5rem 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  transition: box-shadow 0.3s;
}

details:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

summary {
  background: transparent;
  padding: 1.2rem 1.5rem;
  cursor: pointer;
  font-weight: 600;
  color: inherit;
  border-radius: 8px 8px 0 0;
  font-size: 1.1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

details[open] summary {
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.exam-content {
  padding: 1.5rem;
}

.question {
  margin: 1.5rem 0;
  padding: 1rem;
  background: transparent;
  border-radius: 6px;
  border-left: 3px solid #4285f4;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.question-title {
  font-weight: 600;
  color: inherit;
  margin-bottom: 0.8rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.points {
  background: #4285f4;
  color: white;
  padding: 0.2rem 0.6rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
}

.math-content {
  line-height: 1.6;
  font-size: 1rem;
}

.math-content p {
  margin: 0.8rem 0;
}

.solution {
  margin: 1rem 0;
}

.solution summary {
  background: transparent;
  padding: 0.8rem 1rem;
  cursor: pointer;
  font-weight: 600;
  color: inherit;
  border-radius: 4px;
  font-size: 1rem;
  border: 1px solid rgba(0, 0, 0, 0.1);
  margin-bottom: 0;
}

.solution summary:hover {
  background: rgba(0, 0, 0, 0.02);
}

.solution-content {
  padding: 1rem;
  border-left: 2px solid rgba(0, 0, 0, 0.1);
  margin-top: 0.5rem;
}

.proof {
  background: rgba(255, 243, 224, 0.5);
  border: 1px solid rgba(255, 183, 77, 0.5);
  border-radius: 6px;
  padding: 1rem;
  margin: 1rem 0;
}

.proof-title {
  font-weight: 600;
  color: #e65100;
  margin-bottom: 0.5rem;
}

.optional {
  background: rgba(232, 245, 232, 0.5);
  border: 1px solid rgba(76, 175, 80, 0.5);
  border-radius: 6px;
  padding: 1rem;
  margin: 1rem 0;
}

.optional-title {
  font-weight: 600;
  color: #2e7d32;
  margin-bottom: 0.5rem;
}

@media (max-width: 768px) {
  .exam-content {
    padding: 1rem;
  }
  
  summary {
    padding: 1rem;
  }
  
  .question {
    padding: 0.8rem;
  }
}
</style>

<div id="2024-fall-test1" class="exam-header">
  <h3>2024秋季学期第一次小测</h3>
  <div class="exam-meta">考试时间：2024年11月5日 上午8:00-8:45 | 总分：100分</div>
</div>

<details markdown="1">
  <summary>完整试题</summary>
  <div class="exam-content">
    <div class="question">
      <div class="question-title">
        <span>第1题</span>
        <span class="points">20分</span>
      </div>
      <div class="math-content">
        <p>对任意 \( x = \begin{pmatrix} x_1 \\ x_2 \end{pmatrix} \in \mathbb{R}^2 \)，定义 \(\|x\|_* = \max\{|x_1|, 3|x_2|\}\). 令 \( A = \begin{pmatrix} 3 & -2 \\ 2 & -1 \end{pmatrix} \). </p>
        <p>(1) 证明 \(\| \cdot \|_*\) 是 \(\mathbb{R}^2\) 上的一个范数. </p>
        <p>(2) 记 \( E = (\mathbb{R}^2, \| \cdot \|_*) \)，\(\varphi(x) = Ax, \forall x \in \mathbb{R}^2\). 证明 \(\|\varphi\|_{B(E)} = 7\). </p>
      </div>
    </div>
    <div class="question">
      <div class="question-title">
        <span>第2题</span>
        <span class="points">30分</span>
      </div>
      <div class="math-content">
        <p>设 \((X, d)\) 是度量空间. </p>
        <p>(1) 给出 \( X \) 中 Cauchy 序列的定义. </p>
        <p>(2) 给出 \((X, d)\) 是完备度量空间的定义. 给出一个无穷维的完备的赋范空间的例子（需注明范数的定义）. </p>
        <p>(3) 证明任意 Cauchy 序列是有界的. </p>
      </div>
    </div>
    <div class="question">
      <div class="question-title">
        <span>第3题</span>
        <span class="points">24分</span>
      </div>
      <div class="math-content">
        <p>令 \(\mathbb{R}[x]\) 是 \(\mathbb{R}\) 上所有实系数多项式构成的向量空间. 设 \( E_0 = \{P \in \mathbb{R}[x], P(0) = 0\} \)，定义 \(\varphi(P) = xP'(x)\). </p>
        <p>(1) 证明 \( E_0 \) 是 \(\mathbb{R}[x]\) 是子向量空间. 证明 \(\varphi\) 是 \(E_0\) 上的线性同构，即 \(\varphi\) 是一个线性双射. </p>
        <p>(2) 定义 \( N(P) = \sum_{1 \leq k \leq n} |a_k| \)，其中 \( P(x) = \sum_{1 \leq k \leq n} a_k x^k \). 证明 \( N \) 是 \( E_0 \) 上的一个范数. </p>
        <p>(3) 证明 \(\varphi^{-1}\) 是 \((E_0, N)\) 上的连续映射. 求 \(\|\varphi^{-1}\|_{B(E_0)}\). </p>
      </div>
    </div>
    <div class="question">
      <div class="question-title">
        <span>第4题</span>
        <span class="points">26分</span>
      </div>
      <div class="math-content">
        <p>指出下述命题是否正确. 如果判断命题是错误的，请给出一个相关的正确命题或者举出反例. </p>
        <p>(1) 若 \((X_1, d_1), (X_2, d_2)\) 是两个同胚的度量空间，若 \(X_1\) 完备，则 \(X_2\) 也完备. [注：称两个拓扑空间 \((X_1, d_1), (X_2, d_2)\) 同胚，如果存在 \((X_1, d_1)\) 到 \((X_2, d_2)\) 的映射 \(f\) 是连续双射且 \(f^{-1}\) 也是连续的. ]</p>
        <p>(2) 设 \((X, d)\) 是度量空间，\(A \subset X\)，\(A\) 是 \(X\) 的有界闭集，则 \(A\) 为紧集. </p>
        <p>(3) 赋范线性空间 \(E\) 中绝对收敛级数必收敛. </p>
        <p>(4) 任意 Banach 空间 \(E\) 到自身的线性映射都是连续的. </p>
      </div>
    </div>
  </div>
</details>

<div id="2024-fall-test2" class="exam-header">
  <h3>泛函分析第二次小测验</h3>
  <div class="exam-meta">考试时间：2024年11月27日 下午1:00-2:00 | 总分：100分</div>
</div>

<details markdown="1">
  <summary>完整试题</summary>
  <div class="exam-content">
    <div class="question">
      <div class="question-title">
        <span>第1题</span>
        <span class="points">30分</span>
      </div>
      <div class="math-content">
        <p>设 \(\mathcal{X}\) 是一个内积空间. </p>
        <p>(1) 证明任给 \(x, y \in \mathcal{X}\), 成立 \(\|x + y\|^2 = \|x\|^2 + \|y\|^2 + 2\operatorname{Re}\langle x, y\rangle\). </p>
        <p>(2) 由此推出平行四边形等式：\(\|x + y\|^2 + \|x - y\|^2 = 2(\|x\|^2 + \|y\|^2)\), 对任意的 \(x, y \in \mathcal{X}\). </p>
        <p>(3) 考虑 \(\mathcal{Y} = C([0, 2], \mathbb{R})\) 并赋予范数 \(\|f\| = \max_{t \in [0, 2]} |f(t)|\). 利用 \(f(t) = t\) 和 \(g(t) = 3\), 证明 \(\mathcal{Y}\) 不是内积空间. </p>
      </div>
    </div>
    <div class="question">
      <div class="question-title">
        <span>第2题</span>
        <span class="points">40分</span>
      </div>
      <div class="math-content">
        <p>记 \(\mathcal{X} = \mathbb{R}_1[x]\), 即 \(\mathbb{R}\) 上次数小于等于1的多项式空间. 对任意 \(P, Q \in \mathcal{X}\), 令
          \[\langle P, Q \rangle = P(0)Q(0) + 4P(1)Q(1). \]
        </p>
        <p>(1) 证明 \(\langle \cdot,\cdot \rangle\) 在 \(\mathcal{X}\) 上定义了一个内积. </p>
        <p>(2) 证明 \(\mathcal{X}\) 是一个 Hilbert 空间. </p>
        <p>(3) 记 \(\mathcal{M} = \operatorname{span}\{x\}\). 计算 \(\mathcal{M}^\perp\). </p>
        <p>(4) 给出 \(\mathcal{X}\) 的一个规范正交基. </p>
      </div>
    </div>
    <div class="question">
      <div class="question-title">
        <span>第3题</span>
        <span class="points">30分</span>
      </div>
      <div class="math-content">
        <p>设 \(H\) 是数域 \(\mathbb{K}\) 上的一个 Hilbert 空间，并设 \(T \in \mathcal{B}(H)\) 且 \(\|T\| \leq 1\). </p>
        <p>(1) 证明：\(T(x) = x\) 当且仅当 \(T^*(x) = x, x \in H\). </p>
        <p class="hint">提示：考虑 \(\|T^*(x) - x\|^2\)，并利用条件 \(\|T\| \leq 1\). </p>
        <p>(2) 证明：\(\ker(I - T) = \ker(I - T^*)\). </p>
        <p>(3) 叙述 Hilbert 空间 \(H\) 上的正交分解定理. </p>
        <p>(4) 证明：\(H = \ker(I - T) \oplus \overline{\operatorname{range}(I - T)}\). </p>
        <p class="hint">提示：利用 (2) 和 (3) 的结论. </p>
      </div>
    </div>
  </div>
</details>

<script>
// 添加一些交互功能
document.addEventListener('DOMContentLoaded', function() {
  // 为所有details元素添加切换动画
  const detailsElements = document.querySelectorAll('details');
  
  detailsElements.forEach(details => {
    details.addEventListener('toggle', function() {
      if (this.open) {
        this.style.transition = 'all 0.3s ease';
      }
    });
  });
  
  // 平滑滚动到锚点
  const links = document.querySelectorAll('a[href^="#"]');
  links.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        targetElement.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });
});
</script>
