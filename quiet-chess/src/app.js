import { Chess, DEFAULT_POSITION } from "../vendor/chess/chess.js";
import { StockfishClient } from "./engine.js";

const files = ["a", "b", "c", "d", "e", "f", "g", "h"];
const ranks = ["8", "7", "6", "5", "4", "3", "2", "1"];

const els = {
  appShell: document.querySelector(".app-shell"),
  board: document.querySelector("#board"),
  rankCoords: document.querySelector("#rankCoords"),
  fileCoords: document.querySelector("#fileCoords"),
  globalPlayBtn: document.querySelector("#globalPlayBtn"),
  globalAnalysisBtn: document.querySelector("#globalAnalysisBtn"),
  panels: [...document.querySelectorAll(".mode-panel")],
  statusPill: document.querySelector("#statusPill"),
  statusTitle: document.querySelector("#statusTitle"),
  statusDetail: document.querySelector("#statusDetail"),
  playBotModeBtn: document.querySelector("#playBotModeBtn"),
  playFriendModeBtn: document.querySelector("#playFriendModeBtn"),
  botOptions: [...document.querySelectorAll(".bot-option")],
  startGameBtn: document.querySelector("#startGameBtn"),
  gameModeText: document.querySelector("#gameModeText"),
  gameDetailText: document.querySelector("#gameDetailText"),
  sideSelect: document.querySelector("#sideSelect"),
  difficultySelect: document.querySelector("#difficultySelect"),
  clockSelect: document.querySelector("#clockSelect"),
  clockOption: document.querySelector(".clock-option"),
  whiteClock: document.querySelector("#whiteClock"),
  blackClock: document.querySelector("#blackClock"),
  autoFlipToggle: document.querySelector("#autoFlipToggle"),
  boardQuitBtn: document.querySelector("#boardQuitBtn"),
  flipBtn: document.querySelector("#flipBtn"),
  undoBtn: document.querySelector("#undoBtn"),
  quitBtn: document.querySelector("#quitBtn"),
  backBtn: document.querySelector("#backBtn"),
  forwardBtn: document.querySelector("#forwardBtn"),
  gameBackBtn: document.querySelector("#gameBackBtn"),
  gameForwardBtn: document.querySelector("#gameForwardBtn"),
  gameUndoBtn: document.querySelector("#gameUndoBtn"),
  cursorLabel: document.querySelector("#cursorLabel"),
  gameCursorLabel: document.querySelector("#gameCursorLabel"),
  moveList: document.querySelector("#moveList"),
  capturedWhite: document.querySelector("#capturedWhite"),
  capturedBlack: document.querySelector("#capturedBlack"),
  promotionDialog: document.querySelector("#promotionDialog"),
  freeAnalysisBtn: document.querySelector("#freeAnalysisBtn"),
  fenAnalysisBtn: document.querySelector("#fenAnalysisBtn"),
  pgnAnalysisBtn: document.querySelector("#pgnAnalysisBtn"),
  fenTools: document.querySelector("#fenTools"),
  fenInput: document.querySelector("#fenInput"),
  pgnTools: document.querySelector("#pgnTools"),
  pgnInput: document.querySelector("#pgnInput"),
  loadFenBtn: document.querySelector("#loadFenBtn"),
  loadPgnBtn: document.querySelector("#loadPgnBtn"),
  currentFenInput: document.querySelector("#currentFenInput"),
  copyFenBtn: document.querySelector("#copyFenBtn"),
  evalFill: document.querySelector("#evalFill"),
  evalText: document.querySelector("#evalText"),
  bestLine: document.querySelector("#bestLine")
};

const state = {
  chess: new Chess(),
  screen: "setup",
  gameType: null,
  setupGameType: "bot",
  orientation: "white",
  selected: null,
  legalMoves: [],
  locked: false,
  humanSide: "w",
  difficulty: "medium",
  clockInitial: 0,
  clocks: { w: 0, b: 0 },
  clockLastTick: null,
  timedOut: null,
  clockTimer: null,
  pendingPromotion: null,
  historyCursor: 0,
  analysisToken: 0,
  analysisFen: "",
  analysisActiveFen: "",
  analysisLines: new Map(),
  analysisTool: "free",
  analysis: createAnalysisState()
};

let moveEngine = null;
let analysisEngine = null;
let boardOrderKey = "";
let moveListRenderKey = "";
const squareEls = new Map();

function getMoveEngine() {
  moveEngine ||= new StockfishClient();
  return moveEngine;
}

function getAnalysisEngine() {
  analysisEngine ||= new StockfishClient();
  return analysisEngine;
}

function stopAnalysisEngine() {
  state.analysisActiveFen = "";
  analysisEngine?.stopAnalysis();
}

function resetMoveListCache() {
  moveListRenderKey = "";
}

const icons = {
  analysis: '<path d="M4 19V5"/><path d="M4 19h16"/><path d="m7 14 4-4 3 3 5-7"/>',
  bot: '<rect x="6" y="8" width="12" height="10" rx="2"/><path d="M12 8V4"/><path d="M8 13h.01"/><path d="M16 13h.01"/><path d="M9 20h6"/>',
  chevronLeft: '<path d="m15 18-6-6 6-6"/>',
  chevronRight: '<path d="m9 18 6-6-6-6"/>',
  copy: '<rect x="8" y="8" width="10" height="10" rx="2"/><path d="M6 16H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  flip: '<path d="M21 12a9 9 0 0 1-15.5 6.2"/><path d="M3 12A9 9 0 0 1 18.5 5.8"/><path d="M18 9V5h4"/><path d="M6 15v4H2"/>',
  friend: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  play: '<path d="m8 5 11 7-11 7Z"/>',
  quit: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  undo: '<path d="M9 14 4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 0 12h-2"/>',
  upload: '<path d="M12 3v12"/><path d="m7 8 5-5 5 5"/><path d="M5 21h14"/>'
};

function setButtonContent(button, label, iconName) {
  const icon = icons[iconName];
  if (!button || !icon) return;
  button.replaceChildren();

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "btn-icon");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  svg.innerHTML = icon;

  const span = document.createElement("span");
  span.className = "btn-label";
  span.textContent = label;
  button.append(svg, span);
}

function hydrateButtonIcons() {
  [
    [els.globalPlayBtn, "Play", "play"],
    [els.globalAnalysisBtn, "Analysis", "analysis"],
    [els.boardQuitBtn, "Quit", "quit"],
    [els.backBtn, "Back", "chevronLeft"],
    [els.forwardBtn, "Next", "chevronRight"],
    [els.flipBtn, "Flip", "flip"],
    [els.undoBtn, "Undo", "undo"],
    [els.playBotModeBtn, "Bot", "bot"],
    [els.playFriendModeBtn, "Friend", "friend"],
    [els.gameBackBtn, "Back", "chevronLeft"],
    [els.gameForwardBtn, "Next", "chevronRight"],
    [els.gameUndoBtn, "Undo", "undo"],
    [els.quitBtn, "Quit", "quit"],
    [els.freeAnalysisBtn, "Free", "analysis"],
    [els.fenAnalysisBtn, "FEN", "copy"],
    [els.pgnAnalysisBtn, "PGN", "upload"],
    [els.loadFenBtn, "Load", "upload"],
    [els.loadPgnBtn, "Load", "upload"],
    [els.copyFenBtn, "Copy", "copy"]
  ].forEach(([button, label, iconName]) => setButtonContent(button, label, iconName));
}

function orderedSquares() {
  const fileOrder = state.orientation === "white" ? files : [...files].reverse();
  const rankOrder = state.orientation === "white" ? ranks : [...ranks].reverse();
  return rankOrder.flatMap((rank) => fileOrder.map((file) => file + rank));
}

function initBoard() {
  ranks.forEach((rank) => {
    files.forEach((file) => {
      const square = file + rank;
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.square = square;
      squareEls.set(square, button);
    });
  });

  els.board.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;
    const square = event.target.closest(".square")?.dataset.square;
    if (square) onSquare(square);
  });
}

function liveHistory() {
  return state.chess.history({ verbose: true });
}

function createAnalysisState(mode = "free", rootFen = DEFAULT_POSITION) {
  const normalizedRoot = new Chess(rootFen).fen();
  const { turn, fullmove } = fenMeta(normalizedRoot);
  return {
    mode,
    rootFen: normalizedRoot,
    baseTurn: turn,
    baseFullmove: fullmove,
    mainline: [],
    mainlinePositions: [normalizedRoot],
    mainlineIndex: 0,
    branch: [],
    branchPositions: [normalizedRoot],
    branchIndex: 0,
    branchStartIndex: null,
    structureVersion: 0,
    pgnHeaders: {}
  };
}

function fenMeta(fen) {
  const parts = fen.split(/\s+/);
  return {
    turn: parts[1] || "w",
    fullmove: Number(parts[5] || 1)
  };
}

function moveDescriptor(move) {
  return {
    from: move.from,
    to: move.to,
    promotion: move.promotion || undefined,
    san: move.san
  };
}

function sameMove(a, b) {
  return Boolean(a && b && a.from === b.from && a.to === b.to && (a.promotion || "") === (b.promotion || ""));
}

function isPgnBranchActive() {
  return state.analysis.mode === "pgn" && state.analysis.branchStartIndex !== null;
}

function rebuildAnalysisPosition() {
  const analysis = state.analysis;
  const fen = analysis.mode === "pgn"
    ? (isPgnBranchActive()
      ? analysis.branchPositions[analysis.branchIndex] || analysis.mainlinePositions[analysis.branchStartIndex] || analysis.rootFen
      : analysis.mainlinePositions[analysis.mainlineIndex] || analysis.rootFen)
    : analysis.branchPositions[analysis.branchIndex] || analysis.rootFen;
  state.chess = new Chess(fen);
}

function analysisCanGoBack() {
  const analysis = state.analysis;
  if (analysis.mode === "pgn") {
    return analysis.branchIndex > 0 || analysis.mainlineIndex > 0;
  }
  return analysis.branchIndex > 0;
}

function analysisCanGoForward() {
  const analysis = state.analysis;
  if (analysis.mode === "pgn") {
    return isPgnBranchActive()
      ? analysis.branchIndex < analysis.branch.length
      : analysis.mainlineIndex < analysis.mainline.length;
  }
  return analysis.branchIndex < analysis.branch.length;
}

function isAtLivePosition() {
  return state.screen !== "game" || state.historyCursor === liveHistory().length;
}

function visibleChess() {
  if (state.screen !== "game" || isAtLivePosition()) return state.chess;

  const preview = new Chess();
  for (const move of liveHistory().slice(0, state.historyCursor)) {
    preview.move({ from: move.from, to: move.to, promotion: move.promotion });
  }
  return preview;
}

function visibleLastMove() {
  const history = state.screen === "game" ? liveHistory().slice(0, state.historyCursor) : liveHistory();
  const last = history.at(-1);
  return last ? { from: last.from, to: last.to } : null;
}

function renderBoard() {
  const boardChess = visibleChess();
  const lastMove = visibleLastMove();
  const legalTargets = new Map(state.legalMoves.map((move) => [move.to, move]));
  renderCoordinates();

  const squares = orderedSquares();
  const nextOrderKey = `${state.orientation}:${squares.join("")}`;
  if (nextOrderKey !== boardOrderKey) {
    els.board.replaceChildren(...squares.map((square) => squareEls.get(square)));
    boardOrderKey = nextOrderKey;
  }

  squares.forEach((square) => {
    const fileIndex = files.indexOf(square[0]);
    const rankIndex = ranks.indexOf(square[1]);
    const button = squareEls.get(square);
    const piece = boardChess.get(square);
    const legal = legalTargets.get(square);
    const pieceKey = piece ? `${piece.color}${piece.type}` : "";

    button.className = [
      "square",
      (fileIndex + rankIndex) % 2 === 0 ? "light" : "dark",
      state.selected === square ? "selected" : "",
      lastMove && (lastMove.from === square || lastMove.to === square) ? "last" : "",
      legal && piece ? "capture-target" : "",
      legal && !piece ? "target" : "",
      !isAtLivePosition() ? "readonly" : ""
    ].filter(Boolean).join(" ");
    button.setAttribute("aria-label", `${square}${piece ? " " + piece.color + piece.type : ""}`);

    if (button.dataset.pieceKey !== pieceKey) {
      button.replaceChildren();
      button.dataset.pieceKey = pieceKey;
    }

    if (piece && !button.firstChild) {
      const pieceEl = createPiece(piece);
      pieceEl.setAttribute("class", "piece " + (piece.color === "w" ? "white" : "black"));
      button.append(pieceEl);
    }
  });
}

function renderCoordinates() {
  const fileOrder = state.orientation === "white" ? files : [...files].reverse();
  const rankOrder = state.orientation === "white" ? ranks : [...ranks].reverse();
  els.rankCoords.replaceChildren(...rankOrder.map((rank) => {
    const span = document.createElement("span");
    span.textContent = rank;
    return span;
  }));
  els.fileCoords.replaceChildren(...fileOrder.map((file) => {
    const span = document.createElement("span");
    span.textContent = file;
    return span;
  }));
}

function resetPosition() {
  stopAnalysisEngine();
  stopClock();
  state.chess = new Chess();
  state.selected = null;
  state.legalMoves = [];
  state.locked = false;
  state.timedOut = null;
  state.clockLastTick = null;
  state.pendingPromotion = null;
  state.historyCursor = 0;
  state.analysisToken += 1;
  state.analysisFen = "";
  state.analysisActiveFen = "";
  state.analysisLines = new Map();
  state.analysisTool = "free";
  state.analysis = createAnalysisState();
  resetMoveListCache();
  resetEval();
}

function resetEval() {
  els.evalText.textContent = "Waiting";
  els.evalFill.style.height = "50%";
  els.bestLine.textContent = "Stockfish will analyze the current position.";
}

function showPanel(name) {
  els.panels.forEach((panel) => panel.classList.toggle("hidden", panel.dataset.panel !== name));
}

function renderShellState() {
  const gameFocus = state.screen === "game";
  els.appShell.classList.toggle("game-focus", gameFocus);
  els.appShell.classList.toggle("setup-screen", state.screen === "setup");
}

function setGlobalActive(screen) {
  els.globalPlayBtn.classList.toggle("active", screen !== "analysis");
  els.globalAnalysisBtn.classList.toggle("active", screen === "analysis");
  els.globalPlayBtn.disabled = screen !== "analysis";
  els.globalAnalysisBtn.disabled = screen === "analysis";
}

function enterSetup() {
  resetPosition();
  state.screen = "setup";
  state.gameType = null;
  state.orientation = "white";
  showPanel("setup");
  setGlobalActive("setup");
  renderShellState();
  renderSetupOptions();
  updateAll();
}

function startGame(type) {
  resetPosition();
  state.screen = "game";
  state.gameType = type;
  state.humanSide = els.sideSelect.value;
  state.difficulty = els.difficultySelect.value;
  state.clockInitial = type === "friend" ? Number(els.clockSelect.value) : 0;
  state.clocks = { w: state.clockInitial, b: state.clockInitial };
  state.orientation = type === "bot" && state.humanSide === "b" && !els.autoFlipToggle.checked ? "black" : "white";
  state.historyCursor = 0;
  els.gameModeText.textContent = type === "bot" ? "Bot" : "Friend";
  els.gameDetailText.textContent = gameDetailText(type);
  showPanel("game");
  setGlobalActive("game");
  renderShellState();
  updateAll();
  startClock();
  jumpToBoard();
  maybeBotMove();
}

function setSetupGameType(type) {
  state.setupGameType = type;
  renderSetupOptions();
}

function renderSetupOptions() {
  const isBot = state.setupGameType === "bot";
  els.playBotModeBtn.classList.toggle("active", isBot);
  els.playFriendModeBtn.classList.toggle("active", !isBot);
  els.playBotModeBtn.setAttribute("aria-pressed", String(isBot));
  els.playFriendModeBtn.setAttribute("aria-pressed", String(!isBot));
  els.botOptions.forEach((option) => {
    option.hidden = !isBot;
  });
  els.clockOption.hidden = isBot;
  setButtonContent(els.startGameBtn, isBot ? "Bot game" : "Friend game", "play");
}

function setAnalysisTool(tool) {
  state.analysisTool = tool;
  if (tool === "free") {
    stopAnalysisEngine();
    state.analysis = createAnalysisState();
    state.chess = new Chess(state.analysis.rootFen);
    resetMoveListCache();
    clearSelection(false);
    updateAll();
    return;
  }
  renderAnalysisTools();
  updateStatus();
}

function renderAnalysisTools() {
  const buttons = {
    free: els.freeAnalysisBtn,
    fen: els.fenAnalysisBtn,
    pgn: els.pgnAnalysisBtn
  };
  Object.entries(buttons).forEach(([tool, button]) => {
    const active = state.analysisTool === tool;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  els.fenTools.hidden = state.analysisTool !== "fen";
  els.pgnTools.hidden = state.analysisTool !== "pgn";
}

function jumpToBoard() {
  requestAnimationFrame(() => {
    if (state.screen === "game") {
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      requestAnimationFrame(() => {
        window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      });
      return;
    }
    els.board.scrollIntoView({ block: "start", inline: "nearest", behavior: "auto" });
  });
}

function gameDetailText(type) {
  if (type === "friend") {
    const clock = Number(els.clockSelect.value);
    const clockText = clock ? `${formatClockTime(clock)} clock` : "Untimed";
    return els.autoFlipToggle.checked ? `Local play, ${clockText}, auto-flip on` : `Local play, ${clockText}`;
  }

  const side = els.sideSelect.value === "w" ? "White" : "Black";
  const level = els.difficultySelect.options[els.difficultySelect.selectedIndex].textContent;
  return `${side} vs ${level}`;
}

function hasActiveClock() {
  return state.screen === "game" && state.gameType === "friend" && state.clockInitial > 0 && !state.timedOut;
}

function startClock() {
  stopClock();
  if (!hasActiveClock() || state.chess.isGameOver() || !isAtLivePosition()) {
    renderClocks();
    return;
  }
  state.clockLastTick = performance.now();
  state.clockTimer = window.setInterval(tickClock, 250);
  renderClocks();
}

function stopClock() {
  if (state.clockTimer) {
    window.clearInterval(state.clockTimer);
  }
  state.clockTimer = null;
  state.clockLastTick = null;
}

function tickClock() {
  if (!hasActiveClock() || state.chess.isGameOver() || !isAtLivePosition()) {
    stopClock();
    renderClocks();
    return;
  }

  const now = performance.now();
  const elapsed = state.clockLastTick ? (now - state.clockLastTick) / 1000 : 0;
  state.clockLastTick = now;

  const turn = state.chess.turn();
  state.clocks[turn] = Math.max(0, state.clocks[turn] - elapsed);
  if (state.clocks[turn] <= 0) {
    state.timedOut = turn;
    state.locked = true;
    clearSelection(false);
    stopClock();
    updateAll();
    return;
  }
  renderClocks();
}

function syncClockAfterPositionChange() {
  if (hasActiveClock() && !state.chess.isGameOver() && isAtLivePosition()) {
    startClock();
  } else {
    stopClock();
    renderClocks();
  }
}

function renderClocks() {
  const showClocks = state.screen === "game" && state.gameType === "friend" && state.clockInitial > 0;
  els.whiteClock.hidden = !showClocks;
  els.blackClock.hidden = !showClocks;
  if (!showClocks) {
    els.whiteClock.classList.remove("active", "flagged");
    els.blackClock.classList.remove("active", "flagged");
    return;
  }

  const topColor = state.orientation === "white" ? "b" : "w";
  const bottomColor = state.orientation === "white" ? "w" : "b";
  renderClockRail(els.blackClock, topColor);
  renderClockRail(els.whiteClock, bottomColor);
}

function renderClockRail(clockEl, color) {
  clockEl.querySelector(".mini-label").textContent = color === "w" ? "White" : "Black";
  clockEl.querySelector("strong").textContent = formatClockTime(state.clocks[color]);
  clockEl.classList.toggle("active", state.chess.turn() === color && !state.timedOut && isAtLivePosition());
  clockEl.classList.toggle("flagged", state.timedOut === color);
}

function formatClockTime(seconds) {
  const total = Math.max(0, Math.ceil(seconds));
  const minutes = Math.floor(total / 60);
  const remainingSeconds = total % 60;
  return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
}

function enterAnalysis() {
  resetPosition();
  state.screen = "analysis";
  state.gameType = null;
  state.orientation = "white";
  showPanel("analysis");
  setGlobalActive("analysis");
  renderShellState();
  renderAnalysisTools();
  updateAll();
}

function onSquare(square) {
  if (!canEditBoard()) return;

  const piece = state.chess.get(square);
  if (!state.selected) {
    selectSquare(square);
    return;
  }

  const move = state.legalMoves.find((candidate) => candidate.to === square);
  if (move) {
    maybeMove(move);
    return;
  }

  if (piece && piece.color === state.chess.turn()) {
    selectSquare(square);
    return;
  }

  clearSelection();
}

function canEditBoard() {
  if (state.locked || state.chess.isGameOver()) return false;
  if (state.screen === "setup") return false;
  if (state.screen === "game" && !isAtLivePosition()) return false;
  if (state.screen === "game" && state.gameType === "bot" && state.chess.turn() !== state.humanSide) return false;
  return true;
}

function selectSquare(square) {
  const piece = state.chess.get(square);
  if (!piece || piece.color !== state.chess.turn()) {
    clearSelection();
    return;
  }

  state.selected = square;
  state.legalMoves = state.chess.moves({ square, verbose: true });
  renderBoard();
}

function clearSelection(render = true) {
  state.selected = null;
  state.legalMoves = [];
  if (render) renderBoard();
}

function maybeMove(move) {
  if (move.flags.includes("p")) {
    state.pendingPromotion = move;
    els.promotionDialog.showModal();
    return;
  }
  makeMove({ from: move.from, to: move.to });
}

function makeMove(move) {
  if (state.screen === "analysis") {
    return makeAnalysisMove(move);
  }

  tickClock();
  if (state.timedOut) return null;
  const played = state.chess.move(move);
  if (!played) return null;

  state.historyCursor = liveHistory().length;
  clearSelection(false);

  if (state.screen === "game" && els.autoFlipToggle.checked) {
    flipBoard();
  }

  playMoveSound(played);
  updateAll();
  syncClockAfterPositionChange();
  maybeBotMove();
  return played;
}

function makeAnalysisMove(move) {
  stopAnalysisEngine();
  const played = state.chess.move(move);
  if (!played) return null;

  const descriptor = moveDescriptor(played);
  const analysis = state.analysis;

  if (analysis.mode === "pgn") {
    if (!isPgnBranchActive()) {
      const nextMainline = analysis.mainline[analysis.mainlineIndex];
      if (sameMove(descriptor, nextMainline)) {
        analysis.mainlineIndex += 1;
      } else {
        analysis.branchStartIndex = analysis.mainlineIndex;
        analysis.branch = [descriptor];
        analysis.branchPositions = [analysis.mainlinePositions[analysis.branchStartIndex] || analysis.rootFen, state.chess.fen()];
        analysis.branchIndex = 1;
        analysis.structureVersion += 1;
      }
    } else {
      if (analysis.branchIndex < analysis.branch.length) {
        analysis.branch = analysis.branch.slice(0, analysis.branchIndex);
        analysis.branchPositions = analysis.branchPositions.slice(0, analysis.branchIndex + 1);
        analysis.structureVersion += 1;
      }
      analysis.branch.push(descriptor);
      analysis.branchPositions.push(state.chess.fen());
      analysis.branchIndex = analysis.branch.length;
      analysis.structureVersion += 1;
    }
  } else {
    if (analysis.branchIndex < analysis.branch.length) {
      analysis.branch = analysis.branch.slice(0, analysis.branchIndex);
      analysis.branchPositions = analysis.branchPositions.slice(0, analysis.branchIndex + 1);
      analysis.structureVersion += 1;
    }
    analysis.branch.push(descriptor);
    analysis.branchPositions.push(state.chess.fen());
    analysis.branchIndex = analysis.branch.length;
    analysis.structureVersion += 1;
  }

  clearSelection(false);
  playMoveSound(played);
  updateAll();
  return played;
}

async function maybeBotMove() {
  if (
    state.screen !== "game" ||
    state.gameType !== "bot" ||
    state.chess.isGameOver() ||
    state.chess.turn() === state.humanSide ||
    state.locked ||
    !isAtLivePosition()
  ) {
    return;
  }

  state.locked = true;
  setStatus("Thinking", "Stockfish is choosing a move.", "Engine active");

  const move = await getMoveEngine().bestMove(state.chess.fen(), state.difficulty);
  if (state.screen === "game" && state.gameType === "bot" && move && !state.chess.isGameOver()) {
    const played = state.chess.move(parseUciMove(move));
    if (played) {
      state.historyCursor = liveHistory().length;
      if (els.autoFlipToggle.checked) {
        flipBoard();
      }
      playMoveSound(played);
    }
  }

  state.locked = false;
  updateAll();
}

function parseUciMove(uci) {
  return {
    from: uci.slice(0, 2),
    to: uci.slice(2, 4),
    promotion: uci[4]
  };
}

function updateAll() {
  renderBoard();
  renderMoves();
  renderCaptures();
  renderClocks();
  updateFen();
  updateButtons();
  updateStatus();
  if (state.screen === "analysis") {
    renderAnalysisTools();
    startAnalysis();
  }
}

function updateButtons() {
  const historyLength = liveHistory().length;
  const gameBrowsing = state.screen === "game";
  const canGoBack = state.screen === "analysis" ? analysisCanGoBack() : gameBrowsing && state.historyCursor > 0;
  const canGoForward = state.screen === "analysis" ? analysisCanGoForward() : gameBrowsing && state.historyCursor < historyLength;

  els.backBtn.disabled = !canGoBack || state.locked;
  els.forwardBtn.disabled = !canGoForward || state.locked;
  els.gameBackBtn.disabled = els.backBtn.disabled;
  els.gameForwardBtn.disabled = els.forwardBtn.disabled;
  els.flipBtn.disabled = state.locked;
  els.undoBtn.hidden = state.screen !== "game";
  els.undoBtn.disabled = state.screen !== "game" || historyLength === 0 || state.locked || !isAtLivePosition() || state.timedOut;
  els.gameUndoBtn.disabled = els.undoBtn.disabled;

  if (state.screen === "analysis") {
    els.cursorLabel.textContent = analysisCursorText();
  } else if (state.screen === "game") {
    els.cursorLabel.textContent = state.historyCursor === historyLength
      ? `Move ${historyLength}`
      : `Move ${state.historyCursor} / ${historyLength}`;
  } else {
    els.cursorLabel.textContent = "Start";
  }
  els.gameCursorLabel.textContent = els.cursorLabel.textContent;
}

function analysisCursorText() {
  const analysis = state.analysis;
  if (analysis.mode === "pgn") {
    if (isPgnBranchActive()) {
      return `Branch ${analysis.branchIndex}`;
    }
    return `PGN ${analysis.mainlineIndex} / ${analysis.mainline.length}`;
  }
  const label = analysis.mode === "fen" ? "FEN" : "Free";
  return analysis.branchIndex === analysis.branch.length
    ? `${label} ${analysis.branchIndex}`
    : `${label} ${analysis.branchIndex} / ${analysis.branch.length}`;
}

function updateStatus() {
  if (state.screen === "setup") {
    setStatus("Choose a game", "Start against Stockfish or play locally with a friend.", "New Game");
    return;
  }

  if (state.timedOut) {
    const loser = state.timedOut === "w" ? "White" : "Black";
    const winner = state.timedOut === "w" ? "Black" : "White";
    setStatus(`${winner} wins on time`, `${loser}'s clock reached zero.`, "Flag");
    return;
  }

  if (state.locked) return;

  if (state.screen === "game" && !isAtLivePosition()) {
    setStatus("Reviewing moves", "Use the arrows to return to the live position before playing.", "Read only");
    return;
  }

  const turn = state.chess.turn() === "w" ? "White" : "Black";
  if (state.chess.isCheckmate()) {
    setStatus("Checkmate", `${turn} is checkmated.`, "Game over");
  } else if (state.chess.isStalemate()) {
    setStatus("Stalemate", "No legal moves remain.", "Draw");
  } else if (state.chess.isDraw()) {
    setStatus("Draw", "The position is drawn.", "Game over");
  } else if (state.chess.isCheck()) {
    setStatus(`${turn} to move`, `${turn} is in check.`, "Check");
  } else if (state.screen === "analysis") {
    setAnalysisStatus(turn);
  } else if (state.gameType === "bot" && state.chess.turn() !== state.humanSide) {
    setStatus("Thinking", "Stockfish is choosing a move.", "Engine active");
  } else {
    setStatus(`${turn} to move`, "Choose a piece to see legal moves.", state.gameType === "friend" ? "Friend" : "Your turn");
  }
}

function setStatus(title, detail, pill) {
  els.statusTitle.textContent = title;
  els.statusDetail.textContent = detail;
  els.statusPill.textContent = pill;
}

function setAnalysisStatus(turn) {
  const analysis = state.analysis;
  if (analysisToolNeedsInput()) {
    const detail = state.analysisTool === "fen"
      ? "Paste a FEN to make it the root of this analysis board."
      : "Paste a PGN to review its mainline and explore temporary branches.";
    setStatus(`${turn} to move`, detail, state.analysisTool.toUpperCase());
    return;
  }

  if (analysis.mode === "pgn") {
    const detail = isPgnBranchActive()
      ? "Exploring a temporary branch. Back to the trunk discards it."
      : "Use arrows to review the uploaded game. Play a different move to branch.";
    setStatus(`${turn} to move`, detail, "PGN");
    return;
  }

  if (analysis.mode === "fen") {
    setStatus(`${turn} to move`, "Analyzing from the loaded position root.", "FEN");
    return;
  }

  setStatus(`${turn} to move`, "Free analysis from the starting position.", "Free");
}

function analysisToolNeedsInput() {
  return state.screen === "analysis" && state.analysisTool !== "free" && state.analysis.mode !== state.analysisTool;
}

function renderMoves() {
  if (state.screen === "analysis") {
    renderAnalysisMoves();
    return;
  }

  const history = liveHistory();
  els.moveList.replaceChildren(...history.map((move, index) => {
    const li = document.createElement("li");
    const number = Math.floor(index / 2) + 1;
    li.value = number;
    li.className = state.screen === "game" && index + 1 === state.historyCursor ? "current" : "";
    li.textContent = `${index % 2 === 0 ? number + "." : "..."} ${move.san}`;
    return li;
  }));
  els.moveList.scrollTop = els.moveList.scrollHeight;
}

function renderAnalysisMoves() {
  const analysis = state.analysis;
  const key = analysisMoveStructureKey();

  if (key !== moveListRenderKey) {
    const items = [];

    if (analysis.mode === "pgn") {
      analysis.mainline.forEach((move, index) => {
        items.push(createMoveListItem(move, index, analysis.baseTurn, analysis.baseFullmove, "mainline", index));
      });

      if (isPgnBranchActive()) {
        const branchStart = document.createElement("li");
        branchStart.className = "branch-label";
        branchStart.textContent = `Branch from ${analysisPlyLabel(analysis.branchStartIndex)}`;
        items.push(branchStart);
        analysis.branch.forEach((move, index) => {
          const li = createMoveListItem(move, analysis.branchStartIndex + index, analysis.baseTurn, analysis.baseFullmove, "branch", index);
          li.classList.add("branch-move");
          items.push(li);
        });
      }
    } else {
      analysis.branch.forEach((move, index) => {
        items.push(createMoveListItem(move, index, analysis.baseTurn, analysis.baseFullmove, "branch", index));
      });
    }

    els.moveList.replaceChildren(...items);
    moveListRenderKey = key;
  }

  updateAnalysisMoveClasses();
}

function analysisMoveStructureKey() {
  const analysis = state.analysis;
  return [
    "analysis",
    analysis.mode,
    analysis.structureVersion,
    isPgnBranchActive() ? analysis.branchStartIndex : "trunk"
  ].join(":");
}

function updateAnalysisMoveClasses() {
  const analysis = state.analysis;
  els.moveList.querySelectorAll("li[data-role]").forEach((li) => {
    const index = Number(li.dataset.index);
    const role = li.dataset.role;
    const current = role === "mainline"
      ? !isPgnBranchActive() && index + 1 === analysis.mainlineIndex
      : index + 1 === analysis.branchIndex;
    const future = role === "mainline"
      ? !isPgnBranchActive() && index >= analysis.mainlineIndex
      : index >= analysis.branchIndex;
    li.classList.toggle("current", current);
    li.classList.toggle("future-move", future);
  });
}

function createMoveListItem(move, index, baseTurn, baseFullmove, role = "", roleIndex = index) {
  const li = document.createElement("li");
  li.value = baseFullmove + Math.floor(index / 2);
  li.textContent = `${moveNumberLabel(index, baseTurn, baseFullmove)} ${move.san || move.to}`;
  if (role) {
    li.dataset.role = role;
    li.dataset.index = String(roleIndex);
  }
  return li;
}

function moveNumberLabel(index, baseTurn, baseFullmove) {
  const ply = (baseTurn === "b" ? 1 : 0) + index;
  const fullmove = baseFullmove + Math.floor(ply / 2);
  return ply % 2 === 0 ? `${fullmove}.` : `${fullmove}...`;
}

function analysisPlyLabel(index) {
  if (index === 0) return "root";
  return `PGN ${index}`;
}

function renderCaptures() {
  const captures = { w: [], b: [] };
  const history = state.screen === "game" ? liveHistory().slice(0, state.historyCursor) : liveHistory();
  for (const move of history) {
    if (move.captured) {
      captures[move.color].push(move.captured);
    }
  }
  els.capturedWhite.replaceChildren(...captures.w.map((piece) => createCapturedPiece("b", piece)));
  els.capturedBlack.replaceChildren(...captures.b.map((piece) => createCapturedPiece("w", piece)));
}

function updateFen() {
  els.currentFenInput.value = state.chess.fen();
  if (state.screen === "analysis" && state.analysisTool === "fen" && document.activeElement !== els.fenInput && !els.fenInput.value.trim()) {
    els.fenInput.value = state.chess.fen();
  }
}

function flipBoard() {
  state.orientation = state.orientation === "white" ? "black" : "white";
  renderBoard();
  renderClocks();
}

function undo() {
  if (state.screen !== "game" || state.locked || !isAtLivePosition()) return;
  stopAnalysisEngine();
  stopClock();

  if (state.gameType === "bot") {
    state.chess.undo();
    if (state.chess.turn() !== state.humanSide) {
      state.chess.undo();
    }
  } else {
    state.chess.undo();
  }

  state.historyCursor = liveHistory().length;
  clearSelection(false);
  updateAll();
  syncClockAfterPositionChange();
}

function navigateBack() {
  if (state.locked) return;

  if (state.screen === "analysis") {
    navigateAnalysisBack();
    return;
  }

  if (state.screen !== "game" || state.historyCursor <= 0) return;
  stopClock();
  state.historyCursor -= 1;
  clearSelection(false);
  updateAll();
}

function navigateForward() {
  if (state.locked) return;

  if (state.screen === "analysis") {
    navigateAnalysisForward();
    return;
  }

  const historyLength = liveHistory().length;
  if (state.screen !== "game" || state.historyCursor >= historyLength) return;
  state.historyCursor += 1;
  clearSelection(false);
  updateAll();
  syncClockAfterPositionChange();
}

function navigateAnalysisBack() {
  if (!analysisCanGoBack()) return;
  stopAnalysisEngine();
  const analysis = state.analysis;

  if (analysis.mode === "pgn") {
    if (analysis.branchIndex > 0) {
      analysis.branchIndex -= 1;
      if (analysis.branchIndex === 0) {
        analysis.branch = [];
        analysis.branchPositions = [analysis.mainlinePositions[analysis.branchStartIndex] || analysis.rootFen];
        analysis.branchStartIndex = null;
        analysis.structureVersion += 1;
      }
    } else {
      analysis.mainlineIndex -= 1;
    }
  } else {
    analysis.branchIndex -= 1;
  }

  rebuildAnalysisPosition();
  clearSelection(false);
  updateAll();
}

function navigateAnalysisForward() {
  if (!analysisCanGoForward()) return;
  stopAnalysisEngine();
  const analysis = state.analysis;
  let played = null;

  if (analysis.mode === "pgn") {
    if (isPgnBranchActive()) {
      const next = analysis.branch[analysis.branchIndex];
      analysis.branchIndex += 1;
      played = next;
    } else {
      const next = analysis.mainline[analysis.mainlineIndex];
      analysis.mainlineIndex += 1;
      played = next;
    }
  } else {
    const next = analysis.branch[analysis.branchIndex];
    analysis.branchIndex += 1;
    played = next;
  }

  rebuildAnalysisPosition();
  if (played) playMoveSound(played);
  clearSelection(false);
  updateAll();
}

function loadFen() {
  if (state.screen !== "analysis") return;
  const fen = els.fenInput.value.trim();
  try {
    stopAnalysisEngine();
    state.analysis = createAnalysisState("fen", fen);
    state.analysisTool = "fen";
    state.chess = new Chess(state.analysis.rootFen);
    resetMoveListCache();
    clearSelection(false);
    updateAll();
    setStatus("FEN loaded", "This position is now the root of analysis.", "FEN");
  } catch {
    setStatus("FEN not loaded", "That FEN is not valid.", "Check input");
  }
}

function loadPgn() {
  if (state.screen !== "analysis") return;
  const pgn = els.pgnInput.value.trim();
  if (!pgn) {
    setStatus("PGN not loaded", "Paste a PGN before loading.", "Check input");
    return;
  }

  try {
    stopAnalysisEngine();
    const parsed = new Chess();
    parsed.loadPgn(pgn, { strict: false });
    const history = parsed.history({ verbose: true });
    const headers = typeof parsed.getHeaders === "function" ? parsed.getHeaders() : parsed.header();
    const rootFen = history[0]?.before || headers.FEN || DEFAULT_POSITION;
    const analysis = createAnalysisState("pgn", rootFen);
    analysis.mainline = history.map(moveDescriptor);
    analysis.mainlinePositions = [analysis.rootFen];
    const replay = new Chess(analysis.rootFen);
    for (const move of analysis.mainline) {
      replay.move(move);
      analysis.mainlinePositions.push(replay.fen());
    }
    analysis.branchPositions = [analysis.rootFen];
    analysis.structureVersion += 1;
    analysis.pgnHeaders = headers;
    state.analysis = analysis;
    state.analysisTool = "pgn";
    resetMoveListCache();
    rebuildAnalysisPosition();
    clearSelection(false);
    updateAll();
    setStatus("PGN loaded", `${history.length} moves ready for review.`, "PGN");
  } catch {
    setStatus("PGN not loaded", "That PGN could not be parsed.", "Check input");
  }
}

async function copyFen() {
  await navigator.clipboard.writeText(state.chess.fen());
  setStatus("FEN copied", "Current position copied to clipboard.", "Copied");
}

function startAnalysis() {
  const fen = state.chess.fen();
  if (state.analysisActiveFen === fen) return;

  const token = ++state.analysisToken;
  const sideToMove = state.chess.turn();
  state.analysisActiveFen = fen;
  state.analysisFen = fen;
  state.analysisLines = new Map();
  els.evalText.textContent = "Analyzing";
  els.evalFill.style.height = "50%";
  renderEngineLines();

  getAnalysisEngine().startAnalysis(fen, (line) => {
    if (token !== state.analysisToken) return;
    const parsed = parseInfo(line, sideToMove, fen);
    if (!parsed) return;
    state.analysisLines.set(parsed.multipv, parsed);
    renderEval(state.analysisLines.get(1) || parsed);
    renderEngineLines();
    updateButtons();
  });
}

function parseInfo(line, sideToMove, fen) {
  const depth = line.match(/\bdepth (\d+)/)?.[1];
  const multipv = line.match(/\bmultipv (\d+)/)?.[1] || "1";
  const cp = line.match(/\bscore cp (-?\d+)/)?.[1];
  const mate = line.match(/\bscore mate (-?\d+)/)?.[1];
  const pv = line.match(/\bpv (.+)$/)?.[1];
  if (!depth || (!cp && !mate)) return null;

  const sign = sideToMove === "w" ? 1 : -1;
  return {
    depth: Number(depth),
    multipv: Number(multipv),
    fen,
    cp: cp === undefined ? null : Number(cp) * sign,
    mate: mate === undefined ? null : Number(mate) * sign,
    pv: pv ? pv.split(" ").slice(0, 8) : []
  };
}

function renderEval(info) {
  if (info.mate !== null) {
    els.evalText.textContent = formatEval(info);
    els.evalFill.style.height = info.mate > 0 ? "96%" : "4%";
  } else {
    const pawns = info.cp / 100;
    const percent = Math.max(6, Math.min(94, 50 + pawns * 8));
    els.evalText.textContent = formatEval(info);
    els.evalFill.style.height = `${percent}%`;
  }
}

function renderEngineLines() {
  const lines = [...state.analysisLines.values()].sort((a, b) => a.multipv - b.multipv).slice(0, 3);
  if (!lines.length) {
    els.bestLine.textContent = "Stockfish is reading the position. Early depths can be noisy.";
    return;
  }

  els.bestLine.replaceChildren(...lines.map((line) => {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "engine-line";
    row.disabled = true;

    const rank = document.createElement("span");
    rank.className = "engine-rank";
    rank.textContent = String(line.multipv);

    const evalEl = document.createElement("span");
    evalEl.className = "engine-eval";
    evalEl.textContent = formatEval(line);

    const moves = document.createElement("span");
    moves.className = "engine-pv";
    moves.textContent = formatPv(line.pv, line.fen);

    const depth = document.createElement("span");
    depth.className = "engine-depth";
    depth.textContent = `${line.depth < 12 ? "prelim" : "d"}${line.depth}`;

    row.append(rank, evalEl, moves, depth);
    return row;
  }));
}

function formatEval(info) {
  if (info.mate !== null) {
    const sign = info.mate > 0 ? "+" : "-";
    return `${sign}M${Math.abs(info.mate)}`;
  }
  const pawns = info.cp / 100;
  return `${pawns > 0 ? "+" : ""}${pawns.toFixed(2)}`;
}

function formatPv(pv, fen = state.analysisFen) {
  if (!pv.length) return "No line yet";
  const preview = new Chess(fen);
  const sanMoves = [];

  for (const uci of pv) {
    let played = null;
    try {
      played = preview.move(parseUciMove(uci));
    } catch {
      break;
    }
    if (!played) break;
    sanMoves.push(played.san);
  }

  return sanMoves.join(" ");
}

function createPiece(piece) {
  const image = document.createElement("img");
  const colorPrefix = piece.color === "w" ? "l" : "d";
  image.src = `./assets/pieces/cburnett/${colorPrefix}${piece.type}.svg`;
  image.alt = "";
  image.decoding = "async";
  image.draggable = false;
  image.dataset.type = piece.type;
  return image;
}

const soundFiles = {
  move: "./assets/sounds/move-thud.wav",
  capture: "./assets/sounds/capture-thud.wav",
  checkmate: "./assets/sounds/checkmate-thud.wav"
};
const soundVolumes = {
  move: 0.92,
  capture: 0.92,
  checkmate: 0.94
};
const soundPools = new Map();
let audioPrimed = false;
let lastSoundAt = 0;

function initSoundPools() {
  if (soundPools.size) return;
  Object.entries(soundFiles).forEach(([name, src]) => {
    const pool = Array.from({ length: 4 }, () => {
      const audio = new Audio(src);
      audio.preload = "auto";
      audio.volume = soundVolumes[name] ?? 0.9;
      audio.load();
      return audio;
    });
    soundPools.set(name, pool);
  });
}

function playMoveSound(move) {
  if (state.chess.isCheckmate()) {
    playSound("checkmate");
  } else if (move.captured) {
    playSound("capture");
  } else {
    playSound("move");
  }
}

function unlockMoveAudio() {
  if (audioPrimed) return;
  audioPrimed = true;
  initSoundPools();
  const firstMoveSound = soundPools.get("move")?.[0];
  if (!firstMoveSound) return;
  firstMoveSound.volume = 0;
  firstMoveSound.play()
    .then(() => {
      firstMoveSound.pause();
      firstMoveSound.currentTime = 0;
      firstMoveSound.volume = soundVolumes.move;
    })
    .catch(() => {
      firstMoveSound.volume = soundVolumes.move;
    });
}

function playSound(name) {
  initSoundPools();
  const now = performance.now();
  if (now - lastSoundAt < 45) return;
  const pool = soundPools.get(name);
  if (!pool) return;
  const audio = pool.find((candidate) => candidate.paused || candidate.ended) || pool[0];
  audio.pause();
  audio.currentTime = 0;
  audio.volume = soundVolumes[name] ?? 0.9;
  audio.play().catch(() => {});
  lastSoundAt = now;
}

function createCapturedPiece(color, type) {
  const span = document.createElement("span");
  span.className = "captured-piece";
  const icon = createPiece({ color, type });
  icon.setAttribute("class", "piece " + (color === "w" ? "white" : "black"));
  span.append(icon);
  return span;
}

els.globalPlayBtn.addEventListener("click", () => {
  if (state.screen === "analysis") enterSetup();
});
window.addEventListener("pointerdown", unlockMoveAudio, { once: true, passive: true });
window.addEventListener("touchstart", unlockMoveAudio, { once: true, passive: true });
els.globalAnalysisBtn.addEventListener("click", enterAnalysis);
els.freeAnalysisBtn.addEventListener("click", () => setAnalysisTool("free"));
els.fenAnalysisBtn.addEventListener("click", () => setAnalysisTool("fen"));
els.pgnAnalysisBtn.addEventListener("click", () => setAnalysisTool("pgn"));
els.playBotModeBtn.addEventListener("click", () => setSetupGameType("bot"));
els.playFriendModeBtn.addEventListener("click", () => setSetupGameType("friend"));
els.startGameBtn.addEventListener("click", () => startGame(state.setupGameType));
els.sideSelect.addEventListener("change", () => {
  state.humanSide = els.sideSelect.value;
  if (state.screen === "game" && state.gameType === "bot") {
    startGame("bot");
  }
});
els.difficultySelect.addEventListener("change", () => {
  state.difficulty = els.difficultySelect.value;
});
els.flipBtn.addEventListener("click", flipBoard);
els.undoBtn.addEventListener("click", undo);
els.gameUndoBtn.addEventListener("click", undo);
els.quitBtn.addEventListener("click", enterSetup);
els.boardQuitBtn.addEventListener("click", enterSetup);
els.backBtn.addEventListener("click", navigateBack);
els.forwardBtn.addEventListener("click", navigateForward);
els.gameBackBtn.addEventListener("click", navigateBack);
els.gameForwardBtn.addEventListener("click", navigateForward);
els.loadFenBtn.addEventListener("click", loadFen);
els.loadPgnBtn.addEventListener("click", loadPgn);
els.copyFenBtn.addEventListener("click", copyFen);
els.promotionDialog.addEventListener("close", () => {
  if (!state.pendingPromotion || !els.promotionDialog.returnValue) {
    state.pendingPromotion = null;
    return;
  }
  const move = state.pendingPromotion;
  state.pendingPromotion = null;
  makeMove({ from: move.from, to: move.to, promotion: els.promotionDialog.returnValue });
  els.promotionDialog.returnValue = "";
});
window.addEventListener("keydown", (event) => {
  if (
    event.target instanceof HTMLInputElement ||
    event.target instanceof HTMLSelectElement ||
    event.target instanceof HTMLTextAreaElement
  ) return;
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    navigateBack();
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    navigateForward();
  }
});

initBoard();
hydrateButtonIcons();
enterSetup();
