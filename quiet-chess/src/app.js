import { Chess } from "../vendor/chess/chess.js";
import { StockfishClient } from "./engine.js";

const files = ["a", "b", "c", "d", "e", "f", "g", "h"];
const ranks = ["8", "7", "6", "5", "4", "3", "2", "1"];

const els = {
  board: document.querySelector("#board"),
  rankCoords: document.querySelector("#rankCoords"),
  fileCoords: document.querySelector("#fileCoords"),
  globalPlayBtn: document.querySelector("#globalPlayBtn"),
  globalAnalysisBtn: document.querySelector("#globalAnalysisBtn"),
  panels: [...document.querySelectorAll(".mode-panel")],
  statusPill: document.querySelector("#statusPill"),
  statusTitle: document.querySelector("#statusTitle"),
  statusDetail: document.querySelector("#statusDetail"),
  startBotBtn: document.querySelector("#startBotBtn"),
  startFriendBtn: document.querySelector("#startFriendBtn"),
  gameModeText: document.querySelector("#gameModeText"),
  gameDetailText: document.querySelector("#gameDetailText"),
  sideSelect: document.querySelector("#sideSelect"),
  difficultySelect: document.querySelector("#difficultySelect"),
  autoFlipToggle: document.querySelector("#autoFlipToggle"),
  flipBtn: document.querySelector("#flipBtn"),
  undoBtn: document.querySelector("#undoBtn"),
  quitBtn: document.querySelector("#quitBtn"),
  backBtn: document.querySelector("#backBtn"),
  forwardBtn: document.querySelector("#forwardBtn"),
  cursorLabel: document.querySelector("#cursorLabel"),
  moveList: document.querySelector("#moveList"),
  capturedWhite: document.querySelector("#capturedWhite"),
  capturedBlack: document.querySelector("#capturedBlack"),
  promotionDialog: document.querySelector("#promotionDialog"),
  fenInput: document.querySelector("#fenInput"),
  loadFenBtn: document.querySelector("#loadFenBtn"),
  copyFenBtn: document.querySelector("#copyFenBtn"),
  evalFill: document.querySelector("#evalFill"),
  evalText: document.querySelector("#evalText"),
  bestLine: document.querySelector("#bestLine")
};

const state = {
  chess: new Chess(),
  screen: "setup",
  gameType: null,
  orientation: "white",
  selected: null,
  legalMoves: [],
  locked: false,
  humanSide: "w",
  difficulty: "medium",
  pendingPromotion: null,
  historyCursor: 0,
  analysisToken: 0,
  analysisFen: "",
  analysisLines: new Map(),
  analysisRedo: []
};

const moveEngine = new StockfishClient();
const analysisEngine = new StockfishClient();

function orderedSquares() {
  const fileOrder = state.orientation === "white" ? files : [...files].reverse();
  const rankOrder = state.orientation === "white" ? ranks : [...ranks].reverse();
  return rankOrder.flatMap((rank) => fileOrder.map((file) => file + rank));
}

function liveHistory() {
  return state.chess.history({ verbose: true });
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

  els.board.replaceChildren(...orderedSquares().map((square) => {
    const fileIndex = files.indexOf(square[0]);
    const rankIndex = ranks.indexOf(square[1]);
    const button = document.createElement("button");
    const piece = boardChess.get(square);
    const legal = legalTargets.get(square);

    button.type = "button";
    button.className = [
      "square",
      (fileIndex + rankIndex) % 2 === 0 ? "light" : "dark",
      state.selected === square ? "selected" : "",
      lastMove && (lastMove.from === square || lastMove.to === square) ? "last" : "",
      legal && piece ? "capture-target" : "",
      legal && !piece ? "target" : "",
      !isAtLivePosition() ? "readonly" : ""
    ].filter(Boolean).join(" ");
    button.dataset.square = square;
    button.setAttribute("aria-label", `${square}${piece ? " " + piece.color + piece.type : ""}`);

    if (piece) {
      const pieceEl = createPiece(piece);
      pieceEl.setAttribute("class", "piece " + (piece.color === "w" ? "white" : "black"));
      button.append(pieceEl);
    }

    button.addEventListener("click", () => onSquare(square));
    return button;
  }));
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
  analysisEngine.stopAnalysis();
  state.chess = new Chess();
  state.selected = null;
  state.legalMoves = [];
  state.locked = false;
  state.pendingPromotion = null;
  state.historyCursor = 0;
  state.analysisToken += 1;
  state.analysisFen = "";
  state.analysisLines = new Map();
  state.analysisRedo = [];
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
  updateAll();
}

function startGame(type) {
  resetPosition();
  state.screen = "game";
  state.gameType = type;
  state.humanSide = els.sideSelect.value;
  state.difficulty = els.difficultySelect.value;
  state.orientation = type === "bot" && state.humanSide === "b" ? "black" : "white";
  state.historyCursor = 0;
  els.gameModeText.textContent = type === "bot" ? "Bot" : "Friend";
  els.gameDetailText.textContent = gameDetailText(type);
  showPanel("game");
  setGlobalActive("game");
  updateAll();
  maybeBotMove();
}

function gameDetailText(type) {
  if (type === "friend") {
    return els.autoFlipToggle.checked ? "Local play, auto-flip on" : "Local play";
  }

  const side = els.sideSelect.value === "w" ? "White" : "Black";
  const level = els.difficultySelect.options[els.difficultySelect.selectedIndex].textContent;
  return `${side} vs ${level}`;
}

function enterAnalysis() {
  resetPosition();
  state.screen = "analysis";
  state.gameType = null;
  state.orientation = "white";
  showPanel("analysis");
  setGlobalActive("analysis");
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

function clearSelection() {
  state.selected = null;
  state.legalMoves = [];
  renderBoard();
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
  const played = state.chess.move(move);
  if (!played) return null;

  state.historyCursor = liveHistory().length;
  if (state.screen === "analysis") {
    state.analysisRedo = [];
  }
  clearSelection();

  if (state.screen === "game" && state.gameType === "friend" && els.autoFlipToggle.checked) {
    flipBoard();
  }

  playMoveSound(played);
  updateAll();
  maybeBotMove();
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

  const move = await moveEngine.bestMove(state.chess.fen(), state.difficulty);
  if (state.screen === "game" && state.gameType === "bot" && move && !state.chess.isGameOver()) {
    const played = state.chess.move(parseUciMove(move));
    if (played) {
      state.historyCursor = liveHistory().length;
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
  updateFen();
  updateButtons();
  updateStatus();
  if (state.screen === "analysis") {
    startAnalysis();
  }
}

function updateButtons() {
  const historyLength = liveHistory().length;
  const gameBrowsing = state.screen === "game";
  const canGoBack = state.screen === "analysis" ? historyLength > 0 : gameBrowsing && state.historyCursor > 0;
  const canGoForward = state.screen === "analysis" ? state.analysisRedo.length > 0 : gameBrowsing && state.historyCursor < historyLength;

  els.backBtn.disabled = !canGoBack || state.locked;
  els.forwardBtn.disabled = !canGoForward || state.locked;
  els.flipBtn.disabled = state.locked;
  els.undoBtn.hidden = state.screen !== "game";
  els.undoBtn.disabled = state.screen !== "game" || historyLength === 0 || state.locked || !isAtLivePosition();

  if (state.screen === "analysis") {
    els.cursorLabel.textContent = state.analysisRedo.length ? `Redo ${state.analysisRedo.length}` : "Explore";
  } else if (state.screen === "game") {
    els.cursorLabel.textContent = state.historyCursor === historyLength
      ? `Move ${historyLength}`
      : `Move ${state.historyCursor} / ${historyLength}`;
  } else {
    els.cursorLabel.textContent = "Start";
  }
}

function updateStatus() {
  if (state.locked) return;

  if (state.screen === "setup") {
    setStatus("Choose a game", "Start against Stockfish or play locally with a friend.", "New Game");
    return;
  }

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
    setStatus(`${turn} to move`, "", "Analysis");
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

function renderMoves() {
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
  els.fenInput.value = state.chess.fen();
}

function flipBoard() {
  state.orientation = state.orientation === "white" ? "black" : "white";
  renderBoard();
}

function undo() {
  if (state.screen !== "game" || state.locked || !isAtLivePosition()) return;
  analysisEngine.stopAnalysis();

  if (state.gameType === "bot") {
    state.chess.undo();
    if (state.chess.turn() !== state.humanSide) {
      state.chess.undo();
    }
  } else {
    state.chess.undo();
  }

  state.historyCursor = liveHistory().length;
  clearSelection();
  updateAll();
}

function navigateBack() {
  if (state.locked) return;

  if (state.screen === "analysis") {
    analysisEngine.stopAnalysis();
    const undone = state.chess.undo();
    if (undone) {
      state.analysisRedo.unshift({ from: undone.from, to: undone.to, promotion: undone.promotion });
    }
    clearSelection();
    updateAll();
    return;
  }

  if (state.screen !== "game" || state.historyCursor <= 0) return;
  state.historyCursor -= 1;
  clearSelection();
  updateAll();
}

function navigateForward() {
  if (state.locked) return;

  if (state.screen === "analysis") {
    const next = state.analysisRedo[0];
    if (!next) return;
    state.analysisRedo = state.analysisRedo.slice(1);
    const played = state.chess.move(next);
    if (played) {
      state.historyCursor = liveHistory().length;
      playMoveSound(played);
      clearSelection();
      updateAll();
    }
    return;
  }

  const historyLength = liveHistory().length;
  if (state.screen !== "game" || state.historyCursor >= historyLength) return;
  state.historyCursor += 1;
  clearSelection();
  updateAll();
}

function loadFen() {
  if (state.screen !== "analysis") return;
  const fen = els.fenInput.value.trim();
  try {
    analysisEngine.stopAnalysis();
    state.chess.load(fen);
    state.selected = null;
    state.legalMoves = [];
    state.analysisRedo = [];
    state.historyCursor = liveHistory().length;
    updateAll();
  } catch {
    setStatus("FEN not loaded", "That FEN is not valid.", "Check input");
  }
}

async function copyFen() {
  await navigator.clipboard.writeText(state.chess.fen());
  setStatus("FEN copied", "Current position copied to clipboard.", "Copied");
}

function startAnalysis() {
  const token = ++state.analysisToken;
  const sideToMove = state.chess.turn();
  const fen = state.chess.fen();
  state.analysisFen = fen;
  state.analysisLines = new Map();
  els.evalText.textContent = "Analyzing";
  els.evalFill.style.height = "50%";
  renderEngineLines();

  analysisEngine.startAnalysis(fen, (line) => {
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

let audioContext = null;
let audioMaster = null;

function getAudioContext() {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return null;
  if (!audioContext) {
    audioContext = new AudioContextClass();
    audioMaster = audioContext.createDynamicsCompressor();
    audioMaster.threshold.setValueAtTime(-12, audioContext.currentTime);
    audioMaster.knee.setValueAtTime(16, audioContext.currentTime);
    audioMaster.ratio.setValueAtTime(8, audioContext.currentTime);
    audioMaster.attack.setValueAtTime(0.002, audioContext.currentTime);
    audioMaster.release.setValueAtTime(0.08, audioContext.currentTime);
    audioMaster.connect(audioContext.destination);
  }
  return audioContext;
}

function playMoveSound(move) {
  const context = getAudioContext();
  if (!context) return;
  if (context.state === "suspended") {
    context.resume().catch(() => {});
  }

  if (state.chess.isCheckmate()) {
    playCheckmateSound(context);
  } else if (move.captured) {
    playTap(context, 155, 0.07, 0, 0.42);
    playTap(context, 95, 0.065, 0.065, 0.34);
  } else {
    playTap(context, 140, 0.07, 0, 0.38);
  }
}

function playTap(context, frequency, duration, delay, volume = 0.38) {
  const start = context.currentTime + delay;
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  oscillator.type = "triangle";
  oscillator.frequency.setValueAtTime(frequency, start);
  gain.gain.setValueAtTime(0.0001, start);
  gain.gain.exponentialRampToValueAtTime(volume, start + 0.006);
  gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
  oscillator.connect(gain);
  gain.connect(audioMaster || context.destination);
  oscillator.start(start);
  oscillator.stop(start + duration + 0.01);
}

function playCheckmateSound(context) {
  playTap(context, 196, 0.085, 0, 0.46);
  playTap(context, 146.8, 0.095, 0.09, 0.4);
  playTap(context, 98, 0.13, 0.2, 0.5);
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
els.globalAnalysisBtn.addEventListener("click", enterAnalysis);
els.startBotBtn.addEventListener("click", () => startGame("bot"));
els.startFriendBtn.addEventListener("click", () => startGame("friend"));
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
els.quitBtn.addEventListener("click", enterSetup);
els.backBtn.addEventListener("click", navigateBack);
els.forwardBtn.addEventListener("click", navigateForward);
els.loadFenBtn.addEventListener("click", loadFen);
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
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLSelectElement) return;
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    navigateBack();
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    navigateForward();
  }
});

enterSetup();
