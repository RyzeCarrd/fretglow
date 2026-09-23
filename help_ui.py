"""Getting-started guide and credits."""
from pathlib import Path
import customtkinter as ctk
from PIL import Image
from app_icon import set_icon
from tutorial_content import TOPICS, matching_topics

class Tutorial:
    def __init__(self,app,palette):
        self.index=0;self.palette=palette;self.wrapped=[];self.visible=list(range(len(TOPICS)))
        self.window=ctk.CTkToplevel(app.root);w=self.window
        w.title('FretGlow tutorial');w.geometry('980x740');w.minsize(860,600);w.transient(app.root);w.configure(fg_color=palette['bg'])
        set_icon(w)
        w.grid_columnconfigure(1,weight=1);w.grid_rowconfigure(2,weight=1)
        sidebar=ctk.CTkFrame(w,fg_color=palette['panel'],width=230);sidebar.grid(row=0,column=0,rowspan=4,sticky='nsew',padx=(18,12),pady=18);sidebar.grid_columnconfigure(0,weight=1);sidebar.grid_rowconfigure(2,weight=1)
        ctk.CTkLabel(sidebar,text='Tutorial',font=('Segoe UI',23,'bold'),text_color=palette['text'],anchor='w').grid(row=0,column=0,sticky='ew',padx=16,pady=(16,12))
        search_row=ctk.CTkFrame(sidebar,fg_color='transparent');search_row.grid(row=1,column=0,sticky='ew',padx=12,pady=(0,12));search_row.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(search_row,text='Find a topic',font=('Segoe UI',11),text_color=palette['muted'],anchor='w').grid(row=0,column=0,columnspan=2,sticky='w',pady=(0,4))
        self.search=ctk.CTkEntry(search_row,placeholder_text='Search topics',width=155,height=34,fg_color=palette['bg'],text_color=palette['text'],border_color=palette['line']);self.search.grid(row=1,column=0,sticky='ew');self.search.bind('<KeyRelease>',lambda e:self.filter())
        self.button(search_row,'Clear',self.clear_search,width=50,height=34,font=('Segoe UI',11)).grid(row=1,column=1,padx=(6,0))
        self.navigation=ctk.CTkScrollableFrame(sidebar,fg_color='transparent',width=215);self.navigation.grid(row=2,column=0,sticky='nsew',padx=6)
        self.search_hint=ctk.CTkLabel(sidebar,text='',font=('Segoe UI',11),text_color=palette['muted'],wraplength=200,justify='left',anchor='w');self.search_hint.grid(row=3,column=0,sticky='ew',padx=16,pady=(10,16))
        self.title=ctk.CTkLabel(w,text='',text_color=palette['text'],font=('Segoe UI',25,'bold'),anchor='w',justify='left',wraplength=530);self.title.grid(row=0,column=1,sticky='ew',padx=(8,26),pady=(26,4))
        self.summary=ctk.CTkLabel(w,text='',text_color=palette['muted'],font=('Segoe UI',13),anchor='w',justify='left',wraplength=530);self.summary.grid(row=1,column=1,sticky='ew',padx=(8,26),pady=(0,16))
        self.content=ctk.CTkScrollableFrame(w,fg_color='transparent');self.content.grid(row=2,column=1,sticky='nsew',padx=(0,18));self.content.grid_columnconfigure(0,weight=1)
        self.content._parent_canvas.bind('<Configure>',self.resize_text,add='+')
        buttons=ctk.CTkFrame(w,fg_color='transparent');buttons.grid(row=3,column=1,sticky='ew',padx=(8,26),pady=(16,20));buttons.grid_columnconfigure(1,weight=1)
        self.back=self.button(buttons,'Previous',lambda:self.move(-1),width=105);self.back.grid(row=0,column=0)
        self.step=ctk.CTkLabel(buttons,text='',text_color=palette['muted'],font=('Segoe UI',12));self.step.grid(row=0,column=1)
        self.next=self.button(buttons,'Next topic',lambda:self.move(1),width=105);self.next.grid(row=0,column=2)
        self.filter()
    def button(self,parent,text,command,**kwargs):
        return ctk.CTkButton(parent,text=text,command=command,fg_color=self.palette['accent'],hover_color=self.palette['accent_hover'],**kwargs)
    def filter(self):
        self.visible=matching_topics(self.search.get())
        for child in self.navigation.winfo_children():child.destroy()
        self.topic_buttons={}
        for i in self.visible:
            button=self.button(self.navigation,f'{i+1:02}  {TOPICS[i]["title"]}',lambda i=i:self.select(i),width=213,height=36,anchor='w',font=('Segoe UI',12))
            button.pack(fill='x',pady=2);self.topic_buttons[i]=button
        self.search_hint.configure(text=(f'{len(self.visible)} topics found. Clear search to see all.' if self.search.get() else 'Choose a topic, or use Next topic. Scroll each page to read more.') if self.visible else 'No matching topics. Try save, colour, keyboard or update.')
        if self.visible and self.index not in self.visible:self.index=self.visible[0]
        self.show()
    def select(self,index):self.index=index;self.show()
    def clear_search(self):self.search.delete(0,'end');self.filter()
    def show(self):
        topic=TOPICS[self.index];self.title.configure(text=topic['title']);self.summary.configure(text=topic['summary'])
        for child in self.content.winfo_children():child.destroy()
        self.wrapped=[]
        for i,(heading,text) in enumerate(topic['sections']):
            card=ctk.CTkFrame(self.content,fg_color=self.palette['panel']);card.grid(row=i,column=0,sticky='ew',padx=8,pady=(0,12));card.grid_columnconfigure(0,weight=1)
            title=ctk.CTkLabel(card,text=heading,font=('Segoe UI',16,'bold'),text_color=self.palette['text'],wraplength=480,justify='left',anchor='w');title.grid(row=0,column=0,sticky='ew',padx=18,pady=(16,8))
            body=ctk.CTkLabel(card,text=text,font=('Segoe UI',14),text_color=self.palette['text'],wraplength=480,justify='left',anchor='w');body.grid(row=1,column=0,sticky='ew',padx=18,pady=(0,18));self.wrapped.extend([title,body])
        for i,button in self.topic_buttons.items():button.configure(fg_color=self.palette['accent'] if i==self.index else 'transparent',text_color='#FFFFFF' if i==self.index else self.palette['text'],hover_color=self.palette['accent_hover'] if i==self.index else self.palette['hover'])
        position=self.visible.index(self.index) if self.index in self.visible else -1
        self.step.configure(text=f'Topic {self.index+1} of {len(TOPICS)}')
        self.back.configure(state='normal' if position>0 else 'disabled')
        self.next.configure(state='normal' if position>=0 else 'disabled',text='Finish' if position==len(self.visible)-1 and position>=0 else 'Next topic')
        self.resize_text();self.content._parent_canvas.yview_moveto(0)
    def resize_text(self,event=None):
        width=self.content._reverse_widget_scaling(event.width if event else self.content._parent_canvas.winfo_width())
        wrap=max(340,int(width)-60)
        for label in self.wrapped:label.configure(wraplength=wrap)
        self.title.configure(wraplength=wrap+20);self.summary.configure(wraplength=wrap+20)
    def move(self,amount):
        if self.index not in self.visible:return
        position=self.visible.index(self.index)+amount
        if position>=len(self.visible):self.window.destroy();return
        self.select(self.visible[max(0,position)])

class Credits:
    def __init__(self,app,palette):
        self.window=ctk.CTkToplevel(app.root);w=self.window
        w.title('Credits');w.geometry('400x365');w.resizable(False,False);w.transient(app.root);w.configure(fg_color=palette['bg'])
        set_icon(w)
        with Image.open(Path(__file__).resolve().parent/'assets/harley.png') as picture:
            self.picture=ctk.CTkImage(light_image=picture.copy(),dark_image=picture.copy(),size=(100,124))
        ctk.CTkLabel(w,text='',image=self.picture).pack(pady=(28,20))
        ctk.CTkLabel(w,text='Made by Harley',font=('Segoe UI',24,'bold'),text_color=palette['text']).pack()
        ctk.CTkLabel(w,text='discord: harleydabrit',font=('Segoe UI',15),text_color=palette['muted']).pack(pady=(8,22))
        ctk.CTkButton(w,text='Close',command=w.destroy,width=110,fg_color=palette['accent'],hover_color=palette['accent_hover']).pack()
