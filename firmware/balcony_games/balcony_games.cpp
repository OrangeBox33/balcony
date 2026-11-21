// Две игры для 2D-матрицы: «Жизнь» раундами и «Змейка» с ботом.
// Перенос animations/life/life.html и animations/snake/snake.html — логика та же.
#include "wled.h"
#include <algorithm>

namespace bg {

// ------------------------------------------------------------ общее

struct RGB { uint8_t r, g, b; };
static const RGB C_WHITE = {255, 255, 255};

static inline float frand() { return hw_random16() / 65536.0f; }

static RGB hsv(float h, float s, float v) {
  h -= floorf(h);
  int i = int(h * 6);
  float f = h * 6 - i;
  float p = v * (1 - s), q = v * (1 - f * s), t = v * (1 - (1 - f) * s);
  float r, g, b;
  switch (i % 6) {
    case 0: r = v; g = t; b = p; break;
    case 1: r = q; g = v; b = p; break;
    case 2: r = p; g = v; b = t; break;
    case 3: r = p; g = q; b = v; break;
    case 4: r = t; g = p; b = v; break;
    default: r = v; g = p; b = q; break;
  }
  return {uint8_t(r * 255 + 0.5f), uint8_t(g * 255 + 0.5f), uint8_t(b * 255 + 0.5f)};
}

static inline RGB scaled(RGB c, float k) {
  return {uint8_t(c.r * k + 0.5f), uint8_t(c.g * k + 0.5f), uint8_t(c.b * k + 0.5f)};
}

static inline void px(int x, int y, RGB c) {
  if (x < 0 || y < 0 || x >= SEG_W || y >= SEG_H) return;
  SEGMENT.setPixelColorXY(x, y, RGBW32(c.r, c.g, c.b, 0));
}

static inline bool lit(int x, int y) {
  return SEGMENT.getPixelColorXY(x, y) != 0;
}

// ------------------------------------------------------------ шрифты (1 бит = точка, старший слева)

struct Glyph { char c; uint8_t w; uint8_t rows[7]; };

static const Glyph FONT7[] PROGMEM = {
  {'0', 5, {0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E}},
  {'1', 5, {0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E}},
  {'2', 5, {0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F}},
  {'3', 5, {0x1E, 0x01, 0x01, 0x0E, 0x01, 0x01, 0x1E}},
  {'4', 5, {0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02}},
  {'5', 5, {0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E}},
  {'6', 5, {0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E}},
  {'7', 5, {0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08}},
  {'8', 5, {0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E}},
  {'9', 5, {0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C}},
  {'L', 4, {0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x0F}},
  {'I', 3, {0x07, 0x02, 0x02, 0x02, 0x02, 0x02, 0x07}},
  {'V', 5, {0x11, 0x11, 0x11, 0x11, 0x0A, 0x0A, 0x04}},
  {'E', 4, {0x0F, 0x08, 0x08, 0x0E, 0x08, 0x08, 0x0F}},
  {'G', 5, {0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0E}},
  {'O', 5, {0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E}},
  {'!', 1, {0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x01}},
};
static const Glyph FONT5[] PROGMEM = {
  {'0', 3, {0x07, 0x05, 0x05, 0x05, 0x07}},
  {'1', 3, {0x02, 0x06, 0x02, 0x02, 0x07}},
  {'2', 3, {0x06, 0x01, 0x02, 0x04, 0x07}},
  {'3', 3, {0x06, 0x01, 0x02, 0x01, 0x06}},
  {'4', 3, {0x05, 0x05, 0x07, 0x01, 0x01}},
  {'5', 3, {0x07, 0x04, 0x06, 0x01, 0x06}},
  {'6', 3, {0x03, 0x04, 0x07, 0x05, 0x07}},
  {'7', 3, {0x07, 0x01, 0x02, 0x02, 0x02}},
  {'8', 3, {0x07, 0x05, 0x07, 0x05, 0x07}},
  {'9', 3, {0x07, 0x05, 0x07, 0x01, 0x06}},
};

struct Font { const Glyph *g; uint8_t n, h; };
static const Font F7 = {FONT7, sizeof(FONT7) / sizeof(Glyph), 7};
static const Font F5 = {FONT5, sizeof(FONT5) / sizeof(Glyph), 5};

static const Glyph *glyph(const Font &f, char c) {
  for (unsigned i = 0; i < f.n; i++) if (f.g[i].c == c) return &f.g[i];
  return nullptr;
}

static int textWidth(const char *s, const Font &f) {
  int w = -1;
  for (; *s; s++) { const Glyph *g = glyph(f, *s); if (g) w += g->w + 1; }
  return w;
}

static inline int floorDiv2(int v) { return v >= 0 ? v / 2 : -((1 - v) / 2); }

// Текст по центру. Не влезает крупным — берёт мелкий шрифт (если в нём есть все знаки).
static void putText(const char *s, RGB c) {
  const int W = SEG_W, H = SEG_H;
  const Font *f = &F7;
  if (textWidth(s, F7) > W - 2) {
    bool ok = true;
    for (const char *p = s; *p; p++) if (!glyph(F5, *p)) ok = false;
    if (ok) f = &F5;
  }
  int x = floorDiv2(W - textWidth(s, *f));
  const int y = floorDiv2(H - f->h);
  for (; *s; s++) {
    const Glyph *g = glyph(*f, *s);
    if (!g) continue;
    for (int dy = 0; dy < f->h; dy++)
      for (int dx = 0; dx < g->w; dx++)
        if (g->rows[dy] & (1 << (g->w - 1 - dx))) px(x + dx, y + dy, c);
    x += g->w + 1;
  }
}

// ------------------------------------------------------------ праздник по краям

static int perimLen() { return 2 * SEG_W + 2 * (SEG_H - 2); }

static void perim(int k, int &x, int &y) {
  const int W = SEG_W, H = SEG_H;
  if (k < W) { x = k; y = 0; return; }
  k -= W;
  if (k < H - 1) { x = W - 1; y = k + 1; return; }
  k -= H - 1;
  if (k < W - 1) { x = W - 2 - k; y = H - 1; return; }
  k -= W - 1;
  x = 0; y = H - 2 - k;
}

// Бегущая радуга, вспышки и искры. sparks — ещё и искры во внутреннем кольце.
static void party(uint32_t t, bool sparks) {
  const int W = SEG_W, H = SEG_H, n = perimLen();
  const int shift = t / 35;
  const bool strobe = t % 500 < 90;
  for (int k = 0; k < n; k++) {
    int x, y;
    perim(k, x, y);
    RGB c = {0, 0, 0};
    if (strobe) c = C_WHITE;
    else if ((k + shift) % 6 < 3) c = hsv(float(k) / n + t / 1500.0f, 1, 1);
    if (frand() < 0.08f) c = C_WHITE;
    px(x, y, c);
  }
  if (!sparks) return;
  for (int s = 0; s < 3; s++) {
    int x, y;
    perim(int(frand() * n), x, y);
    int ix = constrain(x, 1, W - 2) + (x == 0 ? 1 : x == W - 1 ? -1 : 0);
    int iy = constrain(y, 1, H - 2) + (y == 0 ? 1 : y == H - 1 ? -1 : 0);
    if (!lit(ix, iy)) px(ix, iy, hsv(frand(), 0.6f, 1));
  }
}

static const uint32_t SCORE_MS = 2000, BIG_SCORE_MS = 10000, COUNT_MS = 1200;

// ------------------------------------------------------------ «Жизнь»

namespace life {

const uint32_t BIG = 1000;        // с этого числа — праздник
const int MAX_MARGIN = 12;
const int SEEN = 201, VIS_SEEN = 61;
enum Phase : uint8_t { RUN, HOLD, SCORE, COUNT };

struct State {
  bool inited;
  uint8_t phase, M;
  uint16_t W, H, FW, FH;
  uint32_t gen, lived, run, best, last, phaseT;
  float acc, hue, nextHue;
  RGB lastColor;
  int holdLeft, visStuck, visEmpty;
  uint64_t seenH[SEEN]; uint32_t seenG[SEEN];
  uint64_t visH[VIS_SEEN]; uint32_t visG[VIS_SEEN];
  // дальше в памяти: cells, next, glow — по FW*FH байт
};

static uint8_t *cells(State *s) { return reinterpret_cast<uint8_t *>(s + 1); }
static size_t fieldMax(int W, int H) { return size_t(W + 2 * MAX_MARGIN) * (H + 2 * MAX_MARGIN); }
static uint8_t *nextBuf(State *s) { return cells(s) + fieldMax(s->W, s->H); }
static uint8_t *glow(State *s) { return cells(s) + 2 * fieldMax(s->W, s->H); }

static uint64_t hashOf(State *s, int x0, int y0, int w, int h) {
  const uint8_t *c = cells(s);
  uint32_t a = 0x811c9dc5, b = 0x01000193 ^ 0x5bd1e995;
  for (int y = y0; y < y0 + h; y++)
    for (int x = x0; x < x0 + w; x++) {
      uint32_t v = c[y * s->FW + x];
      a = (a ^ v) * 0x01000193;
      b = (b ^ (v + x)) * 0x5bd1e995;
    }
  return (uint64_t(a) << 32) | b;
}

// Поколение, когда такая картинка уже была (самое позднее), или -1.
static int32_t lookup(const uint64_t *H, const uint32_t *G, int n, uint64_t h, uint32_t gen, uint32_t window) {
  int32_t best = -1;
  for (int i = 0; i < n; i++)
    if (G[i] != UINT32_MAX && H[i] == h && gen - G[i] <= window && int32_t(G[i]) > best) best = G[i];
  return best;
}

static void remember(State *s) {
  s->seenH[s->gen % SEEN] = hashOf(s, 0, 0, s->FW, s->FH);
  s->seenG[s->gen % SEEN] = s->gen;
  s->visH[s->gen % VIS_SEEN] = hashOf(s, s->M, s->M, s->W, s->H);
  s->visG[s->gen % VIS_SEEN] = s->gen;
}

static void seed(State *s) {
  const float d = (5 + SEGMENT.intensity * 55 / 255) / 100.0f;
  const int n = s->FW * s->FH;
  uint8_t *c = cells(s), *g = glow(s);
  for (int i = 0; i < n; i++) { c[i] = frand() < d ? 1 : 0; g[i] = 0; }
  s->gen = 0;
  s->run++;
  s->hue = s->nextHue;
  s->nextHue = fmodf(s->hue + 0.2f + frand() * 0.6f, 1.0f);   // следующий цвет заметно отличается
  for (int i = 0; i < SEEN; i++) s->seenG[i] = UINT32_MAX;
  for (int i = 0; i < VIS_SEEN; i++) s->visG[i] = UINT32_MAX;
  s->visStuck = s->visEmpty = 0;
  s->phase = RUN;
  s->lived = 0;
  remember(s);
}

static void step(State *s) {
  const int FW = s->FW, FH = s->FH;
  uint8_t *c = cells(s), *nx = nextBuf(s), *g = glow(s);
  for (int y = 0; y < FH; y++)
    for (int x = 0; x < FW; x++) {
      int n = 0;
      for (int dy = -1; dy <= 1; dy++) {
        const int yy = y + dy;
        if (yy < 0 || yy >= FH) continue;
        for (int dx = -1; dx <= 1; dx++) {
          if (!dx && !dy) continue;
          const int xx = x + dx;
          if (xx >= 0 && xx < FW) n += c[yy * FW + xx];
        }
      }
      const int i = y * FW + x;
      nx[i] = (c[i] && (n == 2 || n == 3)) || (!c[i] && n == 3) ? 1 : 0;
      g[i] = nx[i] ? 255 : uint8_t(g[i] * 0.4f);
    }
  memcpy(c, nx, FW * FH);
  s->gen++;
}

// Конец раунда: true + честное число поколений — до момента, когда картинка
// впервые пришла в финальное состояние (проверочные повторы не считаются).
static bool checkEnd(State *s, int all, int vis, uint32_t &lived) {
  if (all == 0) { lived = s->gen; return true; }
  const int32_t g = lookup(s->seenH, s->seenG, SEEN, hashOf(s, 0, 0, s->FW, s->FH), s->gen, SEEN - 1);
  if (g >= 0) { lived = g; return true; }             // gen - period
  s->visEmpty = vis == 0 ? s->visEmpty + 1 : 0;
  if (s->visEmpty >= 20) { lived = s->gen - s->visEmpty + 1; return true; }   // жизнь ушла за кадр
  const bool vseen = lookup(s->visH, s->visG, VIS_SEEN, hashOf(s, s->M, s->M, s->W, s->H), s->gen, VIS_SEEN - 1) >= 0;
  s->visStuck = vseen ? s->visStuck + 1 : 0;
  if (s->visStuck >= 60) { lived = s->gen - s->visStuck; return true; }       // на экране повтор
  const uint32_t maxGen = SEGMENT.custom2 * 20u;                              // 0 — без лимита
  if (maxGen && s->gen >= maxGen) { lived = s->gen; return true; }
  return false;
}

static RGB runColor(State *s) { return SEGMENT.check1 ? C_WHITE : hsv(s->hue, 1, 1); }

static void advance(State *s, float gps) {
  if (s->phase == RUN) {
    step(s);
    int all = 0, vis = 0;
    const uint8_t *c = cells(s);
    for (int y = 0; y < s->FH; y++)
      for (int x = 0; x < s->FW; x++)
        if (c[y * s->FW + x]) {
          all++;
          if (x >= s->M && x < s->M + s->W && y >= s->M && y < s->M + s->H) vis++;
        }
    uint32_t lived;
    const bool end = checkEnd(s, all, vis, lived);
    remember(s);
    if (end) {
      s->lived = lived;
      s->lastColor = runColor(s);
      if (lived > s->best) s->best = lived;
#ifdef BG_TRACE
      bg_trace_life(s->run, lived, s->gen);
#endif
      // короткая пауза на финальной картинке, чтобы глаз успел её увидеть
      s->holdLeft = all == 0 ? 0 : max(3, int(gps * 0.5f + 0.5f));
      s->phase = s->holdLeft ? HOLD : SCORE;
      s->phaseT = 0;
    }
  } else if (s->phase == HOLD) {
    step(s);
    if (--s->holdLeft <= 0) { s->phase = SCORE; s->phaseT = 0; }
  }
}

static void draw(State *s) {
  const int W = s->W, H = s->H;
  if (s->phase == SCORE) {
    char buf[12];
    snprintf(buf, sizeof(buf), "%u", unsigned(s->lived));
    putText(buf, s->lastColor);
    if (s->lived >= BIG) party(s->phaseT, true);
    return;
  }
  if (s->phase == COUNT) {
    static const char *const words[] = {"3", "2", "1", "LIVE!"};
    const int i = min(3, int(s->phaseT / (COUNT_MS / 4)));
    putText(words[i], SEGMENT.check1 ? C_WHITE : hsv(s->nextHue, 1, 1));
    return;
  }
  const RGB col = runColor(s);
  const bool trail = SEGMENT.check2;
  const uint8_t *c = cells(s), *g = glow(s);
  for (int y = 0; y < H; y++)
    for (int x = 0; x < W; x++) {
      const int i = (y + s->M) * s->FW + x + s->M;
      if (c[i]) px(x, y, col);
      else if (trail && g[i]) px(x, y, scaled(col, g[i] / 255.0f));
    }
}

static void mode() {
  if (!strip.isMatrix || !SEGMENT.is2D()) { SEGMENT.fill(BLACK); return; }
  const int W = SEG_W, H = SEG_H;
  const int M = SEGMENT.custom1 * (MAX_MARGIN + 1) / 256;
  if (!SEGENV.allocateData(sizeof(State) + 3 * fieldMax(W, H))) { SEGMENT.fill(BLACK); return; }
  State *s = reinterpret_cast<State *>(SEGENV.data);
  const uint32_t now = strip.now;
  if (!s->inited || s->W != W || s->H != H || s->M != M) {
    const uint32_t run = s->inited ? s->run : 0, best = s->inited ? s->best : 0;
    s->inited = true;
    s->W = W; s->H = H; s->M = M;
    s->FW = W + 2 * M; s->FH = H + 2 * M;
    s->run = run; s->best = best;
    s->nextHue = frand();
    s->acc = 0;
    s->last = now;
    seed(s);
  }
  uint32_t dt = now - s->last;
  if (dt > 250) dt = 250;
  s->last = now;

  const float gps = 1 + SEGMENT.speed * 29 / 255.0f;            // поколений в секунду, 1…30
  if (s->phase == RUN || s->phase == HOLD) {
    const float period = 1000.0f / gps;
    s->acc += dt;
    while (s->acc >= period && (s->phase == RUN || s->phase == HOLD)) {
      s->acc -= period;
      advance(s, gps);
    }
  } else {
    s->acc = 0;
    s->phaseT += dt;
    if (s->phase == SCORE && s->phaseT >= (s->lived >= BIG ? BIG_SCORE_MS : SCORE_MS)) { s->phase = COUNT; s->phaseT = 0; }
    else if (s->phase == COUNT && s->phaseT >= COUNT_MS) seed(s);
  }

  SEGMENT.fill(BLACK);
  draw(s);
}

}  // namespace life

// ------------------------------------------------------------ «Змейка»

namespace snake {

const uint32_t BIG = 250;          // с этого счёта — праздник
const float RISK = 0.15f;          // как часто средний бот идёт к яблоку, не проверив, выберется ли
const uint32_t DEATH_MS = 1200;
const int MAX_CELLS = 2048;
enum Phase : uint8_t { PLAY, DEAD, SCORE, COUNT };
enum Brain : uint8_t { GREEDY, MEDIUM, SMART };

struct State {
  bool inited;
  uint8_t phase;
  uint16_t W, H, N, len;
  int16_t apple;
  uint32_t score, round, best, sinceApple, last, phaseT;
  float accT, hue, nextHue;
  RGB lastColor;
  // дальше в памяти: body, dist, prev, queue, path, virt, moved (int16 по N) и occ (uint8 по N)
};

struct Bufs { int16_t *body, *dist, *prev, *queue, *path, *virt, *moved; uint8_t *occ; };

static Bufs bufs(State *s) {
  int16_t *p = reinterpret_cast<int16_t *>(s + 1);
  const int N = s->N;
  return {p, p + N, p + 2 * N, p + 3 * N, p + 4 * N, p + 5 * N, p + 6 * N, reinterpret_cast<uint8_t *>(p + 7 * N)};
}

static size_t dataSize(int N) { return sizeof(State) + 7 * N * sizeof(int16_t) + N; }

// цвет змейки не должен совпадать с красным яблоком
static float randHue() { return 0.12f + frand() * 0.76f; }

static int neighbors(State *s, int c, int16_t out[4]) {
  const int W = s->W, H = s->H, x = c % W, y = c / W;
  int n = 0;
  if (y > 0) out[n++] = c - W;
  if (x < W - 1) out[n++] = c + 1;
  if (y < H - 1) out[n++] = c + W;
  if (x > 0) out[n++] = c - 1;
  return n;
}

static void occupancy(State *s, const int16_t *body, int len, bool freeTail, uint8_t *occ) {
  memset(occ, 0, s->N);
  for (int i = 0; i < len - (freeTail ? 1 : 0); i++) occ[body[i]] = 1;
}

// BFS: расстояния от start по клеткам, где occ[i] == 0.
static int16_t *bfs(State *s, int start, const uint8_t *occ) {
  Bufs b = bufs(s);
  for (int i = 0; i < s->N; i++) b.dist[i] = -1;
  int qh = 0, qt = 0;
  b.queue[qt++] = start;
  b.dist[start] = 0;
  b.prev[start] = -1;
  while (qh < qt) {
    const int c = b.queue[qh++];
    int16_t nb[4];
    const int n = neighbors(s, c, nb);
    // лёгкая случайность в равных вариантах — партии получаются разными
    if (frand() < 0.5f)
      for (int i = n - 1; i > 0; i--) { const int j = int(frand() * (i + 1)); std::swap(nb[i], nb[j]); }
    for (int k = 0; k < n; k++) {
      const int m = nb[k];
      if (b.dist[m] >= 0 || occ[m]) continue;
      b.dist[m] = b.dist[c] + 1;
      b.prev[m] = c;
      b.queue[qt++] = m;
    }
  }
  return b.dist;
}

// Путь start…target по prev последнего BFS в b.path; возвращает длину.
static int pathTo(State *s, int target) {
  Bufs b = bufs(s);
  int n = 0;
  for (int c = target; c != -1; c = b.prev[c]) b.path[n++] = c;
  std::reverse(b.path, b.path + n);
  return n;
}

// После того как змейка пройдёт path и съест яблоко — сможет ли голова добраться до хвоста?
static bool safeAfter(State *s, int pathLen) {
  Bufs b = bufs(s);
  const int len = s->len + 1;
  int k = 0;
  for (int i = pathLen - 1; i >= 1 && k < len; i--) b.virt[k++] = b.path[i];
  for (int i = 0; i < s->len && k < len; i++) b.virt[k++] = b.body[i];
  occupancy(s, b.virt, k, true, b.occ);
  const int16_t *d = bfs(s, b.virt[0], b.occ);
  return d[b.virt[k - 1]] > 0 || k >= s->N;
}

static int chooseMove(State *s, Brain brain) {
  Bufs b = bufs(s);
  const int head = b.body[0];
  int16_t nb[4];
  const int nn = neighbors(s, head, nb);

  // 1. Кратчайший путь к яблоку
  if (s->apple >= 0) {
    occupancy(s, b.body, s->len, true, b.occ);
    const int16_t *d = bfs(s, head, b.occ);
    if (d[s->apple] > 0) {
      const int pl = pathTo(s, s->apple);
      const bool risky = brain == GREEDY || (brain == MEDIUM && frand() < RISK);
      if (risky || safeAfter(s, pl)) return b.path[1];
    }
  }

  // 2. Тянуть время: идти туда, откуда хвост дальше всего, но достижим
  int bestMove = -1, bestD = -1;
  for (int k = 0; k < nn; k++) {
    const int n = nb[k];
    occupancy(s, b.body, s->len, true, b.occ);
    if (b.occ[n]) continue;
    b.moved[0] = n;
    for (int i = 0; i < s->len - 1; i++) b.moved[i + 1] = b.body[i];
    occupancy(s, b.moved, s->len, true, b.occ);
    const int d = bfs(s, n, b.occ)[b.moved[s->len - 1]];
    if (d > bestD) { bestD = d; bestMove = n; }
  }
  if (bestMove >= 0 && bestD > 0) return bestMove;

  // 3. Безвыходно: туда, где больше свободного места
  int most = -1;
  bestMove = -1;
  for (int k = 0; k < nn; k++) {
    const int n = nb[k];
    occupancy(s, b.body, s->len, true, b.occ);
    if (b.occ[n]) continue;
    const int16_t *d = bfs(s, n, b.occ);
    int area = 0;
    for (int i = 0; i < s->N; i++) if (d[i] >= 0) area++;
    if (area > most) { most = area; bestMove = n; }
  }
  return bestMove;
}

static void placeApple(State *s) {
  Bufs b = bufs(s);
  occupancy(s, b.body, s->len, false, b.occ);
  const int free = s->N - s->len;
  if (free <= 0) { s->apple = -1; return; }
  int r = int(frand() * free);
  for (int i = 0; i < s->N; i++)
    if (!b.occ[i] && r-- == 0) { s->apple = i; return; }
  s->apple = -1;
}

static void newRound(State *s) {
  Bufs b = bufs(s);
  s->round++;
  s->hue = s->nextHue;
  do { s->nextHue = randHue(); } while (fabsf(s->nextHue - s->hue) < 0.2f);
  const int W = s->W, H = s->H;
  const int y = int(frand() * (H - 2)) + 1;
  const int x = W >= 9 ? int(frand() * (W - 8)) + 4 : 2;
  b.body[0] = y * W + x; b.body[1] = y * W + x - 1; b.body[2] = y * W + x - 2;   // голова первой
  s->len = 3;
  s->score = 0;
  s->sinceApple = 0;
  placeApple(s);
  s->phase = PLAY;
}

static void end(State *s) {
  s->lastColor = hsv(s->hue, 1, 1);
  if (s->score > s->best) s->best = s->score;
#ifdef BG_TRACE
  bg_trace_snake(s->round, s->score, s->len);
#endif
  s->phase = DEAD;
  s->phaseT = 0;
}

static void stepGame(State *s, Brain brain) {
  Bufs b = bufs(s);
  const int mv = chooseMove(s, brain);
  if (mv < 0) return end(s);                                   // некуда ползти
  const bool tailFree = mv == b.body[s->len - 1];
  if (!tailFree)
    for (int i = 0; i < s->len; i++) if (b.body[i] == mv) return end(s);   // врезалась в себя
  memmove(b.body + 1, b.body, s->len * sizeof(int16_t));
  b.body[0] = mv;
  s->len++;
  if (mv == s->apple) {
    s->score++;
    s->sinceApple = 0;
    if (s->len >= s->N) return end(s);                         // заполнила всё поле
    placeApple(s);
  } else {
    s->len--;
    if (++s->sinceApple > uint32_t(s->N) * 4) return end(s);    // ходит кругами
  }
}

static void draw(State *s, uint32_t now) {
  Bufs b = bufs(s);
  const int W = s->W;
  if (s->phase == SCORE) {
    char buf[12];
    snprintf(buf, sizeof(buf), "%u", unsigned(s->score));
    putText(buf, s->lastColor);
    if (s->score >= BIG) party(s->phaseT, false);
    return;
  }
  if (s->phase == COUNT) {
    static const char *const words[] = {"3", "2", "1", "GO!"};
    const int i = min(3, int(s->phaseT / (COUNT_MS / 4)));
    putText(words[i], hsv(s->nextHue, 1, 1));
    return;
  }
  // яблоко пульсирует
  if (s->apple >= 0 && s->phase == PLAY) {
    const float k = 0.75f + 0.25f * sinf(now / 160.0f);
    px(s->apple % W, s->apple / W, {uint8_t(255 * k), 0, 0});
  }
  const bool blinkOff = s->phase == DEAD && (s->phaseT / 200) % 2 == 1;
  if (blinkOff) return;
  const int L = s->len;
  const bool rainbow = SEGMENT.check1;
  for (int i = L - 1; i >= 0; i--) {
    const float fade = 1 - 0.5f * i / max(L - 1, 1);           // хвост тусклее, но не гаснет
    RGB c = rainbow ? hsv(s->hue + i * 0.025f, 1, fade) : hsv(s->hue, 1, fade);
    if (i == 0) c = hsv(s->hue, 0.35f, 1);                      // голова светлее
    if (s->phase == DEAD) c = i == 0 ? C_WHITE : RGB{255, 0, 0};
    px(b.body[i] % W, b.body[i] / W, c);
  }
}

static void mode() {
  if (!strip.isMatrix || !SEGMENT.is2D()) { SEGMENT.fill(BLACK); return; }
  const int W = SEG_W, H = SEG_H, N = W * H;
  if (N > MAX_CELLS || W < 4 || H < 3 || !SEGENV.allocateData(dataSize(N))) { SEGMENT.fill(BLACK); return; }
  State *s = reinterpret_cast<State *>(SEGENV.data);
  const uint32_t now = strip.now;
  if (!s->inited || s->W != W || s->H != H) {
    const uint32_t round = s->inited ? s->round : 0, best = s->inited ? s->best : 0;
    s->inited = true;
    s->W = W; s->H = H; s->N = N;
    s->round = round; s->best = best;
    s->nextHue = randHue();
    s->accT = 0;
    s->last = now;
    newRound(s);
  }
  uint32_t dt = now - s->last;
  if (dt > 250) dt = 250;
  s->last = now;

  const Brain brain = SEGMENT.custom1 < 85 ? GREEDY : SEGMENT.custom1 < 170 ? MEDIUM : SMART;
  if (s->phase == PLAY) {
    // с ростом длины змейка разгоняется (до +accel%)
    const float base = 2 + SEGMENT.speed * 38 / 255.0f;        // ходов в секунду, 2…40
    const float accel = SEGMENT.intensity / 255.0f;
    s->accT += dt;
    for (;;) {
      const float period = 1000.0f / (base * (1 + accel * min(s->len / 150.0f, 1.0f)));
      if (s->phase != PLAY || s->accT < period) break;
      s->accT -= period;
      stepGame(s, brain);
    }
  } else {
    s->accT = 0;
    s->phaseT += dt;
    if (s->phase == DEAD && s->phaseT >= DEATH_MS) { s->phase = SCORE; s->phaseT = 0; }
    else if (s->phase == SCORE && s->phaseT >= (s->score >= BIG ? BIG_SCORE_MS : SCORE_MS)) { s->phase = COUNT; s->phaseT = 0; }
    else if (s->phase == COUNT && s->phaseT >= COUNT_MS) newRound(s);
  }

  SEGMENT.fill(BLACK);
  draw(s, now);
}

}  // namespace snake
}  // namespace bg

static void mode_life_rounds() { bg::life::mode(); }
static void mode_snake_bot() { bg::snake::mode(); }

// Ползунки: скорость (поколений/с 1…30), плотность засева 5…60%, запас за краем 0…12,
// предел поколений ×20 (0 — без лимита). Галки: белый цвет, шлейф.
static const char _data_FX_MODE_LIFE_ROUNDS[] PROGMEM =
  "Life Rounds@Gens/sec,Seed density,Off-screen margin,Max gens x20 (0=none),,White,Trail;;;2;sx=123,ix=65,c1=0,c2=0,o1=0,o2=0";
// Ползунки: ходов/с 2…40, разгон с длиной 0…100%, бот (слева новичок, середина средний, справа мастер).
static const char _data_FX_MODE_SNAKE_BOT[] PROGMEM =
  "Snake Bot@Moves/sec,Speed-up,Bot skill,,,Rainbow;;;2;sx=67,ix=102,c1=128,o1=0";

class BalconyGamesUsermod : public Usermod {
 public:
  void setup() override {
    strip.addEffect(255, &mode_life_rounds, _data_FX_MODE_LIFE_ROUNDS);
    strip.addEffect(255, &mode_snake_bot, _data_FX_MODE_SNAKE_BOT);
  }
  void loop() override {}
};

static BalconyGamesUsermod balcony_games;
REGISTER_USERMOD(balcony_games);
