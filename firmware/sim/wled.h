// Подмена wled.h, чтобы собрать эффекты на компьютере и прогнать их без контроллера.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

using std::max;
using std::min;

#define PROGMEM
#define RGBW32(r, g, b, w) (uint32_t((uint8_t(w) << 24) | (uint8_t(r) << 16) | (uint8_t(g) << 8) | (uint8_t(b))))
#define WHITE (uint32_t)0xFFFFFF
#define BLACK (uint32_t)0x000000
#define constrain(v, lo, hi) ((v) < (lo) ? (lo) : (v) > (hi) ? (hi) : (v))
#define USERMOD_ID_UNSPECIFIED 1
#define REGISTER_USERMOD(x) Usermod *um_registered_##x = &x

inline uint32_t sim_rng_state = 12345;
inline uint16_t hw_random16() {
  uint32_t x = sim_rng_state;
  x ^= x << 13; x ^= x >> 17; x ^= x << 5;
  sim_rng_state = x;
  return uint16_t(x >> 8);
}

struct Segment {
  uint8_t speed = 128, intensity = 128, custom1 = 0, custom2 = 0, custom3 = 0;
  bool check1 = false, check2 = false, check3 = false;
  uint32_t call = 0, step = 0;
  uint8_t *data = nullptr;
  size_t dataLen = 0;
  static inline int W = 28, H = 14;
  std::vector<uint32_t> px = std::vector<uint32_t>(W * H);

  static int vWidth() { return W; }
  static int vHeight() { return H; }
  bool is2D() const { return W > 1 && H > 1; }
  bool allocateData(size_t len) {
    if (data && dataLen == len) return true;
    free(data);
    data = static_cast<uint8_t *>(calloc(len, 1));
    dataLen = len;
    return data != nullptr;
  }
  void fill(uint32_t c) { std::fill(px.begin(), px.end(), c); }
  void setPixelColorXY(int x, int y, uint32_t c) {
    if (x >= 0 && y >= 0 && x < W && y < H) px[y * W + x] = c;
  }
  uint32_t getPixelColorXY(int x, int y) const {
    return (x >= 0 && y >= 0 && x < W && y < H) ? px[y * W + x] : 0;
  }
};

typedef void (*mode_ptr)();
struct Strip {
  unsigned long now = 0;
  bool isMatrix = true;
  Segment *_currentSegment = nullptr;
  uint8_t addEffect(uint8_t, mode_ptr, const char *) { return 255; }
};
inline Strip strip;

#define SEGMENT (*strip._currentSegment)
#define SEGENV (*strip._currentSegment)
#define SEG_W Segment::vWidth()
#define SEG_H Segment::vHeight()

class Usermod {
 public:
  virtual ~Usermod() {}
  virtual void setup() {}
  virtual void loop() {}
};
