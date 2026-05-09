export class StockfishClient {
  constructor() {
    this.worker = null;
    this.ready = false;
    this.pendingBestMove = null;
    this.analysisHandler = null;
    this.boot();
  }

  boot() {
    this.worker = new Worker("./vendor/stockfish/stockfish.js#stockfish.wasm");
    this.worker.addEventListener("message", (event) => this.handleLine(String(event.data)));
    this.send("uci");
    this.send("isready");
  }

  handleLine(line) {
    if (line === "uciok" || line === "readyok") {
      this.ready = true;
    }

    if (this.analysisHandler && line.startsWith("info ")) {
      this.analysisHandler(line);
    }

    if (this.pendingBestMove && line.startsWith("bestmove ")) {
      const move = line.split(" ")[1];
      const resolve = this.pendingBestMove;
      this.pendingBestMove = null;
      resolve(move && move !== "(none)" ? move : null);
    }
  }

  send(command) {
    this.worker?.postMessage(command);
  }

  configure(level) {
    const skill = { easy: 3, medium: 10, hard: 18, extra: 20 }[level] ?? 10;
    this.send("setoption name Skill Level value " + skill);
    this.send("setoption name UCI_LimitStrength value " + (level === "hard" || level === "extra" ? "false" : "true"));
    if (level !== "hard" && level !== "extra") {
      const elo = { easy: 900, medium: 1450 }[level];
      this.send("setoption name UCI_Elo value " + elo);
    }
  }

  configureAnalysis() {
    this.send("setoption name UCI_AnalyseMode value true");
    this.send("setoption name UCI_LimitStrength value false");
    this.send("setoption name Skill Level value 20");
    this.send("setoption name MultiPV value 3");
  }

  bestMove(fen, level) {
    this.configure(level);
    this.send("stop");
    this.send("position fen " + fen);
    const search = {
      easy: "go movetime 220",
      medium: "go movetime 650",
      hard: "go depth 13",
      extra: "go depth 20"
    }[level] ?? "go movetime 650";

    return new Promise((resolve) => {
      this.pendingBestMove = resolve;
      this.send(search);
    });
  }

  startAnalysis(fen, onInfo) {
    this.send("stop");
    this.pendingBestMove = null;
    this.analysisHandler = onInfo;
    this.configureAnalysis();
    this.send("position fen " + fen);
    this.send("go depth 20");
  }

  stopAnalysis() {
    this.analysisHandler = null;
    this.send("stop");
  }
}
