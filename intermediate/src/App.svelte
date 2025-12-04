<script>
// @ts-nocheck

  import { onMount } from 'svelte';
  import * as XLSX from 'xlsx';
  let triangleInput = ``;
  let triangleResult = null;
  let triangleError = '';
  let triangleLoading = false;

  let darkMode = false;

  // For selecting float from triangle
  let selectedRow = 0;
  let selectedCol = 0;
  let triangleArray = [];
  let selectedFloat = '';
  let rowLabels = [];
  let colLabels = [];

  let ultimateLossResult = null;
  let ultimateLossError = '';
  let ultimateLossLoading = false;

  // IBNR states
  let costDealt = '';
  let ibnrResult = null;
  let ibnrError = '';

  // Drag and drop states
  let dragActive = false;

  // On mount, check system preference and localStorage
  onMount(() => {
    if (localStorage.getItem('darkMode') === 'enabled') {
      darkMode = true;
    } else if (localStorage.getItem('darkMode') === 'disabled') {
      darkMode = false;
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      darkMode = true;
    }
    updateBodyClass();
  });

  function updateBodyClass() {
    if (typeof document !== 'undefined') {
      document.body.classList.toggle('dark-mode', darkMode);
    }
  }

  function toggleDarkMode() {
    darkMode = !darkMode;
    localStorage.setItem('darkMode', darkMode ? 'enabled' : 'disabled');
    updateBodyClass();
  }

  function handleDragOver(event) {
    event.preventDefault();
    dragActive = true;
  }
  function handleDragLeave(event) {
    event.preventDefault();
    dragActive = false;
  }
  function handleDrop(event) {
    event.preventDefault();
    dragActive = false;
    const file = event.dataTransfer.files[0];
    if (!file) return;
    handleFile(file);
  }
  function handleFileInput(event) {
    const file = event.target.files[0];
    if (!file) return;
    handleFile(file);
  }
  async function handleFile(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext === 'csv') {
      const text = await file.text();
      parseCSV(text);
    } else if (ext === 'xlsx' || ext === 'xls') {
      // Use SheetJS for Excel
      try {
        const data = await file.arrayBuffer();
        const workbook = XLSX.read(data, { type: 'array' });
        const sheetName = workbook.SheetNames[0];
        const sheet = workbook.Sheets[sheetName];
        const arr = XLSX.utils.sheet_to_json(sheet, { header: 1, blankrows: false });
        setTriangleFromArray(arr);
      } catch (e) {
        triangleError = 'Failed to parse Excel file.';
      }
    } else {
      triangleError = 'Unsupported file type. Please upload a CSV or Excel file.';
    }
  }
  function parseCSV(text) {
    const rows = text.split(/\r?\n/).filter(row => row.trim() !== '');
    const arr = rows.map(row => row.split(',').map(cell => {
      const trimmed = cell.trim();
      if (trimmed === '' || trimmed.toLowerCase() === 'null') return null;
      // If header, keep as string
      if (isNaN(Number(trimmed)) && trimmed !== null) return trimmed;
      const num = Number(trimmed);
      return isNaN(num) ? null : num;
    }));
    setTriangleFromArray(arr);
  }
  function setTriangleFromArray(arr) {
    // If first row is header, use it for colLabels
    if (!Array.isArray(arr) || arr.length < 2 || !Array.isArray(arr[0])) {
      triangleError = 'Invalid file format. Must be a 2D table with header row.';
      return;
    }
    colLabels = arr[0].slice(1); // skip first col (row label)
    rowLabels = arr.slice(1).map(row => row[0]);
    // Build numeric array, pad with nulls
    const maxCols = colLabels.length;
    triangleArray = arr.slice(1).map(row => {
      const nums = row.slice(1).map(cell => (cell === '' || cell === null || typeof cell === 'string') ? null : cell);
      while (nums.length < maxCols) nums.push(null);
      return nums;
    });
    triangleInput = JSON.stringify(triangleArray);
    triangleError = '';
    // Set default selection
    selectedRow = 0;
    selectedCol = 0;
    selectedFloat = triangleArray[0][0];
  }

  async function submitTriangle() {
    triangleError = '';
    triangleResult = null;
    ultimateLossResult = null;
    ultimateLossError = '';
    ibnrResult = null;
    ibnrError = '';
    costDealt = '';
    selectedRow = 0;
    selectedCol = 0;
    selectedFloat = '';
    try {
      const parsed = JSON.parse(triangleInput);
      triangleArray = parsed;
      selectedRow = 0;
      selectedCol = 0;
      selectedFloat = parsed[0][0];
      const response = await fetch('http://localhost:5000/triangle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: parsed })
      });
      const data = await response.json();
      if (!response.ok) {
        triangleError = data.error || 'Error processing triangle.';
      } else {
        triangleResult = data.data;
      }
    } catch (e) {
      triangleError = e.message;
    }
    triangleLoading = false;
  }

  function updateSelectedFloat() {
    if (
      triangleArray &&
      triangleArray[selectedRow] &&
      triangleArray[selectedRow][selectedCol] !== undefined &&
      triangleArray[selectedRow][selectedCol] !== null
    ) {
      selectedFloat = triangleArray[selectedRow][selectedCol];
    } else {
      selectedFloat = '';
    }
  }

  async function submitUltimateLoss() {
    ultimateLossError = '';
    ultimateLossResult = null;
    ultimateLossLoading = true;
    ibnrResult = null;
    ibnrError = '';
    costDealt = '';
    try {
      const response = await fetch('http://localhost:5000/ultimate_loss', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify([selectedFloat, triangleResult])
      });
      const data = await response.json();
      if (!response.ok) {
        ultimateLossError = data.error || 'Error processing ultimate loss.';
      } else {
        ultimateLossResult = data.data;
      }
    } catch (e) {
      ultimateLossError = e.message;
    }
    ultimateLossLoading = false;
  }

  function submitIBNR() {
    ibnrError = '';
    ibnrResult = null;
    if ((!costDealt || isNaN(parseFloat(costDealt))) && costDealt != 0) {
      ibnrError = 'Please enter a valid cost dealt.';
      return;
    }
    if (!ultimateLossResult || ultimateLossResult.length === 0) {
      ibnrError = 'Ultimate loss result is not available.';
      return;
    }
    const ultimate = ultimateLossResult[ultimateLossResult.length - 1];
    ibnrResult = ultimate - parseFloat(costDealt);
  }
  
</script>

<main class:dark-mode={darkMode}>
  <button class="toggle-dark" on:click={toggleDarkMode} aria-label="Toggle dark mode">
    {#if darkMode}
      <span class="icon sun-icon"></span> Light Mode
    {:else}
      <span class="icon moon-icon"></span> Dark Mode
    {/if}
  </button>
  <div class="container">
    <div class="glass-form"
      role="region"
      aria-label="Triangle input area"
      on:dragover={handleDragOver}
      on:dragleave={handleDragLeave}
      on:drop={handleDrop}
      style="position: relative;">
      {#if dragActive}
        <div class="drop-overlay">
          <span>Drop CSV or Excel file to load triangle</span>
        </div>
      {/if}
      <!-- Step 1: Triangle Calculation -->
      <form class="triangle-form" on:submit|preventDefault={submitTriangle}>
        <label for="triangle" class="label">Triangle Array (JSON):</label>
        <textarea
          id="triangle"
          bind:value={triangleInput}
          rows="7"
          class="input-area triangle-input-large"
          spellcheck="false"
        ></textarea>
        <button type="submit" class="button" disabled={triangleLoading}>
          {triangleLoading ? 'Calculating...' : 'Calculate'}
        </button>
        {#if triangleError}
          <div class="error">{triangleError}</div>
        {/if}
      </form>

      <!-- Step 2: Ultimate Loss Calculation -->
        {#if triangleResult}
          <div class="result-section">
            <div class="result-label">LDFs (Link Development Factors) for Each Development Period:</div>
            <ul class="triangle-list">
              {#each triangleResult as value, i (i)}
                <li>
                  {(colLabels[i] && colLabels[i+1])
                    ? `${colLabels[i]} → ${colLabels[i+1]}`
                    : `Period ${i+1} → ${i+2}`}
                  <span class="triangle-value">{value}</span>
                </li>
              {/each}
            </ul>
          </div>
          <form class="triangle-form" on:submit|preventDefault={submitUltimateLoss}>
            <label class="label" for="triangle-value-select-row">Select value from Triangle for Ultimate Loss Year Data:</label>
            <div style="display: flex; gap: 1rem; align-items: center;">
              <div>
                <label for="triangle-value-select-row">Row:</label>
                <select id="triangle-value-select-row" class="styled-select" bind:value={selectedRow} on:change={updateSelectedFloat}>
                  {#each rowLabels as label, i (label)}
                    <option value={String(i)}>{label}</option>
                  {/each}
                </select>
              </div>
              <div>
                <label for="triangle-value-select-col">Col:</label>
                <select id="triangle-value-select-col" class="styled-select" bind:value={selectedCol} on:change={updateSelectedFloat}>
                  {#each colLabels as label, j (label)}
                    <option value={String(j)}>{label}</option>
                  {/each}
                </select>
              </div>
              <div>
                <span id="triangle-value-label" class="label" style="margin-right: 0.5em;">Value:</span>
                <span class="triangle-value" aria-labelledby="triangle-value-label">{selectedFloat}</span>
              </div>
            </div>
            <button type="submit" class="button" disabled={ultimateLossLoading || selectedFloat === ''}>
              {ultimateLossLoading ? 'Calculating...' : 'Calculate Ultimate Loss'}
            </button>
            {#if ultimateLossError}
              <div class="error">{ultimateLossError}</div>
            {/if}
          </form>
        {/if}

      <!-- Step 3: IBNR Calculation -->
      {#if ultimateLossResult}
        <div class="result-section">
          <div class="result-label">Ultimate Loss Result:</div>
          <ul class="triangle-list">
            {#each ultimateLossResult as value, i (i)}
              <li>{(colLabels[i] !== undefined && colLabels[i] !== null && colLabels[i] !== "") ? colLabels[i] : `Year ${i + 1}`} <span class="triangle-value">{value}</span></li>
            {/each}
          </ul>
        </div>
        <form class="triangle-form" on:submit|preventDefault={submitIBNR}>
          <label for="costDealt" class="label">Cost Dealt (float):</label>
          <input
            id="costDealt"
            type="number"
            step="any"
            bind:value={costDealt}
            class="input-area"
          />
          <button type="submit" class="button">Calculate IBNR</button>
          {#if ibnrError}
            <div class="error">{ibnrError}</div>
          {/if}
        </form>
      {/if}

      <!-- Step 4: Show IBNR Result -->
      {#if ibnrResult !== null}
        <div class="result-section">
          <div class="result-label">IBNR Result:</div>
          <div class="result-box">{ibnrResult}</div>
        </div>
      {/if}
    </div>
  </div>
</main>




<style>
:global(html), :global(body), :global(main) {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
  background: #e8ebee;
  color: #222;
  box-sizing: border-box;
  min-height: 100vh;
  width: 100vw;
  overscroll-behavior: none;
  -webkit-overflow-scrolling: touch;
}
:global(body) {
  background-color: #e8ebee;
}
:global(::selection) {
  background: #cfd8dc;
}
:global(::backdrop) {
  background-color: #e8ebee;
}
main {
  min-height: 100vh;
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e8ebee;
  box-sizing: border-box;
  position: relative;
}
.container {
  max-width: 720px;
  width: 100%;
  min-height: 100vh;
  padding: 3rem 2rem;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3rem;
  box-sizing: border-box;
  overflow-wrap: break-word;
  position: relative;
}
.glass-form {
  width: 100%;
  background: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border-radius: 24px;
  padding: 2.5rem 3rem;
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  box-sizing: border-box;
  min-height: 280px;
  color: inherit;
  overflow-wrap: break-word;
  overflow-x: auto;
  position: relative;
}
.drop-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(108,99,255,0.18);
  border-radius: 24px;
  border: 2.5px dashed #6c63ff;
  pointer-events: none;
  animation: dropFadeIn 0.4s cubic-bezier(.4,2,.6,1) both, dropGlow 1.2s infinite alternate;
}
.drop-overlay span {
  font-size: 1.3rem;
  color: #6c63ff;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-shadow: 0 2px 12px #a6a1ff44;
  animation: dropTextPop 0.5s cubic-bezier(.4,2,.6,1) both;
}
@keyframes dropFadeIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
@keyframes dropGlow {
  from { box-shadow: 0 0 0 0 #6c63ff44; }
  to { box-shadow: 0 0 32px 8px #6c63ff55; }
}
@keyframes dropTextPop {
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
}
.triangle-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
  background: none;
  border-radius: 0;
  box-shadow: none;
  padding: 0;
  border: none;
  box-sizing: border-box;
}
.label {
  font-size: 1.13rem;
  color: #222;
  font-weight: 500;
  margin-bottom: 0.1rem;
  letter-spacing: 0.01em;
}
.input-area {
  border: none;
  border-radius: 14px;
  padding: 1.2rem 1.5rem;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(12px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
  color: inherit;
  font-size: 1.1rem;
  transition: background 0.3s, color 0.3s;
  box-sizing: border-box;
  min-height: 56px;
  font-family: 'SF Mono', Consolas, monospace;
  line-height: 1.5;
  overflow-wrap: break-word;
}
.input-area:focus {
  background: #f4f4ff;
  outline: 2px solid #6c63ff;
}
.button {
  padding: 0.85rem 2.25rem;
  font-size: 1.1rem;
  font-weight: 600;
  border: none;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(18px);
  box-shadow: 0 5px 16px rgba(0, 0, 0, 0.12);
  color: inherit;
  cursor: pointer;
  transition: background-color 0.3s, box-shadow 0.3s;
  user-select: none;
  min-width: 140px;
  text-align: center;
}
.button:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.4);
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.18);
}
.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.button:active {
  background: rgba(255, 255, 255, 0.35);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.1);
}
.toggle-dark {
  position: fixed;
  top: 1.2rem;
  right: 1.2rem;
  z-index: 1000;
  background: rgba(255,255,255,0.15);
  border: none;
  border-radius: 9999px;
  padding: 0.6rem 1.25rem;
  font-weight: 600;
  color: inherit;
  cursor: pointer;
  transition: background 0.3s;
  user-select: none;
  font-size: 1rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.toggle-dark:hover {
  background: rgba(255,255,255,0.3);
}
.toggle-dark:active {
  transform: scale(0.96);
  transition-duration: 0.1s;
}
.icon {
  display: inline-block;
  width: 20px;
  height: 20px;
  background-size: contain;
  background-repeat: no-repeat;
}
.sun-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='currentColor'%3E%3Cpath d='M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z'/%3E%3C/svg%3E");
}
.moon-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='currentColor'%3E%3Cpath fill-rule='evenodd' d='M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.701-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z' clip-rule='evenodd'/%3E%3C/svg%3E");
}
.result-section {
  width: 100%;
  margin: 0;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.7rem;
  animation: smoothFadeIn 0.6s ease-in-out;
  box-sizing: border-box;
  padding: 0;
}
.result-label {
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
  color: inherit;
}
.result-box {
  font-size: 1.1rem;
  color: #1a1a1a;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 14px;
  padding: 1.25rem 1.5rem;
  word-break: break-word;
  width: 100%;
  box-sizing: border-box;
  box-shadow: 0 1px 6px 0 rgba(0,0,0,0.02);
  border: none;
  min-height: 56px;
  color: inherit;
}
.triangle-list {
  list-style: none;
  margin: 0;
  padding: 0;
  background: rgba(255,255,255,0.5);
  border-radius: 14px;
  box-shadow: 0 1px 6px 0 rgba(0,0,0,0.02);
  padding: 1.25rem 1.5rem;
  font-size: 1.1rem;
  color: inherit;
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}
.triangle-list li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  letter-spacing: 0.01em;
  color: inherit;
}
.triangle-value {
  font-family: 'SF Mono', Consolas, monospace;
  font-weight: 600;
  color: #6c63ff;
  background: rgba(108,99,255,0.07);
  border-radius: 6px;
  padding: 0.1em 0.5em;
  margin-left: 0.2em;
  font-size: 1.08em;
}
.dark-mode .triangle-list {
  background: rgba(30, 30, 40, 0.6);
  color: #f3f3f3;
}
.dark-mode .triangle-value {
  color: #a6a1ff;
  background: rgba(166,161,255,0.13);
}
.error {
  color: #d43f3f;
  font-size: 1rem;
  margin-top: 0.6rem;
  animation: smoothFadeIn 0.6s ease-in-out;
}
@keyframes smoothFadeIn {
  0% {
    opacity: 0;
    transform: translateY(10px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}
/* Dark mode support */
:global(.dark-mode), :global(.dark-mode) :global(main), :global(.dark-mode) :global(html), :global(.dark-mode) :global(body) {
  background: #181a1b !important;
  color: #f3f3f3 !important;
}
:global(.dark-mode) :global(body) {
  background-color: #181a1b !important;
}
:global(.dark-mode) :global(::selection) {
  background: #23263a;
}
:global(.dark-mode) :global(::backdrop) {
  background-color: #181a1b;
}
.dark-mode .container {
  background: none;
}
.dark-mode .glass-form {
  background: rgba(30, 30, 40, 0.45);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
.dark-mode .label {
  color: #e0e0e0;
}
.dark-mode .input-area {
  background: rgba(30, 30, 40, 0.5);
  color: #f3f3f3;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
}
.dark-mode .input-area:focus {
  background: #23263a;
  outline: 2px solid #6c63ff;
}
.dark-mode .button {
  background: rgba(30, 30, 40, 0.4);
  color: #f0f0f0;
  box-shadow: 0 5px 16px rgba(0, 0, 0, 0.25);
}
.dark-mode .button:hover:not(:disabled) {
  background: rgba(50, 50, 60, 0.6);
}
.dark-mode .button:disabled {
  background: #33373a;
  color: #888;
}
.dark-mode .result-box {
  background: rgba(30, 30, 40, 0.6);
  color: #f3f3f3;
  box-shadow: 0 1px 6px 0 rgba(0,0,0,0.18);
}
.dark-mode .error {
  background: #3a2323;
  color: #ffb3b3;
  box-shadow: 0 1px 4px 0 rgba(176,0,32,0.18);
}
@media (max-width: 768px) {
  .container {
    padding: 2rem 1.5rem;
  }
  .glass-form {
    padding: 1.8rem;
  }
}
.styled-select {
  border: none;
  border-radius: 14px;
  padding: 0.6rem 1.1rem;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(12px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
  color: inherit;
  font-size: 1.1rem;
  font-family: 'SF Mono', Consolas, monospace;
  min-height: 38px;
  margin-top: 0.2rem;
  margin-bottom: 0.2rem;
  transition: background 0.3s, color 0.3s;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
  box-sizing: border-box;
}
.styled-select:focus {
  background: #f4f4ff;
  outline: 2px solid #6c63ff;
}
.dark-mode .styled-select {
  background: rgba(30, 30, 40, 0.5);
  color: #f3f3f3;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
}
.dark-mode .styled-select:focus {
  background: #23263a;
  outline: 2px solid #6c63ff;
}
.triangle-input-large {
  min-height: 120px;
  font-size: 1.13rem;
  width: 100%;
  resize: vertical;
}
</style>