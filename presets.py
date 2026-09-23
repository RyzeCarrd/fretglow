"""Named local presets and the three guitar slots."""
from copy import deepcopy
import json
from pathlib import Path
import uuid
import onboard

def packet(settings):
    return onboard.encode(settings['colours'],settings['brightness'],settings['mode'],settings['keys'],settings['effect_colour'])

class Library:
    def __init__(self,path):
        self.path=Path(path);self.items=[];self.slots=[None]*3;self.start=0
        if self.path.exists():
            data=json.loads(self.path.read_text(encoding='utf-8'))
            items=data['items'];ids=set()
            for item in items:
                if not isinstance(item['name'],str) or not item['name'].strip() or item['id'] in ids:raise ValueError('Invalid preset library')
                packet(item['settings']);ids.add(item['id'])
            slots=data['slots'];start=data['start']
            if len(slots)!=3 or any(s is not None and s not in ids for s in slots) or type(start)is not int or start not in range(3):raise ValueError('Invalid guitar slots')
            self.items=items;self.slots=slots;self.start=start
    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temp=self.path.with_suffix('.tmp')
        temp.write_text(json.dumps(dict(items=self.items,slots=self.slots,start=self.start),indent=2),encoding='utf-8');temp.replace(self.path)
    def get(self,id):return next(item for item in self.items if item['id']==id)
    def add(self,name,settings):
        name=name.strip()
        if not name or len(name)>40:raise ValueError('Use a preset name between 1 and 40 characters.')
        if any(i['name'].casefold()==name.casefold() for i in self.items):raise ValueError('That name is already saved. Choose another name.')
        packet(settings)
        item=dict(id=uuid.uuid4().hex,name=name,settings=deepcopy(settings));self.items.append(item)
        try:self.save()
        except Exception:self.items.pop();raise
        return item['id']
    def assign(self,slot,id):
        if id is not None:self.get(id)
        previous=self.slots.copy();old_start=self.start;self.slots[slot]=id
        if self.slots[self.start] is None:self.start=next((i for i,value in enumerate(self.slots) if value is not None),0)
        try:self.save()
        except Exception:self.slots=previous;self.start=old_start;raise
    def bank(self):
        filled=[i for i,id in enumerate(self.slots) if id is not None]
        if not filled:raise ValueError('Drag a preset into a guitar slot first.')
        start=self.start if self.start in filled else filled[0]
        fallback=packet(self.get(self.slots[start])['settings'])
        profiles=[packet(self.get(id)['settings']) if id else fallback for id in self.slots]
        return onboard.encode_bank(profiles,sum(1<<i for i in filled),start)
