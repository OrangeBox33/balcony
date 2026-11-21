// Прогон эффектов на компьютере: ./sim life|snake [ключ=значение ...]
//   secs=600      сколько секунд игры прогнать (время виртуальное, считается мгновенно)
//   fps=42        кадров в секунду, как у WLED по умолчанию
//   seed=1        зерно случайности
//   sx= ix= c1= c2= o1= o2=   ползунки и галки эффекта
//   dump=файл from=0 to=30    записать кадры (сырые RGB 28×14) за отрезок времени в секундах
#include <string>

void bg_trace_life(uint32_t run, uint32_t lived, uint32_t gen);
void bg_trace_snake(uint32_t round, uint32_t score, uint32_t len);
#define BG_TRACE
#include "wled.h"
#include "../balcony_games/balcony_games.cpp"

static double now_s = 0;
void bg_trace_life(uint32_t run, uint32_t lived, uint32_t gen) {
  printf("ROUND %u lived=%u gen=%u t=%.1f\n", run, lived, gen, now_s);
}
void bg_trace_snake(uint32_t round, uint32_t score, uint32_t len) {
  printf("ROUND %u score=%u len=%u t=%.1f\n", round, score, len, now_s);
}

int main(int argc, char **argv) {
  if (argc < 2) return 1;
  const std::string game = argv[1];
  double secs = 600, from = 0, to = 0;
  int fps = 42;
  std::string dump;
  Segment seg;
  for (int i = 2; i < argc; i++) {
    std::string a = argv[i];
    const auto eq = a.find('=');
    const std::string k = a.substr(0, eq), v = a.substr(eq + 1);
    if (k == "secs") secs = std::stod(v);
    else if (k == "fps") fps = std::stoi(v);
    else if (k == "seed") sim_rng_state = std::stoul(v) * 2654435761u + 1;
    else if (k == "sx") seg.speed = std::stoi(v);
    else if (k == "ix") seg.intensity = std::stoi(v);
    else if (k == "c1") seg.custom1 = std::stoi(v);
    else if (k == "c2") seg.custom2 = std::stoi(v);
    else if (k == "o1") seg.check1 = std::stoi(v);
    else if (k == "o2") seg.check2 = std::stoi(v);
    else if (k == "dump") dump = v;
    else if (k == "from") from = std::stod(v);
    else if (k == "to") to = std::stod(v);
  }
  strip._currentSegment = &seg;
  FILE *out = dump.empty() ? nullptr : fopen(dump.c_str(), "wb");
  const long frames = long(secs * fps);
  for (long f = 0; f < frames; f++) {
    now_s = double(f) / fps;
    strip.now = (unsigned long)(now_s * 1000);
    if (game == "life") mode_life_rounds(); else mode_snake_bot();
    seg.call++;
    if (out && now_s >= from && now_s < to)
      for (uint32_t c : seg.px) { uint8_t rgb[3] = {uint8_t(c >> 16), uint8_t(c >> 8), uint8_t(c)}; fwrite(rgb, 1, 3, out); }
  }
  if (out) fclose(out);
  return 0;
}
