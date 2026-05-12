export class StockfishClient {
  constructor() {
    this.worker = null;
    this.ready = false;
    this.resolveReady = null;
    this.readyPromise = new Promise((resolve) => {
      this.resolveReady = resolve;
    });
    this.pendingBestMove = null;
    this.analysisHandler = null;
    this.analysisRunId = 0;
    this.boot();
  }

  boot() {
    this.worker = new Worker("./vendor/stockfish/stockfish.js#stockfish.wasm");
    this.worker.addEventListener("message", (event) => this.handleLine(String(event.data)));
    this.send("uci");
    this.send("isready");
  }

  handleLine(line) {
    if (line === "readyok") {
      this.ready = true;
      this.resolveReady?.();
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

  async ensureReady() {
    if (!this.ready) {
      await this.readyPromise;
    }
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

  async bestMove(fen, level) {
    await this.ensureReady();
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
    const runId = ++this.analysisRunId;
    this.pendingBestMove = null;
    this.analysisHandler = onInfo;
    this.send("stop");
    this.ensureReady().then(() => {
      if (runId !== this.analysisRunId || this.analysisHandler !== onInfo) return;
      this.configureAnalysis();
      this.send("position fen " + fen);
      this.send("go depth 20");
    });
  }

  stopAnalysis() {
    this.analysisRunId += 1;
    this.analysisHandler = null;
    this.send("stop");
  }
}
