#pragma once
#include <stdint.h>
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {
#endif
void fretglow_setup(void);
void fretglow_tick(void);
void fretglow_render(void);
void fretglow_keyboard(uint8_t *raw,uint8_t *modifiers);
bool fretglow_valid(uint8_t type, uint8_t req, uint16_t value, uint16_t index, uint16_t len);
uint16_t fretglow_request(uint8_t req, uint8_t *buf);
#ifdef __cplusplus
}
#endif
