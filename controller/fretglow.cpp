// SPDX-License-Identifier: GPL-3.0-or-later
// This hardware profile: Pico, five APA102 frets, GP16 Start / GP17 Back.
#include <Arduino.h>
#include <EEPROM.h>
#include <string.h>
#include "shared_main.h"
#include "fretglow.h"
static uint8_t saved[64], pending[64], saveStatus;
static bool configured, custom, preview, queued;
static uint32_t queuedAt;
static const uint8_t pins[9] = {11,12,10,14,15,9,8,16,17};
static bool buttons[9], previous[9], rawPrevious[9], latched[5];
static uint32_t rawChanged[9];
struct Hold { bool armed, down, fired; uint32_t since, pulse; };
static Hold holds[2];
static uint32_t crc(const uint8_t *p) {
    uint32_t c=0xffffffff;
    for (int i=0;i<60;i++) { c^=p[i]; for(int j=0;j<8;j++) c=(c>>1)^((c&1)?0xedb88320:0); }
    return ~c;
}
static bool valid(const uint8_t *p) {
    uint32_t expected; memcpy(&expected,p+60,4);
    if(memcmp(p,"FGL1",4)||(p[4]!=1&&p[4]!=2)||p[5]>31||p[6]>2||p[7]||p[32]!=0x88||p[33]!=0x13||crc(p)!=expected) return false;
    for(int i=23;i<32;i++) {
        bool key=p[i]==0||(p[i]>=4&&p[i]<=(p[4]==1?82:115))||(p[4]==2&&p[i]>=224&&p[i]<=231);
        if(!key) return false;
    }
    for(int i=p[4]==1?34:37;i<60;i++) if(p[i]) return false;
    return true;
}
static void clearLights() { for(int i=0;i<5;i++) { ledState[i].select=0; latched[i]=false; } }
void fretglow_setup() {
    for(int i=0;i<64;i++) saved[i]=EEPROM.read(64+i);
    configured=valid(saved); custom=configured;
    if(!configured) {
        memset(saved,0,64); memcpy(saved,"FGL1",4); saved[4]=1; saved[5]=9; saved[6]=1;
        const uint8_t colours[15]={48,223,114,255,65,104,255,227,76,66,138,255,255,148,56};
        const uint8_t keys[9]={4,22,14,15,16,82,81,40,42};
        memcpy(saved+8,colours,15); memcpy(saved+23,keys,9); saved[32]=0x88; saved[33]=0x13;
        uint32_t c=crc(saved); memcpy(saved+60,&c,4);
    }
}
void fretglow_tick() {
    uint32_t now=millis();
    if(queued && uint32_t(now-queuedAt)>=100) {
        for(int i=0;i<64;i++) EEPROM.write(64+i,pending[i]);
        if(EEPROM.commit()) { memcpy(saved,pending,64); configured=true; custom=true; preview=false; clearLights(); saveStatus=0; }
        else saveStatus=3;
        queued=false;
    }
    for(int i=0;i<9;i++) {
        bool raw=!gpio_get(pins[i]);
        if(raw!=rawPrevious[i]) { rawPrevious[i]=raw; rawChanged[i]=now; }
        if(uint32_t(now-rawChanged[i])>=3) buttons[i]=raw;
        if(i<5 && buttons[i]&&!previous[i]) latched[i]=!latched[i];
        previous[i]=buttons[i];
    }
    for(int i=0;i<2;i++) {
        Hold &h=holds[i]; bool down=buttons[7+i];
        if(!down) {
            if(h.down&&!h.fired) h.pulse=now;
            h.down=false; h.fired=false; h.armed=true; continue;
        }
        if(!h.armed) continue; // Require release after USB mode reboot.
        if(!h.down) { h.down=true; h.since=now; h.pulse=0; }
        if(!h.fired && uint32_t(now-h.since)>=5000) {
            h.fired=true;
            if(i==0) { custom=configured&&!custom; preview=false; clearLights(); }
            else { set_console_type(consoleType==KEYBOARD_MOUSE ? UNIVERSAL : KEYBOARD_MOUSE); return; }
        }
    }
}
void fretglow_render() {
    if(!custom||preview) return;
    for(int i=0;i<5;i++) {
        bool active=saved[6]==1 ? buttons[i] : saved[6]==2 && latched[i];
        Led_t &led=ledState[4-i]; led.select=1; led.brightness=saved[5];
        led.r=active?(saved[4]==1?255:saved[34]):saved[8+i*3];
        led.g=active?(saved[4]==1?255:saved[35]):saved[9+i*3];
        led.b=active?(saved[4]==1?255:saved[36]):saved[10+i*3];
    }
}
void fretglow_keyboard(uint8_t *raw,uint8_t *modifiers) {
    for(int i=0;i<9;i++) {
        // Short Start/Back presses type on release; long holds never repeat keys.
        bool down=i<7 ? buttons[i] : holds[i-7].pulse && uint32_t(millis()-holds[i-7].pulse)<40;
        uint8_t key=saved[23+i];
        if(down&&key) {
            if(key>=224&&key<=231) *modifiers|=1u<<(key-224);
            else raw[key/8]|=1u<<(key%8);
        }
    }
}
bool fretglow_valid(uint8_t type,uint8_t req,uint16_t value,uint16_t index,uint16_t len) {
    if(value||index!=2) return false;
    return (type==0xa1 && ((req==0x70&&len==16)||(req==0x71&&len==64))) ||
           (type==0x21 && ((req==0x72&&len==64)||(req==0x74&&len==1)));
}
uint16_t fretglow_request(uint8_t req,uint8_t *buf) {
    if(req==0x70) {
        memset(buf,0,16); memcpy(buf,"FGLW",4); buf[4]=2;
        buf[5]=(custom?1:0)|(consoleType==KEYBOARD_MOUSE?2:0)|(preview?4:0)|(configured?8:0);
        buf[6]=saveStatus; memcpy(buf+8,saved+60,4); return 16;
    }
    if(req==0x71) { memcpy(buf,saved,64); return 64; }
    if(req==0x72) {
        if(queued) return 0;
        if(!valid(buf)) { saveStatus=2; return 0; }
        if(configured&&!memcmp(saved,buf,64)) { saveStatus=0; custom=true; preview=false; clearLights(); return 0; }
        memcpy(pending,buf,64); queued=true; queuedAt=millis(); saveStatus=1;
    }
    if(req==0x74 && buf[0]<=1) { preview=buf[0]; clearLights(); }
    return 0;
}
